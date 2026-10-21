import { createPrompt, type Prompt } from '../modules/prompt';
import type { OnboardingState } from '../modules/progress';
import { saveSectionData, markSectionComplete, saveState } from '../modules/progress';
import {
  type BrokerType,
  getAllBrokers,
  getBrokerInfo,
  getBrokerDisplayName
} from '../modules/broker-types';
import { isBrokerSupported } from '../modules/broker-registry';

export interface BrokerSelectionData {
  broker: BrokerType;
  broker_name: string;
  csv_export_guide: string;
  is_supported: boolean;
}

function displayBrokerMenu() {
  console.log('');
  console.log('Available Brokers:');
  console.log('');

  const brokers = getAllBrokers();

  brokers.forEach((broker, index) => {
    const supported = isBrokerSupported(broker.id);
    const supportedTag = supported ? '✅' : '⚠️ Coming Soon';
    console.log(`  ${index + 1}. ${broker.name} ${supportedTag}`);
    console.log(`     ${broker.description}`);
    console.log('');
  });
}

async function promptBrokerSelection(rl: Prompt): Promise<BrokerType> {
  const brokers = getAllBrokers();

  return new Promise((resolve) => {
    const ask = () => {
      rl.question('Enter the number of your broker: ', (answer) => {
        const selection = parseInt(answer.trim(), 10);

        if (isNaN(selection) || selection < 1 || selection > brokers.length) {
          console.log(`❌ Invalid selection. Please enter a number between 1 and ${brokers.length}.`);
          ask();
          return;
        }

        const selectedBroker = brokers[selection - 1];
        resolve(selectedBroker.id);
      });
    };
    ask();
  });
}

function displayExportInstructions(brokerType: BrokerType) {
  const broker = getBrokerInfo(brokerType);
  const supported = isBrokerSupported(brokerType);

  console.log('');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log(`📤 CSV Export Instructions for ${broker.name}`);
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('');

  if (!supported) {
    console.log('⚠️  WARNING: This broker is not yet fully supported.');
    console.log('   CSV imports for this broker require manual column mapping.');
    console.log('   Automated parsing will be added in a future update.');
    console.log('');
  }

  console.log('To export your portfolio data:');
  console.log('');
  console.log(`  ${broker.csvExportGuide}`);
  console.log('');
  console.log('You will need TWO CSV files:');
  console.log('  1. Positions CSV (your stock/ETF holdings)');
  console.log('  2. Balances CSV (cash, margin debt, account totals)');
  console.log('');
  console.log('Save these files to: notebooks/updates/');
  console.log('');

  if (supported) {
    console.log('✅ Finance Guru will automatically detect and parse these files.');
  } else {
    console.log('⚠️  You will need to manually map CSV columns during import.');
  }

  console.log('');
}

async function confirmSelection(
  rl: Prompt,
  brokerType: BrokerType
): Promise<boolean> {
  const broker = getBrokerInfo(brokerType);

  return new Promise((resolve) => {
    rl.question(
      `\nYou selected: ${broker.name}. Is this correct? (y/n) `,
      (answer) => {
        const confirmed = answer.trim().toLowerCase() === 'y';
        resolve(confirmed);
      }
    );
  });
}

export async function runBrokerSelectionSection(state: OnboardingState): Promise<OnboardingState> {
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('🏦 Broker Selection');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('');
  console.log('Finance Guru needs to know which broker you use to import your');
  console.log('portfolio data. Each broker exports CSV files in a different format.');
  console.log('');

  const rl = createPrompt();

  try {
    let selectedBroker: BrokerType | null = null;
    let confirmed = false;

    while (!confirmed) {
      displayBrokerMenu();
      selectedBroker = await promptBrokerSelection(rl);
      displayExportInstructions(selectedBroker);
      confirmed = await confirmSelection(rl, selectedBroker);

      if (!confirmed) {
        console.log('');
        console.log('Let\'s try again...');
      }
    }

    if (!selectedBroker) {
      throw new Error('No broker selected');
    }

    const broker = getBrokerInfo(selectedBroker);
    const supported = isBrokerSupported(selectedBroker);

    const brokerData: BrokerSelectionData = {
      broker: selectedBroker,
      broker_name: broker.name,
      csv_export_guide: broker.csvExportGuide,
      is_supported: supported
    };

    saveSectionData(state, 'broker_selection', brokerData);

    markSectionComplete(state, 'broker_selection', 'investments');

    saveState(state);

    console.log('');
    console.log(`✅ Broker Selection: ${broker.name}`);
    console.log('');

    if (!supported) {
      console.log('ℹ️  Note: Manual CSV mapping will be required during portfolio import.');
      console.log('');
    }

    return state;
  } finally {
    rl.close();
  }
}
