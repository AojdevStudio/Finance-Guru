import { createPrompt, promptWithValidation, type Prompt } from '../modules/prompt';
import { writeFileSync } from 'fs';
import { join } from 'path';
import { validateNonEmpty } from '../modules/input-validator';
import type { OnboardingState } from '../modules/progress';
import { saveSectionData, markSectionComplete, saveState } from '../modules/progress';

export interface EnvSetupData {
  user_name: string;
  communication_language: string;
  has_alphavantage?: boolean;
  alphavantage_key?: string;
  has_brightdata?: boolean;
  brightdata_key?: string;
  google_sheets_credentials?: string;
  primary_brokerage?: string;
  brokerage_account_number?: string;
}

async function promptYesNo(
  rl: Prompt,
  question: string
): Promise<boolean> {
  return new Promise((resolve) => {
    rl.question(`${question} (Y/n): `, (answer) => {
      const normalized = answer.trim().toLowerCase();
      resolve(normalized === 'y' || normalized === 'yes' || normalized === '');
    });
  });
}

function generateEnvFile(envData: EnvSetupData, state: OnboardingState): void {
  const timestamp = new Date().toISOString();
  const projectRoot = process.cwd();

  let envContent = `# Finance Guru Environment Configuration
# Generated: ${timestamp}

# User Configuration
USER_NAME="${envData.user_name}"
COMMUNICATION_LANGUAGE="${envData.communication_language}"
`;

  if (envData.has_alphavantage && envData.alphavantage_key) {
    envContent += `
# MCP Server Configuration
ALPHA_VANTAGE_API_KEY="${envData.alphavantage_key}"
`;
  }

  if (envData.has_brightdata && envData.brightdata_key) {
    if (!envData.has_alphavantage) {
      envContent += `\n# MCP Server Configuration\n`;
    }
    envContent += `BRIGHT_DATA_API_KEY="${envData.brightdata_key}"
`;
  }

  if (envData.google_sheets_credentials) {
    envContent += `
# Google Sheets Integration
GOOGLE_SHEETS_CREDENTIALS_PATH="${envData.google_sheets_credentials}"
`;
  }

  if (envData.primary_brokerage) {
    envContent += `
# Portfolio Tracking
PRIMARY_BROKERAGE="${envData.primary_brokerage}"
`;
    if (envData.brokerage_account_number) {
      envContent += `BROKERAGE_ACCOUNT_NUMBER="${envData.brokerage_account_number}"
`;
    }
  }

  envContent += `
# System Paths (auto-detected, edit if needed)
PROJECT_ROOT="${projectRoot}"
FIN_GURU_PATH="${projectRoot}/fin-guru"
NOTEBOOKS_PATH="${projectRoot}/notebooks"
`;

  const envPath = join(projectRoot, '.env');
  writeFileSync(envPath, envContent, { encoding: 'utf-8' });

  console.log('');
  console.log(`✅ Generated .env file at: ${envPath}`);
}

export async function runEnvSetupSection(state: OnboardingState): Promise<OnboardingState> {
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('🔐 Section 7 of 7: Environment Setup');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('');
  console.log('Finance Guru uses a .env file for sensitive configuration.');
  console.log('This includes API keys, user settings, and integration credentials.');
  console.log('');

  const rl = createPrompt();

  try {
    console.log('1. User Configuration');
    console.log('');

    const userName = await promptWithValidation(
      rl,
      'Your name (used in reports and agent communications): ',
      validateNonEmpty
    );

    const language = await promptWithValidation(
      rl,
      'Preferred language for communication (default: English): ',
      (input: string) => input.trim() || 'English',
      true
    );

    console.log('');
    console.log('2. API Keys (Optional)');
    console.log('');
    console.log('Finance Guru can integrate with various data providers.');
    console.log('These are optional - you can add them later if needed.');
    console.log('');

    const hasAlphaVantage = await promptYesNo(
      rl,
      'Do you have an Alpha Vantage API key? (free tier available at https://www.alphavantage.co)'
    );

    let alphaVantageKey: string | undefined;
    if (hasAlphaVantage) {
      alphaVantageKey = await promptWithValidation(
        rl,
        'Alpha Vantage API key: ',
        validateNonEmpty
      );
    }

    const hasBrightData = await promptYesNo(
      rl,
      'Do you have a Bright Data API key? (paid service for web scraping)'
    );

    let brightDataKey: string | undefined;
    if (hasBrightData) {
      brightDataKey = await promptWithValidation(
        rl,
        'Bright Data API key: ',
        validateNonEmpty
      );
    }

    console.log('');
    console.log('3. Google Sheets Integration (Optional)');
    console.log('');

    const hasGoogleSheets = await promptYesNo(
      rl,
      'Do you want to configure Google Sheets integration?'
    );

    let googleSheetsCredentials: string | null = null;
    if (hasGoogleSheets) {
      console.log('');
      console.log('You will need a Google Cloud service account credentials JSON file.');
      console.log('See: https://developers.google.com/sheets/api/quickstart');
      console.log('');

      googleSheetsCredentials = await promptWithValidation(
        rl,
        'Path to Google Sheets credentials JSON file (or press Enter to skip): ',
        (input: string) => input.trim(),
        true
      );
    }

    console.log('');
    console.log('4. Portfolio Tracking (Optional)');
    console.log('');

    const configurePortfolio = await promptYesNo(
      rl,
      'Do you want to configure portfolio tracking settings?'
    );

    let primaryBrokerage: string | undefined;
    let brokerageAccountNumber: string | undefined;

    if (configurePortfolio) {
      primaryBrokerage = await promptWithValidation(
        rl,
        'Primary brokerage (e.g., Fidelity, Schwab, Vanguard): ',
        validateNonEmpty
      );

      const wantAccountNumber = await promptYesNo(
        rl,
        'Do you want to store your brokerage account number?'
      );

      if (wantAccountNumber) {
        console.log('');
        console.log('⚠️  Warning: Account number will be stored in plain text in .env');
        console.log('Make sure .env is in .gitignore (it is by default)');
        console.log('');

        brokerageAccountNumber = await promptWithValidation(
          rl,
          'Brokerage account number: ',
          validateNonEmpty
        );
      }
    }

    const envData: EnvSetupData = {
      user_name: userName,
      communication_language: language || 'English'
    };

    if (hasAlphaVantage && alphaVantageKey) {
      envData.has_alphavantage = true;
      envData.alphavantage_key = alphaVantageKey;
    }

    if (hasBrightData && brightDataKey) {
      envData.has_brightdata = true;
      envData.brightdata_key = brightDataKey;
    }

    if (googleSheetsCredentials) {
      envData.google_sheets_credentials = googleSheetsCredentials;
    }

    if (primaryBrokerage) {
      envData.primary_brokerage = primaryBrokerage;
    }

    if (brokerageAccountNumber) {
      envData.brokerage_account_number = brokerageAccountNumber;
    }

    generateEnvFile(envData, state);

    saveSectionData(state, 'env_setup', envData);

    markSectionComplete(state, 'env_setup', 'summary');

    saveState(state);

    console.log('');
    console.log('✅ Environment Setup: Complete');
    console.log('');
    console.log('🔒 Security Notes:');
    console.log('   • .env file is automatically gitignored');
    console.log('   • Never commit .env to version control');
    console.log('   • API keys are stored in plain text locally');
    console.log('   • Backup .env securely if needed');
    console.log('');

    return state;
  } finally {
    rl.close();
  }
}
