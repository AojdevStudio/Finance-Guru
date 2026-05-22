"""Tests for the read-only SnapTrade integration seam."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from pydantic import SecretStr

from src.integrations.snaptrade.cli import main
from src.integrations.snaptrade.client import SnapTradeClientWrapper
from src.integrations.snaptrade.models import SnapTradeCredentials


class FakeResponse:
    """Small SDK response double with a `.body` attribute."""

    def __init__(self, body):
        """Store fake response body."""
        self.body = body


class FakeAccountInformation:
    """Fake SnapTrade account_information API."""

    def list_user_accounts(self, user_id: str, user_secret: str):
        """Return representative SDK account payloads."""
        assert user_id == "user"
        assert user_secret == "secret"
        return FakeResponse(
            [
                {
                    "id": "acct-1",
                    "name": "Brokerage Individual",
                    "institution_name": "Fidelity",
                    "type": "MARGIN",
                    "currency": {"code": "USD"},
                    "number": "123456789",
                }
            ]
        )

    def get_user_account_balance(self, account_id: str, user_id: str, user_secret: str):
        """Return representative balance payload."""
        assert account_id == "acct-1"
        return FakeResponse(
            [
                {
                    "currency": {"code": "USD"},
                    "cash": 100.5,
                    "buying_power": 1000,
                    "maintenance_excess": 250,
                }
            ]
        )

    def get_user_account_positions(
        self, account_id: str, user_id: str, user_secret: str
    ):
        """Return representative position payload."""
        assert account_id == "acct-1"
        return FakeResponse(
            [
                {
                    "symbol": {"symbol": {"symbol": "SPAXX"}},
                    "average_purchase_price": 1,
                },
                {"symbol": {"symbol": {"symbol": "TSLA"}}},
            ]
        )


class FakeSDKClient:
    """Fake SnapTrade SDK client root."""

    account_information = FakeAccountInformation()


def _credentials() -> SnapTradeCredentials:
    return SnapTradeCredentials(
        client_id=SecretStr("client"),
        consumer_key=SecretStr("consumer"),
        user_id=SecretStr("user"),
        user_secret=SecretStr("secret"),
    )


def test_list_accounts_normalizes_and_masks_account_number():
    """Wrapper normalizes account payloads without exposing full account number."""
    client = SnapTradeClientWrapper(_credentials(), sdk_client=FakeSDKClient())

    accounts = client.list_accounts()

    assert len(accounts) == 1
    assert accounts[0].id == "acct-1"
    assert accounts[0].institution_name == "Fidelity"
    assert accounts[0].currency == "USD"
    assert accounts[0].number_masked == "****6789"


def test_probe_account_reports_phase_0_diagnostics():
    """Probe detects SPAXX positions and average purchase price coverage."""
    client = SnapTradeClientWrapper(_credentials(), sdk_client=FakeSDKClient())

    probe = client.probe_account("acct-1")

    assert probe["balance_count"] == 1
    assert probe["position_count"] == 2
    assert probe["spaxx_as_position"] is True
    assert probe["average_purchase_price_present_count"] == 1
    assert probe["average_purchase_price_missing_count"] == 1


def test_credentials_from_env_reports_missing_keys(monkeypatch: pytest.MonkeyPatch):
    """Missing SnapTrade env keys fail closed with key names only."""
    for key in (
        "SNAPTRADE_CLIENT_ID",
        "SNAPTRADE_CONSUMER_KEY",
        "SNAPTRADE_USER_ID",
        "SNAPTRADE_USER_SECRET",
    ):
        monkeypatch.setenv(key, "")

    with pytest.raises(ValueError, match="SNAPTRADE_CLIENT_ID"):
        SnapTradeCredentials.from_env()


def test_accounts_cli_writes_unassigned_disabled_config(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    """CLI writes conservative local routing config for later phases."""

    class FakeWrapper:
        @classmethod
        def from_env(cls):
            return cls()

        def list_accounts(self):
            return SnapTradeClientWrapper(
                _credentials(), sdk_client=FakeSDKClient()
            ).list_accounts()

    monkeypatch.setattr(
        "src.integrations.snaptrade.cli.SnapTradeClientWrapper", FakeWrapper
    )
    config_path = tmp_path / "snaptrade-accounts.yaml"

    exit_code = main(
        [
            "accounts",
            "--output",
            "json",
            "--write-config",
            str(config_path),
        ]
    )

    assert exit_code == 0
    assert '"account_count": 1' in capsys.readouterr().out
    config = yaml.safe_load(config_path.read_text())
    assert config["accounts"][0]["snaptrade_account_id"] == "acct-1"
    assert config["accounts"][0]["role"] == "unassigned"
    assert config["accounts"][0]["enabled"] is False
