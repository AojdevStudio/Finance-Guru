"""Provide the single Step 0: refresh entrypoint for all financial data."""

from __future__ import annotations

import argparse
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.config.instance_paths import InstancePaths, load_instance_env
from src.integrations.simplefin.sync_expenses_db import sync as sync_expenses
from src.integrations.snaptrade.sync_db import sync as sync_positions
from src.integrations.snaptrade.sync_transactions_db import sync as sync_transactions


def refresh(database_url: str | None, *, months: int = 12) -> dict[str, Any]:
    """Run every financial sync independently in dependency order.

    Args:
        database_url: SQLite database URL or ``None`` for the configured default.
        months: Number of SimpleFIN transaction months to request.

    Returns:
        Per-source statuses and the refresh timestamp.
    """
    account_config = Path("config/snaptrade-accounts.yaml")
    operations: tuple[tuple[str, Callable[[], dict[str, Any]]], ...] = (
        ("positions", lambda: sync_positions(account_config, database_url)),
        ("transactions", lambda: sync_transactions(account_config, database_url)),
        ("expenses", lambda: sync_expenses(database_url, months=months)),
    )
    sources: list[dict[str, Any]] = []
    for name, operation in operations:
        try:
            sources.append({"source": name, "status": "ok", "summary": operation()})
        except Exception as exc:  # Each source must be isolated from sibling failures.
            sources.append({"source": name, "status": "error", "error": str(exc)})
    return {
        "synced_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "sources": sources,
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
        if source["status"] == "ok":
            print(f"{source['source']}: ok")
        else:
            print(f"{source['source']}: error: {source['error']}")
    return 0 if all(source["status"] == "ok" for source in result["sources"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
