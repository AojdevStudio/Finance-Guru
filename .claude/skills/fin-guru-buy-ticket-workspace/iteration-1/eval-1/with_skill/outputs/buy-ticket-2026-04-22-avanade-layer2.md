---
document_type: buy-ticket
strategy_name: "Avanade W2 Paycheck — Layer 2 Income Deployment (April 2026)"
generated_on: "2026-04-22"
generated_by: "strategy-advisor"
portfolio_context_date: "2026-04-21"
deployment_amount: "$3,200.00"
cash_available: "$3,200.00"
remaining_cash_buffer: "$0.00"
price_snapshot_as_of: "Apr-21-2026 (Fidelity Portfolio_Positions_Apr-21-2026.csv — market_data.py unavailable due to circular-import error)"
itc_applicability: "unsupported"
itc_risk_score: "N/A"
---

# Buy Ticket — Avanade W2 Paycheck: Layer 2 Income Deployment (April 2026)

## Execution Summary

| Ticker    | Category                   | Weight   | $ Amount     | Price    | Shares     |
| --------- | -------------------------- | -------- | ------------ | -------- | ---------- |
| JEPI      | Covered-Call ETF (S&P 500) | 30.0%    | $960.00      | $57.50   | 16.696     |
| JEPQ      | Covered-Call ETF (NDX)     | 30.0%    | $960.00      | $58.64   | 16.371     |
| QQQI      | Covered-Call ETF (NDX)     | 20.0%    | $640.00      | $53.68   | 11.923     |
| SPYI      | Covered-Call ETF (S&P 500) | 20.0%    | $640.00      | $52.29   | 12.239     |
|           |                            |          |              |          |            |
| **TOTAL** |                            | **100%** | **$3,200.00** |          | **57.229** |

_Note: Prices sourced from `Portfolio_Positions_Apr-21-2026.csv` (last close Apr-21-2026 16:38 ET). Verify live prices at Fidelity before execution — market_data.py unavailable._

## Portfolio Context

- Portfolio context source: `notebooks/updates/Portfolio_Positions_Apr-21-2026.csv` (downloaded Apr-21-2026 16:38 ET; 1 day stale — within 2-day freshness window)
- Gross long positions: $262,787.21
- Margin debit (Pending Activity): $42,569.69
- Net portfolio equity: $220,217.52
- Margin utilization pre-deploy: 16.2% (margin debit / gross positions)
- Cash source: Avanade W2 paycheck $3,200 — deploying to cash account; no additional margin draw
- Margin utilization post-deploy (portfolio grows by $3,200): ~16.0%
- Remaining cash buffer after deployment: $0.00 (full paycheck deployed)

_User context note: Portfolio ~$220K net equity aligns with user's stated context of ~$220K with 19-20% margin utilization. The CSV-derived margin utilization of 16.2% reflects "Pending Activity" which includes the margin debit; actual margin utilization per Fidelity's margin dashboard may be 19-20% depending on additional margin balance data not present in the positions CSV._

## Strategy Rationale

**Source of funds:** Avanade W2 paycheck received on or around 2026-04-22, deposited to Fidelity cash sweep. $3,200.00 available for immediate deployment.

**Why Layer 2 reinforcement (not Layer 1 growth or balanced):**

1. **Coverage math is the binding constraint.** Monthly margin interest on the ~$42,570 debit at Fidelity's 11.325% rate is approximately $401/mo. The Layer 2 portfolio currently generates an estimated $800–900/mo combined dividend run-rate across JEPI, JEPQ, QQQI, SPYI, QQQY, YMAX, AMZY, MSTY, and CEF positions. Coverage ratio stands at approximately 2.0–2.2×. Strengthening income via fresh covered-call ETF shares directly widens the net margin spread and reinforces the coverage floor.

2. **Layer 1 is not underweight.** Growth exposure (PLTR $53,972, TSLA $28,595, VOO $26,537, SPMO $13,347, FNILX $12,690, PARR $11,016, NVDA $2,399, GOOGL $3,443, AAPL $2,933, COIN $6,039) totals approximately $161K — roughly 61% of gross portfolio. Adding more growth compounds concentration without solving the coverage math. Layer 2 is the binding constraint.

3. **Framework alignment.** Per `margin-strategy.md` Tier 1/Conservative band: maximum 20–30% margin utilization, minimum 3× dividend coverage target, asset class preference for established covered-call ETFs and high-quality CEFs over YieldMax volatility-harvesting products. Current YieldMax exposure (YMAX, AMZY, MSTY, QQQY) is already present — adding more increases yield-trap and NAV-erosion risk. JEPI/JEPQ/QQQI/SPYI are the preferred reinforcement path per Tier 1.

4. **No new tickers.** All four targets are existing portfolio incumbents. This deployment compounds existing positions, not new concentration points. Per `modern-income-vehicles.md` guidance on Options Premium Funds: JEPI and JEPQ represent the most stable covered-call ETF category (±5–10% distribution variance), while QQQI and SPYI (NEOS) carry slightly higher yield with comparable risk profile. The roster is already familiar and monitored.

**Allocation framework:**

- **JEPI 30% ($960)**: S&P 500 covered-call premium income. Monthly pay, ~$0.36/sh recent distribution = ~$6.01/mo income from this deployment tranche. Core position at 162.543 existing shares ($9,346 market value). Brings JEPI to ~$10,306 (3.9% of portfolio). JPM's distribution predictability and deep S&P 500 coverage make this the anchor of the Layer 2 income stack.
- **JEPQ 30% ($960)**: NDX covered-call premium income. Monthly pay, ~$0.45/sh = ~$7.37/mo. Existing combined position 233.706 shares ($13,705 market value). Brings JEPQ to ~$14,665 (5.5%). NDX-focused complement to JEPI — same JPM platform, different underlying index, adds tech-premium income to the S&P 500 base.
- **QQQI 20% ($640)**: NEOS NDX high-income. Monthly pay, ~$0.61/sh = ~$7.27/mo. Existing combined position 331.630 shares ($17,802 market value). Brings QQQI to ~$18,442 (6.9%). Highest individual ETF weight in the portfolio — reinforcing the incumbent income leader. NEOS tax-efficient structure preferred.
- **SPYI 20% ($640)**: NEOS S&P 500 high-income. Monthly pay, ~$0.51/sh = ~$6.24/mo. Existing combined position 231.712 shares ($12,116). Brings SPYI to ~$12,756 (4.8%). Complements QQQI with S&P 500 index, maintaining the 50/50 S&P/NDX balance that mirrors the existing SPY/QQQ put hedge structure.

**Weighting rationale:** 60% equal-weight JEPI/JEPQ (institutional-grade JPM coverage with distribution-policy predictability, lower variance ±5–10%) versus 40% QQQI/SPYI (NEOS higher-yield products, slightly higher NAV-erosion risk, superior tax efficiency). This split is consistent with the prior Apr-21-2026 Layer 2 reinforcement deployment and maintains the portfolio's established S&P-vs-NDX income balance.

## Execution Details

- Price snapshot captured: `notebooks/updates/Portfolio_Positions_Apr-21-2026.csv` at 2026-04-21 16:38 ET (last close)
- Price fallback used: market_data.py unavailable (circular-import error — `src/utils/logging.py` shadows stdlib `logging`). CSV Last Price column used as fallback per workflow-patterns.md Step 3 degradation protocol.
- Fractional shares: enabled on all four tickers (Fidelity supports fractional on JEPI, JEPQ, QQQI, SPYI)
- DRIP enabled: YES on all four (accumulation phase — reinvest distributions)
- Monthly income target from this deployment: ~$26.89/mo (~$322.71/yr, ~10.1% effective yield)
- This deployment: $3,200.00 one-shot paycheck deployment (full paycheck to Layer 2 per current-phase mandate)

## Risk Notes

- **Prices stale by 1 day**: CSV dated Apr-21-2026. Market opened Apr-22-2026. Verify current prices at Fidelity before placing orders — overnight moves may affect share counts. Shares field is indicative; Fidelity's order preview will show actuals.
- **Covered-call ETF upside cap**: All four positions sell call options, capping monthly price appreciation. In strong bull-run months, these funds underperform their underlying indices. Acceptable trade-off: the Layer 2 mandate prioritizes income over capital appreciation.
- **QQQI concentration note**: Post-deploy, QQQI becomes the largest individual ETF position at ~$18,442 (~6.9% of gross portfolio). Still well inside the 30% single-position limit. No concentration warning triggered. Layer 2 as a combined category reaches ~$99,339 (approximately 37.7% of gross portfolio post-deploy) — this is a high allocation to income vehicles; user has explicitly accepted this as the Layer 2 mandate.
- **Interest rate / VIX sensitivity**: Covered-call premium income compresses when VIX < 14 for extended periods. Per `modern-income-vehicles.md`, ±5–10% monthly distribution variance is normal for JEPI/JEPQ; ±5–10% for QQQI/SPYI. Do not flag monthly variance as structural concern unless it exceeds 30% sustained over 3 months.
- **Zero cash buffer post-deploy**: Full paycheck deployed. Any unexpected near-term cash need draws against margin. Existing margin debit (~$42,570) and net equity ($220K) provide ample headroom. Monitor for any large upcoming expense before executing.
- **Margin utilization**: Deploying cash (not margin) keeps debit flat at ~$42,570. Post-deploy margin utilization drops marginally (16.0% vs 16.2%) as gross portfolio increases. Comfortably within Tier 1/Conservative band (20–30% ceiling). No margin risk advisory required.

## Sources & Assumptions

- Price snapshot: `notebooks/updates/Portfolio_Positions_Apr-21-2026.csv` at 2026-04-21 16:38 ET (fallback — market_data.py circular-import error)
- Portfolio context: Fidelity Apr-21-2026 positions CSV; no same-day Balances CSV present
- Distribution estimates: JEPI ~$0.36/sh/mo, JEPQ ~$0.45/sh/mo, QQQI ~$0.61/sh/mo, SPYI ~$0.51/sh/mo — derived from recent trailing distribution rates consistent with gold-standard buy-ticket-2026-04-21-layer2-reinforcement.md
- Margin interest rate: 11.325% annual (per prior ticket context; verify current Fidelity rate)
- Net equity calculation: gross long positions ($262,787) minus pending activity debit ($42,570)
- Execution assumptions: Fidelity market orders during regular session Apr-22-2026; fractional fills allowed; DRIP auto-enabled for these tickers; no concurrent options roll required with this deployment

## Progress Tracking

- Month 4 of 2026 deployment cycle; second Layer 2 deployment this month (follows Apr-21 $5,196 Layer 2 reinforcement)
- Monthly income impact: +$26.89/mo from this tranche
- Target success probability: Monte Carlo not run; standard income accumulation posture
- Next planned deployment: TBD — pending next paycheck or Goucher distribution; continue Layer 2 reinforcement cadence through Q2 2026

---

**Educational Notice:** For educational purposes only; not investment advice. Consult a licensed financial professional before acting. All investments involve risk, including possible loss of principal. Covered-call ETFs feature NAV erosion risk in prolonged bull markets and yield compression in low-volatility regimes (VIX < 14). Options-premium income is variable and not guaranteed. Past performance does not guarantee future results.
