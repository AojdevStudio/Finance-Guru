---
phase: 08-rolling-tracker-hedge-sizer
plan: 02
subsystem: analysis
tags: [hedging, options, contract-sizing, portfolio-protection, budget-validation]

# Dependency graph
requires:
  - phase: 06-config-loader-shared-hedging-models
    provides: HedgeConfig model and config_loader, HedgeSizeRequest model
provides:
  - HedgeSizer calculator class with sizing, allocation, and budget validation
  - calculate_contract_count helper (floor formula HS-01)
  - allocate_contracts helper (weight-based with remainder)
  - read_portfolio_value_from_csv (Fidelity CSV parser)
  - Portfolio value cascade (CLI -> CSV -> error)
affects: [08-rolling-tracker-hedge-sizer plan 03 (CLI), 08-rolling-tracker-hedge-sizer plan 06 (integration)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Layer 2 calculator with module-level helpers + class methods"
    - "Portfolio value cascade: CLI flag -> Fidelity CSV -> ValueError"
    - "redirect_stderr for suppressing scan_chain output"

key-files:
  created:
    - src/analysis/hedge_sizer.py
    - tests/python/test_hedge_sizer.py
  modified: []

key-decisions:
  - "Portfolio value cascade: CLI flag > Fidelity CSV > ValueError (no config fallback)"
  - "Over-budget warning shows full recommendation, does NOT scale down contracts"
  - "allocate_contracts remainder goes to highest-weight underlying first"
  - "validate_budget uses median premium from scan_chain results for cost estimation"

patterns-established:
  - "Fidelity CSV parsing: glob for latest by mtime, case-insensitive row match"
  - "Budget validation: warn but show full recommendation when over budget"

# Metrics
duration: 6min
completed: 2026-02-18
---

# Phase 8 Plan 02: HedgeSizer Calculator Summary

**HedgeSizer calculator with floor(portfolio/50k) sizing, weight-based allocation with remainder distribution, Fidelity CSV portfolio reader, and budget validation against live premiums**

## Performance

- **Duration:** 6 min
- **Started:** 2026-02-18T03:57:35Z
- **Completed:** 2026-02-18T04:03:50Z
- **Tasks:** 1
- **Files created:** 2

## Accomplishments
- Implemented calculate_contract_count with floor(portfolio_value / ratio) formula (HS-01)
- Implemented allocate_contracts with weight-based distribution and remainder to highest-weight underlying
- Built Fidelity CSV parser (read_portfolio_value_from_csv) for portfolio value cascade
- HedgeSizer class with resolve_portfolio_value, calculate, and validate_budget methods
- 43 unit tests covering all methods with synthetic data (96.2% file coverage)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create HedgeSizer calculator with sizing, allocation, and budget validation** - `1625c99` (feat)

**Plan metadata:** (pending)

## Files Created/Modified
- `src/analysis/hedge_sizer.py` - Layer 2 calculator with HedgeSizer class, contract sizing, allocation, CSV reader, budget validation
- `tests/python/test_hedge_sizer.py` - 43 unit tests covering all public functions and class methods

## Decisions Made
- Portfolio value cascade has two sources (CLI flag, Fidelity CSV) -- config fallback removed to keep cascade simple and explicit
- Over-budget warning shows full recommendation without scaling down -- user decides whether to act on the warning
- validate_budget uses median premium (not mean) from scan_chain results for more robust cost estimation
- allocate_contracts remainder distribution uses descending weight order (highest-weight underlying gets remainder first)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added unit tests for coverage threshold**
- **Found during:** Task 1 (pre-commit hook)
- **Issue:** Adding hedge_sizer.py (120 lines, 0% coverage) dropped total coverage from 80.6% to 78.6%, below the 80% fail-under threshold
- **Fix:** Created tests/python/test_hedge_sizer.py with 43 comprehensive unit tests covering all public functions and class methods
- **Files created:** tests/python/test_hedge_sizer.py
- **Verification:** Full test suite passes (837 tests, 81.8% coverage)
- **Committed in:** 1625c99 (part of task commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Test addition was necessary to pass coverage gate. Improved quality assurance for the module.

## Issues Encountered
- Pre-commit ruff-format reformatted hedge_sizer.py on first commit attempt (normal auto-formatting, not a problem)
- Mock path for scan_chain needed to target source module (options_chain_cli) rather than hedge_sizer since import is local to validate_budget method

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- HedgeSizer calculator is complete and ready for CLI wrapper (Plan 03)
- All public functions tested with synthetic data
- Portfolio value cascade successfully reads from Fidelity CSV

---
*Phase: 08-rolling-tracker-hedge-sizer*
*Completed: 2026-02-18*
