#!/usr/bin/env bun
/**
 * Hook Performance Test Suite
 *
 * Spawns each of the 3 hooks as child processes and asserts they complete
 * in under 500ms. Includes a warmup run to prime Bun's transpile cache.
 */

import { describe, it, expect } from "bun:test";
import { spawn } from "child_process";
import { join } from "path";

const HOOKS_DIR = join(import.meta.dir, "..");
const PROJECT_ROOT = join(HOOKS_DIR, "../..");
const MAX_EXECUTION_MS = 500;

/**
 * Spawn a hook as a child process, measure wall-clock time, and return results.
 */
async function timeHook(
  hookPath: string,
  input: Record<string, unknown>
): Promise<{
  stdout: string;
  stderr: string;
  exitCode: number;
  durationMs: number;
}> {
  const start = performance.now();
  return new Promise((resolve, reject) => {
    const proc = spawn("bun", [hookPath], {
      env: { ...process.env },
    });

    let stdout = "";
    let stderr = "";

    proc.stdout.on("data", (data) => {
      stdout += data.toString();
    });

    proc.stderr.on("data", (data) => {
      stderr += data.toString();
    });

    proc.stdin.write(JSON.stringify(input));
    proc.stdin.end();

    proc.on("close", (code) => {
      const durationMs = performance.now() - start;
      resolve({ stdout, stderr, exitCode: code || 0, durationMs });
    });

    proc.on("error", (err) => {
      reject(err);
    });
  });
}

describe("Hook Performance (< 500ms)", () => {
  it("warmup: prime bun transpile cache", async () => {
    const result = await timeHook(
      join(HOOKS_DIR, "load-fin-core-config.ts"),
      { session_id: "warmup", event: "session_start" }
    );
    expect(result.exitCode).toBe(0);
  });

  it("load-fin-core-config.ts completes in < 500ms", async () => {
    const result = await timeHook(
      join(HOOKS_DIR, "load-fin-core-config.ts"),
      { session_id: "perf-test", event: "session_start" }
    );
    expect(result.exitCode).toBe(0);
    expect(result.durationMs).toBeLessThan(MAX_EXECUTION_MS);
  });

  it("skill-activation-prompt.ts completes in < 500ms", async () => {
    const result = await timeHook(
      join(HOOKS_DIR, "skill-activation-prompt.ts"),
      {
        session_id: "perf-test",
        transcript_path: "/tmp/test-transcript.txt",
        cwd: PROJECT_ROOT,
        permission_mode: "normal",
        prompt: "test prompt for performance measurement",
      }
    );
    expect(result.exitCode).toBe(0);
    expect(result.durationMs).toBeLessThan(MAX_EXECUTION_MS);
  });

  it("post-tool-use-tracker.ts completes in < 500ms", async () => {
    const result = await timeHook(
      join(HOOKS_DIR, "post-tool-use-tracker.ts"),
      {
        tool_name: "Edit",
        tool_input: { file_path: "/tmp/test-file.ts" },
        session_id: "perf-test",
      }
    );
    expect(result.exitCode).toBe(0);
    expect(result.durationMs).toBeLessThan(MAX_EXECUTION_MS);
  });
});
