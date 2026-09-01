"""Tests for the portfolio summary header."""

from pathlib import Path

import pytest

from src.ui.widgets.portfolio_header import PortfolioHeader


def test_empty_portfolio_names_resolved_imports_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FIN_GURU_DATA_ROOT", str(tmp_path))

    message = PortfolioHeader().render().plain

    assert str(tmp_path / "imports") in message
