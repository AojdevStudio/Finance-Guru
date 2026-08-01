---
title: "Finance Guru setup"
description: "Install the supported local analysis environment"
category: setup
---

# Finance Guru setup

This guide installs the checked-in Python and Bun workspaces. The supported
data store is the local, gitignored `family_office.db`; Google Sheets is not a
data source and no Google Drive integration is required.

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

Copy the sample environment file only when you need an optional provider or a
personal integration. Do not commit the resulting `.env` file.

```bash
cp .env.example .env
```

See [API keys](api-keys.md) for the variables consumed by the supported
integrations. Keep account exports, API keys, and database files out of Git.

## Refresh local financial data

The all-source refresh command must run as a module so Python can resolve the
repository package imports:

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
