#!/usr/bin/env bun
/**
 * Tests for Finance Guru Core Config Loader Hook
 *
 * This test suite validates that the load-fin-core-config hook:
 * - Runs successfully with Bun runtime
 * - Correctly parses session input
 * - Loads all required configuration files
 * - Outputs correctly formatted system-reminder content
 */

import { afterAll, beforeAll, describe, expect, it } from "bun:test";
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "fs";
import { tmpdir } from "os";
import { basename, dirname, join } from "path";
import { spawn } from "child_process";
import { Database } from "bun:sqlite";

const HOOK_PATH = join(import.meta.dir, "../load-fin-core-config.ts");
const TEST_INSTANCE_ROOT = mkdtempSync(join(tmpdir(), "finance-guru-hook-test-"));

beforeAll(() => {
  mkdirSync(join(TEST_INSTANCE_ROOT, "imports"));
  writeFileSync(
    join(TEST_INSTANCE_ROOT, "config.yaml"),
    'module_name: "Finance Guru™"\nversion: "2.0.0"\n',
  );
  writeFileSync(join(TEST_INSTANCE_ROOT, "user-profile.yaml"), "profile: test-fixture\n");
  writeFileSync(join(TEST_INSTANCE_ROOT, "system-context.md"), "# Test system context\n");
  writeFileSync(
    join(TEST_INSTANCE_ROOT, "pyproject.toml"),
    '[project]\nname = "finance-guru-instance"\n',
  );
});

afterAll(() => {
  rmSync(TEST_INSTANCE_ROOT, { recursive: true, force: true });
});

// Helper to run hook with input
async function runHook(
  input: { session_id: string; event: string },
  useWorkingDirectory = false,
  extraEnv: Record<string, string> = {},
  cwd?: string,
): Promise<{ stdout: string; stderr: string; exitCode: number }> {
  return new Promise((resolve, reject) => {
    const env: Record<string, string | undefined> = { ...process.env };
    delete env.CLAUDE_PLUGIN_ROOT;
    delete env.CLAUDE_PROJECT_DIR;
    if (useWorkingDirectory) {
      delete env.FIN_GURU_DATA_ROOT;
    } else {
      env.FIN_GURU_DATA_ROOT = TEST_INSTANCE_ROOT;
    }
    Object.assign(env, extraEnv);

    const proc = spawn("bun", [HOOK_PATH], {
      cwd: cwd ?? (useWorkingDirectory ? TEST_INSTANCE_ROOT : undefined),
      env,
    });

    let stdout = "";
    let stderr = "";

    proc.stdout.on("data", (data) => {
      stdout += data.toString();
    });

    proc.stderr.on("data", (data) => {
      stderr += data.toString();
    });

    // Send input via stdin
    proc.stdin.write(JSON.stringify(input));
    proc.stdin.end();

    proc.on("close", (code) => {
      resolve({ stdout, stderr, exitCode: code || 0 });
    });

    proc.on("error", (err) => {
      reject(err);
    });
  });
}

describe("load-fin-core-config hook with Bun", () => {
  it("should execute successfully with Bun runtime", async () => {
    const result = await runHook({
      session_id: "test-bun-runtime",
      event: "session_start"
    });

    expect(result.exitCode).toBe(0);
    expect(result.stderr).toBe("");
  });

  it("should parse session input correctly", async () => {
    const sessionId = "test-session-" + Date.now();
    const result = await runHook({
      session_id: sessionId,
      event: "session_start"
    });

    expect(result.stdout).toContain(sessionId);
  });

  it("should load all required configuration sections", async () => {
    const result = await runHook({
      session_id: "test-sections",
      event: "session_start"
    });

    // Verify all main sections are present
    expect(result.stdout).toContain("FINANCE GURU CORE CONTEXT LOADED");
    expect(result.stdout).toContain("FIN-CORE SKILL");
    expect(result.stdout).toContain("SYSTEM CONFIGURATION");
    expect(result.stdout).toContain("USER PROFILE");
    expect(result.stdout).toContain("SYSTEM CONTEXT");
    expect(result.stdout).toContain("PORTFOLIO LEDGER");
  });

  it("should output properly formatted system-reminder", async () => {
    const result = await runHook({
      session_id: "test-format",
      event: "session_start"
    });

    // Should have header with box drawing
    expect(result.stdout).toContain("━");
    expect(result.stdout).toContain("🏦 FINANCE GURU CORE CONTEXT LOADED");

    // Should have section separators
    expect(result.stdout).toContain("═");

    // Should end with completion message
    expect(result.stdout).toContain("✅ Finance Guru context fully loaded and ready");
  });

  it("should include session ID in output", async () => {
    const testSessionId = "test-" + Math.random().toString(36).slice(2, 9);
    const result = await runHook({
      session_id: testSessionId,
      event: "session_start"
    });

    expect(result.stdout).toContain(`Session: ${testSessionId}`);
  });

  it("should load fin-core skill content", async () => {
    const result = await runHook({
      session_id: "test-skill",
      event: "session_start"
    });

    expect(result.stdout).toContain("Finance Guru™ Core Context");
    expect(result.stdout).toContain("Auto-loaded at every session start");
  });

  it("should load system configuration", async () => {
    const result = await runHook({
      session_id: "test-config",
      event: "session_start"
    });

    expect(result.stdout).toContain("module_name: \"Finance Guru™\"");
    expect(result.stdout).toContain("version: \"2.0.0\"");
  });

  it("should use the working directory when FIN_GURU_DATA_ROOT is unset", async () => {
    const result = await runHook(
      { session_id: "test-working-directory", event: "session_start" },
      true,
    );

    expect(result.stdout).toContain('module_name: "Finance Guru™"');
    expect(result.stdout).toContain("profile: test-fixture");
    expect(result.stdout).toContain("# Test system context");
  });

  it("should print nothing outside an instance", async () => {
    const outside = mkdtempSync(join(tmpdir(), "finance-guru-not-instance-"));
    try {
      const result = await runHook(
        { session_id: "test-outside", event: "session_start" },
        true,
        {},
        outside,
      );

      expect(result.exitCode).toBe(0);
      expect(result.stdout).toBe("");
    } finally {
      rmSync(outside, { recursive: true, force: true });
    }
  });

  it("should let a checkout's own hook copy run instead of the plugin copy", async () => {
    const checkout = mkdtempSync(join(tmpdir(), "finance-guru-checkout-"));
    mkdirSync(join(checkout, ".claude/hooks"), { recursive: true });
    writeFileSync(join(checkout, ".claude/hooks/load-fin-core-config.ts"), "");
    try {
      const result = await runHook({ session_id: "test-dup", event: "session_start" }, false, {
        CLAUDE_PLUGIN_ROOT: join(import.meta.dir, "../../.."),
        CLAUDE_PROJECT_DIR: checkout,
      });

      expect(result.exitCode).toBe(0);
      expect(result.stdout).toBe("");
    } finally {
      rmSync(checkout, { recursive: true, force: true });
    }
  });

  it("should point at the ledger instead of broker CSV downloads", async () => {
    const result = await runHook({ session_id: "test-no-ledger", event: "session_start" });
    const ledgerSection = result.stdout.split("PORTFOLIO LEDGER")[1];

    expect(ledgerSection).toContain(`Ledger not found at ${join(TEST_INSTANCE_ROOT, "family_office.db")}`);
    expect(ledgerSection).toContain("instance-onboarding");
    expect(ledgerSection).not.toContain("Fidelity");
  });

  it("should report the last balance sync from the ledger", async () => {
    const ledger = join(TEST_INSTANCE_ROOT, "family_office.db");
    const db = new Database(ledger);
    db.run("CREATE TABLE balances (account_id TEXT PRIMARY KEY, synced_at TEXT NOT NULL)");
    db.run("INSERT INTO balances VALUES ('a', '2026-01-02T03:04:05+00:00')");
    db.close();
    try {
      const result = await runHook({ session_id: "test-ledger", event: "session_start" });

      expect(result.stdout).toContain(`Ledger: ${ledger}`);
      expect(result.stdout).toContain("Balances last synced 2026-01-02T03:04:05+00:00");
      expect(result.stdout).toContain("older than 7 days");
    } finally {
      rmSync(ledger);
    }
  });

  it("should report no balance sync for a ledger with no balances table", async () => {
    const ledger = join(TEST_INSTANCE_ROOT, "family_office.db");
    writeFileSync(ledger, "");
    try {
      const result = await runHook({ session_id: "test-empty-ledger", event: "session_start" });

      expect(result.stdout).toContain("has no balance sync yet");
      expect(result.stdout).toContain("portfolio-syncing");
    } finally {
      rmSync(ledger);
    }
  });

  it("should check the ledger that DATABASE_URL in the instance .env names", async () => {
    const envFile = join(TEST_INSTANCE_ROOT, ".env");
    writeFileSync(envFile, "DATABASE_URL=sqlite:///custom/ledger.db\n");
    try {
      const result = await runHook({ session_id: "test-db-url", event: "session_start" });

      expect(result.stdout).toContain(join(TEST_INSTANCE_ROOT, "custom/ledger.db"));
    } finally {
      rmSync(envFile);
    }
  });

  it("should flag a ledger it cannot read instead of calling it fresh", async () => {
    const ledger = join(TEST_INSTANCE_ROOT, "family_office.db");
    writeFileSync(ledger, "this is not a sqlite database, it is plain text padding ".repeat(20));
    try {
      const result = await runHook({ session_id: "test-corrupt-ledger", event: "session_start" });

      expect(result.stdout).toContain("could not be read");
      expect(result.stdout).not.toContain("Balances last synced");
    } finally {
      rmSync(ledger);
    }
  });

  it("should read an export-style DATABASE_URL line the way python-dotenv does", async () => {
    const envFile = join(TEST_INSTANCE_ROOT, ".env");
    writeFileSync(envFile, "export DATABASE_URL = custom/exported.db\n");
    try {
      const result = await runHook({ session_id: "test-export-env", event: "session_start" });

      expect(result.stdout).toContain(join(TEST_INSTANCE_ROOT, "custom/exported.db"));
    } finally {
      rmSync(envFile);
    }
  });

  it("should print nothing in an unrelated repo that has a config.yaml", async () => {
    const repo = mkdtempSync(join(tmpdir(), "finance-guru-unrelated-"));
    writeFileSync(join(repo, "config.yaml"), "api_key: not-for-the-model\n");
    writeFileSync(join(repo, "user-profile.yaml"), "name: someone else\n");
    try {
      const result = await runHook({ session_id: "test-unrelated", event: "session_start" }, true, {}, repo);

      expect(result.exitCode).toBe(0);
      expect(result.stdout).toBe("");
    } finally {
      rmSync(repo, { recursive: true, force: true });
    }
  });

  it("should accept any TOML spelling of the scaffolded project name", async () => {
    const instance = mkdtempSync(join(tmpdir(), "finance-guru-toml-"));
    writeFileSync(join(instance, "user-profile.yaml"), "profile: toml-variant\n");
    writeFileSync(join(instance, "pyproject.toml"), "[project]\nname='finance-guru-instance'\n");
    try {
      const result = await runHook({ session_id: "test-toml", event: "session_start" }, true, {}, instance);

      expect(result.stdout).toContain("profile: toml-variant");
    } finally {
      rmSync(instance, { recursive: true, force: true });
    }
  });

  it("should expand ~ in FIN_GURU_DATA_ROOT the way InstancePaths does", async () => {
    const result = await runHook({ session_id: "test-tilde", event: "session_start" }, false, {
      HOME: dirname(TEST_INSTANCE_ROOT),
      FIN_GURU_DATA_ROOT: `~/${basename(TEST_INSTANCE_ROOT)}`,
    });

    expect(result.stdout).toContain("profile: test-fixture");
  });

  it("should let the instance .env DATABASE_URL win, as refresh_all does", async () => {
    const envFile = join(TEST_INSTANCE_ROOT, ".env");
    writeFileSync(envFile, "DATABASE_URL=sqlite:///from-env-file.db\n");
    try {
      const result = await runHook({ session_id: "test-env-wins", event: "session_start" }, false, {
        DATABASE_URL: "sqlite:///from-process.db",
      });

      expect(result.stdout).toContain(join(TEST_INSTANCE_ROOT, "from-env-file.db"));
    } finally {
      rmSync(envFile);
    }
  });

  it("should take the last DATABASE_URL line, as python-dotenv does", async () => {
    const envFile = join(TEST_INSTANCE_ROOT, ".env");
    writeFileSync(envFile, "DATABASE_URL=sqlite:///first.db\nDATABASE_URL=sqlite:///second.db\n");
    try {
      const result = await runHook({ session_id: "test-dotenv-0", event: "session_start" }, false, {});

      expect(result.stdout).toContain(`Ledger not found at ${join(TEST_INSTANCE_ROOT, "second.db")}.`);
    } finally {
      rmSync(envFile);
    }
  });

  it("should strip an inline comment from an unquoted DATABASE_URL", async () => {
    const envFile = join(TEST_INSTANCE_ROOT, ".env");
    writeFileSync(envFile, "DATABASE_URL=sqlite:///commented.db # main ledger\n");
    try {
      const result = await runHook({ session_id: "test-dotenv-1", event: "session_start" }, false, {});

      expect(result.stdout).toContain(`Ledger not found at ${join(TEST_INSTANCE_ROOT, "commented.db")}.`);
    } finally {
      rmSync(envFile);
    }
  });

  it("should treat an empty DATABASE_URL in .env as the default ledger", async () => {
    const envFile = join(TEST_INSTANCE_ROOT, ".env");
    writeFileSync(envFile, "DATABASE_URL=\n");
    try {
      const result = await runHook({ session_id: "test-dotenv-2", event: "session_start" }, false, { DATABASE_URL: "sqlite:///from-process.db" });

      expect(result.stdout).toContain(`Ledger not found at ${join(TEST_INSTANCE_ROOT, "family_office.db")}.`);
    } finally {
      rmSync(envFile);
    }
  });

  it("should fall back to the process DATABASE_URL when .env has no such line", async () => {
    const envFile = join(TEST_INSTANCE_ROOT, ".env");
    writeFileSync(envFile, "OTHER=1\n");
    try {
      const result = await runHook({ session_id: "test-dotenv-3", event: "session_start" }, false, { DATABASE_URL: "sqlite:///from-process.db" });

      expect(result.stdout).toContain(`Ledger not found at ${join(TEST_INSTANCE_ROOT, "from-process.db")}.`);
    } finally {
      rmSync(envFile);
    }
  });

  it("should include completion footer", async () => {
    const result = await runHook({
      session_id: "test-footer",
      event: "session_start"
    });

    expect(result.stdout).toContain("Finance Guru context fully loaded and ready");
  });
});
