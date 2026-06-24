#!/usr/bin/env bun
/**
 * Tests for Skill Activation Prompt Hook
 *
 * This test suite validates that the skill-activation-prompt hook:
 * - Runs successfully with Bun runtime
 * - Correctly parses prompt input
 * - Matches keywords and intent patterns
 * - Groups skills by priority correctly
 * - Outputs correctly formatted activation warnings
 */

import { describe, it, expect } from "bun:test";
import { join } from "path";
import { spawn } from "child_process";

const HOOK_PATH = join(import.meta.dir, "../skill-activation-prompt.ts");

// Helper to run hook with input
async function runHook(input: {
  session_id: string;
  transcript_path: string;
  cwd: string;
  permission_mode: string;
  prompt: string;
}): Promise<{ stdout: string; stderr: string; exitCode: number }> {
  return new Promise((resolve, reject) => {
    const proc = spawn("bun", [HOOK_PATH], {
      env: { ...process.env }
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

// Helper to create test input
function createTestInput(prompt: string, cwd?: string) {
  return {
    session_id: "test-session",
    transcript_path: "/tmp/transcript.txt",
    cwd: cwd || join(import.meta.dir, "../../.."),  // Go up to project root (tests -> hooks -> .claude -> project)
    permission_mode: "normal",
    prompt
  };
}

describe("skill-activation-prompt hook with Bun", () => {
  it("should execute successfully with Bun runtime", async () => {
    const result = await runHook(createTestInput("test prompt"));

    if (result.exitCode !== 0) {
      console.log("STDOUT:", result.stdout);
      console.log("STDERR:", result.stderr);
    }

    expect(result.exitCode).toBe(0);
    expect(result.stderr).toBe("");
  });

  it("should not output anything for non-matching prompts", async () => {
    const result = await runHook(createTestInput("hello world this is a test"));

    expect(result.exitCode).toBe(0);
    expect(result.stdout).toBe("");
  });

  it("should detect keyword matches", async () => {
    const result = await runHook(createTestInput("I want to sync portfolio"));

    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("SKILL ACTIVATION CHECK");
    expect(result.stdout).toContain("portfolio-syncing");
  });

  it("should detect intent pattern matches", async () => {
    const result = await runHook(createTestInput("update my fidelity positions"));

    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("SKILL ACTIVATION CHECK");
    expect(result.stdout).toContain("portfolio-syncing");
  });

  it("should group skills by priority - critical", async () => {
    const result = await runHook(createTestInput("update margin dashboard"));

    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("⚠️ CRITICAL SKILLS (REQUIRED):");
    expect(result.stdout).toContain("margin-management");
  });

  it("should group skills by priority - high", async () => {
    const result = await runHook(createTestInput("update dividend tracker"));

    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("📚 RECOMMENDED SKILLS:");
    expect(result.stdout).toContain("dividend-tracking");
  });

  it("should include action message", async () => {
    const result = await runHook(createTestInput("sync portfolio"));

    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("ACTION: Use Skill tool BEFORE responding");
  });

  it("should handle multiple skill matches", async () => {
    const result = await runHook(createTestInput("generate report for dividend tracker"));

    expect(result.exitCode).toBe(0);
    // Should match both finance-report and dividend-tracking
    expect(result.stdout).toContain("SKILL ACTIVATION CHECK");
    // Count of skills should be > 1
    const skillMatches = (result.stdout.match(/→/g) || []).length;
    expect(skillMatches).toBeGreaterThan(1);
  });

  it("should output properly formatted activation check", async () => {
    const result = await runHook(createTestInput("sync portfolio"));

    expect(result.exitCode).toBe(0);
    // Should have header with box drawing
    expect(result.stdout).toContain("━");
    expect(result.stdout).toContain("🎯 SKILL ACTIVATION CHECK");
  });

  it("should be case-insensitive for keywords", async () => {
    const result = await runHook(createTestInput("SYNC PORTFOLIO"));

    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("portfolio-syncing");
  });

  it("should match formula-protection skill", async () => {
    const result = await runHook(createTestInput("fix formula error #N/A"));

    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("formula-protection");
    expect(result.stdout).toContain("CRITICAL SKILLS");
  });

  it("should match retirement-syncing skill", async () => {
    const result = await runHook(createTestInput("sync vanguard IRA"));

    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("retirement-syncing");
  });

  it("should match finance-report skill", async () => {
    const result = await runHook(createTestInput("generate analysis report for NVDA"));

    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("finance-report");
  });

  it("should handle prompts with special characters", async () => {
    const result = await runHook(createTestInput("fix #DIV/0! in column C"));

    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("formula-protection");
  });

  it("should exit with code 0 even when no matches found", async () => {
    const result = await runHook(createTestInput("random unrelated text"));

    expect(result.exitCode).toBe(0);
  });
});
