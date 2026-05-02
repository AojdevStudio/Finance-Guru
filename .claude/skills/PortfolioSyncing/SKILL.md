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

This skill has three invocation modes. Pick the one that matches the user's trigger phrase and run it without detours.

| Mode | Trigger phrases | What runs | Behavior |
|------|-----------------|-----------|----------|
| **E2E (default for "portfolio-sync")** | `portfolio-sync`, `sync portfolio`, `import fidelity`, `run the full skill`, `run the full skill e2e`, `full portfolio sync`, `sync my portfolio`, user says they just downloaded from Fidelity and wants the sheet updated | IngestPositions -> SyncPortfolio, chained | Run both in sequence with a single one-line handoff between them. Do NOT ask "Proceed?" between the two workflows. Pause only if a Safety Gate fires. |
| **Ingest-only** | `ingest positions`, `import positions`, `bring in positions`, `move fidelity files`, user explicitly wants to stage files without touching the sheet | `workflows/IngestPositions.md` | Stop after ingest. Report files moved and let the user decide next steps. |
| **Sync-only** | `push to sheets`, `sync to datahub`, user confirms files are already in `notebooks/updates/` | `workflows/SyncPortfolio.md` | Skip ingest. Read existing CSVs in `notebooks/updates/` and push to Google Sheets. |

**Default-to-E2E rule**: When the trigger is ambiguous (e.g., "portfolio-sync"), assume the user wants the whole flow. The noun "portfolio-sync" in this household means "take what I just downloaded and make the sheet reflect it." The split between Ingest and Sync is an implementation detail, not a user-facing choice.

**Chaining rule (E2E mode)**: Between IngestPositions and SyncPortfolio, log exactly one handoff line and continue:

```
Ingest complete ({N} files moved). Chaining into SyncPortfolio ->
```

Then run SyncPortfolio immediately. Do not re-confirm, re-list files, or ask the user to approve the handoff. The only valid reasons to pause mid-chain are the Safety Gate conditions below — real data anomalies, not routine workflow boundaries.

**Notifications (emit once when the mode is chosen):**

```
Running the **Full E2E** flow from the **PortfolioSyncing** skill (IngestPositions -> SyncPortfolio)...
```
```
Running the **IngestPositions** workflow from the **PortfolioSyncing** skill (ingest-only mode)...
```
```
Running the **SyncPortfolio** workflow from the **PortfolioSyncing** skill (sync-only mode)...
```

## Examples

**Example 1: E2E flow (default) — "portfolio-sync" or "run the full skill e2e"**
```
User: "portfolio-sync"  (or "sync portfolio", "run the full skill e2e", etc.)
-> Emits: "Running the Full E2E flow from the PortfolioSyncing skill..."
-> Runs IngestPositions:
   -> Scans ~/Downloads/ for Portfolio_Positions_*.csv and Balances_*.csv
   -> Classifies regular vs dividend view by headers
   -> Moves files into notebooks/updates/ (regular as-is, dividend renamed, Balances overwrites)
-> Emits ONE handoff line: "Ingest complete (3 files moved). Chaining into SyncPortfolio ->"
-> Runs SyncPortfolio immediately (no "Proceed?" prompt):
   -> Reads CSVs from notebooks/updates/, compares with DataHub
   -> Updates quantities, cost basis, SPAXX, margin debt
-> Prints final summary. Pauses only if a Safety Gate fired mid-flow.
```

**Example 2: Ingest-only — "ingest positions"**
```
User: "ingest positions" or "bring in positions"
-> Emits: "Running the IngestPositions workflow ... (ingest-only mode)..."
-> Moves files from ~/Downloads/ to notebooks/updates/
-> Prints the full POSITION INGESTION COMPLETE report
-> Stops. User decides whether to run "portfolio-sync" next.
```

**Example 3: Sync-only — files already staged**
```
User: "push to sheets"  (files are already in notebooks/updates/)
-> Emits: "Running the SyncPortfolio workflow ... (sync-only mode)..."
-> Skips ingest
-> Reads existing CSVs in notebooks/updates/ and pushes to Google Sheets
```

**Example 4: Update positions after trades (safety gate trips)**
```
User: "I just bought more JEPI, sync my portfolio"
-> Runs E2E flow
-> During SyncPortfolio, detects JEPI quantity change > 10%
-> STOP condition fires: pauses, shows diff table, asks for confirmation
-> Resumes only after user approves
-> This is the ONLY kind of pause the skill should produce
```

**Example 5: Handling duplicate downloads**
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

Safety Gates exist for one reason: to catch data that looks wrong before it hits the sheet. They are **not** a generic "are you sure?" prompt. The list below is exhaustive — if none of these fire, do not pause.

**STOP conditions** (require user confirmation — these are the ONLY legitimate reasons to pause mid-flow):
1. CSV has fewer tickers than sheet (possible sales or missing data)
2. Any quantity change > 10%
3. Any cost basis change > 20%
4. 3+ formula errors detected
5. Margin balance jumped > $5,000 (unintentional draw)
6. **SPAXX discrepancy > $100** (cash mismatch between sheet and CSV)

**FLAG conditions** (alert user but proceed — do NOT pause):
- SPAXX differs from "Settled cash" by $1-$100 (minor discrepancy)
- Pending Activity differs from "Net debit" by >$100

**When STOPPED**: Show clear diff table, ask user to confirm, proceed only after explicit approval.

**When FLAGGED**: Show the discrepancy, proceed with update but highlight in summary.

### When NOT to pause

Agents tend to over-confirm data operations. Resist that instinct. Specifically, do **not** pause for confirmation:

- Between IngestPositions and SyncPortfolio in the E2E flow — that's routine, not suspicious.
- Before reading files that are already in `notebooks/updates/`.
- Before issuing writes to the sheet that fall within the FLAG or no-gate range.
- To restate the plan the user already triggered by invoking the skill.

The user invoked this skill because they want the sheet updated from the latest Fidelity export. Asking "Proceed?" between routine steps defeats the purpose and is the single most common UX complaint with this skill. Pause only when the data itself is flagged by a STOP condition above.

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
