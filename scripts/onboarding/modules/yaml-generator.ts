import { mkdirSync, readFileSync, writeFileSync } from 'fs';
import { join } from 'path';

type LiquidAssetsData = {
  liquid_assets_total?: number;
  liquid_assets_count?: number;
  liquid_assets_yield?: number;
  liquid_assets_structure?: string;
};

type PortfolioData = {
  portfolio_value?: number;
  brokerage?: string;
  broker_type?: string;
  broker_name?: string;
  has_retirement?: boolean;
  retirement_value?: number;
  allocation_strategy?: string;
  risk_tolerance?: string;
  google_sheets_id?: string;
};

type CashFlowData = {
  monthly_income?: number;
  fixed_expenses?: number;
  variable_expenses?: number;
  current_savings?: number;
  investment_capacity?: number;
};

type DebtData = {
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
};

type PreferencesData = {
  investment_philosophy?: string;
  focus_areas?: string[];
  emergency_fund_months?: number;
};

type EnvironmentData = {
  has_alphavantage?: boolean;
  alphavantage_key?: string;
  has_brightdata?: boolean;
  brightdata_key?: string;
  google_sheets_credentials?: string;
  account_number?: string;
};

export type UserData = {
  user_name: string;
  language?: string;
} & LiquidAssetsData &
  PortfolioData &
  CashFlowData &
  DebtData &
  PreferencesData &
  EnvironmentData;

/** Values the templates read that are derived from UserData at generation time. */
type DerivedTemplateData = {
  timestamp: string;
  date: string;
  repository_name: string;
  possessive_name: string;
  project_root: string;
  portfolio_value_formatted: string;
  monthly_income_formatted: string;
  investment_capacity_formatted: string;
  focus_areas_list: string;
};

export type TemplateData = UserData & DerivedTemplateData;

function processTemplate(template: string, data: Readonly<Record<string, unknown>>): string {
  let result = template;

  const ifRegex = /\{\{#if\s+(\w+)\}\}([\s\S]*?)\{\{\/if\}\}/g;
  result = result.replace(ifRegex, (match, condition: string, content: string) => {
    const value = data[condition];
    return value ? content : '';
  });

  const varRegex = /\{\{(\w+)\}\}/g;
  result = result.replace(varRegex, (match, key: string) => {
    const value = data[key];
    return value !== undefined && value !== null ? String(value) : '';
  });

  return result;
}

export function possessive(name: string): string {
  return name.endsWith('s') ? `${name}'` : `${name}'s`;
}

function formatCurrency(value?: number): string {
  if (!value) return '$0';
  return `$${value.toLocaleString('en-US')}`;
}

function prepareUserData(data: UserData): TemplateData {
  const now = new Date();
  const timestamp = now.toISOString();
  const date = now.toISOString().split('T')[0];

  return {
    ...data,
    timestamp,
    date,
    possessive_name: possessive(data.user_name),
    repository_name: 'family-office',
    project_root: process.cwd(),
    portfolio_value_formatted: formatCurrency(data.portfolio_value),
    monthly_income_formatted: formatCurrency(data.monthly_income),
    investment_capacity_formatted: formatCurrency(data.investment_capacity),
    focus_areas_list: data.focus_areas ? data.focus_areas.join(', ') : ''
  };
}

function loadTemplate(templateName: string): string {
  const templatePath = join(__dirname, 'templates', `${templateName}.template.yaml`);

  try {
    return readFileSync(templatePath, 'utf-8');
  } catch (error) {
    throw new Error(`Failed to load template ${templateName}: ${error}`);
  }
}

export function generateUserProfile(data: UserData): string {
  const template = loadTemplate('user-profile');
  const preparedData = prepareUserData(data);
  return processTemplate(template, preparedData);
}

export function generateConfig(data: UserData): string {
  const template = loadTemplate('config');
  const preparedData = prepareUserData(data);
  return processTemplate(template, preparedData);
}

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

export function writeConfigFile(filePath: string, content: string): void {
  try {
    writeFileSync(filePath, content, 'utf-8');
  } catch (error) {
    throw new Error(`Failed to write file ${filePath}: ${error}`);
  }
}

export function generateAllConfigs(data: UserData, outputDir: string = process.cwd()): void {
  const importDirectories = [
    join(outputDir, 'imports'),
    join(outputDir, 'imports', 'transactions'),
    join(outputDir, 'imports', 'retirement')
  ];

  for (const directory of importDirectories) {
    mkdirSync(directory, { recursive: true });
  }

  const configs = [
    {
      path: join(outputDir, 'user-profile.yaml'),
      content: generateUserProfile(data)
    },
    {
      path: join(outputDir, 'config.yaml'),
      content: generateConfig(data)
    },
    {
      path: join(outputDir, 'system-context.md'),
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
