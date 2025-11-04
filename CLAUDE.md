# CLAUDE.md

Finance Guru™ - Private AI-powered family office system built on BMAD-CORE™ v6.

**Key Principle**: This IS Finance Guru (not a product) - a personal financial command center. Use "your" when discussing assets/strategies/portfolios.

## Architecture

**Multi-Agent System**: Claude transforms into specialized financial agents
**Entry Point**: Finance Orchestrator (Cassandra Holt) - `.claude/commands/fin-guru/agents/finance-orchestrator.md`

**Path Variables**: `{project-root}`, `{module-path}`, `{current_datetime}`, `{current_date}`, `{user_name}`

**MCP Servers Required**: exa, bright-data, sequential-thinking, financial-datasets, gdrive, web-search

**Temporal Awareness**: All agents MUST run `date` and `date +"%Y-%m-%d"` at startup to establish temporal context

**Compliance**: All outputs must include educational-only disclaimer, "not investment advice", consult professionals, risk disclosure

## Technology Stack

- **Python**: 3.12+ | **Package Manager**: `uv`
- **Dependencies**: pandas, numpy, scipy, scikit-learn, yfinance, streamlit, beautifulsoup4, requests, pydantic, python-dotenv

**Architecture**: 3-layer pattern (Pydantic Models → Calculator Classes → CLI)
**Docs**: `notebooks/tools-needed/type-safety-strategy.md`, `.claude/tools/python-tools.md`

## CLI Command Patterns

**Base**: `uv run python <script> <ticker(s)> [flags]`

**Common Flags**: `--days N` (90=quarter, 252=year), `--output json`, `--benchmark SPY`

**Example Tickers**: TSLA, PLTR, NVDA, SPY

**Portfolio Loop**:
```bash
for ticker in TSLA PLTR NVDA; do
    uv run python <tool> $ticker [flags]
done
```

**Package Management**: `uv sync` (install), `uv add/remove <pkg>` (manage)

**Market Data**: `uv run python src/utils/market_data.py TSLA [PLTR AAPL ...]`

## Financial Analysis Tools

| Tool | Script Path | Metrics/Features | Unique Flags | Docs |
|------|-------------|------------------|--------------|------|
| **Risk Metrics** | `src/analysis/risk_metrics_cli.py` | VaR, CVaR, Sharpe, Sortino, Max DD, Calmar, Volatility, Beta, Alpha | `--benchmark SPY`, `--save-to <path>` | `docs/guides/risk-metrics-tool-guide.md` |
| **Momentum** | `src/utils/momentum_cli.py` | RSI, MACD, Stochastic, Williams %R, ROC, Confluence | `--indicator <type>`, `--rsi-period`, `--macd-*` | - |
| **Volatility** | `src/utils/volatility_cli.py` | Bollinger Bands, ATR, Historical Vol, Keltner, StdDev, Regime | `--atr-period`, `--bb-period`, `--bb-std` | - |
| **Correlation** | `src/analysis/correlation_cli.py` | Pearson matrix, Covariance, Diversification, Concentration | `--rolling <N>` (requires 2+ tickers) | - |
| **Backtesting** | `src/strategies/backtester_cli.py` | RSI, SMA cross, Buy-hold, Sharpe, Win rate, Drawdown | `--strategy <type>`, `--capital`, `--commission`, `--slippage` | - |
| **Moving Averages** | `src/utils/moving_averages_cli.py` | SMA, EMA, WMA, HMA, Golden/Death Cross | `--ma-type <type>`, `--period`, `--fast`, `--slow` | - |
| **Portfolio Optimizer** | `src/strategies/optimizer_cli.py` | Max Sharpe, Risk Parity, Min Variance, Mean-Var, Black-Litterman | `--method <type>`, `--max-position`, `--view <ticker:return>` | - |

## Agent-Tool Matrix

| Agent | Primary Tools | Use Cases |
|-------|--------------|-----------|
| **Market Researcher** | Momentum, Moving Averages, Risk Metrics | Quick scans, trend identification, initial risk assessment |
| **Quant Analyst** | All tools | Deep analysis, custom parameters, optimization, factor analysis |
| **Strategy Advisor** | Optimizer, Backtesting, Correlation | Portfolio construction, rebalancing, validation, diversification |
| **Compliance Officer** | Volatility, Risk Metrics, Backtesting | Position limits, risk profiles, strategy approval |
| **Margin Specialist** | Volatility | Leverage assessment, ATR-based position sizing |

## Output & Validation

**Document Output**: `docs/fin-guru/analysis/` | Format: Markdown + YAML frontmatter | Naming: `{topic}-{analysis}-{YYYY-MM-DD}.md` | Required: Date stamp, disclaimer, citations

**Validation Checklist**: Agent activation, workflow execution, document generation, compliance disclaimers, market data retrieval

## Version Info

**Finance Guru™**: v2.0.0 | **BMAD-CORE™**: v6.0.0 | **Build**: 2025-10-08 | **Updated**: 2025-10-13 | **Tools**: 7/11 complete

---

**Note**: Private family office system - maintain exclusive, personalized nature of Finance Guru service.
