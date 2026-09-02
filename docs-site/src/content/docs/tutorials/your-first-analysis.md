---
title: "Your first analysis"
description: "Run one risk-metrics analysis with the Finance Guru engine and read the result."
sidebar:
  order: 2
---

In this tutorial you run one analysis command against public market data and read its output. No credentials, database, or instance are required.

## Before you start

You need an engine checkout with the development environment installed.

```bash
git clone https://github.com/YOUR-USERNAME/Finance-Guru.git
cd Finance-Guru
uv sync --dev
```

## Step 1. Run a risk-metrics analysis

From the repository root, analyze one year of AAPL history against the SPY benchmark.

```bash
uv run python src/analysis/risk_metrics_cli.py AAPL --days 252 --benchmark SPY
```

The command downloads public price history and prints risk metrics for the ticker. Expect values for Value at Risk, Conditional Value at Risk, Sharpe ratio, Sortino ratio, maximum drawdown, and the beta and alpha computed against the benchmark.

The command needs network access to a public market-data provider. If it fails, see [Troubleshoot common failures](../../how-to/troubleshoot/).

## Step 2. Explore the options

Every analysis command documents its own flags.

```bash
uv run python src/analysis/risk_metrics_cli.py --help
```

Try a shorter window or machine-readable output. The help text lists supported values for the confidence level, the VaR method, and the output format.

## What you learned

You ran one command through the engine's standard shape. Every analysis tool follows the same pattern of a ticker, a window, and optional flags. The [CLI reference](../../reference/cli/) lists every supported command.

## Important notice

Finance Guru provides educational analysis only. It is not investment, tax, or legal advice. Financial markets involve risk, including loss of principal. Consult appropriately licensed professionals for decisions about your assets.

_This page is built from the Wiki Getting Started page and `docs/reference/api.md` in the repository._
