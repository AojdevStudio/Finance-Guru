---
document_type: options-open-ticket
strategy_name: "[Descriptor, e.g., Initial Protective Put Program — April 2026]"
generated_on: "{current_date}"
generated_by: "[strategy-advisor|margin-specialist]"
portfolio_context_date: "[YYYY-MM-DD]"
total_premium_outlay: "$[amount]"
monthly_amortized_cost: "$[amount]"
price_snapshot_as_of: "[timestamp + source]"
hedge_framework: "fin-guru/data/hedging-strategies.md v[version]"
---

# Options Open Ticket — [Strategy Name]

## Execution Summary

| # | Action        | Contract                              | Qty | Target Price       | Est. Cash Impact |
|---|---------------|---------------------------------------|-----|--------------------|------------------|
| 1 | BUY TO OPEN   | [UNDERLYING] [EXP-DATE] $[STRIKE] PUT | [N] | Mid ~$[x.xx]/sh    | **−$[total]**    |
| 2 | BUY TO OPEN   | [UNDERLYING] [EXP-DATE] $[STRIKE] PUT | [N] | Mid ~$[x.xx]/sh    | **−$[total]**    |
| 3 | BUY TO OPEN   | [UNDERLYING] [EXP-DATE] $[STRIKE] PUT | [N] | Mid ~$[x.xx]/sh    | **−$[total]**    |
|   |               |                                       |     | **Total outlay**   | **≈ −$[sum]**    |

## Portfolio Context

- Portfolio value: $[amount]
- Concentration: [top sectors / tickers and % weight — drives multi-underlying allocation]
- Current margin balance: $[amount] ([utilization %])
- Hedge budget: $[amount]/month (from `user-profile.yaml` Layer 3)
- Proposed outlay amortized: $[total] / [N] months = **$[monthly] /month** [✅ in budget | ⚠️ over budget]

## Sizing Rationale

- Framework: ~1 contract per ~$50k portfolio → $[portfolio_value] ≈ [N] contracts total
- Chosen contract count: **[N]** (rationale: [at target, below target, budget-constrained])
- Multi-underlying weights (framework target QQQ 40-50%, SPY 30-40%, IWM 10-20%):
  - QQQ: [N] contracts ([weight %]) — rationale: [tech concentration, growth exposure]
  - SPY: [N] contracts ([weight %]) — rationale: [broad-market coverage]
  - IWM: [N] contracts ([weight %]) — rationale: [small-cap exposure or omitted]
- Weighting adjustment from framework default: [explain if portfolio concentration required reweighting]

## Contract Selection Rationale

**Why [EXP-DATE] expiry:**

- [N] DTE from today — targets ~30 DTE maintenance window after first roll
- Monthly expiry for liquidity (tighter bid-ask than weeklies)
- [Any holiday / earnings / macro catalyst considerations]

**Why $[STRIKE] strikes:**

- [UNDERLYING] spot ~$[price] → strike $[strike] = [X.X]% OTM (framework target 10-20%)
- Cost efficiency rationale: [closer = more protection but costs more; further = cheaper but only pays in severe drawdowns]
- Payoff at strike: [describe breakeven and max-pain scenarios]

**Why protective puts (not collar, not inverse ETF):**

- Collar would cap upside via short calls — violates growth-layer thesis for [tickers like PLTR/TSLA/NVDA/MSTR]
- Inverse ETFs (SQQQ, SH) suffer multi-week volatility drag (per `hedging-strategies.md` lines 96-101)
- Net cost of protective puts fits framework budget of $[budget]/month

## Budget Impact

| Metric | Value |
|---|---|
| Total premium outlay | $[total] |
| Coverage period | [N] months (until [exp-date]) |
| Amortized monthly cost | $[monthly] |
| Framework target monthly | $[target] |
| Variance | [± amount / percent] |
| Annualized cost of protection | [X.X]% of portfolio |

## First Roll Trigger

- **Target roll date**: [exp-date − 7 days] (5-7 DTE trigger per framework)
- **Reminder mechanism**: [rolling_tracker_cli log-open, calendar reminder, DataHub note]
- **Next skill invocation**: `fin-guru-hedge-roll` in ROLL mode when user says "roll my puts"

## Risk Notes

- **Premium-loss risk**: If market stays flat or rises through [exp-date], all $[total] premium is lost. This is the cost of insurance — frame accordingly.
- **IV environment at open**: Current IV [elevated | normal | depressed]. [If elevated, paying more for same protection; if depressed, getting a deal.]
- **Assignment risk**: Far OTM puts with [N] DTE — early assignment extremely unlikely.
- **Leg risk**: If opening multiple underlyings, place each leg separately to avoid combo-order issues on Fidelity.
- **Margin interaction**: $[total] debit reduces cash by same amount; if funded from margin, utilization increases by [X]% to [new %].
- **Tax**: Premium outlay is capital cost; no realization event until close/roll/expiry.

## Execution Checklist

Before placing orders, verify at Fidelity:

- [ ] [UNDERLYING] [EXP-DATE] $[STRIKE] PUT bid/ask and mid
- [ ] Account maintenance requirement unchanged after open
- [ ] Options trading level supports long puts (Level 1+ on Fidelity)
- [ ] Hard-stop outlay: total debit ≤ $[max_acceptable]
- [ ] If IV spikes between analysis and execution, pause and reassess

## Sources & Assumptions

- Hedge framework: `fin-guru/data/hedging-strategies.md` v[version] ([date])
- Options insurance framework: `fin-guru/data/options-insurance-framework.md` v[version]
- Current positions: `notebooks/updates/Portfolio_Positions_[MMM-DD-YYYY].csv` at [timestamp]
- [UNDERLYING] spot: [source — live market_data.py, CSV last-price, or VOO proxy with tracker-ratio] at [timestamp]
- Option premium estimates: [derived from options_chain_cli.py scan at timestamp, or IV assumption]
- Framework version: [cite the hedging-strategies.md version stamp]

## Post-Open State (to seed rolling_tracker)

```yaml
positions:
  - ticker: [UNDERLYING]
    strike: [STRIKE]
    expiry: [EXP-DATE]
    quantity: [N]
    entry_premium: $[x.xx per share]
    entry_date: {current_date}
```

After fills confirmed, invoke `rolling_tracker_cli.py log-open` to register these positions for future roll tracking.

---

**Educational Notice:** For educational purposes only; not investment advice. Options strategies carry risk of total premium loss. Past performance does not guarantee future results. Always consult qualified financial, tax, and legal advisors before implementing any hedging strategy.
