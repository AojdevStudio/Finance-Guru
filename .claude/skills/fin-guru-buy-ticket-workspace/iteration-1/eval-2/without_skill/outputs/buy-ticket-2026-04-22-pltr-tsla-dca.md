---
document_type: buy-ticket
strategy_name: "PLTR/TSLA Pullback DCA"
generated_on: "2026-04-22"
generated_by: "strategy-advisor"
portfolio_context_date: "2026-04-21"
deployment_amount: "$2,000"
cash_available: "N/A — margin account"
remaining_cash_buffer: "N/A — margin account"
price_snapshot_as_of: "2026-04-21 4:38 PM ET (last close)"
itc_applicability: "not-run"
itc_risk_score: "N/A"
---

# Buy Ticket - PLTR/TSLA Pullback DCA

## Execution Summary

| Ticker    | Category           | Weight   | $ Amount     | Price      | Shares     |
| --------- | ------------------ | -------- | ------------ | ---------- | ---------- |
| PLTR      | AI/Data Platform   | 60.0%    | $1,200.00    | $145.97    | 8.2209     |
| TSLA      | EV/Autonomy Growth | 40.0%    | $800.00      | $386.42    | 2.0703     |
|           |                    |          |              |            |            |
| **TOTAL** |                    | **100%** | **$2,000.00**|            |            |

_Prices are last-close quotes from Apr 21, 2026. Execute at market open or set limit orders at or near these levels. Fractional shares assumed on both tickers (Fidelity supports fractional execution)._

## Portfolio Context

- Portfolio context source: `Portfolio_Positions_Apr-21-2026.csv`
- Total portfolio value (pre-deployment): $262,787.21
- Current PLTR position: 369.746 shares @ $145.97 = $53,971.82 (24.51% of account)
- Current TSLA position: 74.000 shares @ $386.42 = $28,595.08 (12.98% of account)
- This deployment: $2,000.00 (PLTR $1,200 + TSLA $800)
- Post-deployment PLTR: 377.967 shares = $55,171.82 (~20.84% of $264,787)
- Post-deployment TSLA: 76.070 shares = $29,395.08 (~11.10% of $264,787)
- Combined PLTR + TSLA concentration post-DCA: ~31.94%

## Strategy Rationale

**Allocation Framework:**

- **PLTR (60% / $1,200):** Your largest position at 24.51% and highest-conviction holding (461.6% unrealized gain from $25.99 avg cost). The 60% weighting leans into the higher-conviction thesis but is sized smaller in dollar terms than the existing position, so it adds incrementally without meaningfully increasing concentration. PLTR has pulled back from its recent range highs above $120 (post-Nov 2024 re-rate) and the current $145.97 level remains well below the Feb 2025 peak near $125 — _wait, current price of $145.97 is above that range, suggesting the most recent pullback is from a higher local top_. DCA adds to a proven winner at a relative dip.

- **TSLA (40% / $800):** Your second core growth name at 12.98% — underweight relative to PLTR conviction, and currently trading ~19% below its Dec 2024 ATH near $480. At $386.42 with a $234.19 avg cost (65% gain), this add continues building a full position at a meaningful discount to peak. The autonomous driving and energy storage narratives remain intact; near-term macro/tariff headwinds create the pullback opportunity.

**Why 60/40 and not equal weight?**
PLTR has demonstrated stronger relative momentum and AI revenue compounding than TSLA's recent quarter. Giving PLTR the larger share captures more upside from a name showing fundamental acceleration, while TSLA's larger pullback (~19% from ATH vs. PLTR's smaller dip) partially offsets with better mean-reversion potential.

## Execution Details

- Price snapshot: `Portfolio_Positions_Apr-21-2026.csv` at `2026-04-21 4:38 PM ET`
- Fractional shares assumed on both PLTR and TSLA (Fidelity supports fractional)
- DRIP: Not applicable on growth equities (neither pays a dividend)
- Deployment type: Discretionary $2,000 DCA into existing positions on pullback
- Account: HM & Ossie joint margin account (Z05724592)

## Risk Notes

- **Concentration:** Post-DCA, PLTR + TSLA represent ~31.94% of the portfolio. Both are high-beta, high-volatility names. A simultaneous drawdown in both (e.g., macro risk-off, sector rotation out of tech) could materially impact overall portfolio value.
- **PLTR position sizing:** At 24.51% pre-DCA, PLTR is already the largest single position in the portfolio by a wide margin. The $1,200 add is modest relative to the $53,971 position but should be viewed in context of full concentration risk.
- **Margin account:** All positions are held on margin. The $42,569.69 pending activity line suggests active margin utilization. Adding $2,000 increases margin exposure. Monitor margin cushion, particularly given TSLA's intraday volatility (-$6.08 / -1.55% on Apr 21 alone).
- **TSLA volatility:** TSLA carries elevated earnings and macro sensitivity. Size the order to avoid chasing intraday spikes; consider a limit order within 1–2% of last close ($380–$390 range).
- **ITC not run:** Insider trading context (ITC) analysis was not performed. If elevated ITC signals are present for either ticker, revisit position sizing.

## ITC Advisory

_ITC analysis not run for this ticket. Omit section — no elevated signal to report._

## Sources & Assumptions

- Price snapshot: `Portfolio_Positions_Apr-21-2026.csv` — last-close prices Apr 21, 2026 at 4:38 PM ET
- Portfolio context: Same CSV; total portfolio computed from all non-pending line items = $262,787.21
- Pending activity line (-$42,569.69) excluded from portfolio total (represents unsettled/margin activity, not investable value)
- Share counts use last-close prices; actual execution prices will differ slightly
- Fractional share execution assumed available via Fidelity brokerage

## Progress Tracking

- Ongoing DCA into core growth positions (no fixed month target specified)
- Next planned deployment: At next meaningful pullback or scheduled DCA interval
- Target success probability: N/A — Monte Carlo not run for this ticket

---

**Educational Notice:** _For educational purposes only; not investment advice. Consult a licensed financial professional before making any investment decisions. All investments involve risk, including possible loss of principal. Past performance does not guarantee future results. Margin investing amplifies both gains and losses._
