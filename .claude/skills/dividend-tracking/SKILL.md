---
name: dividend-tracking
description: Refresh the local DB, then read and analyze DIVIDEND rows from family_office.db for Layer 2 income tracking. Sync-first so dividend income is never stale; symbol resolution for null tickers is handled in the activities sync. Triggers on sync dividends, update dividends, dividend tracker, layer 2 income, or monthly dividend analysis.
---

# Dividend Tracking

## Purpose

Read received-dividend records from the local DB `transactions` table (refreshed sync-first) and report Layer 2 income against target.

`family_office.db` is the system of record. The Dividends sheet and its Apps Script automation were retired 2026-07-31.

## Step 0: Refresh (sync-first, mandatory)

Dividend records come from the DB, refreshed FIRST so income can never be stale. Follow the shared **[Sync-First + DB-Read](../_shared/SyncFirstDbRead.md)** pattern.

```bash
uv run python -m src.integrations.snaptrade.sync_transactions_db          # writes transactions
uv run python -m src.integrations.snaptrade.sync_transactions_db --show   # confirm freshness
```

Completion criterion: _the sync command reports success before any dividend is read._

**Do not gate on `MAX(synced_at)` advancing.** The activities sync is idempotent
via `dedupe_key` and only stamps rows it actually writes, so a run that finds no
new activity leaves the timestamp untouched. Verified 2026-08-04: the sync
reported `2690 fetched, 0 new, 2690 duplicates skipped` and `MAX(synced_at)`
stayed at the prior run's value. That is a healthy no-op, not a stale table.

Read the command's own output line instead:

- `N new` greater than 0, timestamp advances → new activity ingested.
- `0 new, N duplicates skipped` → already complete, timestamp correctly unchanged.
- Command errors or reports nothing → genuine failure, stop.

Completeness is guaranteed by the dedupe key, not by the stamp.

**Month-end lag:** distributions post over several days, so the current month is
incomplete until roughly the 3rd or 4th of the following month. On 2026-07-31,
July read $1,346 across 30 payments; the month actually closed at **$1,570 across
42**. Never compare a partial current month against completed prior months, and
never call a month-over-month decline until the month has closed.

## Reading dividends

```bash
sqlite3 family_office.db \
  "SELECT date, symbol, amount, description FROM transactions WHERE type = 'DIVIDEND' ORDER BY date;"
```

Each row carries `date`, `symbol`, `amount`, and `description`. **Null-symbol dividends already have a ticker resolved** during the activities sync (parsed from the `description`, for example `... ETF (SCHD)`, mirroring the positions/options symbol fallback), so `symbol` is reliable.

Dedupe needs no external ledger: the activities sync is idempotent via `dedupe_key`, so re-running never double-counts.

## Monthly analysis

Aggregate by ticker and month:

```bash
sqlite3 family_office.db \
  "SELECT strftime('%Y-%m', date) AS month, symbol, ROUND(SUM(amount), 2) AS received
   FROM transactions WHERE type = 'DIVIDEND'
   GROUP BY month, symbol ORDER BY month DESC, received DESC;"
```

Monthly total against the Layer 2 target:

```bash
sqlite3 family_office.db \
  "SELECT strftime('%Y-%m', date) AS month, ROUND(SUM(amount), 2) AS total
   FROM transactions WHERE type = 'DIVIDEND' GROUP BY month ORDER BY month DESC LIMIT 12;"
```

## Evaluation standard

- Judge holdings on **trailing 12-month yield**, not month-to-month distribution changes.
- **±5-15% monthly distribution variance is NORMAL** for options-based funds. Do not flag it as risk.
- **Sell triggers are red flags only:** sustained decline greater than 30%, NAV erosion, or a strategy change. Not normal variance.

## Margin coverage

Dividend income against margin interest is the coverage ratio that drives the scaling triggers. See the `margin-management` skill; do not recompute the thresholds here.

## CSV fallback

`notebooks/updates/dividend.csv` (the Fidelity dividend view export) remains a manual reconciliation source if the live activities sync is unavailable. It is not the primary path.

## Reference Files

- **User Profile**: `fin-guru/data/user-profile.yaml`
- **Sync-first pattern**: `.claude/skills/_shared/SyncFirstDbRead.md`
- **Income vehicle framework**: `fin-guru/data/modern-income-vehicles.md`

---

_Educational purposes only. Not investment advice. Dividend distributions are not guaranteed, past yield does not predict future income, and options-based income funds carry risk of principal loss. Consult licensed financial and tax professionals before acting._

_Skill Type_: Domain (workflow guidance)
_Enforcement_: SUGGEST
_Priority_: High
