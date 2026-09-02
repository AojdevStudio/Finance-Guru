"""Regression coverage for the SnapTrade sync backlog."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import pytest

from src.integrations.snaptrade import client as snaptrade_client
from src.integrations.snaptrade.cli import _account_balances
from src.integrations.snaptrade.client import SnapTradeAPIError, _summarize_activity
from src.integrations.snaptrade.sync_db import _net_positions
from src.integrations.snaptrade.sync_db import main as sync_positions_main
from src.integrations.snaptrade.sync_db import sync as sync_positions
from src.integrations.snaptrade.sync_transactions_db import (
    _SCHEMA as TRANSACTION_SCHEMA,
)
from src.integrations.snaptrade.sync_transactions_db import _dedupe_key
from src.integrations.snaptrade.sync_transactions_db import show as show_transactions
from src.integrations.snaptrade.sync_transactions_db import sync as sync_transactions


def _activity(*, activity_id: str, date: str = "2026-01-03") -> dict[str, Any]:
    return {
        "id": activity_id,
        "type": "BUY",
        "date": date,
        "symbol": "AAPL",
        "amount": -1000.0,
        "quantity": 10.0,
        "currency": "USD",
        "description": "SYNTHETIC BUY",
        "account": "acct-test",
    }


def _raw_activity(*, activity_id: str | None, trade_date: str) -> dict[str, Any]:
    activity = {
        "type": "BUY",
        "trade_date": trade_date,
        "symbol": {"symbol": "AAPL"},
        "amount": -1000.0,
        "units": 10.0,
        "currency": {"code": "USD"},
        "description": "SYNTHETIC BUY",
        "account": {"id": "acct-test"},
    }
    if activity_id is not None:
        activity["id"] = activity_id
    return activity


def _legacy_dedupe_key(account_id: str, activity: dict[str, Any]) -> str:
    parts = [
        account_id,
        str(activity.get("date") or ""),
        str(activity.get("type") or ""),
        str(activity.get("amount") if activity.get("amount") is not None else ""),
        str(activity.get("symbol") or ""),
        str(activity.get("quantity") if activity.get("quantity") is not None else ""),
        str(activity.get("description") or ""),
    ]
    return "|".join(parts)


def _write_routing_config(path: Path) -> None:
    path.write_text(
        "accounts:\n"
        "- snaptrade_account_id: acct-test\n"
        "  name: Synthetic account\n"
        "  role: taxable_margin\n"
        "  enabled: true\n",
        encoding="utf-8",
    )


def test_activity_identity_distinguishes_identical_executions() -> None:
    first = _activity(activity_id="execution-1")
    second = _activity(activity_id="execution-2")

    assert _dedupe_key("acct-test", first) != _dedupe_key("acct-test", second)


def test_activity_dates_normalize_equivalent_timezone_shapes() -> None:
    local = _summarize_activity(
        _raw_activity(
            activity_id="execution-1",
            trade_date="2026-01-03T23:30:00-06:00",
        )
    )
    utc = _summarize_activity(
        _raw_activity(
            activity_id="execution-1",
            trade_date="2026-01-04T05:30:00Z",
        )
    )

    assert local["id"] == utc["id"] == "execution-1"
    assert local["date"] == utc["date"] == "2026-01-04"


@pytest.mark.parametrize("invalid_date", ["01/03/2026", "2026-01-03T12:00:00"])
def test_activity_date_rejects_non_iso_external_shape(invalid_date: str) -> None:
    with pytest.raises(SnapTradeAPIError, match="date"):
        _summarize_activity(
            _raw_activity(activity_id="execution-1", trade_date=invalid_date)
        )


def test_activity_missing_id_uses_stable_fallback() -> None:
    raw = _raw_activity(activity_id=None, trade_date="2026-01-03")

    first = _summarize_activity(raw)
    second = _summarize_activity(dict(reversed(list(raw.items()))))

    assert first["id"].startswith("fallback:")
    assert first["id"] == second["id"]


def test_repeat_sync_migrates_natural_key_and_keeps_both_executions(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    activities = [
        _activity(activity_id="execution-1"),
        _activity(activity_id="execution-2"),
    ]

    class ActivityClient:
        @classmethod
        def from_env(cls) -> ActivityClient:
            return cls()

        def get_activities(self, account_id: str) -> list[dict[str, Any]]:
            assert account_id == "acct-test"
            return activities

    monkeypatch.setattr(
        "src.integrations.snaptrade.sync_transactions_db.SnapTradeClientWrapper",
        ActivityClient,
    )
    config_path = tmp_path / "snaptrade-accounts.yaml"
    database_path = tmp_path / "family_office.db"
    _write_routing_config(config_path)

    legacy_activity = {
        **activities[0],
        "date": "2026-01-02T19:00:00-06:00",
    }
    with sqlite3.connect(database_path) as connection:
        connection.executescript(TRANSACTION_SCHEMA)
        connection.execute(
            "INSERT INTO transactions "
            "(account_id, date, type, symbol, description, amount, quantity, "
            "currency, dedupe_key, synced_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                "acct-test",
                legacy_activity["date"],
                legacy_activity["type"],
                legacy_activity["symbol"],
                legacy_activity["description"],
                legacy_activity["amount"],
                legacy_activity["quantity"],
                legacy_activity["currency"],
                _legacy_dedupe_key("acct-test", legacy_activity),
                "2026-01-01T00:00:00+00:00",
            ),
        )

    first = sync_transactions(config_path, str(database_path))
    second = sync_transactions(config_path, str(database_path))

    with sqlite3.connect(database_path) as connection:
        persisted = {
            (row[0], row[1])
            for row in connection.execute(
                "SELECT dedupe_key, date FROM transactions ORDER BY dedupe_key"
            )
        }

    assert persisted == {
        (_dedupe_key("acct-test", activities[0]), "2026-01-03"),
        (_dedupe_key("acct-test", activities[1]), "2026-01-03"),
    }
    assert first["accounts"][0]["migrated_legacy_keys"] == 1
    assert first["accounts"][0]["inserted"] == 1
    assert second["accounts"][0]["migrated_legacy_keys"] == 0
    assert second["accounts"][0]["inserted"] == 0


def test_net_positions_divides_cost_by_priced_quantity_and_surfaces_gap() -> None:
    result = _net_positions(
        [
            {
                "symbol": "AAPL",
                "instrument": "equity",
                "quantity": 10.0,
                "average_purchase_price": 100.0,
                "price": 110.0,
            },
            {
                "symbol": "AAPL",
                "instrument": "equity",
                "quantity": 10.0,
                "average_purchase_price": None,
                "price": 110.0,
            },
        ]
    )

    assert result.positions[0]["quantity"] == 20.0
    assert result.positions[0]["avg_cost"] == 100.0
    assert result.unpriced_lots[0].model_dump() == {
        "symbol": "AAPL",
        "instrument": "equity",
        "quantity": 10.0,
    }


def test_position_sync_returns_unpriced_lots_to_caller(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    class PositionClient:
        @classmethod
        def from_env(cls) -> PositionClient:
            return cls()

        def get_positions(self, account_id: str) -> list[dict[str, Any]]:
            assert account_id == "acct-test"
            return [
                {
                    "symbol": "AAPL",
                    "instrument": "equity",
                    "quantity": 10.0,
                    "average_purchase_price": 100.0,
                    "price": 110.0,
                },
                {
                    "symbol": "AAPL",
                    "instrument": "equity",
                    "quantity": 10.0,
                    "average_purchase_price": None,
                    "price": 110.0,
                },
            ]

        def get_options(self, account_id: str) -> list[dict[str, Any]]:
            assert account_id == "acct-test"
            return []

        def get_balances(self, account_id: str) -> list[dict[str, Any]]:
            assert account_id == "acct-test"
            return [{"currency": "USD", "cash": 0.0, "buying_power": 0.0}]

        def get_account_equity(self, account_id: str) -> float:
            assert account_id == "acct-test"
            return 2200.0

    monkeypatch.setattr(
        "src.integrations.snaptrade.sync_db.SnapTradeClientWrapper",
        PositionClient,
    )
    config_path = tmp_path / "snaptrade-accounts.yaml"
    database_path = tmp_path / "family_office.db"
    _write_routing_config(config_path)

    summary = sync_positions(config_path, str(database_path))

    assert summary["accounts"][0]["unpriced_lots"] == [
        {"symbol": "AAPL", "instrument": "equity", "quantity": 10.0}
    ]
    with sqlite3.connect(database_path) as connection:
        assert connection.execute(
            "SELECT quantity, avg_cost FROM positions WHERE symbol = 'AAPL'"
        ).fetchone() == (20.0, 100.0)


class _BalanceClient:
    def __init__(
        self,
        balances: list[dict[str, Any]],
        *,
        equity: float | None = 1000.0,
        price: float | None = 100.0,
    ) -> None:
        self.balances = balances
        self.equity = equity
        self.price = price

    def get_balances(self, account_id: str) -> list[dict[str, Any]]:
        assert account_id == "acct-test"
        return self.balances

    def get_account_equity(self, account_id: str) -> float | None:
        assert account_id == "acct-test"
        return self.equity

    def get_positions(self, account_id: str) -> list[dict[str, Any]]:
        assert account_id == "acct-test"
        return [
            {
                "symbol": "AAPL",
                "instrument": "equity",
                "quantity": 10.0,
                "price": self.price,
            }
        ]

    def get_options(self, account_id: str) -> list[dict[str, Any]]:
        assert account_id == "acct-test"
        return []


def test_account_balances_selects_requested_currency() -> None:
    client = _BalanceClient(
        [
            {"currency": "EUR", "cash": 25.0, "buying_power": 30.0},
            {"currency": "USD", "cash": 50.0, "buying_power": 60.0},
        ]
    )

    balance = _account_balances(client, "acct-test", currency="USD")

    assert balance["currency"] == "USD"
    assert balance["settled_cash"] == 50.0
    assert balance["buying_power"] == 60.0


def test_account_balances_rejects_single_non_requested_currency() -> None:
    client = _BalanceClient([{"currency": "EUR", "cash": 25.0, "buying_power": 30.0}])

    with pytest.raises(SnapTradeAPIError) as error:
        _account_balances(client, "acct-test", currency="USD")

    assert type(error.value).__name__ == "BalanceCurrencyMismatchError"


def test_margin_debt_rejects_missing_equity_with_typed_failure() -> None:
    stocks = [{"symbol": "AAPL", "price": 100.0, "quantity": 10.0}]

    with pytest.raises(SnapTradeAPIError) as error:
        snaptrade_client.derive_margin_debt(stocks, [], equity=None)

    assert type(error.value).__name__ == "MissingAccountEquityError"


def test_margin_debt_rejects_missing_position_mark_with_typed_failure() -> None:
    stocks = [{"symbol": "AAPL", "price": None, "quantity": 10.0}]

    with pytest.raises(SnapTradeAPIError) as error:
        snaptrade_client.derive_margin_debt(stocks, [], equity=1000.0)

    assert type(error.value).__name__ == "MissingPositionMarkError"


def test_position_sync_cli_renders_nullable_money_fields(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("FIN_GURU_DATA_ROOT", str(tmp_path))
    monkeypatch.setattr(
        "src.integrations.snaptrade.sync_db.sync",
        lambda config_path, database_url: {
            "db": str(tmp_path / "family_office.db"),
            "synced_at": "2026-01-01T00:00:00+00:00",
            "accounts": [
                {
                    "name": "Synthetic account",
                    "role": "taxable_margin",
                    "equity_rows": 1,
                    "option_rows": 0,
                    "account_equity": None,
                    "settled_cash": None,
                    "margin_debt": None,
                    "unpriced_lots": [],
                }
            ],
        },
    )

    assert sync_positions_main([]) == 0

    output = capsys.readouterr().out
    assert "equity=n/a cash=n/a margin=n/a" in output


def test_transaction_show_renders_nullable_type(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    database_path = tmp_path / "family_office.db"
    with sqlite3.connect(database_path) as connection:
        connection.executescript(TRANSACTION_SCHEMA)
        connection.execute(
            "INSERT INTO transactions "
            "(account_id, date, type, symbol, description, amount, quantity, "
            "currency, dedupe_key, synced_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                "acct-test",
                "2026-01-03",
                None,
                None,
                None,
                None,
                None,
                "USD",
                "snaptrade|acct-test|execution-1",
                "2026-01-01T00:00:00+00:00",
            ),
        )

    show_transactions(str(database_path))

    assert "unknown" in capsys.readouterr().out
