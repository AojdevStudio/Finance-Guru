"""An explicit percent sign defines the rate unit at every positive magnitude."""

from __future__ import annotations

import json

import pytest

from src.analysis import margin_metrics as mm


@pytest.mark.parametrize(
    "raw,expected", [("1%", 0.01), ("0.5%", 0.005), ("0.125%", 0.00125)]
)
def test_margin_rate_preserves_explicit_percent_unit(raw, expected):
    assert mm.parse_rate(raw) == pytest.approx(expected)


@pytest.mark.parametrize("raw,expected", [("0.12", 0.12), ("12", 0.12), ("1", 1)])
def test_margin_rate_preserves_unmarked_decimal_and_whole_percent(raw, expected):
    assert mm.parse_rate(raw) == expected


def test_margin_cli_computes_one_percent_interest(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("FIN_GURU_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("FG_MARGIN_JUMP_ALERT_THRESHOLD", "5000")
    monkeypatch.setenv("FG_DIVIDEND_MONTHLY_INCOME", "0")
    monkeypatch.delenv("FG_STRATEGY_START_DATE", raising=False)
    path = tmp_path / "synthetic-balances.csv"
    path.write_text("Balance,Value\nTotal account value,100000\nNet debit,-12000\n")

    assert mm.main(["--csv", str(path), "--annual-rate", "1%"]) == 0

    result = json.loads(capsys.readouterr().out)
    assert result["annual_interest_rate"] == 0.01
    assert result["monthly_interest_cost"] == 10
    assert result["annual_interest_cost"] == 120
