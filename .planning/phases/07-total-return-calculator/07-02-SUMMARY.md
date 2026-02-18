---
phase: 07-total-return-calculator
plan: 02
subsystem: analysis
tags: [total-return, CLI, DRIP, verdict, league-table, yfinance, finnhub, portfolio-csv]

# Dependency graph
requires:
  - phase: 07-total-return-calculator
    provides: TotalReturnCalculator, TotalReturnResult, DividendDataError in src/analysis/total_return.py
  - phase: 06-config-loader-shared-hedging-models
    provides: TotalReturnInput, DividendRecord, TickerReturn models in src/models/total_return_inputs.py
provides:
  - Total return CLI (src/analysis/total_return_cli.py) with argparse, multi-ticker comparison, verdict display, league table
  - Portfolio CSV auto-reader from notebooks/updates/Portfolio_Positions_*.csv
  - Finnhub real-time price integration with yfinance fallback
  - 70 total tests in tests/python/test_total_return.py (39 calculator + 31 CLI)
  - CLAUDE.md updated: Total Return in Financial Analysis Tools and Agent-Tool Matrix
affects:
  - 08-rolling-tracker-hedge-sizer (may reference total return CLI patterns)
  - 09-sqqq-vs-puts-comparison (imports total return models and may compare total returns)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Layer 3 CLI follows risk_metrics_cli.py and correlation_cli.py patterns"
    - "build_parser() extracted for testability (separate from main())"
    - "Portfolio CSV auto-detection via glob for dollar impact display"
    - "Verdict narrative on sign-flip (price < 0, total > 0) with 'Price misleading' indicator"
    - "League table ranks multi-ticker results by total return"

key-files:
  created:
    - src/analysis/total_return_cli.py
  modified:
    - tests/python/test_total_return.py
    - CLAUDE.md

key-decisions:
  - "build_parser() extracted as separate function for unit testing argparse without running main()"
  - "Portfolio CSV reader uses glob sorted order (latest file by filename) rather than file mtime"
  - "Verdict display triggers on sign-flip only (price < 0 AND total > 0), not any positive spread"
  - "League table only shown for multi-ticker comparison (2+ tickers), not single ticker"
  - "JSON output wraps results in {total_return_analysis: [...], disclaimer: ...} envelope"
  - "Finnhub mocking uses patch.dict('sys.modules') for lazy yfinance import inside fetch_ticker_data"

patterns-established:
  - "Sign-flip verdict pattern: detect when dividends flip negative price return to positive total return"
  - "League table pattern: sort results by total return descending, mark sign-flip tickers"
  - "Portfolio CSV integration: auto-read share counts for dollar impact display"
  - "build_parser() extraction pattern for CLI testability"

# Metrics
duration: 8min
completed: 2026-02-17
---

# Phase 07 Plan 02: Total Return CLI Summary

**Total return CLI with DRIP/non-DRIP side-by-side display, Sean-insight verdict narratives, league table ranking, portfolio CSV dollar amounts, and Finnhub real-time pricing -- 660 lines, 31 new tests**

## Performance

- **Duration:** 8 min
- **Started:** 2026-02-18T03:41:50Z
- **Completed:** 2026-02-18T03:50:11Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Complete Layer 3 CLI with 10 features: argparse, multi-ticker, DRIP side-by-side, verdict narrative, dollar amounts, period breakdown, league table, JSON output, Finnhub realtime, educational disclaimer
- 31 new CLI integration tests (10 arg parsing, 4 CSV reader, 15 verdict/formatting, 2 Finnhub) all passing
- CLAUDE.md updated with Total Return in Financial Analysis Tools table (9/11 complete) and Agent-Tool Matrix for 3 agents
- Full test suite: 794 passed, 86.38% coverage

## Task Commits

Each task was committed atomically:

1. **Task 1: Create total_return_cli.py with all presentation features** - `f3ee752` (feat)
2. **Task 2: Add CLI integration tests and update CLAUDE.md tool reference** - `35f56ef` (test)

## Files Created/Modified

- `src/analysis/total_return_cli.py` - Layer 3 CLI interface (660 lines) with argparse, DRIP comparison, verdict display, league table, portfolio CSV reader, Finnhub integration
- `tests/python/test_total_return.py` - Expanded from 39 to 70 tests with 4 new test classes for CLI testing
- `CLAUDE.md` - Total Return added to Financial Analysis Tools and Agent-Tool Matrix sections, tool count updated to 9/11

## Decisions Made

- Extracted `build_parser()` as separate function so tests can instantiate the parser without running `main()` -- enables thorough arg parsing tests without mocking sys.argv
- Portfolio CSV reader uses `sorted(glob.glob(...))` for deterministic selection -- filenames with date prefixes sort chronologically
- Verdict narrative only triggers on sign-flip (price negative AND total positive), not on any spread -- this is Sean's specific insight about misleading price returns
- League table omitted for single-ticker runs -- only meaningful for comparison
- JSON output uses envelope format `{total_return_analysis: [...], disclaimer: ...}` for consistency with structured API patterns
- Finnhub test uses `patch.dict("sys.modules")` to mock the lazy `import yfinance as yf` inside `fetch_ticker_data()` since yfinance is not installed in test environment

## Deviations from Plan

None -- plan executed exactly as written.

## Issues Encountered

- Pre-commit ruff-format reformatted the CLI file on first commit attempt -- re-staged the formatted version and committed successfully on second attempt
- yfinance not available in test environment -- Finnhub integration tests use sys.modules patching to provide a mock yfinance module
- Initial portfolio CSV test used month names (Jan, Feb) which have inconsistent sort order on different platforms -- switched to deterministic A/B naming

## User Setup Required

None -- no external service configuration required.

## Next Phase Readiness

- Phase 7 (Total Return Calculator) is complete: calculator (Plan 01) + CLI (Plan 02) both shipped
- Total Return tool fully operational: `uv run python src/analysis/total_return_cli.py SCHD JEPI --days 252`
- 70 tests covering calculator logic, data quality validation, CLI arg parsing, formatting, and Finnhub integration
- CLAUDE.md updated for agent discoverability
- Ready for Phase 8 (Rolling Tracker / Hedge Sizer)

---
*Phase: 07-total-return-calculator*
*Completed: 2026-02-17*
