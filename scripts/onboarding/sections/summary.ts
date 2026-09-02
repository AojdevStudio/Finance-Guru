/**
 * Summary & Confirmation Section
 * Displays collected data and asks for final confirmation before generating config files
 */

import { createInterface } from 'readline';
import type { OnboardingState } from '../modules/progress';
import { getSectionData, markSectionComplete, saveState, clearState } from '../modules/progress';
import { generateAllConfigs } from '../modules/yaml-generator';

/**
 * Creates a readline interface for prompting user
 */
function createPrompt() {
  return createInterface({
    input: process.stdin,
    output: process.stdout
  });
}

/**
 * Formats currency for display
 * @param value - Numeric value
 * @returns Formatted currency string
 */
function formatCurrency(value?: number): string {
  if (value === undefined || value === null) return 'Not provided';
  return `$${value.toLocaleString('en-US')}`;
}

/**
 * Formats percentage for display
 * @param value - Decimal value (e.g., 0.04)
 * @returns Formatted percentage string
 */
function formatPercentage(value?: number): string {
  if (value === undefined || value === null) return 'Not provided';
  return `${(value * 100).toFixed(2)}%`;
}

/**
 * Prompts user with a yes/no question
 * @param rl - Readline interface
 * @param question - Question to ask
 * @returns Promise resolving to true for yes, false for no
 */
async function promptYesNo(
  rl: ReturnType<typeof createInterface>,
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

/**
 * Displays summary of liquid assets
 * @param data - Liquid assets data
 */
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

/**
 * Displays summary of investment portfolio
 * @param data - Investment portfolio data
 */
function displayInvestmentsSummary(data: any): void {
  console.log('  📈 Investment Portfolio');
  console.log(`     Total Value: ${formatCurrency(data.total_value)}`);
  console.log(`     Retirement Accounts: ${formatCurrency(data.retirement_accounts)}`);
  console.log(`     Allocation: ${data.allocation || 'Not provided'}`);
  console.log(`     Risk Profile: ${data.risk_profile || 'Not provided'}`);
}

/**
 * Displays summary of cash flow
 * @param data - Cash flow data
 */
function displayCashFlowSummary(data: any): void {
  console.log('  💵 Cash Flow');
  console.log(`     Monthly Income: ${formatCurrency(data.monthly_income)}`);
  console.log(`     Fixed Expenses: ${formatCurrency(data.fixed_expenses)}`);
  console.log(`     Variable Expenses: ${formatCurrency(data.variable_expenses)}`);
  console.log(`     Current Savings: ${formatCurrency(data.current_savings)}`);
  console.log(`     Investment Capacity: ${formatCurrency(data.investment_capacity)}`);
}

/**
 * Displays summary of debt profile
 * @param data - Debt profile data
 */
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

/**
 * Displays summary of preferences
 * @param data - Preferences data
 */
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

/**
 * Runs the Summary & Confirmation section
 * @param state - Current onboarding state
 * @returns Updated state
 */
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
    // Display each section's summary
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

    // Ask for confirmation
    const confirmed = await promptYesNo(
      rl,
      'Save this profile and generate configuration files? (y/n): '
    );

    if (confirmed) {
      console.log('');
      console.log('✅ Confirmed! Generating configuration files...');
      console.log('');

      // Generate all configuration files
      try {
        await generateAllConfigs(state);
        console.log('✅ Configuration files generated successfully');
        console.log('');
        console.log('Files created:');
        console.log('  ✓ user-profile.yaml');
        console.log('  ✓ fin-guru/config.yaml');
        console.log('  ✓ fin-guru/data/system-context.md');
        console.log('');

        // Mark section as complete (next sections are optional: mcp_config, env_setup)
        markSectionComplete(state, 'summary', 'mcp_config');

        // Save final state
        saveState(state);

        // Clear progress file (onboarding complete)
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

        // Clear state to start fresh
        clearState();
      } else {
        console.log('');
        console.log('💾 Your progress has been saved');
        console.log('You can resume later by running: bun scripts/onboarding/index.ts --resume');
        console.log('');

        // Keep state for resume
        saveState(state);
      }
    }

    return state;

  } finally {
    rl.close();
  }
}
