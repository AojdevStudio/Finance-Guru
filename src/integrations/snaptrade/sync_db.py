#!/usr/bin/env python3
"""Sync live SnapTrade positions + balances into the local SQLite DB.

Replaces the retired Google Sheets DataHub as the portfolio store. Target is
DATABASE_URL (e.g. ``sqlite:///family_office.db``). Read-only against SnapTrade;
the only writes are to the local DB.

    uv run python -m src.integrations.snaptrade.sync_db          # sync
    uv run python -m src.integrations.snaptrade.sync_db --show   # print current snapshot

Snapshot semantics: each sync REPLACES the rows for every synced account (a
current-state store, like the old DataHub). ponytail: if per-sync history is
ever wanted, add an append-only `position_history` table keyed on synced_at.
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.config.instance_paths import InstancePaths, _db_path, load_instance_env
from src.integrations.snaptrade.cli import _account_balances, _account_positions
from src.integrations.snaptrade.client import SnapTradeAPIError, SnapTradeClientWrapper
from src.integrations.snaptrade.models import SnapTradeAccountsConfig

DEFAULT_CONFIG_PATH = Path("config/snaptrade-accounts.yaml")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS positions (
    account_id  TEXT NOT NULL,
    symbol      TEXT NOT NULL,
    instrument  TEXT NOT NULL,
    quantity    REAL,
    avg_cost    REAL,
    price       REAL,
    synced_at   TEXT NOT NULL,
    PRIMARY KEY (account_id, symbol, instrument)
);
CREATE TABLE IF NOT EXISTS balances (
    account_id         TEXT PRIMARY KEY,
    currency           TEXT,
    settled_cash       REAL,
    buying_power       REAL,
    account_equity     REAL,
    gross_market_value REAL,
    margin_debt        REAL,
    synced_at          TEXT NOT NULL
);
"""


def _net_positions(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Net multiple lots of the same (symbol, instrument) into one row.

    SnapTrade can return a symbol as several lots (observed: SPMO twice). The
    store is one row per ticker, so quantities sum and cost is share-weighted.
    """
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for p in rows:
        if not p.get("symbol"):
            continue
        groups[(p["symbol"], p.get("instrument", "equity"))].append(p)
    netted: list[dict[str, Any]] = []
    for (symbol, instrument), lots in groups.items():
        qty = sum((lot.get("quantity") or 0) for lot in lots)
        cost_lots = [
            lot for lot in lots if lot.get("average_purchase_price") is not None
        ]
        weighted = sum(
            (lot["average_purchase_price"] * (lot.get("quantity") or 0))
            for lot in cost_lots
        )
        avg_cost = (
            (weighted / qty)
            if (qty and cost_lots)
            else (cost_lots[0]["average_purchase_price"] if cost_lots else None)
        )
        price = next(
            (lot.get("price") for lot in lots if lot.get("price") is not None), None
        )
        netted.append(
            {
                "symbol": symbol,
                "instrument": instrument,
                "quantity": qty,
                "avg_cost": avg_cost,
                "price": price,
            }
        )
    netted.sort(key=lambda r: (r["instrument"], r["symbol"]))
    return netted


def sync(config_path: Path, database_url: str | None) -> dict[str, Any]:
    """Pull live positions + balances and write a snapshot to the local DB."""
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
            positions = _net_positions(_account_positions(client, aid))
            balances = _account_balances(client, aid)
            with conn:  # one transaction per account
                conn.execute("DELETE FROM positions WHERE account_id = ?", (aid,))
                conn.executemany(
                    "INSERT INTO positions "
                    "(account_id, symbol, instrument, quantity, avg_cost, price, synced_at) "
                    "VALUES (?,?,?,?,?,?,?)",
                    [
                        (
                            aid,
                            p["symbol"],
                            p["instrument"],
                            p["quantity"],
                            p["avg_cost"],
                            p["price"],
                            now,
                        )
                        for p in positions
                    ],
                )
                conn.execute(
                    "INSERT OR REPLACE INTO balances "
                    "(account_id, currency, settled_cash, buying_power, account_equity, "
                    "gross_market_value, margin_debt, synced_at) VALUES (?,?,?,?,?,?,?,?)",
                    (
                        aid,
                        balances.get("currency"),
                        balances.get("settled_cash"),
                        balances.get("buying_power"),
                        balances.get("account_equity"),
                        balances.get("gross_market_value"),
                        balances.get("margin_debt"),
                        now,
                    ),
                )
            summary["accounts"].append(
                {
                    "account_id": aid,
                    "name": account.name,
                    "role": str(account.role),
                    "equity_rows": sum(
                        1 for p in positions if p["instrument"] == "equity"
                    ),
                    "option_rows": sum(
                        1 for p in positions if p["instrument"] == "option"
                    ),
                    "settled_cash": balances.get("settled_cash"),
                    "margin_debt": balances.get("margin_debt"),
                    "account_equity": balances.get("account_equity"),
                }
            )
    finally:
        conn.close()
    return summary


def show(database_url: str | None) -> None:
    """Print the current DB snapshot."""
    db = _db_path(database_url)
    if not db.exists():
        print(f"No DB at {db}", file=sys.stderr)
        return
    conn = sqlite3.connect(db)
    try:
        conn.row_factory = sqlite3.Row
        print(f"# {db}")
        for b in conn.execute("SELECT * FROM balances"):
            print(
                f"\n[{b['account_id']}] equity={b['account_equity']} "
                f"cash={b['settled_cash']} margin_debt={b['margin_debt']} "
                f"(synced {b['synced_at']})"
            )
            rows = conn.execute(
                "SELECT symbol, instrument, quantity, avg_cost FROM positions "
                "WHERE account_id=? ORDER BY instrument, symbol",
                (b["account_id"],),
            ).fetchall()
            print(f"  {len(rows)} positions:")
            for r in rows:
                print(
                    f"    {r['symbol']:12} {r['instrument']:7} qty={r['quantity']:<12} avg={r['avg_cost']}"
                )
    finally:
        conn.close()


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint."""
    paths = InstancePaths.resolve()
    load_instance_env(paths)
    parser = argparse.ArgumentParser(description="Sync SnapTrade -> local SQLite DB")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    parser.add_argument(
        "--show", action="store_true", help="Print current snapshot and exit"
    )
    args = parser.parse_args(argv)
    database_url = paths.database_url()
    try:
        if args.show:
            show(database_url)
            return 0
        summary = sync(Path(args.config), database_url)
    except (SnapTradeAPIError, ValueError, RuntimeError, FileNotFoundError) as exc:
        print(f"Sync error: {exc}", file=sys.stderr)
        return 1
    print(f"Synced to {summary['db']} at {summary['synced_at']}")
    for a in summary["accounts"]:
        print(
            f"- {a['name']} ({a['role']}): {a['equity_rows']} equities, "
            f"{a['option_rows']} options | equity=${a['account_equity']:,} "
            f"cash=${a['settled_cash']:,} margin=${a['margin_debt']:,}"
        )
    if not summary["accounts"]:
        print("- no syncable accounts (check config role/enabled)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
