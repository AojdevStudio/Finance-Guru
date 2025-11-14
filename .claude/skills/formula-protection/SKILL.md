---
name: formula-protection
description: Prevent accidental modification of sacred spreadsheet formulas in Google Sheets Portfolio Tracker. Blocks edits to GOOGLEFINANCE formulas, calculated columns, and total rows. Allows only IFERROR wrappers, fixing broken references, and expanding ranges. Triggers on update formula, modify column, fix errors, or any attempt to edit formula-based cells.
---

# Formula Protection

## Purpose

**GUARDRAIL SKILL** - Prevents accidental modification or deletion of critical formulas that maintain spreadsheet integrity. Ensures financial data accuracy by protecting auto-calculated columns.

## When to Use (Auto-Blocks)

This skill **automatically blocks** when detecting:
- Attempts to "update formula", "modify formula", "change formula"
- Editing Column C (GOOGLEFINANCE price formulas)
- Modifying Columns D-F, H-S (calculated formulas)
- Fixing formula errors (#N/A, #DIV/0!, #REF!) without proper protocol
- User mentions: "fix formula", "edit cell", "update column C/D/E"

**This is a BLOCKING skill** - You MUST use this skill before proceeding with any formula-related edits.

## Sacred Formulas (NEVER TOUCH)

### DataHub Tab

**Column C: Last Price**
```
=GOOGLEFINANCE(A2, "price")
```
- Auto-updates stock prices in real-time
- ❌ **NEVER modify** - prices must come from Google Finance
- ❌ **NEVER replace with static values**
- ✅ **ONLY wrap with IFERROR** if showing #N/A for delisted stocks

**Columns D-E: $ Change, % Change**
```
=C2 - G2  ($ Change)
=D2 / G2  (% Change)
```
- Calculated from Last Price (C) and Avg Cost Basis (G)
- ❌ **NEVER touch** - let formulas calculate automatically

**Columns H-M: Gains/Losses**
```
=L2 - M2  (Total G/L $)
=K2 / M2  (Total G/L %)
=B2 * C2  (Current Value)
=B2 * G2  (Cost Basis Total)
```
- Core portfolio performance metrics
- ❌ **NEVER modify** - accuracy depends on these formulas
- ✅ **ONLY add IFERROR** if #DIV/0! errors appear

**Columns N-S: Advanced Metrics**
- Contains ranges, dividend data, layer classifications
- Mix of formulas and manual classifications
- ⚠️ **Consult spreadsheet-architecture.md before editing**

### Dividend Tracker Tab

**Column F: Total Dividend $**
```
=D2 * E2  (Shares × Dividend Per Share)
```
- Calculates expected dividend income per fund
- ❌ **NEVER modify** - must remain formula-driven

**Total Row Formula**
```
=SUM(F2:F50)  (TOTAL EXPECTED DIVIDENDS)
```
- Sums all dividend income
- ❌ **NEVER delete or modify**
- ✅ **ONLY expand range** if data grows beyond row 50

### Margin Dashboard Tab

**Coverage Ratio**
```
=IFERROR(B10 / B11, 0)  (Dividends ÷ Interest Cost)
```
- Critical safety metric for margin strategy
- ❌ **NEVER remove IFERROR wrapper**
- ✅ **ONLY update** if adding new safety thresholds

## Allowed Operations

### ✅ SAFE: Add IFERROR() Wrappers

**Purpose**: Prevent error display without changing logic

**Example**:
```
Before: =GOOGLEFINANCE(A2, "price")
After: =IFERROR(GOOGLEFINANCE(A2, "price"), "N/A")

Before: =B10 / B11
After: =IFERROR(B10 / B11, 0)
```

**When to use**:
- #N/A errors from delisted stocks (GOOGLEFINANCE failures)
- #DIV/0! errors when margin balance = $0
- #REF! errors from deleted rows (use IFERROR as temporary fix)

### ✅ SAFE: Fix Broken Sheet References

**Purpose**: Correct renamed or moved sheet names

**Example**:
```
Before: =Sheet1!A1
After: ='DataHub'!A1

Before: ='Dividend Tracker OLD'!B10
After: ='Dividend Tracker'!B10
```

**When to use**:
- Sheet was renamed (Sheet1 → DataHub)
- Sheet was duplicated and old reference remains
- Tab moved to different position

### ✅ SAFE: Expand Formula Ranges

**Purpose**: Include new data rows without changing logic

**Example**:
```
Before: =SUM(F2:F50)
After: =SUM(F2:F100)

Before: =AVERAGE(B2:B30)
After: =AVERAGE(B2:B50)
```

**When to use**:
- New portfolio positions added beyond row 50
- Dividend tracker grows beyond expected size
- Margin dashboard accumulates monthly entries

### ✅ SAFE: Fix Cell Reference Typos

**Purpose**: Correct obvious mistakes in formula construction

**Example**:
```
Before: =B100 * C100  (B100 doesn't exist)
After: =B10 * C10

Before: =A2 + A2  (duplicate cell reference)
After: =A2 + B2  (correct cells)
```

**When to use**:
- Formula references non-existent row
- Clear typo in cell reference
- Formula clearly broken due to manual error

## Forbidden Operations

### ❌ NEVER: Change Formula Logic

**Example of what NOT to do**:
```
❌ =SUM(F2:F50) → =AVERAGE(F2:F50)  (changes meaning)
❌ =B2 * C2 → =B2 + C2  (changes calculation)
❌ =GOOGLEFINANCE(A2, "price") → =GOOGLEFINANCE(A2, "volume")
```

**Why**: Changes the meaning of calculated data, breaks dashboard integrity

### ❌ NEVER: Replace Formulas with Static Values

**Example of what NOT to do**:
```
❌ =GOOGLEFINANCE("TSLA", "price") → 445.47  (hardcoded)
❌ =B2 * C2 → 32964.78  (static value)
❌ =SUM(F2:F50) → 2847.32  (loses dynamic calculation)
```

**Why**: Data becomes stale, no longer updates automatically

### ❌ NEVER: Delete Formulas

**Example of what NOT to do**:
```
❌ Deleting Column C (Last Price formulas) to "clean up"
❌ Removing total row formulas to "simplify"
❌ Clearing formula cells to "start fresh"
```

**Why**: Destroys data pipeline, breaks all dependent calculations

### ❌ NEVER: Modify GOOGLEFINANCE Parameters

**Example of what NOT to do**:
```
❌ =GOOGLEFINANCE(A2, "price") → =GOOGLEFINANCE(A2, "closeyest")
❌ =GOOGLEFINANCE("TSLA", "price") → =GOOGLEFINANCE("NASDAQ:TSLA", "price")
```

**Why**: May break price lookups, change data source unexpectedly

## Smart Formula Repair Workflow

### Step 1: Identify Error Type

**Scan spreadsheet for**:
- #N/A (not available - usually GOOGLEFINANCE or VLOOKUP failures)
- #DIV/0! (division by zero - usually margin calculations when balance = $0)
- #REF! (reference error - deleted rows/columns)
- #VALUE! (wrong data type - rare in financial sheets)

### Step 2: Classify Repair Strategy

#### For #N/A Errors:

**GOOGLEFINANCE failures** (Column C):
```
Cause: Stock delisted, ticker invalid, or Google Finance API issue
Solution: Wrap with IFERROR()
=IFERROR(GOOGLEFINANCE(A2, "price"), "DELISTED")
```

**VLOOKUP failures** (if used):
```
Cause: Lookup value doesn't exist in source data
Solution: Check source data exists, expand range, or add IFERROR()
=IFERROR(VLOOKUP(A2, Data!A:B, 2, FALSE), "NOT FOUND")
```

#### For #DIV/0! Errors:

**Margin coverage ratio** (when margin = $0):
```
Before: =B10 / B11
After: =IFERROR(B10 / B11, 0)
```

**Percentage calculations** (when denominator = 0):
```
Before: =K2 / M2
After: =IFERROR(K2 / M2, 0)
```

#### For #REF! Errors:

**Deleted rows/columns**:
```
Cause: Formula references Sheet1!A10 but row 10 was deleted
Solution: If temporary, wrap with IFERROR(). If permanent, reconstruct formula.
Temporary: =IFERROR(Sheet1!A10, 0)
Permanent: Identify correct new reference and update
```

### Step 3: Test Repair on Single Cell

**Before applying broadly**:
1. Copy original formula to notes (for rollback)
2. Apply repair to ONE cell
3. Verify result looks correct
4. Check no new errors introduced
5. If successful, apply to other similar errors

### Step 4: Validate No New Errors

**After repair**:
- Scan entire sheet for new #N/A, #DIV/0!, #REF!
- Verify totals still sum correctly
- Check formulas still reference correct cells
- Confirm no unexpected data changes

### Step 5: Document Repair

**Log all changes**:
```
✅ Fixed #DIV/0! in Margin Dashboard C10 by adding IFERROR()
Formula change: =B10/B11 → =IFERROR(B10/B11, 0)
Reason: Margin balance was $0 causing division by zero
Date: 2025-11-11
```

## Pre-Flight Checklist (Before Editing Formulas)

**Ask yourself**:
- [ ] Am I trying to modify a formula-based column? (C, D-F, H-S)
- [ ] Is this a GOOGLEFINANCE formula? (**STOP** - don't touch)
- [ ] Is this a total/summary formula? (**STOP** - don't touch)
- [ ] Am I changing formula logic? (**STOP** - forbidden)
- [ ] Am I replacing formula with static value? (**STOP** - forbidden)
- [ ] Am I adding IFERROR to existing formula? (✅ Allowed)
- [ ] Am I fixing a broken sheet reference? (✅ Allowed)
- [ ] Am I expanding a range for new data? (✅ Allowed)
- [ ] Have I consulted `spreadsheet-architecture.md`? (Required)

**If ANY stop condition triggered**: Use this skill, review rules, proceed with caution

## Emergency Rollback Procedure

**If formula modification breaks the spreadsheet**:

1. **STOP immediately** - Do not attempt additional fixes
2. **Alert user** - Clearly explain what went wrong
3. **Document the error**:
   - Which cell/column was modified
   - What formula change was made
   - What error occurred (new #N/A, wrong calculations, etc.)
4. **Restore from Google Sheets version history**:
   - File → Version History → See Version History
   - Find last working version (before modification)
   - Click "Restore this version"
5. **Learn from it** - Update this skill if new edge case discovered

## Example Scenarios

### ❌ WRONG: Modifying Last Price Formula

**User request**: "The price for TSLA isn't updating, let me fix the formula"

**Agent response**:
```
🛑 BLOCKED by formula-protection skill

You're attempting to modify Column C (Last Price) which contains GOOGLEFINANCE formulas.
These are sacred formulas and must NEVER be modified.

If TSLA price isn't updating, the issue is likely:
1. Google Finance API delay (wait 5-10 minutes)
2. Market is closed (prices only update during trading hours)
3. Ticker symbol incorrect (verify "TSLA" is correct)

❌ Do NOT modify =GOOGLEFINANCE(A2, "price")
✅ If truly broken, wrap with: =IFERROR(GOOGLEFINANCE(A2, "price"), "N/A")
```

### ✅ RIGHT: Adding IFERROR Wrapper

**User request**: "Column C shows #N/A for delisted stock, can you fix?"

**Agent response**:
```
✅ Using formula-protection skill

I'll safely wrap the GOOGLEFINANCE formula with IFERROR() to handle the delisted stock.

Before: =GOOGLEFINANCE(A45, "price")
After: =IFERROR(GOOGLEFINANCE(A45, "price"), "DELISTED")

This preserves the formula logic while displaying "DELISTED" instead of #N/A.
The formula will still work if the stock relists in the future.

✅ Safe operation - formula logic unchanged
```

### ✅ RIGHT: Expanding Summary Range

**User request**: "Total dividends formula only goes to row 50, but I have 55 funds now"

**Agent response**:
```
✅ Using formula-protection skill

I'll safely expand the SUM range to include all 55 funds.

Before: =SUM(F2:F50)
After: =SUM(F2:F100)

This expands the range to accommodate current data (55 funds) plus room for growth.
Formula logic unchanged - still summing Total Dividend $ column.

✅ Safe operation - range expanded, logic preserved
```

## Google Sheets Integration

**Spreadsheet ID**: Read from `fin-guru/data/user-profile.yaml` → `google_sheets.portfolio_tracker.spreadsheet_id`

**Use the mcp__gdrive__sheets tool**:

**Read-only operations** (to detect formula errors):
```javascript
// STEP 1: Read Spreadsheet ID from user profile
// Load fin-guru/data/user-profile.yaml
// Extract: google_sheets.portfolio_tracker.spreadsheet_id

// STEP 2: Scan for errors
mcp__gdrive__sheets(
    operation: "spreadsheets.values.get",
    params: {
        spreadsheetId: SPREADSHEET_ID,  // from user-profile.yaml
        range: "DataHub!A1:Z100"
    }
)
// Check for #N/A, #DIV/0!, #REF! in returned values
```

**Write operations** (only for safe repairs):
```javascript
// Add IFERROR wrapper to fix formula errors
mcp__gdrive__sheets(
    operation: "spreadsheets.values.update",
    params: {
        spreadsheetId: SPREADSHEET_ID,  // from user-profile.yaml
        range: "DataHub!C2:C2",
        valueInputOption: "USER_ENTERED",
        requestBody: {
            values: [["=IFERROR(GOOGLEFINANCE(A2, \"price\"), \"N/A\")"]]
        }
    }
)
```

## Agent Permissions

**Builder** (Write-enabled with formula-protection):
- Can add IFERROR wrappers
- Can fix broken sheet references
- Can expand formula ranges
- Can fix cell reference typos
- MUST follow this skill's rules

**All Other Agents** (Strictly Read-only):
- Market Researcher, Quant Analyst, Strategy Advisor, Margin Specialist, Dividend Specialist
- Can read all data including formulas
- **CANNOT modify any formulas**
- Must defer to Builder for any formula repairs
- Should alert Builder if formula errors detected

## Reference Files

For complete details, see:
- **Spreadsheet Architecture**: `fin-guru/data/spreadsheet-architecture.md` (lines 380-440)
- **Quick Reference**: `fin-guru/data/spreadsheet-quick-ref.md`
- **Agent Permissions**: `fin-guru/data/spreadsheet-architecture.md` (lines 91-136)

## Key Takeaways

**Remember**:
- 🛑 **Formulas are sacred** - Default assumption is DON'T TOUCH
- ✅ **IFERROR is your friend** - Safe way to handle errors
- 📖 **Consult docs first** - Read spreadsheet-architecture.md before any edit
- 🤝 **Ask user if unsure** - Better to ask than break financial data
- 🔄 **Google Sheets has version history** - Mistakes can be rolled back

**When in doubt**: READ-ONLY and ASK USER for guidance.

---

**Skill Type**: Guardrail (safety mechanism)
**Enforcement**: BLOCK (prevents formula modifications)
**Priority**: Critical
**Line Count**: < 500 (following 500-line rule) ✅
