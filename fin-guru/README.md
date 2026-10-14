# fin-guru

The shared material the specialist personas and skills read at runtime. The specialist agents live in `.claude/agents/`; this directory holds what they load.

| Path | What it holds | Who reads it |
| --- | --- | --- |
| `data/` | The knowledge base: definitions, the risk framework, hedging strategies, income vehicles, and the compliance policy. | Personas and skills on demand. `just check-definitions` keeps `definitions.md` in sync with `src/` constants. |
| `tasks/` | Step-by-step task definitions such as `load-portfolio-context.md` and `create-doc.md`. | Personas when a command maps to a task. |
| `templates/` | Analysis report, buy ticket, compliance memo, income strategy, and Excel model spec templates. | The builder persona and `fin-guru-create-doc`. |
| `checklists/` | Margin strategy, dividend framework, and cash-flow policy. | `fin-guru-checklist`, the strategy advisor, and the specialists who apply those policies. |

Private values never live here. Instance files such as `user-profile.yaml`, `system-context.md`, and `family_office.db` resolve from `FIN_GURU_DATA_ROOT` or the current directory. See [AGENTS.md](../AGENTS.md) for the operating rules.
