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

After Step 0, require a successful result for each source the analysis needs.
Keep that result with the analysis date and data source. Do not use a table's
`MAX(synced_at)` alone as proof that the source refreshed successfully.

Positions and balances are snapshots. Inspect their generation timestamp and
the refresh output for the accounts the analysis needs. Transaction history is
append-only. A successful refresh that fetches only duplicate activities adds
no rows, so its row timestamps can stay unchanged. An empty history also has no
row timestamp. Neither case proves a refresh failure.

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
