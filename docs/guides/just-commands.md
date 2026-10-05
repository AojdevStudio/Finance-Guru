---
title: "Just Commands Reference"
description: "Justfile recipes for Finance Guru agent personas and context loading"
category: guides
---

# Just Commands Reference

Finance Guru uses [just](https://github.com/casey/just) as a command launchpad. Run `just --list` to see all available recipes.

## Agent Personas

Launch [Claude Code](https://code.claude.com/) pre-loaded with a specialist persona:

| Recipe | Agent | Description |
|--------|-------|-------------|
| `just orchestrator` | Cassandra Holt | Finance Orchestrator — coordinates the team |
| `just quant` | Quant Analyst | Quantitative analysis, risk metrics, models |
| `just strategy` | Strategy Advisor | Portfolio optimization, allocation |
| `just market` | Market Researcher | Market intelligence, trend scanning |
| `just compliance` | Compliance Officer | Risk limits, regulatory checks |
| `just margin` | Margin Specialist | Leverage analysis, ATR position sizing |
| `just dividend` | Dividend Specialist | Income optimization, DRIP modeling |
| `just teaching` | Teaching Specialist | Financial education, learning paths |
| `just builder` | Builder | Document generation, report creation |
| `just qa` | QA Advisor | Quality assurance, validation |

Each recipe runs:
```bash
claude --dangerously-skip-permissions --agent fg-{agent}
```

## Context Loading

Load mermaid architecture diagrams into Claude Code context:

| Recipe | Description |
|--------|-------------|
| `just load-diagrams` | Load all mermaid diagrams |
| `just load-hedging` | Load hedging integration architecture |
| `just load-explorer` | Load knowledge explorer architecture |
| `just load <keyword>` | Load diagram matching keyword |

## Prerequisites

- [just](https://github.com/casey/just) — `brew install just` or `cargo install just`
- [Claude Code](https://code.claude.com/) — must be installed and authenticated
- Agent persona files in `.claude/agents/fg-*.md`

## Version

- **Last Updated**: 2026-02-18

## Plugin evals

`just eval` scores the plugin against the cases in `evals/` with `claude plugin eval`, once with the plugin and once without it, and writes the results and an HTML report to `evals/results/<timestamp>/`. Pass a run count, as in `just eval 3`, for a steadier score. Each run spends model usage, and the recipe stops at a $10 list-price estimate.
