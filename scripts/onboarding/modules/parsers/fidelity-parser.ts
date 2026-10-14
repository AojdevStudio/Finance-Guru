import { readFile } from 'fs/promises';
import type { BrokerCSVParser, Position, AccountBalances } from '../broker-types';

const FIDELITY_CORE_CASH_SYMBOLS: ReadonlySet<string> = new Set(['SPAXX', 'FDRXX', 'FCASH']);

/** Parses a Fidelity amount such as `$1,234.56` or `($12.34)`. Parentheses mean negative. */
export function parseAccountingNumber(raw: string): number {
  const trimmed = raw.trim();
  const negative = /^\(.*\)$/.test(trimmed);
  const value = parseFloat(trimmed.replace(/[$,()\s]/g, ''));
  return negative ? -Math.abs(value) : value;
}

export function parseCSVLine(line: string): string[] {
  const result: string[] = [];
  let current = '';
  let inQuotes = false;

  for (let i = 0; i < line.length; i++) {
    const char = line[i];

    if (char === '"' && inQuotes && line[i + 1] === '"') {
      current += '"';
      i++;
    } else if (char === '"') {
      inQuotes = !inQuotes;
    } else if (char === ',' && !inQuotes) {
      result.push(current);
      current = '';
    } else {
      current += char;
    }
  }

  result.push(current);
  return result;
}

export class FidelityParser implements BrokerCSVParser {
  async parsePositionsCSV(csvPath: string): Promise<Position[]> {
    const content = await readFile(csvPath, 'utf-8');
    const lines = content.split('\n').filter(line => line.trim());

    if (lines.length < 2) {
      throw new Error('CSV file is empty or has no data rows');
    }

    const header = lines[0].split(',').map(h => h.trim().toLowerCase());
    const symbolIdx = header.indexOf('symbol');
    const quantityIdx = header.indexOf('quantity');
    const lastPriceIdx = header.indexOf('last price');
    const currentValueIdx = header.indexOf('current value');
    const costBasisIdx = this.findCostBasisColumn(header);

    if (symbolIdx === -1 || quantityIdx === -1 || costBasisIdx === -1) {
      throw new Error('Required columns not found in CSV. Expected: Symbol, Quantity, Average Cost Basis');
    }

    const positions: Position[] = [];

    for (let i = 1; i < lines.length; i++) {
      const line = lines[i];
      if (!line.trim()) continue;

      const columns = parseCSVLine(line);

      const symbol = columns[symbolIdx]?.trim();
      const quantityStr = columns[quantityIdx];
      const lastPriceStr = columns[lastPriceIdx];
      const currentValueStr = columns[currentValueIdx];
      const costBasisStr = columns[costBasisIdx];

      if (!symbol || !quantityStr || !costBasisStr) continue;

      if (FIDELITY_CORE_CASH_SYMBOLS.has(symbol)) continue;

      const quantity = parseAccountingNumber(quantityStr);
      const costBasis = parseAccountingNumber(costBasisStr);

      if (isNaN(quantity) || isNaN(costBasis)) {
        console.warn(`Skipping invalid row: ${symbol} (quantity: ${quantityStr}, cost basis: ${costBasisStr})`);
        continue;
      }

      const position: Position = {
        symbol,
        quantity,
        averageCostBasis: costBasis
      };

      if (lastPriceIdx !== -1 && lastPriceStr) {
        const lastPrice = parseAccountingNumber(lastPriceStr);
        if (!isNaN(lastPrice)) {
          position.lastPrice = lastPrice;
        }
      }

      if (currentValueIdx !== -1 && currentValueStr) {
        const currentValue = parseAccountingNumber(currentValueStr);
        if (!isNaN(currentValue)) {
          position.currentValue = currentValue;
        }
      }

      positions.push(position);
    }

    return positions;
  }

  async parseBalancesCSV(csvPath: string): Promise<AccountBalances> {
    const content = await readFile(csvPath, 'utf-8');
    const lines = content.split('\n').filter(line => line.trim());

    const balances: Partial<AccountBalances> = {
      settledCash: 0,
      netDebit: 0,
      accountEquityPercentage: 100,
      marginInterestAccrued: 0,
      totalAccountValue: 0
    };

    for (const line of lines) {
      const [key, value] = parseCSVLine(line).map(s => s.trim());
      if (!key || !value) continue;

      const keyLower = key.toLowerCase();
      const numericValue = parseAccountingNumber(value);

      if (keyLower.includes('settled cash')) {
        balances.settledCash = numericValue || 0;
      } else if (keyLower.includes('net debit')) {
        balances.netDebit = numericValue;
      } else if (keyLower.includes('account equity percentage') || keyLower.includes('equity percentage')) {
        balances.accountEquityPercentage = numericValue || 100;
      } else if (keyLower.includes('margin interest accrued')) {
        balances.marginInterestAccrued = numericValue || 0;
      } else if (keyLower.includes('total account value') || keyLower.includes('account value')) {
        balances.totalAccountValue = numericValue || 0;
      }
    }

    return balances as AccountBalances;
  }

  async validateCSVFormat(csvPath: string): Promise<boolean> {
    try {
      const content = await readFile(csvPath, 'utf-8');
      const lines = content.split('\n').filter(line => line.trim());

      if (lines.length < 2) return false;

      const header = lines[0].toLowerCase();

      const hasFidelityColumns =
        header.includes('symbol') &&
        (header.includes('quantity') || header.includes('qty')) &&
        (header.includes('average cost basis') || header.includes('cost basis'));

      return hasFidelityColumns;
    } catch (error) {
      return false;
    }
  }

  getExpectedFilePatterns() {
    return {
      positions: [
        'Portfolio_Positions_*.csv',
        'portfolio_positions_*.csv',
        'positions_*.csv',
        'fidelity_positions_*.csv'
      ],
      balances: [
        'Balances_for_Account_*.csv',
        'balances_for_account_*.csv',
        'account_balances_*.csv',
        'fidelity_balances_*.csv'
      ]
    };
  }

  private findCostBasisColumn(header: string[]): number {
    const costBasisVariants = [
      'average cost basis',
      'avg cost basis',
      'cost basis',
      'average cost',
      'avg cost',
      'basis'
    ];

    for (const variant of costBasisVariants) {
      const idx = header.findIndex(h => h.includes(variant));
      if (idx !== -1) return idx;
    }

    return -1;
  }
}

export function createFidelityParser(): BrokerCSVParser {
  return new FidelityParser();
}
