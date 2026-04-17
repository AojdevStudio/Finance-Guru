---
title: Portfolio Sync
cadence: ad-hoc
owner: Ossie
last-reviewed: 2026-04-17
---

# Portfolio Sync

## Purpose

Ingest a fresh Fidelity `Portfolio_Positions_*.csv` file, push it to the Google Sheets DataHub, and validate that all downstream calculations (allocation, dividend coverage, margin coverage) updated correctly.

## When to run

- _Any time_ a new Fidelity CSV export lands — typically after a trade or at month-end
- _Before_ invoking quantitative analysis on current positions
- _Before_ generating FinanceReport PDFs (so reports reflect reality)

## Prerequisites

- Fidelity positions CSV downloaded to `~/Downloads/` or dropped directly into `notebooks/updates/`
- `fin-core` skill auto-loaded
- `gdrive` MCP server configured (required for DataHub writes)
- You have the correct Google Sheet ID in your user profile

## Steps

1. _Confirm filename pattern_ — Fidelity exports as `Portfolio_Positions_MMM-DD-YYYY.csv` (e.g., `Portfolio_Positions_Apr-17-2026.csv`). Do NOT rename.
2. _Move to the updates directory_:
   ```bash
   mv ~/Downloads/Portfolio_Positions_*.csv notebooks/updates/
   ```
3. _Invoke the PortfolioSyncing skill_:
   ```
   /PortfolioSyncing
   ```
4. _Review the ingestion report_ — the skill will echo:
   - The filename it picked (latest by date in filename)
   - Total positions detected
   - SPAXX (money market) and margin balance rows validated
   - Safety check: total market value within expected range
5. _Approve the push_ when prompted — the skill asks before writing to Google Sheets
6. _Spot-check the DataHub tab_:
   - _Positions_ tab — row count matches the CSV
   - _Allocation_ tab — percentages sum to 100% ± 0.01
   - _Margin Dashboard_ — coverage ratio refreshed

## Verification

- `ls notebooks/updates/Portfolio_Positions_*.csv` shows the new file
- Google Sheets DataHub → _Positions_ tab: last-updated timestamp is today
- No red formula error cells (the formula-protection skill will have blocked bad edits)
- Allocation percentages reconcile to total market value
- If positions changed materially, rerun _Margin Dashboard Update_ runbook

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Skill picks the wrong CSV | Check filename date — the hook uses filename date, not mtime |
| SPAXX row missing | Fidelity sometimes exports SPAXX as "SPAXX**" — the skill handles this; if not, verify the input area rows 2-46 |
| Formula error after sync | Invoke `formula-protection` skill; it will identify the modified cell and restore it |
| Sheet tab doesn't update | Confirm `gdrive` MCP is connected — `/gdrive:status` or restart Claude Code session |
| "Write would overwrite calculated cell" | Good — the formula-protection skill blocked a bad edit; review the attempted change |

## Related skills

- `PortfolioSyncing` — primary skill
- `formula-protection` — protects calculated cells from accidental overwrite
- `dividend-tracking` — sync dividends alongside positions if both files are fresh
- `TransactionSyncing` — transaction history is a separate ingestion path
- `retirement-syncing` — for Vanguard / Fidelity retirement accounts
