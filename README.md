# Finance Guru™ - Private Family Office

This is my private Finance Guru™ system - my personal AI-powered family office.

## 🎯 What This Is

This repository is where I interact with Finance Guru™ - my team of specialized AI agents that serve as my personal family office. This is not an app or product - this IS Finance Guru, working exclusively for me to manage my financial strategies, analysis, and decision-making.


## 🤖 My Finance Guru Team

My personal team of specialized agents:

- **Cassandra Holt** - Finance Orchestrator (Master Coordinator)
- **Market Researcher** - Intelligence & market analysis
- **Quant Analyst** - Data modeling & metrics
- **Strategy Advisor** - Portfolio optimization
- **Compliance Officer** - Risk & regulatory oversight
- **Margin Specialist** - Leveraged strategies
- **Dividend Specialist** - Income optimization
- **Tax Optimizer** - Business structure & tax efficiency

## 📊 Quantitative Analysis Suite

Finance Guru™ includes **11 production-ready quantitative analysis tools** built specifically for your portfolio. All tools use real market data and professional-grade calculations.

### 🔬 Risk & Performance Analysis

**1. Risk Metrics Calculator** - Measure portfolio risk
- VaR (Value at Risk), CVaR (Conditional VaR)
- Sharpe Ratio, Sortino Ratio, Calmar Ratio
- Max Drawdown, Annual Volatility
- Beta, Alpha (vs. benchmark)

```bash
# Quick risk scan
uv run python src/analysis/risk_metrics_cli.py TSLA --days 90

# Full analysis with benchmark
uv run python src/analysis/risk_metrics_cli.py TSLA --days 252 --benchmark SPY
```

**2. Factor Analysis Engine** - Understand what drives your returns
- CAPM (Capital Asset Pricing Model)
- Market beta and alpha calculations
- Return attribution by factor
- Statistical significance testing

```bash
# Analyze return drivers
uv run python src/analysis/factors_cli.py TSLA --days 252 --benchmark SPY
```

### 📈 Technical Analysis Tools

**3. Momentum Indicators** - Identify trend strength
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- Stochastic Oscillator, Williams %R, ROC
- Confluence analysis (signal aggregation)

```bash
# Check momentum across all indicators
uv run python src/utils/momentum_cli.py TSLA --days 90
```

**4. Volatility Metrics** - Assess price stability
- Bollinger Bands
- ATR (Average True Range)
- Historical Volatility
- Keltner Channels
- Volatility regime assessment (low/normal/high/extreme)

```bash
# Assess volatility and get position sizing guidance
uv run python src/utils/volatility_cli.py TSLA --days 90
```

**5. Moving Average Toolkit** - Detect trends
- SMA (Simple), EMA (Exponential), WMA (Weighted), HMA (Hull)
- Golden Cross / Death Cross detection
- Crossover analysis and timing

```bash
# Classic 50/200 Golden Cross check
uv run python src/utils/moving_averages_cli.py TSLA --days 252 --fast 50 --slow 200
```

**6. Technical Screener** - Find trading opportunities automatically
- 8 pattern types: Golden Cross, RSI signals, MACD, Breakouts
- Signal strength classification (weak/moderate/strong)
- Portfolio screening with ranking
- Buy/Sell/Hold recommendations

```bash
# Screen multiple stocks for opportunities
uv run python src/utils/screener_cli.py TSLA PLTR NVDA AAPL --days 252
```

### 📊 Portfolio Management

**7. Correlation & Covariance Engine** - Measure diversification
- Correlation matrices (how assets move together)
- Covariance analysis
- Rolling correlations (time-varying relationships)
- Diversification scoring
- Concentration risk detection

```bash
# Check portfolio diversification
uv run python src/analysis/correlation_cli.py TSLA PLTR NVDA --days 90
```

**8. Portfolio Optimizer** - Build optimal allocations
- Mean-Variance Optimization (Markowitz)
- Risk Parity (equal risk contribution)
- Min Variance (defensive)
- Max Sharpe (aggressive growth)
- Black-Litterman (with your views)

```bash
# Optimize for maximum risk-adjusted returns
uv run python src/strategies/optimizer_cli.py TSLA PLTR NVDA SPY --days 252 --method max_sharpe
```

### 🧪 Strategy Development

**9. Backtesting Framework** - Test strategies before deploying
- RSI mean reversion
- SMA crossover
- Buy-and-hold benchmark
- Transaction cost modeling (commissions + slippage)
- Performance metrics and trade logs

```bash
# Test RSI strategy with realistic costs
uv run python src/strategies/backtester_cli.py TSLA --days 252 --strategy rsi \
    --capital 500000 --commission 5.0 --slippage 0.001
```

### 🛡️ Data Quality & Options

**10. Data Validator** - Ensure data quality
- Missing data detection
- Outlier detection (3 methods)
- Stock split detection
- Date gap analysis
- Quality scoring (completeness, consistency, reliability)

```bash
# Validate data before analysis
uv run python src/utils/data_validator_cli.py TSLA --days 90
```

**11. Options Analytics** - Price options and calculate Greeks
- Black-Scholes pricing (calls & puts)
- All five Greeks: Delta, Gamma, Theta, Vega, Rho
- Implied volatility calculation
- Put-call parity checks
- Intrinsic vs. time value breakdown

```bash
# Price a call option
uv run python src/analysis/options_cli.py \
    --ticker TSLA \
    --spot 265 \
    --strike 250 \
    --days 90 \
    --volatility 0.45 \
    --type call
```

### 🏗️ Architecture

All tools follow a **3-layer architecture**:
1. **Pydantic Models** - Type-safe input validation
2. **Calculator Classes** - Business logic and calculations
3. **CLI Interfaces** - Command-line integration for agents

This design ensures:
- ✅ Data validation before any calculations
- ✅ Educational documentation for non-developers
- ✅ Consistent output formats (human-readable & JSON)
- ✅ Easy integration with all Finance Guru agents

### 📚 Tool Documentation

For detailed guides on each tool, see:
- **Complete Suite**: `docs/guides/final-4-tools-guide.md`
- **Risk Metrics**: `docs/guides/risk-metrics-tool-guide.md`
- **Architecture**: `notebooks/tools-needed/type-safety-strategy.md`

### 🔗 Agent Tool Mapping

Different agents use different tools for their specialization:

| Agent | Primary Tools |
|-------|--------------|
| **Market Researcher** | Technical Screener, Momentum, Moving Averages, Data Validator |
| **Quant Analyst** | Risk Metrics, Factor Analysis, Correlation, Volatility, Options |
| **Strategy Advisor** | Portfolio Optimizer, Backtester, Technical Screener |
| **Compliance Officer** | Risk Metrics, Data Validator, Volatility (position limits) |
| **Margin Specialist** | Volatility, Options Greeks, Risk Metrics (Beta, VaR) |
| **Dividend Specialist** | Correlation (portfolio construction), Risk Metrics |

## 📁 Repository Structure

```
family-office/
│
├── src/                   # Python modules for analysis
│   ├── analysis/          # Risk, factors, correlation, options
│   ├── strategies/        # Backtester, optimizer
│   ├── utils/             # Momentum, volatility, screener, validators
│   └── models/            # Pydantic models for all tools
├── scripts/               # Financial parsing & automation
├── notebooks/             # Jupyter analysis notebooks
├── docs/                  # My financial documents & summaries
│   ├── fin-guru/          # Generated analyses
│   └── guides/            # Tool documentation
├── research/finance/      # My assessment data
└── fin-guru/              # Finance Guru agent configurations
    ├── agents/            # Agent definitions
    ├── tasks/             # Workflow definitions
    ├── templates/         # Document templates
    └── data/              # Knowledge base & user profile
```

## 🚀 How I Use This

### Primary Interface
```bash
/finance-orchestrator    # Cassandra coordinates everything
```

### Direct Agent Access
```bash
*agent market-research   # Become Market Researcher
*agent quant            # Become Quant Analyst
*agent strategy         # Become Strategy Advisor
```

### Task Execution
```bash
*research               # Execute research workflow
*analyze                # Execute quantitative analysis
*strategize             # Execute strategy integration
```

### Status Check
```bash
*status                 # Current context & progress
*help                   # Show available commands
```

## 💡 Example Workflows

### Quick Market Analysis
```bash
# 1. Check data quality
uv run python src/utils/data_validator_cli.py TSLA --days 90

# 2. Assess risk profile
uv run python src/analysis/risk_metrics_cli.py TSLA --days 90 --benchmark SPY

# 3. Check momentum and trend
uv run python src/utils/momentum_cli.py TSLA --days 90
uv run python src/utils/moving_averages_cli.py TSLA --days 252 --fast 50 --slow 200
```

### Portfolio Rebalancing
```bash
# 1. Check current correlations
uv run python src/analysis/correlation_cli.py TSLA PLTR NVDA SPY --days 90

# 2. Optimize allocation
uv run python src/strategies/optimizer_cli.py TSLA PLTR NVDA SPY --days 252 \
    --method max_sharpe --max-position 0.30

# 3. Validate with backtesting
uv run python src/strategies/backtester_cli.py TSLA --days 252 --strategy rsi
```

### Options Strategy Analysis
```bash
# 1. Check current volatility regime
uv run python src/utils/volatility_cli.py TSLA --days 90

# 2. Price option and get Greeks
uv run python src/analysis/options_cli.py \
    --ticker TSLA --spot 265 --strike 250 --days 90 \
    --volatility 0.45 --type call

# 3. Calculate implied volatility from market price
uv run python src/analysis/options_cli.py \
    --ticker TSLA --spot 265 --strike 250 --days 90 \
    --market-price 25.50 --type call --implied-vol
```

## 🔒 Security Note

This is my private financial command center. All data stays local. No external access.

## 📊 Working Areas

- Portfolio optimization & rebalancing
- Cash flow analysis & projections
- Tax strategy & business structure optimization
- Investment research & due diligence
- Risk assessment & hedging strategies
- Debt optimization & refinancing analysis
- Options strategy development & Greeks-based hedging
- Technical analysis & opportunity screening

## ⚠️ Important Disclaimers

**Educational Use Only**: All analyses and recommendations generated by Finance Guru™ are for educational purposes only and should not be considered financial advice.

**Not Investment Advice**: Finance Guru™ is a research and analysis tool. Always consult with licensed financial professionals before making investment decisions.

**Risk Disclosure**: All investments carry risk, including potential loss of principal. Past performance does not guarantee future results.

**Data Accuracy**: While Finance Guru™ uses professional-grade calculations and validates data quality, always verify critical information independently.

## 🛠️ Technical Stack

- **Python 3.12+** - Core language
- **uv** - Package manager (fast, reliable)
- **pandas, numpy, scipy** - Data analysis & statistics
- **yfinance** - Real-time market data
- **scikit-learn** - Machine learning & regression
- **pydantic** - Type-safe data validation
- **streamlit** - Visualization (when needed)

## 📖 Learning Resources

This system is built with educational explanations throughout:
- Tool help text: `<tool> --help`
- In-code documentation: Check Python docstrings
- Comprehensive guides: `docs/guides/`
- Architecture notes: `notebooks/tools-needed/`

## 🔄 Version Information

- **Finance Guru™**: v2.0.0
- **BMAD-CORE™**: v6.0.0
- **Tools Built**: 11 of 11 (Complete Suite)
- **Last Updated**: 2025-10-13

---

**This is Finance Guru™** - My AI-powered family office, working exclusively for me.
