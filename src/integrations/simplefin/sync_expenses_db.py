"""Import SimpleFIN transactions into the shared SQLite transaction table."""

from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import sys
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from src.config.instance_paths import InstancePaths, _db_path, load_instance_env
from src.integrations.simplefin.categorize import (
    CATEGORY_PATTERNS,
    CategoryOverridesError,
    PatternTable,
    categorize_expense,
    load_category_overrides,
    load_merchant_rules,
    merge_patterns,
)


class SimpleFinSyncError(RuntimeError):
    """Raised when SimpleFIN data cannot be fetched or parsed."""


DEFAULT_APP_DIR = Path(__file__).resolve().parents[3] / "apps" / "simplefin-sync"

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


_WITHDRAWAL_MARKERS = (
    "direct debit",
    "debit card purchase",
    "cash advance",
    "transferred to",
    "transfer withdrawal",
)
_DEPOSIT_MARKERS = ("direct deposit", "direct dep", "transferred from")


Direction = Literal["credit", "debit"]


def resolve_direction(text: str | None, amount: float | None) -> Direction:
    """Resolve credit/debit, preferring explicit feed wording over amount sign.

    Fidelity's sign is unreliable in BOTH directions, so sign alone is not
    trustworthy for that feed: inbound payroll arrives negative, while debit-card
    purchases and cash advances arrive positive. Verified 2026-08-31 against the
    authoritative SnapTrade ``transactions`` rows for the same transactions.
    Explicit wording wins; sign remains the fallback for feeds that get it right.

    Note ``transferred to`` (outflow) and ``transferred from`` (inflow) are both
    listed: the two legs of an internal Fidelity transfer share an amount sign,
    so only the wording distinguishes them.

    Args:
        text: Joined payee and description text, may be None.
        amount: Parsed transaction amount, used only when no marker matches.

    Returns:
        ``"debit"`` for outflows, ``"credit"`` for inflows. Defaults to
        ``"credit"`` when neither a marker nor a negative amount is present.
    """
    normalized = (text or "").lower()
    if any(marker in normalized for marker in _WITHDRAWAL_MARKERS):
        return "debit"
    if any(marker in normalized for marker in _DEPOSIT_MARKERS):
        return "credit"
    return "debit" if amount is not None and amount < 0 else "credit"


def _category_text(txn: dict[str, Any]) -> str:
    """Join payee and description, since either one can carry the merchant."""
    return " ".join(part for part in (txn.get("payee"), txn.get("description")) if part)


def _signed_amount(amount: float | None, direction: Direction) -> float | None:
    """Return the amount positive for a credit and negative for a debit."""
    if amount is None:
        return None
    return abs(amount) if direction == "credit" else -abs(amount)


def normalize_transaction(
    account: dict[str, Any],
    txn: dict[str, Any],
    now: str,
    patterns: PatternTable | None = None,
    overrides: Mapping[str, str] | None = None,
) -> tuple[Any, ...]:
    """Normalize a SimpleFIN transaction into database column order.

    Args:
        account: SimpleFIN account containing the transaction.
        txn: SimpleFIN transaction payload.
        now: ISO timestamp for the current sync.
        patterns: Category table, the public table merged with the household
            rules. Defaults to the public table alone.
        overrides: Per-transaction categories that take precedence over patterns.

    Returns:
        A tuple matching the ``bank_transactions`` column order.
    """
    posted = txn.get("posted")
    try:
        posted_ts = int(posted) if posted is not None else None
    except (TypeError, ValueError):
        posted_ts = None
    raw_amount = _to_float(txn.get("amount"))
    direction = resolve_direction(_category_text(txn), raw_amount)
    amount = _signed_amount(raw_amount, direction)
    category = categorize_expense(
        _category_text(txn), amount, account.get("name"), patterns
    )
    if overrides is not None:
        category = overrides.get(str(txn["id"]), category)
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
        direction,
        category,
        now,
    )


def sync(
    database_url: str | None,
    *,
    months: int = 12,
    app_dir: Path = DEFAULT_APP_DIR,
    dump_provider: Callable[[int, Path], dict[str, Any]] = run_dump,
    merchant_rules: Path | None = None,
    category_overrides: Path | None = None,
) -> dict[str, Any]:
    """Sync SimpleFIN transactions into the shared SQLite database.

    Args:
        database_url: SQLite database URL or ``None`` for the configured default.
        months: Number of months of history to request.
        app_dir: Directory containing the SimpleFIN Bun application.
        dump_provider: Callable that returns a SimpleFIN account-set payload.
        merchant_rules: Household ``merchant-rules.yaml``; ``None`` categorizes
            with the public table alone.
        category_overrides: Private transaction IDs mapped to categories.

    Returns:
        Counts and metadata describing the completed sync.

    Raises:
        SimpleFinSyncError: If the provider returns an invalid payload.
        MerchantRulesError: If ``merchant_rules`` is malformed.
        CategoryOverridesError: If overrides are invalid or ambiguous.
    """
    db = _db_path(database_url)
    patterns = merge_patterns(
        CATEGORY_PATTERNS,
        load_merchant_rules(merchant_rules) if merchant_rules else {},
    )
    overrides = load_category_overrides(category_overrides)
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    payload = dump_provider(months, app_dir)
    if not isinstance(payload, dict) or "accounts" not in payload:
        raise SimpleFinSyncError("SimpleFIN payload must contain accounts")

    accounts = payload.get("accounts") or []
    errors = payload.get("errors") or []
    errlist = payload.get("errlist") or []
    partial_errors = len(errors) + len(errlist)
    if partial_errors:
        details = "; ".join(str(item) for item in [*errors, *errlist])
        raise SimpleFinSyncError(
            f"SimpleFIN reported {partial_errors} partial account error(s); "
            f"sync aborted: {details}"
        )
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
            row = normalize_transaction(account, txn, now, patterns, overrides)
            rows.append(row)
            category = str(row[10])
            by_category[category] = by_category.get(category, 0) + 1

    conn = sqlite3.connect(db)
    try:
        with conn:
            conn.executescript(_SCHEMA)
            conn.execute("BEGIN IMMEDIATE")
            existing_keys = {
                (account_id, txn_id)
                for account_id, txn_id in conn.execute(
                    "SELECT account_id, txn_id FROM bank_transactions"
                )
            }
            override_accounts: dict[str, set[str]] = {}
            for account_id, txn_id in [
                *existing_keys,
                *((row[0], row[3]) for row in rows),
            ]:
                if txn_id in overrides:
                    override_accounts.setdefault(txn_id, set()).add(account_id)
            if any(len(accounts) > 1 for accounts in override_accounts.values()):
                raise CategoryOverridesError(
                    "An overridden transaction ID belongs to multiple accounts"
                )
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
        "partial_errors": partial_errors,
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
    paths = InstancePaths.resolve()
    load_instance_env(paths)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--months", type=int, default=12)
    parser.add_argument("--show", action="store_true")
    args = parser.parse_args(argv)
    database_url = paths.database_url()

    if args.show:
        show(database_url)
        return 0

    try:
        summary = sync(
            database_url,
            months=args.months,
            merchant_rules=paths.merchant_rules,
            category_overrides=paths.category_overrides,
        )
    except (SimpleFinSyncError, ValueError, RuntimeError, OSError) as exc:
        print(f"Sync error: {exc}", file=sys.stderr)
        return 1

    print(
        f"Synced {summary['transactions_seen']} transactions: "
        f"{summary['inserted']} inserted, {summary['updated']} updated, "
        f"{summary['skipped_missing_id']} skipped."
    )
    partial = int(summary.get("partial_errors", 0))
    if partial:
        print(
            f"partial: {partial} account error(s); bank_transactions may be "
            "incomplete for those accounts",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
