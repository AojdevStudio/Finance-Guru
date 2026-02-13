"""Input Validation Calculator for Finance Guru™.

This module implements data quality validation for financial time series data.
Uses validated Pydantic models from validation_inputs.py to ensure type safety.

ARCHITECTURE NOTE:
This is Layer 2 of our 3-layer architecture:
    Layer 1: Pydantic Models - Data validation (validation_inputs.py)
    Layer 2: Calculator Classes (THIS FILE) - Business logic
    Layer 3: CLI Interface - Agent integration

EDUCATIONAL CONTEXT:
Data validation is critical in financial analysis:
- Bad data → Bad decisions → Lost money
- Outliers can be data errors OR real market events
- Missing data can skew calculations
- This module helps distinguish between real patterns and data problems

VALIDATION CHECKS IMPLEMENTED:
1. Missing Data Detection - Identifies gaps in time series
2. Outlier Detection - Z-score, IQR, and Modified Z-score methods
3. Date Gap Analysis - Finds suspicious gaps in trading days
4. Stock Split Detection - Identifies potential corporate actions
5. Quality Scoring - Provides overall data reliability metrics

Author: Finance Guru™ Development Team
Created: 2026-01-16
"""

from datetime import date

import numpy as np
import pandas as pd

from src.models.validation_inputs import (
    DataAnomaly,
    OutlierMethod,
    PriceSeriesInput,
    ValidationConfig,
    ValidationOutput,
)


class InputValidator:
    """Data quality validation calculator.

    WHAT: Validates financial time series data for quality issues
    WHY: Ensures data is reliable before analysis and trading decisions
    HOW: Statistical methods + domain-specific rules (market hours, splits, etc.)

    USAGE EXAMPLE:
        # Create configuration
        config = ValidationConfig(
            outlier_method=OutlierMethod.Z_SCORE,
            outlier_threshold=3.0,
            missing_data_threshold=0.05,
            check_splits=True
        )

        # Create validator
        validator = InputValidator(config)

        # Validate price series
        result = validator.validate_price_series(price_data)

        # Check results
        if result.is_valid:
            print(f"Data quality: {result.reliability_score:.1%}")
        else:
            print(f"Found {len(result.anomalies)} issues")
    """

    def __init__(self, config: ValidationConfig):
        """Initialize validator with configuration.

        Args:
            config: Validated configuration (Pydantic model ensures correctness)
        """
        self.config = config

    def validate_price_series(self, price_data: PriceSeriesInput) -> ValidationOutput:
        """Perform comprehensive validation on price series data.

        Args:
            price_data: Historical price data (validated by Pydantic)

        Returns:
            ValidationOutput: Complete validation report with anomalies and scores

        EDUCATIONAL NOTE:
        This is the main entry point. It orchestrates all validation checks
        and combines them into a single comprehensive report.
        """
        # Convert to pandas for easier calculations
        df = pd.DataFrame(
            {
                "date": price_data.dates,
                "price": price_data.prices,
            }
        )

        if price_data.volumes is not None:
            df["volume"] = price_data.volumes

        # Initialize anomaly list
        anomalies: list[DataAnomaly] = []
        warnings: list[str] = []
        recommendations: list[str] = []

        # 1. Check for missing data
        missing_count = self._check_missing_data(df, anomalies, warnings)

        # 2. Detect outliers
        outlier_count = self._detect_outliers(df, anomalies, warnings)

        # 3. Check for date gaps
        gap_count = self._check_date_gaps(df, anomalies, warnings)

        # 4. Check for stock splits (if enabled)
        split_count = 0
        if self.config.check_splits:
            split_count = self._detect_splits(df, anomalies, warnings)

        # 5. Calculate quality scores
        total_points = len(df)
        completeness_score = max(0.0, 1.0 - (missing_count / total_points))
        consistency_score = max(0.0, 1.0 - (outlier_count / total_points))

        # 6. Determine overall validity
        is_valid = self._determine_validity(
            completeness_score, consistency_score, anomalies
        )

        # 7. Generate recommendations
        self._generate_recommendations(
            is_valid, completeness_score, consistency_score, anomalies, recommendations
        )

        # Build and return output (Pydantic calculates reliability_score)
        return ValidationOutput(
            ticker=price_data.ticker,
            validation_date=date.today(),
            is_valid=is_valid,
            total_points=total_points,
            missing_count=missing_count,
            outlier_count=outlier_count,
            gap_count=gap_count,
            potential_splits=split_count,
            completeness_score=completeness_score,
            consistency_score=consistency_score,
            reliability_score=0.0,  # Calculated by Pydantic validator
            anomalies=anomalies,
            warnings=warnings,
            recommendations=recommendations,
        )

    def _check_missing_data(
        self, df: pd.DataFrame, anomalies: list[DataAnomaly], warnings: list[str]
    ) -> int:
        """Check for missing data points.

        EDUCATIONAL NOTE:
        Missing data can occur due to:
        - Holidays/weekends (normal for stocks)
        - Data provider outages (problematic)
        - Delisted stocks (critical issue)
        """
        # For now, we consider missing data as NULL values
        # More sophisticated version would check for expected trading days
        missing_count = df["price"].isna().sum()

        if missing_count > 0:
            missing_ratio = missing_count / len(df)

            if missing_ratio > self.config.missing_data_threshold:
                severity = "critical" if missing_ratio > 0.10 else "high"
                anomalies.append(
                    DataAnomaly(
                        anomaly_type="missing",
                        severity=severity,
                        description=f"Found {missing_count} missing data points ({missing_ratio:.1%})",
                        location=None,
                        value=missing_count,
                        recommendation=(
                            "Fill missing data using forward-fill or interpolation. "
                            "For large gaps, consider fetching data from alternative source."
                        ),
                    )
                )
                warnings.append(f"Missing data: {missing_ratio:.1%} of series")

        return missing_count

    def _detect_outliers(
        self, df: pd.DataFrame, anomalies: list[DataAnomaly], warnings: list[str]
    ) -> int:
        """Detect price outliers using configured method.

        EDUCATIONAL NOTE:
        Outliers can be:
        - Data errors (wrong prices in feed)
        - Real market events (flash crashes, circuit breakers)
        - Corporate actions (splits not adjusted)

        Different methods:
        - Z-score: Good for normal distributions
        - IQR: Robust to skewed data
        - Modified Z: Best for extreme outliers
        """
        prices = df["price"].values

        if self.config.outlier_method == OutlierMethod.Z_SCORE:
            outliers, outlier_indices = self._zscore_outliers(prices)
        elif self.config.outlier_method == OutlierMethod.IQR:
            outliers, outlier_indices = self._iqr_outliers(prices)
        else:  # MODIFIED_Z
            outliers, outlier_indices = self._modified_zscore_outliers(prices)

        # Record anomalies
        for idx in outlier_indices:
            severity = (
                "medium"
                if abs(outliers[idx]) < self.config.outlier_threshold * 1.5
                else "high"
            )
            anomalies.append(
                DataAnomaly(
                    anomaly_type="outlier",
                    severity=severity,
                    description=f"Price outlier detected (z-score: {outliers[idx]:.2f})",
                    location=str(df.iloc[idx]["date"]),
                    value=float(prices[idx]),
                    recommendation=(
                        "Verify price from alternative data source. "
                        "If legitimate, consider if it's a corporate action."
                    ),
                )
            )

        outlier_count = len(outlier_indices)
        if outlier_count > 0:
            outlier_ratio = outlier_count / len(df)
            warnings.append(
                f"Found {outlier_count} outliers ({outlier_ratio:.1%} of data)"
            )

        return outlier_count

    def _zscore_outliers(self, prices: np.ndarray) -> tuple[np.ndarray, list[int]]:
        """Calculate outliers using z-score method."""
        mean = np.mean(prices)
        std = np.std(prices, ddof=1)

        if std == 0:
            return np.zeros_like(prices), []

        z_scores = np.abs((prices - mean) / std)
        outlier_mask = z_scores > self.config.outlier_threshold
        outlier_indices = np.where(outlier_mask)[0].tolist()

        return z_scores, outlier_indices

    def _iqr_outliers(self, prices: np.ndarray) -> tuple[np.ndarray, list[int]]:
        """Calculate outliers using IQR method."""
        q1 = np.percentile(prices, 25)
        q3 = np.percentile(prices, 75)
        iqr = q3 - q1

        lower_bound = q1 - (self.config.outlier_threshold * iqr)
        upper_bound = q3 + (self.config.outlier_threshold * iqr)

        outlier_mask = (prices < lower_bound) | (prices > upper_bound)
        outlier_indices = np.where(outlier_mask)[0].tolist()

        # Calculate "scores" for compatibility (distance from bounds in IQR units)
        scores = np.zeros_like(prices)
        scores[prices < lower_bound] = (
            lower_bound - prices[prices < lower_bound]
        ) / iqr
        scores[prices > upper_bound] = (
            prices[prices > upper_bound] - upper_bound
        ) / iqr

        return scores, outlier_indices

    def _modified_zscore_outliers(
        self, prices: np.ndarray
    ) -> tuple[np.ndarray, list[int]]:
        """Calculate outliers using modified z-score (median-based).

        EDUCATIONAL NOTE:
        Modified z-score is more robust than regular z-score because:
        - Uses median instead of mean (not affected by outliers)
        - Uses MAD (median absolute deviation) instead of std
        - Better for financial data with fat tails
        """
        median = np.median(prices)
        mad = np.median(np.abs(prices - median))

        if mad == 0:
            return np.zeros_like(prices), []

        # Modified z-score formula: 0.6745 * (x - median) / MAD
        modified_z = 0.6745 * (prices - median) / mad
        outlier_mask = np.abs(modified_z) > self.config.outlier_threshold
        outlier_indices = np.where(outlier_mask)[0].tolist()

        return np.abs(modified_z), outlier_indices

    def _check_date_gaps(
        self, df: pd.DataFrame, anomalies: list[DataAnomaly], warnings: list[str]
    ) -> int:
        """Check for suspicious gaps between dates.

        EDUCATIONAL NOTE:
        Normal gaps (3-4 days) = weekends
        Longer gaps (7-10 days) = holidays
        Very long gaps (>10 days) = potential data issues or stock halts
        """
        dates = pd.to_datetime(df["date"])
        date_diffs = dates.diff().dt.days

        # Find gaps exceeding threshold
        gap_mask = date_diffs > self.config.max_gap_days
        gap_indices = np.where(gap_mask)[0].tolist()

        for idx in gap_indices:
            gap_days = int(date_diffs.iloc[idx])
            severity = "medium" if gap_days < 30 else "high"

            anomalies.append(
                DataAnomaly(
                    anomaly_type="gap",
                    severity=severity,
                    description=f"Large date gap of {gap_days} days",
                    location=f"{dates.iloc[idx - 1]} to {dates.iloc[idx]}",
                    value=gap_days,
                    recommendation=(
                        "Verify no data available for this period. "
                        "Check if stock was halted or delisted."
                    ),
                )
            )

        gap_count = len(gap_indices)
        if gap_count > 0:
            warnings.append(f"Found {gap_count} suspicious date gaps")

        return gap_count

    def _detect_splits(
        self, df: pd.DataFrame, anomalies: list[DataAnomaly], warnings: list[str]
    ) -> int:
        """Detect potential stock splits or reverse splits.

        EDUCATIONAL NOTE:
        Stock splits cause large price jumps:
        - 2:1 split = ~50% price drop overnight
        - 1:2 reverse split = ~100% price jump overnight

        These are NOT real returns - they're corporate actions.
        Most data providers adjust for splits, but sometimes they miss them.
        """
        prices = df["price"].values
        dates = df["date"].values

        # Calculate daily returns
        returns = np.diff(prices) / prices[:-1]

        # Find large jumps
        split_mask = np.abs(returns) > self.config.split_threshold
        split_indices = np.where(split_mask)[0].tolist()

        for idx in split_indices:
            return_pct = returns[idx]
            severity = "medium" if abs(return_pct) < 0.40 else "high"

            anomalies.append(
                DataAnomaly(
                    anomaly_type="split",
                    severity=severity,
                    description=f"Potential stock split detected ({return_pct:.1%} price change)",
                    location=f"{dates[idx]} to {dates[idx + 1]}",
                    value=float(return_pct),
                    recommendation=(
                        "Verify if this is a stock split or reverse split. "
                        "Ensure all historical prices are split-adjusted."
                    ),
                )
            )

        split_count = len(split_indices)
        if split_count > 0:
            warnings.append(f"Found {split_count} potential stock splits")

        return split_count

    def _determine_validity(
        self,
        completeness_score: float,
        consistency_score: float,
        anomalies: list[DataAnomaly],
    ) -> bool:
        """Determine if data is valid for analysis.

        EDUCATIONAL NOTE:
        Data is considered invalid if:
        - Too much missing data (>5% by default)
        - Too many outliers (>5% by default)
        - Critical anomalies present
        """
        # Check for critical anomalies
        has_critical = any(a.severity == "critical" for a in anomalies)

        # Check if scores meet thresholds
        completeness_ok = completeness_score >= (
            1.0 - self.config.missing_data_threshold
        )

        # Consistency threshold derived from outlier checks
        # If we allow 5% outliers, we need 95% consistency
        1.0 - (self.config.outlier_threshold / 100.0)
        consistency_ok = consistency_score >= 0.90  # 90% minimum

        return completeness_ok and consistency_ok and not has_critical

    def _generate_recommendations(
        self,
        is_valid: bool,
        completeness_score: float,
        consistency_score: float,
        anomalies: list[DataAnomaly],
        recommendations: list[str],
    ) -> None:
        """Generate actionable recommendations based on validation results.

        EDUCATIONAL NOTE:
        Recommendations guide users on next steps:
        - Excellent data (>95%) = proceed with analysis
        - Good data (90-95%) = proceed with caution
        - Poor data (<90%) = clean or reject
        """
        if is_valid:
            if completeness_score > 0.98 and consistency_score > 0.98:
                recommendations.append(
                    "✓ Data quality is excellent - proceed with analysis"
                )
            else:
                recommendations.append(
                    "✓ Data quality is acceptable - proceed with caution"
                )
                recommendations.append(
                    "Consider reviewing anomalies before making critical decisions"
                )
        else:
            recommendations.append(
                "✗ Data quality is insufficient for reliable analysis"
            )

            if completeness_score < 0.95:
                recommendations.append(
                    "→ Address missing data: fill gaps or fetch from alternative source"
                )

            if consistency_score < 0.95:
                recommendations.append(
                    "→ Investigate outliers: verify prices and check for data errors"
                )

            # Check for critical issues
            critical_anomalies = [a for a in anomalies if a.severity == "critical"]
            if critical_anomalies:
                recommendations.append(
                    f"→ CRITICAL: {len(critical_anomalies)} critical issues must be resolved"
                )


# Export main class
__all__ = ["InputValidator"]
