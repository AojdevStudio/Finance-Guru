"""Tests for DataValidator calculator.

Tests cover:
- Missing data detection
- Outlier detection (z-score, IQR, modified z-score)
- Date gap detection
- Stock split detection
- Quality scores (completeness, consistency, reliability)
- Validity determination
- Recommendation generation
- Convenience function

RUNNING TESTS:
    uv run pytest tests/python/test_data_validator.py -v
"""

from datetime import date, timedelta

import numpy as np
import pytest

from src.models.validation_inputs import (
    OutlierMethod,
    PriceSeriesInput,
    ValidationConfig,
)
from src.utils.data_validator import DataValidator, validate_price_data

_SERIES_START = date(2025, 1, 1)
_TWO_FOR_ONE = 2


def _daily_dates(count: int, start: date = _SERIES_START) -> list[date]:
    """Return ``count`` consecutive calendar dates from ``start``."""
    return [start + timedelta(days=i) for i in range(count)]


def _make_clean_series(n=100, start_price=100.0, seed=42):
    """Create clean price series with no anomalies."""
    rng = np.random.RandomState(seed)
    dates = _daily_dates(n)

    prices = [start_price]
    for _ in range(n - 1):
        daily_return = rng.normal(0.001, 0.01)
        prices.append(prices[-1] * (1 + daily_return))

    return PriceSeriesInput(ticker="TSLA", prices=prices, dates=dates)


@pytest.fixture
def clean_series():
    return _make_clean_series()


@pytest.fixture
def default_config():
    return ValidationConfig()


class TestBasicValidation:
    def test_clean_data_is_valid(self, clean_series, default_config):
        validator = DataValidator(default_config)
        result = validator.validate(clean_series)

        assert result.is_valid is True
        assert result.total_points == len(clean_series.prices)
        assert result.ticker == "TSLA"

    def test_quality_scores_high_for_clean_data(self, clean_series, default_config):
        validator = DataValidator(default_config)
        result = validator.validate(clean_series)

        assert result.completeness_score >= 0.95
        assert result.consistency_score >= 0.90
        assert result.reliability_score > 0


class TestMissingData:
    def test_detects_no_missing_data(self, clean_series, default_config):
        validator = DataValidator(default_config)
        result = validator.validate(clean_series)

        assert result.missing_count == 0

    def test_detects_nan_prices(self, default_config):
        dates = _daily_dates(20)
        prices = [100.0 + i * 0.5 for i in range(20)]
        missing_indices = (5, 10)
        for index in missing_indices:
            prices[index] = float("nan")

        series = PriceSeriesInput(ticker="TSLA", prices=prices, dates=dates)
        validator = DataValidator(default_config)
        result = validator.validate(series)

        assert result.missing_count >= len(missing_indices)


class TestOutlierDetection:
    def test_z_score_finds_outliers(self):
        config = ValidationConfig(
            outlier_method=OutlierMethod.Z_SCORE,
            outlier_threshold=2.0,
        )
        dates = _daily_dates(50)
        prices = [100.0 + i * 0.1 for i in range(50)]
        prices[len(prices) // 2] = 200.0

        series = PriceSeriesInput(ticker="TSLA", prices=prices, dates=dates)
        validator = DataValidator(config)
        result = validator.validate(series)

        assert result.outlier_count > 0

    def test_iqr_method(self):
        config = ValidationConfig(
            outlier_method=OutlierMethod.IQR,
            outlier_threshold=1.5,
        )
        dates = _daily_dates(50)
        prices = [100.0 + i * 0.1 for i in range(50)]
        prices[len(prices) // 2] = 200.0

        series = PriceSeriesInput(ticker="TSLA", prices=prices, dates=dates)
        validator = DataValidator(config)
        result = validator.validate(series)

        assert result.outlier_count > 0

    def test_modified_z_method(self):
        config = ValidationConfig(
            outlier_method=OutlierMethod.MODIFIED_Z,
            outlier_threshold=2.0,
        )
        dates = _daily_dates(50)
        prices = [100.0 + i * 0.1 for i in range(50)]
        prices[len(prices) // 2] = 200.0

        series = PriceSeriesInput(ticker="TSLA", prices=prices, dates=dates)
        validator = DataValidator(config)
        result = validator.validate(series)

        assert result.outlier_count > 0


class TestDateGaps:
    def test_detects_large_gaps(self):
        max_gap_days = 5
        config = ValidationConfig(max_gap_days=max_gap_days)
        before_gap = _daily_dates(10)
        after_gap = _daily_dates(
            10, start=before_gap[-1] + timedelta(days=max_gap_days + 1)
        )
        dates = before_gap + after_gap
        prices = [100.0 + i * 0.5 for i in range(len(dates))]

        series = PriceSeriesInput(ticker="TSLA", prices=prices, dates=dates)
        validator = DataValidator(config)
        result = validator.validate(series)

        assert result.gap_count > 0

    def test_no_gaps_in_daily_data(self, clean_series, default_config):
        validator = DataValidator(default_config)
        result = validator.validate(clean_series)

        assert result.gap_count == 0


class TestStockSplits:
    def test_detects_potential_split(self):
        config = ValidationConfig(check_splits=True, split_threshold=0.25)
        dates = _daily_dates(20)
        pre_split = [100.0 + i * 0.5 for i in range(10)]
        prices = pre_split + [p / _TWO_FOR_ONE for p in pre_split]

        series = PriceSeriesInput(ticker="TSLA", prices=prices, dates=dates)
        validator = DataValidator(config)
        result = validator.validate(series)

        assert result.potential_splits > 0

    def test_no_split_check_when_disabled(self):
        config = ValidationConfig(check_splits=False)
        dates = _daily_dates(20)
        pre_split = [100.0 + i * 0.5 for i in range(10)]
        prices = pre_split + [p / _TWO_FOR_ONE for p in pre_split]

        series = PriceSeriesInput(ticker="TSLA", prices=prices, dates=dates)
        validator = DataValidator(config)
        result = validator.validate(series)

        assert result.potential_splits == 0


class TestQualityScores:
    def test_completeness_perfect_for_clean_data(self, clean_series, default_config):
        validator = DataValidator(default_config)
        result = validator.validate(clean_series)

        assert result.completeness_score == 1.0

    def test_reliability_is_weighted_average(self, clean_series, default_config):
        validator = DataValidator(default_config)
        result = validator.validate(clean_series)

        expected = 0.6 * result.completeness_score + 0.4 * result.consistency_score
        assert result.reliability_score == pytest.approx(expected, abs=0.01)


class TestValidity:
    def test_invalid_when_too_many_missing(self, default_config):
        dates = _daily_dates(20)
        prices = [float("nan")] * 5 + [100.0 + i * 0.5 for i in range(15)]

        series = PriceSeriesInput(ticker="TSLA", prices=prices, dates=dates)
        validator = DataValidator(default_config)
        result = validator.validate(series)

        assert result.completeness_score < 0.95


class TestRecommendations:
    def test_excellent_data_gets_positive_recommendation(
        self, clean_series, default_config
    ):
        validator = DataValidator(default_config)
        result = validator.validate(clean_series)

        assert len(result.recommendations) > 0
        assert any(
            "proceed" in r.lower() or "good" in r.lower() or "excellent" in r.lower()
            for r in result.recommendations
        )


class TestConvenienceFunction:
    def test_validate_price_data_works(self):
        dates = [d.isoformat() for d in _daily_dates(20)]
        prices = [100.0 + i * 0.5 for i in range(20)]

        result = validate_price_data(
            ticker="TSLA",
            prices=prices,
            dates=dates,
        )

        assert result.ticker == "TSLA"
        assert result.total_points == len(prices)

    def test_validate_price_data_with_volumes(self):
        dates = [d.isoformat() for d in _daily_dates(20)]
        prices = [100.0 + i * 0.5 for i in range(20)]
        volumes = [1_000_000.0 + i * 10_000 for i in range(20)]

        result = validate_price_data(
            ticker="TSLA",
            prices=prices,
            dates=dates,
            volumes=volumes,
        )

        assert result.total_points == len(prices)
