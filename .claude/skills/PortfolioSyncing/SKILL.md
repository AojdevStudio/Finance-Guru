---
name: PortfolioSyncing
description: Import and sync broker CSV portfolio data to Google Sheets DataHub. Supports multiple brokers (Fidelity, Schwab, Vanguard, etc.). USE WHEN user mentions import broker data OR sync portfolio OR update positions OR CSV import OR portfolio-sync OR working with Portfolio_Positions CSVs. Handles position updates, SPAXX/margin validation, safety checks, and formula protection.
---

# PortfolioSyncing

Safely import broker CSV position exports into the Google Sheets DataHub tab, ensuring data integrity, validating changes, and protecting sacred formulas.

## Multi-Broker Support

**Supported Brokers**:
- ✅ **Fidelity** - Fully automated parsing
- ⚠️ **Schwab, Vanguard, TD Ameritrade, E*TRADE, Robinhood** - Manual mapping required (coming soon)

**Broker Detection**: Finance Guru automatically detects your broker from `user-profile.yaml` (set during onboarding). CSV parsing is tailored to your broker's format.

**See**: `docs/broker-csv-export-guide.md` for detailed export instructions per broker.

## Workflow Routing

**When executing this workflow, output this notification:**

```
Running the **SyncPortfolio** workflow from the **PortfolioSyncing** skill...
```

| Workflow | Trigger | File |
|----------|---------|------|
| **SyncPortfolio** | "sync portfolio", "portfolio-sync", "import fidelity" | `workflows/SyncPortfolio.md` |

## Examples

**Example 1: Sync after downloading new Fidelity CSV**
```
User: "portfolio-sync"
-> Reads Portfolio_Positions_*.csv and Balances_*.csv from notebooks/updates/
-> Compares with Google Sheets DataHub
-> Updates quantities, cost basis, SPAXX, margin debt
-> Reports changes and validates formulas
```

**Example 2: Update positions after trades**
```
User: "I just bought more JEPI, sync my portfolio"
-> Invokes SyncPortfolio workflow
-> Detects quantity change in JEPI
-> If >10% change, asks for confirmation
-> Updates DataHub with new position data
```

**Example 3: Import new Fidelity export**
```
User: "import fidelity CSV"
-> Locates latest CSV files by date
-> Runs safety checks (position count, large changes)
-> Syncs all positions and cash/margin values
-> Logs update summary
```

## Core Workflow

### 1. Read Latest Fidelity CSVs

**Positions File**: `notebooks/updates/Portfolio_Positions_MMM-DD-YYYY.csv`

**Key Fields to Extract**:
- **Symbol** → Column A: Ticker
- **Quantity** → Column B: Quantity
- **Average Cost Basis** → Column G: Avg Cost Basis

**CSV Format**:
```csv
Symbol,Quantity,Last Price,Current Value,Total Gain/Loss Dollar,...,Average Cost Basis
TSLA,74,$445.47,$32964.78,+$15634.71,...,$234.19
PLTR,369.746,$188.90,$69845.01,+$60235.59,...,$25.99
```

**Balances File**: `notebooks/updates/Balances_for_Account_{account_id}.csv`

**Key Fields to Extract for Cash & Margin**:
- **"Settled cash"** → Use for SPAXX row (Column L: Current Value)
- **"Account equity percentage"** → If 100%, margin debt = $0
- **"Net debit"** → Actual margin balance (negative value = margin debt)
- **"Margin interest accrued this month"** → If > $1, there IS margin debt

**⚠️ IMPORTANT: Cash Position Logic**
- Do NOT use `SPAXX` value from Positions CSV (shows only settled money market)
- Use **"Settled cash"** from Balances CSV for the SPAXX row
- If "Settled cash" = 0, then SPAXX = $0 (all funds are invested or in margin)
- "Cash market value" is NOT cash - it's the value of positions in your Cash account (vs Margin account)

**Margin Debt Logic**:
```
IF "Account equity percentage" == 100% THEN
    Margin Debt = $0.00
ELSE
    Margin Debt = Total Account Value × (1 - Equity Percentage)
END
```

### 2. Compare with Current Sheet

**Read from Google Sheets DataHub**:
- Column A: Ticker
- Column B: Quantity
- Column G: Avg Cost Basis

**Identify**:
- ✅ **NEW tickers**: In CSV but not in sheet (additions)
- ✅ **EXISTING tickers**: In both (updates)
- ⚠️ **MISSING tickers**: In sheet but not in CSV (possible sales)

### 3. Safety Checks (STOP if triggered)

**Position Mismatches**:
- If CSV has fewer tickers than sheet, **STOP** and alert user
- User must confirm sales/transfers before proceeding

**Large Quantity Changes (>10%)**:
- If any ticker quantity changes more than 10%, **STOP** and show diff
- Example: TSLA goes from 74 → 85 shares (+14.9%) = ALERT
- User must confirm intentional trades

**Cost Basis Changes (>20%)**:
- If average cost basis changes more than 20%, **FLAG** for review
- Possible corporate action (split, merger, dividend reinvestment)
- User should verify this is correct

**Formula Validation**:
- Scan Columns C-S for #N/A, #DIV/0!, #REF! errors before updating
- If 3+ errors detected, **STOP** and suggest formula repair first

### 3.5 Transaction History Cross-Check (Optional Validation)

**Transactions File**: `notebooks/transactions/History_for_Account_{account_id}.csv`

When large quantity changes (>10%) are detected, cross-reference with the transaction history to validate:

**Key Fields to Check**:
- **Run Date** → Date of transaction
- **Action** → BUY, SELL, DIVIDEND, etc.
- **Symbol** → Ticker symbol
- **Quantity** → Shares bought/sold
- **Amount** → Dollar value of transaction

**Validation Logic**:
```
For each ticker with >10% change:
1. Read transaction history for that ticker
2. Sum recent BUY transactions since last sync
3. Verify: Current CSV Qty ≈ Previous Sheet Qty + Net Transactions
4. If mismatch > 1 share, FLAG for manual review
```

**Example Cross-Check**:
```
JEPI shows +18.9 shares (90.82 → 109.72)
Transaction History shows:
  - Dec 15: BUY JEPI 10 shares
  - Dec 18: BUY JEPI 8.9 shares (DRIP)
  Total: +18.9 shares ✅ VERIFIED
```

**When to Skip**:
- Small changes (<10%) - trust CSV
- User explicitly confirms changes
- Transaction file unavailable or outdated

### 4. Update Operations

#### For EXISTING Tickers:
```
Update Column B (Quantity) = CSV Quantity
Update Column G (Avg Cost Basis) = CSV Average Cost Basis
```

**DO NOT TOUCH**:
- Column C (Last Price) - Google Finance formula auto-updates
- Columns D-F ($ Change, % Change, Volume) - Formulas/Alpha Vantage
- Columns H-M (Gains/Losses) - Calculated formulas
- Columns N-S (Ranges, dividends, layer) - Formulas or manual classification

**🚨 CRITICAL: NEVER PASS EMPTY STRINGS TO FORMULA COLUMNS**
- **WRONG**: Updating entire row range with empty strings (`""`) will OVERWRITE formulas
- **RIGHT**: Update ONLY columns A, B, G using individual cell ranges
- Empty strings (`""`) will DELETE formulas in columns C-F - this BREAKS the sheet

#### For NEW Tickers:
```
1. Add new row
2. Set Column A (Ticker) = CSV Symbol
3. Set Column B (Quantity) = CSV Quantity
4. Set Column G (Avg Cost Basis) = CSV Average Cost Basis
5. Apply pattern-based layer classification to Column S:
   - If ticker in [JEPI, JEPQ, SPYI, QQQI, CLM, CRF, etc.] → "Layer 2 - Dividend"
   - If ticker in [SQQQ] → "Layer 3 - Hedge"
   - If ticker in [TSLA, PLTR, NVDA, COIN, MSTR, SOFI] → "Layer 1 - Growth"
   - If ticker in [VOO, VTI, FZROX, FNILX] → "Layer 1 - Index"
6. Column C (Last Price) will auto-populate from GOOGLEFINANCE formula
```

**Log Addition**:
```
Added {TICKER} - {SHARES} shares @ ${AVG_COST} - Layer: {LAYER}
Example: Added MSTY - 87.9 shares @ $11.94 - Layer: Layer 2 - Dividend
```

### 5. Update Cash & Margin Rows (MANDATORY)

**🚨 CRITICAL: This step is NOT optional. SPAXX and Margin must be updated every sync.**

**SPAXX (Cash Position) - Row 37, Column L**:
```
1. Read "Settled cash" from Balances CSV
2. If "Settled cash" = 0 → Update DataHub!L37 with " $ -   " (zero cash)
3. If "Settled cash" > 0 → Update DataHub!L37 with formatted value
4. ⚠️ SAFETY CHECK: If current sheet SPAXX differs from CSV by >$100, FLAG for user
```

**Pending Activity - Row 38, Column L**:
```
1. Read "Net debit" from Balances CSV (will be negative if margin used)
2. Update DataHub!L38 with this value (format: " $ (X,XXX.XX)" for negative)
```

**Margin Debt - Row 39, Column L**:
```
1. Read "Net debit" from Balances CSV
2. Convert to positive: Margin Debt = ABS(Net debit)
3. Update DataHub!L39 with positive value (format: " $ X,XXX.XX ")
4. If Net debit = 0 → Update with " $ -   "
```

**Example**:
```javascript
// Cash position from Balances CSV "Settled cash" = 0
mcp__gdrive__sheets(operation: "updateCells", params: {
    spreadsheetId: SPREADSHEET_ID,
    range: "DataHub!L37:L37",
    values: [[" $ -   "]]
})

// Pending Activity from "Net debit" = -7822.71
mcp__gdrive__sheets(operation: "updateCells", params: {
    spreadsheetId: SPREADSHEET_ID,
    range: "DataHub!L38:L38",
    values: [[" $ (7,822.71)"]]
})

// Margin debt = ABS(-7822.71) = 7822.71
mcp__gdrive__sheets(operation: "updateCells", params: {
    spreadsheetId: SPREADSHEET_ID,
    range: "DataHub!L39:L39",
    values: [[" $ 7,822.71 "]]
})
```

### 6. Post-Update Validation

**Verify**:
- [ ] Google Finance formulas auto-populated prices for new tickers
- [ ] Formulas still functional (no new #N/A errors)
- [ ] Row count matches expected additions
- [ ] Total account value approximately matches Fidelity total
- [ ] **SPAXX reflects "Settled cash" from Balances CSV** (MANDATORY)
- [ ] **Pending Activity reflects "Net debit" from Balances CSV** (MANDATORY)
- [ ] **Margin Debt = ABS(Net debit)** (MANDATORY)

**Log Update Summary**:
```
✅ Updated 25 positions (quantity + cost basis)
✅ Added 3 new tickers: MSTY, YMAX, AMZY
✅ SPAXX updated: $0 (Settled cash = 0)
✅ Pending Activity: -$7,822.71 (Net debit)
✅ Margin debt: $7,822.71 (ABS of Net debit)
✅ No formula errors detected
✅ Portfolio value: $228,809.41 (matches Fidelity)
```

## Critical Rules

### WRITABLE Columns (from CSV)
- ✅ Column A: Ticker
- ✅ Column B: Quantity
- ✅ Column G: Avg Cost Basis

### SACRED Columns (NEVER TOUCH)
- ❌ Column C: Last Price (GOOGLEFINANCE formulas)
- ❌ Columns D-F: $ Change, % Change, Volume (formulas)
- ❌ Columns H-M: Gains/Losses calculations (formulas)
- ❌ Columns N-S: Ranges, dividends, layer (formulas/manual)

### Pattern-Based Layer Classification

Use these patterns to auto-classify new tickers in Column S:

**Layer 2 - Dividend** (Income funds):
- JEPI, JEPQ, SPYI, QQQI, QQQY
- CLM, CRF, ETY, ETV, BDJ, UTG, BST
- MSTY, YMAX, AMZY
- Any ticker with "yield" or "income" in description

**Layer 3 - Hedge** (Downside protection):
- SQQQ (ProShares UltraPro Short QQQ)

**Layer 1 - Growth** (Core holdings):
- TSLA, PLTR, NVDA, AAPL, GOOGL
- COIN, MSTR (Bitcoin proxies)
- SOFI

**Layer 1 - Index** (Passive core):
- VOO, VTI, VUG, QQQ
- FZROX, FNILX, FZILX, VXUS

## Safety Gates

**STOP conditions** (require user confirmation):
1. CSV has fewer tickers than sheet (possible sales)
2. Any quantity change > 10%
3. Any cost basis change > 20%
4. 3+ formula errors detected
5. Margin balance jumped > $5,000 (unintentional draw)
6. **SPAXX discrepancy > $100** (cash mismatch between sheet and CSV)

**FLAG conditions** (alert user but proceed):
- SPAXX differs from "Settled cash" by $1-$100 (minor discrepancy)
- Pending Activity differs from "Net debit" by >$100

**When STOPPED**:
- Show clear diff table
- Ask user to confirm changes
- Proceed only after explicit approval

**When FLAGGED**:
- Show the discrepancy
- Proceed with update but highlight in summary

## Example Scenario

**User downloads**: `Portfolio_Positions_Nov-11-2025.csv`

**Agent workflow**:
1. ✅ Read CSV - found 35 positions
2. ✅ Compare with sheet - 32 existing positions
3. ⚠️ NEW TICKERS DETECTED:
   - MSTY: 87.9 shares @ $11.94
   - YMAX: 110.982 shares @ $12.32
   - AMZY: 65.748 shares @ $14.44
4. ✅ SAFETY CHECKS PASSED - No large changes
5. ✅ UPDATE OPERATIONS:
   - Updated 32 existing positions (B, G columns)
   - Added 3 new tickers with Layer 2 classification
6. ✅ VALIDATION - All formulas working, no errors
7. ✅ LOG: "Updated 32 positions, added 3 new dividend funds"

## Google Sheets Integration

**Spreadsheet ID**: Read from `fin-guru/data/user-profile.yaml` → `google_sheets.portfolio_tracker.spreadsheet_id`

### ❌ BAD: Multi-Column Range Updates with Empty Strings

**THIS WILL BREAK FORMULAS:**
```javascript
// ❌ WRONG - Passing empty strings overwrites formulas in columns C-F
mcp__gdrive__sheets(
    operation: "updateCells",
    params: {
        spreadsheetId: SPREADSHEET_ID,
        range: "DataHub!A13:G27",  // ❌ Multi-column range
        values: [
            ["JEPI", "72.942", "", "", "", "", "$56.48"],  // ❌ Empty strings kill formulas
            ["JEPQ", "92.043", "", "", "", "", "$58.08"],
            ["CLM", "763.367", "", "", "", "", "$8.32"]
        ]
    }
)
```
**Why this breaks**: Empty strings (`""`) in columns C-F **DELETE** the GOOGLEFINANCE and calculation formulas.

---

### ✅ GOOD: Individual Cell Updates (Columns A, B, G Only)

**THIS PRESERVES FORMULAS:**
```javascript
// ✅ RIGHT - Update ONLY writable columns, one at a time
// Update JEPI quantity (Column B only)
mcp__gdrive__sheets(
    operation: "updateCells",
    params: {
        spreadsheetId: SPREADSHEET_ID,
        range: "DataHub!B13:B13",  // ✅ Single column, specific row
        values: [["72.942"]]
    }
)

// Update JEPI cost basis (Column G only)
mcp__gdrive__sheets(
    operation: "updateCells",
    params: {
        spreadsheetId: SPREADSHEET_ID,
        range: "DataHub!G13:G13",  // ✅ Single column, specific row
        values: [["$56.48"]]
    }
)

// Add new ticker (Columns A, B, G - formulas in C-F will auto-populate)
mcp__gdrive__sheets(
    operation: "updateCells",
    params: {
        spreadsheetId: SPREADSHEET_ID,
        range: "DataHub!A28:A28",  // ✅ Ticker only
        values: [["ECAT"]]
    }
)
mcp__gdrive__sheets(
    operation: "updateCells",
    params: {
        spreadsheetId: SPREADSHEET_ID,
        range: "DataHub!B28:B28",  // ✅ Quantity only
        values: [["72.884"]]
    }
)
mcp__gdrive__sheets(
    operation: "updateCells",
    params: {
        spreadsheetId: SPREADSHEET_ID,
        range: "DataHub!G28:G28",  // ✅ Cost basis only
        values: [["$15.92"]]
    }
)
```
**Why this works**: Only touching columns A, B, G leaves formulas in C-F intact and functional.

---

### Update Pattern Summary

| Action | ✅ GOOD | ❌ BAD |
|--------|---------|--------|
| **Update quantity** | `range: "DataHub!B13:B13"` | `range: "DataHub!A13:G13"` with `["", "72.942", "", "", "", "", ""]` |
| **Update cost basis** | `range: "DataHub!G13:G13"` | Including columns C-F in range |
| **Add new ticker** | 3 separate calls (A, B, G) | Single call with empty strings in C-F |
| **Multiple tickers** | Loop through rows, update B and G individually | Batch update entire range A:G |

**Golden Rule**: **NEVER** include columns C-F in your update range. **NEVER** pass empty strings to any cell.

## Agent Permissions

**Builder** (Write-enabled):
- Can update columns A, B, G
- Can add new rows
- Can apply layer classification
- CANNOT modify formulas

**All Other Agents** (Read-only):
- Market Researcher, Quant Analyst, Strategy Advisor
- Can read all data
- Cannot write to spreadsheet
- Must defer to Builder for updates

## Reference Files

For complete architecture details, see:
- **Full Architecture**: `fin-guru/data/spreadsheet-architecture.md`
- **Quick Reference**: `fin-guru/data/spreadsheet-quick-ref.md`
- **User Profile**: `fin-guru/data/user-profile.yaml`

## Pre-Flight Checklist

Before importing CSV:
- [ ] **Positions CSV** (`Portfolio_Positions_*.csv`) is latest by date
- [ ] **Balances CSV** (`Balances_for_Account_*.csv`) is available and current
- [ ] Both CSVs are from Fidelity (not M1 Finance or other broker)
- [ ] Files are in `notebooks/updates/` directory
- [ ] Google Sheets DataHub tab exists
- [ ] No pending manual edits in sheet (user should save first)
- [ ] Current portfolio value is known (for validation)

**⚠️ BOTH CSVs Required**: Positions CSV alone is insufficient. Balances CSV provides:
- "Settled cash" → SPAXX value
- "Net debit" → Pending Activity and Margin Debt values

---

**Skill Type**: Domain (workflow guidance)
**Enforcement**: BLOCK (data integrity critical)
**Priority**: Critical
**Line Count**: < 300 (following 500-line rule) ✅
