---
title: "Run the data syncs"
description: "Refresh SnapTrade and SimpleFIN data into the local Finance Guru database."
sidebar:
  order: 3
---

Follow this guide to refresh configured brokerage and bank data into the local, gitignored [SQLite](https://www.sqlite.org/) database. Credentials must already be configured. See [Configure live sync credentials](../configure-live-sync-credentials/) first.

Run these commands from your instance directory so the engine resolves the instance database. Sync modules run in Python's module form so package imports resolve.

## Refresh everything

The supported all-source command runs the configured [SnapTrade](https://snaptrade.com/) positions and transactions sync plus the [SimpleFIN](https://www.simplefin.org/) expenses sync.

```bash
uv run python -m src.integrations.refresh_all
```

A partial refresh exits non-zero, so automation can detect a stale source. When one source fails, check that source's status individually before retrying.

## Show the current snapshot

Print the current local position and balance tables without contacting any provider.

```bash
uv run python -m src.integrations.refresh_all --show
```

## Run one source at a time

| Command | Purpose |
| --- | --- |
| `uv run python -m src.integrations.snaptrade.cli` | Inspect linked SnapTrade accounts, positions, balances, or activities. |
| `uv run python -m src.integrations.snaptrade.sync_db` | Refresh SnapTrade positions and balances into local SQLite. |
| `uv run python -m src.integrations.snaptrade.sync_transactions_db` | Refresh SnapTrade activities into local SQLite. |
| `uv run python -m src.integrations.simplefin.sync_expenses_db` | Refresh SimpleFIN transactions into local SQLite. |

Each command supports `--help` for its full flag reference.

## Recover from a failed sync

For SnapTrade, verify the required private environment variables and the account routing file are configured. For SimpleFIN, verify the private access URL has been claimed and is available to the [Bun](https://bun.sh/) workspace. Do not copy either credential into terminal history, issue text, or screenshots. See [Troubleshoot common failures](../troubleshoot/) for the full recovery paths.

_This page is built from `docs/reference/api.md` and `docs/setup/SETUP.md` in the repository._
