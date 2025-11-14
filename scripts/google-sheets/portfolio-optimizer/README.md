# Portfolio Optimizer - Apps Script Suite

**Version:** 1.0
**Script ID:** `1qE0sv8ABE7LpXpUXSdcGvckFF84MrjbxYm91LTEsHJZ5pYw5mPypoBUI`
**Timezone:** America/New_York
**Runtime:** V8

---

## 📋 Overview

A comprehensive Google Apps Script suite for portfolio optimization, dividend tracking, and hedging analysis. Designed for dividend-focused portfolios with multi-factor scoring algorithms, real-time dividend data fetching, and Black-Scholes options hedging.

**Primary Use Case:** Optimizing Layer 2 dividend income allocation across 11+ covered call ETFs and CEFs.

---

## 📂 File Structure

```
portfolio-optimizer/
├── Code.js          # Main portfolio allocation optimizer (36KB)
├── Dividend.js      # Real-time dividend data fetcher (18KB)
├── Hedge.js         # Black-Scholes hedge analysis (30KB)
├── Fire Model.js    # FIRE modeling calculations (8.6KB)
├── History.js       # Historical price data builder (2KB)
├── NAV Data.js      # NAV data operations (1.8KB)
└── README.md        # This file
```

---

## 🎯 Core Modules

### **1. Code.js - Portfolio Allocation Optimizer**

**Purpose:** Calculates optimal allocation of new deposits across dividend positions using multi-factor scoring.

#### **Features**
- ✅ **Dynamic column detection** - Works with flexible sheet layouts
- ✅ **12-factor scoring algorithm** - Combines yield, momentum, volatility, diversification
- ✅ **Cap management** - Prevents over-concentration (default 30% per position)
- ✅ **Core ticker prioritization** - Special allocation for high-conviction holdings
- ✅ **Mode-based allocation** - CORE vs. general diversification

#### **Custom Menu (Portfolio sheet)**
```
Portfolio Optimizer
├── Update Dividend Data   → Runs updateDividendDataFast()
├── History Data          → Runs buildHistory()
├── Deposit              → Runs findOptimalDividendFocusedMix()
└── Hedge Analysis        → Runs analyzeHedge()
```

#### **Required Columns (Row 2 headers)**
The script auto-detects columns with these patterns:

| Column Purpose | Header Patterns | Example |
|----------------|----------------|---------|
| Ticker | "ticker" | Ticker |
| Current Price | "price", "current price" | Current Price |
| Cost Basis | "cost basis" | Cost Basis |
| Shares Owned | "shares", "qty owned", "quantity" | Shares Owned |
| Shares to Buy (Output) | "share buy", "shares to buy", "out qty" | Shares to Buy |
| TTM Dividend | "ttm div", "dividend ttm", "annual div" | TTM Dividend |
| Manual Boost | "manual boost", "manual" | Manual Boost |
| Ex-Dividend Date | "ex dividend date", "ex date" | Ex-Dividend Date |
| Maintenance % | "maintenance", "maint" | Maintenance |

#### **Configuration (Row 1)**
- **Deposit Amount** - Cell with "deposit" label (or B1 fallback)
- **Allocation Mode** - Cell with "mode" label (or C1 fallback)
  - `CORE` - Prioritize core tickers
  - `PORTFOLIO-CAP` - Limit by total portfolio percentage
  - `DEPOSIT-CAP` - Limit by deposit percentage
  - `HYBRID` - Both caps enforced

#### **Scoring Components (12 factors)**

| Factor | Weight Key | Description | Normalization |
|--------|-----------|-------------|---------------|
| Cost Base | `costBase` | Buys underwater positions (1 if loss, 0 if gain) | No |
| Yield Boost | `yieldBoost` | Tiered yield scoring (8%→0.5, 6%→0.4, 4%→0.3, 2%→0.2, 1%→0.1) | Yes |
| Ex-Date Boost | `exBoost` | Proximity to ex-dividend date (28-day window) | No |
| Cost Boost | `costBoost` | Dividend efficiency (yield on price vs. cost basis) | Yes |
| Manual Boost | `manualBoost` | User override (set in Manual Boost column) | No |
| Mode Boost | `modeBoost` | CORE mode bonus for core tickers | No |
| Maintenance Boost | `maintBoost` | Margin maintenance favorability (≤30%→+0.5, ≥100%→-0.5) | No |
| Diversification | `diversificationBoost` | Under-allocated positions (<5% target) | Yes |
| Heavy Penalty | `heavyPenalty` | Over-allocated non-core positions (>10% threshold) | No |
| **Momentum** | `momentum` | 5-day MA vs 20-day MA (requires History sheet) | Yes |
| **Volatility** | `volatility` | Annualized std dev (requires History sheet) | Yes |
| **Sharpe-Yield** | `sharpeYield` | (Yield - RF) / Volatility (requires History sheet) | Yes |

**Normalization:** "Yes" = min-max scaled to [0,1], "No" = raw value used directly.

#### **Weights Sheet Configuration**

Create a sheet named `Weights` with two columns (no headers):

```
Key                    | Value
-----------------------|-------
CAP_PCT               | 0.3
CAP_MODE              | HYBRID
CORE_TICKERS          | CLM,CRF,GOF
YIELD_THRESHOLDS      | 8,6,4,2,1
YIELD_VALUES          | 0.5,0.4,0.3,0.2,0.1
HEAVY_THRESHOLD       | 0.10
CORE_RESERVE_MULTIPLIER| 1.0
costBase              | 5.0
yieldBoost            | 10.0
exBoost               | 3.0
costBoost             | 2.0
manualBoost           | 8.0
modeBoost             | 15.0
maintBoost            | 4.0
diversificationBoost  | 6.0
heavyPenalty          | -10.0
momentum              | 3.0
volatility            | -2.0
sharpeYield           | 5.0
```

**Weight Tuning Guide:**
- **Positive weights** → Higher score → More allocation
- **Negative weights** → Penalty → Less allocation
- Typical range: -10 to +15
- Start with defaults, adjust based on performance

---

### **2. Dividend.js - Real-Time Dividend Fetcher**

**Purpose:** Fetches live dividend data from web sources and populates dividend columns.

#### **Populates Columns**
- **Column I:** Days Until Ex-Date (or "ExDate" if today is ex-date)
- **Column K:** Days Until Pay Date (or "$$$$" if pay date today/past)
- **Column L:** Next Pay Amount (per-share × shares owned)
- **Column M:** Dividend Yield (TTM / Current Price)
- **Column G:** TTM Dividend (annual)

#### **Features**
- 🚀 **1-hour cache** - Reduces API calls (3600 sec TTL)
- ⏱️ **Rate limiting** - 150ms sleep between fetches
- 📅 **Cadence detection** - Weekly, 4-week, monthly, quarterly patterns
- 🎯 **Tolerance handling** - Manages irregular payment schedules

#### **Trigger**
- **Auto-runs** when cell `M1` is edited on Portfolio sheet
- **Manual run** via menu: "Update Dividend Data"

#### **Configuration**
```javascript
const DD_CFG = {
  SHEET_NAME: 'Portfolio',
  HEADER_ROW: 2,
  START_ROW: 3,
  CACHE_TTL_SEC: 3600,
  SLEEP_MS_BETWEEN_FETCHES: 150
};
```

---

### **3. Hedge.js - Black-Scholes Hedge Analysis**

**Purpose:** Calculates optimal put option hedge using Black-Scholes pricing model.

#### **Features**
- 📊 **Index coverage:** SPY, QQQ, IWM, DIA
- 💰 **Proxy ETFs:** SPLG, QQQM, VTWO, IYY (lower premium costs)
- 🧮 **Black-Scholes pricing** with implied volatility
- 📈 **Greeks calculation:** Delta, Gamma, Theta, Vega
- 📉 **VIX integration** - Reads from cell `M9` on Portfolio sheet
- 🎯 **Budget-based sizing** - Default 0.5% of portfolio value
- 🛡️ **Target drop protection** - Default 10% portfolio drawdown hedge

#### **Output Sheet: HedgeAnalysis**
Creates/updates a sheet with:
- Recommended put options (strike, expiry, quantity)
- Cost breakdown (premium, total hedge cost)
- Greeks (Delta, Gamma, Theta, Vega)
- Coverage analysis (expected protection at target drop)

#### **Configuration (HedgeAnalysis sheet, cells H1:H4)**
```
G1: Budget % of Portfolio    → H1: 0.5%    (0.005 as decimal)
G2: Target Portfolio Drop %   → H2: 10%     (0.10 as decimal)
G3: DTE (days)               → H3: 30      (days to expiration)
G4: Downside Weight          → H4: 1.0     (0-1 scale)
```

#### **Black-Scholes Assumptions**
- Risk-free rate: 3.0% annualized
- Dividend yields:
  - SPY: 1.4%, QQQ: 0.6%, IWM: 1.5%, DIA: 2.0%
  - SPLG: 1.4%, QQQM: 0.6%, VTWO: 1.5%, IYY: 1.8%

#### **Auto-Optimization Knobs**
```javascript
MIN_COVERAGE_AT_TARGET = 0.30;   // Minimum 30% coverage
STRIKE_TIGHTEN_FACTOR  = 0.9;    // Strike price adjustment
MIN_OTM_FRACTION       = 0.02;   // Minimum 2% out-of-the-money
```

#### **Trigger**
- **Manual run** via menu: "Hedge Analysis"

#### **Requirements**
- Portfolio sheet with positions
- History sheet with 90+ days of price data for indexes
- VIX value in cell M9 (Portfolio sheet)

---

### **4. History.js - Historical Data Builder**

**Purpose:** Builds historical price database for momentum and volatility calculations.

#### **Output Sheet: History**
Three-column structure:
```
Ticker | Date | Close
-------|------|------
PLTR   | 2025-10-01 | 72.50
PLTR   | 2025-10-02 | 73.15
```

#### **Usage**
- **Manual run** via menu: "History Data"
- Required for:
  - Momentum scoring (5-day vs 20-day MA)
  - Volatility scoring (annualized std dev)
  - Sharpe-Yield scoring (risk-adjusted yield)
  - Hedge analysis (index correlations)

#### **Minimum Requirements**
- 30 days minimum per ticker
- 90 days recommended for hedge analysis
- Date format: YYYY-MM-DD

---

### **5. Fire Model.js**

**Purpose:** Financial Independence Retire Early (FIRE) modeling calculations.

*Documentation pending - module not yet analyzed*

---

### **6. NAV Data.js**

**Purpose:** Net Asset Value operations for CEFs and ETFs.

*Documentation pending - module not yet analyzed*

---

## 🚀 Deployment Guide

### **Prerequisites**
1. Google Apps Script API enabled: [script.google.com/home/usersettings](https://script.google.com/home/usersettings)
2. Clasp CLI installed: `npm install -g @google/clasp`
3. Authenticated: `clasp login`

### **Initial Setup**
```bash
cd scripts/google-sheets/portfolio-optimizer/
clasp clone 1qE0sv8ABE7LpXpUXSdcGvckFF84MrjbxYm91LTEsHJZ5pYw5mPypoBUI
```

### **Development Workflow**
```bash
# Pull latest from Google
clasp pull

# Make local changes
# Edit Code.js, Dividend.js, etc.

# Push to Google
clasp push

# Watch mode (auto-push on save)
clasp push -w

# Open in Apps Script editor
clasp open
```

### **Deployment**
```bash
# Create new deployment
clasp deploy --description "v1.0 - Initial deployment"

# List deployments
clasp deployments

# Update existing deployment
clasp deploy --deploymentId <deployment-id> --description "v1.1 - Bug fixes"
```

---

## 📊 Google Sheets Setup

### **Required Sheets**

1. **Portfolio** (main data sheet)
   - Row 1: Configuration (Deposit amount, Mode)
   - Row 2: Column headers
   - Row 3+: Position data

2. **Weights** (scoring configuration)
   - Column A: Weight keys
   - Column B: Weight values
   - No headers, starts at row 1

3. **History** (historical prices - optional but recommended)
   - Column A: Ticker
   - Column B: Date
   - Column C: Close price
   - Header row required

4. **HedgeAnalysis** (auto-created by Hedge.js)
   - Output sheet for hedge recommendations

### **Example Portfolio Sheet Structure**

```
Row 1: [Deposit:] [$13,317] [Mode:] [HYBRID]
Row 2: [Ticker] [Current Price] [Cost Basis] [Shares Owned] [Shares to Buy] [TTM Dividend] [Manual Boost] [Ex-Dividend Date] [Maintenance] [Days Until Ex] [Days Until Pay] [Next Pay Amount] [Dividend Yield]
Row 3: [JEPI] [57.11] [56.42] [61.342] [] [5.89] [0] [2025-11-20] [30] [] [] [] []
Row 4: [JEPQ] [58.72] [58.08] [92.043] [] [6.84] [0] [2025-11-21] [30] [] [] [] []
...
```

---

## 🔧 Customization

### **Adding New Core Tickers**
Edit `CORE_TICKERS` in Weights sheet:
```
CORE_TICKERS | CLM,CRF,GOF,JEPI
```

### **Adjusting Position Caps**
```
CAP_PCT | 0.25    (25% max per position)
```

### **Changing Yield Thresholds**
```
YIELD_THRESHOLDS | 10,8,6,4,2
YIELD_VALUES     | 0.6,0.5,0.4,0.3,0.2
```

### **Tuning Weight Values**
Start with defaults, then:
- Increase weight → More allocation to that factor
- Decrease/negative → Penalize that factor
- Set to 0 → Ignore that factor

**Example: Prioritize yield over momentum**
```
yieldBoost | 15.0   (increase from 10.0)
momentum   | 1.0    (decrease from 3.0)
```

---

## 🐛 Troubleshooting

### **"Missing required column header" Error**
- Check row 2 headers match expected patterns
- Headers are case-insensitive
- Must include: Ticker, Price, Shares, TTM Dividend

### **"Not enough history" in Hedge Analysis**
- Run "History Data" from menu
- Ensure 90+ days of data for each ticker
- Check History sheet has 3 columns: Ticker, Date, Close

### **Dividend data not populating**
- Check cell M1 trigger (edit M1 to force refresh)
- Verify internet connectivity (script fetches from web)
- Check cache TTL (default 1 hour)

### **Allocation results seem wrong**
- Verify Weights sheet exists and is populated
- Check scoring component weights (positive vs negative)
- Review Weights sheet output (rows 20+) for boost breakdown

---

## 📈 Integration with Finance Guru™

This Apps Script suite is designed to complement your Finance Guru™ Layer 2 dividend income strategy:

- **Portfolio Positions sheet** → Primary data source
- **Dividend Tracker sheet** → Enhanced by Dividend.js output
- **Margin Dashboard** → Uses Maintenance % column
- **Layer 2 tickers** → Optimized allocation via Code.js
- **Layer 3 hedging** → Calculated by Hedge.js

---

## 📝 Version History

**v1.0** (2025-11-12)
- Initial deployment
- Core optimizer with 12-factor scoring
- Real-time dividend fetching
- Black-Scholes hedge analysis
- Historical data builder

---

## 🔗 Links

- **Apps Script Editor:** [script.google.com](https://script.google.com/home/projects/1qE0sv8ABE7LpXpUXSdcGvckFF84MrjbxYm91LTEsHJZ5pYw5mPypoBUI/edit)
- **Google Sheets:** [Portfolio Tracker](https://docs.google.com/spreadsheets/d/1HtHRP3CbnOePb8RQ0RwzFYOQxk0uWC6L8ZMJeQYfWk4/edit)
- **Clasp Documentation:** [developers.google.com/apps-script/guides/clasp](https://developers.google.com/apps-script/guides/clasp)

---

**Last Updated:** 2025-11-12
**Maintained by:** Finance Guru™ Builder (Alexandra Kim)
