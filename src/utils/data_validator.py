"""Data Quality Validator for Finance Guru™.

This module implements comprehensive data validation using statistical methods.
All calculations follow industry-standard data quality practices.

ARCHITECTURE NOTE:
This is Layer 2 of our 3-layer architecture:
    Layer 1: Pydantic Models - Data validation (validation_inputs.py)
    Layer 2: Calculator Classes (THIS FILE) - Business logic
    Layer 3: CLI Interface - Agent integration

EDUCATIONAL CONTEXT:
Data validation is the first step in any analysis. Before calculating risk
metrics or running strategies, you need to know your data is reliable.

This validator checks for:
1. COMPLETENESS: Are there missing data points?
2. CONSISTENCY: Are there outliers or anomalies?
3. CONTINUITY: Are there suspicious gaps in dates?
4. INTEGRITY: Are there signs of stock splits or data errors?

WHY THIS MATTERS:
- One bad data point can skew an entire risk calculation
- Missing data can hide important market events
- Undetected stock splits make returns analysis meaningless
- Outliers might be real volatility or data provider errors

Author: Finance Guru™ Development Team
Created: 2025-10-13
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


class DataValidator:
    """Comprehensive data quality validator.

    WHAT: Validates financial data quality using statistical methods
    WHY: Ensures data is reliable before analysis
    HOW: Uses statistical tests to detect anomalies

    USAGE EXAMPLE:
        # Create configuration
        config = ValidationConfig(
            outlier_method=OutlierMethod.Z_SCORE,
            outlier_threshold=3.0,
            missing_data_threshold=0.05
        )

        # Create validator
        validator = DataValidator(config)

        # Validate data
        results = validator.validate(price_series)

        # Check results
        if results.is_valid:
            print(f"✅ Data quality: {results.reliability_score:.1%}")
        else:
            print(f"❌ Found {len(results.anomalies)} issues")
    """

    def __init__(self, config: ValidationConfig):
        """Initialize validator with configuration.

        Args:
            config: Validated configuration (Pydantic model ensures correctness)

        EDUCATIONAL NOTE:
        By accepting a Pydantic model, we KNOW the config is valid.
        All threshold values are within acceptable ranges.
        """
        self.config = config

    def validate(self, price_series: PriceSeriesInput) -> ValidationOutput:
        """Perform comprehensive data validation.

        Args:
            price_series: Historical price data (validated by Pydantic)

        Returns:
            ValidationOutput: Complete validation report

        EDUCATIONAL NOTE:
        This method orchestrates all validation checks:
        1. Check for missing data
        2. Detect outliers in prices
        3. Find suspicious date gaps
        4. Identify potential stock splits
        5. Calculate quality scores
        6. Generate recommendations
        """
        # Convert to pandas for easier analysis
        df = pd.DataFrame(
            {
                "date": price_series.dates,
                "price": price_series.prices,
            }
        )
        if price_series.volumes:
            df["volume"] = price_series.volumes

        # Initialize results tracking
        anomalies: list[DataAnomaly] = []
        warnings_list: list[str] = []
        recommendations: list[str] = []

        # Run validation checks
        missing_count = self._check_missing_data(df, anomalies, warnings_list)
        outlier_count = self._check_outliers(df, anomalies, warnings_list)
        gap_count = self._check_date_gaps(df, anomalies, warnings_list)
        split_count = self._check_splits(df, anomalies, warnings_list)

        # Calculate quality scores
        completeness = self._calculate_completeness_score(df, missing_count)
        consistency = self._calculate_consistency_score(df, outlier_count)

        # Determine if data is valid
        is_valid = self._determine_validity(completeness, consistency, anomalies)

        # Generate recommendations
        self._generate_recommendations(
            is_valid, completeness, consistency, anomalies, recommendations
        )

        # Return validated output
        return ValidationOutput(
            ticker=price_series.ticker,
            validation_date=date.today(),
            is_valid=is_valid,
            total_points=len(df),
            missing_count=missing_count,
            outlier_count=outlier_count,
            gap_count=gap_count,
            potential_splits=split_count,
            completeness_score=completeness,
            consistency_score=consistency,
            reliability_score=0.0,  # Calculated by model_validator
            anomalies=anomalies,
            warnings=warnings_list,
            recommendations=recommendations,
        )

    def _check_missing_data(
        self, df: pd.DataFrame, anomalies: list[DataAnomaly], warnings_list: list[str]
    ) -> int:
        """Check for missing data points.

        WHAT: Identifies gaps in price data
        WHY: Missing data can bias analysis results
        HOW: Look for NaN/None values, calculate missing ratio

        EDUCATIONAL NOTE:
        Missing data is one of the most common data quality issues.
        It can occur due to:
        - Market closures (holidays, weekends)
        - Data provider gaps
        - Network errors during data fetch
        - Corporate actions (trading halts)
        """
        missing_prices = df["price"].isna().sum()
        missing_dates = df["date"].isna().sum()
        total_missing = int(missing_prices + missing_dates)

        if total_missing > 0:
            missing_ratio = total_missing / len(df)

            severity = "low"
            if missing_ratio > self.config.missing_data_threshold:
                severity = "critical"
            elif missing_ratio > self.config.missing_data_threshold / 2:
                severity = "high"

            anomalies.append(
                DataAnomaly(
                    anomaly_type="missing",
                    severity=severity,  # type: ignore
                    description=f"Found {total_missing} missing data points ({missing_ratio:.1%})",
                    value=total_missing,
                    recommendation=(
                        "Fill gaps using forward-fill or interpolation"
                        if severity in ["low", "medium"]
                        else "Data has too many gaps - consider using alternative source"
                    ),
                )
            )

            warnings_list.append(
                f"Missing data: {total_missing} points ({missing_ratio:.1%})"
            )

        return total_missing

    def _check_outliers(
        self, df: pd.DataFrame, anomalies: list[DataAnomaly], warnings_list: list[str]
    ) -> int:
        """Detect outliers in price data.

        WHAT: Identifies unusually large price movements
        WHY: Outliers might be errors or real volatility events
        HOW: Uses statistical methods (z-score, IQR, modified z-score)

        EDUCATIONAL NOTE:
        Outlier detection is tricky because:
        - Real market events (crashes, rallies) create outliers
        - Data errors also create outliers
        - You need domain knowledge to distinguish them

        The three methods:
        1. Z-SCORE: (value - mean) / std_dev > threshold
           - Assumes normal distribution
           - Good for typical price changes
           - Threshold: usually 3.0 (99.7% of normal data)

        2. IQR (Interquartile Range): value outside [Q1 - 1.5*IQR, Q3 + 1.5*IQR]
           - Doesn't assume distribution shape
           - Robust to existing outliers
           - Good for skewed data

        3. MODIFIED Z-SCORE: (value - median) / MAD > threshold
           - MAD = Median Absolute Deviation
           - Most robust to extreme outliers
           - Good when data has many anomalies
        """
        # Calculate daily returns for outlier detection
        returns = df["price"].pct_change().dropna()

        outliers = []
        outlier_indices = []

        if self.config.outlier_method == OutlierMethod.Z_SCORE:
            # Z-score method
            mean_return = returns.mean()
            std_return = returns.std()
            z_scores = np.abs((returns - mean_return) / std_return)
            outlier_mask = z_scores > self.config.outlier_threshold
            outliers = returns[outlier_mask]
            outlier_indices = returns[outlier_mask].index.tolist()

        elif self.config.outlier_method == OutlierMethod.IQR:
            # IQR method
            q1 = returns.quantile(0.25)
            q3 = returns.quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - (self.config.outlier_threshold * iqr)
            upper_bound = q3 + (self.config.outlier_threshold * iqr)
            outlier_mask = (returns < lower_bound) | (returns > upper_bound)
            outliers = returns[outlier_mask]
            outlier_indices = returns[outlier_mask].index.tolist()

        else:  # MODIFIED_Z
            # Modified z-score method (most robust)
            median_return = returns.median()
            mad = np.median(np.abs(returns - median_return))
            # Avoid division by zero
            if mad == 0:
                mad = np.std(returns) / 1.4826  # Fallback to std
            modified_z_scores = 0.6745 * np.abs((returns - median_return) / mad)
            outlier_mask = modified_z_scores > self.config.outlier_threshold
            outliers = returns[outlier_mask]
            outlier_indices = returns[outlier_mask].index.tolist()

        outlier_count = len(outliers)

        if outlier_count > 0:
            outlier_ratio = outlier_count / len(returns)

            # Determine severity based on count and magnitude
            severity = "low"
            if outlier_ratio > 0.10:  # More than 10% outliers
                severity = "high"
            elif outlier_ratio > 0.05:  # More than 5% outliers
                severity = "medium"

            # Add anomalies for each outlier
            for idx, return_val in zip(outlier_indices, outliers, strict=True):
                date_str = str(df.loc[idx, "date"]) if idx < len(df) else "unknown"
                anomalies.append(
                    DataAnomaly(
                        anomaly_type="outlier",
                        severity=severity,  # type: ignore
                        description=f"Price return of {return_val:.2%} exceeds threshold",
                        location=date_str,
                        value=float(return_val),
                        recommendation=(
                            "Verify this is a real market movement, not a data error"
                        ),
                    )
                )

            warnings_list.append(
                f"Found {outlier_count} outliers ({outlier_ratio:.1%} of data) "
                f"using {self.config.outlier_method.value} method"
            )

        return outlier_count

    def _check_date_gaps(
        self, df: pd.DataFrame, anomalies: list[DataAnomaly], warnings_list: list[str]
    ) -> int:
        """Check for suspicious gaps in dates.

        WHAT: Identifies unusually large gaps between consecutive dates
        WHY: Large gaps might indicate missing data or trading halts
        HOW: Calculate days between consecutive dates

        EDUCATIONAL NOTE:
        Normal gaps:
        - Weekends: 2-3 days (Friday to Monday)
        - Holidays: 1-4 days (long weekends)
        - Market closures: Usually announced in advance

        Suspicious gaps:
        - 10+ days: Might indicate data fetch error
        - 30+ days: Almost certainly a data problem
        - Inconsistent gaps: Suggests data quality issues

        WHY IT MATTERS:
        - Gaps hide market events (earnings, news, crashes)
        - Returns calculations become meaningless across gaps
        - Risk metrics underestimate true volatility
        """
        # Calculate gaps between consecutive dates
        date_series = pd.Series(df["date"])
        date_diffs = date_series.diff().dt.days.dropna()

        # Find gaps exceeding threshold
        suspicious_gaps = date_diffs[date_diffs > self.config.max_gap_days]
        gap_count = len(suspicious_gaps)

        if gap_count > 0:
            for idx, gap_days in suspicious_gaps.items():
                if idx > 0 and idx < len(df):
                    start_date = df.loc[idx - 1, "date"]
                    end_date = df.loc[idx, "date"]

                    severity = "low"
                    if gap_days > 30:
                        severity = "critical"
                    elif gap_days > 20:
                        severity = "high"
                    elif gap_days > self.config.max_gap_days:
                        severity = "medium"

                    anomalies.append(
                        DataAnomaly(
                            anomaly_type="gap",
                            severity=severity,  # type: ignore
                            description=f"Gap of {gap_days} days in data",
                            location=f"{start_date} to {end_date}",
                            value=float(gap_days),
                            recommendation=(
                                f"Investigate {gap_days}-day gap. "
                                "Check for trading halts, data provider issues, or market closures."
                            ),
                        )
                    )

            warnings_list.append(f"Found {gap_count} suspicious date gaps")

        return gap_count

    def _check_splits(
        self, df: pd.DataFrame, anomalies: list[DataAnomaly], warnings_list: list[str]
    ) -> int:
        """Check for potential stock splits or data errors.

        WHAT: Identifies sudden large price changes
        WHY: Stock splits require price adjustment for accurate analysis
        HOW: Look for returns exceeding split threshold

        EDUCATIONAL NOTE:
        Stock splits are corporate actions where companies divide shares:
        - 2-for-1 split: Price drops ~50%, shares double
        - 3-for-1 split: Price drops ~67%, shares triple

        WHY THEY MATTER:
        - Unadjusted data shows fake -50% "crash"
        - Returns calculations become meaningless
        - Risk metrics hugely overestimate volatility

        DETECTION HEURISTICS:
        - Return of -40% to -60% → Likely 2:1 split
        - Return of -60% to -70% → Likely 3:1 split
        - Return > +100% → Likely reverse split (1:2)

        Most data providers (yfinance, Bloomberg) pre-adjust for splits,
        but errors can occur for recent splits or exotic ratios.
        """
        if not self.config.check_splits:
            return 0

        # Calculate daily returns
        returns = df["price"].pct_change().dropna()

        # Look for returns exceeding split threshold (e.g., 25% = 0.25)
        potential_splits = returns[np.abs(returns) > self.config.split_threshold]
        split_count = len(potential_splits)

        if split_count > 0:
            for idx, return_val in potential_splits.items():
                if idx < len(df):
                    split_date = df.loc[idx, "date"]
                    df.loc[idx - 1, "price"] if idx > 0 else None
                    df.loc[idx, "price"]

                    # Estimate split ratio
                    split_ratio = "unknown"
                    if -0.60 < return_val < -0.40:
                        split_ratio = "2:1"
                    elif -0.70 < return_val < -0.60:
                        split_ratio = "3:1"
                    elif return_val > 1.0:
                        split_ratio = "1:2 (reverse)"

                    anomalies.append(
                        DataAnomaly(
                            anomaly_type="split",
                            severity="high",
                            description=(
                                f"Potential stock split detected: {return_val:.1%} price change"
                            ),
                            location=str(split_date),
                            value=float(return_val),
                            recommendation=(
                                f"Verify stock split (estimated {split_ratio} ratio) and ensure "
                                "historical prices are split-adjusted. Check company announcements."
                            ),
                        )
                    )

            warnings_list.append(
                f"Found {split_count} potential stock splits or large price gaps"
            )

        return split_count

    def _calculate_completeness_score(
        self, df: pd.DataFrame, missing_count: int
    ) -> float:
        """Calculate data completeness score.

        FORMULA: completeness = (total_points - missing_points) / total_points

        INTERPRETATION:
            1.00 = Perfect (no missing data)
            0.95 = Excellent (5% missing)
            0.90 = Good (10% missing)
            < 0.90 = Poor (too much missing data)
        """
        if len(df) == 0:
            return 0.0

        completeness = (len(df) - missing_count) / len(df)
        return float(max(0.0, min(1.0, completeness)))

    def _calculate_consistency_score(
        self, df: pd.DataFrame, outlier_count: int
    ) -> float:
        """Calculate data consistency score.

        FORMULA: consistency = (total_points - outlier_points) / total_points

        INTERPRETATION:
            1.00 = Perfect (no outliers)
            0.95 = Excellent (5% outliers)
            0.90 = Good (10% outliers)
            < 0.90 = Poor (too many outliers)

        EDUCATIONAL NOTE:
        Some outliers are legitimate (market crashes, earnings surprises).
        A score of 0.90-0.95 is actually quite good for volatile stocks.
        """
        if len(df) == 0:
            return 0.0

        consistency = (len(df) - outlier_count) / len(df)
        return float(max(0.0, min(1.0, consistency)))

    def _determine_validity(
        self, completeness: float, consistency: float, anomalies: list[DataAnomaly]
    ) -> bool:
        """Determine if data is valid for analysis.

        CRITERIA:
        1. Completeness >= 95% (at most 5% missing)
        2. Consistency >= 90% (at most 10% outliers)
        3. No critical anomalies

        EDUCATIONAL NOTE:
        These thresholds are conservative but reasonable:
        - Financial analysis needs high-quality data
        - One bad data point can skew risk calculations
        - When in doubt, reject the data and get better quality
        """
        # Check for critical anomalies
        has_critical = any(a.severity == "critical" for a in anomalies)

        # Data is valid if it passes all checks
        is_valid = completeness >= 0.95 and consistency >= 0.90 and not has_critical

        return is_valid

    def _generate_recommendations(
        self,
        is_valid: bool,
        completeness: float,
        consistency: float,
        anomalies: list[DataAnomaly],
        recommendations: list[str],
    ) -> None:
        """Generate actionable recommendations based on validation results.

        EDUCATIONAL NOTE:
        Recommendations follow this priority:
        1. If data is excellent → Proceed with analysis
        2. If data has minor issues → Proceed with caution
        3. If data has major issues → Clean data first
        4. If data is critically flawed → Reject and get new data
        """
        if is_valid:
            if completeness >= 0.99 and consistency >= 0.99:
                recommendations.append(
                    "✅ Data quality is excellent - proceed with confidence"
                )
            else:
                recommendations.append(
                    "✅ Data quality is good - proceed with analysis"
                )
                recommendations.append(
                    "⚠️  Review flagged anomalies to ensure they're legitimate"
                )
        else:
            # Data has issues - provide specific guidance
            if completeness < 0.95:
                recommendations.append(
                    "❌ Too much missing data - consider using alternative data source"
                )
            if consistency < 0.90:
                recommendations.append(
                    "⚠️  High outlier count - verify data integrity before analysis"
                )

            critical_count = sum(1 for a in anomalies if a.severity == "critical")
            if critical_count > 0:
                recommendations.append(
                    f"🚨 Found {critical_count} critical issues - data should NOT be used"
                )

            recommendations.append(
                "🔧 Clean data by addressing anomalies, or fetch fresh data"
            )


# Convenience function
def validate_price_data(
    ticker: str,
    prices: list[float],
    dates: list[str],
    volumes: list[float] | None = None,
    **config_kwargs,
) -> ValidationOutput:
    """Convenience function for validating price data.

    Args:
        ticker: Stock ticker symbol
        prices: List of historical prices
        dates: List of corresponding dates (YYYY-MM-DD format)
        volumes: Optional list of trading volumes
        **config_kwargs: Additional config options

    Returns:
        ValidationOutput with validation results

    Example:
        results = validate_price_data(
            ticker="TSLA",
            prices=[250.0, 252.5, 248.0, ...],
            dates=["2025-09-01", "2025-09-02", ...],
            outlier_method=OutlierMethod.Z_SCORE,
            outlier_threshold=3.0
        )
    """
    from datetime import date as date_type

    # Convert string dates to date objects
    date_objects = [date_type.fromisoformat(d) for d in dates]

    # Create input model
    price_series = PriceSeriesInput(
        ticker=ticker,
        prices=prices,
        dates=date_objects,
        volumes=volumes,
    )

    # Create config
    config = ValidationConfig(**config_kwargs)

    # Validate
    validator = DataValidator(config)
    return validator.validate(price_series)


# Type exports
__all__ = [
    "DataValidator",
    "validate_price_data",
]
