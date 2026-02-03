# Phase 9: SQQQ vs Puts Comparison - Research

**Researched:** 2026-02-02
**Domain:** Leveraged ETF daily compounding simulation, protective put modeling, VIX-SPX regression, breakeven analysis
**Confidence:** HIGH (core math is well-established; VIX-SPX regression parameters are MEDIUM)

## Summary

Phase 9 builds the highest-complexity component of the M2 Hedging milestone: a CLI tool that compares SQQQ (3x leveraged inverse ETF) hedging versus protective puts across discrete market drop scenarios (-5%, -10%, -20%, -40%). The key technical challenge is NOT the comparison logic itself, but the accurate simulation of SQQQ's day-by-day compounding with volatility drag and the IV expansion model for repricing puts during crashes.

The codebase already contains a complete Black-Scholes calculator (`src/analysis/options.py`) with `price_option()` and `_put_price()` methods, plus `scipy.stats.norm` for cumulative normal distribution. Phase 6 creates shared models (`HedgeConfig`, `HedgePosition`) and `config_loader.py`. Phase 7 establishes `total_return.py` with the `TotalReturnCalculator` class. Phase 9 adds two new files: `hedge_comparison.py` (Layer 2 calculator) and `hedge_comparison_cli.py` (Layer 3 CLI). No new dependencies are needed -- all required math (exp, log, sqrt, norm.cdf) is already available via scipy 1.16.2, numpy 2.3.3, and Python stdlib math.

The research flags from the roadmap -- daily compounding validation and VIX-SPX regression parameters -- are addressed: (1) SQQQ simulation uses the formula `SQQQ_n = SQQQ_{n-1} * (1 + (-3) * r_QQQ_n - daily_fee)` which can be validated against historical SQQQ vs QQQ data via yfinance, and (2) VIX-SPX regression uses a piecewise model derived from historical crash data where the VIX response is convex (non-linear) with SPX drops.

**Primary recommendation:** Build a `HedgeComparisonCalculator` class with separate methods for SQQQ simulation and put payoff modeling. Use point-in-time scenario analysis (NOT path simulation) for the comparison output, as this is clearer for users and matches the requirement for discrete scenarios. Reuse the existing `OptionsCalculator.price_option()` for put valuation with expanded IV. Hand-build only the SQQQ day-by-day simulation and the VIX-SPX regression model -- there are no established Python libraries for these specific use cases.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| scipy | 1.16.2 | `scipy.stats.norm.cdf` for Black-Scholes put pricing | Already installed, used by `src/analysis/options.py` |
| numpy | 2.3.3 | Array operations for day-by-day simulation, vectorized returns | Already installed, used throughout codebase |
| pandas | 2.3.2 | Historical price data handling, time-series alignment | Already installed, used for all market data |
| pydantic | 2.12.0 | Input/output model validation (3-layer architecture) | Already installed, required by all models |
| yfinance | >=0.2.66 | Historical QQQ and SQQQ price data for validation | Already installed, used by market_data.py |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| math (stdlib) | - | `exp`, `log`, `sqrt` for Black-Scholes and compounding formulas | Core calculation primitives |
| argparse (stdlib) | - | CLI argument parsing | Layer 3 CLI interface |
| json (stdlib) | - | JSON output serialization | `--output json` flag |
| datetime (stdlib) | - | Date handling | Scenario date stamps |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Hand-built SQQQ sim | QuantLib LETF module | QuantLib is massive dependency for one calculation; hand-built is ~20 lines |
| Hand-built VIX regression | VIX futures data via CBOE API | Requires paid API access; static regression table is adequate for educational tool |
| Black-Scholes for puts | Binomial tree pricing | BS is already implemented in codebase; binomial adds complexity without material accuracy gain for this use case |
| Point-in-time scenarios | Full Monte Carlo path simulation | Monte Carlo is over-engineered for discrete scenario comparison; requirements explicitly state discrete scenarios |

**Installation:**
```bash
# No new dependencies required. Everything is already in pyproject.toml.
uv sync
```

## Architecture Patterns

### Recommended Project Structure
```
src/
  models/
    hedging_inputs.py          # [Phase 6] HedgePosition, HedgeSizeRequest (exists)
    hedge_comparison_inputs.py # [Phase 9] NEW: ScenarioInput, SQQQSimResult, PutPayoffResult, ComparisonOutput
  analysis/
    options.py                 # [Existing] OptionsCalculator with price_option() - REUSE
    hedge_comparison.py        # [Phase 9] NEW: HedgeComparisonCalculator (Layer 2)
    hedge_comparison_cli.py    # [Phase 9] NEW: CLI interface (Layer 3)
tests/
  python/
    test_hedge_comparison.py   # [Phase 9] NEW: Known-answer tests (HEDG-13)
docs/
  architecture/
    m2-hedging-components.mmd  # [Phase 9] NEW: Mermaid diagram (HEDG-11)
```

### Pattern 1: SQQQ Day-by-Day Simulation (HC-01)

**What:** Simulate SQQQ value over N days using daily QQQ returns with -3x leverage and expense ratio drag
**When to use:** Calculating SQQQ hedge payoff for each market drop scenario
**Why NOT simple -3x:** A -10% QQQ drop over 10 volatile days produces a SQQQ return that differs significantly from +30% due to daily compounding and volatility drag

```python
# Source: ProShares SQQQ prospectus + leveraged ETF compounding math
# Verified against: arxiv.org/html/2504.20116v1 (Hsieh et al., 2025)

SQQQ_EXPENSE_RATIO = 0.0095  # 0.95% annual (net, with fee waiver through Sep 2026)
SQQQ_DAILY_FEE = SQQQ_EXPENSE_RATIO / 252  # ~0.00377% per trading day
SQQQ_LEVERAGE = -3  # -3x daily target

def simulate_sqqq_day_by_day(
    daily_qqq_returns: list[float],
    initial_value: float = 10000.0,
) -> float:
    """
    Simulate SQQQ value using day-by-day compounding with volatility drag.

    Formula per day:
        SQQQ_n = SQQQ_{n-1} * (1 + (-3) * r_QQQ_n - daily_fee)

    This is NOT equivalent to -3 * cumulative QQQ return.
    The path matters: volatile paths produce worse SQQQ outcomes.

    Args:
        daily_qqq_returns: List of daily QQQ percentage returns (e.g., [0.01, -0.02, ...])
        initial_value: Starting SQQQ position value in dollars

    Returns:
        Final SQQQ position value after all days
    """
    value = initial_value
    for r in daily_qqq_returns:
        value *= (1.0 + SQQQ_LEVERAGE * r - SQQQ_DAILY_FEE)
        # SQQQ cannot go below zero (circuit breaker)
        value = max(value, 0.0)
    return value
```

**Critical insight -- volatility drag formula:**
For a leveraged ETF with leverage L, the expected compounding loss over T days with daily volatility sigma is approximately:
```
Volatility drag ≈ -0.5 * L^2 * sigma^2 * T
```
For SQQQ (L=-3), with 1.5% daily QQQ volatility:
```
30-day drag ≈ -0.5 * 9 * 0.015^2 * 30 ≈ -3.0%
```
This means even if QQQ is flat over 30 days, SQQQ loses ~3% just from daily rebalancing.

### Pattern 2: Scenario Generation for SQQQ (HC-02)

**What:** Generate realistic daily return paths that produce a target cumulative drop
**When to use:** Creating the daily QQQ returns that feed into the SQQQ simulation
**Why needed:** A -20% QQQ drop can happen via many different daily return paths, each producing different SQQQ outcomes

```python
import numpy as np

def generate_scenario_paths(
    target_drop_pct: float,
    days: int = 30,
    daily_volatility: float = 0.015,
    num_paths: int = 3,
    seed: int = 42,
) -> list[list[float]]:
    """
    Generate daily return paths that produce a target cumulative drop.

    Generates three representative paths:
    1. Gradual decline (uniform daily drops)
    2. Crash-then-flat (sharp drop followed by flat)
    3. Volatile path (random walk conditioned on final value)

    Args:
        target_drop_pct: Target cumulative drop (e.g., -0.20 for -20%)
        days: Number of trading days over which the drop occurs
        daily_volatility: Expected daily volatility of QQQ
        num_paths: Number of scenario paths to generate

    Returns:
        List of daily return lists, each producing approximately target_drop_pct
    """
    paths = []

    # Path 1: Gradual uniform decline
    daily_return = (1 + target_drop_pct) ** (1 / days) - 1
    paths.append([daily_return] * days)

    # Path 2: Sharp crash (first 5 days), then flat
    crash_days = min(5, days)
    crash_daily = (1 + target_drop_pct) ** (1 / crash_days) - 1
    path2 = [crash_daily] * crash_days + [0.0] * (days - crash_days)
    paths.append(path2)

    # Path 3: Volatile path (adds noise but targets same final value)
    rng = np.random.default_rng(seed)
    noise = rng.normal(0, daily_volatility, days)
    # Adjust noise so cumulative product matches target
    cumulative = np.cumprod(1 + noise)
    adjustment = (1 + target_drop_pct) / cumulative[-1]
    adjusted_returns = (1 + noise) * (adjustment ** (1 / days)) - 1
    paths.append(adjusted_returns.tolist())

    return paths
```

### Pattern 3: Put Payoff with IV Expansion (HC-04)

**What:** Calculate protective put value at a given market drop, accounting for IV expansion
**When to use:** The "puts" column of the comparison table
**Reuses:** Existing `OptionsCalculator.price_option()` from `src/analysis/options.py`

```python
# Source: Existing Black-Scholes implementation in src/analysis/options.py
# VIX-SPX relationship: Whaley (2000), macroption.com historical data

from src.analysis.options import OptionsCalculator
from src.models.options_inputs import BlackScholesInput

# VIX-SPX regression: empirical piecewise model
# Based on: 2008 GFC (VIX peaked 89.53), 2020 COVID (VIX peaked 82.69),
# 2018 Volmageddon (VIX doubled on -5% SPX), Whaley (2000) regression
VIX_SPX_TABLE = {
    # market_drop_pct: estimated_vix_level
    0.00: 18.0,     # Normal baseline VIX
    -0.05: 28.0,    # Mild correction
    -0.10: 38.0,    # Moderate correction
    -0.20: 55.0,    # Bear market territory
    -0.40: 80.0,    # Crisis (2008/2020 levels)
}

def estimate_iv_at_drop(
    market_drop_pct: float,
    baseline_iv: float = 0.20,
    baseline_vix: float = 18.0,
) -> float:
    """
    Estimate implied volatility of QQQ puts at a given market drop level.

    Uses piecewise linear interpolation of VIX-SPX empirical relationship,
    then scales baseline IV proportionally to VIX change.

    IV_new = baseline_iv * (VIX_at_drop / baseline_vix)

    This is an approximation. Actual IV expansion is regime-dependent.

    Args:
        market_drop_pct: Market drop as negative decimal (e.g., -0.20)
        baseline_iv: Current implied volatility of the put
        baseline_vix: Current VIX level

    Returns:
        Estimated IV at the given market drop level
    """
    # Interpolate VIX from table
    drops = sorted(VIX_SPX_TABLE.keys())
    vix_at_drop = _interpolate_vix(market_drop_pct, drops, VIX_SPX_TABLE)

    # Scale IV proportionally
    return baseline_iv * (vix_at_drop / baseline_vix)


def calculate_put_payoff(
    spot_price: float,
    strike: float,
    premium_paid: float,
    market_drop_pct: float,
    time_to_expiry: float,
    baseline_iv: float = 0.20,
    risk_free_rate: float = 0.045,
) -> dict:
    """
    Calculate put option payoff at a given market drop with IV expansion.

    Steps:
    1. Calculate new spot price after drop
    2. Estimate new IV using VIX-SPX regression
    3. Price the put at new spot + new IV using Black-Scholes
    4. Calculate P&L vs premium paid

    Returns:
        Dict with put_value, pnl, pnl_pct, iv_used, intrinsic, time_value
    """
    new_spot = spot_price * (1 + market_drop_pct)
    new_iv = estimate_iv_at_drop(market_drop_pct, baseline_iv)

    calculator = OptionsCalculator()
    bs_input = BlackScholesInput(
        spot_price=new_spot,
        strike=strike,
        time_to_expiry=time_to_expiry,
        volatility=new_iv,
        risk_free_rate=risk_free_rate,
        option_type="put",
    )
    greeks = calculator.price_option(bs_input)

    intrinsic = max(strike - new_spot, 0.0)
    pnl = greeks.option_price - premium_paid

    return {
        "put_value": greeks.option_price,
        "pnl": pnl,
        "pnl_pct": pnl / premium_paid if premium_paid > 0 else 0.0,
        "iv_used": new_iv,
        "intrinsic": intrinsic,
        "time_value": greeks.option_price - intrinsic,
    }
```

### Pattern 4: Breakeven Analysis (HC-03)

**What:** Find the market drop percentage at which each hedge strategy becomes profitable
**When to use:** The breakeven row of the comparison table

```python
from scipy.optimize import brentq

def find_breakeven_sqqq(
    sqqq_cost: float,
    days: int = 30,
    daily_volatility: float = 0.015,
) -> float:
    """
    Find the QQQ drop at which SQQQ position breaks even.

    Uses gradual decline path (conservative estimate).
    Solves: simulate_sqqq(path_for_drop_X) = sqqq_cost

    Returns:
        Breakeven QQQ drop as negative decimal (e.g., -0.03 for -3%)
    """
    def objective(drop):
        daily_return = (1 + drop) ** (1 / days) - 1
        daily_returns = [daily_return] * days
        final_value = simulate_sqqq_day_by_day(daily_returns, sqqq_cost)
        return final_value - sqqq_cost  # Breakeven when this = 0

    # SQQQ breaks even when the market drops enough to offset fees/drag
    # Search between -0.001 (tiny drop) and -0.50 (massive crash)
    try:
        breakeven = brentq(objective, -0.50, -0.001, xtol=0.0001)
        return breakeven
    except ValueError:
        return float('nan')  # No breakeven found in range


def find_breakeven_put(
    premium_paid: float,
    spot_price: float,
    strike: float,
) -> float:
    """
    Find the market drop at which protective put breaks even.

    Breakeven for a put hedge:
        drop_pct = -(premium_paid) / spot_price  (simplified, ignoring IV change)

    More precisely:
        breakeven_spot = strike - premium_paid
        breakeven_drop = (breakeven_spot - spot_price) / spot_price

    Returns:
        Breakeven market drop as negative decimal
    """
    breakeven_spot = strike - premium_paid
    return (breakeven_spot - spot_price) / spot_price
```

### Pattern 5: 3-Layer Architecture for Comparison (Established)

**What:** Models -> Calculator -> CLI following existing codebase convention
**When to use:** The entire Phase 9 implementation

Layer 1 (Models):
```python
# src/models/hedge_comparison_inputs.py
from pydantic import BaseModel, Field
from typing import Literal

class ScenarioInput(BaseModel):
    """Input for a single market drop scenario."""
    market_drop_pct: float = Field(..., lt=0, ge=-0.99, description="Market drop as decimal (e.g., -0.20)")
    holding_days: int = Field(default=30, ge=1, le=252, description="Holding period in trading days")
    daily_volatility: float = Field(default=0.015, gt=0, le=0.10, description="Expected daily QQQ volatility")

class SQQQResult(BaseModel):
    """SQQQ simulation result for a scenario."""
    market_drop_pct: float
    sqqq_return_pct: float  # Actual SQQQ return (less than 3x due to drag)
    naive_3x_return_pct: float  # What simple -3x would give (for comparison)
    volatility_drag_pct: float  # Difference: drag = naive - actual
    final_value: float
    initial_value: float

class PutResult(BaseModel):
    """Protective put result for a scenario."""
    market_drop_pct: float
    put_value_after: float
    premium_paid: float
    pnl: float
    pnl_pct: float
    iv_before: float
    iv_after: float
    intrinsic: float
    time_value: float

class ComparisonRow(BaseModel):
    """One row of the comparison table (one scenario)."""
    scenario_label: str  # e.g., "-5% correction"
    market_drop_pct: float
    sqqq: SQQQResult
    put: PutResult
    winner: Literal["sqqq", "put", "neither"]

class ComparisonOutput(BaseModel):
    """Full comparison output."""
    scenarios: list[ComparisonRow]
    sqqq_breakeven_drop: float
    put_breakeven_drop: float
    disclaimers: list[str]
    parameters: dict  # Config snapshot
```

Layer 2 (Calculator):
```python
# src/analysis/hedge_comparison.py
class HedgeComparisonCalculator:
    """Compare SQQQ hedge vs protective puts across market scenarios."""

    def __init__(self, config: HedgeConfig):
        self.config = config
        self.options_calc = OptionsCalculator()  # Reuse existing

    def simulate_sqqq(self, scenario: ScenarioInput, allocation: float) -> SQQQResult:
        """Day-by-day SQQQ simulation for a scenario."""

    def calculate_put_payoff(self, scenario: ScenarioInput, put_params: dict) -> PutResult:
        """Put payoff with IV expansion for a scenario."""

    def find_breakevens(self) -> tuple[float, float]:
        """Find breakeven drops for both strategies."""

    def compare_all(self, scenarios: list[float]) -> ComparisonOutput:
        """Run comparison across all scenarios. Main entry point."""
```

Layer 3 (CLI):
```python
# src/analysis/hedge_comparison_cli.py
# uv run python src/analysis/hedge_comparison_cli.py --scenarios -5,-10,-20,-40
# uv run python src/analysis/hedge_comparison_cli.py --scenarios -5,-10,-20,-40 --output json
```

### Anti-Patterns to Avoid

- **Simple -3x multiplication for SQQQ:** The most critical anti-pattern. SQQQ does NOT return 3x the inverse of multi-day QQQ returns. You MUST simulate day-by-day. This is requirement HC-01 and success criterion #2.
- **Ignoring IV expansion for puts:** Pricing puts at their original IV during a -20% crash produces drastically wrong values. IV can triple during crashes (from 20% to 60%+). This is requirement HC-04.
- **Monte Carlo for scenario comparison:** The requirements specify discrete scenarios (-5%, -10%, -20%, -40%), not continuous distribution. Monte Carlo is over-engineered. Use deterministic scenarios with representative paths.
- **Importing private variables from options.py:** Use the public `OptionsCalculator.price_option()` and `price_option()` convenience function. Do not import `_calculate_d1_d2` or other private helpers.
- **Hardcoding VIX-SPX parameters without documenting source:** The VIX-SPX regression table MUST be documented with sources and marked as approximate (HC-05 disclaimer requirement).

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Black-Scholes put pricing | Custom BS implementation | `src/analysis/options.OptionsCalculator.price_option()` | Already tested, handles all Greeks and edge cases |
| Normal CDF | Manual approximation | `scipy.stats.norm.cdf()` | Exact, already used by options.py |
| Root finding for breakeven | Manual bisection loop | `scipy.optimize.brentq()` | Robust, handles edge cases, much faster |
| CLI argument parsing | Custom parser | `argparse` with epilog examples | Consistent with all 15+ existing CLIs |
| JSON serialization | Custom dict builder | `model.model_dump_json(indent=2)` | Pydantic handles serialization correctly |
| Config loading | Direct YAML parsing | `config_loader.load_hedge_config()` | Phase 6 provides this; DRY requirement |
| Market data fetching | Custom HTTP requests | `yfinance` via `market_data.py` | Already integrated in codebase |

**Key insight:** The only genuinely new code in Phase 9 is (1) the SQQQ day-by-day simulation loop (~20 lines), (2) the VIX-SPX regression table (~15 lines), (3) the scenario path generator (~30 lines), and (4) the comparison orchestration logic. Everything else reuses existing components.

## Common Pitfalls

### Pitfall 1: SQQQ Simple Multiplication Trap
**What goes wrong:** Using `SQQQ_return = -3 * QQQ_return` for multi-day periods, which dramatically overestimates SQQQ gains during crashes and underestimates SQQQ losses during volatile sideways markets.
**Why it happens:** The -3x daily target is intuitive to extrapolate to longer periods. Academic literature calls this "volatility drag" or "beta slippage."
**How to avoid:** ALWAYS use day-by-day compounding formula: `SQQQ_n = SQQQ_{n-1} * (1 + (-3) * r_QQQ_n - daily_fee)`. Show both naive -3x AND simulated returns in output so users see the difference.
**Warning signs:** SQQQ returns matching exactly -3x of QQQ cumulative returns; no mention of path dependency in output.
**Validation:** Download historical QQQ and SQQQ data for any 30-day period. Compare simulated vs actual SQQQ. Expect <2% daily tracking error, but multi-day deviation can be 5-15% depending on volatility.

### Pitfall 2: VIX-SPX Regression Overprecision
**What goes wrong:** Presenting VIX-SPX regression results with false precision (e.g., "at -20% drop, VIX will be 54.73").
**Why it happens:** Regression models produce exact numbers, but the underlying relationship is highly variable and regime-dependent.
**How to avoid:** Use round numbers in the VIX-SPX table. Include HC-05 disclaimer: "SQQQ decay is path-dependent, results are approximate." Add disclaimer that VIX-SPX relationship varies by regime and IV expansion estimates are educational, not predictive.
**Warning signs:** Showing 4+ decimal places in IV estimates; claiming "VIX will be X" instead of "VIX is estimated at approximately X."

### Pitfall 3: Ignoring SQQQ Circuit Breaker / Zero Floor
**What goes wrong:** SQQQ simulation produces negative values during extreme scenarios (-40% QQQ drop in a single day would mean SQQQ goes up 120%, which is fine, but if QQQ rises >33% in a day, SQQQ would theoretically go below zero).
**Why it happens:** The formula `(1 + (-3) * r)` can go negative if `r > 0.333` (33% daily gain).
**How to avoid:** Add a `max(value, 0.0)` floor after each day's calculation. In practice, SQQQ has never been in this situation because QQQ has never risen 33% in a single day, and the fund has circuit breakers.
**Warning signs:** Negative SQQQ values in simulation output.

### Pitfall 4: Using Adjusted Close for SQQQ Validation
**What goes wrong:** Comparing simulation against SQQQ Adjusted Close instead of Close, which double-counts distributions.
**Why it happens:** yfinance returns both Close and Adj Close. SQQQ occasionally distributes capital gains.
**How to avoid:** Use raw Close prices for SQQQ validation. Use QQQ raw Close for daily return calculation.
**Warning signs:** Validation shows systematic positive bias (simulation consistently overestimates SQQQ decay).

### Pitfall 5: Put Breakeven Ignoring IV Expansion Benefit
**What goes wrong:** Calculating put breakeven as simply `strike - premium - spot`, which ignores that IV expansion during the drop adds value to the put above intrinsic.
**Why it happens:** Intrinsic value breakeven is simpler to calculate than full Black-Scholes breakeven.
**How to avoid:** For the comparison tool, calculate two breakeven metrics: (1) intrinsic breakeven (simple formula) and (2) full breakeven including IV expansion benefit (requires Black-Scholes repricing). Show both to users. The IV-adjusted breakeven will be a smaller drop (more favorable to the put).
**Warning signs:** Put breakeven showing a larger drop than SQQQ breakeven in all scenarios (puts usually have better breakeven for small drops due to IV expansion).

### Pitfall 6: Not Testing Against Known Academic Results
**What goes wrong:** SQQQ simulation produces plausible-looking but incorrect numbers because there is no reference answer to validate against.
**Why it happens:** Unlike standard Black-Scholes (which has analytical solutions), SQQQ simulation is numerical and path-dependent.
**How to avoid:** Build known-answer tests (STD-04) using: (1) constant daily returns (where analytical solution exists: SQQQ_final = initial * (1 + (-3)*r - fee)^n), (2) zero-return flat market (SQQQ should lose exactly fees + volatility drag), (3) historical 30-day periods where actual SQQQ data is available.
**Warning signs:** No tests with known expected values; tests only check "output is a number."

## Code Examples

Verified patterns from the existing codebase and financial domain:

### Reusing Existing OptionsCalculator for Put Pricing
```python
# Source: src/analysis/options.py (already implemented and tested)
from src.analysis.options import OptionsCalculator, price_option
from src.models.options_inputs import BlackScholesInput

# Convenience function for quick pricing
greeks = price_option(
    spot=480.0,          # QQQ current price
    strike=430.0,        # 10% OTM put
    days_to_expiry=75,   # ~2.5 months
    volatility=0.20,     # Current IV
    option_type="put",
    risk_free_rate=0.045,
)
print(f"Put premium: ${greeks.option_price:.2f}")
print(f"Delta: {greeks.delta:.3f}")
```

### SQQQ Validation Against Historical Data
```python
# Source: yfinance API (already in codebase)
import yfinance as yf
import numpy as np

def validate_sqqq_simulation(start_date: str, end_date: str) -> dict:
    """
    Compare simulated SQQQ against actual SQQQ prices.

    Fetches QQQ daily returns, simulates SQQQ, compares to actual SQQQ.
    Returns tracking error metrics.
    """
    qqq = yf.Ticker("QQQ").history(start=start_date, end=end_date)
    sqqq = yf.Ticker("SQQQ").history(start=start_date, end=end_date)

    qqq_returns = qqq['Close'].pct_change().dropna().tolist()

    # Simulate
    simulated = [sqqq['Close'].iloc[0]]
    for r in qqq_returns:
        prev = simulated[-1]
        new_val = prev * (1.0 + (-3) * r - SQQQ_DAILY_FEE)
        simulated.append(max(new_val, 0.0))

    actual = sqqq['Close'].tolist()

    # Calculate tracking error
    min_len = min(len(simulated), len(actual))
    errors = [(s - a) / a for s, a in zip(simulated[:min_len], actual[:min_len]) if a > 0]

    return {
        "mean_tracking_error": np.mean(errors),
        "max_tracking_error": np.max(np.abs(errors)),
        "rmse": np.sqrt(np.mean(np.array(errors) ** 2)),
        "days": min_len,
    }
```

### CLI Output Format (Following Established Pattern)
```python
# Source: Pattern from src/analysis/correlation_cli.py and risk_metrics_cli.py
def format_comparison_table(output: ComparisonOutput) -> str:
    """Format the SQQQ vs Puts comparison as human-readable text."""
    lines = []
    lines.append(f"\n{'='*80}")
    lines.append("SQQQ vs PROTECTIVE PUTS - HEDGE COMPARISON")
    lines.append(f"{'='*80}\n")

    # Header row
    lines.append(f"{'Scenario':<20} {'SQQQ Return':>14} {'Put P&L':>14} {'Winner':>10}")
    lines.append("-" * 60)

    for row in output.scenarios:
        sqqq_str = f"{row.sqqq.sqqq_return_pct:+.1%}"
        put_str = f"${row.put.pnl:+,.0f}"
        lines.append(f"{row.scenario_label:<20} {sqqq_str:>14} {put_str:>14} {row.winner:>10}")

    lines.append("")
    lines.append(f"SQQQ breakeven: {output.sqqq_breakeven_drop:.1%} QQQ drop")
    lines.append(f"Put breakeven:  {output.put_breakeven_drop:.1%} QQQ drop")

    lines.append(f"\n{'='*80}")
    for d in output.disclaimers:
        lines.append(f"  {d}")
    lines.append(f"{'='*80}\n")

    return "\n".join(lines)
```

### Known-Answer Test for SQQQ Simulation
```python
# Source: Mathematical derivation (analytical for constant returns)
import pytest

class TestSQQQSimulation:
    """Known-answer tests for SQQQ day-by-day simulation."""

    def test_constant_daily_return(self):
        """With constant daily returns, result is analytically deterministic."""
        daily_return = -0.01  # QQQ drops 1% every day
        days = 10
        initial = 10000.0

        # Analytical: value = initial * (1 + (-3)*(-0.01) - fee)^10
        #           = initial * (1.03 - 0.0000377)^10
        daily_factor = 1.0 + (-3) * daily_return - SQQQ_DAILY_FEE
        expected = initial * (daily_factor ** days)

        result = simulate_sqqq_day_by_day([daily_return] * days, initial)
        assert abs(result - expected) < 0.01  # Sub-penny accuracy

    def test_flat_market_loses_to_fees(self):
        """In a flat market (0% daily return), SQQQ loses only fees."""
        days = 252  # Full year
        initial = 10000.0
        result = simulate_sqqq_day_by_day([0.0] * days, initial)

        # Should lose approximately expense ratio over a year
        expected_loss = initial * SQQQ_EXPENSE_RATIO
        actual_loss = initial - result
        assert abs(actual_loss - expected_loss) < 5.0  # Within $5

    def test_volatile_flat_market_has_drag(self):
        """Volatile but net-flat market shows volatility drag."""
        # QQQ: +2%, -2%, +2%, -2%, ... (net ~flat due to compounding)
        days = 20
        daily_returns = [0.02, -0.02] * (days // 2)
        initial = 10000.0

        result = simulate_sqqq_day_by_day(daily_returns, initial)

        # QQQ cumulative: (1.02 * 0.98)^10 = 0.9996^10 ≈ 0.996 (QQQ ~flat)
        # SQQQ with 3x leverage should show MORE drag than QQQ
        # SQQQ daily factors: (1 + (-3)*0.02 = 0.94) and (1 + (-3)*(-0.02) = 1.06)
        # SQQQ cumulative: (0.94 * 1.06)^10 = 0.9964^10 ≈ 0.9646
        # So SQQQ loses about 3.5% even though QQQ is roughly flat
        sqqq_return = (result - initial) / initial
        assert sqqq_return < -0.02  # Should lose at least 2%
        assert sqqq_return > -0.10  # But not catastrophically

    def test_sqqq_cannot_go_negative(self):
        """SQQQ value floored at zero even with extreme daily gain in QQQ."""
        # QQQ gains 40% in one day (impossible but tests floor)
        result = simulate_sqqq_day_by_day([0.40], 10000.0)
        assert result >= 0.0


class TestPutPayoff:
    """Known-answer tests for put payoff calculation."""

    def test_deep_itm_put(self):
        """Deep ITM put should be worth approximately strike - spot."""
        # Spot drops to 80, strike is 100, put should be ~$20 + time value
        result = calculate_put_payoff(
            spot_price=100.0,
            strike=100.0,
            premium_paid=3.0,
            market_drop_pct=-0.20,  # -20% drop
            time_to_expiry=0.20,    # ~73 days
            baseline_iv=0.20,
        )
        assert result["intrinsic"] == pytest.approx(20.0, abs=0.01)
        assert result["put_value"] > 20.0  # IV expansion adds time value
        assert result["pnl"] > 0  # Should be profitable at -20%

    def test_otm_put_at_zero_drop(self):
        """OTM put with no drop should lose premium."""
        result = calculate_put_payoff(
            spot_price=100.0,
            strike=90.0,        # 10% OTM
            premium_paid=2.0,
            market_drop_pct=0.0,
            time_to_expiry=0.20,
            baseline_iv=0.20,
        )
        assert result["intrinsic"] == 0.0
        assert result["pnl"] < 0  # Loses premium


class TestBreakeven:
    """Known-answer tests for breakeven analysis."""

    def test_put_breakeven_atm(self):
        """ATM put breakeven should be approximately premium / spot."""
        be = find_breakeven_put(
            premium_paid=5.0,
            spot_price=100.0,
            strike=100.0,
        )
        # Breakeven: spot must fall to 95 (strike - premium)
        # Drop = (95 - 100) / 100 = -5%
        assert abs(be - (-0.05)) < 0.001
```

## VIX-SPX Regression Model Detail

### Historical Data Points (for calibration)

| Event | Date | SPX Drop | VIX Start | VIX Peak | VIX Multiple |
|-------|------|----------|-----------|----------|--------------|
| 2008 GFC | Sep-Nov 2008 | -46% (peak-to-trough) | ~22 | 89.53 (intraday) / 80.86 (close) | 3.7x |
| 2018 Volmageddon | Feb 5, 2018 | -5% (intraday) | 17.31 | 37.32 | 2.2x |
| 2020 COVID | Feb-Mar 2020 | -34% (peak-to-trough) | ~14 | 82.69 (close) | 5.9x |
| 2025 Tariffs | Apr 2025 | ~-12% | ~18 | ~45 | 2.5x |

### Regression Model

The VIX-SPX relationship is non-linear and convex (Whaley 2000, Sepp 2018). A simple linear model explains ~60% of variance but severely underestimates extreme moves. The conditional model shows that a -7% SPX decline produces ~80% VIX increase under low-volatility starting conditions.

**Recommended model for this tool:** Piecewise linear interpolation with conservative estimates:

```python
# Conservative VIX estimates at market drop levels
# Sources: macroption.com VIX historical data, Whaley (2000), Sepp (2018)
VIX_AT_DROP = {
    0.00:  18,   # Normal market (long-term VIX median ~17-19)
    -0.05: 28,   # Mild correction (2018 Volmageddon: 37, but that was extreme)
    -0.10: 38,   # Moderate correction (2025 tariff shock: ~45 at -12%)
    -0.20: 55,   # Bear market (between moderate and crisis)
    -0.40: 80,   # Full crisis (2008: 80-89, 2020: 82)
}
```

**Confidence: MEDIUM.** These values are rounded estimates from historical data. The actual VIX at any given SPX drop depends heavily on: (1) starting VIX level, (2) speed of the drop, (3) whether the drop is expected or surprise, (4) macro regime. The tool MUST include a disclaimer (HC-05) stating these are approximations.

### IV Scaling Formula

To translate VIX to QQQ put IV:
```
QQQ_IV_estimated = baseline_QQQ_IV * (VIX_at_drop / baseline_VIX)
```

This assumes QQQ IV moves proportionally to VIX, which is approximately true because:
- QQQ has ~1.1 beta to SPX
- VIX measures SPX option IV
- QQQ IV is typically slightly higher than SPX IV due to tech concentration

For greater accuracy, multiply by a QQQ beta factor of 1.1-1.2, but the base model without this factor is adequate for an educational comparison tool.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Simple -3x multiplication | Day-by-day compounding simulation | Always been wrong, but still common in online discussions | Critical: use day-by-day or results are meaningless |
| Constant IV for put pricing | IV expansion using VIX-SPX regression | Academic literature 2000s+ (Whaley, CBOE research) | Moderate: significantly changes put value at large drops |
| Gaussian VIX-SPX model | Conditional/convex VIX-SPX model | Sepp (2018) showed linear model fails at extremes | Low impact for this tool: piecewise interpolation handles this |
| Single scenario per drop | Multiple path scenarios per drop | Recent LETF research (Hsieh et al., 2025) | Enhancement opportunity: show best/worst SQQQ outcomes per drop level |

**Deprecated/outdated:**
- Using VIX as a direct volatility forecast: VIX systematically overestimates realized volatility (the "variance premium"). For this tool, this is not a concern because we use VIX as an IV proxy, not a realized vol forecast.
- Using `auto_adjust=True` in yfinance without understanding: For SQQQ validation, use raw Close prices.

## Open Questions

Things that couldn't be fully resolved:

1. **VIX-SPX regression precision for the -40% scenario**
   - What we know: VIX peaked at ~80-89 during 2008 (SPX -57% total) and 2020 (SPX -34% total). At -40%, VIX of 80 is a reasonable estimate.
   - What's unclear: The exact VIX level at exactly -40% (not peak-to-trough). VIX spikes are intraday and short-lived; the closing VIX may be lower.
   - Recommendation: Use 80 as the -40% VIX estimate. Add disclaimer that this is based on 2008/2020 crash peaks. Flag for validation: compare against VIX daily data from FRED during crash periods.
   - Confidence: MEDIUM

2. **SQQQ tracking error magnitude during extreme volatility**
   - What we know: Normal tracking error is <0.5% daily. During high volatility, tracking error can be 1-3% daily due to execution slippage, futures roll costs, and intraday rebalancing timing.
   - What's unclear: Exact magnitude during the -40% scenario (which implies extreme daily volatility).
   - Recommendation: Include a note in output that simulation assumes perfect daily rebalancing. Actual SQQQ may deviate more during extreme events. Acceptable validation threshold: <5% cumulative error over 30 days in normal markets.
   - Confidence: MEDIUM

3. **Phase 6 HedgeConfig field for SQQQ allocation**
   - What we know: Phase 6 research shows `sqqq_allocation_pct: 0.06` (6% of Layer 3) in the YAML template.
   - What's unclear: Whether Phase 6 has been implemented yet. If not, Phase 9 needs to handle missing config gracefully.
   - Recommendation: Use `config_loader.load_hedge_config()` with fallback defaults. If `sqqq_allocation_pct` is not in config, default to a reasonable comparison amount (e.g., $1,000 for both SQQQ and put premium).
   - Confidence: HIGH (fallback pattern is established)

4. **HEDG-12: Integration test for all 4 CLI tools**
   - What we know: Success criterion #5 requires `--help` to work for total_return, rolling_tracker, hedge_sizer, and hedge_comparison CLIs. Phase 9 only creates hedge_comparison.
   - What's unclear: Whether the other 3 CLIs exist when Phase 9 runs (depends on Phase 7 and 8 completion).
   - Recommendation: Phase 9 tests should verify hedge_comparison_cli.py works with `--help`. The cross-CLI integration test (HEDG-12) should be a final verification step that checks all 4, run after all phases are complete.
   - Confidence: HIGH

5. **Architecture diagram scope (HEDG-11)**
   - What we know: Requirement says "Architecture diagram (.mmd) showing all new M2 components." An existing diagram exists at `.dev/specs/backlog/diagrams/finance-guru-hedging-integration-arch.mmd` that covers the full M2 scope.
   - What's unclear: Whether HEDG-11 wants a NEW diagram or an UPDATE to the existing one. The existing diagram already shows hedge_comparison.py.
   - Recommendation: Update the existing `.mmd` diagram to reflect the actual implemented components and data flow. Create a focused diagram in `docs/architecture/` that shows just the M2 data flow (not the full system).
   - Confidence: HIGH

## Sources

### Primary (HIGH confidence)
- Codebase direct inspection: `src/analysis/options.py` -- complete Black-Scholes implementation with `price_option()`, `_put_price()`, `calculate_implied_vol()` (497 lines, tested)
- Codebase direct inspection: `src/models/options_inputs.py` -- `BlackScholesInput`, `GreeksOutput`, `OptionContractData` models (403 lines)
- Codebase direct inspection: `pyproject.toml` -- scipy 1.16.2, numpy 2.3.3, pandas 2.3.2, pydantic 2.12.0 confirmed
- Codebase direct inspection: Phase 6 research (`.planning/phases/06/06-RESEARCH.md`) -- `HedgeConfig`, `config_loader.py`, hedging model design
- Codebase direct inspection: Phase 7 research (`.planning/phases/07/07-RESEARCH.md`) -- `TotalReturnCalculator`, yfinance dividend patterns
- ProShares SQQQ prospectus (September 2025) -- expense ratio 0.95% net, daily -3x target, path-dependency disclosure
- ProShares SQQQ product page (proshares.com) -- confirmed 0.95% net expense ratio with fee waiver through Sep 2026

### Secondary (MEDIUM confidence)
- [Hsieh et al. (2025)](https://arxiv.org/html/2504.20116v1) -- "Compounding Effects in Leveraged ETFs: Beyond the Volatility Drag Paradigm" -- confirms volatility drag formula, AR(1)/GARCH modeling of LETF returns
- [macroption.com VIX all-time high](https://www.macroption.com/vix-all-time-high/) -- VIX peak levels: 89.53 (2008 intraday), 82.69 (2020 close), 37.32 (2018)
- [Whaley (2000/2009)](https://w4.stern.nyu.edu/glucksman/docs/Manda2010.pdf) -- VIX-SPX regression: -0.707% SPX per 100bp VIX increase; strengthened during 2008 crisis to -1.468%
- [Sepp (2018)](https://artursepp.com/2018/02/15/lessons-from-the-crash-of-short-volatility-etfs/) -- Conditional convexity in VIX-SPX: -7% SPX → +80% VIX (1-month futures); linear model requires -26% SPX for +100% VIX
- [Columbia Black-Scholes reference](https://www.columbia.edu/~mh2078/FoundationsFE/BlackScholes.pdf) -- Black-Scholes PDE and put pricing formula verification

### Tertiary (LOW confidence)
- [FasterCapital Beta Slippage explainer](https://fastercapital.com/content/Beta-Slippage--Navigating-the-Slippery-Slope--Understanding-Beta-Slippage-in-Leveraged-ETFs.html) -- conceptual explanation of beta slippage (cross-verified with academic source)
- [Aptus Capital volatility drag article](https://aptuscapitaladvisors.com/leveraged-etfs-the-hidden-costs-of-volatility-drag/) -- volatility drag formula: geometric mean = arithmetic mean - (StdDev^2 / 2) (cross-verified with Hsieh et al.)
- [FRED VIX historical data](https://fred.stlouisfed.org/series/VIXCLS) -- available for validation of VIX levels during specific dates (not fetched, but reliable source)
- IV expansion rule of thumb (~1.5-2.5 IV points per 1% SPX drop) -- practitioner estimate, no single authoritative source; should be validated against historical options data

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- All libraries already installed; zero new dependencies needed
- SQQQ simulation formula: HIGH -- Well-documented daily compounding formula, verified against ProShares prospectus and academic literature
- Put payoff calculation: HIGH -- Reuses existing tested Black-Scholes implementation
- VIX-SPX regression parameters: MEDIUM -- Based on historical crash data from multiple sources, but relationship is regime-dependent and approximate
- Breakeven analysis: HIGH -- Mathematical formula is deterministic; scipy.optimize.brentq is well-tested
- Architecture patterns: HIGH -- Follows established 3-layer codebase convention with 15+ existing examples
- Volatility drag formula: HIGH -- Confirmed by both academic paper (Hsieh 2025) and practitioner sources

**Research date:** 2026-02-02
**Valid until:** 2026-03-04 (30 days -- stable domain; VIX-SPX regression parameters may need updating if a new major crash occurs that changes the empirical relationship)
