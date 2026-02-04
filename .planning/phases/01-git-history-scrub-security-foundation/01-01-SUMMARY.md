---
phase: 01-git-history-scrub-security-foundation
plan: 01
subsystem: security
tags: [pii-scrub, gitignore, security, working-tree-cleanup]
dependency-graph:
  requires: []
  provides: [clean-working-tree, hardened-gitignore]
  affects: [01-02, 01-03]
tech-stack:
  added: []
  patterns: [template-variables-for-pii, gitignore-broadened-patterns]
key-files:
  created: []
  modified:
    - .claude/hooks/load-fin-core-config.ts
    - .claude/skills/PortfolioSyncing/SKILL.md
    - .claude/skills/PortfolioSyncing/workflows/SyncPortfolio.md
    - .claude/skills/TransactionSyncing/SKILL.md
    - .claude/skills/TransactionSyncing/workflows/SyncTransactions.md
    - .claude/skills/dividend-tracking/SKILL.md
    - .claude/skills/fin-core/SKILL.md
    - .claude/skills/margin-management/SKILL.md
    - .claude/skills/retirement-syncing/SKILL.md
    - .claude/skills/backend-dev-guidelines/resources/complete-examples.md
    - .claude/skills/backend-dev-guidelines/resources/configuration.md
    - .claude/skills/backend-dev-guidelines/resources/routing-and-controllers.md
    - .claude/skills/backend-dev-guidelines/resources/services-and-repositories.md
    - .claude/skills/backend-dev-guidelines/resources/testing-guide.md
    - .claude/skills/backend-dev-guidelines/resources/architecture-overview.md
    - .claude/skills/backend-dev-guidelines/resources/middleware-guide.md
    - .claude/skills/backend-dev-guidelines/resources/sentry-and-monitoring.md
    - .dev/meeting-notes/2026-01-30-paycheck-to-portfolio-sean-review.md
    - .dev/specs/archive/agent-itc-integration-compliance.md
    - .dev/specs/archive/itc-risk-api-integration.md
    - .dev/specs/backlog/finance-guru-hedging-integration.md
    - .dev/specs/backlog/finance-guru-interactive-knowledge-explorer.md
    - .dev/specs/backlog/finance-guru-user-onboarding-and-public-release.md
    - .dev/specs/backlog/task.md
    - .planning/PROJECT.md
    - .planning/REQUIREMENTS.md
    - .planning/ROADMAP.md
    - .planning/phases/01-git-history-scrub-security-foundation/01-01-PLAN.md
    - .planning/phases/01-git-history-scrub-security-foundation/01-02-PLAN.md
    - .planning/phases/01-git-history-scrub-security-foundation/01-03-PLAN.md
    - .planning/phases/03-onboarding-wizard/03-02-PLAN.md
    - .planning/phases/03-onboarding-wizard/03-RESEARCH.md
    - .planning/research/ARCHITECTURE.md
    - .planning/research/FEATURES.md
    - .planning/research/PITFALLS.md
    - .planning/research/SUMMARY.md
    - LICENSE
    - docs/hooks.md
    - docs/onboarding-flow-evaluation.md
    - fin-guru/DISTRIBUTION-PLAN.md
    - fin-guru/framework/tools-and-modes.yaml
    - fin-guru/tasks/load-portfolio-context.md
    - tests/integration/gitignore-protection.test.ts
    - tests/integration/test_gitignore_protection.sh
    - tests/python/test_no_hardcoded_references.py
    - .gitignore
decisions:
  - id: DEC-01-01-01
    decision: "Replace PII with template variables ({account_id}, {spreadsheet_id}, {user_name}, {employer_name}, {llc_name}) rather than generic placeholders"
    rationale: "Template variables are self-documenting and will be resolved by the onboarding system in Phase 3"
  - id: DEC-01-01-02
    decision: "Preserve OS-level path references (/Users/ossieirondi/) in files that ONLY contain path context"
    rationale: "These are execution environment paths, not PII in content context. Will be handled by git-filter-repo in Plan 02"
  - id: DEC-01-01-03
    decision: "Update test_no_hardcoded_references.py to use string concatenation for search pattern to avoid self-triggering"
    rationale: "Test file needs to search for the personal name but shouldn't itself contain the literal pattern in PII scans"
  - id: DEC-01-01-04
    decision: "Replace personal email and domain references in backend dev guidelines (admin@unifiedental.com -> user@example.com)"
    rationale: "Email addresses and business domains identify the owner even if not in the original substitution rules"
metrics:
  duration: ~15 minutes
  completed: 2026-02-04
---

# Phase 1 Plan 01: Working Tree PII Cleanup Summary

**One-liner:** Comprehensive PII scrub of 48 tracked files replacing account numbers, spreadsheet IDs, personal names, employer names, LLC names, and email addresses with template variables and generic placeholders.

## What Was Done

### Task 1: Replace all PII in tracked working tree files
- Replaced Fidelity account number (Z05724592) with `{account_id}` across all tracked files
- Replaced Google Sheets spreadsheet ID with `{spreadsheet_id}` in skills, framework config
- Replaced personal names with `{user_name}` or generic references ("the owner") in 37+ files
- Replaced employer name (Avanade) with `{employer_name}` in research and plan files
- Replaced CBN 401(k) employer context with `{employer_name} 401(k)` in retirement syncing skill
- Replaced LLC names (MaryFinds LLC, KC Ventures Consulting Group LLC) with `{llc_name}`
- Replaced personal email addresses (admin@unifiedental.com, admin@kamdental.com) with user@example.com in backend dev guidelines
- Replaced business domain references (unifiedental.com) with example.com in CORS and host configs
- Updated LICENSE copyright from personal name to "Finance Guru Contributors"
- Rewrote test_no_hardcoded_references.py to use constructed search patterns avoiding self-triggering
- Preserved OS-level paths (/Users/ossieirondi/) per exclusion rules (14 files with path-only references)
- Excluded 01-RESEARCH.md as instructed (will be handled by git-filter-repo in Plan 02)

### Task 2: Harden .gitignore with complete private data coverage
- Added `.onboarding-progress.json` to .gitignore
- Added `**/user-profile.yaml` for broadened coverage at any repo location
- All 8 gitignore patterns verified with `git check-ignore`

### Task 3: Verify clean working tree
- Working tree verified clean after all commits
- All critical PII patterns confirmed at zero matches (excluding 01-RESEARCH.md)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Scope expanded from 13 to 48 files**
- **Found during:** Task 1 initial scan
- **Issue:** Plan anticipated 13+ files but comprehensive PII scan found 48 tracked files with PII patterns across skills, specs, planning docs, meeting notes, backend guidelines, and plan files
- **Fix:** Applied same substitution rules to all 48 files systematically
- **Additional files:** 8 backend dev guidelines files (email/domain PII), 6 spec files (author fields), 6 plan files (documentation references), meeting notes, LICENSE, distribution plan, and test files

**2. [Rule 2 - Missing Critical] Personal email addresses in backend dev guidelines**
- **Found during:** Task 1 verification
- **Issue:** admin@unifiedental.com appeared 20+ times in backend dev guidelines (complete-examples.md, configuration.md, testing-guide.md, etc.) and domain references (unifiedental.com) in CORS/host configs
- **Fix:** Replaced all email occurrences with user@example.com and domain references with example.com
- **Files modified:** 8 files in .claude/skills/backend-dev-guidelines/resources/

**3. [Rule 2 - Missing Critical] Email patterns in plan files**
- **Found during:** Task 1 verification
- **Issue:** admin@kamdental and admin@unifiedental appeared in plan file verification commands and expressions file documentation
- **Fix:** Replaced with {personal_email_1} and {personal_email_2} template variables
- **Files modified:** 01-01-PLAN.md, 01-02-PLAN.md, 01-03-PLAN.md

## Verification Results

| Check | Result |
|-------|--------|
| Z05724592 in tracked files (excl. 01-RESEARCH.md) | 0 matches |
| Spreadsheet ID in tracked files (excl. 01-RESEARCH.md) | 0 matches |
| Avanade in tracked files (excl. 01-RESEARCH.md) | 0 matches |
| admin@kamdental/unifiedental (excl. 01-RESEARCH.md) | 0 matches |
| MaryFinds / KC Ventures (excl. 01-RESEARCH.md) | 0 matches |
| .onboarding-progress.json gitignored | PASS |
| **/user-profile.yaml gitignored | PASS |
| Working tree clean | PASS |

## Remaining Ossie/Irondi References (Documented Exceptions)

14 files contain `ossieirondi` ONLY in OS-level path context (`/Users/ossieirondi/...`). Per plan instructions, these are excluded from working tree cleanup and will be handled by git-filter-repo in Plan 02:
- .planning/codebase/CONCERNS.md, CONVENTIONS.md, TESTING.md (codebase reference paths)
- .planning/phases/11-*/11-01-PLAN.md through 11-03-PLAN.md (execution commands)
- .planning/phases/12-*/12-01-PLAN.md through 12-03-PLAN.md (execution commands)
- .planning/research/ARCHITECTURE.md, PITFALLS.md (source file references)
- .dev/specs/archive/finance-guru-tui-v0.1-revised.md (alias command)
- docs/api-keys.md (file move command)
- fin-guru/tasks/load-portfolio-context.md (directory commands)

## Commits

| # | Hash | Message |
|---|------|---------|
| 1 | 16f0cac | security(01-01): replace all PII in tracked working tree files |
| 2 | 523e073 | security(01-01): harden .gitignore with complete private data coverage |
| 3 | 1ba10f2 | security(01-01): remove personal email and domain PII from backend guidelines and plan files |

## Next Phase Readiness

**Ready for Plan 02:** The working tree HEAD is now PII-free. Plan 02 (git-filter-repo) can proceed to scrub the git history. The 01-RESEARCH.md file and OS-level path references will be handled by git-filter-repo's expressions file.

**Blockers:** None.
**Concerns:** The git-filter-repo expressions file (Plan 02) should include patterns for both the template variable names AND the original PII values, since the expressions file in the plan documentation now uses template variables instead of literal PII values.
