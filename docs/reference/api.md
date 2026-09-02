---
title: "Finance Guru CLI reference"
description: "Checked-in command entry points for the stable analysis engine"
category: reference
---

# Finance Guru CLI reference

This is the checked-in command inventory, not a promise that every command is
configured for every fork. Use `--help` before relying on a command's arguments
or provider requirements. Commands that query markets or a personal integration
may require network access or private credentials.

## Command pattern

Run standalone scripts from the repository root with uv:

```bash
uv run python path/to/script.py --help
```

The refresh entry point is a Python module, not a standalone script:

```bash
uv run python -m src.integrations.refresh_all --help
```

## Analysis commands

| Command | Purpose |
| --- | --- |
| `src/analysis/correlation_cli.py` | Correlation and diversification analysis. |
| `src/analysis/factors_cli.py` | Factor analysis. |
| `src/analysis/hedge_comparison_cli.py` | Compare hedge approaches. |
| `src/analysis/hedge_sizer_cli.py` | Calculate hedge sizing. |
| `src/analysis/itc_risk_cli.py` | Query ITC risk-model data. |
| `src/analysis/margin_metrics.py` | Calculate margin metrics from configured local data. |
| `src/analysis/options_chain_cli.py` | Inspect options-chain data. |
| `src/analysis/options_cli.py` | Run options calculations. |
| `src/analysis/risk_metrics_cli.py` | Calculate risk and benchmark metrics. |
| `src/analysis/rolling_tracker_cli.py` | Track a rolling analysis series. |
| `src/analysis/total_return_cli.py` | Calculate total return. |

## Strategy commands

| Command | Purpose |
| --- | --- |
| `src/strategies/backtester_cli.py` | Backtest your strategy using supported implementations. |
| `src/strategies/optimizer_cli.py` | Produce allocations for your portfolio using supported optimization methods. |

## Utility commands

| Command | Purpose |
| --- | --- |
| `src/utils/data_validator_cli.py` | Check data quality. |
| `uv run python -m src.utils.input_validation_cli` | Validate financial time-series inputs. |
| `src/utils/market_data.py` | Retrieve market data. |
| `src/utils/momentum_cli.py` | Calculate momentum indicators. |
| `src/utils/moving_averages_cli.py` | Calculate moving averages and crossover signals. |
| `src/utils/screener_cli.py` | Run the market screener. |
| `src/utils/volatility_cli.py` | Calculate volatility indicators. |
| `uv run python -m src.utils.yaml_generator_cli` | Generate supported YAML artifacts. |

## Interactive interface

| Command | Purpose |
| --- | --- |
| `src/cli/fin_guru.py` | Start the Textual terminal interface. |

`uv run python -m src.cli.instance_init <root> --repo .` is the supported setup
command. The TypeScript onboarding wizard under `scripts/onboarding/` predates it
and is not part of the command contract.

## Data refresh command

| Command | Purpose |
| --- | --- |
| `uv run python -m src.integrations.refresh_all` | Refresh configured SnapTrade and SimpleFIN data into the local database. |
| `uv run python -m src.integrations.snaptrade.cli` | Inspect linked SnapTrade accounts, positions, balances, or activities. |
| `uv run python -m src.integrations.snaptrade.sync_db` | Refresh SnapTrade positions and balances into local SQLite. |
| `uv run python -m src.integrations.snaptrade.sync_transactions_db` | Refresh SnapTrade activities into local SQLite. |
| `uv run python -m src.integrations.simplefin.sync_expenses_db` | Refresh SimpleFIN transactions into local SQLite. |

## Output and safety

Financial-analysis output is for educational purposes only. It is not
investment advice. It may be wrong or incomplete, and loss of principal is
possible. Review input data and results independently and consult appropriately
licensed financial, tax, and legal professionals before acting.

Never put account numbers, balances, positions, access tokens, or database
files in command arguments, checked-in examples, or Git commits. See
[Privacy](../../PRIVACY.md) and [setup](../setup/SETUP.md).
