---
title: "Wiki evidence ledger"
description: "Sources and status labels for canonical documentation claims"
category: reference
---

# Wiki evidence ledger

This ledger is the source boundary for the GitHub Wiki. A claim is published
only when it has a source below or is visibly marked _planned_ or _unknown_.
Code and live GitHub state take precedence over older repository prose.

| Claim | Status | Evidence |
| --- | --- | --- |
| Finance Guru stores supported positions, balances, transactions, and bank transactions in local SQLite. | Verified | `CLAUDE.md`, `src/integrations/refresh_all.py`, and the gitignored `family_office.db` paths. |
| The all-source refresh entry point is `uv run python -m src.integrations.refresh_all`. | Verified | `src/integrations/refresh_all.py`; `--help` rendered successfully on 2026-07-31. |
| SnapTrade and SimpleFIN are external read sources that write local snapshots. | Verified | `src/integrations/snaptrade/`, `src/integrations/simplefin/`, and `apps/simplefin-sync/`. |
| The analysis engine is CLI-first and uses Pydantic models, calculators or strategies, and CLI adapters. | Verified | `src/models/`, `src/analysis/`, `src/strategies/`, `src/utils/`, and the checked-in CLI inventory. |
| The checked-in analysis commands are all functional. | Unknown | The CLI inventory is command-by-command; `momentum_cli` and `input_validation_cli` have open defects [#108](https://github.com/AojdevStudio/Finance-Guru/issues/108) and [#120](https://github.com/AojdevStudio/Finance-Guru/issues/120). |
| The Claude Code skills and hooks are transitional, not a supported public installation path. | Verified | `docs/CONTRIBUTING.md` defines these surfaces as transitional. |
| The standalone macOS application is available. | Planned | `docs/VISION.md` describes direction only; no checked-in release or production proof exists. |
| Financial analysis is educational material, not investment advice. | Verified | `README.md`, `docs/CONTRIBUTING.md`, and CLI-output requirements require that boundary. |
| A local test or CI pass does not prove a release, production deployment, or provider success. | Verified | Repository tests and GitHub checks verify repository behavior only; provider and release state require separate live evidence. |
| The engine resolves every private path from one instance root, taken from `FIN_GURU_DATA_ROOT` or the current working directory. | Verified | `src/config/instance_paths.py` (`InstancePaths.resolve`) and the `FIN_GURU_DATA_ROOT` entry in `.env.example`. |
| The instance layout is flat. The root holds `.env`, `user-profile.yaml`, `config.yaml`, `system-context.md`, `family_office.db`, `snaptrade-accounts.yaml`, `dividend-schedules.yaml`, and the directories `imports/`, `analysis/`, `tickets/`, `strategies/`, `hedging/`, `reports/`, `auto-tickets/`, `notes/`. | Verified | `InstancePaths` properties in `src/config/instance_paths.py` and the scaffold plan in `src/cli/instance_init.py`. |
| An instance is created with `uv run --project "<repo>" python -m src.cli.instance_init "<root>" --repo "<repo>"` and the initializer is idempotent. | Verified | `src/cli/instance_init.py` and step 1 of `docs/runbooks/instance-migration.md`. |
| The instance is a uv project depending on the engine, so `uv run python -m src.<tool>` works from inside it. | Verified | `_instance_pyproject` and `_instance_instructions` in `src/cli/instance_init.py`; merged PR [#135](https://github.com/AojdevStudio/Finance-Guru/pull/135). |
| The SnapTrade account-routing file is `snaptrade-accounts.yaml` directly under the instance root. | Verified | `InstancePaths.snaptrade_accounts` in `src/config/instance_paths.py`. The older `config/snaptrade-accounts.yaml` path in `docs/setup/api-keys.md` is stale; doc contract bugs are tracked in [#137](https://github.com/AojdevStudio/Finance-Guru/issues/137). |
| `notebooks/`, `fin-guru-private/`, and `fin-guru/data/user-profile.yaml` no longer exist as data locations; their contents move into the instance. | Verified | `docs/runbooks/instance-migration.md` and the P2 landing comment on [#131](https://github.com/AojdevStudio/Finance-Guru/issues/131). |
| A runbook documents moving existing private data into an instance. | Verified | `docs/runbooks/instance-migration.md`. |
| `DATABASE_URL` is optional and defaults to `family_office.db` under the instance root. | Verified | `InstancePaths.database_url` in `src/config/instance_paths.py` and `.env.example`. |
| Skills and agents invoke engine tools in module form so they run with the instance as the working directory. | Verified | Merged PR [#136](https://github.com/AojdevStudio/Finance-Guru/pull/136) and the P2 landing comment on [#131](https://github.com/AojdevStudio/Finance-Guru/issues/131). |
| Plugin installation arrives through the Claude Code marketplace. | Planned | Phase P3 of [#131](https://github.com/AojdevStudio/Finance-Guru/issues/131); no manifest or marketplace entry is on main. |
| An onboarding skill scaffolds a user instance. | Planned | Phase P3 of [#131](https://github.com/AojdevStudio/Finance-Guru/issues/131); not on main. |
| A Diátaxis documentation site is built. | Planned | Maintainer direction only; no repository source or tracking issue found on 2026-09-02. |

## Refresh procedure

Refresh this ledger whenever a change affects setup, CLI entry points, data
storage, privacy, testing, distribution, or a Wiki page. Do not replace a
source with an issue title, a planned design, or a passing local test that does
not cover the claim.
