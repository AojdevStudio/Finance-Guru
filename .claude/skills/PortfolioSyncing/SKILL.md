---
name: portfolio-syncing
description: Refresh positions and balances from SnapTrade into family_office.db, then validate the snapshot. Reads live positions, cost basis, SPAXX, and margin from the DB (never a stale CSV). USE WHEN user mentions sync portfolio OR update positions OR portfolio-sync OR refresh positions OR downloaded from Fidelity.
---

# PortfolioSyncing

Refresh positions and balances from SnapTrade into `family_office.db`, then validate the snapshot against safety thresholds before anyone reasons off it.

`family_office.db` is the system of record. The Google Sheets DataHub was retired 2026-07-31; there is no spreadsheet to push to and no gdrive MCP configured.

## Step 0: Refresh (sync-first, mandatory)

Positions and balances come from the local DB, refreshed FIRST so it can never be stale. Follow the shared **[Sync-First + DB-Read](../_shared/SyncFirstDbRead.md)** pattern.

```bash
uv run python -m src.integrations.snaptrade.sync_db          # writes positions + balances
uv run python -m src.integrations.snaptrade.sync_db --show   # read back the snapshot
```

Completion criterion: _the `positions` and `balances` tables carry this run's `synced_at`._ Everything downstream reads the DB, not a CSV.

To refresh positions, transactions, and bank expenses together:

```bash
uv run python -m src.integrations.refresh_all
```

## Account Routing

`config/snaptrade-accounts.yaml` declares each account's `role` and `enabled` flag. An account with no declared role refuses to sync rather than guessing. Cash-management accounts belong to SimpleFIN (`TransactionSyncing`), not here, so brokerage margin math stays clean.

## Safety Gates

> ⚠️ **Capture the "before" state first, or these gates cannot fire.** `sync_db`
> is a current-state store: it deletes each account's prior position rows and
> overwrites its single `balances` row (which is keyed on `account_id`). No
> history survives the refresh, so read the existing snapshot **before** running
> Step 0 and hold it in the session to diff against. There is no
> `position_history` table to fall back on.

```bash
# BEFORE Step 0 — capture the prior generation
sqlite3 family_office.db \
  "SELECT symbol, quantity, average_purchase_price FROM positions ORDER BY symbol;"
sqlite3 family_office.db "SELECT * FROM balances;"
```

**STOP conditions** (require user confirmation):

1. Fewer tickers than the previous snapshot (possible sales)
2. Any quantity change > 10%
3. Any cost basis change > 20%
4. Margin balance jumped > $5,000 (unintentional draw)
5. SPAXX discrepancy > $100 against the balances row

**FLAG conditions** (alert but proceed): SPAXX off by $1-$100; pending activity off by more than $100.

**When STOPPED**: show a clear diff table, ask the user to confirm, proceed only after explicit approval.

## Cash Position Logic

- Do NOT use the `SPAXX` position value; it shows only settled money market.
- Use **"Settled cash"** from the balances row for the SPAXX figure.
- If settled cash is 0, SPAXX is $0 (all funds invested or in margin).
- "Cash market value" is NOT cash; it is the value of positions held in the Cash account rather than the Margin account.

## Layer Classification for New Tickers

Dividend funds → Layer 2, growth → Layer 1, hedges → Layer 3. If a new ticker does not clearly match a pattern, mark it `UNKNOWN - Manual Review Required` and ask the user rather than guessing.

## CSV Fallback

CSV import is a fallback and re-verification path only, not the primary flow. The `IngestPositions` workflow archives `Portfolio_Positions_*.csv` and `Balances_*.csv` from `~/Downloads` into `notebooks/updates/`. Use it when a live source is down or the user explicitly wants an archive.

Classifier for Fidelity position exports: a header containing `Ex-date` is the dividend view; a header containing `Average Cost Basis` is the regular view. The dividend view and transaction history CSVs are still consumed by `dividend-tracking` and `TransactionSyncing`.

## Pre-Flight Checklist

- [ ] SnapTrade account is enabled and routed in `config/snaptrade-accounts.yaml`
- [ ] `SNAPTRADE_*` keys are present in `.env`
- [ ] `DATABASE_URL` is set in `.env`

## Reference Files

- **User Profile**: `fin-guru/data/user-profile.yaml`
- **Account routing**: `config/snaptrade-accounts.yaml`
- **Sync-first pattern**: `.claude/skills/_shared/SyncFirstDbRead.md`

---

**Skill Type**: Domain (workflow guidance)
**Enforcement**: BLOCK (data integrity critical)
**Priority**: Critical
