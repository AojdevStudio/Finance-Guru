# IncorporateBuyTicket Workflow

Incorporate a specific buy ticket into the Monte Carlo simulation by adjusting starting portfolio values.

## When to Use

Use this workflow when the user wants to:
- Include a recent buy ticket in the simulation
- See how a specific purchase affects projections
- Model a deployment that hasn't yet been reflected in Fidelity CSV

## Workflow Steps

### Step 1: Find the Buy Ticket

Search for buy tickets in `tickets/`:

```bash
ls -la tickets/buy-ticket-*.md
```

If user specifies a date (e.g., "12-31"), find the matching ticket:

```bash
ls tickets/buy-ticket-*12-31*.md 2>/dev/null || ls tickets/buy-ticket-2025-12-31*.md 2>/dev/null
```

### Step 2: Parse the Buy Ticket

Read the buy ticket and extract:
- **Frontmatter metadata**:
  - `deployment_amount`
  - `cash_available`
  - `price_snapshot_as_of`
  - `generated_on`
- **Execution Summary allocations**: Which tickers and how much to each

Example buy ticket format:
```markdown
---
document_type: buy-ticket
deployment_amount: "$5,000.00"
cash_available: "$6,000.00"
price_snapshot_as_of: "2026-01-31T09:45:00-05:00"
---

## Execution Summary
| Ticker | Category | Weight | $ Amount | Price | Shares |
|--------|----------|--------|----------|-------|--------|
| JEPI | JPMorgan Income | 10.0% | $500 | $55.00 | 9.09 |
| JEPQ | JPMorgan Income | 10.0% | $500 | $52.00 | 9.61 |
| CLM | CEF Stable | 20.0% | $1,000 | $7.50 | 133.33 |
...
```

### Step 3: Categorize Allocations by Layer

**Layer 2 allocations** (most buy tickets):
- Any income fund: JEPI, JEPQ, QQQI, SPYI, QQQY, CLM, CRF, ECAT, BDJ, ETY, ETV, BST, UTG, YMAX, AMZY, MSTY

**Layer 3 allocations**:
- SQQQ

**GOOGL allocations**:
- GOOGL

**Layer 1 allocations** (rare in buy tickets):
- PLTR, TSLA, NVDA, AAPL, VOO, etc.

### Step 4: Calculate Adjusted Starting Values

Get current portfolio values from RunSimulation workflow, then add:

```
adjusted_layer2 = current_layer2 + sum(layer2_allocations)
adjusted_layer3 = current_layer3 + sum(layer3_allocations)
adjusted_googl = current_googl + sum(googl_allocations)
adjusted_layer1 = current_layer1 + sum(layer1_allocations)
```

### Step 5: Update Simulation

Update `strategies/dividend_margin_monte_carlo.py` with adjusted values:

```python
# Initialize with ADJUSTED values (includes buy ticket from {ticket_date})
layer1_portfolio = {adjusted_layer1}   # Layer 1: Growth + ticket
income_portfolio = {adjusted_layer2}   # Layer 2: Income + ticket
googl_position = {adjusted_googl}      # GOOGL + ticket
hedge_position = {adjusted_layer3}     # Layer 3: Hedge + ticket
margin_balance = {current_margin}      # Margin unchanged by buy ticket
```

### Step 6: Run Simulation

Follow RunSimulation workflow steps 4-6.

### Step 7: Document Changes

Note in the output that this simulation includes the buy ticket:

```
## Simulation Notes
- Includes buy ticket: {ticket_filename}
- Total additional deployment: ${ticket_total}
- Layer 2 adjustment: +${layer2_adjustment}
- Layer 3 adjustment: +${layer3_adjustment}
- GOOGL adjustment: +${googl_adjustment}
```

## Example

**User Request:** "Run monte carlo with my 12-31 payroll ticket"

**Workflow Execution:**

1. Find ticket: `tickets/buy-ticket-2025-12-31-w2-payroll.md`

2. Parse allocations:
   - JEPI: 10% of ticket total
   - JEPQ: 10% of ticket total
   - CLM: 10% of ticket total
   - SQQQ: 16% of ticket total
   - etc.

3. Categorize:
   - Layer 2: ~84% of ticket total
   - Layer 3: ~16% of ticket total
   - Total: ticket total = 100%

4. Adjust starting values:
   - Layer 2: starting balance increased ~7% after the deployment
   - Layer 3: starting balance increased ~6% after the deployment

5. Run simulation with adjusted values

6. Report results with note about included ticket

## Important Notes

- Buy tickets typically deploy on payday (15th or last day of month)
- The Fidelity CSV may take 1-2 days to reflect new purchases
- If the ticket is already in the CSV, don't double-count!
- Check the ticket date vs. CSV date to avoid duplication
