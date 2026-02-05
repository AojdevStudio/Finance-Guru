## /gsd:discuss-phase — “vision decision” checklist

These phases need your input because the plans had to assume UX/presentation details.

### Discuss first (highest risk / most UX ambiguity)

- **Phase 3 — Onboarding Wizard** (`/gsd:discuss-phase 3`)
  - **Why**: user-facing interactive CLI
  - **Decide**: question flow, presentation style, validation behavior, help text, branching vs linear

- **Phase 8 — Rolling Tracker & Hedge Sizer** (`/gsd:discuss-phase 8`)
  - **Why**: most complex phase (6 plans); CLI design heavy
  - **Decide**: subcommand naming, output format (`status` / `suggest-roll` / `history`), how roll suggestions display

- **Phase 10 — Template Engine** (`/gsd:discuss-phase 10`)
  - **Why**: visual interactive product
  - **Decide**: explorer layout, node appearance, interaction patterns (click / hover / drag), color scheme

- **Phase 11 — Self-Assessment & Topics** (`/gsd:discuss-phase 11`)
  - **Why**: interactive UX choices
  - **Decide**: 4-state cycling behavior, guided vs standard vs YOLO differences, topic content depth

- **Phase 12 — Maya / CLI / Landing** (`/gsd:discuss-phase 12`)
  - Landing page design + CLI ergonomics (templates exist; builds on phases 10–11)
- **Phase 9 — SQQQ vs Puts** (`/gsd:discuss-phase 9`)
  - Mostly presentation (math/formulas fixed by research)
- **Phase 7 — Total Return** (`/gsd:discuss-phase 7`)
  - Mainly CLI output formatting (narrow scope; follows existing patterns)

### Skip (infrastructure; minimal gray areas)

- **Phase 1 — Git Scrub**: tool-dictated (git-filter-repo, gitleaks)
- **Phase 2 — Setup Automation**: scripts/automation, minimal UX
- **Phase 4 — Polish & Hooks**: mostly technical (SIGINT, Bun migration)
- **Phase 5 — Agent Readiness**: needs planning, but scope is lint/templates/coverage (low UX ambiguity)
- **Phase 6 — Config & Models**: internal infrastructure for downstream CLIs

---

## PR #8 status

**Status:** Ready to merge (pending checks)

| Item | Status |
| --- | --- |
| Merge conflicts | Resolved — rebased clean branch with only Phase 11 commits |
| Mergeable | Yes |
| CodeRabbit | Re-reviewing (triggered by force push) |
| GitGuardian | In progress |
| Claude Review | Queued |

### Codex GPT-5.2 review findings

#### Good

- All prior CodeRabbit issues addressed
- Plan docs are well-structured with consistent frontmatter and verification blocks
- Persistence architecture is sound (per-topic keying, version-aware, migration-aware)

#### Issues to note (non-blocking; plan docs, not code)

- **"7 knowledge values" but only 6 listed** (low)
  - Detail: Plan says 7, but the enum lists 6: `know`, `fuzzy`, `unknown`, `familiar`, `confident`, `mastered`. Fix during execution.
- **"Yolo" vs "YOLO" casing mismatch** (low)
  - Detail: Context says "Yolo", plans use "YOLO". Cosmetic — resolve at implementation.
- **Color mapping inconsistency** (low)
  - Detail: Context says gray/blue/green/gold; plans hardcode red/amber/blue/green. Plans are more specific; context is aspirational.
- **`src/explorer/` doesn’t exist on branch** (expected)
  - Detail: Phase 10 creates those files. Plans reference future paths correctly.
- **localStorage fallback is export-only** (noted)
  - Detail: No import path — acceptable for v1; can add in a later phase.

None of these block merge. They’re plan-level inconsistencies that get resolved during Phase 11 execution.

### Learn (7/7)

**Summary:** PR #8 merge conflicts resolved via branch rebase. Now mergeable, awaiting automated checks (CodeRabbit, GitGuardian, Claude Review). Codex review found no blocking issues.

**Next:** Wait for checks to pass, then merge. You can resume Codex with `codex resume` for follow-up analysis.

**Obi:** PR #8 is now mergeable. Checks are running — once they pass, it’s ready to merge. Codex found only cosmetic plan-doc inconsistencies, nothing blocking.