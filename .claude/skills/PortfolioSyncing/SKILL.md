---
name: PortfolioSyncing
description: Import and sync broker CSV portfolio data to Google Sheets DataHub. Supports Fidelity (automated) with multi-broker planned. USE WHEN user mentions import broker data OR sync portfolio OR update positions OR CSV import OR portfolio-sync OR ingest positions OR bring in positions OR downloaded from Fidelity OR working with Portfolio_Positions CSVs. Handles file ingestion from Downloads, position updates, SPAXX/margin validation, safety checks, and formula protection.
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

**When executing a workflow, output the corresponding notification:**

| Workflow | Trigger | File |
|----------|---------|------|
| **IngestPositions** | "ingest positions", "import positions", "bring in positions", user mentions downloading from Fidelity | `workflows/IngestPositions.md` |
| **SyncPortfolio** | "sync portfolio", "portfolio-sync", "import fidelity" | `workflows/SyncPortfolio.md` |

**Typical flow**: IngestPositions (move from Downloads) -> SyncPortfolio (push to Google Sheets)

**Notifications:**
```
Running the **IngestPositions** workflow from the **PortfolioSyncing** skill...
```
```
Running the **SyncPortfolio** workflow from the **PortfolioSyncing** skill...
```

## Examples

**Example 1: Full flow from Downloads**
```
User: "ingest positions" or "bring in positions"
-> Scans ~/Downloads/ for Portfolio_Positions_*.csv and Balances_*.csv
-> Classifies regular vs dividend view by reading headers
-> Moves regular view as-is (already date-tagged)
-> Renames dividend view to Dividend_Positions_MMM-DD-YYYY.csv
-> Moves Balances file (overwrites existing)
-> Reports files moved and suggests "portfolio-sync" next
```

**Example 2: Sync after ingest**
```
User: "portfolio-sync"
-> Reads Portfolio_Positions_*.csv and Balances_*.csv from notebooks/updates/
-> Compares with Google Sheets DataHub
-> Updates quantities, cost basis, SPAXX, margin debt
-> Reports changes and validates formulas
```

**Example 3: Update positions after trades**
```
User: "I just bought more JEPI, sync my portfolio"
-> Invokes SyncPortfolio workflow
-> Detects quantity change in JEPI
-> If >10% change, asks for confirmation
-> Updates DataHub with new position data
```

**Example 4: Handling duplicate downloads**
```
User downloads both regular and dividend views from Fidelity
-> ~/Downloads/ contains: Portfolio_Positions_Mar-06-2026.csv
                          Portfolio_Positions_Mar-06-2026 (1).csv
-> Reads header of each to classify
-> Regular view (has "Average Cost Basis") -> notebooks/updates/Portfolio_Positions_Mar-06-2026.csv
-> Dividend view (has "Ex-date") -> notebooks/updates/Dividend_Positions_Mar-06-2026.csv
```

## CSV Format Reference

### Fidelity Positions CSV (Regular View)

**Header row** (17 columns):
```csv
Account Number,Account Name,Investment Type,Symbol,Description,Quantity,Last Price,Last Price Change,Current Value,Today's Gain/Loss Dollar,Today's Gain/Loss Percent,Total Gain/Loss Dollar,Total Gain/Loss Percent,Percent Of Account,Cost Basis Total,Average Cost Basis,Type
```

**Key fields for sync**: Symbol (col 4), Quantity (col 6), Average Cost Basis (col 16), Type (col 17 — "Margin" or "Cash")

### Fidelity Positions CSV (Dividend View)

**Header row** (19 columns):
```csv
Account Number,Account Name,Investment Type,Symbol,Description,Quantity,Last Price,Last Price Change,Current Value,Percent Of Account,Ex-date,Amount per share,Pay date,Dist. yield,Distribution yield as of,SEC yield,SEC yield as of,Est. annual income,Type
```

**Quick classifier**: If header contains `Ex-date` -> dividend view. If header contains `Average Cost Basis` -> regular view.

### Fidelity Balances CSV

Key-value format (not columnar). Extract:
- **"Settled cash"** → SPAXX row (Column L: Current Value)
- **"Account equity percentage"** → If 100%, margin debt = $0
- **"Net debit"** → Actual margin balance (negative value = margin debt)
- **"Margin interest accrued this month"** → If > $1, there IS margin debt

**Cash Position Logic**:
- Do NOT use `SPAXX` value from Positions CSV (shows only settled money market)
- Use **"Settled cash"** from Balances CSV for the SPAXX row
- If "Settled cash" = 0, then SPAXX = $0 (all funds are invested or in margin)
- "Cash market value" is NOT cash — it's the value of positions in your Cash account (vs Margin account)

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

### Update Pattern: Individual Cell Updates ONLY

**Golden Rule**: **NEVER** include columns C-F in your update range. **NEVER** pass empty strings to any cell.

Empty strings (`""`) in columns C-F **DELETE** the GOOGLEFINANCE and calculation formulas. Always update columns A, B, G individually:

```javascript
// ✅ RIGHT - Update ONLY writable columns, one at a time
mcp__gdrive__sheets(operation: "updateCells", params: {
    spreadsheetId: SPREADSHEET_ID,
    range: "DataHub!B13:B13",  // ✅ Single column, specific row
    values: [["72.942"]]
})
```

```javascript
// ❌ WRONG - Multi-column range with empty strings kills formulas
mcp__gdrive__sheets(operation: "updateCells", params: {
    range: "DataHub!A13:G13",
    values: [["JEPI", "72.942", "", "", "", "", "$56.48"]]  // ❌ Empty strings delete formulas
})
```

| Action | Correct | Wrong |
|--------|---------|-------|
| **Update quantity** | `range: "DataHub!B13:B13"` | `range: "DataHub!A13:G13"` with empty strings |
| **Update cost basis** | `range: "DataHub!G13:G13"` | Including columns C-F in range |
| **Add new ticker** | 3 separate calls (A, B, G) | Single call with empty strings in C-F |

### Layer Classification for New Tickers

When adding new tickers, classify into the correct portfolio layer in Column S.

**Do NOT hardcode layer assignments.** Instead, read the current layer definitions from:
- **Primary**: `fin-guru/data/spreadsheet-architecture.md` → "Pattern-Based Layer Classification" section
- **Fallback**: Read existing Column S values from DataHub to learn current classification patterns

If a new ticker doesn't clearly match any layer pattern, set to `"UNKNOWN - Manual Review Required"` and alert the user for classification.

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

**When STOPPED**: Show clear diff table, ask user to confirm, proceed only after explicit approval.

**When FLAGGED**: Show the discrepancy, proceed with update but highlight in summary.

## Google Sheets Integration

**Spreadsheet ID**: Read from `fin-guru/data/user-profile.yaml` → `google_sheets.portfolio_tracker.spreadsheet_id`

## Agent Permissions

**Builder** (Write-enabled): Can update columns A, B, G; can add new rows; can apply layer classification; CANNOT modify formulas.

**All Other Agents** (Read-only): Market Researcher, Quant Analyst, Strategy Advisor — can read all data, cannot write, must defer to Builder for updates.

## Reference Files

- **Full Architecture**: `fin-guru/data/spreadsheet-architecture.md`
- **Quick Reference**: `fin-guru/data/spreadsheet-quick-ref.md`
- **User Profile**: `fin-guru/data/user-profile.yaml`
- **Formula Protection**: See the `formula-protection` skill for sacred formula rules

## Pre-Flight Checklist

Before syncing (SyncPortfolio):
- [ ] **Positions CSV** (`Portfolio_Positions_*.csv`) is latest by date in `notebooks/updates/`
- [ ] **Balances CSV** (`Balances_for_Account_*.csv`) is available and current in `notebooks/updates/`
- [ ] Both CSVs are from Fidelity (not M1 Finance or other broker)
- [ ] Google Sheets DataHub tab exists
- [ ] No pending manual edits in sheet (user should save first)
- [ ] Current portfolio value is known (for validation)

**Files not in `notebooks/updates/` yet?** Run **IngestPositions** first to move them from `~/Downloads/`.

**Both CSVs Required**: Positions CSV alone is insufficient. Balances CSV provides:
- "Settled cash" → SPAXX value
- "Net debit" → Pending Activity and Margin Debt values

---

**Skill Type**: Domain (workflow guidance)
**Enforcement**: BLOCK (data integrity critical)
**Priority**: Critical
