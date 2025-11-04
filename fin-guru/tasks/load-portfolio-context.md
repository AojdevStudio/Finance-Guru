# Load Portfolio Context

**Task ID:** `load-portfolio-context`
**Category:** System Initialization
**Required By:** All financial specialists before analysis
**Auto-Run:** Yes (in agent critical-actions)

---

## Purpose

Load current portfolio positions and key metrics into the agent's working memory to ensure all recommendations and analysis are based on real-time portfolio state.

---

## Execution Steps

### 1. Locate Latest Portfolio Export

Find the most recent portfolio CSV within `notebooks/` (lists every match so you can confirm the latest export):

```bash
cd /Users/ossieirondi/Documents/Irondi-Household/family-office && find notebooks -name "Portfolio_Positions*.csv" -type f 2>/dev/null
```

Expected format: `Portfolio_Positions_[YYYY-MM-DD].csv` or `Portfolio_Positions_[MonthName-DD-YYYY].csv`

### 2. Load Portfolio Data

Read the latest CSV file using the Read tool.

### 2a. Load Account Balance Data

Check for margin and balance information:

```bash
cd /Users/ossieirondi/Documents/Irondi-Household/family-office && ls notebooks/updates/Balances_for_Account_Z05724592.csv 2>/dev/null
```

If the balance file exists, read it using the Read tool. This file contains:
- Total account value
- Cash available
- Margin debit balance (amount borrowed)
- Buying power
- Margin maintenance requirement
- Other balance-related metrics

**Note:** If balance file is not found, agent should note this and proceed with positions-only analysis. The balance file is optional but highly recommended for margin strategy analysis.

### 3. Extract Key Metrics

Calculate and store in session memory:

**Portfolio Summary:**
- Total portfolio value (sum of Current Value column)
- Cash available (SPAXX** Current Value)
- Invested capital (Total - Cash)
- Today's gain/loss (sum of Today's Gain/Loss Dollar)
- Total gain/loss (sum of Total Gain/Loss Dollar)
- All-time return percentage

**Position Breakdown:**
- Margin positions: Sum all rows where Type = "Margin"
- Cash positions: Sum all rows where Type = "Cash"
- Margin/Cash ratio

**Top Holdings (Top 5 by Current Value):**
- Ticker
- Current Value
- Percent of Account
- Total Gain/Loss %

**Pending Activity:**
- Check for "Pending activity" row
- Note amount if present

**Margin & Balance Data (if balance file available):**
- Margin debit balance (amount borrowed)
- Buying power available
- Margin maintenance requirement
- Portfolio-to-margin ratio (Total Value / Margin Debit)
- Margin utilization percentage

### 4. Validation Checks

Before proceeding, verify:
- ✅ Total portfolio value > $0
- ✅ At least 5 positions found
- ✅ Data downloaded today or yesterday (check date in filename or footer)
- ⚠️ If data is >2 days old, warn user

### 5. Store Context

Create a structured summary in working memory:

```
PORTFOLIO CONTEXT LOADED: [Date from filename]

OVERVIEW:
- Total Value: $XXX,XXX
- Cash Available: $X,XXX
- Today's Performance: +/- $X,XXX (+/- X.XX%)
- All-Time Return: +$XX,XXX (+XX.XX%)

POSITION STRUCTURE:
- Margin Positions: $XXX,XXX (XX%)
- Cash Positions: $XX,XXX (XX%)

MARGIN STATUS (if balance file loaded):
- Margin Debit Balance: $XX,XXX (amount borrowed)
- Buying Power: $XX,XXX
- Portfolio-to-Margin Ratio: X.XX:1
- ⚠️ Margin Utilization: XX%

TOP 5 HOLDINGS:
1. TICKER ($XX,XXX, XX% of portfolio, +XX% gain)
2. TICKER ($XX,XXX, XX% of portfolio, +XX% gain)
3. TICKER ($XX,XXX, XX% of portfolio, +XX% gain)
4. TICKER ($XX,XXX, XX% of portfolio, +XX% gain)
5. TICKER ($XX,XXX, XX% of portfolio, +XX% gain)

CONCENTRATION RISK:
- Top 2 positions: XX% combined
- Top 5 positions: XX% combined

PENDING ACTIVITY: $X,XXX (if any)

✅ Portfolio context ready for analysis
```

---

## Error Handling

**If no CSV found:**
- Alert user: "No portfolio export found in notebooks/updates/. Please download latest positions from Fidelity."
- Provide instructions for export location

**If CSV is malformed:**
- Alert user: "Portfolio CSV format unexpected. Please verify export is from Fidelity positions download."
- Show first few rows for debugging

**If data is stale (>2 days old):**
- ⚠️ Warning: "Portfolio data is from [date], which is X days old. Recommendations may not reflect current positions."
- Ask user if they want to proceed or update data first

---

## Agent Integration

**In agent `<critical-actions>`:**

```xml
<i>Execute task: load-portfolio-context.md before any portfolio analysis or recommendations</i>
```

**When to skip:**
- User is asking general educational questions (not portfolio-specific)
- User is asking about market news/events (not their positions)
- User explicitly says "don't load my portfolio"

**When mandatory:**
- Making buy/sell recommendations
- Analyzing risk exposure
- Discussing position sizing
- Rebalancing suggestions
- Performance analysis

---

## Output Format

This task should produce:
1. Console output confirming load success
2. Structured summary stored in agent memory
3. Ready state for agent to proceed with user request

---

## Notes

- This task does NOT modify any files
- This task does NOT make trading recommendations
- This task ONLY loads data into memory
- Portfolio CSV should remain in `notebooks/updates/` for historical tracking
- Agents should reference this loaded context throughout the session

---

**Last Updated:** 2025-10-31
**Maintained By:** Finance Orchestrator (Cassandra Holt)
