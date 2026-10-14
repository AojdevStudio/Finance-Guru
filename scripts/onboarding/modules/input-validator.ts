export const RISK_TOLERANCES = ['aggressive', 'moderate', 'conservative'] as const;
export type RiskTolerance = (typeof RISK_TOLERANCES)[number];

export const INVESTMENT_PHILOSOPHIES = [
  'aggressive_growth',
  'growth_and_income',
  'income_focused',
  'index_investing'
] as const;
export type InvestmentPhilosophy = (typeof INVESTMENT_PHILOSOPHIES)[number];

function matchOneOf<T extends string>(values: readonly T[], input: string): T | undefined {
  return values.find(value => value === input);
}

export function validateCurrency(input: string): number {
  const cleaned = input.replace(/[$,]/g, '').trim();

  const num = parseFloat(cleaned);

  if (isNaN(num)) {
    throw new Error(`Invalid currency format: ${input}`);
  }

  if (num < 0) {
    throw new Error(`Currency must be positive: ${input}`);
  }

  return num;
}

export function validatePercentage(input: string): number {
  const cleaned = input.replace(/%/g, '').trim();

  const num = parseFloat(cleaned);

  if (isNaN(num)) {
    throw new Error(`Invalid percentage format: ${input}`);
  }

  if (num < 0 || num > 100) {
    throw new Error(`Percentage must be between 0 and 100: ${input}`);
  }

  return num;
}

/** Converts a percentage such as 4.5 (from validatePercentage) to the rate 0.045. */
export function percentToRate(percent: number): number {
  return percent / 100;
}

export function validatePositiveInteger(input: string): number {
  const num = parseInt(input.trim(), 10);

  if (isNaN(num)) {
    throw new Error(`Invalid integer format: ${input}`);
  }

  if (num < 0) {
    throw new Error(`Integer must be positive: ${input}`);
  }

  return num;
}

export function validateNonEmpty(input: string): string {
  const trimmed = input.trim();

  if (trimmed.length === 0) {
    throw new Error('Input cannot be empty');
  }

  return trimmed;
}

export function validateEmail(input: string): string {
  const trimmed = input.trim();
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  if (!emailRegex.test(trimmed)) {
    throw new Error(`Invalid email format: ${input}`);
  }

  return trimmed;
}

export function validateRiskTolerance(input: string): RiskTolerance {
  const match = matchOneOf(RISK_TOLERANCES, input.toLowerCase().trim());

  if (match) {
    return match;
  }

  throw new Error(`Invalid risk tolerance: ${input}. Must be one of: ${RISK_TOLERANCES.join(', ')}`);
}

export function validateInvestmentPhilosophy(input: string): InvestmentPhilosophy {
  const match = matchOneOf(INVESTMENT_PHILOSOPHIES, input.toLowerCase().replace(/\s+/g, '_').trim());

  if (match) {
    return match;
  }

  throw new Error(
    `Invalid investment philosophy: ${input}. Must be one of: ${INVESTMENT_PHILOSOPHIES.join(', ')}`
  );
}

export function validateBrokerage(input: string): string {
  const normalized = input.trim();

  const knownBrokerages: Record<string, string> = {
    'fidelity': 'Fidelity',
    'schwab': 'Charles Schwab',
    'vanguard': 'Vanguard',
    'etrade': 'E*TRADE',
    'td ameritrade': 'TD Ameritrade',
    'merrill': 'Merrill Lynch',
    'robinhood': 'Robinhood',
    'webull': 'Webull',
    'interactive brokers': 'Interactive Brokers',
    'm1 finance': 'M1 Finance'
  };

  const lowerInput = normalized.toLowerCase();

  return knownBrokerages[lowerInput] || normalized;
}

export function validateEnum(input: string, allowedValues: string[], fieldName: string = 'value'): string {
  const normalized = input.toLowerCase().trim();

  if (allowedValues.includes(normalized)) {
    return normalized;
  }

  throw new Error(`Invalid ${fieldName}: ${input}. Must be one of: ${allowedValues.join(', ')}`);
}
