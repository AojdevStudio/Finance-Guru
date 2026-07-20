---
title: Portfolio Sync
cadence: ad-hoc
owner: Family Office Owner
last-reviewed: 2026-07-20
---

# Portfolio Sync

## Purpose

Pull current positions and balances from SnapTrade, sync approved changes to the Google Sheets DataHub, and validate downstream allocation and margin calculations.

The SnapTrade CLI is read-only. The `PortfolioSyncing` skill retains the existing comparison, approval, formula-protection, and Google Sheets write workflow.

## When to run

- _After_ a trade or other material account change
- _Before_ invoking quantitative analysis on current positions
- _Before_ generating FinanceReport PDFs (so reports reflect reality)

## Prerequisites

- The four `SNAPTRADE_*` credentials from `.env.example` are set in local `.env`
- `config/snaptrade-accounts.yaml` exists
- Each account to sync has `enabled: true` and a `role` other than `unassigned`
- `fin-core` skill auto-loaded
- `gdrive` MCP server configured (required for DataHub writes)
- You have the correct Google Sheet ID in your user profile

For a new connection, generate the routing file conservatively:

```bash
uv run python -m src.integrations.snaptrade.cli accounts \
  --probe \
  --output json \
  --write-config config/snaptrade-accounts.yaml
```

The generated accounts are disabled and unassigned. Verify each account against a known-good broker statement or CSV before assigning its role and setting `enabled: true`. Do not use `--force` unless replacing an existing routing file is intentional.

## Steps

1. _Check the routing gate_:

   ```bash
   uv run python -m src.integrations.snaptrade.cli positions --output text
   uv run python -m src.integrations.snaptrade.cli balances --output text
   ```

   Confirm the expected number of accounts synced and review every refused account. These commands fetch data but do not write to Google Sheets.

2. _Invoke the PortfolioSyncing skill_:

   ```
   /PortfolioSyncing
   ```

3. _Review the proposed diff_:
   - SnapTrade equity positions map to DataHub position rows
   - Options are excluded from position rows but included in margin-debt math
   - Settled cash maps to SPAXX
   - Margin debt is derived as gross market value minus net account equity
   - Safety checks flag missing tickers, large quantity or cost-basis changes, formula errors, and material cash or margin differences

4. _Approve the push_ only after the proposed changes reconcile with the broker account.

5. _Spot-check the DataHub tab_:
   - _Positions_ tab — symbols and quantities match SnapTrade
   - SPAXX, Pending Activity, and Margin Debt rows match the approved balance update

   Portfolio sync does not update the Margin Dashboard coverage ratio. Run [Margin Dashboard Update](margin-dashboard-update.md) after material balance changes.

## Verification

- The CLI output reports the expected `synced_account_count`
- Expected accounts do not appear in the `refused` list
- DataHub symbols, quantities, and average costs match the approved diff
- No red formula error cells (the formula-protection skill will have blocked bad edits)
- Total account value approximately reconciles to SnapTrade `account_equity`
- SPAXX matches `settled_cash`; Margin Debt matches derived `margin_debt`
- If positions changed materially, rerun _Margin Dashboard Update_ runbook

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `Missing required SnapTrade environment keys` | Add all four `SNAPTRADE_*` values to local `.env`; never commit that file |
| `SnapTrade routing config not found` | Generate `config/snaptrade-accounts.yaml` with the `accounts --write-config` command above |
| Account is refused | Set both a verified non-`unassigned` role and `enabled: true`; refusal is fail-closed behavior |
| No account syncs | Inspect `synced_account_count` and `refused`; disabled or unassigned accounts do not trigger a network call |
| Position or balance differs from the broker | Stop the Sheet update and compare the live output with a fresh broker statement or Fidelity CSV |
| Exact margin debit differs slightly | SnapTrade does not expose the loan directly; derived debt can differ due to intraday pricing |
| Formula error after sync | Invoke `formula-protection` to identify the protected cell; only apply a repair that the skill explicitly permits |
| Sheet tab doesn't update | Confirm the `gdrive` MCP server is configured and available, then retry the approved write |
| "Write would overwrite calculated cell" | Good — the formula-protection skill blocked a bad edit; review the attempted change |

Legacy Fidelity positions and balances CSVs may be used for manual re-verification, but the active portfolio-sync path does not ingest them. Retirement accounts remain on their separate broker-CSV workflow until routed through SnapTrade.

## Related skills

- `PortfolioSyncing` — primary skill
- `formula-protection` — protects calculated cells from accidental overwrite
- `dividend-tracking` — sync realized dividends through the separate activities workflow
- `TransactionSyncing` — transaction history is a separate ingestion path
- `retirement-syncing` — for Vanguard / Fidelity retirement accounts

## Related reference

- [SnapTrade bridge ADR](../adr/0001-snaptrade-live-sync-for-legacy-finance-guru.md)
- [Margin Dashboard Update](margin-dashboard-update.md)
