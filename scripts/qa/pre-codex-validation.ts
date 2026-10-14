#!/usr/bin/env bun

import { existsSync, readFileSync, statSync } from 'fs';
import { join } from 'path';

interface CheckResult {
  name: string;
  passed: boolean;
  message: string;
  severity: 'critical' | 'warning' | 'info';
}

const results: CheckResult[] = [];
const projectRoot = process.cwd();

type Severity = CheckResult['severity'];

function checkFile(path: string, description: string, severity: Severity): void {
  const exists = existsSync(join(projectRoot, path));
  results.push({
    name: description,
    passed: exists,
    message: exists ? `✓ ${path}` : `✗ Missing: ${path}`,
    severity
  });
}

function requireFile(path: string, description: string): void {
  checkFile(path, description, 'critical');
}

function optionalFile(path: string, description: string): void {
  checkFile(path, description, 'warning');
}

function checkDirectory(path: string, description: string, severity: Severity): void {
  const fullPath = join(projectRoot, path);
  const exists = existsSync(fullPath) && statSync(fullPath).isDirectory();
  results.push({
    name: description,
    passed: exists,
    message: exists ? `✓ ${path}/` : `✗ Missing directory: ${path}/`,
    severity
  });
}

function requireDirectory(path: string, description: string): void {
  checkDirectory(path, description, 'critical');
}

function optionalDirectory(path: string, description: string): void {
  checkDirectory(path, description, 'warning');
}

function checkFileContent(path: string, searchString: string, description: string): void {
  const fullPath = join(projectRoot, path);
  if (!existsSync(fullPath)) {
    results.push({
      name: description,
      passed: false,
      message: `✗ Cannot check content: ${path} not found`,
      severity: 'critical'
    });
    return;
  }

  const content = readFileSync(fullPath, 'utf-8');
  const contains = content.includes(searchString);
  results.push({
    name: description,
    passed: contains,
    message: contains
      ? `✓ ${path} contains "${searchString}"`
      : `✗ ${path} missing "${searchString}"`,
    severity: 'warning'
  });
}

console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('🔍 Pre-Codex Validation - Finance Guru™');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log();

console.log('📄 Checking core documentation...');
requireFile('CLAUDE.md', 'CLAUDE.md exists');
requireFile('README.md', 'README.md exists');
requireFile('src/CLAUDE.md', 'src/CLAUDE.md exists (developer guidance)');
requireFile('docs/setup/SETUP.md', 'Setup documentation exists');
optionalFile('docs/setup/TROUBLESHOOTING.md', 'Troubleshooting guide exists');

console.log('🏗️  Checking system architecture...');
requireDirectory('src', 'src/ directory exists');
requireDirectory('src/analysis', 'src/analysis/ exists');
requireDirectory('src/strategies', 'src/strategies/ exists');
requireDirectory('src/utils', 'src/utils/ exists');
requireDirectory('src/models', 'src/models/ exists');
requireDirectory('fin-guru', 'fin-guru/ directory exists');

console.log('🏦 Checking live sync implementation...');
optionalFile('config/snaptrade-accounts.yaml', 'Optional SnapTrade routing config exists');
requireDirectory('src/integrations/snaptrade', 'SnapTrade integration exists');
requireDirectory('src/integrations/simplefin', 'SimpleFIN integration exists');
requireDirectory('apps/simplefin-sync', 'SimpleFIN Bun app exists');

console.log('🔧 Checking tools documentation...');
optionalFile('docs/reference/tools.md', 'Tools documentation exists');

console.log('🤖 Checking agent system...');
requireFile('.claude/agents/fg-finance-orchestrator.md', 'Finance Orchestrator exists');

const requiredAgents = [
  'market-researcher',
  'quant-analyst',
  'strategy-advisor',
  'compliance-officer',
  'margin-specialist',
  'dividend-specialist'
];

requiredAgents.forEach(agent => {
  optionalFile(`.claude/agents/fg-${agent}.md`, `Agent: ${agent}`);
});

console.log('⚙️  Checking configuration files...');
requireFile('pyproject.toml', 'Python project configuration');
optionalFile('package.json', 'Node.js package configuration');
requireFile('.gitignore', '.gitignore exists');

console.log('🧪 Checking test infrastructure...');
optionalDirectory('tests', 'tests/ directory exists');
requireFile('docs/reports/MANUAL_TEST_CHECKLIST.md', 'Manual test checklist exists');

console.log('💡 Checking skills...');
optionalDirectory('.claude/skills', 'Skills directory exists');

console.log('✅ Validating recent task completions...');

checkFileContent('README.md', 'skills', 'README mentions skills/commands installation');

if (existsSync(join(projectRoot, 'src/CLAUDE.md'))) {
  const srcClaude = readFileSync(join(projectRoot, 'src/CLAUDE.md'), 'utf-8');
  results.push({
    name: 'src/CLAUDE.md has developer guidance',
    passed: srcClaude.length > 100,
    message: srcClaude.length > 100
      ? '✓ src/CLAUDE.md contains guidance'
      : '✗ src/CLAUDE.md appears empty or incomplete',
    severity: 'warning'
  });
}

console.log();
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('📊 Validation Results');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log();

const critical = results.filter(r => !r.passed && r.severity === 'critical');
const warnings = results.filter(r => !r.passed && r.severity === 'warning');
const passed = results.filter(r => r.passed);

console.log(`✅ Passed: ${passed.length}`);
console.log(`⚠️  Warnings: ${warnings.length}`);
console.log(`❌ Critical: ${critical.length}`);
console.log();

if (critical.length > 0) {
  console.log('❌ CRITICAL ISSUES:');
  critical.forEach(r => console.log(`   ${r.message}`));
  console.log();
}

if (warnings.length > 0) {
  console.log('⚠️  WARNINGS:');
  warnings.forEach(r => console.log(`   ${r.message}`));
  console.log();
}

console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
if (critical.length === 0 && warnings.length <= 5) {
  console.log('✅ SYSTEM READY FOR CODEX REVIEW');
  console.log();
  console.log('Next step: Run Codex full review (Task 5.2)');
  console.log('   → Create/update a GitHub issue or handoff doc for the review');
  process.exit(0);
} else if (critical.length === 0) {
  console.log('⚠️  SYSTEM MOSTLY READY (warnings exist)');
  console.log();
  console.log('System has warnings but no critical issues.');
  console.log('You may proceed with Codex review or address warnings first.');
  process.exit(0);
} else {
  console.log('❌ SYSTEM NOT READY');
  console.log();
  console.log(`Fix ${critical.length} critical issue(s) before Codex review.`);
  process.exit(1);
}
