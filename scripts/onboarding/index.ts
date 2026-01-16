#!/usr/bin/env bun

/**
 * Finance Guru™ Onboarding CLI
 * Main entry point for interactive onboarding wizard
 */

import {
  hasExistingState,
  loadState,
  createNewState,
  saveState,
  clearState,
  getTimeSinceLastUpdate,
  isComplete,
  type OnboardingState
} from './modules/progress';

// Parse command line arguments
const args = process.argv.slice(2);
const isResumeMode = args.includes('--resume');
const isTestMode = args.includes('--test');

/**
 * Display welcome screen
 */
function displayWelcome(): void {
  console.log('╔══════════════════════════════════════════════════════════╗');
  console.log('║                                                          ║');
  console.log('║          🏦 Finance Guru™ Setup Wizard                   ║');
  console.log('║                                                          ║');
  console.log('║    Transform Claude into your private family office     ║');
  console.log('║                                                          ║');
  console.log('╚══════════════════════════════════════════════════════════╝');
  console.log('');
  console.log('This wizard will guide you through setting up Finance Guru.');
  console.log('We\'ll collect information about:');
  console.log('');
  console.log('  1. Your liquid assets (cash accounts)');
  console.log('  2. Investment portfolio');
  console.log('  3. Monthly cash flow');
  console.log('  4. Debt profile');
  console.log('  5. Investment preferences');
  console.log('  6. MCP server configuration');
  console.log('  7. Environment variables');
  console.log('');
  console.log('⏱️  Estimated time: 10-15 minutes');
  console.log('💾 Your progress is auto-saved (resume anytime with --resume)');
  console.log('🔒 All data stays local (never transmitted)');
  console.log('');
}

/**
 * Display resume screen
 */
function displayResume(state: OnboardingState): void {
  console.log('╔══════════════════════════════════════════════════════════╗');
  console.log('║                                                          ║');
  console.log('║          🏦 Finance Guru™ Setup Wizard                   ║');
  console.log('║                 (Resume Mode)                            ║');
  console.log('║                                                          ║');
  console.log('╚══════════════════════════════════════════════════════════╝');
  console.log('');
  console.log(`Found existing onboarding session (started ${getTimeSinceLastUpdate(state)})`);
  console.log('');
  console.log('Completed sections:');
  if (state.completed_sections.length === 0) {
    console.log('  (none yet)');
  } else {
    state.completed_sections.forEach(section => {
      console.log(`  ✅ ${section.replace(/_/g, ' ')}`);
    });
  }
  console.log('');

  if (state.current_section) {
    console.log(`Next section: ${state.current_section.replace(/_/g, ' ')}`);
  } else {
    console.log('All sections completed!');
  }
  console.log('');
}

/**
 * Display completion message
 */
function displayComplete(): void {
  console.log('');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('🎉 Setup Complete!');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('');
  console.log('Your Finance Guru is now configured.');
  console.log('');
  console.log('Next steps:');
  console.log('  1. Start Claude Code in this directory');
  console.log('  2. Finance Guru will auto-load your configuration');
  console.log('  3. Run /finance-orchestrator to activate your AI team');
  console.log('');
  console.log('To update your configuration later:');
  console.log('  → Run: bun run scripts/onboarding/index.ts --resume');
  console.log('');
  console.log('Documentation:');
  console.log('  → Setup guide: docs/SETUP.md');
  console.log('  → User guide: docs/USER-GUIDE.md');
  console.log('  → Troubleshooting: docs/TROUBLESHOOTING.md');
  console.log('');
  console.log('Ready to get started? Open Claude Code and say:');
  console.log('  "Hi, I\'m [Your Name]. Let\'s review my portfolio."');
  console.log('');
}

/**
 * Main onboarding flow
 */
async function main() {
  try {
    let state: OnboardingState;

    // Check for existing state
    if (hasExistingState() && isResumeMode) {
      const existingState = loadState();
      if (existingState) {
        displayResume(existingState);

        // Check if already complete
        if (isComplete(existingState)) {
          console.log('✅ Onboarding already complete!');
          console.log('');
          console.log('To reconfigure, delete .onboarding-state.json and run again.');
          console.log('');
          return;
        }

        state = existingState;
      } else {
        console.log('⚠️  Failed to load existing state. Starting fresh.');
        state = createNewState();
      }
    } else {
      displayWelcome();
      state = createNewState();
    }

    // TODO: Implement section flows
    // For now, just save the initial state
    console.log('🚧 Onboarding CLI structure created.');
    console.log('📋 Section implementations coming in subsequent tasks.');
    console.log('');
    console.log('Structure created:');
    console.log('  ✅ scripts/onboarding/index.ts');
    console.log('  ✅ scripts/onboarding/modules/input-validator.ts');
    console.log('  ✅ scripts/onboarding/modules/progress.ts');
    console.log('  ✅ scripts/onboarding/modules/yaml-generator.ts');
    console.log('  ✅ scripts/onboarding/modules/templates/');
    console.log('  📂 scripts/onboarding/sections/ (ready for implementation)');
    console.log('  📂 scripts/onboarding/tests/ (ready for implementation)');
    console.log('');

    // Save state
    saveState(state);

    console.log('💾 Progress saved to .onboarding-state.json');
    console.log('');

  } catch (error) {
    console.error('❌ Error during onboarding:', error);
    process.exit(1);
  }
}

// Run main function
main();
