---
phase: 08-rolling-tracker-hedge-sizer
plan: 04
subsystem: analysis
tags: [hedge-sizer, cli, argparse, options, portfolio-protection]

# Dependency graph
requires:
  - phase: 08-02
    provides: HedgeSizer calculator with sizing, allocation, and budget validation
  - phase: 06-02
    provides: load_hedge_config and HedgeConfig Pydantic model
provides:
  - Hedge Sizer CLI with flat argparse pattern for agent integration
  - --portfolio, --underlyings, --ratio, --budget, --output, --skip-budget flags
  - Portfolio value cascade (CLI flag > Fidelity CSV > ValueError)
affects: [08-06, 09-sqqq-vs-puts-comparison]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Standard flat argparse CLI with build_parser() extraction"
    - "Human + JSON dual output format with format_*_output() helpers"
    - "Portfolio value cascade with source tracking"

key-files:
  created:
    - src/analysis/hedge_sizer_cli.py
  modified: []

key-decisions:
  - "Equal-weight fallback when underlyings not in config weights (consistent with HedgeSizer.calculate)"
  - "Budget warning section only shows pricing notes when unavailable data exists (avoid redundant warnings)"
  - "stderr used for progress messages, stdout for formatted output (agent-parseable)"

patterns-established:
  - "Hedge CLI pattern: config loading with cli_overrides dict, sizer instantiation, cascade resolution"

# Metrics
duration: 2min
completed: 2026-02-18
---

# Phase 8 Plan 04: Hedge Sizer CLI Summary

**Flat argparse CLI for hedge contract sizing with allocation, coverage, budget validation, and dual output formats**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-18T04:11:40Z
- **Completed:** 2026-02-18T04:13:48Z
- **Tasks:** 1
- **Files created:** 1

## Accomplishments

- Standard flat argparse CLI matching all existing 15+ CLIs in codebase
- Portfolio value cascade functional: CLI flag > Fidelity CSV > clear error message
- Human output with allocation table, coverage ratio, and budget analysis
- JSON output with structured envelope format for programmatic parsing
- All pre-commit hooks pass (ruff, mypy, pytest, secret detection)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create hedge_sizer_cli.py with flat argparse and formatted output** - `c9f4ba9` (feat)

## Files Created/Modified

- `src/analysis/hedge_sizer_cli.py` - Layer 3 CLI with argparse, human/JSON output, portfolio cascade, budget validation

## Decisions Made

- Equal-weight fallback when requested underlyings are not all in config weights (consistent with HedgeSizer.calculate behavior)
- Budget warning display separates the main over-budget warning from the "estimate unavailable" notes to avoid redundancy
- All progress/status messages go to stderr; only the formatted result goes to stdout (standard for agent-parseable CLIs)

## Deviations from Plan

None -- plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None -- no external service configuration required.

## Next Phase Readiness

- Hedge Sizer CLI complete, ready for integration with agent workflows
- Plans 03 and 06 remain in Phase 8 (rolling tracker CLI and tests)
- All hedging Layer 2 calculators and Layer 3 CLIs now available

---
*Phase: 08-rolling-tracker-hedge-sizer*
*Completed: 2026-02-18*
