# Finance Guru™ 15-Tab Architecture Overview

**Document Purpose:** Complete visual guide to the 15-tab Google Sheets structure, data flows, and Apps Script integration

**Spreadsheet ID:** `1HtHRP3CbnOePb8RQ0RwzFYOQxk0uWC6L8ZMJeQYfWk4`

**Last Updated:** 2025-11-12

---

## 📐 System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FINANCE GURU™ SPREADSHEET ECOSYSTEM                      │
└─────────────────────────────────────────────────────────────────────────────┘

    ZONE 1: DATAHUB (Master Source - Finance Guru Writes)
    ┌──────────────────────────────────────────────────────────────┐
    │ DataHub (1039 rows × 19 columns)                             │
    │ ├─ Rows 2-40: Active Portfolio (Fidelity TOD)                │
    │ ├─ Rows 45-64: Retirement Accounts (Vanguard + 401k)         │
    │ └─ Rows 67+: Cryptocurrency Holdings                         │
    │                                                               │
    │ Authoritative Columns: A (Ticker), B (Qty), G (Cost Basis)   │
    │ Formula Columns: C (Price), D-E (Changes), H-S (Gains/Divs)  │
    └──────────────────────────────────────────────────────────────┘
                              │
                              │ (Feeds all 14 other tabs)
                              ↓
    ┌─────────────────────────────────────────────────────────────┐
    │     ZONE 2: APPS SCRIPT WORKSPACE (9 operational tabs)       │
    ├─────────────────────────────────────────────────────────────┤
    │                                                               │
    │  1. Portfolio (Main Optimizer Hub)                           │
    │     ├─ Read from: DataHub (Layer 2 dividend tickers)         │
    │     ├─ Reads from: DataHub Column A (Ticker)                 │
    │     ├─ Columns: Ticker, Current Price, Cost Basis, Shares    │
    │     │            Shares to Buy, TTM Dividend, Manual Boost    │
    │     │            Days Until Ex-Date, Yield %, Maintenance %   │
    │     ├─ Output: "Shares to Buy" recommendations (Col F)        │
    │     └─ Scripts: Code.js (optimizer), Dividend.js (fetcher)   │
    │                                                               │
    │  2. Weights (Configuration Sheet)                            │
    │     ├─ Purpose: Scoring algorithm parameters (16 weights)    │
    │     ├─ Format: 2-column (Key | Value)                        │
    │     ├─ Examples: CAP_PCT, CORE_TICKERS, yield thresholds     │
    │     └─ Updates: User adjusts weights to tune optimizer       │
    │                                                               │
    │  3. History (Technical Data Foundation)                      │
    │     ├─ Format: Ticker | Date | Close Price (90+ days)        │
    │     ├─ Purpose: Momentum, volatility, Sharpe-Yield scoring   │
    │     ├─ Populated by: History.js (via "History Data" menu)    │
    │     └─ Updated: Weekly or before hedge analysis              │
    │                                                               │
    │  4. HedgeAnalysis (Put Option Recommendations)               │
    │     ├─ Inputs: Portfolio value, target drop %, budget %      │
    │     ├─ Calculation: Black-Scholes put pricing (Hedge.js)     │
    │     ├─ Outputs: Strike price, expiry, quantity, cost, Greeks │
    │     ├─ Indices covered: SPY, QQQ, IWM, DIA                   │
    │     └─ Proxies: SPLG, QQQM, VTWO, IYY (lower premium)        │
    │                                                               │
    │  5. Dividends (Real-time Dividend Tracking)                  │
    │     ├─ Format: Fund | Shares | Annual Dividend | Ex-Date     │
    │     ├─ Populated by: Dividend.js (fetches live web data)     │
    │     ├─ Columns: Days Until Pay, Pay Amount, Dividend Yield   │
    │     └─ Auto-refreshes: When cell M1 edited on Portfolio tab  │
    │                                                               │
    │  6. FIRE Model (28-Month Projections)                        │
    │     ├─ Purpose: Financial independence projections            │
    │     ├─ Inputs: Dividend income, margin strategy, reinvest %  │
    │     ├─ Projection: 28 months cash flow to "break-even"       │
    │     ├─ Calculated by: FireModel.js                           │
    │     └─ Trigger: "Analyze" button on FIRE Model sheet         │
    │                                                               │
    │  7. Budget Planner (Expense Coverage Tracking)               │
    │     ├─ Purpose: Match expenses to dividend/income streams     │
    │     ├─ Input: Monthly expenses, dividend amounts             │
    │     ├─ Output: Coverage analysis, deposit needed             │
    │     └─ Feeds: FIRE Model calculations                        │
    │                                                               │
    │  8. Expense Tracker (Transaction Log)                        │
    │     ├─ Purpose: Daily/monthly expense ledger                 │
    │     ├─ Columns: Date, Category, Amount, Notes                │
    │     ├─ Categories: Must match Budget Planner                 │
    │     └─ Feeds: Budget Planner summaries                       │
    │                                                               │
    │  9. Option Tracker (Options ROI Record)                      │
    │     ├─ Purpose: Track covered call/put execution impact      │
    │     ├─ Columns: Strike, Expiry, Premium, Assignment status   │
    │     └─ Feeds: Portfolio optimization feedback                │
    │                                                               │
    └─────────────────────────────────────────────────────────────┘
                              │
                              │ (Read-only from DataHub)
                              ↓
    ┌─────────────────────────────────────────────────────────────┐
    │  ZONE 3: ANALYTICS & TRACKING (5 reporting tabs)             │
    ├─────────────────────────────────────────────────────────────┤
    │                                                               │
    │  10. Dividend Tracker (OLD - Being Phased Out)               │
    │      ⚠️  DEPRECATED: Being replaced by Dividends tab (tab 5) │
    │      Status: Marked for deletion after migration complete    │
    │                                                               │
    │  11. Margin Dashboard (Interest & Coverage Metrics)          │
    │      ├─ Purpose: Track margin usage, leverage, risk ratios   │
    │      ├─ Columns: Date, Balance, Interest Rate, Monthly Cost  │
    │      ├─ Calculates: Portfolio-to-Margin ratio, Coverage      │
    │      ├─ Safety Gates: >$5k jump alert, margin tracking       │
    │      └─ Status: Active - Agent writes, no workflows yet      │
    │                                                               │
    │  12. Cash Flow Monitor (Deposit/Withdrawal Ledger)           │
    │      ├─ Purpose: Track deposits, withdrawals, transfers      │
    │      ├─ Columns: Date, Type, Amount, Account, Notes          │
    │      └─ Status: Paused - Workflows to be defined             │
    │                                                               │
    │  13. Weekly Review (Performance Summaries)                   │
    │      ├─ Purpose: Auto-generated weekly snapshots             │
    │      ├─ Columns: Date, P&L %, Holdings Changed, Top Movers   │
    │      ├─ Future: LLM-generated narrative summaries             │
    │      └─ Status: Paused - Manual entry only currently         │
    │                                                               │
    │  14. Bitcoin Enhanced Growth - Friend (Special Tracking)     │
    │      ├─ Purpose: Track shared Bitcoin investment             │
    │      ├─ Status: READ-ONLY (external data)                    │
    │      └─ Not part of active portfolio analysis                │
    │                                                               │
    └─────────────────────────────────────────────────────────────┘

    LEGEND:
    ─────────────────
    Zone 1 = Master data source (Finance Guru writes from Fidelity CSV)
    Zone 2 = Active optimization (Apps Script automation, user workflows)
    Zone 3 = Reporting & analytics (tracking only, mostly paused)
```

---

## 🔄 Data Flow: Fidelity CSV → DataHub → Portfolio → Recommendations

```
┌─────────────────────────────────────┐
│  FIDELITY CSV EXPORT                │
│  (notebooks/updates/)               │
│                                     │
│  Portfolio_Positions_MMM-DD.csv     │
│  ├─ Symbol (PLTR, JEPI, CLM, etc)  │
│  ├─ Quantity (100, 50, 25 shares)   │
│  ├─ Avg Cost Basis ($71.50, etc)    │
│  └─ Updated: ~weekly                │
└──────────────────┬──────────────────┘
                   │
                   │ Finance Guru Import
                   │ (Builder Agent)
                   ↓
┌─────────────────────────────────────┐
│  DATAHUB (Master Holdings Tracker)  │
│                                     │
│  Row 1: Headers                     │
│  Rows 2-40: Active Portfolio        │
│  ├─ Column A: Ticker Symbol         │
│  ├─ Column B: Quantity (from CSV)   │
│  ├─ Column C: Last Price (Formula)  │
│  │   =GOOGLEFINANCE(A{row},"price") │
│  ├─ Columns D-E: Price Changes      │
│  ├─ Column G: Cost Basis (from CSV) │
│  ├─ Columns H-M: Gain/Loss calcs    │
│  ├─ Column S: Layer (1/2/3)         │
│  └─ Auto-refreshes: During trading  │
│                                     │
│  Rows 45-64: Retirement (read-only) │
│  Rows 67+: Cryptocurrency (manual)  │
└──────────────────┬──────────────────┘
                   │
                   │ References
                   │ (Formulas pull from DataHub)
                   ↓
┌─────────────────────────────────────┐
│  PORTFOLIO TAB (Apps Script Hub)    │
│                                     │
│  Row 1: Configuration               │
│  ├─ Deposit Amount (e.g., $13,317)  │
│  └─ Mode (CORE, HYBRID, etc)        │
│                                     │
│  Row 2: Column Headers              │
│  ├─ Ticker (=DataHub!A{row})        │
│  ├─ Current Price (fetched live)    │
│  ├─ Cost Basis (=DataHub!G{row})    │
│  ├─ Shares Owned (=DataHub!B{row})  │
│  ├─ TTM Dividend (fetched by code)  │
│  ├─ Manual Boost (user override)    │
│  ├─ Maintenance % (from DataHub)    │
│  ├─ Days Until Ex-Date (calculated) │
│  └─ Days Until Pay Date             │
│                                     │
│  Row 3+: Layer 2 dividend tickers   │
│  ├─ JEPI, JEPQ, CLM, CRF, GOF,etc  │
│  └─ Only dividend-focused positions │
│                                     │
│  Column F Output: Shares to Buy     │
│  ├─ Formula: =Code.js algorithm     │
│  ├─ Updates: When "Deposit" clicked │
│  └─ Shows: Recommended buy shares   │
│                                     │
│  Cell F1: Estimated Monthly Income  │
│  └─ With proposed allocation        │
└──────────────────┬──────────────────┘
                   │
                   │ Scripts Calculate
                   │ (12-factor scoring)
                   ↓
┌─────────────────────────────────────┐
│  OPTIMIZATION CALCULATIONS          │
│  (Code.js in Apps Script)           │
│                                     │
│  12-Factor Scoring Algorithm:       │
│  ├─ 1. Cost Base (value buying)     │
│  ├─ 2. Yield Boost (high income)    │
│  ├─ 3. Ex-Date Boost (timing)       │
│  ├─ 4. Cost Boost (efficiency)      │
│  ├─ 5. Manual Boost (user override) │
│  ├─ 6. Mode Boost (CORE priority)   │
│  ├─ 7. Maintenance Boost (margin)   │
│  ├─ 8. Diversification (balance)    │
│  ├─ 9. Heavy Penalty (over-alloc)   │
│  ├─ 10. Momentum (5 vs 20-day MA)   │
│  ├─ 11. Volatility (annualized)     │
│  └─ 12. Sharpe-Yield (risk-adj)     │
│                                     │
│  Weights Applied (from Weights tab) │
│  └─ User-configurable factors       │
│                                     │
│  Cap Enforcement:                   │
│  ├─ Max position size (default 30%) │
│  ├─ Respect deposit cap             │
│  └─ Prevent over-concentration      │
└──────────────────┬──────────────────┘
                   │
                   │ Outputs
                   ↓
┌─────────────────────────────────────┐
│  RESULTS (Column F - Portfolio tab) │
│                                     │
│  ├─ JEPI: Buy 234 shares ($13,317)  │
│  ├─ JEPQ: Buy 227 shares            │
│  ├─ CLM: Buy 189 shares             │
│  ├─ CRF: Buy 0 shares (at cap)       │
│  └─ GOF: Buy 45 shares              │
│                                     │
│  F1: Monthly income = +$847/month   │
│      (with proposed allocation)     │
│                                     │
│  User Decision:                     │
│  ├─ Execute suggested buys?         │
│  ├─ Adjust deposit amount?          │
│  ├─ Change mode or weights?         │
│  └─ Update DataHub with final qty   │
└─────────────────────────────────────┘
```

---

## 🎯 Apps Script Integration Layer

### Custom Menu (Portfolio Tab)

When user opens Portfolio sheet, Apps Script adds custom menu:

```
Portfolio Optimizer ▼
├─ Update Dividend Data     → Runs Dividend.js (fetches live dividend data)
├─ History Data             → Runs History.js (builds 90-day price history)
├─ Deposit                  → Runs Code.js (calculates optimal allocation)
└─ Hedge Analysis           → Runs Hedge.js (calculates put hedges)
```

### Triggers (Automation)

**onOpen() Trigger:**
- Fires when user opens Portfolio sheet
- Adds custom menu (Portfolio Optimizer)
- Loads configuration from Weights sheet
- Initializes data cache

**onEdit(e) Trigger:**
- Watches cell M1 on Portfolio sheet
- When cell M1 is edited → Triggers `updateDividendDataFast()`
- Automatically refreshes dividend data without manual menu click
- Caches results for 1 hour (to avoid API rate limits)

---

## 📊 Apps Script Modules & Workflows

### 1. Code.js - Portfolio Allocation Optimizer

**Primary Function:** `findOptimalDividendFocusedMix()`

**When User Clicks "Deposit":**

1. Reads deposit amount from Portfolio sheet cell B1
2. Reads allocation mode from cell C1 (CORE/HYBRID/etc)
3. Reads all positions from Portfolio rows 3+
4. Fetches weights from Weights sheet (16 parameters)
5. Loads historical data from History sheet (if available)
6. Calculates 12-factor score for each position
7. Applies position caps (max 30% per position)
8. Allocates deposit amount proportionally to scores
9. Writes recommended share counts to Column F (Shares to Buy)
10. Updates cell F1 with estimated monthly income impact

**Configuration (Row 1, Portfolio tab):**
| Cell | Label | Purpose | Example |
|------|-------|---------|---------|
| B1 | Deposit | Amount to allocate | $13,317 |
| C1 | Mode | Allocation strategy | HYBRID |
| M9 | VIX | Market volatility (info only) | 14.2 |

**Configuration (Weights Sheet - 2 columns, no headers):**

```
CAP_PCT                  | 0.30        (max 30% per position)
CAP_MODE                 | HYBRID      (hybrid cap enforcement)
CORE_TICKERS             | CLM,CRF,GOF (high-conviction names)
YIELD_THRESHOLDS         | 8,6,4,2,1   (yield breakpoints)
YIELD_VALUES             | 0.5,0.4,0.3,0.2,0.1
HEAVY_THRESHOLD          | 0.10        (over-allocation penalty)
CORE_RESERVE_MULTIPLIER  | 1.0         (CORE boost factor)
costBase                 | 5.0         (value buying weight)
yieldBoost               | 10.0        (dividend yield weight)
exBoost                  | 3.0         (ex-date proximity weight)
costBoost                | 2.0         (yield efficiency weight)
manualBoost              | 8.0         (user override weight)
modeBoost                | 15.0        (CORE mode weight)
maintBoost               | 4.0         (margin maintenance weight)
diversificationBoost     | 6.0         (under-allocated boost)
heavyPenalty             | -10.0       (over-allocation penalty)
momentum                 | 3.0         (5-day vs 20-day MA)
volatility               | -2.0        (penalize high vol)
sharpeYield              | 5.0         (risk-adjusted yield)
```

**Output Format (Column F - Portfolio tab):**
```
Row 1: [F1] = Estimated monthly income ($847)
Row 2: [F2] = Header "Shares to Buy"
Row 3+: [F3], [F4], etc = Share counts to purchase
         Color: Blue cell = recommended action
                Empty cell = no action needed
                0 = position at cap (don't buy)
```

---

### 2. Dividend.js - Real-Time Dividend Data Fetcher

**Primary Function:** `updateDividendDataFast()`

**When User Clicks "Update Dividend Data":**

1. Reads all tickers from Portfolio sheet (Column A, rows 3+)
2. Fetches live dividend data from web sources
3. Calculates days until ex-dividend date
4. Calculates days until pay date
5. Populates dividend columns (I, K, L, M, G)
6. Caches results for 1 hour (to limit API calls)
7. Sleeps 150ms between fetches (API rate limit)

**Auto-Trigger (onEdit):**
- When user edits cell M1 (Portfolio tab) → Automatically triggers `updateDividendDataFast()`
- No manual menu click needed

**Columns Populated (Portfolio tab):**

| Column | Header | Purpose | Example |
|--------|--------|---------|---------|
| G | TTM Dividend | Annual dividend | $5.89 |
| I | Days Until Ex | Days to ex-dividend | 8 |
| K | Days Until Pay | Days to payment | 15 |
| L | Next Pay Amount | Per-share × shares | $362.50 |
| M | Dividend Yield | TTM / Current Price | 10.3% |

**Configuration (Portfolio sheet, cell M1):**
- Edit this cell to trigger dividend refresh
- Can contain any value (e.g., "Refresh", timestamp, etc)
- Useful for forcing update without using menu

---

### 3. Hedge.js - Black-Scholes Put Hedge Analysis

**Primary Function:** `analyzeHedge()`

**When User Clicks "Hedge Analysis":**

1. Reads portfolio total value from DataHub
2. Reads hedge configuration from HedgeAnalysis sheet
3. Fetches 90+ days of index price data (SPY, QQQ, IWM, DIA)
4. Calculates index volatility (annualized)
5. Calculates optimal put strike price
6. Prices put using Black-Scholes model
7. Calculates Greeks (Delta, Gamma, Theta, Vega)
8. Outputs hedge recommendations to HedgeAnalysis sheet
9. Shows expected protection at target portfolio drop %

**Configuration (HedgeAnalysis sheet, cells H1-H4):**

| Cell | Label (G) | Default | Purpose |
|------|-----------|---------|---------|
| H1 | Budget % | 0.5% | Max % of portfolio for hedge cost |
| H2 | Target Drop % | 10% | Expected portfolio decline to hedge |
| H3 | DTE (days) | 30 | Days to option expiration |
| H4 | Downside Weight | 1.0 | Coverage intensity (0-1 scale) |

**Output (HedgeAnalysis sheet):**

```
Row 1: [G1] Budget % | [H1] 0.5%
Row 2: [G2] Target Drop % | [H2] 10%
Row 3: [G3] DTE | [H3] 30
Row 4: [G4] Downside Weight | [H4] 1.0

Recommendations:
├─ Index: SPY (or QQQ depending on portfolio)
├─ Strike: $575.00 (out-of-the-money)
├─ Expiry: 2025-12-12 (30 days)
├─ Quantity: 12 contracts
├─ Premium Cost: $4,200 (0.5% of $840k portfolio)
├─ Protection: 95% of portfolio covered at -10% drop
└─ Greeks:
   ├─ Delta: -0.45 (moves -$0.45 per $1 drop)
   ├─ Gamma: 0.002
   ├─ Theta: -$12/day (decay)
   └─ Vega: $250/vol point
```

**Indices Supported:**
- Primary: SPY, QQQ, IWM, DIA
- Proxy (lower cost): SPLG, QQQM, VTWO, IYY

---

### 4. History.js - Historical Price Data Builder

**Primary Function:** `buildHistory()`

**When User Clicks "History Data":**

1. Reads all tickers from Portfolio sheet
2. Fetches 90+ days of daily close prices
3. Stores in History sheet format: Ticker | Date | Close
4. Used by other scripts for:
   - Momentum scoring (5-day vs 20-day MA)
   - Volatility scoring (annualized std dev)
   - Sharpe-Yield scoring (risk-adjusted returns)
   - Hedge analysis (index correlations)

**Output Format (History sheet):**

```
Row 1: [Headers] Ticker | Date | Close
Row 2+:
  PLTR | 2025-10-01 | 72.50
  PLTR | 2025-10-02 | 73.15
  PLTR | 2025-10-03 | 72.80
  ...
  JEPI | 2025-10-01 | 57.25
  JEPI | 2025-10-02 | 57.42
  ...
```

**Requirements:**
- Minimum 30 days per ticker
- 90 days recommended (for hedge analysis)
- Date format: YYYY-MM-DD
- Must include market-traded days only

---

### 5. Fire Model.js - 28-Month Projection Calculator

**Primary Function:** `calculateFireModel()`

**When User Clicks "Analyze" on FIRE Model tab:**

1. Reads current portfolio value from DataHub
2. Reads monthly dividend income from Dividends tab
3. Reads margin interest cost from Portfolio tab (G25)
4. Reads monthly expenses from Budget Planner tab
5. Reads reinvestment percentage
6. Projects 28 months forward month-by-month
7. Calculates breakeven point (dividends cover all expenses)
8. Shows cash flow runway and portfolio growth

**Key Assumptions:**
- Dividend growth: 2% annually
- Margin interest: 10.875% (or user-entered rate)
- Expense growth: 1% annually
- Position allocations: Static (no rebalancing)

**Output (FIRE Model sheet):**

```
Month  | Dividends | Expenses | Margin Int | Net Cash | Portfolio Value
-------|-----------|----------|------------|----------|----------------
0      | $3,200    | $4,500   | $625       | -$1,925  | $840,000
1      | $3,215    | $4,545   | $625       | -$1,955  | $842,000
...
28     | $3,800    | $4,500   | $0         | +$300    | $1,050,000 (GOAL)
```

---

### 6. NAV Data.js - Net Asset Value Operations

**Purpose:** Helper functions for CEF/ETF NAV data retrieval

**Functions:**
- `fetchNAV(ticker)` - Get NAV for closed-end fund
- `calculatePremiumDiscount()` - Market price vs NAV
- `fetchHistoricalNAV()` - NAV time series for analysis

*Used by hedge analysis and performance tracking*

---

## 🔗 Key Data Relationships & Formulas

### DataHub → Portfolio Sheet Reference Formula

**Portfolio sheet, Column A (Ticker):**
```
=FILTER(DataHub!A2:A40, DataHub!S2:S40="Layer 2 - Dividend")
```
(Pulls only dividend positions from DataHub)

**Portfolio sheet, Column C (Current Price):**
```
=ARRAYFORMULA(
  IF(ROW(A3:A100)=ROW(A3:A),
    VLOOKUP(A3:A100, DataHub!A:C, 3, FALSE),
    ""
  )
)
```
(Dynamically looks up current prices from DataHub)

**Portfolio sheet, Column G (Cost Basis):**
```
=VLOOKUP(A3, DataHub!A:G, 7, FALSE)
```
(Syncs cost basis from DataHub)

---

## 🚀 Workflow Summary: User Actions & Triggers

### Daily Workflow

```
USER ACTION                 → SCRIPT TRIGGERED              → OUTPUT
────────────────────────────────────────────────────────────────────
1. Open Portfolio sheet    → onOpen()                       → Menu appears
                           → Loads Weights config
                           → Initializes cache

2. Edit cell M1           → onEdit() monitors M1           → Dividend.js runs
   (e.g., type "Refresh")  → updateDividendDataFast()       → Columns G,I,K,L,M populate

3. Review dividend data   → Manual inspection              → User sees latest yields,
                           → Compare with portfolio targets  ex-dates, pay dates

4. Enter deposit amount   → User updates B1                → Portfolio updates
   in cell B1              → (no script runs yet)            → Price lookups refresh
```

### Weekly Workflow

```
USER ACTION                 → SCRIPT TRIGGERED              → OUTPUT
────────────────────────────────────────────────────────────────────
1. Click menu item         → onOpen() added menu items     → "History Data" ready
   "History Data"          → buildHistory()                 → History sheet populates
                           → Fetches 90 days               → With 90+ days price data

2. Review history          → Manual inspection              → Momentum/volatility
                           → Check for gaps/errors          → calculations enabled
```

### Monthly Workflow (Deposit Optimization)

```
USER ACTION                 → SCRIPT TRIGGERED              → OUTPUT
────────────────────────────────────────────────────────────────────
1. New deposit arrives     → User enters amount in B1      →

2. Click "Deposit" menu    → findOptimalDividendFocusedMix()→ Column F populates
                           → Reads Weights config          → With share buy amounts
                           → 12-factor scoring runs        → F1 shows monthly income
                           → Applies position caps         → impact

3. Review recommendation   → User inspects Column F        → Blue cells = actions
   in Column F             → (no script runs)               → 0 or empty = skip

4. Accept/adjust           → User updates DataHub manually  → Finance Guru tracks
                           → (outside Apps Script)          → New positions
                           → Or reject and run again

5. Next month: repeat      → History sheet updates         → New month scores
```

### Quarterly Workflow (Hedge Analysis)

```
USER ACTION                 → SCRIPT TRIGGERED              → OUTPUT
────────────────────────────────────────────────────────────────────
1. Review portfolio risk   → User opens HedgeAnalysis tab  → Configuration visible

2. Adjust hedge config     → User updates H1-H4            →
   (budget %, target drop) → (no script runs yet)

3. Click "Hedge Analysis"  → analyzeHedge()               → HedgeAnalysis sheet
   menu item               → Fetches index data (90 days)   → Shows put recommendations
                           → Calculates Black-Scholes      → With Greeks
                           → Sizes position to budget      → And coverage %

4. Review put options      → User inspects output          → Decides to hedge or wait
                           → (no script runs)
```

---

## 🔐 Data Write Boundaries (Apps Script vs User)

**Apps Script is ALLOWED to write to:**
- Portfolio sheet: Columns F (Shares to Buy), calculated helper columns
- Dividends sheet: Columns with fetched data (ex-date, pay-date, amounts)
- HedgeAnalysis sheet: Recommendation output
- History sheet: Historical price data
- FIRE Model sheet: Projection calculations

**Apps Script is FORBIDDEN from writing to:**
- DataHub: Only Finance Guru agent writes (Fidelity CSV import)
- Weights sheet: Only user configures
- Budget Planner/Expense Tracker: Only user enters

**User is allowed to edit (anywhere):**
- Manual Boost column (Portfolio sheet, Column N)
- Deposit amount (B1)
- Allocation mode (C1)
- All configuration cells in Weights sheet

---

## ⚠️ Critical Guardrails

### Before Running Code.js (Deposit Optimizer)

✅ Checklist:
- [ ] History sheet has 90+ days of data (run "History Data" first if not)
- [ ] Weights sheet exists and is populated
- [ ] Portfolio sheet row 2 has correct headers
- [ ] Portfolio sheet rows 3+ have valid tickers
- [ ] Deposit amount > 0 in cell B1
- [ ] DataHub current prices are fresh (updated during market hours)

### Before Running Hedge.js (Hedge Analysis)

✅ Checklist:
- [ ] History sheet has 90+ days of index data (SPY, QQQ, IWM, or DIA)
- [ ] Portfolio sheet row 2 has correct headers
- [ ] Portfolio positions are current
- [ ] VIX value entered in cell M9 (Portfolio sheet)
- [ ] HedgeAnalysis sheet exists
- [ ] Budget % and Target Drop % reasonable (H1-H2)

---

## 📈 Performance Metrics & Monitoring

### Key Indicators (Portfolio Sheet)

| Metric | Source | Refresh | Purpose |
|--------|--------|---------|---------|
| Avg Yield | Portfolio Col M | When "Update Dividend Data" | Monitor income potential |
| Days to Ex-Date | Portfolio Col I | When "Update Dividend Data" | Time dividend distributions |
| Monthly Income (F1) | Code.js output | When "Deposit" clicked | Project income post-allocation |
| Allocation Score | Code.js calc | When "Deposit" clicked | Quality of recommendations |

### Key Indicators (Margin Dashboard)

| Metric | Source | Refresh | Purpose |
|--------|--------|---------|---------|
| Margin Balance | Fidelity CSV import | Weekly (manual) | Track leverage |
| Coverage Ratio | Formula (Div÷Interest) | When dividend sync | Check income sufficiency |
| Portfolio-to-Margin | Calculated | When margin updated | Monitor leverage risk |

### Key Indicators (FIRE Model)

| Metric | Source | Refresh | Purpose |
|--------|--------|---------|---------|
| Months to Breakeven | FIRE Model.js | When "Analyze" clicked | Track progress to goal |
| Dividend Sufficiency | Month-by-month | When "Analyze" clicked | When income > expenses |
| Portfolio Growth Path | 28-month projection | When "Analyze" clicked | Wealth trajectory |

---

## 🎯 Next Steps: Paused Workflows

**These tabs exist but have NO automation workflows yet:**

1. **Margin Dashboard**
   - Status: Manual entry only
   - Next: Define escalation rules for Month 6/12/18 alerts
   - Responsible: Margin Specialist agent

2. **Cash Flow Monitor**
   - Status: Paused - no workflows defined
   - Next: Define deposit/withdrawal tracking rules
   - Responsible: Builder agent

3. **Weekly Review**
   - Status: Manual entry only
   - Next: Create LLM-powered narrative generation
   - Responsible: Teaching Specialist agent

4. **Budget Planner & Expense Tracker**
   - Status: Core tabs exist
   - Next: Connect to FIRE Model (partial connection exists)
   - Responsible: Finance Guru core team

---

## 📚 Integration with Finance Guru™ Agents

This Apps Script suite integrates with Finance Guru agent network:

| Agent | Interaction | Responsibilities |
|-------|-------------|------------------|
| **Finance Orchestrator** (Cassandra) | Coordinates script execution | Decides when to run optimization, hedge analysis |
| **Builder** | Maintains Apps Script code | Updates modules, deploys changes, fixes bugs |
| **Quant Analyst** | Interprets results | Reviews scoring breakdown, suggests weight adjustments |
| **Strategy Advisor** | Uses recommendations | Makes final allocation decisions, manages cash |
| **Margin Specialist** | Monitors leveraging | Reviews margin dashboard, enforces leverage limits |
| **Dividend Specialist** | Tracks income | Uses Dividends tab, syncs with Budget Planner |
| **Compliance Officer** | Audits rules | Verifies allocation caps, position limits, hedge coverage |

---

**Document Version:** 1.0
**Last Updated:** 2025-11-12
**Maintained by:** Finance Guru™ Doc Curator
