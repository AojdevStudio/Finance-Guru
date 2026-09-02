---
title: "Hooks"
description: "The Claude Code hooks the plugin ships and what each one does"
category: reference
---

# Hooks

`.claude/settings.json` wires four hooks. The plugin ships the same four, so a plugin-mode instance and a checkout run identical hooks.

| Event | Script | What it does |
| --- | --- | --- |
| `SessionStart` | `.claude/hooks/load-fin-core-config.ts` | Prints the `fin-core` skill, then the instance profile, configuration, and latest portfolio files from `FIN_GURU_DATA_ROOT` or the current directory. Warns when the instance files are missing. |
| `UserPromptSubmit` | `.claude/hooks/skill-activation-prompt.ts` | Matches the prompt against `.claude/skills/skill-rules.json` and suggests the matching skill. |
| `PostToolUse` | `.claude/hooks/post-tool-use-tracker.ts` | Records tool use for the stop check. |
| `Stop` | `.claude/hooks/stop-build-check-enhanced.sh` | Runs the build check before the session ends. |

Start sessions from the instance directory, or export `FIN_GURU_DATA_ROOT`, so the session-start hook finds the instance files. The hooks are not required to run the Python analysis engine from a shell.
