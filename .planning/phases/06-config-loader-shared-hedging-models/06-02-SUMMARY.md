---
phase: 06-config-loader-shared-hedging-models
plan: 02
subsystem: config
tags: [pydantic, yaml, config-loader, hedging, validation]

# Dependency graph
requires:
  - phase: 05-agent-readiness-hardening
    provides: pre-commit hooks, ruff linting, mypy type checking
provides:
  - HedgeConfig Pydantic model with 8 validated fields
  - load_hedge_config() DRY bridge function (CLI > YAML > defaults)
  - src/config/ package with backward-compatible FinGuruConfig re-export
  - fin-guru-private/hedging/ directory with 3 YAML data templates
affects:
  - 06-03-config-loader-shared-hedging-models (may use HedgeConfig)
  - 07-total-return-calculator (imports load_hedge_config)
  - 08-rolling-tracker-hedge-sizer (reads/writes hedging YAML templates)
  - 09-sqqq-vs-puts-comparison (imports load_hedge_config)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Config priority chain: CLI flags > YAML file > Pydantic defaults"
    - "Module-to-package refactor with backward-compatible re-exports"
    - "Defensive YAML loading with graceful fallback to defaults"

key-files:
  created:
    - src/config/__init__.py
    - src/config/config_loader.py
    - src/config/fin_guru_config.py
    - fin-guru-private/hedging/positions.yaml
    - fin-guru-private/hedging/roll-history.yaml
    - fin-guru-private/hedging/budget-tracker.yaml
  modified: []

key-decisions:
  - "Converted src/config.py to src/config/ package to colocate config_loader.py; backward compat preserved via __init__.py re-export of FinGuruConfig"
  - "Accepted linter-imposed conditional import pattern in __init__.py for defensive coding"
  - "fin-guru-private/hedging/ templates are gitignored (private data); no git commit for Task 2 files"

patterns-established:
  - "Config bridge pattern: Pydantic model + load function that merges YAML + CLI overrides"
  - "Graceful YAML fallback: try/except around safe_load, return Pydantic defaults on failure"
  - "None-filtering for CLI overrides: {k: v for k, v in overrides.items() if v is not None}"

# Metrics
duration: 5min
completed: 2026-02-17
---

# Phase 06 Plan 02: Config Loader and Hedging Data Templates Summary

**HedgeConfig Pydantic model with load_hedge_config() DRY bridge (CLI > YAML > Pydantic defaults) plus fin-guru-private/hedging/ YAML templates for positions, rolls, and budget tracking**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-18T02:18:23Z
- **Completed:** 2026-02-18T02:23:07Z
- **Tasks:** 2
- **Files modified:** 6 (3 created in git, 3 created locally as gitignored templates)

## Accomplishments

- Created HedgeConfig Pydantic model with 8 validated fields (budget, roll window, weights, OTM range, DTE range, SQQQ allocation)
- Implemented load_hedge_config() with three-tier priority chain: CLI flags > YAML hedging section > Pydantic defaults
- Converted src/config.py to src/config/ package with full backward compatibility (672 tests still pass)
- Created three YAML data templates in fin-guru-private/hedging/ for positions, roll history, and budget tracking

## Task Commits

Each task was committed atomically:

1. **Task 1: Create config_loader.py with HedgeConfig and load_hedge_config()** - `8470092` (feat)
2. **Task 2: Create fin-guru-private/hedging/ YAML templates** - _not committed_ (gitignored private data)

**Plan metadata:** _(pending)_

## Files Created/Modified

- `src/config/__init__.py` - Package init re-exporting FinGuruConfig, HedgeConfig, load_hedge_config
- `src/config/config_loader.py` - HedgeConfig model + load_hedge_config() function (~200 lines)
- `src/config/fin_guru_config.py` - Moved from src/config.py with updated PROJECT_ROOT path
- `fin-guru-private/hedging/positions.yaml` - Active hedge positions template (gitignored)
- `fin-guru-private/hedging/roll-history.yaml` - Historical roll records template (gitignored)
- `fin-guru-private/hedging/budget-tracker.yaml` - Monthly budget tracking template (gitignored)

## Decisions Made

- **Module-to-package refactor:** Converted `src/config.py` to `src/config/` package to colocate `config_loader.py` alongside existing `FinGuruConfig`. Required updating `PROJECT_ROOT` path (one more `.parent` level). All existing imports (`from src.config import FinGuruConfig`) continue to work via `__init__.py` re-export.
- **Conditional import pattern:** Accepted linter-imposed try/except pattern in `__init__.py` for `HedgeConfig`/`load_hedge_config` imports, providing defensive coding if `config_loader.py` were ever missing.
- **Gitignored templates:** `fin-guru-private/hedging/` YAML templates are private data and correctly excluded from git. No commit needed for Task 2.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Converted src/config.py to src/config/ package**
- **Found during:** Task 1 (Create config_loader.py)
- **Issue:** Python cannot have both `src/config.py` (file) and `src/config/` (directory) -- namespace conflict
- **Fix:** Moved `src/config.py` to `src/config/fin_guru_config.py`, created `__init__.py` with backward-compatible re-exports, updated `PROJECT_ROOT` path depth
- **Files modified:** src/config.py (deleted), src/config/fin_guru_config.py (created), src/config/__init__.py (created)
- **Verification:** 672 existing tests pass, `from src.config import FinGuruConfig` works identically
- **Committed in:** 8470092 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Essential structural change for Python package compatibility. No scope creep. Full backward compatibility maintained.

## Issues Encountered

- Pre-commit hooks (ruff lint + ruff format) reformatted `config_loader.py` on first commit attempt. Re-staged and committed successfully on second attempt.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `load_hedge_config()` is ready for import by all four hedging CLIs (total_return, rolling_tracker, hedge_sizer, sqqq_comparison)
- `fin-guru-private/hedging/` directory and templates exist for Phase 8 (rolling_tracker, hedge_sizer) to read/write
- HedgeConfig validation ensures all downstream tools receive valid configuration
- Existing test suite fully passes with the config package refactor

---
*Phase: 06-config-loader-shared-hedging-models*
*Completed: 2026-02-17*
