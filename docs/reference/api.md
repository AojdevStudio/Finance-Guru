---
title: "CLI Tools API Reference"
description: "Complete reference for all Finance Guru Python CLI tools"
category: reference
---

# CLI Tools API Reference

Finance Guru provides 12 production-ready CLI tools for financial analysis. All tools follow a consistent 3-layer architecture:

```
Pydantic Models → Calculator Classes → CLI Interfaces
     ↓                    ↓                  ↓
 Type Safety         Business Logic      Agent Access
```

## Quick Reference

| Tool | Script | Primary Metrics |
|------|--------|-----------------|
| Risk Metrics | `src/analysis/risk_metrics_cli.py` | VaR, CVaR, Sharpe, Sortino, Max DD |
| ITC Risk | `src/analysis/itc_risk_cli.py` | Market-implied risk scores |
| Momentum | `src/utils/momentum_cli.py` | RSI, MACD, Stochastic, Williams %R |
| Volatility | `src/utils/volatility_cli.py` | Bollinger Bands, ATR, Regime |
| Moving Averages | `src/utils/moving_averages_cli.py` | SMA, EMA, Golden Cross |
| Correlation | `src/analysis/correlation_cli.py` | Pearson, diversification score |
| Portfolio Optimizer | `src/strategies/optimizer_cli.py` | Max Sharpe, Risk Parity |
| Backtester | `src/strategies/backtester_cli.py` | Strategy validation |
| Options | `src/analysis/options_cli.py` | Black-Scholes, Greeks, IV |
| Screener | `src/utils/screener_cli.py` | Pattern detection, signals |
| Factors | `src/analysis/factors_cli.py` | CAPM, Alpha, Beta |
| Data Validator | `src/utils/data_validator_cli.py` | Quality checks, outliers |

## Base Command Pattern

```bash
uv run python <script> <ticker(s)> [flags]
```

**Common flags**:
- `--days N` - Lookback period (90=quarter, 252=year)
- `--output json` - JSON output format
- `--benchmark SPY` - Benchmark comparison

---

## Risk Metrics

Calculate comprehensive risk metrics for a security.

### Usage

```bash
uv run python src/analysis/risk_metrics_cli.py TSLA --days 90
uv run python src/analysis/risk_metrics_cli.py TSLA --days 252 --benchmark SPY
uv run python src/analysis/risk_metrics_cli.py TSLA --output json
```

### Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--days` | 90 | Lookback period in trading days |
| `--benchmark` | SPY | Benchmark for beta/alpha calculations |
| `--output` | text | Output format: text, json |
| `--save-to` | - | Save results to file path |

### Output Metrics

- **VaR (95%)**: Value at Risk - maximum expected loss at 95% confidence
- **CVaR (95%)**: Conditional VaR - average loss beyond VaR threshold
- **Sharpe Ratio**: Risk-adjusted return (excess return / volatility)
- **Sortino Ratio**: Downside risk-adjusted return
- **Max Drawdown**: Largest peak-to-trough decline
- **Calmar Ratio**: Annual return / Max drawdown
- **Volatility**: Annualized standard deviation
- **Beta**: Systematic risk relative to benchmark
- **Alpha**: Excess return above benchmark-adjusted expectation

### Example Output

```
Risk Metrics for TSLA (90 days)
================================
VaR (95%):        -3.42%
CVaR (95%):       -5.18%
Sharpe Ratio:     1.24
Sortino Ratio:    1.87
Max Drawdown:     -18.34%
Calmar Ratio:     2.15
Volatility:       42.3%
Beta:             1.82
Alpha:            12.4%
```

---

## ITC Risk Models

External market-implied risk scores from ITC Risk Models API.

### Usage

```bash
uv run python src/analysis/itc_risk_cli.py TSLA
uv run python src/analysis/itc_risk_cli.py TSLA --universe tradfi
uv run python src/analysis/itc_risk_cli.py BTC --universe crypto
uv run python src/analysis/itc_risk_cli.py --list-supported
```

### Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--universe` | tradfi | Asset universe: tradfi, crypto |
| `--full-table` | false | Show complete risk band table |
| `--list-supported` | false | List all supported tickers |

### Supported Tickers

**TradFi**: TSLA, AAPL, MSTR, NFLX, SP500, Commodities
**Crypto**: BTC, ETH, SOL (varies by API coverage)

### Output

- **Risk Score**: Current market-implied risk (0-100)
- **Risk Band**: Low, Medium, High, Very High
- **Entry Signal**: Based on risk score positioning

---

## Momentum Indicators

Technical momentum analysis with confluence scoring.

### Usage

```bash
uv run python src/utils/momentum_cli.py TSLA --days 90
uv run python src/utils/momentum_cli.py TSLA --indicator rsi
uv run python src/utils/momentum_cli.py TSLA --indicator macd
uv run python src/utils/momentum_cli.py TSLA --rsi-period 14 --macd-fast 12 --macd-slow 26
```

### Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--days` | 90 | Lookback period |
| `--indicator` | all | Specific indicator: rsi, macd, stochastic, williams, roc |
| `--rsi-period` | 14 | RSI calculation period |
| `--macd-fast` | 12 | MACD fast EMA period |
| `--macd-slow` | 26 | MACD slow EMA period |
| `--macd-signal` | 9 | MACD signal line period |

### Output Metrics

- **RSI (14)**: Relative Strength Index (0-100, >70 overbought, <30 oversold)
- **MACD**: Moving Average Convergence Divergence
- **Stochastic %K/%D**: Price position in recent range
- **Williams %R**: Similar to stochastic, inverted scale
- **ROC**: Rate of Change (momentum)
- **Confluence Score**: Agreement across indicators

---

## Volatility Metrics

Volatility analysis with regime detection.

### Usage

```bash
uv run python src/utils/volatility_cli.py TSLA --days 90
uv run python src/utils/volatility_cli.py TSLA --atr-period 14
uv run python src/utils/volatility_cli.py TSLA --bb-period 20 --bb-std 2
```

### Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--days` | 90 | Lookback period |
| `--atr-period` | 14 | ATR calculation period |
| `--bb-period` | 20 | Bollinger Bands period |
| `--bb-std` | 2 | Bollinger Bands standard deviations |

### Output Metrics

- **Bollinger Bands**: Upper, middle, lower bands with %B position
- **ATR**: Average True Range (absolute volatility)
- **Historical Volatility**: Annualized standard deviation
- **Keltner Channels**: ATR-based bands
- **Volatility Regime**: Low, Normal, High, Extreme

---

## Moving Averages

Trend analysis with crossover detection.

### Usage

```bash
uv run python src/utils/moving_averages_cli.py TSLA --days 252
uv run python src/utils/moving_averages_cli.py TSLA --ma-type ema --period 50
uv run python src/utils/moving_averages_cli.py TSLA --fast 50 --slow 200
```

### Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--days` | 252 | Lookback period |
| `--ma-type` | sma | Moving average type: sma, ema, wma, hma |
| `--period` | 20 | Single MA period |
| `--fast` | 50 | Fast MA for crossover |
| `--slow` | 200 | Slow MA for crossover |

### Output

- **Current Price** vs MA levels
- **Golden Cross**: 50-day crosses above 200-day (bullish)
- **Death Cross**: 50-day crosses below 200-day (bearish)
- **Days Since Crossover**: Time since last signal

---

## Correlation Analysis

Portfolio diversification analysis.

### Usage

```bash
# Requires 2+ tickers
uv run python src/analysis/correlation_cli.py TSLA PLTR NVDA --days 90
uv run python src/analysis/correlation_cli.py TSLA PLTR NVDA AAPL GOOGL --rolling 30
```

### Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--days` | 90 | Lookback period |
| `--rolling` | - | Rolling correlation window |

### Output Metrics

- **Correlation Matrix**: Pairwise Pearson correlations
- **Covariance Matrix**: For portfolio optimization
- **Diversification Score**: How uncorrelated the assets are (higher = better)
- **Concentration Risk**: Portfolio concentration measure

---

## Portfolio Optimizer

Optimal portfolio allocation.

### Usage

```bash
uv run python src/strategies/optimizer_cli.py TSLA PLTR NVDA AAPL --days 252
uv run python src/strategies/optimizer_cli.py TSLA PLTR NVDA --method max_sharpe
uv run python src/strategies/optimizer_cli.py TSLA PLTR NVDA --method risk_parity --max-position 0.4
```

### Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--days` | 252 | Lookback period |
| `--method` | max_sharpe | Optimization method |
| `--max-position` | 1.0 | Maximum position size (0-1) |
| `--view` | - | Black-Litterman views: `TSLA:0.15,NVDA:0.20` |

### Optimization Methods

- **max_sharpe**: Maximize Sharpe ratio
- **min_variance**: Minimize portfolio variance
- **risk_parity**: Equal risk contribution
- **mean_variance**: Custom risk/return tradeoff
- **black_litterman**: Incorporate investor views

### Output

- **Optimal Weights**: Allocation per asset
- **Expected Return**: Portfolio expected annual return
- **Expected Volatility**: Portfolio standard deviation
- **Sharpe Ratio**: Risk-adjusted return
- **Efficient Frontier**: Risk/return tradeoff curve

---

## Backtester

Strategy validation and performance testing.

### Usage

```bash
uv run python src/strategies/backtester_cli.py TSLA --days 252
uv run python src/strategies/backtester_cli.py TSLA --strategy rsi --days 252
uv run python src/strategies/backtester_cli.py TSLA --strategy sma_cross --capital 10000
```

### Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--days` | 252 | Backtest period |
| `--strategy` | buy_hold | Strategy: buy_hold, rsi, sma_cross |
| `--capital` | 10000 | Starting capital |
| `--commission` | 0.001 | Commission per trade (0.1%) |
| `--slippage` | 0.001 | Slippage per trade (0.1%) |

### Strategy Types

- **buy_hold**: Baseline buy and hold
- **rsi**: RSI mean reversion (buy oversold, sell overbought)
- **sma_cross**: Moving average crossover

### Output Metrics

- **Total Return**: Cumulative return
- **Sharpe Ratio**: Risk-adjusted performance
- **Max Drawdown**: Largest decline
- **Win Rate**: Percentage of winning trades
- **Number of Trades**: Trade count
- **Comparison vs Buy-Hold**: Strategy alpha

---

## Options Pricer

Black-Scholes options pricing and Greeks calculation.

### Usage

```bash
# Price a call option
uv run python src/analysis/options_cli.py --ticker TSLA \
    --spot 265 --strike 250 --days 90 --volatility 0.45 --type call

# Price a put option
uv run python src/analysis/options_cli.py --ticker TSLA \
    --spot 265 --strike 270 --days 30 --volatility 0.50 --type put

# Calculate implied volatility
uv run python src/analysis/options_cli.py --ticker TSLA \
    --spot 265 --strike 250 --days 90 --market-price 25.50 --type call --implied-vol
```

### Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--ticker` | required | Underlying ticker |
| `--spot` | required | Current stock price |
| `--strike` | required | Option strike price |
| `--days` | required | Days to expiration |
| `--type` | required | Option type: call, put |
| `--volatility` | - | Annual volatility (e.g., 0.45 = 45%) |
| `--market-price` | - | Market price for IV calculation |
| `--implied-vol` | false | Calculate implied volatility |
| `--risk-free-rate` | 0.045 | Annual risk-free rate |
| `--dividend-yield` | 0.0 | Annual dividend yield |

### Output Metrics

- **Option Price**: Theoretical Black-Scholes price
- **Delta (Δ)**: Price sensitivity to underlying
- **Gamma (Γ)**: Delta's rate of change
- **Theta (Θ)**: Time decay per day
- **Vega (ν)**: Sensitivity to volatility
- **Rho (ρ)**: Sensitivity to interest rates
- **Implied Volatility**: Market-implied vol from option price

---

## Technical Screener

Screen stocks for technical patterns and trading signals.

### Usage

```bash
# Screen single ticker
uv run python src/utils/screener_cli.py TSLA --days 252

# Screen multiple tickers (portfolio mode)
uv run python src/utils/screener_cli.py TSLA PLTR NVDA AAPL --days 252

# Custom patterns
uv run python src/utils/screener_cli.py TSLA PLTR --days 252 \
    --patterns golden_cross rsi_oversold breakout
```

### Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--days` | 252 | Historical data days |
| `--patterns` | all | Patterns to screen for |
| `--rsi-oversold` | 30 | RSI oversold threshold |
| `--rsi-overbought` | 70 | RSI overbought threshold |
| `--ma-fast` | 50 | Fast MA period |
| `--ma-slow` | 200 | Slow MA period |
| `--volume-multiplier` | 1.5 | Volume multiplier for breakouts |

### Pattern Types

- **golden_cross**: 50-day crosses above 200-day
- **death_cross**: 50-day crosses below 200-day
- **rsi_oversold**: RSI below threshold
- **rsi_overbought**: RSI above threshold
- **breakout**: Price breakout with volume

### Output

- **Composite Score**: Overall signal strength
- **Recommendation**: strong_buy, buy, hold, sell, strong_sell
- **Confidence**: Signal confidence level
- **Signals Detected**: List of triggered patterns
- **Rank**: Position among screened tickers

---

## Factor Analysis

CAPM and factor analysis for return attribution.

### Usage

```bash
# CAPM analysis (market factor only)
uv run python src/analysis/factors_cli.py TSLA --days 252 --benchmark SPY

# JSON output
uv run python src/analysis/factors_cli.py TSLA --days 252 --benchmark SPY --output json
```

### Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--days` | 252 | Data period |
| `--benchmark` | SPY | Market benchmark |
| `--risk-free-rate` | 0.045 | Annual risk-free rate |

### Output Metrics

- **Market Beta**: Systematic risk exposure
- **Alpha (Annualized)**: Excess return above benchmark
- **R-squared**: Explained variance by market
- **T-statistics**: Statistical significance
- **Return Attribution**: Market vs alpha contribution

---

## Data Validator

Validate data quality before analysis.

### Usage

```bash
# Basic validation
uv run python src/utils/data_validator_cli.py TSLA --days 90

# Custom outlier detection
uv run python src/utils/data_validator_cli.py TSLA --days 252 \
    --outlier-method iqr --outlier-threshold 2.5

# Strict validation (Compliance Officer mode)
uv run python src/utils/data_validator_cli.py TSLA --days 90 \
    --missing-threshold 0.01 --max-gap 5
```

### Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--days` | 90 | Historical data days |
| `--outlier-method` | z_score | Method: z_score, iqr, modified_z |
| `--outlier-threshold` | 3.0 | Detection threshold |
| `--missing-threshold` | 0.05 | Max missing data ratio (5%) |
| `--max-gap` | 10 | Max gap between dates (days) |
| `--check-splits` | true | Check for stock splits |
| `--split-threshold` | 0.25 | Split detection threshold (25%) |

### Output

- **Is Valid**: Pass/fail status
- **Completeness Score**: Data completeness percentage
- **Consistency Score**: Data consistency percentage
- **Reliability Score**: Overall quality score
- **Anomalies**: Detected issues with severity
- **Recommendations**: Actions to improve data quality

---

## Portfolio Loop Pattern

Analyze multiple tickers efficiently:

```bash
for ticker in TSLA PLTR NVDA AAPL GOOGL; do
    echo "=== $ticker ==="
    uv run python src/analysis/risk_metrics_cli.py $ticker --days 90
done
```

## JSON Output for Piping

```bash
uv run python src/analysis/risk_metrics_cli.py TSLA --output json | jq '.sharpe_ratio'
```

## Agent-Tool Matrix

| Agent | Primary Tools |
|-------|--------------|
| Market Researcher | Momentum, Moving Averages, ITC Risk, Screener |
| Quant Analyst | All tools (full access), Options, Factors |
| Strategy Advisor | Optimizer, Backtester, Correlation, Screener |
| Compliance Officer | Risk Metrics, Volatility, Data Validator |
| Margin Specialist | Volatility (ATR-based sizing), Options |
| Dividend Specialist | Correlation (income diversification) |

---

**Note**: All tools require `uv sync` to install dependencies. Market data is fetched via yfinance.
