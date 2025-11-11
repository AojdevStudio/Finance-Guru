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

## Prerequisites

Before using Finance Guru, ensure you have the following components installed and configured:

### System Requirements

- **Claude Code**: Latest version (multi-agent orchestration platform)
    - Install: `curl -fsSL https://claude.ai/install.sh | bash`
- **Node.js/TypeScript**: For skill activation hooks and automation
    - Install: `curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash`
- **Python 3.12+**: Required for all financial analysis tools
    - Install: `https://github.com/pyenv/pyenv?tab=readme-ov-file#installation`
- **uv Package Manager**: Modern Python package manager for dependency management
  - Install: `curl -LsSf https://astral.sh/uv/install.sh | sh`
  - Usage: `uv sync` (install all dependencies)
- **Google Sheets Access**: Portfolio tracking and data management


## 📊 Quantitative Analysis Suite

Finance Guru™ includes **11 production-ready quantitative analysis tools** built specifically for your portfolio. All tools use real market data and professional-grade calculations.

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
- **Complete Suite**: `docs/guides/final-4-tools-guide.md` and `docs/guides/quantitative-analysis-tools.md`
- **Risk Metrics**: `docs/guides/risk-metrics-tool-guide.md`
- **Architecture**: `notebooks/tools-needed/type-safety-strategy.md`
-

### Skills System

Finance Guru uses 6 active workflow skills with automatic activation:

1. **skill-developer** (domain, block) - Skill system management
2. **error-tracking** (domain, suggest) - Sentry monitoring patterns
3. **portfolio-syncing** (domain, block) - Fidelity CSV imports to Google Sheets
4. **dividend-tracking** (domain, suggest) - Dividend portfolio sync and calculations
5. **margin-management** (domain, block) - Margin dashboard updates and alerts
6. **formula-protection** (guardrail, block) - Spreadsheet formula safety

**Configuration**: `.claude/skills/skill-rules.json`

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
