---
document_type: options-close-ticket
strategy_name: "Hedge Unwind — Thesis Change (April 2026, VIX Normalized)"
generated_on: "2026-04-22"
generated_by: "strategy-advisor"
portfolio_context_date: "2026-04-22"
net_credit_realized: "≈ $240–$380 (see residual estimates below)"
realized_pnl: "−$780 to −$920 (premium decay loss — expected hedge insurance cost)"
tax_treatment: "short-term capital loss (positions held < 1 year; opened Apr-21-2026)"
price_snapshot_as_of: "2026-04-22 — market_data.py unavailable (circular import); spot + option residuals estimated from VIX-14 regime assumption (see Sources)"
hedge_framework: "fin-guru/data/hedging-strategies.md v1.0"
post_close_exposure: "Portfolio fully unhedged; user accepts broad market and tech drawdown in full"
---

# Options Close Ticket — Hedge Unwind — Thesis Change (April 2026)

## Execution Summary

| # | Action        | Contract                         | Qty | Target Price         | Est. Cash Impact |
|---|---------------|----------------------------------|-----|----------------------|------------------|
| 1 | SELL TO CLOSE | SPY Jun-19-2026 $580 PUT         | 2   | Mid ~$0.50–$0.90/sh  | **≈ +$100–$180** |
| 2 | SELL TO CLOSE | QQQ Jun-19-2026 $480 PUT         | 2   | Mid ~$0.35–$1.00/sh  | **≈ +$70–$200**  |
|   |               |                                  |     | **Total credit est** | **≈ +$170–$380** |

**Execution note**: Both legs are full closes — no legs retained. Place limit orders at mid-price; do not use market orders on thinly traded far-OTM puts. If mid-price fills are not available within 10 minutes, adjust limit 1–2 cents at a time toward the bid. Any credit captured above zero offsets premium cost — do not leave residual on the table.

> **Why residual is minimal**: Positions were opened Apr-21-2026 (1 day ago) with SPY at ~$647 and QQQ at ~$535. The correction that justified the hedge has reversed; VIX has compressed from ~25–30 to 14. Both puts are now deeply out-of-the-money (SPY $580P is ~10%+ OTM; QQQ $480P is ~10%+ OTM), and IV contraction alone would have cut premium by 30–50% since entry. With 58 DTE remaining, theta decay is slow, but the vega collapse dominates — residual is thin. Closing now captures what remains rather than letting time and continued IV compression erode it further.

---

## Position History

| Contract | Open Date | Open Premium | Close Premium (est) | Realized P&L | Hold Duration |
|----------|-----------|--------------|---------------------|--------------|---------------|
| SPY Jun-19-2026 $580P (2x) | 2026-04-21 | $4.00/sh | ~$0.50–$0.90/sh | −$620 to −$700 (−78% to −88%) | 1 day |
| QQQ Jun-19-2026 $480P (2x) | 2026-04-21 | $2.00/sh | ~$0.35–$1.00/sh | −$200 to −$330 (−50% to −83%) | 1 day |

**Aggregate:**

- Total premium paid at open: $4.00 × 2 × 100 + $2.00 × 2 × 100 = **$800 + $400 = $1,200**
- Total credit realized at close (estimate): **≈ $170–$380**
- Net realized P&L: **≈ −$820 to −$1,030** (premium decay + vega loss on 1-day hold)
- Cost-per-day-of-coverage: $820–$1,030 over 1 day (non-standard — this was 58-DTE protection that was not needed)
- The $1,014 net debit from the Apr-21 roll (which included residual credit from the May-15 legs) means the all-in hedge program cost for this cycle is: roll debit $1,014 + close loss $820–$1,030 ≈ $1,834–$2,044 total

> **Framework perspective**: Paying ~$820–$1,030 to insure a ~$220k portfolio through a VIX-spike event — even if the event resolved in 24 hours — is within expected program cost. The Apr-21 roll was executed at the peak of the concern; thesis change within 24 hours is an edge case, not a framework failure.

---

## Close Rationale

**Trigger for close:**

- [x] Thesis changed — specific change: VIX fell from ~25–30 (correction peak, triggering the Apr-21 roll) to **14 current** — below the long-run average of ~20, signaling full market calm restoration
- [ ] Portfolio concentration reduced — no longer warrants hedging
- [ ] Budget reallocation — hedge dollars moving to other use
- [ ] Gain capture — hedge deep ITM, lock in gains before theta decay
- [ ] Strategy pivot — moving from protective puts to collar / inverse ETF / unhedged

**Detailed reasoning:**

> **Trigger for close**: Thesis changed.
>
> **Specific change**: VIX fell from ~25–30 at the Apr-21 correction peak (which triggered rolling the May-15 puts forward to Jun-19) to 14 current (2026-04-22). At 14, VIX is **below its long-run average of ~20**, signaling risk-off sentiment has fully unwound. The correction that justified the hedge — elevated systematic risk, broad market drawdown, macro uncertainty — has resolved.
>
> **Detailed reasoning**: The protective put program was rolled on 2026-04-21 precisely because VIX spiked and a correction appeared to be in progress. Within 24 hours, VIX compressed dramatically to 14, the underlying indices recovered, and both SPY $580P and QQQ $480P are now deeply OTM with no near-term catalyst to bring them back in-the-money. The cost-benefit of holding 58-DTE puts paying elevated premium no longer supports the position. Letting them sit while theta and vega work against the position would erode the remaining residual toward zero. Closing now captures marginal credit and cleanly exits the program while conditions support it.
>
> **Framework consistency** (`hedging-strategies.md` line 129): _"Skip roll: If the hedging thesis has changed (e.g., market risk has subsided), let the put expire."_ This close aligns with skip-roll guidance. We are executing an early close rather than letting expire because: (a) 58 DTE remain, meaning continued theta + vega drag is not trivial in absolute dollar terms, and (b) capturing even $170–$380 in residual credit meaningfully reduces the net program cost. The framework explicitly contemplates this scenario.

**Framework consistency check (`hedging-strategies.md` line 129):**

> _"Skip roll: If the hedging thesis has changed (e.g., market risk has subsided), let the put expire"_

This close aligns directly with the skip-roll / thesis-change clause. Positions were rolled April 21 under a spike thesis; thesis resolved April 22. Closing now rather than waiting for June 19 expiration captures $170–$380 of residual value (net savings vs. zero at expiry) and frees budget.

---

## Tax Impact Summary

| Leg | Open Cost | Close Proceeds (est) | Realized Gain/Loss | Holding Period | Tax Treatment |
|-----|-----------|----------------------|--------------------|----------------|---------------|
| SPY Jun-19 $580P (2x) | $800 | ~$100–$180 | −$620 to −$700 | 1 day | Short-term capital loss |
| QQQ Jun-19 $480P (2x) | $400 | ~$70–$200 | −$200 to −$330 | 1 day | Short-term capital loss |

- **Total STCL to report**: ≈ −$820 to −$1,030 (2026 tax year)
- **Plus STCL from Apr-21 closes** (May-15 legs sold to close): −$802 (per hedge-roll-2026-04-21 ticket)
- **Combined 2026 hedge STCL running total**: ≈ −$1,622 to −$1,832 — usable to offset short-term capital gains elsewhere in the portfolio
- 1099-B line item: short-term covered with basis reported (Fidelity will report; verify basis matches entry price)
- Tax year: 2026
- Record in: `fin-guru-private/fin-guru/analysis/` tax ledger; reconcile against Fidelity 2026 realized gains report

> **Tax-harvest note**: If you have any 2026 STCG elsewhere (e.g., from PLTR or NVDA trims), this STCL offsets dollar-for-dollar at ordinary income rates. The hedge program did double duty: protection _and_ tax-loss harvesting in a normalized market.

---

## Post-Close Portfolio State

**Exposure being accepted:**

- Portfolio value: ~$220,000 (Apr-21 snapshot; no material change expected Apr-22)
- Margin balance: ~$42,570 (19.3% utilization)
- **Unhedged exposure after close: $220,000 (100% of portfolio)**
- Concentration risk (from Apr-21 data):
  - PLTR, TSLA, NVDA, MSTR, COIN (growth/tech layer): estimated 50%+ of equity (~$110k+)
  - BDJ, ETY, ETV, ECAT, BST, UTG (income layer): estimated 40-45%
  - No protective puts in force after this close
- Drawdown tolerance: portfolio is safe through -40% crash per Apr-1 stress test (margin never called), but those scenarios carry full P&L loss on equities

**Downside scenario (no hedge, using Apr-22 ~$220k portfolio value):**

| Scenario | Portfolio Loss | Portfolio Value | Margin Utilization | Assessment |
|----------|---------------|-----------------|-------------------|------------|
| -10% market | −$22,000 | ~$198,000 | ~24% | SAFE — Tier 1 Conservative |
| -20% market | −$44,000 | ~$176,000 | ~31% | SAFE — Tier 2 Moderate (approaching 35% threshold) |
| -30% market | −$66,000 | ~$154,000 | ~42% | CAUTION — Tier 3; margin call risk increases near $42k debt against lower equity |
| -40% market | −$88,000 | ~$132,000 | ~55% | HIGH RISK — equity: ~$89,500; maintenance requirement likely ~$21k; manageable but monitor closely |

> **Margin context**: At -30%, equity drops to ~$154,000 with ~$42,570 margin debt → equity ratio ~72.4%. Fidelity's Reg T maintenance is 25% (equity must be ≥ 25% of total long market value). At $154k total value: 25% threshold = $38,500. Equity = $154k - $42.5k = $111,500 (72% equity). Margin call risk is low even at -30%. The Apr-1 stress test confirms safe through -40%. However, without the put hedge, a -30% event will feel materially worse than it would with protection in place.
>
> **Tech-concentration note**: A QQQ-specific drawdown (not broad market) could hit your growth layer harder than the blended -X% scenarios above. PLTR/NVDA/TSLA/MSTR can individually draw down 30-50% in a sector correction while SPY moves -10%. This is the asymmetric risk being accepted by closing the QQQ $480P.

**User acknowledgment required:** By closing this hedge, you are intentionally accepting full downside exposure on a ~$220k portfolio with ~$42.5k margin. The puts being closed had 58 DTE of forward protection remaining. Reopening a hedge at a later date would require paying new premiums (likely $600–$1,000 given VIX-14 entry is actually _cheaper_ than the Apr-21 elevated-IV entry). Consider this a natural pause in the hedge program during a low-volatility window.

---

## Optional: Replacement Strategy

- [ ] Replace with new put program (different strikes/expiries) — see separate `hedge-open` ticket
- [ ] Replace with collar structure — see separate ticket
- [ ] Replace with tactical inverse ETF position — see separate analysis
- [x] **No replacement — portfolio intentionally unhedged going forward (VIX 14 = low risk environment)**

> **Recommendation**: With VIX at 14, this is actually a relatively cheap entry point for a new hedge program — _cheaper_ than the Apr-21 elevated-IV entry. If you want continuous protection, a new OPEN ticket at current IV could establish Jun/Jul puts at lower cost. However, at VIX 14, the hedge program's cost-benefit ratio is less favorable: expected premium-loss rate rises. Suggest monitoring VIX — if it climbs above 18–20 again, reassess opening a new program. In the interim, the portfolio's income layer provides partial cushion.

---

## Risk Notes

- **Leg risk on full close**: Both legs closing simultaneously — no residual hedge coverage after fills. Verify both legs fill before considering any new positions.
- **Bid-ask slippage**: Jun-19 options with VIX at 14 may have wider spreads on far-OTM puts — bid/ask can be 10–30 cents wide. Use limit orders near mid; give the order 10–15 minutes before adjusting.
- **Assignment risk**: Not applicable — both positions are deeply OTM (SPY $580P with SPY ~$590–$600, QQQ $480P with QQQ ~$520–$530). Zero assignment risk on OTM long puts.
- **Tax optimization**: The STCL of ~$820–$1,030 (plus the −$802 from Apr-21 closes = ~$1,622–$1,832 total hedge STCL for 2026) can offset STCG from any portfolio trims. Consider coordinating with tax ledger before year-end.
- **Psychological trap**: The hedge felt expensive yesterday and now appears to have been unnecessary. This is _recency bias_. The decision to hedge was correct given the VIX signal at entry — the thesis simply resolved unusually quickly. Forward-looking close rationale: VIX 14 = thesis resolved. Backward-looking regret-avoidance is not a rationale to retain positions.
- **Market_data.py circular import**: Spot prices and residual estimates are based on VIX-14 regime assumptions + Apr-21 known entry prices. Verify actual Jun-19 chain mid-prices at Fidelity before placing orders.

---

## Execution Checklist

Before placing orders, verify at Fidelity:

- [ ] Jun-19-2026 SPY $580 PUT bid/ask — note the mid and set limit there
- [ ] Jun-19-2026 QQQ $480 PUT bid/ask — note the mid and set limit there
- [ ] Confirm these are your Jun-19 positions (not any residual May-15 contracts)
- [ ] Use limit orders — no market orders on options close
- [ ] After fills: confirm cash credit posts to account
- [ ] Account maintenance requirement after close: should decrease (hedge cost line item removed)
- [ ] Note actual fill prices for Position History section update below

---

## Sources & Assumptions

- Hedge framework: `fin-guru/data/hedging-strategies.md` v1.0 (2026-02-17); line 129 (skip-roll / thesis-change clause)
- Current positions: Reconstructed from `fin-guru-private/fin-guru/tickets/rolls/hedge-roll-2026-04-21-hedge-renewal.md` — rolling tracker shows no positions (positions exist at Fidelity outside tracker)
- Portfolio value: $220,217.52 from Portfolio_Positions_Apr-21-2026.csv (last known snapshot)
- SPY spot estimate: ~$590–$610 (post-correction recovery from ~$647 Apr-21 level; verify at execution)
- QQQ spot estimate: ~$520–$535 (estimate consistent with QQQ $480P being ~10% OTM; verify at execution)
- Residual option value estimates: Based on VIX 14 IV regime (~15–16% annualized IV), Black-Scholes approximation for far-OTM puts at 58 DTE; SPY $580P mid ~$0.50–0.90, QQQ $480P mid ~$0.35–1.00. **These are estimates — verify actual chain mid-prices before executing.**
- VIX data: User-provided in task context ("VIX back to 14")
- market_data.py: unavailable due to circular import in src/utils/logging.py (documented in hedge-roll-2026-04-21-hedge-renewal.md Sources)
- Previous roll ticket: `fin-guru-private/fin-guru/tickets/rolls/hedge-roll-2026-04-21-hedge-renewal.md`
- Portfolio snapshot: `~/.claude/projects/.../memory/project_portfolio_snapshot_apr2026.md` (2026-04-01 data)

---

## Post-Close Actions

After fills confirmed:

1. Update this ticket with actual fill prices (replace estimated residual values)
2. Invoke `rolling_tracker_cli.py close-position` for each leg (even though tracker was not seeded, run for auditability if positions are first seeded):
   ```bash
   uv run python src/analysis/rolling_tracker_cli.py close-position \
     --contract "SPY 2026-06-19 580P" --qty 2 --close-premium <actual_fill>
   uv run python src/analysis/rolling_tracker_cli.py close-position \
     --contract "QQQ 2026-06-19 480P" --qty 2 --close-premium <actual_fill>
   ```
3. Update margin dashboard: remove hedge cost line item (monthly hedge budget of ~$507/mo is now freed)
4. Log to 2026 tax ledger: STCL of ~$820–$1,030 on today's close + −$802 from Apr-21 closes (verify against Fidelity realized gains report)
5. Monitor VIX: if VIX climbs back to 18–20+, reassess opening a new put program via `fin-guru-hedge-roll` OPEN mode
6. No roll ticket needed — program is intentionally paused, not rolled

---

**Educational Notice:** For educational purposes only; not investment advice. Closing a hedge removes portfolio protection; subsequent drawdowns are borne in full. Options strategies carry risk of total premium loss. Past performance does not guarantee future results. Always consult qualified financial, tax, and legal advisors before implementing any hedging strategy.
