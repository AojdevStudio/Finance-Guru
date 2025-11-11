# Google Sheets Architecture & Agent Workflow Rules
<!-- Finance Guru™ Portfolio Tracker | Established: 2025-11-11 -->

## 📊 Spreadsheet Overview

**Spreadsheet ID**: `1HtHRP3CbnOePb8RQ0RwzFYOQxk0uWC6L8ZMJeQYfWk4`
**URL**: https://docs.google.com/spreadsheets/d/1HtHRP3CbnOePb8RQ0RwzFYOQxk0uWC6L8ZMJeQYfWk4/edit
**Purpose**: Portfolio tracking, dividend income monitoring, margin strategy dashboard

---

## 🏗️ Tab Structure & Purpose

### 1. Portfolio Positions (1039 rows × 19 columns)
**Purpose**: Master holdings tracker with real-time prices, gains/losses, and layer classification

**Columns**:
- **A**: Ticker Symbol (agent-writable from CSV)
- **B**: Quantity (agent-writable from CSV)
- **C**: Last Price (Google Finance formula - auto-updates)
- **D-E**: $ Change, % Change (formulas based on Column C)
- **F**: Volume (Alpha Vantage - partially working)
- **G**: Avg Cost Basis (agent-writable from CSV)
- **H-M**: Gains/Losses (Day G/L $, Day G/L %, Total G/L $, Total G/L %) - FORMULA-MAINTAINED
- **N-P**: Day Range, 52W Range, Earnings Date (Alpha Vantage - partially working)
- **Q-S**: Div Amount, Div Ex-Date, Portfolio Layer (formulas + manual)

**Agent Rules**:
- ✅ WRITE: Columns A (Ticker), B (Quantity), G (Avg Cost Basis) from Fidelity CSV
- ❌ READ-ONLY: All other columns (maintained by Google Finance formulas, Alpha Vantage, or calculated formulas)
- ⚠️ NEW POSITIONS: Auto-add using pattern-based layer classification

### 2. Dividend Tracker (1013 rows × 26 columns)
**Purpose**: Track expected and received dividend payments with DRIP status

**Columns**:
- Date Received
- Fund Symbol
- Fund Name
- Shares Owned (synced from Portfolio Positions)
- Dividend Per Share
- Total Dividend $
- Reinvested? (Yes/No)
- Notes

**Agent Rules**:
- ✅ AUTO-SYNC: Read ticker + shares from Portfolio Positions
- ✅ LOOKUP: Fetch current dividend amounts and ex-dates
- ✅ CALCULATE: Total Dividend $ = Shares × Dividend Per Share
- ⚠️ VALIDATE: Flag mismatches between Portfolio Positions shares and Dividend Tracker shares

### 3. Margin Dashboard (1009 rows × 26 columns)
**Purpose**: Track margin usage, interest costs, coverage ratios, and strategy scaling alerts

**Columns**:
- Date
- Margin Balance (from Fidelity CSV)
- Interest Rate
- Monthly Interest Cost (calculated)
- Notes

**Agent Rules**:
- ✅ ADD ENTRIES: Import margin balance from Fidelity CSV `Balances_for_Account_Z05724592.csv`
- ✅ CALCULATE METRICS:
  - Portfolio-to-margin ratio (Portfolio Value ÷ Margin Balance)
  - Monthly interest accrued (Balance × Rate ÷ 12)
  - Coverage ratio (Dividends ÷ Interest)
- ✅ SCALING ALERTS: Flag Month 6, Month 12, Month 18 triggers per margin-living strategy
- ⚠️ SAFETY GATE: Warn if margin balance jumps >$5k in single update

### 4. Cash Flow Monitor (1011 rows × 26 columns)
**Purpose**: Track deposits, withdrawals, and cash movements

**Agent Rules**: TBD (not yet defined in architecture session) //TODO: Remind user to define these rules.

### 5. Weekly Review (1028 rows × 26 columns) //TODO: Remind user to complete this task.
**Purpose**: Auto-generated weekly performance summaries (future: Google App Script + LLM)

**Agent Rules**:
- ⏳ FUTURE ENHANCEMENT: Auto-summaries via App Script calling LLM with specific prompt
- 📝 CURRENT: Manual entry only

### 6. Bitcoin Enhanced Growth - Friend (50 rows × 12 columns)
**Purpose**: Special tracking tab (context TBD)

**Agent Rules**: READ-ONLY (personal/external data)

---

## 🔄 Data Flow Architecture

```
Fidelity CSV Exports (notebooks/updates/)
    ↓
Portfolio Positions (Columns A, B, G updated)
    ↓ (Google Finance formulas auto-update Column C prices)
    ↓
    ├─→ Dividend Tracker (auto-sync shares + lookup dividends)
    ├─→ Margin Dashboard (import balances, calculate ratios)
    └─→ Weekly Review (future: auto-generate summaries)
```

### Primary Data Sources

1. **Fidelity CSV Files** (`notebooks/updates/`) - AUTHORITATIVE SOURCE:
   - `Balances_for_Account_Z05724592.csv` (exact match required) - Margin balances, account values
   - `Portfolio_Positions_MMM-DD-YYYY.csv` (latest by date in filename) - Ticker, Quantity, Avg Cost Basis

2. **Google Finance Formulas** (CURRENT - AUTO-UPDATING):
   - **Column C (Last Price)**: `=GOOGLEFINANCE(A{row}, "price")` - Real-time stock prices
   - **Columns D-E**: Calculated from price changes (formula-driven)
   - Updates automatically during market hours

3. **Alpha Vantage API** (`src/utils/market_data.py`) - PARTIALLY WORKING:
   - **Column F (Volume)**: Attempting to pull volume data (not fully functional)
   - **Columns N-P (Day Range, 52W Range)**: Market data integration in progress
   - Note: Needs troubleshooting to work reliably

4. **Portfolio Positions Tab** (authoritative for holdings):
   - Ticker symbols (Column A) - from Fidelity CSV
   - Quantities (Column B) - from Fidelity CSV
   - Avg Cost Basis (Column G) - from Fidelity CSV
   - Layer classification (Column S) - pattern-based auto-assignment

---

## 🤖 Agent Permission Matrix

| Agent | Portfolio Positions | Dividend Tracker | Margin Dashboard | Other Tabs |
|-------|---------------------|------------------|------------------|------------|
| **Quant Analyst** | READ-ONLY | READ-ONLY | READ-ONLY | READ-ONLY |
| **Market Researcher** | READ-ONLY | READ-ONLY | READ-ONLY | READ-ONLY |
| **Strategy Advisor** | WRITE (A,B,G) | READ-ONLY | READ-ONLY | READ-ONLY |
| **Builder** | WRITE (A,B,G) | READ/WRITE | READ/WRITE | READ/WRITE |
| **Dividend Specialist** | READ-ONLY | READ/WRITE | READ-ONLY | READ-ONLY |
| **Margin Specialist** | READ-ONLY | READ-ONLY | READ/WRITE | READ-ONLY |
| **Compliance Officer** | READ-ONLY | READ-ONLY | READ-ONLY | READ-ONLY |
| **Teaching Specialist** | READ-ONLY | READ-ONLY | READ-ONLY | READ-ONLY |

**Key Principles**:
- **Read-Only Agents**: Quant, Market Researcher, Compliance, Teaching
- **Write-Enabled Agents**: Builder (all tabs), Strategy Advisor (Portfolio A,B,G only), Dividend/Margin Specialists (their respective tabs)
- **Finance Orchestrator (Cassandra)**: Can coordinate changes but delegates execution to write-enabled agents
- **Column Access**: Portfolio Positions columns A (Ticker), B (Quantity), G (Avg Cost Basis) writable from CSV data
- **Price Data**: Column C (Last Price) maintained by Google Finance formulas - DO NOT TOUCH

---

## 🚨 Safety Guardrails & Warning Triggers

### CRITICAL STOPS (Must halt and alert user)

1. **Position Count Mismatch**:
   - Fidelity CSV has fewer tickers than current Portfolio Positions
   - **Reason**: Possible sale/liquidation - requires manual confirmation before deletion
   - **Action**: Flag missing tickers, WAIT for user approval

2. **Large Quantity Changes (>10%)**:
   - Share count changes by more than 10% for any position
   - **Reason**: Possible stock split, large buy/sell, or data error
   - **Action**: Display old vs new quantities, WAIT for confirmation

3. **Formula Error Cascade (3+ errors)**:
   - Updating data creates 3 or more #N/A, #DIV/0!, #REF! errors
   - **Reason**: Formulas may be broken or data format incompatible
   - **Action**: Rollback changes, show error cells, WAIT for fix

4. **Margin Balance Jump (>$5k single update)**:
   - Margin balance increases by more than $5,000 in one entry
   - **Reason**: Large draw should be intentional and confirmed
   - **Action**: Display new balance, ask user to confirm

### WARNINGS (Proceed with caution)

- **New Position Detected**: Auto-add with pattern-based layer classification, log addition
- **Dividend Amount Change**: If dividend per share changes >20%, flag for review
- **Missing Ex-Date**: If dividend fund lacks ex-date in tracker, flag for manual entry
- **Stale Data Alert**: If Fidelity CSV is >7 days old, warn at session start (already implemented in fin-core hook)

---

## 🎯 Pattern-Based Layer Classification

**Layer 1 - Growth** (Keep 100% - Never Touch):
- **Mega Winners**: PLTR, TSLA, MSTR, COIN
- **Tech Giants**: NVDA, AAPL, GOOGL, SOFI
- **Index Core**: VOO, FNILX, FZROX, FZILX, VTI, VXUS, VUG, QQQ
- **Rule**: High growth stocks, mega-cap tech, passive indexes, Bitcoin proxies

**Layer 2 - Dividend/Income** (Build with W2 Income):
- **Monthly Payers**: JEPI, JEPQ, CLM, CRF, GOF, ETY, ETV, BST, UTG, BDJ
- **High-Income ETFs**: QQQI, SPYI, QQQY, YMAX, MSTY, AMZY
- **Rule**: Monthly dividend distributors, covered call strategies, CEFs with high yields

**Layer 3 - Protection/Hedge** (6% allocation):
- **Inverse ETFs**: SQQQ (ProShares UltraPro Short QQQ)
- **Rule**: Inverse/leveraged ETFs, volatility hedges, protective puts

**Classification Logic**:
```
IF ticker in [JEPI, JEPQ, CLM, CRF, GOF, ETY, ETV, BST, UTG, BDJ, QQQI, SPYI, QQQY, YMAX, MSTY, AMZY]:
    THEN Layer = "Layer 2 - Dividend"
ELSE IF ticker in [SQQQ, UVXY, VXX, SPXU]:
    THEN Layer = "Layer 3 - Protection"
ELSE IF ticker in [PLTR, TSLA, MSTR, COIN, NVDA, AAPL, GOOGL]:
    THEN Layer = "Layer 1 - Growth"
ELSE IF ticker matches index pattern [VOO, VTI, QQQ, FNILX, FZROX, FZILX]:
    THEN Layer = "Layer 1 - Growth"
ELSE:
    THEN Layer = "UNKNOWN - Manual Review Required"
    ALERT user for classification
```

---

## 📋 Agent Update Workflows

### Workflow 1: Import Fidelity CSV to Portfolio Positions

**Trigger**: User downloads new Fidelity CSV to `notebooks/updates/`
**Responsible Agent**: Builder
**Steps**:

1. **Read Latest CSV**:
   - Locate `Portfolio_Positions_MMM-DD-YYYY.csv` (most recent by date)
   - Parse key fields from Fidelity CSV:
     - Symbol (→ Column A: Ticker)
     - Quantity (→ Column B: Quantity)
     - Average Cost Basis (→ Column G: Avg Cost Basis)

2. **Compare with Current Sheet**:
   - Read Portfolio Positions columns A (Ticker), B (Quantity), G (Avg Cost Basis)
   - Identify: NEW tickers, EXISTING tickers, MISSING tickers (in sheet but not CSV)

3. **Safety Checks**:
   - **Missing Tickers**: If CSV has fewer tickers, STOP and alert user (possible sale)
   - **Large Quantity Changes**: If any ticker quantity changes >10%, STOP and show diff
   - **Cost Basis Changes**: If avg cost basis changes >20%, flag for review (possible corporate action)
   - **Formula Validation**: Check columns C-S for #N/A or #DIV/0! errors before updating

4. **Update Operations**:
   - **Existing Tickers**: Update Column B (Quantity) AND Column G (Avg Cost Basis)
   - **New Tickers**:
     - Add row with Ticker (A), Quantity (B), Avg Cost Basis (G)
     - Apply pattern-based layer classification (Column S)
     - Google Finance formula in Column C will auto-populate price
     - Log addition: "Added {TICKER} - {SHARES} shares @ ${AVG_COST} - Layer: {LAYER}"
   - **Do NOT touch**:
     - Column C (Last Price - Google Finance formula)
     - Columns D-F ($ Change, % Change, Volume - formulas/Alpha Vantage)
     - Columns H-M (Gains/Losses - calculated formulas)
     - Columns N-S (Ranges, dividends, layer - formulas or manual)

5. **Post-Update Validation**:
   - Verify Google Finance formulas auto-populated prices for new tickers
   - Verify formulas still functional (no new #N/A errors)
   - Check row count matches expected additions
   - Log update summary: "Updated {N} positions (quantity + cost basis), added {M} new tickers"

---

### Workflow 2: Sync Dividend Tracker from Portfolio Positions

**Trigger**: Portfolio Positions updated OR monthly dividend cycle
**Responsible Agent**: Dividend Specialist
**Steps**:

1. **Read Portfolio Positions**:
   - Get all tickers from Layer 2 - Dividend (Column S filter)
   - Extract Ticker (A), Quantity (B), Layer (S)

2. **Cross-Reference Dividend Tracker**:
   - Match tickers between Portfolio Positions and Dividend Tracker
   - Identify: MISSING funds (in portfolio but not tracker), MISMATCHED shares

3. **Lookup Dividend Data** (if needed):
   - Use financial APIs or web search to find:
     - Current dividend per share
     - Ex-dividend date
     - Payment frequency (monthly/quarterly)
     - DRIP status (check user-profile.yaml for fund-specific preferences)

4. **Update Dividend Tracker**:
   - **Existing Funds**:
     - Update "Shares Owned" to match Portfolio Positions
     - Recalculate "Total Dividend $" = Shares × Dividend Per Share
   - **New Funds**:
     - Add row with Fund Symbol, Fund Name, Shares, Dividend Per Share
     - Set DRIP status based on portfolio strategy (default: No - Cash for income funds)
     - Calculate Total Dividend $
   - **Validate Totals**: Ensure "TOTAL EXPECTED DIVIDENDS" formula sums correctly (fix #N/A if needed)

5. **Generate Alerts**:
   - Flag dividend cuts (>20% reduction in dividend per share)
   - Flag missing ex-dates for upcoming months
   - Report expected monthly income total

---

### Workflow 3: Update Margin Dashboard from Fidelity Balances

**Trigger**: User downloads new Fidelity balances CSV
**Responsible Agent**: Margin Specialist
**Steps**:

1. **Read Balances CSV**:
   - Locate `Balances_for_Account_Z05724592.csv` (exact match)
   - Parse key fields:
     - Total account value (Portfolio Value)
     - Margin balance (Net debit or Margin market value)
     - Margin interest rate
     - Margin interest accrued this month

2. **Safety Check**:
   - **Margin Jump**: If new balance > previous balance + $5,000, STOP and confirm
   - **Reason**: Large draws should be intentional per margin-living strategy

3. **Add Entry to Margin Dashboard**:
   - Insert new row with:
     - Date: Current date
     - Margin Balance: From CSV
     - Interest Rate: From CSV (default: 10.875%)
     - Monthly Interest Cost: Calculate (Balance × Rate ÷ 12)
     - Notes: Auto-generate (e.g., "Month 3 - On track per strategy")

4. **Update Summary Section**:
   - **Current Margin Balance**: Latest entry
   - **Monthly Interest Cost**: Latest calculated cost
   - **Annual Interest Cost**: Monthly × 12
   - **Dividend Income**: Pull from Dividend Tracker "TOTAL EXPECTED DIVIDENDS"
   - **Coverage Ratio**: Dividends ÷ Interest Cost (fix #DIV/0! if margin = $0)

5. **Calculate Strategy Metrics**:
   - **Portfolio-to-Margin Ratio**: Portfolio Value ÷ Margin Balance
   - **Alert Thresholds**:
     - Green: Ratio > 4.0 (target)
     - Yellow: Ratio 3.5-4.0 (warning)
     - Red: Ratio < 3.0 (alert - inject business income)

6. **Scaling Alerts** (based on time elapsed since Oct 9, 2025 start):
   - **Month 6 (Apr 2026)**: Check if dividends > $2,000/month AND ratio > 4:1 → Suggest scaling to $6,213
   - **Month 12 (Oct 2026)**: Check if dividends > $4,500/month (break-even) → Suggest scaling to $8,000
   - **Month 18 (Apr 2027)**: Check if dividends > $7,000/month AND declining margin → Suggest scaling to $10,000

---

### Workflow 4: Smart Formula Repair

**Trigger**: Agent detects #N/A, #DIV/0!, #REF! errors in formulas
**Responsible Agent**: Builder
**Steps**:

1. **Identify Broken Formulas**:
   - Scan all tabs for error codes
   - Log: Cell location, error type, formula content

2. **Classify Repair Type**:
   - **#DIV/0!**: Usually margin dashboard when balance = $0 → Add IFERROR() wrapper
   - **#N/A**: Usually VLOOKUP failures → Check if source data exists, fix range references
   - **#REF!**: Deleted rows/columns → Reconstruct formula or mark for manual review

3. **Safe Repair Operations**:
   - ✅ ALLOWED: Add IFERROR() wrappers to prevent display issues
   - ✅ ALLOWED: Fix broken cell references (e.g., change `Sheet1!A1` to `Portfolio Positions!A1`)
   - ✅ ALLOWED: Update formula ranges if data expanded (e.g., A2:A50 → A2:A100)
   - ❌ FORBIDDEN: Change formula logic (e.g., SUM → AVERAGE)
   - ❌ FORBIDDEN: Remove formulas and replace with static values

4. **Validation**:
   - Test repair on single cell first
   - If successful, apply to all similar errors
   - If repair creates new errors, ROLLBACK and alert user

5. **Documentation**:
   - Log all repairs: "Fixed #DIV/0! in Margin Dashboard C10 by adding IFERROR()"
   - Report summary to user

---

## 📐 Formula Protection Rules

### NEVER TOUCH (Sacred Formulas)

These formulas are core to the spreadsheet's integrity and must NEVER be modified by agents:

1. **Portfolio Positions**:
   - **Last Price** (Column C): `=GOOGLEFINANCE(A{row}, "price")` - DO NOT TOUCH (auto-updates)
   - **$ Change, % Change** (Columns D-E): Formulas based on Column C - DO NOT TOUCH
   - **Current Value** (Column L): `=B{row} * C{row}` (Quantity × Last Price) - DO NOT TOUCH
   - **Total G/L $** (Column K): `=L{row} - M{row}` (Current Value - Cost Basis) - DO NOT TOUCH
   - **Total G/L %** (Column L): `=K{row} / M{row}` (Total G/L $ ÷ Cost Basis) - DO NOT TOUCH
   - **Note**: Column G (Avg Cost Basis) is WRITABLE from CSV, Column M (Cost Basis) is formula-calculated

2. **Dividend Tracker**:
   - **Total Dividend $**: `=D{row} * E{row}` (Shares × Dividend Per Share)
   - **TOTAL EXPECTED DIVIDENDS**: `=SUM(F2:F{lastrow})`

3. **Margin Dashboard**:
   - **Coverage Ratio**: `=IFERROR(Dividends / Interest, 0)` - Only add IFERROR if missing

### ALLOWED REPAIRS

- ✅ Add `IFERROR(formula, 0)` or `IFERROR(formula, "N/A")` to prevent error display
- ✅ Fix broken sheet references (e.g., `Sheet1!A1` → `Portfolio Positions!A1`)
- ✅ Expand ranges if data grows (e.g., `A2:A50` → `A2:A100`)
- ✅ Fix typos in cell references (e.g., `B100` → `B10` if B100 doesn't exist)

---

## 🔐 Version Control & Backups

**Primary Backup**: Google Sheets native version history
- Google automatically versions every change
- Agents do NOT need to create backup tabs
- User can restore via: File → Version History → See Version History

**Secondary Backup**: Git snapshots (optional)
- After major batch updates, agents MAY export CSV snapshots to Git
- Location: `notebooks/updates/snapshots/{YYYY-MM-DD}/`
- Only for significant changes (e.g., added 10+ new positions, major formula repair)

---

## 📖 Agent Reference Checklist

Before ANY write operation to the spreadsheet, agents MUST verify:

- [ ] **Permission Check**: Is my role allowed to write to this tab? (see Agent Permission Matrix)
- [ ] **Column Check**: Am I only touching allowed columns? (Portfolio Positions = A, B, G only)
- [ ] **Data Source**: Is this data from authoritative Fidelity CSV or Portfolio Positions?
- [ ] **Safety Gates**: Did I check for position mismatches, large changes (>10%), cost basis changes (>20%), margin jumps?
- [ ] **Formula Protection**: Am I about to touch any formulas? (STOP if yes, unless repair workflow)
  - **NEVER touch Column C** (Google Finance price formulas)
  - **NEVER touch Columns D-F, H-M** (calculated formulas)
- [ ] **Validation**: Will this change create new errors? (Test first if uncertain)
- [ ] **Logging**: Am I documenting what changed and why?
- [ ] **User Notification**: Should user be alerted before or after this change?

**Golden Rule**: When in doubt, READ-ONLY and ASK USER for guidance.

---

## 🎓 Teaching Notes for New Agents

If you're a Finance Guru agent encountering this spreadsheet for the first time:

1. **READ THIS DOCUMENT FIRST** - Don't touch the sheet until you understand the rules
2. **Check Your Role** - Are you read-only or write-enabled? (see Agent Permission Matrix)
3. **Understand Data Flow** - Fidelity CSV → Portfolio Positions (A, B, G) → Other tabs derived
4. **Respect Formula Boundaries**:
   - **WRITABLE**: Columns A (Ticker), B (Quantity), G (Avg Cost Basis) from CSV
   - **SACRED**: Column C (Google Finance formulas), Columns D-F, H-S (calculated formulas)
5. **Use Safety Gates** - Stop and alert on mismatches, large changes (>10%), errors (3+)
6. **Document Changes** - Log every write operation with timestamp and reasoning
7. **Ask Questions** - If architecture is unclear, ask Cassandra (Finance Orchestrator) or user

**Common Mistakes to Avoid**:
- ❌ Updating prices manually in Portfolio Positions (they're formula-calculated)
- ❌ Deleting positions without user confirmation (might be intentional sale)
- ❌ Changing layer classification without pattern-based logic
- ❌ Breaking formulas while "helping" fix them
- ❌ Creating backup tabs (Google handles this natively)

---

## 📅 Maintenance Schedule

**Daily**:
- Agents should READ-ONLY access for analysis (no writes)

**Weekly**:
- Check for new Fidelity CSV exports in `notebooks/updates/`
- If new CSV found, trigger Workflow 1 (Import to Portfolio Positions)

**Monthly**:
- Sync Dividend Tracker (Workflow 2) around ex-dividend dates
- Update Margin Dashboard (Workflow 3) after month-end Fidelity export
- Validate formula health (run Workflow 4 if errors detected)

**Quarterly**:
- Full spreadsheet audit by Compliance Officer
- Review layer classifications for any portfolio drift
- Update strategy metrics (scaling alerts, coverage ratios)

---

## 🆘 Emergency Procedures

### If Agent Breaks the Spreadsheet

1. **STOP immediately** - Do not attempt to fix it yourself
2. **Alert user** - Clearly explain what went wrong
3. **Document the error** - Cell locations, what changed, what broke
4. **Suggest rollback** - User can restore via Google Sheets version history
5. **Learn from it** - Update this architecture doc if new edge case discovered

### If Data Looks Wrong

1. **Verify source** - Is Fidelity CSV corrupted or outdated?
2. **Check formulas** - Are there #N/A or #REF! errors upstream?
3. **Compare totals** - Does Portfolio Value match Fidelity total?
4. **Flag for user** - Don't assume data is wrong, ASK first

### If User Overrides Agent Rules

- Document the exception (e.g., "User manually edited formula in Column C")
- Update architecture doc if this becomes a pattern
- Adapt workflows to accommodate user's preferences

---

**Last Updated**: 2025-11-11
**Version**: 1.0
**Maintained by**: Finance Guru™ Finance Orchestrator (Cassandra Holt)
**Questions**: Route through Cassandra or ask user directly
