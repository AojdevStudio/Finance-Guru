---
name: dividend-tracking
description: Sync dividend portfolio data between DataHub and Dividend Tracker sheet. Cross-references Layer 2 dividend holdings, updates share counts, looks up dividend data, calculates expected income, and identifies distribution cuts. Triggers on dividend tracker, sync dividends, layer 2 income, DRIP status, or monthly dividend analysis.
---

# Dividend Tracking

## Purpose

Maintain accurate dividend income tracking by syncing Layer 2 dividend fund holdings from DataHub to the Dividend Tracker sheet, ensuring expected monthly income calculations are current.

## When to Use

Use this skill when:
- DataHub updated with new dividend funds
- Monthly dividend cycle (checking expected payments)
- User mentions: "dividend tracker", "sync dividends", "update dividends", "layer 2 income"
- Analyzing dividend income or DRIP status
- Working with dividend-related files in `fin-guru/data/`

## Core Workflow

### 1. Read DataHub

**Filter**: Column S = "Layer 2 - Dividend"

**Extract**:
- Column A: Ticker
- Column B: Quantity (shares owned)
- Column S: Layer (confirm "Layer 2 - Dividend")

**Example Layer 2 Holdings**:
```
JEPI: 61.342 shares
JEPQ: 92.043 shares
SPYI: 100.051 shares
QQQI: 124.443 shares
QQQY: 74.73 shares
CLM: 734.467 shares
CRF: 502.667 shares
ETY: 108.63 shares
ETV: 75.87 shares
BDJ: 228.59 shares
UTG: 26.54 shares
MSTY: 87.9 shares
YMAX: 110.982 shares
AMZY: 65.748 shares
```

### 2. Cross-Reference Dividend Tracker

**Read Dividend Tracker**:
- Column A: Fund Symbol
- Column B: Fund Name
- Column C: Dividend Frequency (Monthly/Quarterly)
- Column D: Shares Owned
- Column E: Dividend Per Share
- Column F: Total Dividend $ (formula: D × E)
- Column G: Ex-Dividend Date
- Column H: DRIP Status (Yes/No)

**Identify Discrepancies**:
- ❌ **MISSING funds**: In DataHub but not in Dividend Tracker
- ⚠️ **MISMATCHED shares**: Share count differs between sheets
- ⚠️ **OUTDATED data**: Dividend per share hasn't been updated in 30+ days

### 3. Lookup Dividend Data (for missing/outdated funds)

**Data Sources**:
- Financial APIs (Alpha Vantage, financial-datasets MCP)
- Web search for recent dividend announcements
- Fund websites (e.g., JPMorgan for JEPI/JEPQ)

**Key Data Points**:
- **Current dividend per share**: Latest declared dividend
- **Ex-dividend date**: When to own shares to receive payment
- **Payment frequency**: Monthly, Quarterly, Annual
- **Distribution history**: Check for recent cuts or increases
- **DRIP availability**: Check user-profile.yaml for fund-specific preferences

**Example Lookup**:
```
MSTY (YieldMax MSTR Option Income)
- Dividend Per Share: $0.42 (monthly)
- Ex-Dividend Date: 11/20/2025
- Payment Date: 11/27/2025
- Frequency: Monthly
- DRIP: No (Cash distribution per strategy)
```

### 4. Update Dividend Tracker

#### For EXISTING Funds:

**Update share count**:
```
Column D (Shares Owned) = DataHub Column B
```

**Recalculate Total Dividend $**:
```
Column F = D × E (Shares × Dividend Per Share)
```

**Example**:
```
JEPI: 61.342 shares × $0.46/share = $28.22/month
JEPQ: 92.043 shares × $0.51/share = $46.94/month
```

#### For NEW Funds:

**Add new row with**:
- Column A: Fund Symbol (from DataHub)
- Column B: Fund Name (lookup from API or web search)
- Column C: Dividend Frequency (Monthly/Quarterly)
- Column D: Shares Owned (from DataHub)
- Column E: Dividend Per Share (lookup current rate)
- Column F: Total Dividend $ (formula: =D × E)
- Column G: Ex-Dividend Date (lookup next ex-date)
- Column H: DRIP Status (default: "No" for income funds per strategy)

**Log Addition**:
```
✅ Added MSTY to Dividend Tracker
- 87.9 shares @ $0.42/month = $36.92/month
- Ex-date: 11/20/2025
- DRIP: No (Cash for income)
```

#### Validate Totals:

**Check formula**:
```
=SUM(F2:F{lastrow})
```

**Fix if broken**:
- If #N/A or #DIV/0! errors, add IFERROR() wrapper
- If range doesn't capture all rows, expand to F2:F100
- If formula deleted, recreate: `=SUM(F2:F50)`

### 5. Generate Alerts

#### Dividend Cut Alert (>20% reduction):
```
⚠️ ALERT: CLM dividend reduced from $0.10 to $0.07 (-30%)
Action: Consider rotating to Bucket 1 (JEPI/JEPQ) per strategy
```

#### Distribution Cut Alert (>50% reduction):
```
🚨 MAJOR CUT: QQQY dividend reduced from $0.25 to $0.10 (-60%)
Action: SELL within 48 hours, rotate to JEPI/JEPQ per rotation rules
```

#### Missing Ex-Dates:
```
⚠️ MISSING EX-DATES for 3 funds (ETY, ETV, UTG)
Action: Look up ex-dates for upcoming month
```

#### Expected Monthly Income Report:
```
📊 TOTAL EXPECTED DIVIDENDS: $2,847.32/month
- Target: $8,333/month (to reach $100k/year)
- Progress: 34.2% of goal
- Months elapsed: 1 of 28 (on track per Monte Carlo)
```

## Critical Rules

### WRITABLE Columns (Dividend Tracker)
- ✅ Column D: Shares Owned (sync from DataHub)
- ✅ Column E: Dividend Per Share (update from API/web search)
- ✅ Column G: Ex-Dividend Date (update from API/web search)

### SACRED Columns (NEVER TOUCH)
- ❌ Column F: Total Dividend $ (formula: D × E)
- ❌ Total row formula: `=SUM(F2:F{lastrow})`

### DRIP Status Logic

**Default: "No" for Layer 2 - Income funds**
- Per user strategy, Layer 2 dividends pay CASH (not reinvested)
- Cash dividends pay down margin debt from Month 1
- DRIP only enabled if explicitly requested by user

**Exceptions** (check user-profile.yaml):
- User may enable DRIP for specific funds during accumulation phase
- Builder fund (future) may have DRIP enabled

## Expected Dividend Income Calculation

**Formula**:
```
Monthly Income = SUM of all (Shares × Dividend Per Share × Frequency/12)
```

**Example**:
```
JEPI: 61.342 × $0.46 × (12/12) = $28.22/month
SPYI: 100.051 × $0.52 × (12/12) = $52.03/month
CLM: 734.467 × $0.09 × (12/12) = $66.10/month
ETY: 108.63 × $0.12 × (4/12) = $4.35/month (quarterly)
───────────────────────────────────
TOTAL: $2,847.32/month
```

## Monthly Review Triggers

**When to run this workflow**:
1. **After DataHub update** (new funds added)
2. **Before ex-dividend dates** (validate shares owned)
3. **After dividend payments** (confirm amounts match expectations)
4. **Monthly strategy review** (assess progress toward $100k/year goal)
5. **Distribution cut detected** (fund rotation decision)

## Fund Rotation Rules (from strategy)

**Rotation Criteria** (per Dividend Master Strategy):
- **Single fund cuts 50%+**: SELL within 48 hours, rotate to Bucket 1 (JEPI/JEPQ)
- **Single fund cuts 30%+**: PAUSE purchases, monitor 30 days
- **Blended yield drops below 24%**: Major rebalancing within 2 weeks

**Action Steps**:
1. Detect distribution cut via API or web search
2. Calculate impact on total monthly income
3. If triggers rotation rule, alert user immediately
4. Suggest replacement fund from Bucket 1 (JEPI/JEPQ always safe)
5. Execute rotation only after user approval

## Google Sheets Integration

**Spreadsheet ID**: Read from `fin-guru/data/user-profile.yaml` → `google_sheets.portfolio_tracker.spreadsheet_id`

**Use the mcp__gdrive__sheets tool**:
```javascript
// STEP 1: Read Spreadsheet ID from user profile
// Load fin-guru/data/user-profile.yaml
// Extract: google_sheets.portfolio_tracker.spreadsheet_id

// STEP 2: Read Dividend Tracker
mcp__gdrive__sheets(
    operation: "spreadsheets.values.get",
    params: {
        spreadsheetId: SPREADSHEET_ID,  // from user-profile.yaml
        range: "Dividend Tracker!A2:H50"
    }
)

// STEP 3: Update shares and dividend data
mcp__gdrive__sheets(
    operation: "spreadsheets.values.update",
    params: {
        spreadsheetId: SPREADSHEET_ID,  // from user-profile.yaml
        range: "Dividend Tracker!D2:E50",
        valueInputOption: "USER_ENTERED",
        requestBody: {
            values: [[shares, dividend_per_share], ...]
        }
    }
)
```

## Agent Permissions

**Dividend Specialist** (Write-enabled):
- Can update Columns D, E, G in Dividend Tracker
- Can add new rows for new funds
- Can look up dividend data from APIs
- CANNOT modify Total Dividend $ formula (Column F)

**Builder** (Write-enabled):
- Can add new funds after DataHub sync
- Can repair broken formulas
- Can update DRIP status

**All Other Agents** (Read-only):
- Market Researcher, Quant Analyst, Strategy Advisor
- Can read dividend data for analysis
- Cannot write to spreadsheet
- Must defer to Dividend Specialist or Builder

## Reference Files

For complete details, see:
- **Dividend Strategy**: `docs/fin-guru/strategies/active/dividend-income-master-strategy.md`
- **Portfolio Strategy**: `docs/fin-guru/strategies/active/portfolio-master-strategy.md`
- **User Profile**: `fin-guru/data/user-profile.yaml`
- **Spreadsheet Architecture**: `fin-guru/data/spreadsheet-architecture.md`

## Pre-Flight Checklist

Before syncing Dividend Tracker:
- [ ] DataHub is up-to-date (CSV import completed)
- [ ] Layer 2 filter applied correctly (Column S)
- [ ] Dividend Tracker sheet exists in Google Sheets
- [ ] No manual edits pending (user should save first)
- [ ] Financial API or web search available for lookups
- [ ] Current month's ex-dividend dates known

## Example Scenario

**Trigger**: DataHub updated with 3 new dividend funds

**Agent workflow**:
1. ✅ Read DataHub Layer 2 - found 14 dividend funds
2. ✅ Read Dividend Tracker - found 11 funds
3. ⚠️ MISSING FUNDS DETECTED:
   - MSTY: 87.9 shares (not in tracker)
   - YMAX: 110.982 shares (not in tracker)
   - AMZY: 65.748 shares (not in tracker)
4. ✅ LOOKUP DIVIDEND DATA:
   - MSTY: $0.42/month, ex-date 11/20/2025
   - YMAX: $0.38/month, ex-date 11/18/2025
   - AMZY: $0.41/month, ex-date 11/22/2025
5. ✅ UPDATE DIVIDEND TRACKER:
   - Added 3 new rows with share counts, dividends, ex-dates
   - Set DRIP status: No (Cash for income)
6. ✅ RECALCULATE TOTAL:
   - Previous: $2,732.45/month
   - New: $2,847.32/month (+$114.87)
7. ✅ LOG: "Synced 14 funds, added 3 new (MSTY, YMAX, AMZY), income +$114.87/month"

---

**Skill Type**: Domain (workflow guidance)
**Enforcement**: SUGGEST (high priority advisory)
**Priority**: High
**Line Count**: < 350 (following 500-line rule) ✅
