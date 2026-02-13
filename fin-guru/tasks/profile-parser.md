# Profile Parser Task
<!-- Finance Guru™ Task | v1.0 | 2025-09-25 -->

## Purpose
Parse Financial Structure Assessment CSV and populate user-profile.yaml with personalized data.

## Execution Steps

### 1. Parse CSV Data
When assessment CSV is found at the path specified in user-profile.yaml:
```
READ: Financial Structure Assessment (Responses) - Form Responses 1 (1).csv
EXTRACT:
- Total liquid assets: $14,491
- Account structure: 10 accounts (2 business, 4 checking, 4 savings)
- Interest rates: <4%
- Investment accounts: $500,000 (401k, IRA, taxable brokerage)
- Monthly income: $25,000 after-tax
- Fixed expenses: $4,500
- Variable expenses: $10,000
- Monthly savings: $5,000
- Mortgage: $365,139.76 balance, $1,712.68/month
- Other debt: 2 car loans, student loans (8%), credit cards
- Risk profile: Aggressive
```

### 2. Calculate Derived Metrics
```
COMPUTE:
- Investment capacity: Income - Fixed - Variable = $10,500/month potential
- Debt service ratio: Total debt payments / Income
- Opportunity cost: Student loans at 8% vs savings at <4%
- Portfolio leverage potential: $500k * conservative margin = $250k
```

### 3. Update Profile YAML
```yaml
orientation_status:
  completed: true
  assessment_path: "research/finance/Financial Structure Assessment (Responses) - Form Responses 1 (1).csv"
  last_updated: "2025-09-25"
  onboarding_phase: "active"

user_profile:
  liquid_assets:
    total: 14491
    accounts_count: 10
    average_yield: 0.04

  investment_portfolio:
    total_value: 500000
    allocation: "diversified"
    risk_profile: "aggressive"

  cash_flow:
    monthly_income: 25000
    fixed_expenses: 4500
    variable_expenses: 10000
    investment_capacity: 10500

  debt_profile:
    mortgage_balance: 365139.76
    mortgage_payment: 1712.68
    other_debt:
      - type: "student_loans"
        rate: 0.08
      - type: "car_loans"
        rate: 0.04
      - type: "credit_cards"
    weighted_interest_rate: 0.06

opportunities:
  high_priority:
    - "Refinance student loans from 8% to lower rate"
    - "Move liquid assets from <4% savings to higher yield"
  medium_priority:
    - "Implement margin strategy on $500k portfolio"
    - "Establish dividend income stream"
  strategic:
    - "Tax-loss harvesting opportunities"
    - "Business expense optimization"

recommended_workflows:
  primary:
    - "*coordinate margin-optimization"
    - "*delegate dividend-specialist analyze"
  secondary:
    - "*task debt-restructuring"
    - "*coordinate tax-optimization"
  educational:
    - "*agent teaching-specialist"
```

### 4. Generate Welcome Message
```
Welcome back! Here's your Finance Guru™ profile:

💼 Portfolio: $500,000 (Aggressive allocation)
💵 Monthly Capacity: $10,500 available for investment
🎯 Focus Areas: Margin strategies, Dividend income
⚡ Quick Actions:
  1. Review debt refinancing opportunities (save ~$200/month)
  2. Optimize cash yields (gain ~$40/month)
  3. Explore margin strategies (access $250k liquidity)

Type a number or use *help for all commands.
```

## Integration
- Called by assessment-orientation.md
- Updates persist across sessions
- Profile drives all personalized recommendations
