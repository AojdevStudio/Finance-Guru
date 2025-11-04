#!/usr/bin/env tsx

/**
 * Finance Guru Core Config Loader
 * Session Start Hook
 * 
 * Automatically loads Finance Guru system context at session start:
 * - System configuration (config.yaml)
 * - User profile (user-profile.yaml) 
 * - Latest portfolio updates (balances, positions)
 * - fin-core skill content
 */

import { readFileSync, readdirSync, statSync } from 'fs';
import { join, resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

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
    const latestBalances = getLatestFile(updatesDir, /^Balances.*\.csv$/);
    const latestPositions = getLatestFile(updatesDir, /^Portfolio_Positions.*\.csv$/);
    
    const balancesContent = latestBalances ? loadFile(latestBalances) : '[No balances file found]';
    const positionsContent = latestPositions ? loadFile(latestPositions) : '[No positions file found]';
    
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
