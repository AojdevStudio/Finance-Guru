# Bun Hook Test Suite

A comprehensive, self-testing test suite for Claude Code hooks using Bun runtime.

## Overview

This test suite validates that:

1. **The test infrastructure itself is functional** (self-testing)
2. **All Claude Code hooks work correctly** with Bun runtime
3. **Hook patterns and best practices** are followed

## Test Files

| Test File | Purpose |
|-----------|---------|
| `test_suite.test.ts` | **Self-testing suite** - validates test infrastructure |
| `test_load_fin_core_config.test.ts` | Tests SessionStart hook (Finance Guru context loader) |
| `test_post_tool_use_tracker.test.ts` | Tests PostToolUse hook (file tracking) |
| `test_skill_activation_prompt.test.ts` | Tests UserPromptSubmit hook (skill activation) |

## Running Tests

### Quick Start

```bash
# From .claude/hooks directory
./run-tests.sh
```

### All Options

```bash
# Run all tests
./run-tests.sh

# Run only the self-testing suite
./run-tests.sh --suite-only

# Run tests with coverage report
./run-tests.sh --coverage

# Run tests directly with bun
bun test tests/

# Run specific test file
bun test tests/test_suite.test.ts

# Run with test name pattern
bun test --test-name-pattern "should validate"
```

## Self-Testing Features

The `test_suite.test.ts` file is unique - it tests the test suite itself to ensure the testing infrastructure is reliable:

### What It Tests

1. **Test Runner Capabilities**
   - Verifies `describe`, `it`, `expect`, `beforeEach`, `afterEach` are available
   - Confirms Bun test runner is functional

2. **Assertion Capabilities**
   - Tests all assertion methods: `toBe`, `toEqual`, `toContain`, etc.
   - Validates async assertions work: `resolves`, `rejects`

3. **Test Lifecycle**
   - Ensures `beforeEach` and `afterEach` run correctly
   - Verifies test isolation (no state sharing)

4. **File System Access**
   - Tests file/directory creation, deletion
   - Validates cleanup patterns work

5. **Process Spawning**
   - Confirms ability to spawn child processes
   - Tests Bun runtime execution

6. **Meta-Validation**
   - **The test suite runs itself** to verify it works
   - Confirms all test files can be discovered

### Example: Self-Testing Test

```typescript
it("should validate that this test file itself can be executed", async () => {
  // Run this test file with bun test
  const result = await new Promise<{ exitCode: number }>((resolve) => {
    const proc = spawn("bun", ["test", __filename], {
      cwd: join(import.meta.dir, ".."),
    });

    proc.on("close", (code) => {
      resolve({ exitCode: code || 0 });
    });
  });

  expect(result.exitCode).toBe(0);
});
```

This test literally runs itself and validates it passes!

## Hook Test Patterns

All hook tests follow these patterns:

### 1. The `runHook` Helper

```typescript
async function runHook(input: HookInput): Promise<{ stdout: string; stderr: string; exitCode: number }> {
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
```

### 2. Cleanup Pattern

```typescript
beforeEach(() => {
  // Setup - create fresh test environment
  cleanupCacheDir();
});

afterEach(() => {
  // Cleanup - remove test artifacts
  cleanupCacheDir();
});
```

### 3. Input Validation Pattern

```typescript
it("should parse session input correctly", async () => {
  const sessionId = "test-session-" + Date.now();
  const result = await runHook({
    session_id: sessionId,
    event: "session_start"
  });

  expect(result.stdout).toContain(sessionId);
});
```

## Test Coverage

Current test coverage:

- **Test Infrastructure**: 100% (self-testing)
- **load-fin-core-config.ts**: 8 tests
- **post-tool-use-tracker.ts**: 33 tests
- **skill-activation-prompt.ts**: 15 tests
- **Total Tests**: 97+ tests across 4 files

## Adding New Tests

### For a New Hook

1. Create `tests/test_your_hook.test.ts`
2. Use the `runHook` pattern from existing tests
3. Test success cases, error cases, edge cases
4. Add cleanup with `beforeEach`/`afterEach`

Example:

```typescript
#!/usr/bin/env bun
import { describe, it, expect } from "bun:test";
import { spawn } from "child_process";
import { join } from "path";

const HOOK_PATH = join(import.meta.dir, "../your-hook.ts");

async function runHook(input: any): Promise<{ stdout: string; stderr: string; exitCode: number }> {
  // ... (use standard runHook pattern)
}

describe("your-hook with Bun", () => {
  it("should execute successfully", async () => {
    const result = await runHook({ /* input */ });
    expect(result.exitCode).toBe(0);
  });
});
```

### For Test Infrastructure

Add tests to `test_suite.test.ts` to validate new testing capabilities.

## CI/CD Integration

Add to your CI pipeline:

```yaml
- name: Run Bun Hook Tests
  run: |
    cd .claude/hooks
    ./run-tests.sh
```

Or use directly:

```yaml
- name: Test Hooks
  run: cd .claude/hooks && bun test tests/
```

## Troubleshooting

### Tests Won't Run

1. **Check Bun is installed**:
   ```bash
   bun --version
   ```

2. **Check test files are executable**:
   ```bash
   chmod +x tests/*.test.ts
   ```

3. **Run with verbose output**:
   ```bash
   bun test tests/ --verbose
   ```

### Tests Fail

1. **Run self-testing suite first**:
   ```bash
   ./run-tests.sh --suite-only
   ```
   If this fails, your test infrastructure has issues.

2. **Run individual test files**:
   ```bash
   bun test tests/test_suite.test.ts
   bun test tests/test_load_fin_core_config.test.ts
   ```

3. **Check hook dependencies**:
   - Hooks may depend on project files (config.yaml, user-profile.yaml, etc.)
   - Ensure test environment has access to these files

### Cache Issues

Clean up test cache:

```bash
rm -rf .claude/tsc-cache/test-*
rm -rf tests/.test-tmp
```

## Philosophy

This test suite follows the principle of **self-testing**:

> "How do you know your tests work? Test them!"

The `test_suite.test.ts` file is a meta-test that validates the testing infrastructure itself. This ensures:

1. Tests are reliable (they test themselves)
2. Test failures are real (not infrastructure issues)
3. New developers can trust the test suite
4. CI/CD failures indicate real problems

## Future Enhancements

- [ ] Add test for `error-handling-reminder.ts` hook
- [ ] Add test for `stop-build-check-enhanced.sh` hook
- [ ] Add performance benchmarking tests
- [ ] Add test coverage reporting
- [ ] Add mutation testing to validate test quality

## References

- [Bun Test Documentation](https://bun.sh/docs/cli/test)
- [Claude Code Hooks Guide](../README.md)
- [Hook Configuration](../CONFIG.md)
