"""Tests for Finance Guru volatility calculator.

Tests the VolatilityCalculator class with synthetic OHLC data.
No real API calls -- all data is generated with numpy.
"""

from datetime import date, timedelta

import numpy as np
import pytest

from src.models.volatility_inputs import (
    ATROutput,
    BollingerBandsOutput,
    HistoricalVolatilityOutput,
    KeltnerChannelsOutput,
    VolatilityConfig,
    VolatilityDataInput,
    VolatilityMetricsOutput,
)
from src.utils.volatility import VolatilityCalculator, calculate_volatility

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_dates(n: int) -> list[date]:
    start = date(2025, 1, 2)
    return [start + timedelta(days=i) for i in range(n)]


def _make_vol_data(
    n: int = 60,
    start_price: float = 100.0,
    daily_vol: float = 2.0,
    trend: float = 0.0,
    seed: int = 42,
) -> VolatilityDataInput:
    """Build VolatilityDataInput with synthetic OHLC data."""
    rng = np.random.default_rng(seed)
    closes = [start_price]
    for _ in range(n - 1):
        closes.append(closes[-1] + trend + rng.normal(0, daily_vol))
    closes = [max(c, 1.0) for c in closes]

    # Generate realistic high/low around close
    high = [c + abs(rng.normal(0, daily_vol * 0.5)) for c in closes]
    low = [c - abs(rng.normal(0, daily_vol * 0.5)) for c in closes]
    high = [max(h, c) for h, c in zip(high, closes, strict=True)]
    low = [min(lo, c) for lo, c in zip(low, closes, strict=True)]
    low = [max(lo, 0.01) for lo in low]  # keep positive

    return VolatilityDataInput(
        ticker="TEST",
        dates=_make_dates(n),
        high=high,
        low=low,
        close=closes,
    )


@pytest.fixture
def config() -> VolatilityConfig:
    return VolatilityConfig()


@pytest.fixture
def vol_data() -> VolatilityDataInput:
    return _make_vol_data()


@pytest.fixture
def calculator(config: VolatilityConfig) -> VolatilityCalculator:
    return VolatilityCalculator(config)


# ---------------------------------------------------------------------------
# Bollinger Bands
# ---------------------------------------------------------------------------


class TestBollingerBands:
    """Bollinger Bands indicator tests."""

    def test_bollinger_bands_structure(
        self, calculator: VolatilityCalculator, vol_data: VolatilityDataInput
    ):
        result = calculator.calculate_all_metrics(vol_data)
        bb = result.bollinger_bands
        assert isinstance(bb, BollingerBandsOutput)

    def test_upper_above_middle_above_lower(
        self, calculator: VolatilityCalculator, vol_data: VolatilityDataInput
    ):
        bb = calculator.calculate_all_metrics(vol_data).bollinger_bands
        assert bb.upper_band > bb.middle_band > bb.lower_band

    def test_bandwidth_positive(
        self, calculator: VolatilityCalculator, vol_data: VolatilityDataInput
    ):
        bb = calculator.calculate_all_metrics(vol_data).bollinger_bands
        assert bb.bandwidth > 0

    def test_percent_b_reasonable(
        self, calculator: VolatilityCalculator, vol_data: VolatilityDataInput
    ):
        bb = calculator.calculate_all_metrics(vol_data).bollinger_bands
        # %B can be outside [0,1] if price is outside bands, but should be finite
        assert np.isfinite(bb.percent_b)

    def test_wider_std_gives_wider_bands(self, vol_data: VolatilityDataInput):
        """Larger std_dev multiplier should widen the bands."""
        narrow = VolatilityCalculator(VolatilityConfig(bb_std_dev=1.0))
        wide = VolatilityCalculator(VolatilityConfig(bb_std_dev=3.0))
        bb_narrow = narrow.calculate_all_metrics(vol_data).bollinger_bands
        bb_wide = wide.calculate_all_metrics(vol_data).bollinger_bands
        assert bb_wide.bandwidth > bb_narrow.bandwidth


# ---------------------------------------------------------------------------
# ATR
# ---------------------------------------------------------------------------


class TestATR:
    """Average True Range tests."""

    def test_atr_positive(
        self, calculator: VolatilityCalculator, vol_data: VolatilityDataInput
    ):
        atr = calculator.calculate_all_metrics(vol_data).atr
        assert isinstance(atr, ATROutput)
        assert atr.atr > 0

    def test_atr_percent_positive(
        self, calculator: VolatilityCalculator, vol_data: VolatilityDataInput
    ):
        atr = calculator.calculate_all_metrics(vol_data).atr
        assert atr.atr_percent > 0

    def test_higher_volatility_higher_atr(self):
        """More volatile data should have higher ATR."""
        low_vol = _make_vol_data(daily_vol=0.5, seed=1)
        high_vol = _make_vol_data(daily_vol=5.0, seed=1)
        calc = VolatilityCalculator(VolatilityConfig())
        atr_low = calc.calculate_all_metrics(low_vol).atr.atr
        atr_high = calc.calculate_all_metrics(high_vol).atr.atr
        assert atr_high > atr_low


# ---------------------------------------------------------------------------
# Historical Volatility
# ---------------------------------------------------------------------------


class TestHistoricalVolatility:
    """Historical volatility tests."""

    def test_hvol_positive(
        self, calculator: VolatilityCalculator, vol_data: VolatilityDataInput
    ):
        hvol = calculator.calculate_all_metrics(vol_data).historical_volatility
        assert isinstance(hvol, HistoricalVolatilityOutput)
        assert hvol.daily_volatility > 0
        assert hvol.annual_volatility > 0

    def test_annual_gt_daily(
        self, calculator: VolatilityCalculator, vol_data: VolatilityDataInput
    ):
        """Annual volatility should be greater than daily (sqrt(252) factor)."""
        hvol = calculator.calculate_all_metrics(vol_data).historical_volatility
        assert hvol.annual_volatility > hvol.daily_volatility

    def test_higher_price_vol_gives_higher_hvol(self):
        low = _make_vol_data(daily_vol=0.3, seed=1)
        high = _make_vol_data(daily_vol=5.0, seed=1)
        calc = VolatilityCalculator(VolatilityConfig())
        hvol_low = calc.calculate_all_metrics(
            low
        ).historical_volatility.annual_volatility
        hvol_high = calc.calculate_all_metrics(
            high
        ).historical_volatility.annual_volatility
        assert hvol_high > hvol_low


# ---------------------------------------------------------------------------
# Keltner Channels
# ---------------------------------------------------------------------------


class TestKeltnerChannels:
    """Keltner Channels tests."""

    def test_keltner_structure(
        self, calculator: VolatilityCalculator, vol_data: VolatilityDataInput
    ):
        kc = calculator.calculate_all_metrics(vol_data).keltner_channels
        assert isinstance(kc, KeltnerChannelsOutput)

    def test_upper_gt_middle_gt_lower(
        self, calculator: VolatilityCalculator, vol_data: VolatilityDataInput
    ):
        kc = calculator.calculate_all_metrics(vol_data).keltner_channels
        assert kc.upper_channel > kc.middle_line > kc.lower_channel


# ---------------------------------------------------------------------------
# Volatility Regime
# ---------------------------------------------------------------------------


class TestVolatilityRegime:
    """Volatility regime classification tests."""

    def test_regime_is_valid_string(
        self, calculator: VolatilityCalculator, vol_data: VolatilityDataInput
    ):
        result = calculator.calculate_all_metrics(vol_data)
        assert result.volatility_regime in ("low", "normal", "high", "extreme")

    def test_low_vol_data_gives_low_or_normal_regime(self):
        """Very low volatility data should not be classified as extreme."""
        data = _make_vol_data(daily_vol=0.1, seed=5)
        calc = VolatilityCalculator(VolatilityConfig())
        result = calc.calculate_all_metrics(data)
        assert result.volatility_regime in ("low", "normal")

    def test_extreme_vol_data_gives_high_or_extreme_regime(self):
        """Very high volatility data should be classified as high or extreme."""
        data = _make_vol_data(daily_vol=15.0, seed=5)
        calc = VolatilityCalculator(VolatilityConfig())
        result = calc.calculate_all_metrics(data)
        assert result.volatility_regime in ("high", "extreme")


# ---------------------------------------------------------------------------
# Full metrics output
# ---------------------------------------------------------------------------


class TestFullMetricsOutput:
    """Tests for calculate_all_metrics."""

    def test_full_output_structure(
        self, calculator: VolatilityCalculator, vol_data: VolatilityDataInput
    ):
        result = calculator.calculate_all_metrics(vol_data)
        assert isinstance(result, VolatilityMetricsOutput)
        assert result.ticker == "TEST"
        assert result.current_price > 0

    def test_calculation_date_matches_last_date(
        self, calculator: VolatilityCalculator, vol_data: VolatilityDataInput
    ):
        result = calculator.calculate_all_metrics(vol_data)
        assert result.calculation_date == vol_data.dates[-1]


# ---------------------------------------------------------------------------
# Convenience function
# ---------------------------------------------------------------------------


class TestConvenienceFunction:
    """Tests for calculate_volatility wrapper."""

    def test_convenience_returns_output(self, vol_data: VolatilityDataInput):
        result = calculate_volatility(vol_data)
        assert isinstance(result, VolatilityMetricsOutput)

    def test_convenience_with_custom_config(self, vol_data: VolatilityDataInput):
        config = VolatilityConfig(bb_period=10, atr_period=7)
        result = calculate_volatility(vol_data, config)
        assert isinstance(result, VolatilityMetricsOutput)
