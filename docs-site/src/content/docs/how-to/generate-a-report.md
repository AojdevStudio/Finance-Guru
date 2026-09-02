---
title: "Generate an analysis report"
description: "Produce a PDF investment-analysis report for a ticker with the FinanceReport tooling."
sidebar:
  order: 4
---

Follow this guide to produce a branded PDF analysis report for one ticker. Report generation is part of the transitional agent-skill stack, not the stable engine contract. The tools work from the command line, but their shape may change as the standalone-app transition proceeds.

## Prerequisites

You need the engine checkout with `uv sync --dev` completed, and network access for market data. Reports read a portfolio value for position sizing. Pass it explicitly, or the tooling reads it from your instance profile.

## Generate a chart

```bash
uv run python .claude/skills/FinanceReport/tools/ChartKit.py \
  --ticker TSLA \
  --chart-type line \
  --data-source cli
```

## Generate the report

```bash
uv run python .claude/skills/FinanceReport/tools/ReportGenerator.py \
  --ticker TSLA \
  --portfolio-value 250000
```

The `250000` value is a round scenario number for sizing examples. Substitute your own value locally; never commit a real one. The report draws on the same engine tools documented in the [CLI reference](../../reference/cli/), including risk metrics, volatility, and correlation.

## Verify the result

The report is written to the reports directory of your instance. Confirm the PDF exists and open it. Every report ends with the educational-use disclaimer, and its analysis is not investment advice.

## When it fails

Market-data steps can fail for the same reasons as any analysis command. Work through [Troubleshoot common failures](../troubleshoot/). If the report tooling itself errors, record the exact command and traceback and check the repository issues before filing a new one.

_This page is built from `.claude/skills/FinanceReport/SKILL.md` in the repository._
