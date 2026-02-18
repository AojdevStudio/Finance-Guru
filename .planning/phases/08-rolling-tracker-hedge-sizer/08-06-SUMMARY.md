---
phase: 08-rolling-tracker-hedge-sizer
plan: 06
subsystem: testing
tags: [tdd, known-answer-tests, cli-integration, rolling-tracker, hedge-sizer]
dependency_graph:
  requires: ["08-01", "08-02", "08-03", "08-04"]
  provides: ["comprehensive-test-coverage-for-phase-8-calculators"]
  affects: ["09-xx"]
tech_stack:
  added: []
  patterns: ["subprocess CLI integration testing", "mocked scan_chain for suggest-rolls"]
key_files:
  modified:
    - tests/python/test_rolling_tracker.py
    - tests/python/test_hedge_sizer.py
decisions: []
metrics:
  duration: "4 min"
  completed: "2026-02-18"
---

# Phase 8 Plan 06: Known-Answer Tests for RollingTracker and HedgeSizer Summary

**TL;DR:** Reviewed existing 79 tests across both calculators, added 6 missing tests (suggest-rolls with expiring position, CLI integration for both tools). Combined suite: 85 tests, all passing, zero lint errors.

## What Was Done

### Task 1: Review and Augment RollingTracker Tests

Reviewed existing 36 tests against plan requirements. Found strong coverage of all unit test categories (price_american_put, _dte_status, _rank_contract_score, position persistence, get_status, log_roll, get_history, suggest_rolls). Two gaps identified and filled:

1. **test_expiring_position_generates_suggestion** -- Tests that a put position with DTE <= 7 triggers scan_chain and returns a candidate suggestion. Uses mocked get_prices and scan_chain_quiet.
2. **CLI integration tests** -- test_cli_help (verifies --help exits 0 with "status" and "suggest-roll" in output) and test_cli_status_json (verifies status --output json returns valid JSON).

Final count: 38 tests (36 existing + 2 new).

### Task 2: Review and Augment HedgeSizer Tests

Reviewed existing 43 tests against plan requirements. All unit test categories covered comprehensively (calculate_contract_count, allocate_contracts, CSV parsing, resolve_portfolio_value, calculate, validate_budget). Three CLI integration tests missing and added:

1. **test_cli_help** -- Verifies --help exits 0 and shows --portfolio flag.
2. **test_cli_sizing_skip_budget** -- Verifies --portfolio 200000 --underlyings QQQ,SPY --skip-budget exits 0.
3. **test_cli_json_output** -- Verifies --output json returns valid JSON with total_contracts=4, allocations, and disclaimer keys.

Final count: 46 tests (43 existing + 3 new).

## Test Coverage Matrix

| Category | RollingTracker | HedgeSizer |
|----------|---------------|------------|
| Core formula tests | 5 (price_american_put) | 11 (calculate_contract_count) |
| DTE status / allocation | 7 (_dte_status) + 4 (_rank_contract_score) | 8 (allocate_contracts) |
| Persistence / CSV parsing | 6 (YAML) + 3 (roll history) | 5 (CSV) |
| Calculator integration | 4 (get_status) + 2 (log_roll) + 2 (get_history) | 7 (calculate) + 7 (validate_budget) |
| Suggest rolls / resolve | 4 (suggest_rolls) | 5 (resolve_portfolio_value) |
| CLI integration | 2 (help + JSON) | 3 (help + skip-budget + JSON) |
| **Total** | **38** | **46** |

## Deviations from Plan

None -- plan executed exactly as written. The existing test files already covered all unit test categories; only the CLI integration tests and the suggest-rolls-with-expiring test were genuinely missing.

## Verification Results

- `uv run pytest tests/python/test_rolling_tracker.py tests/python/test_hedge_sizer.py -v`: 85 passed
- `uv run pytest ... --co`: 85+ tests collected (> 25 threshold)
- `uv run ruff check tests/python/test_rolling_tracker.py tests/python/test_hedge_sizer.py`: All checks passed

## Next Phase Readiness

Phase 8 is now complete (all 6 plans executed). Both calculators have comprehensive test suites with known-answer tests, synthetic data, and CLI integration coverage. Ready to proceed to Phase 9.
