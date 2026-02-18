"""Tests for Finance Guru momentum indicators calculator.

Tests the MomentumIndicators class with synthetic OHLC data.
No real API calls -- all data is generated with numpy/pandas.
"""

from datetime import date, timedelta

import numpy as np
import pytest

from src.models.momentum_inputs import (
    AllMomentumOutput,
    MACDOutput,
    MomentumConfig,
    MomentumDataInput,
    ROCOutput,
    RSIOutput,
    StochasticOutput,
    WilliamsROutput,
)
from src.utils.momentum import MomentumIndicators, calculate_momentum

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_dates(n: int) -> list[date]:
    start = date(2025, 1, 2)
    return [start + timedelta(days=i) for i in range(n)]


def _make_momentum_data(
    n: int = 60,
    start_price: float = 100.0,
    trend: float = 0.0,
    volatility: float = 2.0,
    seed: int = 42,
    include_hlv: bool = True,
) -> MomentumDataInput:
    """Build MomentumDataInput with synthetic data.

    Args:
        trend: daily price drift (positive = uptrend)
        volatility: daily price std deviation
        include_hlv: whether to include high/low/volume
    """
    rng = np.random.default_rng(seed)
    closes = [start_price]
    for _ in range(n - 1):
        closes.append(closes[-1] + trend + rng.normal(0, volatility))
    closes = [max(c, 1.0) for c in closes]  # keep positive

    high = (
        [c + abs(rng.normal(0, volatility * 0.5)) for c in closes]
        if include_hlv
        else None
    )
    low = (
        [c - abs(rng.normal(0, volatility * 0.5)) for c in closes]
        if include_hlv
        else None
    )
    # Ensure high >= close >= low
    if high and low:
        high = [max(h, c) for h, c in zip(high, closes, strict=True)]
        low = [min(lo, c) for lo, c in zip(low, closes, strict=True)]

    return MomentumDataInput(
        ticker="TEST",
        dates=_make_dates(n),
        close=closes,
        high=high,
        low=low,
    )


@pytest.fixture
def config() -> MomentumConfig:
    return MomentumConfig()


@pytest.fixture
def momentum_data() -> MomentumDataInput:
    return _make_momentum_data()


@pytest.fixture
def calculator(config: MomentumConfig) -> MomentumIndicators:
    return MomentumIndicators(config)


# ---------------------------------------------------------------------------
# RSI
# ---------------------------------------------------------------------------


class TestRSI:
    """RSI indicator tests."""

    def test_rsi_returns_output(
        self, calculator: MomentumIndicators, momentum_data: MomentumDataInput
    ):
        result = calculator.calculate_rsi(momentum_data)
        assert isinstance(result, RSIOutput)
        assert result.ticker == "TEST"

    def test_rsi_in_valid_range(
        self, calculator: MomentumIndicators, momentum_data: MomentumDataInput
    ):
        result = calculator.calculate_rsi(momentum_data)
        assert 0 <= result.current_rsi <= 100

    def test_rsi_overbought_on_strong_uptrend(self):
        """Strongly rising prices should push RSI toward overbought."""
        data = _make_momentum_data(n=40, trend=3.0, volatility=0.5, seed=10)
        calc = MomentumIndicators(MomentumConfig(rsi_period=14))
        result = calc.calculate_rsi(data)
        assert result.current_rsi > 60  # strong uptrend

    def test_rsi_oversold_on_strong_downtrend(self):
        """Strongly falling prices should push RSI toward oversold."""
        data = _make_momentum_data(
            n=40, start_price=200.0, trend=-3.0, volatility=0.5, seed=10
        )
        calc = MomentumIndicators(MomentumConfig(rsi_period=14))
        result = calc.calculate_rsi(data)
        assert result.current_rsi < 40

    def test_rsi_insufficient_data_raises(self):
        """RSI should raise ValueError with insufficient data."""
        data = MomentumDataInput(
            ticker="SHORT",
            dates=_make_dates(14),
            close=[100.0 + i for i in range(14)],
        )
        calc = MomentumIndicators(MomentumConfig(rsi_period=14))
        with pytest.raises(ValueError, match="Need at least"):
            calc.calculate_rsi(data)

    def test_rsi_signal_matches_value(self, calculator: MomentumIndicators):
        """Signal should correspond to RSI value thresholds."""
        # Build data that gives a known RSI range
        data = _make_momentum_data(n=60, trend=0.0, volatility=2.0, seed=42)
        result = calculator.calculate_rsi(data)
        if result.current_rsi > 70:
            assert result.rsi_signal == "overbought"
        elif result.current_rsi < 30:
            assert result.rsi_signal == "oversold"
        else:
            assert result.rsi_signal == "neutral"


# ---------------------------------------------------------------------------
# MACD
# ---------------------------------------------------------------------------


class TestMACD:
    """MACD indicator tests."""

    def test_macd_returns_output(
        self, calculator: MomentumIndicators, momentum_data: MomentumDataInput
    ):
        result = calculator.calculate_macd(momentum_data)
        assert isinstance(result, MACDOutput)

    def test_histogram_equals_macd_minus_signal(
        self, calculator: MomentumIndicators, momentum_data: MomentumDataInput
    ):
        result = calculator.calculate_macd(momentum_data)
        assert result.histogram == pytest.approx(
            result.macd_line - result.signal_line, abs=1e-8
        )

    def test_macd_signal_matches_relationship(
        self, calculator: MomentumIndicators, momentum_data: MomentumDataInput
    ):
        result = calculator.calculate_macd(momentum_data)
        if result.macd_line > result.signal_line:
            assert result.signal == "bullish"
        else:
            assert result.signal == "bearish"

    def test_macd_insufficient_data_raises(self):
        data = MomentumDataInput(
            ticker="SHORT",
            dates=_make_dates(20),
            close=[100.0 + i * 0.1 for i in range(20)],
        )
        calc = MomentumIndicators(MomentumConfig())
        with pytest.raises(ValueError, match="Need at least"):
            calc.calculate_macd(data)

    def test_macd_bullish_on_uptrend(self):
        """Sustained uptrend should give bullish MACD."""
        data = _make_momentum_data(n=60, trend=1.0, volatility=0.3, seed=5)
        calc = MomentumIndicators(MomentumConfig())
        result = calc.calculate_macd(data)
        assert result.macd_line > 0  # Fast EMA > slow EMA in uptrend


# ---------------------------------------------------------------------------
# Stochastic
# ---------------------------------------------------------------------------


class TestStochastic:
    """Stochastic Oscillator tests."""

    def test_stochastic_returns_output(
        self, calculator: MomentumIndicators, momentum_data: MomentumDataInput
    ):
        result = calculator.calculate_stochastic(momentum_data)
        assert isinstance(result, StochasticOutput)

    def test_k_and_d_in_range(
        self, calculator: MomentumIndicators, momentum_data: MomentumDataInput
    ):
        result = calculator.calculate_stochastic(momentum_data)
        assert 0 <= result.k_value <= 100
        assert 0 <= result.d_value <= 100

    def test_stochastic_requires_high_low(self):
        """Should raise when high/low are missing."""
        data = MomentumDataInput(
            ticker="NOHL",
            dates=_make_dates(30),
            close=[100.0 + i for i in range(30)],
        )
        calc = MomentumIndicators(MomentumConfig())
        with pytest.raises(ValueError, match="high and low"):
            calc.calculate_stochastic(data)

    def test_stochastic_signal_thresholds(
        self, calculator: MomentumIndicators, momentum_data: MomentumDataInput
    ):
        result = calculator.calculate_stochastic(momentum_data)
        if result.k_value > 80:
            assert result.signal == "overbought"
        elif result.k_value < 20:
            assert result.signal == "oversold"
        else:
            assert result.signal == "neutral"


# ---------------------------------------------------------------------------
# Williams %R
# ---------------------------------------------------------------------------


class TestWilliamsR:
    """Williams %R tests."""

    def test_williams_r_returns_output(
        self, calculator: MomentumIndicators, momentum_data: MomentumDataInput
    ):
        result = calculator.calculate_williams_r(momentum_data)
        assert isinstance(result, WilliamsROutput)

    def test_williams_r_in_range(
        self, calculator: MomentumIndicators, momentum_data: MomentumDataInput
    ):
        result = calculator.calculate_williams_r(momentum_data)
        assert -100 <= result.williams_r <= 0

    def test_williams_r_requires_high_low(self):
        data = MomentumDataInput(
            ticker="NOHL",
            dates=_make_dates(30),
            close=[100.0 + i for i in range(30)],
        )
        calc = MomentumIndicators(MomentumConfig())
        with pytest.raises(ValueError, match="high and low"):
            calc.calculate_williams_r(data)

    def test_williams_r_signal_thresholds(
        self, calculator: MomentumIndicators, momentum_data: MomentumDataInput
    ):
        result = calculator.calculate_williams_r(momentum_data)
        if result.williams_r > -20:
            assert result.signal == "overbought"
        elif result.williams_r < -80:
            assert result.signal == "oversold"
        else:
            assert result.signal == "neutral"


# ---------------------------------------------------------------------------
# ROC
# ---------------------------------------------------------------------------


class TestROC:
    """Rate of Change tests."""

    def test_roc_returns_output(
        self, calculator: MomentumIndicators, momentum_data: MomentumDataInput
    ):
        result = calculator.calculate_roc(momentum_data)
        assert isinstance(result, ROCOutput)

    def test_roc_positive_for_rising_prices(self):
        """ROC should be positive when recent price > past price."""
        data = _make_momentum_data(n=30, trend=2.0, volatility=0.1, seed=7)
        calc = MomentumIndicators(MomentumConfig(roc_period=12))
        result = calc.calculate_roc(data)
        assert result.roc > 0
        assert result.signal == "bullish"

    def test_roc_negative_for_falling_prices(self):
        data = _make_momentum_data(
            n=30, start_price=200.0, trend=-2.0, volatility=0.1, seed=7
        )
        calc = MomentumIndicators(MomentumConfig(roc_period=12))
        result = calc.calculate_roc(data)
        assert result.roc < 0
        assert result.signal == "bearish"

    def test_roc_insufficient_data_raises(self):
        data = MomentumDataInput(
            ticker="SHORT",
            dates=_make_dates(14),
            close=[100.0 + i for i in range(14)],
        )
        calc = MomentumIndicators(MomentumConfig(roc_period=14))
        with pytest.raises(ValueError, match="Need at least"):
            calc.calculate_roc(data)


# ---------------------------------------------------------------------------
# calculate_all
# ---------------------------------------------------------------------------


class TestCalculateAll:
    """Tests for the combined calculate_all method."""

    def test_calculate_all_returns_combined_output(
        self, calculator: MomentumIndicators, momentum_data: MomentumDataInput
    ):
        result = calculator.calculate_all(momentum_data)
        assert isinstance(result, AllMomentumOutput)
        assert isinstance(result.rsi, RSIOutput)
        assert isinstance(result.macd, MACDOutput)
        assert isinstance(result.stochastic, StochasticOutput)
        assert isinstance(result.williams_r, WilliamsROutput)
        assert isinstance(result.roc, ROCOutput)


# ---------------------------------------------------------------------------
# Convenience function
# ---------------------------------------------------------------------------


class TestConvenienceFunction:
    """Tests for calculate_momentum wrapper."""

    def test_convenience_returns_all_output(self):
        n = 60
        dates = [str(date(2025, 1, 2) + timedelta(days=i)) for i in range(n)]
        rng = np.random.default_rng(42)
        close = [100.0 + i * 0.1 + rng.normal(0, 1) for i in range(n)]
        close = [max(c, 1.0) for c in close]
        high = [c + abs(rng.normal(0, 0.5)) for c in close]
        low = [c - abs(rng.normal(0, 0.5)) for c in close]
        high = [max(h, c) for h, c in zip(high, close, strict=True)]
        low = [min(lo, c) for lo, c in zip(low, close, strict=True)]

        result = calculate_momentum(
            ticker="CONV",
            dates=dates,
            close=close,
            high=high,
            low=low,
        )
        assert isinstance(result, AllMomentumOutput)
        assert result.ticker == "CONV"
