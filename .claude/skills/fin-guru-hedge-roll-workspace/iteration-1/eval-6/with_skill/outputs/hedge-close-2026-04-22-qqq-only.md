---
document_type: options-close-ticket
strategy_name: "Partial Hedge Close — QQQ Only (Tech Concentration Reduced)"
generated_on: "2026-04-22"
generated_by: "strategy-advisor"
portfolio_context_date: "2026-04-22"
net_credit_realized: "~$380–$400"
realized_pnl: "~−$0 to −$20 (1-day hold, bid-ask slippage only)"
tax_treatment: "short-term capital loss — QQQ legs only"
price_snapshot_as_of: "2026-04-22 (inferred from Apr-21 roll; verify at execution)"
hedge_framework: "fin-guru/data/hedging-strategies.md v1.0"
post_close_exposure: "MIXED — hedged vs broad-market drawdown (SPY 2x retained); NOT hedged vs tech-specific drawdown (QQQ legs closed)"
---

# Options Close Ticket — Partial Hedge Close: QQQ Only (April 2026)

## Execution Summary

| # | Action        | Contract                        | Qty | Target Price      | Est. Cash Impact |
|---|---------------|---------------------------------|-----|-------------------|------------------|
| 1 | SELL TO CLOSE | QQQ Jun-19-2026 $480 PUT        | 2   | Mid ~$1.90–$2.00/sh | **+$380–$400** |
|   |               |                                 |     | **Total credit**  | **≈ +$380–$400** |

**SPY legs retained — no action**: SPY Jun-19-2026 $580 PUT (2×) remains open. Do not touch these contracts.

**Execution note**: Use a limit order at mid-price or slightly above bid. These are 59-DTE puts opened yesterday; the bid-ask spread may be $0.10–$0.20/sh. Avoid market orders to prevent unnecessary slippage.

## Position History

| Contract | Open Date | Open Premium | Close Premium | Realized P&L | Hold Duration |
|----------|-----------|--------------|---------------|--------------|---------------|
| QQQ Jun-19-2026 $480P (2×) | 2026-04-21 | $2.00/sh | ~$1.90–$2.00/sh | ~−$0 to −$20 | 1 day |

**Aggregate (QQQ legs only):**
- Total premium paid for QQQ legs: $400 (2 contracts × $2.00/sh × 100)
- Total credit realized at close: ~$380–$400
- Net realized P&L: ~−$0 to −$20 (essentially break-even; any loss is bid-ask slippage, not market move)
- Effective cost of 1-day coverage: ~$0–$20 — negligible

**Note on timing**: The QQQ legs were opened on Apr-21 as part of the hedge renewal roll and are being closed the following day (Apr-22). The tech concentration reduction that motivates this close occurred after the roll ticket was placed. The thesis was invalidated within 24 hours of opening; the close captures essentially full premium value rather than waiting for decay.

## Close Rationale

**Trigger for close:**

- [x] Portfolio concentration reduced — tech exposure trimmed; QQQ-specific hedge no longer proportional
- [x] Partial close — SPY legs retained; QQQ legs closed

**Detailed reasoning per closed leg (QQQ Jun-19 $480P × 2):**

The QQQ puts were opened on 2026-04-21 as part of the hedge renewal roll (see `hedge-roll-2026-04-21-hedge-renewal.md`). Their thesis was tech-concentration risk: the portfolio carried meaningful weight in high-beta growth names (PLTR, TSLA, NVDA, MSTR, COIN) that are disproportionately captured by QQQ.

A tech concentration reduction was executed after the roll was placed — reducing tech exposure below the threshold that warranted a QQQ-specific overlay. The QQQ hedge was proportional to that concentration; with concentration reduced, the QQQ leg is now oversized relative to remaining tech exposure.

The leg is 1 day old. Rather than letting the QQQ puts continue to accrue theta cost for a risk that no longer exists at the same scale, closing today returns ~$380–$400 of the $400 premium paid — near full recovery with minimal loss. Allowing the position to run to expiration, or through the next roll cycle, would waste premium on a thesis that no longer holds.

**Retained leg rationale (SPY Jun-19 $580P × 2):**

Broad-market risk is unchanged. A broad-market drawdown scenario (geopolitical shock, Fed policy surprise, credit event) is independent of sector concentration. The SPY puts hedge portfolio-level beta drawdown regardless of whether tech concentration is high or low. These legs remain fully consistent with the hedging thesis and are retained.

**Framework consistency check** (`hedging-strategies.md` line 129):

> "Skip roll: If the hedging thesis has changed (e.g., market risk has subsided), let the put expire"

This close is a partial implementation of the skip-roll guidance applied to the QQQ leg specifically. The QQQ-specific thesis has changed (tech concentration subsided). Per line 129, the correct action is to skip the next roll on that leg. Because the position has only 1 day of decay, closing early captures ~full premium ($380–$400 vs $400 cost) rather than waiting for expiry worthless or the next roll cycle to let it lapse. The SPY thesis is unchanged, so the SPY leg continues per normal roll cadence.

## Tax Impact Summary

_QQQ legs only. SPY legs are unaffected and not reported here._

| Leg | Open Cost | Close Proceeds | Realized Gain/Loss | Holding Period | Tax Treatment |
|-----|-----------|----------------|--------------------|----------------|---------------|
| QQQ Jun-19-2026 $480P (2×) | $400 | ~$380–$400 | ~−$0 to −$20 | 1 day | Short-term capital loss |

- Total STCL to report: ~$0–$20 (immaterial; exact amount depends on execution fill)
- 1099-B line item: "short-term covered, basis reported" (Fidelity reports options with basis)
- Tax year: 2026
- Record in: Fidelity realized gains report; notebooks/tax-ledger/ (2026 log)
- **Harvest note**: The STCL is de minimis (~$0–$20). No meaningful harvest opportunity; flag as negligible on year-end reconciliation.

## Post-Close Portfolio State

**MIXED coverage: hedged vs broad-market drawdown, NOT hedged vs tech-specific drawdown**

**Retained protection (SPY legs):**
- Contract: SPY Jun-19-2026 $580 PUT × 2
- SPY spot (as of Apr-21 reference): ~$647 (VOO proxy)
- Strike OTM: 10.4% OTM — within 10-20% framework band
- Notional floor: 2 contracts × 100 shares × $580 = $116,000 of SPY-equivalent downside protection
- DTE remaining: ~58 days (next roll trigger: when DTE reaches 5-7, ~mid-June)
- Coverage thesis: broad-market beta drawdown (recession, credit event, Fed shock) — still live

**Exposure accepted (QQQ legs removed):**
- Portfolio tech-sector allocation is reduced but not zero; residual tech exposure is unhedged
- A tech-specific drawdown (AI sector rotation, semiconductor correction, growth-to-value rotation) will be borne in full for the remaining tech-adjacent positions
- User acknowledges: no QQQ put protection means a -15% QQQ-specific selloff is no longer partially absorbed

**Portfolio context:**
- Portfolio value: ~$220,217 (April 21 snapshot; verify current)
- Margin utilization: ~19.3% before close; effectively unchanged after close (no margin impact — QQQ puts are long options, no margin requirement at close)

**Downside scenarios — broad market (SPY puts retained):**

| Scenario | SPY Move | Portfolio Impact (est.) | SPY Put Offset | Net Loss |
|----------|----------|------------------------|----------------|----------|
| Mild correction | −10% | ~−$22,000 | ~+$2,000–$4,000 (put approaches ITM) | ~−$18,000–$20,000 |
| Sharp drawdown | −20% | ~−$44,000 | ~+$15,000–$20,000 (deep ITM, ~$5,400 intrinsic) | ~−$24,000–$29,000 |
| Crash scenario | −30% | ~−$66,000 | ~+$28,000–$34,000 (deeply ITM) | ~−$32,000–$38,000 |

_SPY put offsets are estimates. Actual payoff depends on execution fill and remaining DTE at close._

**Downside scenarios — tech-specific (QQQ protection removed):**

| Scenario | QQQ Move | Tech Portfolio Impact (est.) | QQQ Put Offset | Net Loss |
|----------|----------|------------------------------|----------------|----------|
| Tech correction | −15% | Proportional to remaining tech weight | $0 (no put) | Full unhedged loss on tech positions |
| Tech selloff | −25% | Proportional to remaining tech weight | $0 (no put) | Full unhedged loss on tech positions |

_User acknowledges these scenarios are now unhedged. Concentration reduction reduces the size of the tech-specific impact but does not eliminate it._

**User acknowledgment required:** By closing the QQQ legs, tech-specific drawdown risk is intentionally accepted. Broad-market drawdown risk remains partially hedged via SPY puts. This is a _deliberate asymmetric coverage posture_ consistent with the concentration reduction rationale.

## Optional: Replacement Strategy

- [ ] Replace QQQ puts with new program if tech concentration rebuilds above threshold
- [x] No replacement at this time — concentration reduction makes QQQ overlay unnecessary until weighting reverts
- [ ] Monitor: if tech re-concentrates above 40-45% of portfolio, reopen QQQ put program via separate `fin-guru-hedge-roll` OPEN ticket

## Risk Notes

- **Asymmetric post-close coverage**: The portfolio is now hedged at the index level (SPY) but unhedged at the sector level (QQQ/tech). This is intentional but should be documented. A broad index crash will likely drag tech names harder than the index — SPY puts provide partial but not full coverage for a tech-concentrated portfolio.
- **Bid-ask slippage**: QQQ Jun-19 $480P was opened at ~$2.00/sh. The bid at close will likely be $0.10–$0.20 below mid. Use limit orders at mid; do not accept bid.
- **Leg risk**: SPY legs are being retained; closing only QQQ eliminates no accidental exposure — this is a clean partial close.
- **Tax**: STCL is immaterial (~$0–$20). No wash-sale issue — closing a long put, not re-opening the same contract immediately.
- **Re-open trigger**: If tech concentration rebuilds (PLTR/NVDA/TSLA/MSTR weight > 40%), initiate a new QQQ put open ticket. Do not assume current reduced concentration is permanent.

## Execution Checklist

Before placing orders, verify at Fidelity:

- [ ] Jun-19-2026 QQQ $480 PUT — check bid/ask; confirm mid is near $1.90–$2.00/sh
- [ ] Do NOT touch Jun-19-2026 SPY $580 PUT — retained; verify it still shows in open positions
- [ ] Use limit order on QQQ close; set limit at mid, accept partial fill and re-enter if needed
- [ ] Confirm close settles as credit to cash account
- [ ] Verify post-close: SPY $580P (2×) still open; QQQ $480P position is flat

## Sources & Assumptions

- Hedge framework: `fin-guru/data/hedging-strategies.md` v1.0 (2026-02-17) — line 129 (skip-roll guidance)
- Options insurance framework: `fin-guru/data/options-insurance-framework.md` v1.0
- Current positions (inherited from roll): `fin-guru-private/fin-guru/tickets/rolls/hedge-roll-2026-04-21-hedge-renewal.md`
- QQQ entry premium: $2.00/sh (stated in Apr-21 roll ticket, row 4)
- QQQ close premium estimate: $1.90–$2.00/sh — 1-day hold, no material QQQ spot move assumed; derived from Apr-21 entry with minimal theta decay (59 DTE → 58 DTE)
- Portfolio value: $220,217.52 (Apr-21 CSV — verify against current Fidelity balance)
- Spot estimates: SPY ~$647 (VOO proxy from Apr-21); QQQ ~$535 (inferred from Apr-21 roll OTM analysis)
- **Caveat**: `market_data.py` has a known circular import in this environment. Premium and spot figures are indicative. Verify actual bid/ask at Fidelity before executing.
- Tech concentration reduction: user-stated (post-roll, Apr-22); specific names/weights not quantified in this ticket — add to position notes if available

## Post-Close Actions

After fills confirmed:

1. Run `rolling_tracker_cli.py close-position --contract "QQQ 2026-06-19 480P" --qty 2 --close-premium <actual-fill>`
2. Verify SPY Jun-19 $580P (2×) still active in rolling tracker — do not mark it closed
3. Update margin dashboard: QQQ premium cost line item removed; SPY line item unchanged
4. Log QQQ close to 2026 tax ledger (STCL ~$0–$20; mark as de minimis)
5. Set a reminder: if QQQ tech weighting rebuilds above 40-45%, re-open QQQ put program

---

**Educational Notice:** For educational purposes only; not investment advice. Closing a hedge removes portfolio protection; subsequent drawdowns are borne in full. Options strategies carry risk of total premium loss. Past performance does not guarantee future results. Always consult qualified financial, tax, and legal advisors before implementing any hedging strategy.
