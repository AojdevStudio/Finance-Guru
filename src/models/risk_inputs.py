"""
Risk Analysis Pydantic Models for Finance Guru™

This module defines type-safe data structures for risk calculations.
All models use Pydantic for automatic validation and type checking.

ARCHITECTURE NOTE:
These models represent Layer 1 of our 3-layer architecture:
    Layer 1: Pydantic Models (THIS FILE) - Data validation
    Layer 2: Calculator Classes - Business logic
    Layer 3: CLI Interface - Agent integration

EDUCATIONAL CONTEXT:
- Pydantic validates data automatically when you create instances
- Type hints (like 'float', 'list[float]') enable IDE autocomplete
- Field validators catch bad data before it reaches calculations
- Examples in model_config serve as documentation for agents

Author: Finance Guru™ Development Team
Created: 2025-10-13
"""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class PriceDataInput(BaseModel):
    """
    Historical price data for risk calculations.

    WHAT: Container for time-series price data
    WHY: Ensures price data is valid before risk calculations begin
    VALIDATES:
        - Prices are positive (can't have negative stock prices)
        - Dates are chronologically sorted
        - Minimum 30 data points (statistical significance)
        - Equal number of prices and dates (data alignment)

    USAGE EXAMPLE:
        price_data = PriceDataInput(
            ticker="TSLA",
            prices=[250.0, 252.5, 248.0, 255.0],
            dates=[date(2025,10,10), date(2025,10,11), date(2025,10,12), date(2025,10,13)]
        )
    """

    ticker: str = Field(
        ...,
        description="Stock ticker symbol (e.g., 'TSLA', 'AAPL', 'SPY')",
        min_length=1,
        max_length=10,
        pattern=r"^[A-Z]+$",  # Uppercase letters only
    )

    prices: list[float] = Field(
        ...,
        description="Historical closing prices (minimum 30 days for statistical validity)",
        min_length=30,
    )

    dates: list[date] = Field(
        ...,
        description="Corresponding dates in YYYY-MM-DD format",
        min_length=30,
    )

    @field_validator("prices")
    @classmethod
    def prices_must_be_positive(cls, v: list[float]) -> list[float]:
        """
        Ensure all prices are positive numbers.

        WHY: Stock prices cannot be negative. Zero prices indicate
        delisted stocks or data errors. We reject both.

        EDUCATIONAL NOTE:
        This validator runs automatically when you create a PriceDataInput.
        If validation fails, you get a clear error message instead of
        silent calculation errors later.
        """
        if any(price <= 0 for price in v):
            raise ValueError(
                "All prices must be positive. Found zero or negative price. "
                "Check your data source for errors or delisted securities."
            )
        return v

    @field_validator("dates")
    @classmethod
    def dates_must_be_sorted(cls, v: list[date]) -> list[date]:
        """
        Ensure dates are in chronological order.

        WHY: Time-series calculations assume sequential data.
        Out-of-order dates produce incorrect returns and volatility.

        EDUCATIONAL NOTE:
        We compare the list to its sorted version. If they're not equal,
        the dates are out of order.
        """
        if v != sorted(v):
            raise ValueError(
                "Dates must be in chronological order (earliest to latest). "
                "Sort your data by date before creating PriceDataInput."
            )
        return v

    @model_validator(mode="after")
    def validate_price_date_alignment(self) -> "PriceDataInput":
        """
        Ensure equal number of prices and dates.

        WHY: Each price needs a corresponding date.
        Misalignment causes index errors in calculations.

        EDUCATIONAL NOTE:
        This is a 'model validator' - it runs after all field validators
        and can access multiple fields simultaneously.
        """
        if len(self.prices) != len(self.dates):
            raise ValueError(
                f"Length mismatch: {len(self.prices)} prices but {len(self.dates)} dates. "
                "Each price must have a corresponding date."
            )
        return self

    @model_validator(mode="after")
    def check_for_duplicate_dates(self) -> "PriceDataInput":
        """
        Warn if duplicate dates are present.

        WHY: Duplicate dates indicate data quality issues
        (e.g., accidentally loading the same file twice).

        EDUCATIONAL NOTE:
        We convert to a set (which removes duplicates) and compare lengths.
        """
        if len(self.dates) != len(set(self.dates)):
            raise ValueError(
                "Duplicate dates found in price data. "
                "Each date should appear only once. Check your data source."
            )
        return self

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "ticker": "TSLA",
                    "prices": [
                        250.0, 252.5, 248.0, 255.0, 253.5, 256.0, 254.5, 257.0, 259.5, 258.0,
                        260.5, 262.0, 261.5, 263.0, 265.5, 264.0, 266.5, 268.0, 267.5, 269.0,
                        271.5, 270.0, 272.5, 274.0, 273.5, 275.0, 277.5, 276.0, 278.5, 280.0
                    ],
                    "dates": [
                        "2025-09-01", "2025-09-02", "2025-09-03", "2025-09-04", "2025-09-05",
                        "2025-09-08", "2025-09-09", "2025-09-10", "2025-09-11", "2025-09-12",
                        "2025-09-15", "2025-09-16", "2025-09-17", "2025-09-18", "2025-09-19",
                        "2025-09-22", "2025-09-23", "2025-09-24", "2025-09-25", "2025-09-26",
                        "2025-09-29", "2025-09-30", "2025-10-01", "2025-10-02", "2025-10-03",
                        "2025-10-06", "2025-10-07", "2025-10-08", "2025-10-09", "2025-10-10"
                    ]
                }
            ]
        }
    }


class RiskCalculationConfig(BaseModel):
    """
    Configuration parameters for risk metric calculations.

    WHAT: Standardized settings for risk analysis
    WHY: Ensures consistent risk calculations across all agents
    USE CASES:
        - Compliance Officer: Enforce standard risk parameters
        - Quant Analyst: Configure analysis sensitivity
        - Strategy Advisor: Align with investment horizon

    EDUCATIONAL NOTE:
    These parameters control HOW we calculate risk. Different settings
    are appropriate for different investment styles:
    - Day traders: Low rolling_window (30 days), high confidence_level
    - Long-term investors: High rolling_window (252 days), lower confidence_level
    """

    confidence_level: float = Field(
        default=0.95,
        ge=0.50,  # At least 50% confidence
        le=0.99,  # At most 99% confidence
        description="Confidence level for VaR calculation (0.95 = 95% confidence)",
    )

    var_method: Literal["historical", "parametric"] = Field(
        default="historical",
        description=(
            "Method for calculating Value at Risk:\n"
            "  - 'historical': Uses actual historical returns (non-parametric)\n"
            "  - 'parametric': Assumes normal distribution (requires fewer data points)"
        ),
    )

    rolling_window: int = Field(
        default=252,
        ge=30,  # Minimum 30 days for statistical validity
        le=756,  # Maximum 3 years (beyond that, markets change too much)
        description="Number of days for rolling calculations (252 = 1 trading year)",
    )

    risk_free_rate: float = Field(
        default=0.045,
        ge=0.0,  # Risk-free rate can't be negative (except in rare circumstances)
        le=0.20,  # Sanity check: if >20%, likely a data entry error
        description="Annual risk-free rate for Sharpe/Sortino calculations (0.045 = 4.5%)",
    )

    @field_validator("confidence_level")
    @classmethod
    def validate_confidence_makes_sense(cls, v: float) -> float:
        """
        Provide guidance on confidence level selection.

        EDUCATIONAL NOTE:
        Common confidence levels:
        - 90% (0.90): Less conservative, more frequent VaR breaches
        - 95% (0.95): Industry standard for risk reporting
        - 99% (0.99): Very conservative, rare VaR breaches
        """
        if v < 0.90:
            # This is a warning, not an error - we still allow it
            import warnings
            warnings.warn(
                f"Confidence level {v:.1%} is below 90%. "
                "Consider using at least 90% for meaningful risk assessment."
            )
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "confidence_level": 0.95,
                    "var_method": "historical",
                    "rolling_window": 252,
                    "risk_free_rate": 0.045
                },
                {
                    "confidence_level": 0.99,
                    "var_method": "parametric",
                    "rolling_window": 126,
                    "risk_free_rate": 0.050
                }
            ]
        }
    }


class RiskMetricsOutput(BaseModel):
    """
    Comprehensive risk metrics output.

    WHAT: All calculated risk metrics in a single validated structure
    WHY: Guarantees agents receive complete, properly-typed risk data
    USE CASES:
        - Strategy Advisor: Evaluate risk-adjusted returns
        - Compliance Officer: Monitor risk limit breaches
        - Market Researcher: Compare risk profiles across securities

    EDUCATIONAL NOTE:
    Each metric tells you something different about risk:
    - VaR/CVaR: "What can we lose?" (loss magnitude)
    - Sharpe/Sortino: "Are we being paid enough for this risk?" (risk-adjusted return)
    - Max Drawdown: "What was the worst peak-to-trough decline?" (historical worst case)
    - Volatility: "How much does this bounce around?" (price stability)
    - Beta/Alpha: "How does this relate to the market?" (systematic vs idiosyncratic risk)
    """

    # Identification
    ticker: str = Field(
        ...,
        description="Stock ticker symbol"
    )

    calculation_date: date = Field(
        ...,
        description="Date of calculation (typically the latest date in the price series)"
    )

    # Value at Risk Metrics
    var_95: float = Field(
        ...,
        description=(
            "95% Value at Risk (daily loss threshold). "
            "Example: -0.035 means '95% of days, losses won't exceed 3.5%'"
        )
    )

    cvar_95: float = Field(
        ...,
        description=(
            "95% Conditional VaR (expected loss beyond VaR). "
            "Example: -0.048 means 'when losses DO exceed VaR, average loss is 4.8%'"
        )
    )

    # Return-Based Risk Metrics
    sharpe_ratio: float = Field(
        ...,
        description=(
            "Sharpe Ratio (excess return per unit of total risk). "
            "Rule of thumb: <1.0=poor, 1.0-2.0=good, >2.0=excellent. "
            "Example: 1.25 means you earn 1.25% excess return per 1% of volatility"
        )
    )

    sortino_ratio: float = Field(
        ...,
        description=(
            "Sortino Ratio (excess return per unit of downside risk). "
            "Like Sharpe but only penalizes downside volatility. "
            "Generally higher than Sharpe for asymmetric return distributions."
        )
    )

    # Drawdown Metrics
    max_drawdown: float = Field(
        ...,
        le=0.0,  # Drawdowns are always negative or zero
        description=(
            "Maximum peak-to-trough decline (always negative or zero). "
            "Example: -0.32 means 'worst decline was 32% from peak'"
        )
    )

    calmar_ratio: float = Field(
        ...,
        description=(
            "Calmar Ratio (annual return / absolute max drawdown). "
            "Measures return per unit of worst-case loss. "
            "Higher is better. Example: 0.85 means 0.85% return per 1% max drawdown"
        )
    )

    # Volatility Metrics
    annual_volatility: float = Field(
        ...,
        ge=0.0,  # Volatility is always positive
        description=(
            "Annualized volatility (standard deviation of returns). "
            "Example: 0.42 means 42% annual volatility (high for stocks, typical for crypto)"
        )
    )

    # Market Relationship Metrics (Optional)
    beta: float | None = Field(
        default=None,
        description=(
            "Beta vs benchmark (sensitivity to market movements). "
            "Example: 1.8 means stock moves 1.8x as much as the market. "
            "None if benchmark data not provided."
        )
    )

    alpha: float | None = Field(
        default=None,
        description=(
            "Alpha vs benchmark (excess return above what beta predicts). "
            "Example: 0.05 means 5% annualized outperformance vs benchmark. "
            "None if benchmark data not provided."
        )
    )

    @field_validator("var_95", "cvar_95")
    @classmethod
    def var_metrics_should_be_negative(cls, v: float, info) -> float:
        """
        Validate that VaR metrics are negative (representing losses).

        EDUCATIONAL NOTE:
        VaR and CVaR represent LOSSES, so they should be negative.
        If you see positive VaR, either:
        1. The security had no down days (very rare)
        2. There's a sign error in your calculation
        """
        if v > 0:
            import warnings
            warnings.warn(
                f"{info.field_name} is positive ({v:.4f}). "
                "VaR metrics typically represent losses and should be negative. "
                "Verify your calculation logic."
            )
        return v

    @field_validator("max_drawdown")
    @classmethod
    def drawdown_must_be_non_positive(cls, v: float) -> float:
        """
        Ensure max drawdown is negative or zero.

        EDUCATIONAL NOTE:
        Drawdown is peak-to-trough decline, so it's always ≤ 0.
        If you see positive drawdown, there's a calculation error.
        """
        if v > 0:
            raise ValueError(
                f"Max drawdown must be ≤ 0 (found {v:.4f}). "
                "Drawdown represents peak-to-trough decline and cannot be positive."
            )
        return v

    @model_validator(mode="after")
    def validate_risk_metric_relationships(self) -> "RiskMetricsOutput":
        """
        Check logical relationships between risk metrics.

        EDUCATIONAL NOTE:
        Some metrics have mathematical relationships:
        - CVaR should be more extreme than VaR (it's the "tail" beyond VaR)
        - Sortino should generally be higher than Sharpe (less penalized)
        """
        # CVaR should be more extreme (more negative) than VaR
        if self.cvar_95 > self.var_95:
            import warnings
            warnings.warn(
                f"CVaR ({self.cvar_95:.4f}) is less extreme than VaR ({self.var_95:.4f}). "
                "CVaR should represent worse losses than VaR. Check calculation logic."
            )

        return self

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "ticker": "TSLA",
                    "calculation_date": "2025-10-13",
                    "var_95": -0.035,
                    "cvar_95": -0.048,
                    "sharpe_ratio": 1.25,
                    "sortino_ratio": 1.58,
                    "max_drawdown": -0.32,
                    "calmar_ratio": 0.85,
                    "annual_volatility": 0.42,
                    "beta": 1.8,
                    "alpha": 0.05
                },
                {
                    "ticker": "AAPL",
                    "calculation_date": "2025-10-13",
                    "var_95": -0.022,
                    "cvar_95": -0.031,
                    "sharpe_ratio": 1.68,
                    "sortino_ratio": 2.12,
                    "max_drawdown": -0.18,
                    "calmar_ratio": 1.35,
                    "annual_volatility": 0.28,
                    "beta": 1.2,
                    "alpha": 0.03
                }
            ]
        }
    }


# Type exports for convenience
__all__ = [
    "PriceDataInput",
    "RiskCalculationConfig",
    "RiskMetricsOutput",
]
