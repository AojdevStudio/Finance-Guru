---
title: "Your first instance"
description: "Create a local Finance Guru instance, add a profile and a CSV import, and verify it with a data refresh."
sidebar:
  order: 1
---

An instance is the private home for your financial data. It lives outside the engine checkout, so nothing personal can land in the public repository. In this tutorial you create an instance, fill in a profile, add a broker CSV export, and verify the instance with a data refresh.

## Before you start

You need a Finance Guru engine checkout with its development environment installed. The [setup path](../../how-to/troubleshoot/) requires Python 3.12 or later and [uv](https://docs.astral.sh/uv/). In the commands below, `<repo>` is the path to your engine checkout and `<root>` is the directory where your instance will live.

## Step 1. Create the instance

Run the instance initializer from anywhere.

```bash
uv run --project "<repo>" python -m src.cli.instance_init "<root>" --repo "<repo>"
```

The command prints one line per step, marked `created` or `exists`. It scaffolds the instance directories, a `.env` file, an empty profile, a local git repository, and a virtual environment. It never overwrites an existing file, so it is safe to rerun.

Check that the instance virtual environment exists.

```bash
test -d "<root>/.venv"
```

Check that the project link exists.

```bash
test -L "<root>/.claude"
```

Both commands exit silently on success.

## Step 2. Fill in your profile

The initializer wrote an empty profile template to `<root>/user-profile.yaml`. Open it in your editor and add your instance-specific values. The instance has its own local git repository with no remote, so your profile stays on your machine. Never copy these values into the engine checkout.

## Step 3. Add a broker CSV export

Finance Guru works on day one with broker CSV exports. Download a positions or balances export from your broker and place it in the instance import directory.

```bash
ls "<root>/imports"
```

The import directory holds your source CSVs. Live provider sync is optional and comes later. See [Configure live sync credentials](../../how-to/configure-live-sync-credentials/) when you are ready.

## Step 4. Verify with a refresh

Change to the instance directory and print the current local snapshot.

```bash
cd "<root>"
uv run python -m src.integrations.refresh_all --show
```

The `--show` flag reads the current local database snapshot without contacting any provider. A brand-new instance prints empty position and balance tables. That is the expected result. The tables fill once you run a sync with configured credentials, as described in [Run the data syncs](../../how-to/run-the-syncs/).

## What you built

You now have a private instance directory with a profile, an import area, and a working database path. Continue with [Your first analysis](../your-first-analysis/) to run the analysis engine.

_This page is built from `docs/runbooks/instance-migration.md` and `src/cli/instance_init.py` in the repository._
