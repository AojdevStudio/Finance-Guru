---
title: Portfolio Sync
cadence: ad-hoc
owner: Ossie
last-reviewed: 2026-07-27
---

# Portfolio Sync

## Purpose

Pull current taxable-account positions and balances through the read-only SnapTrade
bridge, push approved changes to the Google Sheets DataHub, and verify downstream
allocation and margin calculations.

## When to run

- After a trade or material balance change
- Before quantitative analysis that depends on current holdings
- Before generating FinanceReport PDFs
- During initial account cutover, alongside a known-good broker export

## Prerequisites

- The four `SNAPTRADE_*` values are present in the project-root `.env`
- The target account has a non-`unassigned` role and `enabled: true` in
  `config/snaptrade-accounts.yaml`
- `fin-core` skill auto-loaded
- `gdrive` MCP server configured (required for DataHub writes)
- The Google Sheet ID is configured in the user profile
- Initial cutover only: positions and balances have been reconciled with a
  known-good broker export

See [SnapTrade Live Sync](../guides/snaptrade-live-sync.md) for first-time
configuration and routing.

## Steps

1. _Establish the sync date_:

   ```bash
   date
   ```

2. _Check the read-only source before any Sheet write_:

   ```bash
   uv run python -m src.integrations.snaptrade.cli positions --output text
   uv run python -m src.integrations.snaptrade.cli balances --output text
   ```

   Confirm the expected account is synced and investigate every refusal.

3. _Invoke the PortfolioSyncing skill_ by requesting `portfolio-sync`.

4. _Review the comparison report_:
   - Routed account and total positions detected
   - Equity and option symbols, quantities, and available cost basis
   - Settled cash mapped to SPAXX
   - Margin debt derived from gross market value minus account equity
   - Quantity, cost-basis, cash, and margin safety-gate diffs

5. _Approve the push_ only when the reported changes match expected trading
   activity.

6. _Spot-check the DataHub_:
   - Position row count and symbols match the live response
   - _Allocation_ tab — percentages sum to 100% ± 0.01
   - _Margin Dashboard_ — coverage ratio refreshed

The SnapTrade CLI only reads broker data. Google Sheets changes occur through the
skill and remain protected by the formula-protection rules.

## Verification

- The CLI reports the intended account under `accounts`, not `refused`
- Google Sheets DataHub shows today's last-updated date
- Position quantities and cost basis reconcile with the normalized live response
- SPAXX and margin debt reconcile with the live balance response
- No red formula error cells (the formula-protection skill will have blocked bad edits)
- Allocation percentages reconcile to total market value
- If margin changed materially, run the
  [Margin Dashboard Update](margin-dashboard-update.md) runbook

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| Missing environment-key error | Add every named `SNAPTRADE_*` key to `.env`; do not place credentials in the routing YAML |
| Routing config not found | Run the `accounts --write-config` command in the SnapTrade guide |
| Zero accounts synced | Inspect `refused`; set both a valid role and `enabled: true` only after reconciliation |
| Unexpected or incomplete position | Disable the route and compare SnapTrade with a fresh broker export before writing |
| SPAXX mismatch | Compare SnapTrade `settled_cash`, the SPAXX position, and the DataHub cash row |
| Formula error after sync | Invoke `formula-protection` skill; it will identify the modified cell and restore it |
| Sheet tab doesn't update | Confirm `gdrive` MCP is connected — `/gdrive:status` or restart Claude Code session |
| "Write would overwrite calculated cell" | Good — the formula-protection skill blocked a bad edit; review the attempted change |

## CSV fallback

CSV files are no longer the regular taxable-account source. Use the documented
fallback only when SnapTrade is unavailable or a route fails reconciliation:

1. Disable the affected route.
2. Export fresh positions and balances from the broker.
3. Follow [Broker CSV Inputs and Fallbacks](../guides/required-csv-uploads.md).
4. Reconcile the discrepancy before re-enabling live sync.

## Related skills

- `PortfolioSyncing` — primary skill
- `formula-protection` — protects calculated cells from accidental overwrite
- `dividend-tracking` — sync dividends alongside positions if both files are fresh
- `TransactionSyncing` — transaction history is a separate ingestion path
- `retirement-syncing` — for Vanguard / Fidelity retirement accounts
