"""Moving Average Pydantic Models for Finance Guru™.

This module defines type-safe data structures for moving average calculations.
All models use Pydantic for automatic validation and type checking.

ARCHITECTURE NOTE:
These models represent Layer 1 of our 3-layer architecture:
    Layer 1: Pydantic Models (THIS FILE) - Data validation
    Layer 2: Calculator Classes - Business logic
    Layer 3: CLI Interface - Agent integration

EDUCATIONAL CONTEXT:
Moving averages are fundamental technical indicators that smooth price data by
creating a constantly updated average price. They help:
- Identify trend direction (price above MA = uptrend, below = downtrend)
- Smooth out price noise (reduce day-to-day volatility)
- Generate trading signals (crossovers, support/resistance)

Different types serve different purposes:
- SMA (Simple): Equal weight to all prices, easiest to understand
- EMA (Exponential): More weight to recent prices, responsive to changes
- WMA (Weighted): Linear increasing weights, balanced approach
- HMA (Hull): Smoothest with least lag, advanced calculation

Author: Finance Guru™ Development Team
Created: 2025-10-13
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class MovingAverageDataInput(BaseModel):
    """Price data for moving average calculations.

    WHAT: Container for price and date data
    WHY: Moving averages need historical price series
    VALIDATES:
        - All prices are positive (negative prices indicate data errors)
        - Dates are chronologically sorted (required for time-series)
        - Minimum data points for longest MA calculations
        - All arrays have equal length

    EDUCATIONAL NOTE:
    Moving averages require sufficient historical data:
    - Short-term MA (5-20): Need at least 30 days
    - Medium-term MA (50): Need at least 75 days
    - Long-term MA (200): Need at least 250 days

    More data points = more reliable signals
    """

    ticker: str = Field(
        ...,
        description="Stock ticker symbol (e.g., 'TSLA', 'AAPL', 'BRK-B')",
        min_length=1,
        max_length=10,
        pattern=r"^[A-Z\-\.]+$",  # Uppercase letters, hyphens, and dots (e.g., BRK-B, BRK.B)
    )

    dates: list[date] = Field(
        ...,
        description="Trading dates in chronological order",
        min_length=50,  # Minimum for 50-day MA
    )

    prices: list[float] = Field(
        ...,
        description="Closing prices (used for all MA calculations)",
        min_length=50,
    )

    @field_validator("prices")
    @classmethod
    def prices_must_be_positive(cls, v: list[float]) -> list[float]:
        """Ensure all prices are positive.

        WHY: Negative prices indicate data errors.
        Zero prices indicate delisted securities or missing data.
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
        """Ensure dates are chronologically ordered.

        WHY: Moving averages require sequential time-series data.
        Out-of-order dates produce incorrect MA values.
        """
        if v != sorted(v):
            raise ValueError(
                "Dates must be in chronological order (earliest to latest). "
                "Sort your data before creating MovingAverageDataInput."
            )
        return v

    @model_validator(mode="after")
    def validate_data_alignment(self) -> MovingAverageDataInput:
        """Ensure prices array has the same length as dates.

        WHY: Each date needs a corresponding price.
        Misalignment causes index errors in calculations.
        """
        if len(self.prices) != len(self.dates):
            raise ValueError(
                f"Prices length ({len(self.prices)}) must match dates length ({len(self.dates)})"
            )
        return self

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "ticker": "TSLA",
                    "dates": ["2025-09-01", "2025-09-02", "2025-09-03"],
                    "prices": [250.0, 252.5, 248.0],
                }
            ]
        }
    }


class MovingAverageConfig(BaseModel):
    """Configuration for moving average calculations.

    WHAT: Standard parameters for MA calculations
    WHY: Ensures consistent calculations across agents
    USE CASES:
        - Market Researcher: Standard periods for quick trend checks
        - Quant Analyst: Custom periods for strategy testing
        - Strategy Advisor: Multiple MAs for crossover signals

    EDUCATIONAL NOTE:
    Common MA periods and their uses:
    - 5-20 days: Short-term trading (day traders)
    - 50 days: Intermediate trend (swing traders)
    - 100 days: Long-term trend confirmation
    - 200 days: Major trend indicator (institutional favorite)

    Crossover combinations:
    - 50/200: Golden Cross/Death Cross (most famous)
    - 20/50: Intermediate crossover
    - 10/30: Short-term crossover
    """

    ma_type: Literal["SMA", "EMA", "WMA", "HMA"] = Field(
        default="SMA", description="Type of moving average to calculate"
    )

    period: int = Field(
        default=50,
        ge=5,
        le=200,
        description="MA period in days (default: 50, range: 5-200)",
    )

    # Optional second MA for crossover detection
    secondary_ma_type: Literal["SMA", "EMA", "WMA", "HMA"] | None = Field(
        default=None, description="Type of second MA for crossover detection (optional)"
    )

    secondary_period: int | None = Field(
        default=None,
        ge=5,
        le=200,
        description="Second MA period for crossover detection (optional)",
    )

    @model_validator(mode="after")
    def validate_crossover_config(self) -> MovingAverageConfig:
        """Validate crossover configuration.

        WHY: For crossovers, we need two different periods.
        Fast MA (shorter period) must be less than slow MA (longer period).
        """
        # If one crossover parameter is set, both must be set
        has_secondary_type = self.secondary_ma_type is not None
        has_secondary_period = self.secondary_period is not None

        if has_secondary_type != has_secondary_period:
            raise ValueError(
                "For crossover detection, both secondary_ma_type and secondary_period "
                "must be specified, or neither."
            )

        # If both are set, ensure periods are different and properly ordered
        if (
            has_secondary_type
            and has_secondary_period
            and self.period == self.secondary_period
        ):
            raise ValueError(
                f"Primary period ({self.period}) must differ from "
                f"secondary period ({self.secondary_period}) for crossover detection"
            )

        # Warn if the "fast" MA is actually slower (unusual but not invalid)
        # We'll just ensure they're different - user decides which is fast/slow

        return self

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "ma_type": "SMA",
                    "period": 50,
                    "secondary_ma_type": "SMA",
                    "secondary_period": 200,
                }
            ]
        }
    }


class MovingAverageOutput(BaseModel):
    """Single moving average output.

    WHAT: Calculated MA values and metadata
    WHY: Provides complete MA information for trend analysis
    USE CASES:
        - Trend identification: Price vs MA relationship
        - Support/resistance: MAs act as dynamic support/resistance
        - Chart plotting: Full MA series for visualization

    EDUCATIONAL NOTE:
    Interpreting moving averages:
    - Price > MA: Bullish (uptrend)
    - Price < MA: Bearish (downtrend)
    - Price touching MA: Potential support/resistance
    - MA sloping up: Uptrend gaining strength
    - MA sloping down: Downtrend gaining strength
    - MA flattening: Trend weakening or consolidation
    """

    ticker: str
    calculation_date: date = Field(
        ..., description="Most recent date in calculation (today's value)"
    )
    ma_type: Literal["SMA", "EMA", "WMA", "HMA"] = Field(
        ..., description="Type of moving average calculated"
    )
    period: int = Field(..., description="Period used for calculation (in days)")
    current_value: float | None = Field(
        ...,
        description="Current MA value (most recent calculation), None if insufficient data",
    )
    current_price: float = Field(
        ..., gt=0.0, description="Current price (for comparison with MA)"
    )
    price_vs_ma: Literal["ABOVE", "BELOW", "AT"] = Field(
        ..., description="Price position relative to MA (trend indicator)"
    )
    ma_values: list[float] = Field(
        ..., description="Full MA series (for charting/analysis)"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "ticker": "TSLA",
                    "calculation_date": "2025-10-13",
                    "ma_type": "SMA",
                    "period": 50,
                    "current_value": 248.50,
                    "current_price": 252.30,
                    "price_vs_ma": "ABOVE",
                    "ma_values": [245.0, 246.5, 248.5],
                }
            ]
        }
    }


class CrossoverOutput(BaseModel):
    """Moving average crossover analysis.

    WHAT: Detects and interprets MA crossovers
    WHY: Crossovers are powerful trading signals
    HOW: Compares fast MA (shorter period) vs slow MA (longer period)

    EDUCATIONAL NOTE:
    Famous crossover signals:
    - Golden Cross: Fast MA crosses ABOVE slow MA = BULLISH
      * 50-day crosses above 200-day = Major buy signal
      * Signals potential start of bull market
      * Most reliable when volume confirms

    - Death Cross: Fast MA crosses BELOW slow MA = BEARISH
      * 50-day crosses below 200-day = Major sell signal
      * Signals potential start of bear market
      * Most reliable after extended uptrend

    FALSE SIGNALS (Whipsaws):
    - Can occur in choppy/sideways markets
    - Use additional confirmation (volume, RSI, MACD)
    - Consider trend context (crossover more reliable in trending markets)

    TIMING:
    - Crossovers are lagging indicators (confirm trends, don't predict)
    - May miss early move, but catch sustained trends
    - Best used with other indicators for confirmation
    """

    ticker: str
    calculation_date: date
    fast_ma_type: Literal["SMA", "EMA", "WMA", "HMA"]
    fast_period: int
    fast_value: float = Field(..., gt=0.0)

    slow_ma_type: Literal["SMA", "EMA", "WMA", "HMA"]
    slow_period: int
    slow_value: float = Field(..., gt=0.0)

    current_signal: Literal["BULLISH", "BEARISH", "NEUTRAL"] = Field(
        ..., description="Current crossover signal based on MA positions"
    )

    last_crossover_date: date | None = Field(
        default=None, description="Date of most recent crossover (if any)"
    )

    crossover_type: Literal["GOLDEN_CROSS", "DEATH_CROSS", "NONE"] = Field(
        ..., description="Type of most recent crossover (if 50/200 SMA)"
    )

    days_since_crossover: int | None = Field(
        default=None, ge=0, description="Days since last crossover (signal freshness)"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "ticker": "TSLA",
                    "calculation_date": "2025-10-13",
                    "fast_ma_type": "SMA",
                    "fast_period": 50,
                    "fast_value": 248.50,
                    "slow_ma_type": "SMA",
                    "slow_period": 200,
                    "slow_value": 242.30,
                    "current_signal": "BULLISH",
                    "last_crossover_date": "2025-09-15",
                    "crossover_type": "GOLDEN_CROSS",
                    "days_since_crossover": 28,
                }
            ]
        }
    }


class MovingAverageAnalysis(BaseModel):
    """Complete moving average analysis including optional crossover.

    WHAT: Single or dual MA analysis with full interpretation
    WHY: Convenient for comprehensive trend analysis
    USE CASES:
        - Strategy Advisor: Full trend context for decisions
        - Market Researcher: Quick trend assessment
        - Quant Analyst: Data for backtesting strategies
    """

    ticker: str
    calculation_date: date
    primary_ma: MovingAverageOutput
    secondary_ma: MovingAverageOutput | None = Field(
        default=None, description="Second MA if crossover analysis requested"
    )
    crossover_analysis: CrossoverOutput | None = Field(
        default=None, description="Crossover signals if dual MA analysis"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "ticker": "TSLA",
                    "calculation_date": "2025-10-13",
                    "primary_ma": {
                        "ticker": "TSLA",
                        "calculation_date": "2025-10-13",
                        "ma_type": "SMA",
                        "period": 50,
                        "current_value": 248.50,
                        "current_price": 252.30,
                        "price_vs_ma": "ABOVE",
                        "ma_values": [],
                    },
                    "secondary_ma": None,
                    "crossover_analysis": None,
                }
            ]
        }
    }


# Type exports
__all__ = [
    "MovingAverageDataInput",
    "MovingAverageConfig",
    "MovingAverageOutput",
    "CrossoverOutput",
    "MovingAverageAnalysis",
]
