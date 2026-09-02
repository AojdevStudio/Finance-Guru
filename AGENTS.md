# Finance Guru

Finance Guru is a self-hosted family office engine: typed Python calculators, a private SQLite ledger, and specialist agents that run inside Claude Code or Codex. It is the open-core engine behind Keepfolio. The README describes the product for people. This file is the canonical instruction set for any agent working in the repository or in an instance built from it. `CLAUDE.md` imports it and adds only what is specific to Claude Code.

## The split

Agents propose. Typed code computes. Every number an agent quotes comes from a calculator under `src/` with a CLI you can run. Every irreversible action passes through a guardrail that blocks with a typed reason when an input is missing. Do the judgment. Leave the arithmetic to the CLI.

## Operating rules

- Run `date` and `date +"%Y-%m-%d"` at the start of every session. Persona files use them as `{current_datetime}` and `{current_date}`, alongside `{project-root}`, `{module-path}`, `{data-root}`, and `{user_name}`. Resolve every variable to a real path or value before use.
- Quote calculator output, never your own arithmetic. Pass `--output json` where the CLI offers it. `margin_metrics_cli` prints JSON by default and has no `--output` flag.
- Fail closed. A guardrail with a missing input returns a block with a typed reason. Do not fill the gap with an estimate.
- Every financial output carries the educational-only disclaimer, a "not investment advice" statement, a recommendation to consult licensed professionals, a risk disclosure, a date stamp, and its data source. The CLIs print the disclaimer. The skills expect it.
- Speak to the owner in the second person. This is their family office, so it is "your portfolio" and "your margin balance", never "the user's".

## The instance

Private data lives in an instance directory outside the repository, resolved from `FIN_GURU_DATA_ROOT` or the current working directory. The instance holds `.env`, `user-profile.yaml`, `config.yaml`, `family_office.db`, broker CSV exports under `imports/`, and every artifact the engine writes. Tracked files in this repository never carry personal values. `uv run python -m src.cli.instance_init <root> --repo .` scaffolds an instance.

- Run engine commands from the instance as `uv run python -m src.<tool>` so private paths resolve from the current directory.
- `family_office.db` is the single source of truth for positions, balances, transactions, and bank transactions. `src.integrations.refresh_all` fills it from SnapTrade (brokerage) and SimpleFIN (bank and card) and raises on a partial provider response. CSV exports in `imports/` are an ingestion path into the database, not a second ledger.
- The Google Sheets DataHub is retired. Do not write to Sheets, reference a spreadsheet ID, or reintroduce a gdrive MCP dependency.
- Write analysis to `analysis/` as `{topic}-{YYYY-MM-DD}.md` and buy tickets to `tickets/` as `buy-ticket-{YYYY-MM-DD}-{descriptor}.md`. Markdown with YAML frontmatter, date stamp, disclaimer, and citations.
- The pre-push compliance scan blocks a push that carries secrets or PII. A fresh checkout installs it with `.claude/skills/compliance-scan/scripts/install-pre-push.sh`.

## Skills and specialists

Skills live in `.claude/skills/<name>/SKILL.md`. Route on the `description` in each file's frontmatter and read the full file before using it. Specialist personas live in `.claude/commands/fin-guru/agents/`, and the finance orchestrator there routes between them. `just --list` shows the launcher for each persona.

### Codex instance skill discovery

A scaffolded checkout-mode instance holds `.agents` and `.claude` symlinks to the engine's single `.claude` tree. Codex started from an instance discovers skills under `./.agents/skills`. Read the selected `SKILL.md` in full. Never copy skill content into the instance or maintain a second harness-specific skill tree. A plugin-mode instance omits both symlinks because the installed plugin is the source of agents, skills, and hooks.

## Code

- Every calculator is three layers: a Pydantic input model in `src/models/`, a calculator class, and a `*_cli.py` wrapper in the same directory. A new tool ships all three plus a test under `tests/python/` that runs without a network. Conventions and gotchas for the Python code are in `src/CLAUDE.md`.
- The CLI reference is `docs/reference/api.md`. Every CLI answers `--help`.
- `apps/simplefin-sync/` is a Bun workspace. Use `bun`, never npm.
- Research skills may call the MCP servers named in their persona files. None are required to run the calculators or the sync.
- Markdown emphasis uses underscores, `_like this_`. markdownlint rule MD049 enforces it.

## Toolchain and gates

Python 3.12 or later, managed with `uv`. These gates mirror CI and the pre-commit hook:

```bash
uv sync --dev
uv run ruff format --check .
uv run ruff check .
uv run mypy src/
uv run pytest -m "not integration"
```

- The pre-commit hook runs the full pytest suite with the 80% coverage gate on every commit, so a commit takes about ten seconds. Tests marked `integration` need real API keys.
- Tests assume no `.env` in the repository root. A scaffolded `.env` holds placeholder strings such as `your_monthly_dividend_income_here`, and `python-dotenv` loads them, which fails the margin-metrics tests with `could not convert string to float`. Delete the file or fill in real numbers.
- Pull requests get CodeRabbit and Claude reviews. Verify each finding against the source before acting on it and dismiss a false positive with a written reason.

## Session end

Work is not complete until `git push` succeeds. Before ending a session: file issues for follow-up work, run the gates if code changed, commit, `git pull --rebase`, push, and confirm `git status` reports the branch is up to date with origin. If the push fails, resolve the cause and push again.

## Cursor Cloud

The startup script already runs `uv sync --dev` and `bun install`. `uv` lives at `~/.local/bin/uv` and `bun` at `~/.bun/bin/bun`. Both are on `PATH` for interactive shells only, so a fresh non-interactive shell needs `export PATH="$HOME/.local/bin:$HOME/.bun/bin:$PATH"` first. There is no long-running server. Run an analysis with `uv run python -m src.analysis.risk_metrics_cli AAPL --days 252 --benchmark SPY`, which fetches live data through yfinance with no API key, or launch the dashboard with `uv run python -m src.cli.fin_guru` and quit with `q`.

## Documentation

`docs/index.md` is the hub for setup, the CLI reference, live-sync credentials, runbooks, and troubleshooting. `docs/CONTRIBUTING.md` states the accepted surfaces and the privacy rules every push must pass. `CHANGELOG.md` carries every release.
