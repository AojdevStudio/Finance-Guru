import { expect, test } from "bun:test";
import { mkdtempSync, readFileSync, rmSync } from "fs";
import { tmpdir } from "os";
import { join } from "path";
import { createNewState } from "../../scripts/onboarding/modules/progress";
import { profileFromState } from "../../scripts/onboarding/sections/summary";
import { generateAllConfigs, generateEnv, generateUserProfile } from "../../scripts/onboarding/modules/yaml-generator";

test("summary converts section data into generated profile values", () => {
  const state = createNewState();
  state.data.env_setup = { user_name: "Synthetic Owner", communication_language: "English" };
  state.data.liquid_assets = { total: 100, accounts_count: 2, average_yield: 0.01, structure: [] };
  state.data.investments = { total_value: 200, retirement_accounts: 300, allocation: "balanced", risk_profile: "moderate" };
  state.data.cash_flow = { monthly_income: 400 };
  const directory = mkdtempSync(join(tmpdir(), "fg-summary-"));
  try {
    generateAllConfigs(profileFromState(state), directory);
    const profile = readFileSync(join(directory, "user-profile.yaml"), "utf8");
    expect(profile).toContain("total: 100");
    expect(profile).toContain("total_value: 200");
    expect(profile).toContain("monthly_income: 400");
    expect(readFileSync(join(directory, ".env"), "utf8")).toContain('USER_NAME="Synthetic Owner"');
  } finally {
    rmSync(directory, { recursive: true });
  }
});

test("summary refuses to invent the owner's name", () => {
  expect(() => profileFromState(createNewState())).toThrow("name");
});

test("templates never generate retired Sheets configuration", () => {
  const data = { user_name: "Synthetic Owner", google_sheets_id: "synthetic", google_sheets_credentials: "synthetic.json" };
  expect(generateEnv(data)).not.toContain("GOOGLE_SHEETS");
  expect(generateUserProfile(data)).not.toContain("google_sheets");
});


test("onboarding entry point runs the real wizard help", async () => {
  const child = Bun.spawn(["bun", "scripts/onboarding/index.ts", "--help"], { stdout: "pipe", stderr: "pipe" });
  const output = await new Response(child.stdout).text();
  expect(await child.exited).toBe(0);
  expect(output).toContain("onboarding-wizard");
  expect(output).toContain("--dry-run");
  expect(output).not.toContain("structure created");
});


test("broker selection and summary use valid section and profile types", async () => {
  const child = Bun.spawn([
    "bunx", "--package", "typescript", "tsc", "--noEmit", "--target", "esnext",
    "--module", "preserve", "--moduleResolution", "bundler", "--types", "bun", "--skipLibCheck",
    "scripts/onboarding/sections/broker-selection.ts", "scripts/onboarding/sections/summary.ts",
    "scripts/onboarding/sections/investment-portfolio.ts",
  ], { stdout: "pipe", stderr: "pipe" });
  const output = await new Response(child.stdout).text();
  const errors = await new Response(child.stderr).text();
  expect({ code: await child.exited, output, errors }).toEqual({ code: 0, output: "", errors: "" });
});
