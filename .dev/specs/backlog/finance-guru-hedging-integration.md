---
title: "Finance Guru Hedging & Portfolio Protection Integration"
status: backlog
created: 2026-02-02
updated: 2026-02-02
author: "Ossie Irondi"
spec_id: finance-guru-hedging-integration
version: "1.0.0"
description: "Integrate Paycheck to Portfolio hedging strategies into Finance Guru CLI tools, private config, and agent knowledge base"
tags:
  - finance-guru
  - options
  - hedging
  - puts
  - sqqq
  - dividends
  - total-return
  - privacy
  - cli
references:
  - ../../meeting-notes/2026-01-30-paycheck-to-portfolio-sean-review.md
  - finance-guru-interactive-knowledge-explorer.md
supersedes: []
diagrams:
  human: "diagrams/finance-guru-hedging-integration-arch.png"
  machine: "diagrams/finance-guru-hedging-integration-arch.mmd"
---

<!-- ALL frontmatter fields above are MANDATORY per .dev/CLAUDE.md. No exceptions. -->

# Finance Guru Hedging & Portfolio Protection Integration

## Overview

Integrate strategies from the January 30, 2026 Paycheck to Portfolio advisory session into Finance Guru's CLI-first architecture. This adds four new CLI tools (rolling strategy tracker, portfolio-aware hedge sizer, SQQQ vs puts analyzer, total return calculator), extends the private config layer for personal hedging preferences, and captures strategy knowledge for the 8-agent teaching system.

## Project Type

Feature (Large — 5 discrete scopes in single umbrella spec)

## Source Material

**Meeting:** January 30, 2026 with Sean (Paycheck to Portfolio)
**Key strategies covered:**
- QQQ/SPY protective puts: 10-20% OTM, ~30 DTE, roll every 5-7 days
- Sizing rule: ~1 contract per $50,000 portfolio value
- Monthly insurance budget: ~$500-$600
- SQQQ (3x inverse ETF) as alternative/complement to puts
- Total return accounting: must include dividends in performance
- Borrow-vs-sell tax optimization
- Living off portfolio equity tracking

**Stored at:** `.dev/meeting-notes/2026-01-30-paycheck-to-portfolio-sean-review.md`

## Linear Issue Integration

| Issue | Title | Status | Integration |
|-------|-------|--------|-------------|
| AOJ-194 | User onboarding + fix hardcoded user name | In Progress (Urgent) | Extend user-profile.yaml with hedging config fields |
| AOJ-231 | Interactive Knowledge Explorer | Todo (High) | Knowledge capture feeds into explorer topic data |
| AOJ-122 | Finance API Documentation | Todo (High) | Options data sources documented alongside yfinance |

## Tech Stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Language | Python 3.12+ | Existing Finance Guru stack |
| Package Manager | uv | Already configured in pyproject.toml |
| Validation | Pydantic v2 | Established 3-layer pattern (models -> calc -> CLI) |
| Testing | pytest | 365 existing tests, test patterns established |
| Market Data | yfinance | Already integrated for options chain scanner |
| Math | scipy + numpy | Black-Scholes and statistical calculations |
| CLI | argparse | Standard library, matches existing 13 CLIs |
| Config | YAML + python-dotenv | Existing user-profile.yaml pattern |

## Scope Definition

| Aspect | Definition |
|--------|------------|
| **In scope** | 4 new CLI tools, private config extension, knowledge base content, architecture diagram |
| **Out of scope** | Web UI, Streamlit dashboard updates, new API integrations (beyond yfinance), agent personality changes |
| **Stop condition** | All 4 CLIs work with `uv run`, tests pass, private config loads hedging prefs, knowledge files loadable by agents |
| **Edge cases** | No market data available (yfinance down), zero-premium contracts, expired positions in rolling tracker, user has no hedging config yet (graceful defaults) |

---

## Architecture

### Component Structure

```
family-office/
├── src/
│   ├── models/
│   │   ├── options_inputs.py          # EXISTING - 8 models
│   │   ├── hedging_inputs.py          # NEW - Shared hedging models
│   │   ├── total_return_inputs.py     # NEW - Dividend/return models
│   │   └── __init__.py                # UPDATE - Export new models
│   │
│   ├── analysis/
│   │   ├── options.py                 # EXISTING - Black-Scholes calculator
│   │   ├── options_chain_cli.py       # EXISTING - Scanner CLI
│   │   ├── rolling_tracker.py         # NEW - Roll management logic
│   │   ├── rolling_tracker_cli.py     # NEW - Roll tracker CLI
│   │   ├── hedge_sizer.py            # NEW - Portfolio-aware sizing logic
│   │   ├── hedge_sizer_cli.py        # NEW - Hedge sizer CLI
│   │   ├── hedge_comparison.py        # NEW - SQQQ vs puts analysis
│   │   ├── hedge_comparison_cli.py    # NEW - Comparison CLI
│   │   ├── total_return.py           # NEW - Dividend-inclusive returns
│   │   └── total_return_cli.py       # NEW - Total return CLI
│   │
│   └── utils/
│       └── config_loader.py           # NEW - Load hedging config from user-profile.yaml
│
├── fin-guru/
│   └── data/
│       ├── knowledge/                  # NEW - Strategy knowledge for agents
│       │   ├── hedging-strategies.md
│       │   ├── options-insurance-framework.md
│       │   ├── dividend-total-return.md
│       │   └── borrow-vs-sell-tax.md
│       └── ...
│
├── fin-guru-private/                   # GITIGNORED - Personal config
│   └── hedging/
│       ├── positions.yaml              # Current hedge positions
│       ├── roll-history.yaml           # Roll history log
│       └── budget-tracker.yaml         # Monthly insurance spend
│
├── tests/python/
│   ├── test_options_chain.py          # EXISTING - 25 tests
│   ├── test_rolling_tracker.py        # NEW
│   ├── test_hedge_sizer.py           # NEW
│   ├── test_hedge_comparison.py       # NEW
│   ├── test_total_return.py          # NEW
│   └── test_config_loader.py         # NEW
│
└── scripts/onboarding/modules/templates/
    └── user-profile.template.yaml     # UPDATE - Add hedging section
```

### Data Flow

```
User Config (user-profile.yaml)
        │
        ├──> config_loader.py ──> HedgeConfig model
        │                              │
        │    ┌─────────────────────────┤
        │    │                         │
        ▼    ▼                         ▼
  rolling_tracker.py          hedge_sizer.py
  (Roll management)           (Position sizing)
        │                         │
        ▼                         ▼
  rolling_tracker_cli.py     hedge_sizer_cli.py
        │                         │
        └────────┬────────────────┘
                 │
         hedge_comparison.py ──> hedge_comparison_cli.py
         (SQQQ vs Puts analysis)
                 │
         total_return.py ──> total_return_cli.py
         (Dividend-inclusive performance)
```

### Integration Points

| Existing Component | New Integration |
|-------------------|-----------------|
| `options_chain_cli.py` | Rolling tracker uses scanner output to find replacement positions |
| `options.py` (Black-Scholes) | Hedge sizer uses Greeks for position evaluation |
| `user-profile.yaml` | Config loader reads hedging preferences (portfolio value, budget, risk tolerance) |
| `fin-guru/agents/` | Strategy Advisor and Quant Analyst agents reference new knowledge files |
| `PortfolioSyncing` skill | Total return calculator can consume synced position data |

---

## Scope 1: Private Config Extension (AOJ-194 Integration)

### Goal
Extend the existing `user-profile.yaml` template and config loading to include hedging preferences, portfolio value, and insurance budget parameters.

### Requirements

#### Explicit
- [ ] Add `hedging` section to `user-profile.template.yaml` with: `enabled`, `strategy` (puts/sqqq/both), `monthly_budget`, `roll_frequency_days`, `target_dte`, `otm_min`, `otm_max`, `underlyings` (list of tickers)
- [ ] Add `portfolio.total_value` field (numeric, updated manually or via sync)
- [ ] Create `config_loader.py` that reads `user-profile.yaml` and returns typed `HedgeConfig` Pydantic model
- [ ] Graceful defaults when hedging section is missing (disabled, conservative defaults)
- [ ] Create `fin-guru-private/hedging/` directory structure in setup.sh

#### Implicit
- [ ] No private data in git history — validate .gitignore coverage
- [ ] Config loader handles missing file, malformed YAML, partial config
- [ ] Tests use fixture YAML, never real user-profile.yaml

### Models (hedging_inputs.py — partial)

```python
class HedgeConfig(BaseModel):
    """User's hedging preferences loaded from user-profile.yaml"""
    enabled: bool = False
    strategy: Literal["puts", "sqqq", "both"] = "puts"
    monthly_budget: float = 500.0
    roll_frequency_days: int = 7
    target_dte: int = 30
    otm_min: float = 10.0
    otm_max: float = 20.0
    underlyings: list[str] = ["QQQ", "SPY"]
    contracts_per_50k: int = 1

class PortfolioConfig(BaseModel):
    """Portfolio-level config from user-profile.yaml"""
    total_value: float | None = None
    equity_pct: float | None = None
```

---

## Scope 2: Rolling Strategy Tracker CLI

### Goal
Track current protective put positions, alert when positions need rolling (approaching expiration), suggest replacement positions using the existing options chain scanner, and log roll history.

### Requirements

#### Explicit
- [ ] `rolling_tracker_cli.py` CLI with subcommands: `status`, `suggest-roll`, `log-roll`, `history`
- [ ] `status`: Show current positions, days until expiry, current value, profit/loss
- [ ] `suggest-roll`: For positions within N days of expiry (default: 7), scan for replacement puts using `options_chain_cli` logic
- [ ] `log-roll`: Record a completed roll (old position closed, new position opened) to `fin-guru-private/hedging/roll-history.yaml`
- [ ] `history`: Display roll history with cost tracking
- [ ] Positions stored in `fin-guru-private/hedging/positions.yaml` (gitignored)
- [ ] Read hedge config from `user-profile.yaml` via config_loader

#### Implicit
- [ ] Positions file doesn't exist on first run — initialize empty
- [ ] Handle expired positions gracefully (mark as expired, don't crash)
- [ ] Tests mock yfinance calls, never hit live API

### Models (hedging_inputs.py — partial)

```python
class HedgePosition(BaseModel):
    """A single protective position (put or inverse ETF)"""
    ticker: str                      # QQQ, SPY
    position_type: Literal["put", "inverse_etf"]
    strike: float | None = None      # Only for puts
    expiry: date | None = None       # Only for puts
    contracts: int = 1
    entry_price: float               # Premium paid per contract
    entry_date: date
    underlying_price_at_entry: float

class RollSuggestion(BaseModel):
    """Suggested replacement position for an expiring hedge"""
    current: HedgePosition
    suggested_strike: float
    suggested_expiry: date
    suggested_premium: float
    cost_to_roll: float              # new premium - any remaining value
    days_to_current_expiry: int

class RollRecord(BaseModel):
    """Historical record of a completed roll"""
    roll_date: date
    closed_position: HedgePosition
    opened_position: HedgePosition
    net_cost: float                  # Cost of the roll
    reason: str = "scheduled"        # scheduled, early, emergency
```

### CLI Interface

```bash
# Show current hedge positions
uv run python src/analysis/rolling_tracker_cli.py status

# Suggest rolls for positions expiring within 7 days
uv run python src/analysis/rolling_tracker_cli.py suggest-roll

# Suggest rolls with custom threshold
uv run python src/analysis/rolling_tracker_cli.py suggest-roll --days-threshold 10

# Log a completed roll
uv run python src/analysis/rolling_tracker_cli.py log-roll \
  --old-ticker QQQ --old-strike 480 --old-expiry 2026-02-15 \
  --new-ticker QQQ --new-strike 475 --new-expiry 2026-03-15 \
  --new-premium 3.20

# View roll history
uv run python src/analysis/rolling_tracker_cli.py history
uv run python src/analysis/rolling_tracker_cli.py history --last 10
```

---

## Scope 3: Portfolio-Aware Hedge Sizer CLI

### Goal
Given a portfolio value, calculate the recommended number of protective put contracts (SPY + QQQ), monthly insurance cost, and coverage ratio. Uses Sean's "1 contract per $50k" sizing rule as a baseline with adjustable parameters.

### Requirements

#### Explicit
- [ ] `hedge_sizer_cli.py` CLI with: portfolio value input (or auto-load from config), sizing calculation, budget validation, multi-underlying support
- [ ] Sizing formula: `contracts = floor(portfolio_value / (contracts_per_50k * 50000))`
- [ ] Split contracts across configured underlyings (e.g., 3 QQQ + 3 SPY for $300k)
- [ ] Calculate monthly cost: fetch current premiums via options chain scanner, multiply by contract count
- [ ] Budget check: compare monthly cost against configured `monthly_budget`
- [ ] Output: recommended positions, monthly cost, coverage ratio, budget utilization %
- [ ] Support `--portfolio-value` flag to override config
- [ ] JSON and human-readable output

#### Implicit
- [ ] If no portfolio value in config and no flag, prompt or error clearly
- [ ] Handle odd splits (3 underlyings, 5 contracts — distribute evenly with remainder to primary)
- [ ] Tests don't require live market data

### Models (hedging_inputs.py — partial)

```python
class HedgeSizeRequest(BaseModel):
    """Input for hedge sizing calculation"""
    portfolio_value: float
    contracts_per_50k: int = 1
    underlyings: list[str] = ["QQQ", "SPY"]
    target_dte: int = 30
    otm_min: float = 10.0
    otm_max: float = 20.0

class HedgeSizeResult(BaseModel):
    """Output of hedge sizing calculation"""
    portfolio_value: float
    total_contracts: int
    positions: list[dict]            # {ticker, contracts, estimated_premium, monthly_cost}
    total_monthly_cost: float
    monthly_budget: float | None
    budget_utilization_pct: float | None
    coverage_ratio: float            # % of portfolio "insured"
    sizing_rule: str                 # e.g., "1 contract per $50,000"
```

### CLI Interface

```bash
# Auto-load portfolio value from config
uv run python src/analysis/hedge_sizer_cli.py

# Override portfolio value
uv run python src/analysis/hedge_sizer_cli.py --portfolio-value 300000

# Custom sizing
uv run python src/analysis/hedge_sizer_cli.py --portfolio-value 300000 \
  --underlyings QQQ SPY IWM --contracts-per-50k 1

# JSON output
uv run python src/analysis/hedge_sizer_cli.py --output json
```

---

## Scope 4: SQQQ vs Puts Analyzer CLI

### Goal
Compare the effectiveness of SQQQ (3x inverse Nasdaq ETF) as a hedge versus protective puts for the same portfolio, across multiple market decline scenarios. Helps answer: "Should I use SQQQ, puts, or both?"

### Requirements

#### Explicit
- [ ] `hedge_comparison_cli.py` CLI comparing SQQQ position vs QQQ puts for same budget
- [ ] Model scenarios: -5%, -10%, -20%, -40% market drops (configurable)
- [ ] For SQQQ: calculate position size from budget, model 3x leveraged inverse returns per scenario
- [ ] For puts: use existing Black-Scholes to model put value at each scenario, include IV expansion estimate
- [ ] Account for SQQQ drag (daily rebalancing decay over 30-day period)
- [ ] Account for put time decay (theta) over holding period
- [ ] Output comparison table: scenario, SQQQ P&L, put P&L, winner, notes
- [ ] Include breakeven analysis: at what drop % does each strategy become profitable
- [ ] JSON and human-readable output

#### Implicit
- [ ] SQQQ modeling is approximate (daily rebalance compounding is path-dependent)
- [ ] Include educational disclaimer about SQQQ decay and put theta
- [ ] IV expansion estimate uses historical VIX correlation (simplified)
- [ ] Tests verify math with known scenarios, not live data

### Models (hedging_inputs.py — partial)

```python
class HedgeComparisonInput(BaseModel):
    """Input for SQQQ vs puts comparison"""
    portfolio_value: float
    hedge_budget: float
    holding_period_days: int = 30
    scenarios: list[float] = [-5.0, -10.0, -20.0, -40.0]  # % drops
    current_vix: float | None = None  # Optional, for IV modeling
    put_strike_otm_pct: float = 15.0
    put_dte: int = 30

class ScenarioResult(BaseModel):
    """Result for a single market drop scenario"""
    scenario_pct: float
    sqqq_pnl: float
    sqqq_return_pct: float
    put_pnl: float
    put_return_pct: float
    winner: Literal["sqqq", "puts", "tie"]
    notes: str

class HedgeComparisonOutput(BaseModel):
    """Full comparison result"""
    portfolio_value: float
    hedge_budget: float
    sqqq_position_value: float
    put_contracts: int
    put_total_premium: float
    scenarios: list[ScenarioResult]
    sqqq_breakeven_drop_pct: float
    put_breakeven_drop_pct: float
    recommendation: str
    educational_notes: list[str]
```

### CLI Interface

```bash
# Compare with default scenarios
uv run python src/analysis/hedge_comparison_cli.py \
  --portfolio-value 300000 --budget 2000

# Custom scenarios
uv run python src/analysis/hedge_comparison_cli.py \
  --portfolio-value 300000 --budget 2000 \
  --scenarios 5 10 15 20 30 40

# Auto-load from config
uv run python src/analysis/hedge_comparison_cli.py

# JSON output
uv run python src/analysis/hedge_comparison_cli.py --output json
```

---

## Scope 5: Total Return Calculator CLI

### Goal
Calculate total return including dividends/distributions for holdings, solving the "you can't say it's down without dividends" accounting problem Sean highlighted. Shows price return vs total return side-by-side.

### Requirements

#### Explicit
- [ ] `total_return_cli.py` CLI accepting ticker(s), date range, and dividend reinvestment toggle
- [ ] Fetch historical price data and dividend history via yfinance
- [ ] Calculate: price-only return, dividend-only return, total return (price + dividends)
- [ ] Optional: dividend reinvestment modeling (DRIP — buy fractional shares at ex-div date)
- [ ] Support multiple tickers for comparison (e.g., YMAX vs SPY vs QQQ)
- [ ] Output: per-ticker returns table, dividend history, total return with and without reinvestment
- [ ] JSON and human-readable output
- [ ] `--save-to` for file export

#### Implicit
- [ ] Handle tickers with no dividend history (pure growth stocks)
- [ ] Handle partial date ranges where data isn't available
- [ ] yfinance dividend data may have gaps — note data quality in output
- [ ] Tests use mocked yfinance data

### Models (total_return_inputs.py)

```python
class TotalReturnInput(BaseModel):
    """Input for total return calculation"""
    tickers: list[str]
    start_date: date
    end_date: date = Field(default_factory=date.today)
    reinvest_dividends: bool = True
    initial_investment: float = 10000.0  # Hypothetical for comparison

class DividendRecord(BaseModel):
    """Single dividend payment"""
    date: date
    ticker: str
    amount_per_share: float
    shares_held: float
    total_received: float
    reinvested: bool
    shares_bought: float | None = None  # If reinvested

class TickerReturn(BaseModel):
    """Return breakdown for a single ticker"""
    ticker: str
    start_price: float
    end_price: float
    price_return_pct: float
    dividends_collected: float
    dividend_return_pct: float
    total_return_pct: float
    total_return_with_drip_pct: float | None
    dividend_history: list[DividendRecord]
    annualized_return_pct: float

class TotalReturnOutput(BaseModel):
    """Complete return analysis"""
    period: str                      # "2025-10-01 to 2026-02-02"
    initial_investment: float
    results: list[TickerReturn]
    comparison_notes: list[str]      # Educational context
```

### CLI Interface

```bash
# Single ticker total return
uv run python src/analysis/total_return_cli.py YMAX \
  --start 2025-10-01

# Compare multiple tickers
uv run python src/analysis/total_return_cli.py YMAX MSTY SPY QQQ \
  --start 2025-10-01 --reinvest

# Without dividend reinvestment
uv run python src/analysis/total_return_cli.py YMAX MSTY \
  --start 2025-10-01 --no-reinvest

# JSON output to file
uv run python src/analysis/total_return_cli.py YMAX MSTY \
  --start 2025-10-01 --output json --save-to analysis/total-returns.json
```

---

## Scope 6: Knowledge Capture for Agent System

### Goal
Create structured knowledge files in `fin-guru/data/knowledge/` that the 8-agent system (especially Strategy Advisor and Teaching Specialist) can reference when answering hedging, options, and dividend questions.

### Requirements

#### Explicit
- [ ] `hedging-strategies.md` — Protective puts framework: sizing, rolling, budget, always-on philosophy
- [ ] `options-insurance-framework.md` — Options-as-insurance mental model: homeowners insurance analogy, max loss/gain asymmetry, Greeks simplified, IV expansion during crashes
- [ ] `dividend-total-return.md` — Total return accounting: why dividends must be included, rental property analogy, common accounting mistakes
- [ ] `borrow-vs-sell-tax.md` — Tax-optimized liquidity: borrow against equity vs selling, capital gains avoidance, property tax payment strategy
- [ ] Knowledge files use consistent frontmatter (title, category, tags, source)
- [ ] Reference meeting notes as source material
- [ ] Agent definitions updated to include knowledge file references

#### Implicit
- [ ] Knowledge is generic/educational — no personal portfolio details
- [ ] Content suitable for a public repo
- [ ] Structured for agent consumption (clear sections, actionable frameworks)

---

## Scope 7: Architecture Diagram

### Goal
Create a Mermaid architecture diagram showing how the new hedging tools integrate with existing Finance Guru components.

### Requirements
- [ ] Mermaid (.mmd) diagram at `.dev/specs/backlog/diagrams/finance-guru-hedging-integration-arch.mmd`
- [ ] Show: existing components, new CLIs, data flow, private vs public boundary, config loading, agent knowledge integration

---

## Task Items

See `finance-guru-hedging-integration.tasks.json` for structured task data.

## Completion Criteria

All of the following must be true:
- [ ] All 4 new CLI tools work with `uv run python src/analysis/<tool>_cli.py`
- [ ] All new tests pass (`uv run pytest tests/python/test_rolling_tracker.py test_hedge_sizer.py test_hedge_comparison.py test_total_return.py test_config_loader.py`)
- [ ] Private config loads hedging preferences from user-profile.yaml
- [ ] Knowledge files exist in fin-guru/data/knowledge/ and are referenced by agents
- [ ] Architecture diagram renders correctly
- [ ] No private data in any committed file
- [ ] Existing 365 tests still pass (no regressions)
- [ ] tasks.json has all `passes: true`
