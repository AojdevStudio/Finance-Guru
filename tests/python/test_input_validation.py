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


class TestPydanticModelValidation:
    """Test Pydantic models catch invalid input."""

    def test_price_series_requires_positive_prices(self):
        """Prices must be positive."""
        with pytest.raises(ValueError, match="positive"):
            PriceSeriesInput(
                ticker="TSLA",
                prices=[100.0] * 9 + [-50.0],  # Negative price (need 10 points)
                dates=[date(2025, 10, i) for i in range(10, 20)],
            )

    def test_price_series_requires_sorted_dates(self):
        """Dates must be chronological."""
        with pytest.raises(ValueError, match="chronological"):
            dates_list = [date(2025, 10, i) for i in range(10, 19)]
            dates_list.append(date(2025, 10, 12))  # Out of order (goes back in time)
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
                prices=[100.0] * 10,  # 10 prices
                dates=[date(2025, 10, i) for i in range(10, 21)],  # 11 dates (mismatch)
            )

    def test_price_series_valid_ticker_format(self):
        """Ticker must be uppercase letters, hyphens, dots."""
        # Valid tickers
        PriceSeriesInput(
            ticker="TSLA",
            prices=[100.0] * 10,
            dates=[date(2025, 10, i) for i in range(10, 20)],
        )

        PriceSeriesInput(
            ticker="BRK-B",  # Valid with hyphen
            prices=[100.0] * 10,
            dates=[date(2025, 10, i) for i in range(10, 20)],
        )

        # Invalid ticker (lowercase)
        with pytest.raises(ValueError):
            PriceSeriesInput(
                ticker="tsla",
                prices=[100.0] * 10,
                dates=[date(2025, 10, i) for i in range(10, 20)],
            )

    def test_validation_config_bounds(self):
        """Config parameters must be within valid ranges."""
        # Valid config
        config = ValidationConfig(
            outlier_threshold=3.0,
            missing_data_threshold=0.05,
            max_gap_days=10,
        )
        assert config.outlier_threshold == 3.0

        # Invalid outlier threshold (too low)
        with pytest.raises(ValueError):
            ValidationConfig(outlier_threshold=1.0)

        # Invalid missing threshold (too high)
        with pytest.raises(ValueError):
            ValidationConfig(missing_data_threshold=0.6)


class TestInputValidatorBasics:
    """Basic validation functionality tests."""

    def test_clean_data_passes_validation(self):
        """Clean data should pass all checks."""
        # Create clean price series
        prices = [100 + i * 0.5 for i in range(100)]  # Smooth uptrend
        dates_list = [date(2025, 1, 1) + timedelta(days=i) for i in range(100)]

        price_series = PriceSeriesInput(
            ticker="TEST",
            prices=prices,
            dates=dates_list,
        )

        # Validate
        config = ValidationConfig()
        validator = InputValidator(config)
        result = validator.validate_price_series(price_series)

        # Should pass
        assert result.is_valid
        assert result.completeness_score > 0.99
        assert result.consistency_score > 0.99
        assert result.reliability_score > 0.99
        assert len(result.anomalies) == 0

    def test_data_with_outliers_detected(self):
        """Outliers should be detected and reported."""
        # Create data with obvious outlier
        np.random.seed(42)
        prices = [100.0 + np.random.normal(0, 2) for _ in range(50)]
        prices[25] = 500.0  # Massive outlier
        dates_list = [date(2025, 1, 1) + timedelta(days=i) for i in range(50)]

        price_series = PriceSeriesInput(
            ticker="OUT",
            prices=prices,
            dates=dates_list,
        )

        # Validate with default z-score method
        config = ValidationConfig(outlier_method=OutlierMethod.Z_SCORE)
        validator = InputValidator(config)
        result = validator.validate_price_series(price_series)

        # Should detect outlier
        assert result.outlier_count > 0
        assert any(a.anomaly_type == "outlier" for a in result.anomalies)

    def test_large_date_gaps_detected(self):
        """Large gaps between dates should be detected."""
        # Create data with 30-day gap
        prices = [100.0] * 20
        dates_list = [date(2025, 1, i) for i in range(1, 11)]  # Jan 1-10
        dates_list.extend(
            [date(2025, 2, i) for i in range(10, 20)]
        )  # Feb 10-19 (30 day gap)

        price_series = PriceSeriesInput(
            ticker="GAP",
            prices=prices,
            dates=dates_list,
        )

        # Validate
        config = ValidationConfig(max_gap_days=10)
        validator = InputValidator(config)
        result = validator.validate_price_series(price_series)

        # Should detect gap
        assert result.gap_count > 0
        assert any(a.anomaly_type == "gap" for a in result.anomalies)


class TestOutlierDetectionMethods:
    """Test different outlier detection methods."""

    def test_zscore_outlier_detection(self):
        """Z-score method detects outliers based on standard deviations."""
        # Normal data: mean=100, std=5
        np.random.seed(42)
        prices = [100.0 + np.random.normal(0, 5) for _ in range(100)]

        # Add outlier (>3 std from mean)
        prices[50] = 100.0 + (3.5 * 5)  # 3.5 standard deviations

        dates_list = [date(2025, 1, 1) + timedelta(days=i) for i in range(100)]

        price_series = PriceSeriesInput(
            ticker="ZTEST",
            prices=prices,
            dates=dates_list,
        )

        config = ValidationConfig(
            outlier_method=OutlierMethod.Z_SCORE, outlier_threshold=3.0
        )
        validator = InputValidator(config)
        result = validator.validate_price_series(price_series)

        assert result.outlier_count >= 1

    def test_iqr_outlier_detection(self):
        """IQR method detects outliers based on interquartile range."""
        # Create skewed data (IQR is more robust for this)
        prices = [100.0 + i * 0.1 for i in range(100)]
        prices[50] = 200.0  # Clear outlier

        dates_list = [date(2025, 1, 1) + timedelta(days=i) for i in range(100)]

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
        # Data with some variation and an extreme outlier
        np.random.seed(42)
        prices = [100.0 + np.random.normal(0, 1) for _ in range(100)]
        prices[50] = 500.0  # Extreme outlier

        dates_list = [date(2025, 1, 1) + timedelta(days=i) for i in range(100)]

        price_series = PriceSeriesInput(
            ticker="MOD",
            prices=prices,
            dates=dates_list,
        )

        config = ValidationConfig(
            outlier_method=OutlierMethod.MODIFIED_Z,
            outlier_threshold=3.0,
            check_splits=False,  # Disable split detection for this test
        )
        validator = InputValidator(config)
        result = validator.validate_price_series(price_series)

        assert result.outlier_count >= 1


class TestStockSplitDetection:
    """Test stock split detection."""

    def test_detect_2_for_1_split(self):
        """Detect a 2:1 stock split (50% price drop)."""
        # Before split: $200, After split: $100
        prices = [200.0] * 30
        prices.extend([100.0] * 30)  # 50% drop = 2:1 split

        dates_list = [date(2025, 1, 1) + timedelta(days=i) for i in range(60)]

        price_series = PriceSeriesInput(
            ticker="SPLIT",
            prices=prices,
            dates=dates_list,
        )

        config = ValidationConfig(
            check_splits=True,
            split_threshold=0.25,  # 25% change threshold
        )
        validator = InputValidator(config)
        result = validator.validate_price_series(price_series)

        # Should detect split
        assert result.potential_splits > 0
        assert any(a.anomaly_type == "split" for a in result.anomalies)

    def test_no_split_on_normal_volatility(self):
        """Normal price movements should not trigger split detection."""
        # Realistic daily volatility (~2%)
        np.random.seed(42)
        prices = [100.0]
        for _ in range(99):
            change = np.random.normal(0, 2)  # 2% std
            prices.append(prices[-1] * (1 + change / 100))

        dates_list = [date(2025, 1, 1) + timedelta(days=i) for i in range(100)]

        price_series = PriceSeriesInput(
            ticker="NORM",
            prices=prices,
            dates=dates_list,
        )

        config = ValidationConfig(check_splits=True, split_threshold=0.25)
        validator = InputValidator(config)
        result = validator.validate_price_series(price_series)

        # Should not detect false splits
        assert result.potential_splits == 0


class TestQualityScores:
    """Test quality score calculations."""

    def test_completeness_score_calculation(self):
        """Completeness score reflects data coverage."""
        # Perfect data
        prices = [100.0] * 100
        dates_list = [date(2025, 1, 1) + timedelta(days=i) for i in range(100)]

        price_series = PriceSeriesInput(
            ticker="COMP",
            prices=prices,
            dates=dates_list,
        )

        config = ValidationConfig()
        validator = InputValidator(config)
        result = validator.validate_price_series(price_series)

        # Should have perfect completeness
        assert result.completeness_score == 1.0
        assert result.missing_count == 0

    def test_consistency_score_reflects_outliers(self):
        """Consistency score decreases with outliers."""
        # Data with 5% outliers
        np.random.seed(42)
        prices = [100.0 + np.random.normal(0, 2) for _ in range(100)]

        # Add 5 extreme outliers
        for i in [10, 30, 50, 70, 90]:
            prices[i] = 500.0

        dates_list = [date(2025, 1, 1) + timedelta(days=i) for i in range(100)]

        price_series = PriceSeriesInput(
            ticker="CONS",
            prices=prices,
            dates=dates_list,
        )

        config = ValidationConfig(outlier_threshold=3.0)
        validator = InputValidator(config)
        result = validator.validate_price_series(price_series)

        # Consistency should be reduced
        assert result.consistency_score < 1.0
        assert result.outlier_count > 0

    def test_reliability_score_is_weighted_average(self):
        """Reliability = 60% completeness + 40% consistency."""
        # Create data with known scores
        prices = [100.0] * 100
        dates_list = [date(2025, 1, 1) + timedelta(days=i) for i in range(100)]

        price_series = PriceSeriesInput(
            ticker="REL",
            prices=prices,
            dates=dates_list,
        )

        config = ValidationConfig()
        validator = InputValidator(config)
        result = validator.validate_price_series(price_series)

        # Calculate expected reliability
        expected = 0.6 * result.completeness_score + 0.4 * result.consistency_score

        assert abs(result.reliability_score - expected) < 0.01


class TestEdgeCases:
    """Edge case handling."""

    def test_minimum_data_points(self):
        """Handle minimum required data (10 points)."""
        prices = [100.0] * 10
        dates_list = [date(2025, 1, i) for i in range(1, 11)]

        price_series = PriceSeriesInput(
            ticker="MIN",
            prices=prices,
            dates=dates_list,
        )

        config = ValidationConfig()
        validator = InputValidator(config)
        result = validator.validate_price_series(price_series)

        # Should not crash
        assert result.total_points == 10

    def test_zero_volatility_data(self):
        """Handle constant prices (zero volatility)."""
        # All same price
        prices = [100.0] * 50
        dates_list = [date(2025, 1, 1) + timedelta(days=i) for i in range(50)]

        price_series = PriceSeriesInput(
            ticker="FLAT",
            prices=prices,
            dates=dates_list,
        )

        config = ValidationConfig()
        validator = InputValidator(config)
        result = validator.validate_price_series(price_series)

        # Should handle gracefully (no outliers for flat data)
        assert result.outlier_count == 0
        assert result.is_valid

    def test_very_high_volatility(self):
        """Handle extremely volatile data."""
        # Very high volatility (50% daily moves)
        np.random.seed(42)
        prices = [100.0]
        for _ in range(99):
            change = np.random.uniform(-50, 50)
            prices.append(max(1.0, prices[-1] * (1 + change / 100)))

        dates_list = [date(2025, 1, 1) + timedelta(days=i) for i in range(100)]

        price_series = PriceSeriesInput(
            ticker="VOL",
            prices=prices,
            dates=dates_list,
        )

        config = ValidationConfig(outlier_threshold=5.0)  # Higher threshold
        validator = InputValidator(config)
        result = validator.validate_price_series(price_series)

        # Should complete without error
        assert result.total_points == 100
