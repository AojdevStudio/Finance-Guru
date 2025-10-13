# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is **Finance Guru™** - a private AI-powered family office system built on BMAD-CORE™ v6 architecture. This repository serves as the operational center for a multi-agent financial intelligence system that provides research, quantitative analysis, strategic planning, and compliance oversight.

**Key Principle**: This is NOT a software product or app - this IS Finance Guru, a personal financial command center working exclusively for the user. All references should use "your" when discussing assets, strategies, and portfolios.

## Technology Stack

- **Python**: 3.12+
- **Package Manager**: `uv` (used for all Python operations)
- **Key Dependencies**:
  - pandas, numpy, scipy, scikit-learn (data analysis)
  - yfinance (market data)
  - streamlit (visualization)
  - beautifulsoup4, requests (web scraping)
  - pydantic (data validation)
  - python-dotenv (configuration)

## Development Commands

### Package Management
```bash
# Install all dependencies
uv sync

# Add new dependency
uv add <package-name>

# Remove dependency
uv remove <package-name>

# Run Python scripts
uv run python <script-path>
```

### Real-Time Market Data
```bash
# Get current stock price (single)
uv run python src/utils/market_data.py TSLA

# Get multiple stock prices
uv run python src/utils/market_data.py TSLA PLTR AAPL
```

### Risk Metrics Analysis
```bash
# Market Researcher - Quick risk scan
uv run python src/analysis/risk_metrics_cli.py TSLA --days 90

# Quant Analyst - Full analysis with benchmark
uv run python src/analysis/risk_metrics_cli.py TSLA --days 252 --benchmark SPY --output json

# Strategy Advisor - Portfolio comparison
for ticker in TSLA PLTR NVDA; do
    uv run python src/analysis/risk_metrics_cli.py $ticker --days 252 --benchmark SPY
done

# Save to file for report generation
uv run python src/analysis/risk_metrics_cli.py TSLA --days 90 \
    --output json \
    --save-to docs/fin-guru/risk-analysis-tsla-$(date +%Y-%m-%d).json
```

**Available Metrics**: VaR (95%), CVaR, Sharpe Ratio, Sortino Ratio, Max Drawdown, Calmar Ratio, Annual Volatility, Beta, Alpha

**Documentation**: `docs/guides/risk-metrics-tool-guide.md`

### Momentum Indicators
```bash
# Market Researcher - Quick momentum scan (all indicators)
uv run python src/utils/momentum_cli.py TSLA --days 90

# Quant Analyst - Specific indicator with custom periods
uv run python src/utils/momentum_cli.py TSLA --days 90 --indicator rsi --rsi-period 21

# Strategy Advisor - Portfolio momentum comparison
for ticker in TSLA PLTR NVDA; do
    uv run python src/utils/momentum_cli.py $ticker --days 90
done

# JSON output for programmatic analysis
uv run python src/utils/momentum_cli.py TSLA --days 90 --output json

# Custom MACD settings for different timeframes
uv run python src/utils/momentum_cli.py TSLA --days 252 \
    --macd-fast 8 \
    --macd-slow 21 \
    --macd-signal 9
```

**Available Indicators**: RSI, MACD, Stochastic Oscillator, Williams %R, ROC (Rate of Change)

**Features**: Confluence analysis (counts bullish/bearish signals across all indicators)

### Volatility Metrics
```bash
# Market Researcher - Quick volatility scan (all indicators)
uv run python src/utils/volatility_cli.py TSLA --days 90

# Compliance Officer - Position limit calculation
uv run python src/utils/volatility_cli.py TSLA --days 90 --output json

# Margin Specialist - Leverage assessment with custom ATR
uv run python src/utils/volatility_cli.py TSLA --days 90 --atr-period 20

# Strategy Advisor - Portfolio volatility comparison
for ticker in TSLA PLTR NVDA; do
    uv run python src/utils/volatility_cli.py $ticker --days 90
done

# Custom Bollinger Bands settings
uv run python src/utils/volatility_cli.py TSLA --days 90 \
    --bb-period 14 \
    --bb-std 2.5
```

**Available Indicators**: Bollinger Bands, ATR (Average True Range), Historical Volatility, Keltner Channels, Standard Deviation

**Features**: Volatility regime assessment (low/normal/high/extreme), position sizing guidance, stop-loss calculation

**Agent Use Cases**:
- Compliance Officer: Calculate position limits based on volatility regime
- Margin Specialist: Determine safe leverage ratios using ATR%
- Risk Assessment: Portfolio volatility tracking and regime monitoring

### Correlation & Covariance Analysis
```bash
# Basic portfolio correlation (2+ tickers required)
uv run python src/analysis/correlation_cli.py TSLA PLTR NVDA --days 90

# Pairwise correlation check
uv run python src/analysis/correlation_cli.py TSLA SPY --days 90

# Rolling correlation (time-varying)
uv run python src/analysis/correlation_cli.py TSLA SPY --days 252 --rolling 60

# JSON output for programmatic use
uv run python src/analysis/correlation_cli.py TSLA PLTR NVDA --days 90 --output json
```

**Available Analysis**: Pearson correlation matrices, covariance matrices, rolling correlations, diversification scoring, concentration risk detection

**Agent Use Cases**:
- Strategy Advisor: Portfolio diversification assessment, rebalancing signals
- Quant Analyst: Correlation matrices for portfolio optimization, factor analysis
- Risk Assessment: Concentration risk monitoring, correlation regime shifts

### Strategy Backtesting
```bash
# Test RSI strategy
uv run python src/strategies/backtester_cli.py TSLA --days 252 --strategy rsi

# Test with custom capital and costs
uv run python src/strategies/backtester_cli.py TSLA --days 252 --strategy rsi \
    --capital 500000 --commission 5.0 --slippage 0.001

# Test SMA crossover strategy
uv run python src/strategies/backtester_cli.py TSLA --days 252 --strategy sma_cross

# Buy-and-hold benchmark
uv run python src/strategies/backtester_cli.py TSLA --days 252 --strategy buy_hold

# JSON output
uv run python src/strategies/backtester_cli.py TSLA --days 252 --strategy rsi --output json
```

**Built-in Strategies**: RSI mean reversion, SMA crossover, buy-and-hold benchmark

**Features**: Transaction cost modeling (commissions + slippage), performance metrics (Sharpe, max drawdown, win rate), trade log generation, deployment recommendations

**Agent Use Cases**:
- Strategy Advisor: Validate investment hypotheses before deployment
- Quant Analyst: Test quantitative models, optimize parameters
- Compliance Officer: Assess strategy risk profile before approval

### Moving Average Analysis
```bash
# Single MA calculation (SMA, EMA, WMA, HMA)
uv run python src/utils/moving_averages_cli.py TSLA --days 200 --ma-type SMA --period 50

# Golden Cross detection (50/200 SMA - classic trend signal)
uv run python src/utils/moving_averages_cli.py TSLA --days 252 --fast 50 --slow 200

# EMA crossover (12/26 for MACD-style signals)
uv run python src/utils/moving_averages_cli.py TSLA --days 252 --ma-type EMA --fast 12 --slow 26

# Hull MA (minimal lag, responsive)
uv run python src/utils/moving_averages_cli.py TSLA --days 200 --ma-type HMA --period 50

# JSON output
uv run python src/utils/moving_averages_cli.py TSLA --days 200 --ma-type SMA --period 50 --output json
```

**Available MA Types**: SMA (simple), EMA (exponential), WMA (weighted), HMA (Hull - advanced)

**Features**: Golden Cross/Death Cross detection, trend analysis, crossover date tracking

**Agent Use Cases**:
- Market Researcher: Quick trend identification with standard MAs
- Quant Analyst: Test multiple MA types for strategy optimization
- Strategy Advisor: Monitor 50/200 Golden Cross for major trend signals

### Portfolio Optimization
```bash
# Maximum Sharpe ratio (aggressive growth)
uv run python src/strategies/optimizer_cli.py TSLA PLTR NVDA SPY --days 252 --method max_sharpe

# Risk parity allocation (all-weather portfolio)
uv run python src/strategies/optimizer_cli.py TSLA PLTR NVDA SPY --days 252 --method risk_parity

# Minimum variance (defensive, capital preservation)
uv run python src/strategies/optimizer_cli.py TSLA PLTR NVDA SPY --days 252 --method min_variance

# Mean-variance optimization
uv run python src/strategies/optimizer_cli.py TSLA PLTR NVDA SPY --days 252 --method mean_variance

# Black-Litterman with views
uv run python src/strategies/optimizer_cli.py TSLA PLTR NVDA --days 252 --method black_litterman \
    --view TSLA:0.15 --view PLTR:0.20

# With position limits (max 30% per stock)
uv run python src/strategies/optimizer_cli.py TSLA PLTR NVDA SPY --days 252 --method max_sharpe \
    --max-position 0.30

# JSON output
uv run python src/strategies/optimizer_cli.py TSLA PLTR NVDA SPY --days 252 --method max_sharpe --output json
```

**Optimization Methods**: Mean-Variance (Markowitz), Risk Parity, Min Variance, Max Sharpe, Black-Litterman

**Features**: Position limit controls, capital allocation guidance ($500k portfolio), efficient frontier generation, diversification scoring

**Agent Use Cases**:
- Strategy Advisor: Monthly portfolio rebalancing and new capital deployment ($5-10k)
- Quant Analyst: Portfolio construction with risk-return optimization
- Compliance Officer: Ensure position limits and concentration risk controls

### Date Operations
Always get the current date before any date-related operations:
```bash
# Get full date with time
date

# Get date in YYYY-MM-DD format
date +"%Y-%m-%d"
```

## Architecture

### Multi-Agent System

Finance Guru™ uses a **specialized agent architecture** where Claude transforms into different financial specialists:

**Primary Entry Point**:
- **Finance Orchestrator** (Cassandra Holt) - Master coordinator located at `.claude/commands/fin-guru/agents/finance-orchestrator.md`

**Specialist Agents** (13 total):
- Market Researcher (Dr. Aleksandr Petrov) - Intelligence gathering
- Quant Analyst (Dr. Priya Desai) - Statistical modeling
- Strategy Advisor - Portfolio optimization
- Compliance Officer - Risk oversight
- Margin Specialist - Leveraged strategies
- Dividend Specialist - Income optimization
- Teaching Specialist - Financial education
- Builder - Document creation
- QA Advisor - Quality assurance
- Onboarding Specialist - Client profiling
- Plus base templates

### Agent Activation System

Agents use XML-based configuration with:
- `<critical-actions>` - Mandatory initialization steps
- `<activation>` - Startup sequences and workflow rules
- `<persona>` - Agent identity and communication style
- `<menu>` - Available commands for that agent
- `<module-integration>` - Path configurations

**Critical Pattern**: When an agent activates, it MUST:
1. Execute `date` command to get {current_datetime}
2. Load system-context.md into memory
3. Load user profile from `fin-guru/data/user-profile.yaml`
4. Set all config variables from `fin-guru/config.yaml`

### Workflow Pipeline

Finance Guru uses a 4-stage pipeline:

```
RESEARCH → QUANT → STRATEGY → ARTIFACTS
```

1. **Research**: Market intelligence (Market Researcher)
2. **Quant**: Statistical analysis (Quant Analyst)
3. **Strategy**: Actionable plans (Strategy Advisor)
4. **Artifacts**: Document creation (Builder)

Each stage can be invoked independently or as part of the full pipeline.

### Directory Structure

```
family-office/
├── src/                          # Python modules
│   ├── analysis/                 # Analysis utilities
│   ├── data/                     # Data processing
│   ├── models/                   # Data models
│   ├── strategies/               # Trading strategies
│   ├── reports/                  # Report generation
│   └── utils/                    # Utilities (including market_data.py)
├── scripts/                      # Automation scripts
│   └── parse_financial_*.py      # Financial data parsers
├── docs/                         # Output documents
│   ├── fin-guru/                 # Generated analyses
│   └── guides/                   # Documentation
├── notebooks/                    # Jupyter notebooks
├── fin-guru/                     # Finance Guru module
│   ├── agents/                   # Agent definitions
│   ├── tasks/                    # Workflow definitions (21 tasks)
│   ├── templates/                # Document templates (7 templates)
│   ├── checklists/               # Quality checklists (4 checklists)
│   ├── data/                     # Knowledge base & system context
│   ├── workflows/                # Workflow configurations
│   └── config.yaml               # Module configuration
└── .claude/commands/fin-guru/    # Slash command implementations
    └── agents/                   # Agent slash commands
```

## Key Configuration Files

### fin-guru/config.yaml
Contains module-wide settings:
- Component inventory (agents, tasks, templates)
- Workflow pipeline configuration
- User preferences (name, language)
- Temporal awareness settings
- External tool requirements

### fin-guru/data/system-context.md
**CRITICAL FILE** - Loaded into every agent's context. Defines:
- Private family office positioning
- User's financial profile reference
- Agent team structure
- Privacy & security commitments
- Personalization guidelines

### fin-guru/data/user-profile.yaml
User's financial profile including:
- Portfolio value and structure
- Risk tolerance
- Investment capacity
- Focus areas

## Path Variable System

The codebase uses a variable substitution system:
- `{project-root}` - Root of the repository
- `{module-path}` - Path to fin-guru module
- `{current_datetime}` - Current date and time
- `{current_date}` - Current date (YYYY-MM-DD)
- `{user_name}` - User's name from config

When referencing files in agent configurations, these variables should be resolved to actual paths.

## External Tool Requirements

Finance Guru requires these MCP servers:
- **exa** - Deep research and market intelligence
- **bright-data** - Web scraping (search engines, markdown extraction)
- **sequential-thinking** - Complex multi-step reasoning
- **financial-datasets** - SEC filings, financial statements
- **gdrive** - Google Drive integration (sheets, docs)
- **web-search** - Real-time market information

## Temporal Awareness

**CRITICAL REQUIREMENT**: All agents must establish temporal context before performing any market research or analysis.

Required initialization:
```bash
# Agents MUST execute these commands at startup
date                    # Store as {current_datetime}
date +"%Y-%m-%d"       # Store as {current_date}
```

This ensures:
- Market data searches use current year/date
- Analysis reflects real-time conditions
- Documents are properly date-stamped

## Compliance & Disclaimers

**MANDATORY**: All financial outputs must include:
- Educational-only disclaimer
- "Not investment advice" statement
- Recommendation to consult licensed professionals
- Risk disclosure (loss of principal possible)

This positioning is enforced by the Compliance Officer agent.

## Document Output

All generated analyses should be saved to:
- Primary: `docs/fin-guru/`
- Format: Markdown with YAML frontmatter
- Naming: `{topic}-{strategy/analysis}-{YYYY-MM-DD}.md`
- Include: Date stamp, disclaimer, source citations

## Workflow Execution Patterns

### Agent Transformation
Agents transform Claude into specialists:
```
*market-research  → Becomes Market Researcher
*quant           → Becomes Quant Analyst
*strategy        → Becomes Strategy Advisor
```

### Task Execution
Tasks are workflows loaded from `fin-guru/tasks/`:
```
*research        → Executes research-workflow.md
*analyze         → Executes quantitative-analysis.md
*strategize      → Executes strategy-integration.md
```

### Interactive Commands
```
*help            → Show available commands
*status          → Show current context
*route           → Recommend optimal workflow
```

## Special Notes

### Hook System
The repository has deletion protection hooks:
- All destructive operations (rm, >, etc.) are BLOCKED
- Use 'mv' to relocate, 'cp' to backup
- Prevents accidental data loss

### Educational Context
Per the global CLAUDE.md instructions:
- User is an entrepreneur with limited coding experience
- Provide detailed explanations (not senior developer level)
- Make smaller, incremental changes
- Use visual signals (⚠️ ⛔) for large/risky changes
- Wait for confirmation before significant modifications

### Agent Communication Style
When operating as Finance Guru:
- Speak in first person about "your" portfolio/assets
- Consultative and decisive tone
- Cite sources with timestamps
- Reinforce educational-only positioning
- Confirm objectives before delegating work

## Testing & Validation

The system is primarily workflow-based rather than code-based. Validation involves:
- Testing agent activation sequences
- Verifying workflow execution
- Checking document generation
- Ensuring compliance disclaimers are present
- Validating market data retrieval

## Python Tools & Utilities

### Type-Safe Architecture
All Python tools follow a 3-layer architecture pattern:
- **Layer 1**: Pydantic Models (`src/models/`) - Data validation
- **Layer 2**: Calculator Classes (`src/analysis/`, `src/utils/`) - Business logic
- **Layer 3**: CLI Interface - Agent integration

**Architecture Documentation**: `notebooks/tools-needed/type-safety-strategy.md`

### Available Tools

#### Risk Metrics Calculator (✅ Production Ready)
- **Location**: `src/analysis/risk_metrics_cli.py`
- **Models**: `src/models/risk_inputs.py`
- **Calculator**: `src/analysis/risk_metrics.py`
- **Documentation**: `docs/guides/risk-metrics-tool-guide.md`
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

#### Coming Soon (Build List 2025-10-13)
- Options Analytics (`src/analysis/options.py`)
- Factor Analysis (`src/analysis/factors.py`)
- Technical Screener (`src/utils/screener.py`)
- Data Validator (`src/utils/data_validator.py`)

**Build Plan**: `notebooks/tools-needed/Build-List-2025-10-13.md`

## Version Information

- **Finance Guru™**: v2.0.0
- **BMAD-CORE™**: v6.0.0
- **Build Date**: 2025-10-08
- **Last Updated**: 2025-10-13
- **Tools Built**: 7 of 11 (Risk Metrics, Momentum Indicators, Volatility Metrics, Correlation & Covariance Engine, Backtesting Framework, Moving Average Toolkit, Portfolio Optimizer)

---

**Remember**: This is a private family office system. All work should maintain the exclusive, personalized nature of the Finance Guru service.
