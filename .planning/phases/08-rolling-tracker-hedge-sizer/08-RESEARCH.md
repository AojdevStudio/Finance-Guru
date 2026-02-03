# Phase 8: Rolling Tracker & Hedge Sizer - Research

**Researched:** 2026-02-02
**Domain:** Options position tracking, roll management, hedge sizing, argparse subcommands, Black-Scholes American-style limitations, agent knowledge base integration
**Confidence:** HIGH

## Summary

Phase 8 builds two new CLI tools -- `rolling_tracker_cli.py` (position monitoring + roll suggestions) and `hedge_sizer_cli.py` (contract sizing + budget validation) -- plus knowledge base files and agent definition updates. This is the most complex phase in M2 because it combines live market data (yfinance options chains), YAML state management (positions.yaml, roll-history.yaml, budget-tracker.yaml), integration with Phase 6's shared models and config loader, and the first argparse subcommand pattern in the codebase.

The primary technical risks are: (1) the `scan_chain()` function in `options_chain_cli.py` has 12 `print(..., file=sys.stderr)` statements that pollute stderr when called programmatically -- this is a known concern from STATE.md; (2) yfinance options chain data can have NaN values, zero bid/ask spreads, and stale pricing; (3) American-style options (which US equity options are) cannot be correctly priced by Black-Scholes alone -- an intrinsic value floor is required. All three concerns have clean mitigations documented below.

The established 3-layer architecture (Models -> Calculator -> CLI) applies to both tools. Phase 6 creates the required Pydantic models (`HedgePosition`, `RollSuggestion`, `HedgeSizeRequest`) and config infrastructure (`load_hedge_config()`, `HedgeConfig`). Phase 8 consumes these directly. No new dependencies are required.

**Primary recommendation:** Build `rolling_tracker_cli.py` with argparse subcommands (status, suggest-roll, log-roll, history) using `add_subparsers(dest='command', required=True)` with `set_defaults(func=handler)` per subcommand. Build `hedge_sizer_cli.py` as a standard single-command argparse CLI (matching the existing 15-tool pattern). Wrap `scan_chain()` by redirecting stderr to suppress its progress messages when called from the rolling tracker. Apply `max(bs_price, intrinsic_value)` floor for all American-style put pricing.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pydantic | 2.12.0 | Model validation (HedgePosition, RollSuggestion, HedgeSizeRequest, HedgeConfig) | Already installed; Phase 6 creates the models |
| pyyaml | 6.0.3 | YAML read/write for positions.yaml, roll-history.yaml, budget-tracker.yaml | Already installed; used by src/config.py and config_loader.py |
| yfinance | >=0.2.66 | Options chain data (Ticker.option_chain, Ticker.options), spot prices | Already installed; used by options_chain_cli.py |
| argparse | stdlib | CLI with subcommands (rolling_tracker) and standard args (hedge_sizer) | Used by all 15+ existing CLIs |
| scipy.stats | (scipy) | norm.cdf/norm.pdf for Black-Scholes Greeks | Already installed; used by src/analysis/options.py |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| datetime | stdlib | DTE calculations, date comparisons | Position status, roll window detection |
| math | stdlib | math.floor for contract sizing, math.isnan for NaN handling | Hedge sizer formula, yfinance data cleanup |
| pathlib | stdlib | Path resolution for YAML files | Reading/writing positions.yaml etc. |
| json | stdlib | JSON output serialization | --output json flag on both CLIs |
| io.StringIO | stdlib | Capturing stderr from scan_chain() | Suppressing scan_chain progress output |
| contextlib.redirect_stderr | stdlib | Clean stderr suppression | Wrapping scan_chain() calls |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| argparse subcommands | click/typer | argparse is the codebase standard; click adds dependency |
| YAML state files | SQLite | YAML is human-readable, already the pattern; SQLite is overkill for <100 records |
| scan_chain() wrapper | Refactor scan_chain() | Pragmatic wrapping avoids modifying tested, working code |
| Black-Scholes + floor | Binomial tree model | BS + intrinsic floor is standard industry shortcut; binomial is over-engineered for this use case |

**Installation:**
```bash
# No new dependencies required. Everything already in pyproject.toml.
```

## Architecture Patterns

### Recommended Project Structure
```
src/
  models/
    hedging_inputs.py        # [Phase 6] HedgePosition, RollSuggestion, HedgeSizeRequest
  config/
    config_loader.py         # [Phase 6] HedgeConfig, load_hedge_config()
  analysis/
    rolling_tracker.py       # [Phase 8] RollingTracker calculator class (Layer 2)
    rolling_tracker_cli.py   # [Phase 8] CLI with subcommands (Layer 3)
    hedge_sizer.py           # [Phase 8] HedgeSizer calculator class (Layer 2)
    hedge_sizer_cli.py       # [Phase 8] CLI interface (Layer 3)
    options_chain_cli.py     # [Existing] scan_chain() function to import
    options.py               # [Existing] price_option() for BS pricing

fin-guru/
  data/
    hedging-strategies.md          # [Phase 8] Knowledge base - hedging strategies
    options-insurance-framework.md # [Phase 8] Knowledge base - options as insurance
  agents/
    strategy-advisor.md      # [Phase 8] Add knowledge file references
    teaching-specialist.md   # [Phase 8] Add knowledge file references
    quant-analyst.md         # [Phase 8] Add knowledge file references

fin-guru-private/
  hedging/
    positions.yaml           # [Phase 6 scaffolds] Active positions (Phase 8 reads/writes)
    roll-history.yaml        # [Phase 6 scaffolds] Roll records (Phase 8 appends)
    budget-tracker.yaml      # [Phase 6 scaffolds] Budget tracking (Phase 8 updates)

tests/
  python/
    test_rolling_tracker.py  # [Phase 8] Known-answer tests
    test_hedge_sizer.py      # [Phase 8] Known-answer tests
```

### Pattern 1: Argparse Subcommands (NEW pattern for this codebase)
**What:** A single CLI with multiple subcommands (status, suggest-roll, log-roll, history)
**When to use:** rolling_tracker_cli.py -- the first subcommand CLI in the codebase
**Why new:** All 15 existing CLIs use a flat argparse pattern. The rolling tracker has 4 distinct operations on the same data, making subcommands the natural fit. HEDG-04 explicitly requires this.

```python
# Source: Python 3.12+ argparse docs, verified pattern
import argparse
import sys

def cmd_status(args):
    """Display current hedge positions with P&L, DTE, value."""
    # Implementation
    pass

def cmd_suggest_roll(args):
    """Identify positions within DTE roll window and scan for replacements."""
    # Implementation
    pass

def cmd_log_roll(args):
    """Record a completed roll (close old position, open new)."""
    # Implementation
    pass

def cmd_history(args):
    """Display roll history."""
    # Implementation
    pass

def main():
    parser = argparse.ArgumentParser(
        description='Rolling Tracker - Monitor and manage hedge positions',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s status                           Show current positions with P&L
  %(prog)s suggest-roll                     Find positions needing rolls
  %(prog)s suggest-roll --window 14         Custom roll window (14 days)
  %(prog)s log-roll --old QQQ260417P00420000 --new QQQ260619P00440000 --cost 8.50
  %(prog)s history                          Show roll history
  %(prog)s history --output json            Roll history as JSON
        """,
    )

    # Shared top-level arguments
    parser.add_argument(
        '--output', choices=['human', 'json'], default='human',
        help='Output format (default: human)'
    )
    parser.add_argument(
        '--config', type=str, default=None,
        help='Path to user-profile.yaml (default: auto-detect)'
    )

    # Subcommands
    subparsers = parser.add_subparsers(
        dest='command',
        required=True,
        help='Available commands'
    )

    # status subcommand
    status_parser = subparsers.add_parser('status', help='Display current positions')
    status_parser.set_defaults(func=cmd_status)

    # suggest-roll subcommand
    roll_parser = subparsers.add_parser('suggest-roll', help='Find positions needing rolls')
    roll_parser.add_argument(
        '--window', type=int, default=None,
        help='Roll window in days (default: from config, usually 7)'
    )
    roll_parser.set_defaults(func=cmd_suggest_roll)

    # log-roll subcommand
    log_parser = subparsers.add_parser('log-roll', help='Record a completed roll')
    log_parser.add_argument('--old', required=True, help='Old contract symbol to close')
    log_parser.add_argument('--new', required=True, help='New contract symbol opened')
    log_parser.add_argument('--cost', type=float, required=True, help='Premium paid for new contract')
    log_parser.add_argument('--received', type=float, default=0.0, help='Premium received for closing old')
    log_parser.set_defaults(func=cmd_log_roll)

    # history subcommand
    hist_parser = subparsers.add_parser('history', help='Display roll history')
    hist_parser.set_defaults(func=cmd_history)

    args = parser.parse_args()
    return args.func(args)

if __name__ == '__main__':
    sys.exit(main() or 0)
```

**Key conventions for this codebase:**
- Use `required=True` on subparsers (prevents confusing error on missing subcommand)
- Use `set_defaults(func=handler)` pattern (clean dispatch without if/elif chain)
- Top-level `--output` and `--config` shared by all subcommands
- Subcommand-specific args (like `--window` for suggest-roll) on individual parsers
- Hyphenated subcommand names (`suggest-roll`, `log-roll`) match CLI convention
- Each handler returns int (0 success, 1 error) for sys.exit

### Pattern 2: YAML State Management (positions.yaml read/write)
**What:** Load positions from YAML, update them, write back
**When to use:** rolling_tracker status, log-roll; hedge_sizer budget validation

```python
# Source: Codebase pattern from src/config.py + Phase 6 template design
import yaml
from pathlib import Path
from src.models.hedging_inputs import HedgePosition

PROJECT_ROOT = Path(__file__).parent.parent.parent
HEDGING_DIR = PROJECT_ROOT / "fin-guru-private" / "hedging"

def load_positions() -> list[HedgePosition]:
    """Load active hedge positions from positions.yaml."""
    positions_file = HEDGING_DIR / "positions.yaml"
    if not positions_file.exists():
        return []

    try:
        with open(positions_file) as f:
            data = yaml.safe_load(f) or {}
    except Exception:
        return []

    raw_positions = data.get("positions", [])
    if not raw_positions:
        return []

    positions = []
    for entry in raw_positions:
        try:
            positions.append(HedgePosition(**entry))
        except Exception as e:
            print(f"Warning: Skipping invalid position: {e}", file=sys.stderr)
    return positions

def save_positions(positions: list[HedgePosition]) -> None:
    """Write positions back to positions.yaml."""
    HEDGING_DIR.mkdir(parents=True, exist_ok=True)
    data = {"positions": [p.model_dump(mode="json") for p in positions]}
    with open(HEDGING_DIR / "positions.yaml", "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
```

### Pattern 3: Wrapping scan_chain() to Suppress stderr
**What:** Call the existing `scan_chain()` function while suppressing its 12+ progress messages to stderr
**When to use:** rolling_tracker suggest-roll subcommand

The `scan_chain()` function in `options_chain_cli.py` (lines 222-226, 233, 237, 244, 275, 288, 366, 395, 401) writes progress messages like "Fetching spot price for QQQ..." and "Scanning 2026-04-17 (60 days out)..." to stderr. These are useful for interactive CLI usage but pollute output when called programmatically by the rolling tracker.

**Side effects inventory (verified from codebase):**
- Line 222: `print(f"Fetching spot price for {ticker}...", file=sys.stderr)`
- Line 226: `print(f"Spot price: ${spot_price:.2f}", file=sys.stderr)`
- Line 233: `print("Fetching available expirations...", file=sys.stderr)`
- Line 237: `print(f"Found {len(all_expirations)} expiration dates", file=sys.stderr)`
- Line 244: `print(f"Expirations in {days_min}-{days_max} day range: ...", file=sys.stderr)`
- Line 250-253: `print(f"No expirations found...", file=sys.stderr)` (early return path)
- Line 275: `print(f"Scanning {exp_str} ({days_to_expiry} days out)...", file=sys.stderr)`
- Line 288: `print(f"  No {option_type}s found for {exp_str}", file=sys.stderr)`
- Line 366-369: `print(f"  Greeks calc failed...", file=sys.stderr)` (error path)
- Line 395: `print(f"  Error scanning {exp_str}: {e}", file=sys.stderr)` (error path)
- Line 401: `print(f"Found {len(contracts)} matching contracts", file=sys.stderr)`

**Recommended approach: `contextlib.redirect_stderr`**

```python
# Source: Python 3.12 stdlib contextlib
import io
from contextlib import redirect_stderr
from src.analysis.options_chain_cli import scan_chain

def scan_chain_quiet(
    ticker: str,
    option_type: str,
    otm_min: float,
    otm_max: float,
    days_min: int,
    days_max: int,
    budget: float | None = None,
    target_contracts: int = 1,
) -> OptionsChainOutput:
    """Call scan_chain() with stderr suppressed."""
    stderr_capture = io.StringIO()
    with redirect_stderr(stderr_capture):
        result = scan_chain(
            ticker=ticker,
            option_type=option_type,
            otm_min=otm_min,
            otm_max=otm_max,
            days_min=days_min,
            days_max=days_max,
            budget=budget,
            target_contracts=target_contracts,
        )
    return result
```

**Why this approach over refactoring scan_chain():**
- scan_chain() is tested, working code (738-line file with comprehensive logic)
- Modifying it risks regressions to the existing options_chain_cli.py
- redirect_stderr is zero-cost, zero-risk, stdlib only
- If error messages from scan_chain() are needed, the captured StringIO can be logged at DEBUG level

### Pattern 4: Hedge Sizing Formula
**What:** Calculate contract counts from portfolio value with configurable ratio
**When to use:** hedge_sizer_cli.py core logic

```python
# Source: Requirement HS-01: floor(portfolio_value / 50000) baseline
import math

def calculate_contract_count(
    portfolio_value: float,
    ratio_per_contract: float = 50000.0,
) -> int:
    """
    Calculate number of hedge contracts.

    Formula: floor(portfolio_value / ratio_per_contract)
    Default: 1 contract per $50,000 of portfolio value

    Example: $200,000 portfolio -> floor(200000/50000) = 4 contracts
    """
    if portfolio_value <= 0 or ratio_per_contract <= 0:
        return 0
    return math.floor(portfolio_value / ratio_per_contract)

def allocate_contracts(
    total_contracts: int,
    underlying_weights: dict[str, float],
) -> dict[str, int]:
    """
    Distribute contracts across underlyings by weight.

    Example: 4 contracts, {"QQQ": 0.6, "SPY": 0.4}
    -> {"QQQ": 2, "SPY": 2} (floor rounding, remainder to largest weight)
    """
    allocated = {}
    remaining = total_contracts

    # Sort by weight descending for remainder allocation
    sorted_underlyings = sorted(
        underlying_weights.items(), key=lambda x: x[1], reverse=True
    )

    for ticker, weight in sorted_underlyings:
        count = math.floor(total_contracts * weight)
        allocated[ticker] = count
        remaining -= count

    # Distribute remainder to highest-weight underlyings
    for ticker, _ in sorted_underlyings:
        if remaining <= 0:
            break
        allocated[ticker] += 1
        remaining -= 1

    return allocated
```

### Pattern 5: Budget Validation with Live Premiums
**What:** Fetch current option premiums via yfinance and compare against monthly budget
**When to use:** hedge_sizer_cli.py budget validation (HS-02)

```python
# Budget validation flow:
# 1. Calculate contract count from portfolio value
# 2. For each underlying, fetch current put premium from options chain
# 3. Calculate total cost = contracts * premium * 100
# 4. Compare against monthly budget
# 5. Show utilization percentage

def validate_budget(
    contract_allocations: dict[str, int],  # {"QQQ": 3, "SPY": 1}
    config: HedgeConfig,
) -> dict:
    """
    Validate hedge cost against monthly budget.

    Returns dict with:
      - total_estimated_cost: float
      - monthly_budget: float
      - utilization_pct: float (0-100+)
      - per_underlying: list of per-ticker details
      - within_budget: bool
    """
    # For each underlying, scan for a representative put premium
    # Use scan_chain_quiet() with config's OTM and DTE parameters
    # Take the median premium from results as the estimate
    # total_cost = sum(contracts * median_premium * 100 for each underlying)
    pass
```

### Pattern 6: American Options - Intrinsic Value Floor
**What:** Apply `max(bs_price, intrinsic_value)` to all put pricing
**When to use:** Any Black-Scholes calculation for US equity options (which are American-style)

```python
# Source: Standard derivatives pricing practice
# Black-Scholes assumes European exercise (only at expiry).
# American puts can be exercised anytime, so their price is ALWAYS >= intrinsic value.
# For deep ITM puts near expiry, BS can underestimate significantly.

from src.analysis.options import price_option

def price_american_put(
    spot: float,
    strike: float,
    days_to_expiry: int,
    volatility: float,
    risk_free_rate: float = 0.045,
    dividend_yield: float = 0.0,
) -> float:
    """
    Price an American-style put with intrinsic value floor.

    BS limitation: European model can price puts BELOW intrinsic value
    for deep ITM options near expiry. American puts are always worth at
    least their intrinsic value (since you can exercise immediately).

    Adjustment: max(bs_price, intrinsic_value)
    """
    greeks = price_option(
        spot=spot,
        strike=strike,
        days_to_expiry=days_to_expiry,
        volatility=volatility,
        option_type="put",
        risk_free_rate=risk_free_rate,
        dividend_yield=dividend_yield,
    )

    intrinsic_value = max(strike - spot, 0.0)
    adjusted_price = max(greeks.option_price, intrinsic_value)

    return adjusted_price
```

### Anti-Patterns to Avoid
- **Calling scan_chain() without stderr suppression:** Progress messages from scan_chain() will intermix with your CLI output, confusing users and agents
- **Modifying options_chain_cli.py:** Introduces regression risk to a tested 738-line file; wrap instead
- **Writing positions.yaml without Pydantic validation:** Always load raw YAML into HedgePosition models before saving back -- ensures data integrity
- **Hardcoding $50,000 per contract:** Use HedgeConfig for the ratio; the requirement says "configurable ratio via HedgeConfig"
- **Using Black-Scholes price directly for American puts:** Must apply intrinsic value floor; BS can underestimate deep ITM puts
- **Treating budget-tracker.yaml as a database:** It is a simple monthly tracking file; do not try to implement transactions or locking
- **Creating subcommands in hedge_sizer_cli.py:** The sizer is a single operation (size -> validate -> output); use standard flat argparse like all other CLIs

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Options chain scanning | Custom yfinance chain parsing | `scan_chain()` from options_chain_cli.py | 400+ lines of tested NaN handling, OTM filtering, Greeks calculation |
| Black-Scholes pricing | Custom BS implementation | `price_option()` from options.py | 500-line tested calculator with all Greeks |
| Config loading | Direct YAML parsing in CLI | `load_hedge_config()` from config_loader.py | DRY bridge with override chain, Phase 6 tested |
| Position validation | Manual field checks | `HedgePosition(**data)` Pydantic model | Validates ticker uppercase, strike positive, put-requires-expiry |
| Roll suggestion validation | Manual dict building | `RollSuggestion(...)` Pydantic model | Validates future expiry, positive cost |
| JSON output | Custom dict serialization | `model.model_dump_json(indent=2)` | Pydantic handles date serialization automatically |
| Spot price fetching | Custom yfinance wrapper | `get_prices()` from market_data.py | Already handles single/multi ticker, error handling |
| Contract sizing formula | Inline math | Dedicated `calculate_contract_count()` function | Testable, reusable, matches existing calculator class pattern |

**Key insight:** Phase 8 is primarily an *integration* phase. The heavy lifting (options chain scanning, BS pricing, config loading, model validation) is already built. Phase 8 wires these together into two user-facing CLIs.

## Common Pitfalls

### Pitfall 1: scan_chain() stderr Pollution
**What goes wrong:** Rolling tracker output is cluttered with "Fetching spot price..." messages from scan_chain()
**Why it happens:** scan_chain() was designed for interactive CLI use and prints progress to stderr (12 print statements)
**How to avoid:** Use `contextlib.redirect_stderr(io.StringIO())` to capture and suppress stderr when calling scan_chain() programmatically (see Architecture Pattern 3)
**Warning signs:** CLI output has interleaved progress messages; JSON output is invalid because stderr and stdout mix

### Pitfall 2: positions.yaml Date Serialization
**What goes wrong:** YAML dates are loaded as datetime.date objects by PyYAML, but Pydantic expects strings or specific formats; OR dates are written back as Python repr strings
**Why it happens:** PyYAML has native date handling -- `"2026-04-17"` can be parsed as either str or date depending on quoting. HedgePosition has `expiry: date | None` which needs a date object, not a string.
**How to avoid:** When loading from YAML, PyYAML will parse unquoted dates like `2026-04-17` as `datetime.date` objects, which is correct for HedgePosition. When writing, use `model_dump(mode="json")` which serializes dates as ISO strings. Always quote dates in the YAML templates to be explicit.
**Warning signs:** `ValidationError: invalid date format`; dates appearing as `2026-04-17 00:00:00` in YAML

### Pitfall 3: DTE Calculation Off-by-One
**What goes wrong:** Position shows DTE of 0 on expiration day but options may still have value until market close
**Why it happens:** `(expiry_date - today).days` gives 0 on the expiry date itself
**How to avoid:** DTE of 0 is correct for the "days remaining" display. The roll window check should use `dte <= roll_window_days` (inclusive) so that positions expiring TODAY are flagged for roll. Document this clearly.
**Warning signs:** Position with 0 DTE not showing in roll suggestions when it should

### Pitfall 4: Budget Validation with Stale Premiums
**What goes wrong:** Budget shows "within budget" but actual premium has moved since the scan
**Why it happens:** Options premiums change continuously during market hours; the scan is a point-in-time snapshot
**How to avoid:** Always label the estimate clearly: "Estimated cost based on mid-price as of [scan time]". Add a warning: "Actual premium may differ. Verify before executing trade."
**Warning signs:** User relies on budget validation as an execution guarantee

### Pitfall 5: Empty positions.yaml Handling
**What goes wrong:** `yaml.safe_load()` returns `None` for an empty file; `data.get("positions", [])` throws AttributeError
**Why it happens:** An empty YAML file parses to None, not an empty dict
**How to avoid:** Always use `data = yaml.safe_load(f) or {}` -- the `or {}` handles the None case
**Warning signs:** `AttributeError: 'NoneType' object has no attribute 'get'`

### Pitfall 6: Contract Symbol Lookup Mismatch
**What goes wrong:** User tries to log a roll with `--old QQQ260417P420` but positions.yaml has `QQQ260417P00420000` (full OCC format)
**Why it happens:** Options contract symbols have a specific 21-character OCC format. Users may abbreviate.
**How to avoid:** For log-roll, match by contract_symbol exactly (require full OCC format) OR implement a prefix/contains match. Recommend requiring exact match for v1 simplicity and documenting the expected format in --help.
**Warning signs:** "Position not found" error when user knows the position exists

### Pitfall 7: Multi-Underlying Weight Validation in Sizer
**What goes wrong:** Weights sum to >1.0 or <1.0, causing under/over-allocation of contracts
**Why it happens:** User passes --underlyings QQQ,SPY but weights come from config where they may not sum to 1.0
**How to avoid:** HedgeConfig already validates weights sum near 1.0 (Phase 6 model_validator). When CLI passes `--underlyings` as a comma-separated list, use the config weights for those underlyings only. If the requested underlyings are not all in the weight config, fall back to equal weighting.
**Warning signs:** Total allocated contracts does not equal calculated total; "weight sum" validation error

## Code Examples

Verified patterns from the existing codebase:

### Loading HedgeConfig for CLI Use
```python
# Source: Phase 6 config_loader.py pattern (from 06-02-PLAN.md)
from pathlib import Path
from src.config.config_loader import load_hedge_config

def main():
    args = parse_args()

    # Build CLI override dict (None values filtered by config_loader)
    cli_overrides = {
        "roll_window_days": getattr(args, 'window', None),
        "monthly_budget": getattr(args, 'budget', None),
    }

    config_path = Path(args.config) if args.config else None
    config = load_hedge_config(
        profile_path=config_path,
        cli_overrides=cli_overrides,
    )
    # config now has: CLI value > YAML value > Pydantic default
```

### Position Status Display with Live Pricing
```python
# Source: Codebase pattern from market_data.py + options_inputs.py
from datetime import date
from src.utils.market_data import get_prices
from src.models.hedging_inputs import HedgePosition

def display_position_status(position: HedgePosition) -> dict:
    """
    Enrich a position with live market data.

    Returns dict with: ticker, type, strike, expiry, dte, entry_premium,
    current_value (estimated), p_and_l, status
    """
    today = date.today()

    # DTE calculation
    dte = (position.expiry - today).days if position.expiry else None

    # For options: estimate current value from spot price + BS pricing
    # For inverse ETFs: use current market price
    if position.hedge_type == "put":
        # Fetch spot price for underlying
        price_data = get_prices(position.ticker)
        spot = price_data[position.ticker].price

        # Current theoretical put value (with intrinsic floor)
        current_value = price_american_put(
            spot=spot,
            strike=position.strike,
            days_to_expiry=max(dte, 1),  # Avoid 0 DTE in BS
            volatility=0.30,  # Use IV from last scan if available, else default
        )
    else:  # inverse_etf
        price_data = get_prices(position.ticker)
        current_value = price_data[position.ticker].price

    # P&L calculation
    entry_cost = position.premium_paid * (100 if position.hedge_type == "put" else position.quantity)
    current_total = current_value * (100 if position.hedge_type == "put" else position.quantity) * position.quantity
    p_and_l = current_total - entry_cost

    return {
        "ticker": position.ticker,
        "type": position.hedge_type,
        "strike": position.strike,
        "expiry": str(position.expiry) if position.expiry else "N/A",
        "dte": dte,
        "entry_premium": position.premium_paid,
        "current_value": round(current_value, 2),
        "p_and_l": round(p_and_l, 2),
        "status": "ROLL" if dte is not None and dte <= 7 else "OK",
    }
```

### Knowledge Base File Structure
```markdown
<!-- Finance Guru(tm) Hedging Strategies | v1.0 | 2026-02-02 -->

# Hedging Strategies for Portfolio Protection

## Overview

This guide provides educational content on hedging strategies...

[CRITICAL DISCLAIMER]
DISCLAIMER: For educational purposes only. Not investment advice.
Consult a qualified financial professional before implementing any hedging strategy.
[/CRITICAL DISCLAIMER]

## Protective Put Strategy
...

## Options as Insurance
...
```

**Knowledge base file conventions (from existing files in fin-guru/data/):**
- HTML comment header with title, version, date (see margin-strategy.md pattern)
- OR YAML frontmatter with title, description, category, tags (see risk-framework.md pattern)
- Educational disclaimer early in the document
- Markdown with sections, subsections
- Generic/educational content only (no personalized data)
- Referenced by agents via `<i>Load COMPLETE file {project-root}/fin-guru/data/filename.md ...</i>`

### Agent Definition Update Pattern
```xml
<!-- Adding to an agent's <critical-actions> section -->
<critical-actions>
  <!-- ... existing actions ... -->
  <i>Load COMPLETE file {project-root}/fin-guru/data/hedging-strategies.md for hedging strategy context</i>
  <i>Load COMPLETE file {project-root}/fin-guru/data/options-insurance-framework.md for options-as-insurance education</i>
</critical-actions>
```

**Agents to update (HEDG-10):**
1. `strategy-advisor.md` -- Add both knowledge files (Elena Rodriguez-Park needs hedging strategy context)
2. `teaching-specialist.md` -- Add both knowledge files (Maya Brooks needs hedging education content)
3. `quant-analyst.md` -- Add both knowledge files (Dr. Priya Desai needs options pricing context)

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| European BS for all options | BS + intrinsic value floor for American | Standard practice | Prevents underpricing deep ITM puts |
| Flat argparse only | argparse subcommands for multi-operation CLIs | Python 3.2+ (matured) | Natural fit for tracker's 4 operations |
| Manual stderr control | contextlib.redirect_stderr | Python 3.4+ | Clean, stdlib-only solution for scan_chain wrapping |
| Pydantic v1 serialization | model_dump(mode="json") for YAML-safe output | Pydantic 2.0 | Dates serialize as ISO strings for YAML |

**Deprecated/outdated:**
- `@validator` decorator: Replaced by `@field_validator` in Pydantic v2. Codebase uses v2 exclusively.
- Manual argparse dispatch (if/elif on args.command): Replaced by `set_defaults(func=...)` pattern.

## Open Questions

Things that could not be fully resolved:

1. **IV estimate for position status P&L**
   - What we know: To calculate current put value for P&L display, we need implied volatility. The positions.yaml does not store IV at entry.
   - What's unclear: Should we fetch current IV from the options chain for each position? This is slow (requires yfinance API call per position per expiry).
   - Recommendation: For status display, use the BS pricing with a default IV estimate (30%) as a rough P&L indicator. Add a note: "P&L is estimated. For accurate current value, run a full options chain scan." For suggest-roll, the full scan_chain() call will provide accurate market data.

2. **Contract symbol format for log-roll**
   - What we know: OCC options symbols are 21 characters (e.g., `QQQ260417P00420000`). Users may not know this format.
   - What's unclear: Should log-roll accept abbreviated formats?
   - Recommendation: Require full contract symbol for v1 (simpler, unambiguous). Document the format in --help. The suggest-roll output should display full symbols so users can copy-paste them to log-roll.

3. **Budget tracker auto-reset on new month**
   - What we know: budget-tracker.yaml has `current_month` and `spent_this_month` fields.
   - What's unclear: Should the CLI automatically reset `spent_this_month` when the month changes?
   - Recommendation: Yes, implement auto-reset. When hedge_sizer detects `current_month` differs from today's month, set `spent_this_month: 0` and `remaining: monthly_limit`. Append the previous month to `history` if it had any spending.

4. **Dividend yield for BS pricing of puts on ETFs**
   - What we know: QQQ/SPY/IWM pay small dividends. The existing `price_option()` accepts `dividend_yield` parameter (default 0.0).
   - What's unclear: Should we fetch actual dividend yield for each underlying?
   - Recommendation: Use 0.0 for v1. The dividend yield effect on put pricing is small for ETFs with <2% yield. Document this as a known simplification. Phase 9 or a future iteration can add dividend yield lookup if needed.

## Sources

### Primary (HIGH confidence)
- Codebase direct inspection: `src/analysis/options_chain_cli.py` (738 lines) -- scan_chain() function signature, inputs, outputs, all 12 stderr print statements documented
- Codebase direct inspection: `src/analysis/options.py` (503 lines) -- price_option() convenience function, OptionsCalculator class, Black-Scholes implementation
- Codebase direct inspection: `src/models/options_inputs.py` (404 lines) -- OptionContractData, OptionsChainOutput models
- Codebase direct inspection: `src/utils/market_data.py` -- get_prices() function for spot price fetching
- Codebase direct inspection: All 15 existing CLI files -- argparse patterns, output formatting, disclaimer conventions
- Codebase direct inspection: `fin-guru/agents/strategy-advisor.md`, `teaching-specialist.md`, `quant-analyst.md` -- knowledge file reference pattern via `<i>Load COMPLETE file ...</i>`
- Codebase direct inspection: `fin-guru/data/margin-strategy.md`, `risk-framework.md` -- knowledge base file format conventions
- Phase 6 plans: `06-01-PLAN.md` (HedgePosition, RollSuggestion, HedgeSizeRequest model specs), `06-02-PLAN.md` (config_loader.py, YAML templates)
- Phase 7 plans: `07-01-PLAN.md` (TotalReturnCalculator pattern), `07-02-PLAN.md` (total_return_cli.py argparse pattern)
- [Python argparse docs](https://docs.python.org/3/library/argparse.html) -- add_subparsers with set_defaults(func=...) pattern verified

### Secondary (MEDIUM confidence)
- [Black-Scholes Wikipedia](https://en.wikipedia.org/wiki/Black%E2%80%93Scholes_model) -- European vs American distinction, intrinsic value floor requirement
- [PwC Black-Scholes Guide](https://viewpoint.pwc.com/dt/us/en/pwc/accounting_guides/stockbased_compensat/stockbased_compensat__3_US/chapter_8_estimating_US/84_the_blackscholes__US.html) -- American options adjustment practices
- [yfinance options chain tutorial](https://www.fintut.com/yahoo-finance-options-python/) -- Ticker.option_chain() usage, column names, NaN handling
- [Real Python argparse guide](https://realpython.com/command-line-interfaces-python-argparse/) -- subcommand best practices

### Tertiary (LOW confidence)
- None. All findings are from direct codebase inspection, official Python docs, and verified financial theory.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- All libraries already installed; zero new dependencies
- Architecture (rolling tracker): HIGH -- Subcommand pattern from Python stdlib; all integration points verified in codebase
- Architecture (hedge sizer): HIGH -- Standard flat argparse pattern matching 15 existing CLIs
- scan_chain() integration: HIGH -- All 12 stderr statements documented; redirect_stderr is stdlib
- Black-Scholes American adjustment: HIGH -- Intrinsic value floor is standard industry practice; implementation is a one-line max()
- Knowledge base files: HIGH -- Exact file format and agent reference pattern verified from 6 existing knowledge files and 13 agent definitions
- YAML state management: HIGH -- Pattern verified from existing config.py and Phase 6 template designs
- Budget validation: MEDIUM -- Live premium fetching via scan_chain is verified, but median premium estimation is a design choice (not industry standard)

**Research date:** 2026-02-02
**Valid until:** 2026-03-04 (30 days -- stable domain; yfinance API unchanged; financial formulas timeless)
