---
phase: 03-onboarding-wizard
plan: 02
subsystem: cli
tags: [questionary, pydantic, yaml-generation, onboarding, config-files, bun-hooks]

# Dependency graph
requires:
  - phase: 03-01
    provides: "OnboardingState model, 8 section runners, domain validators, ask_with_retry"
  - phase: 02-setup-automation
    provides: "YAMLGenerator, write_config_files, Pydantic models (yaml_generation_inputs)"
provides:
  - "Wizard CLI at src/cli/onboarding_wizard.py callable via uv run python src/cli/onboarding_wizard.py"
  - "State-to-model conversion with string-to-enum mapping (convert_state_to_user_data)"
  - "Config file generation to correct paths: private to fin-guru-private/, project root for CLAUDE.md/.env/.claude/mcp.json"
  - "Hook path fix: agents now read profile from wizard output location (ONBD-17 runtime chain complete)"
  - "63 new tests covering validators, sections, and wizard integration"
affects: [04-save-resume, 05-agent-readiness, 11-hedging-tools]

# Tech tracking
tech-stack:
  added: [pytest-mock]
  patterns: [string-to-enum-conversion, backup-before-overwrite, mocked-questionary-testing]

key-files:
  created:
    - src/cli/onboarding_wizard.py
    - tests/python/test_onboarding_validators.py
    - tests/python/test_onboarding_sections.py
    - tests/python/test_onboarding_wizard.py
  modified:
    - .claude/hooks/load-fin-core-config.ts
    - pyproject.toml
    - uv.lock

key-decisions:
  - "String-to-enum via _safe_enum helper with case-insensitive fallback and UserWarning on unknown values"
  - "Private configs written by write_config_files(base_dir='fin-guru-private'), project-root files by explicit Path.write_text()"
  - "Agent files already genericized (no hardcoded names found); Task 4 confirmed no changes needed"
  - "pytest-mock added as dev dependency for questionary mocking pattern"

patterns-established:
  - "_safe_enum(enum_cls, raw_value, default): safe string-to-enum conversion with fallback"
  - "_backup_file(path): backup existing files before overwriting (.backup extension)"
  - "Mock questionary at src.utils.onboarding_sections.questionary.* (where imported, not global)"

# Metrics
duration: 10min
completed: 2026-02-06
---

# Phase 3 Plan 02: Wizard CLI with Config Generation and Hook Fix Summary

**8-section wizard CLI orchestrating onboarding flow, generating user-profile.yaml/CLAUDE.md/.env/mcp.json to correct output paths, with hook path fix completing the agent runtime chain (ONBD-17)**

## Performance

- **Duration:** 10 min
- **Started:** 2026-02-06T01:03:52Z
- **Completed:** 2026-02-06T01:13:35Z
- **Tasks:** 4
- **Files modified:** 7

## Accomplishments

- Wizard CLI (`src/cli/onboarding_wizard.py`) orchestrates all 8 sections, converts state to UserDataInput with string-to-enum mapping, and generates all 6 config files to their correct locations
- Hook path fix ensures agents read profile from `fin-guru-private/fin-guru/data/user-profile.yaml` (where wizard writes), completing the ONBD-17 runtime chain: wizard -> hook -> agents see user_name
- 63 new tests covering validators (34), sections (11), and wizard integration (18) with 0 regressions across the full 426-test suite

## Task Commits

Each task was committed atomically:

1. **Task 1: Wizard CLI entry point with config generation** - `3c95a9d` (feat)
2. **Task 2: Fix hook profile path** - `4f2f9ac` (fix)
3. **Task 3: Comprehensive test suite** - `8bd9fa4` (test)
4. **Task 4: Agent genericization** - No commit needed (agents already use {user_name})

## Files Created/Modified

- `src/cli/onboarding_wizard.py` - Wizard CLI: 8-section orchestration, convert_state_to_user_data, generate_config_files, argparse with --dry-run
- `.claude/hooks/load-fin-core-config.ts` - Fixed configPath/profilePath/systemContextPath to read from fin-guru-private/
- `tests/python/test_onboarding_validators.py` - 34 tests: currency/percentage/integer parsing + ask_with_retry retry/skip/Ctrl+C
- `tests/python/test_onboarding_sections.py` - 11 tests: mocked questionary for liquid assets, investments, cash flow, preferences, env setup, summary
- `tests/python/test_onboarding_wizard.py` - 18 tests: state-to-model conversion, config file generation, backup, SECTION_ORDER
- `pyproject.toml` - Added pytest-mock dev dependency
- `uv.lock` - Updated lockfile

## Decisions Made

- **_safe_enum helper**: Wraps enum conversion with case-insensitive fallback and UserWarning on unknown values, rather than raising exceptions (graceful degradation)
- **Separate writes for project-root files**: write_config_files() writes to base_dir, but CLAUDE.md/.env/mcp.json need project root -- solved by explicit Path.write_text() after the bulk write
- **Agent genericization already done**: Grep showed all agent files already use `{user_name}` from prior work; no modifications needed for Task 4
- **pytest-mock added**: Required for questionary mocking pattern (mocker.patch); mock at import site (src.utils.onboarding_sections.questionary) not global

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added sys.path for direct CLI invocation**
- **Found during:** Task 1 (wizard CLI)
- **Issue:** `uv run python src/cli/onboarding_wizard.py --help` failed with ModuleNotFoundError because `src.` imports require project root on sys.path
- **Fix:** Added `sys.path.insert(0, str(Path(__file__).parent.parent.parent))` following existing pattern from `src/cli/fin_guru.py`
- **Files modified:** src/cli/onboarding_wizard.py
- **Verification:** `uv run python src/cli/onboarding_wizard.py --help` works
- **Committed in:** 3c95a9d (Task 1 commit)

**2. [Rule 3 - Blocking] Installed pytest-mock dev dependency**
- **Found during:** Task 1 prep (before Task 3 tests)
- **Issue:** pytest-mock not in dev dependencies, required for mocker fixture in tests
- **Fix:** `uv add --group dev pytest-mock`
- **Files modified:** pyproject.toml, uv.lock
- **Verification:** `uv run python -c "import pytest_mock"` succeeds
- **Committed in:** 3c95a9d (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (2 blocking)
**Impact on plan:** Both fixes necessary for CLI invocation and test execution. No scope creep.

## Issues Encountered

None -- all tasks executed smoothly.

## User Setup Required

None -- no external service configuration required.

## Next Phase Readiness

- Onboarding wizard is functionally complete: sections collect data, wizard converts to models, generates all config files
- Phase 4 (save/resume) can add persistence to OnboardingState for interrupted sessions
- Phase 5 (agent readiness) benefits from the pytest-mock dependency and testing patterns established here
- Hook path fix means new users who complete onboarding will have agents load their profile automatically

---
*Phase: 03-onboarding-wizard*
*Completed: 2026-02-06*
