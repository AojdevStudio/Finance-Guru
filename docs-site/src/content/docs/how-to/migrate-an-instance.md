---
title: "Migrate private data into an instance"
description: "Move an existing checkout's private files into a dedicated Finance Guru instance directory."
sidebar:
  order: 1
---

Follow this guide when private data still lives inside an engine checkout and you want it moved into a dedicated instance. The result is a checkout that holds only public code and an instance that holds everything personal.

In the commands below, `<repo>` is the engine checkout and `<root>` is the instance directory. Each `mv` step applies only when the source file exists in your checkout.

## Create the instance

Create the local instance.

```bash
uv run --project "<repo>" python -m src.cli.instance_init "<root>" --repo "<repo>"
```

Check that the instance virtual environment exists.

```bash
test -d "<root>/.venv"
```

Check that the project link exists.

```bash
test -L "<root>/.claude"
```

## Move the data

Move the user profile over the empty instance template.

```bash
command mv "<repo>/fin-guru/data/user-profile.yaml" "<root>/user-profile.yaml"
```

Move the database and each [SQLite](https://www.sqlite.org/) sidecar that exists.

```bash
command mv "<repo>/family_office.db" "<root>/family_office.db"
command mv "<repo>/family_office.db-wal" "<root>/family_office.db-wal"
command mv "<repo>/family_office.db-shm" "<root>/family_office.db-shm"
command mv "<repo>/family_office.db-journal" "<root>/family_office.db-journal"
```

Move the environment and [SnapTrade](https://snaptrade.com/) routing files.

```bash
command mv "<repo>/.env" "<root>/.env"
command mv "<repo>/config/snaptrade-accounts.yaml" "<root>/snaptrade-accounts.yaml"
```

Move report, analysis, ticket, strategy, and hedging artifacts into their instance directories. The full step-by-step sequence, including the merge order for nested archives, lives in the repository runbook at `docs/runbooks/instance-migration.md`. Follow it exactly when your checkout contains the older private directory layout.

Move CSV imports last. Replace the empty imports directory with your portfolio updates, then add transaction and retirement exports.

```bash
command rmdir "<root>/imports"
command mv "<repo>/notebooks/updates" "<root>/imports"
command mv "<repo>/notebooks/transactions" "<root>/imports/transactions"
command mv "<repo>/notebooks/retirement-accounts" "<root>/imports/retirement"
```

## Verify the instance

Change to the instance directory and refresh the local database from the migrated credentials and routing file.

```bash
cd "<root>"
uv run python -m src.integrations.refresh_all
```

Print the position and balance tables.

```bash
uv run python -m src.integrations.refresh_all --show
```

Check the checkout for unexpected untracked files under the moved paths.

```bash
git -C "<repo>" status --short --untracked-files=all
```

## Commit the instance

The instance has its own local git repository with no remote. Commit the migrated data there.

```bash
cd "<root>"
git add -A && git commit -m "migrate household data from the checkout"
```

## Start future sessions from the instance

Change to the instance directory before starting a Finance Guru session, and confirm the working directory with `pwd`. The engine resolves every private path from the working directory unless `FIN_GURU_DATA_ROOT` overrides it. See the [instance layout reference](../../reference/instance-layout/).

_This page is built from `docs/runbooks/instance-migration.md` in the repository._
