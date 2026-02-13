---
title: "Available Tools Reference"
description: "Quick reference for all available CLI tools and their capabilities"
category: reference
---

### Available Tools

#### Risk Metrics Calculator (✅ Production Ready)
- **Location**: `src/analysis/risk_metrics_cli.py`
- **Models**: `src/models/risk_inputs.py`
- **Calculator**: `src/analysis/risk_metrics.py`
- **Documentation**: `fin-guru-private/guides/risk-metrics-tool-guide.md`
- **Metrics**: VaR, CVaR, Sharpe, Sortino, Max Drawdown, Calmar, Volatility, Beta, Alpha
- **Usage**: See "Risk Metrics Analysis" section above

#### Momentum Indicators (✅ Production Ready)
- **Location**: `src/utils/momentum_cli.py`
- **Models**: `src/models/momentum_inputs.py`
- **Calculator**: `src/utils/momentum.py`
- **Indicators**: RSI, MACD, Stochastic, Williams %R, ROC
- **Features**: Confluence analysis (signal aggregation across 5 indicators)
- **Usage**: See "Momentum Indicators" section above

#### Volatility Metrics (✅ Production Ready)
- **Location**: `src/utils/volatility_cli.py`
- **Models**: `src/models/volatility_inputs.py`
- **Calculator**: `src/utils/volatility.py`
- **Indicators**: Bollinger Bands, ATR, Historical Volatility, Keltner Channels, Standard Deviation
- **Features**: Volatility regime assessment, position sizing guidance, stop-loss calculation
- **Usage**: See "Volatility Metrics" section above

#### Correlation & Covariance Engine (✅ Production Ready)
- **Location**: `src/analysis/correlation_cli.py`
- **Models**: `src/models/correlation_inputs.py`
- **Calculator**: `src/analysis/correlation.py`
- **Analysis**: Pearson correlation, covariance matrices, rolling correlations, diversification scoring
- **Usage**: See "Correlation & Covariance Analysis" section above

#### Backtesting Framework (✅ Production Ready)
- **Location**: `src/strategies/backtester_cli.py`
- **Models**: `src/models/backtest_inputs.py`
- **Engine**: `src/strategies/backtester.py`
- **Strategies**: RSI, SMA crossover, buy-and-hold
- **Features**: Realistic cost modeling, performance metrics, deployment recommendations
- **Usage**: See "Strategy Backtesting" section above

#### Moving Average Toolkit (✅ Production Ready)
- **Location**: `src/utils/moving_averages_cli.py`
- **Models**: `src/models/moving_avg_inputs.py`
- **Calculator**: `src/utils/moving_averages.py`
- **MA Types**: SMA, EMA, WMA, HMA (Hull)
- **Features**: Golden Cross/Death Cross detection, crossover analysis
- **Usage**: See "Moving Average Analysis" section above

#### Portfolio Optimizer (✅ Production Ready)
- **Location**: `src/strategies/optimizer_cli.py`
- **Models**: `src/models/portfolio_inputs.py`
- **Engine**: `src/strategies/optimizer.py`
- **Methods**: Mean-Variance, Risk Parity, Min Variance, Max Sharpe, Black-Litterman
- **Features**: Position limits, $500k allocation guidance, efficient frontier
- **Usage**: See "Portfolio Optimization" section above

#### Additional Tools (✅ Implemented)
- **Options Analytics** (`src/analysis/options_cli.py`) - Black-Scholes pricing, Greeks, IV analysis
- **Factor Analysis** (`src/analysis/factors_cli.py`) - CAPM, Alpha, Beta calculations
- **Technical Screener** (`src/utils/screener_cli.py`) - Pattern detection, technical signals
- **Data Validator** (`src/utils/data_validator_cli.py`) - Data quality checks, outlier detection

See `docs/api.md` for CLI usage examples.
