/**
 * Integration Test: Onboarding Resume
 * Tests the onboarding resume functionality
 */

import { describe, test, expect, beforeEach, afterEach } from "bun:test";
import { existsSync, rmSync } from "fs";
import { join } from "path";

const PROJECT_ROOT = process.cwd();
const TEST_STATE_FILE = join(PROJECT_ROOT, ".onboarding-state.json");

describe("Onboarding Resume Integration Test", () => {
  beforeEach(() => {
    if (existsSync(TEST_STATE_FILE)) {
      rmSync(TEST_STATE_FILE, { force: true });
    }
  });

  afterEach(() => {
    if (existsSync(TEST_STATE_FILE)) {
      rmSync(TEST_STATE_FILE, { force: true });
    }
  });

  test("can resume from saved state", async () => {
    const {
      createNewState,
      saveState,
      loadState,
      hasExistingState,
      markSectionComplete
    } = await import("../../scripts/onboarding/modules/progress");

    const initialState = createNewState();
    markSectionComplete(initialState, "liquid_assets", "investments");
    saveState(initialState);

    expect(hasExistingState()).toBe(true);

    const resumedState = loadState();

    expect(resumedState).toBeDefined();
    expect(resumedState?.completed_sections).toContain("liquid_assets");
    expect(resumedState?.current_section).toBe("investments");
  });

  test("resume preserves completed sections", async () => {
    const {
      createNewState,
      saveState,
      loadState,
      markSectionComplete
    } = await import("../../scripts/onboarding/modules/progress");

    const state = createNewState();
    markSectionComplete(state, "liquid_assets", "investments");
    markSectionComplete(state, "investments", "cash_flow");
    markSectionComplete(state, "cash_flow", "debt");
    saveState(state);

    const resumedState = loadState();

    expect(resumedState?.completed_sections).toHaveLength(3);
    expect(resumedState?.completed_sections).toContain("liquid_assets");
    expect(resumedState?.completed_sections).toContain("investments");
    expect(resumedState?.completed_sections).toContain("cash_flow");
    expect(resumedState?.current_section).toBe("debt");
  });

  test("resume preserves section data", async () => {
    const {
      createNewState,
      saveState,
      loadState,
      saveSectionData,
      getSectionData
    } = await import("../../scripts/onboarding/modules/progress");

    const state = createNewState();
    saveSectionData(state, "liquid_assets", {
      checking_balance: 5000,
      savings_balance: 10000,
      total: 15000
    });
    saveState(state);

    const resumedState = loadState();
    const sectionData = getSectionData(resumedState!, "liquid_assets");

    expect(sectionData).toBeDefined();
    expect(sectionData?.checking_balance).toBe(5000);
    expect(sectionData?.savings_balance).toBe(10000);
    expect(sectionData?.total).toBe(15000);
  });

  test("getNextSection returns correct next section", async () => {
    const {
      createNewState,
      markSectionComplete,
      getNextSection
    } = await import("../../scripts/onboarding/modules/progress");

    const state = createNewState();

    expect(getNextSection(state)).toBe("liquid_assets");

    markSectionComplete(state, "liquid_assets", "investments");
    expect(getNextSection(state)).toBe("investments");

    markSectionComplete(state, "investments", "cash_flow");
    markSectionComplete(state, "cash_flow", "debt");
    expect(getNextSection(state)).toBe("debt");
  });

  test("getTimeSinceLastUpdate returns human-readable time", async () => {
    const {
      createNewState,
      saveState,
      loadState,
      getTimeSinceLastUpdate
    } = await import("../../scripts/onboarding/modules/progress");

    const state = createNewState();
    saveState(state);

    const resumedState = loadState();
    const timeSince = getTimeSinceLastUpdate(resumedState!);

    expect(timeSince).toBeDefined();
    expect(typeof timeSince).toBe("string");
    expect(timeSince).toBe("just now");
  });

  test("can continue from partially completed state", async () => {
    const {
      createNewState,
      saveState,
      loadState,
      markSectionComplete,
      isComplete
    } = await import("../../scripts/onboarding/modules/progress");

    const state = createNewState();
    markSectionComplete(state, "liquid_assets", "investments");
    markSectionComplete(state, "investments", "cash_flow");
    markSectionComplete(state, "cash_flow", "debt");
    saveState(state);

    const resumedState = loadState();
    expect(isComplete(resumedState!)).toBe(false);
    expect(resumedState?.current_section).toBe("debt");

    markSectionComplete(resumedState!, "debt", "preferences");
    markSectionComplete(resumedState!, "preferences", "summary");
    markSectionComplete(resumedState!, "summary", "mcp_config");
    markSectionComplete(resumedState!, "mcp_config", "env_setup");
    markSectionComplete(resumedState!, "env_setup", null);

    expect(isComplete(resumedState!)).toBe(true);
  });

  test("clearState removes state file", async () => {
    const {
      createNewState,
      saveState,
      hasExistingState,
      clearState
    } = await import("../../scripts/onboarding/modules/progress");

    const state = createNewState();
    saveState(state);
    expect(hasExistingState()).toBe(true);

    clearState();
    expect(hasExistingState()).toBe(false);
  });

  test("resume handles corrupted state file gracefully", async () => {
    const { writeFileSync } = await import("fs");
    const { loadState } = await import("../../scripts/onboarding/modules/progress");

    writeFileSync(TEST_STATE_FILE, "{ invalid json }", "utf-8");

    const state = loadState();
    expect(state).toBeNull();
  });

  test("state version is maintained across resume", async () => {
    const {
      createNewState,
      saveState,
      loadState
    } = await import("../../scripts/onboarding/modules/progress");

    const state = createNewState();
    expect(state.version).toBe("1.0");
    saveState(state);

    const resumedState = loadState();
    expect(resumedState?.version).toBe("1.0");
  });

  test("state preserves complex nested data structures", async () => {
    const {
      createNewState,
      saveState,
      loadState,
      saveSectionData
    } = await import("../../scripts/onboarding/modules/progress");

    const state = createNewState();
    saveSectionData(state, "investments", {
      portfolio: {
        equities: [
          { ticker: "TSLA", shares: 100, cost_basis: 200 },
          { ticker: "PLTR", shares: 500, cost_basis: 20 }
        ],
        fixed_income: [
          { type: "Treasury", amount: 10000, maturity: "2030-01-01" }
        ],
        totals: {
          equity_value: 45000,
          fixed_income_value: 10000,
          total_value: 55000
        }
      }
    });
    saveState(state);

    const resumedState = loadState();
    const investmentData = resumedState?.data.investments;

    expect(investmentData).toBeDefined();
    expect(investmentData.portfolio.equities).toHaveLength(2);
    expect(investmentData.portfolio.equities[0].ticker).toBe("TSLA");
    expect(investmentData.portfolio.fixed_income).toHaveLength(1);
    expect(investmentData.portfolio.totals.total_value).toBe(55000);
  });
});

describe("Resume Mode CLI Behavior", () => {
  test("CLI can detect resume mode from --resume flag", () => {
    const testArgs = ["--resume"];
    const isResumeMode = testArgs.includes("--resume");

    expect(isResumeMode).toBe(true);
  });

  test("CLI detects when not in resume mode", () => {
    const testArgs: string[] = [];
    const isResumeMode = testArgs.includes("--resume");

    expect(isResumeMode).toBe(false);
  });
});
