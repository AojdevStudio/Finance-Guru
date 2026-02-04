#!/usr/bin/env bun

/**
 * Finance Guru Core Config Loader
 * Session Start Hook
 *
 * Automatically loads Finance Guru system context at session start:
 * - System configuration (config.yaml)
 * - User profile (user-profile.yaml)
 * - Latest portfolio updates (balances, positions)
 * - fin-core skill content
 *
 * Refactored to use Bun runtime for improved performance.
 */

import { readFileSync, readdirSync, statSync } from 'fs';
import { join, resolve, dirname } from 'path';

// Bun provides import.meta.dir directly
const __dirname = import.meta.dir;

interface HookInput {
  session_id: string;
  event: string;
}

function getProjectRoot(): string {
  // Hook is in family-office/.claude/hooks/
  // Project root is family-office/
  return resolve(__dirname, '../..');
}

function getLatestFile(dir: string, pattern: RegExp): string | null {
  try {
    const files = readdirSync(dir)
      .filter(f => pattern.test(f))
      .map(f => ({
        name: f,
        path: join(dir, f),
        mtime: statSync(join(dir, f)).mtime.getTime()
      }))
      .sort((a, b) => b.mtime - a.mtime); // newest first

    return files.length > 0 ? files[0].path : null;
  } catch (err) {
    return null;
  }
}

function parsePositionsFileDate(filename: string): Date | null {
  // Pattern: Portfolio_Positions_Nov-05-2025.csv
  const match = filename.match(/Portfolio_Positions_([A-Za-z]{3})-(\d{2})-(\d{4})\.csv$/);
  if (!match) return null;

  const [, month, day, year] = match;
  const monthMap: Record<string, number> = {
    'Jan': 0, 'Feb': 1, 'Mar': 2, 'Apr': 3, 'May': 4, 'Jun': 5,
    'Jul': 6, 'Aug': 7, 'Sep': 8, 'Oct': 9, 'Nov': 10, 'Dec': 11
  };

  const monthNum = monthMap[month];
  if (monthNum === undefined) return null;

  return new Date(parseInt(year), monthNum, parseInt(day));
}

function getLatestPositionsFile(dir: string): string | null {
  try {
    const files = readdirSync(dir)
      .filter(f => /^Portfolio_Positions_[A-Za-z]{3}-\d{2}-\d{4}\.csv$/.test(f))
      .map(f => ({
        name: f,
        path: join(dir, f),
        date: parsePositionsFileDate(f)
      }))
      .filter(f => f.date !== null)
      .sort((a, b) => (b.date!.getTime() - a.date!.getTime())); // newest first by date in filename

    return files.length > 0 ? files[0].path : null;
  } catch (err) {
    return null;
  }
}

function isFileRecent(filePath: string, maxAgeDays: number = 7): boolean {
  try {
    const stats = statSync(filePath);
    const ageMs = Date.now() - stats.mtime.getTime();
    const ageDays = ageMs / (1000 * 60 * 60 * 24);
    return ageDays <= maxAgeDays;
  } catch (err) {
    return false;
  }
}

function generateUpdateAlert(missingBalances: boolean, missingPositions: boolean, outdatedBalances: boolean, outdatedPositions: boolean): string {
  const alerts: string[] = [];

  if (missingBalances) {
    alerts.push('⚠️ MISSING: Balances file (notebooks/updates/Balances_for_Account_{account_id}.csv)');
  } else if (outdatedBalances) {
    alerts.push('⚠️ OUTDATED: Balances file is older than 7 days');
  }

  if (missingPositions) {
    alerts.push('⚠️ MISSING: Portfolio positions file (notebooks/updates/Portfolio_Positions_MMM-DD-YYYY.csv)');
  } else if (outdatedPositions) {
    alerts.push('⚠️ OUTDATED: Portfolio positions file is older than 7 days');
  }

  if (alerts.length === 0) return '';

  return `
═══════════════════════════════════════════
🚨 PORTFOLIO DATA ALERT
═══════════════════════════════════════════

${alerts.join('\n')}

📥 ACTION REQUIRED:
Please update your portfolio data by downloading the latest files from Fidelity:
1. Balances: Export to notebooks/updates/Balances_for_Account_{account_id}.csv
2. Positions: Export to notebooks/updates/Portfolio_Positions_MMM-DD-YYYY.csv

Your Finance Guru analysis will be more accurate with current data.
`;
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
    const projectRoot = getProjectRoot();
    
    // File paths (all project-specific)
    const skillPath = join(projectRoot, '.claude/skills/fin-core/SKILL.md');
    const configPath = join(projectRoot, 'fin-guru/config.yaml');
    const profilePath = join(projectRoot, 'fin-guru/data/user-profile.yaml');
    const systemContextPath = join(projectRoot, 'fin-guru/data/system-context.md');
    const updatesDir = join(projectRoot, 'notebooks/updates');
    
    // Load core files
    const skillContent = loadFile(skillPath);
    const configContent = loadFile(configPath);
    const profileContent = loadFile(profilePath);
    const systemContext = loadFile(systemContextPath);
    
    // Load latest portfolio updates
    const latestBalances = getLatestFile(updatesDir, /^Balances_for_Account_{account_id}\.csv$/);
    const latestPositions = getLatestPositionsFile(updatesDir);

    // Check file status
    const missingBalances = !latestBalances;
    const missingPositions = !latestPositions;
    const outdatedBalances = latestBalances ? !isFileRecent(latestBalances, 7) : false;
    const outdatedPositions = latestPositions ? !isFileRecent(latestPositions, 7) : false;

    const balancesContent = latestBalances ? loadFile(latestBalances) : '[No balances file found]';
    const positionsContent = latestPositions ? loadFile(latestPositions) : '[No positions file found]';

    // Generate alert if needed
    const updateAlert = generateUpdateAlert(missingBalances, missingPositions, outdatedBalances, outdatedPositions);
    
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
💰 LATEST PORTFOLIO BALANCES
═══════════════════════════════════════════

File: ${latestBalances || 'Not found'}

${balancesContent}

═══════════════════════════════════════════
📊 LATEST PORTFOLIO POSITIONS
═══════════════════════════════════════════

File: ${latestPositions || 'Not found'}

${positionsContent}
${updateAlert}
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
