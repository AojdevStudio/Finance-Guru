@AGENTS.md

## Claude Code

- Ask the owner a question only through the `AskUserQuestion` tool.
- The plugin install path is `claude plugin marketplace add AojdevStudio/Finance-Guru` then `claude plugin install finance-guru@finance-guru`. The plugin is the source of agents, skills, and hooks for a plugin-mode instance. The checkout path in the README stays fully supported.
- `.claude/settings.json` wires four hooks for a checkout. The plugin ships only `load-fin-core-config.ts`, through `hooks/hooks.json`. That hook loads the instance profile and portfolio files at session start from `FIN_GURU_DATA_ROOT` or the session directory, and prints nothing outside an instance. `skill-activation-prompt.ts` suggests skills from `.claude/skills/skill-rules.json`. The other two track tool use and run the build check on stop. `docs/reference/hooks.md` describes their status.
- `src/CLAUDE.md` loads on its own when you work under `src/`.
