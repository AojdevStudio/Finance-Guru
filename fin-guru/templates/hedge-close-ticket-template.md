---
document_type: options-close-ticket
strategy_name: "[Descriptor, e.g., Hedge Unwind — Thesis Change (April 2026)]"
generated_on: "{current_date}"
generated_by: "[strategy-advisor|margin-specialist]"
portfolio_context_date: "[YYYY-MM-DD]"
net_credit_realized: "$[amount]"
realized_pnl: "[$ and % — positive = hedge paid out; negative = premium decay]"
tax_treatment: "[short-term capital gain/loss]"
price_snapshot_as_of: "[timestamp + source]"
hedge_framework: "fin-guru/data/hedging-strategies.md v[version]"
post_close_exposure: "[description of downside risk being accepted]"
---

# Options Close Ticket — [Strategy Name]

## Execution Summary

| # | Action        | Contract                              | Qty | Target Price       | Est. Cash Impact |
|---|---------------|---------------------------------------|-----|--------------------|------------------|
| 1 | SELL TO CLOSE | [UNDERLYING] [EXP-DATE] $[STRIKE] PUT | [N] | Mid ~$[x.xx]/sh    | **+$[credit]**   |
| 2 | SELL TO CLOSE | [UNDERLYING] [EXP-DATE] $[STRIKE] PUT | [N] | Mid ~$[x.xx]/sh    | **+$[credit]**   |
|   |               |                                       |     | **Total credit**   | **≈ +$[net]**    |

**Execution note**: Partial closes supported — specify which legs to close and which (if any) to retain.

## Position History

| Contract | Open Date | Open Premium | Close Premium | Realized P&L | Hold Duration |
|----------|-----------|--------------|---------------|--------------|---------------|
| [UNDERLYING] [EXP-DATE] $[STRIKE]P ([N]x) | [date] | $[x.xx]/sh | $[x.xx]/sh | [$ and %] | [N days] |
| [UNDERLYING] [EXP-DATE] $[STRIKE]P ([N]x) | [date] | $[x.xx]/sh | $[x.xx]/sh | [$ and %] | [N days] |

**Aggregate:**
- Total premium paid across position lifetime: $[total]
- Total credit realized at close: $[credit]
- Net realized P&L: [$ and %]
- Cost-per-month-of-coverage: $[amount]

## Close Rationale

**Trigger for close:**

- [ ] Thesis changed — specific change: [e.g., VIX normalized from 35 to 15, macro catalyst resolved]
- [ ] Portfolio concentration reduced — no longer warrants hedging
- [ ] Budget reallocation — hedge dollars moving to [other use]
- [ ] Gain capture — hedge deep ITM, lock in gains before theta decay
- [ ] Strategy pivot — moving from protective puts to [collar / inverse ETF / unhedged]

**Detailed reasoning:**

[2-4 sentence narrative explaining WHY the thesis changed, WHAT specific signals support the close, and WHY this is the right moment rather than letting the hedge expire or rolling again.]

**Framework consistency check** (`hedging-strategies.md` line 129):
> "Skip roll: If the hedging thesis has changed (e.g., market risk has subsided), let the put expire"

Does this close align with the "skip roll" guidance, or is this an earlier-than-expiry close to capture residual value? [explanation]

## Tax Impact Summary

| Leg | Open Cost | Close Proceeds | Realized Gain/Loss | Holding Period | Tax Treatment |
|-----|-----------|----------------|--------------------|-----------------|---------------|
| [UNDERLYING] [EXP] $[STRIKE]P | $[cost] | $[proceeds] | [$ amount] | [N days] | [short-term] |
| [UNDERLYING] [EXP] $[STRIKE]P | $[cost] | $[proceeds] | [$ amount] | [N days] | [short-term] |

- Total STCG/STCL to report: $[amount]
- 1099-B line item: [e.g., "short-term covered with basis reported"]
- Tax year: [YYYY]
- Record in: [notebooks/tax-ledger/, Fidelity realized gains report, etc.]

## Post-Close Portfolio State

**Exposure being accepted:**

- Portfolio value: $[amount]
- Unhedged exposure: $[amount] ([X]% of portfolio)
- Concentration risk: [top tickers and weights]
- Drawdown tolerance accepted: -[X]% scenario = $[dollar loss]
- Margin context: if portfolio drops [X]%, margin utilization rises to [Y]%

**Downside scenario (no hedge):**

- -10% market move → $[loss amount] unrealized loss
- -20% market move → $[loss amount] unrealized loss; margin utilization [Y]%
- -30% market move → $[loss amount] unrealized loss; [liquidation risk assessment]

**User acknowledgment required:** By closing this hedge, the user is intentionally accepting the above downside scenarios. If this is a partial close, note which exposures remain protected and which do not.

## Optional: Replacement Strategy

If this close is part of a strategy pivot, specify:

- [ ] Replace with new put program (different strikes/expiries) — see separate `hedge-open` ticket
- [ ] Replace with collar structure — see separate ticket
- [ ] Replace with tactical inverse ETF position — see separate analysis
- [ ] No replacement — portfolio intentionally unhedged going forward

## Risk Notes

- **Leg risk on partial close**: Selling some puts while keeping others changes the net portfolio protection — verify post-close coverage matches intent.
- **Bid-ask slippage**: Thin options chains may widen spreads at close — use limit orders near mid, not market orders.
- **Assignment risk**: If any leg is deep ITM, assignment before close is possible; plan for it.
- **Tax optimization**: If STCL, consider harvest-to-offset-STCG from other positions in this tax year.
- **Psychological trap**: Hedges that felt expensive in calm periods and then "paid off" during volatility can create recency bias — ensure close rationale is forward-looking, not an attempt to rationalize sunk cost.

## Execution Checklist

Before placing orders, verify at Fidelity:

- [ ] [EXP-DATE] [UNDERLYING-A] $[STRIKE-A] PUT bid/ask (plan to sell near mid, not bid)
- [ ] [EXP-DATE] [UNDERLYING-B] $[STRIKE-B] PUT bid/ask
- [ ] Account maintenance requirement after close (should decrease or stay flat)
- [ ] Use limit orders; avoid market-order slippage on multi-leg close
- [ ] Confirm close settles in cash account, not used to offset margin automatically (if that matters)

## Sources & Assumptions

- Hedge framework: `fin-guru/data/hedging-strategies.md` v[version] ([date])
- Current positions: `notebooks/updates/Portfolio_Positions_[MMM-DD-YYYY].csv` at [timestamp]
- Rolling tracker state: `rolling_tracker_cli.py status` output at [timestamp]
- Option bid/ask estimates: [source + method + caveat]
- Thesis-change evidence: [link or cite market data, VIX, news, portfolio concentration reports]

## Post-Close Actions

After fills confirmed:

1. Invoke `rolling_tracker_cli.py close-position` for each leg closed
2. Update margin dashboard: remove hedge cost line item (or reduce proportionally for partial close)
3. Log to tax ledger for [YYYY] 1099-B reconciliation
4. If strategy pivot, schedule follow-up `fin-guru-hedge-roll` in OPEN mode for replacement

---

**Educational Notice:** For educational purposes only; not investment advice. Closing a hedge removes portfolio protection; subsequent drawdowns are borne in full. Options strategies carry risk of total premium loss. Past performance does not guarantee future results. Always consult qualified financial, tax, and legal advisors before implementing any hedging strategy.
