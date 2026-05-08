---
name: fin-core
description: |
  Finance Guru™ Core Context Loader

  Auto-loads essential Finance Guru system configuration and user profile at session start.
  Ensures complete context availability for all financial operations.
---

# Finance Guru™ Core Context

**Auto-loaded at every session start**

## Core Identity

**System Name**: Finance Guru™ v2.0.0
**Architecture**: BMAD-CORE™ v6.0.0
**Type**: Private Family Office AI System
**Owner**: Sole client (exclusive service)
**Purpose**: Institutional-grade multi-agent financial intelligence, quantitative analysis, strategic portfolio planning, and compliance oversight

**Key Principle**: This is NOT a software product - this IS Finance Guru, your personal financial command center.

---

## Essential Files (Auto-Loaded)

These files are automatically loaded into context at session start:

### 1. System Configuration
**Path**: `fin-guru/config.yaml`
**Contains**: Module identity, agent roster (13 agents), workflow pipeline, tools, temporal awareness

### 2. User Profile
**Path**: `fin-guru/data/user-profile.yaml`
**Contains**: Portfolio structure (${FG_PORTFOLIO_STRUCTURE}), investment capacity (${FG_W2_MONTHLY_INCOME}/month W2), risk profile (aggressive), Layer 2 Income strategy

### 3. Portfolio Updates
**Path**: `notebooks/updates/`
**Contains**: Latest Fidelity account balances, positions, transaction history

**File Patterns**:
- Balances: `Balances_for_Account_{account_id}.csv` (exact match)
- Positions: `Portfolio_Positions_MMM-DD-YYYY.csv` (e.g., `Portfolio_Positions_Nov-05-2025.csv`)
- The hook automatically finds the **latest positions file by date** in the filename
- Files older than 7 days trigger an update alert at session start

### 4. System Context
**Path**: `fin-guru/data/system-context.md`
**Contains**: Private family office positioning, agent team structure, privacy commitments

---

## Production-Ready Tools (7 Available)

All tools use 3-layer type-safe architecture (Pydantic → Calculator → CLI):

### Risk & Performance
1. **Risk Metrics** (`src/analysis/risk_metrics_cli.py`)
   VaR, CVaR, Sharpe, Sortino, Max Drawdown, Beta, Alpha

2. **Volatility Metrics** (`src/utils/volatility_cli.py`)
   Bollinger Bands, ATR, Historical Vol, Keltner Channels, regime assessment

### Technical Analysis
3. **Momentum Indicators** (`src/utils/momentum_cli.py`)
   RSI, MACD, Stochastic, Williams %R, ROC, confluence analysis

4. **Moving Averages** (`src/utils/moving_averages_cli.py`)
   SMA, EMA, WMA, HMA, Golden Cross/Death Cross detection

### Portfolio Construction
5. **Correlation & Covariance** (`src/analysis/correlation_cli.py`)
   Pearson correlation, covariance matrices, diversification scoring

6. **Portfolio Optimizer** (`src/strategies/optimizer_cli.py`)
   Mean-Variance, Risk Parity, Min Variance, Max Sharpe, Black-Litterman

7. **Backtesting Framework** (`src/strategies/backtester_cli.py`)
   Strategy validation, performance metrics, deployment recommendations

**Documentation**: See `CLAUDE.md` for usage examples and agent workflows

---

## Multi-Agent System

**Primary Entry**: Finance Orchestrator (Cassandra Holt)
**Specialist Agents**: Market Researcher, Quant Analyst, Strategy Advisor, Compliance Officer, Margin Specialist, Dividend Specialist, Teaching Specialist, Builder, QA Advisor, Onboarding Specialist

**Workflow Pipeline**: RESEARCH → QUANT → STRATEGY → ARTIFACTS

---

## Personal Strategy Inputs

Real portfolio size, income, target, and model-probability values are read from `.env` (see `.env.example`): `FG_PORTFOLIO_STRUCTURE`, `FG_W2_MONTHLY_INCOME`, `FG_ANNUAL_DIVIDEND_TARGET`, `FG_DIVIDEND_TARGET_MONTHS`, and `FG_MONTE_CARLO_PROBABILITY`. Do not hardcode personal numbers in this skill.

## Current Strategic Focus

**Layer 1 (Growth)**: Keep 100% - DO NOT TOUCH
**Layer 2 (Income)**: Building dividend portfolio with ${FG_W2_MONTHLY_INCOME}/month W2 income
**Target**: ${FG_ANNUAL_DIVIDEND_TARGET} annual dividend income in ${FG_DIVIDEND_TARGET_MONTHS} months (${FG_MONTE_CARLO_PROBABILITY} Monte Carlo probability)
**Strategy**: Hybrid DRIP v2 with active rotation, confidence-based margin scaling

---

## Temporal Awareness

**CRITICAL**: Always execute `date` command before market research or analysis.
Ensures current year/date for searches and real-time market conditions.

---

**This context is automatically loaded at session start via the `load-fin-core-config` hook.**
