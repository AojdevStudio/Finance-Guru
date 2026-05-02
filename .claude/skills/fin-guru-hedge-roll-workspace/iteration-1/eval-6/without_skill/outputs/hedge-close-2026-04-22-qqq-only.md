---
document_type: options-close-ticket
strategy_name: "Partial Hedge Unwind — QQQ Puts Only (Tech Concentration Reduced)"
generated_on: "2026-04-22"
generated_by: "strategy-advisor"
portfolio_context_date: "2026-04-01"
net_credit_realized: "TBD — verify at Fidelity before execution"
realized_pnl: "TBD — depends on current QQQ put market value vs. open premium"
tax_treatment: "short-term capital gain or loss (holding period < 1 year)"
price_snapshot_as_of: "2026-04-22 — pull live bid/ask at Fidelity before placing orders"
hedge_framework: "fin-guru/data/hedging-strategies.md v1.0 (2026-02-17)"
post_close_exposure: "QQQ/tech sector: unhedged. SPY broad-market protection remains active."
---

# Options Close Ticket — Partial Hedge Unwind: QQQ Puts Only

## Execution Summary

| # | Action        | Contract                     | Qty | Target Price     | Est. Cash Impact |
|---|---------------|------------------------------|-----|------------------|------------------|
| 1 | SELL TO CLOSE | QQQ [EXP-DATE] $[STRIKE] PUT | [N] | Mid ~$[x.xx]/sh  | **+$[credit]**   |
|   |               |                              |     | **Total credit** | **≈ +$[net]**    |

> **Fill values to be confirmed at Fidelity.** Pull the current bid/ask on the QQQ put(s) immediately before placing orders; use limit orders at or near mid-price — do not use market orders.

**SPY puts: RETAIN — do not touch.** Broad-market downside risk remains live per close rationale below.

## Position History

| Contract | Open Date | Open Premium | Close Premium | Realized P&L | Hold Duration |
|----------|-----------|--------------|---------------|--------------|---------------|
| QQQ [EXP-DATE] $[STRIKE]P ([N]x) | [open date] | $[x.xx]/sh | $[x.xx]/sh at close | [$ and % — TBD] | [N days] |

**Aggregate (QQQ leg only):**
- Total premium paid on QQQ puts: $[amount]
- Credit realized at close: $[credit]
- Net realized P&L: [$ and % — positive = hedge paid out; negative = premium decayed]
- Cost-per-month-of-QQQ-coverage: $[amount]

_SPY puts remain open — their P&L is not captured here._

## Close Rationale

**Trigger for close:**

- [x] Portfolio concentration reduced — tech exposure materially reduced; QQQ hedge no longer required at prior sizing
- [ ] Thesis changed — macro / volatility catalyst resolved
- [ ] Budget reallocation
- [ ] Gain capture
- [ ] Strategy pivot

**Detailed reasoning:**

Tech concentration in your portfolio has been deliberately reduced — the specific catalyst that warranted QQQ protective puts (concentrated Nasdaq-100 / growth exposure) is no longer present at the same magnitude. Continuing to pay QQQ put premiums for an exposure that has been trimmed is over-hedging, which hedging-strategies.md explicitly flags as a return drag. Broad-market risk, however, remains fully live — SPY exposure is unchanged and the macro environment has not cleared — so SPY puts are intentionally retained. This is a surgical partial close, not a full hedge unwind.

**Framework consistency check** (`hedging-strategies.md` — "Skip roll" guidance):

> _"Skip roll: If the hedging thesis has changed (e.g., market risk has subsided), let the put expire"_

The QQQ thesis has changed at the _portfolio level_ (reduced concentration), not because market risk has subsided. This is an earlier-than-expiry close to recapture remaining premium value rather than letting time value decay to zero. Aligns with the skip-roll principle; executing as an active close (rather than expiry) recovers residual bid value.

## Post-Close Portfolio State

**Remaining protection after this close:**

| Underlying | Status       | Coverage Rationale                          |
|------------|--------------|---------------------------------------------|
| QQQ puts   | CLOSED       | Tech concentration reduced — no longer needed |
| SPY puts   | RETAINED     | Broad-market risk live; macro thesis unchanged |

**Exposure being accepted (QQQ / tech sector):**

- Portfolio value: ~$198,474 (April 1 snapshot; verify current value)
- QQQ/tech exposure: unhedged after this close
- If tech sells off independently of broad market, SPY puts will not fully compensate
- Residual tech risk must be managed via position sizing, not options going forward (unless re-opened)

**Downside scenarios (QQQ leg, no hedge):**

- -10% tech/QQQ move → unrealized loss proportional to remaining tech holdings (verify current weights)
- -20% tech/QQQ move → meaningful unrealized loss; SPY puts partially offset if move is broad-market
- Sector-specific tech correction: SPY hedge provides partial but incomplete coverage

**Margin context (April 1 baseline — $45,657 debt, 23% utilization):**

A tech-specific selloff without QQQ hedge protection would increase margin utilization. Stress test remains safe through -40% (per April snapshot), but that test assumed the hedge program was intact. Verify margin headroom against updated portfolio value before closing.

## Tax Impact Summary

| Leg | Open Cost | Close Proceeds | Realized Gain/Loss | Holding Period | Tax Treatment |
|-----|-----------|----------------|--------------------|----------------|---------------|
| QQQ [EXP] $[STRIKE]P | $[cost] | $[proceeds] | [$ amount] | [N days] | Short-term |

- Total STCG or STCL from this close: $[amount — TBD]
- 1099-B treatment: short-term covered (Fidelity reports basis)
- Tax year: 2026
- Record in tax ledger; cross-reference against other 2026 STCG/STCL for harvest opportunity if loss

## Optional: Replacement Strategy

- [ ] Replace QQQ put program at reduced size (if tech is re-concentrated in future) — open new `hedge-open` ticket
- [ ] Add collar on specific large tech positions instead of index puts
- [x] No replacement — intentionally running unhedged on tech until concentration warrants re-opening

## Risk Notes

- **Partial close leg risk**: SPY puts remain open — confirm they are on a separate order line and not inadvertently included.
- **Bid-ask slippage**: QQQ options are highly liquid, but use limit orders at mid; do not use market orders.
- **Psychological trap**: If QQQ sold off recently and puts are in-the-money, resist the urge to "let them ride" past your thesis — the thesis is the anchor, not the P&L.
- **Recency bias**: A tech selloff that made these puts valuable does not mean tech risk is higher going forward if the portfolio has genuinely been de-concentrated. Close is thesis-driven.
- **SPY puts**: Do not second-guess the SPY retention. Broad-market risk is explicitly live per close rationale. Hold.

## Execution Checklist

Before placing orders at Fidelity:

- [ ] Pull current QQQ put bid/ask; confirm lot count and contract details match what is on record
- [ ] Confirm SPY put positions are on a separate row — visually verify they will NOT be touched
- [ ] Check account maintenance requirement before and after simulated close (should decrease slightly)
- [ ] Place QQQ sell-to-close as limit order near mid-price
- [ ] After fill: confirm SPY puts still show as open positions

## Post-Close Actions

After fills confirmed:

1. Update margin dashboard — remove QQQ hedge cost line item; retain SPY hedge cost
2. Log QQQ close to tax ledger (2026 STCG/STCL entry)
3. Note portfolio tech concentration at time of close — establishes baseline for re-hedge decision
4. If QQQ / tech exposure is rebuilt materially in future, re-open via `fin-guru-hedge-roll` in OPEN mode

## Sources & Assumptions

- Hedge framework: `fin-guru/data/hedging-strategies.md` v1.0 (2026-02-17)
- Portfolio baseline: `memory/project_portfolio_snapshot_apr2026.md` — April 1, 2026
- Options positions reference: Portfolio sync note — "2 options positions (QQQ/SPY puts, temporary)" as of April 1, 2026
- Specific contract details (strike, expiry, open premium, current market value): **must be pulled from Fidelity at time of execution** — not available in memory files
- Broad-market risk thesis (SPY retention): stated by user — "broad-market risk is still live"

---

**Educational Notice:** For educational purposes only; not investment advice. Closing a hedge removes portfolio protection for the closed legs; subsequent drawdowns in tech/QQQ are borne in full. SPY puts retained per user direction — broad-market protection remains active. Options strategies carry risk of total premium loss. Past performance does not guarantee future results. Always consult qualified financial, tax, and legal advisors before implementing any hedging strategy.
