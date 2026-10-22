---
title: "Hooks"
description: "The Claude Code hooks the plugin ships and what each one does"
category: reference
---

# Hooks

A checkout-mode instance owns its settings and runs one SessionStart hook,
derived from the product manifest in `hooks/hooks.json`. Plugin mode runs that
same product hook from the installed plugin. The engine repository wires four
hooks for development. Bun must be installed before starting an agent session.
The PR gate runs before every repository Bash tool call.

| Event | Script | Runs in | What it does |
| --- | --- | --- | --- |
| `SessionStart` | `.claude/hooks/load-fin-core-config.ts` | Instances, plugin and repository | Prints the `fin-core` skill, the instance profile and configuration, and the ledger's last balance sync. Prints nothing outside an instance. |
| `PreToolUse` | `.dev/pr-kit/open-pr/gate.ts` | Repository only | Checks PR commands and blocks a failed or unavailable gate. |
| `PostToolUse` | `.claude/hooks/post-tool-use-tracker.ts` | Repository only | Records tool use for the stop check. |
| `Stop` | `.claude/hooks/stop-build-check-enhanced.sh` | Repository only | Runs the build check before the session ends. |

The canonical kit uses its developer layout. Its unchanged payload lives in
`.dev/pr-kit`, with explicit repository instruction and hook references. It
does not add developer skills to `.claude/skills` or the finance plugin manifest.
Checkout instances share finance assets through links and own their settings.
They never inherit the repository PR gate, tool tracker, or build hook.

## Personal plugins

The committed `.claude/settings.json` wires the repository hooks in the table above. Instances own their settings and do not inherit this file.

Enable a personal plugin for yourself in user settings at `~/.claude/settings.json`. That file stays on your machine and applies across your projects. To enable one for this checkout or instance alone, put the same block in its `.claude/settings.local.json`. Git ignores that file, so the opt-in stays on your machine. The official iMessage plugin looks like this:

```json
{
  "enabledPlugins": {
    "imessage@claude-plugins-official": true
  }
}
```

These commands write that entry. The shell command does not prompt for a scope, so pass one:

```bash
claude plugin enable imessage@claude-plugins-official --scope user
claude plugin enable imessage@claude-plugins-official --scope local
```

`--scope user` writes `~/.claude/settings.json`, which applies across your projects. `--scope local` writes `.claude/settings.local.json` for the current checkout or instance. Without `--scope`, the command uses the most specific settings file that already mentions the plugin, checking local, then project, then user. A project declaration selects that directory's `.claude/settings.json`. A user declaration selects `~/.claude/settings.json` and applies the plugin in every project.

The session-start hook resolves the instance the same way the engine does: `FIN_GURU_DATA_ROOT`, else the directory you start the session in. It treats the session directory as an instance only when it holds `user-profile.yaml` plus a Finance Guru marker, the scaffolded `pyproject.toml` or `family_office.db`, so a plugin installed at user scope stays silent in every other repo. A root named in `FIN_GURU_DATA_ROOT` needs only `user-profile.yaml`. When a checkout runs its own copy through `.claude/settings.json`, the plugin copy steps aside, so the hook runs once. Skills load from each `SKILL.md` description, so no hook routes prompts to skills. The hooks are not required to run the Python analysis engine from a shell.
