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

---

## Docs follow-ups (hooks + onboarding + reference updates)

### Hooks docs (`docs/reference/hooks.md`)

- After we finish the GSD plan, we need a focused brainstorming pass on **the “hook system” direction**.
  - Likely moving beyond running inside Claude Code and toward the **Claude Agents SDK**.
  - Hooks need to be designed/implemented so they can work in both contexts (or have a clean compatibility layer).
- Even within Claude Code, ensure hooks are actually “proper”.
  - **Most likely keeper**: the **session start** hook that loads the **core configs**.
  - Everything else likely needs to change:
    - adopt / align with **Pi/PAI-related hooks**
    - re-think hook lifecycle/events and how they map to Agents SDK callbacks

### Reference docs that need refresh

- **API references**: update `docs/reference/api.md`
- **Available tools references**: update `docs/reference/tools.md`

### CSV mappings (missing brokers)

The `docs/csv-mappings/` coverage is missing several common brokers. We need example exports so we can map headers/fields correctly.

- Add mappings for:
  - **M1 Finance**
  - **Ally** (Ally Invest)
  - **SoFi**
  - **Public** (Public.com)
- Action needed: collect sample CSV exports for each broker (positions + transactions if applicable), then create/update mapping JSONs.

### Reports cleanup / archiving

- Under `docs/reports/`, we can likely **archive or remove** `docs/reports/codex-full-review-report.md` (keep it somewhere “historical” if we still want it).

### Manual test checklist extension

- Extend the manual checklist after we build everything:
  - File: `docs/reports/MANUAL_TEST_CHECKLIST.md`

### Setup docs updates

- Update these as the system evolves:
  - `docs/setup/api-keys.md`
  - `docs/setup/SETUP.md`
  - `docs/setup/TROUBLESHOOTING.md`



    Best PAI skills for this build, in recommended order:

  Tier 1: Architecture & Design (use first)

  1. /brainstorming (compound-engineering)
  Explore the TUI framework choice before committing. The key decision is:
  - Ink (React for terminals) — component-based, styled, layout engine, TS-native
  - Blessed-contrib — lower-level curses, more control, less ergonomic
  - Raw ANSI + Inquirer — lightest weight, no framework dependency

  This skill walks through user intent, tradeoffs, and design decisions before planning.

  2. /CreateCLI
  Generates TypeScript CLI structure with proper arg parsing, command routing, and project scaffolding. Would create the bin entry, command structure, and
  interactive mode scaffolding.

  3. BrandGuidelines
  Defines the Finance Guru terminal color palette, text styling conventions, and visual identity rules for the TUI. Think: accent color for Cassandra,
  specialist-specific colors, panel borders, logo treatment.

  Tier 2: Implementation Planning

  4. /compound-engineering:workflows:plan
  Transforms the TUI feature description into a structured project plan with tasks, phases, and verification.

  5. RepoArchitect
  Structures the TUI code within the existing fin-guru standalone repo — where components live, how the Ink render tree maps to the agent system.

  Tier 3: Build & Polish

  6. /compound-engineering:frontend-design
  Despite saying "frontend", this skill produces distinctive, polished interfaces. For a TUI, it'd drive the visual design: panel layouts, animation timing,
  color harmony, typography (which matters even in terminals).

  7. Agents (PAI custom agents)
  Could compose custom rendering agents — one that handles the streaming chat view, one that handles the menu system, one that handles the
  specialist-switcher panel.

  8. BeCreative (extended thinking)
  Deep design thinking for the interaction model: How does streaming SDK output map to the TUI? How do tool-use permission prompts surface? How does the menu
   coexist with the chat?. Use the art skill to generate the banner once (FIGlet-style), then print it with ANSI color

  Recommended Architecture

  ┌─────────────────────────────────────────────┐
  │  🎯 Finance Guru v3.0                       │
  │  ─────────────────────────────────────────── │
  │                                              │
  │  Cassandra Holt, Master Portfolio            │
  │  Orchestrator                                │
  │                                              │
  │  Welcome to your private Finance Guru        │
  │  family office. How can I help today?        │
  │                                              │
  │  ┌──────────────────────────────────────┐    │
  │  │ 1. Market Research  (Dr. Petrov)     │    │
  │  │ 2. Quant Analysis   (Dr. Desai)     │    │
  │  │ 3. Strategy         (Rodriguez-Park) │    │
  │  │ 4. Compliance       (Marcus Allen)   │    │
  │  │ 5. Margin           (Richard Chen)   │    │
  │  │ 6. Dividends        (Sarah Martinez) │    │
  │  │ 7. Learn            (Maya Brooks)    │    │
  │  │ 8. Free-form prompt                  │    │
  │  └──────────────────────────────────────┘    │
  │                                              │
  │  > _                                         │
  └─────────────────────────────────────────────┘

  Framework Recommendation: Ink (React for terminals)

  - ink + ink-text-input + ink-select-input + ink-spinner
  - Component-based: <ChatView>, <MenuPanel>, <AgentHeader>, <StreamingResponse>
  - SDK query() runs async, Ink re-renders as tokens stream
  - TS-native, works with Bun, fits the existing stack perfectly
  - Used by Vercel CLI, Gatsby CLI, Prisma — battle-tested

  Recommended Skill Sequence

  /brainstorming          → Framework choice + interaction model
  /CreateCLI              → Scaffold interactive CLI structure
  BrandGuidelines         → Define terminal color/style system
  /plan                   → Full implementation plan
  /frontend-design        → Visual design for each TUI screen
  BeCreative              → Deep think on streaming UX + menus
  Build                   → Ink components wired to SDK query()

  🗣️ Obi: Start with brainstorming for framework choice, then CreateCLI for scaffolding, BrandGuidelines for visual identity, and Ink for the React-based
  terminal UI.
