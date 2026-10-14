"""
Tests for Finance Guru input validation module.

This test suite validates the data quality validation system:
- Layer 1: Pydantic models (validation_inputs.py)
- Layer 2: Calculator classes (input_validation.py)
- Layer 3: CLI interface (input_validation_cli.py)

Test Categories:
1. Model Validation Tests - Ensure Pydantic models catch bad input
2. Calculator Tests - Verify validation logic is correct
3. Outlier Detection Tests - Test different outlier methods
4. Edge Cases - Handle unusual but valid scenarios
"""

from datetime import date, timedelta

import numpy as np
import pytest

from src.models.validation_inputs import (
    OutlierMethod,
    PriceSeriesInput,
    ValidationConfig,
)
from src.utils.input_validation import InputValidator

_SERIES_START = date(2025, 1, 1)


def _daily_dates(count: int, start: date = _SERIES_START) -> list[date]:
    """Return ``count`` consecutive calendar dates from ``start``."""
    return [start + timedelta(days=i) for i in range(count)]


class TestPydanticModelValidation:
    """Test Pydantic models catch invalid input."""

    def test_price_series_requires_positive_prices(self):
        """Prices must be positive."""
        with pytest.raises(ValueError, match="positive"):
            PriceSeriesInput(
                ticker="TSLA",
                prices=[100.0] * 9 + [-50.0],
                dates=_daily_dates(10),
            )

    def test_price_series_requires_sorted_dates(self):
        """Dates must be chronological."""
        with pytest.raises(ValueError, match="chronological"):
            dates_list = _daily_dates(9)
            dates_list.append(dates_list[0])
            PriceSeriesInput(
                ticker="AAPL",
                prices=[100.0] * 10,
                dates=dates_list,
            )

    def test_price_series_requires_aligned_data(self):
        """Prices and dates must have same length."""
        with pytest.raises(ValueError, match="Length mismatch"):
            PriceSeriesInput(
                ticker="NVDA",
                prices=[100.0] * 10,
                dates=_daily_dates(11),
            )

    def test_price_series_valid_ticker_format(self):
        """Ticker must be uppercase letters, hyphens, dots."""
        PriceSeriesInput(
            ticker="TSLA",
            prices=[100.0] * 10,
            dates=_daily_dates(10),
        )

        PriceSeriesInput(
            ticker="BRK-B",
            prices=[100.0] * 10,
            dates=_daily_dates(10),
        )

        with pytest.raises(ValueError):
            PriceSeriesInput(
                ticker="tsla",
                prices=[100.0] * 10,
                dates=_daily_dates(10),
            )

    def test_validation_config_bounds(self):
        """Config parameters must be within valid ranges."""
        config = ValidationConfig(
            outlier_threshold=3.0,
            missing_data_threshold=0.05,
            max_gap_days=10,
        )
        assert config.outlier_threshold == 3.0

        with pytest.raises(ValueError):
            ValidationConfig(outlier_threshold=1.0)

        with pytest.raises(ValueError):
            ValidationConfig(missing_data_threshold=0.6)


class TestInputValidatorBasics:
    """Basic validation functionality tests."""

    def test_clean_data_passes_validation(self):
        """Clean data should pass all checks."""
        prices = [100 + i * 0.5 for i in range(100)]
        dates_list = _daily_dates(len(prices))

        price_series = PriceSeriesInput(
            ticker="TEST",
            prices=prices,
            dates=dates_list,
        )

        config = ValidationConfig()
        validator = InputValidator(config)
        result = validator.validate_price_series(price_series)

        assert result.is_valid
        assert result.completeness_score > 0.99
        assert result.consistency_score > 0.99
        assert result.reliability_score > 0.99
        assert len(result.anomalies) == 0

    def test_data_with_outliers_detected(self):
        """Outliers should be detected and reported."""
        np.random.seed(42)
        prices = [100.0 + np.random.normal(0, 2) for _ in range(50)]
        prices[len(prices) // 2] = 500.0
        dates_list = _daily_dates(len(prices))

        price_series = PriceSeriesInput(
            ticker="OUT",
            prices=prices,
            dates=dates_list,
        )

        config = ValidationConfig(outlier_method=OutlierMethod.Z_SCORE)
        validator = InputValidator(config)
        result = validator.validate_price_series(price_series)

        assert result.outlier_count > 0
        assert any(a.anomaly_type == "outlier" for a in result.anomalies)

    def test_large_date_gaps_detected(self):
        """Large gaps between dates should be detected."""
        max_gap_days = 10
        before_gap = _daily_dates(10)
        after_gap = _daily_dates(
            10, start=before_gap[-1] + timedelta(days=max_gap_days + 1)
        )
        dates_list = before_gap + after_gap
        prices = [100.0] * len(dates_list)

        price_series = PriceSeriesInput(
            ticker="GAP",
            prices=prices,
            dates=dates_list,
        )

        config = ValidationConfig(max_gap_days=max_gap_days)
        validator = InputValidator(config)
        result = validator.validate_price_series(price_series)

        assert result.gap_count > 0
        assert any(a.anomaly_type == "gap" for a in result.anomalies)


class TestOutlierDetectionMethods:
    """Test different outlier detection methods."""

    def test_zscore_outlier_detection(self):
        """Z-score method detects outliers based on standard deviations."""
        np.random.seed(42)
        noise_std = 5.0
        outlier_threshold = 3.0
        spike_sigmas = outlier_threshold + 0.5
        prices = [100.0 + np.random.normal(0, noise_std) for _ in range(100)]
        prices[len(prices) // 2] = 100.0 + spike_sigmas * noise_std

        dates_list = _daily_dates(len(prices))

        price_series = PriceSeriesInput(
            ticker="ZTEST",
            prices=prices,
            dates=dates_list,
        )

        config = ValidationConfig(
            outlier_method=OutlierMethod.Z_SCORE, outlier_threshold=outlier_threshold
        )
        validator = InputValidator(config)
        result = validator.validate_price_series(price_series)

        assert result.outlier_count >= 1

    def test_iqr_outlier_detection(self):
        """IQR method detects outliers based on interquartile range."""
        prices = [100.0 + i * 0.1 for i in range(100)]
        prices[len(prices) // 2] = 200.0

        dates_list = _daily_dates(len(prices))

        price_series = PriceSeriesInput(
            ticker="IQR",
            prices=prices,
            dates=dates_list,
        )

        config = ValidationConfig(
            outlier_method=OutlierMethod.IQR, outlier_threshold=1.5
        )
        validator = InputValidator(config)
        result = validator.validate_price_series(price_series)

        assert result.outlier_count >= 1

    def test_modified_zscore_outlier_detection(self):
        """Modified z-score uses median and is robust to extreme outliers."""
        np.random.seed(42)
        prices = [100.0 + np.random.normal(0, 1) for _ in range(100)]
        prices[len(prices) // 2] = 500.0

        dates_list = _daily_dates(len(prices))

        price_series = PriceSeriesInput(
            ticker="MOD",
            prices=prices,
            dates=dates_list,
        )

        config = ValidationConfig(
            outlier_method=OutlierMethod.MODIFIED_Z,
            outlier_threshold=3.0,
            check_splits=False,
        )
        validator = InputValidator(config)
        result = validator.validate_price_series(price_series)

        assert result.outlier_count >= 1


class TestStockSplitDetection:
    """Test stock split detection."""

    def test_detect_2_for_1_split(self):
        """Detect a 2:1 stock split (50% price drop)."""
        prices = [200.0] * 30
        prices.extend([100.0] * 30)

        dates_list = _daily_dates(len(prices))

        price_series = PriceSeriesInput(
            ticker="SPLIT",
            prices=prices,
            dates=dates_list,
        )

        config = ValidationConfig(
            check_splits=True,
            split_threshold=0.25,
        )
        validator = InputValidator(config)
        result = validator.validate_price_series(price_series)

        assert result.potential_splits > 0
        assert any(a.anomaly_type == "split" for a in result.anomalies)

    def test_no_split_on_normal_volatility(self):
        """Normal price movements should not trigger split detection."""
        np.random.seed(42)
        prices = [100.0]
        for _ in range(99):
            change = np.random.normal(0, 2)
            prices.append(prices[-1] * (1 + change / 100))

        dates_list = _daily_dates(len(prices))

        price_series = PriceSeriesInput(
            ticker="NORM",
            prices=prices,
            dates=dates_list,
        )

        config = ValidationConfig(check_splits=True, split_threshold=0.25)
        validator = InputValidator(config)
        result = validator.validate_price_series(price_series)

        assert result.potential_splits == 0


class TestQualityScores:
    """Test quality score calculations."""

    def test_completeness_score_calculation(self):
        """Completeness score reflects data coverage."""
        prices = [100.0] * 100
        dates_list = _daily_dates(len(prices))

        price_series = PriceSeriesInput(
            ticker="COMP",
            prices=prices,
            dates=dates_list,
        )

        config = ValidationConfig()
        validator = InputValidator(config)
        result = validator.validate_price_series(price_series)

        assert result.completeness_score == 1.0
        assert result.missing_count == 0

    def test_consistency_score_reflects_outliers(self):
        """Consistency score decreases with outliers."""
        np.random.seed(42)
        prices = [100.0 + np.random.normal(0, 2) for _ in range(100)]

        for i in [10, 30, 50, 70, 90]:
            prices[i] = 500.0

        dates_list = _daily_dates(len(prices))

        price_series = PriceSeriesInput(
            ticker="CONS",
            prices=prices,
            dates=dates_list,
        )

        config = ValidationConfig(outlier_threshold=3.0)
        validator = InputValidator(config)
        result = validator.validate_price_series(price_series)

        assert result.consistency_score < 1.0
        assert result.outlier_count > 0

    def test_reliability_score_is_weighted_average(self):
        """Reliability = 60% completeness + 40% consistency."""
        prices = [100.0] * 100
        dates_list = _daily_dates(len(prices))

        price_series = PriceSeriesInput(
            ticker="REL",
            prices=prices,
            dates=dates_list,
        )

        config = ValidationConfig()
        validator = InputValidator(config)
        result = validator.validate_price_series(price_series)

        expected = 0.6 * result.completeness_score + 0.4 * result.consistency_score

        assert abs(result.reliability_score - expected) < 0.01


class TestEdgeCases:
    """Edge case handling."""

    def test_minimum_data_points(self):
        """Handle minimum required data (10 points)."""
        prices = [100.0] * 10
        dates_list = _daily_dates(len(prices))

        price_series = PriceSeriesInput(
            ticker="MIN",
            prices=prices,
            dates=dates_list,
        )

        config = ValidationConfig()
        validator = InputValidator(config)
        result = validator.validate_price_series(price_series)

        assert result.total_points == 10

    def test_zero_volatility_data(self):
        """Handle constant prices (zero volatility)."""
        prices = [100.0] * 50
        dates_list = _daily_dates(len(prices))

        price_series = PriceSeriesInput(
            ticker="FLAT",
            prices=prices,
            dates=dates_list,
        )

        config = ValidationConfig()
        validator = InputValidator(config)
        result = validator.validate_price_series(price_series)

        assert result.outlier_count == 0
        assert result.is_valid

    def test_very_high_volatility(self):
        """Handle extremely volatile data."""
        np.random.seed(42)
        prices = [100.0]
        for _ in range(99):
            change = np.random.uniform(-50, 50)
            prices.append(max(1.0, prices[-1] * (1 + change / 100)))

        dates_list = _daily_dates(len(prices))

        price_series = PriceSeriesInput(
            ticker="VOL",
            prices=prices,
            dates=dates_list,
        )

        config = ValidationConfig(outlier_threshold=5.0)
        validator = InputValidator(config)
        result = validator.validate_price_series(price_series)

        assert result.total_points == 100
