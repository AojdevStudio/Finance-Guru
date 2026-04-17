---
title: Margin Dashboard Update
cadence: weekly
owner: Ossie
last-reviewed: 2026-04-17
---

# Margin Dashboard Update

## Purpose

Keep the Margin Dashboard in the Google Sheets DataHub current with fresh Fidelity balance data, so the coverage ratio and safety alerts reflect reality before the market opens each week.

## When to run

- _Every Monday_ before 9:00 AM ET
- _Any time_ after a large margin draw (≥5% of portfolio value)
- _Before_ a planned margin-heavy trade

## Prerequisites

- Latest Fidelity balance export saved to `notebooks/updates/Balances_for_Account_{account_id}.csv`
- `fin-core` skill auto-loaded (happens at session start via hook)
- You know your current margin target range (see `fin-guru/data/user-profile.yaml`)

## Steps

1. _Download the balance CSV_ from Fidelity:
   - Accounts → Balances → Export → CSV
   - Move the file into `notebooks/updates/` and confirm the filename matches the exact pattern `Balances_for_Account_{account_id}.csv`
2. _Invoke the margin-management skill_ in Claude Code:
   ```
   /margin-management
   ```
3. _Confirm the skill read the right file_ — it should echo the filename and account ID
4. _Review the coverage ratio_ in the skill output:
   - _Green_ (≥2.0x): no action needed
   - _Yellow_ (1.5–2.0x): plan dividend / CC reinvestment to restore buffer
   - _Red_ (<1.5x): halt new margin draws, check scaling threshold
5. _Act on alerts_:
   - If a _Large Draw Alert_ fires, read the triggering transaction and confirm intent
   - If a _Scaling Threshold_ alert fires, review the time-based scaling recommendation
6. _Update the Margin Dashboard notes_ — append one line to the weekly notes block with date, coverage ratio, and any action taken

## Verification

- Google Sheets DataHub → _Margin Dashboard_ tab shows today's date in the last-updated cell
- Coverage ratio cell is populated (not `#N/A` or empty)
- No formula errors in the calculated columns (the formula-protection skill will have flagged any)
- If you took an action, the notes block has one new row

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Skill says "balances file not found" | Re-check filename against exact pattern `Balances_for_Account_{account_id}.csv` — extension must be `.csv`, not `.CSV` |
| Coverage ratio shows `#N/A` | A GOOGLEFINANCE formula is lagging; wait 60s and retry, or invoke `formula-protection` to repair |
| Large Draw Alert for a draw you didn't make | Audit the transaction immediately; could be an unauthorized pull |
| Yellow band persists for 3+ weeks | Review scaling plan with strategy-advisor — portfolio may have drifted from target |

## Related skills

- `margin-management` — primary skill for this runbook
- `formula-protection` — guards the sacred GOOGLEFINANCE formulas
- `PortfolioSyncing` — refresh positions alongside balances if both are stale
- `fin-guru-checklist` — weekly quality checklist includes margin dashboard freshness
