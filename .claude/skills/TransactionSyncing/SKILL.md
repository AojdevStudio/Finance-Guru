---
name: transaction-syncing
description: Refresh the local DB, then push investment activities and card/bank expenses to Google Sheets. Investment activities come from the DB transactions table (SnapTrade); debit-card and bank spending comes from the DB bank_transactions table (SimpleFIN), auto-categorized. Sync-first so nothing is stale. USE WHEN user mentions "sync transactions", "transaction history", "expense tracker", "categorize spending", OR "update expenses".
---

# TransactionSyncing

Push financial activity into Google Sheets from the local DB (refreshed sync-first): the master Transactions tab from investment activities (`transactions` table), plus the Expense Tracker from card/bank spending (`bank_transactions` table), auto-categorized for Budget Planner integration.

## Step 0: Refresh (sync-first, mandatory)

Both halves read from the local DB, refreshed FIRST so nothing is stale. Follow the shared **[Sync-First + DB-Read](../_shared/SyncFirstDbRead.md)** pattern. This skill needs two sources:

```bash
uv run python -m src.integrations.snaptrade.sync_transactions_db          # investment activities -> transactions
uv run python -m src.integrations.simplefin.sync_expenses_db --months 3   # card/bank spending -> bank_transactions
# or refresh everything at once:
uv run python -m src.integrations.refresh_all --months 3
```

Completion criterion: _the `transactions` and `bank_transactions` tables carry this run's `synced_at` before any Sheet write._

## Workflow Routing

**When executing this workflow, output this notification:**

```
Running the **SyncTransactions** workflow from the **TransactionSyncing** skill...
```

| Workflow | Trigger | File |
|----------|---------|------|
| **IngestTransactions** | "ingest transactions", "import history", "bring in transactions", user points to Downloads CSV | `workflows/IngestTransactions.md` |
| **SyncTransactions** | "sync transactions", "push to sheets", "transaction sync" | `workflows/SyncTransactions.md` |

**Typical flow**: IngestTransactions (local archive) -> SyncTransactions (Google Sheets)

## Examples

**Example 1: Sync after downloading Fidelity transaction history**
```
User: "sync transactions"
-> Reads History_for_Account_{account_id}.csv from notebooks/transactions/
-> Creates/updates Transactions tab with full Fidelity data
-> Routes DEBIT CARD PURCHASE entries to Expense Tracker
-> Auto-categorizes expenses (H-E-B -> Groceries, Tesla -> Auto & Transport)
-> Reports: "Added 45 transactions, 12 expenses categorized"
```

**Example 2: Import new transaction export**
```
User: "import the transaction history"
-> Invokes SyncTransactions workflow
-> Detects duplicates by date + action + amount
-> Skips existing entries, adds only new ones
-> Flags uncategorized expenses for manual review
```

**Example 3: Check recent transactions**
```
User: "import fidelity transactions and update expense tracker"
-> Full sync with expense routing
-> Generates summary of dividends received, purchases, margin interest
```

## Architecture Overview

### Data Flow

```
SnapTrade activities            SimpleFIN dump (bun run src/dump.ts)
        |                                |
        v                                v
  sync_transactions_db            sync_expenses_db (categorize.py)
        |                                |
        v                                v
+------------------+           +--------------------+
| transactions     |           | bank_transactions  |  <- categorized, upserted
| table (DB)       |           | table (DB)         |
+------------------+           +--------------------+
        |                                | direction == "debit"
        v                                v
+------------------+           +--------------------+
| Transactions Tab |           | Expense Tracker    |  <- Budget Planner integration
| (Google Sheets)  |           | (Google Sheets)    |
+------------------+           +--------------------+
```

### Transaction Types Handled

| Fidelity Action | Destination | Category |
|-----------------|-------------|----------|
| DIVIDEND RECEIVED | Transactions only | DIVIDEND |
| REINVESTMENT | Transactions only | REINVESTMENT |
| DEBIT CARD PURCHASE | Transactions + Expense Tracker | Auto-categorized |
| MARGIN INTEREST | Transactions only | MARGIN_INTEREST |
| DIRECT DEPOSIT | Transactions only | INCOME |
| LONG-TERM CAP GAIN | Transactions only | CAP_GAIN |
| JOURNALED | Transactions only | INTERNAL_TRANSFER |

### Smart Categorization

Categorization is executable and runs inside the expense adapter, so the
`category` column arrives pre-filled on every `bank_transactions` row. The rules
live in code at `src/integrations/simplefin/categorize.py`
(`categorize_expense(text, amount)`), which is the source of truth mirroring the
human-readable `CategoryRules.md`. Keep the two in sync when adding patterns.

**Sample patterns:**
- `H-E-B`, `KROGER`, `COSTCO`, `WAL-MART` -> Groceries
- `Tesla`, `SUPERCHA` -> Auto & Transport
- `BENIHANA`, `GOLDEN CORRAL`, `PAPA JOHN` -> Dining Out
- `CVS`, `PHARMACY` -> Health & Wellness
- amount < $1.00 or `verification` text -> Exempt; no match -> Uncategorized

## Input Sources: the local DB (primary)

### Half A: Investment activities (`transactions` table)

After Step 0's refresh, read investment activity from the DB:

```bash
sqlite3 family_office.db \
  "SELECT date, type, symbol, description, amount, quantity, currency FROM transactions ORDER BY date;"
```

Each row has a stable shape (`type`, `date`, `symbol`, `amount`, `quantity`,
`currency`, `description`). Map it onto the master Transactions tab (type -> Action,
date -> Date, amount -> Amount, etc.).

### Half B: Card / bank expenses (`bank_transactions` table)

Debit-card and bank spending has **no SnapTrade equivalent**, so it comes from
SimpleFIN via the expense adapter, already normalized and categorized:

```bash
sqlite3 family_office.db \
  "SELECT date, payee, description, amount, direction, category FROM bank_transactions ORDER BY date DESC;"
```

The adapter (`src/integrations/simplefin/sync_expenses_db.py`) pulls the SimpleFIN
dump, categorizes each row via the executable rules in
`src/integrations/simplefin/categorize.py` (the code source of truth mirroring
`CategoryRules.md`), and upserts into `bank_transactions` keyed on
`(account_id, txn_id)`. Route `direction == "debit"` rows to the Expense Tracker
using the `category` column.

**Dedupe:** Google Sheets stays the single source of truth for what has been
posted. For Half A detect duplicates by `date` + `type` + `amount`; for Half B by
`date` + `description` + `amount`. Add only new rows. The DB layer is already
idempotent (activities via `dedupe_key`, expenses via the upsert key), so
re-running is safe.

**Fallback:** the Fidelity History CSV path below remains a manual reconciliation
fallback only; it is no longer the primary path.

## Core Workflow

### 1. Read Fidelity Transaction History CSV

**Location**: `notebooks/transactions/History_for_Account_{account_id}.csv`

**CSV Columns**:
```
Run Date, Action, Symbol, Description, Type, Price ($), Quantity,
Commission ($), Fees ($), Accrued Interest ($), Amount ($),
Cash Balance ($), Settlement Date
```

### 2. Create/Update Transactions Tab

**Google Sheets Structure**:

| Column | Header | Source |
|--------|--------|--------|
| A | Date | Run Date |
| B | Action | Action (cleaned) |
| C | Symbol | Symbol |
| D | Description | Description |
| E | Type | Type (Cash/Margin) |
| F | Amount | Amount ($) |
| G | Category | Auto-assigned |
| H | Balance | Cash Balance ($) |
| I | Settlement | Settlement Date |

### 3. Deduplicate

**Match criteria**: Date + Action + Amount

```
For each CSV row:
  key = f"{run_date}|{action}|{amount}"
  if key exists in sheet:
    SKIP (already imported)
  else:
    ADD to Transactions tab
```

### 4. Route Expenses to Expense Tracker

**Filter**: Action contains "DEBIT CARD PURCHASE"

**Expense Tracker Format**:
| Date | Description | Category | Amount | Month |
|------|-------------|----------|--------|-------|

**Category Assignment**: See `CategoryRules.md`

### 5. Generate Summary

```
SYNC SUMMARY - [Date]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TRANSACTIONS TAB:
  New entries: 45
  Skipped (duplicates): 12

EXPENSE TRACKER:
  Expenses routed: 18
  Auto-categorized: 15
  Needs review: 3

BY TYPE:
  Dividends: $342.50
  Margin Interest: -$18.43
  Debit Card: -$1,245.67
  Direct Deposit: +$5,054.09
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Google Sheets Integration

**Spreadsheet ID**: Read from `fin-guru/data/user-profile.yaml` -> `google_sheets.portfolio_tracker.spreadsheet_id`

### Creating Transactions Tab (if needed)

```javascript
// Check if Transactions tab exists
mcp__gdrive__sheets(operation: "listSheets", params: {
    spreadsheetId: SPREADSHEET_ID
})

// Create if missing
mcp__gdrive__sheets(operation: "createSheet", params: {
    spreadsheetId: SPREADSHEET_ID,
    title: "Transactions"
})

// Add headers
mcp__gdrive__sheets(operation: "updateCells", params: {
    spreadsheetId: SPREADSHEET_ID,
    range: "Transactions!A1:I1",
    values: [["Date", "Action", "Symbol", "Description", "Type", "Amount", "Category", "Balance", "Settlement"]]
})
```

### Adding to Expense Tracker

```javascript
// Append expense row
mcp__gdrive__sheets(operation: "appendRows", params: {
    spreadsheetId: SPREADSHEET_ID,
    sheetName: "Expense Tracker",
    values: [[date, description, category, amount, month]]
})
```

## Critical Rules

### WRITABLE Destinations
- Transactions tab: All columns (new tab, we control format)
- Expense Tracker: Append new rows only (preserve existing)

### NEVER MODIFY
- Budget Planner formulas
- Existing Expense Tracker entries

### Deduplication Key
- Transactions tab: `Date|Action|Amount`
- Expense Tracker: `Date|Description|Amount`

## Reference Files

- **CategoryRules.md**: Pattern matching rules for expense categorization
- **fin-guru/data/user-profile.yaml**: Spreadsheet ID
- **scripts/google-sheets/portfolio-optimizer/**: Apps Script reference

## Pre-Flight Checklist

Before syncing transactions:
- [ ] Transaction History CSV exists in `notebooks/transactions/`
- [ ] CSV is from Fidelity (not other broker)
- [ ] Expense Tracker tab exists in Google Sheets
- [ ] Current date retrieved via `date` command

---

**Skill Type**: Domain (workflow guidance)
**Enforcement**: SUGGEST
**Priority**: Medium
**Line Count**: < 300 (following 500-line rule)
