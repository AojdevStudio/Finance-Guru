---
name: fin-guru-research
description: "Market research on a ticker, sector, or theme with dated sources, plus technical screening through the screener, moving-average, momentum, and volatility calculators. Use when the owner asks what is happening with a company, wants catalysts, risks, sector context, or a competitor comparison, or wants a screen for setups. Not for risk statistics (use fin-guru-quant-analysis) or position sizing (use fin-guru-strategize)."
---

# Research Workflow Skill

Execute structured market research with source validation and temporal awareness.

## Capability probe

Before data collection, follow the shared **[paid MCP capability probe](../_shared/PaidMcpCapabilityProbe.md)**. This workflow wants `exa` for deep semantic research and `bright-data` for pages that ordinary fetching cannot reach. If either is absent, announce the `WebSearch`/`WebFetch` fallback and its coverage caveat, or stop with the shared missing-capability message.

## Workflow Steps

1. **Scope Definition** — Clarify research objectives, timeframe, and deliverable format
2. **Data Collection** — Gather intelligence from multiple sources with temporal qualifiers
3. **Source Validation** — Flag market data older than same-day, economic data older than 30 days
4. **Analysis** — Apply analytical frameworks to collected data
5. **Synthesis** — Produce research summary with confidence levels and data gaps
6. **Handoff** — Package findings for downstream analysis (quant, strategy)

## Tools Integration

- `screener_cli.py` — Multi-pattern technical screening (8 patterns)
- `moving_averages_cli.py` — Trend identification (SMA/EMA/WMA/HMA)
- `momentum_cli.py` — Confluence analysis (RSI, MACD, Stochastic, Williams %R, ROC)
- `volatility_cli.py` — Regime analysis and opportunity assessment
- `data_validator_cli.py` — Data integrity verification (100% quality required)
- `itc_risk_cli.py` — Market-implied risk scores for supported tickers

## Output

Return the [`fin-guru-output-contract`](../fin-guru-output-contract/SKILL.md) skill. Cite each web source under Evidence with its publisher, date, and URL. A claim without a dated source goes under Assumptions and gaps, not under Bottom line.

## Requirements

- ALL web searches MUST include temporal qualifiers using current date context
- Separate verified data from assumptions with confidence levels
- Cite all sources with START/END tags and precise timestamps
- Flag data gaps relevant to downstream analysis
