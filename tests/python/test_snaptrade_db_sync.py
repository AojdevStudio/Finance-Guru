"""Tests for the SnapTrade -> local SQLite sync helpers (money paths)."""

from __future__ import annotations

from pathlib import Path

from src.config.instance_paths import InstancePaths, _db_path
from src.integrations.snaptrade.sync_db import _net_positions
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
    out = _net_positions(rows)
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
    out = _net_positions(rows)
    assert len({(r["symbol"], r["instrument"]) for r in out}) == 3


def test_dedupe_key_stable_and_distinguishes_same_day_dividends() -> None:
    """Same activity -> same key (idempotent); different symbol -> different key."""
    a = {
        "date": "2026-01-02",
        "type": "DIVIDEND",
        "amount": 12.5,
        "symbol": "JEPI",
        "quantity": 0.0,
        "description": "DIV",
    }
    b = {**a, "symbol": "JEPQ"}  # same day, same amount, different holding
    assert _dedupe_key("acct1", a) == _dedupe_key("acct1", a)
    assert _dedupe_key("acct1", a) != _dedupe_key("acct1", b)


def test_db_path_resolves_relative_locations_under_instance_root(
    tmp_path: Path,
) -> None:
    """SQLite URLs and bare paths resolve under the instance root."""
    paths = InstancePaths(root=tmp_path)

    assert _db_path("sqlite:///family_office.db", paths) == (
        tmp_path / "family_office.db"
    )
    assert _db_path("family_office.db", paths) == tmp_path / "family_office.db"


def test_categorize_matches_and_prioritizes_transfers() -> None:
    """Merchant text maps to the right category; transfers win over merchant reads."""
    from src.integrations.simplefin.categorize import categorize_expense as categorize

    assert categorize("H-E-B #063 Pearland TX") == "Groceries"
    assert categorize("CVS/PHARMACY # MANVEL TX") == "Health & Wellness"
    assert categorize("Delta Airlines") == "Travel"
    # "American Express Travel" must read as Travel, not a bank/transfer
    assert categorize("American Express Travel") == "Travel"
    # explicit remittance stays a Transfer, not miscategorized as a merchant
    assert categorize("Taptap Send") == "Transfer"
    assert categorize("Some Random LLC 12345") == "Uncategorized"
