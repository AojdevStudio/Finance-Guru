"""Cross-field rules on the screener input and output models."""

from datetime import date

import pytest
from pydantic import ValidationError

from src.models.screener_inputs import PortfolioScreeningOutput, ScreeningCriteria


def test_ma_slow_must_exceed_ma_fast() -> None:
    with pytest.raises(ValidationError, match="ma_slow"):
        ScreeningCriteria(ma_fast=100, ma_slow=100)


def test_ma_slow_above_fast_is_accepted() -> None:
    criteria = ScreeningCriteria(ma_fast=50, ma_slow=200)

    assert criteria.ma_slow > criteria.ma_fast


def test_rsi_overbought_below_oversold_is_rejected() -> None:
    with pytest.raises(ValidationError):
        ScreeningCriteria(rsi_oversold=40.0, rsi_overbought=20.0)


def test_tickers_matching_cannot_exceed_total_screened() -> None:
    with pytest.raises(ValidationError, match="tickers_matching"):
        PortfolioScreeningOutput(
            screening_date=date(2025, 10, 13),
            criteria_used=[],
            total_tickers_screened=2,
            tickers_matching=3,
            summary="",
        )


def test_tickers_matching_equal_to_total_is_accepted() -> None:
    output = PortfolioScreeningOutput(
        screening_date=date(2025, 10, 13),
        criteria_used=[],
        total_tickers_screened=3,
        tickers_matching=3,
        summary="",
    )

    assert output.tickers_matching == output.total_tickers_screened
