---
phase: 06-config-loader-shared-hedging-models
plan: 01
subsystem: models
tags: [pydantic, hedging, total-return, options, DRIP, validation]

# Dependency graph
requires:
  - phase: 05-agent-readiness-hardening
    provides: pre-commit hooks, ruff linting, mypy type checking, test coverage enforcement
provides:
  - HedgePosition, RollSuggestion, HedgeSizeRequest models in src/models/hedging_inputs.py
  - TotalReturnInput, DividendRecord, TickerReturn models in src/models/total_return_inputs.py
  - All six models re-exported from src.models
affects:
  - 06-config-loader-shared-hedging-models (plans 02-03 use these models)
  - 07-total-return-calculator (imports TotalReturnInput, DividendRecord, TickerReturn)
  - 08-rolling-tracker-hedge-sizer (imports HedgePosition, RollSuggestion, HedgeSizeRequest)
  - 09-sqqq-vs-puts-comparison (imports both hedging and total return models)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Hedging models follow same 3-layer architecture as options_inputs.py"
    - "Model validators: field_validator for single fields, model_validator(mode=after) for cross-field"
    - "Literal types for constrained string enums (hedge_type: put|inverse_etf)"
    - "Conditional required fields via model_validator (put requires strike+expiry)"
    - "Warning-only validation via warnings.warn in TickerReturn consistency check"

key-files:
  created:
    - src/models/hedging_inputs.py
    - src/models/total_return_inputs.py
  modified:
    - src/models/__init__.py

key-decisions:
  - "HedgePosition uses model_validator to conditionally require strike/expiry for puts"
  - "TickerReturn warns (not rejects) when total_return != price_return + dividend_return"
  - "DividendRecord uses float for shares_at_ex to support fractional DRIP shares"

patterns-established:
  - "Conditional field requirements via model_validator(mode=after) for variant models"
  - "Warning-only validators using warnings.warn for soft consistency checks"

# Metrics
duration: 8min
completed: 2026-02-17
---

# Phase 06 Plan 01: Shared Hedging Models Summary

**Six Pydantic v2 models for hedging positions and total return calculations with type-safe validation across put options, inverse ETFs, and DRIP dividend tracking**

## Performance

- **Duration:** 8 min
- **Started:** 2026-02-18T02:17:17Z
- **Completed:** 2026-02-18T02:25:43Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments

- Created HedgePosition model supporting both put options and inverse ETFs with conditional validation
- Created TotalReturnInput/DividendRecord/TickerReturn models with DRIP-aware share tracking
- All six models re-exported from src.models (55 total exports), zero circular imports
- All validators working: uppercase ticker, positive strike, date ordering, put-requires-strike-and-expiry

## Task Commits

Each task was committed atomically:

1. **Task 1: Create hedging_inputs.py** - `03209e3` (feat)
2. **Task 2: Create total_return_inputs.py** - `6a258df` (feat)
3. **Task 3: Update __init__.py exports** - `09c16e2` (feat)

## Files Created/Modified

- `src/models/hedging_inputs.py` - HedgePosition, RollSuggestion, HedgeSizeRequest with put/ETF validation
- `src/models/total_return_inputs.py` - TotalReturnInput, DividendRecord, TickerReturn with DRIP support
- `src/models/__init__.py` - Re-exports all six new models (55 total)

## Decisions Made

- HedgePosition uses `model_validator(mode="after")` to conditionally require strike and expiry only for put hedge_type, while inverse ETFs have these as None
- TickerReturn uses `warnings.warn` (not ValueError) when total_return deviates from price_return + dividend_return by >0.01, since floating point arithmetic can cause small diffs
- DividendRecord.shares_at_ex is `float` (not `int`) to support fractional shares from DRIP reinvestment

## Deviations from Plan

None -- plan executed exactly as written.

## Issues Encountered

- Pre-commit first run encountered stale staged files from a prior session (config package restructure). Resolved by unstaging pre-existing files and committing only task-specific changes.

## User Setup Required

None -- no external service configuration required.

## Next Phase Readiness

- All six shared models ready for Phase 06-02 (config loader) and 06-03 (HedgeConfig)
- Models are self-contained with no cross-imports between hedging_inputs and total_return_inputs
- Layer 2 calculators (Phases 07-09) can now import from `src.models` with full type safety

---
*Phase: 06-config-loader-shared-hedging-models*
*Completed: 2026-02-17*
