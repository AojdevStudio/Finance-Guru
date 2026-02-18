---
phase: 03-onboarding-wizard
plan: 01
subsystem: onboarding
tags: [questionary, pydantic, wizard, cli, validation, interactive-prompts]

# Dependency graph
requires:
  - phase: 02-setup-automation
    provides: "setup.sh, user-profile.yaml template at fin-guru/data/"
provides:
  - "OnboardingState model with 8-section SectionName enum"
  - "Domain validators: validate_currency, validate_percentage, validate_positive_integer"
  - "ask_with_retry wrapper with 3-retry-then-skip using questionary.confirm"
  - "8 section runner functions for interactive financial profile collection"
affects: [03-onboarding-wizard plan 02, phase 4 save/resume]

# Tech tracking
tech-stack:
  added: [questionary 2.1.1, prompt-toolkit 3.0.52]
  patterns: ["ask_with_retry validation wrapper", "raw-data-then-convert pattern for wizard state"]

key-files:
  created:
    - src/models/onboarding_inputs.py
    - src/utils/onboarding_validators.py
    - src/utils/onboarding_sections.py
  modified:
    - pyproject.toml
    - uv.lock

key-decisions:
  - "State stores raw strings for enum fields; string-to-enum conversion deferred to Plan 02 convert_state_to_user_data"
  - "Percentages collected as human-friendly (4.5 for 4.5%) then divided by 100 for decimal storage"
  - "25k/1.5M shorthand multipliers supported in currency parsing"

patterns-established:
  - "ask_with_retry: 3-retry then questionary.confirm skip pattern for all validated prompts"
  - "Section runner signature: (OnboardingState) -> OnboardingState with raw dict storage in state.data"
  - "Ctrl+C (None) returns state without marking section complete"

# Metrics
duration: 6min
completed: 2026-02-05
---

# Phase 3 Plan 1: Onboarding Models, Validators, and Section Runners Summary

**OnboardingState model, 3 domain validators with 25k/1.5M smart parsing, ask_with_retry 3-fail-then-skip wrapper, and 8 questionary-powered section runners for interactive financial profile collection**

## Performance

- **Duration:** 6 min
- **Started:** 2026-02-06T00:52:36Z
- **Completed:** 2026-02-06T00:58:38Z
- **Tasks:** 2/2
- **Files modified:** 5 (3 created, 2 updated)

## Accomplishments

- OnboardingState Pydantic model tracks wizard progress across 8 sections with create_new(), is_section_complete(), and mark_complete() methods
- Smart currency parsing handles $10,000.50, 25k, 1.5M formats; percentage parser enforces 0-100 range; integer parser rejects zero and negatives
- ask_with_retry wrapper implements ONBD-02 requirement: 3 retries with clear error messages, then questionary.confirm skip offer with sensible default
- All 8 section runners mirror TypeScript scaffold question flow using questionary.text(), .select(), .confirm(), and .checkbox() with graceful Ctrl+C handling

## Task Commits

Each task was committed atomically:

1. **Task 1: Onboarding models and retry-with-skip validators** - `3c81f10` (feat)
2. **Task 2: Eight section runner functions** - `47a4396` (feat)

## Files Created/Modified

- `src/models/onboarding_inputs.py` - SectionName enum (8 values), OnboardingState model with wizard progress tracking (90 lines)
- `src/utils/onboarding_validators.py` - validate_currency, validate_percentage, validate_positive_integer, ask_with_retry wrapper (226 lines)
- `src/utils/onboarding_sections.py` - 8 section runner functions: liquid assets, investments, cash flow, debt, preferences, broker, env setup, summary (882 lines)
- `pyproject.toml` - Added questionary dependency
- `uv.lock` - Locked questionary 2.1.1 + prompt-toolkit 3.0.52 + wcwidth 0.5.3

## Decisions Made

- **Raw string storage for enums:** Section runners store questionary return values as-is (e.g., "aggressive", "growth"). Conversion to enum instances (RiskTolerance.AGGRESSIVE) deferred to Plan 02's convert_state_to_user_data function. This keeps wizard state decoupled from Pydantic model validation during collection.
- **Percentage storage convention:** Users enter human-friendly values (4.5 for 4.5%). Rates stored as decimals (0.045) in state.data to match existing yaml_generation_inputs.py field constraints (ge=0, le=1).
- **Smart currency multipliers:** Added support for 25k and 1.5M shorthand in validate_currency (not in original TS scaffold) per CONTEXT.md decision that smart dollar parsing is a key usability win.

## Deviations from Plan

None -- plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None -- no external service configuration required.

## Next Phase Readiness

- All three files ready for Plan 02 to import and orchestrate as the wizard CLI
- Plan 02 needs: wizard CLI entry point, convert_state_to_user_data function (maps raw strings to enum instances), YAML generation integration
- Section runners are self-contained -- each can be called independently for section re-edit flow

---
*Phase: 03-onboarding-wizard*
*Completed: 2026-02-05*
