---
title: "Finance Guru Public Release Tasks"
status: backlog
created: 2026-01-10
updated: 2026-02-02
author: "{user_name}"
spec_id: task
version: "1.0.0"
description: "Task checklist for preparing Finance Guru for public sharing and new user onboarding"
tags:
  - finance-guru
  - public-release
  - tasks
  - onboarding
references:
  - finance-guru-user-onboarding-and-public-release.md
supersedes: []
diagrams:
  human: ""
  machine: ""
---

# Finance Guru Public Release Tasks

---

## CRITICAL: EXECUTION PROTOCOL

Before starting any tasks, follow this protocol:

1. **Read this entire document first** - understand the full scope
2. **Work through tasks sequentially** - dependencies exist between phases
3. **Be autonomous** - make decisions, don't ask for clarification unless blocked
4. **Document changes** - update relevant docs as you go
5. **Final step is Codex review** - run `/ask-codex` for full codebase review at the end
6. **Accept and fix all Codex feedback** - iterate until Codex passes

---

## Phase 1: Setup Script Enhancement

### 1.1 Load Finance Guru Agent Commands

**Goal:** Setup script should copy agent commands to user's .claude/commands directory

**Tasks:**
- [ ] Modify `setup.sh` to copy `fin-guru/agents/*.md` files to `.claude/commands/fin-guru/agents/`
- [ ] Ensure directory structure is created: `.claude/commands/fin-guru/agents/`
- [ ] Copy these agent command files:
  - `finance-orchestrator.md`
  - `market-researcher.md`
  - `quant-analyst.md`
  - `strategy-advisor.md`
  - `compliance-officer.md`
  - `margin-specialist.md`
  - `dividend-specialist.md`
  - `teaching-specialist.md`
  - `onboarding-specialist.md`
  - `builder.md`
  - `qa-advisor.md`

**Acceptance Criteria:**
- After running setup.sh, user can invoke `/fin-guru:agents:finance-orchestrator`
- All agent commands are accessible via slash commands

### 1.2 Load Finance Guru Skills

**Goal:** Setup script should copy skills to user's .claude/skills directory

**Tasks:**
- [ ] Modify `setup.sh` to copy skill directories to `.claude/skills/`
- [ ] Copy these skill directories (with all contents):
  - `dividend-tracking/`
  - `FinanceReport/`
  - `margin-management/`
  - `MonteCarlo/`
  - `PortfolioSyncing/`
  - `retirement-syncing/`
  - `transaction-syncing/`
- [ ] Update `skill-rules.json` to include activation rules for all copied skills
- [ ] Ensure skills auto-activate based on keywords/intent patterns

**Source Location:** `.claude/skills/` (current project)
**Target Location:** User's `~/.claude/skills/` or project `.claude/skills/`

**Acceptance Criteria:**
- Skills load when relevant keywords are mentioned
- skill-rules.json has entries for all Finance Guru skills

### 1.3 Update README for Skills/Commands Installation

**Goal:** Document how setup.sh installs commands and skills

**Tasks:**
- [ ] Add section to README.md explaining what setup.sh installs
- [ ] List all agent commands that become available
- [ ] List all skills that get installed
- [ ] Explain skill auto-activation behavior

---

## Phase 2: Documentation Restructuring

### 2.1 Move Python Tools Documentation

**Goal:** Move python-tools.md to public docs directory

**Tasks:**
- [ ] Move `.claude/tools/python-tools.md` to `docs/tools.md`
- [ ] Update any references to the old location
- [ ] Add "Coming Soon" roadmap section to the tools doc

**Roadmap Items to Add:**
- Options pricing enhancements
- Real-time data streaming
- Portfolio alerts/notifications
- Multi-broker support
- Tax-loss harvesting automation
- Dividend reinvestment optimization

### 2.2 Create Strategic CLAUDE.md Files

**Goal:** Add CLAUDE.md files to help developers understand each area

**Tasks:**
- [ ] Create `src/CLAUDE.md` with:
  - Overview of the 3-layer architecture (Pydantic → Calculator → CLI)
  - Guide to adding new CLI tools
  - Testing patterns
  - Common imports and utilities
  - Link to docs/api.md for full reference

**Note:** Do NOT create CLAUDE.md in scripts/ - that folder is gitignored (private)

**Acceptance Criteria:**
- Developer opening src/ folder immediately understands the structure
- Clear guidance on how to extend the codebase

---

## Phase 3: Notebooks Folder Structure

### 3.1 Update Setup Script for Notebooks

**Goal:** Create correct notebook folder structure for new users

**Tasks:**
- [ ] Ensure `setup.sh` creates `notebooks/` directory
- [ ] Create `notebooks/updates/` for CSV exports (Fidelity, etc.)
- [ ] Do NOT create `notebooks/tools-needed/` (this is private development folder)
- [ ] Add `.gitkeep` files to preserve empty directories in git

**Required Folder Structure:**
```
notebooks/
├── updates/           # User uploads broker CSV exports here
│   └── .gitkeep
└── retirement-accounts/  # For retirement account CSVs
    └── .gitkeep
```

**Acceptance Criteria:**
- Fresh clone + setup.sh creates correct structure
- No private/development folders exposed

---

## Phase 4: Onboarding Specialist Enhancement

### 4.1 Evaluate Current Onboarding Flow

**Goal:** Ensure onboarding specialist can confidently onboard new clients

**Tasks:**
- [ ] Review `fin-guru/agents/onboarding-specialist.md`
- [ ] Identify gaps in current onboarding flow
- [ ] Document what information is currently collected

### 4.2 Add Multi-Broker Support

**Goal:** Handle CSV formats from different brokers

**Current Support:** Fidelity only

**Brokers to Support:**
- [ ] Fidelity (current)
- [ ] TD Ameritrade / Charles Schwab
- [ ] Robinhood
- [ ] Vanguard
- [ ] E*TRADE
- [ ] Interactive Brokers

**Tasks:**
- [ ] Update onboarding to ASK user which broker they use
- [ ] Create broker-specific CSV mapping configurations
- [ ] Store broker preference in user-profile.yaml
- [ ] Update parsing skills to use broker-specific mappings

**Add to user-profile.yaml:**
```yaml
broker_configuration:
  primary_broker: "fidelity"  # or schwab, robinhood, vanguard, etc.
  csv_mappings:
    positions_file: "Portfolio_Positions_*.csv"
    balances_file: "Balances_*.csv"
    transactions_file: "History_*.csv"
  column_mappings:
    ticker: "Symbol"
    quantity: "Quantity"
    price: "Last Price"
    cost_basis: "Cost Basis Total"
```

### 4.3 Document Required CSV Uploads

**Goal:** Tell user exactly what files to upload

**Tasks:**
- [ ] Update onboarding flow to request these CSV types:
  1. **Portfolio Positions** - Current holdings with quantities, prices, cost basis
  2. **Account Balances** - Cash, margin, buying power
  3. **Transaction History** - Buys, sells, dividends, transfers
- [ ] Create `fin-guru/data/csv-requirements.md` documenting:
  - What each CSV type contains
  - Where to download from each broker
  - Example file naming patterns
  - Required columns per CSV type
- [ ] Add CSV upload instructions to onboarding flow

**Onboarding Questions to Add:**
1. "Which brokerage do you use for your primary investment account?"
2. "Please upload your Portfolio Positions CSV to `notebooks/updates/`"
3. "Please upload your Account Balances CSV to `notebooks/updates/`"
4. "Please upload your Transaction History CSV to `notebooks/updates/`"

### 4.4 Create Broker CSV Mapping Templates

**Goal:** Map different broker CSV formats to our standard schema

**Tasks:**
- [ ] Create `fin-guru/data/broker-mappings/` directory
- [ ] Create mapping files for each broker:
  - `fidelity.yaml`
  - `schwab.yaml`
  - `robinhood.yaml`
  - `vanguard.yaml`
  - `etrade.yaml`
  - `interactive-brokers.yaml`

**Mapping File Structure:**
```yaml
broker: "schwab"
display_name: "Charles Schwab"

positions_csv:
  file_pattern: "Positions_*.csv"
  columns:
    ticker: "Symbol"
    quantity: "Quantity"
    price: "Price"
    market_value: "Market Value"
    cost_basis: "Cost Basis"
    gain_loss: "Gain/Loss"
    gain_loss_pct: "Gain/Loss %"

balances_csv:
  file_pattern: "Balances_*.csv"
  columns:
    total_value: "Account Total"
    cash: "Cash & Cash Investments"
    margin_balance: "Margin Balance"

transactions_csv:
  file_pattern: "Transactions_*.csv"
  columns:
    date: "Date"
    action: "Action"
    ticker: "Symbol"
    quantity: "Quantity"
    price: "Price"
    amount: "Amount"
```

---

## Phase 5: Final Review & Validation

### 5.1 Pre-Codex Checklist

**Before running Codex review, verify:**

- [ ] All setup.sh changes work on fresh clone
- [ ] Agent commands are accessible after setup
- [ ] Skills load and activate correctly
- [ ] Documentation is complete and accurate
- [ ] Onboarding flow handles multiple brokers
- [ ] No private/sensitive data in public files
- [ ] README reflects all new features

### 5.2 Run Codex Full Review

**Goal:** Get comprehensive code review from Codex

**Command:**
```
/ask-codex
```

**Prompt for Codex:**
```
Review the entire Finance Guru codebase for:
1. Documentation accuracy - do docs match implementation?
2. Setup script completeness - does it set up everything needed?
3. Onboarding flow - can a new user get started successfully?
4. Multi-broker support - are broker mappings complete and correct?
5. Public readiness - any private data or broken links exposed?
6. Code quality - any issues, inconsistencies, or improvements?

Provide specific file:line references for all issues found.
```

### 5.3 Fix Codex Feedback

**Protocol:**
1. Read all Codex feedback
2. Create a fix list from feedback
3. Fix issues one by one
4. Re-run Codex review if significant changes made
5. Repeat until Codex passes with no critical issues

### 5.4 Final Commit

**After all fixes:**
- [ ] Run git status
- [ ] Stage all changes
- [ ] Commit with message: "feat: prepare Finance Guru for public release"
- [ ] Push to remote
- [ ] Verify push succeeded

---

## Phase 6: Changelog & GitHub Release

### 6.1 Create CHANGELOG.md

**Goal:** Document all changes for public release

**Tasks:**
- [ ] Create `CHANGELOG.md` in project root
- [ ] Follow [Keep a Changelog](https://keepachangelog.com/) format
- [ ] Document all features in v2.0.0 release

**CHANGELOG.md Structure:**
```markdown
# Changelog

All notable changes to Finance Guru will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-01-XX

### Added
- Multi-agent system with 11 specialized financial agents
- 12 production-ready CLI analysis tools
- Hook-driven architecture for context injection
- Multi-broker support (Fidelity, Schwab, Robinhood, Vanguard, E*TRADE, IBKR)
- Onboarding specialist for new user setup
- Comprehensive documentation (api.md, hooks.md, contributing.md)
- Setup script for automated installation
- Skills system with auto-activation

### Features
- Risk Metrics CLI (VaR, CVaR, Sharpe, Sortino, Max DD)
- Momentum CLI (RSI, MACD, Stochastic)
- Volatility CLI (Bollinger Bands, ATR, Regime)
- Correlation CLI (Pearson, diversification scoring)
- Portfolio Optimizer (Max Sharpe, Risk Parity, Black-Litterman)
- Backtester (strategy validation)
- Options Pricer (Black-Scholes, Greeks, IV)
- Technical Screener (pattern detection)
- Factor Analysis (CAPM, Alpha, Beta)
- Data Validator (quality checks)

### Architecture
- CLI-First design for token efficiency
- 3-layer pattern (Pydantic → Calculator → CLI)
- Session start context injection via hooks
- Skills auto-activation based on intent patterns

## [1.0.0] - 2025-XX-XX

### Added
- Initial release (private)
```

### 6.2 Create GitHub Release

**Goal:** Create official v2.0.0 release on GitHub

**Tasks:**
- [ ] Create git tag: `git tag -a v2.0.0 -m "Finance Guru v2.0.0 - Public Release"`
- [ ] Push tag: `git push origin v2.0.0`
- [ ] Create GitHub release via `gh` CLI:

**Command:**
```bash
gh release create v2.0.0 \
  --title "Finance Guru v2.0.0 - Public Release" \
  --notes-file RELEASE_NOTES.md \
  --latest
```

### 6.3 Create RELEASE_NOTES.md

**Goal:** Detailed release notes for GitHub release page

**Tasks:**
- [ ] Create `RELEASE_NOTES.md` with:
  - Overview of Finance Guru
  - Key features
  - Quick start instructions
  - Breaking changes (if any)
  - Migration guide (if applicable)
  - Known issues
  - Contributors

**Template:**
```markdown
# Finance Guru v2.0.0 - Public Release

Your AI-powered private family office. Stop juggling 10 browser tabs for financial analysis—one command activates 8 AI specialists who work together.

## Highlights

- **11 Specialized Agents** - Finance Orchestrator, Market Researcher, Quant Analyst, and more
- **12 CLI Tools** - Production-ready analysis tools for risk, momentum, volatility, correlation
- **Multi-Broker Support** - Works with Fidelity, Schwab, Robinhood, Vanguard, E*TRADE, IBKR
- **Token Efficient** - CLI-first architecture keeps context window free

## Quick Start

\`\`\`bash
git clone https://github.com/AojdevStudio/Finance-Guru.git
cd Finance-Guru
./setup.sh
claude
/fin-guru:agents:onboarding-specialist
\`\`\`

## Requirements

- Python 3.12+
- Claude Code CLI
- MCP Servers: exa, bright-data, sequential-thinking

## Documentation

- [README](README.md) - Project overview
- [API Reference](docs/api.md) - CLI tools documentation
- [Hooks System](docs/hooks.md) - Architecture details
- [Contributing](docs/contributing.md) - Development guide

## Educational Disclaimer

Finance Guru is for educational purposes only. Not investment advice.
```

### 6.4 Verify Release

**Tasks:**
- [ ] Verify tag exists: `git tag -l`
- [ ] Verify release on GitHub: `gh release view v2.0.0`
- [ ] Test clone from release: `git clone --branch v2.0.0 ...`
- [ ] Verify setup.sh works on fresh release clone

---

## Summary Checklist

| Phase | Task | Status |
|-------|------|--------|
| 1.1 | Load agent commands in setup.sh | [ ] |
| 1.2 | Load skills in setup.sh | [ ] |
| 1.3 | Update README for installation | [ ] |
| 2.1 | Move python-tools.md to docs | [ ] |
| 2.2 | Create src/CLAUDE.md | [ ] |
| 3.1 | Fix notebooks folder structure | [ ] |
| 4.1 | Evaluate onboarding flow | [ ] |
| 4.2 | Add multi-broker support | [ ] |
| 4.3 | Document CSV requirements | [ ] |
| 4.4 | Create broker mapping templates | [ ] |
| 5.1 | Pre-Codex checklist | [ ] |
| 5.2 | Run Codex review | [ ] |
| 5.3 | Fix Codex feedback | [ ] |
| 5.4 | Final commit and push | [ ] |
| 6.1 | Create CHANGELOG.md | [ ] |
| 6.2 | Create GitHub release | [ ] |
| 6.3 | Create RELEASE_NOTES.md | [ ] |
| 6.4 | Verify release | [ ] |

---

## Notes for Executor

- **Be autonomous** - make reasonable decisions without asking
- **Prioritize user experience** - new users should have zero confusion
- **Keep it simple** - don't over-engineer solutions
- **Document as you go** - update docs alongside code changes
- **Test on fresh clone** - verify setup.sh works from scratch
