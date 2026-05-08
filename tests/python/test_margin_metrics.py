from __future__ import annotations

import os
from datetime import date

import pytest

from src.analysis.margin_metrics import (
    calculate_margin_metrics,
    metrics_from_runtime,
    parse_money,
    parse_rate,
    read_fidelity_balances,
)


def write_balances(path):
    path.write_text(
        "Balance,Day change\n"
        "Total account value,100000.00,250.00\n"
        "Margin buying power,50000.00,-100.00\n"
        "Net debit,-10000.00,-500.00\n"
        "Margin interest accrued this month,12.34,\n"
    )


def test_parse_money_supports_currency_commas_percent_and_k():
    assert parse_money("$5,000") == 5000
    assert parse_money("97.5%") == 97.5
    assert parse_money("$31k+") == 31000
    assert parse_money("") is None


def test_parse_rate_accepts_decimal_or_percent():
    assert parse_rate("0.12") == pytest.approx(0.12)
    assert parse_rate("12%") == pytest.approx(0.12)


def test_read_fidelity_balances_parses_current_facts(tmp_path):
    csv_path = tmp_path / "Balances_for_Account_Z123.csv"
    write_balances(csv_path)

    balances = read_fidelity_balances(csv_path)

    assert balances.total_account_value == 100000
    assert balances.margin_buying_power == 50000
    assert balances.net_debit == -10000
    assert balances.margin_interest_accrued_this_month == 12.34


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
    older = tmp_path / "Balances_for_Account_OLD.csv"
    newer = tmp_path / "Balances_for_Account_NEW.csv"
    write_balances(older)
    write_balances(newer)
    os.utime(older, (1, 1))
    os.utime(newer, (2, 2))

    monkeypatch.setenv("FIN_GURU_PORTFOLIO_DIR", str(tmp_path))
    monkeypatch.setenv("FG_MARGIN_INTEREST_RATE_DECIMAL", "0.12")
    monkeypatch.setenv("FG_MARGIN_JUMP_ALERT_THRESHOLD", "$5,000")
    monkeypatch.setenv("FG_DIVIDEND_MONTHLY_INCOME", "$250")
    monkeypatch.setenv("FG_STRATEGY_START_DATE", "2025-12-01")

    metrics = metrics_from_runtime(today=date(2026, 1, 1))

    assert metrics.source_file.endswith("Balances_for_Account_NEW.csv")
    assert metrics.monthly_interest_cost == 100
    assert metrics.coverage_ratio == 2.5
    assert metrics.months_elapsed == 1
