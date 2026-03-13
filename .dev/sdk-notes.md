# Finance Guru SDK/TUI Notes (Stream Capture)

Date: 2026-02-19
Source: Live stream-of-consciousness product and architecture notes

## Follow-this checklist (single source of truth)

Use this checklist as the canonical tracker. The rest of this file is archived context.

### Status legend

- `[x]` done (decision or research complete)
- `[~]` blocked (cannot proceed yet)
- `[ ]` next (not done)

### Done so far

- [x] Decide custom tool architecture: SDK-native in-process MCP via `tool()` + `createSdkMcpServer()`.
- [x] Validate performance assumption: in-process MCP overhead is negligible relative to Python tool execution.
- [x] Decide startup architecture: SDK-driven startup flow (greeting, date context, portfolio snapshot, command center).
- [x] Define MCP integration direction for Finance Guru through the SDK-native tool architecture.

### Current blocker

- [~] Complete OpenTUI migration (this gates tool rollout and startup implementation work).

### Execution order (follow top to bottom)

#### Phase 1 - Unblock the runtime foundation

1. [ ] Migrate from Ink to OpenTUI baseline shell (layout, input loop, status line).
2. [ ] Implement OpenTUI interaction components needed immediately (`Select`, `TabSelect`, clean markdown rendering).
3. [ ] Unpause missing tools and wire them in: `AskUserQuestion`, `TodoWrite`, MCP resource tooling.

#### Phase 2 - Core user experience

4. [ ] Implement startup flow from the approved design (temporal context, greeting, portfolio snapshot, command center chooser).
5. [ ] Fix persona switching so the selected specialist fully owns responses and introduction.
6. [ ] Build onboarding fallback: if profile is missing, trigger onboarding immediately.
7. [ ] Set interactive mode as default launch mode.
8. [ ] Finalize menu UX progression (numeric baseline first, interactive controls second).
9. [ ] Upgrade markdown rendering path for clean, styled terminal output.

#### Phase 3 - Research and product polish

10. [ ] Query both notebooks and capture implementation guidance:
   - `OpenTUI Terminal User Interface Development Guide`
   - `master in the Anthropic Agent SDK for custom AI agents`
11. [ ] Run branding pass for logo and tagline (Haiku-inspired direction).
12. [ ] Run focused status-line design pass (minimal, balanced, power-user variants) and prototype in OpenTUI.

#### Phase 4 - Integrations, automation, and memory roadmap

13. [ ] Add Slack and Gmail integrations (read/search/send where appropriate).
14. [ ] Implement brokerage-email detection/extraction for execution intelligence.
15. [ ] Build buy-ticket confirmation loop (Gmail first, Plaid later).
16. [ ] Design always-on urgent triage mode with prioritized reminders.
17. [ ] Add scheduled cron workflows (daily summaries, roll reminders, opportunity alerts).
18. [ ] Define per-agent model routing policy by specialist role.
19. [ ] Design proactive memory-write rules for corrections/feedback.
20. [ ] Implement 3-tier memory architecture (session, persistent, archival) on Convex.
21. [ ] Add push notifications and real-time sync through Convex.
22. [ ] Research and prioritize Composio connectors (Gmail, Slack, GitHub, others) by impact.

## Archive: stream notes (reference)

- We are missing the `AskUserQuestion` tool. This is critical.
- We need the `TodoWrite` tool so tasks can be managed properly.
- We also need MCP resource tools in the workflow.
- Action: audit current `schema.yaml` tool list against required runtime capabilities.

## 2) Extend agents with custom tools

- Beyond built-in tools, we should add custom tools to extend agent reach into specialized Finance Guru domains.
- Use the `@tool` decorator to create Python/TypeScript functions that run as in-process MCP servers.
- This approach is ideal for controlled access to:
  - internal databases,
  - proprietary APIs,
  - and domain-specific logic that generic tools cannot handle securely/efficiently.
- Finance Guru includes proprietary Python-based tooling already.
- Open question: whether decorator-based wrapping materially improves speed/perf or mainly improves integration ergonomics.
- Action: run focused research/benchmark before making performance claims.

## 3) TUI framework direction: move from Ink to OpenTUI

- Current direction: move away from Ink and use OpenTUI instead.
- Reasoning:
  - OpenTUI has a versatile TypeScript library.
  - It supports sophisticated terminal UI development.
  - It aligns with Bun runtime usage.
- We already have a notebook for this:
  - `OpenTUI Terminal User Interface Development Guide`
- Action: use notebook skills to query that notebook for concrete implementation patterns.

## 4) MCP integration gap in Finance Guru

- Finance Guru relies on specific MCPs.
- Those MCPs are not incorporated into the workflow yet.
- Action: define and implement MCP integration map (required MCPs, startup checks, failure behavior, and UX fallbacks).

## 5) Launch defaults and branding exploration

- Default mode at Finance Guru launch should be interactive mode.
- We need to iterate on logo and tagline.
- Inspiration source: Haiku logo and tagline style.
- Action: run a dedicated brainstorming pass on brand direction options.

## 6) Agent switching UX/persona issue

- Observed behavior: when requesting a different specialist, Cassandra still answers.
- Desired behavior:
  - when user switches agent, response fully adopts selected agent persona,
  - selected agent introduces themselves clearly (as done historically inside Claude Code),
  - no lingering Cassandra voice unless Cassandra is explicitly active.
- This is primarily a UI/UX + routing/persona-state problem.

## 7) Menu design and interaction model

- We need to decide how menus are presented.
- Baseline approach (quick implementation): numbered list + numeric selection.
- Preferred approach (better UX): interactive selection controls.
- OpenTUI capabilities noted:
  - `Select` for vertical list selection,
  - `TabSelect` for horizontal selection.
- Potential combo:
  - pair selection components with `AskUserQuestion` so users can choose answers naturally.

## 8) Markdown rendering quality

- Current markdown rendering is not acceptable.
- Need better rendering so users do not see raw/ugly markdown symbols.
- From current understanding:
  - OpenTUI supports clean styled text rendering,
  - and has a dedicated markdown component for improved presentation.
- Action: research OpenTUI markdown rendering approach and integrate clean display path for Finance Guru responses.

## 9) Onboarding framework requirement (critical)

- Full onboarding framework needs to be built in.
- Current failure mode observed:
  - user asks "what is my name?",
  - system says it will pull profile,
  - no profile found and flow stalls.
- Desired behavior:
  - if profile/onboarding data is missing, immediately trigger onboarding flow.
  - explicit message example: "You haven't done onboarding. Let's get you onboarded."
  - then walk through full onboarding process.
- Action: run separate brainstorming task to define onboarding stages and desired data collected.

## 10) Desired startup experience (Claude Code parity)

- On launch, orchestrator should:
  - establish temporal context (run date checks),
  - greet user with identity,
  - display current date,
  - display portfolio snapshot,
  - show command center options (specialists, workflows, utilities),
  - let user choose directly from those options.
- These startup elements are considered essential, not optional.

## 11) Selection UX implementation options

- Option A: start with numeric menu input (simple, fast, low risk).
- Option B: interactive keyboard navigation (up/down and select).
- Option C: tab-based horizontal selectors for grouped workflows.
- Recommendation direction from notes: start simple, then upgrade to interactive controls quickly.

## 12) Notebook queries needed

- Notebook to query for TUI build details:
  - `OpenTUI Terminal User Interface Development Guide`
- Notebook to query for Anthropic SDK behavior:
  - `master in the Anthropic Agent SDK for custom AI agents`
- Specific question to resolve:
  - how does Anthropic render ask-user-question style interactions to end users?

## 13) Consolidated status list from this stream

- ~~Add missing tools: `AskUserQuestion`, `TodoWrite`, MCP resource tooling.~~ **PAUSED** — blocked on OpenTUI migration (Area 1). Revisit after TUI port.
- ~~Design and implement custom `@tool` wrappers for proprietary capabilities.~~ **DONE** — Decision finalized: SDK-native in-process MCP via `tool()` + `createSdkMcpServer()`. See `docs/brainstorms/2026-02-19-sdk-tool-architecture-brainstorm.md`.
- ~~Validate any performance assumptions around decorator-based tool wrapping.~~ **DONE** — In-process MCP has ~5-10ms overhead vs 500-3000ms Python execution. Negligible.
- Migrate UI framework direction from Ink to OpenTUI.
- ~~Implement Finance Guru-specific MCP integration in runtime workflow.~~ **DONE** — Architecture direction finalized and covered by SDK-native tool architecture. See brainstorm doc.
- Set interactive mode as default launch mode.
- Brainstorm and iterate logo + tagline inspired by Haiku direction.
- Fix persona switching so selected specialist fully owns responses.
- Redesign menu UX (numeric baseline, interactive evolution path).
- Upgrade markdown rendering with OpenTUI markdown/styled text components.
- Build onboarding detection + immediate onboarding flow when profile is missing.
- ~~Ensure startup includes greeting, date context, portfolio snapshot, and specialist/workflow/utility chooser.~~ **DONE** — Decision finalized: SDK-driven startup (Approach B). Implementation blocked on OpenTUI migration.
- Query both notebooks for implementation details and Anthropic rendering behavior.

### Brainstorm Decisions (2026-02-19)

- **Area 1 (Missing Tools):** PAUSED until OpenTUI migration complete
- **Area 2 (Custom Tool Wrappers): DONE** — SDK-native in-process MCP (Approach E). Bash removed from most agents. 3-layer observability (StatusBar, inline badge, /tools panel). Phase 1: wrap top 3 tools as proof-of-concept.
- **Area 3 (Startup Experience): DONE** — SDK-driven (Approach B). Agent generates greeting, date, portfolio, command center. Implementation blocked on OpenTUI migration.

## 14) Integration roadmap: communication and broker intelligence

- Add communication app integrations as first-class tools/workflows.
- Priority capabilities:
  - read/send Slack messages,
  - search and read Gmail,
  - detect brokerage-related emails and extract execution context.
- Core operating need: brokerages email reports and execution confirmations frequently; Finance Guru should ingest this signal automatically.

## 15) Buy-ticket execution feedback loop

- Problem: if Finance Guru generates a buy ticket, it still needs a reliable way to confirm execution status.
- Near-term source of truth:
  - Gmail brokerage confirmations (trade executed / partial fill / rejected / canceled).
- Future source of truth:
  - Plaid API integration for closer-to-real-time account/trade visibility.
- Direction: build execution-tracking workflow that starts with Gmail and later upgrades to Plaid-backed confirmation.

## 16) Always-on workflow + urgent triage

- Users may run options workflows that require rolling every 5-7 days.
- Finance Guru needs an "always-on" operating mode for monitoring and triage.
- Desired query pattern:
  - user asks what is urgent or forgotten,
  - agent returns prioritized urgent items and pending actions.
- System should help surface critical timing windows, not wait for manual prompting.

## 17) Scheduled automation and reminders

- Add built-in cron/scheduled workflows for daily and recurring tasks.
- Daily outputs should include:
  - summarized action items,
  - reminder alerts (example: "need to roll this option"),
  - opportunity alerts (example: potential low-price stock buy per strategy),
  - signal ideas to improve alpha generation.
- Direction: scheduled runs + actionable summaries + reminder delivery.

## 18) Agent model routing policy

- Different specialists should run on different model tiers.
- Requirement: support per-agent model assignment (example: some on Sonnet, some on Opus).
- Action: define role-to-model routing table balancing quality, latency, and cost.

## 19) Memory system upgrade (proactive + categorized)

- Current memory needs to be more advanced and proactive.
- Requirement: agent stores critical information, feedback, and corrections without explicit user instruction each time.
- Memory buckets:
  - Session memory: active/current interaction context.
  - Persistent memory: durable facts, references, portfolio state, selected strategies.
  - Archival memory: large reference corpora (example: full YouTube transcripts, Finance Guru method documents, deep knowledge assets).
- Direction: implement memory lifecycle and retrieval policies across all three buckets.

## 20) Convex-backed memory, automation, and sync

- Convex should be used as backend foundation for:
  - memory storage/retrieval,
  - real-time syncing,
  - cron jobs and automations.
- Add push-notification capabilities for urgent/important events.
- Future-proofing target:
  - if/when web app or desktop app exists, state and workflows sync through the same Convex backend.

## 21) Consolidated TODO list from this stream

- Add Slack and Gmail integrations with read/search/send workflows where appropriate.
- Implement brokerage-email detection and extraction pipeline for execution intelligence.
- Build buy-ticket execution confirmation loop (Gmail-first, Plaid-next).
- Design always-on urgent triage mode with prioritized reminders.
- Add scheduled cron workflows for daily summaries and options-roll reminders.
- Implement opportunity alerts aligned to strategy constraints.
- Define per-agent model routing policy (Sonnet vs Opus by specialist role).
- Design proactive memory-write rules for critical corrections and feedback.
- Implement 3-tier memory architecture (session, persistent, archival) using Convex.
- Add push notifications and real-time multi-surface sync via Convex.

## 22) TUI status line redesign (agent-aware + polished UX)

- Current status line shows:
  - session,
  - model,
  - turns,
  - cost.
- Keep these, but add explicit agent identity:
  - "Who am I speaking to right now?" should always be visible.
- Required status line fields moving forward:
  - session,
  - model,
  - turn count,
  - active agent/persona,
  - cost estimate (API cost visibility).
- Design intent: make the status line both highly informative and visually polished.

### Status line brainstorm directions

- Add visual emphasis to active agent name (distinct color/badge/icon).
- Show quick agent-switch indicator when persona changes.
- Consider compact vs expanded status modes for different terminal widths.
- Add urgency indicator when scheduled triage has pending items.
- Add sync/automation health indicators (example: cron active, memory sync healthy, MCP connected).
- Add lightweight notification count for reminders/alerts awaiting review.
- Ensure rendering stays clean and readable in OpenTUI (no clutter, no noisy separators).

### Follow-up action

- Run a focused brainstorming/design pass specifically for status-line UX variants (minimal, balanced, and power-user views), then prototype in OpenTUI.

## 23) External integrations via Composio

- Use Composio as the primary integration layer for external tools and services.
- Initial connector targets include:
  - Gmail,
  - Slack,
  - GitHub,
  - and similar productivity/ops systems.
- Direction: standardize external tool access through Composio-first patterns where feasible.
- Research task:
  - search and catalog relevant Composio tools/connectors that Finance Guru can utilize in future phases.
  - prioritize by impact (brokerage intelligence, workflow automation, communications, developer operations).
