"""Import SimpleFIN transactions into the shared SQLite transaction table."""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from src.integrations.simplefin.categorize import categorize_expense
from src.integrations.snaptrade.sync_db import _db_path


class SimpleFinSyncError(RuntimeError):
    """Raised when SimpleFIN data cannot be fetched or parsed."""


DEFAULT_APP_DIR = Path("apps/simplefin-sync")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS bank_transactions (
    account_id TEXT NOT NULL,
    account_name TEXT,
    org TEXT,
    txn_id TEXT NOT NULL,
    date TEXT,
    posted_ts INTEGER,
    payee TEXT,
    description TEXT,
    amount REAL,
    direction TEXT,
    category TEXT,
    synced_at TEXT NOT NULL,
    PRIMARY KEY (account_id, txn_id)
);
"""

_UPSERT = """
INSERT INTO bank_transactions (
    account_id, account_name, org, txn_id, date, posted_ts,
    payee, description, amount, direction, category, synced_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(account_id, txn_id) DO UPDATE SET
    account_name=excluded.account_name,
    org=excluded.org,
    date=excluded.date,
    posted_ts=excluded.posted_ts,
    payee=excluded.payee,
    description=excluded.description,
    amount=excluded.amount,
    direction=excluded.direction,
    category=excluded.category,
    synced_at=excluded.synced_at
"""


def run_dump(months: int, app_dir: Path = DEFAULT_APP_DIR) -> dict[str, Any]:
    """Run the SimpleFIN dump application and return its JSON payload.

    Args:
        months: Number of months of transaction history to request.
        app_dir: Directory containing the SimpleFIN Bun application.

    Returns:
        Parsed SimpleFIN account-set payload.

    Raises:
        SimpleFinSyncError: If the dump fails or returns invalid JSON.
    """
    try:
        result = subprocess.run(
            ["bun", "run", "src/dump.ts", str(months)],
            cwd=app_dir,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise SimpleFinSyncError("SimpleFIN dump timed out after 120 seconds") from exc
    except FileNotFoundError as exc:
        raise SimpleFinSyncError(f"SimpleFIN dump could not start: {exc}") from exc

    if result.returncode != 0:
        detail = result.stderr.strip() or f"exit code {result.returncode}"
        raise SimpleFinSyncError(f"SimpleFIN dump failed: {detail}")

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise SimpleFinSyncError(
            f"SimpleFIN dump returned invalid JSON: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise SimpleFinSyncError("SimpleFIN dump JSON must be an object")
    return payload


def _to_float(v: Any) -> float | None:
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _iso_date(posted_ts: Any) -> str | None:
    try:
        timestamp = int(posted_ts)
    except (TypeError, ValueError):
        return None
    if timestamp <= 0:
        return None
    return datetime.fromtimestamp(timestamp, UTC).date().isoformat()


def normalize_transaction(
    account: dict[str, Any], txn: dict[str, Any], now: str
) -> tuple[Any, ...]:
    """Normalize a SimpleFIN transaction into database column order.

    Args:
        account: SimpleFIN account containing the transaction.
        txn: SimpleFIN transaction payload.
        now: ISO timestamp for the current sync.

    Returns:
        A tuple matching the ``bank_transactions`` column order.
    """
    posted = txn.get("posted")
    try:
        posted_ts = int(posted) if posted is not None else None
    except (TypeError, ValueError):
        posted_ts = None
    amount = _to_float(txn.get("amount"))
    return (
        account["id"],
        account.get("name"),
        (account.get("org") or {}).get("name"),
        txn["id"],
        _iso_date(posted_ts),
        posted_ts,
        txn.get("payee"),
        txn.get("description"),
        amount,
        "debit" if amount is not None and amount < 0 else "credit",
        categorize_expense(txn.get("description") or txn.get("payee"), amount),
        now,
    )


def sync(
    database_url: str | None,
    *,
    months: int = 12,
    app_dir: Path = DEFAULT_APP_DIR,
    dump_provider: Callable[[int, Path], dict[str, Any]] = run_dump,
) -> dict[str, Any]:
    """Sync SimpleFIN transactions into the shared SQLite database.

    Args:
        database_url: SQLite database URL or ``None`` for the configured default.
        months: Number of months of history to request.
        app_dir: Directory containing the SimpleFIN Bun application.
        dump_provider: Callable that returns a SimpleFIN account-set payload.

    Returns:
        Counts and metadata describing the completed sync.

    Raises:
        SimpleFinSyncError: If the provider returns an invalid payload.
    """
    db = _db_path(database_url)
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    payload = dump_provider(months, app_dir)
    if not isinstance(payload, dict) or "accounts" not in payload:
        raise SimpleFinSyncError("SimpleFIN payload must contain accounts")

    accounts = payload.get("accounts") or []
    errors = payload.get("errors") or []
    errlist = payload.get("errlist") or []
    rows: list[tuple[Any, ...]] = []
    transactions_seen = 0
    skipped_missing_id = 0
    by_category: dict[str, int] = {}

    for account in accounts:
        if not account.get("id"):
            continue
        for txn in account.get("transactions") or []:
            transactions_seen += 1
            if not txn.get("id"):
                skipped_missing_id += 1
                continue
            row = normalize_transaction(account, txn, now)
            rows.append(row)
            category = str(row[10])
            by_category[category] = by_category.get(category, 0) + 1

    conn = sqlite3.connect(db)
    try:
        with conn:
            conn.executescript(_SCHEMA)
            existing_keys = {
                (account_id, txn_id)
                for account_id, txn_id in conn.execute(
                    "SELECT account_id, txn_id FROM bank_transactions"
                )
            }
            inserted = sum((row[0], row[3]) not in existing_keys for row in rows)
            updated = len(rows) - inserted
            conn.executemany(_UPSERT, rows)
    finally:
        conn.close()

    return {
        "db": str(db),
        "synced_at": now,
        "accounts": len(accounts),
        "transactions_seen": transactions_seen,
        "inserted": inserted,
        "updated": updated,
        "skipped_missing_id": skipped_missing_id,
        "partial_errors": len(errors) + len(errlist),
        "by_category": by_category,
    }


def show(database_url: str | None) -> None:
    """Print stored transaction totals grouped by category and direction.

    Args:
        database_url: SQLite database URL or ``None`` for the configured default.
    """
    db = _db_path(database_url)
    if not db.exists():
        print(f"No database found at {db}")
        return

    conn = sqlite3.connect(db)
    try:
        table_exists = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='bank_transactions'"
        ).fetchone()
        if not table_exists:
            print("No bank transactions found.")
            return
        total = conn.execute("SELECT COUNT(*) FROM bank_transactions").fetchone()[0]
        print(f"Bank transactions: {total}")
        for label, column in (("Category", "category"), ("Direction", "direction")):
            print(f"{label} counts:")
            for value, count in conn.execute(
                f"SELECT {column}, COUNT(*) FROM bank_transactions "
                f"GROUP BY {column} ORDER BY COUNT(*) DESC, {column}"
            ):
                print(f"  {value or 'Uncategorized'}: {count}")
    finally:
        conn.close()


def main(argv: list[str] | None = None) -> int:
    """Run the SimpleFIN expense sync command.

    Args:
        argv: Optional command-line arguments.

    Returns:
        Process exit status.
    """
    load_dotenv(override=True)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--months", type=int, default=12)
    parser.add_argument("--show", action="store_true")
    args = parser.parse_args(argv)
    database_url = os.getenv("DATABASE_URL")

    if args.show:
        show(database_url)
        return 0

    try:
        summary = sync(database_url, months=args.months)
    except (SimpleFinSyncError, ValueError, RuntimeError, OSError) as exc:
        print(f"Sync error: {exc}", file=sys.stderr)
        return 1

    print(
        f"Synced {summary['transactions_seen']} transactions: "
        f"{summary['inserted']} inserted, {summary['updated']} updated, "
        f"{summary['skipped_missing_id']} skipped."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
