import { afterAll, beforeAll, describe, expect, it } from 'bun:test';
import { mkdtemp, rm, writeFile } from 'fs/promises';
import { tmpdir } from 'os';
import { join } from 'path';
import {
  FidelityParser,
  parseAccountingNumber,
  parseCSVLine
} from '../../scripts/onboarding/modules/parsers/fidelity-parser';

let dir: string;

beforeAll(async () => {
  dir = await mkdtemp(join(tmpdir(), 'fidelity-parser-'));
});

afterAll(async () => {
  await rm(dir, { recursive: true, force: true });
});

async function csv(name: string, content: string): Promise<string> {
  const path = join(dir, name);
  await writeFile(path, content);
  return path;
}

describe('parseAccountingNumber', () => {
  it('reads parentheses as a negative value', () => {
    expect(parseAccountingNumber('($1,234.56)')).toBe(-1234.56);
  });

  it('reads a plain dollar amount', () => {
    expect(parseAccountingNumber('$1,234.56')).toBe(1234.56);
  });

  it('keeps a leading minus sign', () => {
    expect(parseAccountingNumber('-$12.50')).toBe(-12.5);
  });

  it('returns NaN for text that is not a number', () => {
    expect(parseAccountingNumber('n/a')).toBeNaN();
  });
});

describe('parseCSVLine', () => {
  it('keeps an escaped quote inside a quoted field', () => {
    expect(parseCSVLine('ABC,"ABC ""Class A"", Shares",10')).toEqual([
      'ABC',
      'ABC "Class A", Shares',
      '10'
    ]);
  });
});

describe('FidelityParser.parseBalancesCSV', () => {
  it('keeps the sign of every parenthesized balance, not only net debit', async () => {
    const path = await csv(
      'balances.csv',
      [
        'Settled cash,($250.00)',
        'Net debit,"($1,000.00)"',
        'Margin interest accrued,($12.34)',
        'Total account value,"$10,500.00"'
      ].join('\n')
    );

    const balances = await new FidelityParser().parseBalancesCSV(path);

    expect(balances.settledCash).toBe(-250);
    expect(balances.netDebit).toBe(-1000);
    expect(balances.marginInterestAccrued).toBe(-12.34);
    expect(balances.totalAccountValue).toBe(10500);
  });

  it('keeps a negative equity percentage and total account value', async () => {
    const path = await csv(
      'negative-balances.csv',
      ['Account equity percentage,(12.50%)', 'Total account value,"($2,000.00)"'].join('\n')
    );

    const balances = await new FidelityParser().parseBalancesCSV(path);

    expect(balances.accountEquityPercentage).toBe(-12.5);
    expect(balances.totalAccountValue).toBe(-2000);
  });
});

describe('FidelityParser.parsePositionsCSV', () => {
  it('reads a quoted field that holds an escaped quote', async () => {
    const path = await csv(
      'positions.csv',
      [
        'Symbol,Description,Quantity,Last Price,Current Value,Average Cost Basis',
        'ABC,"ABC ""Class A"" Shares",10,$5.00,"$1,050.00",$4.00',
        'SPAXX,Money market,100,$1.00,$100.00,$1.00'
      ].join('\n')
    );

    const positions = await new FidelityParser().parsePositionsCSV(path);

    expect(positions).toEqual([
      { symbol: 'ABC', quantity: 10, averageCostBasis: 4, lastPrice: 5, currentValue: 1050 }
    ]);
  });

  it('keeps the sign of every numeric position field', async () => {
    const path = await csv(
      'short-positions.csv',
      [
        'Symbol,Description,Quantity,Last Price,Current Value,Average Cost Basis',
        'XYZ,Short position,(10),($5.00),"($1,050.00)",($4.00)'
      ].join('\n')
    );

    const positions = await new FidelityParser().parsePositionsCSV(path);

    expect(positions).toEqual([
      { symbol: 'XYZ', quantity: -10, averageCostBasis: -4, lastPrice: -5, currentValue: -1050 }
    ]);
  });
});
