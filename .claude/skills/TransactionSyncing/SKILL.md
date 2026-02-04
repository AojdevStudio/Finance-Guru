---
name: TransactionSyncing
description: Import Fidelity transaction history CSV into Google Sheets with smart categorization. USE WHEN user mentions "sync transactions", "import transactions", "transaction history", OR wants to import Fidelity History CSV. Routes debit card purchases to Expense Tracker with auto-categorization.
---

# TransactionSyncing

Import Fidelity transaction history CSV into Google Sheets using a hybrid architecture: master Transactions tab for full audit trail + auto-routing of debit card purchases to Expense Tracker for Budget Planner integration.

## Workflow Routing

**When executing this workflow, output this notification:**

```
Running the **SyncTransactions** workflow from the **TransactionSyncing** skill...
```

| Workflow | Trigger | File |
|----------|---------|------|
| **SyncTransactions** | "sync transactions", "import transactions", "transaction sync" | `workflows/SyncTransactions.md` |

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
Fidelity CSV (notebooks/transactions/)
         |
         v
+-------------------+
| Transactions Tab  |  <- Master source (ALL transactions)
| (Full Fidelity)   |
+-------------------+
         |
         | Filter: DEBIT CARD PURCHASE
         v
+-------------------+
| Expense Tracker   |  <- Budget Planner integration
| (Categorized)     |
+-------------------+
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

See `CategoryRules.md` for the full pattern matching rules.

**Sample patterns:**
- `H-E-B`, `KROGER`, `COSTCO`, `WAL-MART` -> Groceries
- `Tesla`, `SUPERCHA` -> Auto & Transport
- `BENIHANA`, `GOLDEN CORRAL`, `PAPA JOHN` -> Dining Out
- `CVS`, `PHARMACY` -> Health & Wellness

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
