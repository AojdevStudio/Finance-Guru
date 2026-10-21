"""Chart calculators fail closed before chart generation."""

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest


def chart_kit():
    path = (
        Path(__file__).resolve().parents[1]
        / ".claude/skills/FinanceReport/tools/ChartKit.py"
    )
    spec = importlib.util.spec_from_file_location("chart_kit", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_failed_calculator_propagates(mocker):
    module = chart_kit()
    mocker.patch.object(
        module.subprocess,
        "run",
        side_effect=subprocess.CalledProcessError(1, ["calculator"], stderr="failed"),
    )
    with pytest.raises(subprocess.CalledProcessError):
        module.run_cli_tool("calculator", [])


def test_invalid_calculator_json_propagates(mocker):
    module = chart_kit()
    mocker.patch.object(
        module.subprocess,
        "run",
        return_value=subprocess.CompletedProcess([], 0, "invalid"),
    )
    with pytest.raises(json.JSONDecodeError):
        module.run_cli_tool("calculator", [])
