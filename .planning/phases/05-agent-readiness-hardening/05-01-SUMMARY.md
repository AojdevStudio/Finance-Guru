---
phase: 05-agent-readiness-hardening
plan: 01
subsystem: tooling
tags: [ruff, linter, formatter, code-quality, python]

# Dependency graph
requires:
  - phase: 04-onboarding-polish-hook-refactoring
    provides: stable Python codebase to lint
provides:
  - ruff configuration as sole linter/formatter
  - zero-error baseline for pre-commit hooks
  - black removed from dependencies
affects: [05-03-pre-commit-hooks, 05-04-test-coverage]

# Tech tracking
tech-stack:
  added: [ruff 0.15.1]
  patterns: [ruff lint + format replaces black, Google-style docstrings, noqa annotations for complex CLI functions]

key-files:
  created: []
  modified:
    - pyproject.toml
    - 92 Python files across src/, tests/, .agents/, .claude/

key-decisions:
  - "Ignored D205/D100/D107/B028/E402 globally -- low-value rules for this codebase"
  - "Per-file N803/N806 ignores for src/analysis/, src/strategies/, src/utils/ -- financial code uses conventional uppercase vars (S, K, T, r)"
  - "C901 handled with noqa annotations on 12 complex CLI format functions -- refactoring deferred"
  - "B017 test fix: narrowed pytest.raises(Exception) to pytest.raises(ValueError) for PydanticSerializationError"

patterns-established:
  - "ruff as sole linter+formatter: `uv run ruff check .` and `uv run ruff format .`"
  - "Google-style docstrings enforced via pydocstyle convention"
  - "noqa: C901 for complex CLI display functions (acceptable complexity)"

# Metrics
duration: 17min
completed: 2026-02-13
---

# Phase 5 Plan 1: Ruff Lint Setup Summary

**Ruff configured as sole Python linter/formatter with zero-error baseline across 92 files, replacing black**

## Performance

- **Duration:** 17 min
- **Started:** 2026-02-13T17:29:33Z
- **Completed:** 2026-02-13T17:47:07Z
- **Tasks:** 2
- **Files modified:** 92

## Accomplishments
- Complete ruff configuration in pyproject.toml (lint rules E/F/I/UP/W/B/SIM/C90/N/D + format)
- Removed black from dev dependencies, replaced with ruff 0.15.1
- One-time lint cleanup: 1074 initial errors resolved to zero
- All 438 existing tests pass with zero regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: Add ruff config and remove black** - `cca5ce9` (chore)
2. **Task 2: Ruff lint and format cleanup** - `39bc0ed` (style)

## Files Created/Modified
- `pyproject.toml` - Complete ruff config (lint + format), black removed from dev deps
- `src/**/*.py` (65 files) - Import sorting, format cleanup, bug fixes (bare excepts, raise from, zip strict)
- `tests/**/*.py` (16 files) - Format cleanup, test narrowing (Exception -> ValueError)
- `.agents/**/*.py` (2 files) - Nested if collapsing, C901 noqa
- `.claude/**/*.py` (2 files) - Bare except -> specific exception types
- `main.py` - Added missing docstring

## Decisions Made
- **Ignored rules globally:** E501 (line length, handled by formatter), E402 (module-level imports not at top -- common pattern in this codebase), D107 (missing __init__ docstring), D205 (blank line in docstring), D100 (module docstring), B028 (stacklevel in warnings -- noise for this codebase)
- **Per-file ignores for naming:** N803/N806 suppressed in analysis/strategies/utils dirs because financial code uses conventional single-letter uppercase variables (S, K, T, r, N, X)
- **C901 complexity:** Added noqa annotations to 12 CLI format functions rather than refactoring -- these are display-only functions with acceptable complexity
- **B017 test narrowing:** Changed `pytest.raises(Exception)` to `pytest.raises(ValueError)` to match actual PydanticSerializationError hierarchy

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Narrowed B017 blind exception assertion in test**
- **Found during:** Task 2 (lint cleanup)
- **Issue:** `pytest.raises(Exception)` is too broad -- B017 flags it as it catches all exceptions including SystemExit/KeyboardInterrupt
- **Fix:** Changed to `pytest.raises(ValueError)` matching PydanticSerializationError's actual MRO
- **Files modified:** tests/python/test_onboarding_wizard.py
- **Verification:** Test passes, correctly catches the specific error type
- **Committed in:** 39bc0ed

**2. [Rule 2 - Missing Critical] Added `strict=` to zip() calls**
- **Found during:** Task 2 (lint cleanup)
- **Issue:** 5 zip() calls without strict parameter -- could silently truncate mismatched iterables
- **Fix:** Added `strict=True` where lengths should match, `strict=False` for diagnostic zip
- **Files modified:** src/models/correlation_inputs.py, src/models/momentum_inputs.py, src/models/portfolio_inputs.py, src/strategies/optimizer.py, src/utils/data_validator.py
- **Verification:** All tests pass
- **Committed in:** 39bc0ed

**3. [Rule 2 - Missing Critical] Added exception chaining with `raise from`**
- **Found during:** Task 2 (lint cleanup)
- **Issue:** 4 except clauses re-raising without chaining -- loses original traceback context
- **Fix:** Added `from e` or `from None` to preserve exception chain
- **Files modified:** src/ui/services/portfolio_loader.py, src/utils/onboarding_validators.py
- **Verification:** All tests pass, traceback context preserved
- **Committed in:** 39bc0ed

---

**Total deviations:** 3 auto-fixed (1 bug, 2 missing critical)
**Impact on plan:** All auto-fixes improve code correctness. No scope creep.

## Issues Encountered
- Initial ruff check found 1074 errors; 761 auto-fixed, 313 required manual intervention or config tuning
- Pragmatic config tuning needed to suppress low-value rules (D205, E402, B028) rather than rewriting hundreds of docstrings

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Ruff baseline established, ready for pre-commit hook integration (Plan 03)
- All lint and format checks pass, providing clean foundation for test coverage thresholds (Plan 04)
- No blockers

---
*Phase: 05-agent-readiness-hardening*
*Completed: 2026-02-13*
