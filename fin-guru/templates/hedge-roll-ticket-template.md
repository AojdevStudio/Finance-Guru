---
document_type: options-roll-ticket
strategy_name: "[Descriptor, e.g., Hedge Roll — May 15 → Jun 19 expiry (April 2026)]"
generated_on: "{current_date}"
generated_by: "[strategy-advisor|margin-specialist]"
portfolio_context_date: "[YYYY-MM-DD]"
net_debit_estimate: "$[amount]"
price_snapshot_as_of: "[timestamp + source]"
hedge_framework: "fin-guru/data/hedging-strategies.md v[version]"
---

# Options Roll Ticket — [Strategy Name]

## Execution Summary

| # | Action              | Contract                              | Qty | Target Price       | Est. Cash Impact |
|---|---------------------|---------------------------------------|-----|--------------------|------------------|
| 1 | SELL TO CLOSE       | [UNDERLYING] [OLD-EXP] $[OLD-STRIKE] PUT | [N] | Mid ~$[x.xx]/sh    | **+$[credit]**   |
| 2 | SELL TO CLOSE       | [UNDERLYING] [OLD-EXP] $[OLD-STRIKE] PUT | [N] | Mid ~$[x.xx]/sh    | **+$[credit]**   |
| 3 | BUY TO OPEN         | [UNDERLYING] [NEW-EXP] **$[NEW-STRIKE] PUT** | [N] | Mid ~$[x.xx]/sh est | **−$[debit]**    |
| 4 | BUY TO OPEN         | [UNDERLYING] [NEW-EXP] **$[NEW-STRIKE] PUT** | [N] | Mid ~$[x.xx]/sh est | **−$[debit]**    |
|   |                     |                                       |     | **Net debit**      | **≈ −$[net]**    |

⚠️ **Execution order matters**: place SELL TO CLOSE legs BEFORE BUY TO OPEN legs to recover residual value first. Alternatively use a diagonal-spread combo order if Fidelity supports "roll" as a single ticket type.

## Portfolio Context

- Portfolio value: $[amount]
- Current margin balance: $[amount] ([utilization %])
- Post-roll margin estimate: ~$[amount] ([new utilization %] — [band per margin-strategy.md])
- Hedge budget framework target: $[amount]/month
- Proposed roll amortized: $[net] / [N] months ([old-exp] → [new-exp]) = **$[monthly]/month** [✅ in budget | ⚠️ over budget]

## Current Hedge State ([date])

| Contract | Spot Est. | Strike | OTM % | DTE | Residual | Original Cost | P&L |
|----------|-----------|--------|-------|-----|----------|---------------|------|
| [UNDERLYING] [OLD-EXP] $[OLD-STRIKE]P ([N]x) | ~$[spot] | $[strike] | [X.X]% | [N] | $[residual] | $[cost] | [$ and %] |
| [UNDERLYING] [OLD-EXP] $[OLD-STRIKE]P ([N]x) | ~$[spot] | $[strike] | [X.X]% | [N] | $[residual] | $[cost] | [$ and %] |

**Framework diagnostics:**

- **DTE ([N])**: [In or out of 5-7 roll trigger window]. [Early roll rationale if applicable.] Framework target: maintain ~30 DTE for active protection.
- **[UNDERLYING-A] strike ([X.X]% OTM)**: [Within or outside framework 10-20% target]. [Decision: roll flat, adjust closer, adjust further].
- **[UNDERLYING-B] strike ([X.X]% OTM)**: [Same analysis].
- **Contract count ([N] total)**: $[portfolio] ÷ $50k per contract = [target range] contracts. Current [N] [✅ appropriate | ⚠️ under/over sized].

## Roll Strategy Rationale

**Why [NEW-EXP] expiry (not [alt-exp-1] or [alt-exp-2]):**

- [NEW-EXP] = [N] DTE from today — targets "30 DTE maintenance window" after mid-roll
- Monthly expiries have deeper liquidity than weeklies — tighter bid-ask, better mid-price execution
- [Any holiday / earnings / macro catalyst considerations]

**Why $[NEW-STRIKE-A] [UNDERLYING-A] / $[NEW-STRIKE-B] [UNDERLYING-B] strikes:**

- **[UNDERLYING-A] $[NEW-STRIKE-A] ([X.X]% OTM from ~$[spot])**: Hits framework 10-20% target. [Cost savings or premium tradeoff vs alternative strikes.] Still pays on [X]% drawdown.
- **[UNDERLYING-B] $[NEW-STRIKE-B] ([X.X]% OTM from ~$[spot])**: [Same analysis — note any shift from previous strike and why]. Consistent with [UNDERLYING-A] strike distance.

**Why NOT a collar (sell call to offset premium):**

- User's growth layer ([tickers like PLTR, TSLA, NVDA, MSTR, COIN]) has high volatility and conviction. Capping upside via short calls violates Pillar 3 thesis (equity building).
- Net cost of pure protective puts ($[monthly]/mo) is in framework budget. No need to finance via short calls.

**Why NOT inverse ETF (SQQQ/SH) instead:**

- Inverse ETFs suffer volatility drag on multi-week holds (documented in `hedging-strategies.md` lines 96-101). For a [N]-day hedge, protective puts are cleaner.

## Sizing & Cost Verification

- Framework: 1 contract per ~$50k portfolio → $[portfolio] = [target] contracts. [✅ or ⚠️] ([actual N])
- Framework: Budget $[budget]/month → Roll cost $[net] / [N] months = $[monthly]/mo [✅ or ⚠️]
- Framework: Target ~30 DTE average → Roll to [N] DTE, next roll at ~[N-30] DTE [✅ or ⚠️]
- Framework: Strike 10-20% OTM → $[NEW-STRIKE-A] [UNDERLYING-A] ([X.X]%) and $[NEW-STRIKE-B] [UNDERLYING-B] ([X.X]%) [✅ or ⚠️]

## Risk Notes

- **Price estimates are indicative, not executable**: If `market_data.py` is unavailable, spot and option premium estimates derived from [proxy source or CSV]. **Verify actual [NEW-EXP] chain mid-prices at Fidelity before placing orders.**
- **Implied volatility risk**: If VIX spikes between analysis and execution, new put premiums balloon. Hard stop-loss on roll cost: if net debit > $[max], pause and reassess (consider closer strikes or shorter expiry).
- **Leg-risk**: Executing close legs before open legs creates a ~1-minute window with no hedge. Acceptable in normal markets; during high-vol session, use Fidelity's "roll" combo ticket if available.
- **Assignment risk**: [Low/medium/high] — [reasoning based on moneyness and DTE].
- **Tax**: Close transactions realize [short-term capital loss / gain] on the [old-exp] legs ($[amount] STCL/STCG). Capture in [tax year] tax ledger.

## Execution Checklist

Before placing orders, verify at Fidelity:

- [ ] [NEW-EXP] [UNDERLYING-A] $[NEW-STRIKE-A] PUT bid/ask and mid
- [ ] [NEW-EXP] [UNDERLYING-B] $[NEW-STRIKE-B] PUT bid/ask and mid
- [ ] Net debit of full roll ≤ $[max] (hard stop)
- [ ] Account maintenance requirement unchanged after roll
- [ ] Options trading level supports short/long put (should be Level 2+ on Fidelity)

## Sources & Assumptions

- Hedge framework: `fin-guru/data/hedging-strategies.md` v[version] ([date])
- Options insurance framework: `fin-guru/data/options-insurance-framework.md` v[version]
- Current positions: `notebooks/updates/Portfolio_Positions_[MMM-DD-YYYY].csv` at [timestamp]
- [UNDERLYING-A] spot estimate: [source + method + caveat — e.g., VOO proxy × tracker-ratio 1.0]
- [UNDERLYING-B] spot estimate: [source + method + caveat]
- New put premium estimates: [$x.xx/sh [UNDERLYING-A], $x.xx/sh [UNDERLYING-B]] — derived from [IV assumption or options_chain_cli scan] (verify at execution)

---

**Educational Notice:** For educational purposes only; not investment advice. Options strategies carry risk of total premium loss. Past performance does not guarantee future results. Always consult qualified financial, tax, and legal advisors before implementing any hedging strategy.
