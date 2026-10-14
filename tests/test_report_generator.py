"""Tests for the FinanceReport skill's PDF report generator."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

from src.utils.market_data import PriceData

_GENERATOR_PATH = (
    Path(__file__).resolve().parents[1]
    / ".claude/skills/FinanceReport/tools/ReportGenerator.py"
)


@pytest.fixture
def generator() -> ModuleType:
    spec = importlib.util.spec_from_file_location("report_generator", _GENERATOR_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _cell_texts(report) -> list[str]:
    texts: list[str] = []
    for flowable in report.story:
        for row in getattr(flowable, "_cellvalues", []):
            texts.extend(str(cell) for cell in row)
    return texts


def test_main_exits_nonzero_when_price_is_missing(generator, monkeypatch, tmp_path):
    monkeypatch.setattr("src.utils.market_data.get_prices", lambda *a, **k: {})
    monkeypatch.setattr(
        sys,
        "argv",
        ["ReportGenerator.py", "--ticker", "ZZZZ", "--output-dir", str(tmp_path)],
    )

    with pytest.raises(SystemExit) as exit_info:
        generator.main()

    assert exit_info.value.code != 0
    assert list(tmp_path.iterdir()) == []


def test_main_labels_the_daily_change_and_omits_ytd(generator, monkeypatch, tmp_path):
    quote = PriceData(
        symbol="ABC",
        price=50.0,
        change=1.0,
        change_percent=2.0,
        timestamp="2026-10-14T15:00:00Z",
        source="yfinance",
    )
    monkeypatch.setattr(
        "src.utils.market_data.get_prices", lambda *a, **k: {"ABC": quote}
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["ReportGenerator.py", "--ticker", "ABC", "--output-dir", str(tmp_path)],
    )
    built: list = []
    monkeypatch.setattr(
        generator.FinanceGuruReport, "build", lambda self: built.append(self)
    )

    generator.main()

    cells = _cell_texts(built[0])
    assert "Daily Change:" in cells
    assert "+2.0%" in cells
    assert "YTD Performance:" not in cells


def _built_story(generator, monkeypatch, report) -> list:
    captured: list = []
    monkeypatch.setattr(
        generator.SimpleDocTemplate,
        "build",
        lambda self, story: captured.extend(story),
    )
    report.build()
    return captured


def _disclaimer_count(story: list) -> int:
    return sum("DISCLAIMER" in getattr(f, "text", "") for f in story)


def test_build_adds_the_disclaimer_exactly_once(generator, monkeypatch, tmp_path):
    report = generator.FinanceGuruReport(ticker="ABC", output_dir=tmp_path)
    report.add_disclaimer()

    assert _disclaimer_count(_built_story(generator, monkeypatch, report)) == 1


def test_build_adds_a_missing_disclaimer(generator, monkeypatch, tmp_path):
    report = generator.FinanceGuruReport(ticker="ABC", output_dir=tmp_path)

    assert _disclaimer_count(_built_story(generator, monkeypatch, report)) == 1
