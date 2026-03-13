---
date: 2026-02-20
topic: selection-ux-interaction-spec
---

# Selection UX Interaction Spec

## What We're Building
Finance Guru will use keyboard-interactive selection as the default menu interaction model in the TUI. The default behavior is option B: directional navigation with explicit selection confirmation, tuned for polish and consistency across all menu surfaces.

This spec defines the canonical keymap, focus behavior, visual states, error handling, accessibility expectations, and acceptance criteria so implementation can proceed without ambiguity.

## Why This Approach
We considered three options: numeric-only menus, keyboard-interactive menus, and mixed/horizontal tab-first controls. Numeric-only is fast but low polish. Tab-first everywhere adds complexity too early. Keyboard-interactive by default gives the best immediate UX quality while keeping implementation risk manageable if we centralize behavior in one selection engine.

## Key Decisions
- Default interaction is keyboard navigation (`Up`/`Down` + `Enter`) because this optimizes polish and speed for frequent use.
- Numeric input remains available as recovery fallback only, not primary UX, to preserve reliability in edge terminals.
- `TabSelect` is scoped to top-level grouped navigation (Agents, Workflows, Utilities), while regular list selection uses vertical `Select`.
- Focus behavior is deterministic and stateful: users should always know what is selected and where input focus is.

## Interaction Rules

### Global Keymap
- `Up` / `k`: move selection up one item.
- `Down` / `j`: move selection down one item.
- `Enter`: confirm current selection.
- `Esc`: cancel current menu layer and return to previous context.
- `Tab` / `Shift+Tab`: move between top-level groups when group tabs are present.
- `1-9`: numeric emergency fallback select (hidden hint, not primary prompt).
- `q` or `Ctrl+C`: quit only from root shell/menu states, never during critical confirmation prompts.

### Navigation Semantics
- Selection wraps at list boundaries (last -> first, first -> last).
- Disabled items are skipped during keyboard navigation and cannot be selected.
- If all items are disabled, selection is unset and `Enter` is no-op with inline guidance.
- Multi-column layouts must preserve one active item model, not per-column independent focus.

### Confirmation Semantics
- `Enter` executes only the currently highlighted actionable item.
- Confirmation prompts use explicit two-choice selection with default set to safest non-destructive action.
- Destructive actions require an additional explicit confirmation step (no single-key destructive execution).

## Focus Management

### Initial Focus
- On menu mount, focus first enabled item unless a valid previous selection exists for that menu key.
- If a previous selection exists and remains enabled, restore it.

### Focus Persistence
- Preserve last selected item per menu context key (example: `root.agents`, `root.workflows`).
- On data refresh/rerender, preserve current selection by stable item ID.
- If selected ID disappears, fallback to nearest enabled sibling; if none, first enabled item.

### Post-Action Focus
- After non-navigational action completion, return focus to invoking menu context.
- After agent switch, focus remains on agent-switch surface only until selection is acknowledged.
- Streaming responses never steal focus from an active menu.

## Visual and UX Polish Rules
- Active item has high-contrast highlight and optional agent/workflow badge.
- Non-active items remain readable with clear contrast hierarchy.
- Disabled items are visually distinct and include reason text on focus.
- Key hint strip is always visible for active selection surfaces.
- Avoid flicker by batching UI updates and preventing full-menu rerender on token stream updates.
- Status line should reflect active agent and current interaction mode.

## Error and Edge States
- Unknown key input: ignored silently unless in text-entry mode.
- Empty menu: render explicit empty-state message with next-step action.
- Data fetch failure: show inline retry action and fallback command path.
- Terminal capability downgrade: switch to numeric fallback mode with visible notice.

## Accessibility and Input Compatibility
- Full keyboard-only operation is required.
- Vim aliases (`j/k`) are supported in addition to arrow keys.
- Behavior must be consistent across common terminal emulators and SSH sessions.
- Color cannot be the only state indicator; selected item also uses prefix marker/symbol.

## Telemetry and Diagnostics (Dev)
- Capture selection latency (first keypress to confirmed action).
- Capture focus-loss events and forced fallback mode transitions.
- Log menu context key, selected item ID, and action outcome for debug builds.

## Acceptance Criteria
1. User can complete core navigation (switch agent, open workflow, execute action) with keyboard only and no numeric input.
2. Focus remains stable across streaming updates and rerenders.
3. Disabled and empty states behave deterministically and never allow invalid execution.
4. `TabSelect` works only for grouped top-level navigation and does not conflict with vertical selection.
5. Numeric fallback works when interactive mode degrades, with clear mode indicator.
6. No visible flicker under normal streaming response rates.

## Out of Scope (This Pass)
- Mouse interaction support.
- Multi-select checklist flows.
- Custom keybinding remapping UI.

## Open Questions
- Should wrap navigation be configurable (`wrap=true/false`) for power users?
- Should `h/l` be added for group tab movement in addition to `Tab`?
- What exact fallback trigger threshold should switch from interactive to numeric mode?

## Next Steps
1. Build a shared selection controller/state machine in the TUI layer.
2. Implement OpenTUI `Select` with this keymap and focus lifecycle.
3. Add top-level `TabSelect` integration for grouped navigation only.
4. Add regression tests for focus persistence, disabled-item behavior, and fallback mode.
5. Run manual UX pass in narrow and wide terminal widths before default enablement.
