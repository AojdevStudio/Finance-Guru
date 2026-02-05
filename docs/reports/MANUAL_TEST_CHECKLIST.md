---
title: "Manual Test Checklist"
description: "Comprehensive manual testing checklist for Finance Guru system validation"
category: reports
---

# Manual Test Checklist

> **Purpose**: Comprehensive manual testing checklist for Finance Guru™ system validation
>
> **Last Updated**: 2026-01-16
>
> **Version**: 1.0.0

---

## Table of Contents

1. [Pre-Testing Setup](#pre-testing-setup)
2. [System Architecture Tests](#system-architecture-tests)
3. [Financial Analysis Tools Tests](#financial-analysis-tools-tests)
4. [Agent System Tests](#agent-system-tests)
5. [Data Integration Tests](#data-integration-tests)
6. [UI/Dashboard Tests](#uidashboard-tests)
7. [Documentation & Compliance Tests](#documentation--compliance-tests)
8. [End-to-End Workflow Tests](#end-to-end-workflow-tests)
9. [Session Completion Tests](#session-completion-tests)

---

## Pre-Testing Setup

### Environment Verification

- [ ] Python 3.12+ installed and accessible
- [ ] `uv` package manager installed
- [ ] Virtual environment activated (`.venv`)
- [ ] All dependencies installed (`uv sync`)
- [ ] Required MCP servers configured:
  - [ ] exa
  - [ ] bright-data
  - [ ] sequential-thinking
  - [ ] financial-datasets
  - [ ] gdrive
  - [ ] web-search

### API Keys & Configuration

- [ ] `.env` file exists in project root
- [ ] All required API keys present:
  - [ ] Financial data API keys
  - [ ] MCP server credentials
  - [ ] Google Drive/Sheets credentials (if applicable)
- [ ] Test API connectivity: `uv run python src/utils/market_data.py SPY --days 5`

### Repository State

- [ ] Git repository initialized
- [ ] On correct branch (typically `main`)
- [ ] No uncommitted changes from previous sessions

---

## System Architecture Tests

### Core System Components

- [ ] **CLAUDE.md** exists and contains current configuration
- [ ] **BMAD-CORE™** version matches expected (v6.0.0)
- [ ] Finance Guru™ version correct (v2.0.0)
- [ ] All path variables resolve correctly:
  - [ ] `{project-root}`
  - [ ] `{module-path}`
  - [ ] `{current_datetime}` / `{current_date}`

### Directory Structure

- [ ] `src/` directory structure intact:
  - [ ] `src/analysis/`
  - [ ] `src/strategies/`
  - [ ] `src/utils/`
  - [ ] `src/models/`
  - [ ] `src/ui/`
  - [ ] `src/cli/`
- [ ] `fin-guru-private/` directory exists
- [ ] `notebooks/` directory exists
- [ ] `tests/` directory structure:
  - [ ] `tests/integration/`
  - [ ] `tests/onboarding/`
  - [ ] `tests/python/`
  
### Agent Infrastructure

- [ ] Finance Orchestrator command exists: `.claude/commands/fin-guru/agents/finance-orchestrator.md`
- [ ] All specialized agents accessible:
  - [ ] Market Researcher
  - [ ] Quant Analyst
  - [ ] Strategy Advisor
  - [ ] Compliance Officer
  - [ ] Margin Specialist
  - [ ] Dividend Specialist
  - [ ] Builder
  - [ ] Onboarding Specialist
  - [ ] QA Advisor
  - [ ] Teaching Specialist

---

## Financial Analysis Tools Tests

### Risk Metrics Tool

**Script**: `src/analysis/risk_metrics_cli.py`

- [ ] Single ticker execution: `uv run python src/analysis/risk_metrics_cli.py TSLA --days 90`
- [ ] Multiple tickers: `uv run python src/analysis/risk_metrics_cli.py TSLA PLTR NVDA`
- [ ] Custom benchmark: `uv run python src/analysis/risk_metrics_cli.py TSLA --benchmark QQQ`
- [ ] JSON output: `uv run python src/analysis/risk_metrics_cli.py TSLA --output json`
- [ ] Save to file: `uv run python src/analysis/risk_metrics_cli.py TSLA --save-to /tmp/risk.json`
- [ ] Verify metrics calculated:
  - [ ] VaR (Value at Risk)
  - [ ] CVaR (Conditional VaR)
  - [ ] Sharpe Ratio
  - [ ] Sortino Ratio
  - [ ] Maximum Drawdown
  - [ ] Calmar Ratio
  - [ ] Volatility
  - [ ] Beta
  - [ ] Alpha

### Momentum Indicators Tool

**Script**: `src/utils/momentum_cli.py`

- [ ] RSI calculation: `uv run python src/utils/momentum_cli.py TSLA --indicator rsi`
- [ ] MACD: `uv run python src/utils/momentum_cli.py TSLA --indicator macd`
- [ ] Stochastic: `uv run python src/utils/momentum_cli.py TSLA --indicator stochastic`
- [ ] Williams %R: `uv run python src/utils/momentum_cli.py TSLA --indicator williams`
- [ ] ROC: `uv run python src/utils/momentum_cli.py TSLA --indicator roc`
- [ ] Confluence: `uv run python src/utils/momentum_cli.py TSLA --indicator confluence`
- [ ] Custom periods: `uv run python src/utils/momentum_cli.py TSLA --indicator rsi --rsi-period 21`

### Volatility Analysis Tool

**Script**: `src/utils/volatility_cli.py`

- [ ] Bollinger Bands: `uv run python src/utils/volatility_cli.py TSLA --days 90`
- [ ] ATR: `uv run python src/utils/volatility_cli.py TSLA --atr-period 14`
- [ ] Historical Volatility calculation
- [ ] Keltner Channels
- [ ] Standard Deviation
- [ ] Volatility Regime detection
- [ ] Custom parameters: `uv run python src/utils/volatility_cli.py TSLA --bb-period 30 --bb-std 2.5`

### Correlation Analysis Tool

**Script**: `src/analysis/correlation_cli.py`

- [ ] Portfolio correlation matrix: `uv run python src/analysis/correlation_cli.py TSLA PLTR NVDA SPY`
- [ ] Minimum 2 tickers enforced
- [ ] Pearson correlation matrix output
- [ ] Covariance matrix
- [ ] Diversification score
- [ ] Concentration analysis
- [ ] Rolling correlation: `uv run python src/analysis/correlation_cli.py TSLA PLTR --rolling 30`

### Backtesting Tool

**Script**: `src/strategies/backtester_cli.py`

- [ ] RSI strategy: `uv run python src/strategies/backtester_cli.py TSLA --strategy rsi`
- [ ] SMA crossover: `uv run python src/strategies/backtester_cli.py TSLA --strategy sma_cross`
- [ ] Buy and hold baseline: `uv run python src/strategies/backtester_cli.py TSLA --strategy buy_hold`
- [ ] Custom capital: `uv run python src/strategies/backtester_cli.py TSLA --capital 100000`
- [ ] Commission/slippage: `uv run python src/strategies/backtester_cli.py TSLA --commission 0.001 --slippage 0.0005`
- [ ] Verify metrics:
  - [ ] Sharpe Ratio
  - [ ] Win Rate
  - [ ] Maximum Drawdown
  - [ ] Total Return
  - [ ] Trade count

### Moving Averages Tool

**Script**: `src/utils/moving_averages_cli.py`

- [ ] SMA: `uv run python src/utils/moving_averages_cli.py TSLA --ma-type sma --period 50`
- [ ] EMA: `uv run python src/utils/moving_averages_cli.py TSLA --ma-type ema --period 20`
- [ ] WMA: `uv run python src/utils/moving_averages_cli.py TSLA --ma-type wma`
- [ ] HMA: `uv run python src/utils/moving_averages_cli.py TSLA --ma-type hma`
- [ ] Golden/Death Cross: `uv run python src/utils/moving_averages_cli.py TSLA --fast 50 --slow 200`

### Portfolio Optimizer Tool

**Script**: `src/strategies/optimizer_cli.py`

- [ ] Max Sharpe: `uv run python src/strategies/optimizer_cli.py TSLA PLTR NVDA --method max_sharpe`
- [ ] Risk Parity: `uv run python src/strategies/optimizer_cli.py TSLA PLTR NVDA --method risk_parity`
- [ ] Min Variance: `uv run python src/strategies/optimizer_cli.py TSLA PLTR NVDA --method min_variance`
- [ ] Mean-Variance: `uv run python src/strategies/optimizer_cli.py TSLA PLTR NVDA --method mean_var`
- [ ] Black-Litterman: `uv run python src/strategies/optimizer_cli.py TSLA PLTR NVDA --method black_litterman --view TSLA:0.15`
- [ ] Position limits: `uv run python src/strategies/optimizer_cli.py TSLA PLTR NVDA --max-position 0.40`
- [ ] Verify allocation weights sum to 1.0

### ITC Risk Tool

**Script**: `src/analysis/itc_risk_cli.py`

- [ ] Crypto universe: `uv run python src/analysis/itc_risk_cli.py BTC --universe crypto`
- [ ] TradFi universe: `uv run python src/analysis/itc_risk_cli.py TSLA --universe tradfi`
- [ ] List supported assets: `uv run python src/analysis/itc_risk_cli.py --list-supported`
- [ ] Full table output: `uv run python src/analysis/itc_risk_cli.py TSLA --full-table`
- [ ] Verify metrics:
  - [ ] ITC Risk Score
  - [ ] Risk Band classification
  - [ ] High Risk Threshold
  - [ ] Price Context

---

## Agent System Tests

### Agent Activation

- [ ] Finance Orchestrator (Cassandra Holt) can be invoked
- [ ] Temporal awareness commands execute:
  - [ ] `date` command runs at startup
  - [ ] `date +"%Y-%m-%d"` provides correct format
- [ ] Agent personality traits functional per CORE skill

### Agent-Tool Matrix Validation

**Market Researcher Agent:**
- [ ] Can execute Momentum tools
- [ ] Can execute Moving Averages
- [ ] Can execute Risk Metrics
- [ ] Can execute ITC Risk
- [ ] Appropriate for quick scans and trend identification

**Quant Analyst Agent:**
- [ ] Has access to ALL analysis tools
- [ ] Can run deep analysis with custom parameters
- [ ] Can perform optimization tasks
- [ ] Can conduct factor analysis
- [ ] Can analyze ITC risk bands

**Strategy Advisor Agent:**
- [ ] Can use Portfolio Optimizer
- [ ] Can execute Backtesting
- [ ] Can run Correlation analysis
- [ ] Can assess ITC Risk
- [ ] Appropriate for portfolio construction and rebalancing

**Compliance Officer Agent:**
- [ ] Can access Volatility tools
- [ ] Can access Risk Metrics
- [ ] Can review Backtesting results
- [ ] Can enforce position limits

**Margin Specialist Agent:**
- [ ] Can use Volatility tools
- [ ] Can perform ATR-based position sizing
- [ ] Can assess leverage appropriateness

### Multi-Agent Workflows

- [ ] Orchestrator delegates tasks appropriately
- [ ] Agents can work in parallel on independent tasks
- [ ] Agent context switching maintains state
- [ ] Agent outputs follow structured format

---

## Data Integration Tests

### Market Data Retrieval

- [ ] Single ticker fetch: `uv run python src/utils/market_data.py TSLA`
- [ ] Multiple tickers: `uv run python src/utils/market_data.py TSLA PLTR AAPL GOOGL`
- [ ] Custom date ranges work
- [ ] Data validation passes (no NaN, correct columns)
- [ ] Caching mechanism (if implemented)

### Google Drive/Sheets Integration

- [ ] Can read from Google Sheets (if configured)
- [ ] Can write analysis results to Sheets
- [ ] Portfolio data sync functional
- [ ] Dividend tracking updates correctly

### CSV/Data Import

- [ ] Fidelity CSV import works
- [ ] Transaction history parsing
- [ ] Dividend data extraction
- [ ] Retirement account data sync

---

## UI/Dashboard Tests

### Streamlit Dashboard

**Launch**: `uv run streamlit run src/ui/app.py`

- [ ] Dashboard loads without errors
- [ ] Portfolio header displays correctly
- [ ] Ticker input widget functional
- [ ] Results panel displays
- [ ] Analysis runner service executes
- [ ] Portfolio loader service works
- [ ] Interactive elements respond
- [ ] Data refresh works
- [ ] Charts/visualizations render

### CLI Interface

**Launch**: `uv run python src/cli/fin_guru.py`

- [ ] CLI help menu displays
- [ ] Commands execute properly
- [ ] Error messages clear and actionable
- [ ] Output formatting consistent

---

## Documentation & Compliance Tests

### Output Document Validation

**Location**: `fin-guru-private/fin-guru/analysis/`

- [ ] Analysis reports follow naming convention: `{topic}-{YYYY-MM-DD}.md`
- [ ] Buy tickets named correctly: `buy-ticket-{YYYY-MM-DD}-{short-descriptor}.md`
- [ ] Strategy docs: `{strategy-name}-master-strategy.md`
- [ ] Monthly reports: `monthly-refresh-{YYYY-MM-DD}.md`

### Document Content Checklist

Every generated document must have:

- [ ] YAML frontmatter with metadata
- [ ] Date stamp in filename
- [ ] Compliance disclaimer: "Educational purposes only"
- [ ] Risk disclosure statement
- [ ] "Not investment advice" notice
- [ ] "Consult professionals" guidance
- [ ] Citations for data sources
- [ ] Markdown formatting valid

### Guide Documentation

- [ ] Risk Metrics Tool Guide: `fin-guru-private/guides/risk-metrics-tool-guide.md`
- [ ] Final 4 Tools Guide: `fin-guru-private/guides/final-4-tools-guide.md`
- [ ] Quantitative Analysis Tools: `fin-guru-private/guides/quantitative-analysis-tools.md`
- [ ] All guides up to date with current tool versions

---

## End-to-End Workflow Tests

### Portfolio Analysis Workflow

1. [ ] **Setup**: Define test portfolio (e.g., TSLA, PLTR, NVDA, SPY)
2. [ ] **Risk Assessment**: Run risk metrics on all tickers
3. [ ] **Correlation Analysis**: Check diversification
4. [ ] **Optimization**: Generate optimal allocation
5. [ ] **Backtesting**: Validate strategy historically
6. [ ] **Documentation**: Generate analysis report
7. [ ] **Compliance Review**: Verify all disclaimers present

### New Position Evaluation Workflow

1. [ ] **Market Research**: Run momentum indicators
2. [ ] **Risk Analysis**: Calculate risk metrics
3. [ ] **ITC Risk Check**: Determine risk band
4. [ ] **Volatility Assessment**: Check ATR and Bollinger Bands
5. [ ] **Strategy Validation**: Backtest entry strategy
6. [ ] **Buy Ticket Generation**: Create properly formatted buy ticket
7. [ ] **Compliance Sign-off**: Review risk profile

### Monthly Portfolio Refresh

1. [ ] **Data Collection**: Fetch latest market data for all holdings
2. [ ] **Performance Review**: Calculate returns and risk metrics
3. [ ] **Rebalancing Check**: Run optimizer to check drift
4. [ ] **Dividend Analysis**: Review income layer performance
5. [ ] **Risk Update**: Recalculate portfolio risk profile
6. [ ] **Report Generation**: Create monthly refresh document
7. [ ] **Archive**: Save to proper location with date stamp

### Monte Carlo Simulation (if implemented)

- [ ] 4-layer portfolio simulation runs
- [ ] Growth layer results
- [ ] Income layer projections
- [ ] Hedge layer performance
- [ ] GOOGL component analysis
- [ ] Auto-detection of current values from CSV
- [ ] Probability distributions valid

---

## Session Completion Tests

### Landing the Plane Checklist

**Critical**: Execute ALL steps before ending session

1. [ ] **File Remaining Work**
   - [ ] All follow-up tasks captured as issues
   - [ ] Task descriptions clear and actionable
   - [ ] Dependencies properly set
   - [ ] Priorities assigned

2. [ ] **Run Quality Gates** (if code changed)
   - [ ] Tests pass: `bun run test`
   - [ ] Type checking: `bun run typecheck`
   - [ ] Python tests (if applicable): `uv run pytest`
   - [ ] Linting clean

3. [ ] **Update Issue Status**
   - [ ] Completed issues closed
   - [ ] In-progress issues updated
   - [ ] Blocked issues marked
   - [ ] Dependencies verified

4. [ ] **PUSH TO REMOTE** (MANDATORY)
   ```bash
   git pull --rebase
   git push
   git status  # MUST show "up to date with origin"
   ```
   - [ ] `git push` succeeded
   - [ ] Remote is up to date
   - [ ] No uncommitted changes

5. [ ] **Clean Up**
   - [ ] Stashes cleared
   - [ ] Temporary files removed
   - [ ] Unused branches pruned

6. [ ] **Verify**
   - [ ] All changes committed
   - [ ] All commits pushed
   - [ ] No local-only work

7. [ ] **Hand Off**
   - [ ] Context documented for next session
   - [ ] Open issues clearly described
   - [ ] Next steps identified

---

## Test Execution Tracking

### Test Run Metadata

- **Tester Name**: ___________________
- **Test Date**: ___________________
- **Finance Guru Version**: ___________________
- **BMAD-CORE Version**: ___________________
- **Python Version**: ___________________
- **Test Environment**: (Local / Staging / Production)

### Pass/Fail Summary

| Test Category | Total Tests | Passed | Failed | Skipped | Notes |
|---------------|-------------|--------|--------|---------|-------|
| Pre-Testing Setup | | | | | |
| System Architecture | | | | | |
| Financial Tools | | | | | |
| Agent System | | | | | |
| Data Integration | | | | | |
| UI/Dashboard | | | | | |
| Documentation | | | | | |
| End-to-End Workflows | | | | | |
| Session Completion | | | | | |

### Issues Discovered

| Issue ID | Severity | Description | Test Category | Status |
|----------|----------|-------------|---------------|--------|
| | | | | |

### Sign-Off

- [ ] All critical tests passed
- [ ] Known issues documented
- [ ] System ready for use / deployment

**Tester Signature**: _____________________  **Date**: ___________________

---

## Appendix

### Common Test Tickers

- **Tech Growth**: TSLA, PLTR, NVDA, GOOGL
- **Market Benchmarks**: SPY, QQQ, IWM
- **Crypto** (if supported): BTC, ETH
- **Dividend**: KO, JNJ, PG
- **High Volatility**: GME, AMC, MARA

### Expected Output Formats

**Risk Metrics JSON**:
```json
{
  "ticker": "TSLA",
  "var_95": -0.0234,
  "cvar_95": -0.0312,
  "sharpe_ratio": 1.42,
  "sortino_ratio": 1.89,
  "max_drawdown": -0.1567
}
```

**Optimizer Allocation**:
```
TSLA: 35.2%
PLTR: 28.7%
NVDA: 22.4%
SPY: 13.7%
```

### Troubleshooting Reference

| Error Type | Likely Cause | Solution |
|------------|--------------|----------|
| Import errors | Missing dependencies | `uv sync` |
| API failures | Invalid/missing keys | Check `.env` file |
| Data fetch errors | Network/API issues | Retry, check API status |
| Tool execution fails | Wrong parameters | Check `--help` for tool |
| Agent not found | Missing agent file | Verify `.claude/commands/fin-guru/agents/` |

---

**Document Version**: 1.0.0
**Last Review**: 2026-01-16
**Next Review**: TBD
**Maintainer**: Finance Guru™ Team
