---
phase: 05-agent-readiness-hardening
plan: 03
subsystem: infra
tags: [pre-commit, ruff, mypy, gitleaks, type-checking, linting, git-hooks]

# Dependency graph
requires:
  - phase: 05-01
    provides: Ruff linter configuration in pyproject.toml
provides:
  - Pre-commit framework with ruff, mypy, gitleaks, and hygiene hooks
  - mypy type-checking configuration with standard mode
  - Automated hook installation via setup.sh
affects: [05-04, 05-05]

# Tech tracking
tech-stack:
  added: [pre-commit 4.5.1, mirrors-mypy v1.19.1, gitleaks v8.24.2, pandas-stubs, types-requests, types-PyYAML]
  patterns: [pre-commit hook framework, mypy per-module overrides for gradual typing]

key-files:
  created: [.pre-commit-config.yaml]
  modified: [pyproject.toml, setup.sh, src/cli/onboarding_wizard.py]

key-decisions:
  - "mypy standard mode (not --strict) to avoid requiring full annotations on 23k-line codebase"
  - "Per-module relaxed overrides for 20+ existing financial modules with pre-existing type issues"
  - "Exclude tests/ and .claude/ from mypy pre-commit hook; tests have separate CI coverage"
  - "Template YAML files excluded from check-yaml (Handlebars syntax not valid YAML)"
  - "pre-commit install uses default migration mode, preserving bd hooks as .legacy"

patterns-established:
  - "Pre-commit framework: all code quality checks run automatically on git commit"
  - "Gradual mypy adoption: new code checked strictly, legacy modules have relaxed overrides"
  - "Hook exclusion patterns: gitignored dirs and template files excluded from hooks"

# Metrics
duration: 12min
completed: 2026-02-13
---

# Phase 5 Plan 3: Pre-commit Framework Summary

**Pre-commit framework with ruff, mypy, gitleaks, and hygiene hooks enforcing code quality on every commit**

## Performance

- **Duration:** 12 min
- **Started:** 2026-02-13T17:50:48Z
- **Completed:** 2026-02-13T18:03:00Z
- **Tasks:** 2
- **Files modified:** 39

## Accomplishments
- Pre-commit framework configured with 8 hooks across 4 repos (hygiene, ruff, mypy, gitleaks)
- mypy type-checking in standard mode with pydantic/requests/PyYAML/pandas stubs
- Per-module relaxed overrides for 20+ existing financial analysis modules
- setup.sh auto-installs pre-commit hooks with bd hook preservation via migration mode
- Trailing whitespace and EOF issues auto-fixed across 35 files

## Task Commits

Each task was committed atomically:

1. **Task 1: Create .pre-commit-config.yaml and add mypy config** - `e0cbd79` (feat)
2. **Task 2: Integrate pre-commit install into setup.sh** - `ae4ae35` (feat)

## Files Created/Modified
- `.pre-commit-config.yaml` - Pre-commit framework hook definitions (ruff, mypy, gitleaks, hygiene)
- `pyproject.toml` - Added [tool.mypy] section with standard mode config and per-module overrides
- `setup.sh` - Added install_pre_commit_hooks() function with uv tool install fallback
- `src/cli/onboarding_wizard.py` - Fixed callable type annotation (builtins.callable -> Callable)
- 35 files - Auto-fixed trailing whitespace and EOF issues via hygiene hooks

## Decisions Made
- **mypy standard mode**: Not using --strict to avoid requiring full annotations on 23k-line codebase. Standard mode catches obvious errors while allowing gradual adoption.
- **Per-module overrides**: 20+ financial analysis modules have relaxed mypy checks (disabled arg-type, assignment, no-any-return, operator, etc.) to allow pre-commit to pass. Tightening deferred to dedicated type-safety plan.
- **Exclude tests/ from mypy hook**: Tests have separate CI coverage and many use pytest fixtures that confuse mypy without full project context.
- **Exclude template YAML**: Handlebars template files (*.template.yaml) excluded from check-yaml since they contain template syntax not valid YAML.
- **Migration mode for pre-commit install**: Default mode backs up existing bd hooks as .legacy and chains them, preserving both pre-commit framework and bd hook functionality.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed callable type annotation in onboarding_wizard.py**
- **Found during:** Task 1 (mypy hook execution)
- **Issue:** `SECTION_ORDER` typed as `list[tuple[SectionName, callable]]` using builtin `callable` as a type, which mypy rejects
- **Fix:** Changed to `Callable[..., Any]` from `collections.abc` with proper imports
- **Files modified:** src/cli/onboarding_wizard.py
- **Verification:** mypy passes on onboarding_wizard.py
- **Committed in:** e0cbd79 (Task 1 commit)

**2. [Rule 3 - Blocking] Installed pre-commit via uv tool**
- **Found during:** Task 1 (pre-commit not available on system)
- **Issue:** pre-commit CLI not installed, needed to run hooks
- **Fix:** Ran `uv tool install pre-commit` to install globally
- **Verification:** `pre-commit --version` returns 4.5.1
- **Committed in:** Part of Task 1 setup

**3. [Rule 1 - Bug] Excluded fin-guru-private/ from ruff hooks**
- **Found during:** Task 1 (ruff hook failing on gitignored files)
- **Issue:** `--all-files` mode causes ruff to scan fin-guru-private/ which has lint errors in private strategy files
- **Fix:** Added `exclude: '^fin-guru-private/'` to ruff and ruff-format hooks
- **Verification:** ruff hook passes on --all-files
- **Committed in:** e0cbd79 (Task 1 commit)

---

**Total deviations:** 3 auto-fixed (2 bugs, 1 blocking)
**Impact on plan:** All auto-fixes necessary for hooks to pass. No scope creep.

## Issues Encountered
- 341 initial mypy errors across 53 files required iterative exclusions and per-module overrides to reach passing state. This was expected per plan guidance.
- Template YAML files with Handlebars syntax failed check-yaml; resolved with exclude pattern.

## User Setup Required
None - pre-commit hooks install automatically via setup.sh or `pre-commit install`.

## Next Phase Readiness
- Pre-commit framework operational, all hooks passing
- Ready for 05-04 (test coverage) and 05-05 (coverage thresholds)
- mypy overrides can be tightened incrementally in future plans

---
*Phase: 05-agent-readiness-hardening*
*Completed: 2026-02-13*
