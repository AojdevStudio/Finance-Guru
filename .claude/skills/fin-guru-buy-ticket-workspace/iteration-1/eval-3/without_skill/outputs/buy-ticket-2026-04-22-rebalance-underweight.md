---
document_type: buy-ticket
strategy_name: "Rebalance Underweight Layer 2 Buckets"
generated_on: "2026-04-22"
generated_by: "strategy-advisor"
portfolio_context_date: "2026-04-21"
deployment_amount: "$5,000.00"
cash_available: "$5,000.00"
remaining_cash_buffer: "$0.00"
price_snapshot_as_of: "2026-04-21 4:38 PM ET (Fidelity export)"
itc_applicability: "not-run"
itc_risk_score: "N/A"
---

# Buy Ticket — Rebalance Underweight Layer 2 Buckets

## Execution Summary

| Ticker    | Category                | Weight  | $ Amount    | Price    | Shares   |
| --------- | ----------------------- | ------- | ----------- | -------- | -------- |
| JEPI      | JPMorgan Income         | 32.7%   | $1,635.07   | $57.50   | 28.436   |
| JEPQ      | JPMorgan Income         | 32.7%   | $1,635.07   | $58.64   | 27.883   |
| YMAX      | YieldMax Volatility     | 11.4%   | $570.86     | $8.48    | 67.318   |
| MSTY      | YieldMax Volatility     | 11.8%   | $588.16     | $25.50   | 23.065   |
| AMZY      | YieldMax Volatility     | 11.4%   | $570.86     | $12.36   | 46.186   |
|           |                         |         |             |          |          |
| **TOTAL** |                         | **100%**| **$5,000.02** |        |          |

## Portfolio Context

- Portfolio context source: `notebooks/updates/Portfolio_Positions_Apr-21-2026.csv`
- Layer 2 Income portfolio total (as of Apr 21): $96,139.23
- Cash available before deployment: $5,000.00
- This deployment: $5,000.00
- Remaining cash buffer after deployment: $0.00

## Allocation Framework — Layer 2 Deviation Analysis

The rebalance targets the two underweight Layer 2 buckets identified from the Apr 21 snapshot vs. the 5-bucket target framework in `config/bucket-allocations.json`.

| Bucket               | Target % | Target $    | Actual $    | Actual % | Deviation    |
| -------------------- | -------- | ----------- | ----------- | -------- | ------------ |
| JPMorgan Income      | 27%      | $25,957.59  | $23,050.73  | 24.0%    | **–$2,906.86** (UNDERWEIGHT) |
| CEF Stable           | 20%      | $19,227.85  | $19,837.51  | 20.6%    | +$609.66 (over) |
| Covered Call ETFs    | 35%      | $33,648.73  | $34,296.56  | 35.7%    | +$647.83 (over) |
| YieldMax Volatility  | 10%      | $9,613.92   | $8,076.22   | 8.4%     | **–$1,537.70** (UNDERWEIGHT) |
| DRIP v2 CEFs         | 8%       | $7,691.14   | $10,878.21  | 11.3%    | +$3,187.07 (over) |

**Total positive deviation (underweight gap): $4,444.56**

The $5,000 budget is allocated pro-rata to underweight deviations only — no overshoot of targets:

- JPMorgan Income: $2,906.86 ÷ $4,444.56 × $5,000 = **$3,270.13** (65.4%)
- YieldMax Volatility: $1,537.70 ÷ $4,444.56 × $5,000 = **$1,729.87** (34.6%)

## Strategy Rationale

**Allocation Framework:**

- **JPMorgan Income (27% target):** JEPI + JEPQ at 50/50 within-bucket split. This bucket is the core stability anchor — low volatility, 8-10% yield, highest liquidity. It is the most underweight by dollar amount ($2,907 gap). Per strategy mandate, JEPI/JEPQ absorb the majority of catch-up capital.

- **YieldMax Volatility (10% target):** YMAX, MSTY, AMZY at 33/34/33% within-bucket split. The portfolio's high-yield satellite carries genuine NAV erosion risk, but a sustained 1.6% underweight (8.4% vs. 10% target) drifts the blended portfolio yield below the 24-30% target band. Reintroducing pro-rata allocation across all three tickers restores bucket balance without crowding any single name.

- **No capital to CEF Stable, Covered Call ETFs, or DRIP v2 CEFs:** All three are overweight. Directing new capital there would compound the imbalance. They receive $0 this deployment.

## Execution Details

- Price snapshot source: Fidelity CSV export (`Portfolio_Positions_Apr-21-2026.csv`) at 4:38 PM ET Apr 21, 2026
- Fractional shares assumed on all 5 tickers (Fidelity supports fractional equity/ETF purchases)
- DRIP status: Confirm DRIP settings for JEPI, JEPQ, YMAX, MSTY, AMZY in Fidelity account settings
- Account: Z05724592 (HM & Ossie — Margin account)
- All purchases execute in Margin sweep unless cash is available at the time of order

## Risk Notes

- **MSTY concentration warning:** MSTY is already –47.09% from cost basis ($1,060 → $561). The YieldMax bucket carries the strategy's highest variance tolerance (±25%). The $588 allocation is within the pro-rata framework, but MSTY's NAV erosion trajectory warrants monitoring — if MSTR continues downward, consider pausing MSTY within the bucket and routing its share to YMAX or AMZY.
- **YieldMax bucket as a whole:** YMAX/MSTY/AMZY collectively are high-decay, option-premium strategies. The 10% target cap is itself the risk guardrail — this deployment restores it to target, not above.
- **Margin context:** Portfolio carries ~$42,570 in pending margin activity (per CSV). Current Layer 2 at $96k vs. total portfolio equity of ~$220k (excluding pending activity) implies margin is within normal operating range. This $5,000 deployment does not materially change margin exposure.

## ITC Advisory

- ITC applicability: not-run
- No ITC signal was consulted for this rebalance. Deployment is rules-based (target-weight deviation), not momentum-triggered.

## Sources & Assumptions

- Price snapshot: `notebooks/updates/Portfolio_Positions_Apr-21-2026.csv` at 4:38 PM ET, 2026-04-21
- Portfolio context: Same CSV — Layer 2 position values aggregated across Margin and Cash sub-types
- Allocation targets: `fin-guru-private/fin-guru/strategies/active/config/bucket-allocations.json` (v3.0, last updated 2025-11-13)
- Strategy framework: `fin-guru-private/fin-guru/strategies/active/portfolio-master-strategy.md` (v3.4)
- Within-bucket splits: 50/50 for JPMorgan; 33/34/33 for YieldMax (from bucket-allocations.json)
- Shares calculated at last CSV price — actual execution price will vary
- QQQI appears in both Margin ($14,097.97) and Cash ($3,703.92) rows; combined as single position

## Progress Tracking

- Layer 2 post-deployment value (estimated): $101,139.23
- Post-deployment JPMorgan Income share: ~24.9% (narrows gap from 24.0% → target 27%)
- Post-deployment YieldMax Volatility share: ~9.7% (from 8.4% → approaching 10% target)
- Next planned deployment: May 2026 paycheck cycle (~$6,418)
- Monthly dividend income (current baseline): ~$1,072/month

---

**Educational Notice:** For educational purposes only; not investment advice. Consult a licensed financial professional before acting. All investments involve risk, including possible loss of principal.
