---
name: retirement-syncing
description: Parse and report retirement holdings from Vanguard and Fidelity CSV exports. CSV-only by design — the Vanguard IRAs and Fidelity 401k are not connected in SnapTrade, so there is no live/DB path yet and no persistent destination. Triggers on sync retirement, update retirement, vanguard sync, 401k update, IRA sync, or working with notebooks/retirement-accounts/ files.
---

# Retirement Account Syncing

## Data source: CSV-only (no live path yet)

Unlike the other syncing skills, retirement accounts do **not** use the
sync-first + DB-read pattern. The Vanguard IRAs / brokerage and the Fidelity
401(k) are **not authorized in SnapTrade** (only the one taxable-margin Fidelity
account is routed in `config/snaptrade-accounts.yaml`). So there is no live API
snapshot to refresh into `family_office.db` for these accounts, and CSV exports
remain the only source. This is a deliberate, documented exception to the shared
**[Sync-First + DB-Read](../_shared/SyncFirstDbRead.md)** pattern.

**Prerequisite for a live path (before this skill can become DB-backed):**
1. Authorize the Vanguard and Fidelity retirement institutions in SnapTrade.
2. Add each resulting account to `config/snaptrade-accounts.yaml` with a `role`
   set and `enabled: true`.
3. Extend the positions sync (or a retirement-specific sync) to write those
   accounts into the DB, then rewrite this skill to Step 0 refresh + DB-read.

Until all three are done, do not fabricate a live path: use the CSV workflow below.

## Purpose

Parse Vanguard and Fidelity retirement account CSV exports and report current holdings and quantities.

> ⚠️ **This skill currently has no persistent destination.** The Google Sheets DataHub it used to write to was retired 2026-07-31, and `family_office.db` has no retirement table because these accounts are not in SnapTrade. Until the three prerequisites above are met, this skill parses and reports only. Do not claim holdings were "synced" anywhere.

## When to Use

Use this skill when:
- Syncing retirement account positions from `notebooks/retirement-accounts/`
- User mentions: "sync retirement", "update retirement", "vanguard sync", "401k update", "IRA sync"
- Working with files in `notebooks/retirement-accounts/` directory

## Source Files

**Location**: `notebooks/retirement-accounts/`

| File | Source | Contents |
|------|--------|----------|
| `OfxDownload.csv` | Vanguard IRAs | Account `<ira-1>` & `<ira-2>` holdings |
| `OfxDownload (1).csv` | Vanguard Brokerage | Account `<brokerage-1>` & `<brokerage-2>` holdings |
| `Portfolio_Positions_*.csv` | Fidelity 401(k) | {employer_name} 401(k) Plan holdings |

## CSV Formats

### Vanguard OFX Format (OfxDownload.csv)
```csv
Account Number,Investment Name,Symbol,Shares,Share Price,Total Value,
<account-number>,VANGUARD S&P 500 INDEX ETF,VOO,18.1817,629.3,11441.74,
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

## Known retirement tickers

Holdings seen across the Vanguard IRAs, Vanguard brokerage, and Fidelity 401(k):
VOO, VUG, VTSAX, SCHG, PLTR, NVDA, TSLA, VB, ARKK, VMFXX, FGCKX, FXAIX.

Mary's Goucher 403(b) and Principal 401(k) allocations are tracked separately in
`fin-guru/data/user-profile.yaml` and the strategy docs, not through this skill.

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
- PLTR: Sum across accounts (`<brokerage-1>` + `<brokerage-2>`)
- SCHG: Sum across accounts
- VMFXX: Sum across accounts (all money market)
- VTSAX: Sum across accounts

### 3. Report the aggregated holdings

Present ticker and total quantity as a table in the response. There is no
destination to write to, so the report IS the deliverable.

## Safety Checks

**Before reporting:**
- Verify all 3 CSV files exist in `notebooks/retirement-accounts/`
- Note the export date of each CSV; flag anything older than 30 days
- Call out any ticker not previously seen in the known-tickers list

**Large Change Warning (>20%):** if any quantity moved more than 20% since the
last reported figures, show the diff and confirm with the user before treating
the numbers as accurate.

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
