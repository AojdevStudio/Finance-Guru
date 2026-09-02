---
title: "Architecture and data flow"
description: "How the local-first engine, the instance directory, and the provider integrations fit together."
sidebar:
  order: 1
---

Finance Guru is a local, CLI-first environment. It has no required long-running server for analysis commands. Everything runs as a command against local files and, when configured, read-only provider APIs.

## The data boundary

```text
SnapTrade or SimpleFIN credentials (local configuration)
                  |
                  v
Provider sync modules -> family_office.db (local, gitignored SQLite)
                  |
                  v
Python analysis and strategy CLIs -> local terminal output or local artifacts
```

The public repository must not contain database files, access URLs, account numbers, balances, positions, or credentials. Google Sheets and Google Drive are not part of the current data path.

## Why an instance directory

The engine checkout is public code. Private data lives in a separate instance directory, resolved through one path resolver from `FIN_GURU_DATA_ROOT` or the current working directory. This split exists so the repository can be shared, forked, and reviewed without ever being anyone's private working residence. The [instance layout reference](../../reference/instance-layout/) lists every path.

## The three layers

Every analysis tool follows one 3-layer pattern. Pydantic models validate inputs and outputs. Calculator classes hold the business logic. Thin CLI entry points handle input and output only. The pattern keeps calculations testable and keeps command surfaces consistent, so every tool takes a ticker, a window, and flags in the same shape.

## Where data comes from

Two read-only integrations feed the local database. The SnapTrade modules sync brokerage positions, balances, and activities. The SimpleFIN workspace syncs bank and card transactions. Broker CSV exports remain a first-class source, dropped into the instance import directory, so the system works without any live credentials. The coordinating entry point is `src.integrations.refresh_all`, which runs every configured source and exits non-zero on a partial refresh.

## Verified implementation seams

- `src/integrations/refresh_all.py` coordinates the configured refreshes.
- `src/integrations/snaptrade/` contains account, position, balance, and activity synchronization surfaces.
- `src/integrations/simplefin/sync_expenses_db.py` imports configured bank and card transaction data into local SQLite.
- `src/models/`, `src/analysis/`, and the CLI entry points form the checked-in validation, business-logic, and command layers.

## What sits outside the stable core

The agent skills and hooks under `.claude/` orchestrate these same commands from an AI harness. They are transitional. The planned standalone application removes that dependency entirely. See [hooks and skills](../../reference/hooks-and-skills/) for the current status.

_This page is built from the Wiki Architecture and Data Flow page and `src/CLAUDE.md` in the repository._
