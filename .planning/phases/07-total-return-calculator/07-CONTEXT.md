# Phase 7: Total Return Calculator - Context

**Gathered:** 2026-02-17
**Status:** Ready for planning

<domain>
## Phase Boundary

CLI tool that calculates and compares total returns (price + dividends) across tickers with DRIP modeling. Directly addresses Sean's meeting insight: "You can't say a fund is down without counting distributions." Users can evaluate whether income funds (CLM, YMAX, MSTY, JEPI, etc.) are actually losing money or just appear that way by price return alone.

</domain>

<decisions>
## Implementation Decisions

### The "Verdict" Display
- Show both side-by-side columns (Price Return | Dividend Return | Total Return) AND a summary narrative line
- Summary line flags when price return is negative but total return flips positive — the "Sean insight" reframing
- Flag triggers on sign flip only (price negative, total positive) — not on any spread
- Show both dollar amounts and percentages: "$824 in distributions (+8.2%)"
- Dollar amounts require share count — auto-read from latest Portfolio_Positions CSV in notebooks/updates/
- Fallback to per-share math if no CSV found

### DRIP Modeling
- Show both "with DRIP" and "without DRIP" side-by-side by default — user sees compounding effect
- Period breakdown shows every individual dividend event: date, dividend/share, shares acquired, running total
- Full granularity even for weekly payers (QQQY) — list every event, not monthly rollups
- Reinvestment price: ex-date close price from yfinance

### Data Sources
- yfinance for historical dividend data and historical prices
- Finnhub for current real-time prices (requires FINNHUB_API_KEY in .env)
- Graceful fallback: if Finnhub key not set, use yfinance for current prices too

### Data Quality
- Refuse to calculate when dividend data has gaps — show error with count of missing records and require --force flag to override
- Detect gaps via known dividend schedule lookup in config YAML (CLM=monthly, QQQY=weekly, SCHD=quarterly, etc.)
- Dividend schedules stored in a config YAML file in fin-guru-private/ (per-ticker metadata)
- Return-of-capital (ROC) not distinguished — total return counts all distributions equally (ROC is a tax concern, not a return concern)

### Multi-Ticker Comparison
- Results ranked by total return (best first, worst last)
- Explicitly call out tickers where price return is negative but total return flips positive — mark with indicator (e.g., "Price misleading")
- League table summary at bottom after individual breakdowns: #1 JEPI +12.3%, #2 CLM +4.2%, etc.
- Keep focused on price return + dividend return + total return — no yield efficiency analysis (separate tool)

### Claude's Discretion
- Exact table formatting and column widths
- Warning/error message wording
- How to handle tickers with zero dividends (growth stocks passed to the tool)
- --force flag behavior when overriding data quality refusal

</decisions>

<specifics>
## Specific Ideas

- Sean's meeting (2026-01-30): "You can't say it's down without dividends" — total return must include distributions. Analogy: judging rental property without counting rent checks.
- Action item from Sean: "Reassess fund 'down' flags only after total-return accounting is correct" — this tool directly enables that reassessment
- Key tickers for testing: CLM (-3.95% price, pays monthly), YMAX (-25.36% price, pays weekly), MSTY (-50.37% price, pays monthly) — all should show different story with distributions
- Portfolio CSV auto-read pattern: `notebooks/updates/Portfolio_Positions_*.csv` (latest by date in filename)

</specifics>

<deferred>
## Deferred Ideas

- Dividend yield efficiency analysis (high yield + NAV erosion detection) — separate analysis tool
- Financial-datasets MCP server integration for dividend data — available at agent-time but CLI needs standalone source
- ROC classification and tax-lot impact analysis — tax tooling, not return tooling

</deferred>

---

*Phase: 07-total-return-calculator*
*Context gathered: 2026-02-17*
