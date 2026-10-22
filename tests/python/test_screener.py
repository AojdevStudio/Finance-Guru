"""Pattern dispatch and match rules in the technical screener."""

from datetime import date

import pandas as pd
import pytest

from src.models.screener_inputs import PatternType, ScreeningCriteria, TechnicalSignal
from src.utils.screener import TechnicalScreener


def _signal(strength: str) -> TechnicalSignal:
    return TechnicalSignal(
        signal_type=PatternType.BREAKOUT,
        strength=strength,
        description="",
        date_detected=date(2025, 10, 13),
    )


@pytest.fixture
def screener() -> TechnicalScreener:
    return TechnicalScreener(ScreeningCriteria())


def test_detector_value_error_means_no_signal(screener, mocker) -> None:
    mocker.patch.object(
        screener, "_detect_golden_cross", side_effect=ValueError("bad input")
    )

    assert (
        screener._detect_pattern("T", PatternType.GOLDEN_CROSS, pd.DataFrame()) is None
    )


def test_detector_bug_is_not_swallowed(screener, mocker) -> None:
    mocker.patch.object(screener, "_detect_golden_cross", side_effect=KeyError("price"))

    with pytest.raises(KeyError):
        screener._detect_pattern("T", PatternType.GOLDEN_CROSS, pd.DataFrame())


@pytest.mark.parametrize(
    ("strengths", "expected"),
    [
        pytest.param([], False, id="no-signals"),
        pytest.param(["strong"], True, id="one-strong"),
        pytest.param(["moderate"], False, id="one-moderate"),
        pytest.param(["moderate", "moderate"], True, id="two-moderate"),
        pytest.param(["weak", "weak"], False, id="two-weak"),
        pytest.param(["weak", "weak", "weak"], True, id="three-weak"),
    ],
)
def test_meets_criteria(screener, strengths, expected) -> None:
    assert screener._meets_criteria([_signal(s) for s in strengths]) is expected


def test_score_sums_strength_points(screener) -> None:
    signals = [_signal("strong"), _signal("moderate"), _signal("weak")]

    assert screener._calculate_score(signals) == 6.0


def _price_frame(prices: list[float]) -> pd.DataFrame:
    dates = pd.bdate_range("2026-01-02", periods=len(prices))
    return pd.DataFrame({"price": prices}, index=[d.date() for d in dates])


def test_steady_decline_reports_rsi_oversold(screener) -> None:
    falling = _price_frame([100.0 - day for day in range(40)])

    signal = screener._detect_rsi_oversold(falling)

    assert signal is not None
    assert signal.signal_type == PatternType.RSI_OVERSOLD
    assert screener._get_current_rsi(falling) == pytest.approx(signal.value)


def test_a_zero_price_in_history_still_screens(screener) -> None:
    prices = [100.0 + day for day in range(60)]
    prices[10] = 0.0
    dates = [d.date() for d in pd.bdate_range("2026-01-02", periods=len(prices))]

    result = screener.screen_ticker("TEST", prices, dates)

    assert result.ticker == "TEST"


def _business_dates(count: int) -> list[date]:
    return [d.date() for d in pd.bdate_range("2026-01-02", periods=count)]


def test_bearish_only_screen_never_recommends_buying() -> None:
    prices = [100.0 + 2 * day for day in range(60)] + [
        218.0 + 0.1 * (day + 1) for day in range(20)
    ]
    screener = TechnicalScreener(ScreeningCriteria(patterns=list(PatternType)))

    result = screener.screen_ticker("TEST", prices, _business_dates(len(prices)))

    detected = {signal.signal_type for signal in result.signals}
    assert detected <= {PatternType.RSI_OVERBOUGHT, PatternType.MACD_BEARISH}
    assert detected
    assert result.recommendation in {"sell", "strong_sell"}


def test_weighted_bearish_signal_never_recommends_buying() -> None:
    prices = [200.0 - day for day in range(80)]
    screener = TechnicalScreener(
        ScreeningCriteria(patterns=[PatternType.MACD_BEARISH], pattern_weight=2)
    )

    result = screener.screen_ticker("TEST", prices, _business_dates(len(prices)))

    assert result.recommendation in {"hold", "sell", "strong_sell"}


def test_portfolio_screening_propagates_a_ticker_failure(screener, mocker):
    mocker.patch.object(
        screener, "screen_ticker", side_effect=RuntimeError("failed detector")
    )
    with pytest.raises(RuntimeError, match="failed detector"):
        screener.screen_portfolio({"SYNTHETIC": ([100.0], [date(2026, 1, 1)], None)})
