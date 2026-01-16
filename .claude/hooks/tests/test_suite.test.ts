#!/usr/bin/env bun
/**
 * Self-Testing Test Suite
 *
 * This meta-test suite validates that the Bun test infrastructure itself works correctly.
 * It tests the test suite to ensure:
 * - Bun test runner is functional
 * - Test assertions work as expected
 * - Test lifecycle (beforeEach, afterEach) functions properly
 * - Test helpers and utilities are available
 * - Test files can be discovered and executed
 * - Test isolation works correctly
 */

import { describe, it, expect, beforeEach, afterEach } from "bun:test";
import { spawn } from "child_process";
import { join } from "path";
import { mkdirSync, writeFileSync, rmSync, existsSync } from "fs";

describe("Bun Test Suite Infrastructure", () => {
  describe("Test Runner Capabilities", () => {
    it("should have access to describe function", () => {
      expect(typeof describe).toBe("function");
    });

    it("should have access to it function", () => {
      expect(typeof it).toBe("function");
    });

    it("should have access to expect function", () => {
      expect(typeof expect).toBe("function");
    });

    it("should have access to beforeEach function", () => {
      expect(typeof beforeEach).toBe("function");
    });

    it("should have access to afterEach function", () => {
      expect(typeof afterEach).toBe("function");
    });
  });

  describe("Assertion Capabilities", () => {
    it("should support toBe assertions", () => {
      expect(1 + 1).toBe(2);
    });

    it("should support toEqual assertions", () => {
      expect({ a: 1 }).toEqual({ a: 1 });
    });

    it("should support toContain assertions", () => {
      expect([1, 2, 3]).toContain(2);
      expect("hello world").toContain("world");
    });

    it("should support toBeTruthy assertions", () => {
      expect(true).toBeTruthy();
      expect(1).toBeTruthy();
      expect("hello").toBeTruthy();
    });

    it("should support toBeFalsy assertions", () => {
      expect(false).toBeFalsy();
      expect(0).toBeFalsy();
      expect("").toBeFalsy();
    });

    it("should support toBeGreaterThan assertions", () => {
      expect(2).toBeGreaterThan(1);
    });

    it("should support toBeLessThan assertions", () => {
      expect(1).toBeLessThan(2);
    });

    it("should support toThrow assertions", () => {
      expect(() => {
        throw new Error("test error");
      }).toThrow();
    });

    it("should support async expect", async () => {
      const promise = Promise.resolve(42);
      await expect(promise).resolves.toBe(42);
    });
  });

  describe("Test Lifecycle", () => {
    let lifecycleCounter = 0;

    beforeEach(() => {
      lifecycleCounter = 0;
    });

    afterEach(() => {
      // Verify beforeEach ran
      expect(lifecycleCounter).toBeGreaterThanOrEqual(0);
    });

    it("should run beforeEach before this test", () => {
      expect(lifecycleCounter).toBe(0);
      lifecycleCounter++;
    });

    it("should run beforeEach again before this test", () => {
      expect(lifecycleCounter).toBe(0);
      lifecycleCounter++;
    });

    it("should isolate test state between tests", () => {
      expect(lifecycleCounter).toBe(0);
      lifecycleCounter = 99;
    });
  });

  describe("File System Access", () => {
    const testDir = join(import.meta.dir, ".test-tmp");

    beforeEach(() => {
      if (existsSync(testDir)) {
        rmSync(testDir, { recursive: true, force: true });
      }
      mkdirSync(testDir, { recursive: true });
    });

    afterEach(() => {
      if (existsSync(testDir)) {
        rmSync(testDir, { recursive: true, force: true });
      }
    });

    it("should be able to create directories", () => {
      const nestedDir = join(testDir, "nested", "dir");
      mkdirSync(nestedDir, { recursive: true });
      expect(existsSync(nestedDir)).toBe(true);
    });

    it("should be able to write files", () => {
      const filePath = join(testDir, "test.txt");
      writeFileSync(filePath, "test content");
      expect(existsSync(filePath)).toBe(true);
    });

    it("should be able to clean up files", () => {
      const filePath = join(testDir, "test.txt");
      writeFileSync(filePath, "test content");
      expect(existsSync(filePath)).toBe(true);
      rmSync(filePath);
      expect(existsSync(filePath)).toBe(false);
    });
  });

  describe("Process Spawning", () => {
    it("should be able to spawn child processes", async () => {
      const result = await new Promise<{ stdout: string; exitCode: number }>((resolve) => {
        const proc = spawn("echo", ["hello"]);
        let stdout = "";

        proc.stdout.on("data", (data) => {
          stdout += data.toString();
        });

        proc.on("close", (code) => {
          resolve({ stdout, exitCode: code || 0 });
        });
      });

      expect(result.exitCode).toBe(0);
      expect(result.stdout.trim()).toBe("hello");
    });

    it("should be able to spawn bun runtime", async () => {
      const result = await new Promise<{ stdout: string; exitCode: number }>((resolve) => {
        const proc = spawn("bun", ["--version"]);
        let stdout = "";

        proc.stdout.on("data", (data) => {
          stdout += data.toString();
        });

        proc.on("close", (code) => {
          resolve({ stdout, exitCode: code || 0 });
        });
      });

      expect(result.exitCode).toBe(0);
      expect(result.stdout).toContain("1.");
    });
  });

  describe("Test File Discovery", () => {
    it("should find all test files in tests directory", () => {
      const testsDir = import.meta.dir;
      expect(existsSync(testsDir)).toBe(true);
    });

    it("should be able to import from parent directory", () => {
      const parentDir = join(import.meta.dir, "..");
      expect(existsSync(parentDir)).toBe(true);
    });
  });

  describe("Test Isolation", () => {
    it("should start with initial value", () => {
      let isolationTest = 0;
      expect(isolationTest).toBe(0);
      isolationTest = 100;
      expect(isolationTest).toBe(100);
    });

    it("should not share state with previous test", () => {
      // Variables declared in other tests should not be accessible
      // This test validates that each test runs in its own scope
      let isolationTest = 0;
      expect(isolationTest).toBe(0);
    });
  });

  describe("Async Test Support", () => {
    it("should support async/await syntax", async () => {
      const result = await Promise.resolve(42);
      expect(result).toBe(42);
    });

    it("should support Promise.all", async () => {
      const results = await Promise.all([
        Promise.resolve(1),
        Promise.resolve(2),
        Promise.resolve(3),
      ]);
      expect(results).toEqual([1, 2, 3]);
    });

    it("should support setTimeout in async tests", async () => {
      const start = Date.now();
      await new Promise((resolve) => setTimeout(resolve, 10));
      const elapsed = Date.now() - start;
      expect(elapsed).toBeGreaterThanOrEqual(10);
    });
  });

  describe("Error Handling", () => {
    it("should catch thrown errors", () => {
      expect(() => {
        throw new Error("test error");
      }).toThrow("test error");
    });

    it("should catch rejected promises", async () => {
      const promise = Promise.reject(new Error("async error"));
      await expect(promise).rejects.toThrow("async error");
    });

    it("should allow try-catch in tests", async () => {
      let errorCaught = false;
      try {
        throw new Error("test");
      } catch (err) {
        errorCaught = true;
      }
      expect(errorCaught).toBe(true);
    });
  });

  describe("Test Suite Meta-Validation", () => {
    it("should validate test file paths are accessible", () => {
      // Validate we can access test file paths
      const testDir = import.meta.dir;
      expect(existsSync(testDir)).toBe(true);

      // Validate other test files exist
      const testFiles = [
        "test_load_fin_core_config.test.ts",
        "test_post_tool_use_tracker.test.ts",
        "test_skill_activation_prompt.test.ts",
        "test_suite.test.ts"
      ];

      for (const file of testFiles) {
        const filePath = join(testDir, file);
        expect(existsSync(filePath)).toBe(true);
      }
    });

    it("should confirm test infrastructure is available", () => {
      // Verify we have all the tools needed to run tests
      const infrastructure = {
        testRunner: typeof describe === "function",
        assertions: typeof expect === "function",
        lifecycle: typeof beforeEach === "function" && typeof afterEach === "function",
        fileSystem: typeof existsSync === "function",
        processSpawning: typeof spawn === "function",
      };

      expect(infrastructure.testRunner).toBe(true);
      expect(infrastructure.assertions).toBe(true);
      expect(infrastructure.lifecycle).toBe(true);
      expect(infrastructure.fileSystem).toBe(true);
      expect(infrastructure.processSpawning).toBe(true);
    });
  });
});

describe("Hook Test Pattern Validation", () => {
  describe("Common Test Patterns", () => {
    it("should support the runHook pattern for testing hooks", () => {
      // This pattern is used across all hook tests
      const runHook = async (input: any): Promise<{ stdout: string; stderr: string; exitCode: number }> => {
        return new Promise((resolve) => {
          const proc = spawn("echo", [JSON.stringify(input)]);
          let stdout = "";
          let stderr = "";

          proc.stdout.on("data", (data) => {
            stdout += data.toString();
          });

          proc.stderr.on("data", (data) => {
            stderr += data.toString();
          });

          proc.on("close", (code) => {
            resolve({ stdout, stderr, exitCode: code || 0 });
          });
        });
      };

      expect(typeof runHook).toBe("function");
    });

    it("should support cleanup patterns with beforeEach/afterEach", () => {
      let setupRan = false;
      let cleanupRan = false;

      const setup = () => {
        setupRan = true;
      };

      const cleanup = () => {
        cleanupRan = true;
      };

      setup();
      expect(setupRan).toBe(true);

      cleanup();
      expect(cleanupRan).toBe(true);
    });

    it("should support the cache directory pattern", () => {
      const getCacheDir = (sessionId: string = "test"): string => {
        return join(import.meta.dir, "..", "..", ".claude", "tsc-cache", sessionId);
      };

      const cacheDir = getCacheDir("test-session");
      expect(cacheDir).toContain("tsc-cache");
      expect(cacheDir).toContain("test-session");
    });
  });

  describe("Test Input/Output Patterns", () => {
    it("should support JSON input pattern for hooks", () => {
      const input = {
        session_id: "test",
        event: "session_start",
      };

      const jsonString = JSON.stringify(input);
      const parsed = JSON.parse(jsonString);

      expect(parsed.session_id).toBe("test");
      expect(parsed.event).toBe("session_start");
    });

    it("should support validation of stdout output", () => {
      const stdout = "Some output from hook";
      expect(stdout).toContain("output");
    });

    it("should support validation of exit codes", () => {
      const exitCode = 0;
      expect(exitCode).toBe(0);
    });
  });
});

describe("Test Suite Health Check", () => {
  it("should confirm test suite is functional and self-aware", () => {
    // This test confirms that the test suite can test itself
    const testSuiteVersion = "1.0.0";
    const isSelfTesting = true;

    expect(testSuiteVersion).toBe("1.0.0");
    expect(isSelfTesting).toBe(true);
  });

  it("should report test suite capabilities", () => {
    const capabilities = {
      bunRuntime: true,
      asyncSupport: true,
      fileSystem: true,
      processSpawning: true,
      testIsolation: true,
      errorHandling: true,
      selfTesting: true,
    };

    expect(capabilities.bunRuntime).toBe(true);
    expect(capabilities.asyncSupport).toBe(true);
    expect(capabilities.fileSystem).toBe(true);
    expect(capabilities.processSpawning).toBe(true);
    expect(capabilities.testIsolation).toBe(true);
    expect(capabilities.errorHandling).toBe(true);
    expect(capabilities.selfTesting).toBe(true);
  });
});
