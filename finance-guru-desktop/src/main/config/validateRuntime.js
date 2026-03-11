const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const { PYTHON_BIN, CLAUDE_DIR, SRC_DIR } = require('./runtimePaths');

function checkClaudeAuth() {
  const homeDir = require('os').homedir();
  const claudeConfigDir = path.join(homeDir, '.claude');

  // ANTHROPIC_API_KEY is the most reliable signal
  if (process.env.ANTHROPIC_API_KEY) {
    return { ok: true, error: null };
  }

  // Check for actual credential artifacts inside ~/.claude/
  // A bare directory is not enough — look for auth state files
  if (fs.existsSync(claudeConfigDir)) {
    const credentialFiles = ['.credentials.json', 'credentials.json', 'config.json'];
    const hasCredentials = credentialFiles.some(f =>
      fs.existsSync(path.join(claudeConfigDir, f))
    );
    if (hasCredentials) {
      return { ok: true, error: null };
    }
  }

  return {
    ok: false,
    error: 'Claude authentication not found. Run `claude` in your terminal to authenticate, or set ANTHROPIC_API_KEY.'
  };
}

/**
 * Validate runtime environment. Accepts optional path overrides for testing.
 */
function validateRuntime(overrides = {}) {
  const pythonBin = overrides.pythonBin || PYTHON_BIN;
  const srcDir = overrides.srcDir || SRC_DIR;
  const claudeDir = overrides.claudeDir || CLAUDE_DIR;

  const errors = [];
  const warnings = [];

  // Check Python venv
  if (!fs.existsSync(pythonBin)) {
    errors.push(`Python not found at ${pythonBin}. Ensure family-office .venv is set up.`);
  } else {
    try {
      execFileSync(pythonBin, ['--version'], { timeout: 5000, encoding: 'utf8' });
    } catch {
      errors.push(`Python at ${pythonBin} failed to execute.`);
    }
  }

  // Check family-office src/ directory
  if (!fs.existsSync(srcDir)) {
    errors.push(`Family office src/ not found at ${srcDir}.`);
  }

  // Check .claude directory
  if (!fs.existsSync(claudeDir)) {
    errors.push(`Claude directory not found at ${claudeDir}.`);
  }

  // Check Claude auth (non-blocking warning)
  const auth = checkClaudeAuth();
  if (!auth.ok) {
    warnings.push(auth.error);
  }

  return {
    ok: errors.length === 0,
    errors,
    warnings,
    claudeAuth: auth
  };
}

module.exports = { validateRuntime, checkClaudeAuth };
