#!/usr/bin/env python3
"""Sync live SnapTrade activities (transaction history) into the local SQLite DB.

Replaces the retired Google Sheets Transactions tab. Target is DATABASE_URL
(``sqlite:///family_office.db``). Read-only against SnapTrade; only local writes.

    uv run python -m src.integrations.snaptrade.sync_transactions_db          # sync
    uv run python -m src.integrations.snaptrade.sync_transactions_db --show   # summary

Accumulate semantics: transactions are history, so rows are INSERTed and never
deleted. A UNIQUE natural key (account+date+type+amount+symbol+quantity+desc)
makes re-runs idempotent — only genuinely new activities are added.

Expense-Tracker routing is intentionally NOT implemented: SnapTrade activities
carry no DEBIT CARD PURCHASE records (types are BUY/SELL/DIVIDEND/JOURNALED/
WITHDRAWAL/CONTRIBUTION/...), and the Budget Planner destination lived in the
retired Sheet. ponytail: add categorized-expense routing only if a debit-card
data source appears.
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from src.integrations.snaptrade.client import SnapTradeAPIError, SnapTradeClientWrapper
from src.integrations.snaptrade.models import SnapTradeAccountsConfig
from src.integrations.snaptrade.sync_db import _db_path

DEFAULT_CONFIG_PATH = Path("config/snaptrade-accounts.yaml")

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
    """Natural key that stays stable across re-runs but keeps distinct rows.

    Coarser than the Sheet's date|type|amount would collide same-day dividends
    of equal size across symbols, so symbol/quantity/description are included.
    """
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
            before = conn.total_changes
            with conn:
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
            print(f"  {r['type']:14} {r['n']:>5}  net ${r['total']}")
    finally:
        conn.close()


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint."""
    load_dotenv(override=True)
    parser = argparse.ArgumentParser(
        description="Sync SnapTrade activities -> local SQLite DB"
    )
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    parser.add_argument("--show", action="store_true", help="Print summary and exit")
    args = parser.parse_args(argv)
    database_url = os.getenv("DATABASE_URL")
    try:
        if args.show:
            show(database_url)
            return 0
        summary = sync(Path(args.config), database_url)
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
