# Finance Guru Documentation

Welcome to the Finance Guru documentation. This hub provides navigation to all technical documentation for the system.

## Quick Links

| Document | Description |
|----------|-------------|
| [README](../README.md) | Project overview, quick start, architecture |
| [Setup Guide](SETUP.md) | **Complete installation and configuration guide** |
| [API Reference](api.md) | CLI tools documentation |
| [Hooks System](hooks.md) | How hooks power auto-activation |
| [Contributing](contributing.md) | How to contribute |

## Finance Guru Module Docs

| Document | Description |
|----------|-------------|
| [Finance Guru Module](../fin-guru/README.md) | Module configuration and agents |
| [fin-guru-private/](../fin-guru-private/) | Your personal strategies and analysis (created by setup.sh) |

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
│   ├── api.md           # CLI tools reference
│   ├── hooks.md         # Hooks documentation
│   └── contributing.md  # Contribution guide
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
2. **api.md** - CLI tool usage and examples
3. **hooks.md** - Understanding the hooks system
4. **fin-guru/INDEX.md** - Active strategies and analysis

## Version

- **Finance Guru**: v2.0.0
- **BMAD-CORE**: v6.0.0
- **Last Updated**: 2026-01-10
