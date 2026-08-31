# GenerateSingleReport Workflow

Generate a single ticker analysis PDF report.

## Trigger Phrases
- "generate report for TSLA"
- "create PDF for PLTR"
- "make analysis report"

## Prerequisites
- Ticker symbol
- Current market data available
- Finance Guru CLI tools functional

## Workflow Steps

### Step 1: Gather Quantitative Data

Run Finance Guru CLI tools to collect metrics:

```bash
# Risk metrics (252-day lookback)
uv run python src/analysis/risk_metrics_cli.py {TICKER} --days 252 --output json > /tmp/{TICKER}_risk.json

# Momentum indicators (90-day)
uv run python src/utils/momentum_cli.py {TICKER} --days 90 --output json > /tmp/{TICKER}_momentum.json

# Volatility assessment
uv run python src/utils/volatility_cli.py {TICKER} --days 90 --output json > /tmp/{TICKER}_volatility.json
```

### Step 2: Fetch Market Sentiment (Perplexity MCP)

```python
# Search for analyst ratings and sentiment
mcp__perplexity__search(query=f"{TICKER} stock analyst ratings 2025")

# Get 2026 catalysts and risks
mcp__perplexity__reason(query=f"What are the key catalysts and risks for {TICKER} in 2026?")
```

### Step 3: Get Current Price Data

```bash
# Using yfinance via market_data utility
uv run python src/utils/market_data.py {TICKER}
```

### Step 4: Calculate Portfolio Sizing

Based on user profile ($250k default):
- Recommended allocation: 2-3% for moderate conviction
- Dollar amount: 2-3% of portfolio value
- Share count: Calculate from current price

### Step 5: Generate PDF Report

```bash
uv run python .claude/skills/FinanceReport/tools/ReportGenerator.py \
  --ticker {TICKER} \
  --portfolio-value 250000 \
  --output-dir fin-guru-private/fin-guru/analysis/reports/
```

Or programmatically build sections:

```python
from ReportGenerator import FinanceGuruReport

report = FinanceGuruReport(ticker=TICKER, portfolio_value=250000)

report.add_cover_page(
    title=f"{TICKER} Analysis",
    subtitle="2026 Watchlist",
    current_price=current_price,
    ytd_performance=ytd_pct
)

report.add_executive_summary(
    thesis=thesis_text,
    key_findings=findings_list,
    rating=rating,
    conviction=conviction,
    risk_level=risk
)

report.add_quant_analysis(risk_data, momentum_data, volatility_data)
report.add_portfolio_sizing(recommended_pct, current_price, entry_strategy)
report.add_sentiment_section(sentiment, ratings, catalysts, risks)

output_path = report.build()
```

### Step 6: Validate Output

- Confirm PDF exists at expected path
- Check file size (should be 20-50KB for 8-10 pages)
- Verify all sections rendered

## Output

PDF saved to: `fin-guru-private/fin-guru/analysis/reports/{TICKER}-analysis-{YYYY-MM-DD}.pdf`

## Error Handling

| Error | Resolution |
|-------|------------|
| CLI tool fails | Check ticker validity, retry with --days 90 |
| Perplexity timeout | Use cached data or skip sentiment |
| PDF generation fails | Check reportlab installation |

## Example

```
User: "Generate a report for NVDA"

1. Run risk_metrics_cli.py NVDA --days 252
   → Sharpe: 1.85, Beta: 1.45, Max DD: -22%

2. Run momentum_cli.py NVDA --days 90
   → RSI: 62, MACD: Bullish

3. Query Perplexity for sentiment
   → 25 Buy, 8 Hold, 2 Sell, Target: $165

4. Calculate sizing for $250k portfolio
   → 2.5% of portfolio = ~45 shares at $138

5. Generate PDF
   → fin-guru-private/fin-guru/analysis/reports/NVDA-analysis-2025-12-18.pdf (32KB)
```
