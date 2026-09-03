---
title: "Finance Guru troubleshooting"
description: "Recover the supported local development and data-sync workflows"
category: setup
---

# Finance Guru troubleshooting

Start with the command that exposes the failure. Do not paste credentials,
account numbers, balances, positions, or access URLs into an issue or log.

## Python or uv is unavailable

Check the installed tools:

```bash
python3 --version
uv --version
```

Finance Guru requires Python 3.12 or later. Install [uv](https://docs.astral.sh/uv/) using the command from
[its official installation guide](https://docs.astral.sh/uv/getting-started/installation/),
then recreate the development environment:

```bash
uv sync --dev
```

## A Python module cannot be imported

Run repository entry points with uv from the repository root. Integration
modules must use Python's module form so package imports resolve:

```bash
uv run python -m src.integrations.refresh_all --help
```

If a standalone command still reports a missing module, check the
[CLI reference](../reference/api.md) for its supported invocation and report
the exact command and traceback in an issue.

## Tests fail because `.env` contains placeholders

The sample `.env.example` contains non-secret placeholder values. The runtime
loads `.env`, so a placeholder in a numeric setting can make tests fail before
they reach the behavior under test. Remove the local `.env` file or replace
only the values you intentionally use, then rerun the focused command:

```bash
uv run pytest -m "not integration"
```

Never commit `.env`.

## Market-data command fails or returns no data

Market-data commands query external providers and can fail because of an
invalid ticker, rate limiting, a network outage, or a provider-side change.

1. Confirm the CLI itself parses arguments with `--help`.
2. Retry with a known, currently listed symbol after checking its provider.
3. Record the command, timestamp, provider error, and whether the failure is
   reproducible before opening an issue.

Do not treat an unavailable market-data provider as evidence that local
calculations or the database are corrupted.

## SnapTrade or SimpleFIN refresh fails

The supported all-source command is:

```bash
uv run python -m src.integrations.refresh_all --show
```

`--show` reads the current local snapshots; omit it to attempt a sync. The
command returns a non-zero status when one source fails, even if another source
succeeds. Check the individual source status before retrying.

For [SnapTrade](https://snaptrade.com/), verify the owner has configured the required private environment
variables and account routing file. For [SimpleFIN](https://www.simplefin.org/), verify the private access
URL has been claimed and is available to the [Bun](https://bun.sh/) workspace. Do not copy either
credential into terminal history, issue text, or screenshots.

## Bun workspace errors

The TypeScript SimpleFIN workspace has its own dependency graph:

```bash
cd apps/simplefin-sync
bun install
```

Return to the repository root before running Python commands. If Bun cannot
run, verify `bun --version` and reinstall it from the official Bun installer.

## Private data appears in Git status

Stop before committing. Confirm that the file is ignored and that it is not
staged:

```bash
git status --ignored
git diff --cached
git check-ignore .env
```

If private data is already in a pushed commit, do not force-push a history
rewrite without coordinating with every affected collaborator. Treat the
exposure as a security incident and rotate exposed credentials first.

## Getting help

Search [open issues](https://github.com/AojdevStudio/Finance-Guru/issues)
before opening a new one. Include the command, a redacted error, environment
versions, and the smallest reproducible sequence. Label feature ideas and
questions separately from confirmed bugs.
