---
name: retirement-syncing
description: Sync retirement account data from Vanguard and Fidelity CSV exports to Google Sheets DataHub. Handles multiple accounts, aggregates holdings by ticker, and updates quantities in retirement section (rows 46-62). Triggers on sync retirement, update retirement, vanguard sync, 401k update, IRA sync, or working with notebooks/retirement-accounts/ files.
---

# Retirement Account Syncing

## Purpose

Safely import Vanguard and Fidelity retirement account CSV exports into the Google Sheets DataHub retirement section, updating only quantities (Column B).

## When to Use

Use this skill when:
- Syncing retirement account positions from `notebooks/retirement-accounts/`
- User mentions: "sync retirement", "update retirement", "vanguard sync", "401k update", "IRA sync"
- Working with files in `notebooks/retirement-accounts/` directory

## Source Files

**Location**: `notebooks/retirement-accounts/`

| File | Source | Contents |
|------|--------|----------|
| `OfxDownload.csv` | Vanguard IRAs | Account 39321600 & 35407271 holdings |
| `OfxDownload (1).csv` | Vanguard Brokerage | Account 53527429 & 50580939 holdings |
| `Portfolio_Positions_*.csv` | Fidelity 401(k) | {employer_name} 401(k) Plan holdings |

## CSV Formats

### Vanguard OFX Format (OfxDownload.csv)
```csv
Account Number,Investment Name,Symbol,Shares,Share Price,Total Value,
39321600,VANGUARD S&P 500 INDEX ETF,VOO,18.1817,629.3,11441.74,
```

**Key Fields:**
- Column 3: Symbol
- Column 4: Shares (quantity)

### Fidelity 401k Format (Portfolio_Positions_*.csv)
```csv
Account Number,Account Name,Symbol,Description,Quantity,Last Price,...
86689,{employer_name} 401(K) PLAN,FGCKX,FID GROWTH CO K,4.447,$50.04,...
```

**Key Fields:**
- Column 3: Symbol
- Column 5: Quantity

## DataHub Target Location

**Spreadsheet ID**: Read from `fin-guru/data/user-profile.yaml`

**Retirement Section**: Rows 46-62 (after the "RETIREMENT ACCOUNTS (VANGUARD)" header at row 45)

| Row | Ticker | Description |
|-----|--------|-------------|
| 46 | VOO | Vanguard S&P 500 ETF |
| 47 | VUG | Vanguard Growth ETF |
| 48 | VTSAX | Vanguard Total Stock Market |
| 49 | SCHG | Schwab US Large-Cap Growth |
| 50 | PLTR | Palantir |
| 51 | NVDA | NVIDIA |
| 52 | TSLA | Tesla |
| 53 | VB | Vanguard Small-Cap ETF |
| 54 | ARKK | ARK Innovation |
| 55 | VMFXX | Vanguard Money Market |
| 56 | FGCKX | Fidelity Growth Company K |
| 57 | FXAIX | Fidelity 500 Index |
| 58-62 | Reserved | Future holdings |

## Core Workflow

### 1. Read All CSV Files

```python
# Read Vanguard files
vanguard_1 = read_csv("notebooks/retirement-accounts/OfxDownload.csv")
vanguard_2 = read_csv("notebooks/retirement-accounts/OfxDownload (1).csv")

# Read latest Fidelity file (by date in filename)
fidelity = read_csv("notebooks/retirement-accounts/Portfolio_Positions_*.csv")
```

### 2. Aggregate Holdings by Ticker

Since the same ticker can appear in multiple accounts, **SUM** all quantities:

```python
holdings = {}
for file in [vanguard_1, vanguard_2, fidelity]:
    for row in file:
        ticker = row['Symbol']
        shares = float(row['Shares'] or row['Quantity'])
        holdings[ticker] = holdings.get(ticker, 0) + shares
```

**Expected Aggregations:**
- VOO: Sum across accounts (IRA + Brokerage)
- VUG: Sum across accounts
- PLTR: Sum across accounts (53527429 + 50580939)
- SCHG: Sum across accounts
- VMFXX: Sum across accounts (all money market)
- VTSAX: Sum across accounts

### 3. Update DataHub Column B Only

**WRITABLE**: Column B (Quantity) only

**DO NOT TOUCH**:
- Column A (Ticker) - already set
- Column C onwards - formulas

```javascript
// Update VOO quantity (Row 46)
mcp__gdrive__sheets(operation: "updateCells", params: {
    spreadsheetId: SPREADSHEET_ID,
    range: "DataHub!B46:B46",
    values: [["214.7947"]]  // Aggregated quantity
})
```

### 4. Update Pattern

Loop through each retirement ticker and update Column B:

| Ticker | Range | Aggregation |
|--------|-------|-------------|
| VOO | B46 | 18.1817 + 196.613 = 214.7947 |
| VUG | B47 | 10.9488 + 2.1164 = 13.0652 |
| VTSAX | B48 | 126.336 + 102.126 = 228.462 |
| SCHG | B49 | 100 + 6 = 106 |
| PLTR | B50 | 25 + 42 = 67 |
| NVDA | B51 | 150 |
| TSLA | B52 | 58 |
| VB | B53 | 20 |
| ARKK | B54 | 16.13 |
| VMFXX | B55 | 2.94 + 0.57 + 179.92 + 428.42 = 611.85 |
| FGCKX | B56 | 4.447 |
| FXAIX | B57 | 3.705 |

## Safety Checks

**Before updating:**
- Verify all 3 CSV files exist in `notebooks/retirement-accounts/`
- Confirm row mapping matches expected tickers
- Log any new tickers not in current sheet

**Large Change Warning (>20%):**
- If any quantity changes more than 20%, show diff and ask for confirmation

## Example Execution

```javascript
// Step 1: Read CSVs and aggregate
const holdings = aggregateFromCSVs();

// Step 2: Update each ticker's quantity
const updates = [
    { range: "DataHub!B46:B46", values: [[holdings.VOO.toFixed(4)]] },
    { range: "DataHub!B47:B47", values: [[holdings.VUG.toFixed(4)]] },
    { range: "DataHub!B48:B48", values: [[holdings.VTSAX.toFixed(3)]] },
    // ... etc
];

for (const update of updates) {
    mcp__gdrive__sheets(operation: "updateCells", params: {
        spreadsheetId: SPREADSHEET_ID,
        ...update
    });
}

// Step 3: Log summary
console.log("Updated 12 retirement positions");
```

## Post-Update Validation

**Verify:**
- [ ] All quantities updated correctly
- [ ] Formulas in columns C+ still working
- [ ] Total retirement value approximately matches sum of CSV totals
- [ ] No formula errors introduced

**Log Summary:**
```
Updated 12 retirement positions:
- VOO: 214.7947 shares
- VUG: 13.0652 shares
- VTSAX: 228.462 shares
...
Total Retirement Value: ~$387,806
```

## Critical Rules

### WRITABLE Column
- Column B: Quantity ONLY

### DO NOT TOUCH
- Column A: Tickers (pre-set)
- Columns C-S: All formulas

### Row Mapping
Retirement section starts at row 46 (after header at row 45).
Rows 46-62 are reserved for retirement holdings.

## Trigger Keywords

- "sync retirement"
- "update retirement"
- "retirement accounts"
- "vanguard sync"
- "401k update"
- "IRA sync"
- "retirement quantities"

---

**Skill Type**: Domain (workflow guidance)
**Enforcement**: SUGGEST
**Priority**: Medium
**Line Count**: < 200
