/**
 * Input Validation Module
 * Provides validation utilities for Finance Guru onboarding CLI
 */

export type RiskTolerance = 'aggressive' | 'moderate' | 'conservative';
export type InvestmentPhilosophy = 'aggressive_growth' | 'growth_and_income' | 'income_focused' | 'index_investing';

/**
 * Validates currency input
 * Accepts formats: "10000", "$10,000", "10000.50"
 * @param input - String to validate as currency
 * @returns Number value or throws error
 */
export function validateCurrency(input: string): number {
  // Remove $ and , characters
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

/**
 * Validates percentage input
 * Accepts formats: "4.5", "4.5%", "100"
 * @param input - String to validate as percentage
 * @returns Number value (0-100) or throws error
 */
export function validatePercentage(input: string): number {
  // Remove % character
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

/**
 * Validates positive integer input
 * @param input - String to validate as positive integer
 * @returns Integer value or throws error
 */
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

/**
 * Validates non-empty string
 * @param input - String to validate
 * @returns Trimmed string or throws error
 */
export function validateNonEmpty(input: string): string {
  const trimmed = input.trim();

  if (trimmed.length === 0) {
    throw new Error('Input cannot be empty');
  }

  return trimmed;
}

/**
 * Validates email format (basic validation)
 * @param input - String to validate as email
 * @returns Email string or throws error
 */
export function validateEmail(input: string): string {
  const trimmed = input.trim();
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  if (!emailRegex.test(trimmed)) {
    throw new Error(`Invalid email format: ${input}`);
  }

  return trimmed;
}

/**
 * Validates Google Sheets spreadsheet ID format
 * Expected format: 44-character alphanumeric string
 * @param input - String to validate as spreadsheet ID
 * @returns Spreadsheet ID or throws error
 */
export function validateSpreadsheetId(input: string): string {
  const trimmed = input.trim();

  // Google Sheets IDs are typically 44 characters long and alphanumeric with some special chars
  if (trimmed.length < 40) {
    throw new Error('Spreadsheet ID is too short (expected ~44 characters)');
  }

  const idRegex = /^[a-zA-Z0-9_-]+$/;
  if (!idRegex.test(trimmed)) {
    throw new Error(`Invalid spreadsheet ID format: ${input}`);
  }

  return trimmed;
}

/**
 * Validates risk tolerance input
 * @param input - String to validate
 * @returns Risk tolerance type or throws error
 */
export function validateRiskTolerance(input: string): RiskTolerance {
  const normalized = input.toLowerCase().trim();

  const validValues: RiskTolerance[] = ['aggressive', 'moderate', 'conservative'];

  if (validValues.includes(normalized as RiskTolerance)) {
    return normalized as RiskTolerance;
  }

  throw new Error(`Invalid risk tolerance: ${input}. Must be one of: ${validValues.join(', ')}`);
}

/**
 * Validates investment philosophy input
 * @param input - String to validate
 * @returns Philosophy type or throws error
 */
export function validateInvestmentPhilosophy(input: string): InvestmentPhilosophy {
  const normalized = input.toLowerCase().replace(/\s+/g, '_').trim();

  const validValues: InvestmentPhilosophy[] = [
    'aggressive_growth',
    'growth_and_income',
    'income_focused',
    'index_investing'
  ];

  if (validValues.includes(normalized as InvestmentPhilosophy)) {
    return normalized as InvestmentPhilosophy;
  }

  throw new Error(`Invalid investment philosophy: ${input}. Must be one of: ${validValues.join(', ')}`);
}

/**
 * Validates and normalizes brokerage name
 * @param input - Brokerage name to validate
 * @returns Normalized brokerage name
 */
export function validateBrokerage(input: string): string {
  const normalized = input.trim();

  // Known brokerages with capitalization standards
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

  // Return standardized name if known, otherwise return input as-is
  return knownBrokerages[lowerInput] || normalized;
}
