import { createPrompt, promptWithValidation, type Prompt } from '../modules/prompt';
import type { OnboardingState } from '../modules/progress';
import { getSectionData, markSectionComplete, saveState, clearState, OPTIONAL_SECTIONS } from '../modules/progress';
import { generateAllConfigs, type UserData } from '../modules/yaml-generator';
import { validateNonEmpty } from '../modules/input-validator';
import { saveSectionData } from '../modules/progress';
import type { LiquidAssetsData } from './liquid-assets';
import type { InvestmentPortfolioData } from './investment-portfolio';
import type { CashFlowData } from './cash-flow';
import type { DebtProfileData } from './debt-profile';
import type { PreferencesData } from './preferences';
import type { EnvSetupData } from './env-setup';
import type { BrokerSelectionData } from './broker-selection';

export function profileFromState(state: OnboardingState): UserData {
  const env: Partial<EnvSetupData> = getSectionData(state, 'env_setup') ?? {};
  if (!env.user_name?.trim()) throw new Error('Your name is required before saving your profile');
  const assets: Partial<LiquidAssetsData> = getSectionData(state, 'liquid_assets') ?? {};
  const investments: Partial<InvestmentPortfolioData> = getSectionData(state, 'investments') ?? {};
  const cashFlow: Partial<CashFlowData> = getSectionData(state, 'cash_flow') ?? {};
  const debt: Partial<DebtProfileData> = getSectionData(state, 'debt') ?? {};
  const preferences: Partial<PreferencesData> = getSectionData(state, 'preferences') ?? {};
  const broker: Partial<BrokerSelectionData> = getSectionData(state, 'broker_selection') ?? {};
  return {
    user_name: env.user_name,
    language: env.communication_language,
    liquid_assets_total: assets.total,
    liquid_assets_count: assets.accounts_count,
    liquid_assets_yield: assets.average_yield,
    liquid_assets_structure: assets.structure?.join(', '),
    portfolio_value: investments.total_value,
    retirement_value: investments.retirement_accounts,
    has_retirement: (investments.retirement_accounts ?? 0) > 0,
    allocation_strategy: investments.allocation,
    risk_tolerance: preferences.risk_tolerance ?? investments.risk_profile,
    ...cashFlow,
    mortgage_balance: debt.mortgage_balance,
    mortgage_payment: debt.mortgage_payment,
    has_mortgage: (debt.mortgage_balance ?? 0) > 0,
    other_debt: debt.other_debt?.map(item => item.type).join(', '),
    weighted_rate: debt.weighted_interest_rate,
    investment_philosophy: preferences.investment_philosophy,
    focus_areas: preferences.focus_areas,
    brokerage: env.primary_brokerage ?? broker.broker_name,
    account_number: env.brokerage_account_number,
    has_alphavantage: env.has_alphavantage,
    alphavantage_key: env.alphavantage_key,
    has_brightdata: env.has_brightdata,
    brightdata_key: env.brightdata_key,
  };
}


function formatCurrency(value?: number): string {
  if (value === undefined || value === null) return 'Not provided';
  return `$${value.toLocaleString('en-US')}`;
}

function formatPercentage(value?: number): string {
  if (value === undefined || value === null) return 'Not provided';
  return `${(value * 100).toFixed(2)}%`;
}

async function promptYesNo(
  rl: Prompt,
  question: string
): Promise<boolean> {
  return new Promise((resolve) => {
    const ask = () => {
      rl.question(question, (answer) => {
        const normalized = answer.trim().toLowerCase();

        if (normalized === 'y' || normalized === 'yes') {
          resolve(true);
        } else if (normalized === 'n' || normalized === 'no') {
          resolve(false);
        } else {
          console.log('❌ Please answer "y" (yes) or "n" (no)');
          ask();
        }
      });
    };
    ask();
  });
}

function displayLiquidAssetsSummary(data: any): void {
  console.log('  💰 Liquid Assets');
  console.log(`     Total: ${formatCurrency(data.total)}`);
  console.log(`     Accounts: ${data.accounts_count || 'Not provided'}`);
  console.log(`     Average Yield: ${formatPercentage(data.average_yield)}`);

  if (data.structure && data.structure.length > 0) {
    console.log(`     Structure:`);
    data.structure.forEach((item: string) => {
      console.log(`       - ${item}`);
    });
  }
}

function displayInvestmentsSummary(data: any): void {
  console.log('  📈 Investment Portfolio');
  console.log(`     Total Value: ${formatCurrency(data.total_value)}`);
  console.log(`     Retirement Accounts: ${formatCurrency(data.retirement_accounts)}`);
  console.log(`     Allocation: ${data.allocation || 'Not provided'}`);
  console.log(`     Risk Profile: ${data.risk_profile || 'Not provided'}`);
}

function displayCashFlowSummary(data: any): void {
  console.log('  💵 Cash Flow');
  console.log(`     Monthly Income: ${formatCurrency(data.monthly_income)}`);
  console.log(`     Fixed Expenses: ${formatCurrency(data.fixed_expenses)}`);
  console.log(`     Variable Expenses: ${formatCurrency(data.variable_expenses)}`);
  console.log(`     Current Savings: ${formatCurrency(data.current_savings)}`);
  console.log(`     Investment Capacity: ${formatCurrency(data.investment_capacity)}`);
}

function displayDebtSummary(data: any): void {
  console.log('  🏦 Debt Profile');
  console.log(`     Mortgage Balance: ${formatCurrency(data.mortgage_balance)}`);
  console.log(`     Mortgage Payment: ${formatCurrency(data.mortgage_payment)}`);

  if (data.other_debt && data.other_debt.length > 0) {
    console.log(`     Other Debt:`);
    data.other_debt.forEach((debt: any) => {
      console.log(`       - ${debt.type}: Rate ${formatPercentage(debt.rate)}`);
    });
  } else {
    console.log(`     Other Debt: None`);
  }
}

function displayPreferencesSummary(data: any): void {
  console.log('  🎯 Investment Preferences');
  console.log(`     Risk Tolerance: ${data.risk_tolerance || 'Not provided'}`);
  console.log(`     Investment Philosophy: ${data.investment_philosophy || 'Not provided'}`);
  console.log(`     Time Horizon: ${data.time_horizon || 'Not provided'}`);

  if (data.focus_areas && data.focus_areas.length > 0) {
    console.log(`     Focus Areas:`);
    data.focus_areas.forEach((area: string) => {
      console.log(`       - ${area.replace(/_/g, ' ')}`);
    });
  } else {
    console.log(`     Focus Areas: None specified`);
  }
}

export async function runSummarySection(state: OnboardingState): Promise<OnboardingState> {
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('📋 Section 6 of 7: Summary & Confirmation');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('');
  console.log('Please review your information:');
  console.log('');
  console.log('╔══════════════════════════════════════════════════════════╗');
  console.log('║                    Your Finance Guru Profile             ║');
  console.log('╚══════════════════════════════════════════════════════════╝');
  console.log('');

  const rl = createPrompt();

  try {
    const liquidAssets = getSectionData(state, 'liquid_assets');
    if (liquidAssets) {
      displayLiquidAssetsSummary(liquidAssets);
      console.log('');
    }

    const investments = getSectionData(state, 'investments');
    if (investments) {
      displayInvestmentsSummary(investments);
      console.log('');
    }

    const cashFlow = getSectionData(state, 'cash_flow');
    if (cashFlow) {
      displayCashFlowSummary(cashFlow);
      console.log('');
    }

    const debt = getSectionData(state, 'debt');
    if (debt) {
      displayDebtSummary(debt);
      console.log('');
    }

    const preferences = getSectionData(state, 'preferences');
    if (preferences) {
      displayPreferencesSummary(preferences);
      console.log('');
    }

    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log('');

    const confirmed = await promptYesNo(
      rl,
      'Save this profile and generate configuration files? (y/n): '
    );

    if (confirmed) {
      console.log('');
      console.log('✅ Confirmed! Generating configuration files...');
      console.log('');

      try {
        const identity = getSectionData(state, 'env_setup');
        if (!identity?.user_name) {
          const userName = await promptWithValidation(rl, 'Your name: ', validateNonEmpty);
          saveSectionData(state, 'env_setup', { ...identity, user_name: userName });
          saveState(state);
        }
        generateAllConfigs(profileFromState(state));
        console.log('✅ Configuration files generated successfully');
        console.log('');
        console.log('Files created:');
        console.log('  ✓ user-profile.yaml');
        console.log('  ✓ config.yaml');
        console.log('  ✓ system-context.md');
        console.log('');

        markSectionComplete(state, 'summary', OPTIONAL_SECTIONS[0]);

        saveState(state);

        clearState();

        console.log('🎉 Onboarding Complete!');
        console.log('');
        console.log('Next steps:');
        console.log('  1. Continue with MCP server configuration (optional)');
        console.log('  2. Configure environment variables (optional)');
        console.log('  3. Launch Claude Code and activate Finance Guru');
        console.log('');

      } catch (error) {
        console.error('');
        console.error('❌ Error generating configuration files:');
        console.error(error instanceof Error ? error.message : String(error));
        console.error('');
        console.error('Your progress has been saved. You can:');
        console.error('  1. Fix the issue and run setup.sh again');
        console.error('  2. Contact support with the error message above');
        console.error('');
        throw error;
      }

    } else {
      console.log('');
      console.log('❌ Profile not saved');
      console.log('');

      const restartChoice = await promptYesNo(
        rl,
        'Do you want to restart from the beginning? (y/n): '
      );

      if (restartChoice) {
        console.log('');
        console.log('🔄 Restarting onboarding...');
        console.log('Please run the setup script again.');
        console.log('');

        clearState();
      } else {
        console.log('');
        console.log('💾 Your progress has been saved');
        console.log('You can resume later by running: bun scripts/onboarding/index.ts --resume');
        console.log('');

        saveState(state);
      }
    }

    return state;

  } finally {
    rl.close();
  }
}
