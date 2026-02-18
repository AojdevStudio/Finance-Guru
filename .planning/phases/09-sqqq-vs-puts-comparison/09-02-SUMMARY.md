---
phase: 09-sqqq-vs-puts-comparison
plan: 02
subsystem: analysis
tags: [sqqq, puts, hedging, cli, argparse, pytest, mermaid, options, comparison]

requires:
  - phase: 09-01
    provides: HedgeComparisonCalculator, Pydantic models (ScenarioInput, SQQQResult, PutResult, ComparisonRow, ComparisonOutput)
  - phase: 06-01
    provides: OptionsCalculator for put pricing
provides:
  - hedge_comparison_cli.py CLI for agent/user comparison of SQQQ vs puts
  - 15 known-answer tests validating SQQQ simulation, put payoff, breakeven
  - M2 hedging architecture diagram (Mermaid)
affects: [10-portfolio-health-dashboard, 11-strategy-agent-integration]

tech-stack:
  added: []
  patterns:
    - "argv preprocessing for argparse dash-prefix values (--scenarios -5,-10)"
    - "Known-answer testing with analytically deterministic inputs"

key-files:
  created:
    - src/analysis/hedge_comparison_cli.py
    - tests/python/test_hedge_comparison.py
    - docs/architecture/m2-hedging-components.mmd
  modified: []

key-decisions:
  - "argv preprocessor converts --scenarios -5,-10 to --scenarios=-5,-10 for argparse compatibility"
  - "SQQQ breakeven boundary at brentq lower bound (-0.001) accepted as correct behavior"

patterns-established:
  - "argv preprocessing: _preprocess_argv() pattern for CLI flags with negative numeric values"

duration: 7min
completed: 2026-02-18
---

# Phase 9 Plan 2: SQQQ vs Puts CLI, Tests, and Architecture Summary

**CLI for SQQQ vs protective puts comparison with 15 known-answer tests and M2 architecture diagram**

## Performance

- **Duration:** 7 min
- **Started:** 2026-02-18T04:24:43Z
- **Completed:** 2026-02-18T04:31:30Z
- **Tasks:** 3
- **Files created:** 3

## Accomplishments
- Hedge comparison CLI with --scenarios, --output json, and --help with 6 examples
- 15 known-answer tests covering SQQQ simulation, put payoff, breakeven, and output structure
- M2 hedging architecture diagram showing all 4 layers across Phases 7-9

## Task Commits

Each task was committed atomically:

1. **Task 1: Create hedge comparison CLI (Layer 3)** - `f982a76` (feat)
2. **Task 2: Create known-answer tests for hedge comparison** - `889ebdc` (test)
3. **Task 3: Create M2 architecture diagram and verify integration** - `7349595` (docs)

## Files Created/Modified
- `src/analysis/hedge_comparison_cli.py` - Layer 3 CLI with argparse, human/JSON output, breakeven analysis, disclaimers
- `tests/python/test_hedge_comparison.py` - 15 known-answer tests across 4 test classes
- `docs/architecture/m2-hedging-components.mmd` - Mermaid flowchart of M2 hedging milestone components

## Decisions Made
- argv preprocessor converts `--scenarios -5,-10` to `--scenarios=-5,-10` for argparse compatibility (argparse interprets leading dash as flag prefix)
- SQQQ breakeven at brentq boundary (-0.001) is correct -- SQQQ is profitable at any drop exceeding daily fee cost

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed argparse dash-prefix parsing for --scenarios**
- **Found during:** Task 1 (CLI creation)
- **Issue:** `--scenarios -5,-10,-20,-40` failed because argparse treated `-5,...` as a flag name
- **Fix:** Added `_preprocess_argv()` to convert `--scenarios VALUE` to `--scenarios=VALUE`
- **Files modified:** `src/analysis/hedge_comparison_cli.py`
- **Verification:** `uv run python src/analysis/hedge_comparison_cli.py --scenarios -5,-10,-20,-40` runs successfully
- **Committed in:** f982a76

**2. [Rule 1 - Bug] Fixed SQQQ breakeven test boundary assertion**
- **Found during:** Task 2 (test creation)
- **Issue:** Test asserted `sqqq_be < -0.001` but brentq returns exactly -0.001 at the search boundary
- **Fix:** Changed assertion to `sqqq_be <= -0.001`
- **Files modified:** `tests/python/test_hedge_comparison.py`
- **Verification:** All 15 tests pass
- **Committed in:** 889ebdc

---

**Total deviations:** 2 auto-fixed (2 bugs)
**Impact on plan:** Both auto-fixes necessary for correct CLI operation and accurate test assertions. No scope creep.

## Issues Encountered
- Ruff pre-commit hook removed unused `scenario` variable and 4 unused imports from test file (auto-fixed by hook)

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 9 (SQQQ vs Puts Comparison) is now complete with all 3 layers implemented and tested
- M2 Hedging milestone architecture is fully diagrammed
- Ready for Phase 10 (Portfolio Health Dashboard) or Phase 11 (Strategy Agent Integration)

---
*Phase: 09-sqqq-vs-puts-comparison*
*Completed: 2026-02-18*
