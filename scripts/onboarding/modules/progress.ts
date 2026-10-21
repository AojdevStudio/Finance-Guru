import { existsSync, readFileSync, writeFileSync, unlinkSync } from 'fs';
import { join } from 'path';

const REQUIRED_SECTIONS = [
  'liquid_assets',
  'investments',
  'cash_flow',
  'debt',
  'preferences',
  'summary'
] as const;

export const OPTIONAL_SECTIONS = ['mcp_config', 'env_setup'] as const;

export const SECTION_ORDER = [...REQUIRED_SECTIONS, ...OPTIONAL_SECTIONS] as const;

export type SectionName = (typeof SECTION_ORDER)[number] | 'broker_selection';

export interface OnboardingState {
  version: string;
  started_at: string;
  last_updated: string;
  completed_sections: SectionName[];
  current_section: SectionName | null;
  data: Record<string, any>;
}

const STATE_FILE = '.onboarding-state.json';

function getStatePath(): string {
  return join(process.cwd(), STATE_FILE);
}

export function hasExistingState(): boolean {
  return existsSync(getStatePath());
}

export function loadState(): OnboardingState | null {
  const statePath = getStatePath();

  if (!existsSync(statePath)) {
    return null;
  }

  try {
    const content = readFileSync(statePath, 'utf-8');
    return JSON.parse(content) as OnboardingState;
  } catch (error) {
    console.error('Failed to load onboarding state:', error);
    return null;
  }
}

export function saveState(state: OnboardingState): void {
  const statePath = getStatePath();

  try {
    state.last_updated = new Date().toISOString();
    const content = JSON.stringify(state, null, 2);
    writeFileSync(statePath, content, 'utf-8');
  } catch (error) {
    console.error('Failed to save onboarding state:', error);
    throw error;
  }
}

export function createNewState(): OnboardingState {
  const now = new Date().toISOString();

  return {
    version: '1.0',
    started_at: now,
    last_updated: now,
    completed_sections: [],
    current_section: null,
    data: {}
  };
}

export function markSectionComplete(
  state: OnboardingState,
  completedSection: SectionName,
  nextSection: SectionName | null
): OnboardingState {
  if (!state.completed_sections.includes(completedSection)) {
    state.completed_sections.push(completedSection);
  }

  state.current_section = nextSection;

  return state;
}

export function saveSectionData(
  state: OnboardingState,
  section: SectionName,
  data: Record<string, any>
): OnboardingState {
  state.data[section] = data;
  return state;
}

export function getSectionData(
  state: OnboardingState,
  section: SectionName
): Record<string, any> | null {
  return state.data[section] || null;
}

export function clearState(): void {
  const statePath = getStatePath();

  if (existsSync(statePath)) {
    try {
      unlinkSync(statePath);
    } catch (error) {
      console.error('Failed to delete onboarding state:', error);
      throw error;
    }
  }
}

export function getNextSection(state: OnboardingState): SectionName | null {
  const nextSection = SECTION_ORDER.find(
    section => !state.completed_sections.includes(section)
  );

  return nextSection || null;
}

export function isComplete(state: OnboardingState): boolean {
  return SECTION_ORDER.every(section => state.completed_sections.includes(section));
}

export function getTimeSinceLastUpdate(state: OnboardingState): string {
  const now = new Date();
  const lastUpdate = new Date(state.last_updated);
  const diffMs = now.getTime() - lastUpdate.getTime();

  const diffMinutes = Math.floor(diffMs / (1000 * 60));
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays > 0) {
    return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
  } else if (diffHours > 0) {
    return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
  } else if (diffMinutes > 0) {
    return `${diffMinutes} minute${diffMinutes > 1 ? 's' : ''} ago`;
  } else {
    return 'just now';
  }
}
