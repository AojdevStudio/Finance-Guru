---
title: Quarterly Review
cadence: quarterly
owner: Ossie
last-reviewed: 2026-04-17
---

# Quarterly Review

## Purpose

Full family-office review — run the finance-orchestrator, stress-test the portfolio with MonteCarlo, generate FinanceReport PDFs for top holdings, and pass every output through compliance review. The goal is a quarterly snapshot that captures _what the portfolio looks like_, _what could go wrong_, and _what should change next quarter_.

## When to run

- _Last week of March, June, September, December_ — after earnings season but before the next quarter starts
- _After a major life event_ (job change, large inflow / outflow)
- _Before_ rebalancing or making large allocation changes

## Prerequisites

- Portfolio Sync runbook completed within the last 3 days (fresh positions)
- Margin Dashboard Update runbook completed within the last 3 days (fresh coverage ratio)
- Monthly Dividend Review completed for the most recent full month
- User profile at `fin-guru/data/user-profile.yaml` reflects current goals
- 2-3 hours of uninterrupted focus

## Steps

1. _Kick off the orchestrator_:
   ```
   /fin-guru:agents:finance-orchestrator
   ```
   Ask: "Run a full quarterly review — current snapshot, risks, recommendations."
2. _Let the orchestrator delegate_ — it will invoke market-researcher, quant-analyst, strategy-advisor, and compliance-officer in sequence
3. _Run a MonteCarlo stress test_:
   ```
   /MonteCarlo
   ```
   - 10,000 iterations minimum
   - Stress each of the 4 portfolio layers (Growth, Income, Hedge, GOOGL)
   - Capture the 5th / 50th / 95th percentile outcomes for 1-year and 5-year horizons
4. _Generate FinanceReport PDFs_ for the top 5 holdings by position size:
   ```
   /FinanceReport
   ```
   - Include VGT-style header, embedded charts, Perplexity sentiment
   - Save under `fin-guru/analysis/{YYYY-Q{N}}/`
5. _Run a compliance review_ on the combined outputs:
   ```
   /fin-guru-compliance-review
   ```
   - Disclaimers present on every document
   - No "investment advice" language
   - Risk disclosures match ITC risk scores
6. _Update strategy notes_ — append one section to `fin-guru/data/strategy-notes.md` (or create it) with date, key findings, and planned changes
7. _File follow-up issues_ in GitHub for any action items (use `needs-triage` label)

## Verification

- Orchestrator session produced a written summary with _at least_ 3 findings and 1 recommendation
- MonteCarlo output file exists under `fin-guru/analysis/` for the quarter
- FinanceReport PDFs exist for each of the top 5 holdings
- Compliance review returned "no blocking issues" or you have fixed the ones it flagged
- Strategy notes document has a new dated section
- GitHub issues filed for any action items

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Orchestrator stops partway through | Resume with `*resume` — the session context is preserved |
| MonteCarlo runs out of memory | Drop iterations to 5,000 or run one layer at a time |
| FinanceReport generation fails on a ticker | Check yfinance availability; fall back to Finnhub if configured |
| Compliance review flags an "investment advice" phrase | Revise to educational framing (`consider`, `explore`, `depending on your profile`) |
| PDFs render without charts | Ensure `plotly` and `reportlab` are current — `uv sync --dev` |

## Related skills

- `fin-guru:agents:finance-orchestrator` — entry point for the full review
- `MonteCarlo` — portfolio stress testing
- `FinanceReport` — institutional-quality PDF reports
- `fin-guru-compliance-review` — regulatory gate
- `fin-guru-quant-analysis` — standalone quantitative deep-dive if needed
- `fin-guru-strategize` — translates findings into next-quarter plan
