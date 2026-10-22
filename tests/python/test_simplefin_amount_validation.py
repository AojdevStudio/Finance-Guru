"""Reject invalid provider amounts before any transaction rows change."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import pytest

from src.integrations.simplefin.sync_expenses_db import SimpleFinSyncError, sync


def _payload(transactions: list[dict[str, Any]]) -> dict[str, Any]:
    return {"accounts": [{"id": "synthetic-account", "transactions": transactions}]}


@pytest.mark.parametrize(
    "invalid_amount",
    [None, "invalid", "NaN", "Infinity", "-Infinity", True, 10**400],
    ids=[
        "missing",
        "text",
        "nan",
        "infinity",
        "negative-infinity",
        "boolean",
        "overflow",
    ],
)
def test_invalid_amount_preserves_the_whole_saved_batch(
    tmp_path: Path, invalid_amount: Any
) -> None:
    database = tmp_path / "synthetic.db"
    original = _payload([{"id": "existing", "amount": "-10"}])
    sync(str(database), dump_provider=lambda *_: original)
    with sqlite3.connect(database) as connection:
        before = connection.execute("SELECT * FROM bank_transactions").fetchall()
    malformed = _payload(
        [
            {"id": "new", "amount": "-20"},
            {"id": "existing", "amount": invalid_amount},
        ]
    )

    failure = None
    try:
        sync(str(database), dump_provider=lambda *_: malformed)
    except SimpleFinSyncError as error:
        failure = error

    with sqlite3.connect(database) as connection:
        assert (
            connection.execute("SELECT * FROM bank_transactions").fetchall() == before
        )
    assert failure is not None, "Invalid amount must raise SimpleFinSyncError"
    assert str(failure) == "SimpleFIN transaction amount must be a finite number"


@pytest.mark.parametrize("amount", [0, "0", "-12.50", 12.5])
def test_finite_amounts_still_import(tmp_path: Path, amount: Any) -> None:
    database = tmp_path / "synthetic.db"
    payload = _payload([{"id": "valid", "amount": amount}])

    summary = sync(str(database), dump_provider=lambda *_: payload)

    assert summary["inserted"] == 1
    with sqlite3.connect(database) as connection:
        assert connection.execute(
            "SELECT amount FROM bank_transactions"
        ).fetchone() == (float(amount),)
