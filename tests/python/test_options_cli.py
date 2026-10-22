"""Offline contract checks for implied-volatility CLI outcomes."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.analysis.options import OptionsCalculator
from src.models.options_inputs import BlackScholesInput


def _run_implied_vol(option_type, premium, output, save_to=None):
    command = [
        sys.executable,
        "-m",
        "src.analysis.options_cli",
        "--ticker",
        "SYNTH",
        "--spot",
        "100",
        "--strike",
        "100",
        "--days",
        "365",
        "--type",
        option_type,
        "--risk-free-rate",
        "0",
        "--market-price",
        repr(premium),
        "--implied-vol",
        "--output",
        output,
    ]
    if save_to is not None:
        command.extend(["--save-to", str(save_to)])
    return subprocess.run(
        command,
        cwd=Path(__file__).resolve().parents[2],
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )


@pytest.mark.parametrize("option_type", ["call", "put"])
@pytest.mark.parametrize("output", ["json", "human"])
@pytest.mark.parametrize("premium", [0.1, 101.0])
def test_implied_vol_nonconvergence_is_a_cli_failure(option_type, output, premium):
    result = _run_implied_vol(option_type, premium, output)

    assert result.returncode == 1, result.stderr
    assert "did not converge" in result.stderr
    assert "✅" not in result.stderr
    assert "Traceback" not in result.stderr
    if output == "json":
        report = json.loads(result.stdout)
        assert report["converged"] is False
        assert report["market_price"] == premium
        assert report["pricing_error"] > 0
    else:
        assert "Solver did not converge" in result.stdout


@pytest.mark.parametrize("option_type", ["call", "put"])
@pytest.mark.parametrize("output", ["json", "human"])
def test_implied_vol_convergence_remains_a_cli_success(option_type, output):
    premium = (
        OptionsCalculator()
        .price_option(
            BlackScholesInput(
                spot_price=100.0,
                strike=100.0,
                time_to_expiry=1.0,
                volatility=0.3,
                risk_free_rate=0.0,
                option_type=option_type,
            )
        )
        .option_price
    )
    result = _run_implied_vol(option_type, premium, output)

    assert result.returncode == 0, result.stderr
    assert "✅ Converged" in result.stderr
    if output == "json":
        report = json.loads(result.stdout)
        assert report["converged"] is True
        assert report["implied_volatility"] == pytest.approx(0.3, abs=0.001)
    else:
        assert "Solution converged successfully" in result.stdout


def test_nonconverged_report_is_saved_before_failure_exit(tmp_path):
    destination = tmp_path / "implied-vol.json"
    result = _run_implied_vol("call", 0.1, "json", save_to=destination)

    assert result.returncode == 1, result.stderr
    assert not result.stdout
    report = json.loads(destination.read_text())
    assert report["converged"] is False
    assert report["market_price"] == 0.1
