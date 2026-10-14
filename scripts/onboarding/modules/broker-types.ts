export type BrokerType = 'fidelity' | 'schwab' | 'vanguard' | 'td_ameritrade' | 'etrade' | 'robinhood' | 'other';

export interface BrokerInfo {
  id: BrokerType;
  name: string;
  description: string;
  csvExportGuide: string;
}

export interface Position {
  symbol: string;
  quantity: number;
  averageCostBasis: number;
  lastPrice?: number;
  currentValue?: number;
}

export interface AccountBalances {
  settledCash: number;
  netDebit: number;
  accountEquityPercentage: number;
  marginInterestAccrued: number;
  totalAccountValue: number;
}

export interface ParsedPortfolioData {
  positions: Position[];
  balances: AccountBalances;
  broker: BrokerType;
  exportDate: Date;
}

export interface BrokerCSVParser {
  parsePositionsCSV(csvPath: string): Promise<Position[]>;

  parseBalancesCSV(csvPath: string): Promise<AccountBalances>;

  validateCSVFormat(csvPath: string): Promise<boolean>;

  getExpectedFilePatterns(): {
    positions: string[];
    balances: string[];
  };
}

export const SUPPORTED_BROKERS: Record<BrokerType, BrokerInfo> = {
  fidelity: {
    id: 'fidelity',
    name: 'Fidelity Investments',
    description: 'One of the largest brokerages in the US. Export from Accounts > Positions.',
    csvExportGuide: 'Login → Accounts → Select Account → Positions → Export'
  },
  schwab: {
    id: 'schwab',
    name: 'Charles Schwab',
    description: 'Full-service brokerage. Export from Account Positions.',
    csvExportGuide: 'Login → Accounts → Positions → Export to CSV'
  },
  vanguard: {
    id: 'vanguard',
    name: 'Vanguard',
    description: 'Index fund pioneer. Export from Holdings.',
    csvExportGuide: 'Login → My Accounts → Holdings → Download'
  },
  td_ameritrade: {
    id: 'td_ameritrade',
    name: 'TD Ameritrade',
    description: 'Now owned by Schwab. Export from Account Statement.',
    csvExportGuide: 'Login → My Account → Statements → Download CSV'
  },
  etrade: {
    id: 'etrade',
    name: 'E*TRADE',
    description: 'Morgan Stanley brokerage. Export from Portfolio.',
    csvExportGuide: 'Login → Portfolio → Complete View → Export'
  },
  robinhood: {
    id: 'robinhood',
    name: 'Robinhood',
    description: 'Commission-free trading app. Export from Account.',
    csvExportGuide: 'App → Account → Statements & History → Account Statements'
  },
  other: {
    id: 'other',
    name: 'Other Broker',
    description: 'Manual CSV import. You will need to map columns manually.',
    csvExportGuide: 'Export positions and balances to CSV format'
  }
};

export function getBrokerInfo(brokerId: BrokerType): BrokerInfo {
  return SUPPORTED_BROKERS[brokerId];
}

export function getAllBrokers(): BrokerInfo[] {
  return Object.values(SUPPORTED_BROKERS);
}

export function getBrokerDisplayName(brokerId: BrokerType): string {
  return SUPPORTED_BROKERS[brokerId]?.name || 'Unknown Broker';
}
