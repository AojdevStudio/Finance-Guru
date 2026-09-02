# fin-guru

The shared material the specialist personas and skills read at runtime. The personas that Claude Code and Codex run live in `.claude/commands/fin-guru/agents/`; this directory holds what they load.

| Path | What it holds | Who reads it |
| --- | --- | --- |
| `config.yaml` | Module paths, the agent roster, and the workflow pipeline. | Every persona at activation. |
| `data/` | The knowledge base: definitions, margin and dividend frameworks, hedging strategies, income vehicles, the compliance policy, and `guru-kb.md`. | Personas and skills on demand. `just check-definitions` keeps `definitions.md` in sync with `src/` constants. |
| `framework/` | Directives, routing, knowledge-base index, and tool modes as YAML. | The finance orchestrator when it routes a request. |
| `tasks/` | Step-by-step task definitions such as `load-portfolio-context.md` and `create-doc.md`. | Personas when a command maps to a task. |
| `templates/` | Analysis report, buy ticket, compliance memo, income strategy, and Excel model spec templates. | The builder persona and `fin-guru-create-doc`. |
| `checklists/` | Analyst, cash-flow, dividend, and margin checklists. | `fin-guru-checklist` and the compliance officer. |
| `agents/` | The source persona definitions the `.claude/commands/` files were built from, plus `agent-template.md`. | Maintainers when editing a persona. |
| `_module-installer/`, `workflows/`, `DISTRIBUTION-PLAN.md` | Module metadata from the earlier framework-based packaging. | Nothing at runtime. |

Private values never live here. Instance files such as `user-profile.yaml`, `system-context.md`, and `family_office.db` resolve from `FIN_GURU_DATA_ROOT` or the current directory. See [AGENTS.md](../AGENTS.md) for the operating rules.
