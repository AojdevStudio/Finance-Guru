"""Offline margin buying-power tests with synthetic broker responses."""

from __future__ import annotations

import pytest

from src.analysis.margin_metrics import _broker_balances_from_snaptrade
from src.integrations.snaptrade.client import BalanceCurrencyMismatchError


class SyntheticMarginClient:
    def __init__(self, balances: list[dict[str, object]]) -> None:
        self.balances = balances

    def get_balances(self, account_id: str) -> list[dict[str, object]]:
        return self.balances

    def get_account_equity(self, account_id: str) -> float:
        return 100000.0

    def get_positions(self, account_id: str) -> list[dict[str, object]]:
        return [{"symbol": "SYNTHETIC", "quantity": 1100.0, "price": 100.0}]

    def get_options(self, account_id: str) -> list[dict[str, object]]:
        return []


@pytest.mark.parametrize("buying_power", [50000.0, 0.0, None])
def test_live_margin_buying_power_uses_usd_row(buying_power: float | None) -> None:
    client = SyntheticMarginClient(
        [
            {"currency": "EUR", "cash": 0.0, "buying_power": 7.0},
            {"currency": "USD", "cash": 0.0, "buying_power": buying_power},
        ]
    )

    balances = _broker_balances_from_snaptrade(client, "synthetic-margin")

    assert balances.margin_buying_power == buying_power
    assert balances.margin_debt == 10000.0


@pytest.mark.parametrize(
    "balances",
    [[], [{"currency": "EUR", "cash": 0.0, "buying_power": 50000.0}]],
    ids=["missing-balances", "foreign-currency-only"],
)
def test_live_margin_buying_power_refuses_missing_usd_row(
    balances: list[dict[str, object]],
) -> None:
    client = SyntheticMarginClient(balances)

    with pytest.raises(BalanceCurrencyMismatchError, match="no USD balance row"):
        _broker_balances_from_snaptrade(client, "synthetic-margin")
