import { createPrompt, promptWithValidation } from '../modules/prompt';
import { validateEnum } from '../modules/input-validator';
import type { OnboardingState } from '../modules/progress';
import { saveSectionData, markSectionComplete, saveState } from '../modules/progress';

export interface PreferencesData {
  risk_tolerance: string;
  investment_philosophy: string;
  time_horizon: string;
  focus_areas?: string[];
}

export async function runPreferencesSection(state: OnboardingState): Promise<OnboardingState> {
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('🎯 Section 5 of 7: Investment Preferences');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('');
  console.log("Let's understand your investment approach and goals.");
  console.log('');

  const rl = createPrompt();

  try {
    console.log('1. Risk Tolerance');
    console.log('   Choose one:');
    console.log('   - conservative: Prioritize capital preservation, minimal volatility');
    console.log('   - moderate: Balanced growth and stability');
    console.log('   - aggressive: Maximize growth, accept higher volatility');
    console.log('');

    const riskTolerance = await promptWithValidation(
      rl,
      'Risk tolerance (conservative/moderate/aggressive): ',
      (input: string) => validateEnum(input, ['conservative', 'moderate', 'aggressive'], 'risk tolerance')
    );

    console.log('');
    console.log('2. Investment Philosophy');
    console.log('   Choose one:');
    console.log('   - growth: Focus on capital appreciation');
    console.log('   - income: Focus on dividend/interest income');
    console.log('   - balanced: Mix of growth and income');
    console.log('   - aggressive_growth: Maximum growth, high risk');
    console.log('   - aggressive_growth_plus_income: Growth with income layer');
    console.log('');

    const investmentPhilosophy = await promptWithValidation(
      rl,
      'Investment philosophy: ',
      (input: string) => validateEnum(
        input,
        ['growth', 'income', 'balanced', 'aggressive_growth', 'aggressive_growth_plus_income'],
        'investment philosophy'
      )
    );

    console.log('');
    console.log('3. Time Horizon');
    console.log('   Choose one:');
    console.log('   - short_term: Less than 3 years');
    console.log('   - medium_term: 3-10 years');
    console.log('   - long_term: 10+ years');
    console.log('');

    const timeHorizon = await promptWithValidation(
      rl,
      'Time horizon (short_term/medium_term/long_term): ',
      (input: string) => validateEnum(input, ['short_term', 'medium_term', 'long_term'], 'time horizon')
    );

    console.log('');
    console.log('4. Focus Areas (Optional)');
    console.log('   Select areas of interest (comma-separated, or press Enter to skip):');
    console.log('   Available options:');
    console.log('   - dividend_portfolio_construction');
    console.log('   - living_off_brokerage_income');
    console.log('   - two_layer_portfolio_strategy');
    console.log('   - margin_strategies');
    console.log('   - tax_efficiency');
    console.log('   - options_trading');
    console.log('   - real_estate_investing');
    console.log('');

    const focusAreasInput = await promptWithValidation(
      rl,
      'Focus areas (comma-separated, or press Enter to skip): ',
      (input: string) => input.trim(),
      true
    );

    const validFocusAreas = [
      'dividend_portfolio_construction',
      'living_off_brokerage_income',
      'two_layer_portfolio_strategy',
      'margin_strategies',
      'tax_efficiency',
      'options_trading',
      'real_estate_investing'
    ];

    const focusAreas: string[] = focusAreasInput && focusAreasInput.length > 0
      ? focusAreasInput.split(',')
          .map(area => area.trim())
          .filter(area => {
            if (validFocusAreas.includes(area)) {
              return true;
            } else {
              console.log(`⚠️  Skipping invalid focus area: "${area}"`);
              return false;
            }
          })
      : [];

    const preferencesData: PreferencesData = {
      risk_tolerance: riskTolerance,
      investment_philosophy: investmentPhilosophy,
      time_horizon: timeHorizon
    };

    if (focusAreas.length > 0) {
      preferencesData.focus_areas = focusAreas;
    }

    saveSectionData(state, 'preferences', preferencesData);

    markSectionComplete(state, 'preferences', 'summary');

    saveState(state);

    console.log('');
    console.log('✅ Preferences: Complete');
    console.log('');

    return state;
  } finally {
    rl.close();
  }
}
