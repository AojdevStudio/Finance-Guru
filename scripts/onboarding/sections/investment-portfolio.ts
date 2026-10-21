import { createPrompt, promptWithValidation } from '../modules/prompt';
import { validateCurrency, validateRiskTolerance, validateNonEmpty } from '../modules/input-validator';
import type { OnboardingState } from '../modules/progress';
import { saveSectionData, markSectionComplete, saveState } from '../modules/progress';

export interface InvestmentPortfolioData {
  total_value: number;
  retirement_accounts: number;
  bitcoin_holdings: string;
  total_net_worth: number;
  allocation: string;
  accounts: string[];
  risk_profile: string;
}

export async function runInvestmentPortfolioSection(state: OnboardingState): Promise<OnboardingState> {
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('📈 Section 2 of 7: Investment Portfolio');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('');
  console.log("Now let's gather information about your investment portfolio.");
  console.log('');

  const rl = createPrompt();

  try {
    const totalValue = await promptWithValidation(
      rl,
      'What is the total value of your brokerage/investment accounts? $',
      validateCurrency
    );

    const retirementAccounts = await promptWithValidation(
      rl,
      'What is the total value of your retirement accounts (401k, IRA, etc.)? $',
      validateCurrency
    );

    console.log('');
    console.log('Do you have Bitcoin or cryptocurrency holdings?');
    console.log('Enter the value, or type "excluded" if you want to exclude from planning.');
    console.log('');

    const bitcoinInput = await promptWithValidation(
      rl,
      'Bitcoin/Crypto value ($ or "excluded"): ',
      (input: string) => {
        const trimmed = input.trim().toLowerCase();
        if (trimmed === 'excluded' || trimmed === 'exclude') {
          return 'EXCLUDED_FROM_PLANNING';
        }
        return validateCurrency(input).toString();
      }
    );

    const bitcoinValue = bitcoinInput === 'EXCLUDED_FROM_PLANNING' ? 0 : parseFloat(bitcoinInput);
    const totalNetWorth = totalValue + retirementAccounts + bitcoinValue;

    console.log('');
    console.log('What is your overall portfolio allocation strategy?');
    console.log('Examples: "aggressive_growth", "balanced", "income_focused", "conservative"');
    console.log('');

    const allocation = await promptWithValidation(
      rl,
      'Allocation strategy: ',
      validateNonEmpty
    );

    console.log('');
    console.log('List your investment accounts (comma-separated)');
    console.log('Example: "Fidelity Brokerage, Vanguard 401k, Roth IRA"');
    console.log('');

    const accountsInput = await promptWithValidation(
      rl,
      'Investment accounts: ',
      validateNonEmpty
    );

    const accounts = accountsInput
      .split(',')
      .map((account: string) => account.trim())
      .filter((account: string) => account.length > 0);

    console.log('');
    const riskProfile = await promptWithValidation(
      rl,
      'What is your risk tolerance? (conservative/moderate/aggressive) ',
      validateRiskTolerance
    );

    const investmentPortfolioData: InvestmentPortfolioData = {
      total_value: totalValue,
      retirement_accounts: retirementAccounts,
      bitcoin_holdings: bitcoinInput,
      total_net_worth: totalNetWorth,
      allocation,
      accounts,
      risk_profile: riskProfile
    };

    saveSectionData(state, 'investments', investmentPortfolioData);

    markSectionComplete(state, 'investments', 'cash_flow');

    saveState(state);

    console.log('');
    console.log('✅ Investment Portfolio: Complete');
    console.log('');

    return state;
  } finally {
    rl.close();
  }
}
