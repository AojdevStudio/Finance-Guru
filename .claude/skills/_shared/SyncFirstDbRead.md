# Sync-First + DB-Read (shared pattern)

Single source of truth for how the data-syncing skills stay current. Every skill
that reports portfolio, margin, dividend, transaction, or expense facts follows
this exact process. Defined once here so the skills point at it instead of
restating it.

## The rule

The local SQLite database `family_office.db` (`DATABASE_URL=sqlite:///family_office.db`)
is the store of record for financial facts. Stale snapshots are the failure this
pattern eliminates (the retired CSVs were routinely 3+ weeks old). So:

1. **Step 0: Refresh (mandatory, every run).** Trigger a fresh sync into the DB
   BEFORE reading anything.
2. **Then read from the DB.** All facts come from the tables below, never from a
   downloaded CSV on the primary path.

**Completion criterion (checkable):** _"DB refreshed this run before any read."_
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

It exits 0 when any source succeeds and prints a per-source `ok` / `error` line.
Read the output: if a source a skill depends on shows `error`, surface that (do
not report its facts as fresh).

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

After Step 0, confirm the tables carry this run's timestamp before reading:

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
