# SyncPortfolio Workflow

**Purpose:** Pull live positions + balances from SnapTrade, compare with the Google Sheets DataHub, and sync position data while preserving sacred formulas.

> **Data source:** Positions and balances come from the **SnapTrade CLI** (live, read-only). The legacy Fidelity-CSV read path was retired after account-by-account verification (issue 71). Equity positions, options, settled cash, and margin debt were verified to match a known-good Fidelity export before cutover. CSV files are no longer read for position/balance sync.

---

## Step 1: Pre-Flight Checks

- [ ] SnapTrade account is **enabled and routed** in `config/snaptrade-accounts.yaml` (`role` ≠ `unassigned`, `enabled: true`). Disabled/unassigned accounts are refused by the CLI, not synced.
- [ ] SnapTrade credentials are present in `.env` (`SNAPTRADE_CLIENT_ID`, `SNAPTRADE_CONSUMER_KEY`, `SNAPTRADE_USER_ID`, `SNAPTRADE_USER_SECRET`).

---

## Step 2: Pull Live SnapTrade Data

### Positions

```bash
uv run python -m src.integrations.snaptrade.cli positions --output json
```

Per account, `accounts[].positions[]` carries:
- **`symbol`** → DataHub Column A (equities are plain tickers; options use Fidelity form `-QQQ260918P595`)
- **`quantity`** → DataHub Column B
- **`average_purchase_price`** → DataHub Column G (per-share; options already normalized ÷100)
- **`instrument`** → `"equity"` or `"option"`

**Sync only `instrument == "equity"` to the position rows (DataHub rows 2-40).** SnapTrade returns one net position per symbol — there is no Margin/Cash split to combine. Options are **not** written as position rows (the DataHub does not track option rows); they are reflected only in the margin-debt math (Step 7).

### Balances

```bash
uv run python -m src.integrations.snaptrade.cli balances --output json
```

Per account, `accounts[].balances` carries:
- **`settled_cash`** → SPAXX row (DataHub Column L)
- **`margin_debt`** → Margin Debt and Pending Activity rows (derived: gross market value − net equity; SnapTrade does not expose the loan directly)
- **`account_equity`** → net account value (for the Step 8 total check)
- **`gross_market_value`** → total long market value (sanity check)

**Margin Debt Logic**: `margin_debt > 0` means a margin loan exists. `margin_debt <= 0` means no debt — set the SPAXX/Pending Activity/Margin Debt rows to `$0` accordingly.

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

**Identify** (SnapTrade equity positions vs sheet):
- ✅ **NEW tickers**: In SnapTrade but not in sheet (additions)
- ✅ **EXISTING tickers**: In both (updates)
- ⚠️ **MISSING tickers**: In sheet but not in SnapTrade (possible sales)

---

## Step 5: Safety Checks (STOP if triggered)

**STOP conditions** (require user confirmation):
1. SnapTrade returns fewer tickers than the sheet (possible sales)
2. Any quantity change > 10%
3. Any cost basis change > 20%
4. 3+ formula errors detected
5. Margin balance jumped > $5,000 vs the sheet's current Margin Debt
6. **SPAXX discrepancy > $100** (SnapTrade `settled_cash` vs sheet SPAXX)

**When STOPPED**:
- Show clear diff table
- Ask user to confirm changes
- Proceed only after explicit approval

### Transaction History Cross-Check (Optional, legacy CSV)

Transaction-level verification still uses the Fidelity History CSV (transactions are out of scope for the SnapTrade positions/balances cutover). When large quantity changes (>10%) are detected and `notebooks/transactions/History_for_Account_{account_id}.csv` is available:

```
For each ticker with >10% change:
1. Read transaction history for that ticker
2. Sum recent BUY transactions since last sync
3. Verify: Current SnapTrade Qty ≈ Previous Sheet Qty + Net Transactions
4. If mismatch > 1 share, FLAG for manual review
```

Skip cross-check if: small changes (<10%), user explicitly confirms, or the transaction file is unavailable.

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

This step is NOT optional. SPAXX and Margin must be updated every sync, from the SnapTrade `balances` output.

**SPAXX (Row 37, Column L)** — from `settled_cash`:
```javascript
mcp__gdrive__sheets(operation: "updateCells", params: {
    spreadsheetId: SPREADSHEET_ID,
    range: "DataHub!L37:L37",
    values: [[" $ -   "]]  // settled_cash; " $ -   " when 0, else " $ X,XXX.XX "
})
```

**Pending Activity (Row 38, Column L)** — negative of `margin_debt`:
```javascript
mcp__gdrive__sheets(operation: "updateCells", params: {
    spreadsheetId: SPREADSHEET_ID,
    range: "DataHub!L38:L38",
    values: [[" $ (83,820.02)"]]  // -(margin_debt), format " $ (X,XXX.XX)"; " $ -   " if no debt
})
```

**Margin Debt (Row 39, Column L)** — `margin_debt` (positive):
```javascript
mcp__gdrive__sheets(operation: "updateCells", params: {
    spreadsheetId: SPREADSHEET_ID,
    range: "DataHub!L39:L39",
    values: [[" $ 83,820.02 "]]  // margin_debt, format " $ X,XXX.XX "; " $ -   " if no debt
})
```

> **Note on derived margin:** `margin_debt` is computed (gross market value − net equity) because SnapTrade does not expose the loan directly. It tracks Fidelity's "Net debit" within ~0.1%, the gap being intraday price timing. If the sync needs the exact broker figure, fall back to a Fidelity Balances export for that one number.

---

## Step 8: Post-Update Validation

**Verify**:
- [ ] Formulas still functional (no new #N/A errors)
- [ ] SPAXX reflects SnapTrade `settled_cash`
- [ ] Pending Activity reflects −`margin_debt`
- [ ] Margin Debt reflects `margin_debt`
- [ ] Total account value ≈ SnapTrade `account_equity`

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
✅ Account equity: ${VALUE} (SnapTrade)
```

---

## Done

Portfolio sync complete. DataHub now matches live SnapTrade data.
