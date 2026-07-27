---
title: "Broker CSV Inputs and Fallbacks"
description: "CSV formats retained for cutover verification, fallback, and retirement sync"
category: guides
---

# Broker CSV Inputs and Fallbacks

Reference for broker CSV files that Finance Guru™ retains for verification,
fallback, and retirement workflows.

## Overview

SnapTrade is the preferred live input for taxable positions, balances,
transactions, and realized dividends. CSV exports remain important during account
cutover, when the live API is unavailable, and for retirement accounts that have
not moved to SnapTrade.

Start with [SnapTrade Live Sync](snaptrade-live-sync.md) for live configuration.
Use this guide when a workflow explicitly selects its CSV fallback.

**Quick Navigation:**
- [CSV Types Summary](#csv-types-summary)
- [File Locations](#file-locations)
- [CSV Formats](#csv-formats)
- [Broker Export Instructions](#broker-export-instructions)
- [Upload Workflow](#upload-workflow)

---

## CSV Types Summary

| CSV Type | When needed | Live source | Skills Using It |
| --- | --- | --- | --- |
| Portfolio Positions | Initial reconciliation or fallback | SnapTrade `positions` | PortfolioSyncing |
| Account Balances | Initial reconciliation or `margin_metrics --source csv` fallback | SnapTrade `balances` | PortfolioSyncing, margin-management |
| Transaction History | Reconciliation or fallback until activity cutover completes | SnapTrade `activities` | TransactionSyncing |
| Dividend History | Reconciliation or fallback until activity cutover completes | SnapTrade `activities` | dividend-tracking |
| Retirement Accounts | Current workflow when applicable | Deferred | retirement-syncing |

---

## File Locations

Place only the CSVs required by the selected fallback workflow in this
`notebooks/` directory structure:

```
notebooks/
├── updates/                      # Active portfolio CSVs
│   ├── Portfolio_Positions_*.csv   # Position verification/fallback
│   ├── Balances_*.csv              # Cash/margin verification/fallback
│   └── dividend.csv                # Dividend reconciliation/fallback
├── transactions/                 # Transaction history
│   └── History_for_Account_*.csv
└── retirement-accounts/          # Retirement CSVs
    ├── OfxDownload.csv           # Vanguard IRAs
    ├── OfxDownload (1).csv       # Vanguard Brokerage
    └── Portfolio_Positions_*.csv # Fidelity 401k
```

**Important:** These directories are `.gitignore`'d to protect your financial data. Never commit CSV files with real data.

---

## CSV Formats

### 1. Portfolio Positions CSV (Fallback)

**Purpose:** Updates stock/ETF holdings in Google Sheets DataHub

**File naming:** `Portfolio_Positions_MMM-DD-YYYY.csv`

**Location:** `notebooks/updates/`

**Required columns:**
- `Symbol` - Ticker (e.g., TSLA, AAPL, JEPI)
- `Quantity` - Number of shares
- `Average Cost Basis` - Your purchase price per share

**Optional columns:**
- `Last Price` - Current market price
- `Current Value` - Position value
- `Total Gain/Loss Dollar` - Unrealized gains

**Example (Fidelity format):**
```csv
Symbol,Quantity,Last Price,Current Value,Total Gain/Loss Dollar,Percent Of Account,Average Cost Basis
TSLA,74,$445.47,$32964.78,+$15634.71,14.41%,$234.19
PLTR,369.746,$188.90,$69845.01,+$60235.59,30.54%,$25.99
JEPI,72.942,$63.85,$46582.66,+$2468.50,20.36%,$56.48
```

**What it updates:**
- DataHub Column A: Ticker
- DataHub Column B: Quantity
- DataHub Column G: Avg Cost Basis
- DataHub Column S: Layer classification (auto-assigned)

---

### 2. Account Balances CSV (Fallback)

**Purpose:** Updates cash, margin debt, and account equity

**File naming:** `Balances_for_Account_XXXXXXXX.csv`

**Location:** `notebooks/updates/`

**Required fields:**
- `Settled cash` - Available cash balance
- `Net debit` - Margin balance (negative = debt)
- `Account equity percentage` - Non-margin percentage
- `Total account value` - Portfolio total

**Optional fields:**
- `Margin interest accrued this month` - Interest charges

**Example (Fidelity format):**
```csv
Account Feature,Value
Settled cash,$0.00
Net debit,$(7822.71)
Account equity percentage,96.58%
Margin interest accrued this month,$0.00
Total account value,$228809.41
```

**What it updates:**
- DataHub Row 37: SPAXX (cash position)
- DataHub Row 38: Pending Activity
- DataHub Row 39: Margin Debt

---

### 3. Transaction History CSV (Optional)

**Purpose:** Import all transactions for audit trail and expense tracking

**File naming:** `History_for_Account_XXXXXXXX.csv`

**Location:** `notebooks/transactions/`

**Required columns:**
- `Run Date` - Transaction date
- `Action` - Type (BUY, SELL, DIVIDEND, DEBIT CARD PURCHASE)
- `Symbol` - Ticker (if applicable)
- `Description` - Transaction details
- `Amount ($)` - Dollar amount
- `Cash Balance ($)` - Ending balance

**Example (Fidelity format):**
```csv
Run Date,Action,Symbol,Description,Type,Price ($),Quantity,Commission ($),Fees ($),Accrued Interest ($),Amount ($),Cash Balance ($),Settlement Date
12/18/2025,DIVIDEND RECEIVED,JEPI,DIVIDEND,Cash,,,,,,$51.63,$0.00,12/18/2025
12/15/2025,DEBIT CARD PURCHASE,,H-E-B #458,Cash,,,,,,-$127.44,-$127.44,12/15/2025
```

**What it creates:**
- Transactions tab: Full transaction log
- Expense Tracker: Debit card purchases (auto-categorized)

---

### 4. Dividend History CSV (Optional)

**Purpose:** Track dividend income for Layer 2 (income) strategy

**File naming:** `dividend.csv`

**Location:** `notebooks/updates/`

**Required columns:**
- `Symbol` - Ticker paying dividend
- `Quantity` - Shares owned
- `Amount per share` - Dividend per share
- `Pay date` - Payment date
- `Type` - Cash or Margin

**Example (Fidelity format):**
```csv
Symbol,Quantity,Amount per share,Pay date,Type
JEPI,72.942,$0.7080,01/05/2026,Cash
JEPQ,92.043,$0.8542,01/05/2026,Cash
CLM,763.367,$0.1089,01/12/2026,Margin
```

**What it updates:**
- Dividends tab input area (A2:D43)
- Triggers Apps Script to append to historical log

---

### 5. Retirement Accounts CSVs (Optional)

**Purpose:** Sync IRA, 401k, and retirement brokerage holdings

**File naming:**
- Vanguard: `OfxDownload.csv`, `OfxDownload (1).csv`
- Fidelity 401k: `Portfolio_Positions_*.csv`

**Location:** `notebooks/retirement-accounts/`

**Required columns:**
- Vanguard: `Symbol`, `Shares`
- Fidelity: `Symbol`, `Quantity`

**Example (Vanguard OFX format):**
```csv
Account Number,Investment Name,Symbol,Shares,Share Price,Total Value,
39321600,VANGUARD S&P 500 INDEX ETF,VOO,18.1817,629.3,11441.74,
35407271,VANGUARD GROWTH ETF,VUG,10.9488,355.18,3889.21,
```

**What it updates:**
- DataHub Rows 46-62: Retirement holdings (Column B quantities only)

---

## Broker Export Instructions

Export broker files only when performing initial SnapTrade reconciliation or a
fallback workflow.

_Detailed export instructions for your broker:_

👉 **See:** [Broker CSV Export Guide](broker-csv-export-guide.md)

**Supported brokers:**
- ✅ **Fidelity Investments** - Fully automated parsing
- ⚠️ **Schwab, Vanguard, TD Ameritrade, E*TRADE** - Manual mapping required (coming soon)

_Fallback export checklist:_
1. Login to your broker
2. Navigate to account summary/positions
3. Export only the data required by the current workflow
4. Save files to the appropriate `notebooks/` subdirectory
5. Re-enable the live route only after any discrepancy is understood

---

## Upload Workflow

### Initial SnapTrade Cutover

1. Configure the live bridge using
   [SnapTrade Live Sync](snaptrade-live-sync.md).
2. Export a known-good positions and balances snapshot.
3. Compare the live CLI output with the snapshot.
4. Assign the account role and set `enabled: true` only after reconciliation.
5. Keep the CSV path available as a fallback until the account is verified.

### Regular Live Updates

1. Run the relevant SnapTrade command or invoke the matching skill.
2. Review refused accounts, missing values, and safety-gate diffs.
3. Approve the Google Sheets write when the comparison is expected.
4. Verify quantities, cash or margin balances, and protected formulas.

### CSV Fallback

1. Disable the affected live route if its data is unreliable.
2. Download a fresh broker export.
3. Place it in the directory shown in [File Locations](#file-locations).
4. Select the workflow's documented CSV path, such as:

   ```bash
   uv run python -m src.analysis.margin_metrics --source csv --pretty
   ```

5. Reconcile the live source before re-enabling the route.

### What Gets Synced

| Data Type | Preferred Input | Skill | Target Sheet |
| --- | --- | --- | --- |
| Positions | SnapTrade `positions` | `portfolio-sync` | DataHub |
| Balances | SnapTrade `balances` | `portfolio-sync` | DataHub |
| Transactions | SnapTrade `activities` | `sync transactions` | Transactions, Expense Tracker |
| Dividends | SnapTrade `activities` filtered to `DIVIDEND` | `sync dividends` | Dividends |
| Retirement | Broker CSV | `sync retirement` | DataHub |

---

## Data Validation

### Safety Checks (Auto-Applied)

Finance Guru applies the same safety checks to normalized live data and CSV
fallbacks before writing:

**Position checks:**
- ✅ Fewer tickers than current sheet → STOP (confirm sales)
- ✅ Quantity change >10% → STOP (confirm trades)
- ✅ Cost basis change >20% → FLAG (possible corporate action)

**Balance checks:**
- ✅ SPAXX discrepancy >$100 → FLAG (cash mismatch)
- ✅ Margin debt jump >$5,000 → STOP (unintended draw)

**Formula protection:**
- ✅ 3+ formula errors → STOP (repair formulas first)
- ✅ Empty strings in formula columns → BLOCKED (preserves calculations)

### Manual Validation

After each sync, verify:
- [ ] Position quantities match broker
- [ ] Cash balance matches broker
- [ ] Margin debt matches broker
- [ ] Total account value ±$10 of broker
- [ ] No formula errors (#N/A, #REF!, #DIV/0!)

---

## Common Issues

### Problem: CSV Fallback Import Fails

**Solution:**
1. Confirm the workflow is intentionally using its CSV fallback
2. Ensure the CSV is in the correct `notebooks/` subdirectory
3. Check that the file has a header row
4. Verify required columns are present
5. Remove trailing blank rows

### Problem: Broker Not Supported

**Solution:**
1. Export CSV in whatever format available
2. During onboarding, select **"Other Broker"**
3. You'll be guided through manual column mapping
4. File GitHub issue to request broker support

### Problem: Wrong Values After Sync

**Solution:**
1. Check CSV is most recent export
2. Verify date in filename matches download date
3. Confirm all trades settled (not pending)
4. Re-export from broker if data stale

### Problem: Formulas Broken After Sync

**Solution:**
1. **DO NOT PANIC** - your data is safe
2. Contact support (file GitHub issue)
3. Restore from Google Sheets version history if needed

---

## Security & Privacy

**Critical reminders:**

- ✅ All `notebooks/` subdirectories are `.gitignore`'d
- ✅ CSV fallback files remain local
- ✅ SnapTrade credentials remain in the local `.env`
- ⚠️ Live sync sends read-only requests to the external SnapTrade API
- ❌ **NEVER commit CSV files with real data**
- ❌ **NEVER share CSVs publicly**

**Best practices:**
- Delete CSV files after successful import
- Use encrypted disk if storing long-term
- Anonymize data before sharing screenshots
- Review `.gitignore` before git commits

---

## Quick Reference Table

| CSV Type | Status | Location | Workflow |
| --- | --- | --- | --- |
| Positions | Verification/fallback | `notebooks/updates/` | `portfolio-sync` |
| Balances | Verification/fallback | `notebooks/updates/` | `margin_metrics --source csv` |
| Transactions | Reconciliation/fallback | `notebooks/transactions/` | `sync transactions` |
| Dividends | Reconciliation/fallback | `notebooks/updates/` | `sync dividends` |
| Retirement | Current when applicable | `notebooks/retirement-accounts/` | `sync retirement` |

---

## Related Documentation

- **Broker Export Instructions:** [broker-csv-export-guide.md](broker-csv-export-guide.md)
- **SnapTrade Live Sync:** [snaptrade-live-sync.md](snaptrade-live-sync.md)
- **Portfolio Syncing Skill:** `.claude/skills/PortfolioSyncing/SKILL.md`
- **Transaction Syncing Skill:** `.claude/skills/TransactionSyncing/SKILL.md`
- **Dividend Tracking Skill:** `.claude/skills/dividend-tracking/SKILL.md`
- **Retirement Syncing Skill:** `.claude/skills/retirement-syncing/SKILL.md`
- **Troubleshooting Guide:** [TROUBLESHOOTING.md](../setup/TROUBLESHOOTING.md)

---

## Contributing

Help improve CSV support:

1. **Report issues:** File GitHub issue for parsing errors
2. **Request brokers:** Share CSV format (anonymized!) for unsupported brokers
3. **Submit patterns:** Contribute expense categorization rules

**We welcome contributions to expand broker coverage!**

---

_Last Updated:_ 2026-07-27
_CSV Types Documented:_ 5
