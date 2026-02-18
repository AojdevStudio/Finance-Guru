# Phase 4: Onboarding Polish & Hook Refactoring - Context

**Gathered:** 2026-02-05
**Status:** Ready for planning

<domain>
## Phase Boundary

Make onboarding interruption-safe (Ctrl+C saves progress, restart resumes) and port all Claude hooks from shell scripts to Bun TypeScript under 500ms. Existing 428 pytest tests must stay green (zero regressions).

</domain>

<decisions>
## Implementation Decisions

### Save/resume behavior
- Auto-save after each completed section completes + on Ctrl+C signal
- Save partial field answers within interrupted sections (resume picks up at exact field)
- On restart: show progress summary ("Resuming from Section X — Y of Z complete") and ask "Continue from here or start over?"
- Progress file: JSON with `schemaVersion: 1` field for forward compatibility
- Storage location: `~/.config/family-office/onboarding-progress.json`
- Atomic writes via write-to-temp-then-rename pattern to prevent corruption from kill -9
- On completed onboarding: rename progress file to `onboarding-complete.json` (acts as "wizard already ran" marker)
- Re-running after completion: warn + confirm ("Re-run will overwrite current config. Continue?")
- Corrupt progress file: discard silently, show "Progress file corrupted, starting fresh"
- Schema version mismatch: discard old progress, show "Wizard updated since last run. Starting fresh."
- CLI flags: `--fresh` (ignore progress, don't delete), `--reset` (delete progress + completion marker, start over)

### Hook cleanup scope
- Critical hook for this project: `load-fin-core-config.ts` (already Bun TS — wire into settings.json)
- Port ALL remaining `.sh` hooks to Bun TypeScript (clean sweep):
  - `error-handling-reminder.sh` → `.ts`
  - `stop-build-check-enhanced.sh` → `.ts`
  - `trigger-build-resolver.sh` → `.ts`
  - `tsc-check.sh` → `.ts`
  - `run-tests.sh` → `.ts`
  - `skill-activation-prompt.sh` → delete (`.ts` already exists)
  - `post-tool-use-tracker.sh` → delete (`.ts` already exists)
- Delete all `.sh` wrapper files — settings.json points directly to `.ts` via `bun run`
- Create shared `hook-utils.ts` module: shared stdin reader, TypeScript interfaces (HookInput, ToolInput), common helpers — all hooks import from it
- Fresh Bun-native `package.json` for hooks directory (drop npm/node artifacts)
- GSD hooks (`gsd-check-update.cjs`, `gsd-statusline.cjs/.js`): untouched — third-party, out of scope
- Phase 4 rewires `settings.json` to point to `.ts` files AND updates onboarding wizard template so future runs produce correct hook paths

### Interruption edge cases
- Corrupt progress files: discard and start fresh (no recovery attempt)
- Kill -9 / terminal crash protection: write-rename atomic pattern
- Schema version mismatch: discard old progress, start fresh (no migration)
- `--fresh` flag: skip resume, ignore existing progress (doesn't delete file)
- `--reset` flag: delete progress file AND completion marker, then run fresh
- Both flags available simultaneously for different use cases

### Regression testing approach
- 428 existing pytest tests must all pass (verified: `uv run pytest --collect-only` returns 428)
- New tests for save/resume and hook ports use `bun:test` (Bun's native test runner)
- Test philosophy: intelligently combine tests for proper integration AND unit coverage — no tests for the sake of tests
- Hook parity verification: write behavior-based tests for TS hooks (expected files, exit codes, stdout) + one-time manual side-by-side diff against .sh output before deleting shell files
- Performance target: 500ms local, 800ms CI (environment-aware threshold)
- Performance measurement: both automated `bun:test` with timing assertions AND a benchmark script for manual profiling
- Integration smoke test: one test that simulates a Claude Code session, triggers each hook type, verifies no crashes and correct side effects
- CI: hook correctness tests go to CI permanently. Performance benchmarks use relaxed 800ms threshold in CI.

### Claude's Discretion
- Exact internal structure of `hook-utils.ts` shared module
- Signal handling implementation details (SIGINT, SIGTERM)
- Progress file internal JSON schema (beyond the required `schemaVersion` field)
- Benchmark script output format and iteration count
- Hook porting order and intermediate commits

</decisions>

<specifics>
## Specific Ideas

- Tech stack alignment: TypeScript is default for all product work, Bun is preferred runtime (from `techstackpreferences.md`)
- `bun:test` for hook tests, consistent with Bun-native approach
- The `load-fin-core-config.ts` hook is the most important hook for the project right now
- Tests should be intelligent — combine unit + integration coverage, not just line-count padding

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 04-onboarding-polish-hook-refactoring*
*Context gathered: 2026-02-05*
