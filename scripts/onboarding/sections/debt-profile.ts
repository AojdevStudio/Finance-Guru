/**
 * Debt Profile Section
 * Interactive prompts for collecting debt and liability information
 */

import { createInterface } from 'readline';
import { validateCurrency, validatePercentage } from '../modules/input-validator';
import type { OnboardingState } from '../modules/progress';
import { saveSectionData, markSectionComplete, saveState } from '../modules/progress';

export interface DebtItem {
  type: string;
  rate?: number;
  count?: number | string;
  priority?: string;
}

export interface DebtProfileData {
  mortgage_balance: number;
  mortgage_payment: number;
  other_debt: DebtItem[];
  weighted_interest_rate: number;
  irregular_expenses?: string;
}

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
 * Prompts user for input with validation
 * @param rl - Readline interface
 * @param question - Question to ask
 * @param validator - Validation function
 * @param allowEmpty - Whether empty input is allowed
 * @returns Validated value
 */
async function promptWithValidation<T>(
  rl: ReturnType<typeof createInterface>,
  question: string,
  validator: (input: string) => T,
  allowEmpty: boolean = false
): Promise<T> {
  return new Promise((resolve) => {
    const ask = () => {
      rl.question(question, (answer) => {
        if (allowEmpty && answer.trim() === '') {
          resolve(null as T);
          return;
        }

        try {
          const validated = validator(answer);
          resolve(validated);
        } catch (error) {
          if (error instanceof Error) {
            console.log(`❌ ${error.message}`);
          }
          console.log('Please try again.');
          ask();
        }
      });
    };
    ask();
  });
}

/**
 * Prompts for yes/no question
 * @param rl - Readline interface
 * @param question - Question to ask
 * @returns true if yes, false if no
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
          console.log('Please answer yes (y) or no (n).');
          ask();
        }
      });
    };
    ask();
  });
}

/**
 * Runs the Debt Profile section
 * @param state - Current onboarding state
 * @returns Updated state with debt profile data
 */
export async function runDebtProfileSection(state: OnboardingState): Promise<OnboardingState> {
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('💳 Section 4 of 7: Debt Profile');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('');
  console.log("Let's understand your debt obligations and liabilities.");
  console.log('');

  const rl = createPrompt();

  try {
    const otherDebt: DebtItem[] = [];
    let totalDebtBalance = 0;
    let weightedInterestSum = 0;

    // Prompt for mortgage
    console.log('📊 Mortgage Information');
    console.log('');

    const hasMortgage = await promptYesNo(rl, 'Do you have a mortgage? (y/n) ');

    let mortgageBalance = 0;
    let mortgagePayment = 0;

    if (hasMortgage) {
      mortgageBalance = await promptWithValidation(
        rl,
        'What is your current mortgage balance? $',
        validateCurrency
      );

      mortgagePayment = await promptWithValidation(
        rl,
        'What is your monthly mortgage payment? $',
        validateCurrency
      );

      // For weighted interest calculation
      const mortgageRate = await promptWithValidation(
        rl,
        'What is your mortgage interest rate? (%) ',
        validatePercentage
      );

      totalDebtBalance += mortgageBalance;
      weightedInterestSum += mortgageBalance * mortgageRate;
    }

    // Prompt for student loans
    console.log('');
    console.log('📚 Student Loans');
    console.log('');

    const hasStudentLoans = await promptYesNo(rl, 'Do you have student loans? (y/n) ');

    if (hasStudentLoans) {
      const studentLoanBalance = await promptWithValidation(
        rl,
        'What is the total balance of your student loans? $',
        validateCurrency
      );

      const studentLoanRate = await promptWithValidation(
        rl,
        'What is the average interest rate on your student loans? (%) ',
        validatePercentage
      );

      otherDebt.push({
        type: 'student_loans',
        rate: studentLoanRate,
        priority: 'low'
      });

      totalDebtBalance += studentLoanBalance;
      weightedInterestSum += studentLoanBalance * studentLoanRate;
    }

    // Prompt for car loans
    console.log('');
    console.log('🚗 Car Loans');
    console.log('');

    const hasCarLoans = await promptYesNo(rl, 'Do you have any car loans? (y/n) ');

    if (hasCarLoans) {
      const carLoanCount = await promptWithValidation(
        rl,
        'How many car loans do you have? ',
        (input: string) => {
          const value = parseInt(input, 10);
          if (isNaN(value) || value < 1) {
            throw new Error('Please enter a valid number of car loans');
          }
          return value;
        }
      );

      const carLoanBalance = await promptWithValidation(
        rl,
        'What is the total balance of your car loans? $',
        validateCurrency
      );

      const carLoanRate = await promptWithValidation(
        rl,
        'What is the average interest rate on your car loans? (%) ',
        validatePercentage
      );

      otherDebt.push({
        type: 'car_loans',
        count: carLoanCount,
        rate: carLoanRate
      });

      totalDebtBalance += carLoanBalance;
      weightedInterestSum += carLoanBalance * carLoanRate;
    }

    // Prompt for credit cards
    console.log('');
    console.log('💳 Credit Cards');
    console.log('');

    const hasCreditCardDebt = await promptYesNo(rl, 'Do you carry credit card balances? (y/n) ');

    if (hasCreditCardDebt) {
      const ccCount = await promptWithValidation(
        rl,
        'How many credit cards carry a balance? ',
        (input: string) => {
          const value = parseInt(input, 10);
          if (isNaN(value) || value < 1) {
            throw new Error('Please enter a valid number of credit cards');
          }
          return value;
        }
      );

      const ccBalance = await promptWithValidation(
        rl,
        'What is the total credit card balance? $',
        validateCurrency
      );

      const ccRate = await promptWithValidation(
        rl,
        'What is the average APR on your credit cards? (%) ',
        validatePercentage
      );

      otherDebt.push({
        type: 'credit_cards',
        count: ccCount === 1 ? '1' : 'several',
        rate: ccRate
      });

      totalDebtBalance += ccBalance;
      weightedInterestSum += ccBalance * ccRate;
    }

    // Calculate weighted interest rate
    const weightedInterestRate = totalDebtBalance > 0
      ? weightedInterestSum / totalDebtBalance
      : 0;

    // Prompt for irregular expenses
    console.log('');
    const hasIrregularExpenses = await promptYesNo(
      rl,
      'Do you have any irregular debt-related expenses (e.g., property taxes at year end)? (y/n) '
    );

    let irregularExpenses: string | undefined;
    if (hasIrregularExpenses) {
      irregularExpenses = await promptWithValidation(
        rl,
        'Please describe your irregular expenses: ',
        (input: string) => {
          if (input.trim().length === 0) {
            throw new Error('Please provide a description');
          }
          return input.trim();
        }
      );
    }

    // Create debt profile data
    const debtProfileData: DebtProfileData = {
      mortgage_balance: mortgageBalance,
      mortgage_payment: mortgagePayment,
      other_debt: otherDebt,
      weighted_interest_rate: weightedInterestRate,
      irregular_expenses: irregularExpenses
    };

    // Save section data
    saveSectionData(state, 'debt', debtProfileData);

    // Mark section as complete and set next section
    markSectionComplete(state, 'debt', 'preferences');

    // Save state to disk
    saveState(state);

    console.log('');
    console.log('✅ Debt Profile: Complete');
    console.log('');

    // Display summary
    if (totalDebtBalance > 0) {
      console.log(`Total debt: $${totalDebtBalance.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`);
      console.log(`Weighted average interest rate: ${(weightedInterestRate * 100).toFixed(2)}%`);
      console.log('');
    } else {
      console.log('No debt reported - excellent position!');
      console.log('');
    }

    return state;
  } finally {
    rl.close();
  }
}
