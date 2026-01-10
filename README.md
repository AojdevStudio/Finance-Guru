# Finance Guru™

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Powered-blueviolet)](https://claude.ai/claude-code)
[![Tools](https://img.shields.io/badge/analysis%20tools-11-green.svg)](#11-production-ready-analysis-tools)
[![Agents](https://img.shields.io/badge/AI%20agents-8-orange.svg)](#what-i-built)
[![License](https://img.shields.io/badge/license-Private-red.svg)](#security--privacy)

**Stop juggling 10 browser tabs for financial analysis. One command activates 8 AI specialists who work together as your private family office.**

![Architecture](docs/images/finance-guru-architecture.png)

---

## The Problem I Solved

I was drowning in complexity. Every investment decision meant:
- Opening Yahoo Finance for prices
- Switching to a spreadsheet for calculations
- Googling "how to calculate Sharpe ratio" (again)
- Copy-pasting data between 5 different tools
- Second-guessing myself because I couldn't see the full picture

**The real cost wasn't time—it was confidence.** I never felt certain my analysis was complete.

## The Insight

What if instead of me becoming an expert in everything, I could have a *team* of experts who already knew my portfolio, my risk tolerance, and my goals?

Not a chatbot. Not an app. A **personal family office** that treats me like a wealth management client—but built on AI agents that can actually run calculations.

## What I Built

Finance Guru™ is my private AI-powered family office. It's not software you install—it's a system where Claude transforms into specialized financial agents who work exclusively for me.

**One command:**
```bash
/finance-orchestrator
```

**Eight specialists activate:**

| Agent | Expertise | What They Do |
|-------|-----------|--------------|
| **Cassandra Holt** | Orchestrator | Coordinates the team, routes my requests |
| **Market Researcher** | Intelligence | Scans markets, identifies opportunities |
| **Quant Analyst** | Data Science | Runs calculations, builds models |
| **Strategy Advisor** | Portfolio | Optimizes allocations, validates strategies |
| **Compliance Officer** | Risk | Checks position limits, flags concerns |
| **Margin Specialist** | Leverage | Analyzes margin strategies safely |
| **Dividend Specialist** | Income | Optimizes yield, tracks distributions |
| **Tax Optimizer** | Efficiency | Structures holdings for tax advantage |

## See It In Action

**Me:** "Should I add more TSLA to my portfolio?"

**What happens behind the scenes:**
```bash
# Market Researcher checks momentum
uv run python src/utils/momentum_cli.py TSLA --days 90

# Quant Analyst calculates risk metrics
uv run python src/analysis/risk_metrics_cli.py TSLA --days 90 --benchmark SPY

# Quant Analyst checks market-implied risk
uv run python src/analysis/itc_risk_cli.py TSLA --universe tradfi

# Strategy Advisor checks correlation with existing holdings
uv run python src/analysis/correlation_cli.py TSLA PLTR NVDA --days 90

# Compliance Officer validates position size
# → Checks if addition exceeds concentration limits
```

**What I get:** A coordinated answer that considers momentum, risk, correlation, and compliance—not just a single data point.

## The Technical Foundation

### 11 Production-Ready Analysis Tools

Every tool follows the same bulletproof pattern:

```
Pydantic Models → Calculator Classes → CLI Interfaces
     ↓                    ↓                  ↓
 Type Safety         Business Logic      Agent Access
```

| Category | Tools | Key Metrics |
|----------|-------|-------------|
| **Risk** | Risk Metrics, ITC Risk | VaR, CVaR, Sharpe, Sortino, Max Drawdown, Beta, Alpha |
| **Technical** | Momentum, Moving Averages, Volatility | RSI, MACD, Golden Cross, Bollinger Bands, ATR |
| **Portfolio** | Correlation, Optimizer, Backtester | Diversification score, Max Sharpe, Risk Parity |
| **Options** | Options Pricer | Black-Scholes, Greeks, Implied Volatility |

### External Risk Intelligence

**ITC Risk Models API** integration provides market-implied risk scores:
- Real-time risk assessment for TSLA, AAPL, MSTR, NFLX, SP500, commodities
- Risk bands help agents validate entry/exit timing
- Complements internal quant metrics with external perspective

## Quick Start

### Prerequisites
```bash
# Claude Code (the orchestration platform)
curl -fsSL https://claude.ai/install.sh | bash

# Python 3.12+ with uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync
```

### Your First Analysis
```bash
# Activate Finance Guru
/finance-orchestrator

# Or go direct to a specialist
*agent quant            # "Analyze TSLA risk profile"
*agent strategy         # "Optimize my portfolio allocation"
*agent market-research  # "What's the momentum on NVDA?"
```

## Project Structure

```
family-office/
├── src/                      # Analysis engine
│   ├── analysis/             # Risk, correlation, options, ITC Risk
│   ├── strategies/           # Backtester, optimizer
│   ├── utils/                # Momentum, volatility, validators
│   └── models/               # Pydantic type definitions
├── scripts/                  # Automation
│   ├── reports/              # 21 report templates
│   ├── simulations/          # Monte Carlo, DRIP projections
│   └── rbp/                  # Autonomous execution framework
├── fin-guru/                 # Agent system
│   ├── agents/               # 8 specialist definitions
│   ├── tasks/                # Workflow configurations
│   └── data/                 # Knowledge base, user profile
└── docs/                     # Analysis outputs & guides
```

## Why This Approach Works

**Traditional tools** give you data. Finance Guru gives you **judgment**.

The difference:
- A stock screener tells you RSI is 75
- Finance Guru tells you "RSI is overbought, but your portfolio is underweight tech, and Compliance says you have room for a small position if Quant's risk metrics confirm"

**It's the coordination that creates value**—not any single calculation.

## Security & Privacy

- All data stays local on my machine
- No external access to financial information
- Portfolio data never leaves this repository
- This is a private system, not a service

## Built With

- **Claude Code** - Multi-agent orchestration
- **Python 3.12** - Analysis engine
- **Pydantic** - Type-safe validation
- **yfinance** - Market data
- **pandas/numpy/scipy** - Calculations
- **ITC Risk Models** - External risk intelligence

## Educational Disclaimer

Finance Guru™ is for educational purposes only. This is not investment advice. All investments carry risk, including potential loss of principal. Always consult licensed financial professionals before making investment decisions.

---

<p align="center">
  <strong>Finance Guru™ v2.0.0</strong><br>
  My AI-powered family office, working exclusively for me.
</p>
