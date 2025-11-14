# Google Sheets Architecture & Agent Workflow Rules
<!-- Finance Guru™ Portfolio Tracker | Established: 2025-11-11 -->

## 📊 Spreadsheet Overview

**Spreadsheet ID**: `1HtHRP3CbnOePb8RQ0RwzFYOQxk0uWC6L8ZMJeQYfWk4`
**URL**: https://docs.google.com/spreadsheets/d/1HtHRP3CbnOePb8RQ0RwzFYOQxk0uWC6L8ZMJeQYfWk4/edit
**Purpose**: Portfolio tracking, dividend income monitoring, margin strategy dashboard

---

## 🏗️ Tab Structure & Purpose

### 1. DataHub (1039 rows × 19 columns)
**Purpose**: Master holdings tracker with real-time prices, gains/losses, and layer classification

**Sheet Structure**:
- **Rows 2-40**: Active Portfolio (Fidelity TOD) - **FINANCE GURU FOCUS**
- **Rows 45-64**: Retirement Accounts (Vanguard + 401k) - **TRACKING ONLY**
- **Rows 67+**: Cryptocurrency Holdings (BTC) - **TRACKING ONLY**

**Columns**:
- **A**: Ticker Symbol (agent-writable from CSV)
- **B**: Quantity (agent-writable from CSV)
- **C**: Last Price (Google Finance formula - auto-updates, except crypto = manual)
- **D-E**: $ Change, % Change (formulas based on Column C)
- **F**: Volume (Alpha Vantage - partially working)
- **G**: Avg Cost Basis (agent-writable from CSV for active portfolio only)
- **H-M**: Gains/Losses (Day G/L $, Day G/L %, Total G/L $, Total G/L %) - FORMULA-MAINTAINED
- **N-P**: Day Range, 52W Range, Earnings Date (Alpha Vantage - partially working)
- **Q-S**: Div Amount, Div Ex-Date, Portfolio Layer (formulas + manual)

**Agent Rules**:
- ✅ WRITE (Active Portfolio, Rows 2-40): Columns A, B, G from Fidelity CSV
- ✅ WRITE (Retirement, Rows 45-64): Columns A, B from `notebooks/retirement-accounts/` - NO Column G
- ✅ WRITE (Crypto, Rows 67+): Columns A, B, C (manual pricing)
- ❌ READ-ONLY: All other columns (maintained by Google Finance formulas, Alpha Vantage, or calculated formulas)
- ⚠️ NEW POSITIONS: Auto-add using pattern-based layer classification (active portfolio only)
- ⚠️ CRITICAL: Do NOT include retirement/crypto in Finance Guru strategy analysis

### 2. Dividend Tracker (1013 rows × 26 columns)
**Purpose**: Track expected and received dividend payments with DRIP status

**Columns**:
- Date Received
- Fund Symbol
- Fund Name
- Shares Owned (synced from DataHub)
- Dividend Per Share
- Total Dividend $
- Reinvested? (Yes/No)
- Notes

**Agent Rules**:
- ✅ AUTO-SYNC: Read ticker + shares from DataHub
- ✅ LOOKUP: Fetch current dividend amounts and ex-dates
- ✅ CALCULATE: Total Dividend $ = Shares × Dividend Per Share
- ⚠️ VALIDATE: Flag mismatches between DataHub shares and Dividend Tracker shares

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
┌─ ACTIVE PORTFOLIO ──────────────────────────────────────┐
│ Fidelity CSV Exports (notebooks/updates/)              │
│     ↓                                                    │
│ DataHub Rows 2-40 (Columns A, B, G updated) │
│     ↓ (Google Finance formulas auto-update Column C)    │
│     ├─→ Dividend Tracker (auto-sync shares)             │
│     ├─→ Margin Dashboard (import balances)              │
│     └─→ Weekly Review (future: auto-summaries)          │
└──────────────────────────────────────────────────────────┘

┌─ RETIREMENT ACCOUNTS (Monthly) ─────────────────────────┐
│ Vanguard/401k CSV Exports (notebooks/retirement-accounts/) │
│     ↓                                                    │
│ DataHub Rows 45-64 (Columns A, B updated)   │
│     ↓ (Google Finance OR manual pricing Column C)       │
│     └─→ Total Assets calculation only                   │
└──────────────────────────────────────────────────────────┘

┌─ CRYPTOCURRENCY (As Needed) ────────────────────────────┐
│ User-provided data (quantity + price)                   │
│     ↓                                                    │
│ DataHub Rows 67+ (Columns A, B, C manual)   │
│     └─→ Total Assets calculation only                   │
└──────────────────────────────────────────────────────────┘
```

### Primary Data Sources

1. **Fidelity CSV Files** (`notebooks/updates/`) - AUTHORITATIVE for active portfolio:
   - `Balances_for_Account_Z05724592.csv` (exact match required) - Margin balances, account values
   - `Portfolio_Positions_MMM-DD-YYYY.csv` (latest by date in filename) - Ticker, Quantity, Avg Cost Basis

2. **Retirement Account CSVs** (`notebooks/retirement-accounts/`) - Monthly updates:
   - `OfxDownload.csv`, `OfxDownload (1).csv` (Vanguard exports) - Ticker, Quantity
   - `Portfolio_Positions_Nov-11-2025.csv` (CBN 401k) - Ticker, Quantity
   - **NO cost basis tracking** for retirement accounts

3. **Cryptocurrency Data** - User-provided:
   - Manual entry of ticker (BTC, ETH, etc.), quantity, and current price
   - Updated as needed, not on regular schedule

4. **Google Finance Formulas** (CURRENT - AUTO-UPDATING):
   - **Column C (Last Price)**: `=GOOGLEFINANCE(A{row}, "price")` - Real-time stock prices
   - **Columns D-E**: Calculated from price changes (formula-driven)
   - Updates automatically during market hours
   - **Exception**: Crypto rows use manual pricing (Google Finance doesn't support BTC)

5. **Alpha Vantage API** (`src/utils/market_data.py`) - PARTIALLY WORKING:
   - **Column F (Volume)**: Attempting to pull volume data (not fully functional)
   - **Columns N-P (Day Range, 52W Range)**: Market data integration in progress
   - Note: Needs troubleshooting to work reliably

6. **DataHub Tab** (authoritative for holdings):
   - **Active Portfolio**: Ticker (A), Quantities (B), Avg Cost Basis (G) from Fidelity CSV
   - **Retirement Accounts**: Ticker (A), Quantities (B) from retirement CSVs, NO cost basis
   - **Crypto**: Manual entry for all columns
   - Layer classification (Column S) - pattern-based auto-assignment (active portfolio only)

---

## 🤖 Apps Script Automation Layer

**Script ID:** `1qE0sv8ABE7LpXpUXSdcGvckFF84MrjbxYm91LTEsHJZ5pYw5mPypoBUI`

**Purpose:** Multi-module portfolio optimization, dividend fetching, and hedge analysis automation

**Location:** `scripts/google-sheets/portfolio-optimizer/`

### Custom Menu (Portfolio Sheet)

When user opens the Google Sheets document, Apps Script adds a custom menu to the Portfolio sheet:

```
Portfolio Optimizer ▼
├─ Update Dividend Data     → Runs Dividend.js (fetches real-time dividend data)
├─ History Data             → Runs History.js (builds 90+ day price history)
├─ Deposit                  → Runs Code.js (calculates optimal allocation)
└─ Hedge Analysis           → Runs Hedge.js (Black-Scholes put recommendations)
```

### Automated Triggers

**onOpen() Trigger:**
- Fires when user opens spreadsheet
- Adds Portfolio Optimizer custom menu
- Loads configuration from Weights sheet
- Initializes data cache for 1-hour TTL

**onEdit(e) Trigger:**
- Monitors cell M1 on Portfolio sheet
- When M1 is edited → Automatically runs `updateDividendDataFast()`
- Use case: User edits M1 cell (any value) to trigger immediate dividend refresh
- No manual menu click needed for quick updates

### Portfolio Optimizer Integration (Code.js)

**Primary Function:** `findOptimalDividendFocusedMix()`

**When User Clicks "Deposit" Menu Item:**

1. **Reads Configuration:**
   - Deposit amount from Portfolio sheet cell B1
   - Allocation mode from cell C1 (CORE, HYBRID, SCORE, etc)
   - Weights configuration from Weights sheet (16 parameters)

2. **Processes Portfolio Data:**
   - Reads all positions from Portfolio sheet rows 3+
   - Fetches column headers from row 2 (auto-detects pattern)
   - Maps columns: Ticker (A), Price (C), Cost Basis (D), Shares Owned (E), TTM Dividend (G)

3. **Calculates 12-Factor Score:**
   - **Cost Base**: Value buying bonus if position underwater
   - **Yield Boost**: Tiered based on dividend yield (8%→0.5, 6%→0.4, etc)
   - **Ex-Date Boost**: Proximity to ex-dividend date (28-day window)
   - **Cost Boost**: Dividend efficiency (yield on price vs cost basis)
   - **Manual Boost**: User override from Portfolio sheet column N
   - **Mode Boost**: CORE mode bonus for core tickers (from Weights)
   - **Maintenance Boost**: Margin maintenance favorability
   - **Diversification**: Under-allocated positions (<5% of portfolio)
   - **Heavy Penalty**: Over-allocated non-core positions (>10%)
   - **Momentum**: 5-day vs 20-day moving average (requires History sheet)
   - **Volatility**: Annualized standard deviation (requires History sheet)
   - **Sharpe-Yield**: Risk-adjusted dividend yield (requires History sheet)

4. **Applies Position Caps:**
   - Default cap: 30% of portfolio per position
   - Mode enforcement: CAP_PCT from Weights sheet
   - Respects CORE ticker prioritization

5. **Outputs Recommendations:**
   - Writes share counts to Column F "Shares to Buy"
   - Updates cell F1 with estimated monthly income impact
   - Color-codes blue cells (action items)

**Configuration (Row 1, Portfolio Sheet):**

| Cell | Label | Purpose | Example |
|------|-------|---------|---------|
| B1 | Deposit | Amount to allocate this month | $13,317 |
| C1 | Mode | Allocation strategy | HYBRID |
| M9 | VIX | Market volatility reference (info only) | 14.2 |

**Configuration (Weights Sheet):**

Create a sheet named `Weights` with 2 columns (no headers):

| Key | Value | Purpose |
|-----|-------|---------|
| CAP_PCT | 0.30 | Max 30% per position |
| CAP_MODE | HYBRID | Enforce both caps |
| CORE_TICKERS | CLM,CRF,GOF | Core tickers get priority |
| YIELD_THRESHOLDS | 8,6,4,2,1 | Yield breakpoints |
| YIELD_VALUES | 0.5,0.4,0.3,0.2,0.1 | Score values for yields |
| HEAVY_THRESHOLD | 0.10 | Over-allocation penalty threshold |
| costBase | 5.0 | Weight for value buying |
| yieldBoost | 10.0 | Weight for high yield |
| exBoost | 3.0 | Weight for ex-date proximity |
| costBoost | 2.0 | Weight for yield efficiency |
| manualBoost | 8.0 | Weight for user override |
| modeBoost | 15.0 | Weight for CORE mode |
| maintBoost | 4.0 | Weight for margin maintenance |
| diversificationBoost | 6.0 | Weight for under-allocated |
| heavyPenalty | -10.0 | Penalty for over-allocated |
| momentum | 3.0 | Weight for 5/20-day MA |
| volatility | -2.0 | Penalty for high volatility |
| sharpeYield | 5.0 | Weight for risk-adjusted yield |

**Output (Column F - Portfolio Sheet):**

```
Row 1: [F1] = Estimated monthly income (e.g., $847)
Row 2: [F2] = Header "Shares to Buy"
Row 3+: [F3], [F4], etc = Recommended share quantities
        Format: Blue cell = action needed
                0 = position at cap
                Empty = no allocation
```

---

### Dividend Data Fetcher Integration (Dividend.js)

**Primary Function:** `updateDividendDataFast()`

**When User Clicks "Update Dividend Data" OR Edits Cell M1:**

1. **Reads Portfolio Data:**
   - All tickers from Portfolio sheet column A (rows 3+)
   - Identifies Layer 2 dividend positions

2. **Fetches Live Dividend Data:**
   - Ex-dividend dates
   - Pay dates
   - Dividend amounts per share
   - Payment frequency (weekly, monthly, quarterly)

3. **Calculates Dividend Metrics:**
   - Days until ex-dividend date (Column I)
   - Days until pay date (Column K)
   - Next payment amount per share (Column L)
   - Dividend yield = TTM ÷ Current Price (Column M)

4. **Populates Columns (Portfolio Sheet):**

   | Column | Header | Purpose | Example |
   |--------|--------|---------|---------|
   | G | TTM Dividend | Annual dividend per share | $5.89 |
   | I | Days Until Ex | Days to ex-dividend date | 8 |
   | K | Days Until Pay | Days to payment | 15 |
   | L | Next Pay Amount | Per-share amt × shares owned | $362.50 |
   | M | Dividend Yield | TTM / Current Price | 10.3% |

**Auto-Trigger Configuration:**
- Edit cell M1 (Portfolio sheet) to trigger automatic run
- 1-hour cache to reduce API calls
- 150ms sleep between fetches (rate limiting)

**Cache Configuration:**
```javascript
const DD_CFG = {
  SHEET_NAME: 'Portfolio',
  HEADER_ROW: 2,
  START_ROW: 3,
  CACHE_TTL_SEC: 3600,    // 1 hour
  SLEEP_MS_BETWEEN_FETCHES: 150
};
```

---

### Hedge Analysis Integration (Hedge.js)

**Primary Function:** `analyzeHedge()`

**When User Clicks "Hedge Analysis" Menu Item:**

1. **Reads Portfolio Configuration:**
   - Portfolio total value (from DataHub)
   - Budget for hedge (% of portfolio) - Cell H1
   - Target portfolio drop to protect against (%) - Cell H2
   - Days to option expiration (DTE) - Cell H3
   - Downside weight (coverage intensity) - Cell H4

2. **Fetches Index Data:**
   - 90+ days historical prices for SPY, QQQ, IWM, or DIA
   - Calculates index volatility (annualized)
   - Prices put options using Black-Scholes model

3. **Calculates Black-Scholes Option Pricing:**
   - Assumptions: Risk-free rate 3.0%, dividend yields vary by index
   - Computes Greeks: Delta, Gamma, Theta, Vega
   - Sizes position to budget percentage

4. **Outputs Hedge Recommendations to HedgeAnalysis Sheet:**
   - Recommended put strike price
   - Expiration date
   - Number of contracts to buy
   - Total premium cost
   - Expected protection at target drop %
   - Greeks for hedge Greeks monitoring

**Configuration (HedgeAnalysis Sheet, Cells G1-H4):**

```
G1: Budget % of Portfolio         | H1: 0.5%   (max 0.5% of portfolio value)
G2: Target Portfolio Drop %       | H2: 10%    (protect against 10% decline)
G3: DTE (days)                    | H3: 30     (30-day expiration)
G4: Downside Weight               | H4: 1.0    (1.0 = full coverage)
```

**Supported Indices & Proxies:**
- Primary: SPY (S&P 500), QQQ (Nasdaq 100), IWM (Russell 2000), DIA (Dow)
- Proxy (lower cost): SPLG, QQQM, VTWO, IYY

---

### History Data Builder Integration (History.js)

**Primary Function:** `buildHistory()`

**When User Clicks "History Data" Menu Item:**

1. **Fetches Historical Prices:**
   - 90+ days of daily close prices for all Portfolio sheet tickers
   - Fetches from reliable market data sources

2. **Creates History Sheet:**
   - Format: 3 columns - Ticker | Date | Close
   - Minimum 30 days per ticker
   - 90 days recommended (for hedge analysis)

3. **Used By Other Modules:**
   - Code.js: Momentum scoring (5-day vs 20-day MA)
   - Code.js: Volatility scoring (annualized std dev)
   - Code.js: Sharpe-Yield scoring (risk-adjusted return)
   - Hedge.js: Index correlations and VaR calculations

**Output Format (History Sheet):**
```
Row 1: [Headers] Ticker | Date | Close
Row 2+:
  PLTR | 2025-10-01 | 72.50
  PLTR | 2025-10-02 | 73.15
  JEPI | 2025-10-01 | 57.25
  ...
```

---

### FIRE Model Integration (FireModel.js)

**Primary Function:** `calculateFireModel()`

**When User Clicks "Analyze" on FIRE Model Sheet:**

1. **Reads Base Data:**
   - Portfolio value from DataHub (current holdings)
   - Monthly dividend income (from Dividends sheet)
   - Margin interest cost (from Portfolio sheet G25)
   - Monthly expenses (from Budget Planner sheet)

2. **Projects 28 Months Forward:**
   - Assumes 2% annual dividend growth
   - Assumes margin interest at 10.875% (or user-entered)
   - Assumes 1% annual expense growth
   - Tracks breakeven point (when dividends > expenses)

3. **Outputs Projection Table:**

   | Month | Dividends | Expenses | Margin Int | Net Cash | Portfolio Value |
   |-------|-----------|----------|------------|----------|-----------------|
   | 0 | $3,200 | $4,500 | $625 | -$1,925 | $840,000 |
   | 1 | $3,215 | $4,545 | $625 | -$1,955 | $842,000 |
   | ... | ... | ... | ... | ... | ... |
   | 28 | $3,800 | $4,500 | $0 | +$300 | $1,050,000 |

---

## Data Relationships & Formulas

### DataHub → Apps Script Workflows

**Formula Pattern: Active Portfolio Ticker Filtering**
```
=FILTER(DataHub!A2:A40, DataHub!S2:S40="Layer 2 - Dividend")
```
(Automatically pulls only Layer 2 dividend tickers from DataHub)

**Column Reference Pattern: Cost Basis Sync**
```
=VLOOKUP(A3, DataHub!A:G, 7, FALSE)
```
(Portfolio sheet Column D syncs cost basis from DataHub automatically)

**Column Reference Pattern: Current Price Lookup**
```
=VLOOKUP(A3, {DataHub!A:C}, 3, FALSE)
```
(Portfolio sheet Column C looks up latest prices from DataHub)

---

## 🤖 Agent Permission Matrix

| Agent | DataHub | Dividend Tracker | Margin Dashboard | Portfolio (Apps) | Weights | History |
|-------|---------------------|------------------|------------------|-----------------|---------|---------|
| **Quant Analyst** | READ-ONLY | READ-ONLY | READ-ONLY | READ-ONLY | READ-ONLY | READ-ONLY |
| **Market Researcher** | READ-ONLY | READ-ONLY | READ-ONLY | READ-ONLY | READ-ONLY | READ-ONLY |
| **Strategy Advisor** | WRITE (A,B,G) | READ-ONLY | READ-ONLY | READ-ONLY | READ-ONLY | READ-ONLY |
| **Builder** | WRITE (A,B,G) | READ/WRITE | READ/WRITE | READ-ONLY | WRITE | WRITE |
| **Dividend Specialist** | READ-ONLY | READ/WRITE | READ-ONLY | READ-ONLY | READ-ONLY | READ-ONLY |
| **Margin Specialist** | READ-ONLY | READ-ONLY | READ/WRITE | READ-ONLY | READ-ONLY | READ-ONLY |
| **Compliance Officer** | READ-ONLY | READ-ONLY | READ-ONLY | READ-ONLY | READ-ONLY | READ-ONLY |
| **Teaching Specialist** | READ-ONLY | READ-ONLY | READ-ONLY | READ-ONLY | READ-ONLY | READ-ONLY |

**Key Principles**:
- **Read-Only Agents**: Quant, Market Researcher, Compliance, Teaching
- **Write-Enabled Agents**: Builder (all tabs), Strategy Advisor (DataHub A,B,G only), Dividend/Margin Specialists (their respective tabs)
- **Apps Script Automation**: Builder maintains Code.js, Dividend.js, Hedge.js modules
- **Finance Orchestrator (Cassandra)**: Coordinates script execution, doesn't directly write
- **Column Access**:
  - **Active Portfolio (Rows 2-40)**: Columns A (Ticker), B (Quantity), G (Avg Cost Basis) writable from Fidelity CSV
  - **Retirement (Rows 45-64)**: Columns A, B writable from retirement CSVs monthly - NO Column G
  - **Crypto (Rows 67+)**: Columns A, B, C writable when requested by user
  - **Portfolio Sheet (Apps Script)**: Apps Script writes only to Column F (Shares to Buy) and helper columns
- **Price Data**: DataHub Column C maintained by Google Finance formulas - DO NOT TOUCH (except crypto rows)
- **Strategy Analysis**: Finance Guru analysis includes ONLY active portfolio (rows 2-40), NOT retirement or crypto

---

## 🚨 Safety Guardrails & Warning Triggers

### CRITICAL STOPS (Must halt and alert user)

1. **Position Count Mismatch**:
   - Fidelity CSV has fewer tickers than current DataHub
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

### Workflow 1: Import Fidelity CSV to DataHub

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
   - Read DataHub columns A (Ticker), B (Quantity), G (Avg Cost Basis)
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

### Workflow 2: Sync Dividend Tracker from DataHub

**Trigger**: DataHub updated OR monthly dividend cycle
**Responsible Agent**: Dividend Specialist
**Steps**:

1. **Read DataHub**:
   - Get all tickers from Layer 2 - Dividend (Column S filter)
   - Extract Ticker (A), Quantity (B), Layer (S)

2. **Cross-Reference Dividend Tracker**:
   - Match tickers between DataHub and Dividend Tracker
   - Identify: MISSING funds (in portfolio but not tracker), MISMATCHED shares

3. **Lookup Dividend Data** (if needed):
   - Use financial APIs or web search to find:
     - Current dividend per share
     - Ex-dividend date
     - Payment frequency (monthly/quarterly)
     - DRIP status (check user-profile.yaml for fund-specific preferences)

4. **Update Dividend Tracker**:
   - **Existing Funds**:
     - Update "Shares Owned" to match DataHub
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
   - ✅ ALLOWED: Fix broken cell references (e.g., change `Sheet1!A1` to `DataHub!A1`)
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

### Workflow 5: Update Retirement Accounts (Monthly)

**Trigger**: User downloads retirement account CSVs monthly
**Responsible Agent**: Builder
**Frequency**: Monthly
**Steps**:

1. **Read Retirement CSVs**:
   - Locate files in `notebooks/retirement-accounts/`:
     - `OfxDownload.csv`, `OfxDownload (1).csv` (Vanguard accounts)
     - `Portfolio_Positions_Nov-11-2025.csv` (CBN 401k)
   - Parse key fields:
     - Symbol (→ Column A: Ticker)
     - Quantity/Shares (→ Column B: Quantity)

2. **Update DataHub Rows 45-64**:
   - **Existing tickers**: Update Column B (Quantity) only
   - **New tickers**:
     - Add row with Ticker (A), Quantity (B)
     - Add Google Finance formula in Column C: `=GOOGLEFINANCE(A{row}, "price")`
     - If Google Finance fails (#N/A), manually enter price or leave for user
   - **Do NOT touch**: Column G (no cost basis for retirement accounts)

3. **Manual Pricing for Unsupported Tickers**:
   - Common unsupported tickers: VMFXX, VGINF, FGCKX, FXAIX, VMCPX, VSCPX
   - If Google Finance returns #N/A, leave price field for user to manually update
   - User will provide price from their statement

4. **Post-Update Validation**:
   - Verify row count in retirement section (45-64)
   - Check for formula errors
   - Log summary: "Updated {N} retirement positions"

5. **⚠️ CRITICAL REMINDER**:
   - Do NOT include retirement accounts in Finance Guru strategy analysis
   - These are TRACKING ONLY - not part of active trading decisions

---

### Workflow 6: Update Cryptocurrency Holdings (As Needed)

**Trigger**: User provides crypto quantity and current price
**Responsible Agent**: Builder
**Frequency**: As needed (irregular)
**Steps**:

1. **Receive User Data**:
   - Ticker (BTC, ETH, etc.)
   - Quantity (e.g., 4.03 BTC)
   - Current price (e.g., $102,197.00)

2. **Update DataHub Row 68+**:
   - **Column A**: Ticker symbol (BTC, ETH, etc.)
   - **Column B**: Quantity
   - **Column C**: Price (manual entry - Google Finance doesn't support crypto)
   - **Do NOT add Google Finance formula** for crypto

3. **Calculate Current Value**:
   - Column L should have formula: `=B{row} * C{row}`
   - Verify calculation is correct

4. **Post-Update Validation**:
   - Verify crypto total is included in "Total Assets" row
   - Log update: "Updated {TICKER} - {QUANTITY} @ ${PRICE}"

5. **⚠️ CRITICAL REMINDER**:
   - Do NOT include cryptocurrency in Finance Guru strategy analysis
   - Crypto is TRACKING ONLY - not part of active trading decisions
   - User stores crypto in cold storage (not on exchange/brokerage)

---

## 📐 Formula Protection Rules

### NEVER TOUCH (Sacred Formulas)

These formulas are core to the spreadsheet's integrity and must NEVER be modified by agents:

1. **DataHub**:
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
- ✅ Fix broken sheet references (e.g., `Sheet1!A1` → `DataHub!A1`)
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
- [ ] **Column Check**: Am I only touching allowed columns? (DataHub = A, B, G only)
- [ ] **Data Source**: Is this data from authoritative Fidelity CSV or DataHub?
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
3. **Understand Data Flow** - Fidelity CSV → DataHub (A, B, G) → Apps Script → Recommendations
4. **Respect Formula Boundaries**:
   - **WRITABLE**: Columns A (Ticker), B (Quantity), G (Avg Cost Basis) from CSV
   - **SACRED**: Column C (Google Finance formulas), Columns D-F, H-S (calculated formulas)
5. **Use Safety Gates** - Stop and alert on mismatches, large changes (>10%), errors (3+)
6. **Apps Script Understanding** - Code.js, Dividend.js, Hedge.js, History.js handle optimization and data fetching
7. **Document Changes** - Log every write operation with timestamp and reasoning
8. **Ask Questions** - If architecture is unclear, ask Cassandra (Finance Orchestrator) or user

**Common Mistakes to Avoid**:
- ❌ Updating prices manually in DataHub (they're formula-calculated)
- ❌ Deleting positions without user confirmation (might be intentional sale)
- ❌ Changing layer classification without pattern-based logic
- ❌ Breaking formulas while "helping" fix them
- ❌ Creating backup tabs (Google handles this natively)
- ❌ Writing to Portfolio sheet without understanding Apps Script integration
- ❌ Running optimizer without first running History Data (for momentum/volatility scoring)

---

## 📅 Maintenance Schedule

**Daily**:
- Agents should READ-ONLY access for analysis (no writes)

**Weekly**:
- Check for new Fidelity CSV exports in `notebooks/updates/`
- If new CSV found, trigger Workflow 1 (Import to Active Portfolio)
- Run "History Data" to keep 90+ days of price history current

**Monthly**:
- Sync Dividend Tracker (Workflow 2) around ex-dividend dates
- Update Margin Dashboard (Workflow 3) after month-end Fidelity export
- **Update Retirement Accounts (Workflow 5)** from `notebooks/retirement-accounts/` CSVs
- Validate formula health (run Workflow 4 if errors detected)

**As Needed**:
- **Update Cryptocurrency (Workflow 6)** when user provides new quantity/price data
- Run "Deposit" optimization when new deposit arrives (Workflow 1 must complete first)
- Run "Hedge Analysis" quarterly or when market volatility spikes

**Quarterly**:
- Full spreadsheet audit by Compliance Officer
- Review layer classifications for any portfolio drift (active portfolio only)
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

**Last Updated**: 2025-11-12
**Version**: 1.2 (Added Apps Script Automation Layer section)
**Maintained by**: Finance Guru™ Finance Orchestrator (Cassandra Holt)
**Questions**: Route through Cassandra or ask user directly
