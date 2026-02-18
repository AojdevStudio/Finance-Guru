# Financial Structure Assessment Orientation
<!-- Finance Guru™ Task | v1.0 | 2025-09-25 -->

## Overview
First-time user orientation using personalized financial assessment data to configure Finance Guru™ for optimal guidance.

## Workflow Steps

### 1. Check for Existing Assessment
```
CHECK: Look for Financial Structure Assessment CSV in:
- research/finance/Financial Structure Assessment (Responses)*.csv
- User's provided file path
- Google Drive connected workspace
```

### 2A. If Assessment Exists
```
PARSE: Extract key financial metrics:
- Total liquid assets across checking/savings
- Investment account balances and allocations
- Monthly income (after-tax)
- Fixed and variable expenses
- Current savings/investment rate
- Debt structure and rates
- Risk profile and investment philosophy
```

### 2B. If No Assessment
```
CREATE: Generate assessment form via Google Drive MCP
- Use template questions from existing form structure
- Create Google Form with following sections:
  * Liquid Assets Structure
  * Investment Accounts
  * Income & Expenses
  * Debt Profile
  * Risk Tolerance
  * Investment Goals
```

### 3. Profile Generation
```
BUILD: Create personalized user profile:
- Financial Health Score (based on ratios)
- Opportunity Areas (high-interest debt, low-yield savings)
- Investment Capacity (monthly surplus for investing)
- Risk-Adjusted Strategy Recommendations
- Priority Action Items
```

### 4. Configuration
```
CONFIGURE: Set Finance Guru parameters:
- Default risk tolerance level
- Preferred analysis timeframes
- Focus areas (dividend income, margin strategies, tax optimization)
- Compliance requirements
- Reporting preferences
```

## Assessment Questions Template

### Liquid Assets
1. Total balance across all checking/savings accounts?
2. How are these accounts currently structured?
3. Current interest rates earned?

### Investments
4. Existing investment accounts?
5. Current balances and allocations?
6. Current asset allocation philosophy?
7. Any dividend-focused investments?

### Cash Flow
8. Combined monthly household income (after-tax)?
9. Fixed monthly expenses?
10. Variable monthly expenses?
11. Monthly savings/investment amount?
12. Irregular large expenses?

### Debt Profile
13. Current mortgage balance and payment?
14. Other debt (credit cards, car loans, student loans)?
15. Interest rates on existing debt?

### Risk & Goals
16. Emergency fund target?
17. Monthly expense multiplier for reserves?
18. Investing beyond retirement accounts?

## Output Format

```markdown
## 📊 Your Financial Profile Summary

### Current Position
- **Liquid Assets**: $[amount] across [n] accounts
- **Investment Portfolio**: $[amount] ([allocation])
- **Monthly Cash Flow**: $[income] income, $[expenses] expenses
- **Investment Capacity**: $[monthly_surplus]/month

### Opportunity Analysis
1. **High-Priority**: [Refinance high-interest debt at X%]
2. **Medium-Priority**: [Optimize low-yield savings earning <Y%]
3. **Strategic**: [Tax-loss harvesting opportunities]

### Recommended Workflows
Based on your profile, I recommend starting with:
1. `*coordinate margin-optimization` - Leverage your $[amount] portfolio
2. `*delegate dividend-specialist analyze` - Generate passive income
3. `*task debt-restructuring` - Save $[amount]/year on interest

### Quick Actions
- Type `1` for detailed margin strategy analysis
- Type `2` for dividend portfolio construction
- Type `3` for debt optimization roadmap
- Type `*help` for all available commands
```

## Integration Points

- **Google Drive MCP**: Form creation and response collection
- **CSV Parser**: Data extraction and validation
- **Profile Storage**: Save to `.guru-core/data/user-profile.json`
- **Specialist Activation**: Auto-configure based on profile needs

## Compliance Note
All recommendations are educational only. Consult licensed advisors before implementation.
