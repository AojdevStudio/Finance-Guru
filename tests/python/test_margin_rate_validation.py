"""Borrowing rates must be finite and nonnegative before money is computed."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.analysis import margin_metrics as mm


@pytest.fixture
def balances_csv(tmp_path, monkeypatch):
    monkeypatch.setenv("FIN_GURU_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("FG_MARGIN_JUMP_ALERT_THRESHOLD", "5000")
    monkeypatch.setenv("FG_DIVIDEND_MONTHLY_INCOME", "0")
    monkeypatch.delenv("FG_STRATEGY_START_DATE", raising=False)
    path = tmp_path / "synthetic-balances.csv"
    path.write_text("Balance,Value\nTotal account value,100000\nNet debit,-12000\n")
    return path


@pytest.mark.parametrize("rate", [-0.01, float("nan"), float("inf"), float("-inf")])
def test_margin_calculator_refuses_invalid_annual_rate(balances_csv, rate):
    balances = mm.read_fidelity_balances(balances_csv)

    with pytest.raises(ValidationError, match="annual_rate"):
        mm.calculate_margin_metrics(
            balances, annual_rate=rate, jump_alert_threshold=5000
        )


@pytest.mark.parametrize("rate,monthly_cost", [(0, 0), (0.12, 120), (1, 1000)])
def test_margin_calculator_preserves_valid_annual_rate(
    balances_csv, rate, monthly_cost
):
    balances = mm.read_fidelity_balances(balances_csv)

    metrics = mm.calculate_margin_metrics(
        balances, annual_rate=rate, jump_alert_threshold=5000
    )

    assert metrics.annual_interest_rate == rate
    assert metrics.monthly_interest_cost == monthly_cost


@pytest.mark.parametrize("raw", ["nan", "inf"])
def test_margin_cli_refuses_nonfinite_interest_json(balances_csv, raw, capsys):
    with pytest.raises(ValidationError, match="annual_rate"):
        mm.main(["--csv", str(balances_csv), "--annual-rate", raw])

    assert capsys.readouterr().out == ""
