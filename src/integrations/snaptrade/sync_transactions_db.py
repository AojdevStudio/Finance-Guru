#!/usr/bin/env python3
"""Sync live SnapTrade activities (transaction history) into the local SQLite DB.

Replaces the retired Google Sheets Transactions tab. Target is DATABASE_URL
(``sqlite:///family_office.db``). Read-only against SnapTrade; only local writes.

    uv run python -m src.integrations.snaptrade.sync_transactions_db          # sync
    uv run python -m src.integrations.snaptrade.sync_transactions_db --show   # summary

Accumulate semantics: transaction history is append-only outside the identity
migration. The UNIQUE key uses SnapTrade's activity identity. On the first sync,
matching legacy natural keys are updated in place. A redundant legacy row is
removed only if its provider-keyed replacement already exists. Re-running the
migration is a no-op.

Expense-Tracker routing is intentionally NOT implemented: SnapTrade activities
carry no DEBIT CARD PURCHASE records (types are BUY/SELL/DIVIDEND/JOURNALED/
WITHDRAWAL/CONTRIBUTION/...), and the Budget Planner destination lived in the
retired Sheet. ponytail: add categorized-expense routing only if a debit-card
data source appears.
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.config.instance_paths import InstancePaths, _db_path, load_instance_env
from src.integrations.snaptrade.client import (
    SnapTradeAPIError,
    SnapTradeClientWrapper,
    SnapTradeDataError,
    canonical_activity_date,
)
from src.integrations.snaptrade.models import SnapTradeAccountsConfig

_SCHEMA = """
CREATE TABLE IF NOT EXISTS transactions (
    account_id  TEXT NOT NULL,
    date        TEXT,
    type        TEXT,
    symbol      TEXT,
    description TEXT,
    amount      REAL,
    quantity    REAL,
    currency    TEXT,
    dedupe_key  TEXT NOT NULL UNIQUE,
    synced_at   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_txn_date ON transactions(date);
CREATE INDEX IF NOT EXISTS idx_txn_type ON transactions(type);
"""


def _dedupe_key(account_id: str, a: dict[str, Any]) -> str:
    """Provider identity key that keeps identical executions distinct."""
    activity_id = a.get("id")
    if activity_id is None or not str(activity_id).strip():
        raise ValueError("Normalized SnapTrade activity is missing id")
    return f"snaptrade|{account_id}|{str(activity_id).strip()}"


def _natural_dedupe_key(account_id: str, a: dict[str, Any]) -> str:
    """Return the pre-provider-identity key for idempotent row migration."""
    parts = [
        account_id,
        str(a.get("date") or ""),
        str(a.get("type") or ""),
        str(a.get("amount") if a.get("amount") is not None else ""),
        str(a.get("symbol") or ""),
        str(a.get("quantity") if a.get("quantity") is not None else ""),
        str(a.get("description") or ""),
    ]
    return "|".join(parts)


def _migrate_natural_dedupe_keys(
    connection: sqlite3.Connection,
    account_id: str,
    activities: list[dict[str, Any]],
) -> int:
    """Replace matching legacy keys with deterministic provider identity keys."""
    replacements: dict[str, list[tuple[str, str]]] = {}
    for activity in activities:
        replacements.setdefault(_natural_dedupe_key(account_id, activity), []).append(
            (_dedupe_key(account_id, activity), str(activity["date"]))
        )

    migrated = 0
    legacy_rows = connection.execute(
        "SELECT rowid, date, type, symbol, description, amount, quantity, currency "
        "FROM transactions WHERE account_id = ? AND dedupe_key NOT LIKE 'snaptrade|%'",
        (account_id,),
    ).fetchall()
    for legacy_row in legacy_rows:
        try:
            legacy_date = canonical_activity_date(legacy_row[1]).isoformat()
        except SnapTradeDataError:
            continue
        legacy_activity = {
            "date": legacy_date,
            "type": legacy_row[2],
            "symbol": legacy_row[3],
            "description": legacy_row[4],
            "amount": legacy_row[5],
            "quantity": legacy_row[6],
            "currency": legacy_row[7],
        }
        candidates = replacements.get(
            _natural_dedupe_key(account_id, legacy_activity), []
        )
        if not candidates:
            continue
        target = next(
            (
                candidate
                for candidate in sorted(set(candidates))
                if connection.execute(
                    "SELECT 1 FROM transactions WHERE dedupe_key = ?",
                    (candidate[0],),
                ).fetchone()
                is None
            ),
            None,
        )
        if target is None:
            connection.execute(
                "DELETE FROM transactions WHERE rowid = ?",
                (legacy_row[0],),
            )
        else:
            connection.execute(
                "UPDATE transactions SET dedupe_key = ?, date = ? WHERE rowid = ?",
                (target[0], target[1], legacy_row[0]),
            )
        migrated += 1
    return migrated


def sync(config_path: Path, database_url: str | None) -> dict[str, Any]:
    """Pull full activity history and accumulate new rows into the local DB."""
    config = SnapTradeAccountsConfig.from_path(config_path)
    syncable = config.syncable
    db = _db_path(database_url)
    now = datetime.now(UTC).replace(microsecond=0).isoformat()

    summary: dict[str, Any] = {"db": str(db), "accounts": [], "synced_at": now}
    conn = sqlite3.connect(db)
    try:
        conn.executescript(_SCHEMA)
        if not syncable:
            return summary
        client = SnapTradeClientWrapper.from_env()
        for account in syncable:
            aid = account.snaptrade_account_id
            activities = client.get_activities(aid)
            with conn:
                migrated = _migrate_natural_dedupe_keys(conn, aid, activities)
                before = conn.total_changes
                conn.executemany(
                    "INSERT OR IGNORE INTO transactions "
                    "(account_id, date, type, symbol, description, amount, quantity, "
                    "currency, dedupe_key, synced_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                    [
                        (
                            aid,
                            a.get("date"),
                            a.get("type"),
                            a.get("symbol"),
                            a.get("description"),
                            a.get("amount"),
                            a.get("quantity"),
                            a.get("currency"),
                            _dedupe_key(aid, a),
                            now,
                        )
                        for a in activities
                    ],
                )
            inserted = conn.total_changes - before
            summary["accounts"].append(
                {
                    "account_id": aid,
                    "name": account.name,
                    "role": str(account.role),
                    "fetched": len(activities),
                    "inserted": inserted,
                    "skipped_duplicates": len(activities) - inserted,
                    "migrated_legacy_keys": migrated,
                }
            )
    finally:
        conn.close()
    return summary


def show(database_url: str | None) -> None:
    """Print a summary of the transactions table."""
    db = _db_path(database_url)
    if not db.exists():
        print(f"No DB at {db}", file=sys.stderr)
        return
    conn = sqlite3.connect(db)
    try:
        conn.row_factory = sqlite3.Row
        total = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
        rng = conn.execute("SELECT MIN(date), MAX(date) FROM transactions").fetchone()
        print(f"# {db}\n{total} transactions | {rng[0]} -> {rng[1]}")
        print("\nby type:")
        for r in conn.execute(
            "SELECT type, COUNT(*) n, ROUND(SUM(amount),2) total FROM transactions "
            "GROUP BY type ORDER BY n DESC"
        ):
            activity_type = r["type"] or "unknown"
            print(f"  {activity_type:14} {r['n']:>5}  net ${r['total']}")
    finally:
        conn.close()


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint."""
    paths = InstancePaths.resolve()
    load_instance_env(paths, override=True)
    parser = argparse.ArgumentParser(
        description="Sync SnapTrade activities -> local SQLite DB"
    )
    parser.add_argument(
        "--config",
        default=None,
        help=(
            "Account routing config. Defaults to snaptrade-accounts.yaml "
            "under the instance data root."
        ),
    )
    parser.add_argument("--show", action="store_true", help="Print summary and exit")
    args = parser.parse_args(argv)
    database_url = paths.database_url()
    config_path = (
        Path(args.config) if args.config is not None else paths.snaptrade_accounts
    )
    try:
        if args.show:
            show(database_url)
            return 0
        summary = sync(config_path, database_url)
    except (SnapTradeAPIError, ValueError, RuntimeError, FileNotFoundError) as exc:
        print(f"Sync error: {exc}", file=sys.stderr)
        return 1
    print(f"Synced transactions to {summary['db']} at {summary['synced_at']}")
    for a in summary["accounts"]:
        print(
            f"- {a['name']} ({a['role']}): {a['fetched']} fetched, "
            f"{a['inserted']} new, {a['skipped_duplicates']} duplicates skipped"
        )
    if not summary["accounts"]:
        print("- no syncable accounts (check config role/enabled)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
