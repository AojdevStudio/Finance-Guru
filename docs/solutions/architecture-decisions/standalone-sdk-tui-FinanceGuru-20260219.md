---
module: Finance Guru
date: 2026-02-19
problem_type: architecture_decision
component: standalone_cli
symptoms:
  - "Finance Guru coupled to PAI monorepo runtime conventions"
  - "No independent CLI — requires Claude Code session with hooks/skills"
  - "BMAD-CORE XML agent format not portable outside .claude/commands/"
root_cause: architectural_coupling
severity: high
tags: [sdk, standalone, ink, tui, architecture, agent-sdk, decoupling]
---

# Standalone Finance Guru via Anthropic Agent SDK

## Context

Finance Guru v2.0 was a mature 11-agent financial system running inside the PAI monorepo as Claude Code skills/commands/hooks. While it had zero _code_ dependencies on PAI, it was coupled to:
- BMAD-CORE XML format for agent definitions
- `.claude/commands/` layout for agent routing
- PAI hooks system for session management
- User's `~/.claude/` global config (hooks, skills, CLAUDE.md)

## Decision

Build Finance Guru as a **standalone TypeScript CLI** using the `@anthropic-ai/claude-code` SDK (the same runtime Claude Code uses internally). Key decisions:

1. **YAML agent definitions** — Convert all 11 agents from BMAD-CORE XML to portable YAML. A TypeScript loader compiles them to `AgentDefinition` objects at runtime.

2. **Bash tool for Python CLIs** — Agents use the built-in `Bash` tool to run `uv run python tools/src/...` directly. No MCP tool wrappers needed.

3. **Config isolation via `setting-sources: "project"`** — Passes `extraArgs: { "setting-sources": "project" }` to the SDK, preventing inheritance of the user's global `~/.claude/` hooks and skills. This was critical for preventing PAI format leakage.

4. **Interactive Ink TUI** — React + Ink for a branded chat-first terminal interface. Multi-turn via `AsyncIterable<SDKUserMessage>` prompt input to `query()`.

5. **Default-deny Bash allowlist** — `PreToolUse` hook only allows Python CLI tools, `date`, and read-only inspection commands. Blocks `curl`, `ssh`, `git`, `env`, pipes, redirects.

6. **Model shorthand resolution** — Maps `opus`→`claude-opus-4-6`, `sonnet`→`claude-sonnet-4-6`, `haiku`→`claude-haiku-4-5-20251001` since the SDK needs full model IDs.

## What Was Built

### Location
`/Users/ossieirondi/Documents/Irondi-Household/fin-guru/` (separate repo from family-office)

### Structure
```
fin-guru/
  agents/              — 11 YAML agent definitions + schema + defaults
  src/                 — 6 TypeScript runtime files
    tui/               — Ink TUI components and hooks
      components/      — Header, ChatMessage, InputBar, StatusBar, etc.
      hooks/           — useSession (SDK bridge)
  tools/src/           — Python CLI tools (unmodified copy from family-office/src/)
  knowledge/           — Data, tasks, templates, checklists
  bin/fin-guru         — Shell entry (symlinked as `guru`)
  tests/               — 123 agent schema + hook security tests
  .memory/             — Session persistence (gitignored)
```

### Completed Phases

| Phase | Status | What |
|-------|--------|------|
| **Phase 1: Foundation** | DONE | YAML agents, TS runtime, package.json, tsconfig, .gitignore, CLAUDE.md, bin/fin-guru, pyproject.toml, 123 tests |
| **Phase 2: Chat Interface** | DONE | Header, WelcomeScreen, ChatMessage, AgentBadge, InputBar, StatusBar components |
| **Phase 3: SDK Integration** | DONE | useSession hook with AsyncIterable bridge, streaming tokens, session capture |
| **Phase 4: CLI Integration** | DONE | `--interactive`/`-i` flag, `--no-banner`, `guru` alias (symlink-safe), headless mode preserved |
| **Phase 5: Polish** | DONE | Slash commands (/help, /model, /cost, /sessions, /exit), Ctrl+C interrupt, Ctrl+D exit, error handling (max_turns, execution errors), compaction notices, 30fps token batching for anti-flicker |

### Key Files Created

| File | Purpose |
|------|---------|
| `agents/*.yaml` (11 + 2) | Portable agent definitions (source of truth) |
| `src/orchestrator.ts` | SDK query runner with `buildQueryOptions()` + `loadSDK()` |
| `src/agent-loader.ts` | YAML → AgentDefinition compiler |
| `src/hooks.ts` | Default-deny Bash allowlist + PreCompact archive |
| `src/memory.ts` | Session persistence + memory tool handler |
| `src/types.ts` | TypeScript interfaces for YAML schema |
| `src/index.ts` | CLI entry with headless + interactive modes |
| `src/tui/App.tsx` | Root Ink component with slash command handling |
| `src/tui/hooks/useSession.ts` | SDK↔React bridge via push-based AsyncIterable |
| `src/tui/components/*.tsx` | 6 branded UI components |
| `src/tui/theme.ts` | Brand colors, agent color map |
| `tests/agent-schema.test.ts` | 123 tests (schema, loader, hooks) |

### Verified Working

- `guru` — launches interactive TUI from anywhere
- `guru "analyze TSLA risk"` — headless mode from anywhere
- `guru --help`, `guru --sessions` — CLI commands work
- 123 bun tests pass
- No PAI references in agents/ or src/
- No hardcoded user paths
- No BMAD-CORE XML tags
- Config isolation prevents PAI hook leakage

## Bugs Found and Fixed

1. **Model ID format** — SDK needs `claude-sonnet-4-6`, not `sonnet`. Added `MODEL_MAP` resolver.
2. **extraArgs key format** — SDK prepends `--` to keys, so `"setting-sources"` not `"--setting-sources"`.
3. **Path resolution via symlink** — `$(dirname "$0")` resolves to symlink dir, not real dir. Fixed with `readlink` loop in bin/fin-guru.
4. **`process.cwd()` assumption** — orchestrator and memory used cwd for project root. Fixed with `import.meta.url` resolution.
5. **Streaming flicker** — Per-token setState caused excessive Ink re-renders. Fixed with 33ms (~30fps) batched flush.

## Release Strategy (NOT YET DECIDED)

**Open questions:**
- Should this be a breaking change on the existing AojdevStudio/Finance-Guru repo?
- Or should it be a separate repo entirely?
- Extensive user testing needed before declaring it replaces BMAD v6 architecture
- The `guru` command must prove itself over weeks of daily use before migration

**Recommendation:** Keep as a separate directory for now. Test daily. When confidence is high, either:
1. Release as v3.0.0 on Finance-Guru repo (breaking change, new architecture)
2. Create a new repo `fin-guru-sdk` and archive the BMAD agents in the original

## Prevention / Lessons Learned

1. **Always test SDK calls before giving commands to the user** — the model ID and extraArgs bugs would have been caught immediately.
2. **`setting-sources` is the key to SDK isolation** — without it, the subprocess inherits ALL global Claude Code config.
3. **The NotebookLM CLI (`nlm`) is valuable for SDK research** — the "Mastering the Anthropic Agent SDK" notebook had the answer about `setting_sources` that wasn't in the SDK docs.
4. **Symlinks break relative paths** — always resolve the real path in shell scripts.
5. **`process.cwd()` is not project root** — use `import.meta.url` for portable path resolution.

## Related

- Brainstorm: `docs/brainstorms/2026-02-18-tui-framework-brainstorm.md`
- Plan: `docs/plans/2026-02-18-feat-interactive-ink-tui-plan.md`
- SDK types: `node_modules/@anthropic-ai/claude-code/sdk.d.ts`
- Ossie's notes: `.dev/sdk-notes.md`
