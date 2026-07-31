---
title: Finance Guru Runbooks
description: Operational procedures the family office owner runs on a cadence
last-reviewed: 2026-04-17
---

# Runbooks

Runbooks are _step-by-step procedures_ for recurring operational work: the things the owner does every week, month, or quarter to keep the family office running. They exist so a procedure that worked once doesn't get forgotten, and so Claude Code can execute them from context without guessing.

## When to use a runbook

- You are about to do something you have done before and will do again
- The procedure has side effects (writes to the database, edits CSVs, sends emails)
- Getting a step wrong would cost time to recover

If it's a one-off investigation, skip the runbook and just take notes in `.claude/MEMORY/`.

## Available runbooks

| Runbook | Cadence | Summary |
|---------|---------|---------|
| [Quarterly Review](quarterly-review.md) | Quarterly | Full orchestrator pass — MonteCarlo, FinanceReport PDFs, compliance review |

The weekly margin, ad-hoc portfolio sync, and monthly dividend runbooks were removed on 2026-07-31 with the Google Sheets DataHub. Their live equivalents are the `margin-management`, `portfolio-syncing`, and `dividend-tracking` skills, which read `family_office.db`.

## Cadence guide

| Cadence | When |
|---------|------|
| Daily | — (no daily runbooks yet; add one if spending analysis becomes routine) |
| Weekly | Margin Dashboard Update — run Monday morning before the market opens |
| Monthly | Dividend Review — first week of the month once all dividends have settled |
| Quarterly | Full review — end of Q1 / Q2 / Q3 / Q4 after earnings season |

## How to add a new runbook

1. Copy [margin-dashboard-update.md](margin-dashboard-update.md) as a template
2. Keep the frontmatter (title, cadence, owner, last-reviewed) and the seven sections: Purpose, When to run, Prerequisites, Steps, Verification, Troubleshooting, Related skills
3. Stay under 200 lines — link out to `docs/reference/*` for deep background
4. Add the new row to the table above
5. Update `last-reviewed` whenever you run the procedure and find it still accurate
