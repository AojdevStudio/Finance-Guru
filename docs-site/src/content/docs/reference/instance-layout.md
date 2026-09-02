---
title: "Instance layout"
description: "Every file and directory the engine resolves under one instance root."
sidebar:
  order: 2
---

The engine resolves every private path from one instance root. The resolver is `InstancePaths` in `src/config/instance_paths.py`.

## Root resolution

The root is the value of `FIN_GURU_DATA_ROOT` when that variable is set and non-empty. Otherwise the root is the current working directory. A relative value is resolved against the current working directory. Start Finance Guru sessions from your instance directory so the default resolution finds your data.

## Files under the root

| Path | Purpose |
| --- | --- |
| `.env` | Instance environment file, loaded into the process environment. |
| `user-profile.yaml` | User profile. |
| `config.yaml` | Instance configuration. |
| `snaptrade-accounts.yaml` | SnapTrade account-routing configuration. |
| `system-context.md` | Generated system context. |
| `family_office.db` | Default family-office SQLite database. |
| `dividend-schedules.yaml` | Dividend schedule file. |

## Directories under the root

| Path | Purpose |
| --- | --- |
| `imports/` | Broker CSV import directory. |
| `analysis/` | Analysis artifact directory. |
| `tickets/` | Buy-ticket directory. |
| `strategies/` | Strategy document directory. |
| `hedging/` | Hedge position and history directory. |
| `reports/` | Report artifact directory. |
| `auto-tickets/` | Automated-ticket runtime directory. |
| `notes/` | Instance notes and meeting records directory. |

## Database URL resolution

`DATABASE_URL` is optional. When it is unset, the engine uses a SQLite URL for `family_office.db` under the instance root. The in-memory values `:memory:` and `sqlite:///:memory:` are passed through. A `sqlite:///` URL with a relative path is resolved under the instance root. Any other URL scheme is returned unchanged by the resolver, but the engine only supports SQLite databases.

## Scaffolded extras

The instance initializer also creates a `.gitignore`, a `pyproject.toml` that depends on the engine checkout as an editable source, a local git repository, a `.claude` symlink to the engine's agent tooling, an instance `CLAUDE.md`, and a `.venv` created by `uv sync`. See [Your first instance](../../tutorials/your-first-instance/) for the creation walkthrough.

_This page is built from `src/config/instance_paths.py` and `src/cli/instance_init.py` in the repository._
