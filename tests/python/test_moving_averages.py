"""Tests for Finance Guru moving averages calculator.

Tests the MovingAverageCalculator class with synthetic price data.
No real API calls -- all data is generated with numpy.
"""

from datetime import date, timedelta

import numpy as np
import pytest

from src.models.moving_avg_inputs import (
    MovingAverageAnalysis,
    MovingAverageConfig,
    MovingAverageDataInput,
    MovingAverageOutput,
)
from src.utils.moving_averages import MovingAverageCalculator, calculate_moving_average


def _make_dates(n: int) -> list[date]:
    start = date(2024, 1, 2)
    return [start + timedelta(days=i) for i in range(n)]


def _make_ma_data(
    n: int = 100,
    start_price: float = 100.0,
    trend: float = 0.1,
    volatility: float = 1.0,
    seed: int = 42,
) -> MovingAverageDataInput:
    """Build MovingAverageDataInput with synthetic price data."""
    rng = np.random.default_rng(seed)
    prices = [start_price]
    for _ in range(n - 1):
        prices.append(prices[-1] + trend + rng.normal(0, volatility))
    prices = [max(p, 0.01) for p in prices]

    return MovingAverageDataInput(
        ticker="TEST",
        dates=_make_dates(n),
        prices=prices,
    )


@pytest.fixture
def ma_data() -> MovingAverageDataInput:
    return _make_ma_data()


class TestSMA:
    """Simple Moving Average tests."""

    def test_sma_known_answer(self):
        """Each SMA value is the plain mean of the trailing window."""
        import pandas as pd

        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        window = 3
        config = MovingAverageConfig(ma_type="SMA", period=5)
        calc = MovingAverageCalculator(config)
        sma = calc.calculate_sma(pd.Series(values), window)
        expected = [
            sum(values[end - window + 1 : end + 1]) / window
            for end in range(window - 1, len(values))
        ]
        assert sma.iloc[window - 1 :].tolist() == pytest.approx(expected)

    def test_sma_output_type(self, ma_data: MovingAverageDataInput):
        config = MovingAverageConfig(ma_type="SMA", period=20)
        calc = MovingAverageCalculator(config)
        result = calc.calculate_ma(ma_data)
        assert isinstance(result, MovingAverageOutput)
        assert result.ma_type == "SMA"

    def test_sma_period_matches_config(self, ma_data: MovingAverageDataInput):
        config = MovingAverageConfig(ma_type="SMA", period=30)
        calc = MovingAverageCalculator(config)
        result = calc.calculate_ma(ma_data)
        assert result.period == 30

    def test_sma_current_value_finite(self, ma_data: MovingAverageDataInput):
        config = MovingAverageConfig(ma_type="SMA", period=20)
        calc = MovingAverageCalculator(config)
        result = calc.calculate_ma(ma_data)
        assert result.current_value is not None
        assert np.isfinite(result.current_value)


class TestEMA:
    """Exponential Moving Average tests."""

    def test_ema_output_type(self, ma_data: MovingAverageDataInput):
        config = MovingAverageConfig(ma_type="EMA", period=20)
        calc = MovingAverageCalculator(config)
        result = calc.calculate_ma(ma_data)
        assert result.ma_type == "EMA"

    def test_ema_more_responsive_than_sma(self, ma_data: MovingAverageDataInput):
        """EMA should track recent prices more closely than SMA."""
        config_sma = MovingAverageConfig(ma_type="SMA", period=20)
        config_ema = MovingAverageConfig(ma_type="EMA", period=20)
        sma_calc = MovingAverageCalculator(config_sma)
        ema_calc = MovingAverageCalculator(config_ema)
        sma_val = sma_calc.calculate_ma(ma_data).current_value
        ema_val = ema_calc.calculate_ma(ma_data).current_value
        assert sma_val is not None
        assert ema_val is not None
        assert sma_val != pytest.approx(ema_val, abs=1e-6)


class TestWMA:
    """Weighted Moving Average tests."""

    def test_wma_known_answer(self):
        """WMA weights the newest price most, linearly: 1, 2, ..., period."""
        import pandas as pd

        values = [10.0, 11.0, 12.0, 13.0, 14.0]
        weights = range(1, len(values) + 1)
        config = MovingAverageConfig(ma_type="WMA", period=5)
        calc = MovingAverageCalculator(config)
        wma = calc.calculate_wma(pd.Series(values), len(values))
        expected = sum(w * v for w, v in zip(weights, values, strict=True)) / sum(
            weights
        )
        assert wma.iloc[-1] == pytest.approx(expected, abs=0.01)

    def test_wma_output_type(self, ma_data: MovingAverageDataInput):
        config = MovingAverageConfig(ma_type="WMA", period=20)
        calc = MovingAverageCalculator(config)
        result = calc.calculate_ma(ma_data)
        assert result.ma_type == "WMA"


class TestHMA:
    """Hull Moving Average tests."""

    def test_hma_output_type(self, ma_data: MovingAverageDataInput):
        config = MovingAverageConfig(ma_type="HMA", period=20)
        calc = MovingAverageCalculator(config)
        result = calc.calculate_ma(ma_data)
        assert result.ma_type == "HMA"

    def test_hma_finite_value(self, ma_data: MovingAverageDataInput):
        config = MovingAverageConfig(ma_type="HMA", period=20)
        calc = MovingAverageCalculator(config)
        result = calc.calculate_ma(ma_data)
        assert result.current_value is not None
        assert np.isfinite(result.current_value)


class TestPricePosition:
    """Price vs MA position detection."""

    def test_price_above_ma_in_uptrend(self):
        """In a strong uptrend, price should be above the SMA."""
        data = _make_ma_data(n=100, trend=1.0, volatility=0.1, seed=5)
        config = MovingAverageConfig(ma_type="SMA", period=50)
        calc = MovingAverageCalculator(config)
        result = calc.calculate_ma(data)
        assert result.price_vs_ma == "ABOVE"

    def test_price_below_ma_in_downtrend(self):
        """In a strong downtrend, price should be below the SMA."""
        data = _make_ma_data(
            n=100, start_price=200.0, trend=-1.0, volatility=0.1, seed=5
        )
        config = MovingAverageConfig(ma_type="SMA", period=50)
        calc = MovingAverageCalculator(config)
        result = calc.calculate_ma(data)
        assert result.price_vs_ma == "BELOW"


class TestCrossover:
    """MA crossover detection tests."""

    def test_crossover_requires_secondary_config(self, ma_data: MovingAverageDataInput):
        """calculate_with_crossover should raise without secondary config."""
        config = MovingAverageConfig(ma_type="SMA", period=20)
        calc = MovingAverageCalculator(config)
        with pytest.raises(ValueError, match="secondary_ma_type"):
            calc.calculate_with_crossover(ma_data)

    def test_crossover_returns_analysis(self, ma_data: MovingAverageDataInput):
        config = MovingAverageConfig(
            ma_type="SMA",
            period=10,
            secondary_ma_type="SMA",
            secondary_period=30,
        )
        calc = MovingAverageCalculator(config)
        result = calc.calculate_with_crossover(ma_data)
        assert isinstance(result, MovingAverageAnalysis)
        assert result.crossover_analysis is not None

    def test_crossover_signal_is_valid(self, ma_data: MovingAverageDataInput):
        config = MovingAverageConfig(
            ma_type="SMA",
            period=10,
            secondary_ma_type="SMA",
            secondary_period=30,
        )
        calc = MovingAverageCalculator(config)
        result = calc.calculate_with_crossover(ma_data)
        assert result.crossover_analysis is not None
        assert result.crossover_analysis.current_signal in (
            "BULLISH",
            "BEARISH",
            "NEUTRAL",
        )

    def test_bullish_crossover_in_uptrend(self):
        """Strong uptrend should show bullish (fast > slow) signal."""
        data = _make_ma_data(n=100, trend=1.0, volatility=0.1, seed=5)
        config = MovingAverageConfig(
            ma_type="SMA",
            period=10,
            secondary_ma_type="SMA",
            secondary_period=30,
        )
        calc = MovingAverageCalculator(config)
        result = calc.calculate_with_crossover(data)
        assert result.crossover_analysis is not None
        assert result.crossover_analysis.current_signal == "BULLISH"

    def test_secondary_period_shorter_than_primary_is_rejected(self):
        """The primary MA is the fast line, so its period must be the shorter one."""
        with pytest.raises(ValueError, match="must be shorter than"):
            MovingAverageConfig(
                ma_type="SMA",
                period=30,
                secondary_ma_type="SMA",
                secondary_period=10,
            )


class TestConvenienceFunction:
    """Tests for calculate_moving_average wrapper."""

    def test_single_ma(self):
        n = 80
        dates = [str(d) for d in _make_dates(n)]
        prices = [100.0 + i * 0.1 for i in range(n)]
        result = calculate_moving_average(
            ticker="CONV",
            dates=dates,
            prices=prices,
            ma_type="SMA",
            period=20,
        )
        assert isinstance(result, MovingAverageAnalysis)
        assert result.primary_ma.ma_type == "SMA"
        assert result.secondary_ma is None
        assert result.crossover_analysis is None

    def test_crossover_analysis(self):
        n = 80
        dates = [str(d) for d in _make_dates(n)]
        prices = [100.0 + i * 0.1 for i in range(n)]
        result = calculate_moving_average(
            ticker="CONV",
            dates=dates,
            prices=prices,
            ma_type="SMA",
            period=10,
            secondary_ma_type="SMA",
            secondary_period=30,
        )
        assert isinstance(result, MovingAverageAnalysis)
        assert result.crossover_analysis is not None


class TestEdgeCases:
    """Edge case handling."""

    def test_exactly_one_period_of_data_is_enough(self):
        """A series exactly as long as the SMA period still yields a value."""
        period = 50
        data = MovingAverageDataInput(
            ticker="SHORT",
            dates=_make_dates(period),
            prices=[100.0 + i for i in range(period)],
        )
        config = MovingAverageConfig(ma_type="SMA", period=period)
        calc = MovingAverageCalculator(config)
        result = calc.calculate_ma(data)
        assert result.current_value is not None
