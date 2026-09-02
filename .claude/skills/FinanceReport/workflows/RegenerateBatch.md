# RegenerateBatch Workflow

Regenerate reports for multiple tickers using parallel subagents.

## Trigger Phrases
- "regenerate batch 1"
- "redo all reports"
- "regenerate watchlist reports"

## Prerequisites
- List of tickers to regenerate
- Subagent capability available
- Existing reports to replace

## Workflow Steps

### Step 1: Capture Batch Date

Compute the simulation date once before launching any subagents:

```bash
simulation_date=$(date +%Y-%m-%d)
```

Store that value as `{simulation_date}` and reuse it for every output in the batch.

### Step 2: Identify Tickers

**Batch 1 (Original 8):**
- CRWD, BRK.B, APLD, IREN, GOOG, MSFT, SOFI, VTV

**Batch 2 (Added 9):**
- VGT, NVDA, AVGO, PLTR, META, VRT, AMZN, FTNT, ARM

### Step 3: Launch Parallel Subagents

Use the Task tool to launch one subagent per ticker:

```python
# Launch 8 subagents in parallel (single message, multiple tool calls)
for ticker in ["CRWD", "BRKB", "APLD", "IREN", "GOOG", "MSFT", "SOFI", "VTV"]:
    Task(
        description=f"Generate {ticker} 2026 report",
        prompt=f"""
        Execute the FullResearchWorkflow for {ticker}:

        1. MARKET RESEARCH
           - Use Perplexity MCP to research company overview
           - Find 2026 catalysts and risks
           - Get analyst ratings

        2. QUANT ANALYSIS
           - Run: uv run python -m src.analysis.risk_metrics_cli {ticker} --days 252
           - Run: uv run python -m src.utils.momentum_cli {ticker} --days 90
           - Run: uv run python -m src.utils.volatility_cli {ticker} --days 90

        3. STRATEGY
           - Determine buy/hold/sell recommendation
           - Calculate position sizing for $250k portfolio
           - Define entry strategy

        4. GENERATE PDF
           - Build comprehensive 8-10 page report
           - Use VGT-style header
           - Include all quant data
           - Save to reports/{ticker}-analysis-{simulation_date}.pdf

        Follow the FinanceReport skill workflows.
        Replace existing PDF if present.
        """,
        subagent_type="general-purpose",
        model="sonnet"
    )
```

### Step 4: Monitor Completion

Each subagent will:
1. Complete full research workflow
2. Generate PDF report
3. Report back with summary

### Step 5: Validate All Reports

After all subagents complete:

```bash
# Check all reports exist
ls -la reports/*.pdf

# Verify file sizes
for f in reports/*.pdf; do
    size=$(wc -c < "$f")
    echo "$f: $size bytes"
done
```

### Step 6: Update Watchlist Document (Optional)

Update `analysis/2026-watchlist-{simulation_date}.md` with:
- Verdict summaries for each ticker
- Links to PDF reports
- Consolidated recommendations

## Batch Definitions

### Batch 1: Original Watchlist
```python
BATCH_1 = ["CRWD", "BRKB", "APLD", "IREN", "GOOG", "MSFT", "SOFI", "VTV"]
```

### Batch 2: Extended Watchlist
```python
BATCH_2 = ["VGT", "NVDA", "AVGO", "PLTR", "META", "VRT", "AMZN", "FTNT", "ARM"]
```

### Full Watchlist
```python
ALL_TICKERS = BATCH_1 + BATCH_2  # 17 total
```

## Performance Notes

- Each subagent takes ~3-5 minutes
- Parallel execution: 8 agents = same time as 1
- Total batch time: ~5 minutes for 8 tickers
- Full watchlist (17 tickers): ~10 minutes (2 batches)

## Error Handling

| Error | Resolution |
|-------|------------|
| Subagent timeout | Retry individual ticker |
| API rate limit | Add delay between batches |
| Report validation fails | Check logs, regenerate |

## Output

All PDFs saved to: `reports/`
File pattern: `{TICKER}-analysis-{YYYY-MM-DD}.pdf`
