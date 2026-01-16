/**
 * Progress Save/Resume System
 * Manages onboarding state persistence
 */

import { existsSync, readFileSync, writeFileSync, unlinkSync } from 'fs';
import { join } from 'path';

export type SectionName =
  | 'liquid_assets'
  | 'investments'
  | 'cash_flow'
  | 'debt'
  | 'preferences'
  | 'mcp_config'
  | 'env_setup';

export interface OnboardingState {
  version: string;
  started_at: string;
  last_updated: string;
  completed_sections: SectionName[];
  current_section: SectionName | null;
  data: Record<string, any>;
}

const STATE_FILE = '.onboarding-state.json';

/**
 * Gets the path to the state file
 * @returns Absolute path to state file
 */
function getStatePath(): string {
  return join(process.cwd(), STATE_FILE);
}

/**
 * Checks if a saved state exists
 * @returns True if state file exists
 */
export function hasExistingState(): boolean {
  return existsSync(getStatePath());
}

/**
 * Loads the onboarding state from disk
 * @returns OnboardingState or null if doesn't exist
 */
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

/**
 * Saves the onboarding state to disk
 * @param state - OnboardingState to save
 */
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

/**
 * Creates a new onboarding state
 * @returns New OnboardingState
 */
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

/**
 * Marks a section as completed and updates the current section
 * @param state - Current state
 * @param completedSection - Section that was completed
 * @param nextSection - Next section to work on (or null if done)
 * @returns Updated state
 */
export function markSectionComplete(
  state: OnboardingState,
  completedSection: SectionName,
  nextSection: SectionName | null
): OnboardingState {
  // Add to completed list if not already there
  if (!state.completed_sections.includes(completedSection)) {
    state.completed_sections.push(completedSection);
  }

  // Update current section
  state.current_section = nextSection;

  return state;
}

/**
 * Saves section data to state
 * @param state - Current state
 * @param section - Section name
 * @param data - Section data
 * @returns Updated state
 */
export function saveSectionData(
  state: OnboardingState,
  section: SectionName,
  data: Record<string, any>
): OnboardingState {
  state.data[section] = data;
  return state;
}

/**
 * Gets data for a specific section
 * @param state - Current state
 * @param section - Section name
 * @returns Section data or null
 */
export function getSectionData(
  state: OnboardingState,
  section: SectionName
): Record<string, any> | null {
  return state.data[section] || null;
}

/**
 * Deletes the onboarding state file
 */
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

/**
 * Gets the next section to work on based on current progress
 * @param state - Current state
 * @returns Next section or null if all complete
 */
export function getNextSection(state: OnboardingState): SectionName | null {
  const allSections: SectionName[] = [
    'liquid_assets',
    'investments',
    'cash_flow',
    'debt',
    'preferences',
    'mcp_config',
    'env_setup'
  ];

  // Find first section not in completed list
  const nextSection = allSections.find(
    section => !state.completed_sections.includes(section)
  );

  return nextSection || null;
}

/**
 * Checks if onboarding is complete
 * @param state - Current state
 * @returns True if all sections completed
 */
export function isComplete(state: OnboardingState): boolean {
  const allSections: SectionName[] = [
    'liquid_assets',
    'investments',
    'cash_flow',
    'debt',
    'preferences',
    'mcp_config',
    'env_setup'
  ];

  return allSections.every(section => state.completed_sections.includes(section));
}

/**
 * Formats time since state was last updated
 * @param state - Current state
 * @returns Human-readable time difference
 */
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
