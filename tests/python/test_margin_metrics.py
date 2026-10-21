from __future__ import annotations

import json
import os
import sqlite3
import sys
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from src.analysis import margin_metrics as mm
from src.analysis.margin_metrics import (
    FidelityBalances,
    IncompleteBalanceGenerationError,
    MarginAccountRoutingError,
    UnsupportedMarginSourceError,
    _broker_balances_from_snaptrade,
    calculate_margin_metrics,
    metrics_from_runtime,
    parse_money,
    parse_rate,
    read_fidelity_balances,
)
from src.analysis.options import OPTION_CONTRACT_MULTIPLIER


def write_balances(path):
    path.write_text(
        "Balance,Day change\n"
        "Total account value,100000.00,250.00\n"
        "Margin buying power,50000.00,-100.00\n"
        "Net debit,-10000.00,-500.00\n"
        "Margin interest accrued this month,12.34,\n"
    )


def freeze_balance_clock(monkeypatch, current: datetime) -> None:
    class FixedDatetime(datetime):
        @classmethod
        def now(cls, tz):
            return current.astimezone(tz)

    monkeypatch.setattr(mm, "datetime", FixedDatetime)


def write_account_config(path: Path, accounts: list[tuple[str, str, bool]]) -> None:
    path.write_text(
        json.dumps(
            {
                "generated_at": "2026-01-01T00:00:00+00:00",
                "accounts": [
                    {
                        "snaptrade_account_id": account_id,
                        "role": role,
                        "enabled": enabled,
                    }
                    for account_id, role, enabled in accounts
                ],
            }
        )
    )


def write_balances_db(
    path: Path, rows: list[tuple[str, float, float, float, str]]
) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            "CREATE TABLE balances (account_id TEXT PRIMARY KEY, currency TEXT, "
            "settled_cash REAL, buying_power REAL, account_equity REAL, "
            "gross_market_value REAL, margin_debt REAL, synced_at TEXT NOT NULL)"
        )
        conn.executemany(
            "INSERT INTO balances VALUES (?, 'USD', 0.0, ?, ?, 0.0, ?, ?)", rows
        )
        conn.commit()
    finally:
        conn.close()


def test_parse_money_supports_currency_commas_percent_and_k():
    assert parse_money("$5,000") == 5000
    assert parse_money("97.5%") == 97.5
    assert parse_money("$31k+") == 31000
    assert parse_money("") is None


def test_parse_money_supports_fidelity_accounting_parentheses():
    assert parse_money("$(123.45)") == pytest.approx(-123.45)
    assert parse_money("$(1,234.56)") == pytest.approx(-1234.56)
    assert parse_money("-123.45") == pytest.approx(-123.45)


def test_parse_rate_accepts_decimal_or_percent():
    assert parse_rate("0.12") == pytest.approx(0.12)
    assert parse_rate("12%") == pytest.approx(0.12)


def test_read_fidelity_balances_parses_current_facts(tmp_path):
    csv_path = tmp_path / "Balances_for_Account_Z123.csv"
    write_balances(csv_path)

    balances = read_fidelity_balances(csv_path)

    assert balances.total_account_value == 100000
    assert balances.margin_buying_power == 50000
    assert balances.margin_debt == 10000
    assert balances.margin_interest_accrued_this_month == 12.34


def test_read_fidelity_balances_parses_accounting_paren_net_debit(tmp_path):
    csv_path = tmp_path / "Balances_for_Account_SYNTHETIC.csv"
    csv_path.write_text(
        "Account Feature,Value\nNet debit,$(123.45)\nTotal account value,$1000.00\n"
    )
    balances = read_fidelity_balances(csv_path)
    assert balances.total_account_value == pytest.approx(1000)
    assert balances.margin_debt == pytest.approx(123.45)


def test_calculate_margin_metrics_derives_values_from_live_balances(tmp_path):
    csv_path = tmp_path / "Balances_for_Account_Z123.csv"
    write_balances(csv_path)
    balances = read_fidelity_balances(csv_path)

    metrics = calculate_margin_metrics(
        balances,
        annual_rate=0.12,
        jump_alert_threshold=5000,
        monthly_dividend_income=250,
        today=date(2026, 1, 1),
    )

    assert metrics.portfolio_value == 100000
    assert metrics.margin_balance == 10000
    assert metrics.monthly_interest_cost == 100
    assert metrics.annual_interest_cost == 1200
    assert metrics.coverage_ratio == 2.5
    assert metrics.portfolio_margin_ratio == 10
    assert metrics.alert_status == "green"


def test_metrics_from_runtime_uses_latest_csv_and_env_config(tmp_path, monkeypatch):
    imports_dir = tmp_path / "imports"
    imports_dir.mkdir()
    older = imports_dir / "Balances_for_Account_OLD.csv"
    newer = imports_dir / "Balances_for_Account_NEW.csv"
    write_balances(older)
    write_balances(newer)
    os.utime(older, (1, 1))
    os.utime(newer, (2, 2))

    monkeypatch.setenv("FIN_GURU_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("FG_MARGIN_INTEREST_RATE_DECIMAL", "0.12")
    monkeypatch.setenv("FG_MARGIN_JUMP_ALERT_THRESHOLD", "$5,000")
    monkeypatch.setenv("FG_DIVIDEND_MONTHLY_INCOME", "$250")
    monkeypatch.setenv("FG_STRATEGY_START_DATE", "2025-12-01")

    metrics = metrics_from_runtime(source="csv", today=date(2026, 1, 1))

    assert metrics.source_file.endswith("Balances_for_Account_NEW.csv")
    assert metrics.monthly_interest_cost == 100
    assert metrics.coverage_ratio == 2.5
    assert metrics.months_elapsed == 1


class _FakeSnapClient:
    """Minimal SnapTrade client double for the balance adapter."""

    EQUITY = 185294.88
    STOCK = {"price": 100.0, "quantity": 2668.029}
    OPTION = {"price": 3.93, "quantity": 2.0}

    def get_balances(self, account_id):
        return [{"currency": "USD", "cash": 0.0, "buying_power": 0.0}]

    def get_account_equity(self, account_id):
        return self.EQUITY

    def get_positions(self, account_id):
        return [self.STOCK]

    def get_options(self, account_id):
        return [self.OPTION]


def test_metrics_from_runtime_defaults_to_db(monkeypatch):
    """With no source/csv_path, runtime metrics read the local DB snapshot (default)."""
    sentinel = FidelityBalances(
        source_file="db:family_office.db",
        total_account_value=185294.88,
        total_account_day_change=None,
        margin_buying_power=0.0,
        margin_buying_power_day_change=None,
        margin_debt=83820.02,
        net_debit_day_change=None,
        margin_interest_accrued_this_month=None,
    )
    monkeypatch.setattr(mm, "read_db_balances", lambda: sentinel)
    monkeypatch.setenv("FG_MARGIN_INTEREST_RATE_DECIMAL", "0.12")
    monkeypatch.setenv("FG_MARGIN_JUMP_ALERT_THRESHOLD", "$5,000")

    metrics = metrics_from_runtime(today=date(2026, 1, 1))

    assert metrics.source_file == "db:family_office.db"
    assert metrics.margin_balance == 83820.02


def test_metrics_from_runtime_snaptrade_source_reads_api(monkeypatch):
    """source='snaptrade' pulls live from the SnapTrade API adapter."""
    sentinel = FidelityBalances(
        source_file="snaptrade:acct-1",
        total_account_value=185294.88,
        total_account_day_change=None,
        margin_buying_power=0.0,
        margin_buying_power_day_change=None,
        margin_debt=83820.02,
        net_debit_day_change=None,
        margin_interest_accrued_this_month=None,
    )
    monkeypatch.setattr(mm, "read_snaptrade_balances", lambda: sentinel)
    monkeypatch.setenv("FG_MARGIN_INTEREST_RATE_DECIMAL", "0.12")
    monkeypatch.setenv("FG_MARGIN_JUMP_ALERT_THRESHOLD", "$5,000")

    metrics = metrics_from_runtime(source="snaptrade", today=date(2026, 1, 1))

    assert metrics.source_file == "snaptrade:acct-1"
    assert metrics.margin_balance == 83820.02


def test_metrics_from_runtime_rejects_unsupported_source(monkeypatch):
    sentinel = FidelityBalances(
        source_file="db:synthetic.db",
        total_account_value=100000.0,
        total_account_day_change=None,
        margin_buying_power=1000.0,
        margin_buying_power_day_change=None,
        margin_debt=10000.0,
        net_debit_day_change=None,
        margin_interest_accrued_this_month=None,
    )
    monkeypatch.setattr(mm, "read_db_balances", lambda: sentinel)
    monkeypatch.setenv("FG_MARGIN_JUMP_ALERT_THRESHOLD", "$5,000")

    with pytest.raises(UnsupportedMarginSourceError) as exc_info:
        metrics_from_runtime(source="unsupported", annual_rate=0.12)

    assert "db, snaptrade, csv" in str(exc_info.value)


def test_read_db_balances_reads_latest_snapshot(tmp_path, monkeypatch):
    """read_db_balances returns the newest balances row as Fidelity-shaped facts."""
    freeze_balance_clock(monkeypatch, datetime(2026, 7, 18, 16, tzinfo=UTC))
    write_account_config(
        tmp_path / "snaptrade-accounts.yaml",
        [("acct-1", "taxable_margin", True)],
    )
    db_path = tmp_path / "family_office.db"
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "CREATE TABLE balances (account_id TEXT PRIMARY KEY, currency TEXT, "
            "settled_cash REAL, buying_power REAL, account_equity REAL, "
            "gross_market_value REAL, margin_debt REAL, synced_at TEXT NOT NULL)"
        )
        conn.execute(
            "INSERT INTO balances VALUES ('acct-1','USD',0.0,1000.0,150000.00,"
            "200000.00,50000.00,'2026-07-18T15:37:11+00:00')"
        )
        conn.commit()
    finally:
        conn.close()
    monkeypatch.setenv("FIN_GURU_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    balances = mm.read_db_balances()

    assert balances.source_file == f"db:{db_path}"
    assert balances.total_account_value == 150000.00
    assert balances.margin_debt == pytest.approx(50000.00)
    assert balances.margin_interest_accrued_this_month is None


def test_read_db_balances_routes_to_unique_enabled_taxable_margin_account(
    tmp_path, monkeypatch
):
    freeze_balance_clock(monkeypatch, datetime(2026, 1, 1, 1, tzinfo=UTC))
    config_path = tmp_path / "snaptrade-accounts.yaml"
    write_account_config(
        config_path,
        [
            ("synthetic-retirement", "retirement", True),
            ("synthetic-margin", "taxable_margin", True),
            ("synthetic-margin-disabled", "taxable_margin", False),
        ],
    )
    db_path = tmp_path / "family_office.db"
    write_balances_db(
        db_path,
        [
            (
                "synthetic-retirement",
                1000.0,
                900000.0,
                0.0,
                "2026-01-01T00:00:00+00:00",
            ),
            (
                "synthetic-margin",
                5000.0,
                150000.0,
                50000.0,
                "2026-01-01T00:00:00+00:00",
            ),
        ],
    )
    monkeypatch.setenv("FIN_GURU_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    balances = mm.read_db_balances()

    assert balances.total_account_value == 150000.0
    assert balances.margin_debt == 50000.0


def test_read_db_balances_rejects_missing_taxable_margin_account(tmp_path, monkeypatch):
    write_account_config(
        tmp_path / "snaptrade-accounts.yaml",
        [
            ("synthetic-retirement", "retirement", True),
            ("synthetic-margin-disabled", "taxable_margin", False),
        ],
    )
    db_path = tmp_path / "family_office.db"
    write_balances_db(
        db_path,
        [
            (
                "synthetic-retirement",
                1000.0,
                900000.0,
                0.0,
                "2026-01-01T00:00:00+00:00",
            ),
        ],
    )
    monkeypatch.setenv("FIN_GURU_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    with pytest.raises(MarginAccountRoutingError) as exc_info:
        mm.read_db_balances()

    assert "exactly one" in str(exc_info.value)


def test_read_db_balances_rejects_ambiguous_taxable_margin_accounts(
    tmp_path, monkeypatch
):
    write_account_config(
        tmp_path / "snaptrade-accounts.yaml",
        [
            ("synthetic-margin-a", "taxable_margin", True),
            ("synthetic-margin-b", "taxable_margin", True),
        ],
    )
    db_path = tmp_path / "family_office.db"
    write_balances_db(
        db_path,
        [
            (
                "synthetic-margin-a",
                1000.0,
                100000.0,
                10000.0,
                "2026-01-01T00:00:00+00:00",
            ),
            (
                "synthetic-margin-b",
                2000.0,
                200000.0,
                20000.0,
                "2026-01-01T00:00:00+00:00",
            ),
        ],
    )
    monkeypatch.setenv("FIN_GURU_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    with pytest.raises(MarginAccountRoutingError) as exc_info:
        mm.read_db_balances()

    assert "Found 2" in str(exc_info.value)


def test_read_db_balances_rejects_incomplete_latest_generation(tmp_path, monkeypatch):
    freeze_balance_clock(monkeypatch, datetime(2026, 1, 4, tzinfo=UTC))
    write_account_config(
        tmp_path / "snaptrade-accounts.yaml",
        [
            ("synthetic-margin", "taxable_margin", True),
            ("synthetic-retirement", "retirement", True),
        ],
    )
    db_path = tmp_path / "family_office.db"
    write_balances_db(
        db_path,
        [
            (
                "synthetic-margin",
                1000.0,
                100000.0,
                10000.0,
                "2026-01-01T00:00:00+00:00",
            ),
            (
                "synthetic-retirement",
                2000.0,
                200000.0,
                0.0,
                "2026-01-02T00:00:00+00:00",
            ),
        ],
    )
    monkeypatch.setenv("FIN_GURU_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    with pytest.raises(IncompleteBalanceGenerationError) as exc_info:
        mm.read_db_balances()

    assert "run the sync-first refresh" in str(exc_info.value)


def test_margin_cli_json_includes_educational_disclaimer(tmp_path, monkeypatch, capsys):
    csv_path = tmp_path / "Balances_for_Account_SYNTHETIC.csv"
    write_balances(csv_path)
    monkeypatch.setenv("FG_MARGIN_JUMP_ALERT_THRESHOLD", "$5,000")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "margin_metrics",
            "--source",
            "csv",
            "--csv",
            str(csv_path),
            "--annual-rate",
            "0.12",
            "--monthly-dividend-income",
            "250",
            "--pretty",
        ],
    )

    mm.main()

    output = json.loads(capsys.readouterr().out)
    assert "educational purposes only" in output["disclaimer"].lower()
    assert "not investment advice" in output["disclaimer"].lower()
    assert "licensed financial professional" in output["disclaimer"].lower()
    assert "loss of principal" in output["disclaimer"].lower()


def test_broker_balances_from_snaptrade_derives_margin_debt():
    """SnapTrade adapter yields broker balances with the derived margin debt."""
    balances = _broker_balances_from_snaptrade(_FakeSnapClient(), "acct-1")

    assert balances.source_file == "snaptrade:acct-1"
    stock_value = _FakeSnapClient.STOCK["price"] * _FakeSnapClient.STOCK["quantity"]
    option_value = (
        _FakeSnapClient.OPTION["price"]
        * _FakeSnapClient.OPTION["quantity"]
        * OPTION_CONTRACT_MULTIPLIER
    )
    expected_margin_debt = stock_value + option_value - _FakeSnapClient.EQUITY

    assert balances.total_account_value == _FakeSnapClient.EQUITY
    assert balances.margin_debt == pytest.approx(expected_margin_debt)
    assert balances.margin_interest_accrued_this_month is None


@pytest.fixture
def dividend_instance(tmp_path, monkeypatch):
    monkeypatch.setenv("FIN_GURU_DATA_ROOT", str(tmp_path))
    monkeypatch.delenv("FG_DIVIDEND_MONTHLY_INCOME", raising=False)
    monkeypatch.setenv("FG_MARGIN_JUMP_ALERT_THRESHOLD", "5000")
    write_account_config(
        tmp_path / "snaptrade-accounts.yaml",
        [
            ("synthetic-margin", "taxable_margin", True),
            ("synthetic-retirement", "retirement", True),
        ],
    )
    balances = tmp_path / "synthetic-balances.csv"
    write_balances(balances)
    ledger = tmp_path / "family_office.db"
    with sqlite3.connect(ledger) as connection:
        connection.execute(
            "CREATE TABLE transactions (account_id TEXT, date TEXT, type TEXT, amount REAL, currency TEXT)"
        )
        connection.executemany(
            "INSERT INTO transactions VALUES (?, ?, ?, ?, ?)",
            [
                ("synthetic-margin", "2025-10-01", "DIVIDEND", 60, "USD"),
                ("synthetic-margin", "2025-11-15", "DIVIDEND", 90, "USD"),
                ("synthetic-margin", "2025-12-31", "DIVIDEND", 150, "USD"),
                ("synthetic-margin", "2025-09-30", "DIVIDEND", 1000, "USD"),
                ("synthetic-margin", "2026-01-01", "DIVIDEND", 5000, "USD"),
                ("synthetic-retirement", "2025-12-15", "DIVIDEND", 9000, "USD"),
                ("synthetic-margin", "2025-12-15", "BUY", 9000, "USD"),
            ],
        )
    write_balances_db(
        ledger,
        [
            ("synthetic-margin", 50000, 100000, 10000, "2026-01-15T00:00:00Z"),
            ("synthetic-retirement", 0, 500, 0, "2026-01-15T00:00:00Z"),
        ],
    )
    return balances, ledger


def test_margin_cli_derives_income_from_three_closed_months(
    dividend_instance, monkeypatch, capsys
):
    from src.analysis.margin_metrics_cli import main

    class FixedDate(date):
        @classmethod
        def today(cls):
            return cls(2026, 1, 15)

    monkeypatch.setattr(mm, "date", FixedDate)
    balances, ledger = dividend_instance
    original_bytes = ledger.read_bytes()
    assert main(["--annual-rate", "0.12"]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["monthly_dividend_income"] == 100
    assert output["coverage_ratio"] == 1
    assert output["dividend_income"]["source"] == "ledger"
    assert output["dividend_income"]["window_start"] == "2025-10-01"
    assert output["dividend_income"]["window_end_exclusive"] == "2026-01-01"
    assert ledger.read_bytes() == original_bytes


@pytest.mark.parametrize(
    ("flag", "environment", "expected", "source"),
    [
        (0, "250", 0, "flag"),
        (400, "250", 400, "flag"),
        (None, "250", 250, "env"),
    ],
)
def test_dividend_income_precedence(
    dividend_instance, monkeypatch, flag, environment, expected, source
):
    balances, ledger = dividend_instance
    monkeypatch.setenv("FG_DIVIDEND_MONTHLY_INCOME", environment)
    ledger.write_bytes(b"not a SQLite database")
    result = metrics_from_runtime(
        csv_path=balances,
        annual_rate=0.12,
        monthly_dividend_income=flag,
        today=date(2026, 1, 15),
    )
    assert result.monthly_dividend_income == expected
    assert result.dividend_income.source == source
    assert result.dividend_income.window_start is None


def test_missing_dividend_ledger_is_explicit_and_never_created(tmp_path, monkeypatch):
    monkeypatch.setenv("FIN_GURU_DATA_ROOT", str(tmp_path))
    monkeypatch.delenv("FG_DIVIDEND_MONTHLY_INCOME", raising=False)
    monkeypatch.setenv("FG_MARGIN_JUMP_ALERT_THRESHOLD", "5000")
    balances = tmp_path / "synthetic-balances.csv"
    write_balances(balances)
    result = metrics_from_runtime(csv_path=balances, annual_rate=0.12)
    assert result.monthly_dividend_income is None
    assert result.dividend_income.source == "unavailable"
    assert result.dividend_income.unavailable_reason == "ledger_missing"
    assert not (tmp_path / "family_office.db").exists()


@pytest.mark.parametrize(("amount", "currency"), [(None, "USD"), (60, "EUR")])
def test_dividend_fallback_blocks_unknown_amount_or_currency(
    dividend_instance, amount, currency
):
    balances, ledger = dividend_instance
    with sqlite3.connect(ledger) as connection:
        connection.execute(
            "UPDATE transactions SET amount = ?, currency = ? WHERE date = '2025-10-01'",
            (amount, currency),
        )
    with pytest.raises(ValueError, match="known USD amount"):
        metrics_from_runtime(
            csv_path=balances, annual_rate=0.12, today=date(2026, 1, 15)
        )
