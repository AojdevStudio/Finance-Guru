---
title: Margin Dashboard Update
cadence: weekly
owner: Family Office Owner
last-reviewed: 2026-07-20
---

# Margin Dashboard Update

## Purpose

Keep the Margin Dashboard in the Google Sheets DataHub current with live SnapTrade balances, so margin cost, coverage, and safety alerts reflect current account data.

## When to run

- _Every Monday_ before 9:00 AM ET
- _After_ any margin draw or account change that may exceed `FG_MARGIN_JUMP_ALERT_THRESHOLD`
- _Before_ a planned margin-heavy trade

## Prerequisites

- The four `SNAPTRADE_*` credentials from `.env.example` are set in local `.env`
- `config/snaptrade-accounts.yaml` contains an enabled, role-assigned account
- `FG_MARGIN_INTEREST_RATE_DECIMAL` and `FG_MARGIN_JUMP_ALERT_THRESHOLD` are set in local `.env`
- `fin-core` skill auto-loaded (happens at session start via hook)
- You know your current margin target range (see `fin-guru/data/user-profile.yaml`)

## Steps

1. _Calculate live metrics_:

   ```bash
   uv run python -m src.analysis.margin_metrics --pretty
   ```

   The command uses the first enabled and role-assigned account in `config/snaptrade-accounts.yaml`. If more than one account is syncable, confirm the reported `source_file` identifies the intended margin account.

2. _Validate the source and fields_:
   - `source_file` starts with `snaptrade:`
   - `portfolio_value` is SnapTrade net account equity
   - `margin_balance` is derived as gross market value minus net equity
   - `margin_interest_accrued_this_month` and `margin_day_change` are `null` because SnapTrade does not expose them

3. _Compare with the previous dashboard entry_. If the margin balance increased by more than `FG_MARGIN_JUMP_ALERT_THRESHOLD`, stop and confirm the draw before writing to Google Sheets.

4. _Review the CLI health metrics_:
   - `portfolio_margin_ratio` ≥4.0: `green`
   - 3.0–<4.0: `yellow`
   - 2.5–<3.0: `red`
   - <2.5: `critical`
   - No margin balance: `no_margin`
   - `coverage_ratio` is monthly dividend income divided by monthly interest cost; it is `null` when dividend income is unavailable or interest cost is zero

   These bands describe the implemented CLI `alert_status`; they do not replace the stricter strategy gates. The `margin-management` skill pauses scaling below 3.5 and stops draws below 3.0.

5. _Invoke the margin-management skill_ in Claude Code:

   ```
   /margin-management
   ```

6. _Act on alerts_:
   - If a _Margin Jump Alert_ fires, read the triggering transaction and confirm intent
   - If a _Scaling Threshold_ alert fires, review the time-based scaling recommendation

7. _Approve the dashboard write_, then append one line to the weekly notes block with date, ratios, data source, and any action taken.

## Verification

- Google Sheets DataHub → _Margin Dashboard_ tab shows today's date in the last-updated cell
- Dashboard balance and calculated monthly interest cost match the CLI JSON
- Coverage ratio matches the CLI when available; if it is unavailable, record whether dividend income is missing or interest cost is zero
- Coverage ratio does not contain a formula error such as `#N/A` or `#DIV/0!`
- No formula errors in the calculated columns (the formula-protection skill will have flagged any)
- If you took an action, the notes block has one new row

## CSV fallback

Use the legacy Fidelity export only when SnapTrade is unavailable or an exact broker-reported debit or accrued-interest value is required:

```bash
uv run python -m src.analysis.margin_metrics --source csv --pretty
```

This selects the newest `notebooks/updates/Balances_for_Account_*.csv` by modification time. To remove ambiguity, pass a specific file:

```bash
uv run python -m src.analysis.margin_metrics \
  --csv notebooks/updates/Balances_for_Account_EXAMPLE.csv \
  --pretty
```

Record the fallback source in the dashboard notes.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `Missing required SnapTrade environment keys` | Add all four `SNAPTRADE_*` values to local `.env`; never commit that file |
| `SnapTrade routing config not found` | Run the account discovery and routing setup in the [Portfolio Sync](portfolio-sync.md) runbook |
| `No SnapTrade account is enabled+routed` | Verify both the account role and `enabled: true`; the integration fails closed |
| Wrong account appears in `source_file` | Reorder or disable routing entries so the intended margin account is the first syncable account |
| SnapTrade does not return account equity | Do not calculate derived margin debt; retry later or use the CSV fallback |
| `No Fidelity balances CSV found matching ...` | Re-check the exact `Balances_for_Account_*.csv` filename or pass `--csv` explicitly |
| Coverage ratio shows `#N/A` | A GOOGLEFINANCE formula is lagging; wait 60s and retry, or invoke `formula-protection` to repair |
| Margin Jump Alert for a draw you didn't make | Audit the transaction immediately; could be an unauthorized pull |
| Portfolio-to-margin ratio is below 3.5 | Pause scaling and review the strategy with strategy-advisor |

## Related skills

- `margin-management` — primary skill for this runbook
- `formula-protection` — guards the sacred GOOGLEFINANCE formulas
- `PortfolioSyncing` — refresh positions alongside balances if both are stale
- `fin-guru-checklist` — applies the margin-strategy and general-quality checklists

## Related reference

- [SnapTrade bridge ADR](../adr/0001-snaptrade-live-sync-for-legacy-finance-guru.md)
- [Portfolio Sync](portfolio-sync.md)
