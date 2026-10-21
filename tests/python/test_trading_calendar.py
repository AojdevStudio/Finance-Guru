"""Trading-day math goes through src.utils.trading_calendar, never a bare 252."""

import ast
from pathlib import Path

from src.utils.trading_calendar import TRADING_DAYS_PER_YEAR, calendar_days_for

SRC = Path(__file__).resolve().parents[2] / "src"
CALENDAR_MODULE = SRC / "utils" / "trading_calendar.py"


def test_calendar_days_cover_requested_trading_days() -> None:
    assert calendar_days_for(TRADING_DAYS_PER_YEAR) == 378
    assert calendar_days_for(90) == 135
    assert calendar_days_for(3) == 5


def test_src_has_no_literal_trading_days_per_year() -> None:
    offenders = [
        f"{path.relative_to(SRC.parent)}:{node.lineno}"
        for path in sorted(SRC.rglob("*.py"))
        if path != CALENDAR_MODULE
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
        if isinstance(node, ast.Constant)
        and type(node.value) is int
        and node.value == TRADING_DAYS_PER_YEAR
    ]
    assert offenders == [], (
        "Use TRADING_DAYS_PER_YEAR from src.utils.trading_calendar instead of "
        f"the literal 252: {offenders}"
    )
