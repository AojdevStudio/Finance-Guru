---
title: "Finance Guru setup"
description: "Install the supported local analysis environment"
category: setup
---

# Finance Guru setup

This guide installs the checked-in Python and [Bun](https://bun.sh/) workspaces. The supported
data store is the local `family_office.db`, committed only to the instance's
local-only repository; Google Sheets is not a data source and no Google Drive
integration is required.

## Prerequisites

- [Python](https://www.python.org/) 3.12 or later
- [uv](https://docs.astral.sh/uv/)
- [Git](https://git-scm.com/)
- [Bun](https://bun.sh/) for agent session hooks, repository PR gates, and `apps/simplefin-sync/`

The [Claude Code](https://code.claude.com/) plugin is not required to run the Python analysis engine from
a shell.
Bun is not required for that shell-only path. Agent sessions need it before the
session-start hook runs. Repository sessions also run the PR gate before each
Bash tool call.
Repository Claude Code sessions require v2.1.295 or later so
`onFailure: "block"` keeps an unavailable PR gate closed.

## Install

Clone your fork, then install the development dependency group:

```bash
git clone https://github.com/YOUR-USERNAME/Finance-Guru.git
cd Finance-Guru
uv sync --dev
bun install --frozen-lockfile
```

The legacy `./setup.sh` scaffolds private-profile files and points to an
unfinished onboarding flow. It is not part of the supported analysis-engine
setup path.

The locked Bun install supplies the repository's TypeScript checks. Run it
before the commit hook so `bunx` uses the pinned compiler.

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

Checkout instances own their `.claude` settings and link only finance assets.
Their `.agents` link points to that local runtime view. They do not inherit
repository developer hooks or PR tools. Rerun the scaffold command to migrate
an older instance with known checkout symlinks. The migration preserves shared
repository settings and owner notes. An
unknown link or an edited inherited instruction file stops migration before
writes and names the conflicting path.

The scaffold and onboarding writer load the `fin-core` skill and the same
finance rules. They do not import repository developer instructions. The scaffold
can migrate a recognized wizard-generated `CLAUDE.md`. It replaces the old
repository import and removes only the exact generated repository push workflow.
The profile text and owner notes stay intact. An edited legacy push workflow
stops migration before writes.

To switch a checkout instance to plugin mode, first move its `.claude` runtime
directory aside and remove its `.agents` discovery link. Keep any local settings
you need. Then rerun with `--plugin`. The scaffold refuses leftover checkout
discovery paths so the plugin remains the single source of finance assets.

For the [SimpleFIN](https://www.simplefin.org/) workspace, install its Bun dependencies from that workspace:

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
[live sync credentials guide](live-sync-credentials.md) for [SnapTrade](https://snaptrade.com/) and
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
