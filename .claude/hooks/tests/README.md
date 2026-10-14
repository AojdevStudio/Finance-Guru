# Bun Hook Test Suite

A test suite for the Finance Guru Claude Code hooks, run with Bun.

## Overview

This test suite validates that:

1. **All Claude Code hooks work correctly** with Bun runtime
2. **Hook patterns and best practices** are followed

## Test Files

| Test File | Purpose |
|-----------|---------|
| `test_load_fin_core_config.test.ts` | Tests SessionStart hook (Finance Guru context loader) |
| `test_post_tool_use_tracker.test.ts` | Tests PostToolUse hook (file tracking) |
| `test_plugin_paths.test.ts` | Tests the plugin and checkout hook paths |
| `test_hook_performance.test.ts` | Tests hook run time |

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

# Run tests with coverage report
./run-tests.sh --coverage

# Run tests directly with bun
bun test tests/

# Run specific test file
bun test tests/test_load_fin_core_config.test.ts

# Run with test name pattern
bun test --test-name-pattern "should validate"
```


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

- **load-fin-core-config.ts**: 8 tests
- **post-tool-use-tracker.ts**: 33 tests

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

1. **Run individual test files**:
   ```bash
   bun test tests/test_load_fin_core_config.test.ts
   ```

2. **Check hook dependencies**:
   - Hooks may depend on project files (config.yaml, user-profile.yaml, etc.)
   - Ensure test environment has access to these files

### Cache Issues

Clean up test cache:

```bash
rm -rf .claude/tsc-cache/test-*
rm -rf tests/.test-tmp
```

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
