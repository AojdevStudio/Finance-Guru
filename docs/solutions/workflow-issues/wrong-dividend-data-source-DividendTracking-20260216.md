---
module: Dividend Tracking
date: 2026-02-16
problem_type: workflow_issue
component: tooling
symptoms:
  - "Incorrect dividend amounts written to Dividends sheet input area"
  - "Dividend values calculated from projected per-share amounts instead of actual payments"
  - "User flagged data as inaccurate after reviewing written records"
root_cause: missing_workflow_step
resolution_type: workflow_improvement
severity: high
tags: [dividend-tracking, data-source, fidelity-csv, transaction-history, dividends]
---

# Troubleshooting: Wrong CSV Used for Dividend Data Import

## Problem

During dividend sync, the agent used `dividend.csv` (projected per-share dividend amounts) and calculated `Quantity x Amount per share` to derive dividend income. This produced incorrect values. The correct source is the transaction history CSV (`History_for_Account_*.csv`) which contains actual "DIVIDEND RECEIVED" dollar amounts.

## Environment

- Module: Dividend Tracking (Finance Guru)
- System: Finance Guru v2.0.0 / BMAD-CORE v6.0.0
- Affected Component: Dividend Tracking skill, Dividends sheet input area
- Date: 2026-02-16

## Symptoms

- Dividend amounts written to Dividends!A2:D43 did not match actual received payments
- User immediately recognized the data was wrong after reviewing the input area
- Values were calculated projections, not actual historical payments

## What Didn't Work

**Attempted Solution 1:** Read `notebooks/updates/dividend.csv` and calculate `Quantity x Amount per share`
- **Why it failed:** `dividend.csv` contains _projected/expected_ per-share dividend rates from Fidelity's dividend schedule. These are forward-looking estimates, not actual payments received. Multiplying by current quantity gives a projected amount, not the real payment which may differ due to timing, ex-dates, share count at time of payment, and rate changes.

## Solution

Use the transaction history CSV (`History_for_Account_*.csv`) instead, filtering for rows where the `Action` column contains `"DIVIDEND RECEIVED"`.

**Data source comparison:**

```
# WRONG SOURCE: dividend.csv
# Contains: Symbol, Quantity, Amount per share (projected)
# Problem: These are PROJECTED rates, not actual payments
JEPI, 120.91, $0.4939  # This is a per-share rate estimate

# CORRECT SOURCE: History_for_Account_Z05724592.csv
# Contains: Run Date, Action, Symbol, Amount (actual dollars received)
# Solution: Filter for "DIVIDEND RECEIVED" action type
01/05/2026, DIVIDEND RECEIVED, JEPI, $46.86  # This is the ACTUAL payment
```

**Aggregation rules for transaction history:**
1. Filter rows where `Action == "DIVIDEND RECEIVED"`
2. Use the `Amount` column directly (already in dollars, no calculation needed)
3. Aggregate same-ticker entries on the same pay date (Margin + Cash accounts)
4. Skip SPAXX and SHV dividends (money market, not portfolio income)
5. Map old ticker symbols (e.g., `88634T493` -> `MSTY` pre-reverse-split)
6. Only include records with pay dates that have already passed

**Batch processing:** Transaction history can produce 100+ records. Write in batches of 42 (max input area capacity), clicking "Add Dividend" between batches.

## Why This Works

1. **Root cause:** The dividend tracking skill's documentation referenced `dividend.csv` as the data source, but this file contains Fidelity's _projected_ dividend schedule with per-share rates. It does NOT contain actual payment history.
2. **The transaction history CSV** (`History_for_Account_*.csv`) contains the definitive record of every actual dividend payment received, with exact dollar amounts already calculated by Fidelity.
3. **No calculation needed:** The `Amount` column in transaction history is the actual dollars deposited, eliminating errors from projected rates, timing differences, or share count discrepancies.

## Prevention

- **ALWAYS use transaction history CSV** (`History_for_Account_*.csv`) for dividend imports, never `dividend.csv`
- The `dividend.csv` file is useful for _projecting future income_ but NOT for recording _actual received_ dividends
- When the dividend-tracking skill says "Read Dividend CSV," it should be interpreted as "Read the transaction history CSV and filter for DIVIDEND RECEIVED entries"
- Update the dividend-tracking skill documentation to clarify the correct data source
- Add a guard: if the workflow detects it's reading `dividend.csv` for historical import, STOP and redirect to transaction history

## Related Issues

No related issues documented yet.
