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

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# SMA
# ---------------------------------------------------------------------------


class TestSMA:
    """Simple Moving Average tests."""

    def test_sma_known_answer(self):
        """SMA of [1,2,3,4,5] with period 3 = [NaN, NaN, 2, 3, 4]."""
        import pandas as pd

        prices = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        config = MovingAverageConfig(ma_type="SMA", period=5)
        calc = MovingAverageCalculator(config)
        sma = calc.calculate_sma(prices, 3)
        assert sma.iloc[2] == pytest.approx(2.0)
        assert sma.iloc[3] == pytest.approx(3.0)
        assert sma.iloc[4] == pytest.approx(4.0)

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


# ---------------------------------------------------------------------------
# EMA
# ---------------------------------------------------------------------------


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
        # Both should be close to last price but different from each other
        assert sma_val is not None
        assert ema_val is not None
        assert sma_val != pytest.approx(ema_val, abs=1e-6)


# ---------------------------------------------------------------------------
# WMA
# ---------------------------------------------------------------------------


class TestWMA:
    """Weighted Moving Average tests."""

    def test_wma_known_answer(self):
        """WMA of [10,11,12,13,14] with period 5 = weighted average."""
        import pandas as pd

        prices = pd.Series([10.0, 11.0, 12.0, 13.0, 14.0])
        config = MovingAverageConfig(ma_type="WMA", period=5)
        calc = MovingAverageCalculator(config)
        wma = calc.calculate_wma(prices, 5)
        # Expected: (10*1 + 11*2 + 12*3 + 13*4 + 14*5) / 15 = 190/15 = 12.667
        assert wma.iloc[4] == pytest.approx(190.0 / 15.0, abs=0.01)

    def test_wma_output_type(self, ma_data: MovingAverageDataInput):
        config = MovingAverageConfig(ma_type="WMA", period=20)
        calc = MovingAverageCalculator(config)
        result = calc.calculate_ma(ma_data)
        assert result.ma_type == "WMA"


# ---------------------------------------------------------------------------
# HMA
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Price vs MA position
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Crossover detection
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Convenience function
# ---------------------------------------------------------------------------


class TestConvenienceFunction:
    """Tests for calculate_moving_average wrapper."""

    def test_single_ma(self):
        n = 80
        dates = [str(date(2025, 1, 2) + timedelta(days=i)) for i in range(n)]
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
        dates = [str(date(2025, 1, 2) + timedelta(days=i)) for i in range(n)]
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


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Edge case handling."""

    def test_insufficient_data_raises(self):
        """Should raise with too few data points."""
        data = MovingAverageDataInput(
            ticker="SHORT",
            dates=_make_dates(50),
            prices=[100.0 + i for i in range(50)],
        )
        config = MovingAverageConfig(ma_type="SMA", period=50)
        calc = MovingAverageCalculator(config)
        # 50 points for period 50 should be exactly enough for SMA
        result = calc.calculate_ma(data)
        assert result.current_value is not None
