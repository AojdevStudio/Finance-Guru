# SyncPortfolio Workflow

**Purpose:** Refresh the local DB from SnapTrade (sync-first), read positions + balances from `family_office.db`, compare with the Google Sheets DataHub, and sync position data while preserving sacred formulas.

> **Data source:** Positions and balances come from the local `family_office.db` (`positions` + `balances` tables), which Step 1 refreshes from SnapTrade first. See the shared **[Sync-First + DB-Read](../../_shared/SyncFirstDbRead.md)** pattern. The legacy Fidelity-CSV read path was retired after account-by-account verification (issue 71) and remains a manual reconciliation fallback only.

---

## Step 1: Refresh the DB (sync-first, mandatory)

Pre-flight:
- [ ] SnapTrade account is **enabled and routed** in `config/snaptrade-accounts.yaml` (`role` ≠ `unassigned`, `enabled: true`). Disabled/unassigned accounts are refused, not synced.
- [ ] SnapTrade credentials are present in `.env` (`SNAPTRADE_CLIENT_ID`, `SNAPTRADE_CONSUMER_KEY`, `SNAPTRADE_USER_ID`, `SNAPTRADE_USER_SECRET`).

Refresh, so the DB carries this run's snapshot before any read:

```bash
uv run python -m src.integrations.snaptrade.sync_db          # writes positions + balances
uv run python -m src.integrations.snaptrade.sync_db --show   # confirm this run's synced_at
```

**Completion criterion:** the `positions` and `balances` tables show this run's `synced_at`.

---

## Step 2: Read Positions + Balances from the DB

Read the refreshed snapshot (via `--show`, or query `family_office.db` directly):

```bash
sqlite3 family_office.db \
  "SELECT symbol, instrument, quantity, avg_cost FROM positions ORDER BY instrument, symbol;"
sqlite3 family_office.db \
  "SELECT account_equity, settled_cash, buying_power, margin_debt, gross_market_value FROM balances;"
```

### Positions (`positions` table)
- **`symbol`** → DataHub Column A (equities are plain tickers; options use Fidelity form `-QQQ260918P595`)
- **`quantity`** → DataHub Column B
- **`avg_cost`** → DataHub Column G (per-share; options already normalized ÷100)
- **`instrument`** → `"equity"` or `"option"`

**Sync only `instrument == "equity"` to the position rows (DataHub rows 2-40).** One net position per symbol (no Margin/Cash split to combine). Options are **not** written as position rows (the DataHub does not track option rows); they are reflected only in the margin-debt math (Step 7).

### Balances (`balances` table)
- **`settled_cash`** → SPAXX row (DataHub Column L)
- **`margin_debt`** → Margin Debt and Pending Activity rows (derived: gross market value minus net equity; SnapTrade does not expose the loan directly)
- **`account_equity`** → net account value (for the Step 8 total check)
- **`gross_market_value`** → total long market value (sanity check)

**Margin Debt Logic**: `margin_debt > 0` means a margin loan exists. `margin_debt <= 0` means no debt: set the SPAXX/Pending Activity/Margin Debt rows to `$0` accordingly.

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
