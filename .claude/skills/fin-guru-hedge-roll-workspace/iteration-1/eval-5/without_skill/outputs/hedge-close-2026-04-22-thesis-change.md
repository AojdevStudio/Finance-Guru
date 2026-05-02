---
document_type: options-close-ticket
strategy_name: "Hedge Unwind — Thesis Change (April 2026)"
generated_on: "2026-04-22"
generated_by: "strategy-advisor"
portfolio_context_date: "2026-04-22"
net_credit_realized: "~$0–$20 (near-zero residual; puts expired worthless)"
realized_pnl: "-$988 net (-97% on premium paid)"
tax_treatment: "short-term capital loss — both legs"
price_snapshot_as_of: "2026-04-22 (VIX ~14, correction resolved)"
hedge_framework: "fin-guru/data/hedging-strategies.md v1.0"
post_close_exposure: "Fully unhedged — $220K+ portfolio, no put protection"
---

# Options Close Ticket — Hedge Unwind (Thesis Change, April 2026)

## Execution Summary

| # | Action          | Contract                          | Qty | Target Price     | Est. Cash Impact |
|---|-----------------|-----------------------------------|-----|------------------|------------------|
| 1 | SELL TO CLOSE   | SPY May-15-2026 $580 PUT          | 2   | Mid ~$0.05/sh    | **+$10**         |
| 2 | SELL TO CLOSE   | QQQ May-15-2026 $480 PUT          | 2   | Mid ~$0.05/sh    | **+$10**         |
|   |                 |                                   |     | **Total credit** | **≈ +$20**       |

> **Note:** If bid is $0.00 on either leg, skip the close order — at $0.00 bid you receive nothing and pay commissions. Allow those legs to expire worthless at May-15 expiry. Only place a sell-to-close if a non-zero bid exists at execution time.

**Execution note:** These are near-zero residual value positions. Correction resolved, VIX normalized to ~14; hedge thesis is gone. Closing (or allowing expiry) is the correct action. No replacement positions planned at this time.

---

## Position History

| Contract | Open Date | Open Premium | Close Premium | Realized P&L | Hold Duration |
|----------|-----------|--------------|---------------|--------------|---------------|
| SPY May-15-2026 $580P (2x) | ~2026-03-26 | $4.16/sh ($831) | ~$0.05/sh ($10) | **−$821 (−99%)** | ~27 days |
| QQQ May-15-2026 $480P (2x) | ~2026-04-21 | $0.79/sh ($157) | ~$0.05/sh ($10) | **−$147 (−93%)** | ~1 day |

> _Context from prior roll ticket (2026-04-21):_ The roll planned to close SPY May-15 $590P → $580P and QQQ May-15 $525P → $480P. This close ticket assumes the new Jun-19 legs were NOT opened (thesis changed before opening replacement positions), and the May-15 legs are the ones being unwound. If the Jun-19 legs were opened, adjust accordingly.

**Aggregate:**
- Total premium paid across position lifetime: ~$988
- Total credit realized at close: ~$20
- Net realized P&L: **−$968 (−98%)**
- Cost-per-month-of-coverage: ~$494/mo (2 months of protection on ~$200-220K portfolio — within $500-600/mo framework target)

---

## Close Rationale

**Trigger for close:**

- [x] Thesis changed — specific change: VIX normalized from elevated levels back to ~14; correction resolved
- [ ] Portfolio concentration reduced — no longer warrants hedging
- [ ] Budget reallocation — hedge dollars moving to other use
- [ ] Gain capture — hedge deep ITM, lock in gains before theta decay
- [ ] Strategy pivot — moving from protective puts to alternative structure

**Detailed reasoning:**

The hedging thesis was opened during elevated market volatility and correction risk (VIX elevated, macro uncertainty). As of 2026-04-22, VIX has returned to approximately 14 — historically low, indicating the market has absorbed the correction and fear has subsided. The puts are far OTM with 23 days remaining and near-zero intrinsic or time value, having expired worthless in economic terms. Continuing to hold delivers no additional protection, and there is no active macro catalyst that warrants renewing coverage at this time. Closing (or allowing expiry) crystallizes the premium cost as the known insurance expense for this protection period, consistent with the homeowners-insurance analogy — the policy served its purpose by providing peace of mind during the volatile stretch; no claim was needed.

**Framework consistency check** (`hedging-strategies.md` line 129):
> "Skip roll: If the hedging thesis has changed (e.g., market risk has subsided), let the put expire"

This close _fully aligns_ with the skip-roll guidance. VIX at 14 is the canonical example of "market risk has subsided." The correct action per the framework is to let these expire (or sell the residual pennies if a bid exists) and not open replacement contracts until volatility conditions warrant renewed protection.

---

## Tax Impact Summary

| Leg | Open Cost | Close Proceeds | Realized Gain/Loss | Holding Period | Tax Treatment |
|-----|-----------|----------------|--------------------|----------------|---------------|
| SPY May-15-2026 $580P (2x) | $831 | ~$10 | **−$821** | ~27 days | Short-term capital loss |
| QQQ May-15-2026 $480P (2x) | $157 | ~$10 | **−$147** | ~1 day | Short-term capital loss |

- **Total STCL to report: ~−$968**
- 1099-B line item: short-term covered with basis reported (Fidelity auto-tracks)
- Tax year: 2026
- Record in: Fidelity realized gains report; note in tax ledger under `notebooks/tax-ledger/`
- Tax benefit: $968 STCL can offset short-term capital gains realized elsewhere in 2026 — useful given any growth-stock sales or other options activity this year

---

## Post-Close Portfolio State

**Exposure being accepted:**

- Portfolio value: ~$220,000 (estimated, based on Apr-21 snapshot + market recovery)
- Unhedged exposure: ~$220,000 (100% of portfolio — fully unhedged post-close)
- Concentration risk: PLTR, TSLA, NVDA, MSTR, COIN (high-volatility growth layer); closed-end fund income layer (BDJ, ETY, ETV, ECAT, BST, UTG)
- Margin balance: ~$42,570 (19.3% utilization — Tier 1 Conservative)
- Drawdown tolerance accepted: No floor on downside; full market-rate drawdowns apply

**Downside scenario (no hedge):**

| Scenario | Portfolio Loss | Margin Utilization |
|----------|---------------|-------------------|
| −10% market move | ~−$22,000 | ~24% (still safe) |
| −20% market move | ~−$44,000 | ~30% (approaching Tier 2 Moderate) |
| −30% market move | ~−$66,000 | ~37% (watch closely) |
| −40% market move | ~−$88,000 | ~47% (Tier 3 — elevated risk per prior stress test) |

_Note: April portfolio stress test showed safety through −40% without margin call. Proceeding unhedged is an informed, intentional acceptance of these scenarios given current low-volatility environment._

**User acknowledgment:** By closing this hedge, you are intentionally accepting full market-rate downside on ~$220K of equity. The correction that prompted the hedge has resolved. VIX at 14 indicates consensus calm. This is the appropriate time to accept unhedged exposure and pay no further premium.

---

## Replacement Strategy

- [ ] Replace with new put program (different strikes/expiries) — see separate `hedge-open` ticket
- [ ] Replace with collar structure
- [ ] Replace with tactical inverse ETF position
- [x] **No replacement — portfolio intentionally unhedged going forward** (thesis change; re-evaluate when VIX > 20 or next macro catalyst emerges)

**Re-hedge trigger conditions** (per `hedging-strategies.md`):
- VIX climbs above 20 → evaluate new put program
- Upcoming Fed meeting / earnings season with elevated uncertainty → consider short-duration hedge
- Portfolio value crosses $250K threshold → reassess sizing requirements
- Any geopolitical event that materially changes market risk regime

---

## Risk Notes

- **Bid-ask slippage on residual value:** Near-zero positions may show $0.00 bid. Do not place market orders — use limit order at $0.05/sh or allow natural expiry.
- **Commission economics:** At $0.05/sh × 200 shares = $10 gross; if commission + fees approach $10, the close order nets $0 and is not worth placing. Verify Fidelity commission structure (typically $0.65/contract for options close).
- **Psychological trap:** Puts that expired worthless do NOT mean the hedge was a mistake. VIX was elevated; the insurance premium was fairly priced for the risk environment. This is the expected outcome when protection is not needed — the premium is the cost of having been safe. Do not use this outcome to argue against re-hedging when conditions warrant.
- **Tax harvest opportunity:** The ~$968 STCL is a real tax asset. If you have STCG elsewhere in 2026 (other options, short-term stock sales), this loss offsets them dollar-for-dollar.
- **Margin freed:** Closing these puts removes any margin requirement on long put positions (long puts require no margin). No margin impact from this close.

---

## Execution Checklist

Before placing orders, verify at Fidelity:

- [ ] SPY May-15-2026 $580 PUT: check bid/ask — only close if bid > $0.00
- [ ] QQQ May-15-2026 $480 PUT: check bid/ask — only close if bid > $0.00
- [ ] Use limit orders (GTC or day) near mid; avoid market orders on illiquid near-zero puts
- [ ] Confirm account maintenance requirement unchanged (should be flat or lower post-close)
- [ ] Note fill prices in tax ledger immediately after confirmation

---

## Sources & Assumptions

- Hedge framework: `fin-guru/data/hedging-strategies.md` v1.0 (2026-02-17)
- Prior roll ticket: `fin-guru-private/fin-guru/tickets/rolls/hedge-roll-2026-04-21-hedge-renewal.md`
- Portfolio snapshot: memory/project_portfolio_snapshot_apr2026.md (Apr-01-2026 baseline; Apr-21 update: ~$220K)
- VIX level: ~14 (user-stated, 2026-04-22)
- Put residual estimates: near-zero (~$0.05/sh) inferred from puts being deep OTM with VIX at 14 and 23 DTE remaining — verify actual bid at Fidelity before placing orders
- Original premium data: hedge-roll-2026-04-21 ticket (SPY $590P original cost $831.35; QQQ $525P $157.35)

---

## Post-Close Actions

After positions confirmed closed (or expired):

1. Update rolling tracker: `rolling_tracker_cli.py close-position` for each leg
2. Update margin dashboard: remove hedge cost line item (month-over-month cost will drop by ~$500)
3. Log to 2026 tax ledger: −$968 STCL for 1099-B reconciliation (Fidelity realized gains report)
4. Schedule re-hedge evaluation: set a trigger to revisit when VIX > 20 or next macro event materializes
5. No `fin-guru-hedge-roll` open ticket needed at this time — re-hedge evaluation deferred to next volatility regime

---

_Educational Notice: For educational purposes only; not investment advice. Closing a hedge removes all portfolio protection; subsequent drawdowns are borne in full. Options strategies carry risk of total premium loss. Past performance does not guarantee future results. Always consult qualified financial, tax, and legal advisors before implementing any hedging strategy._
