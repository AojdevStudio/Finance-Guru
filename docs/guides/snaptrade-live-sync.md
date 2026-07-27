---
title: "SnapTrade Live Sync"
description: "Configure and operate the read-only SnapTrade bridge"
category: guides
---

# SnapTrade Live Sync

SnapTrade is the preferred source for current taxable-account positions, balances,
transactions, and dividends. The integration replaces recurring broker exports
without replacing the Google Sheets DataHub or its safety checks.

## Architecture

```text
SnapTrade API
    |
    v
read-only Python wrapper
    |
    v
normalized CLI JSON
    |
    v
Finance Guru skills and safety gates
    |
    v
Google Sheets DataHub
```

The CLI in `src/integrations/snaptrade/` is stateless and read-only at the broker.
It does not register users, open the Connection Portal, place trades, or write to
Google Sheets. Sheet writes remain the responsibility of the relevant skill through
the `gdrive` MCP server.

## Prerequisites

- An existing linked SnapTrade user. This repository reuses credentials provisioned
  by the existing SnapTrade connection; it cannot create or repair that connection.
- The four `SNAPTRADE_*` values in the project-root `.env`.
- A known-good broker export for the one-time account cutover check.
- `gdrive` configured only if the resulting data will be written to Google Sheets.

See [API Key Acquisition Guide](../setup/api-keys.md#snaptrade-live-sync) for
credential details.

## Configure the bridge

### 1. Add credentials

Add these values to `.env`; never add real values to `.env.example`:

```dotenv
SNAPTRADE_CLIENT_ID=your_snaptrade_client_id_here
SNAPTRADE_CONSUMER_KEY=your_snaptrade_consumer_key_here
SNAPTRADE_USER_ID=your_snaptrade_user_id_here
SNAPTRADE_USER_SECRET=your_snaptrade_user_secret_here
```

### 2. Discover and probe accounts

```bash
uv run python -m src.integrations.snaptrade.cli accounts --probe --output json
```

The probe checks account visibility, balance rows, SPAXX representation, and cost
basis coverage. Its output contains account and portfolio metadata; do not commit
or paste the output into issues.

### 3. Generate routing configuration

```bash
uv run python -m src.integrations.snaptrade.cli accounts \
  --write-config config/snaptrade-accounts.yaml \
  --output json
```

The command fails if the file already exists. `--force` overwrites it, so use that
flag only when intentionally rebuilding all account routes.

New routes are fail-closed:

```yaml
accounts:
  - snaptrade_account_id: "example-account-id"
    name: "Example Brokerage Account"
    institution: "Example Brokerage"
    role: "unassigned"
    enabled: false
```

`config/snaptrade-accounts.yaml` is gitignored. The committed
`config/snaptrade-accounts.example.yaml` documents the shape.

### 4. Verify and enable each account

Compare the probe, positions, and balances with a known-good broker export. Only
after they reconcile:

1. Set `role` to `taxable_cash`, `taxable_margin`, `retirement`, or `watch_only`.
2. Set `enabled: true`.
3. Leave unverified accounts disabled or unassigned.

An account is fetched only when both conditions are satisfied. If no account is
syncable, routed commands return a successful response with refused-account details
and do not initialize the SnapTrade client.

Retirement Sheet conversion is still deferred; keep using retirement CSV workflows
until that account type has been explicitly reconciled.

## Read live data

All routed commands default to JSON and accept `--output text|json|yaml`:

```bash
# Equities and options
uv run python -m src.integrations.snaptrade.cli positions --output json

# Cash, buying power, account equity, and derived margin debt
uv run python -m src.integrations.snaptrade.cli balances --output json

# Full paginated transaction and dividend history
uv run python -m src.integrations.snaptrade.cli activities --output json
```

Use `--config path/to/config.yaml` when the routing file is not at
`config/snaptrade-accounts.yaml`.

### Output contracts

| Command | Normalized data |
| --- | --- |
| `positions` | `symbol`, `quantity`, `average_purchase_price`, `price`, `instrument`; options also include `occ_symbol` |
| `balances` | `currency`, `settled_cash`, `buying_power`, `account_equity`, `gross_market_value`, `margin_debt` |
| `activities` | `type`, `date`, `symbol`, `amount`, `quantity`, `currency`, `description`, `account` |

Each routed response also reports `synced_account_count`, `refused_account_count`,
successful account payloads, and refusal reasons.

## Data-source boundaries

| Data | Preferred source | CSV status |
| --- | --- | --- |
| Taxable positions | SnapTrade `positions` | Cutover verification and fallback |
| Taxable balances | SnapTrade `balances` | Fallback through `margin_metrics --source csv` |
| Transactions | SnapTrade `activities` | Retained until activity reconciliation is complete |
| Realized dividends | SnapTrade `activities`, filtered to `DIVIDEND` | Retained until activity reconciliation is complete |
| Retirement holdings | Existing Vanguard/Fidelity exports | Current workflow |

The SessionStart hook does not perform a live broker call. Live facts are fetched on
demand by the CLI or a skill that invokes it.

## Known constraints

- SnapTrade does not expose margin debt directly. Finance Guru derives it as gross
  long market value minus net account equity and clamps the result to zero.
- Option cost basis is normalized from per-contract to per-share values. The output
  price is treated as per-share, and market value calculations apply the 100-share
  contract multiplier.
- SnapTrade does not provide accrued margin interest or day changes to this bridge.
  Those fields are `null` in live margin metrics.
- Activities are fetched across all pages. Google Sheets remains the deduplication
  ledger; the bridge creates no local cache.
- A dividend with no symbol may use a ticker parsed from its description. Reconcile
  unfamiliar broker descriptions before writing them to the Sheet.

## Operational workflow

1. Establish the date with `date`.
2. Run the relevant live CLI command and review refusals or missing fields.
3. Invoke `PortfolioSyncing`, `TransactionSyncing`, `dividend-tracking`, or
   `margin-management`.
4. Review safety-gate diffs before approving Sheet writes.
5. Verify the target Sheet and its formulas after the write.

## Troubleshooting

| Symptom | Cause and action |
| --- | --- |
| `Missing required SnapTrade environment keys` | Add every named key to the project-root `.env`, then restart the command |
| `SnapTrade routing config not found` | Generate `config/snaptrade-accounts.yaml` with the `accounts --write-config` command |
| Zero synced accounts | Inspect `refused`; each account needs `enabled: true` and a non-`unassigned` role |
| `Config already exists` | Edit the existing routes; use `--force` only when a full replacement is intended |
| Margin debt differs from the broker | Disable the route and compare positions, options, SPAXX, and net equity with a fresh broker export |
| Missing or unexpected activity symbol | Reconcile the activity description before writing; description parsing is a fallback heuristic |

## Security

- `.env` and `config/snaptrade-accounts.yaml` are gitignored.
- The wrapper masks account numbers and never serializes credentials.
- CLI output still contains sensitive holdings, values, and account identifiers.
- SnapTrade calls an external API; only credentials and routing configuration remain
  local.

## Related documentation

- [SnapTrade architecture decision](../adr/0001-snaptrade-live-sync-for-legacy-finance-guru.md)
- [Required CSV Uploads](required-csv-uploads.md)
- [Portfolio Sync runbook](../runbooks/portfolio-sync.md)
- [Margin Dashboard Update runbook](../runbooks/margin-dashboard-update.md)
