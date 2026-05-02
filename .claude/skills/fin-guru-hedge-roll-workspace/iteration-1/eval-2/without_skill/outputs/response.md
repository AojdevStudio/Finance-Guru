---
title: Portfolio Protection Plan — April 2026
date: 2026-04-22
type: hedge-plan
disclaimer: Educational purposes only. Not investment advice. Options trading involves substantial risk of loss. Consult a licensed financial advisor, tax professional, and legal counsel before implementing any strategy.
---

# Portfolio Protection Plan

_Educational purposes only. Not investment advice. Consult qualified professionals before acting._

---

## Your Situation (as of April 2026)

| Metric | Value |
|--------|-------|
| Portfolio Value | ~$198,500 |
| Margin Debt | $45,657 (23%) |
| Monthly Dividends | ~$1,170 |
| Margin Interest | ~$431/mo |
| Dividend Coverage | 2.7x interest |
| Stress Test (–40%) | Still safe, no margin call |

Your portfolio is structurally sound through a –40% drawdown, but you carry $45K in margin and a concentrated growth/dividend book. That combination makes downside protection meaningful. A –20% move reduces equity cushion — a hedge buys you time and prevents forced selling.

---

## Recommended Approach: Protective Puts on QQQ + SPY

Based on your portfolio size, composition (tech/growth + dividend), and the margin component, a diversified put hedge across QQQ and SPY is the most appropriate starting point.

### Strategy: Protective Puts (30 DTE Rolling)

**Why protective puts over inverse ETFs or collars:**
- Inverse ETFs (SQQQ/SH) decay daily from compounding drag — unsuitable for anything beyond 1–2 weeks
- A collar (sell call + buy put) would cap your upside on a portfolio you want to grow
- Protective puts give you a defined monthly cost, full upside exposure, and a clean floor on losses

---

## Sizing for ~$198,500 Portfolio

Using the _~1 contract per $50,000_ sizing rule, a $198K portfolio warrants **3–4 contracts**.

### Allocation by Index

| Underlying | Rationale | Contract Allocation |
|---|---|---|
| QQQ (Nasdaq-100) | Covers tech/growth holdings | 2 contracts (~50%) |
| SPY (S&P 500) | Broad market / large-cap | 1–2 contracts (~40%) |
| IWM (Small-cap) | Optional, lower weight | 0–1 contracts (~10%) |

Start with **2 QQQ + 1 SPY** (3 total) and adjust as you learn the cost structure.

---

## Strike Selection

Target **10–15% OTM** from current price — this is the sweet spot between cost and protection depth.

| Index | ~Current Level (Apr 2026) | 10% OTM Strike Target | 15% OTM Strike Target |
|---|---|---|---|
| QQQ | ~$450–460 | ~$405–415 | ~$385–390 |
| SPY | ~$530–545 | ~$475–490 | ~$450–465 |

_Verify actual prices before placing any order._

- 10% OTM = lower deductible, higher premium (~$4–6/share per contract)
- 15% OTM = higher deductible, lower premium (~$2–4/share per contract)
- These act like homeowners insurance deductibles: you absorb the first 10–15% of loss before the put pays out

---

## Rolling Cadence

| Timing | Action |
|---|---|
| At purchase | Buy 30 DTE puts at target strike |
| At 5–7 DTE | Roll — sell expiring put, buy new 30 DTE put |
| Monthly | Review IV environment and adjust strikes if underlying moved >10% |

**Cost-to-Roll formula:**
```
Net Roll Cost = New Put Premium − Residual Value of Expiring Put
```

If the expiring put still has residual value (partially ITM or recently OTM), sell it before buying the replacement. The net cost is what you track against your monthly budget.

---

## Budget Estimate

| Scenario | Monthly Cost | Annualized |
|---|---|---|
| 3 contracts, 10% OTM | ~$900–1,500 | ~$10,800–18,000 |
| 3 contracts, 15% OTM | ~$600–900 | ~$7,200–10,800 |
| Target budget | ~$500–700 | ~3–4% of portfolio |

**Key insight:** Your monthly dividends (~$1,170) cover your entire hedge budget. The Three-Pillar framework applies directly: _dividends fund the insurance layer_. Protection is essentially self-financing from your income stream, with surplus left over to service margin interest.

---

## The Three-Pillar View of Your Portfolio

```
         [Insurance Layer — Protective Puts]
                   Protects $198K
                        |
              Funded by |  (~$500–700/mo)
                        v
          [Income Layer — ~$1,170/mo Dividends]
             Covers puts AND margin interest
                        |
           Surplus of   |  ~$470/mo reinvested
                        v
         [Growth Layer — Tech / Dividend Positions]
              Compounds wealth, highest volatility
                        |
              Grows     |  portfolio value
                        v
         [Larger portfolio → more insurance needed
          but more income generated → self-funding]
```

The system works in your favor: dividends already more than cover margin interest (2.7x), and can absorb put premiums without adding new cash. You are already in the income-funds-insurance structure — you just need to execute the put purchases.

---

## When Protection Is Not Worth Buying

Know the exit conditions so you can let hedges expire when the thesis changes:

- Market regime normalizes (VIX falls below 15, broad breadth recovers)
- You reduce margin meaningfully (below $25K), reducing forced-selling risk
- Portfolio diversifies further (less concentration = less idiosyncratic risk)
- Cash reserves build to cover 3+ months of drawdown without forced selling

---

## Immediate Next Steps

1. **Check current VIX level** — if VIX > 20, puts are more expensive; wait for a pullback in vol if you can, or accept the elevated premium as a cost of current risk
2. **Check QQQ and SPY real-time** — verify actual prices and available strikes in your brokerage before selecting exact strikes
3. **Start with 2 QQQ puts at 15% OTM, 30 DTE** — lower cost entry to learn the roll mechanics before adding SPY contracts
4. **Set a calendar reminder at 7 DTE** — to execute your first roll. Building the habit is more important than getting the first strike perfect
5. **Track costs in a simple log** — premium paid, roll cost, cumulative spend. Compare quarterly to dividend income

---

## Important Reminders

- _You already hold QQQ/SPY puts (noted in April 2026 sync) — verify those positions before buying additional contracts to avoid over-hedging_
- American-style options (all US equity/ETF options) can be exercised before expiration; the put value will not fall below intrinsic value even if time value decays
- Options premiums are non-refundable. If the market rises, the full premium is the cost of protection — this is expected and normal, not a loss
- Over-hedging creates its own drag. 3–4 contracts on a $198K portfolio is the ceiling, not the target

---

_This plan is for educational purposes only and does not constitute investment advice. Options trading involves substantial risk of loss and is not suitable for all investors. Past performance does not guarantee future results. Consult a licensed financial advisor, tax professional, and legal counsel before implementing any strategy._
