---
document_type: options-open-ticket
strategy_name: "Initial Protective Put Program — Tech-Heavy $200K Portfolio (April 2026)"
generated_on: "2026-04-22"
generated_by: "strategy-advisor"
portfolio_context_date: "2026-04-21"
total_premium_outlay: "$1,030"
monthly_amortized_cost: "$542"
price_snapshot_as_of: "2026-04-22 09:03 CDT (options_chain_cli.py live scan)"
hedge_framework: "fin-guru/data/hedging-strategies.md v1.0"
---

# Options Open Ticket — Initial Protective Put Program (Tech-Heavy $200K, April 2026)

## Execution Summary

| # | Action        | Contract                            | Qty | Target Price       | Est. Cash Impact |
|---|---------------|-------------------------------------|-----|--------------------|------------------|
| 1 | BUY TO OPEN   | QQQ Jun-18-2026 $550 PUT            | 2   | Mid ~$2.99/sh      | **−$598**        |
| 2 | BUY TO OPEN   | SPY Jun-18-2026 $600 PUT            | 2   | Mid ~$2.16/sh      | **−$432**        |
|   |               |                                     |     | **Total outlay**   | **≈ −$1,030**    |

> _Place legs independently (not as combo order) on Fidelity to avoid combo-order fill issues with long puts._

## Portfolio Context

- Portfolio value (stated): $200,000 (hedging basis)
- Portfolio value (Apr-21-2026 CSV): $220,217 (Fidelity TOD brokerage; using $200K stated as hedge basis per task)
- Margin balance (Apr-21-2026): $42,569.69 (19.3% utilization)
- Post-open margin estimate: ~$43,600 (19.8% utilization — still Tier 1 Conservative, minimal impact)
- **Concentration (tech-heavy profile):**
  - PLTR: 24.5% — high-conviction growth, direct QQQ proxy
  - TSLA: 13.0% — growth/momentum, QQQ + SPY proxy
  - QQQI (2 lots): 8.1% — direct Nasdaq-100 income ETF (QQQ hedge very direct)
  - JEPQ: 5.3% — Nasdaq-100 premium ETF
  - SPMO: 6.1% — S&P 500 momentum (SPY proxy)
  - VOO: 12.1% — direct S&P 500 (SPY direct proxy)
  - FNILX: 5.8% — S&P 500 index (SPY proxy)
  - COIN: 2.7% — crypto proxy, correlated with growth/tech risk-off
  - MSTR: 1.1% — crypto proxy
  - **Effective tech/Nasdaq-100 exposure: ~53% (PLTR + TSLA + QQQI + JEPQ + growth residual)**
  - **Effective S&P 500 exposure: ~27% (VOO + FNILX + SPMO + SPYI + JEPI)**
- Hedge budget: $800/month (from `user-profile.yaml` Layer 3 — portfolio_strategy.deployment_split.layer_3_hedge)
- Proposed outlay amortized: $1,030 / 1.9 months (to Jun 18 roll trigger) = **$542/month** ✅ in budget

## Sizing Rationale

- **Framework sizing**: ~1 contract per ~$50k portfolio → $200k ÷ $50k = **4 contracts total**
  - At QQQ $650/sh: 1 contract = $65,000 notional. 2 contracts = $130,000 notional (QQQ proxy)
  - At SPY $709/sh: 1 contract = $70,900 notional. 2 contracts = $141,800 notional (SPY proxy)
  - _Note: Underlying notional exceeds $200K slightly — this is structural to multi-index hedging. Contract count (4) is the operative sizing lever, not notional coverage._
- **Chosen contract count: 4** (2 QQQ + 2 SPY) — at target sizing
- **Multi-underlying weights (adjusted for tech-heavy concentration):**
  - QQQ: 2 contracts (50%) — _raised above 40-50% framework midpoint; tech/Nasdaq-100 represents ~53% of effective portfolio exposure. QQQ is the most direct hedge for PLTR, TSLA, QQQI, JEPQ._
  - SPY: 2 contracts (50%) — _matches S&P 500 broad-market exposure (VOO, FNILX, SPMO, SPYI, JEPI ~27%). Provides broad-market floor coverage separate from tech-specific correction._
  - IWM: **0 contracts (dropped)** — portfolio has no meaningful small-cap exposure. VXUS ($2K), FZILX (<$500), and PARR ($11K) are not small-cap proxies. Allocating IWM premium would hedge exposure that doesn't exist.
- **Weighting adjustment from framework default**: QQQ held at 50% (top of 40-50% range) vs default 40% midpoint. Justified by 53% effective Nasdaq-100 exposure in portfolio (PLTR + TSLA + QQQI + JEPQ dominate). SPY at 50% (top of 30-40% range) covers remaining broad-market layer. IWM omitted — no small-cap exposure to hedge.

## Contract Selection Rationale

### QQQ Jun-18-2026 $550 PUT (Selected)

**Spot**: $650.12 | **Strike**: $550 | **OTM%**: 15.4% | **DTE**: 57 | **Mid**: $2.99 | **OI**: 55,491 | **Delta**: −0.069

**Why Jun-18-2026 expiry:**
- 57 DTE from today (2026-04-22) — targets the "30 DTE maintenance window" after mid-period. At roll trigger (~7 DTE ≈ Jun 11), ~50 days of active protection will have been consumed.
- Monthly expiry (third Friday) — deepest liquidity. QQQ Jun-18 $550P has OI of 55,491 — exceptional fill quality expected.
- Avoids May 15 (existing roll positions already expiring) and avoids weekly options (thinner liquidity).
- Jun 18 is post-Memorial Day weekend and pre-July 4 — no holiday gap risk in the coverage window.

**Why $550 strike (15.4% OTM):**
- $550 on QQQ spot $650 = exactly 15.4% OTM — squarely in the framework 10-20% target band.
- Pays out if QQQ drops from $650 to below $550 (a -15% move). For a tech-heavy portfolio, a -15% Nasdaq correction is the scenario most worth hedging — not a -5% dip (over-hedging) or a -25% crash (under-hedging the meaningful range).
- Delta of −0.069 means the put gains $6.90 per 1-pt QQQ decline at current spot — appropriate insurance sensitivity.
- Cost efficiency: $2.99/sh vs $5.12/sh for $580P (10.8% OTM). The $580P costs 71% more premium for only 4.6 additional percentage points of closer coverage. At-budget constraint makes $550 the rational choice.
- **Top 3 QQQ candidates considered:**

| Strike | OTM% | Mid | OI | Notes |
|--------|-------|-----|----|-------|
| $550 | 15.4% | $2.99 | 55,491 | **Selected** — sweet spot cost/coverage/liquidity |
| $560 | 13.9% | $3.60 | 45,590 | $0.61/sh more (20% premium increase for 1.5% closer) |
| $540 | 16.9% | $2.55 | 33,325 | Cheaper but pays only on -17% drawdown |

### SPY Jun-18-2026 $600 PUT (Selected)

**Spot**: $709.25 | **Strike**: $600 | **OTM%**: 15.4% | **DTE**: 57 | **Mid**: $2.16 | **OI**: 73,410 | **Delta**: −0.052

**Why Jun-18-2026 expiry:**
- Same rationale as QQQ — 57 DTE, monthly expiry (Jun-18), deepest liquidity. SPY Jun-18 $600P has OI of 73,410 — excellent.
- Consistent expiry across all legs allows simultaneous roll at the single trigger date. Mixed expiries would require separate roll decisions.

**Why $600 strike (15.4% OTM):**
- $600 on SPY spot $709 = 15.4% OTM — mirrors QQQ strike distance exactly. Consistent framework application.
- Pays out if SPY drops from $709 to below $600 (-15.4%). Broad-market -15% is a material drawdown (like March 2020, August 2015 in magnitude terms) — exactly the scenario this hedge covers.
- Delta of −0.052 provides clean broad-market hedge sensitivity.
- OI of 73,410 is the second-highest in the full SPY scan — extremely liquid.
- **Top 3 SPY candidates considered:**

| Strike | OTM% | Mid | OI | Notes |
|--------|-------|-----|----|-------|
| $600 | 15.4% | $2.16 | 73,410 | **Selected** — highest cost-efficiency at target OTM% |
| $620 | 12.6% | $2.96 | 42,430 | $0.80/sh more (37% more premium) for only 2.8% closer |
| $595 | 16.1% | $1.99 | 28,512 | Saves $0.17/sh but slight coverage reduction |

**Why protective puts (not collar, not inverse ETF):**
- **Not collar**: Portfolio's growth layer (PLTR 24.5%, TSLA 13%, COIN/MSTR ~4%) has high conviction and is the primary wealth-building engine (Pillar 3 per hedging-strategies.md). Selling calls against these positions would cap the asymmetric upside that justifies holding them. At $800/month budget, pure protective puts are fully affordable — no need to sacrifice upside to finance.
- **Not SQQQ/SH inverse ETFs**: Inverse ETFs reset daily and suffer volatility drag over multi-week holds (hedging-strategies.md lines 96-113). A 57-day hold of SQQQ in a choppy market would erode capital even without a directional Nasdaq decline. Protective puts have a defined, fixed premium cost and a clean payoff profile.

## Budget Impact

| Metric | Value |
|---|---|
| Total premium outlay | $1,030 |
| Coverage period | ~1.9 months (Apr 22 → Jun 11 roll trigger) |
| Amortized monthly cost | **$542/month** |
| Framework target monthly | $500–600/month |
| User budget (Layer 3) | $800/month |
| Variance vs framework | +$42/month above framework midpoint (within range) |
| Variance vs user budget | −$258/month below budget ✅ |
| Annualized cost of protection | ~3.1% of $200K portfolio |

> The $542/month vs $800 budget leaves $258/month of undeployed hedge budget. Options: (1) hold in reserve for IV-spike rolls when replacement premiums are elevated, (2) add a third underlying if portfolio composition shifts to include small-cap, or (3) redeploy to Layer 2 if hedge thesis remains stable. No action required on Day 1.

## First Roll Trigger

- **Roll trigger date**: ~Jun 11, 2026 (7 DTE from Jun 18 expiry)
- **Target replacement expiry**: Jul 17, 2026 (29 DTE from Jun 11 trigger — monthly expiry, avoids July 4 weekend gap)
- **Reminder mechanism**: Log positions with `rolling_tracker_cli.py log-open` (command in Post-Open State section below). The tracker computes DTE daily and will flag positions at ≤7 DTE.
- **Next skill invocation**: `fin-guru-hedge-roll` in **ROLL mode** when user says "roll my puts" around Jun 11.

## Risk Notes

- **Premium-loss risk (primary)**: If QQQ and SPY stay flat or rise through Jun 18, all $1,030 premium is lost. This is the expected cost of insurance — per the framework analogy, paying a homeowners premium that expires worthless is the intended outcome in a flat/up market. Annualized, $542/month on $200K = 3.1% cost of protection.
- **IV environment at open**: Current IV regime is _elevated_. QQQ Jun-18 $550P implied volatility = 34.3%; SPY Jun-18 $600P IV = 29.5%. VIX conditions in April 2026 remain elevated post-tariff uncertainty. This means these premiums are _more expensive than a low-IV baseline_ — you are paying elevated insurance premiums. Tradeoff: elevated IV means the market is already pricing significant downside risk, which is precisely when protection is most valuable.
- **Assignment risk**: Negligible. Long puts cannot be assigned. Risk is solely total premium loss if OTM at expiry.
- **Leg risk**: Opening two separate legs. No close-before-open risk (this is a pure open, not a roll). Place QQQ leg first, then SPY — no execution order constraint on opens.
- **Margin interaction**: $1,030 debit reduces cash. If funded from margin (current balance $42,570), utilization increases by ~0.5% to ~19.8% — remains Tier 1 Conservative. No margin call risk from this debit.
- **Tech concentration risk not fully hedged**: PLTR (24.5%) is a high-beta Nasdaq name but is not perfectly correlated with QQQ. PLTR could underperform or outperform QQQ in a drawdown. QQQ puts hedge _index-level_ tech risk, not _idiosyncratic_ PLTR risk. If PLTR-specific bad news triggers a drop, the QQQ put may underperform as a hedge.
- **Crypto-proxy residual**: COIN ($6K, 2.7%) and MSTR ($2.5K, 1.1%) carry crypto beta. Neither QQQ nor SPY puts hedge crypto-specific risk. Acceptable at <4% combined weight; monitor if crypto allocation grows.
- **Tax**: Premium outlay ($1,030) is a capital cost. No realization event until the positions are closed, rolled, or expire. If these expire worthless, the $1,030 is a short-term capital loss in 2026.

## Execution Checklist

Before placing orders, verify at Fidelity:

- [ ] QQQ Jun-18-2026 $550 PUT: confirm bid/ask mid is ~$2.99 (accept up to $3.25 before pausing)
- [ ] SPY Jun-18-2026 $600 PUT: confirm bid/ask mid is ~$2.16 (accept up to $2.40 before pausing)
- [ ] Total outlay ≤ $1,200 hard stop (above this, pause and reassess further OTM strikes)
- [ ] Account shows long options permissions enabled (Fidelity Level 1+ required for long puts)
- [ ] Maintenance requirement unchanged after open
- [ ] If IV spikes materially (VIX +20% intraday) between analysis and execution, pause — new premiums may have surged; consider $540 QQQ / $595 SPY alternatives to stay in budget

## Sources & Assumptions

- Hedge framework: `fin-guru/data/hedging-strategies.md` v1.0 (2026-02-17)
- Options insurance framework: `fin-guru/data/options-insurance-framework.md` (referenced via framework-rules.md)
- Portfolio positions: `notebooks/updates/Portfolio_Positions_Apr-21-2026.csv` downloaded 2026-04-21 16:38 ET
- QQQ spot at analysis: $650.12 (options_chain_cli.py live scan, 2026-04-22 ~09:03 CDT)
- SPY spot at analysis: $709.25 (options_chain_cli.py live scan, 2026-04-22 ~09:03 CDT)
- Option premium data: `src/analysis/options_chain_cli.py` live chain scan via yfinance, 2026-04-22 ~09:03 CDT ✅ (chain data retrieved successfully — not a fallback)
- User budget: `fin-guru/data/user-profile.yaml` → `portfolio_strategy.deployment_split.layer_3_hedge: 800`
- Hedge sizer: `src/analysis/hedge_sizer_cli.py --portfolio-value 200000 --budget 800` → 4 contracts total (tool returned 308% utilization warning using QQQ-only default weights; warning is a tool artifact from 4×QQQ pricing, not applicable to this 2-QQQ/2-SPY split which lands at $542/month ✅)
- Multi-underlying allocation: manually applied per `hedging-strategies.md` lines 150-174 with tech-heavy adjustment (QQQ 50%, SPY 50%, IWM 0%)

## Post-Open State (to seed rolling_tracker)

```yaml
positions:
  - ticker: QQQ
    strike: 550
    expiry: 2026-06-18
    quantity: 2
    entry_premium: $2.99
    entry_date: 2026-04-22
  - ticker: SPY
    strike: 600
    expiry: 2026-06-18
    quantity: 2
    entry_premium: $2.16
    entry_date: 2026-04-22
```

After fills confirmed, run:

```bash
uv run python src/analysis/rolling_tracker_cli.py log-open \
  --ticker QQQ --strike 550 --expiry 2026-06-18 --qty 2 --entry-premium 2.99

uv run python src/analysis/rolling_tracker_cli.py log-open \
  --ticker SPY --strike 600 --expiry 2026-06-18 --qty 2 --entry-premium 2.16
```

> _Run these commands only after fill confirmations from Fidelity. Use actual fill prices, not estimates, for accurate P&L tracking._

---

**Educational Notice:** For educational purposes only; not investment advice. Options strategies carry risk of total premium loss. Past performance does not guarantee future results. Always consult qualified financial, tax, and legal advisors before implementing any hedging strategy. Opening a protective put program commits monthly premium that is lost if market rises or stays flat through the expiration date. The $1,030 total outlay represents the maximum possible loss on this program; upside participation in your portfolio positions is fully preserved.
