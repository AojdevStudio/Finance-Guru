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

## Personal Strategy Inputs

Real dollar amounts, dates, and private strategy targets must come from `.env` (see `.env.example`). Use `python-dotenv` or shell environment variables; do not hardcode personal numbers in this skill.

### Required `.env` values

- `FG_STRATEGY_START_DATE`
- `FG_MARGIN_INTEREST_RATE`, `FG_MARGIN_INTEREST_RATE_DECIMAL`
- `FG_MARGIN_JUMP_ALERT_THRESHOLD`
- `FG_CURRENT_MONTHLY_DRAW`, `FG_MONTH6_DRAW_TARGET`, `FG_MONTH12_DRAW_TARGET`, `FG_MONTH18_DRAW_TARGET`
- `FG_BUSINESS_INCOME_MONTHLY`, `FG_BUSINESS_INJECTION_RED`, `FG_BUSINESS_INJECTION_CRITICAL`
- Latest example/demo values: `FG_PORTFOLIO_BASELINE_VALUE`, `FG_MARGIN_BASELINE_BALANCE`, `FG_DIVIDEND_MONTHLY_INCOME`

## Core Workflow

### 1. Read Fidelity Balances CSV

**Location**: `notebooks/updates/Balances_for_Account_{account_id}.csv`

**Key Fields to Extract**:
```csv
Balance,Day change
Total account value,${FG_PORTFOLIO_BASELINE_VALUE_RAW},${FG_PORTFOLIO_DAY_CHANGE_RAW}      → Portfolio Value
Margin buying power,${FG_MARGIN_BUYING_POWER_RAW},${FG_MARGIN_BUYING_POWER_DAY_CHANGE_RAW}
Net debit,${FG_MARGIN_BASELINE_BALANCE_RAW},${FG_MARGIN_DAY_CHANGE_RAW}                 → Margin Balance (abs value)
Margin interest accrued this month,${FG_MARGIN_INTEREST_ACCRUED_THIS_MONTH_RAW},    → Monthly Interest (actual)
```

**Calculations**:
- **Margin Balance**: Absolute value of "Net debit" = ${FG_MARGIN_BASELINE_BALANCE}
- **Interest Rate**: Default ${FG_MARGIN_INTEREST_RATE} (Fidelity $1k-$24.9k tier) unless specified
- **Monthly Interest Cost**: Balance × Rate ÷ 12 = ${FG_MARGIN_BASELINE_BALANCE} × ${FG_MARGIN_INTEREST_RATE_DECIMAL} ÷ 12 = ${FG_MARGIN_MONTHLY_INTEREST_COST}

### 2. Safety Check: Margin Jump Alert

**Rule**: If new margin balance > previous balance + ${FG_MARGIN_JUMP_ALERT_THRESHOLD}, **STOP**

**Reason**: Large draws should be intentional per margin-living strategy

**Example**:
```
Previous: ${FG_MARGIN_BASELINE_BALANCE}
Current: ${FG_MARGIN_JUMP_EXAMPLE_CURRENT} (+${FG_MARGIN_JUMP_EXAMPLE_DIFF}) → 🚨 ALERT - Confirm intentional draw
```

**Action**:
- Alert user immediately
- Show diff: "Margin increased by ${FG_MARGIN_JUMP_EXAMPLE_DIFF} - Confirm this was intentional"
- Wait for user confirmation before proceeding

### 3. Add Entry to Margin Dashboard

**Insert new row with**:
- **Date**: Current date (use `date +"%Y-%m-%d"`)
- **Margin Balance**: From Balances CSV (Net debit absolute value)
- **Interest Rate**: ${FG_MARGIN_INTEREST_RATE} (or updated rate from CSV if available)
- **Monthly Interest Cost**: Calculate (Balance × Rate ÷ 12)
- **Notes**: Auto-generate based on elapsed time since ${FG_STRATEGY_START_DATE}

**Example Entry**:
```
Date: ${FG_MARGIN_EXAMPLE_DATE}
Margin Balance: ${FG_MARGIN_BASELINE_BALANCE}
Interest Rate: ${FG_MARGIN_INTEREST_RATE}
Monthly Interest Cost: ${FG_MARGIN_MONTHLY_INTEREST_COST}
Notes: Month 1 - Building foundation, on track per strategy
```

**Notes Generation Logic**:
```python
import os
from datetime import datetime

months_elapsed = (current_date - datetime.fromisoformat(os.getenv("FG_STRATEGY_START_DATE"))).days // 30

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
Example: ${FG_MARGIN_BASELINE_BALANCE}
```

#### Monthly Interest Cost
```
= Latest calculated cost
Example: ${FG_MARGIN_MONTHLY_INTEREST_COST}/month
```

#### Annual Interest Cost
```
= Monthly Interest Cost × 12
Example: ${FG_MARGIN_MONTHLY_INTEREST_COST} × 12 = ${FG_MARGIN_ANNUAL_INTEREST_COST}/year
```

#### Dividend Income (from Dividend Tracker)
```
= Pull from Dividend Tracker "TOTAL EXPECTED DIVIDENDS"
Example: ${FG_DIVIDEND_MONTHLY_INCOME}/month
```

#### Coverage Ratio
```
= Dividend Income ÷ Monthly Interest Cost
Formula: =IFERROR(Dividends / Interest, 0)
Example: ${FG_DIVIDEND_MONTHLY_INCOME} ÷ ${FG_MARGIN_MONTHLY_INTEREST_COST} = ${FG_DIVIDEND_COVERAGE_RATIO} 🟢
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
Example: ${FG_PORTFOLIO_BASELINE_VALUE} ÷ ${FG_MARGIN_BASELINE_BALANCE} = ${FG_PORTFOLIO_MARGIN_RATIO} 🟢🟢🟢
```

**Safety Thresholds**:
- 🟢 **Green**: Ratio > 4.0:1 (target - healthy margin usage)
- 🟡 **Yellow**: Ratio 3.5-4.0:1 (warning - pause scaling)
- 🔴 **Red**: Ratio < 3.0:1 (alert - stop draws, inject business income)
- ⚫ **Critical**: Ratio < 2.5:1 (emergency - inject ${FG_BUSINESS_INJECTION_CRITICAL}, consider selling)

#### Current Draw vs Fixed Expenses
```
Current monthly draw: ${FG_CURRENT_MONTHLY_DRAW} (fixed expenses only)
Target: Start with ${FG_CURRENT_MONTHLY_DRAW}, scale to ${FG_MONTH6_DRAW_TARGET}, ${FG_MONTH12_DRAW_TARGET}, ${FG_MONTH18_DRAW_TARGET} based on data
```

### 6. Scaling Alerts (Time-Based)

**Strategy Start Date**: ${FG_STRATEGY_START_DATE}

**Calculate months elapsed**:
```python
import os
from datetime import datetime

start = datetime.fromisoformat(os.getenv("FG_STRATEGY_START_DATE"))
current = datetime.now()
months_elapsed = (current - start).days // 30
```

#### Month 6 Alert
```
📊 MONTH 6 MILESTONE CHECK:
✅ Dividends: ${FG_DIVIDEND_MONTHLY_INCOME}/month (need ${FG_MONTH6_DIVIDEND_MINIMUM})
✅ Portfolio-to-Margin Ratio: ${FG_PORTFOLIO_MARGIN_RATIO} (need 4:1+)
✅ Dividend Growth: On track

🎯 RECOMMENDATION: Scale margin draw to ${FG_MONTH6_DRAW_TARGET}/month (add mortgage)
- Current: ${FG_CURRENT_MONTHLY_DRAW} (fixed expenses only)
- New: ${FG_MONTH6_DRAW_TARGET} (fixed + mortgage)
- Safety margin: Excellent
```

#### Month 12 Alert
```
📊 MONTH 12 BREAK-EVEN CHECK:
Expected Dividends: ${FG_MONTH12_DIVIDEND_TARGET}/month (goal: break-even with margin interest)
✅ IF achieved: Consider scaling to ${FG_MONTH12_DRAW_TARGET}/month (add some variable expenses)
⚠️ IF not: Hold at ${FG_MONTH6_DRAW_TARGET}, assess strategy
```

#### Month 18 Alert
```
📊 MONTH 18 MATURE STRATEGY CHECK:
Expected Dividends: ${FG_MONTH18_DIVIDEND_TARGET}/month
Expected Margin: Declining (dividends paying down debt)
✅ IF achieved: Consider scaling to ${FG_MONTH18_DRAW_TARGET}/month (most variable expenses)
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
Action: STOP draws, inject ${FG_BUSINESS_INJECTION_RED} business income
```

#### Critical (Emergency)
```
⛔ Ratio < 2.5:1 OR margin call risk
Action: STOP draws, inject ${FG_BUSINESS_INJECTION_CRITICAL} business income, consider selling hedge (SQQQ)
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
3. **Business income as insurance**: Available ${FG_BUSINESS_INCOME_MONTHLY}/month, not primary strategy
4. **Monte Carlo backstop**: ${FG_BUSINESS_BACKSTOP_PROBABILITY} of scenarios used business income at some point

## Business Income Backstop

**Available**: ${FG_BUSINESS_INCOME_MONTHLY}/month from business operations

**Usage Scenarios**:
1. ⛔ **Margin call (ratio < 3:1)**: MUST USE business income immediately
2. ⚠️ **Market correction (20-30% drop)**: OPTIONAL - assess need
3. 🎯 **Acceleration (reach FI faster)**: OPTIONAL - strategic choice

**Current Philosophy**: Insurance policy only, not active strategy component

## Example Calculations

### Scenario 1: Month 1 (Current State)
```
Portfolio Value: ${FG_PORTFOLIO_BASELINE_VALUE}
Margin Balance: ${FG_MARGIN_BASELINE_BALANCE}
Ratio: ${FG_PORTFOLIO_MARGIN_RATIO} 🟢🟢🟢

Monthly Interest: ${FG_MARGIN_MONTHLY_INTEREST_COST}
Dividend Income: ${FG_DIVIDEND_MONTHLY_INCOME}
Coverage: ${FG_DIVIDEND_COVERAGE_RATIO} 🟢

Status: Excellent - building foundation
```

### Scenario 2: Month 6 (Projected)
```
Portfolio Value: ${FG_MONTH6_PROJECTED_PORTFOLIO} (projected with W2 contributions)
Margin Balance: ${FG_MONTH6_PROJECTED_MARGIN} (scaled to ${FG_MONTH6_DRAW_TARGET}/month draw)
Ratio: ${FG_MONTH6_PROJECTED_RATIO} 🟢

Monthly Interest: ${FG_MONTH6_PROJECTED_MONTHLY_INTEREST}
Dividend Income: ${FG_CURRENT_MONTHLY_DRAW} (projected)
Coverage: ${FG_MONTH6_PROJECTED_COVERAGE} 🟢

Status: Healthy - on track for break-even
```

### Scenario 3: Month 15 (Break-Even)
```
Portfolio Value: ${FG_MONTH15_PROJECTED_PORTFOLIO}
Margin Balance: ${FG_MONTH15_PROJECTED_MARGIN} (scaled to ${FG_MONTH12_DRAW_TARGET}/month draw)
Ratio: ${FG_MONTH15_PROJECTED_RATIO} 🟢

Monthly Interest: ${FG_MONTH15_PROJECTED_MONTHLY_INTEREST}
Dividend Income: ${FG_MONTH15_PROJECTED_DIVIDEND_INCOME}
Coverage: ${FG_MONTH15_PROJECTED_COVERAGE} 🟢

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
1. ✅ Read Balances CSV - Portfolio: ${FG_PORTFOLIO_BASELINE_VALUE}, Margin: ${FG_MARGIN_BASELINE_BALANCE}
2. ✅ Safety check - Previous: $0, Current: ${FG_MARGIN_BASELINE_BALANCE} (+${FG_MARGIN_BASELINE_BALANCE} < ${FG_MARGIN_JUMP_ALERT_THRESHOLD} threshold) - PASS
3. ✅ Calculate metrics:
   - Monthly interest: ${FG_MARGIN_MONTHLY_INTEREST_COST}
   - Portfolio-to-margin ratio: ${FG_PORTFOLIO_MARGIN_RATIO}
   - Coverage ratio: ${FG_DIVIDEND_COVERAGE_RATIO} (dividends ÷ interest)
4. ✅ Add entry to Margin Dashboard:
   - Date: ${FG_MARGIN_EXAMPLE_DATE}
   - Balance: ${FG_MARGIN_BASELINE_BALANCE}
   - Rate: ${FG_MARGIN_INTEREST_RATE}
   - Cost: ${FG_MARGIN_MONTHLY_INTEREST_COST}
   - Notes: "Month 1 - Building foundation, on track"
5. ✅ Update summary section:
   - Current balance: ${FG_MARGIN_BASELINE_BALANCE}
   - Monthly cost: ${FG_MARGIN_MONTHLY_INTEREST_COST}
   - Annual cost: ${FG_MARGIN_ANNUAL_INTEREST_COST}
   - Dividend income: ${FG_DIVIDEND_MONTHLY_INCOME}
   - Coverage: ${FG_DIVIDEND_COVERAGE_RATIO}
6. ✅ Generate status: "🟢 Excellent health - Ratio ${FG_PORTFOLIO_MARGIN_RATIO}, Coverage ${FG_DIVIDEND_COVERAGE_RATIO}"
7. ✅ LOG: "Updated Margin Dashboard - Month 1, ${FG_MARGIN_BASELINE_BALANCE} balance, ${FG_PORTFOLIO_MARGIN_RATIO} ratio"

---

**Skill Type**: Domain (workflow guidance)
**Enforcement**: BLOCK (financial risk critical)
**Priority**: Critical
**Line Count**: < 400 (following 500-line rule) ✅
