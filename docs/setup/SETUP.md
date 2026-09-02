---
title: "Finance Guru setup"
description: "Install the supported local analysis environment"
category: setup
---

# Finance Guru setup

This guide installs the checked-in Python and Bun workspaces. The supported
data store is the local `family_office.db`, committed only to the instance's
local-only repository; Google Sheets is not a data source and no Google Drive
integration is required.

## Prerequisites

- Python 3.12 or later
- [uv](https://docs.astral.sh/uv/)
- Git
- Bun only when working on `apps/simplefin-sync/`

The transitional Claude Code skills and hooks are not required to run the
Python analysis engine.

## Install

Clone your fork, then install the development dependency group:

```bash
git clone https://github.com/YOUR-USERNAME/Finance-Guru.git
cd Finance-Guru
uv sync --dev
```

The legacy `./setup.sh` scaffolds private-profile files and points to an
unfinished onboarding flow. It is not part of the supported analysis-engine
setup path.

## Create an instance

Private data lives in an instance directory outside the checkout. The engine
resolves it from `FIN_GURU_DATA_ROOT` or the current working directory. Create
one from the checkout:

```bash
uv run python -m src.cli.instance_init ~/finance-guru-data --repo .
```

The instance is a small uv project that depends on the engine, so
`uv run python -m src.<tool>` works from inside it with no extra flags. Run
Finance Guru sessions and sync commands from the instance directory.

For the SimpleFIN workspace, install its Bun dependencies from that workspace:

```bash
(
  cd apps/simplefin-sync
  bun install
)
```

## Verify the installation

These checks do not require credentials. The first command verifies the Python
environment; the second confirms an installed CLI can parse its arguments.

```bash
uv run pytest -m "not integration"
uv run python src/analysis/risk_metrics_cli.py --help
```

## Configure credentials privately

The instance scaffold writes an `.env` in the instance root that keeps real
defaults and comments out credentials for you to fill in. Uncomment a variable
only when you need an optional provider or a personal integration. Do not commit
any `.env` file.

See [API keys](api-keys.md) for the variables consumed by the supported
integrations and the
[live sync credentials guide](live-sync-credentials.md) for SnapTrade and
SimpleFIN. Keep account exports, API keys, and database files out of the public
engine checkout. The database is committed only to the instance's local-only
repository, which has no remote.

## Refresh local financial data

Run the all-source refresh from the instance directory:

```bash
uv run python -m src.integrations.refresh_all --show
```

Run without `--show` to execute the configured SnapTrade positions and
transactions sync plus the SimpleFIN expenses sync. A partial refresh exits
non-zero, so automation can detect a stale source.

## Next steps

- Use the [CLI reference](../reference/api.md) to choose an analysis command.
- Read [Troubleshooting](TROUBLESHOOTING.md) for environment and provider
  failures.
- Read [Contributing](../CONTRIBUTING.md) before changing repository code.
- Use the GitHub Wiki for the canonical user and developer guide once it is
  published; repository docs remain the source, contributor, and operational
  reference.
