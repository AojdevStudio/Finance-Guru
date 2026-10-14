import { createPrompt, promptWithValidation } from '../modules/prompt';
import { validateCurrency } from '../modules/input-validator';
import type { OnboardingState } from '../modules/progress';
import { saveSectionData, markSectionComplete, saveState } from '../modules/progress';

export interface CashFlowData {
  monthly_income: number;
  fixed_expenses: number;
  variable_expenses: number;
  current_savings: number;
  investment_capacity: number;
}

export async function runCashFlowSection(state: OnboardingState): Promise<OnboardingState> {
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('💵 Section 3 of 7: Cash Flow');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('');
  console.log("Let's understand your monthly cash flow (after-tax income and expenses).");
  console.log('');

  const rl = createPrompt();

  try {
    const monthlyIncome = await promptWithValidation(
      rl,
      'What is your monthly after-tax income? $',
      validateCurrency
    );

    console.log('');
    console.log('Fixed expenses are recurring bills (rent, insurance, subscriptions, etc.)');
    const fixedExpenses = await promptWithValidation(
      rl,
      'What are your total fixed monthly expenses? $',
      validateCurrency
    );

    console.log('');
    console.log('Variable expenses include groceries, dining, entertainment, shopping, etc.');
    const variableExpenses = await promptWithValidation(
      rl,
      'What are your average variable monthly expenses? $',
      validateCurrency
    );

    console.log('');
    const currentSavings = await promptWithValidation(
      rl,
      'How much do you currently save each month? $',
      validateCurrency
    );

    const totalExpenses = fixedExpenses + variableExpenses;
    const calculatedCapacity = monthlyIncome - totalExpenses;

    console.log('');
    console.log(`Calculated monthly surplus: $${calculatedCapacity.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`);
    console.log('');

    const investmentCapacity = await promptWithValidation(
      rl,
      'What is your monthly investment capacity? $',
      (input: string) => {
        const value = validateCurrency(input);
        if (value > monthlyIncome) {
          throw new Error(
            `Investment capacity ($${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}) cannot exceed monthly income ($${monthlyIncome.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })})`
          );
        }
        return value;
      }
    );

    const cashFlowData: CashFlowData = {
      monthly_income: monthlyIncome,
      fixed_expenses: fixedExpenses,
      variable_expenses: variableExpenses,
      current_savings: currentSavings,
      investment_capacity: investmentCapacity
    };

    saveSectionData(state, 'cash_flow', cashFlowData);

    markSectionComplete(state, 'cash_flow', 'debt');

    saveState(state);

    console.log('');
    console.log('✅ Cash Flow: Complete');
    console.log('');

    return state;
  } finally {
    rl.close();
  }
}
