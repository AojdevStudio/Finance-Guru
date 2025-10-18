"""
Data Validation Pydantic Models for Finance Guru™

This module defines type-safe data structures for data quality validation.
All models use Pydantic for automatic validation and type checking.

ARCHITECTURE NOTE:
These models represent Layer 1 of our 3-layer architecture:
    Layer 1: Pydantic Models (THIS FILE) - Data validation
    Layer 2: Calculator Classes - Business logic
    Layer 3: CLI Interface - Agent integration

EDUCATIONAL CONTEXT:
- Data quality is critical for financial analysis
- Garbage in = garbage out (bad data leads to bad decisions)
- These models help catch data issues before they affect calculations
- Think of this as "quality control" for your financial data

Author: Finance Guru™ Development Team
Created: 2025-10-13
"""

from datetime import date
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class OutlierMethod(str, Enum):
    """
    Methods for detecting outliers in data.

    WHAT: Different statistical approaches to identify unusual data points
    WHY: Different methods catch different types of outliers

    METHODS:
        - Z_SCORE: Standard deviations from mean (assumes normal distribution)
        - IQR: Interquartile range method (robust to non-normal data)
        - MODIFIED_Z: Modified z-score using median (robust to extreme outliers)

    EDUCATIONAL NOTE:
    Z-score works well for normally distributed data (stock returns).
    IQR works better for skewed data (trading volumes).
    Modified z-score is most robust when you suspect extreme outliers.
    """
    Z_SCORE = "z_score"
    IQR = "iqr"
    MODIFIED_Z = "modified_z"


class PriceSeriesInput(BaseModel):
    """
    Historical price series for validation.

    WHAT: Container for price data that needs quality checking
    WHY: Ensures basic data structure is valid before validation
    VALIDATES:
        - Ticker is properly formatted
        - Prices and dates are aligned
        - Minimum data points for validation
        - Dates are chronological

    USAGE EXAMPLE:
        price_series = PriceSeriesInput(
            ticker="TSLA",
            prices=[250.0, 252.5, 248.0, 255.0],
            dates=[date(2025,10,10), date(2025,10,11), date(2025,10,12), date(2025,10,13)],
            volumes=[1000000, 1200000, 950000, 1100000]
        )
    """

    ticker: str = Field(
        ...,
        description="Stock ticker symbol (e.g., 'TSLA', 'AAPL', 'SPY')",
        min_length=1,
        max_length=10,
        pattern=r"^[A-Z]+$",
    )

    prices: list[float] = Field(
        ...,
        description="Historical closing prices",
        min_length=10,
    )

    dates: list[date] = Field(
        ...,
        description="Corresponding dates in YYYY-MM-DD format",
        min_length=10,
    )

    volumes: list[float] | None = Field(
        default=None,
        description="Optional trading volumes for additional validation",
    )

    @field_validator("prices")
    @classmethod
    def prices_must_be_positive(cls, v: list[float]) -> list[float]:
        """
        Ensure all prices are positive.

        EDUCATIONAL NOTE:
        Negative or zero prices indicate data errors.
        This validator catches them early.
        """
        if any(price <= 0 for price in v):
            raise ValueError(
                "All prices must be positive. Found zero or negative price. "
                "Check your data source for errors."
            )
        return v

    @field_validator("dates")
    @classmethod
    def dates_must_be_sorted(cls, v: list[date]) -> list[date]:
        """Ensure dates are in chronological order."""
        if v != sorted(v):
            raise ValueError(
                "Dates must be in chronological order (earliest to latest)."
            )
        return v

    @model_validator(mode="after")
    def validate_alignment(self) -> "PriceSeriesInput":
        """Ensure prices, dates, and volumes are aligned."""
        if len(self.prices) != len(self.dates):
            raise ValueError(
                f"Length mismatch: {len(self.prices)} prices but {len(self.dates)} dates."
            )

        if self.volumes is not None:
            if len(self.volumes) != len(self.prices):
                raise ValueError(
                    f"Length mismatch: {len(self.prices)} prices but {len(self.volumes)} volumes."
                )

        return self


class ValidationConfig(BaseModel):
    """
    Configuration for data validation checks.

    WHAT: Settings that control how strictly we validate data
    WHY: Different use cases need different validation sensitivity
    USE CASES:
        - Compliance Officer: Strict validation (low thresholds)
        - Market Researcher: Moderate validation (default)
        - Historical Analysis: Lenient validation (high thresholds)

    EDUCATIONAL NOTE:
    Think of these parameters as "sensitivity knobs":
    - Lower thresholds = more strict = flags more issues
    - Higher thresholds = more lenient = flags fewer issues
    """

    outlier_method: OutlierMethod = Field(
        default=OutlierMethod.Z_SCORE,
        description="Method for detecting outliers"
    )

    outlier_threshold: float = Field(
        default=3.0,
        ge=1.5,
        le=5.0,
        description=(
            "Threshold for outlier detection:\n"
            "  - z_score: Number of standard deviations (default: 3.0)\n"
            "  - iqr: Multiplier for IQR (default: 3.0)\n"
            "  - modified_z: Modified z-score threshold (default: 3.0)"
        )
    )

    missing_data_threshold: float = Field(
        default=0.05,
        ge=0.0,
        le=0.50,
        description="Maximum acceptable missing data ratio (0.05 = 5%)"
    )

    max_gap_days: int = Field(
        default=10,
        ge=1,
        le=90,
        description="Maximum acceptable gap between dates (in days)"
    )

    check_splits: bool = Field(
        default=True,
        description="Check for stock splits/dividends (large price jumps)"
    )

    split_threshold: float = Field(
        default=0.25,
        ge=0.10,
        le=0.50,
        description="Price change threshold for split detection (0.25 = 25%)"
    )


class DataAnomaly(BaseModel):
    """
    Details about a detected anomaly.

    WHAT: Information about a specific data quality issue
    WHY: Helps users understand and fix data problems
    """

    anomaly_type: Literal["missing", "outlier", "gap", "split", "duplicate"] = Field(
        ...,
        description="Type of anomaly detected"
    )

    severity: Literal["low", "medium", "high", "critical"] = Field(
        ...,
        description="Severity level of the anomaly"
    )

    description: str = Field(
        ...,
        description="Human-readable description of the issue"
    )

    location: str | None = Field(
        default=None,
        description="Where the anomaly was found (e.g., date, index)"
    )

    value: float | str | None = Field(
        default=None,
        description="The problematic value (if applicable)"
    )

    recommendation: str = Field(
        ...,
        description="Suggested action to fix the issue"
    )


class ValidationOutput(BaseModel):
    """
    Comprehensive data validation results.

    WHAT: Complete report of data quality checks
    WHY: Provides actionable insights for data cleaning
    USE CASES:
        - Quant Analyst: Ensure data quality before analysis
        - Compliance Officer: Verify data integrity
        - Data Engineer: Identify data pipeline issues

    EDUCATIONAL NOTE:
    This output tells you:
    1. Is the data usable? (is_valid)
    2. What's wrong with it? (anomalies)
    3. How good is it? (quality scores)
    4. Should I fix it or reject it? (recommendations)
    """

    ticker: str = Field(
        ...,
        description="Stock ticker symbol"
    )

    validation_date: date = Field(
        ...,
        description="Date when validation was performed"
    )

    is_valid: bool = Field(
        ...,
        description="Overall validation result (True = data is usable)"
    )

    # Counts
    total_points: int = Field(
        ...,
        ge=0,
        description="Total number of data points analyzed"
    )

    missing_count: int = Field(
        default=0,
        ge=0,
        description="Number of missing data points"
    )

    outlier_count: int = Field(
        default=0,
        ge=0,
        description="Number of outliers detected"
    )

    gap_count: int = Field(
        default=0,
        ge=0,
        description="Number of suspicious date gaps"
    )

    potential_splits: int = Field(
        default=0,
        ge=0,
        description="Number of potential stock splits detected"
    )

    # Quality Scores (0.0 to 1.0)
    completeness_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Data completeness (1.0 = no missing data)"
    )

    consistency_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Data consistency (1.0 = no outliers)"
    )

    reliability_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall reliability (weighted average)"
    )

    # Detailed Anomalies
    anomalies: list[DataAnomaly] = Field(
        default_factory=list,
        description="List of all detected anomalies"
    )

    # Summary
    warnings: list[str] = Field(
        default_factory=list,
        description="General warnings about data quality"
    )

    recommendations: list[str] = Field(
        default_factory=list,
        description="Suggested actions to improve data quality"
    )

    @model_validator(mode="after")
    def calculate_reliability(self) -> "ValidationOutput":
        """
        Calculate overall reliability score.

        EDUCATIONAL NOTE:
        Reliability is a weighted average of completeness and consistency.
        Completeness is weighted 60% (more important - missing data is fatal).
        Consistency is weighted 40% (outliers can sometimes be real).
        """
        self.reliability_score = (
            0.6 * self.completeness_score +
            0.4 * self.consistency_score
        )
        return self

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "ticker": "TSLA",
                    "validation_date": "2025-10-13",
                    "is_valid": True,
                    "total_points": 252,
                    "missing_count": 2,
                    "outlier_count": 5,
                    "gap_count": 1,
                    "potential_splits": 0,
                    "completeness_score": 0.992,
                    "consistency_score": 0.980,
                    "reliability_score": 0.987,
                    "anomalies": [
                        {
                            "anomaly_type": "outlier",
                            "severity": "medium",
                            "description": "Price outlier detected",
                            "location": "2025-09-15",
                            "value": 285.50,
                            "recommendation": "Verify price data from alternative source"
                        }
                    ],
                    "warnings": [
                        "Found 5 outliers (2.0% of data)"
                    ],
                    "recommendations": [
                        "Data quality is excellent - proceed with analysis",
                        "Review outliers to ensure they're legitimate price movements"
                    ]
                }
            ]
        }
    }


# Type exports
__all__ = [
    "OutlierMethod",
    "PriceSeriesInput",
    "ValidationConfig",
    "DataAnomaly",
    "ValidationOutput",
]
