---
title: Margin Dashboard Update
cadence: weekly
owner: Ossie
last-reviewed: 2026-07-27
---

# Margin Dashboard Update

## Purpose

Refresh the Margin Dashboard from live SnapTrade balances so interest estimates,
coverage ratios, and portfolio-to-margin alerts use current account equity and
holdings.

## When to run

- _Every Monday_ before 9:00 AM ET
- _Any time_ after a large margin draw (≥5% of portfolio value)
- _Before_ a planned margin-heavy trade

## Prerequisites

- The four `SNAPTRADE_*` values are present in the project-root `.env`
- The intended margin account is enabled and routed in
  `config/snaptrade-accounts.yaml`
- `fin-core` skill auto-loaded (happens at session start via hook)
- `.env` contains `FG_MARGIN_INTEREST_RATE_DECIMAL` or
  `FG_MARGIN_INTEREST_RATE`, plus `FG_MARGIN_JUMP_ALERT_THRESHOLD`
- The previous Dashboard margin balance is available for jump detection
- The Dividend Tracker is current if a coverage ratio is required; pass its current
  monthly income with `--monthly-dividend-income` or configure
  `FG_DIVIDEND_MONTHLY_INCOME`

The margin metrics adapter reads the first enabled and routed account in the
routing file. Put the intended margin account first; do not enable multiple
accounts and assume the adapter aggregates them.

## Steps

1. _Establish the update date_:

   ```bash
   date
   ```

2. _Calculate live metrics_:

   ```bash
   uv run python -m src.analysis.margin_metrics --pretty
   ```

3. _Confirm the source_ — `source_file` must be
   `snaptrade:<expected-account-id>`.

4. _Review the live fields_:
   - `portfolio_value`: SnapTrade net account equity
   - `margin_balance`: gross long market value minus net account equity
   - `margin_buying_power`: current buying power when the broker provides it
   - `monthly_interest_cost`: margin balance × configured annual rate ÷ 12
   - `coverage_ratio`: configured monthly dividend income ÷ monthly interest
   - `portfolio_margin_ratio`: portfolio value ÷ margin balance

5. _Compare with the previous Dashboard row_. SnapTrade does not provide the day
   change through this bridge, so `margin_day_change` is `null`. Calculate the
   change from the previous Sheet value and stop for confirmation when it exceeds
   `FG_MARGIN_JUMP_ALERT_THRESHOLD`.

6. _Invoke the `margin-management` skill_ and review its safety and scaling gates.
   The CLI's `alert_status` describes the calculated portfolio-to-margin ratio:

   | Status | CLI condition |
   | --- | --- |
   | `no_margin` | No margin debt |
   | `green` | Ratio ≥ 4.0 |
   | `yellow` | 3.0 ≤ ratio < 4.0 |
   | `red` | 2.5 ≤ ratio < 3.0 |
   | `critical` | Ratio < 2.5 |

   The skill may apply stricter action gates than these display bands.

7. _Update the Margin Dashboard_ only after the comparison passes. Append the
   date, margin balance, configured rate, calculated monthly cost, and operational
   note without modifying protected formulas.

## Verification

- `source_file` identifies the expected SnapTrade account
- The Dashboard shows today's date in the last-updated cell
- The written margin balance and monthly cost match the CLI JSON
- Coverage ratio matches the supplied monthly dividend income, or remains `null`
  when no income was supplied
- No formula errors appear in calculated columns
- If you took an action, the notes block has one new row

## Live-data constraints

- SnapTrade does not expose the margin loan directly. The bridge derives it from
  holdings and account equity, including the 100-share multiplier for options.
- `margin_interest_accrued_this_month` is `null` under SnapTrade. Use
  `monthly_interest_cost` as the configured-rate estimate; do not label it as the
  broker's accrued charge.
- `margin_day_change` and buying-power day change are also unavailable live.
- If account equity is absent, the command fails instead of estimating a margin
  balance.

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| Missing environment-key error | Add every named `SNAPTRADE_*` key to `.env` |
| No enabled and routed account | Verify both `enabled: true` and a non-`unassigned` role in the routing YAML |
| Wrong account in `source_file` | Reorder or disable routes; the adapter uses the first syncable account |
| `SnapTrade did not return account equity` | Disable the route and use a fresh broker CSV fallback while investigating |
| Margin balance differs from broker | Compare equities, options, SPAXX, and net equity before updating the Sheet |
| Coverage ratio shows `#N/A` | A GOOGLEFINANCE formula is lagging; wait 60s and retry, or invoke `formula-protection` to repair |
| Large Draw Alert for a draw you didn't make | Audit the transaction immediately; could be an unauthorized pull |
| Yellow band persists for 3+ weeks | Review scaling plan with strategy-advisor — portfolio may have drifted from target |

## CSV fallback

When SnapTrade is unavailable or fails reconciliation, read the latest Fidelity
balances export:

```bash
uv run python -m src.analysis.margin_metrics --source csv --pretty
```

To select a specific file:

```bash
uv run python -m src.analysis.margin_metrics \
  --source csv \
  --csv notebooks/updates/Balances_for_Account_example.csv \
  --pretty
```

The CSV path can populate accrued interest and day-change fields when those rows
exist. See
[Broker CSV Inputs and Fallbacks](../guides/required-csv-uploads.md).

## Related skills

- `margin-management` — primary skill for this runbook
- `formula-protection` — guards the sacred GOOGLEFINANCE formulas
- `PortfolioSyncing` — refresh positions alongside balances if both are stale
- `fin-guru-checklist` — weekly quality checklist includes margin dashboard freshness
