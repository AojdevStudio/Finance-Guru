---
phase: 04-onboarding-polish-hook-refactoring
plan: 01
subsystem: infra
tags: [bun, typescript, hooks, claude-code, performance-testing]

# Dependency graph
requires:
  - phase: 03-onboarding-wizard
    provides: Bun hook infrastructure and existing test suite (82+ tests)
provides:
  - .ts-only hook architecture with direct bun run invocation for all 3 hooks
  - Performance test suite proving all hooks execute in < 500ms
  - Clean settings.json with SessionStart, UserPromptSubmit, PostToolUse, Stop hooks
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Direct bun run .ts invocation in settings.json (no bash wrappers)"
    - "Performance testing via child_process spawn with performance.now() timing"

key-files:
  created:
    - .claude/settings.json
    - .claude/hooks/tests/test_hook_performance.test.ts
  modified:
    - .claude/hooks/CONFIG.md

key-decisions:
  - "Recreated settings.json (was deleted in e3f008e) with all .ts direct invocations"
  - "500ms threshold with warmup run for reliable performance assertions"
  - "PROJECT_ROOT derived from import.meta.dir for portable test paths"

patterns-established:
  - "timeHook() helper: spawn + performance.now() for hook performance measurement"
  - "Warmup test before timed assertions to prime Bun transpile cache"

# Metrics
duration: 7min
completed: 2026-02-12
---

# Phase 4 Plan 1: Hook Migration Cleanup Summary

**Direct bun .ts invocation for all 3 hooks, dead .sh files deleted, performance test suite proving < 500ms execution**

## Performance

- **Duration:** 7 min
- **Started:** 2026-02-12T15:29:45Z
- **Completed:** 2026-02-12T15:37:15Z
- **Tasks:** 2
- **Files modified:** 5 (1 created settings.json, 1 created test, 1 modified CONFIG.md, 2 deleted .sh)

## Accomplishments
- All 3 hooks (load-fin-core-config, skill-activation-prompt, post-tool-use-tracker) now invoked directly as Bun TypeScript with no bash wrappers
- Deleted 2 dead .sh files (skill-activation-prompt.sh: 6 lines, post-tool-use-tracker.sh: 177 lines)
- Performance test suite with warmup + 3 timed tests, all under 500ms
- CONFIG.md fully updated to reflect .ts-only architecture with TypeScript code examples
- Completes ONBD-10, ONBD-11, ONBD-12, ONBD-13

## Task Commits

Each task was committed atomically:

1. **Task 1: Update settings.json, delete dead .sh files, update CONFIG.md** - `2732efe` (feat)
2. **Task 2: Write Bun performance test suite for all 3 hooks** - `558b109` (test)

## Files Created/Modified
- `.claude/settings.json` - Recreated with all hooks using bun run .ts direct invocation
- `.claude/hooks/tests/test_hook_performance.test.ts` - Performance test suite (105 lines)
- `.claude/hooks/CONFIG.md` - Updated all examples from .sh to .ts with TypeScript syntax
- `.claude/hooks/skill-activation-prompt.sh` - DELETED (dead bash wrapper)
- `.claude/hooks/post-tool-use-tracker.sh` - DELETED (dead bash original)

## Decisions Made
- Recreated `.claude/settings.json` from scratch since it was deleted in commit e3f008e; included SessionStart hook (load-fin-core-config.ts) that was missing from the last version
- Used `PROJECT_ROOT = join(HOOKS_DIR, "../..")` for portable path resolution in tests (skill-activation-prompt.ts needs cwd to find skill-rules.json)
- 1 pre-existing test failure in test_load_fin_core_config.test.ts ("should load system configuration" expects config.yaml content from fin-guru-private which is not available) -- not a regression, not fixed in this plan

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed performance test cwd path for skill-activation-prompt**
- **Found during:** Task 2 (performance test creation)
- **Issue:** skill-activation-prompt.ts uses `data.cwd` to locate skill-rules.json; using `process.cwd()` in test resolved to hooks directory, causing ENOENT
- **Fix:** Used `PROJECT_ROOT = join(HOOKS_DIR, "../..")` to derive project root from test file location
- **Files modified:** .claude/hooks/tests/test_hook_performance.test.ts
- **Verification:** All 4 performance tests pass
- **Committed in:** 558b109

**2. [Rule 3 - Blocking] Recreated settings.json instead of editing**
- **Found during:** Task 1 (settings.json update)
- **Issue:** `.claude/settings.json` was deleted in commit e3f008e; plan assumed it existed
- **Fix:** Created new settings.json with complete hook configuration matching the .ts-only architecture
- **Files modified:** .claude/settings.json
- **Verification:** grep confirms no .sh references for migrated hooks
- **Committed in:** 2732efe

---

**Total deviations:** 2 auto-fixed (1 bug, 1 blocking)
**Impact on plan:** Both fixes necessary for correct operation. No scope creep.

## Issues Encountered
- 1 pre-existing test failure (82/83 existing tests pass) in test_load_fin_core_config.test.ts -- expects `module_name: "Finance Guru"` from config.yaml in fin-guru-private directory which is not available in test environment. Confirmed failure exists on the branch before any changes.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Hook migration is fully complete (ONBD-10, ONBD-11, ONBD-12, ONBD-13)
- Ready for Plan 02 (onboarding save/resume) which is independent of hook changes
- Pre-existing test failure should be addressed in a future maintenance pass

---
*Phase: 04-onboarding-polish-hook-refactoring*
*Completed: 2026-02-12*
