# Sync-First + DB-Read (shared pattern)

Single source of truth for how the data-syncing skills stay current. Every skill
that reports portfolio, margin, dividend, transaction, or expense facts follows
this exact process. Defined once here so the skills point at it instead of
restating it.

## The rule

The local SQLite database `family_office.db` (`DATABASE_URL=sqlite:///family_office.db`)
is the store of record for financial facts. Stale snapshots are the failure this
pattern eliminates (the retired CSVs were routinely 3+ weeks old). So:

1. _Step 0: Refresh (mandatory, every run)._ Trigger a fresh sync into the DB
   BEFORE reading anything.
2. _Then read from the DB._ All facts come from the tables below, never from a
   downloaded CSV on the primary path.

_Completion criterion (checkable):_ _"DB refreshed this run before any read."_
If a skill reports numbers without having refreshed the DB in the same run, the
run is not complete.

## Step 0: Refresh

Run the single refresh entrypoint. It syncs every source in order, each isolated
so one broker hiccup does not block the others:

```bash
uv run python -m src.integrations.refresh_all            # refresh all sources
uv run python -m src.integrations.refresh_all --months 3 # narrow the expense window
uv run python -m src.integrations.refresh_all --show     # print DB snapshot, no sync
```

It exits 0 only when every source succeeds, and 1 if any source fails. It prints
a per-source `ok` / `error` line. A partial refresh still attempts every source.
Read the output: if a source a skill depends on shows `error`, surface that and
do not report its saved facts as fresh. `--show` only displays saved data. Its
zero exit does not prove that a refresh ran or succeeded.

### Targeted refresh (when a skill needs only one source)

| Source | Command | Writes DB table(s) |
|--------|---------|--------------------|
| Positions + balances | `uv run python -m src.integrations.snaptrade.sync_db` | `positions`, `balances` |
| Investment activities | `uv run python -m src.integrations.snaptrade.sync_transactions_db` | `transactions` |
| Card / bank expenses | `uv run python -m src.integrations.simplefin.sync_expenses_db [--months N]` | `bank_transactions` |

Each also accepts `--show` to print its slice of the DB without syncing.

## DB tables (read these)

| Table | Written by | Semantics | Key columns |
|-------|-----------|-----------|-------------|
| `positions` | SnapTrade positions sync | Snapshot (replaced each sync), one row per ticker | `account_id, symbol, instrument, quantity, avg_cost, price, synced_at` |
| `balances` | SnapTrade balances sync | Snapshot (one row per account) | `account_id, settled_cash, buying_power, account_equity, gross_market_value, margin_debt, synced_at` |
| `transactions` | SnapTrade activities sync | Append-only history, idempotent via `dedupe_key` | `account_id, date, type, symbol, description, amount, quantity, currency, synced_at` |
| `bank_transactions` | SimpleFIN expenses sync | Upsert on `(account_id, txn_id)`, kept current | `account_id, account_name, org, txn_id, date, posted_ts, payee, description, amount, direction, category, synced_at` |

`margin_debt` is derived (gross market value minus net equity); SnapTrade does not
expose the loan directly. It tracks Fidelity "Net debit" within ~0.1%.

## Freshness check

After Step 0, require a successful result for each source the analysis needs,
and confirm that it synced the required accounts. An `ok` alone does not prove
account coverage. Keep the result with the analysis date and data source. Do not
use a table's `MAX(synced_at)` alone as proof of a successful refresh.

Positions and balances are snapshots. The combined refresh must print a
`generation` for positions, not `no enabled, routed account synced`. To confirm
specific accounts, use the targeted refresh commands above and check their
per-account output. Both SnapTrade commands print `no syncable accounts` when
the configuration routes no accounts. That is not fresh data for an analysis
that requires an account.

Transaction history is append-only. A successful targeted refresh can report
`N fetched, 0 new, N duplicates skipped` for a required account. It adds no rows,
so row timestamps can stay unchanged. An empty history also has no row timestamp.
Neither case proves a refresh failure. The combined `transactions: ok` line does
not show which accounts synced, so use the targeted command to confirm coverage.

This query shows the latest stored row timestamps for context. It is not a
refresh success check:

```bash
sqlite3 family_office.db "SELECT 'balances', MAX(synced_at) FROM balances
  UNION ALL SELECT 'transactions', MAX(synced_at) FROM transactions
  UNION ALL SELECT 'bank_transactions', MAX(synced_at) FROM bank_transactions;"
```

## CSV fallback (manual only)

The Fidelity / Vanguard CSV paths still exist for reconciliation and for sources
not yet live (see `retirement-syncing`). They are an explicit, opt-in fallback,
never the primary path. Reach for a CSV only when a live source is down or a skill
documents CSV as its only option.
