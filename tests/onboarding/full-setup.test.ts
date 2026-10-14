/**
 * Integration Test: Full Setup Flow
 * Tests the complete onboarding flow from start to finish
 */

import { describe, test, expect, beforeEach, afterEach } from "bun:test";
import { existsSync, rmSync, mkdirSync, writeFileSync, readFileSync } from "fs";
import { join } from "path";
import { spawn } from "bun";

const PROJECT_ROOT = process.cwd();
const TEST_STATE_FILE = join(PROJECT_ROOT, ".onboarding-state.test.json");

describe("Full Setup Flow Integration Test", () => {
  beforeEach(() => {
    // Clean up any existing test state
    if (existsSync(TEST_STATE_FILE)) {
      rmSync(TEST_STATE_FILE, { force: true });
    }
  });

  afterEach(() => {
    // Clean up test state
    if (existsSync(TEST_STATE_FILE)) {
      rmSync(TEST_STATE_FILE, { force: true });
    }
  });

  test("onboarding CLI structure exists", () => {
    const cliPath = join(PROJECT_ROOT, "scripts/onboarding/index.ts");
    expect(existsSync(cliPath)).toBe(true);
  });

  test("onboarding modules directory exists", () => {
    const modulesPath = join(PROJECT_ROOT, "scripts/onboarding/modules");
    expect(existsSync(modulesPath)).toBe(true);

    // Check core modules
    expect(existsSync(join(modulesPath, "progress.ts"))).toBe(true);
    expect(existsSync(join(modulesPath, "input-validator.ts"))).toBe(true);
    expect(existsSync(join(modulesPath, "yaml-generator.ts"))).toBe(true);
  });

  test("onboarding sections directory exists", () => {
    const sectionsPath = join(PROJECT_ROOT, "scripts/onboarding/sections");
    expect(existsSync(sectionsPath)).toBe(true);
  });

  test("required sections are implemented", () => {
    const sectionsPath = join(PROJECT_ROOT, "scripts/onboarding/sections");

    const requiredSections = [
      "investment-portfolio.ts",
      "preferences.ts",
      "liquid-assets.ts",
      "cash-flow.ts",
      "debt-profile.ts",
      "env-setup.ts",
      "summary.ts"
    ];

    for (const section of requiredSections) {
      const sectionPath = join(sectionsPath, section);
      expect(existsSync(sectionPath)).toBe(true);
    }
  });

  test("progress module exports required functions", async () => {
    const {
      hasExistingState,
      loadState,
      createNewState,
      saveState,
      clearState,
      isComplete
    } = await import("../../scripts/onboarding/modules/progress");

    expect(typeof hasExistingState).toBe("function");
    expect(typeof loadState).toBe("function");
    expect(typeof createNewState).toBe("function");
    expect(typeof saveState).toBe("function");
    expect(typeof clearState).toBe("function");
    expect(typeof isComplete).toBe("function");
  });

  test("input validator exports required validation functions", async () => {
    const validator = await import("../../scripts/onboarding/modules/input-validator");

    expect(typeof validator.validateCurrency).toBe("function");
    expect(typeof validator.validateNonEmpty).toBe("function");
    expect(typeof validator.validateRiskTolerance).toBe("function");
  });

  test("yaml generator exports generateUserProfile function", async () => {
    const { generateUserProfile } = await import("../../scripts/onboarding/modules/yaml-generator");

    expect(typeof generateUserProfile).toBe("function");
  });

  test("createNewState creates valid initial state", async () => {
    const { createNewState } = await import("../../scripts/onboarding/modules/progress");

    const state = createNewState();

    expect(state).toBeDefined();
    expect(state.version).toBe("1.0");
    expect(state.started_at).toBeDefined();
    expect(state.last_updated).toBeDefined();
    expect(state.completed_sections).toEqual([]);
    expect(state.current_section).toBeNull();
    expect(state.data).toBeDefined();
  });

  test("saveState and loadState work correctly", async () => {
    const { createNewState, saveState, loadState, hasExistingState } =
      await import("../../scripts/onboarding/modules/progress");

    const originalState = createNewState();
    originalState.data.test_field = "test_value";

    // Save state (uses default .onboarding-state.json in cwd)
    saveState(originalState);

    const defaultStatePath = join(PROJECT_ROOT, ".onboarding-state.json");
    expect(existsSync(defaultStatePath)).toBe(true);
    expect(hasExistingState()).toBe(true);

    const loadedState = loadState();

    expect(loadedState).toBeDefined();
    expect(loadedState?.version).toBe("1.0");
    expect(loadedState?.data.test_field).toBe("test_value");

    // Clean up
    if (existsSync(defaultStatePath)) {
      rmSync(defaultStatePath, { force: true });
    }
  });

  test("validateCurrency accepts valid currency formats", async () => {
    const { validateCurrency } = await import("../../scripts/onboarding/modules/input-validator");

    expect(validateCurrency("1000")).toBe(1000);
    expect(validateCurrency("1,000")).toBe(1000);
    expect(validateCurrency("$1,000")).toBe(1000);
    expect(validateCurrency("1000.50")).toBe(1000.50);
    expect(validateCurrency("$1,234.56")).toBe(1234.56);
  });

  test("validateCurrency rejects invalid formats", async () => {
    const { validateCurrency } = await import("../../scripts/onboarding/modules/input-validator");

    expect(() => validateCurrency("abc")).toThrow();
    expect(() => validateCurrency("-1000")).toThrow();
    expect(() => validateCurrency("")).toThrow();
  });

  test("validateRiskTolerance accepts valid values", async () => {
    const { validateRiskTolerance } = await import("../../scripts/onboarding/modules/input-validator");

    expect(validateRiskTolerance("aggressive")).toBe("aggressive");
    expect(validateRiskTolerance("moderate")).toBe("moderate");
    expect(validateRiskTolerance("conservative")).toBe("conservative");
    expect(validateRiskTolerance("Aggressive")).toBe("aggressive");
  });

  test("validateRiskTolerance rejects invalid values", async () => {
    const { validateRiskTolerance } = await import("../../scripts/onboarding/modules/input-validator");

    expect(() => validateRiskTolerance("risky")).toThrow();
    expect(() => validateRiskTolerance("")).toThrow();
  });

  test("generateUserProfile creates valid YAML structure", async () => {
    const { generateUserProfile } = await import("../../scripts/onboarding/modules/yaml-generator");

    const testData = {
      user_name: "TestUser",
      liquid_assets_total: 10000,
      liquid_assets_count: 2,
      portfolio_value: 100000,
      risk_tolerance: "moderate"
    };

    const yaml = generateUserProfile(testData);

    expect(yaml).toContain("liquid_assets:");
    expect(yaml).toContain("total: 10000");
    expect(yaml).toContain("investment_portfolio:");
    expect(yaml).toContain("total_value: 100000");
    expect(yaml).toContain('risk_profile: "moderate"');
    expect(yaml).toContain('risk_tolerance: "moderate"');
  });

  test("section progression follows correct order", async () => {
    const { createNewState, markSectionComplete } =
      await import("../../scripts/onboarding/modules/progress");

    const state = createNewState();

    expect(state.current_section).toBeNull();

    markSectionComplete(state, "liquid_assets", "investments");
    expect(state.current_section).toBe("investments");
    expect(state.completed_sections).toContain("liquid_assets");

    markSectionComplete(state, "investments", "cash_flow");
    expect(state.current_section).toBe("cash_flow");
    expect(state.completed_sections).toContain("investments");
  });

  test("isComplete returns true when all sections are done", async () => {
    const { createNewState, markSectionComplete, isComplete } =
      await import("../../scripts/onboarding/modules/progress");

    const state = createNewState();

    expect(isComplete(state)).toBe(false);

    // Complete all sections - must match the order defined in progress.ts
    const sections: Array<[string, string | null]> = [
      ["liquid_assets", "investments"],
      ["investments", "cash_flow"],
      ["cash_flow", "debt"],
      ["debt", "preferences"],
      ["preferences", "summary"],
      ["summary", "mcp_config"],
      ["mcp_config", "env_setup"],
      ["env_setup", null]
    ];

    for (const [section, next] of sections) {
      markSectionComplete(state, section as any, next as any);
    }

    expect(isComplete(state)).toBe(true);
    expect(state.current_section).toBeNull();
  });

  test("template files exist in correct location", () => {
    const templatesPath = join(PROJECT_ROOT, "scripts/onboarding/modules/templates");

    // Templates directory should exist
    expect(existsSync(templatesPath)).toBe(true);
  });

  test("CLI can be executed without errors", async () => {
    // This is a smoke test - just verify the CLI can be loaded
    try {
      const cliPath = join(PROJECT_ROOT, "scripts/onboarding/index.ts");
      const module = await import(cliPath);
      expect(module).toBeDefined();
    } catch (error) {
      // If there's a module loading error, the test should fail
      expect(error).toBeNull();
    }
  });
});

describe("Data Validation Rules", () => {
  test("validateNonEmpty rejects empty strings", async () => {
    const { validateNonEmpty } = await import("../../scripts/onboarding/modules/input-validator");

    expect(() => validateNonEmpty("")).toThrow();
    expect(() => validateNonEmpty("   ")).toThrow();
    expect(validateNonEmpty("valid")).toBe("valid");
  });

  test("validateEnum handles case-insensitive matching", async () => {
    const { validateEnum } = await import("../../scripts/onboarding/modules/input-validator");

    const validValues = ["option1", "option2", "option3"];

    expect(validateEnum("option1", validValues)).toBe("option1");
    expect(validateEnum("OPTION1", validValues)).toBe("option1");
    expect(validateEnum("Option2", validValues)).toBe("option2");
    expect(() => validateEnum("invalid", validValues)).toThrow();
  });
});

describe("State Persistence", () => {
  test("state file is created in correct location", async () => {
    const { createNewState, saveState } =
      await import("../../scripts/onboarding/modules/progress");

    const state = createNewState();
    saveState(state);

    const defaultStatePath = join(PROJECT_ROOT, ".onboarding-state.json");
    expect(existsSync(defaultStatePath)).toBe(true);

    const content = readFileSync(defaultStatePath, "utf-8");
    const parsed = JSON.parse(content);

    expect(parsed.version).toBe("1.0");
    expect(parsed.started_at).toBeDefined();

    // Clean up
    if (existsSync(defaultStatePath)) {
      rmSync(defaultStatePath, { force: true });
    }
  });

  test("state preserves custom data between save/load cycles", async () => {
    const { createNewState, saveState, loadState } =
      await import("../../scripts/onboarding/modules/progress");

    const state1 = createNewState();
    state1.data.custom_field = { nested: { value: 123 } };
    saveState(state1);

    const state2 = loadState();
    expect(state2?.data.custom_field.nested.value).toBe(123);

    // Clean up
    const defaultStatePath = join(PROJECT_ROOT, ".onboarding-state.json");
    if (existsSync(defaultStatePath)) {
      rmSync(defaultStatePath, { force: true });
    }
  });
});

describe("Full Setup Flow Integration", () => {
  const defaultStatePath = join(PROJECT_ROOT, ".onboarding-state.json");

  beforeEach(() => {
    // Clean up any existing state
    if (existsSync(defaultStatePath)) {
      rmSync(defaultStatePath, { force: true });
    }
  });

  afterEach(() => {
    // Clean up test state
    if (existsSync(defaultStatePath)) {
      rmSync(defaultStatePath, { force: true });
    }
  });

  test("complete onboarding flow: all sections in sequence", async () => {
    const {
      createNewState,
      saveState,
      loadState,
      markSectionComplete,
      saveSectionData,
      isComplete,
      getNextSection
    } = await import("../../scripts/onboarding/modules/progress");

    // 1. Start fresh onboarding
    let state = createNewState();
    expect(state.completed_sections).toEqual([]);
    expect(state.current_section).toBeNull();
    expect(isComplete(state)).toBe(false);

    saveState(state);
    expect(existsSync(defaultStatePath)).toBe(true);

    // 2. Complete liquid_assets section
    const liquidAssetsData = {
      total: 50000,
      accounts_count: 3,
      average_yield: 0.045,
      structure: ["2 business accounts", "1 high-yield savings"]
    };

    saveSectionData(state, "liquid_assets", liquidAssetsData);
    markSectionComplete(state, "liquid_assets", "investments");
    saveState(state);

    // Verify state was updated
    state = loadState()!;
    expect(state.completed_sections).toContain("liquid_assets");
    expect(state.current_section).toBe("investments");
    expect(state.data.liquid_assets).toEqual(liquidAssetsData);

    // 3. Complete investments section
    const investmentsData = {
      portfolio_value: 250000,
      brokerage: "Fidelity",
      holdings_count: 12,
      asset_allocation: {
        growth: 0.4,
        income: 0.3,
        hedge: 0.2,
        googl: 0.1
      }
    };

    saveSectionData(state, "investments", investmentsData);
    markSectionComplete(state, "investments", "cash_flow");
    saveState(state);

    state = loadState()!;
    expect(state.completed_sections).toContain("investments");
    expect(state.current_section).toBe("cash_flow");

    // 4. Complete cash_flow section
    const cashFlowData = {
      monthly_income: 15000,
      monthly_expenses: 8000,
      income_sources: ["W2 salary", "Consulting income"],
      expense_categories: ["Housing", "Business expenses", "Personal"]
    };

    saveSectionData(state, "cash_flow", cashFlowData);
    markSectionComplete(state, "cash_flow", "debt");
    saveState(state);

    state = loadState()!;
    expect(state.completed_sections).toContain("cash_flow");
    expect(state.current_section).toBe("debt");

    // 5. Complete debt section
    const debtData = {
      total_debt: 50000,
      margin_balance: 50000,
      margin_rate: 0.1375,
      other_debt: []
    };

    saveSectionData(state, "debt", debtData);
    markSectionComplete(state, "debt", "preferences");
    saveState(state);

    state = loadState()!;
    expect(state.completed_sections).toContain("debt");
    expect(state.current_section).toBe("preferences");

    // 6. Complete preferences section
    const preferencesData = {
      risk_tolerance: "moderate",
      investment_style: "value",
      time_horizon: "10+ years",
      special_considerations: ["Tax efficiency", "Dividend growth"]
    };

    saveSectionData(state, "preferences", preferencesData);
    markSectionComplete(state, "preferences", "summary");
    saveState(state);

    state = loadState()!;
    expect(state.completed_sections).toContain("preferences");
    expect(state.current_section).toBe("summary");

    // 7. Complete summary section
    const summaryData = {
      confirmed: true,
      timestamp: new Date().toISOString()
    };

    saveSectionData(state, "summary", summaryData);
    markSectionComplete(state, "summary", "mcp_config");
    saveState(state);

    state = loadState()!;
    expect(state.completed_sections).toContain("summary");
    expect(state.current_section).toBe("mcp_config");

    // 8. Complete mcp_config section (mock)
    const mcpConfigData = {
      configured_servers: ["exa", "perplexity", "context7"],
      config_path: "~/.claude/mcp.json"
    };

    saveSectionData(state, "mcp_config", mcpConfigData);
    markSectionComplete(state, "mcp_config", "env_setup");
    saveState(state);

    state = loadState()!;
    expect(state.completed_sections).toContain("mcp_config");
    expect(state.current_section).toBe("env_setup");

    // 9. Complete env_setup section (final)
    const envSetupData = {
      env_file_created: true,
      api_keys_configured: ["ANTHROPIC_API_KEY", "PERPLEXITY_API_KEY"]
    };

    saveSectionData(state, "env_setup", envSetupData);
    markSectionComplete(state, "env_setup", null);
    saveState(state);

    // 10. Verify completion
    state = loadState()!;
    expect(state.completed_sections).toHaveLength(8);
    expect(state.completed_sections).toEqual([
      "liquid_assets",
      "investments",
      "cash_flow",
      "debt",
      "preferences",
      "summary",
      "mcp_config",
      "env_setup"
    ]);
    expect(state.current_section).toBeNull();
    expect(isComplete(state)).toBe(true);
    expect(getNextSection(state)).toBeNull();

    // Verify all data was preserved
    expect(state.data.liquid_assets).toEqual(liquidAssetsData);
    expect(state.data.investments).toEqual(investmentsData);
    expect(state.data.cash_flow).toEqual(cashFlowData);
    expect(state.data.debt).toEqual(debtData);
    expect(state.data.preferences).toEqual(preferencesData);
    expect(state.data.summary).toEqual(summaryData);
    expect(state.data.mcp_config).toEqual(mcpConfigData);
    expect(state.data.env_setup).toEqual(envSetupData);
  });

  test("state persistence across save/load cycles during flow", async () => {
    const {
      createNewState,
      saveState,
      loadState,
      markSectionComplete,
      saveSectionData
    } = await import("../../scripts/onboarding/modules/progress");

    // Simulate a multi-session onboarding (save/load between each section)
    let state = createNewState();
    saveState(state);

    // Session 1: Liquid assets
    state = loadState()!;
    saveSectionData(state, "liquid_assets", { total: 10000 });
    markSectionComplete(state, "liquid_assets", "investments");
    saveState(state);

    // Session 2: Investments
    state = loadState()!;
    expect(state.completed_sections).toContain("liquid_assets");
    expect(state.data.liquid_assets.total).toBe(10000);
    saveSectionData(state, "investments", { portfolio_value: 100000 });
    markSectionComplete(state, "investments", "cash_flow");
    saveState(state);

    // Session 3: Verify both previous sections are preserved
    state = loadState()!;
    expect(state.completed_sections).toContain("liquid_assets");
    expect(state.completed_sections).toContain("investments");
    expect(state.data.liquid_assets.total).toBe(10000);
    expect(state.data.investments.portfolio_value).toBe(100000);
    expect(state.current_section).toBe("cash_flow");
  });

  test("getNextSection returns correct section in sequence", async () => {
    const {
      createNewState,
      getNextSection,
      markSectionComplete
    } = await import("../../scripts/onboarding/modules/progress");

    const state = createNewState();

    // At start, should return liquid_assets
    expect(getNextSection(state)).toBe("liquid_assets");

    // After completing liquid_assets, should return investments
    markSectionComplete(state, "liquid_assets", "investments");
    expect(getNextSection(state)).toBe("investments");

    // After completing investments, should return cash_flow
    markSectionComplete(state, "investments", "cash_flow");
    expect(getNextSection(state)).toBe("cash_flow");

    // Complete remaining sections
    markSectionComplete(state, "cash_flow", "debt");
    markSectionComplete(state, "debt", "preferences");
    markSectionComplete(state, "preferences", "summary");
    markSectionComplete(state, "summary", "mcp_config");
    markSectionComplete(state, "mcp_config", "env_setup");
    markSectionComplete(state, "env_setup", null);

    // After all sections complete, should return null
    expect(getNextSection(state)).toBeNull();
  });
});
