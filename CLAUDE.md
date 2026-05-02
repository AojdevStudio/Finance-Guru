# Finance Guru v1

Private AI family office on BMAD-CORE™ v6. **Claude Code only** — uses `AskUserQuestion` for user prompts.

This IS Finance Guru, not a product. Use _your_ when discussing assets, strategies, portfolios.

## Distinguishing this repo

- **This repo** (`AojdevStudio/Finance-Guru`) = **v1**, the AGPL Python toolkit + Claude Code agent harness. Active, this is where work has historically happened.
- **KeepFolio** (`AojdevStudio/Finance-Guru-v2`, private) = the commercial Tauri/React desktop app on `pi-mono` (model- and harness-agnostic). Different repo, different runtime, do not conflate.

## Architecture

- Multi-agent system: Claude → specialized financial agents.
- Entry point: Finance Orchestrator (Cassandra Holt) — `.claude/commands/fin-guru/agents/finance-orchestrator.md`.
- Agents must establish temporal context at startup: `date` and `date +"%Y-%m-%d"`.
- Path variables in agent configs: `{project-root}`, `{module-path}`, `{current_datetime}`, `{current_date}`, `{user_name}`.
- Subsystem context: see `./src/CLAUDE.md` for the Python toolkit's 3-layer pattern, conventions, and gotchas.

## Stack pointers

- Python 3.12+, `uv` for everything Python — see `pyproject.toml` for deps.
- Bun/TypeScript apps under `apps/` (managed by `turbo.json`) — current apps: `plaid-dashboard`, `simplefin-sync`.
- Required MCP servers: `exa`, `bright-data`, `sequential-thinking`, `financial-datasets`, `gdrive`, `web-search`.
- Skills are auto-loaded by the SessionStart hook from `.claude/skills/` — `ls .claude/skills/` for the live list. Read full SKILL.md before invoking.

## Tool discovery

- All financial CLIs live under `src/analysis/`, `src/strategies/`, `src/utils/` as `*_cli.py`.
- `ls src/**/*_cli.py` for the live inventory; every CLI supports `--help` for full flag reference.
- All follow the 3-layer pattern: Pydantic Models → Calculator → CLI. See `notebooks/tools-needed/type-safety-strategy.md`.

## Quality gates

```bash
uv run pytest                    # tests (skip API tests with -m "not integration")
uv run ruff format . && uv run ruff check .
uv run mypy src/
just --list                      # see all justfile recipes
```

## Output paths

- Analysis artifacts: `fin-guru-private/fin-guru/analysis/{topic}-{YYYY-MM-DD}.md`
- Buy tickets: `fin-guru-private/fin-guru/tickets/buy-ticket-{YYYY-MM-DD}-{descriptor}.md`
- Strategies: `{strategy}-master-strategy.md`
- All outputs: markdown + YAML frontmatter, date-stamped, with educational-only disclaimer, "not investment advice", consult-licensed-professionals, and risk disclosure. The Compliance Officer agent enforces this.

`fin-guru-private/` holds private strategy data (positions, tickets, analysis). NEVER commit changes here from automation, NEVER post its contents externally — file an issue instead if a fix would touch it.

## Project tracking

- Linear team: **AOJ**
- Linear project: **finance-guru**
- GitHub issues: `gh issue list` on this repo for follow-ups.

## PR review workflow

CodeRabbit + Claude bot review PRs automatically. Fetch comments via `gh api repos/{owner}/{repo}/pulls/{n}/comments`. Address all comments before merge; check which are already resolved in the latest commit before fixing.

## Style

Markdown emphasis: underscores (`_text_`), not asterisks — enforced by markdownlint MD049.

## Landing the Plane (Session Completion)

Work is **NOT complete** until `git push` succeeds.

1. File issues for any remaining work.
2. Run quality gates if code changed (pytest, ruff, mypy).
3. Update issue status — close finished, update in-progress.
4. **Push to remote** (mandatory): `git pull --rebase && git push && git status` — must show "up to date with origin".
5. Clean up stashes; prune remote branches.
6. Verify everything is committed AND pushed.
7. Hand off context for the next session.

Hard rules:
- Never stop before pushing — that strands work locally.
- Never say "ready to push when you are" — push it.
- If push fails, resolve and retry until it succeeds.
