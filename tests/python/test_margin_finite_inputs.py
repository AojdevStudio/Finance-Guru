from __future__ import annotations

import json
import math
import os
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.analysis import margin_metrics as mm

NONFINITE = ["nan", "+nan", "-nan", "inf", "+inf", "-inf"]


@pytest.fixture
def balances_csv(tmp_path):
    path = tmp_path / "synthetic-balances.csv"
    path.write_text("Balance,Value\nTotal account value,100000\nNet debit,-12000\n")
    return path


@pytest.mark.parametrize("field", ["monthly_dividend_income", "jump_alert_threshold"])
@pytest.mark.parametrize("raw", NONFINITE)
def test_calculator_refuses_nonfinite_inputs(balances_csv, field, raw):
    inputs = {"monthly_dividend_income": 0.0, "jump_alert_threshold": 5000.0}
    inputs[field] = float(raw)

    with pytest.raises(ValidationError, match=field):
        mm.calculate_margin_metrics(
            mm.read_fidelity_balances(balances_csv), annual_rate=0.12, **inputs
        )


def run_cli(balances_csv, *, income="0", threshold="5000", flags=()):
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("FG_", "FIN_GURU_")) and key != "DATABASE_URL"
    }
    env.update(
        FIN_GURU_DATA_ROOT=str(balances_csv.parent),
        FG_MARGIN_INTEREST_RATE_DECIMAL="0.12",
        FG_DIVIDEND_MONTHLY_INCOME=income,
        FG_MARGIN_JUMP_ALERT_THRESHOLD=threshold,
        PYTHONPATH=str(Path(__file__).resolve().parents[2]),
    )
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "src.analysis.margin_metrics_cli",
            "--csv",
            str(balances_csv),
            *flags,
        ],
        cwd=balances_csv.parent,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


@pytest.mark.parametrize("source", ["income_flag", "income_env", "threshold_env"])
@pytest.mark.parametrize("raw", NONFINITE)
def test_subprocess_cli_refuses_nonfinite_inputs_without_output_or_writes(
    balances_csv, source, raw
):
    before = balances_csv.read_bytes()
    if source == "income_flag":
        result = run_cli(balances_csv, flags=(f"--monthly-dividend-income={raw}",))
    elif source == "income_env":
        result = run_cli(balances_csv, income=raw)
    else:
        result = run_cli(balances_csv, threshold=raw)

    assert result.returncode != 0, result.stdout
    assert result.stdout == ""
    field = "jump_alert_threshold" if source == "threshold_env" else "monthly_income"
    assert f"\n{field}\n" in result.stderr
    assert "finite_number" in result.stderr
    assert balances_csv.read_bytes() == before
    assert set(balances_csv.parent.iterdir()) == {balances_csv}


@pytest.mark.parametrize(
    "income,coverage", [(None, None), (0.0, 0.0), (-250.0, -2.08), (250.0, 2.08)]
)
def test_calculator_preserves_finite_income_policy(balances_csv, income, coverage):
    metrics = mm.calculate_margin_metrics(
        mm.read_fidelity_balances(balances_csv),
        annual_rate=0.12,
        jump_alert_threshold=0.0,
        monthly_dividend_income=income,
    )

    assert metrics.monthly_dividend_income == income
    assert metrics.jump_alert_threshold == 0.0
    assert metrics.coverage_ratio == coverage


@pytest.mark.parametrize(
    "income,coverage", [("0", 0.0), ("-250", -2.08), ("250", 2.08)]
)
def test_subprocess_cli_preserves_finite_income_and_zero_threshold(
    balances_csv, income, coverage
):
    result = run_cli(balances_csv, income=income, threshold="0")

    assert result.returncode == 0, result.stderr
    metrics = json.loads(result.stdout)
    assert metrics["monthly_dividend_income"] == float(income)
    assert metrics["coverage_ratio"] == coverage
    assert metrics["jump_alert_threshold"] == 0
    assert all(
        math.isfinite(value) for value in metrics.values() if isinstance(value, float)
    )
