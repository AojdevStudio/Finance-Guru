# Finance Guru™

Finance Guru is a self-hosted family office engine for technical operators who
already run Claude Code or Codex. It combines a typed Python analysis engine
with agent skills that read your portfolio from a local SQLite database. All of
it is open under AGPL-3.0. The skills, the agents, and the engine ship
together, and there is no withheld feature tier. Finance Guru is the free,
self-hosted, CLI-native experience. Keepfolio is the polished macOS product for
people who will not run a terminal.

The engine works on day one with broker CSV exports dropped into `imports/`.
Live sync through SnapTrade and SimpleFIN is optional and uses your own
credentials.

## Quick start

You need Python 3.12 or later, [uv](https://docs.astral.sh/uv/), and Git.

Clone the engine, then create an instance directory for your private data. The
instance is a small uv project that depends on the engine, so engine commands
run from it with no extra flags.

```bash
git clone https://github.com/AojdevStudio/Finance-Guru.git
cd Finance-Guru
uv run python -m src.cli.instance_init ~/finance-guru-data --repo .
cd ~/finance-guru-data
uv run python -m src.integrations.refresh_all --show
```

The last command prints the position, transaction, and expense tables. On a new
instance it reports an empty database. Drop broker CSV exports into `imports/`
to work CSV-first, or set up [live sync](#live-sync) later.

Market analysis needs no portfolio data at all. From the instance directory,
run any engine tool as a module.

```bash
uv run python -m src.analysis.risk_metrics_cli TSLA --days 252 --benchmark SPY
```

See the [CLI reference](docs/reference/api.md) for the full tool list.

## Install as a plugin

This install path lands with the plugin release. It is not on main yet.

```bash
claude plugin marketplace add AojdevStudio/Finance-Guru
claude plugin install finance-guru@finance-guru
```

After install, run the `instance-onboarding` skill. It scaffolds the instance
directory described above and walks through the first CSV import.

## What you get

| Surface | Location | What it does |
| --- | --- | --- |
| Python engine | `src/` | Typed calculators and CLIs for risk, momentum, volatility, correlation, portfolio optimization, backtesting, options, factor analysis, total return, hedging, and margin metrics |
| Skills | `.claude/skills/` | Workflows for portfolio sync, dividend tracking, margin management, Monte Carlo simulation, market research, report generation, and compliance scanning |
| Agents | `.claude/commands/fin-guru/agents/` | Specialist financial agents coordinated by the Finance Orchestrator |

Every tool in the engine follows the same three-layer pattern. Pydantic input
models feed a calculator class, and a CLI wraps the calculator. Calculations
stay testable outside any AI session.

## Live sync

CSV exports are enough to start. Power users can connect SnapTrade for
read-only brokerage positions, balances, and transactions, and SimpleFIN for
read-only bank and card activity. Both use credentials you obtain yourself and
keep in local, gitignored files. The
[live sync credentials guide](docs/setup/live-sync-credentials.md) lists the
environment variables each provider needs and explains what
`refresh_all` does with each leg.

## Data and privacy

The engine reads every private file from an instance directory outside the
repository. The instance root comes from `FIN_GURU_DATA_ROOT`, or the current
working directory when that variable is unset. The instance holds `.env`,
`user-profile.yaml`, `config.yaml`, `system-context.md`, `family_office.db`,
`snaptrade-accounts.yaml`, `dividend-schedules.yaml`, and the working
directories `imports/`, `analysis/`, `tickets/`, `strategies/`, `hedging/`,
`reports/`, `auto-tickets/`, and `notes/`.

The repository is public. Tracked files describe behaviour and never carry
personal values. The full rule and its enforcement live in
[DataClassification](.claude/skills/compliance-scan/references/DataClassification.md)
and [PRIVACY.md](PRIVACY.md).

Local-first does not mean network-free. Market data, brokerage, and LLM
integrations send request data to their configured providers. Configure only
the integrations you intend to use.

## Development

The required Python gates mirror CI.

```bash
uv sync --dev
uv run ruff format --check .
uv run ruff check .
uv run mypy src/
uv run pytest -m "not integration"
```

Read [Contributing](docs/CONTRIBUTING.md) before opening a pull request. It
covers the accepted surfaces, the quality gates, and the privacy rules that
every push must pass.

## Documentation

| Document | Purpose |
| --- | --- |
| [Repository documentation](docs/index.md) | Setup, usage, architecture, privacy, contributor, and operational material |
| [Setup](docs/setup/SETUP.md) | Install the engine and create an instance |
| [CLI reference](docs/reference/api.md) | Commands, arguments, and output |
| [Live sync credentials](docs/setup/live-sync-credentials.md) | Bring-your-own-credentials setup for SnapTrade and SimpleFIN |
| [API keys](docs/setup/api-keys.md) | Optional provider configuration |
| [Troubleshooting](docs/setup/TROUBLESHOOTING.md) | Common installation and runtime failures |
| [Runbooks](docs/runbooks/README.md) | Recurring portfolio and operations workflows |
| [Contributing](docs/CONTRIBUTING.md) | Accepted surfaces, review rules, and quality gates |

## License

Finance Guru is licensed under the
[GNU Affero General Public License v3.0](LICENSE).

## Financial disclaimer

Finance Guru is educational software, not investment advice. Financial markets
involve risk, including possible loss of principal. Verify all data and
calculations independently and consult appropriately licensed financial, tax,
and legal professionals before acting.
