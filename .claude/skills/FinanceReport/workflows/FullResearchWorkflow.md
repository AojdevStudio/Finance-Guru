# FullResearchWorkflow

Comprehensive 4-phase analysis workflow for thorough ticker research.

## Trigger Phrases
- "full analysis for AMZN"
- "thorough research on VGT"
- "deep dive into NVDA"
- "comprehensive analysis"

## Workflow Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 1: MARKET RESEARCH                                       │
│  └─ Perplexity/Exa → Company overview, catalysts, risks        │
├─────────────────────────────────────────────────────────────────┤
│  PHASE 2: QUANTITATIVE ANALYSIS                                 │
│  └─ CLI Tools → Risk metrics, momentum, volatility, correlation │
├─────────────────────────────────────────────────────────────────┤
│  PHASE 3: STRATEGY FORMULATION                                  │
│  └─ Synthesis → Buy/Hold/Sell, position sizing, entry strategy  │
├─────────────────────────────────────────────────────────────────┤
│  PHASE 4: REPORT GENERATION                                     │
│  └─ ReportGenerator → 8-10 page PDF with all findings           │
└─────────────────────────────────────────────────────────────────┘
```

## Phase 1: Market Research

### 1.1 Company Overview
```python
# Use Perplexity for comprehensive research
mcp__perplexity__search(
    query=f"{TICKER} company overview business model market position 2025"
)
```

### 1.2 2026 Catalysts
```python
mcp__perplexity__reason(
    query=f"What are the key growth catalysts for {TICKER} in 2026? Consider product launches, market expansion, regulatory changes, and competitive dynamics."
)
```

### 1.3 Risk Assessment
```python
mcp__perplexity__search(
    query=f"{TICKER} stock risks challenges headwinds 2025 2026"
)
```

### 1.4 Analyst Ratings
```python
mcp__perplexity__search(
    query=f"{TICKER} analyst ratings price targets buy sell hold consensus"
)
```

## Phase 2: Quantitative Analysis

### 2.1 Risk Metrics (252-Day)
```bash
uv run python -m src.analysis.risk_metrics_cli {TICKER} --days 252 --benchmark SPY
```

**Metrics Extracted:**
- Sharpe Ratio (risk-adjusted return)
- Sortino Ratio (downside-adjusted)
- Beta (market correlation)
- Alpha (excess return)
- Max Drawdown (worst peak-to-trough)
- VaR 95% (value at risk)
- CVaR (conditional VaR)

### 2.2 Momentum Indicators (90-Day)
```bash
uv run python -m src.utils.momentum_cli {TICKER} --days 90
```

**Metrics Extracted:**
- RSI (14-period)
- MACD (12/26/9)
- Stochastic %K/%D
- Williams %R
- ROC (rate of change)

### 2.3 Volatility Assessment
```bash
uv run python -m src.utils.volatility_cli {TICKER} --days 90
```

**Metrics Extracted:**
- Annualized Volatility
- ATR (14-period)
- Bollinger Band Width
- Volatility Regime (High/Normal/Low)

### 2.4 Portfolio Correlation (Optional)
```bash
# Against existing holdings
uv run python -m src.analysis.correlation_cli {TICKER} PLTR TSLA NVDA VOO --days 252
```

## Phase 3: Strategy Formulation

### 3.1 Synthesize Findings

Create investment thesis integrating:
- Fundamental outlook (from research)
- Technical setup (from quant)
- Risk/reward profile

### 3.2 Rating Decision Matrix

| Factor | Weight | Criteria |
|--------|--------|----------|
| Sharpe Ratio | 20% | >1.5 = Strong, >1.0 = Good, <0.5 = Weak |
| Momentum | 20% | RSI 40-60 = Neutral, <30 = Oversold, >70 = Overbought |
| Volatility | 15% | <25% = Low, 25-40% = Normal, >40% = High |
| Catalysts | 25% | Quality and timing of growth drivers |
| Valuation | 20% | Relative to peers and historical |

### 3.3 Rating Output

| Rating | Criteria |
|--------|----------|
| **STRONG BUY** | Score >80%, multiple catalysts, favorable technicals |
| **BUY** | Score 65-80%, solid fundamentals |
| **CONDITIONAL BUY** | Score 50-65%, with specific conditions |
| **HOLD** | Score 40-50%, wait for better entry |
| **SELL** | Score <40%, deteriorating fundamentals |

### 3.4 Position Sizing

```python
# Based on $250k portfolio and conviction level
SIZING_MATRIX = {
    "STRONG BUY": 3.0,      # 3% of portfolio
    "BUY": 2.5,             # 2.5% of portfolio
    "CONDITIONAL BUY": 2.0, # 2% of portfolio
    "HOLD": 0,              # No new position
    "SELL": 0               # Exit existing
}
```

### 3.5 Entry Strategy

Define entry approach:
- **Scale-in**: 3 tranches (40% now, 30% on 5% dip, 30% on 10% dip)
- **Limit order**: Wait for specific price target
- **Immediate**: Full position at market

## Phase 4: Report Generation

### 4.1 Build Report Sections

```python
from ReportGenerator import FinanceGuruReport

report = FinanceGuruReport(ticker=TICKER, portfolio_value=250000)

# Cover page (VGT-style)
report.add_cover_page(
    title=f"{company_name}",
    subtitle="2026 Watchlist Analysis & Investment Recommendation",
    current_price=price,
    ytd_performance=ytd_pct,
    analyst_team=["Market Researcher", "Quant Analyst", "Strategy Advisor"]
)

# Executive Summary
report.add_executive_summary(
    thesis=thesis_text,
    key_findings=key_findings,
    rating=rating,
    conviction=conviction,
    risk_level=risk_level
)

# Quantitative Analysis
report.add_quant_analysis(
    risk_metrics=risk_data,
    momentum_data=momentum_data,
    volatility_data=vol_data
)

# Portfolio Sizing (with actual $ amounts)
report.add_portfolio_sizing(
    recommended_pct=sizing_pct,
    current_price=price,
    entry_strategy=entry_text
)

# Market Sentiment
report.add_sentiment_section(
    sentiment_summary=sentiment,
    analyst_ratings=ratings,
    catalysts=catalysts_list,
    risks=risks_list
)

# Build PDF
output_path = report.build()
```

### 4.2 Validate Output

- PDF exists and is 20-50KB
- All sections rendered
- No placeholder data
- Disclaimer included

## Complete Example

```
User: "Do a full analysis on AMZN for the 2026 watchlist"

PHASE 1: Market Research
├─ Company: Amazon.com Inc, $2T market cap
├─ Business: AWS, Retail, Advertising
├─ Catalysts: AWS AI, advertising growth, margin expansion
└─ Risks: Antitrust, competition, labor costs

PHASE 2: Quant Analysis
├─ Risk: Sharpe 1.65, Beta 1.12, Max DD -18%
├─ Momentum: RSI 58, MACD Bullish
└─ Volatility: 28%, Normal regime

PHASE 3: Strategy
├─ Rating: STRONG BUY
├─ Conviction: 8.3/10
├─ Sizing: 3% of portfolio (33 shares at $226)
└─ Entry: Scale-in over 2 weeks

PHASE 4: Report
└─ Output: reports/AMZN-analysis-2025-12-18.pdf (35KB)
```
