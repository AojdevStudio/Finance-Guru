"""Tests for the read-only SnapTrade integration seam."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from pydantic import SecretStr

from src.integrations.snaptrade.cli import main
from src.integrations.snaptrade.client import SnapTradeClientWrapper
from src.integrations.snaptrade.models import (
    AccountRole,
    SnapTradeAccountConfig,
    SnapTradeCredentials,
)

# Three activities across the page boundary: a normal-symbol dividend, a
# null-symbol dividend that must fall back to the description ticker, and a buy.
_ACTIVITY_FIXTURE = [
    {
        "id": "a1",
        "type": "DIVIDEND",
        "symbol": {"symbol": "SCHD"},
        "units": 0,
        "price": 0,
        "amount": 51.63,
        "currency": {"code": "USD"},
        "description": "DIVIDEND RECEIVED SCHWAB US DIVIDEND EQUITY ETF (SCHD)",
        "trade_date": "2026-01-05",
        "account": {"id": "acct-1"},
    },
    {
        "id": "a2",
        "type": "DIVIDEND",
        "symbol": None,
        "units": 0,
        "price": 0,
        "amount": 78.62,
        "currency": {"code": "USD"},
        "description": "DIVIDEND RECEIVED JPMORGAN NASDAQ EQTY PREM INC ETF (JEPQ)",
        "trade_date": "2026-01-05",
        "account": {"id": "acct-1"},
    },
    {
        "id": "a3",
        "type": "BUY",
        "symbol": {"symbol": "TSLA"},
        "units": 10,
        "price": 200,
        "amount": -2000,
        "currency": {"code": "USD"},
        "description": "YOU BOUGHT TSLA",
        "trade_date": "2026-01-03",
        "account": {"id": "acct-1"},
    },
]


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
                    "units": 250.5,
                    "price": 1,
                    "average_purchase_price": 1,
                },
                {
                    "symbol": {"symbol": {"symbol": "TSLA"}},
                    "units": 10,
                    "price": 200,
                },
            ]
        )

    def get_user_account_details(self, account_id: str, user_id: str, user_secret: str):
        """Return account details with net equity total."""
        assert account_id == "acct-1"
        return FakeResponse(
            {"balance": {"total": {"amount": 1000.0, "currency": "USD"}}}
        )

    def get_account_activities(
        self,
        account_id: str,
        user_id: str,
        user_secret: str,
        offset: int = 0,
        limit: int = 1000,
        type: str | None = None,
    ):
        """Return a paginated slice of activities (offset/limit, total honored)."""
        assert account_id == "acct-1"
        page = _ACTIVITY_FIXTURE[offset : offset + limit]
        return FakeResponse(
            {
                "data": page,
                "pagination": {
                    "offset": offset,
                    "limit": limit,
                    "total": len(_ACTIVITY_FIXTURE),
                },
            }
        )


class FakeOptions:
    """Fake SnapTrade options API."""

    def list_option_holdings(self, account_id: str, user_id: str, user_secret: str):
        """Return one representative option holding (per-contract cost)."""
        assert account_id == "acct-1"
        return FakeResponse(
            [
                {
                    "symbol": {"option_symbol": {"ticker": "SPY   260918P00620000"}},
                    "units": 2,
                    "price": 3.93,
                    "average_purchase_price": 461.675,
                }
            ]
        )


class FakeSDKClient:
    """Fake SnapTrade SDK client root."""

    account_information = FakeAccountInformation()
    options = FakeOptions()


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


def test_account_config_refusal_gate():
    """Unassigned/disabled accounts are refused; verified+routed ones sync."""
    fresh = SnapTradeAccountConfig(snaptrade_account_id="a")
    assert fresh.is_syncable is False
    assert "enabled=false" in fresh.refusal_reason
    assert "role=unassigned" in fresh.refusal_reason

    enabled_unassigned = SnapTradeAccountConfig(snaptrade_account_id="a", enabled=True)
    assert enabled_unassigned.refusal_reason == "role=unassigned"

    ready = SnapTradeAccountConfig(
        snaptrade_account_id="a", role=AccountRole.TAXABLE_MARGIN, enabled=True
    )
    assert ready.is_syncable is True
    assert ready.refusal_reason is None


def _write_routing_config(path: Path, *, role: str, enabled: bool) -> None:
    path.write_text(
        "accounts:\n"
        "- snaptrade_account_id: acct-1\n"
        "  name: Fidelity ...1\n"
        f"  role: {role}\n"
        f"  enabled: {str(enabled).lower()}\n",
        encoding="utf-8",
    )


class _RoutingWrapper(SnapTradeClientWrapper):
    """Real client wired to FakeSDKClient so every endpoint resolves offline."""

    @classmethod
    def from_env(cls):
        return cls(_credentials(), sdk_client=FakeSDKClient())


def test_positions_command_refuses_unassigned_disabled_without_network(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    """Default config syncs nothing and never reaches the SnapTrade API."""
    config_path = tmp_path / "snaptrade-accounts.yaml"
    _write_routing_config(config_path, role="unassigned", enabled=False)

    def _explode():
        raise AssertionError("from_env must not run when nothing is syncable")

    monkeypatch.setattr(
        "src.integrations.snaptrade.cli.SnapTradeClientWrapper.from_env",
        staticmethod(_explode),
    )

    exit_code = main(["positions", "--config", str(config_path), "--output", "json"])

    assert exit_code == 0
    out = json.loads(capsys.readouterr().out)
    assert out["synced_account_count"] == 0
    assert out["refused_account_count"] == 1
    assert "enabled=false" in out["refused"][0]["reason"]
    assert "role=unassigned" in out["refused"][0]["reason"]


def test_positions_command_syncs_enabled_account(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    """A verified, role-assigned account returns normalized positions."""
    config_path = tmp_path / "snaptrade-accounts.yaml"
    _write_routing_config(config_path, role="taxable_margin", enabled=True)
    monkeypatch.setattr(
        "src.integrations.snaptrade.cli.SnapTradeClientWrapper", _RoutingWrapper
    )

    exit_code = main(["positions", "--config", str(config_path), "--output", "json"])

    assert exit_code == 0
    out = json.loads(capsys.readouterr().out)
    assert out["synced_account_count"] == 1
    by_symbol = {p["symbol"]: p for p in out["accounts"][0]["positions"]}
    assert by_symbol["TSLA"]["quantity"] == 10
    assert by_symbol["SPAXX"]["average_purchase_price"] == 1.0
    # options are merged in, Fidelity-symbolled, with per-share (÷100) cost
    opt = by_symbol["-SPY260918P620"]
    assert opt["instrument"] == "option"
    assert opt["quantity"] == 2
    assert round(opt["average_purchase_price"], 5) == 4.61675


def test_activities_command_emits_normalized_json(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    """The activities subcommand syncs a routed account and emits valid JSON."""
    config_path = tmp_path / "snaptrade-accounts.yaml"
    _write_routing_config(config_path, role="taxable_margin", enabled=True)
    monkeypatch.setattr(
        "src.integrations.snaptrade.cli.SnapTradeClientWrapper", _RoutingWrapper
    )

    exit_code = main(["activities", "--config", str(config_path), "--output", "json"])

    assert exit_code == 0
    out = json.loads(capsys.readouterr().out)  # criterion: valid JSON
    assert out["kind"] == "activities"
    assert out["synced_account_count"] == 1
    activities = out["accounts"][0]["activities"]
    assert len(activities) == 3
    null_div = next(a for a in activities if a["amount"] == 78.62)
    assert null_div["symbol"] == "JEPQ"


def test_activities_command_refuses_unassigned_without_network(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    """An unrouted account is refused and never reaches the SnapTrade API."""
    config_path = tmp_path / "snaptrade-accounts.yaml"
    _write_routing_config(config_path, role="unassigned", enabled=False)

    def _explode():
        raise AssertionError("from_env must not run when nothing is syncable")

    monkeypatch.setattr(
        "src.integrations.snaptrade.cli.SnapTradeClientWrapper.from_env",
        staticmethod(_explode),
    )

    exit_code = main(["activities", "--config", str(config_path), "--output", "json"])

    assert exit_code == 0
    out = json.loads(capsys.readouterr().out)
    assert out["synced_account_count"] == 0
    assert out["refused_account_count"] == 1


def test_balances_command_derives_margin_debt(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    """Balances expose settled cash plus a derived margin debt and gross MV."""
    config_path = tmp_path / "snaptrade-accounts.yaml"
    _write_routing_config(config_path, role="taxable_margin", enabled=True)
    monkeypatch.setattr(
        "src.integrations.snaptrade.cli.SnapTradeClientWrapper", _RoutingWrapper
    )

    exit_code = main(["balances", "--config", str(config_path), "--output", "json"])

    assert exit_code == 0
    bal = json.loads(capsys.readouterr().out)["accounts"][0]["balances"]
    assert bal["settled_cash"] == 100.5
    # stock MV 250.5 + 2000 = 2250.5; option MV 3.93*2*100 = 786; equity 1000
    assert bal["gross_market_value"] == 3036.5
    assert bal["account_equity"] == 1000.0
    assert bal["margin_debt"] == 2036.5


def test_routing_command_mixed_accounts(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    """A config with one routed + one unrouted account syncs only the routed one."""
    config_path = tmp_path / "snaptrade-accounts.yaml"
    config_path.write_text(
        "accounts:\n"
        "- snaptrade_account_id: acct-1\n"
        "  name: Routed\n"
        "  role: taxable_margin\n"
        "  enabled: true\n"
        "- snaptrade_account_id: acct-2\n"
        "  name: Unrouted\n"
        "  role: unassigned\n"
        "  enabled: false\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "src.integrations.snaptrade.cli.SnapTradeClientWrapper", _RoutingWrapper
    )

    exit_code = main(["positions", "--config", str(config_path), "--output", "json"])

    assert exit_code == 0
    out = json.loads(capsys.readouterr().out)
    assert out["synced_account_count"] == 1
    assert out["refused_account_count"] == 1
    assert out["accounts"][0]["account_id"] == "acct-1"
    assert len(out["accounts"][0]["positions"]) > 0
    assert out["refused"][0]["account_id"] == "acct-2"
    assert "role=unassigned" in out["refused"][0]["reason"]


def test_routing_command_reports_missing_config(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    """A missing routing config fails closed with a clear stderr message."""
    exit_code = main(
        ["balances", "--config", str(tmp_path / "nope.yaml"), "--output", "json"]
    )

    assert exit_code == 1
    assert "config" in capsys.readouterr().err.lower()


def test_occ_to_fidelity_symbol_conversion():
    """OCC option tickers convert to Fidelity's -TICKERYYMMDD{C/P}STRIKE form."""
    from src.integrations.snaptrade.client import _occ_to_fidelity_symbol

    assert _occ_to_fidelity_symbol("SPY   260918P00620000") == "-SPY260918P620"
    assert _occ_to_fidelity_symbol("QQQ   260918P00595000") == "-QQQ260918P595"
    # non-OCC input is returned unchanged
    assert _occ_to_fidelity_symbol("AAPL") == "AAPL"


def test_derive_margin_debt_math():
    """Margin debt = gross long MV (options x100) minus net equity."""
    from src.integrations.snaptrade.client import derive_margin_debt

    stocks = [{"price": 100, "quantity": 10}]  # 1000
    options = [{"price": 2.0, "quantity": 3}]  # 2*3*100 = 600
    debt, gross = derive_margin_debt(stocks, options, equity=1200.0)
    assert gross == 1600.0
    assert debt == 400.0
    # unknown equity -> debt None, gross still computed
    debt2, gross2 = derive_margin_debt(stocks, options, equity=None)
    assert debt2 is None and gross2 == 1600.0
    # net-cash account (equity > gross) clamps to 0, never a negative loan
    debt3, _ = derive_margin_debt(stocks, options, equity=2000.0)
    assert debt3 == 0.0
    # settled cash rides inside the SPAXX position, so a cash balance does NOT
    # understate the loan: securities 1000 + SPAXX 100, equity 800 -> loan 300
    with_spaxx = [{"price": 100, "quantity": 10}, {"price": 1.0, "quantity": 100}]
    debt4, gross4 = derive_margin_debt(with_spaxx, [], equity=800.0)
    assert gross4 == 1100.0
    assert debt4 == 300.0  # = loan, not loan - cash


def test_get_activities_pages_through_full_result_set():
    """Activities fetch follows offset/limit pagination until total is reached."""
    client = SnapTradeClientWrapper(_credentials(), sdk_client=FakeSDKClient())

    # page_size 2 forces >1 page over the 3-record fixture (pages of 2 then 1).
    activities = client.get_activities("acct-1", page_size=2)

    assert len(activities) == 3
    assert [a["type"] for a in activities] == ["DIVIDEND", "DIVIDEND", "BUY"]


def test_dividend_with_null_symbol_resolves_ticker_from_description():
    """A DIVIDEND whose symbol is null derives its ticker from the description."""
    client = SnapTradeClientWrapper(_credentials(), sdk_client=FakeSDKClient())

    activities = client.get_activities("acct-1", page_size=2)
    by_id = {a["account"]: a for a in activities}  # all on acct-1
    null_symbol_div = next(
        a for a in activities if a["type"] == "DIVIDEND" and a["amount"] == 78.62
    )

    assert by_id  # sanity: account field is populated
    # symbol was null on the wire; parsed "(JEPQ)" out of the description
    assert null_symbol_div["symbol"] == "JEPQ"
    # the normal-symbol dividend still resolves straight from the symbol object
    schd = next(a for a in activities if a["amount"] == 51.63)
    assert schd["symbol"] == "SCHD"


def test_summarize_activity_emits_stable_shape():
    """Each normalized activity carries the documented stable field set."""
    from src.integrations.snaptrade.client import _summarize_activity

    record = _summarize_activity(_ACTIVITY_FIXTURE[2])  # the TSLA buy

    assert record == {
        "type": "BUY",
        "date": "2026-01-03",
        "symbol": "TSLA",
        "amount": -2000.0,
        "quantity": 10.0,
        "currency": "USD",
        "description": "YOU BOUGHT TSLA",
        "account": "acct-1",
    }
