"""Regression tests for supported CLI help entry points."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    ("command", "expected_option"),
    (
        ([sys.executable, "src/utils/momentum_cli.py", "--help"], "--stoch-k"),
        (
            [sys.executable, "-m", "src.utils.input_validation_cli", "--help"],
            "--outlier-method",
        ),
    ),
    ids=("momentum", "input-validation"),
)
def test_cli_help_renders_without_network(
    command: list[str], expected_option: str
) -> None:
    result = subprocess.run(
        command,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "usage:" in result.stdout
    assert expected_option in result.stdout
