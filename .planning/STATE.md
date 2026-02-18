# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-02)

**Core value:** Anyone can clone the repo, run setup, and have a working personalized Finance Guru with their own financial data -- no hardcoded references, no manual configuration, and a growing suite of institutional-grade CLI analysis tools.
**Current focus:** Phase 6 in progress -- Config Loader and Shared Hedging Models

## Current Position

Phase: 6 of 12 (Config Loader and Shared Hedging Models)
Plan: 2 of 3 in current phase
Status: In progress
Last activity: 2026-02-17 -- Completed 06-01-PLAN.md

Progress: [████████░░░░░░░░░░░░] 39%

## Performance Metrics

**Velocity:**
- Total plans completed: 12
- Average duration: ~9 min
- Total execution time: ~1.87 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-git-scrub | 1/3 | ~15 min | ~15 min |
| 02-setup-automation | 2/2 | 17 min | 9 min |
| 03-onboarding-wizard | 2/2 | 16 min | 8 min |
| 04-onboarding-polish-hook-refactoring | 2/2 | 12 min | 6 min |
| 05-agent-readiness-hardening | 5/5 | 59 min | 12 min |
| 06-config-loader-shared-hedging-models | 2/3 | 13 min | 7 min |

**Recent Trend:**
- Last 5 plans: 05-04 (14 min), 05-05 (12 min), 06-02 (5 min), 06-01 (8 min)
- Trend: ~10 min/plan

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Roadmap]: M1 before M2 is non-negotiable -- hedging tools need user-profile.yaml with stable schema
- [Roadmap]: Phase 1 (git scrub) is CRITICAL prerequisite before any public visibility
- [Roadmap]: Phase 9 (SQQQ comparison) isolated due to highest-risk calculation (was Phase 8, renumbered)
- [Roadmap]: Phases 1, 9, 10 flagged for /gsd:research-phase before planning (renumbered from 1, 8, 9)
- [Roadmap]: Phase 5 (Agent Readiness Hardening) added at end of M1 based on agent-readiness-report (2026-02-02). L1->L2 quick wins: ruff linter, expanded pre-commit hooks, issue/PR templates, test coverage thresholds, CODEOWNERS.
- [01-01]: PII replaced with template variables ({account_id}, {spreadsheet_id}, {user_name}, {employer_name}, {llc_name}) rather than generic placeholders
- [01-01]: OS-level paths preserved, will be handled by git-filter-repo in Plan 02
- [01-01]: Personal email addresses and domains in backend dev guidelines cleaned as additional PII
- [02-01]: Used sort -V for version comparison (avoids Python 4.x false negative from arithmetic)
- [02-01]: check-all-then-fail pattern with set -e + || guards for dependency checking
- [02-02]: File-level idempotency only for setup.sh; field-level YAML merging deferred to Phase 3 onboarding wizard
- [02-02]: verify_directory_structure runs on every execution path (first run and re-run) to catch missing subdirs
- [02-02]: user-profile.yaml template at fin-guru/data/ (tracked in git as template, Phase 3 will populate)
- [03-01]: State stores raw strings for enum fields; string-to-enum conversion deferred to Plan 02 convert_state_to_user_data
- [03-01]: Percentages collected as human-friendly (4.5 for 4.5%) then divided by 100 for decimal storage
- [03-01]: 25k/1.5M shorthand multipliers supported in currency parsing (usability win per CONTEXT.md)
- [03-02]: _safe_enum helper for string-to-enum conversion with case-insensitive fallback and UserWarning on unknown values
- [03-02]: Private configs via write_config_files(base_dir='fin-guru-private'), project-root files via explicit Path.write_text()
- [03-02]: Agent files already genericized ({user_name}); no modifications needed
- [03-02]: pytest-mock added as dev dependency for questionary mocking in tests
- [04-01]: Recreated settings.json (was deleted in e3f008e) with all .ts direct invocations including SessionStart
- [04-01]: 500ms performance threshold with warmup run for Bun transpile cache priming
- [04-02]: Atomic write pattern (tempfile+rename) for crash-safe progress persistence
- [04-02]: WizardInterruptHandler as backup; primary interrupt detection is questionary returning None on Ctrl+C
- [05-02]: Coverage threshold starts at 0 (--cov-fail-under=0); TODO for plan 05-05 to raise to 80
- [05-02]: CI uses astral-sh/setup-uv@v6 and concurrency group with cancel-in-progress
- [05-02]: YAML form format (not markdown) for GitHub issue templates
- [05-01]: Ruff replaces black as sole linter+formatter; D205/D100/D107/B028/E402 ignored globally
- [05-01]: N803/N806 per-file ignored in analysis/strategies/utils -- financial code uses uppercase single-letter vars
- [05-01]: C901 noqa on 12 complex CLI format functions -- refactoring deferred
- [05-03]: mypy standard mode (not --strict) to avoid requiring full annotations on 23k-line codebase
- [05-03]: Per-module relaxed mypy overrides for 20+ existing financial modules; tightening deferred
- [05-03]: pre-commit install uses default migration mode, preserving bd hooks as .legacy
- [05-04]: All tests use synthetic data (numpy random walks) -- zero real API calls
- [05-04]: Known-answer tests where formulas are verifiable (SMA, WMA, beta of self=1.0)
- [05-04]: CLI wrapper files excluded from coverage targets (I/O-only thin wrappers)
- [05-05]: Coverage omit patterns exclude CLI wrappers, UI, screener, dashboard models from coverage
- [05-05]: branch=true in coverage.run for conditional path coverage
- [06-02]: Converted src/config.py to src/config/ package for config_loader.py colocation; backward compat via __init__.py re-export
- [06-02]: fin-guru-private/hedging/ templates are gitignored private data; not committed to git
- [06-01]: HedgePosition uses model_validator to conditionally require strike/expiry for puts only
- [06-01]: TickerReturn warns (not rejects) when total_return != price_return + dividend_return
- [06-01]: DividendRecord.shares_at_ex is float (not int) to support fractional DRIP shares

### Pending Todos

None yet.

### Blockers/Concerns

- [Phase 1]: RESOLVED -- PII audit found 1,645 matches across 157 commits. Plans created to address all.
- [Phase 8]: options_chain scanner (scan_chain) has stderr side effects -- pragmatic vs clean extraction TBD (was Phase 7, renumbered)
- [Phase 10]: Cytoscape.js WebGL vs Canvas decision deferred to research (was Phase 9, renumbered)

## Quick Tasks

| Task | Description | Status | Completed |
|------|-------------|--------|-----------|
| quick-001 | Organize docs with frontmatter categories | Complete | 2026-02-05 |

## Session Continuity

Last session: 2026-02-17
Stopped at: Completed 06-01-PLAN.md (shared hedging and total return models)
Resume file: None
Next action: Execute 06-03-PLAN.md (remaining Phase 06 plan)
