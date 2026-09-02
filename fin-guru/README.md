# fin-guru

The shared material the specialist personas and skills read at runtime. The personas live in `.claude/commands/fin-guru/agents/` and `.claude/agents/`; this directory holds what they load.

| Path | What it holds | Who reads it |
| --- | --- | --- |
| `data/` | The knowledge base: definitions, margin and dividend frameworks, hedging strategies, income vehicles, the compliance policy, and `guru-kb.md`. | Personas and skills on demand. `just check-definitions` keeps `definitions.md` in sync with `src/` constants. |
| `tasks/` | Step-by-step task definitions such as `load-portfolio-context.md` and `create-doc.md`. | Personas when a command maps to a task. |
| `templates/` | Analysis report, buy ticket, compliance memo, income strategy, and Excel model spec templates. | The builder persona and `fin-guru-create-doc`. |
| `checklists/` | Analyst, cash-flow, dividend, and margin checklists. | `fin-guru-checklist` and the compliance officer. |

Private values never live here. Instance files such as `user-profile.yaml`, `system-context.md`, and `family_office.db` resolve from `FIN_GURU_DATA_ROOT` or the current directory. See [AGENTS.md](../AGENTS.md) for the operating rules.
