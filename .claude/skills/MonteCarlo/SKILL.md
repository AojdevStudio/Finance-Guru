---
name: monte-carlo
description: Run Monte Carlo simulations for Finance Guru portfolio strategy. USE WHEN user mentions monte carlo OR run simulation OR stress test portfolio OR probability analysis OR income projections OR margin safety analysis. Supports 4-layer portfolio (Growth, Income, Hedge, GOOGL) with auto-detection of current values from Fidelity CSV.
---

# MonteCarlo

Monte Carlo simulation engine for Finance Guru's 4-layer dividend income + margin living strategy. Runs 10,000 market scenarios to project income probabilities, margin safety, and portfolio outcomes over 28 months.

## Workflow Routing

| Workflow | Trigger | File |
|----------|---------|------|
| **RunSimulation** | "run monte carlo", "simulate portfolio", "stress test" | `workflows/RunSimulation.md` |
| **IncorporateBuyTicket** | "include buy ticket", "add ticket to simulation" | `workflows/IncorporateBuyTicket.md` |

## Examples

**Example 1: Run standard Monte Carlo simulation**
```
User: "Run the monte carlo simulation with current portfolio"
-> Invokes RunSimulation workflow
-> Auto-detects portfolio values from notebooks/updates/Portfolio_Positions_*.csv
-> Runs 10,000 scenarios with v3.0 4-layer model
-> Outputs JSON summary + full CSV + Excel to fin-guru-private/fin-guru/analysis/
```

**Example 2: Incorporate a buy ticket into simulation**
```
User: "Run monte carlo with my new buy ticket from 12-31"
-> Invokes IncorporateBuyTicket workflow
-> Reads buy ticket from fin-guru-private/fin-guru/tickets/buy-ticket-2025-12-31-*.md
-> Parses YAML frontmatter + Execution Summary table from the canonical ticket format
-> Adjusts starting portfolio values based on ticket allocations
-> Runs simulation with updated positions
```

**Example 3: Stress test margin safety**
```
User: "What's my margin call probability?"
-> Invokes RunSimulation workflow
-> Focuses on margin_call_rate and margin_ratio metrics
-> Reports 5th percentile (worst case) margin ratio
```

## Key Metrics Produced

### Success Metrics
- **P($100k income)** - Probability of reaching $100k annual dividend income
- **P($75k income)** - Probability of reaching $75k annual dividend income
- **P($50k income)** - Probability of reaching $50k annual dividend income
- **Margin call rate** - % of scenarios triggering margin call (<3:1 ratio)
- **Backstop usage rate** - % of scenarios requiring business income injection

### Portfolio Metrics
- **Total portfolio value** - Median, P5, P95 at month 28
- **Layer 1 (Growth)** - PLTR, TSLA, VOO, etc. (no new deployment)
- **Layer 2 (Income)** - Dividend funds ($11,517/month deployment)
- **Layer 3 (Hedge)** - SQQQ ($800/month deployment)
- **GOOGL position** - Scale-in ($1,000/month deployment)

### Risk Metrics
- **Margin ratio** - Portfolio / Margin debt (must stay >3:1)
- **Max drawdown** - Worst peak-to-trough decline
- **Break-even timing** - When dividends cover margin draws

## Output Files

All outputs saved to `fin-guru-private/fin-guru/analysis/`:
- `monte-carlo-v3-{date}.json` - Summary statistics
- `monte-carlo-v3-full-results-{date}.csv` - All 10,000 scenarios
- `monte-carlo-v3-analysis-{date}.xlsx` - Excel workbook with charts

## Configuration

Simulation parameters are set in `fin-guru-private/strategies/dividend_margin_monte_carlo.py`:
- Starting portfolio values (auto-detected or manual)
- Monthly deployment amounts
- Bucket allocations and yields
- Margin schedule
- Market regime probabilities

## Model Version

**v3.0** (Jan 2026) - Full 4-layer portfolio:
- Layer 1: Growth portfolio (market returns only, no new deployment)
- Layer 2: Income portfolio (5-bucket dividend allocation)
- Layer 3: Hedge (SQQQ for crisis protection)
- GOOGL: Scale-in position (diverted from Layer 2)

Fixes applied:
- Floor at $0 for all positions (stocks can't go negative)
- Full portfolio margin ratio (all layers count toward Fidelity margin)
- Correct starting values from Fidelity CSV
