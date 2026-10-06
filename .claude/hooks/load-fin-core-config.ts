#!/usr/bin/env bun

/**
 * Finance Guru Core Config Loader
 * Session Start Hook
 *
 * Automatically loads Finance Guru system context at session start:
 * - System configuration (config.yaml)
 * - User profile (user-profile.yaml)
 * - Where the portfolio ledger lives (family_office.db)
 * - fin-core skill content
 *
 * Refactored to use Bun runtime for improved performance.
 */

import { Database } from 'bun:sqlite';
import { existsSync, readFileSync } from 'fs';
import { join, resolve } from 'path';

// Bun provides import.meta.dir directly
const __dirname = import.meta.dir;
const PROJECT_ROOT = resolve(__dirname, '../..');
// Path.expanduser for a leading "~", which InstancePaths applies to the root and bare paths.
function expandHome(path: string): string {
  if (path !== '~' && !path.startsWith('~/')) return path;
  return join(process.env.HOME ?? '~', path.slice(1));
}

// The same rule as InstancePaths.resolve: FIN_GURU_DATA_ROOT, else the session directory.
const CONFIGURED_ROOT = expandHome(process.env.FIN_GURU_DATA_ROOT?.trim() ?? '');
const DATA_ROOT = resolve(CONFIGURED_ROOT || process.cwd());
const STALE_AFTER_DAYS = 7;

interface HookInput {
  session_id: string;
  event: string;
}

// A user-scope plugin hook runs in every session, and config.yaml is common in
// unrelated repos, so the session directory needs a Finance Guru marker before
// any private file is read. A root the owner named in FIN_GURU_DATA_ROOT needs only a profile.
function isInstance(root: string): boolean {
  if (!existsSync(join(root, 'user-profile.yaml'))) return false;
  if (CONFIGURED_ROOT) return true;
  return scaffoldedProject(join(root, 'pyproject.toml')) || existsSync(join(root, 'family_office.db'));
}

// instance_init writes a pyproject.toml whose project is named finance-guru-instance.
function scaffoldedProject(pyproject: string): boolean {
  try {
    return /^\s*name\s*=\s*["']finance-guru-instance["']/m.test(readFileSync(pyproject, 'utf-8'));
  } catch {
    // A missing or unreadable file means this is not a scaffolded instance.
    return false;
  }
}

// A checkout instance or the engine repo runs its own copy through .claude/settings.json.
function checkoutCopyRuns(): boolean {
  const projectDir = process.env.CLAUDE_PROJECT_DIR;
  if (!process.env.CLAUDE_PLUGIN_ROOT || !projectDir) return false;
  return existsSync(join(projectDir, '.claude/hooks/load-fin-core-config.ts'));
}

// The value python-dotenv assigns to key, or undefined when no line sets it.
// Modeled: the last assignment wins, quotes are removed, an unquoted " #" starts a
// comment, an empty value still counts as set, and CRLF files parse. Not modeled:
// ${VAR} expansion, escapes inside quotes, multi-line values, and a leading BOM.
function dotenvValue(envFile: string, key: string): string | undefined {
  if (!existsSync(envFile)) return undefined;
  const assignment = new RegExp(`^\\s*(?:export\\s+)?${key}\\s*=\\s*(.*)$`);
  let value: string | undefined;
  for (const line of readFileSync(envFile, 'utf-8').split(/\r?\n/)) {
    const raw = assignment.exec(line)?.[1];
    if (raw === undefined) continue;
    const quoted = /^(["'])(.*?)\1/.exec(raw);
    value = quoted ? quoted[2] : raw.replace(/\s+#.*$/, '').trim();
  }
  return value;
}

// Finds the ledger refresh_all writes: it loads the instance .env with
// override=True, so DATABASE_URL there wins over the process environment.
// A relative SQLite path resolves under the instance root, as in InstancePaths.database_url.
function ledgerPath(root: string): string | null {
  const fromEnvFile = dotenvValue(join(root, '.env'), 'DATABASE_URL');
  const configured = (fromEnvFile ?? process.env.DATABASE_URL ?? '').trim();
  if (!configured) return join(root, 'family_office.db');
  if (configured.startsWith('sqlite:///')) {
    const path = configured.slice('sqlite:///'.length);
    return path === ':memory:' ? null : resolve(root, path);
  }
  if (configured.includes('://') || configured === ':memory:') return null;
  return resolve(root, expandHome(configured));
}

// The ledger replaced broker CSVs as the source of positions and balances.
function describeLedger(ledgerFile: string): string {
  if (!existsSync(ledgerFile)) {
    return `Ledger not found at ${ledgerFile}.\nRun the instance-onboarding skill to scaffold the instance and its ledger.`;
  }
  let lastSync: string | null = null;
  try {
    const db = new Database(ledgerFile, { readonly: true });
    try {
      const row = db.query('SELECT MAX(synced_at) AS last FROM balances').get() as {
        last: string | null;
      } | null;
      lastSync = row?.last ?? null;
    } finally {
      db.close();
    }
  } catch (err) {
    if (String(err).includes('no such table')) lastSync = null;
    else return `Ledger: ${ledgerFile} could not be read (${err}).\nRun the portfolio-syncing skill before you quote a position or a balance.`;
  }
  if (!lastSync) {
    return `Ledger: ${ledgerFile} has no balance sync yet.\nRun the portfolio-syncing skill before you quote a position or a balance.`;
  }
  const ageDays = (Date.now() - Date.parse(lastSync)) / 86_400_000;
  const freshness =
    ageDays > STALE_AFTER_DAYS
      ? `That is older than ${STALE_AFTER_DAYS} days, so run the portfolio-syncing skill before you quote a number.`
      : 'Run the portfolio-syncing skill to refresh it before you quote a number.';
  return `Ledger: ${ledgerFile}\nBalances last synced ${lastSync}. ${freshness}`;
}

function loadFile(path: string): string {
  try {
    return readFileSync(path, 'utf-8');
  } catch (err) {
    return `[File not found: ${path}]`;
  }
}

function main() {
  // Read stdin (session info)
  let inputData = '';
  process.stdin.setEncoding('utf-8');

  // Handle both piped and direct execution
  if (process.stdin.isTTY) {
    // Direct execution (testing) - use dummy input
    inputData = JSON.stringify({ session_id: 'test', event: 'session_start' });
    processHook(inputData);
  } else {
    // Piped input from Claude Code
    process.stdin.on('data', chunk => {
      inputData += chunk;
    });

    process.stdin.on('end', () => {
      processHook(inputData);
    });
  }
}

function processHook(inputData: string) {
  try {
    const input: HookInput = JSON.parse(inputData);
    if (checkoutCopyRuns() || !isInstance(DATA_ROOT)) {
      process.exit(0);
    }
    // The skill ships with the project; private inputs belong to the instance.
    const skillPath = join(PROJECT_ROOT, '.claude/skills/fin-core/SKILL.md');
    const configPath = join(DATA_ROOT, 'config.yaml');
    const profilePath = join(DATA_ROOT, 'user-profile.yaml');
    const systemContextPath = join(DATA_ROOT, 'system-context.md');
    const ledger = ledgerPath(DATA_ROOT);

    // Load core files
    const skillContent = loadFile(skillPath);
    const configContent = loadFile(configPath);
    const profileContent = loadFile(profilePath);
    const systemContext = loadFile(systemContextPath);

    // Build system reminder output
    const output = `
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏦 FINANCE GURU CORE CONTEXT LOADED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Session: ${input.session_id}

═══════════════════════════════════════════
📘 FIN-CORE SKILL
═══════════════════════════════════════════

${skillContent}

═══════════════════════════════════════════
⚙️ SYSTEM CONFIGURATION
═══════════════════════════════════════════

${configContent}

═══════════════════════════════════════════
👤 USER PROFILE
═══════════════════════════════════════════

${profileContent}

═══════════════════════════════════════════
🌐 SYSTEM CONTEXT
═══════════════════════════════════════════

${systemContext}

═══════════════════════════════════════════
📒 PORTFOLIO LEDGER
═══════════════════════════════════════════

${ledger ? describeLedger(ledger) : 'The ledger is not a local SQLite file, so its freshness is not checked here.'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Finance Guru context fully loaded and ready
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
`.trim();

    // Output to stdout (Claude Code will inject this as system-reminder)
    console.log(output);

    // Exit successfully
    process.exit(0);

  } catch (err) {
    console.error(`Finance Guru core config loader failed: ${err}`);
    process.exit(1);
  }
}

main();
