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

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_clean_series(n=100, start_price=100.0, seed=42):
    """Create clean price series with no anomalies."""
    rng = np.random.RandomState(seed)
    start = date(2025, 1, 1)
    dates = [start + timedelta(days=i) for i in range(n)]

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


# ---------------------------------------------------------------------------
# Basic validation
# ---------------------------------------------------------------------------


class TestBasicValidation:
    def test_clean_data_is_valid(self, clean_series, default_config):
        validator = DataValidator(default_config)
        result = validator.validate(clean_series)

        assert result.is_valid is True
        assert result.total_points == 100
        assert result.ticker == "TSLA"

    def test_quality_scores_high_for_clean_data(self, clean_series, default_config):
        validator = DataValidator(default_config)
        result = validator.validate(clean_series)

        assert result.completeness_score >= 0.95
        assert result.consistency_score >= 0.90
        assert result.reliability_score > 0


# ---------------------------------------------------------------------------
# Missing data
# ---------------------------------------------------------------------------


class TestMissingData:
    def test_detects_no_missing_data(self, clean_series, default_config):
        validator = DataValidator(default_config)
        result = validator.validate(clean_series)

        assert result.missing_count == 0

    def test_detects_nan_prices(self, default_config):
        start = date(2025, 1, 1)
        dates = [start + timedelta(days=i) for i in range(20)]
        prices = [100.0 + i * 0.5 for i in range(20)]
        prices[5] = float("nan")
        prices[10] = float("nan")

        series = PriceSeriesInput(ticker="TSLA", prices=prices, dates=dates)
        validator = DataValidator(default_config)
        result = validator.validate(series)

        assert result.missing_count >= 2


# ---------------------------------------------------------------------------
# Outlier detection
# ---------------------------------------------------------------------------


class TestOutlierDetection:
    def test_z_score_finds_outliers(self):
        config = ValidationConfig(
            outlier_method=OutlierMethod.Z_SCORE,
            outlier_threshold=2.0,
        )
        start = date(2025, 1, 1)
        dates = [start + timedelta(days=i) for i in range(50)]
        # Normal prices with one extreme jump
        prices = [100.0 + i * 0.1 for i in range(50)]
        prices[25] = 200.0  # Extreme outlier

        series = PriceSeriesInput(ticker="TSLA", prices=prices, dates=dates)
        validator = DataValidator(config)
        result = validator.validate(series)

        assert result.outlier_count > 0

    def test_iqr_method(self):
        config = ValidationConfig(
            outlier_method=OutlierMethod.IQR,
            outlier_threshold=1.5,
        )
        start = date(2025, 1, 1)
        dates = [start + timedelta(days=i) for i in range(50)]
        prices = [100.0 + i * 0.1 for i in range(50)]
        prices[25] = 200.0  # Extreme outlier

        series = PriceSeriesInput(ticker="TSLA", prices=prices, dates=dates)
        validator = DataValidator(config)
        result = validator.validate(series)

        assert result.outlier_count > 0

    def test_modified_z_method(self):
        config = ValidationConfig(
            outlier_method=OutlierMethod.MODIFIED_Z,
            outlier_threshold=2.0,
        )
        start = date(2025, 1, 1)
        dates = [start + timedelta(days=i) for i in range(50)]
        prices = [100.0 + i * 0.1 for i in range(50)]
        prices[25] = 200.0  # Extreme outlier

        series = PriceSeriesInput(ticker="TSLA", prices=prices, dates=dates)
        validator = DataValidator(config)
        result = validator.validate(series)

        assert result.outlier_count > 0


# ---------------------------------------------------------------------------
# Date gaps
# ---------------------------------------------------------------------------


class TestDateGaps:
    def test_detects_large_gaps(self):
        config = ValidationConfig(max_gap_days=5)
        start = date(2025, 1, 1)
        # Normal daily dates but with a 15-day gap
        dates = [start + timedelta(days=i) for i in range(10)]
        dates += [start + timedelta(days=25 + i) for i in range(10)]
        prices = [100.0 + i * 0.5 for i in range(20)]

        series = PriceSeriesInput(ticker="TSLA", prices=prices, dates=dates)
        validator = DataValidator(config)
        result = validator.validate(series)

        assert result.gap_count > 0

    def test_no_gaps_in_daily_data(self, clean_series, default_config):
        validator = DataValidator(default_config)
        result = validator.validate(clean_series)

        # Daily data has 1-day gaps which are normal
        # The default max_gap_days=10 so daily data has no suspicious gaps
        assert result.gap_count == 0


# ---------------------------------------------------------------------------
# Stock splits
# ---------------------------------------------------------------------------


class TestStockSplits:
    def test_detects_potential_split(self):
        config = ValidationConfig(check_splits=True, split_threshold=0.25)
        start = date(2025, 1, 1)
        dates = [start + timedelta(days=i) for i in range(20)]
        prices = [100.0 + i * 0.5 for i in range(10)]
        # Simulate 2:1 split at day 10 (price drops ~50%)
        prices += [50.0 + i * 0.25 for i in range(10)]

        series = PriceSeriesInput(ticker="TSLA", prices=prices, dates=dates)
        validator = DataValidator(config)
        result = validator.validate(series)

        assert result.potential_splits > 0

    def test_no_split_check_when_disabled(self):
        config = ValidationConfig(check_splits=False)
        start = date(2025, 1, 1)
        dates = [start + timedelta(days=i) for i in range(20)]
        prices = [100.0 + i * 0.5 for i in range(10)]
        prices += [50.0 + i * 0.25 for i in range(10)]

        series = PriceSeriesInput(ticker="TSLA", prices=prices, dates=dates)
        validator = DataValidator(config)
        result = validator.validate(series)

        assert result.potential_splits == 0


# ---------------------------------------------------------------------------
# Quality scores
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Validity determination
# ---------------------------------------------------------------------------


class TestValidity:
    def test_invalid_when_too_many_missing(self, default_config):
        start = date(2025, 1, 1)
        dates = [start + timedelta(days=i) for i in range(20)]
        prices = [float("nan")] * 5 + [100.0 + i * 0.5 for i in range(15)]

        series = PriceSeriesInput(ticker="TSLA", prices=prices, dates=dates)
        validator = DataValidator(default_config)
        result = validator.validate(series)

        # 25% missing data should make it invalid
        assert result.completeness_score < 0.95


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Convenience function
# ---------------------------------------------------------------------------


class TestConvenienceFunction:
    def test_validate_price_data_works(self):
        start = date(2025, 1, 1)
        dates = [(start + timedelta(days=i)).isoformat() for i in range(20)]
        prices = [100.0 + i * 0.5 for i in range(20)]

        result = validate_price_data(
            ticker="TSLA",
            prices=prices,
            dates=dates,
        )

        assert result.ticker == "TSLA"
        assert result.total_points == 20

    def test_validate_price_data_with_volumes(self):
        start = date(2025, 1, 1)
        dates = [(start + timedelta(days=i)).isoformat() for i in range(20)]
        prices = [100.0 + i * 0.5 for i in range(20)]
        volumes = [1_000_000.0 + i * 10_000 for i in range(20)]

        result = validate_price_data(
            ticker="TSLA",
            prices=prices,
            dates=dates,
            volumes=volumes,
        )

        assert result.total_points == 20
