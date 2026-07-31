# Finance Guru™ v2.0.0 - Release Notes

**Release Date**: October 8, 2025
**Build**: Private AI-Powered Family Office System
**Architecture**: BMAD-CORE™ v6

---

## Overview

Finance Guru™ v2.0.0 is a complete rewrite of personal financial analysis infrastructure. Instead of juggling multiple browser tabs and tools, you now have a coordinated team of AI specialists who understand your portfolio, risk tolerance, and investment goals.

**One command activates eight financial experts who work together as your private family office.**

---

## What's New in v2.0.0

### 🤖 Multi-Agent Financial Intelligence

Transform Claude into 8 specialized financial agents:

| Agent | Role | What They Do |
| ------- | ------ | -------------- |
| **Cassandra Holt** | Finance Orchestrator | Coordinates analysis across specialists |
| **Market Researcher** | Intelligence | Scans markets, identifies opportunities |
| **Quant Analyst** | Data Science | Runs calculations, builds models |
| **Strategy Advisor** | Portfolio Management | Optimizes allocations, validates strategies |
| **Compliance Officer** | Risk Management | Checks position limits, flags concerns |
| **Margin Specialist** | Leverage Analysis | Analyzes margin strategies safely |
| **Dividend Specialist** | Income Optimization | Optimizes yield, tracks distributions |
| **Tax Optimizer** | Tax Efficiency | Structures holdings for tax advantage |

### 🛠️ 11 Production-Ready Analysis Tools

Every tool follows a bulletproof 3-layer architecture (Pydantic Models → Calculator Classes → CLI):

**Risk Analysis:**
- Risk Metrics CLI - VaR, CVaR, Sharpe, Sortino, Max Drawdown, Beta, Alpha
- ITC Risk CLI - Market-implied risk scores and bands

**Technical Analysis:**
- Momentum CLI - RSI, MACD, Stochastic, Williams %R, ROC
- Moving Averages CLI - SMA, EMA, WMA, HMA, Golden/Death Cross
- Volatility CLI - Bollinger Bands, ATR, Historical Vol, Keltner Channels

**Portfolio Management:**
- Correlation CLI - Diversification scoring, Concentration metrics
- Portfolio Optimizer CLI - Max Sharpe, Risk Parity, Min Variance
- Backtester CLI - Strategy validation with performance metrics

**Options Analysis:**
- Options Pricer CLI - Black-Scholes pricing, Greeks, Implied Volatility

### 🚀 Interactive Onboarding System

First-time users are guided through a comprehensive financial assessment:

1. **Financial Profile Questionnaire**
   - Income sources and stability
   - Time horizon and goals
   - Investment experience level

2. **Risk Tolerance Assessment**
   - Portfolio volatility preferences
   - Loss tolerance scenarios
   - Leverage comfort levels

3. **Strategy Recommendations**
   - Personalized allocation guidance
   - Risk-appropriate position sizing
   - Income vs. growth strategy mix

4. **Automated Profile Generation**
   - YAML configuration created from responses
   - Portfolio strategy documented
   - Ready-to-use setup for all agents

### 📊 Smart Context Management

Finance Guru uses session-start hooks to inject:
- System configuration and agent definitions
- User profile with portfolio strategy
- Latest Fidelity balances and positions
- Domain knowledge via auto-activated skills

**Token efficiency**: With all Finance Guru context loaded, you still have **51% of your 200k context window free** for actual analysis work.

### 🔧 9 Finance Guru Skills

Skills auto-activate based on your prompts and provide specialized functionality:

- `fin-core` - Core Finance Guru system context
- `margin-management` - Margin Dashboard integration
- `PortfolioSyncing` - Fidelity CSV → Google Sheets sync
- `MonteCarlo` - Monte Carlo simulation runner
- `retirement-syncing` - Retirement account sync (Vanguard/Fidelity)
- `dividend-tracking` - Dividend data sync
- `FinanceReport` - PDF analysis report generator
- `TransactionSyncing` - Transaction history import
- `formula-protection` - Spreadsheet formula protection

### 🔒 Privacy-First Architecture

Finance Guru is designed to be **forked and used privately**:

- All financial data stays local on your machine
- Sensitive files protected by comprehensive .gitignore
- No external data transmission without explicit user action
- Pull upstream updates without touching your private configs
- User profile and portfolio data never committed to git

### 🧪 Comprehensive Testing

Quality gates ensure reliability:

- Unit tests for all calculator classes
- CLI integration tests
- Hook functionality tests (Bun-based)
- Gitignore protection tests
- Full setup flow integration tests
- Onboarding resume and idempotent re-run tests

---

## Technical Improvements

### Architecture
- **3-Layer Pattern**: Pydantic Models → Calculator Classes → CLI Interfaces
- **Type Safety**: Full Pydantic validation across all tools
- **CLI-First Design**: Heavy computation happens outside token context
- **Standardized Interfaces**: Consistent patterns across all 11 tools

### Performance
- **Bun Runtime**: Converted hooks to Bun for better performance
- **Token Efficiency**: Strategic context loading preserves workspace
- **Parallel Agent Execution**: Multiple specialists can work simultaneously

### Developer Experience
- **Automated Setup**: One script installs dependencies, creates structure, runs onboarding
- **Comprehensive Docs**: Setup guide, API reference, troubleshooting, contribution guidelines
- **Fork-Friendly**: Easy to customize without breaking upstream compatibility

---

## Getting Started

### Prerequisites

```bash
# Claude Code (orchestration platform)
curl -fsSL https://claude.ai/install.sh | bash

# Python 3.12+ with uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Bun (for onboarding and hooks)
curl -fsSL https://bun.sh/install | bash
```

### Installation

```bash
# Fork and clone the repository
git clone https://github.com/YOUR-USERNAME/family-office.git
cd family-office

# Run setup script (installs everything)
./setup.sh

# Start Claude Code
claude

# Activate the Onboarding Specialist
/fin-guru:agents:onboarding-specialist
```

**Current setup guide**: [docs/setup/SETUP.md](docs/setup/SETUP.md)

### First Analysis

After onboarding, activate Finance Guru:

```bash
# Full orchestrator
/fin-guru:agents:finance-orchestrator

# Or go direct to a specialist
*quant            # "Analyze TSLA risk profile"
*strategy         # "Optimize my portfolio allocation"
*market-research  # "What's the momentum on NVDA?"
```

---

## Integration Requirements

### Required MCP Servers

| MCP Server | Purpose |
| ------------ | --------- |
| **exa** | Market research, web intelligence |
| **bright-data** | Web scraping, data extraction |
| **sequential-thinking** | Complex financial reasoning |

### Optional MCP Servers

| MCP Server | Purpose |
| ------------ | --------- |
| **gdrive** | Google Sheets integration for portfolio tracking |
| **perplexity** | AI-powered search with citations |
| **financial-datasets** | Real-time market data feeds |
| **context7** | Framework documentation lookup |

### Optional APIs

All market data works via yfinance by default. These APIs are optional enhancements:

| API                 | Purpose                       | Free Tier    |
| ------------------- | ----------------------------- | ------------ |
| **Finnhub**         | Real-time intraday prices     | 60 calls/min |
| **ITC Risk Models** | External risk intelligence    | Contact ITC  |

See [docs/setup/api-keys.md](docs/setup/api-keys.md) for acquisition instructions.

---

## Migration Notes

### From Previous Versions

This is the first major release (v2.0.0). If you were using an earlier version:

1. **Backup your private data** (`fin-guru-private/`, `notebooks/updates/`)
2. **Run setup.sh** to reinstall dependencies and structure
3. **Run onboarding** to generate the new YAML profile format
4. **Update MCP configuration** with required servers

### Fork Model

If you've already forked Finance Guru:

```bash
# Add upstream remote (one-time)
git remote add upstream https://github.com/AojdevStudio/Finance-Guru.git

# Pull updates safely (won't touch your private configs)
git fetch upstream
git merge upstream/main
```

Your private data in `fin-guru-private/`, `notebooks/updates/`, and `.env` stays untouched.

---

## Known Limitations

- Tools: 8/11 tools complete per CLAUDE.md (3 in development)
- Market data limited to yfinance without API keys
- Options Pricer uses basic Black-Scholes (no exotic options)
- Backtester uses simple strategies (no ML-based strategies yet)

---

## Documentation

| Document | Description |
| ---------- | ------------- |
| [docs/setup/SETUP.md](docs/setup/SETUP.md) | Current setup guide |
| [docs/setup/api-keys.md](docs/setup/api-keys.md) | API key acquisition guide |
| [docs/setup/TROUBLESHOOTING.md](docs/setup/TROUBLESHOOTING.md) | Comprehensive troubleshooting |
| [docs/reference/api.md](docs/reference/api.md) | CLI tools reference |
| [docs/reference/hooks.md](docs/reference/hooks.md) | Transitional hook status |
| [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) | Contribution guidelines |
| [CHANGELOG.md](CHANGELOG.md) | Detailed change history |

---

## Support

- **Issues**: Report bugs at [GitHub Issues](https://github.com/AojdevStudio/Finance-Guru/issues)
- **Documentation**: Full docs at [docs/index.md](docs/index.md)
- **Troubleshooting**: See [TROUBLESHOOTING.md](docs/setup/TROUBLESHOOTING.md)

---

## Educational Disclaimer

Finance Guru™ is for educational purposes only. This is not investment advice. All investments carry risk, including potential loss of principal. Always consult licensed financial professionals before making investment decisions.

---

## License

Finance Guru is free software licensed under the **GNU Affero General Public License v3.0 (AGPLv3)**.

**You are free to:**
- ✅ Use Finance Guru for any purpose (personal, commercial, educational)
- ✅ Study, modify, and share the source code
- ✅ Distribute your modifications

**Under these conditions:**
- 📖 Source code must remain open (copyleft)
- 🌐 Network users get source access
- 📝 Changes must be documented
- 🔄 Derivatives must also be AGPLv3

See [LICENSE](LICENSE) for full legal terms.

---

<p align="center">
  <strong>Finance Guru™ v2.0.0</strong><br>
  Your AI-powered family office, working exclusively for you.
</p>

<p align="center">
  <sub>If Finance Guru helps you, please ⭐ star the repo!</sub>
</p>
