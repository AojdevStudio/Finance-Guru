---
title: "Broker CSV Export Guide"
description: "How to export portfolio data from Fidelity, Schwab, Vanguard and other brokers"
category: guides
---

# Broker CSV Export Guide

This guide explains how to export your portfolio data from various brokerages for use with Finance Guru.

## Overview

Finance Guru requires TWO CSV files from your broker:

1. **Positions CSV** - Your stock/ETF holdings (symbols, quantities, cost basis)
2. **Balances CSV** - Cash, margin debt, and account totals

Save these files to: `notebooks/updates/`

---

## Supported Brokers

### ✅ Fidelity Investments

**Status**: Fully Supported (Automated Parsing)

#### Export Instructions

1. **Login** to fidelity.com
2. Navigate to **Accounts** → Select your account
3. Click **Positions** tab
4. Click **Export** button (top right)
5. Save as: `Portfolio_Positions_MMM-DD-YYYY.csv`

6. Navigate to **Balances** tab
7. Click **Export** button
8. Save as: `Balances_for_Account_XXXXXXXX.csv`

#### Expected CSV Format

**Positions CSV**:
```csv
Symbol,Quantity,Last Price,Current Value,Total Gain/Loss Dollar,Percent Of Account,Average Cost Basis
TSLA,74,$445.47,$32964.78,+$15634.71,14.41%,$234.19
PLTR,369.746,$188.90,$69845.01,+$60235.59,30.54%,$25.99
```

**Balances CSV**:
```csv
Account Feature,Value
Settled cash,$0.00
Net debit,$(7822.71)
Account equity percentage,96.58%
Margin interest accrued this month,$0.00
Total account value,$228809.41
```

---

### ⚠️ Charles Schwab

**Status**: Coming Soon (Manual Mapping Required)

#### Export Instructions

1. **Login** to schwab.com
2. Navigate to **Accounts** → **Positions**
3. Click **Export** → **Export to Spreadsheet**
4. Save as: `schwab_positions_MMM-DD-YYYY.csv`

5. Navigate to **Accounts** → **Account Summary**
6. Click **Export** → **Export to Spreadsheet**
7. Save as: `schwab_balances_MMM-DD-YYYY.csv`

#### Notes

- Schwab CSV format parsing will be added in a future update
- You can still use Schwab data, but will need to manually map columns

---

### ⚠️ Vanguard

**Status**: Coming Soon (Manual Mapping Required)

#### Export Instructions

1. **Login** to investor.vanguard.com
2. Navigate to **My Accounts** → Select account
3. Click **Holdings** tab
4. Click **Download** button
5. Save as: `vanguard_holdings_MMM-DD-YYYY.csv`

6. Navigate to **Balances** tab
7. Click **Download** button
8. Save as: `vanguard_balances_MMM-DD-YYYY.csv`

#### Notes

- Vanguard CSV format parsing will be added in a future update
- You can still use Vanguard data, but will need to manually map columns

---

### ⚠️ TD Ameritrade

**Status**: Coming Soon (Manual Mapping Required)

**Note**: TD Ameritrade is now owned by Charles Schwab. If you've been migrated to Schwab, use the Schwab instructions above.

#### Export Instructions

1. **Login** to tdameritrade.com
2. Navigate to **My Account** → **Positions**
3. Click **Export** button
4. Save as: `tda_positions_MMM-DD-YYYY.csv`

5. Navigate to **Balances & Account Value**
6. Click **Export** button
7. Save as: `tda_balances_MMM-DD-YYYY.csv`

---

### ⚠️ E*TRADE

**Status**: Coming Soon (Manual Mapping Required)

#### Export Instructions

1. **Login** to etrade.com
2. Navigate to **Portfolio** → **Complete View**
3. Click **Export** button (top right)
4. Select **CSV** format
5. Save as: `etrade_portfolio_MMM-DD-YYYY.csv`

6. Navigate to **Accounts** → **Account Details**
7. Click **Export** button
8. Save as: `etrade_balances_MMM-DD-YYYY.csv`

---

### ⚠️ Robinhood

**Status**: Coming Soon (Manual Mapping Required)

#### Export Instructions

1. Open **Robinhood App**
2. Tap **Account** (person icon bottom right)
3. Tap **Statements & History**
4. Tap **Account Statements**
5. Select the most recent statement
6. Tap **Share** → **Save to Files**

**Note**: Robinhood provides PDF statements, not CSV. You may need to:
- Use a third-party tool to convert PDF → CSV
- Manually create a CSV from the PDF data
- Use Robinhood's API (requires developer access)

---

## Required Data Fields

For Finance Guru to work correctly, your CSV must contain:

### Positions CSV (Required)
- **Symbol/Ticker** - Stock ticker (e.g., TSLA, AAPL)
- **Quantity/Shares** - Number of shares you own
- **Cost Basis/Average Cost** - Your average purchase price per share

### Positions CSV (Optional but Recommended)
- **Last Price** - Current market price
- **Current Value** - Total position value

### Balances CSV (Required)
- **Cash/Settled Cash** - Available cash balance
- **Margin Debt/Net Debit** - Amount owed on margin (if using margin)
- **Account Equity** - Percentage of account not on margin
- **Total Account Value** - Sum of all holdings + cash - margin debt

---

## Troubleshooting

### Problem: CSV Import Fails

**Solution**:
1. Ensure CSV is in `notebooks/updates/` directory
2. Check that CSV has header row
3. Verify required columns exist (Symbol, Quantity, Cost Basis)
4. Remove any trailing blank rows

### Problem: Broker Not Supported

**Solution**:
1. Export CSV in whatever format your broker provides
2. During onboarding, select **"Other Broker"**
3. You'll be guided through manual column mapping
4. Alternatively, file an issue on GitHub requesting your broker

### Problem: CSV Has Unexpected Format

**Solution**:
1. Open CSV in text editor (not Excel)
2. Check delimiter (should be comma, not semicolon or tab)
3. Ensure values don't have extra quotes or special characters
4. If broker uses European format (comma for decimal), convert to US format (period for decimal)

---

## Manual CSV Creation (Advanced)

If your broker doesn't export CSV, you can create one manually:

### Positions CSV Template

```csv
Symbol,Quantity,Average Cost Basis
TSLA,74,234.19
PLTR,369.746,25.99
JEPI,72.942,56.48
```

### Balances CSV Template

```csv
Settled cash,0.00
Net debit,-7822.71
Account equity percentage,96.58
Total account value,228809.41
```

**Save these as**:
- `notebooks/updates/manual_positions_YYYY-MM-DD.csv`
- `notebooks/updates/manual_balances_YYYY-MM-DD.csv`

---

## Contributing

If you successfully import CSV data from a broker not listed here:

1. Share the CSV column headers (anonymize values!)
2. File an issue on GitHub with the broker name
3. We'll add official support for that broker

**Help expand broker coverage!**

---

## Security & Privacy

**Important**:
- CSV files in `notebooks/updates/` are `.gitignore`'d by default
- Never commit CSV files with real financial data
- Finance Guru runs 100% locally - no data leaves your machine
- Delete CSV files after import if you're concerned about local storage

---

## Next Steps

After exporting your CSV files:

1. Place them in `notebooks/updates/`
2. Run `./setup.sh` (or continue onboarding)
3. Finance Guru will automatically detect and parse them
4. Verify imported data in Google Sheets DataHub

---

**Last Updated**: 2026-01-16
**Supported Brokers**: 1/7 (Fidelity only)
**Contributions Welcome**: Yes
