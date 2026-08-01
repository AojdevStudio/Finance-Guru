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

## Refresh procedure

Refresh this ledger whenever a change affects setup, CLI entry points, data
storage, privacy, testing, distribution, or a Wiki page. Do not replace a
source with an issue title, a planned design, or a passing local test that does
not cover the claim.
