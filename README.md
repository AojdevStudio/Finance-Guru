# Finance Guru™

Finance Guru is a local-first financial analysis and automation repository built
for a private family office workflow. It combines a typed Python analysis
engine, brokerage-data integrations, operational runbooks, and AI-assisted
workflows.

> [!IMPORTANT]
> The repository is in a product transition. The Python analysis engine and
> documentation are the stable public surfaces. The Claude Code agent/skill
> stack remains usable but is transitional. The planned standalone Tauri v2
> macOS application is described in [the vision document](docs/VISION.md); it
> is not yet present in this repository.

## What is here today

| Area | Purpose | Status |
| --- | --- | --- |
| `src/` | Typed financial calculators, strategies, CLIs, and integrations | Stable |
| `tests/` | Regression and contract tests; provider tests use an integration marker | Stable |
| `buy_ticket_agent/` | Guardrailed buy-ticket generation workflow | Internal |
| `apps/simplefin-sync/` | Bun/TypeScript SimpleFIN ingestion and deposit triggers | Internal |
| `fin-guru/` and `.claude/` | Specialist agents, skills, hooks, and orchestration | Transitional |
| `docs/` | Setup guides, reference material, and operating runbooks | Active |

The stable analysis engine covers risk, momentum, volatility, correlation,
portfolio optimization, backtesting, options, factor analysis, total return,
hedging, margin metrics, and data validation. See the
[CLI reference](docs/reference/api.md) for the core command documentation.

## Quick start

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Git
- Bun for onboarding scripts and TypeScript workspaces
- Claude Code only if you use the transitional agent workflows

### Install

Finance Guru is designed to be forked so private configuration stays separate
from upstream development.

```bash
git clone https://github.com/YOUR-USERNAME/Finance-Guru.git
cd Finance-Guru
./setup.sh
```

For analysis-engine development without the interactive setup:

```bash
uv sync --dev
uv run pytest
```

The script checks prerequisites, installs Python dependencies, prepares local
private-data paths, and prints the onboarding command to run next. It does not
start an agent harness for you.

## Run the analysis engine

Every financial tool follows the same core pattern:

```text
Pydantic input models → calculator or strategy → CLI
```

Examples:

```bash
# Risk and benchmark metrics
uv run python src/analysis/risk_metrics_cli.py TSLA --days 252 --benchmark SPY

# Momentum indicators
uv run python src/utils/momentum_cli.py TSLA --days 90

# Portfolio optimization
uv run python src/strategies/optimizer_cli.py TSLA PLTR NVDA SPY \
  --days 252 \
  --method risk_parity

# Price, dividend, and total-return analysis
uv run python src/analysis/total_return_cli.py SCHD --days 365
```

Most CLIs support structured output for downstream automation:

```bash
uv run python src/analysis/risk_metrics_cli.py TSLA --output json
```

## Use the transitional agent workflows

After running setup, start your supported harness from the repository root.
Claude Code users can activate the existing orchestrator with:

```text
/fin-guru:agents:finance-orchestrator
```

The checked-in skill source is `.claude/skills/`.

These surfaces are scheduled for replacement by the standalone application.
New feature work against agents, skills, hooks, integrations, or other internal
runtime surfaces starts as an issue rather than a pull request. See
[Contributing](docs/CONTRIBUTING.md) for the exact boundaries.

## Architecture

```text
Finance-Guru/
├── src/
│   ├── models/          # Pydantic contracts
│   ├── analysis/        # Risk, return, options, hedging, and factor tools
│   ├── strategies/      # Portfolio optimization and backtesting
│   ├── utils/           # Market data, indicators, validation, and logging
│   ├── integrations/    # Brokerage adapters, including SnapTrade
│   └── config/          # Configuration loading and defaults
├── buy_ticket_agent/    # Guardrailed ticket-generation pipeline
├── apps/
│   └── simplefin-sync/  # Bun/TypeScript financial-data ingestion
├── fin-guru/            # Transitional agent module
├── .claude/             # Transitional skills, commands, and hooks
├── docs/                # Guides, reference, and runbooks
└── tests/               # Python and TypeScript-backed validation
```

The Python engine keeps validation, business logic, and command-line adapters
separate so calculations remain testable outside an AI session. External
providers are adapters around that engine, not the source of its financial
math.

## Data and privacy

The repository's `.gitignore` covers environment files, common portfolio-export
formats, user profiles, designated private directories, and local
account-routing configuration. It cannot prevent an explicit force-add or
protect an arbitrary output path. Before every push:

```bash
git status --ignored
git diff --cached
git check-ignore .env
```

Use synthetic data in tests. Never commit account identifiers, balances,
positions, API keys, or brokerage exports.

Local-first does not mean network-free: market-data, brokerage, research, and
LLM integrations may send request data to their configured providers. Review
each provider's privacy terms and configure only the integrations you intend to
use.

## Development

The required Python gates mirror CI:

```bash
uv sync --dev
uv run ruff format --check .
uv run ruff check .
uv run mypy src/
uv run pytest
```

Pull requests are accepted for documentation and the generic Python analysis
engine. Other surfaces are issues-only while the standalone-app transition is
underway. Read [Contributing](docs/CONTRIBUTING.md) before starting work.

## Documentation

| Document | Purpose |
| --- | --- |
| [Documentation hub](docs/index.md) | Navigation across all maintained docs |
| [CLI reference](docs/reference/api.md) | Commands, arguments, and output |
| [API keys](docs/setup/api-keys.md) | Optional provider configuration |
| [Troubleshooting](docs/setup/TROUBLESHOOTING.md) | Common installation and runtime failures |
| [Runbooks](docs/runbooks/README.md) | Recurring portfolio and operations workflows |
| [Vision](docs/VISION.md) | Standalone application direction and product decisions |
| [Contributing](docs/CONTRIBUTING.md) | Accepted surfaces, review rules, and quality gates |

## License

Finance Guru is licensed under the
[GNU Affero General Public License v3.0](LICENSE).

## Financial disclaimer

Finance Guru is educational software, not investment advice. Financial markets
involve risk, including possible loss of principal. Verify all data and
calculations independently and consult appropriately licensed financial, tax,
and legal professionals before acting.
