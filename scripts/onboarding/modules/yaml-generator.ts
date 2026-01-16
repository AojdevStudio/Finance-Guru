/**
 * YAML Generation Module
 * Generates configuration files from templates and user data
 */

import { readFileSync, writeFileSync } from 'fs';
import { join } from 'path';

export interface UserData {
  // User identity
  user_name: string;
  language?: string;

  // Liquid assets
  liquid_assets_total?: number;
  liquid_assets_count?: number;
  liquid_assets_yield?: number;
  liquid_assets_structure?: string;

  // Investment portfolio
  portfolio_value?: number;
  brokerage?: string;
  has_retirement?: boolean;
  retirement_value?: number;
  allocation_strategy?: string;
  risk_tolerance?: string;
  google_sheets_id?: string;

  // Cash flow
  monthly_income?: number;
  fixed_expenses?: number;
  variable_expenses?: number;
  current_savings?: number;
  investment_capacity?: number;

  // Debt
  has_mortgage?: boolean;
  mortgage_balance?: number;
  mortgage_payment?: number;
  has_student_loans?: boolean;
  student_loan_balance?: number;
  student_loan_rate?: number;
  has_auto_loans?: boolean;
  auto_loan_balance?: number;
  auto_loan_rate?: number;
  has_credit_cards?: boolean;
  credit_card_balance?: number;
  weighted_rate?: number;
  other_debt?: string;

  // Preferences
  investment_philosophy?: string;
  focus_areas?: string[];
  emergency_fund_months?: number;

  // MCP Config
  has_alphavantage?: boolean;
  alphavantage_key?: string;
  has_brightdata?: boolean;
  brightdata_key?: string;

  // Environment
  google_sheets_credentials?: string;
  account_number?: string;
  project_root?: string;

  // Generated fields
  timestamp?: string;
  date?: string;
  repository_name?: string;
  possessive_name?: string;
  portfolio_value_formatted?: string;
  monthly_income_formatted?: string;
  investment_capacity_formatted?: string;
  focus_areas_list?: string;
}

/**
 * Simple template variable substitution
 * Replaces {{variable}} with values from data object
 * Supports {{#if condition}}...{{/if}} for conditional blocks
 * @param template - Template string
 * @param data - Data object with values
 * @returns Processed template
 */
function processTemplate(template: string, data: Record<string, any>): string {
  let result = template;

  // Handle conditional blocks {{#if variable}}...{{/if}}
  const ifRegex = /\{\{#if\s+(\w+)\}\}([\s\S]*?)\{\{\/if\}\}/g;
  result = result.replace(ifRegex, (match, condition, content) => {
    const value = data[condition];
    // Include block if value is truthy
    return value ? content : '';
  });

  // Replace simple variables {{variable}}
  const varRegex = /\{\{(\w+)\}\}/g;
  result = result.replace(varRegex, (match, key) => {
    const value = data[key];
    return value !== undefined && value !== null ? String(value) : '';
  });

  return result;
}

/**
 * Prepares user data with computed fields
 * @param data - Raw user data
 * @returns Enhanced data with computed fields
 */
function prepareUserData(data: UserData): Record<string, any> {
  const now = new Date();
  const timestamp = now.toISOString();
  const date = now.toISOString().split('T')[0];

  // Compute possessive form (simple, just add 's)
  const possessiveName = data.user_name.endsWith('s')
    ? `${data.user_name}'`
    : `${data.user_name}'s`;

  // Format currency values
  const formatCurrency = (value?: number) => {
    if (!value) return '$0';
    return `$${value.toLocaleString('en-US')}`;
  };

  return {
    ...data,
    timestamp,
    date,
    possessive_name: possessiveName,
    repository_name: 'family-office',
    project_root: process.cwd(),
    portfolio_value_formatted: formatCurrency(data.portfolio_value),
    monthly_income_formatted: formatCurrency(data.monthly_income),
    investment_capacity_formatted: formatCurrency(data.investment_capacity),
    focus_areas_list: data.focus_areas ? data.focus_areas.join(', ') : ''
  };
}

/**
 * Loads a template file
 * @param templateName - Name of template file (without .template extension)
 * @returns Template content
 */
function loadTemplate(templateName: string): string {
  const templatePath = join(__dirname, 'templates', `${templateName}.template.yaml`);

  try {
    return readFileSync(templatePath, 'utf-8');
  } catch (error) {
    throw new Error(`Failed to load template ${templateName}: ${error}`);
  }
}

/**
 * Generates user-profile.yaml from template
 * @param data - User data
 * @returns Generated YAML content
 */
export function generateUserProfile(data: UserData): string {
  const template = loadTemplate('user-profile');
  const preparedData = prepareUserData(data);
  return processTemplate(template, preparedData);
}

/**
 * Generates config.yaml from template
 * @param data - User data
 * @returns Generated YAML content
 */
export function generateConfig(data: UserData): string {
  const template = loadTemplate('config');
  const preparedData = prepareUserData(data);
  return processTemplate(template, preparedData);
}

/**
 * Generates system-context.md from template
 * @param data - User data
 * @returns Generated markdown content
 */
export function generateSystemContext(data: UserData): string {
  const templatePath = join(__dirname, 'templates', 'system-context.template.md');

  try {
    const template = readFileSync(templatePath, 'utf-8');
    const preparedData = prepareUserData(data);
    return processTemplate(template, preparedData);
  } catch (error) {
    throw new Error(`Failed to generate system-context.md: ${error}`);
  }
}

/**
 * Generates CLAUDE.md from template
 * @param data - User data
 * @returns Generated markdown content
 */
export function generateClaudeMd(data: UserData): string {
  const templatePath = join(__dirname, 'templates', 'CLAUDE.template.md');

  try {
    const template = readFileSync(templatePath, 'utf-8');
    const preparedData = prepareUserData(data);
    return processTemplate(template, preparedData);
  } catch (error) {
    throw new Error(`Failed to generate CLAUDE.md: ${error}`);
  }
}

/**
 * Generates .env file from template
 * @param data - User data
 * @returns Generated .env content
 */
export function generateEnv(data: UserData): string {
  const templatePath = join(__dirname, 'templates', 'env.template');

  try {
    const template = readFileSync(templatePath, 'utf-8');
    const preparedData = prepareUserData(data);
    return processTemplate(template, preparedData);
  } catch (error) {
    throw new Error(`Failed to generate .env: ${error}`);
  }
}

/**
 * Writes generated content to a file
 * @param filePath - Absolute path to output file
 * @param content - Content to write
 */
export function writeConfigFile(filePath: string, content: string): void {
  try {
    writeFileSync(filePath, content, 'utf-8');
  } catch (error) {
    throw new Error(`Failed to write file ${filePath}: ${error}`);
  }
}

/**
 * Generates all configuration files
 * @param data - Complete user data
 * @param outputDir - Base directory for output files
 */
export function generateAllConfigs(data: UserData, outputDir: string = process.cwd()): void {
  const configs = [
    {
      path: join(outputDir, 'fin-guru', 'data', 'user-profile.yaml'),
      content: generateUserProfile(data)
    },
    {
      path: join(outputDir, 'fin-guru', 'config.yaml'),
      content: generateConfig(data)
    },
    {
      path: join(outputDir, 'fin-guru', 'data', 'system-context.md'),
      content: generateSystemContext(data)
    },
    {
      path: join(outputDir, 'CLAUDE.md'),
      content: generateClaudeMd(data)
    },
    {
      path: join(outputDir, '.env'),
      content: generateEnv(data)
    }
  ];

  for (const config of configs) {
    writeConfigFile(config.path, config.content);
  }
}
