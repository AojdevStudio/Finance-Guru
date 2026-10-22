"""Explicit zero borrowing rates take priority over runtime configuration."""

from __future__ import annotations

import json

import pytest

from src.analysis import margin_metrics as mm


@pytest.fixture
def balances_csv(tmp_path, monkeypatch):
    monkeypatch.setenv("FIN_GURU_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("FG_MARGIN_JUMP_ALERT_THRESHOLD", "5000")
    monkeypatch.setenv("FG_DIVIDEND_MONTHLY_INCOME", "0")
    monkeypatch.delenv("FG_MARGIN_INTEREST_RATE", raising=False)
    monkeypatch.delenv("FG_STRATEGY_START_DATE", raising=False)
    path = tmp_path / "synthetic-balances.csv"
    path.write_text("Balance,Value\nTotal account value,100000\nNet debit,-12000\n")
    return path


@pytest.mark.parametrize("configured", ["0.12", None, "placeholder"])
def test_margin_cli_preserves_explicit_zero_rate(
    balances_csv, configured, monkeypatch, capsys
):
    if configured is None:
        monkeypatch.delenv("FG_MARGIN_INTEREST_RATE_DECIMAL", raising=False)
    else:
        monkeypatch.setenv("FG_MARGIN_INTEREST_RATE_DECIMAL", configured)

    assert mm.main(["--csv", str(balances_csv), "--annual-rate", "0"]) == 0

    result = json.loads(capsys.readouterr().out)
    assert result["annual_interest_rate"] == 0
    assert result["monthly_interest_cost"] == 0
    assert result["annual_interest_cost"] == 0


def test_margin_cli_uses_configured_rate_when_flag_is_absent(
    balances_csv, monkeypatch, capsys
):
    monkeypatch.setenv("FG_MARGIN_INTEREST_RATE_DECIMAL", "0.12")

    assert mm.main(["--csv", str(balances_csv)]) == 0

    result = json.loads(capsys.readouterr().out)
    assert result["annual_interest_rate"] == 0.12
    assert result["monthly_interest_cost"] == 120
