# Buy Ticket Workflow Patterns — Expanded Reference

Read this when SKILL.md's 10-step workflow needs more detail, especially for graceful degradation paths or edge cases.

## Step 2 Detail: Portfolio Context Loading

### Finding the latest CSV

The fin-core hook's existing logic: sort `notebooks/updates/Portfolio_Positions_*.csv` by date-in-filename (format `Portfolio_Positions_MMM-DD-YYYY.csv`), take the most recent. `ls -t` works because filename dates correlate with modification dates, but the authoritative sort is parsing the `MMM-DD-YYYY` from the filename.

### What to extract

From positions CSV:
- `Account Name` (Individual, ROTH, Cash, Margin) — used to identify the correct account
- `Symbol`, `Quantity`, `Last Price`, `Current Value` — used for share counts and price fallback
- `Average Cost Basis`, `Total Gain/Loss $` — not required for buy ticket, useful for rationale
- Pending orders — should be zero in a clean CSV

From balances CSV (if available, `Balances_for_Account_{id}.csv`):
- Margin debit
- Buying power
- Cash balance
- Margin interest rate

### Concentration calculation

```
concentration_pct = position_market_value / total_portfolio_value
```

Flag any position > 25% as a potential concentration warning even before the new deployment.

## Step 3 Detail: Price Snapshot

### `market_data.py` command surface

```bash
# Batch (preferred for buy tickets with multiple tickers)
uv run python src/utils/market_data.py TSLA PLTR NVDA

# Single ticker
uv run python src/utils/market_data.py JEPI

# Real-time via Finnhub (requires FINNHUB_API_KEY in .env; free tier 60 calls/min)
uv run python src/utils/market_data.py JEPI --realtime
```

Output is JSON-ish (pydantic model dump): `symbol`, `price`, `change`, `change_percent`, `timestamp`, `source` (yfinance or finnhub).

### Graceful degradation paths

If market_data.py fails with circular-import or network error:

1. Use `Last Price` column from positions CSV.
2. Annotate `price_snapshot_as_of` with the CSV filename + the CSV timestamp (visible from CSV metadata or filename date).
3. Add a risk note: "Prices derived from portfolio CSV snapshot (market_data.py unavailable). Verify live prices at Fidelity before execution."

If yfinance returns stale data (weekend, holiday, after-hours):
- This is expected; yfinance returns last-close prices outside market hours
- Annotate accordingly: `price_snapshot_as_of: "YYYY-MM-DD 16:00 ET (last close, market closed)"`
- Warn the user if the deployment is time-sensitive

### When to use `--realtime`

- Volatile tickers (TSLA, PLTR, MSTR, NVDA) during market hours
- Deployments near-the-money for options hedges
- Time-of-day matters (close is different from open)

Skip `--realtime` for ETFs and stable dividend positions during market hours; yfinance is sufficient.

## Step 4 Detail: Allocation Math

### Fractional share handling

Fidelity supports fractional on most equities and most ETFs. Check:
- Single stocks: fractional supported
- Most ETFs: fractional supported
- Closed-end funds (CEFs): often NOT fractional — round down to whole shares
- Some thinly-traded ETFs: fractional may fail

If fractional isn't supported for a ticker, round down and put the residual cash either in the next ticker or in remaining cash buffer. Note the rounding in the ticket.

### Rounding tolerance

Sum of dollar amounts in the allocation table should match the deployment amount within ±$0.01. If it's off by more than a cent, there's a calculation bug — don't just round; find it.

## Step 5 Detail: ITC Universe

### Supported tickers (check `src/analysis/itc_risk_cli.py --help` for authoritative list)

**Tradfi**: TSLA, AAPL, MSTR, NFLX, META, GOOGL, MSFT, AMZN, NVDA, DXY, XAUUSD, and similar mega-caps + macro pairs.

**Crypto**: BTC, ETH, BNB, SOL, XRP, ADA, DOGE, and similar top-market-cap coins.

**Unsupported** (most Finance Guru tickers): JEPI, JEPQ, QQQI, SPYI, SCHD, DIVO, YMAX, AMZY, MSTY, QQQY, covered-call ETFs, most CEFs.

### ITC score interpretation

The ITC score is a composite risk indicator derived from implied volatility, term structure, correlation, and momentum. Thresholds:

- **0.0–0.3 🟢 LOW**: Normal risk regime. No buy-ticket advisory needed. Set `itc_risk_score: 0.XX` but omit the advisory block.
- **0.3–0.7 🟡 MEDIUM**: Elevated but not extreme. Mention in Risk Notes: "ITC score X.XX indicates moderate risk concentration". No reduced-position recommendation unless combined with other signals.
- **0.7–1.0 🔴 HIGH**: Risk concentration is extreme. Include the full ITC Advisory section. Recommend: (a) reduced position size by 30-50%, (b) staged entry over 2-3 tranches, (c) waiting for pullback / consolidation.

### When to omit the section entirely

Omit when `itc_applicability: unsupported` OR when the score is LOW and no advisory is materially useful. An empty "ITC Advisory" block adds noise.

## Step 6 Detail: Framework Citation Patterns

### For a Layer 2 reinforcement deployment

Cite:
- `margin-strategy.md` — Tier 1 Conservative band definition, utilization targets
- `dividend-framework.md` — Layer 2 income mandate, distribution sustainability criteria
- `modern-income-vehicles.md` — JEPI/JEPQ/QQQI/SPYI evaluation criteria, NAV-erosion tolerance

Example rationale line:
> "Framework (`margin-strategy.md`) Tier 1/Conservative at current 19.3% margin utilization. Tier 1 explicitly prefers quality covered-call ETFs (JEPI/QYLD/XYLD family) over YieldMax single-stock products."

### For a growth DCA deployment

Cite:
- `margin-strategy.md` — concentration limits, portfolio-layer mandates
- Any specific ticker research under `fin-guru-private/fin-guru/analysis/` if present

### For a rebalance

Cite:
- `margin-strategy.md`
- `cashflow-policy.md` — cash-buffer targets, paycheck deployment cadence
- Any portfolio-level rebalance policy if documented

## Step 8 Detail: Pre-Flight Gate Logic

### Cash buffer check

```
remaining_cash = current_cash - deployment_amount
if remaining_cash < 0:
    warn("Deployment exceeds current cash. Margin draw of ${abs(remaining_cash)} required.")
if remaining_cash < emergency_reserve_target:
    warn("Post-deployment cash ${remaining_cash} below emergency reserve target ${emergency_reserve_target}.")
```

Emergency reserve target is user-specific; check `fin-guru/data/user-profile.yaml` for `cash_buffer_target` or similar.

### Concentration check

```
for ticker in new_allocation:
    existing_value = positions.get(ticker, 0)
    new_value = existing_value + deployment[ticker]
    new_pct = new_value / (portfolio_value + deployment_total)
    if new_pct > 0.30:
        warn(f"{ticker} would be {new_pct:.1%} of portfolio post-deploy (>30% concentration limit)")
```

### Margin coverage check

```
monthly_dividend_income = sum(estimated_dividend_per_ticker)
monthly_margin_interest = margin_balance * margin_rate / 12
coverage_ratio = monthly_dividend_income / monthly_margin_interest
if coverage_ratio < 2.0:
    warn(f"Dividend coverage {coverage_ratio:.1f}× below 2× target. Margin interest may exceed dividend flow in stressed scenario.")
```

## Degraded Paths Summary

| Failure | Fallback | Annotation |
|---------|----------|------------|
| market_data.py circular import | CSV Last Price column | "market_data.py unavailable" in price_snapshot_as_of |
| No recent positions CSV | Ask user to export from Fidelity | Block until CSV available; do not guess positions |
| ITC CLI fails | Proceed without advisory | `itc_applicability: not-run` in frontmatter |
| Positions CSV > 2 days old | Ask user; proceed if confirmed | Add stale-data warning in Risk Notes |
| Monte Carlo unavailable | Proceed; omit success-probability | No annotation needed (field says "Monte Carlo validated when available") |
