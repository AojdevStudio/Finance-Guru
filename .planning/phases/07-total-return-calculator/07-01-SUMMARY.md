---
phase: 07-total-return-calculator
plan: 01
subsystem: analysis
tags: [total-return, DRIP, dividends, TDD, pydantic, yfinance, data-quality]

# Dependency graph
requires:
  - phase: 06-config-loader-shared-hedging-models
    provides: TotalReturnInput, DividendRecord, TickerReturn models in src/models/total_return_inputs.py
provides:
  - TotalReturnCalculator class in src/analysis/total_return.py
  - TotalReturnResult dataclass with DRIP and annualized return fields
  - DividendDataError exception for data quality enforcement
  - load_dividend_schedules() for per-ticker dividend frequency metadata
  - fin-guru-private/dividend-schedules.yaml config (gitignored)
  - 39 known-answer tests in tests/python/test_total_return.py
affects:
  - 07-total-return-calculator (plan 02 CLI will import TotalReturnCalculator)
  - 08-rolling-tracker-hedge-sizer (may reference total return patterns)
  - 09-sqqq-vs-puts-comparison (imports total return models)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "TotalReturnCalculator follows same Layer 2 pattern as RiskCalculator"
    - "TotalReturnResult dataclass wraps TickerReturn with extra computed fields"
    - "YAML-based config in fin-guru-private/ for per-ticker dividend schedules"
    - "DividendDataError for force/refuse semantics on data quality"
    - "Calendar days (365) for annualization, not trading days (252)"

key-files:
  created:
    - src/analysis/total_return.py
    - tests/python/test_total_return.py
    - fin-guru-private/dividend-schedules.yaml
  modified: []

key-decisions:
  - "TotalReturnResult is a dataclass (not Pydantic) wrapping computed fields that TickerReturn lacks"
  - "ex_date_prices passed as dict[date, float] for DRIP reinvestment pricing"
  - "validate_dividend_data() uses statistics.median for split artifact detection (>3x median)"
  - "load_dividend_schedules() returns empty dict on missing file (graceful CI/first-clone fallback)"
  - "dividend-schedules.yaml lives in gitignored fin-guru-private/ (private per-user config)"

patterns-established:
  - "Force/refuse pattern: DividendDataError when quality issues found, force=True to override"
  - "YAML config for per-ticker metadata with lazy loading and missing-file fallback"
  - "TDD with RED (failing import) -> GREEN (all pass) -> commit per phase"

# Metrics
duration: 6min
completed: 2026-02-17
---

# Phase 07 Plan 01: Total Return Calculator Summary

**TotalReturnCalculator with price/dividend/total/DRIP return calculations, 25%-tolerance data quality validation, and split artifact detection using per-ticker dividend schedules from YAML config**

## Performance

- **Duration:** 6 min
- **Started:** 2026-02-18T03:32:30Z
- **Completed:** 2026-02-18T03:38:23Z
- **Tasks:** 2 (TDD: RED + GREEN)
- **Files modified:** 3

## Accomplishments

- TotalReturnCalculator with 6 methods: calculate_price_return(), calculate_dividend_return(), calculate_total_return(), calculate_drip_return(), calculate_annualized_return(), validate_dividend_data()
- 39 known-answer tests covering 8 test classes, all passing with synthetic data
- Data quality validation with 25% tolerance gap detection, >3x median split artifact detection, and known-payer-zero-dividends warning
- Sean insight scenario verified: price return -3.95% + dividend return 8.2% = total return +4.25% (distributions flip the story)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create dividend schedules YAML and write failing tests** - `c3ecb74` (test)
2. **Task 2: Implement TotalReturnCalculator to pass all tests** - `48ed930` (feat)

_Note: TDD task 1 committed with --no-verify (RED phase: module intentionally missing)_

## Files Created/Modified

- `src/analysis/total_return.py` - TotalReturnCalculator class (Layer 2) with DRIP, validation, annualization
- `tests/python/test_total_return.py` - 39 known-answer tests across 8 test classes
- `fin-guru-private/dividend-schedules.yaml` - Per-ticker dividend frequency metadata (gitignored)

## Decisions Made

- TotalReturnResult is a Python dataclass (not Pydantic BaseModel) because it wraps computed output fields that don't need Pydantic validation -- it's an internal calculator result, not an API boundary
- ex_date_prices passed as a separate dict rather than embedded in DividendRecord, because the close price for DRIP reinvestment is a fetching concern (Layer 3) not a model concern (Layer 1)
- statistics.median used instead of manual sorted()[len//2] for split artifact detection -- standard library is more correct for even-length lists
- Lazy-loading of dividend schedules (first access, not init) to avoid file I/O on calculator construction

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed mypy no-any-return on annualized calculation**
- **Found during:** Task 2 (pre-commit hook)
- **Issue:** `(1.0 + total_return) ** (365.0 / calendar_days) - 1.0` inferred as `Any` by mypy
- **Fix:** Wrapped in `float()` cast
- **Files modified:** src/analysis/total_return.py
- **Verification:** mypy passes clean
- **Committed in:** 48ed930 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Minor type annotation fix. No scope creep.

## Issues Encountered

- Pre-commit hooks caught import sorting (ruff I001) on the test file -- auto-fixed by ruff and re-staged before final commit
- fin-guru-private/ is gitignored, so dividend-schedules.yaml is not tracked in git -- this is intentional (private per-user config)

## User Setup Required

None -- no external service configuration required.

## Next Phase Readiness

- TotalReturnCalculator is ready for Plan 02 CLI wrapper (total_return_cli.py)
- CLI needs to implement data fetching (yfinance Ticker().history()), pass prices/dividends/ex_date_prices to calculator
- Multi-ticker comparison table formatting needed in CLI
- All 39 tests passing, full suite of 763 tests green

---
*Phase: 07-total-return-calculator*
*Completed: 2026-02-17*
