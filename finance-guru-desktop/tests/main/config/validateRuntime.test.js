const { describe, test, expect, beforeEach, afterEach } = require('bun:test');
const path = require('path');
const fs = require('fs');
const os = require('os');

describe('validateRuntime', () => {
  let originalEnv;

  beforeEach(() => {
    originalEnv = { ...process.env };
  });

  afterEach(() => {
    process.env = originalEnv;
  });

  // ── Happy path: real repo-bound layout ──

  test('passes with valid repo-bound layout', () => {
    const { validateRuntime } = require('../../../src/main/config/validateRuntime');
    const result = validateRuntime();

    expect(result.ok).toBe(true);
    expect(result.errors).toHaveLength(0);
    expect(result).toHaveProperty('warnings');
    expect(result).toHaveProperty('claudeAuth');
  });

  test('returns structured result with errors and warnings', () => {
    const { validateRuntime } = require('../../../src/main/config/validateRuntime');
    const result = validateRuntime();

    expect(result).toHaveProperty('ok');
    expect(result).toHaveProperty('errors');
    expect(result).toHaveProperty('warnings');
    expect(result).toHaveProperty('claudeAuth');
    expect(Array.isArray(result.errors)).toBe(true);
    expect(Array.isArray(result.warnings)).toBe(true);
  });

  // ── Failure cases: missing paths ──

  test('fails when .venv/bin/python3 is missing', () => {
    const { validateRuntime } = require('../../../src/main/config/validateRuntime');
    const result = validateRuntime({
      pythonBin: '/nonexistent/path/python3'
    });

    expect(result.ok).toBe(false);
    expect(result.errors.length).toBeGreaterThanOrEqual(1);
    expect(result.errors.some(e => e.includes('Python not found'))).toBe(true);
  });

  test('fails when family-office src/ is missing', () => {
    const { validateRuntime } = require('../../../src/main/config/validateRuntime');
    const result = validateRuntime({
      srcDir: '/nonexistent/src'
    });

    expect(result.ok).toBe(false);
    expect(result.errors.some(e => e.includes('src/ not found'))).toBe(true);
  });

  test('fails when .claude/ directory is missing', () => {
    const { validateRuntime } = require('../../../src/main/config/validateRuntime');
    const result = validateRuntime({
      claudeDir: '/nonexistent/.claude'
    });

    expect(result.ok).toBe(false);
    expect(result.errors.some(e => e.includes('Claude directory not found'))).toBe(true);
  });

  test('fails with multiple errors when all paths missing', () => {
    const { validateRuntime } = require('../../../src/main/config/validateRuntime');
    const result = validateRuntime({
      pythonBin: '/bad/python3',
      srcDir: '/bad/src',
      claudeDir: '/bad/.claude'
    });

    expect(result.ok).toBe(false);
    expect(result.errors.length).toBe(3);
  });

  // ── runtimePaths shape ──

  test('runtimePaths exports all required constants', () => {
    const paths = require('../../../src/main/config/runtimePaths');

    expect(paths.PROJECT_ROOT).toBeDefined();
    expect(paths.FAMILY_OFFICE_ROOT).toBeDefined();
    expect(paths.PYTHON_BIN).toBeDefined();
    expect(paths.CLAUDE_DIR).toBeDefined();
    expect(paths.SRC_DIR).toBeDefined();
    expect(paths.SUPPORTED_CSV_ROOTS).toBeDefined();
    expect(Array.isArray(paths.SUPPORTED_CSV_ROOTS)).toBe(true);
    expect(paths.SUPPORTED_CSV_ROOTS.length).toBe(2);
  });

  test('PYTHON_BIN points to .venv/bin/python3', () => {
    const { PYTHON_BIN } = require('../../../src/main/config/runtimePaths');
    expect(PYTHON_BIN).toContain('.venv');
    expect(PYTHON_BIN).toContain('python3');
  });

  test('SUPPORTED_CSV_ROOTS are explicit, not home-directory-wide', () => {
    const { SUPPORTED_CSV_ROOTS } = require('../../../src/main/config/runtimePaths');
    for (const root of SUPPORTED_CSV_ROOTS) {
      expect(root).toContain('family-office');
      expect(root).not.toBe(os.homedir());
    }
  });

  // ── Claude auth ──

  test('claudeAuth returns structured result', () => {
    const { checkClaudeAuth } = require('../../../src/main/config/validateRuntime');
    const auth = checkClaudeAuth();

    expect(auth).toHaveProperty('ok');
    expect(auth).toHaveProperty('error');
    expect(typeof auth.ok).toBe('boolean');
  });

  test('claudeAuth succeeds with ANTHROPIC_API_KEY set', () => {
    process.env.ANTHROPIC_API_KEY = 'sk-test-fake-key';
    // Clear module cache to pick up new env
    delete require.cache[require.resolve('../../../src/main/config/validateRuntime')];
    const { checkClaudeAuth } = require('../../../src/main/config/validateRuntime');
    const auth = checkClaudeAuth();

    expect(auth.ok).toBe(true);
    expect(auth.error).toBeNull();
  });

  test('claudeAuth fails when no credentials exist', () => {
    delete process.env.ANTHROPIC_API_KEY;
    // Temporarily override homedir to a path with no .claude/
    const originalHomedir = os.homedir;
    os.homedir = () => '/nonexistent-home-for-test';

    delete require.cache[require.resolve('../../../src/main/config/validateRuntime')];
    const { checkClaudeAuth } = require('../../../src/main/config/validateRuntime');
    const auth = checkClaudeAuth();

    os.homedir = originalHomedir;

    expect(auth.ok).toBe(false);
    expect(auth.error).toContain('Claude authentication not found');
  });
});
