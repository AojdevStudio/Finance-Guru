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
            get_all_account_positions=response,
            get_user_account_balance=response,
            get_account_activities=response,
        ),
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
        getattr(
            _client({"results": [None]} if method != "get_balances" else [None]), method
        )("synthetic-account")


@pytest.mark.parametrize("method", ["get_positions", "get_options"])
def test_holdings_require_an_identity(method: str) -> None:
    with pytest.raises(SnapTradeDataError, match="symbol"):
        getattr(
            _client(
                {
                    "results": [
                        {"instrument": {"kind": "stock"}, "units": 1, "price": 10}
                    ]
                }
            ),
            method,
        )("synthetic-account")


@pytest.mark.parametrize(
    "method", ["get_positions", "get_options", "get_balances", "get_activities"]
)
@pytest.mark.parametrize("body", [[], {"data": []}, {"data": [], "pagination": {}}])
def test_collection_endpoints_allow_explicitly_empty_results(
    method: str, body: Any
) -> None:
    if method in {"get_positions", "get_options"}:
        body = {"results": []}
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
    ("pages", "expected_error"),
    [
        (
            [
                {"data": [_activity("first")], "pagination": {"total": 2}},
                {"data": [_activity("second")], "pagination": {"total": 3}},
            ],
            "changed",
        ),
        ([{"data": [_activity("first")], "pagination": {"total": 0}}], "exceeds"),
    ],
)
def test_activity_pagination_rejects_inconsistent_totals(
    pages: list[dict[str, Any]], expected_error: str
) -> None:
    with pytest.raises(SnapTradeDataError, match=expected_error):
        _paged_client(pages).get_activities("synthetic-account", page_size=1)


@pytest.mark.parametrize("page_size", [0, -1])
def test_activity_pagination_requires_a_positive_page_size(page_size: int) -> None:
    with pytest.raises(ValueError, match="page_size"):
        _paged_client([]).get_activities("synthetic-account", page_size=page_size)


@pytest.mark.parametrize("total", ["2", True, None, -1, 1.5])
def test_activity_pagination_rejects_malformed_totals(total: Any) -> None:
    client = _client({"data": [_activity("first")], "pagination": {"total": total}})

    with pytest.raises(SnapTradeDataError, match="nonnegative integer"):
        client.get_activities("synthetic-account")


def test_activity_pagination_rejects_non_object_metadata() -> None:
    with pytest.raises(SnapTradeDataError, match="pagination must be an object"):
        _client({"data": [], "pagination": None}).get_activities("synthetic-account")


@pytest.mark.parametrize("page_size", [1, 2])
@pytest.mark.parametrize("provider_id", ["repeated", None])
def test_activity_pagination_rejects_duplicate_identities(
    page_size: int, provider_id: str | None
) -> None:
    repeated = _activity("repeated")
    if provider_id is None:
        repeated.pop("id")
    pages = (
        [
            {"data": [repeated], "pagination": {"total": 2}},
            {"data": [repeated], "pagination": {"total": 2}},
        ]
        if page_size == 1
        else [{"data": [repeated, repeated], "pagination": {"total": 2}}]
    )

    with pytest.raises(SnapTradeDataError, match="duplicate"):
        _paged_client(pages).get_activities("synthetic-account", page_size=page_size)


@pytest.mark.parametrize(
    "body",
    [
        {"unexpected": []},
        {
            "results": [
                {
                    "instrument": {"kind": "stock", "symbol": "NEW"},
                    "units": 1,
                    "price": 10,
                },
                {"instrument": {"kind": "stock"}, "units": 1, "price": 10},
            ]
        },
    ],
)
def test_malformed_holdings_preserve_the_existing_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, body: Any
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
    client = _client(body)
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


@pytest.mark.parametrize(
    "body", [[], {"data": []}, {"results": None}, {"results": "invalid"}]
)
@pytest.mark.parametrize("method", ["get_positions", "get_options"])
def test_unified_holdings_require_a_results_list(body, method):
    with pytest.raises(SnapTradeDataError, match="results"):
        getattr(_client(body), method)("synthetic-account")


@pytest.mark.parametrize(
    "instrument",
    [
        {"kind": "stock"},
        {"kind": "stock", "symbol": " "},
        {"kind": "future", "symbol": "TEST"},
        {"kind": "option", "symbol": "SPY   260918P00620000", "multiplier": "10"},
        {"kind": "option", "symbol": "SPY   260918P00620000"},
    ],
)
@pytest.mark.parametrize("method", ["get_positions", "get_options"])
def test_unified_holdings_validate_every_instrument_before_filtering(
    instrument, method
):
    body = {"results": [{"instrument": instrument, "units": "1", "price": "10"}]}
    with pytest.raises(SnapTradeDataError):
        getattr(_client(body), method)("synthetic-account")
