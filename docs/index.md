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

## Reference

Technical reference documentation.

| Document | Description |
|----------|-------------|
| [API Reference](reference/api.md) | CLI tools documentation |
| [Hooks System](reference/hooks.md) | How hooks power auto-activation |
| [Tools Reference](reference/tools.md) | Quick reference for available tools |

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

## Directory Structure

```
family-office/
├── .claude/
│   ├── hooks/           # Hook scripts
│   │   ├── load-fin-core-config.ts    # SessionStart
│   │   ├── skill-activation-prompt.sh # UserPromptSubmit
│   │   ├── post-tool-use-tracker.sh   # PostToolUse
│   │   └── stop-build-check-enhanced.sh # Stop
│   ├── settings.json    # Hook configuration
│   └── skills/          # Skill definitions
│       ├── fin-core/    # Finance Guru core skill
│       └── skill-rules.json # Activation rules
├── docs/                # Public documentation (tracked in git)
│   ├── index.md         # This file
│   ├── CONTRIBUTING.md  # Contribution guide
│   ├── setup/           # Installation and configuration
│   ├── guides/          # User walkthroughs
│   ├── reference/       # Technical reference
│   └── reports/         # Evaluation reports
├── fin-guru/            # Agent system module
│   ├── agents/          # Agent definitions
│   ├── config.yaml      # Module configuration
│   ├── data/            # Knowledge base (gitignored)
│   └── tasks/           # Workflow definitions
├── fin-guru-private/    # Private docs (gitignored, created by setup.sh)
│   └── fin-guru/        # Your strategies, tickets, analysis
├── src/
│   ├── analysis/        # Risk, correlation, ITC
│   ├── strategies/      # Optimizer, backtester
│   └── utils/           # Momentum, volatility
└── notebooks/
    └── updates/         # Fidelity CSV exports (gitignored)
```

## Getting Help

1. **README.md** - Start here for setup and quick start
2. **reference/api.md** - CLI tool usage and examples
3. **reference/hooks.md** - Understanding the hooks system
4. **fin-guru/INDEX.md** - Active strategies and analysis

## Version

- **Finance Guru**: v2.0.0
- **BMAD-CORE**: v6.0.0
- **Last Updated**: 2026-02-05
