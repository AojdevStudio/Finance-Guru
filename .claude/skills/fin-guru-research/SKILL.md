---
name: fin-guru-research
description: Execute comprehensive market research workflows. Covers market intelligence gathering, sector analysis, security research, and competitive intelligence with temporal validation.
---

# Research Workflow Skill

Execute structured market research with source validation and temporal awareness.

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

## Requirements

- ALL web searches MUST include temporal qualifiers using current date context
- Separate verified data from assumptions with confidence levels
- Cite all sources with START/END tags and precise timestamps
- Flag data gaps relevant to downstream analysis
