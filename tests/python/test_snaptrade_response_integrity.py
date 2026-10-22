"""Offline checks that incomplete SDK responses never become valid snapshots."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from pydantic import SecretStr

from src.integrations.snaptrade.client import SnapTradeClientWrapper, SnapTradeDataError
from src.integrations.snaptrade.models import SnapTradeCredentials
from src.integrations.snaptrade.sync_db import _SCHEMA, sync


def _client(body: Any) -> SnapTradeClientWrapper:
    def response(**kwargs: Any) -> SimpleNamespace:
        return SimpleNamespace(body=body)

    sdk = SimpleNamespace(
        account_information=SimpleNamespace(
            get_user_account_positions=response,
            get_user_account_balance=response,
            get_account_activities=response,
        ),
        options=SimpleNamespace(list_option_holdings=response),
    )
    credentials = SnapTradeCredentials(
        client_id=SecretStr("synthetic-client"),
        consumer_key=SecretStr("synthetic-consumer"),
        user_id=SecretStr("synthetic-user"),
        user_secret=SecretStr("synthetic-secret"),
    )
    return SnapTradeClientWrapper(credentials, sdk_client=sdk)


@pytest.mark.parametrize(
    "method", ["get_positions", "get_options", "get_balances", "get_activities"]
)
@pytest.mark.parametrize("body", [None, {}, {"data": None}, {"data": "invalid"}])
def test_collection_endpoints_reject_malformed_bodies(method: str, body: Any) -> None:
    with pytest.raises(SnapTradeDataError):
        getattr(_client(body), method)("synthetic-account")


@pytest.mark.parametrize("method", ["get_positions", "get_options", "get_balances"])
def test_collection_endpoints_reject_non_object_records(method: str) -> None:
    with pytest.raises(SnapTradeDataError):
        getattr(_client([None]), method)("synthetic-account")


@pytest.mark.parametrize("method", ["get_positions", "get_options"])
def test_holdings_require_an_identity(method: str) -> None:
    with pytest.raises(SnapTradeDataError, match="symbol"):
        getattr(_client([{"units": 1, "price": 10}]), method)("synthetic-account")


@pytest.mark.parametrize(
    "method", ["get_positions", "get_options", "get_balances", "get_activities"]
)
@pytest.mark.parametrize("body", [[], {"data": []}])
def test_collection_endpoints_allow_explicitly_empty_results(
    method: str, body: Any
) -> None:
    assert getattr(_client(body), method)("synthetic-account") == []


def _paged_client(pages: list[dict[str, Any]]) -> SnapTradeClientWrapper:
    client = _client(None)
    pending = iter(pages)

    def response(**kwargs: Any) -> SimpleNamespace:
        return SimpleNamespace(body=next(pending))

    client._client.account_information.get_account_activities = response
    return client


def _activity(identity: str) -> dict[str, str]:
    return {"id": identity, "trade_date": "2026-01-02", "amount": "10"}


def test_activity_pagination_honors_total_after_a_short_page() -> None:
    client = _paged_client(
        [
            {"data": [_activity("first")], "pagination": {"total": 2}},
            {"data": [_activity("second")], "pagination": {"total": 2}},
        ]
    )

    assert [row["id"] for row in client.get_activities("synthetic-account")] == [
        "first",
        "second",
    ]


def test_activity_pagination_rejects_a_truncated_result() -> None:
    client = _paged_client(
        [
            {"data": [_activity("first")], "pagination": {"total": 2}},
            {"data": [], "pagination": {"total": 2}},
        ]
    )

    with pytest.raises(SnapTradeDataError, match="incomplete"):
        client.get_activities("synthetic-account")


@pytest.mark.parametrize(
    "pages",
    [
        [
            {"data": [_activity("first")], "pagination": {"total": 2}},
            {"data": [_activity("second")], "pagination": {"total": 3}},
        ],
        [{"data": [_activity("first")], "pagination": {"total": 0}}],
    ],
)
def test_activity_pagination_rejects_inconsistent_totals(
    pages: list[dict[str, Any]],
) -> None:
    with pytest.raises(SnapTradeDataError, match="total"):
        _paged_client(pages).get_activities("synthetic-account", page_size=1)


@pytest.mark.parametrize("page_size", [0, -1])
def test_activity_pagination_requires_a_positive_page_size(page_size: int) -> None:
    with pytest.raises(ValueError, match="page_size"):
        _paged_client([]).get_activities("synthetic-account", page_size=page_size)


def test_malformed_holdings_preserve_the_existing_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = tmp_path / "routing.yaml"
    config.write_text(
        "accounts:\n- snaptrade_account_id: synthetic-account\n"
        "  role: taxable_cash\n  enabled: true\n"
    )
    database = tmp_path / "synthetic.db"
    with sqlite3.connect(database) as connection:
        connection.executescript(_SCHEMA)
        connection.execute(
            "INSERT INTO positions VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("synthetic-account", "TEST", "equity", 1, 10, 10, "old"),
        )
        connection.execute(
            "INSERT INTO balances (account_id, synced_at) VALUES (?, ?)",
            ("synthetic-account", "old"),
        )
    client = _client({"unexpected": []})
    client._client.account_information.get_user_account_balance = lambda **kwargs: (
        SimpleNamespace(body=[{"currency": "USD", "cash": 0}])
    )
    client._client.account_information.get_user_account_details = lambda **kwargs: (
        SimpleNamespace(body={"balance": {"total": {"amount": 10}}})
    )
    monkeypatch.setattr(SnapTradeClientWrapper, "from_env", lambda: client)

    failure = None
    try:
        sync(config, str(database))
    except SnapTradeDataError as error:
        failure = error

    with sqlite3.connect(database) as connection:
        assert connection.execute(
            "SELECT symbol, quantity, synced_at FROM positions"
        ).fetchall() == [("TEST", 1, "old")]
        assert connection.execute("SELECT synced_at FROM balances").fetchall() == [
            ("old",)
        ]
    assert failure is not None
