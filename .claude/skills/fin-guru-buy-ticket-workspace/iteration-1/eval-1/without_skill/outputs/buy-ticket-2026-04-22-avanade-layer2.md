---
document_type: buy-ticket
strategy_name: "Avanade W2 Paycheck — Layer 2 Income Deployment"
generated_on: "2026-04-22"
generated_by: "strategy-advisor"
portfolio_context_date: "2026-04-21"
deployment_amount: "$3,200.00"
cash_available: "$3,200.00"
remaining_cash_buffer: "$0.00"
price_snapshot_as_of: "2026-04-22 (yfinance close)"
itc_applicability: "not-run"
itc_risk_score: "N/A"
---

# Buy Ticket — Avanade W2 Paycheck: Layer 2 Income Deployment

## Execution Summary

| Ticker    | Category                        | Weight   | $ Amount     | Price    | Shares     |
| --------- | ------------------------------- | -------- | ------------ | -------- | ---------- |
| JEPI      | Covered Call Income — S&P 500   | 30.0%    | $960.00      | $57.61   | 16.664     |
| JEPQ      | Covered Call Income — Nasdaq    | 30.0%    | $960.00      | $58.80   | 16.327     |
| QQQI      | High Income — Nasdaq-100        | 20.0%    | $640.00      | $53.35   | 11.996     |
| SPYI      | High Income — S&P 500           | 20.0%    | $640.00      | $52.01   | 12.305     |
|           |                                 |          |              |          |            |
| **TOTAL** |                                 | **100%** | **$3,200.00**|          |            |

## Portfolio Context

- Portfolio context source: `notebooks/updates/Portfolio_Positions_Apr-21-2026.csv`
- Total portfolio value (Apr 21, 2026): $262,787.21
- Margin balance (pending activity): ~$42,570
- Margin utilization pre-deployment: ~16.2% (well within 19–20% stated range)
- Cash available for deployment: $3,200.00 (Avanade W2 paycheck)
- This deployment: $3,200.00
- Remaining cash buffer after deployment: $0.00

## Strategy Rationale

**Allocation Framework — 30/30/20/20 Layer 2 Pattern:**

- **JPMorgan Covered Call Tier (60%): JEPI + JEPQ** — Core Layer 2 income anchors. JEPI targets S&P 500 equity premium with ELN-based covered call overlay (~7–9% yield). JEPQ applies the same structure to Nasdaq-100 (~10–12% yield). Both pay monthly dividends and hold up with lower drawdown than pure equity in volatile markets. Equal 30% weight reflects the established cadence.

- **NEOS High-Income Tier (40%): QQQI + SPYI** — Higher-yield complement using systematic options writing with tax-efficient return of capital distributions. QQQI (Nasdaq-100) and SPYI (S&P 500) target ~12–15%+ distribution rates. 20% each provides yield uplift without over-concentrating in the more aggressive options overlay.

**Existing Layer 2 positions as of Apr 21, 2026:**
- JEPI: $9,346 | JEPQ: $13,705 | QQQI: $17,802 | SPYI: $12,116
- Total Layer 2 pre-deployment: ~$52,969
- Total Layer 2 post-deployment: ~$56,169

## Execution Details

- Price snapshot captured: `yfinance` (1d close) on 2026-04-22
- Fractional shares assumed on JEPI, JEPQ, QQQI, SPYI (Fidelity supports fractional for ETFs)
- DRIP: Recommend keeping DRIP off — manual redeployment preserves strategic weighting control
- Income source: Avanade W2 paycheck — $3,200.00 (gross check, full deployment)
- All four tickers are existing positions; this deployment adds to established Layer 2 stakes
- Execute as four separate market or limit orders; use limit orders near last close during liquid hours (9:45–11:30 AM ET or 1:30–3:30 PM ET)

## Risk Notes

- Margin utilization sits at ~16.2% pre-deployment, well below the 19–20% range cited. This all-cash deployment does not increase margin; it adds to equity and modestly reduces utilization percentage.
- QQQI and SPYI use NEOS's options overlay which distributes ROC — keep these in taxable account only if comfortable with Schedule K-style reporting; consider tax-advantaged account if available.
- JEPI and JEPQ use ELNs (equity-linked notes) to generate income — not pure covered calls — which introduces slight counterparty and tracking considerations.
- All four positions are already held. This is a size-up, not a new position, which reduces entry-point concentration risk.
- Current market context (Apr 2026): Elevated volatility and tariff-driven uncertainty. Options-income ETFs like JEPI/JEPQ tend to outperform in choppy/range-bound markets; QQQI/SPYI are more sensitive to Nasdaq direction. The 30/30/20/20 weighting leans slightly defensively.

## ITC Advisory

- ITC applicability: not-run
- ITC risk score: N/A
- (No ITC signal data was available for this deployment; omitted per template guidance)

## Sources & Assumptions

- Price snapshot: `yfinance` 1-day close on 2026-04-22 — JEPI $57.61, JEPQ $58.80, QQQI $53.35, SPYI $52.01
- Portfolio context: `notebooks/updates/Portfolio_Positions_Apr-21-2026.csv` downloaded Apr-21-2026 4:38 PM ET
- Deployment amount: $3,200.00 confirmed as Avanade W2 paycheck proceeds
- Share quantities assume fractional execution; round to whole shares if broker requires
- `src/utils/market_data.py` was unavailable due to circular import (structlog → logging shadow); yfinance used as fallback

## Progress Tracking

- Layer 2 income engine: $52,969 pre-deployment → ~$56,169 post-deployment
- At blended ~9–12% estimated distribution yield, Layer 2 income engine targets ~$421–$562/month from these four positions post-deployment
- Next planned deployment: next paycheck cycle or opportunistic dip purchase
- Target: build Layer 2 to $75–100K for full income stack coverage

---

**Educational Notice:** For educational purposes only; not investment advice. Consult a licensed financial professional before making any investment decisions. All investments involve risk, including the possible loss of principal. Past performance does not guarantee future results. Options-based ETFs carry additional complexity and tax considerations.
