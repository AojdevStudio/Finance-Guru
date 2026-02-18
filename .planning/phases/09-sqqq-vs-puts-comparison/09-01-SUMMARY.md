---
phase: 09-sqqq-vs-puts-comparison
plan: 01
subsystem: analysis
tags: [sqqq, puts, hedge-comparison, black-scholes, leveraged-etf, volatility-drag, iv-expansion, pydantic]

# Dependency graph
requires:
  - phase: 06-config-loader-shared-hedging-models
    provides: OptionsCalculator, BlackScholesInput, GreeksOutput for put pricing
provides:
  - HedgeComparisonCalculator with SQQQ simulation, put pricing, and breakeven analysis
  - Pydantic models for hedge comparison I/O (ScenarioInput, SQQQResult, PutResult, ComparisonRow, ComparisonOutput)
affects: [09-02-hedge-comparison-cli, phase-10-visualization]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Day-by-day leveraged ETF simulation with volatility drag"
    - "VIX-SPX regression table for IV expansion modeling"
    - "Three representative scenario paths (gradual, crash-then-flat, volatile)"
    - "brentq root-finding for SQQQ breakeven analysis"

key-files:
  created:
    - src/models/hedge_comparison_inputs.py
    - src/analysis/hedge_comparison.py
  modified:
    - src/models/__init__.py

key-decisions:
  - "Winner comparison uses absolute dollar PnL (SQQQ position value change vs put PnL) rather than percentage returns for apples-to-apples comparison"
  - "SQQQ breakeven uses gradual decline path (conservative) for deterministic root-finding"
  - "Volatile path uses seeded RNG (seed=42) with multiplicative adjustment to match target cumulative drop"

patterns-established:
  - "VIX-SPX regression table: piecewise linear interpolation with extrapolation beyond table boundaries"
  - "Three-path scenario generation: gradual, crash-then-flat, volatile with averaging for path-dependent instruments"

# Metrics
duration: 7min
completed: 2026-02-18
---

# Phase 9 Plan 01: Hedge Comparison Models and Calculator Summary

**Day-by-day SQQQ simulation with volatility drag, IV-expanded put pricing via VIX-SPX regression, and brentq breakeven analysis**

## Performance

- **Duration:** 7 min
- **Started:** 2026-02-18T04:14:31Z
- **Completed:** 2026-02-18T04:21:38Z
- **Tasks:** 2/2
- **Files modified:** 3

## Accomplishments
- 5 Pydantic models (ScenarioInput, SQQQResult, PutResult, ComparisonRow, ComparisonOutput) with validators and zero-floor enforcement
- HedgeComparisonCalculator with day-by-day SQQQ compounding that correctly diverges from naive -3x by 28.96% at -20% market drop
- IV expansion from 20% to 61% at -20% drop via VIX-SPX regression table calibrated from 2008/2018/2020/2025 crash data
- Breakeven analysis: SQQQ breaks even at -0.10% drop, puts at -11.04% drop

## Task Commits

Each task was committed atomically:

1. **Task 1: Create hedge comparison Pydantic models** - `dc557d7` (feat)
2. **Task 2: Create HedgeComparisonCalculator (Layer 2)** - `72974ae` (feat)

## Files Created/Modified
- `src/models/hedge_comparison_inputs.py` - 5 Pydantic models for hedge comparison I/O with validators
- `src/analysis/hedge_comparison.py` - HedgeComparisonCalculator with SQQQ simulation, put pricing, breakevens
- `src/models/__init__.py` - Added 5 model exports for hedge comparison

## Decisions Made
- Winner comparison uses absolute dollar PnL (SQQQ position value change vs put PnL) rather than percentage returns, since the two strategies have different capital bases ($10K SQQQ allocation vs $5 put premium)
- SQQQ breakeven uses the gradual decline path (not averaged paths) for deterministic root-finding with brentq
- Volatile path uses seeded RNG (seed=42) with multiplicative adjustment across all days to match target cumulative drop exactly
- mypy required explicit `Literal` type annotation on `winner` variable to satisfy strict type checking

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added Literal import for mypy compliance**
- **Found during:** Task 2 (HedgeComparisonCalculator commit)
- **Issue:** mypy error: `winner` variable inferred as `str` instead of `Literal["sqqq", "put", "neither"]`
- **Fix:** Added `from typing import Literal` import and explicit type annotation on the `winner` variable
- **Files modified:** src/analysis/hedge_comparison.py
- **Verification:** mypy passes, pre-commit hooks pass
- **Committed in:** `72974ae` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Type annotation fix required for mypy pre-commit hook. No scope creep.

## Issues Encountered
- ruff format reformatted hedge_comparison_inputs.py during first commit attempt (line length adjustments). Re-staged and committed successfully on second attempt.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Calculator is fully functional and ready for CLI wrapper (Plan 02)
- All models exported from src.models for CLI and agent consumption
- OptionsCalculator integration verified for put pricing
- 873 existing tests still pass with 83.6% coverage

---
*Phase: 09-sqqq-vs-puts-comparison*
*Completed: 2026-02-18*
