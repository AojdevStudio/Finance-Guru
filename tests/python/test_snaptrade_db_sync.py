"""Tests for the SnapTrade -> local SQLite sync helpers (money paths)."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.config.instance_paths import InstancePaths, _db_path
from src.integrations.simplefin.categorize import categorize_expense
from src.integrations.snaptrade.sync_db import (
    _net_positions,
)
from src.integrations.snaptrade.sync_db import (
    main as sync_positions_main,
)
from src.integrations.snaptrade.sync_transactions_db import _dedupe_key


def test_net_positions_sums_lots_and_weights_cost() -> None:
    """Two lots of the same symbol net to one share-weighted row (the SPMO case)."""
    rows = [
        {
            "symbol": "SPMO",
            "instrument": "equity",
            "quantity": 1.631,
            "average_purchase_price": 153.2618,
            "price": 100.0,
        },
        {
            "symbol": "SPMO",
            "instrument": "equity",
            "quantity": 105.381,
            "average_purchase_price": 120.4175,
            "price": 100.0,
        },
    ]
    out = _net_positions(rows).positions
    assert len(out) == 1
    row = out[0]
    assert row["quantity"] == 105.381 + 1.631
    expected = (1.631 * 153.2618 + 105.381 * 120.4175) / (1.631 + 105.381)
    assert abs(row["avg_cost"] - expected) < 1e-6


def test_net_positions_keeps_distinct_symbols_and_instruments() -> None:
    """Different symbols, and equity vs option of same symbol, stay separate rows."""
    rows = [
        {
            "symbol": "AAPL",
            "instrument": "equity",
            "quantity": 10,
            "average_purchase_price": 190.0,
        },
        {
            "symbol": "SPY",
            "instrument": "equity",
            "quantity": 5,
            "average_purchase_price": 500.0,
        },
        {
            "symbol": "-SPY260918P620",
            "instrument": "option",
            "quantity": 2,
            "average_purchase_price": 4.6,
        },
    ]
    out = _net_positions(rows).positions
    assert len({(r["symbol"], r["instrument"]) for r in out}) == 3


def test_dedupe_key_stable_and_distinguishes_same_day_dividends() -> None:
    """Same provider activity stays idempotent; distinct activity ids do not collide."""
    a = {
        "id": "activity-1",
        "date": "2026-01-02",
        "type": "DIVIDEND",
        "amount": 12.5,
        "symbol": "JEPI",
        "quantity": 0.0,
        "description": "DIV",
    }
    b = {**a, "id": "activity-2", "symbol": "JEPQ"}
    assert _dedupe_key("acct1", a) == _dedupe_key("acct1", a)
    assert _dedupe_key("acct1", a) != _dedupe_key("acct1", b)


@pytest.mark.parametrize(
    "database_url",
    [
        pytest.param("sqlite:///family_office.db", id="sqlite-url"),
        pytest.param("family_office.db", id="bare-path"),
    ],
)
def test_db_path_resolves_relative_locations_under_instance_root(
    tmp_path: Path, database_url: str
) -> None:
    """SQLite URLs and bare paths resolve under the instance root."""
    paths = InstancePaths(root=tmp_path)

    assert _db_path(database_url, paths) == tmp_path / "family_office.db"


def test_sync_cli_reads_default_account_config_from_instance_root(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    instance_root = tmp_path / "instance"
    working_directory = tmp_path / "cwd"
    instance_root.mkdir()
    working_directory.mkdir()
    (instance_root / "snaptrade-accounts.yaml").write_text(
        "accounts: []\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("FIN_GURU_DATA_ROOT", str(instance_root))
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.chdir(working_directory)

    assert sync_positions_main([]) == 0
    assert (instance_root / "family_office.db").exists()


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        pytest.param("H-E-B #063 Anytown TX", "Groceries", id="grocery"),
        pytest.param("CVS/PHARMACY # ANYTOWN TX", "Health & Wellness", id="pharmacy"),
        pytest.param("Delta Airlines", "Travel", id="airline"),
        pytest.param("American Express Travel", "Travel", id="amex-travel"),
        pytest.param("Taptap Send", "Transfer", id="transfer"),
        pytest.param("Some Random LLC 12345", "Uncategorized", id="unknown"),
    ],
)
def test_categorize_matches_and_prioritizes_transfers(text: str, expected: str) -> None:
    """Merchant text maps to the right category; transfers win over merchant reads."""
    assert categorize_expense(text) == expected
