---
title: "Finance Guru Documentation"
description: "Documentation hub for Finance Guru - your AI-powered private family office"
category: root
---

# Finance Guru Documentation

Welcome to the Finance Guru documentation. This hub provides navigation to all technical documentation for the system.

## Setup

Installation, configuration, and troubleshooting guides.

| Document | Description |
|----------|-------------|
| [Setup Guide](setup/SETUP.md) | Complete installation and configuration guide |
| [API Keys Guide](setup/api-keys.md) | How to obtain and configure API keys |
| [Troubleshooting](setup/TROUBLESHOOTING.md) | Comprehensive troubleshooting guide |

## Guides

User walkthroughs and how-to guides.

| Document | Description |
|----------|-------------|
| [Broker CSV Export Guide](guides/broker-csv-export-guide.md) | How to export CSVs from Fidelity, Schwab, Vanguard, etc. |
| [Required CSV Uploads](guides/required-csv-uploads.md) | Complete guide to broker CSV formats and upload workflow |
| [Just Commands Reference](guides/just-commands.md) | Justfile recipes for agent personas and context loading |

## Reference

Technical reference documentation.

| Document | Description |
|----------|-------------|
| [API Reference](reference/api.md) | CLI tools documentation |
| [Hooks System](reference/hooks.md) | How hooks power auto-activation |
| [Tools Reference](reference/tools.md) | Quick reference for available tools |
| [Observability](reference/observability.md) | Structured logging, PII scrubbing, feature flags |
| [Cross-Harness Skills](reference/cross-harness-skills.md) | Using Finance Guru skills in Claude Code, pi-coding-agent, and other harnesses |

## Runbooks

Step-by-step operational procedures.

| Runbook | Cadence | Summary |
|---------|---------|---------|
| [Runbooks Index](runbooks/README.md) | — | Overview and cadence guide |
| [Margin Dashboard Update](runbooks/margin-dashboard-update.md) | Weekly | Refresh coverage ratio, act on alerts |
| [Portfolio Sync](runbooks/portfolio-sync.md) | Ad-hoc | Ingest broker CSVs → Google Sheets |
| [Monthly Dividend Review](runbooks/monthly-dividend-review.md) | Monthly | Confirm Layer 2 income on target |
| [Quarterly Review](runbooks/quarterly-review.md) | Quarterly | Full orchestrator + MonteCarlo + reports |

## Reports

Evaluation and review reports.

| Document | Description |
|----------|-------------|
| [Codex Full Review Report](reports/codex-full-review-report.md) | Comprehensive code review using OpenAI Codex |
| [Onboarding Flow Evaluation](reports/onboarding-flow-evaluation.md) | Assessment of onboarding implementation |
| [Pre-Codex Validation Report](reports/pre-codex-validation-report.md) | Validation checklist results |
| [Manual Test Checklist](reports/MANUAL_TEST_CHECKLIST.md) | Comprehensive manual testing checklist |

## Resources

Additional resources and data files.

| Resource | Description |
|----------|-------------|
| [CSV Mappings](csv-mappings/) | CSV column mapping configurations |
| [Images](images/) | Architecture diagrams and screenshots |
| [Solutions](solutions/) | Problem-specific solution documents |

## Quick Links

| Document | Description |
|----------|-------------|
| [README](../README.md) | Project overview, quick start, architecture |
| [CONTRIBUTING](CONTRIBUTING.md) | How to contribute |
| [Finance Guru Module](../fin-guru/README.md) | Module configuration and agents |
| [Justfile Recipes](guides/just-commands.md) | Agent persona launchers and context loading |

## Architecture Overview

<p align="center">
  <img src="images/finance-guru-architecture-diagram.png" alt="Finance Guru Architecture" width="800"/>
</p>

The diagram shows the hook-driven agent orchestration pipeline:

1. **SessionStart Hook** - `load-fin-core-config.ts` injects config.yaml, user-profile.yaml, and portfolio data
2. **User Prompt** - `skill-activation-prompt.sh` matches keywords, intent patterns, and file paths
3. **Agent Activation** - Finance Orchestrator routes to specialists (Market Researcher, Quant, Strategy, etc.)
4. **CLI Tools** - Token-efficient Python tools for heavy computation
5. **PostToolUse Hook** - `post-tool-use-tracker.sh` tracks file modifications
6. **Stop Hook** - `stop-build-check-enhanced.sh` validates before completion

## Key Concepts

### CLI-First Architecture

Heavy computation happens in Python CLI tools, not in Claude's context window. This provides:

- **Token efficiency**: Calculations don't consume context
- **Reproducibility**: Same command = same result
- **Composability**: Pipe outputs, chain tools
- **Debuggability**: Run tools standalone

### Session Start Context Injection

The `load-fin-core-config.ts` hook runs at session start and injects:

1. **fin-core skill** - Core Finance Guru knowledge
2. **config.yaml** - Agent roster, tool list, workflow pipeline
3. **user-profile.yaml** - Portfolio strategy, risk tolerance
4. **system-context.md** - Repository structure, privacy rules
5. **Latest portfolio data** - Fidelity balances and positions

### Skills System

Skills are modular knowledge bases that load on-demand:

- **domain skills** (suggest) - Best practices, patterns
- **guardrail skills** (block) - Must use before proceeding

Activation triggers:
- Keywords in prompts
- Intent patterns (regex)
- File path patterns
- Content patterns

### Cross-Harness Skill Portability

Finance Guru skills follow the [Agent Skills standard](https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/docs/sdk.md) — the same `SKILL.md` files work in multiple AI coding agents without rewriting:

| Harness | Reads skills from |
|---------|-------------------|
| Claude Code | `.claude/skills/` (primary source) |
| pi-coding-agent | `.pi/skills/` → (symlink) → `.agents/skills/` → `.claude/skills/` |
| Any Agent-Skills-standard harness | `.agents/skills/` (symlinked fanout) |

See [reference/cross-harness-skills.md](reference/cross-harness-skills.md) for the full setup.

### Multi-Agent Orchestration

Finance Guru uses specialized agents:

| Agent | Role |
|-------|------|
| Cassandra Holt | Orchestrator, routes requests |
| Market Researcher | Intelligence gathering |
| Quant Analyst | Calculations, models |
| Strategy Advisor | Portfolio optimization |
| Compliance Officer | Risk, regulations |
| Margin Specialist | Leverage strategies |
| Dividend Specialist | Income optimization |
| Tax Optimizer | Tax efficiency |
| Teaching Specialist | Financial education |
| Builder | Document generation |
| QA Advisor | Quality assurance |
| Onboarding Specialist | User setup |

## Directory Structure

```
family-office/
├── .claude/
│   ├── hooks/                # Hook scripts
│   │   ├── load-fin-core-config.ts    # SessionStart
│   │   ├── skill-activation-prompt.sh # UserPromptSubmit
│   │   ├── post-tool-use-tracker.sh   # PostToolUse
│   │   └── stop-build-check-enhanced.sh # Stop
│   ├── settings.json         # Hook configuration
│   └── skills/               # Skill definitions (primary source — 19 FG skills)
├── .agents/skills/           # Cross-harness mirror (symlinks to .claude/skills)
├── .pi/skills/               # pi-coding-agent path (→ .agents/skills)
├── .devcontainer/            # Codespaces / VS Code dev container
├── .github/
│   ├── dependabot.yml        # Dependency automation
│   ├── labels.yml            # Label taxonomy
│   ├── branch-protection.yml # Declared branch rules
│   └── workflows/            # CI, release, quality-gates, rollback, error-to-issue
├── apps/                     # Bun monorepo workspaces (turbo.json)
│   ├── plaid-dashboard/      # Next.js 15 + Hono + Drizzle + Plaid
│   └── simplefin-sync/       # Bun/TS indie Plaid alternative
├── docs/                     # Public documentation (tracked in git)
│   ├── index.md              # This file
│   ├── CONTRIBUTING.md       # Contribution guide
│   ├── setup/                # Installation and configuration
│   ├── guides/               # User walkthroughs
│   ├── reference/            # Technical reference
│   ├── runbooks/             # Weekly / monthly / quarterly procedures
│   └── reports/              # Evaluation reports
├── fin-guru/                 # Agent system module (11 specialists)
│   ├── agents/               # Agent definitions
│   ├── config.yaml           # Module configuration
│   ├── data/                 # Knowledge base (gitignored)
│   └── tasks/                # Workflow definitions
├── fin-guru-private/         # Private docs (gitignored, created by setup.sh)
├── finance-guru-desktop/     # Electron + Agent SDK preview (gitignored)
├── monitoring/               # Declarative alerts + routing config
├── src/
│   ├── analysis/             # Risk, correlation, ITC, hedging, options CLIs
│   ├── config/               # Config loader (YAML-default chain)
│   ├── strategies/           # Optimizer, backtester
│   ├── utils/                # Momentum, volatility, logging, feature flags
│   └── models/               # Pydantic type definitions
├── tests/                    # 365+ pytest tests
└── notebooks/
    └── updates/              # Fidelity CSV exports (gitignored)
```

## Getting Help

1. **README.md** - Start here for setup and quick start
2. **reference/api.md** - CLI tool usage and examples
3. **reference/hooks.md** - Understanding the hooks system
4. **fin-guru/INDEX.md** - Active strategies and analysis

## Version

- **Finance Guru**: v2.1.0
- **BMAD-CORE**: v6.0.0
- **Last Updated**: 2026-04-17
