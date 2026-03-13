# SyncPortfolio Workflow

**Purpose:** Read Fidelity CSV exports from `notebooks/updates/`, compare with Google Sheets DataHub, and sync position data while preserving sacred formulas.

---

## Step 1: Pre-Flight Checks

Before importing CSV:
- [ ] **Positions CSV** (`Portfolio_Positions_*.csv`) is latest by date in `notebooks/updates/`
- [ ] **Balances CSV** (`Balances_for_Account_*.csv`) is available and current in `notebooks/updates/`
- [ ] Both CSVs are from Fidelity (not M1 Finance or other broker)

**Files not in `notebooks/updates/`?** Run **IngestPositions** workflow first.

---

## Step 2: Read Latest Fidelity CSVs

### Positions File

`notebooks/updates/Portfolio_Positions_MMM-DD-YYYY.csv` — find the latest by date in filename.

**CSV has 17 columns.** Extract these fields:
- **Symbol** (col 4) → maps to DataHub Column A
- **Quantity** (col 6) → maps to DataHub Column B
- **Average Cost Basis** (col 16) → maps to DataHub Column G
- **Type** (col 17) → "Margin" or "Cash" (same ticker may appear in both — combine quantities)

**Combining Cash + Margin positions**: When a ticker appears in both Margin and Cash rows, sum the quantities and use the weighted average cost basis.

### Balances File

`notebooks/updates/Balances_for_Account_{account_id}.csv`

**Key fields to extract**:
- **"Settled cash"** → SPAXX row (DataHub Column L)
- **"Net debit"** → Pending Activity and Margin Debt
- **"Account equity percentage"** → Margin status

**Margin Debt Logic**:
```
IF "Account equity percentage" == 100% THEN
    Margin Debt = $0.00
ELSE
    Margin Debt = Total Account Value × (1 - Equity Percentage)
END
```

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

### Transaction History Cross-Check (Optional)

When large quantity changes (>10%) are detected, cross-reference with `notebooks/transactions/History_for_Account_{account_id}.csv`:

```
For each ticker with >10% change:
1. Read transaction history for that ticker
2. Sum recent BUY transactions since last sync
3. Verify: Current CSV Qty ≈ Previous Sheet Qty + Net Transactions
4. If mismatch > 1 share, FLAG for manual review
```

Skip cross-check if: small changes (<10%), user explicitly confirms, or transaction file unavailable.

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

**NEVER touch Columns C-F** — these contain formulas.

**For NEW Tickers**:
1. Add new row with 3 separate calls for Columns A, B, G
2. Read layer definitions from `fin-guru/data/spreadsheet-architecture.md` → "Pattern-Based Layer Classification"
3. Apply classification to Column S
4. If ticker doesn't match any pattern, set `"UNKNOWN - Manual Review Required"` and alert user
5. Column C (Last Price) will auto-populate from GOOGLEFINANCE formula

**Log Addition**:
```
Added {TICKER} - {SHARES} shares @ ${AVG_COST} - Layer: {LAYER}
```

---

## Step 7: Update Cash & Margin Rows (MANDATORY)

This step is NOT optional. SPAXX and Margin must be updated every sync.

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
    values: [[" $ (7,822.71)"]]  // format: " $ (X,XXX.XX)" for negative
})
```

**Margin Debt (Row 39, Column L)**:
```javascript
// ABS of "Net debit"
mcp__gdrive__sheets(operation: "updateCells", params: {
    spreadsheetId: SPREADSHEET_ID,
    range: "DataHub!L39:L39",
    values: [[" $ 7,822.71 "]]  // format: " $ X,XXX.XX " positive
})
```

---

## Step 8: Post-Update Validation

**Verify**:
- [ ] Formulas still functional (no new #N/A errors)
- [ ] SPAXX reflects "Settled cash" from Balances CSV
- [ ] Pending Activity reflects "Net debit" from Balances CSV
- [ ] Margin Debt = ABS(Net debit)
- [ ] Total account value approximately matches Fidelity total

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
