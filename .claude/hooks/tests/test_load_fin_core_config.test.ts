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

import { describe, it, expect } from "bun:test";
import { join } from "path";
import { spawn } from "child_process";

const HOOK_PATH = join(import.meta.dir, "../load-fin-core-config.ts");

// Helper to run hook with input
async function runHook(input: { session_id: string; event: string }): Promise<{ stdout: string; stderr: string; exitCode: number }> {
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
    expect(result.stdout).toContain("LATEST PORTFOLIO BALANCES");
    expect(result.stdout).toContain("LATEST PORTFOLIO POSITIONS");
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

  it("should include completion footer", async () => {
    const result = await runHook({
      session_id: "test-footer",
      event: "session_start"
    });

    expect(result.stdout).toContain("Finance Guru context fully loaded and ready");
  });
});
