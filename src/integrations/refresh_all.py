"""Provide the single Step 0: refresh entrypoint for all financial data."""

from __future__ import annotations

import argparse
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from src.config.instance_paths import InstancePaths, load_instance_env
from src.integrations.simplefin.sync_expenses_db import sync as sync_expenses
from src.integrations.snaptrade.sync_db import sync as sync_positions
from src.integrations.snaptrade.sync_db import unpriced_lot_warning
from src.integrations.snaptrade.sync_transactions_db import sync as sync_transactions


def _run_source(name: str, operation: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    """Run one source sync and record its failure instead of stopping the refresh.

    Each source writes its own tables, so a failed source must not block the
    others. The error becomes an ``"error"`` status that ``main`` turns into a
    nonzero exit.

    Args:
        name: Source label reported in the result.
        operation: Sync callable that returns the source summary.

    Returns:
        The source status record.
    """
    try:
        return {"source": name, "status": "ok", "summary": operation()}
    except Exception as exc:
        return {"source": name, "status": "error", "error": str(exc)}


def _print_positions_summary(summary: dict[str, Any]) -> None:
    """Print the positions generation and any unpriced-lot warnings."""
    if not summary["accounts"]:
        print("  no enabled, routed account synced")
        return
    print(f"  generation {summary['synced_at']}")
    for account in summary["accounts"]:
        for lot in account["unpriced_lots"]:
            print(f"  warning: {unpriced_lot_warning(lot)}")


def refresh(database_url: str | None, *, months: int = 12) -> dict[str, Any]:
    """Run every financial sync independently in dependency order.

    Args:
        database_url: SQLite database URL or ``None`` for the configured default.
        months: Number of SimpleFIN transaction months to request.

    Returns:
        Per-source statuses and the refresh timestamp.
    """
    paths = InstancePaths.resolve()
    account_config = paths.snaptrade_accounts
    operations: tuple[tuple[str, Callable[[], dict[str, Any]]], ...] = (
        ("positions", lambda: sync_positions(account_config, database_url)),
        ("transactions", lambda: sync_transactions(account_config, database_url)),
        (
            "expenses",
            lambda: sync_expenses(
                database_url,
                months=months,
                merchant_rules=paths.merchant_rules,
                category_overrides=paths.category_overrides,
            ),
        ),
    )
    return {
        "synced_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "sources": [_run_source(name, operation) for name, operation in operations],
    }


def main(argv: list[str] | None = None) -> int:
    """Run or display all financial data sources.

    Args:
        argv: Optional command-line arguments.

    Returns:
        Zero when every source succeeds, otherwise one (so automation can
        detect a partial refresh where one leg went stale).
    """
    paths = InstancePaths.resolve()
    load_instance_env(paths)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--months", type=int, default=12)
    parser.add_argument("--show", action="store_true")
    args = parser.parse_args(argv)
    database_url = paths.database_url()

    if args.show:
        from src.integrations.simplefin.sync_expenses_db import show as show_expenses
        from src.integrations.snaptrade.sync_db import show as show_positions
        from src.integrations.snaptrade.sync_transactions_db import (
            show as show_transactions,
        )

        show_positions(database_url)
        show_transactions(database_url)
        show_expenses(database_url)
        return 0

    result = refresh(database_url, months=args.months)
    for source in result["sources"]:
        if source["status"] != "ok":
            print(f"{source['source']}: error: {source['error']}")
            continue
        print(f"{source['source']}: ok")
        if source["source"] == "positions":
            _print_positions_summary(source["summary"])
    return 0 if all(source["status"] == "ok" for source in result["sources"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
