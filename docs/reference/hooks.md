---
title: "Hooks"
description: "The Claude Code hooks the plugin ships and what each one does"
category: reference
---

# Hooks

A checkout-mode instance runs the three hooks that `.claude/settings.json` wires, through its `.claude` symlink. The plugin ships only the session-start hook, in `hooks/hooks.json`. The other two serve work on the engine repository itself.

| Event | Script | What it does |
| --- | --- | --- |
| `SessionStart` | `.claude/hooks/load-fin-core-config.ts` | Prints the `fin-core` skill, the instance profile and configuration, and the ledger's last balance sync. Prints nothing outside an instance. |
| `PostToolUse` | `.claude/hooks/post-tool-use-tracker.ts` | Records tool use for the stop check. |
| `Stop` | `.claude/hooks/stop-build-check-enhanced.sh` | Runs the build check before the session ends. |

## Personal plugins

The committed `.claude/settings.json` wires the shared hooks in the table above. A checkout-mode instance inherits that file through its `.claude` symlink, so a plugin listed there turns on for every checkout.

Enable a personal plugin for yourself in user settings at `~/.claude/settings.json`. That file stays on your machine and applies across your projects. To enable one for this checkout alone, put the same block in `.claude/settings.local.json`. Git ignores that file, so the opt-in stays on your machine and on the instances that symlink this checkout. The official iMessage plugin looks like this:

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

`--scope user` writes `~/.claude/settings.json`, which applies across your projects. `--scope local` writes `.claude/settings.local.json` for this checkout. Without `--scope`, the command uses the most specific settings file that already mentions the plugin, checking local, then project, then user. A project declaration selects the shared `.claude/settings.json`, which every checkout-mode instance inherits. A user declaration selects `~/.claude/settings.json` and applies the plugin in every project.

The session-start hook resolves the instance the same way the engine does: `FIN_GURU_DATA_ROOT`, else the directory you start the session in. It treats the session directory as an instance only when it holds `user-profile.yaml` plus a Finance Guru marker, the scaffolded `pyproject.toml` or `family_office.db`, so a plugin installed at user scope stays silent in every other repo. A root named in `FIN_GURU_DATA_ROOT` needs only `user-profile.yaml`. When a checkout runs its own copy through `.claude/settings.json`, the plugin copy steps aside, so the hook runs once. Skills load from each `SKILL.md` description, so no hook routes prompts to skills. The hooks are not required to run the Python analysis engine from a shell.
