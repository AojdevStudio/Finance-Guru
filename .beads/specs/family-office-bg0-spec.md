# Finance Guru User Onboarding and Public Release
**Epic Spec** | Bead: family-office-bg0 | Created: 2026-01-16

---

## Executive Summary

Finance Guru™ is currently hardcoded with Ossie's personal financial data, making it impossible to distribute to other users. This spec outlines the comprehensive transformation required to make Finance Guru a publicly distributable, user-agnostic financial analysis system with an automated onboarding flow.

**Target Audience:**
- New Finance Guru users setting up their own private AI-powered family office
- Developers who want to use Finance Guru for personal financial analysis
- Anyone forking the repository for their own use

**Current State:** Hardcoded personal data in config files, hooks, and templates
**Desired State:** Template-driven system with interactive onboarding CLI that generates personalized configuration

---

## Problem Statement

### Hardcoded Data Locations

Finance Guru currently contains Ossie's personal data in the following locations:

1. **Configuration Files**
   - `fin-guru/config.yaml` - Contains `author: Ossie` and `user_name: Ossie`
   - `fin-guru/data/user-profile.yaml` - 300+ lines of personal financial data including:
     - Portfolio values ($500k)
     - Account structures (Fidelity TOD, 401k, IRA)
     - Specific holdings (PLTR, TSLA, NVDA, etc.)
     - Cash flow details ($25k/month income, $4.5k expenses)
     - Debt profiles (mortgage, student loans, car loans)
     - Investment strategies (margin living, dividend income)
     - Google Sheets IDs for portfolio tracking

2. **Hooks (TypeScript)**
   - `.claude/hooks/load-fin-core-config.ts` - Session start hook that loads config
   - `.claude/hooks/skill-activation-prompt.sh` - Shell wrapper (could be Bun)
   - `.claude/hooks/post-tool-use-tracker.sh` - Shell script (could be Bun)
   - `.claude/settings.json` - Hook registration

3. **Portfolio Data**
   - `notebooks/updates/Balances_for_Account_Z05724592.csv` - Specific Fidelity account
   - `notebooks/updates/Portfolio_Positions_*.csv` - Personal positions
   - File naming patterns expect specific account numbers

4. **Documentation**
   - `fin-guru/data/system-context.md` - References "YOUR private family office"
   - `README.md` - "I built", "my portfolio" language
   - `CLAUDE.md` - Hardcoded project paths and conventions

### Distribution Blockers

**Cannot distribute Finance Guru because:**
1. New users would see Ossie's financial data
2. No mechanism to collect user's financial profile
3. Hooks reference hardcoded file paths
4. No template system for generating user-specific configs
5. Google Sheets integration uses hardcoded spreadsheet IDs
6. `.gitignore` doesn't protect private data directories
7. No setup guide for first-time users

---

## Solution Architecture

### Three-Phase Approach

#### Phase 1: Configuration Templatization
Transform hardcoded configs into templates with placeholder variables.

#### Phase 2: Interactive Onboarding CLI
Build a Bun-based CLI that guides new users through financial assessment and generates personalized configs.

#### Phase 3: Hook Refactoring & Distribution Prep
Convert shell hooks to Bun scripts, update `.gitignore`, create setup documentation.

---

## Detailed Requirements

### 1. Onboarding CLI (`scripts/onboarding/`)

**Tool:** Bun TypeScript CLI
**Entry Point:** `scripts/onboarding/index.ts`

#### 1.1 CLI Structure

```
scripts/onboarding/
├── index.ts                 # Main CLI entry point
├── modules/
│   ├── input-validator.ts   # Validation utilities
│   ├── progress.ts          # Save/resume state management
│   ├── yaml-generator.ts    # Config file generation
│   └── templates/           # Template files
│       ├── user-profile.template.yaml
│       ├── config.template.yaml
│       ├── system-context.template.md
│       └── CLAUDE.template.md
├── sections/
│   ├── liquid-assets.ts     # Section 1: Cash accounts
│   ├── investments.ts       # Section 2: Portfolio
│   ├── cash-flow.ts         # Section 3: Income/expenses
│   ├── debt.ts              # Section 4: Liabilities
│   ├── preferences.ts       # Section 5: Risk/goals
│   ├── mcp-config.ts        # Section 6: MCP server setup
│   └── env-setup.ts         # Section 7: .env file
└── tests/
    ├── validator.test.ts
    ├── generator.test.ts
    └── integration.test.ts
```

#### 1.2 Onboarding Flow

**Welcome Screen:**
```
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║          🏦 Finance Guru™ Setup Wizard                   ║
║                                                          ║
║    Transform Claude into your private family office     ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝

This wizard will guide you through setting up Finance Guru.
We'll collect information about:

  1. Your liquid assets (cash accounts)
  2. Investment portfolio
  3. Monthly cash flow
  4. Debt profile
  5. Investment preferences
  6. MCP server configuration
  7. Environment variables

⏱️  Estimated time: 10-15 minutes
💾 Your progress is auto-saved (resume anytime with --resume)
🔒 All data stays local (never transmitted)

Ready to begin? (Y/n)
```

**Section 1: Liquid Assets**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Section 1 of 7: Liquid Assets
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Let's start with your cash accounts (checking, savings, business accounts).

? What is the total value of your liquid cash? $____
? How many accounts do you have? (checking, savings, business) ___
? What is the average yield on your cash? (e.g., 4.5 for 4.5%) ____%

Would you like to describe your account structure? (optional)
Example: "2 business accounts (LLC A & LLC B), 3 checking, 2 high-yield savings"

[Text input or skip]

✅ Liquid Assets: Complete
```

**Section 2: Investment Portfolio**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 Section 2 of 7: Investment Portfolio
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

? What is your total portfolio value? $____
? Which brokerage do you primarily use? (Fidelity, Schwab, Vanguard, etc.) ____
? Do you have retirement accounts? (401k, IRA) (Y/n)
  → If yes: Estimated total value? $____

? What is your current allocation strategy?
  [ ] Aggressive growth
  [ ] Growth
  [ ] Balanced
  [ ] Conservative
  [ ] Income-focused

? Do you track your portfolio in Google Sheets? (Y/n)
  → If yes: What is your Google Sheets spreadsheet ID?
     (Found in URL: docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit)
     ID: ____

✅ Investment Portfolio: Complete
```

**Section 3: Cash Flow**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 Section 3 of 7: Monthly Cash Flow
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

? After-tax monthly income: $____
? Fixed monthly expenses (mortgage, car, insurance): $____
? Variable monthly expenses (groceries, gas, discretionary): $____
? How much do you currently save/invest per month? $____

→ Calculated investment capacity: $____ per month

✅ Cash Flow: Complete
```

**Section 4: Debt Profile**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏠 Section 4 of 7: Debt Profile
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

? Do you have a mortgage? (Y/n)
  → If yes:
     Balance: $____
     Monthly payment: $____

? Do you have student loans? (Y/n)
  → If yes:
     Balance: $____
     Interest rate: ____%

? Do you have auto loans? (Y/n)
  → If yes:
     Balance: $____
     Interest rate: ____%

? Do you have credit card debt? (Y/n)
  → If yes: Estimated balance: $____

→ Calculated weighted average interest rate: ____%

✅ Debt Profile: Complete
```

**Section 5: Preferences**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 Section 5 of 7: Investment Preferences
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

? What is your risk tolerance?
  [ ] Aggressive (willing to accept high volatility for growth)
  [ ] Moderate (balanced risk/reward)
  [ ] Conservative (capital preservation priority)

? What is your primary investment philosophy?
  [ ] Aggressive growth (maximize capital appreciation)
  [ ] Growth + Income (balance appreciation and dividends)
  [ ] Income-focused (prioritize cash flow)
  [ ] Index investing (passive market exposure)

? What are your main focus areas? (select multiple)
  [ ] Dividend portfolio construction
  [ ] Margin strategies
  [ ] Tax optimization
  [ ] Retirement planning
  [ ] Options trading
  [ ] Real estate investing

? Emergency fund target (months of expenses): ___

✅ Preferences: Complete
```

**Section 6: MCP Server Configuration**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔌 Section 6 of 7: MCP Server Setup
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Finance Guru uses Claude's MCP (Model Context Protocol) servers.
These provide web search, research, and financial data capabilities.

Required MCP servers:
  ✓ exa              (AI-powered search)
  ✓ perplexity       (research and reasoning)
  ✓ sequential-thinking (complex analysis)
  ✓ gdrive           (Google Sheets integration)
  ? context7         (library documentation)

Optional MCP servers:
  ? bright-data      (web scraping, paid)
  ? financial-datasets (market data, requires API key)

? Do you have these MCP servers configured in Claude Code? (Y/n)

→ If no: We'll guide you through setup

For financial-datasets (optional):
? Do you have an Alpha Vantage API key? (free tier available)
  Get one at: https://www.alphavantage.co/support/#api-key
  API Key: ____

✅ MCP Configuration: Complete
```

**Section 7: Environment Variables**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔐 Section 7 of 7: Environment Setup
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Finance Guru uses a .env file for sensitive configuration.

? Your name (used in reports and agent communications): ____
? Preferred language for communication: [English/Spanish/French/etc.]

For Google Sheets integration (if you use it):
? Google Sheets API credentials file path: ____
  (Leave blank to configure later)

✅ Environment Setup: Complete
```

**Final Summary & Confirmation**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 Review Your Configuration
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Portfolio Overview:
  Liquid Assets:        $14,491
  Investment Portfolio: $500,000
  Monthly Income:       $25,000
  Investment Capacity:  $10,500/month

Financial Profile:
  Risk Tolerance:       Aggressive
  Philosophy:           Growth + Income
  Focus Areas:          Dividends, Margin, Tax

Integration:
  Brokerage:           Fidelity
  Google Sheets:       Enabled (ID: 1HtHRP3C...)
  MCP Servers:         5 configured

Files to be created:
  ✓ fin-guru/data/user-profile.yaml
  ✓ fin-guru/config.yaml
  ✓ fin-guru/data/system-context.md
  ✓ CLAUDE.md
  ✓ .env
  ✓ .gitignore (updated)

? Everything look correct? (Y/n)

? Ready to generate your Finance Guru configuration? (Y/n)

[Generating files...]

✅ Configuration generated successfully!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎉 Setup Complete!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Your Finance Guru is now configured.

Next steps:
  1. Start Claude Code in this directory
  2. Finance Guru will auto-load your configuration
  3. Run /finance-orchestrator to activate your AI team

To update your configuration later:
  → Run: bun run scripts/onboarding/index.ts --resume

Documentation:
  → Setup guide: docs/SETUP.md
  → User guide: docs/USER-GUIDE.md
  → Troubleshooting: docs/TROUBLESHOOTING.md

Ready to get started? Open Claude Code and say:
  "Hi, I'm [Your Name]. Let's review my portfolio."
```

#### 1.3 Progress Save/Resume System

**State File:** `.onboarding-state.json` (gitignored)

```json
{
  "version": "1.0",
  "started_at": "2026-01-16T00:24:36Z",
  "last_updated": "2026-01-16T00:30:15Z",
  "completed_sections": ["liquid_assets", "investments"],
  "current_section": "cash_flow",
  "data": {
    "liquid_assets": {
      "total": 14491,
      "accounts_count": 10,
      "average_yield": 0.04
    },
    "investments": {
      "total_value": 500000,
      "primary_brokerage": "Fidelity",
      "has_retirement": true,
      "retirement_value": 200000
    }
  }
}
```

**Resume behavior:**
```bash
$ bun run scripts/onboarding/index.ts --resume

Found existing onboarding session (started 2 days ago)
Completed: Liquid Assets, Investments
Next: Cash Flow

? Resume where you left off? (Y/n)
→ Y: Continue from Cash Flow section
→ n: Start fresh (previous data discarded)
```

#### 1.4 Input Validation

**Validation Module:** `scripts/onboarding/modules/input-validator.ts`

```typescript
// Number validation
validateCurrency(input: string): number | Error
validatePercentage(input: string): number | Error
validatePositiveInteger(input: string): number | Error

// String validation
validateNonEmpty(input: string): string | Error
validateEmail(input: string): string | Error
validateSpreadsheetId(input: string): string | Error

// Range validation
validateRiskTolerance(input: string): 'aggressive' | 'moderate' | 'conservative' | Error
validateInvestmentPhilosophy(input: string): PhilosophyType | Error

// Custom validation
validateBrokerage(input: string): string
// Accepts: "Fidelity", "fidelity", "FIDELITY" → normalizes to "Fidelity"
```

**Validation Rules:**
- Currency: Must be positive number, accepts `$`, `,` formatting
- Percentage: 0-100 range, accepts `%` suffix
- Spreadsheet ID: 44-character alphanumeric (Google Sheets format)
- Risk tolerance: Must be one of the allowed values
- All text inputs: Trim whitespace, prevent empty strings

### 2. Configuration Templates

#### 2.1 User Profile Template

**File:** `scripts/onboarding/modules/templates/user-profile.template.yaml`

```yaml
# Finance Guru™ User Profile Configuration
# Generated: {{timestamp}}
# User: {{user_name}}

system_ownership:
  type: "private_family_office"
  owner: "sole_client"
  mode: "exclusive_service"
  data_location: "local_only"
  repository: "{{repository_name}}"

orientation_status:
  completed: true
  onboarding_version: "1.0"
  completed_at: "{{timestamp}}"
  onboarding_phase: "active"

user_profile:
  liquid_assets:
    total: {{liquid_assets_total}}
    accounts_count: {{liquid_assets_count}}
    average_yield: {{liquid_assets_yield}}
    {{#if liquid_assets_structure}}
    structure: "{{liquid_assets_structure}}"
    {{/if}}

  investment_portfolio:
    total_value: {{portfolio_value}}
    primary_brokerage: "{{brokerage}}"
    {{#if has_retirement}}
    retirement_accounts: {{retirement_value}}
    {{/if}}
    allocation: "{{allocation_strategy}}"
    risk_profile: "{{risk_tolerance}}"

    {{#if google_sheets_id}}
    google_sheets:
      spreadsheet_id: "{{google_sheets_id}}"
      url: "https://docs.google.com/spreadsheets/d/{{google_sheets_id}}/edit"
      purpose: "Finance Guru portfolio tracking"
      last_updated: "{{timestamp}}"
    {{/if}}

  cash_flow:
    monthly_income: {{monthly_income}}
    fixed_expenses: {{fixed_expenses}}
    variable_expenses: {{variable_expenses}}
    current_savings: {{current_savings}}
    investment_capacity: {{investment_capacity}}

  debt_profile:
    {{#if has_mortgage}}
    mortgage_balance: {{mortgage_balance}}
    mortgage_payment: {{mortgage_payment}}
    {{/if}}
    {{#if other_debt}}
    other_debt: {{other_debt}}
    {{/if}}
    weighted_interest_rate: {{weighted_rate}}

  preferences:
    risk_tolerance: "{{risk_tolerance}}"
    investment_philosophy: "{{investment_philosophy}}"
    focus_areas: {{focus_areas}}
    emergency_fund_target: {{emergency_fund_months}}
    time_horizon: "long_term"

opportunities:
  high_priority: []
  medium_priority: []
  strategic: []

recommended_workflows:
  primary: []
  secondary: []
  educational: []

session_context:
  first_interaction: true
  last_command: "onboarding"
  active_workflows: []
  completed_tasks: ["onboarding"]
```

#### 2.2 Config Template

**File:** `scripts/onboarding/modules/templates/config.template.yaml`

```yaml
# Finance Guru™ Module Configuration
# Generated: {{timestamp}}
# User: {{user_name}}

module_name: "Finance Guru™"
module_code: fin-guru
author: {{user_name}}
version: "2.0.0"
description: "Private AI-powered family office system"

user_name: {{user_name}}
communication_language: {{language}}

# [Rest of config.yaml remains unchanged - paths, agents, tools]
```

#### 2.3 System Context Template

**File:** `scripts/onboarding/modules/templates/system-context.template.md`

```markdown
# Finance Guru™ System Context
<!-- Private Family Office Configuration | v1.0 | {{date}} -->

## 🏛️ This is YOUR Private Family Office

### Core Understanding
- Finance Guru™ is {{user_name}}'s personal AI-powered family office
- All agents work exclusively for {{user_name}} - this is not a shared service
- This is NOT an app or product - this IS {{possessive_name}} Finance Guru

### Operational Mode
```yaml
system_type: "private_family_office"
client_model: "single_principal"
service_mode: "exclusive_dedication"
data_sovereignty: "local_only"
external_access: "none"
```

## 👤 Your Financial Profile

Key metrics from {{possessive_name}} assessment:
- Portfolio Value: ${{portfolio_value_formatted}}
- Monthly Income: ${{monthly_income_formatted}}
- Investment Capacity: ${{investment_capacity_formatted}}/month
- Risk Profile: {{risk_tolerance}}
- Focus Areas: {{focus_areas_list}}

[Rest of system-context.md with {{user_name}} replacements]
```

#### 2.4 CLAUDE.md Template

**File:** `scripts/onboarding/modules/templates/CLAUDE.template.md`

```markdown
# CLAUDE.md

Finance Guru™ - {{user_name}}'s private AI-powered family office

*For Claude Code only*: ALWAYS use the `AskUserQuestion` tool when posing questions to the user.

**Key Principle**: This IS {{possessive_name}} Finance Guru (not a product) - a personal financial command center.

[Rest of CLAUDE.md remains largely unchanged]
```

#### 2.5 .env Template

```bash
# Finance Guru Environment Configuration
# Generated: {{timestamp}}

# User Configuration
USER_NAME="{{user_name}}"
COMMUNICATION_LANGUAGE="{{language}}"

# MCP Server Configuration
{{#if has_alphavantage}}
ALPHA_VANTAGE_API_KEY="{{alphavantage_key}}"
{{/if}}

{{#if has_brightdata}}
BRIGHT_DATA_API_KEY="{{brightdata_key}}"
{{/if}}

# Google Sheets Integration
{{#if google_sheets_credentials}}
GOOGLE_SHEETS_CREDENTIALS_PATH="{{google_sheets_credentials}}"
{{/if}}

# Portfolio Tracking
{{#if brokerage_account}}
PRIMARY_BROKERAGE="{{brokerage}}"
BROKERAGE_ACCOUNT_NUMBER="{{account_number}}"
{{/if}}

# System Paths (auto-detected, edit if needed)
PROJECT_ROOT="{{project_root}}"
FIN_GURU_PATH="{{project_root}}/fin-guru"
NOTEBOOKS_PATH="{{project_root}}/notebooks"
```

### 3. Hook Refactoring (Shell → Bun)

#### 3.1 Current Hooks (Shell-based)

**To Refactor:**
- `.claude/hooks/load-fin-core-config.ts` (already TypeScript, check for improvements)
- `.claude/hooks/skill-activation-prompt.sh` → Convert to Bun
- `.claude/hooks/post-tool-use-tracker.sh` → Convert to Bun

**Goal:** All hooks should be Bun TypeScript scripts for consistency, speed, and maintainability.

#### 3.2 Refactored Hook Structure

**Hook:** `load-fin-core-config.ts` (already exists, verify works with templates)

**Hook:** `skill-activation-prompt.ts` (new)

```typescript
#!/usr/bin/env bun

/**
 * Skill Activation Prompt Hook
 * Suggests relevant Finance Guru skills based on user query
 */

import { readFileSync } from 'fs';
import { join } from 'path';

interface HookInput {
  user_message: string;
  session_id: string;
}

interface SkillMapping {
  keywords: string[];
  skill: string;
  description: string;
}

const SKILL_MAPPINGS: SkillMapping[] = [
  {
    keywords: ['report', 'pdf', 'analysis', 'ticker'],
    skill: 'FinanceReport',
    description: 'Generate institutional-quality PDF reports'
  },
  {
    keywords: ['dividend', 'income', 'yield', 'distribution'],
    skill: 'dividend-tracking',
    description: 'Sync dividend data from Fidelity CSV'
  },
  // ... more mappings
];

function detectSkills(message: string): SkillMapping[] {
  const lowerMessage = message.toLowerCase();
  return SKILL_MAPPINGS.filter(mapping =>
    mapping.keywords.some(keyword => lowerMessage.includes(keyword))
  );
}

function main() {
  const input: HookInput = JSON.parse(process.argv[2] || '{}');
  const detectedSkills = detectSkills(input.user_message);

  if (detectedSkills.length === 0) {
    console.log(''); // No skills detected, no output
    return;
  }

  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('🎯 SKILL ACTIVATION CHECK');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log();
  console.log('📚 RECOMMENDED SKILLS:');
  detectedSkills.forEach(skill => {
    console.log(`  → ${skill.skill}`);
  });
  console.log();
  console.log('ACTION: Use Skill tool BEFORE responding');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
}

main();
```

**Hook:** `post-tool-use-tracker.ts` (new)

```typescript
#!/usr/bin/env bun

/**
 * Post-Tool Use Tracker
 * Logs tool usage for analytics and debugging
 */

import { appendFileSync, mkdirSync } from 'fs';
import { join } from 'path';

interface HookInput {
  tool_name: string;
  tool_params: Record<string, any>;
  session_id: string;
  timestamp: string;
}

function main() {
  const input: HookInput = JSON.parse(process.argv[2] || '{}');

  const logDir = join(process.cwd(), '.finance-guru', 'logs');
  mkdirSync(logDir, { recursive: true });

  const logFile = join(logDir, `tool-usage-${new Date().toISOString().split('T')[0]}.jsonl`);

  appendFileSync(logFile, JSON.stringify(input) + '\n');

  // Silent success (no output to user)
}

main();
```

#### 3.3 Updated .claude/settings.json

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bun run $CLAUDE_PROJECT_DIR/.claude/hooks/load-fin-core-config.ts"
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bun run $CLAUDE_PROJECT_DIR/.claude/hooks/skill-activation-prompt.ts '{\"user_message\": \"$USER_MESSAGE\", \"session_id\": \"$SESSION_ID\"}'"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bun run $CLAUDE_PROJECT_DIR/.claude/hooks/post-tool-use-tracker.ts '{\"tool_name\": \"$TOOL_NAME\", \"tool_params\": $TOOL_PARAMS, \"session_id\": \"$SESSION_ID\", \"timestamp\": \"$TIMESTAMP\"}'"
          }
        ]
      }
    ]
  }
}
```

### 4. .gitignore Updates

**File:** `.gitignore` (append to existing)

```bash
# Finance Guru Private Data
# CRITICAL: These directories contain personal financial information
# DO NOT commit these files to public repositories

# User-generated configuration (contains personal data)
fin-guru/data/user-profile.yaml
fin-guru/config.yaml
fin-guru/data/system-context.md
CLAUDE.md
.env

# Onboarding state (resume data)
.onboarding-state.json

# Financial data exports
notebooks/updates/*.csv
notebooks/updates/*.xlsx

# Private documentation (user-specific strategies)
fin-guru-private/

# Analytics logs (may contain sensitive queries)
.finance-guru/logs/

# Google Sheets credentials
google-sheets-credentials.json
credentials.json
token.json

# Brokerage statements
statements/
reports/*.pdf

# Keep sample/template files
!fin-guru/data/user-profile.template.yaml
!fin-guru/config.template.yaml
!scripts/onboarding/modules/templates/*.template.*
```

**CRITICAL:** Add prominent warning in README.md

```markdown
## ⚠️ Privacy Warning

**BEFORE COMMITTING TO GITHUB:**

Finance Guru stores your personal financial data locally. After onboarding:
- `fin-guru/data/user-profile.yaml` contains your portfolio details
- `notebooks/updates/` contains your account exports
- `.env` contains API keys

These files are automatically gitignored, but **double-check** before pushing:

```bash
git status --ignored  # Verify private files are ignored
```

**Fork Model:**
1. Fork this repository
2. Clone to your machine
3. Run onboarding: `bun run scripts/onboarding/index.ts`
4. Your private data stays local (never committed)
5. Pull upstream updates safely (configs in .gitignore)
```

### 5. Documentation

#### 5.1 Setup Guide

**File:** `docs/SETUP.md`

```markdown
# Finance Guru Setup Guide

## Prerequisites

- **Claude Code** (latest version)
- **Bun** (for running scripts and hooks)
- **Python 3.12+** with `uv` (for analysis tools)
- **Git** (for version control)

## Installation

### 1. Fork the Repository

```bash
# Fork via GitHub UI, then clone
git clone https://github.com/YOUR-USERNAME/family-office.git
cd family-office
```

### 2. Install Dependencies

```bash
# Python dependencies
uv sync

# Bun dependencies (for hooks and onboarding)
bun install
```

### 3. Run Onboarding Wizard

```bash
bun run scripts/onboarding/index.ts
```

Follow the interactive prompts to configure your Finance Guru.

### 4. Configure MCP Servers

Finance Guru requires these MCP servers in Claude Code:

**Required:**
- `exa` - AI-powered search
- `perplexity` - Research and reasoning
- `gdrive` - Google Sheets integration

**Optional:**
- `bright-data` - Web scraping (paid)
- `financial-datasets` - Market data (requires API key)

Add to your Claude Code MCP configuration:

```json
{
  "mcpServers": {
    "exa": { "command": "npx", "args": ["-y", "@exa/mcp-server"] },
    "perplexity": { "command": "npx", "args": ["-y", "@perplexity/mcp-server"] },
    "gdrive": { "command": "npx", "args": ["-y", "@google/gdrive-mcp"] }
  }
}
```

### 5. Test Installation

```bash
# Start Claude Code in this directory
claude-code .

# In Claude Code, run:
/finance-orchestrator

# You should see Finance Guru activate with your profile loaded
```

## Troubleshooting

[Common issues and solutions]
```

#### 5.2 Fork Model README Section

**File:** `README.md` (add new section after "Installation")

```markdown
## 🍴 Fork Model: Use Finance Guru Safely

Finance Guru is designed to be **forked** and used privately. Here's how it works:

### Architecture for Privacy

```
┌─────────────────────────────────────────┐
│  Public Repository (GitHub)             │
│  ✓ Tools, agents, templates             │
│  ✓ Documentation                         │
│  ✓ Sample configs                        │
│  ✗ NO personal financial data            │
└─────────────────────────────────────────┘
           ↓ Fork & Clone
┌─────────────────────────────────────────┐
│  Your Local Fork                         │
│  ✓ All public features                   │
│  ✓ Your onboarding-generated configs     │
│  ✓ Your portfolio data (gitignored)      │
│  ✓ Your API keys (.env, gitignored)      │
└─────────────────────────────────────────┘
```

### How to Use

1. **Fork this repository** to your GitHub account
2. **Clone to your machine** (never commit personal data)
3. **Run onboarding** to generate your private configs
4. **Pull upstream updates** safely (configs in .gitignore)

### What's Tracked vs. Ignored

**Tracked (safe to commit):**
- ✅ Tools (`src/`, `scripts/`)
- ✅ Agent definitions (`fin-guru/agents/`)
- ✅ Templates (`scripts/onboarding/modules/templates/`)
- ✅ Documentation (`docs/`, `README.md`)
- ✅ Package files (`pyproject.toml`, `package.json`)

**Ignored (private data):**
- 🔒 `fin-guru/data/user-profile.yaml` (your financial data)
- 🔒 `notebooks/updates/*.csv` (your account exports)
- 🔒 `.env` (your API keys)
- 🔒 `fin-guru-private/` (your private strategies)

### Updating Your Fork

```bash
# Add upstream remote (one-time)
git remote add upstream https://github.com/ORIGINAL-AUTHOR/family-office.git

# Pull updates (safe - won't touch your private configs)
git fetch upstream
git merge upstream/main

# Your private data stays untouched
```

### Security Checklist

Before pushing to GitHub:

```bash
# Verify private files are ignored
git status --ignored

# Ensure no sensitive data in commit
git diff --cached

# Check .env is ignored
ls -la .env  # Should show file exists locally
git check-ignore .env  # Should output ".env" (confirmed ignored)
```
```

### 6. Testing Requirements

#### 6.1 Unit Tests

**File:** `scripts/onboarding/tests/validator.test.ts`

```typescript
import { describe, test, expect } from 'bun:test';
import { validateCurrency, validatePercentage, validateSpreadsheetId } from '../modules/input-validator';

describe('Input Validation', () => {
  test('validateCurrency accepts valid formats', () => {
    expect(validateCurrency('10000')).toBe(10000);
    expect(validateCurrency('$10,000')).toBe(10000);
    expect(validateCurrency('10000.50')).toBe(10000.50);
  });

  test('validateCurrency rejects invalid formats', () => {
    expect(() => validateCurrency('-100')).toThrow();
    expect(() => validateCurrency('abc')).toThrow();
  });

  test('validatePercentage handles percentage formats', () => {
    expect(validatePercentage('4.5')).toBe(4.5);
    expect(validatePercentage('4.5%')).toBe(4.5);
    expect(validatePercentage('100')).toBe(100);
  });

  test('validateSpreadsheetId validates Google Sheets ID format', () => {
    const validId = '1HtHRP3CbnOePb8RQ0RwzFYOQxk0uWC6L8ZMJeQYfWk4';
    expect(validateSpreadsheetId(validId)).toBe(validId);

    expect(() => validateSpreadsheetId('short-id')).toThrow();
  });
});
```

**File:** `scripts/onboarding/tests/generator.test.ts`

```typescript
import { describe, test, expect } from 'bun:test';
import { generateUserProfile, generateConfig } from '../modules/yaml-generator';

describe('YAML Generation', () => {
  test('generateUserProfile creates valid YAML', () => {
    const data = {
      user_name: 'TestUser',
      liquid_assets_total: 10000,
      portfolio_value: 100000,
      // ... other fields
    };

    const yaml = generateUserProfile(data);
    expect(yaml).toContain('user_name: TestUser');
    expect(yaml).toContain('total: 10000');
    expect(yaml).toContain('total_value: 100000');
  });

  test('generateConfig includes user customization', () => {
    const data = {
      user_name: 'TestUser',
      language: 'English'
    };

    const yaml = generateConfig(data);
    expect(yaml).toContain('author: TestUser');
    expect(yaml).toContain('communication_language: English');
  });
});
```

#### 6.2 Integration Tests

**File:** `scripts/onboarding/tests/integration.test.ts`

```typescript
import { describe, test, expect, beforeEach, afterEach } from 'bun:test';
import { existsSync, rmSync, readFileSync } from 'fs';
import { join } from 'path';
import { $ } from 'bun';

describe('Onboarding Integration', () => {
  const testDir = join(process.cwd(), 'test-finance-guru');

  beforeEach(() => {
    // Set up test directory
    if (!existsSync(testDir)) {
      mkdirSync(testDir, { recursive: true });
    }
  });

  afterEach(() => {
    // Clean up test directory
    if (existsSync(testDir)) {
      rmSync(testDir, { recursive: true, force: true });
    }
  });

  test('Full onboarding flow generates all required files', async () => {
    // Simulate onboarding with test data
    process.env.TEST_MODE = 'true';
    process.env.TEST_DIR = testDir;

    await $`bun run scripts/onboarding/index.ts --test`;

    // Verify files were created
    expect(existsSync(join(testDir, 'fin-guru/data/user-profile.yaml'))).toBe(true);
    expect(existsSync(join(testDir, 'fin-guru/config.yaml'))).toBe(true);
    expect(existsSync(join(testDir, '.env'))).toBe(true);
    expect(existsSync(join(testDir, 'CLAUDE.md'))).toBe(true);
  });

  test('Resume functionality preserves progress', async () => {
    // Start onboarding, quit after section 2
    // ...

    // Resume and verify section 2 data is preserved
    // ...
  });

  test('Generated configs are valid YAML', () => {
    // Run onboarding
    // ...

    // Parse generated files
    const userProfile = readFileSync(join(testDir, 'fin-guru/data/user-profile.yaml'), 'utf-8');
    const parsed = YAML.parse(userProfile);

    expect(parsed.user_profile).toBeDefined();
    expect(parsed.user_profile.liquid_assets).toBeDefined();
  });
});
```

#### 6.3 Test Script

**File:** `scripts/onboarding/tests/run-tests.sh`

```bash
#!/bin/bash
# Master test runner for Finance Guru onboarding

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 Finance Guru Onboarding Test Suite"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
echo "1️⃣  Running unit tests..."
bun test scripts/onboarding/tests/validator.test.ts
bun test scripts/onboarding/tests/generator.test.ts

echo ""
echo "2️⃣  Running integration tests..."
bun test scripts/onboarding/tests/integration.test.ts

echo ""
echo "3️⃣  Testing hook refactors..."
bun run .claude/hooks/load-fin-core-config.ts
bun run .claude/hooks/skill-activation-prompt.ts '{"user_message": "test", "session_id": "test"}'

echo ""
echo "✅ All tests passed!"
```

---

## Implementation Plan

### Phase 1: Infrastructure (Tasks 1-3)
1. **Task bg0.1**: Create onboarding CLI structure
   - Set up Bun project in `scripts/onboarding/`
   - Create module files (input-validator, progress, yaml-generator)
   - Define TypeScript interfaces

2. **Task bg0.2-bg0.6**: Implement onboarding sections
   - Build each section's CLI prompts
   - Implement input validation for each section
   - Create progress save/resume logic

3. **Task bg0.7**: Onboarding summary & confirmation
   - Display review screen
   - Generate configuration files from templates

### Phase 2: Configuration System (Tasks 8-10)
4. **Task bg0.8**: CLAUDE.md template system
   - Create template with placeholders
   - Implement variable substitution

5. **Task bg0.9**: Interactive .env setup
   - Prompt for environment variables
   - Generate .env file safely

6. **Task bg0.10**: MCP.json generation
   - Detect installed MCP servers
   - Guide user through configuration

### Phase 3: Hook Refactoring (Tasks 11-14)
7. **Task bg0.11-bg0.13**: Refactor hooks to Bun
   - Convert load-fin-core-config to Bun (verify existing)
   - Convert skill-activation-prompt.sh to TypeScript
   - Convert post-tool-use-tracker.sh to TypeScript

8. **Task bg0.14**: Bun hook test suite
   - Write tests for each hook
   - Verify hooks work in Claude Code

### Phase 4: Cleanup & Documentation (Tasks 15-18)
9. **Task bg0.15**: Remove hardcoded "Ossie" references
   - Scan all files for hardcoded names
   - Replace with template variables
   - Verify all personal data is in templates

10. **Task bg0.16**: Update .gitignore
    - Add private data directories
    - Add warning comments
    - Verify files are ignored

11. **Task bg0.17**: Fork model README section
    - Document fork workflow
    - Add security checklist
    - Explain privacy model

12. **Task bg0.18**: Comprehensive setup guide
    - Write SETUP.md
    - Document prerequisites
    - Troubleshooting section

### Phase 5: Testing & Validation (Tasks 19-21)
13. **Task bg0.19**: Integration test: Full setup flow
    - Test end-to-end onboarding
    - Verify all files generated correctly
    - Test with sample data

14. **Task bg0.20**: Integration test: Onboarding resume
    - Test progress save/resume
    - Verify state persistence

15. **Task bg0.21**: Master test runner
    - Create run-tests.sh script
    - Automate full test suite
    - CI/CD integration (future)

---

## Acceptance Criteria

### For Epic (family-office-bg0)

**User can:**
1. ✅ Fork Finance Guru repository to their GitHub account
2. ✅ Clone the fork locally without seeing Ossie's personal data
3. ✅ Run onboarding CLI: `bun run scripts/onboarding/index.ts`
4. ✅ Complete interactive financial assessment (7 sections)
5. ✅ Save progress mid-onboarding and resume later
6. ✅ Generate personalized configuration files automatically
7. ✅ Start Claude Code and see their Finance Guru activate with their profile
8. ✅ Update configuration by re-running onboarding with `--resume`

**System ensures:**
1. ✅ No hardcoded personal data in public files
2. ✅ All user-generated configs are gitignored
3. ✅ Hooks work with template-based configs
4. ✅ Pull upstream updates without conflicts
5. ✅ All tests pass (unit + integration)
6. ✅ Documentation is complete and accurate
7. ✅ Privacy warnings are prominent

### Validation Tests

**Test 1: Fresh Setup**
```bash
# Fork repository
git clone https://github.com/NEW-USER/family-office.git test-setup
cd test-setup

# Verify no personal data visible
grep -r "Ossie" .  # Should only find in git history
cat fin-guru/data/user-profile.template.yaml  # Should see placeholders

# Run onboarding
bun run scripts/onboarding/index.ts

# Verify files generated
ls fin-guru/data/user-profile.yaml  # Should exist
cat fin-guru/config.yaml | grep "author:"  # Should show NEW-USER's name

# Start Claude Code
claude-code .
# Test: Run /finance-orchestrator, verify NEW-USER's profile loads
```

**Test 2: Resume Onboarding**
```bash
# Start onboarding
bun run scripts/onboarding/index.ts
# Answer sections 1-2, then Ctrl+C to quit

# Verify state saved
cat .onboarding-state.json  # Should show progress

# Resume
bun run scripts/onboarding/index.ts --resume
# Verify sections 1-2 are skipped, starts at section 3
```

**Test 3: Pull Upstream Updates**
```bash
# User has completed onboarding (private configs exist)
ls -la fin-guru/data/user-profile.yaml  # Exists

# Simulate upstream update
git remote add upstream https://github.com/ORIGINAL-AUTHOR/family-office.git
git fetch upstream

# Create mock update in test
echo "# New tool" >> src/utils/new-tool.py
git add src/utils/new-tool.py
git commit -m "Add new tool"

# Merge
git merge upstream/main

# Verify private configs untouched
git status  # Should not show changes to user-profile.yaml
```

**Test 4: Privacy Check**
```bash
# After onboarding, attempt to commit personal data
git add fin-guru/data/user-profile.yaml
git status
# Should NOT appear in staged files (gitignored)

# Verify .env ignored
git add .env
git status
# Should NOT appear in staged files (gitignored)

# Verify all tests pass
bun run scripts/onboarding/tests/run-tests.sh
# Should output: ✅ All tests passed!
```

---

## Dependencies

**External Dependencies:**
- Bun (for CLI and hooks)
- Python 3.12+ with `uv` (for analysis tools)
- Claude Code (runtime environment)
- MCP servers (exa, perplexity, gdrive, etc.)

**Internal Dependencies:**
- Templates must be created before generator can use them
- Hooks must work with template-based configs
- `.gitignore` must be updated before users commit

**Blocked By:**
- None (all tasks are ready to start)

**Blocks:**
- Public distribution of Finance Guru
- Future enhancements (multi-user setups, cloud deployment)

---

## Success Metrics

**Primary Goals:**
1. ✅ Finance Guru can be safely forked and used by anyone
2. ✅ Onboarding takes <15 minutes
3. ✅ Zero personal data leaks to public repository
4. ✅ Users can pull upstream updates without conflicts

**Secondary Goals:**
1. ✅ 100% test coverage for onboarding logic
2. ✅ Documentation is comprehensive and beginner-friendly
3. ✅ Onboarding CLI has <5% error rate

---

## Future Enhancements (Out of Scope)

**Not included in this spec:**
- Web-based onboarding UI (CLI only for v1.0)
- Cloud deployment (local-only for now)
- Multi-user support (single-user assumption)
- Automatic brokerage data import (manual CSV exports)
- Mobile app (desktop-first)
- Encrypted backups (user responsible for backups)

---

## Timeline Estimate

**Rough Breakdown:**
- Phase 1 (Infrastructure): 5-7 days
- Phase 2 (Configuration): 3-4 days
- Phase 3 (Hook Refactoring): 2-3 days
- Phase 4 (Documentation): 2-3 days
- Phase 5 (Testing): 3-4 days

**Total:** ~15-21 days (assuming 1 developer, full-time)

**Critical Path:**
1. CLI structure (bg0.1)
2. Sections 1-6 (bg0.2-bg0.7) [can be parallelized]
3. Hook refactoring (bg0.11-bg0.13)
4. Testing (bg0.19-bg0.21)

---

## Questions & Decisions

**Open Questions:**
1. Should onboarding support importing from existing financial apps (Mint, YNAB)?
   - **Decision:** No, out of scope for v1.0 (manual entry only)

2. Should we include sample data for testing?
   - **Decision:** Yes, create `fin-guru/data/user-profile.sample.yaml`

3. Should onboarding validate Google Sheets access?
   - **Decision:** Yes, test connection and create spreadsheet if needed

4. Should we support multiple languages in onboarding?
   - **Decision:** English only for v1.0, add i18n later

**Decisions Made:**
- ✅ Use Bun for CLI (TypeScript, fast, modern)
- ✅ Template engine: Simple variable substitution (no Handlebars/Mustache)
- ✅ Progress save format: JSON (.onboarding-state.json)
- ✅ Hook language: Bun TypeScript (consistent with CLI)
- ✅ Testing framework: Bun's built-in test runner

---

## Related Beads

**Parent:** family-office-bg0 (this spec)

**Children:**
- family-office-bg0.1: Create Onboarding CLI Script Structure
- family-office-bg0.2: Implement Liquid Assets Section
- family-office-bg0.3: Implement Investment Portfolio Section
- family-office-bg0.4: Implement Cash Flow Section
- family-office-bg0.5: Implement Debt Profile Section
- family-office-bg0.6: Implement Preferences Section
- family-office-bg0.7: Implement Onboarding Summary & Confirmation
- family-office-bg0.8: Implement CLAUDE.md Template System
- family-office-bg0.9: Implement Interactive .env Setup
- family-office-bg0.10: Implement MCP.json Generation
- family-office-bg0.11: Refactor load-fin-core-config Hook to Bun
- family-office-bg0.12: Refactor skill-activation-prompt Hook to Bun
- family-office-bg0.13: Refactor post-tool-use-tracker Hook to Bun
- family-office-bg0.14: Create Bun Hook Test Suite
- family-office-bg0.15: Remove Hardcoded "Ossie" References
- family-office-bg0.16: Update .gitignore for Private Data Protection
- family-office-bg0.17: Write Fork Model README Section
- family-office-bg0.18: Write Comprehensive Setup Guide
- family-office-bg0.19: Create Integration Test: Full Setup Flow
- family-office-bg0.20: Create Integration Test: Onboarding Resume
- family-office-bg0.21: Create Master Test Runner Script

**Related Documentation:**
- `README.md` - Fork model section
- `docs/SETUP.md` - Setup guide
- `.gitignore` - Privacy protection

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-16 | Claude (RBP) | Initial spec created from epic requirements |

---

## Appendix

### A. Example Onboarding Session (Abbreviated)

```
$ bun run scripts/onboarding/index.ts

╔══════════════════════════════════════════╗
║                                          ║
║      🏦 Finance Guru™ Setup Wizard       ║
║                                          ║
╚══════════════════════════════════════════╝

Ready to begin? Y

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Section 1 of 7: Liquid Assets
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

? Total liquid cash: $25000
? Number of accounts: 5
? Average yield: 4.2%

✅ Liquid Assets: Complete

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 Section 2 of 7: Investment Portfolio
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

? Total portfolio value: $750000
? Primary brokerage: Fidelity
? Retirement accounts: Y
  → Value: $300000
? Allocation strategy: Aggressive growth
? Track in Google Sheets: Y
  → Spreadsheet ID: 1HtHRP3C...

✅ Investment Portfolio: Complete

[... sections 3-7 ...]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 Review Your Configuration
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Portfolio Overview:
  Liquid Assets:        $25,000
  Investment Portfolio: $750,000
  Monthly Income:       $30,000

? Everything correct? Y

[Generating files...]

✅ Setup Complete!

Next: Start Claude Code and run /finance-orchestrator
```

### B. File Tree After Onboarding

```
family-office/
├── fin-guru/
│   ├── config.yaml                    # ✅ Generated (user-specific)
│   └── data/
│       ├── user-profile.yaml          # ✅ Generated (user-specific)
│       ├── system-context.md          # ✅ Generated (user-specific)
│       └── *.template.yaml            # 📄 Templates (tracked)
├── scripts/
│   └── onboarding/
│       ├── index.ts                   # 📄 CLI entry (tracked)
│       ├── modules/                   # 📄 Modules (tracked)
│       └── tests/                     # 📄 Tests (tracked)
├── .claude/
│   ├── hooks/
│   │   ├── load-fin-core-config.ts   # 📄 Hook (tracked)
│   │   ├── skill-activation-prompt.ts# 📄 Hook (tracked)
│   │   └── post-tool-use-tracker.ts  # 📄 Hook (tracked)
│   └── settings.json                  # 📄 Hook config (tracked)
├── .env                               # ✅ Generated (GITIGNORED)
├── .onboarding-state.json             # ✅ Progress state (GITIGNORED)
├── CLAUDE.md                          # ✅ Generated (GITIGNORED)
├── .gitignore                         # 📄 Updated (tracked)
└── README.md                          # 📄 Updated (tracked)

Legend:
📄 Tracked in Git (public, safe to commit)
✅ Generated by onboarding (private, gitignored)
```

---

**END OF SPECIFICATION**
