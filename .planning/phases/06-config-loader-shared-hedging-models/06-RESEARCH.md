# Phase 6: Config Loader & Shared Hedging Models - Research

**Researched:** 2026-02-02
**Domain:** Pydantic v2 config models, YAML config loading with CLI override, hedging domain models
**Confidence:** HIGH

## Summary

Phase 6 establishes the shared foundation that all four hedging CLI tools (total return, rolling tracker, hedge sizer, SQQQ comparison) depend on. The research confirms this is entirely a "standard patterns" phase -- every building block uses libraries and conventions already present in the codebase.

The codebase already has 8 model files in `src/models/`, a config loader in `src/config.py`, and 15 CLI tools with argparse. Pydantic 2.12.0 is installed. PyYAML 6.0.3 is installed. No new dependencies are required. The implementation follows the established 3-layer pattern (Models -> Calculators -> CLI) with zero exceptions.

The key design work is: (1) designing the hedging section of user-profile.yaml that Phase 3 onboarding will eventually generate, (2) building config_loader.py as a DRY bridge that 4 CLIs share, (3) creating hedging-specific Pydantic models with proper domain validation, and (4) scaffolding the fin-guru-private/hedging/ directory with YAML templates.

**Primary recommendation:** Follow existing codebase conventions exactly. Copy patterns from `src/models/options_inputs.py` (model structure), `src/config.py` (YAML loading with fallback), and `src/analysis/risk_metrics_cli.py` (argparse + config). No new libraries, no new patterns, no architectural departures.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pydantic | 2.12.0 | Model validation (BaseModel, Field, field_validator, model_validator, Literal) | Already installed, used by all 8+ model files |
| pyyaml | 6.0.3 | YAML parsing (yaml.safe_load) | Already installed, used by src/config.py |
| argparse | stdlib | CLI argument parsing | Used by all 15 existing CLI tools |
| pathlib | stdlib | Path handling | Used throughout codebase |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| datetime | stdlib | Date validation | Already used in risk_inputs.py, backtest_inputs.py |
| typing | stdlib | Literal, Optional types | Used in every model file |
| enum | stdlib | str+Enum pattern | Used in yaml_generation_inputs.py (RiskTolerance, etc.) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| yaml.safe_load | tomllib | YAML is the codebase standard; user-profile.yaml already exists |
| argparse | click/typer | argparse is used by all 15 CLIs; switching one tool would be inconsistent |
| Manual config merging | dynaconf/pydantic-settings | Adds dependency for a trivial merge; manual is 10-15 lines |

**Installation:**
```bash
# No new dependencies required. Everything is already in pyproject.toml:
# pydantic>=2.10.6, pyyaml>=6.0.3
```

## Architecture Patterns

### Recommended Project Structure
```
src/
  models/
    hedging_inputs.py      # HEDG-02: HedgePosition, RollSuggestion, HedgeSizeRequest
    total_return_inputs.py  # HEDG-03: TotalReturnInput, DividendRecord, TickerReturn
    __init__.py             # Updated: add new exports
  config/
    config_loader.py        # CFG-01/02/03: load_hedge_config() function
  analysis/
    (future Phase 7-9 CLIs will import from models/ and config/)

fin-guru-private/
  hedging/                  # HEDG-08: private data templates
    positions.yaml          # Current hedge positions
    roll-history.yaml       # Historical roll records
    budget-tracker.yaml     # Monthly budget tracking
```

**Key decision: `src/config/config_loader.py` vs `src/config_loader.py`**

Use `src/config/config_loader.py` (new `config/` subpackage). Rationale:
- The existing `src/config.py` is a class with classmethods (FinGuruConfig) focused on TUI paths/layers
- The hedging config loader is a different concern (YAML profile reading + CLI override merging)
- A `config/` subpackage keeps the DRY bridge separated from the TUI-focused config
- Phase 8+ may add more config utilities (position persistence, budget tracking)
- Include `__init__.py` that re-exports `load_hedge_config` for clean imports

### Pattern 1: Pydantic Model Conventions (from codebase)
**What:** Every model file follows the exact same structure
**When to use:** All new model files in this phase
**Example:**
```python
# Source: src/models/options_inputs.py, src/models/risk_inputs.py (codebase)
"""
[Tool Name] Pydantic Models for Finance Guru

ARCHITECTURE NOTE:
Layer 1 of 3-layer architecture:
    Layer 1: Pydantic Models (THIS FILE) - Data validation
    Layer 2: Calculator Classes - Business logic
    Layer 3: CLI Interface - Agent integration
"""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class HedgePosition(BaseModel):
    """
    WHAT: A single hedge position (option contract or inverse ETF)
    WHY: Type-safe representation for position tracking and roll suggestions
    VALIDATES:
        - Ticker is uppercase, 1-10 chars
        - Strike/premium are positive
        - Quantity is positive integer
    """

    ticker: str = Field(
        ...,
        description="Underlying ticker being hedged",
        min_length=1,
        max_length=10,
    )
    hedge_type: Literal["put", "inverse_etf"] = Field(
        ...,
        description="Type of hedge instrument"
    )
    # ... more fields with Field(..., description="...")

    @field_validator("ticker")
    @classmethod
    def ticker_must_be_uppercase(cls, v: str) -> str:
        if v != v.upper():
            raise ValueError(f"Ticker '{v}' must be uppercase")
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [{ ... }]
        }
    }

# Type exports
__all__ = ["HedgePosition", ...]
```

### Pattern 2: Config Loading with Fallback (from codebase)
**What:** Load YAML config with graceful fallback to defaults when file is missing
**When to use:** config_loader.py -- the central pattern for CFG-01/02/03
**Example:**
```python
# Source: src/config.py (codebase pattern, adapted for hedging)
from pathlib import Path
import yaml
from pydantic import BaseModel, Field

class HedgeConfig(BaseModel):
    """Validated hedging configuration from user-profile.yaml."""
    monthly_budget: float = Field(default=500.0, ge=0.0, description="Monthly hedge budget")
    roll_window_days: int = Field(default=7, ge=1, le=30, description="Days before expiry to trigger roll")
    underlying_weights: dict[str, float] = Field(
        default_factory=lambda: {"QQQ": 1.0},
        description="Hedge allocation weights by underlying"
    )
    max_otm_pct: float = Field(default=15.0, ge=1.0, le=50.0, description="Maximum OTM percentage")
    target_dte_min: int = Field(default=60, ge=7, description="Minimum days to expiry")
    target_dte_max: int = Field(default=90, ge=14, description="Maximum days to expiry")

def load_hedge_config(
    profile_path: Path | None = None,
    cli_overrides: dict | None = None,
) -> HedgeConfig:
    """
    Load hedging config: YAML file -> defaults -> CLI overrides.

    Priority: CLI flags > YAML file > Pydantic defaults

    Args:
        profile_path: Path to user-profile.yaml (None = use default location)
        cli_overrides: Dict of CLI flag overrides (None-values are skipped)

    Returns:
        Validated HedgeConfig
    """
    config_data: dict = {}

    # Step 1: Try to load from YAML
    if profile_path is None:
        profile_path = Path("fin-guru-private/data/user-profile.yaml")
    # ...fallback logic...

    # Step 2: Apply CLI overrides (non-None values only)
    if cli_overrides:
        config_data.update({k: v for k, v in cli_overrides.items() if v is not None})

    # Step 3: Validate through Pydantic (defaults fill gaps)
    return HedgeConfig(**config_data)
```

### Pattern 3: CLI Flags Override Config (new for this codebase)
**What:** argparse with `default=None` for config-overridable flags, then merge
**When to use:** Every hedging CLI built in Phases 7-9
**Example:**
```python
# Pattern: argparse default=None + merge with config
def parse_args():
    parser = argparse.ArgumentParser(...)
    # Config-overridable flags use default=None (not a value)
    parser.add_argument("--budget", type=float, default=None,
                        help="Monthly hedge budget (default: from config)")
    parser.add_argument("--roll-window", type=int, default=None,
                        help="Roll window in days (default: from config)")
    # Non-config flags use normal defaults
    parser.add_argument("--output", choices=["human", "json"], default="human")
    return parser.parse_args()

def main():
    args = parse_args()

    # Build override dict from CLI args (None values get filtered)
    cli_overrides = {
        "monthly_budget": args.budget,
        "roll_window_days": args.roll_window,
    }

    # Load config with overrides
    config = load_hedge_config(cli_overrides=cli_overrides)
    # config now has: CLI value (if provided) > YAML value > Pydantic default
```

### Pattern 4: Private Data YAML Templates (new)
**What:** Starter YAML files in fin-guru-private/hedging/ with commented examples
**When to use:** HEDG-08 -- template scaffolding
**Example:**
```yaml
# fin-guru-private/hedging/positions.yaml
# Finance Guru - Active Hedge Positions
# Updated automatically by rolling_tracker_cli.py
#
# Each entry represents one active hedge position.
# Fields: ticker, hedge_type, strike, expiry, quantity, premium_paid, entry_date

positions: []

# Example entry (uncomment to use):
# positions:
#   - ticker: QQQ
#     hedge_type: put
#     strike: 420.0
#     expiry: "2026-04-17"
#     quantity: 2
#     premium_paid: 8.50
#     entry_date: "2026-02-01"
```

### Anti-Patterns to Avoid
- **Duplicating YAML parsing across CLIs:** Each of the 4 hedging CLIs should import `load_hedge_config()` -- never call `yaml.safe_load` directly (CFG-01 DRY requirement)
- **Hardcoding fin-guru-private path:** Use `Path(__file__).parent.parent.parent / "fin-guru-private"` or a constant, not string literals
- **Mixing concerns in model files:** `hedging_inputs.py` (hedge position/roll models) and `total_return_inputs.py` (return calculation models) are separate files per HEDG-02 and HEDG-03 -- no circular imports
- **Config model with pandas types:** HedgeConfig should use only simple types (float, int, str, dict, list) -- no `arbitrary_types_allowed` needed since it reads from YAML, not DataFrames
- **Tight coupling to user-profile.yaml structure:** The config_loader should extract the `hedging:` section from user-profile.yaml and pass it to HedgeConfig -- if the YAML structure changes, only config_loader.py changes, not the models

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| YAML parsing | Custom parser | `yaml.safe_load()` | Already used in src/config.py; handles all YAML edge cases |
| Input validation | Manual if/else checks | Pydantic `Field(ge=, le=, gt=)` + `field_validator` | Codebase convention; 8 model files already do this |
| Default value merging | Custom dict merge | Pydantic model defaults + `dict.update()` | Pydantic handles missing fields with defaults; dict.update handles overrides |
| Path resolution | String concatenation | `pathlib.Path` operators | Already standard throughout codebase |
| Argument parsing | Manual sys.argv | `argparse.ArgumentParser` | Used by all 15 existing CLIs |
| Type narrowing | isinstance checks | `Literal["put", "inverse_etf"]` | Pydantic validates at construction time |

**Key insight:** The config-loader + override pattern is about 30-40 lines of straightforward Python. The temptation to use pydantic-settings or dynaconf is unnecessary -- those add dependency weight for a problem that Pydantic defaults + dict.update() solve cleanly.

## Common Pitfalls

### Pitfall 1: Circular Imports Between Model Files
**What goes wrong:** `hedging_inputs.py` imports from `total_return_inputs.py` or vice versa, creating import cycles
**Why it happens:** Models share concepts (e.g., ticker strings, date types) and developers think they should reference each other
**How to avoid:** HEDG-02 and HEDG-03 are explicitly marked "self-contained, no circular imports." Each model file imports only from `pydantic`, `datetime`, `typing`, `enum` -- never from sibling model files. If shared types are needed, extract to a `common_types.py` (but current requirements don't need this)
**Warning signs:** `ImportError` at module load time; models that need each other's types

### Pitfall 2: CLI Flags with Non-None Defaults Clobber Config
**What goes wrong:** `parser.add_argument("--budget", type=float, default=500.0)` always overrides the YAML value, even when user didn't pass `--budget`
**Why it happens:** argparse sets default values whether or not the flag was provided; you can't distinguish "user passed --budget 500" from "argparse used default 500"
**How to avoid:** Use `default=None` for ALL config-overridable CLI flags. The config loader's Pydantic defaults serve as the true fallback. Only non-None CLI values get merged. This is the standard pattern (documented in Architecture Pattern 3 above)
**Warning signs:** Config file values never take effect; user cannot customize via YAML

### Pitfall 3: Hardcoded Paths to user-profile.yaml
**What goes wrong:** Code uses `open("fin-guru/data/user-profile.yaml")` but the file could be at `fin-guru-private/data/user-profile.yaml` or elsewhere
**Why it happens:** The profile path depends on whether onboarding (Phase 3) has run and where it placed the file
**How to avoid:** config_loader.py searches a priority list of known locations:
1. `fin-guru-private/data/user-profile.yaml` (generated by onboarding)
2. `fin-guru/data/user-profile.yaml` (development/example)
3. Return empty config (CFG-03 graceful fallback)

Also accept explicit `--config PATH` CLI flag for override.
**Warning signs:** FileNotFoundError when running without Phase 3 complete

### Pitfall 4: Overly Ambitious HedgeConfig Schema
**What goes wrong:** Designing a config schema that tries to represent every possible hedging parameter upfront
**Why it happens:** Anticipating Phase 7-9 needs before those phases are planned
**How to avoid:** Start with the parameters listed in the requirements: budget, roll_window, underlying_weights. Phases 7-9 can extend HedgeConfig with additional fields (Pydantic models are easy to extend). The YAML `hedging:` section should only contain fields that HedgeConfig validates today
**Warning signs:** 20+ fields in the first version; fields with no CLI consumer

### Pitfall 5: Testing Models Without Testing the Override Chain
**What goes wrong:** Unit tests validate individual models but miss the config_loader merge logic
**Why it happens:** Testing models is straightforward (construct with known inputs); testing the full chain (YAML -> config -> CLI override -> validated output) requires fixtures
**How to avoid:** Write test fixtures: (1) a sample user-profile.yaml with hedging section, (2) test that YAML values are loaded, (3) test that CLI overrides replace YAML values, (4) test that missing YAML uses Pydantic defaults. This is the critical integration path
**Warning signs:** Models pass all tests but the actual CLI ignores the config file

## Code Examples

Verified patterns from the existing codebase:

### Pydantic Field Convention (from options_inputs.py)
```python
# Source: src/models/options_inputs.py line 53-75
ticker: str = Field(
    ...,
    description="Underlying asset ticker",
    min_length=1,
    max_length=10,
)
strike: float = Field(
    ...,
    gt=0.0,
    description="Strike price (must be positive)"
)
option_type: Literal["call", "put"] = Field(
    ...,
    description="Option type: call or put"
)
```

### Field Validator Pattern (from risk_inputs.py)
```python
# Source: src/models/risk_inputs.py line 69-88
@field_validator("prices")
@classmethod
def prices_must_be_positive(cls, v: list[float]) -> list[float]:
    """Ensure all prices are positive numbers."""
    if any(price <= 0 for price in v):
        raise ValueError(
            "All prices must be positive. Found zero or negative price."
        )
    return v
```

### Model Validator Pattern (from risk_inputs.py)
```python
# Source: src/models/risk_inputs.py line 110-127
@model_validator(mode="after")
def validate_price_date_alignment(self) -> "PriceDataInput":
    """Ensure equal number of prices and dates."""
    if len(self.prices) != len(self.dates):
        raise ValueError(
            f"Length mismatch: {len(self.prices)} prices but {len(self.dates)} dates."
        )
    return self
```

### YAML Loading with Fallback (from config.py)
```python
# Source: src/config.py line 35-80
@classmethod
def load_layers(cls) -> dict[str, list[str]]:
    """Load layer configuration with safe fallback to defaults."""
    default_layers = { ... }

    if not cls.LAYERS_FILE.exists():
        return default_layers

    try:
        with open(cls.LAYERS_FILE) as f:
            data = yaml.safe_load(f) or {}
    except Exception:
        return default_layers

    if not isinstance(data, dict):
        return default_layers
    # ... normalize and return
```

### Model Config with Examples (from options_inputs.py)
```python
# Source: src/models/options_inputs.py line 251-274
model_config = {
    "json_schema_extra": {
        "examples": [
            {
                "ticker": "TSLA",
                "option_type": "call",
                "calculation_date": "2025-10-13",
                "option_price": 25.50,
                # ... complete example
            }
        ]
    }
}
```

### Test Pattern with Classes (from test_options_chain.py)
```python
# Source: tests/python/test_options_chain.py line 27-59
class TestOptionContractDataModel:
    """Validate OptionContractData Pydantic model constraints."""

    def test_valid_contract_creation(self):
        """A fully populated contract with valid data should instantiate."""
        from src.models.options_inputs import OptionContractData

        contract = OptionContractData(
            contract_symbol="QQQ260417P00400000",
            expiration="2026-04-17",
            strike=400.0,
            # ... all fields
        )
        assert contract.contract_symbol == "QQQ260417P00400000"
        assert contract.strike == 400.0

    def test_strike_must_be_positive(self):
        """Strike price must be greater than zero."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            OptionContractData(strike=0.0, ...)
```

### __init__.py Export Pattern (from models/__init__.py)
```python
# Source: src/models/__init__.py
from src.models.options_inputs import (
    OptionInput,
    BlackScholesInput,
    GreeksOutput,
    # ... all exports
)

__all__ = [
    "OptionInput",
    "BlackScholesInput",
    "GreeksOutput",
    # ... all exports
]
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Pydantic v1 `@validator` | Pydantic v2 `@field_validator` | Pydantic 2.0 (2023-06) | Codebase already uses v2 style exclusively |
| `Optional[X]` | `X \| None` | Python 3.10+ | Codebase uses `X \| None` in most files |
| `class Config:` | `model_config = {}` | Pydantic 2.0 | Codebase uses `model_config` dict |
| `dict()` / `.dict()` | `model_dump()` / `model_dump_json()` | Pydantic 2.0 | CLIs use `model_dump_json(indent=2)` |

**Deprecated/outdated:**
- `@validator`: Replaced by `@field_validator` in Pydantic v2. Codebase does NOT use old style.
- `schema_extra`: Replaced by `json_schema_extra` in `model_config`. Codebase uses new style.
- `class Config:`: Replaced by `model_config = {}` dict. Codebase uses new style.

## YAML Template Design: user-profile.yaml Hedging Section

This section will be added to user-profile.yaml (either by Phase 3 onboarding or manually). The config_loader reads this section.

```yaml
# Hedging & Portfolio Protection Configuration
# Used by: total_return_cli, rolling_tracker_cli, hedge_sizer_cli, hedge_comparison_cli
hedging:
  # Monthly budget allocated to hedge positions
  monthly_budget: 800  # $800/month (matches layer_3_hedge in deployment_split)

  # Roll window: days before expiry to suggest rolling positions
  roll_window_days: 7

  # Underlying allocation weights for hedge positions
  # Keys are tickers to hedge, values are allocation weights (must sum to 1.0)
  underlying_weights:
    QQQ: 1.0  # 100% to QQQ (primary hedge underlying)

  # Target option parameters
  target_dte_min: 60   # Minimum days to expiry
  target_dte_max: 90   # Maximum days to expiry
  max_otm_pct: 15.0    # Maximum out-of-money percentage
  min_otm_pct: 10.0    # Minimum out-of-money percentage

  # SQQQ comparison parameters
  sqqq_allocation_pct: 0.06  # 6% of Layer 3 for SQQQ
```

**Design rationale:**
- `monthly_budget: 800` maps directly to the existing `deployment_split.layer_3_hedge: 800` in user-profile.yaml
- `underlying_weights` supports multi-underlying hedging (future: SPY + QQQ)
- Option parameters match the existing options_chain_cli.py defaults (10-20% OTM, 60-90 DTE)
- All values have sensible defaults in HedgeConfig Pydantic model, so missing YAML values don't crash

## Private Data Templates Design

### positions.yaml
```yaml
# Active hedge positions tracked by rolling_tracker_cli.py
# Do not edit manually -- use rolling_tracker_cli.py to manage

positions: []
# Example:
# positions:
#   - ticker: QQQ
#     hedge_type: put
#     strike: 420.00
#     expiry: "2026-04-17"
#     quantity: 2
#     premium_paid: 8.50
#     entry_date: "2026-02-01"
#     contract_symbol: "QQQ260417P00420000"
```

### roll-history.yaml
```yaml
# Historical roll records for performance tracking
# Appended by rolling_tracker_cli.py on each roll

rolls: []
# Example:
# rolls:
#   - date: "2026-02-01"
#     closed_position:
#       contract_symbol: "QQQ260321P00400000"
#       premium_paid: 6.80
#       premium_received: 2.10
#     opened_position:
#       contract_symbol: "QQQ260417P00420000"
#       premium_paid: 8.50
#     net_cost: 6.40
```

### budget-tracker.yaml
```yaml
# Monthly hedge budget tracking
# Updated by hedge_sizer_cli.py on each purchase

budget:
  monthly_limit: 800
  current_month: "2026-02"
  spent_this_month: 0.00
  remaining: 800.00

history: []
# Example:
# history:
#   - month: "2026-01"
#     budgeted: 800.00
#     spent: 765.00
#     positions_opened: 2
```

## Model Inventory

### hedging_inputs.py (HEDG-02)
| Model | Purpose | Key Fields |
|-------|---------|------------|
| `HedgePosition` | Active hedge position | ticker, hedge_type, strike, expiry, quantity, premium_paid, entry_date, contract_symbol |
| `RollSuggestion` | Recommendation to roll a position | current_position (HedgePosition), suggested_strike, suggested_expiry, estimated_cost, reason |
| `HedgeSizeRequest` | Input for sizing new hedges | portfolio_value, underlyings (list), budget, target_contracts |

### total_return_inputs.py (HEDG-03)
| Model | Purpose | Key Fields |
|-------|---------|------------|
| `TotalReturnInput` | Input for total return calculation | ticker, start_date, end_date, include_drip |
| `DividendRecord` | Single dividend payment | ex_date, payment_date, amount, shares_at_ex |
| `TickerReturn` | Return calculation output | ticker, price_return, dividend_return, total_return, dividends (list[DividendRecord]) |

### config/config_loader.py (CFG-01, CFG-02, CFG-03)
| Export | Purpose | Key Behavior |
|--------|---------|-------------|
| `HedgeConfig` | Validated config model | Monthly budget, roll window, weights, option params, SQQQ params |
| `load_hedge_config()` | Load + merge function | YAML -> defaults -> CLI overrides; graceful when file missing |

## Dependency Analysis

### What Phase 6 Depends On
- **Phase 3 (user-profile.yaml):** The hedging section schema must be defined here (Phase 6), but the actual YAML file is generated by Phase 3 onboarding. Phase 6 must work WITHOUT the onboarding having run (CFG-03). The hedging section design in Phase 6 becomes the specification that Phase 3 will implement.
- **Existing codebase:** src/models/ conventions, src/config.py patterns, argparse CLI conventions, test class patterns.

### What Depends on Phase 6
- **Phase 7 (Total Return):** Imports TotalReturnInput, DividendRecord, TickerReturn from total_return_inputs.py. Imports load_hedge_config from config_loader.py.
- **Phase 8 (Tracker & Sizer):** Imports HedgePosition, RollSuggestion, HedgeSizeRequest from hedging_inputs.py. Reads/writes to fin-guru-private/hedging/ YAML files.
- **Phase 9 (SQQQ Comparison):** Imports HedgeConfig for SQQQ parameters. Uses hedging_inputs.py models.

### No Dependency On
- options.py, options_chain_cli.py (those are Phase 8 integration points, not Phase 6)
- yfinance, market_data.py (Phase 6 is pure models and config, no market data fetching)
- streamlit, textual (UI layer is separate)

## Open Questions

1. **user-profile.yaml location after Phase 3**
   - What we know: Currently at `fin-guru/data/user-profile.yaml`. Phase 3 onboarding will generate it in `fin-guru-private/data/user-profile.yaml` (gitignored).
   - What's unclear: Should config_loader search both paths? The current `fin-guru/data/user-profile.yaml` is committed (contains real data that Phase 1 will scrub).
   - Recommendation: Search `fin-guru-private/` first, fall back to `fin-guru/data/`, then graceful empty. After Phase 1 scrubs the committed file, only the private path matters. This is a safe approach that handles the transition.

2. **HedgeConfig field set completeness**
   - What we know: Requirements list budget, roll_window, underlying_weights as explicit fields. Phase 7-9 may need additional config fields.
   - What's unclear: Exactly which fields Phase 9 (SQQQ comparison) will need in HedgeConfig.
   - Recommendation: Include the fields documented in the YAML template design above. Phase 9 can add fields to HedgeConfig when it is planned (Pydantic models are trivially extensible with new optional fields).

3. **HedgePosition relationship to OptionContractData**
   - What we know: `OptionContractData` exists in options_inputs.py (market data from live chain scan). `HedgePosition` represents a held position (from positions.yaml).
   - What's unclear: Whether HedgePosition should reference or inherit from OptionContractData.
   - Recommendation: Keep them separate. OptionContractData is a market data snapshot (bid/ask/greeks from live scan). HedgePosition is an owned position (entry price, quantity, P&L). Different lifecycle, different fields. Phase 8 bridges them when generating roll suggestions.

## Sources

### Primary (HIGH confidence)
- Codebase direct inspection: `src/models/options_inputs.py`, `src/models/risk_inputs.py`, `src/models/backtest_inputs.py`, `src/models/portfolio_inputs.py`, `src/models/yaml_generation_inputs.py` -- exact Pydantic v2 conventions
- Codebase direct inspection: `src/config.py` -- YAML loading with safe fallback pattern
- Codebase direct inspection: `src/analysis/risk_metrics_cli.py`, `src/analysis/options_chain_cli.py`, `src/strategies/optimizer_cli.py` -- argparse CLI conventions
- Codebase direct inspection: `tests/python/test_options_chain.py`, `tests/python/test_risk_metrics.py` -- test class patterns
- Codebase direct inspection: `pyproject.toml` -- Pydantic 2.10.6+, PyYAML 6.0.3+
- Runtime verification: `pydantic.__version__` = 2.12.0

### Secondary (MEDIUM confidence)
- `fin-guru/data/user-profile.yaml` -- current schema structure (will be modified by Phase 3)
- `.planning/ROADMAP.md` -- Phase 6 requirements, dependency chain, success criteria
- `.planning/phases/03-onboarding-wizard/03-01-PLAN.md` -- Phase 3 onboarding design (upstream dependency)

### Tertiary (LOW confidence)
- None. All findings are from direct codebase inspection and verified runtime state.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- All libraries already installed and used in codebase; zero new dependencies
- Architecture: HIGH -- Every pattern is directly observed in 8+ existing model files, 15+ CLI tools, and the existing config.py
- Pitfalls: HIGH -- Identified from direct codebase analysis of how existing tools handle config, validation, and overrides
- Domain models: MEDIUM -- Model field sets are inferred from requirements and Phase 8/9 success criteria; may need refinement during those phases

**Research date:** 2026-02-02
**Valid until:** 2026-03-04 (30 days -- stable domain, no moving targets)
