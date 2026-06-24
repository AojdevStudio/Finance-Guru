---
name: dividend-tracking
description: Sync dividend data from Fidelity CSV to Dividends sheet. Reads dividend.csv from notebooks/updates/, calculates actual dividends received (shares × amount per share), writes to input area (rows 2-46), then clicks Add Dividend button to process. Triggers on sync dividends, update dividends, dividend tracker, layer 2 income, or monthly dividend analysis.
---

# Dividend Tracking

## Purpose

Import Fidelity dividend CSV data into the Dividends sheet input area, then trigger the Apps Script to process records into the historical log.

## Workflow Routing

**When executing this workflow, output this notification:**

```
Running the **SyncDividends** workflow from the **dividend-tracking** skill...
```

| Workflow | Trigger | Action |
|----------|---------|--------|
| **SyncDividends** | "sync dividends", "update dividends", "dividend tracker" | CSV → Input Area → Click Button |

## Dividends Sheet Architecture

The Dividends tab has **TWO SECTIONS**:

### Left Side: INPUT AREA (Columns A-D, Rows 2-43)

**This is where YOU write dividend records.**

| Column | Field | Source |
|--------|-------|--------|
| A | Ticket | CSV Symbol |
| B | Dividends Received | Calculated: Quantity × Amount per share |
| C | Date | CSV Pay date (MM/DD/YYYY format) |
| D | DRIP | TRUE/FALSE |

**RULES:**
- ✅ Write to rows 2-43 ONLY (row 1 is header)
- ✅ Maximum 42 records per batch
- ❌ NEVER write past row 43
- After writing, click "Add Dividend" button to process

### Right Side: HISTORICAL LOG (Columns G-U, Rows 4+)

**This is populated by the Apps Script - DO NOT WRITE HERE.**

| Column | Field |
|--------|-------|
| G | Fund Name |
| H | Ticker |
| I-T | Monthly amounts (JAN-DEC) |
| U | Total |

The Apps Script reads from the input area (A-D) and appends to the historical log (G onwards).

## Input Source: SnapTrade activities (preferred) — CSV is fallback

As of SnapTrade Phase 2 (#72), the preferred input is **live normalized activities**, not `dividend.csv`:

```bash
uv run python -m src.integrations.snaptrade.cli activities --output json
```

Filter the returned records to `type == "DIVIDEND"`. Each record carries `date`,
`symbol`, `amount`, `description`, and `account`. **Null-symbol dividends already
have a ticker resolved** — the CLI parses it from the `description` (e.g. `... ETF
(SCHD)`), mirroring the positions/options symbol fallback — so `symbol` is safe to
write straight to Column A.

**Dedupe is unchanged:** Google Sheets stays the single source of truth. The
historical log (cols A-F / SUMIFS in G-U) is the ledger; only write input rows
that are not already represented, and only for pay dates that have passed. No
local cache or state file is introduced.

**Fallback:** the `dividend.csv` path below still works and remains the fallback
until the human reconciliation gate (#72) confirms parity. CSV ingestion is not
removed in this phase (deletion is Phase 3 / #73).

## Core Workflow

### 1. Read Dividend CSV

**File Location**: `notebooks/updates/dividend.csv`

**Key CSV Columns:**
| CSV Column | Use |
|------------|-----|
| Symbol | → Column A (Ticket) |
| Quantity | Used to calculate dividend received |
| Amount per share | Used to calculate dividend received |
| Pay date | → Column C (Date) - format as MM/DD/YYYY |
| Type | Margin/Cash (for aggregation) |

### 2. Calculate Dividends Received

```
Dividends Received = Quantity × Amount per share
```

**Aggregation Rules:**
- Sum quantities for same ticker (Margin + Cash accounts)
- Use single row per ticker
- Skip rows with `--` in Amount per share (non-dividend payers)
- Only include pay dates that have PASSED (already received)

### 3. Check Input Area Status

**Read current input area:**
```javascript
mcp__gdrive__sheets(
    operation: "readSheet",
    params: {
        spreadsheetId: "{spreadsheet_id}",
        range: "Dividends!A2:D43"
    }
)
```

**Determine:**
- First empty row (where to start writing)
- Available slots (max 45 - current entries)
- If full, STOP and alert user to click button first

### 4. Write to Input Area

**Write starting at first empty row:**
```javascript
mcp__gdrive__sheets(
    operation: "updateCells",
    params: {
        spreadsheetId: "{spreadsheet_id}",
        range: "Dividends!A2:D13",  // Adjust range based on record count
        values: [
            ["JEPI", "$51.63", "01/05/2026", "TRUE"],
            ["JEPQ", "$78.62", "01/05/2026", "TRUE"],
            // ... more records
        ]
    }
)
```

### 5. Trigger `addDividendFast()` via apps-script-run web app

After writing records, invoke the dispatcher (replaces the old "click Add Dividend button" UI step):

```bash
curl -sL "${APPS_SCRIPT_RUN_URL}?fn=addDividendFast"
```

The function appends each input row to the historical raw data (cols A-F at the bottom of the sheet) and clears `A2:D44`. SUMIFS formulas in the historical log (cols G-U) auto-aggregate by ticker × month. Returns JSON `{"ok": true, ...}` on success. See the `apps-script-run` skill for the full dispatcher reference.

**Fallback (if web app is unreachable):** Replicate `addDividendFast` directly via the gdrive Sheets API:
1. Read input area `A2:D44`, skip blank rows
2. For each row, compute `year = new Date(date).getFullYear()` and `month = getMonth() + 1`
3. Append `[ticker, amount, date, drip, year, month]` to the next empty row in cols A-F (typically row `getLastRow() + 1`)
4. Clear `A2:D44`

### 6. Verify Processing

After clicking button:
- Input area (A2:D43) should be cleared
- Historical log should have new entries
- Monthly totals should update

## Data Flow Diagram

```
┌─────────────────────────────────┐
│  dividend.csv (Fidelity export) │
│  - Symbol, Quantity             │
│  - Amount per share, Pay date   │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│  Calculate Dividends Received   │
│  Qty × Amount = Total Dividend  │
│  Aggregate by ticker            │
│  Filter: only PAST pay dates    │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│  INPUT AREA (A2:D43)            │
│  Write calculated dividends     │
│  Max 42 records per batch       │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│  CLICK "Add Dividend" BUTTON    │
│  (Browser automation or manual) │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│  HISTORICAL LOG (G4+)           │
│  Apps Script processes input    │
│  Appends to monthly columns     │
└─────────────────────────────────┘
```

## Apps Script Integration

The Dividends sheet has **Apps Script automation** that:
- Reads records from input area (A2:D43)
- Parses ticker, amount, date, DRIP status
- Appends to historical log with proper date formatting
- Updates monthly income columns (I-T)
- Clears input area after processing

**Script Location**: `scripts/google-sheets/portfolio-optimizer/Dividend.js`

**Custom Menu**: "Portfolio Optimizer" → (dividend-related options)

## Critical Rules

### WRITABLE Area
- ✅ Columns A-D, Rows 2-43 (input area)
- ✅ Maximum 42 records per batch
- ✅ Must click "Add Dividend" button after writing

### DO NOT MODIFY
- ❌ Row 1 (header)
- ❌ Rows 44+ in columns A-D
- ❌ Columns G-U (historical log - Apps Script managed)
- ❌ Any formulas

### Date Format
- Use MM/DD/YYYY (e.g., "01/05/2026")
- Match existing entries in the sheet

### DRIP Status
- TRUE = dividend was reinvested (shares increased)
- FALSE = dividend paid as cash
- Default TRUE for accumulation phase

## Pre-Flight Checklist

Before syncing dividends:
- [ ] `dividend.csv` exists in `notebooks/updates/`
- [ ] CSV is recent (check "Date downloaded" at bottom)
- [ ] Input area (A2:D43) has available slots
- [ ] If input area has data, click button first to clear it
- [ ] Browser automation available for button click

## Example Scenario

**User**: "sync dividends"

**Agent workflow**:
1. ✅ Read CSV - found 40 rows
2. ✅ Filter - 12 tickers with dividend data for past pay dates
3. ✅ Aggregate - combined Margin/Cash positions
4. ✅ Calculate - total dividends: $786.86
5. ✅ Check input area - rows 2-43 empty, 42 slots available
6. ✅ Write records - added 12 rows to A2:D13
7. ✅ Open browser - navigate to Dividends sheet
8. ✅ Click button - trigger "Add Dividend" Apps Script
9. ✅ Verify - input area cleared, historical log updated
10. ✅ LOG: "Synced 12 dividend records totaling $786.86"

## Google Sheets Integration

**Spreadsheet ID**: `{spreadsheet_id}`
**Dividends Sheet ID**: `2068577140`
**Direct URL**: `https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit#gid=2068577140`

## Reference Files

- **Dividend CSV**: `notebooks/updates/dividend.csv`
- **Apps Script**: `scripts/google-sheets/portfolio-optimizer/Dividend.js`
- **Spreadsheet**: Finance Guru Portfolio Tracker (Dividends tab)

---

**Skill Type**: Domain (workflow guidance)
**Enforcement**: SUGGEST (high priority advisory)
**Priority**: High
