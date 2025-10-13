"""
Momentum Indicators Pydantic Models for Finance Guru™

This module defines type-safe data structures for momentum indicator calculations.
All models use Pydantic for automatic validation and type checking.

ARCHITECTURE NOTE:
These models represent Layer 1 of our 3-layer architecture:
    Layer 1: Pydantic Models (THIS FILE) - Data validation
    Layer 2: Calculator Classes - Business logic
    Layer 3: CLI Interface - Agent integration

EDUCATIONAL CONTEXT:
Momentum indicators measure the speed and strength of price movements.
They help identify:
- Overbought/oversold conditions (RSI, Stochastic, Williams %R)
- Trend changes (MACD)
- Velocity of price changes (ROC)

These are critical for timing entry/exit points in trading strategies.

Author: Finance Guru™ Development Team
Created: 2025-10-13
"""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class MomentumDataInput(BaseModel):
    """
    Price data for momentum indicator calculations.

    WHAT: Container for OHLCV (Open, High, Low, Close, Volume) data
    WHY: Momentum indicators need price history to calculate trends
    VALIDATES:
        - All prices are positive
        - High >= Low (basic price logic)
        - Dates are chronologically sorted
        - Minimum data points for calculations
        - All arrays have equal length

    EDUCATIONAL NOTE:
    Different momentum indicators use different price data:
    - RSI: Close prices only
    - MACD: Close prices only
    - Stochastic: High, Low, Close prices
    - Williams %R: High, Low, Close prices
    - ROC: Close prices only

    We include all OHLC data for flexibility.
    """

    ticker: str = Field(
        ...,
        description="Stock ticker symbol (e.g., 'TSLA', 'AAPL')",
        min_length=1,
        max_length=10,
        pattern=r"^[A-Z]+$",
    )

    dates: list[date] = Field(
        ...,
        description="Trading dates in chronological order",
        min_length=14,  # Minimum for RSI with 14-day period
    )

    close: list[float] = Field(
        ...,
        description="Closing prices (required for all indicators)",
        min_length=14,
    )

    high: list[float] | None = Field(
        default=None,
        description="High prices (required for Stochastic, Williams %R)",
    )

    low: list[float] | None = Field(
        default=None,
        description="Low prices (required for Stochastic, Williams %R)",
    )

    volume: list[float] | None = Field(
        default=None,
        description="Trading volume (optional, for future volume indicators)",
    )

    @field_validator("close", "high", "low", "volume")
    @classmethod
    def prices_must_be_positive(cls, v: list[float] | None) -> list[float] | None:
        """
        Ensure all prices are positive.

        WHY: Negative prices indicate data errors.
        Zero prices indicate delisted securities or missing data.
        """
        if v is None:
            return v

        if any(price <= 0 for price in v):
            raise ValueError(
                "All prices must be positive. Found zero or negative price. "
                "Check your data source for errors."
            )
        return v

    @field_validator("dates")
    @classmethod
    def dates_must_be_sorted(cls, v: list[date]) -> list[date]:
        """
        Ensure dates are chronologically ordered.

        WHY: Momentum calculations assume sequential time-series data.
        Out-of-order dates produce incorrect indicator values.
        """
        if v != sorted(v):
            raise ValueError(
                "Dates must be in chronological order (earliest to latest). "
                "Sort your data before creating MomentumDataInput."
            )
        return v

    @model_validator(mode="after")
    def validate_data_alignment(self) -> "MomentumDataInput":
        """
        Ensure all price arrays have the same length as dates.

        WHY: Each date needs corresponding price data.
        Misalignment causes index errors in calculations.
        """
        n_dates = len(self.dates)

        # Close is required, must match dates length
        if len(self.close) != n_dates:
            raise ValueError(
                f"Close prices length ({len(self.close)}) must match dates length ({n_dates})"
            )

        # High and Low are optional but must match if provided
        if self.high is not None and len(self.high) != n_dates:
            raise ValueError(
                f"High prices length ({len(self.high)}) must match dates length ({n_dates})"
            )

        if self.low is not None and len(self.low) != n_dates:
            raise ValueError(
                f"Low prices length ({len(self.low)}) must match dates length ({n_dates})"
            )

        if self.volume is not None and len(self.volume) != n_dates:
            raise ValueError(
                f"Volume length ({len(self.volume)}) must match dates length ({n_dates})"
            )

        return self

    @model_validator(mode="after")
    def validate_high_low_relationship(self) -> "MomentumDataInput":
        """
        Ensure High >= Low for each day.

        WHY: High price cannot be lower than Low price.
        This is a fundamental market data constraint.
        """
        if self.high is not None and self.low is not None:
            for i, (h, l) in enumerate(zip(self.high, self.low)):
                if h < l:
                    raise ValueError(
                        f"High price ({h}) is less than Low price ({l}) at index {i} "
                        f"(date: {self.dates[i]}). This is invalid market data."
                    )
        return self

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "ticker": "TSLA",
                    "dates": ["2025-09-01", "2025-09-02", "2025-09-03"],
                    "close": [250.0, 252.5, 248.0],
                    "high": [252.0, 254.0, 250.0],
                    "low": [248.0, 251.0, 246.0],
                    "volume": [1000000, 1200000, 900000]
                }
            ]
        }
    }


class MomentumConfig(BaseModel):
    """
    Configuration for momentum indicator calculations.

    WHAT: Standard parameters for momentum indicators
    WHY: Ensures consistent calculations across agents
    USE CASES:
        - Market Researcher: Standard settings for quick scans
        - Quant Analyst: Custom periods for strategy testing
        - Strategy Advisor: Optimized periods for specific timeframes

    EDUCATIONAL NOTE:
    Different period lengths serve different purposes:
    - Short periods (5-10): More sensitive, more signals, more noise
    - Standard periods (14): Industry standard, balanced
    - Long periods (20-30): Less sensitive, fewer signals, smoother
    """

    rsi_period: int = Field(
        default=14,
        ge=2,
        le=100,
        description="RSI period (default: 14 days, industry standard)",
    )

    macd_fast: int = Field(
        default=12,
        ge=5,
        le=50,
        description="MACD fast EMA period (default: 12 days)",
    )

    macd_slow: int = Field(
        default=26,
        ge=10,
        le=100,
        description="MACD slow EMA period (default: 26 days)",
    )

    macd_signal: int = Field(
        default=9,
        ge=5,
        le=50,
        description="MACD signal line period (default: 9 days)",
    )

    stoch_k_period: int = Field(
        default=14,
        ge=5,
        le=100,
        description="Stochastic %K period (default: 14 days)",
    )

    stoch_d_period: int = Field(
        default=3,
        ge=2,
        le=20,
        description="Stochastic %D smoothing period (default: 3 days)",
    )

    williams_period: int = Field(
        default=14,
        ge=5,
        le=100,
        description="Williams %R period (default: 14 days)",
    )

    roc_period: int = Field(
        default=12,
        ge=1,
        le=100,
        description="Rate of Change period (default: 12 days)",
    )

    @model_validator(mode="after")
    def validate_macd_periods(self) -> "MomentumConfig":
        """
        Ensure MACD fast < slow for proper convergence/divergence.

        WHY: MACD measures the difference between fast and slow EMAs.
        If fast >= slow, the indicator doesn't work properly.
        """
        if self.macd_fast >= self.macd_slow:
            raise ValueError(
                f"MACD fast period ({self.macd_fast}) must be less than "
                f"slow period ({self.macd_slow})"
            )
        return self

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "rsi_period": 14,
                    "macd_fast": 12,
                    "macd_slow": 26,
                    "macd_signal": 9,
                    "stoch_k_period": 14,
                    "stoch_d_period": 3,
                    "williams_period": 14,
                    "roc_period": 12
                }
            ]
        }
    }


class RSIOutput(BaseModel):
    """
    Relative Strength Index output.

    WHAT: Measures momentum on 0-100 scale
    WHY: Identifies overbought/oversold conditions
    INTERPRETATION:
        - RSI > 70: Overbought (potential sell signal)
        - RSI < 30: Oversold (potential buy signal)
        - RSI = 50: Neutral momentum

    EDUCATIONAL NOTE:
    RSI was developed by J. Welles Wilder in 1978.
    It's one of the most popular momentum indicators.
    The 70/30 levels are traditional but can be adjusted:
    - Strong trends: Use 80/20
    - Range-bound: Use 70/30
    - Weak trends: Use 60/40
    """

    ticker: str
    calculation_date: date
    current_rsi: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Current RSI value (0-100 scale)"
    )
    rsi_signal: Literal["overbought", "oversold", "neutral"] = Field(
        ...,
        description="Signal interpretation based on traditional 70/30 levels"
    )
    period: int = Field(..., description="Period used for calculation")

    @field_validator("current_rsi")
    @classmethod
    def validate_rsi_range(cls, v: float) -> float:
        """RSI must be between 0 and 100 by mathematical definition."""
        if not (0 <= v <= 100):
            raise ValueError(f"RSI must be between 0 and 100, got {v}")
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "ticker": "TSLA",
                "calculation_date": "2025-10-13",
                "current_rsi": 68.5,
                "rsi_signal": "neutral",
                "period": 14
            }]
        }
    }


class MACDOutput(BaseModel):
    """
    MACD (Moving Average Convergence Divergence) output.

    WHAT: Trend-following momentum indicator
    WHY: Shows relationship between two moving averages
    INTERPRETATION:
        - MACD > Signal: Bullish (upward momentum)
        - MACD < Signal: Bearish (downward momentum)
        - Histogram positive: Increasing bullish momentum
        - Histogram negative: Increasing bearish momentum

    EDUCATIONAL NOTE:
    MACD was developed by Gerald Appel in the 1970s.
    Three components:
    1. MACD Line: Fast EMA - Slow EMA
    2. Signal Line: EMA of MACD Line
    3. Histogram: MACD - Signal (visual representation)

    Look for:
    - Crossovers: MACD crossing signal line
    - Divergences: Price making new highs/lows but MACD isn't
    """

    ticker: str
    calculation_date: date
    macd_line: float = Field(..., description="MACD line (fast EMA - slow EMA)")
    signal_line: float = Field(..., description="Signal line (EMA of MACD)")
    histogram: float = Field(..., description="MACD - Signal (momentum strength)")
    signal: Literal["bullish", "bearish"] = Field(
        ...,
        description="Signal based on MACD vs Signal line relationship"
    )
    fast_period: int
    slow_period: int
    signal_period: int

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "ticker": "TSLA",
                "calculation_date": "2025-10-13",
                "macd_line": 2.35,
                "signal_line": 1.80,
                "histogram": 0.55,
                "signal": "bullish",
                "fast_period": 12,
                "slow_period": 26,
                "signal_period": 9
            }]
        }
    }


class StochasticOutput(BaseModel):
    """
    Stochastic Oscillator output.

    WHAT: Compares closing price to price range over time
    WHY: Identifies momentum and potential reversals
    INTERPRETATION:
        - %K > 80: Overbought
        - %K < 20: Oversold
        - %K crosses above %D: Bullish signal
        - %K crosses below %D: Bearish signal

    EDUCATIONAL NOTE:
    Developed by George Lane in the 1950s.
    The premise: In uptrends, prices close near the high.
    In downtrends, prices close near the low.

    Two lines:
    - %K: Fast stochastic (current momentum)
    - %D: Slow stochastic (smoothed %K, signal line)
    """

    ticker: str
    calculation_date: date
    k_value: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="%K value (fast stochastic)"
    )
    d_value: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="%D value (slow stochastic)"
    )
    signal: Literal["overbought", "oversold", "neutral"] = Field(
        ...,
        description="Signal based on 80/20 levels"
    )
    k_period: int
    d_period: int

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "ticker": "TSLA",
                "calculation_date": "2025-10-13",
                "k_value": 72.5,
                "d_value": 68.3,
                "signal": "neutral",
                "k_period": 14,
                "d_period": 3
            }]
        }
    }


class WilliamsROutput(BaseModel):
    """
    Williams %R output.

    WHAT: Momentum indicator measuring overbought/oversold
    WHY: Similar to Stochastic but with inverted scale
    INTERPRETATION:
        - %R > -20: Overbought (sell signal)
        - %R < -80: Oversold (buy signal)
        - %R between -20 and -80: Neutral

    EDUCATIONAL NOTE:
    Developed by Larry Williams in 1966.
    Similar to Stochastic but inverted (ranges from 0 to -100).
    Some traders prefer Williams %R because:
    - Inverted scale matches psychological "oversold" concept
    - More responsive to recent price changes
    - Works well in trending markets
    """

    ticker: str
    calculation_date: date
    williams_r: float = Field(
        ...,
        ge=-100.0,
        le=0.0,
        description="Williams %R value (-100 to 0 scale)"
    )
    signal: Literal["overbought", "oversold", "neutral"] = Field(
        ...,
        description="Signal based on -20/-80 levels"
    )
    period: int

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "ticker": "TSLA",
                "calculation_date": "2025-10-13",
                "williams_r": -35.2,
                "signal": "neutral",
                "period": 14
            }]
        }
    }


class ROCOutput(BaseModel):
    """
    Rate of Change output.

    WHAT: Measures percentage change over a period
    WHY: Shows velocity of price changes (momentum strength)
    INTERPRETATION:
        - ROC > 0: Price increasing (bullish momentum)
        - ROC < 0: Price decreasing (bearish momentum)
        - ROC = 0: No change (neutral)
        - Large positive ROC: Strong upward momentum
        - Large negative ROC: Strong downward momentum

    EDUCATIONAL NOTE:
    ROC is one of the simplest momentum indicators.
    Formula: ROC = ((Close - Close_n_periods_ago) / Close_n_periods_ago) * 100

    Advantages:
    - Easy to understand (just % change)
    - No complex smoothing
    - Clear momentum direction

    Disadvantages:
    - Can be choppy (no smoothing)
    - Sensitive to outliers
    """

    ticker: str
    calculation_date: date
    roc: float = Field(..., description="Rate of Change percentage")
    signal: Literal["bullish", "bearish", "neutral"] = Field(
        ...,
        description="Signal based on positive/negative ROC"
    )
    period: int

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "ticker": "TSLA",
                "calculation_date": "2025-10-13",
                "roc": 8.5,
                "signal": "bullish",
                "period": 12
            }]
        }
    }


class AllMomentumOutput(BaseModel):
    """
    Combined output for all momentum indicators.

    WHAT: All momentum indicators in one validated structure
    WHY: Convenient for comprehensive momentum analysis
    USE CASES:
        - Strategy Advisor: Compare multiple signals
        - Quant Analyst: Build composite indicators
        - Market Researcher: Quick momentum overview
    """

    ticker: str
    calculation_date: date
    rsi: RSIOutput
    macd: MACDOutput
    stochastic: StochasticOutput
    williams_r: WilliamsROutput
    roc: ROCOutput

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "ticker": "TSLA",
                "calculation_date": "2025-10-13",
                "rsi": {
                    "ticker": "TSLA",
                    "calculation_date": "2025-10-13",
                    "current_rsi": 68.5,
                    "rsi_signal": "neutral",
                    "period": 14
                },
                "macd": {
                    "ticker": "TSLA",
                    "calculation_date": "2025-10-13",
                    "macd_line": 2.35,
                    "signal_line": 1.80,
                    "histogram": 0.55,
                    "signal": "bullish",
                    "fast_period": 12,
                    "slow_period": 26,
                    "signal_period": 9
                },
                "stochastic": {
                    "ticker": "TSLA",
                    "calculation_date": "2025-10-13",
                    "k_value": 72.5,
                    "d_value": 68.3,
                    "signal": "neutral",
                    "k_period": 14,
                    "d_period": 3
                },
                "williams_r": {
                    "ticker": "TSLA",
                    "calculation_date": "2025-10-13",
                    "williams_r": -35.2,
                    "signal": "neutral",
                    "period": 14
                },
                "roc": {
                    "ticker": "TSLA",
                    "calculation_date": "2025-10-13",
                    "roc": 8.5,
                    "signal": "bullish",
                    "period": 12
                }
            }]
        }
    }


# Type exports
__all__ = [
    "MomentumDataInput",
    "MomentumConfig",
    "RSIOutput",
    "MACDOutput",
    "StochasticOutput",
    "WilliamsROutput",
    "ROCOutput",
    "AllMomentumOutput",
]
