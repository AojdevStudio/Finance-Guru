# Google Sheets Quick Reference for Agents
<!-- CONDENSED VERSION - Full docs: spreadsheet-architecture.md -->

## 🚦 Can I Write to This Tab?

| Your Agent Role | DataHub | Dividend Tracker | Margin Dashboard |
|----------------|---------|------------------|------------------|
| **Builder** | ✅ WRITE (A,B,G) | ✅ Full access | ✅ Full access |
| **Strategy Advisor** | ✅ WRITE (A,B,G) | ❌ Read-only | ❌ Read-only |
| **Dividend Specialist** | ❌ Read-only | ✅ Full access | ❌ Read-only |
| **Margin Specialist** | ❌ Read-only | ❌ Read-only | ✅ Full access |
| **All Others** | ❌ Read-only | ❌ Read-only | ❌ Read-only |

---

## ⚠️ STOP Immediately If...

- [ ] Fidelity CSV has **fewer tickers** than current sheet (possible sale)
- [ ] Any ticker **quantity changes >10%** (possible split or big trade)
- [ ] Update would create **3+ formula errors** (#N/A, #DIV/0!, #REF!)
- [ ] **Margin balance jumps >$5k** in single update (confirm with user)

---

## 📋 DataHub - CRITICAL RULES

### 🎯 Sheet Structure:
- **Rows 2-40**: Active Portfolio (Fidelity TOD) - **FINANCE GURU FOCUS**
- **Rows 45-64**: Retirement Accounts (Vanguard/401k) - **TRACKING ONLY**
- **Rows 67+**: Cryptocurrency Holdings (BTC) - **TRACKING ONLY**

### ✅ YOU CAN (when requested):
**Active Portfolio (Rows 2-40)** - from Fidelity CSV:
- Update **Column A** (Ticker Symbol)
- Update **Column B** (Quantity)
- Update **Column G** (Avg Cost Basis)
- Add new rows for new positions

**Retirement Accounts (Rows 45-64)** - from `notebooks/retirement-accounts/`:
- Update **Column A** (Ticker Symbol)
- Update **Column B** (Quantity)
- **NO Column G** (retirement accounts don't track cost basis)
- Frequency: Monthly updates only

**Cryptocurrency (Rows 67+)** - when user provides data:
- Update **Column A** (Ticker Symbol - e.g., BTC)
- Update **Column B** (Quantity)
- Update **Column C** (Price - manual, not Google Finance)

### ❌ YOU CANNOT:
- Touch **Column C** (Last Price - Google Finance formula auto-updates) **EXCEPT crypto rows**
- Touch **Columns D-F** ($ Change, % Change, Volume - formulas/Alpha Vantage)
- Touch **Columns H-M** (Gains/Losses - calculated formulas)
- Touch **Columns N-S** (Ranges, dividends, layer - formulas or manual)
- Delete rows without user confirmation
- Modify formulas in ANY column
- **Include retirement/crypto in Finance Guru strategy analysis**

### 🎯 Adding New Positions:
```
IF ticker = [JEPI, JEPQ, CLM, CRF, QQQI, SPYI, QQQY, YMAX, MSTY, AMZY]:
    Layer = "Layer 2 - Dividend"
ELSE IF ticker = [SQQQ, UVXY, VXX]:
    Layer = "Layer 3 - Protection"
ELSE IF ticker = [PLTR, TSLA, NVDA, AAPL, GOOGL, MSTR, COIN, SOFI]:
    Layer = "Layer 1 - Growth"
ELSE IF ticker = [VOO, VTI, QQQ, FNILX, FZROX, FZILX]:
    Layer = "Layer 1 - Growth"
ELSE:
    Layer = "UNKNOWN - ALERT USER"
```

---

## 💰 Dividend Tracker - Update Checklist

1. **Read tickers from DataHub** (Layer 2 only)
2. **Match shares** - Flag if mismatched
3. **Add new funds** - Auto-add any Layer 2 ticker not in tracker
4. **Calculate totals** - Total Dividend $ = Shares × Dividend Per Share
5. **Fix #N/A errors** - Usually in "TOTAL EXPECTED DIVIDENDS" sum

---

## 📊 Margin Dashboard - Update Checklist

1. **Read Balances CSV**: `notebooks/updates/Balances_for_Account_Z05724592.csv`
2. **Extract**:
   - Total account value (Portfolio Value)
   - Net debit (Margin Balance)
   - Interest rate (default: 10.875%)
3. **Safety Check**: If balance jumps >$5k, STOP and confirm
4. **Add row**: Date, Balance, Rate, Monthly Cost (Balance × Rate ÷ 12)
5. **Update summary**:
   - Portfolio-to-Margin Ratio = Portfolio Value ÷ Margin Balance
   - Coverage Ratio = Dividends ÷ Interest Cost

---

## 🏦 Retirement Accounts - Update Checklist (Monthly)

1. **Read CSVs**: `notebooks/retirement-accounts/*.csv` (Vanguard + 401k exports)
2. **Parse holdings**:
   - Symbol (→ Column A)
   - Quantity (→ Column B)
   - **NO cost basis** (Column G stays empty)
3. **Update rows 45-64**: Ticker and quantity only
4. **Add Google Finance formulas**: Column C = `=GOOGLEFINANCE(A{row}, "price")` for supported tickers
5. **Manual pricing**: For unsupported tickers (VMFXX, VGINF), enter price manually in Column C
6. **⚠️ CRITICAL**: Do NOT include retirement accounts in Finance Guru strategy analysis

---

## ₿ Cryptocurrency - Update Checklist (As Needed)

1. **User provides**: BTC quantity and current price
2. **Update Row 68** (or add new rows for additional crypto):
   - Column A: Ticker (BTC, ETH, etc.)
   - Column B: Quantity (e.g., 4.03)
   - Column C: Price (manual entry - not Google Finance)
3. **⚠️ CRITICAL**: Do NOT include crypto in Finance Guru strategy analysis

---

## 🔧 Formula Repair - Allowed Operations

### ✅ YOU CAN FIX:
- Add `IFERROR(formula, 0)` wrappers
- Fix broken sheet references (`Sheet1!A1` → `DataHub!A1`)
- Expand ranges if data grew (`A2:A50` → `A2:A100`)

### ❌ YOU CANNOT:
- Change formula logic (SUM → AVERAGE)
- Replace formulas with static values
- Modify working formulas "for optimization"

---

## 📝 Pre-Flight Checklist (Before ANY Write)

- [ ] **Am I allowed?** (Check role matrix above)
- [ ] **Right columns?** (Portfolio = A, B, G only - from CSV)
- [ ] **Safety gates?** (Position count, quantity >10%, cost basis >20%, margin >$5k)
- [ ] **Formula safe?** (Not touching Column C Google Finance or other formulas)
- [ ] **Will this break anything?** (Test if unsure)
- [ ] **Logged change?** (Document what and why)

**Golden Rule**: When in doubt, READ-ONLY and ASK USER.

**Data Sources**:
- **Active Portfolio (Rows 2-40)**:
  - Columns A, B, G: From Fidelity CSV (`Portfolio_Positions_MMM-DD-YYYY.csv`)
  - Column C: Google Finance formula `=GOOGLEFINANCE(A{row}, "price")` - AUTO-UPDATES
- **Retirement Accounts (Rows 45-64)**:
  - Columns A, B: From `notebooks/retirement-accounts/*.csv` (Vanguard/401k)
  - Column C: Google Finance formula OR manual pricing (VGINF, VMFXX, etc.)
  - **Update frequency**: Monthly
- **Cryptocurrency (Rows 67+)**:
  - Columns A, B, C: Manual entry from user
  - **Update frequency**: As needed

---

## 🆘 Emergency

**If you break something**:
1. STOP immediately
2. Alert user with exact cell location
3. User restores via: File → Version History → See Version History

**If data looks wrong**:
1. Verify Fidelity CSV is correct source
2. Check for upstream formula errors
3. Flag for user review - DON'T ASSUME

---

**Full Documentation**: `fin-guru/data/spreadsheet-architecture.md`
**Last Updated**: 2025-11-12
