---
phase: 02-setup-automation
plan: 02
subsystem: infra
tags: [bash, setup-script, idempotency, progress-tracking, uv, directory-scaffolding]

# Dependency graph
requires:
  - phase: 02-setup-automation/01
    provides: "Dependency checker with OS detection, color output, CLI args, --check-deps-only"
provides:
  - "Complete setup.sh: directory creation, config scaffolding, progress tracking, Python deps, summary"
  - "Idempotent re-run via .setup-progress file-level tracking"
  - "fin-guru-private/ directory tree with hedging, strategies, analysis subdirs"
  - "user-profile.yaml template for Phase 3 onboarding wizard to populate"
  - "Integration test covering first run, idempotency, missing dir detection, --check-deps-only, --help"
affects: [03-onboarding-wizard, 06-config-models]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Progress file (.setup-progress) with line-per-step format for resumable setup"
    - "scaffold_file() with [ -t 0 ] tty check for overwrite prompts"
    - "verify_directory_structure() runs on EVERY path for structural validation"
    - "File-level idempotency (skip or prompt) -- field-level YAML merging deferred to Phase 3"

key-files:
  created:
    - ".planning/phases/02-setup-automation/02-02-SUMMARY.md"
  modified:
    - "setup.sh"
    - ".gitignore"
    - "tests/integration/test_setup_onboarding_integration.sh"

key-decisions:
  - "File-level idempotency only: scaffold_file skips existing files or prompts for full overwrite. Field-level YAML merging deferred to Phase 3 onboarding wizard (ONBD-06 scope boundary)"
  - "verify_directory_structure runs on every execution path (first run AND re-run) to catch missing subdirs even when dirs_created is already in progress file"
  - "5 trackable milestones: deps_checked, dirs_created, dirs_verified, config_scaffolded, python_deps_installed"
  - "User-profile.yaml placed at fin-guru/data/ (tracked in git as template) rather than fin-guru-private/ (gitignored)"

patterns-established:
  - "Progress tracking: is_step_complete/mark_step_complete with grep-based line matching"
  - "Config scaffolding: scaffold_file handles tty detection, overwrite prompt defaults to N"
  - "Summary reporting: CREATED_ITEMS/SKIPPED_ITEMS arrays for end-of-run report"

# Metrics
duration: 11min
completed: 2026-02-04
---

# Phase 2 Plan 2: Directory Creation, Config Scaffolding, and Idempotent Re-runs Summary

**Complete setup.sh with fin-guru-private/ directory tree, user-profile.yaml/env/README scaffolding, .setup-progress resumable tracking, uv sync Python deps, and 46-assertion integration test**

## Performance

- **Duration:** 11 min
- **Started:** 2026-02-04T03:34:51Z
- **Completed:** 2026-02-04T03:46:21Z
- **Tasks:** 3 (Task 2 was verification-only, no code changes needed)
- **Files modified:** 3

## Accomplishments
- setup.sh creates all 20+ directories under fin-guru-private/ including hedging/, strategies/active|archive|risk-management, analysis/reports, and notebooks tree
- Config scaffolding with scaffold_file() creates user-profile.yaml template, .env from .env.example, and fin-guru-private/README.md with tty-aware overwrite prompts
- .setup-progress tracks 5 milestones for resumable re-runs; second run shows "Resuming setup... (5/5 steps completed)" and skips completed steps
- verify_directory_structure runs on every execution path, detecting and recreating missing subdirectories even when the progress file shows dirs_created as complete
- Integration test rewritten with 46 assertions covering first run, --check-deps-only isolation, idempotent re-run, missing directory detection, and --help flag

## Task Commits

Each task was committed atomically:

1. **Task 1: Add progress tracking, directory creation, config scaffolding, Python deps, and summary** - `f01f48e` (feat)
2. **Task 2: Implement idempotent re-run behavior and verify SC4** - No commit (verification-only, all behavior correct from Task 1)
3. **Task 3: Update integration test for new setup.sh behavior** - `1ef6a53` (test)

## Files Created/Modified
- `setup.sh` - Added 8 new functions: is_step_complete, mark_step_complete, show_progress, create_dir, create_directory_structure, verify_directory_structure, scaffold_file, scaffold_config_files, install_python_deps, print_summary. Updated main flow with step-based execution.
- `.gitignore` - Added .setup-progress exclusion in Family Office section
- `tests/integration/test_setup_onboarding_integration.sh` - Complete rewrite: 46 assertions across 5 test groups, removed all old onboarding/symlink/MCP references

## Decisions Made
- **File-level idempotency scope boundary (ONBD-06):** scaffold_file handles skip/overwrite at file level only. Field-level YAML merging (parsing existing user-profile.yaml to add missing keys) deferred to Phase 3 onboarding wizard per CONTEXT.md: "setup.sh prepares the environment, it does not collect financial profile data."
- **verify_directory_structure on every path:** Even on first run after create_directory_structure, we run verify. This catches scenarios where dirs already existed from a prior partial run but are missing expected subdirectories.
- **user-profile.yaml at fin-guru/data/ (not fin-guru-private/):** The template is committed to git so new clones get it. Phase 3 onboarding will populate it with user data into the gitignored fin-guru-private/ location or update this template in place.
- **Non-interactive default for scaffold_file:** When stdin is not a tty, existing files are kept without prompting. This prevents CI/test hangs.

## Deviations from Plan

None - plan executed exactly as written. Task 2 (idempotency verification) required zero code fixes; all four scenarios passed on first attempt.

## Issues Encountered
- **Python 3.12 not default in dev environment:** `python3` resolves to 3.11 in this environment while `python3.12` is available at `/usr/bin/python3.12`. Handled via PATH override in testing and in the integration test's PATH Setup section. This is an environment-specific issue, not a script bug -- the dependency checker correctly reports the version mismatch.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- setup.sh is fully functional: `./setup.sh` on a fresh clone creates working environment
- Phase 2 is complete (both plans done): dependency checking + directory/config setup
- Ready for Phase 3 (Onboarding Wizard): user-profile.yaml template exists at fin-guru/data/, onboarding wizard will populate it with interactive financial profile data
- fin-guru-private/ directory structure is in place for hedging tools (Phase 6) and analysis outputs

---
_Phase: 02-setup-automation_
_Completed: 2026-02-04_
