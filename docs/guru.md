# Finance Guru Team CLI (`guru`)

This repo now ships a **thin wrapper** around the open-source **Overstory** orchestrator to give Finance Guru a _tmux-based persona team_.

You get:
- **`guru init`** → starts Cassandra Holt (the coordinator) in tmux
- **`guru quant` / `guru teacher` / …** → starts or attaches to a specific persona agent in tmux
- Agents coordinate via **Overstory mail** (SQLite-backed)

> Design intent: Cassandra _never does the work herself_ — she delegates to specialists.

---

## Prerequisites

You need these CLIs available in your PATH:

- `claude` (Claude Code)
- `tmux`
- `overstory`

### Install Overstory

Overstory is a separate project. Install it once on your machine.

Example (Bun):

```bash
git clone https://github.com/jayminwest/overstory
cd overstory
bun install
bun link
```

Confirm:
```bash
overstory --help
```

---

## Quick start

From the repo root:

```bash
./scripts/guru setup   # one-time: creates/normalizes .overstory config
./scripts/guru init    # starts Cassandra in tmux
```

In another terminal (or after detaching), start a persona agent:

```bash
./scripts/guru quant
```

---

## Commands

### `guru setup`
Idempotent. Ensures `.overstory/` exists and is configured for Finance Guru.

Important configuration choices:
- `beads.enabled=false` (no `bd` dependency)
- `mulch.enabled=false` (no `mulch` dependency)

### `guru init`
Starts the **Overstory coordinator** tmux session, but with a Finance Guru system prompt so the coordinator behaves as **Cassandra Holt**.

Coordinator tmux session name:
- `overstory-finance-guru-coordinator`

### `guru attach`
Attach to Cassandra’s tmux session.

### `guru quant|teacher|analyst|market|strategy|compliance|builder|qa`
Spawns a persona session as an Overstory worker and attaches to it.

Notes:
- Workers are spawned with Overstory capability `builder` so they can write artifacts.
- Overstory will create git worktrees under `.overstory/worktrees/`.
- These commands pass `--force-hierarchy` so you can start a specialist directly without going through Cassandra.

### `guru status`
Shows active Overstory sessions.

### `guru stop [coordinator|all]`
Stops Cassandra or cleans up everything.

### `guru mail ...`
Pass-through to `overstory mail ...`.

Examples:
```bash
./scripts/guru mail check --inject --agent coordinator
./scripts/guru mail send --to coordinator --subject "help" --body "need guidance"
```

---

## How delegation works (recommended pattern)

1) You chat with Cassandra in the `guru init` session.
2) Cassandra clarifies intent + constraints.
3) Cassandra delegates to specialists by messaging them (or instructing a lead to spawn them).

Today, the wrapper gives you the tmux lifecycle + persona bootstraps. The next iteration is to add:
- a `fg-lead` auto-spawn
- a standard “dispatch protocol” message format

---

## Troubleshooting

### “Missing dependency: overstory/tmux/claude”
Install the missing tool and retry.

### tmux attach fails / session not found
Run:
```bash
./scripts/guru status
```
And/or list tmux sessions:
```bash
tmux ls
```

### Where are the Overstory files?
They live in:
- `.overstory/` (config + agent prompts + runtime dbs)
- `.overstory/worktrees/` (per-agent git worktrees)

---

## Security notes

- Finance Guru private data lives in `fin-guru-private/`. Treat it as sensitive.
- The coordinator prompt explicitly instructs agents not to leak private info.

---

## Philosophy

Slash commands are fine as a UI. This wrapper makes them optional.

The _real_ API is: **spawn persona agents, delegate, and produce artifacts** — with tmux sessions you can attach to whenever you want.
