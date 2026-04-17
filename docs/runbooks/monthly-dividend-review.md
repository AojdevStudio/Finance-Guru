---
title: Monthly Dividend Review
cadence: monthly
owner: Ossie
last-reviewed: 2026-04-17
---

# Monthly Dividend Review

## Purpose

Confirm that Layer 2 (dividend income) is on track for the month — sync the month's dividend events from Fidelity, validate the _Dividends_ sheet totals, and flag any cuts or missed distributions before they drift further.

## When to run

- _First week of every month_, after all prior-month dividends have settled
- _Any time_ a tracked position suspends or cuts its distribution
- _Before_ the quarterly review

## Prerequisites

- Fidelity dividend export downloaded to `notebooks/updates/dividend.csv`
- Prior-month Layer 2 target from user profile or strategy notes
- `dividend-tracking` skill available
- Google Sheets DataHub → _Dividends_ sheet accessible

## Steps

1. _Export dividends from Fidelity_ — Activity → Dividends & Interest → filter to the prior month → Export CSV
2. _Save to_ `notebooks/updates/dividend.csv` (exact filename — the skill looks for this)
3. _Invoke the dividend-tracking skill_:
   ```
   /dividend-tracking
   ```
4. _Review the input area_ (rows 2-46) — the skill writes calculated dividends as `shares × amount per share`; confirm no row is blank for a known payer
5. _Click Add Dividend_ — the skill will prompt you or click the button itself (via the gdrive MCP); confirms processing
6. _Review the monthly total_ against your Layer 2 target:
   - _On track_ (≥100% of target): note it and move on
   - _Below target_ (<100%): identify the shortfall driver — missed position, cut dividend, timing lag
   - _Above target_ (>120%): consider reinvestment plan or margin paydown
7. _Document any anomalies_ in your monthly dividend notes (append one line with date and observation)

## Verification

- Google Sheets DataHub → _Dividends_ tab shows rows for the prior month with non-zero totals
- Layer 2 income cell (monthly total) reconciles within $1 of Fidelity's CSV sum
- No position from the portfolio is missing unless it's a non-payer (confirm via positions file)
- Running total for the year has advanced by the month's amount

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Skill says "dividend.csv not found" | Filename must be exactly `dividend.csv` (lowercase, singular) in `notebooks/updates/` |
| A known payer is missing | Check the ex-dividend / payment dates — Fidelity reports on pay date, not declaration |
| Monthly total off by a large amount | Re-pull the Fidelity CSV with date filter set correctly — easy to pick wrong month |
| Input area has stale rows from prior month | The skill clears rows 2-46 before writing; if not, run it again or clear manually |
| Add Dividend button doesn't fire | Google Sheets session may have timed out — refresh the sheet and retry the skill |

## Related skills

- `dividend-tracking` — primary skill
- `PortfolioSyncing` — ensure current positions match before reconciling totals
- `fin-guru-strategize` — if Layer 2 is chronically below target, escalate to strategy review
- `FinanceReport` — generate a monthly Layer 2 PDF summary if you want a formal record
