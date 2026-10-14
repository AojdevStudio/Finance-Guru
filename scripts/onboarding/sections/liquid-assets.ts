import { createPrompt, promptWithValidation } from '../modules/prompt';
import { validateCurrency, validatePositiveInteger, validatePercentage, percentToRate } from '../modules/input-validator';
import type { OnboardingState } from '../modules/progress';
import { saveSectionData, markSectionComplete, saveState } from '../modules/progress';

export interface LiquidAssetsData {
  total: number;
  accounts_count: number;
  average_yield: number;
  structure: string[];
}

export async function runLiquidAssetsSection(state: OnboardingState): Promise<OnboardingState> {
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('📊 Section 1 of 7: Liquid Assets');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('');
  console.log("Let's start with your cash accounts (checking, savings, business accounts).");
  console.log('');

  const rl = createPrompt();

  try {
    const total = await promptWithValidation(
      rl,
      'What is the total value of your liquid cash? $',
      validateCurrency
    );

    const accountsCount = await promptWithValidation(
      rl,
      'How many accounts do you have? (checking, savings, business) ',
      validatePositiveInteger
    );

    const averageYield = await promptWithValidation(
      rl,
      'What is the average yield on your cash? (e.g., 4.5 for 4.5%) ',
      validatePercentage
    );

    console.log('');
    console.log('Would you like to describe your account structure? (optional)');
    console.log('Example: "2 business accounts (LLC A & LLC B), 3 checking, 2 high-yield savings"');
    console.log('');

    const structureInput = await promptWithValidation(
      rl,
      'Account structure (press Enter to skip): ',
      (input: string) => input.trim(),
      true
    );

    const structure: string[] = structureInput && structureInput.length > 0
      ? [structureInput]
      : [];

    const liquidAssetsData: LiquidAssetsData = {
      total,
      accounts_count: accountsCount,
      average_yield: percentToRate(averageYield),
      structure
    };

    saveSectionData(state, 'liquid_assets', liquidAssetsData);

    markSectionComplete(state, 'liquid_assets', 'investments');

    saveState(state);

    console.log('');
    console.log('✅ Liquid Assets: Complete');
    console.log('');

    return state;
  } finally {
    rl.close();
  }
}
