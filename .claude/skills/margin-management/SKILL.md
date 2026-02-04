---
name: margin-management
description: Update Margin Dashboard with Fidelity balance data and calculate margin-living strategy metrics. Monitors margin balance, interest costs, coverage ratios, and scaling thresholds. Triggers safety alerts for large draws and provides time-based scaling recommendations. Use when updating margin, balances, coverage ratio, or margin strategy analysis.
---

# Margin Management

## Purpose

Monitor and manage margin-living strategy by tracking margin balances, interest costs, dividend coverage ratios, and portfolio-to-margin safety thresholds. Provides data-driven scaling recommendations based on strategy milestones.

## When to Use

Use this skill when:
- Importing new Fidelity balances CSV
- Updating margin balance or interest rate
- Calculating coverage ratio (dividends ÷ interest)
- User mentions: "margin dashboard", "margin balance", "coverage ratio", "margin strategy"
- Assessing margin scaling decisions
- Checking safety thresholds

## Core Workflow

### 1. Read Fidelity Balances CSV

**Location**: `notebooks/updates/Balances_for_Account_{account_id}.csv`

**Key Fields to Extract**:
```csv
Balance,Day change
Total account value,228809.41,3447.61      → Portfolio Value
Margin buying power,193919.92,-4667.04
Net debit,-2992.70,-2191.14                 → Margin Balance (abs value)
Margin interest accrued this month,1.12,    → Monthly Interest (actual)
```

**Calculations**:
- **Margin Balance**: Absolute value of "Net debit" = $2,992.70
- **Interest Rate**: Default 10.875% (Fidelity $1k-$24.9k tier) unless specified
- **Monthly Interest Cost**: Balance × Rate ÷ 12 = $2,992.70 × 0.10875 ÷ 12 = $27.11

### 2. Safety Check: Margin Jump Alert

**Rule**: If new margin balance > previous balance + $5,000, **STOP**

**Reason**: Large draws should be intentional per margin-living strategy

**Example**:
```
Previous: $2,992.70
Current: $9,500.00 (+$6,507.30) → 🚨 ALERT - Confirm intentional draw
```

**Action**:
- Alert user immediately
- Show diff: "Margin increased by $6,507 - Confirm this was intentional"
- Wait for user confirmation before proceeding

### 3. Add Entry to Margin Dashboard

**Insert new row with**:
- **Date**: Current date (use `date +"%Y-%m-%d"`)
- **Margin Balance**: From Balances CSV (Net debit absolute value)
- **Interest Rate**: 10.875% (or updated rate from CSV if available)
- **Monthly Interest Cost**: Calculate (Balance × Rate ÷ 12)
- **Notes**: Auto-generate based on elapsed time since Oct 9, 2025

**Example Entry**:
```
Date: 2025-11-11
Margin Balance: $2,992.70
Interest Rate: 10.875%
Monthly Interest Cost: $27.11
Notes: Month 1 - Building foundation, on track per strategy
```

**Notes Generation Logic**:
```python
months_elapsed = (current_date - datetime(2025, 10, 9)).days // 30

if months_elapsed < 6:
    note = f"Month {months_elapsed} - Building foundation, on track per strategy"
elif months_elapsed < 12:
    note = f"Month {months_elapsed} - Approaching Month 6 milestone"
elif months_elapsed < 18:
    note = f"Month {months_elapsed} - Approaching break-even milestone"
else:
    note = f"Month {months_elapsed} - Mature strategy, monitor scaling"
```

### 4. Update Summary Section

**Recalculate Dashboard Metrics**:

#### Current Margin Balance
```
= Latest entry from Margin Dashboard
Example: $2,992.70
```

#### Monthly Interest Cost
```
= Latest calculated cost
Example: $27.11/month
```

#### Annual Interest Cost
```
= Monthly Interest Cost × 12
Example: $27.11 × 12 = $325.32/year
```

#### Dividend Income (from Dividend Tracker)
```
= Pull from Dividend Tracker "TOTAL EXPECTED DIVIDENDS"
Example: $2,847.32/month
```

#### Coverage Ratio
```
= Dividend Income ÷ Monthly Interest Cost
Formula: =IFERROR(Dividends / Interest, 0)
Example: $2,847.32 ÷ $27.11 = 105.0x 🟢
```

**Fix #DIV/0! if margin balance = $0**:
```
Before: =B10 / B11  (causes #DIV/0! when margin = 0)
After: =IFERROR(B10 / B11, 0)  (returns 0 when no margin)
```

### 5. Calculate Strategy Metrics

#### Portfolio-to-Margin Ratio
```
= Total account value ÷ Margin Balance
Example: $228,809.41 ÷ $2,992.70 = 76.5:1 🟢🟢🟢
```

**Safety Thresholds**:
- 🟢 **Green**: Ratio > 4.0:1 (target - healthy margin usage)
- 🟡 **Yellow**: Ratio 3.5-4.0:1 (warning - pause scaling)
- 🔴 **Red**: Ratio < 3.0:1 (alert - stop draws, inject business income)
- ⚫ **Critical**: Ratio < 2.5:1 (emergency - inject $30k+, consider selling)

#### Current Draw vs Fixed Expenses
```
Current monthly draw: $4,500 (fixed expenses only)
Target: Start with $4,500, scale to $6,213, $8,000, $10,000 based on data
```

### 6. Scaling Alerts (Time-Based)

**Strategy Start Date**: October 9, 2025

**Calculate months elapsed**:
```python
from datetime import datetime
start = datetime(2025, 10, 9)
current = datetime.now()
months_elapsed = (current - start).days // 30
```

#### Month 6 Alert (April 2026)
```
📊 MONTH 6 MILESTONE CHECK:
✅ Dividends: $2,847/month (need $2,000+)
✅ Portfolio-to-Margin Ratio: 76.5:1 (need 4:1+)
✅ Dividend Growth: On track

🎯 RECOMMENDATION: Scale margin draw to $6,213/month (add mortgage)
- Current: $4,500 (fixed expenses only)
- New: $6,213 (fixed + mortgage)
- Safety margin: Excellent
```

#### Month 12 Alert (October 2026)
```
📊 MONTH 12 BREAK-EVEN CHECK:
Expected Dividends: $4,500+/month (goal: break-even with margin interest)
✅ IF achieved: Consider scaling to $8,000/month (add some variable expenses)
⚠️ IF not: Hold at $6,213, assess strategy
```

#### Month 18 Alert (April 2027)
```
📊 MONTH 18 MATURE STRATEGY CHECK:
Expected Dividends: $7,000+/month
Expected Margin: Declining (dividends paying down debt)
✅ IF achieved: Consider scaling to $10,000/month (most variable expenses)
⚠️ IF not: Hold current level, reassess timeline
```

### 7. Alert Thresholds

**Generate alerts based on conditions**:

#### Green (Healthy)
```
✅ Ratio > 4:1 AND dividends covering interest
Status: On track, continue per strategy
```

#### Yellow (Caution)
```
⚠️ Ratio 3.5-4:1 OR dividend coverage declining
Action: Pause scaling, monitor weekly
```

#### Red (Alert)
```
🚨 Ratio < 3:1 OR dividend cuts detected
Action: STOP draws, inject $20k business income
```

#### Critical (Emergency)
```
⛔ Ratio < 2.5:1 OR margin call risk
Action: STOP draws, inject $30k+ business income, consider selling hedge (SQQQ)
```

## Critical Rules

### WRITABLE Columns (Margin Dashboard)
- ✅ Date (Column A)
- ✅ Margin Balance (Column B)
- ✅ Interest Rate (Column C)
- ✅ Monthly Interest Cost (Column D - calculated but writeable)
- ✅ Notes (Column E)

### SACRED Formulas (NEVER TOUCH)
- ❌ Coverage Ratio (unless adding IFERROR wrapper)
- ❌ Summary section totals (unless fixing #DIV/0!)

### Margin Strategy Philosophy

**Core Principle**: Confidence-based scaling, not time-based mandates

**Decision Framework**:
1. **Data-driven**: Decisions backed by actual dividend income, not projections
2. **Safety-first**: Never scale if ratio drops below 3.5:1
3. **Business income as insurance**: Available $22k/month, not primary strategy
4. **Monte Carlo backstop**: 98.5% of scenarios used business income at some point

## Business Income Backstop

**Available**: $22,000/month from business operations

**Usage Scenarios**:
1. ⛔ **Margin call (ratio < 3:1)**: MUST USE business income immediately
2. ⚠️ **Market correction (20-30% drop)**: OPTIONAL - assess need
3. 🎯 **Acceleration (reach FI faster)**: OPTIONAL - strategic choice

**Current Philosophy**: Insurance policy only, not active strategy component

## Example Calculations

### Scenario 1: Month 1 (Current State)
```
Portfolio Value: $228,809.41
Margin Balance: $2,992.70
Ratio: 76.5:1 🟢🟢🟢

Monthly Interest: $27.11
Dividend Income: $2,847.32
Coverage: 105.0x 🟢

Status: Excellent - building foundation
```

### Scenario 2: Month 6 (Projected)
```
Portfolio Value: $280,000 (projected with W2 contributions)
Margin Balance: $25,000 (scaled to $6,213/month draw)
Ratio: 11.2:1 🟢

Monthly Interest: $227
Dividend Income: $4,500 (projected)
Coverage: 19.8x 🟢

Status: Healthy - on track for break-even
```

### Scenario 3: Month 15 (Break-Even)
```
Portfolio Value: $350,000
Margin Balance: $50,000 (scaled to $8,000/month draw)
Ratio: 7.0:1 🟢

Monthly Interest: $453
Dividend Income: $6,800
Coverage: 15.0x 🟢

Status: Break-even achieved, dividends > interest
```

## Google Sheets Integration

**Spreadsheet ID**: Read from `fin-guru/data/user-profile.yaml` → `google_sheets.portfolio_tracker.spreadsheet_id`

**Use the mcp__gdrive__sheets tool**:
```javascript
// STEP 1: Read Spreadsheet ID from user profile
// Load fin-guru/data/user-profile.yaml
// Extract: google_sheets.portfolio_tracker.spreadsheet_id

// STEP 2: Read Margin Dashboard
mcp__gdrive__sheets(
    operation: "spreadsheets.values.get",
    params: {
        spreadsheetId: SPREADSHEET_ID,  // from user-profile.yaml
        range: "Margin Dashboard!A2:E50"
    }
)

// STEP 3: Add new margin entry
mcp__gdrive__sheets(
    operation: "spreadsheets.values.update",
    params: {
        spreadsheetId: SPREADSHEET_ID,  // from user-profile.yaml
        range: "Margin Dashboard!A2:E2",
        valueInputOption: "USER_ENTERED",
        requestBody: {
            values: [[date, balance, rate, monthly_cost, notes]]
        }
    }
)
```

## Agent Permissions

**Margin Specialist** (Write-enabled):
- Can add new entries to Margin Dashboard
- Can update margin balance, rate, cost
- Can generate scaling alerts
- CANNOT modify summary formulas (without formula-protection skill)

**Builder** (Write-enabled):
- Can repair broken formulas (#DIV/0!)
- Can update summary section calculations
- Can add new metrics

**All Other Agents** (Read-only):
- Market Researcher, Quant Analyst, Strategy Advisor
- Can read margin data for analysis
- Cannot write to spreadsheet
- Must defer to Margin Specialist or Builder

## Reference Files

For complete strategy details, see:
- **Margin Strategy**: `fin-guru-private/fin-guru/strategies/active/margin-living-master-strategy.md`
- **Portfolio Strategy**: `fin-guru-private/fin-guru/strategies/active/portfolio-master-strategy.md`
- **User Profile**: `fin-guru/data/user-profile.yaml`
- **Spreadsheet Architecture**: `fin-guru/data/spreadsheet-architecture.md`

## Pre-Flight Checklist

Before updating Margin Dashboard:
- [ ] Fidelity Balances CSV is latest by date
- [ ] CSV is in `notebooks/updates/` directory
- [ ] Margin Dashboard sheet exists in Google Sheets
- [ ] Previous margin balance known (for jump detection)
- [ ] Dividend Tracker is up-to-date (for coverage ratio)
- [ ] Current date retrieved via `date` command

## Example Scenario

**Trigger**: User downloads new Fidelity balances CSV

**Agent workflow**:
1. ✅ Read Balances CSV - Portfolio: $228,809.41, Margin: $2,992.70
2. ✅ Safety check - Previous: $0, Current: $2,992.70 (+$2,992.70 < $5k threshold) - PASS
3. ✅ Calculate metrics:
   - Monthly interest: $27.11
   - Portfolio-to-margin ratio: 76.5:1
   - Coverage ratio: 105.0x (dividends ÷ interest)
4. ✅ Add entry to Margin Dashboard:
   - Date: 2025-11-11
   - Balance: $2,992.70
   - Rate: 10.875%
   - Cost: $27.11
   - Notes: "Month 1 - Building foundation, on track"
5. ✅ Update summary section:
   - Current balance: $2,992.70
   - Monthly cost: $27.11
   - Annual cost: $325.32
   - Dividend income: $2,847.32
   - Coverage: 105.0x
6. ✅ Generate status: "🟢 Excellent health - Ratio 76.5:1, Coverage 105x"
7. ✅ LOG: "Updated Margin Dashboard - Month 1, $2,992.70 balance, 76.5:1 ratio"

---

**Skill Type**: Domain (workflow guidance)
**Enforcement**: BLOCK (financial risk critical)
**Priority**: Critical
**Line Count**: < 400 (following 500-line rule) ✅
