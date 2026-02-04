# SyncPortfolio Workflow

**Purpose:** Import Fidelity CSV exports and sync to Google Sheets DataHub.

---

## Step 1: Pre-Flight Checks

Before importing CSV:
- [ ] **Positions CSV** (`Portfolio_Positions_*.csv`) is latest by date
- [ ] **Balances CSV** (`Balances_for_Account_*.csv`) is available and current
- [ ] Both CSVs are from Fidelity (not M1 Finance or other broker)
- [ ] Files are in `notebooks/updates/` directory

---

## Step 2: Read Latest Fidelity CSVs

**Positions File**: `notebooks/updates/Portfolio_Positions_MMM-DD-YYYY.csv`

**Key Fields to Extract**:
- **Symbol** → Column A: Ticker
- **Quantity** → Column B: Quantity
- **Average Cost Basis** → Column G: Avg Cost Basis

**Balances File**: `notebooks/updates/Balances_for_Account_{account_id}.csv`

**Key Fields to Extract**:
- **"Settled cash"** → SPAXX row (Column L)
- **"Net debit"** → Pending Activity and Margin Debt
- **"Account equity percentage"** → Margin status

---

## Step 3: Read Current Google Sheets DataHub

```javascript
mcp__gdrive__sheets(operation: "readSheet", params: {
    spreadsheetId: SPREADSHEET_ID,
    range: "DataHub!A1:S50"
})
```

Extract:
- Column A: Ticker
- Column B: Quantity
- Column G: Avg Cost Basis

---

## Step 4: Compare and Identify Changes

**Identify**:
- ✅ **NEW tickers**: In CSV but not in sheet (additions)
- ✅ **EXISTING tickers**: In both (updates)
- ⚠️ **MISSING tickers**: In sheet but not in CSV (possible sales)

---

## Step 5: Safety Checks (STOP if triggered)

**STOP conditions** (require user confirmation):
1. CSV has fewer tickers than sheet (possible sales)
2. Any quantity change > 10%
3. Any cost basis change > 20%
4. 3+ formula errors detected
5. Margin balance jumped > $5,000
6. **SPAXX discrepancy > $100**

**When STOPPED**:
- Show clear diff table
- Ask user to confirm changes
- Proceed only after explicit approval

---

## Step 6: Update Position Data

**For EXISTING Tickers** (update Columns B and G ONLY):
```javascript
// Update quantity (Column B only)
mcp__gdrive__sheets(operation: "updateCells", params: {
    spreadsheetId: SPREADSHEET_ID,
    range: "DataHub!B{ROW}:B{ROW}",
    values: [["{QUANTITY}"]]
})

// Update cost basis (Column G only)
mcp__gdrive__sheets(operation: "updateCells", params: {
    spreadsheetId: SPREADSHEET_ID,
    range: "DataHub!G{ROW}:G{ROW}",
    values: [["{COST_BASIS}"]]
})
```

**NEVER touch Columns C-F** - these contain formulas.

---

## Step 7: Update Cash & Margin Rows (MANDATORY)

**SPAXX (Row 37, Column L)**:
```javascript
// From "Settled cash" in Balances CSV
mcp__gdrive__sheets(operation: "updateCells", params: {
    spreadsheetId: SPREADSHEET_ID,
    range: "DataHub!L37:L37",
    values: [[" $ -   "]]  // or formatted value if > 0
})
```

**Pending Activity (Row 38, Column L)**:
```javascript
// From "Net debit" in Balances CSV (negative value)
mcp__gdrive__sheets(operation: "updateCells", params: {
    spreadsheetId: SPREADSHEET_ID,
    range: "DataHub!L38:L38",
    values: [[" $ (7,822.71)"]]
})
```

**Margin Debt (Row 39, Column L)**:
```javascript
// ABS of "Net debit"
mcp__gdrive__sheets(operation: "updateCells", params: {
    spreadsheetId: SPREADSHEET_ID,
    range: "DataHub!L39:L39",
    values: [[" $ 7,822.71 "]]
})
```

---

## Step 8: Post-Update Validation

**Verify**:
- [ ] Formulas still functional (no new #N/A errors)
- [ ] SPAXX reflects "Settled cash" from Balances CSV
- [ ] Pending Activity reflects "Net debit" from Balances CSV
- [ ] Margin Debt = ABS(Net debit)

---

## Step 9: Log Summary

Output update summary:
```
✅ Updated {N} positions (quantity + cost basis)
✅ Added {N} new tickers: {LIST}
✅ SPAXX updated: ${VALUE}
✅ Pending Activity: ${VALUE}
✅ Margin debt: ${VALUE}
✅ No formula errors detected
✅ Portfolio value: ${VALUE} (matches Fidelity)
```

---

## Done

Portfolio sync complete. DataHub now matches Fidelity CSV.
