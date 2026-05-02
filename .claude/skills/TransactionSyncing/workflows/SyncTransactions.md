# SyncTransactions Workflow

Import Fidelity transaction history CSV into Google Sheets with smart routing and categorization.

## Step 1: Read Transaction History CSV

**Location**: `notebooks/transactions/History_for_Account_{account_id}.csv`

**Read the CSV and parse**:
```python
# Expected columns (Row 3 has headers - skip rows 1-2)
Run Date, Action, Symbol, Description, Type, Price ($), Quantity,
Commission ($), Fees ($), Accrued Interest ($), Amount ($),
Cash Balance ($), Settlement Date
```

**Key Fields to Extract**:
- **Run Date**: Transaction date (MM/DD/YYYY format)
- **Action**: Transaction type (DIVIDEND RECEIVED, DEBIT CARD PURCHASE, etc.)
- **Symbol**: Ticker symbol (if applicable)
- **Description**: Full description text
- **Type**: Cash or Margin
- **Amount ($)**: Dollar amount (positive = credit, negative = debit)
- **Cash Balance ($)**: Running balance after transaction

## Step 2: Check/Create Transactions Tab

**Read existing sheets**:
```javascript
mcp__gdrive__sheets(operation: "listSheets", params: {
    spreadsheetId: "{spreadsheet_id}"
})
```

**If "Transactions" tab doesn't exist, create it**:
```javascript
mcp__gdrive__sheets(operation: "createSheet", params: {
    spreadsheetId: "{spreadsheet_id}",
    title: "Transactions"
})

// Add headers
mcp__gdrive__sheets(operation: "updateCells", params: {
    spreadsheetId: "{spreadsheet_id}",
    range: "Transactions!A1:I1",
    values: [["Date", "Action", "Symbol", "Description", "Type", "Amount", "Category", "Balance", "Settlement"]]
})
```

## Step 3: Read Existing Transactions (for deduplication)

```javascript
mcp__gdrive__sheets(operation: "readSheet", params: {
    spreadsheetId: "{spreadsheet_id}",
    range: "Transactions!A:F"
})
```

**Build deduplication set**:
```python
existing_keys = set()
for row in sheet_data:
    key = f"{row['Date']}|{row['Action']}|{row['Amount']}"
    existing_keys.add(key)
```

## Step 4: Process CSV Transactions

For each transaction in the CSV:

### 4a. Generate Deduplication Key
```python
key = f"{run_date}|{action}|{amount}"
if key in existing_keys:
    continue  # Skip duplicate
```

### 4b. Assign Category

**Category Assignment Rules** (see CategoryRules.md for full list):

```python
def assign_category(action, description):
    action_lower = action.lower()
    desc_lower = description.lower()

    # Investment categories (Transactions tab only)
    if "dividend" in action_lower:
        return "DIVIDEND"
    if "reinvestment" in action_lower:
        return "REINVESTMENT"
    if "margin interest" in action_lower:
        return "MARGIN_INTEREST"
    if "cap gain" in action_lower:
        return "CAP_GAIN"
    if "direct deposit" in action_lower:
        return "INCOME"
    if "journaled" in action_lower:
        return "INTERNAL_TRANSFER"

    # Expense categories (route to Expense Tracker)
    if "debit card" in action_lower:
        return categorize_expense(desc_lower)

    return "OTHER"

def categorize_expense(description):
    # Groceries
    if any(x in description for x in ['h-e-b', 'heb', 'kroger', 'costco',
            'wal-mart', 'walmart', 'wholefds', 'whole foods', 'makola']):
        return "Groceries"

    # Dining Out
    if any(x in description for x in ['benihana', 'golden corral', 'papa john',
            'chuck e cheese', 'wingstop', 'cinemark']):
        return "Dining Out"

    # Auto & Transport
    if any(x in description for x in ['tesla', 'supercha', 'parking',
            'fastpark']):
        return "Auto & Transport"

    # Personal Care
    if any(x in description for x in ['salon', 'spa', 'barber', 'sephora',
            'beauty supply', 'cash app']):
        return "Personal Care"

    # Health & Wellness
    if any(x in description for x in ['cvs', 'pharmacy', 'walgreens']):
        return "Health & Wellness"

    # Shopping
    if any(x in description for x in ['marshalls', 'target', 'amazon',
            'skims']):
        return "Shopping"

    # Family Care
    if any(x in description for x in ['aqua tots', 'brightwheel']):
        return "Family Care"

    # Bills & Utilities
    if any(x in description for x in ['autopay', 'acctverify']):
        return "Bills & Utilities"

    # Cash Withdrawal
    if 'atm' in description:
        return "Cash Withdrawal"

    # Tuition
    if 'regent univer' in description:
        return "Tuition"

    # Business Expense
    if any(x in description for x in ['gumroad', 'ups']):
        return "Business Expense"

    # Loan Payment
    if 'wells fargo' in description and 'draft' in description:
        return "Loan Payment"

    return "Uncategorized"  # Flag for manual review
```

### 4c. Build Transaction Row

```python
transaction_row = [
    run_date,           # Date
    clean_action(action), # Action (simplified)
    symbol or "",       # Symbol
    description[:50],   # Description (truncated)
    tx_type,            # Type (Cash/Margin)
    amount,             # Amount
    category,           # Category
    balance,            # Balance
    settlement_date     # Settlement
]
```

## Step 5: Batch Update Transactions Tab

⚠️ **KNOWN BUG**: `mcp__gdrive__execute(operation: "appendRows")` is broken — it defaults to `Sheet1` regardless of the `range` argument. Use `updateCells` with an explicit row range instead:

```javascript
// 1) Find last filled row (binary-search if needed; start with rowCount and work down)
mcp__gdrive__execute(service: "sheets", operation: "readSheet",
    args: { spreadsheetId, range: "Transactions!A<last>:A<last+100>" })
// Keep halving/shifting until you find the transition from values -> empty.

// 2) Write at <last_filled + 1>
const startRow = last_filled + 1;
const endRow = startRow + new_rows.length - 1;
mcp__gdrive__execute(service: "sheets", operation: "updateCells",
    args: { spreadsheetId, range: `Transactions!A${startRow}:I${endRow}`, values: new_rows })
```

## Step 6: Route Expenses to Expense Tracker

**Filter expense-bearing actions (NOT just DEBIT CARD PURCHASE)**:
```python
EXPENSE_ACTIONS = ('DEBIT CARD PURCHASE', 'CASH ADVANCE')  # add others as discovered
expense_rows = []
for tx in new_transactions:
    if any(a in tx['action'].upper() for a in EXPENSE_ACTIONS):
        month = get_month_name(tx['date'])  # "January", etc.
        expense_rows.append([tx['date'], tx['description'], tx['category'],
                             format_amount(tx['amount']), month])
```

**Dedup gotcha — scan the FULL existing tab**:

The Transactions tab may have two format eras (e.g., `M/D/YY` old block at the top, `MM/DD/YYYY` new block near the bottom) because the sort order can break over time. A prior sync may have appended to the bottom. Reading only the top rows misses these existing entries, which causes the next sync to re-insert the same dates as duplicates.

- Before appending, read the FULL column A and build a set of all dates present (normalize to one format).
- Skip any CSV rows whose date is already covered, OR use `Date|Action|Amount` dedup key if you need finer resolution.
- When in doubt, filter aggressively (only sync dates > the newest existing date seen ANYWHERE in the tab).

**Append new expenses via `updateCells`** (same fix as Step 5 — `appendRows` is broken):

```javascript
mcp__gdrive__execute(service: "sheets", operation: "updateCells",
    args: { spreadsheetId, range: `Expense Tracker!A${startRow}:E${endRow}`, values: new_expense_rows })
```

## Step 7: Generate Summary Report

```
TRANSACTION SYNC COMPLETE - [Date]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TRANSACTIONS TAB:
  New entries added: XX
  Duplicates skipped: XX

EXPENSE TRACKER:
  Expenses routed: XX
  Auto-categorized: XX
  Needs review (Uncategorized): XX

TRANSACTION BREAKDOWN:
  Dividends:        $XXX.XX (XX entries)
  Reinvestments:    $XXX.XX (XX entries)
  Margin Interest:  -$XX.XX (XX entries)
  Debit Card:       -$X,XXX.XX (XX entries)
  Direct Deposits:  +$X,XXX.XX (XX entries)
  Other:            $XXX.XX (XX entries)

UNCATEGORIZED EXPENSES (needs review):
  - [Date] [Description] [$Amount]
  - [Date] [Description] [$Amount]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Helper Functions

### clean_action(action)
Extract simplified action from verbose Fidelity text:
```python
def clean_action(action):
    if "DIVIDEND RECEIVED" in action:
        return "DIVIDEND"
    if "REINVESTMENT" in action:
        return "REINVESTMENT"
    if "DEBIT CARD PURCHASE" in action:
        return "DEBIT CARD"
    if "MARGIN INTEREST" in action:
        return "MARGIN INTEREST"
    if "DIRECT DEPOSIT" in action:
        return "DIRECT DEPOSIT"
    if "LONG-TERM CAP GAIN" in action:
        return "CAP GAIN"
    if "JOURNALED" in action:
        return "JOURNAL"
    return action[:30]  # Truncate
```

### get_month_name(date_str)
```python
from datetime import datetime
def get_month_name(date_str):
    date = datetime.strptime(date_str, "%m/%d/%Y")
    return date.strftime("%B")  # "January", "February", etc.
```

### format_amount(amount)
```python
def format_amount(amount):
    return f"${abs(float(amount)):,.2f}"
```

## Error Handling

### Missing CSV
```
ERROR: Transaction history CSV not found at notebooks/transactions/
Please download from Fidelity and place in the transactions folder.
```

### Empty CSV
```
WARNING: CSV contains no transactions to import.
```

### Google Sheets API Error
```
ERROR: Failed to update Google Sheets. Check:
1. Spreadsheet ID is correct
2. MCP gdrive server is connected
3. You have edit permissions
```

## Validation Checklist

After sync, verify:
- [ ] Transactions tab contains new entries
- [ ] No duplicate transactions added
- [ ] Expense Tracker has new debit card purchases
- [ ] Categories are correctly assigned
- [ ] Uncategorized items are flagged in summary
- [ ] Amounts match CSV values

---

**Workflow Type**: Data sync
**Estimated Duration**: 30-60 seconds
**Dependencies**: mcp__gdrive__sheets, CSV file access
