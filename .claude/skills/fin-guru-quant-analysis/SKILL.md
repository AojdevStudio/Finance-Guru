---
name: fin-guru-quant-analysis
description: Perform quantitative analysis of returns, correlations, risk factors, and portfolio optimization. Statistical modeling with institutional-grade rigor.
---

# Quantitative Analysis Skill

Execute structured quantitative analysis workflows with statistical validation.

## Workflow Steps

1. **Plan** — Define statistical modeling objectives, metrics, and assumptions
2. **Data Validation** — Use `data_validator_cli.py` for statistical validity (outliers, gaps, splits)
3. **Risk Metrics** — Use `risk_metrics_cli.py` for VaR/CVaR/Sharpe/Sortino/Drawdown (minimum 90 days)
4. **Momentum Analysis** — Use `momentum_cli.py` for confluence analysis
5. **Volatility Metrics** — Use `volatility_cli.py` for regime analysis
6. **Correlation Analysis** — Use `correlation_cli.py` for diversification and covariance matrices
7. **Factor Analysis** — Use `factors_cli.py` for Fama-French 3-factor, Carhart 4-factor models
8. **Strategy Validation** — Use `backtester_cli.py` with transaction costs and realistic slippage
9. **Portfolio Optimization** — Use `optimizer_cli.py` for mean-variance, risk parity, max Sharpe, Black-Litterman

## CLI Commands

```bash
# Risk metrics
uv run python -m src.analysis.risk_metrics_cli TICKER --days 252 --benchmark SPY

# Momentum confluence
uv run python -m src.utils.momentum_cli TICKER --days 90

# Volatility regime
uv run python -m src.utils.volatility_cli TICKER --days 90

# Correlation matrix
uv run python -m src.analysis.correlation_cli TICKER1 TICKER2 --days 90

# Factor analysis
uv run python -m src.analysis.factors_cli TICKER --days 252 --benchmark SPY

# Backtesting
uv run python -m src.strategies.backtester_cli TICKER --days 252 --strategy rsi

# Portfolio optimization
uv run python -m src.strategies.optimizer_cli TICKERS --days 252 --method max_sharpe
```

## Requirements

- Start with clear statistical plan and obtain consent before execution
- Validate all assumptions against compliance policies
- Apply robust methods with proper confidence intervals
- All market data must be timestamped and verified against current date
- Minimum 90 days of data for robust statistics
