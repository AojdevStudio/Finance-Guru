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

The session-start hook resolves the instance the same way the engine does: `FIN_GURU_DATA_ROOT`, else the directory you start the session in. It treats a directory as an instance when it holds `user-profile.yaml` or `config.yaml`, so a plugin installed at user scope stays silent in every other session. When a checkout runs its own copy through `.claude/settings.json`, the plugin copy steps aside, so the hook runs once. Skills load from each `SKILL.md` description, so no hook routes prompts to skills. The hooks are not required to run the Python analysis engine from a shell.
