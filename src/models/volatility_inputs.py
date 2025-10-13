"""
Pydantic models for volatility metrics calculations.

WHAT: Data models for volatility indicator inputs, configuration, and outputs
WHY: Type-safe, validated data structures for Finance Guru agents
ARCHITECTURE: Layer 1 of 3-layer type-safe architecture

Used by: Compliance Officer, Margin Specialist, Risk Assessment workflows
"""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class VolatilityDataInput(BaseModel):
    """
    WHAT: Historical price data for volatility calculations
    WHY: Ensures valid OHLC data before running volatility indicators
    VALIDATES:
      - Prices are positive
      - Dates are chronological
      - Sufficient data points for calculations

    EDUCATIONAL NOTE:
    Volatility indicators need more than just closing prices. They use:
    - High: The highest price during the trading day
    - Low: The lowest price during the trading day
    - Close: The final price at market close

    This gives a complete picture of price movement throughout each day.
    """

    ticker: str = Field(..., description="Stock ticker symbol (e.g., 'TSLA')")
    dates: list[date] = Field(..., min_length=20, description="Trading dates (min 20 days)")
    high: list[float] = Field(..., min_length=20, description="Daily high prices")
    low: list[float] = Field(..., min_length=20, description="Daily low prices")
    close: list[float] = Field(..., min_length=20, description="Daily closing prices")

    @field_validator('high', 'low', 'close')
    @classmethod
    def prices_must_be_positive(cls, v: list[float]) -> list[float]:
        """Validate all prices are positive numbers."""
        if any(price <= 0 for price in v):
            raise ValueError('All prices must be positive')
        return v

    @field_validator('dates')
    @classmethod
    def dates_must_be_sorted(cls, v: list[date]) -> list[date]:
        """Validate dates are in chronological order."""
        if v != sorted(v):
            raise ValueError('Dates must be in chronological order')
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "ticker": "TSLA",
                "dates": ["2025-10-10", "2025-10-11", "2025-10-12"],
                "high": [252.5, 255.0, 253.0],
                "low": [248.0, 250.0, 249.0],
                "close": [250.0, 252.5, 251.0]
            }]
        }
    }


class VolatilityConfig(BaseModel):
    """
    WHAT: Configuration for volatility indicator calculations
    WHY: Standardizes volatility calculations across all Finance Guru agents

    EDUCATIONAL NOTE:
    - Bollinger Bands: Show price channels (typically 2 std devs from moving avg)
    - ATR: Measures average price range over N periods
    - Keltner Channels: Like Bollinger but uses ATR instead of std dev

    These periods (14, 20) are industry standards but can be customized.
    """

    # Bollinger Bands settings
    bb_period: int = Field(
        default=20,
        ge=10,
        le=50,
        description="Bollinger Bands moving average period (default: 20)"
    )
    bb_std_dev: float = Field(
        default=2.0,
        ge=1.0,
        le=3.0,
        description="Bollinger Bands standard deviation multiplier (default: 2.0)"
    )

    # Average True Range (ATR) settings
    atr_period: int = Field(
        default=14,
        ge=7,
        le=30,
        description="ATR calculation period (default: 14)"
    )

    # Historical Volatility settings
    hvol_period: int = Field(
        default=20,
        ge=10,
        le=90,
        description="Historical volatility lookback period (default: 20)"
    )
    hvol_annualization_factor: int = Field(
        default=252,
        ge=200,
        le=365,
        description="Trading days per year for annualization (default: 252)"
    )

    # Keltner Channels settings
    kc_period: int = Field(
        default=20,
        ge=10,
        le=50,
        description="Keltner Channels EMA period (default: 20)"
    )
    kc_atr_multiplier: float = Field(
        default=2.0,
        ge=1.0,
        le=3.0,
        description="Keltner Channels ATR multiplier (default: 2.0)"
    )


class BollingerBandsOutput(BaseModel):
    """
    WHAT: Bollinger Bands calculation results
    WHY: Provides price volatility channels for position sizing

    EDUCATIONAL NOTE:
    - Middle Band: Simple moving average (the "fair value" line)
    - Upper Band: Middle + (2 × standard deviation) - "expensive" zone
    - Lower Band: Middle - (2 × standard deviation) - "cheap" zone
    - %B: Where current price sits within the bands (0.5 = middle, 1.0 = upper, 0 = lower)
    - Bandwidth: How wide the bands are (wider = more volatile)

    USE CASE: When %B > 1.0, price is above upper band (overbought signal)
    """

    middle_band: float = Field(..., description="Simple moving average (middle band)")
    upper_band: float = Field(..., description="Upper Bollinger Band")
    lower_band: float = Field(..., description="Lower Bollinger Band")
    percent_b: float = Field(..., description="%B indicator (position within bands)")
    bandwidth: float = Field(..., ge=0.0, description="Band width as % of middle")


class ATROutput(BaseModel):
    """
    WHAT: Average True Range calculation results
    WHY: Measures absolute volatility for stop-loss and position sizing

    EDUCATIONAL NOTE:
    ATR tells you the average price range over the last N days.

    Example: If TSLA has ATR of $8.50, on a typical day it moves $8.50 from high to low.

    USE CASES:
    - Stop Loss: Set stops at 2× ATR below entry (gives room for normal volatility)
    - Position Size: Higher ATR = smaller position (more volatile = more risk)
    - Breakout Confirmation: High ATR = strong move, low ATR = weak move
    """

    atr: float = Field(..., ge=0.0, description="Average True Range value")
    atr_percent: float = Field(..., ge=0.0, description="ATR as % of current price")


class HistoricalVolatilityOutput(BaseModel):
    """
    WHAT: Historical volatility calculation (standard deviation of returns)
    WHY: Annualized volatility measure for risk assessment

    EDUCATIONAL NOTE:
    This is the same "annual volatility" from your Risk Metrics tool, but calculated
    using a rolling window to see current volatility conditions.

    20% volatility means: Expected annual price swing is ±20% (assuming normal distribution)
    40% volatility means: Expected annual price swing is ±40% (high risk/reward)

    USE CASE: Compare to historical averages - is current vol high or low?
    """

    daily_volatility: float = Field(..., ge=0.0, description="Daily volatility (std dev)")
    annual_volatility: float = Field(..., ge=0.0, description="Annualized volatility")


class KeltnerChannelsOutput(BaseModel):
    """
    WHAT: Keltner Channels calculation results
    WHY: ATR-based volatility channels (alternative to Bollinger Bands)

    EDUCATIONAL NOTE:
    Similar to Bollinger Bands but uses ATR instead of standard deviation.
    - More responsive to actual price movement
    - Less susceptible to volatility squeezes
    - Better for trending markets

    Traders often use BOTH:
    - Price outside Bollinger but inside Keltner = normal volatility move
    - Price outside BOTH = extreme move (strong signal)
    """

    middle_line: float = Field(..., description="EMA (middle line)")
    upper_channel: float = Field(..., description="Upper Keltner Channel")
    lower_channel: float = Field(..., description="Lower Keltner Channel")


class VolatilityMetricsOutput(BaseModel):
    """
    WHAT: Complete volatility analysis output for all indicators
    WHY: Provides comprehensive volatility profile for position sizing and risk decisions

    AGENT USE CASES:
    - Compliance Officer: Uses bandwidth and ATR% to set position limits
    - Margin Specialist: Uses historical vol to determine max leverage
    - Strategy Advisor: Uses %B and channel position to time entries
    """

    ticker: str
    calculation_date: date
    current_price: float = Field(..., gt=0.0, description="Latest closing price")

    # Individual indicator outputs
    bollinger_bands: BollingerBandsOutput
    atr: ATROutput
    historical_volatility: HistoricalVolatilityOutput
    keltner_channels: KeltnerChannelsOutput

    # Summary metrics
    volatility_regime: Literal["low", "normal", "high", "extreme"] = Field(
        ...,
        description="Overall volatility assessment"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "ticker": "TSLA",
                "calculation_date": "2025-10-13",
                "current_price": 250.00,
                "bollinger_bands": {
                    "middle_band": 245.00,
                    "upper_band": 265.00,
                    "lower_band": 225.00,
                    "percent_b": 0.25,
                    "bandwidth": 16.33
                },
                "atr": {
                    "atr": 8.50,
                    "atr_percent": 3.40
                },
                "historical_volatility": {
                    "daily_volatility": 0.0215,
                    "annual_volatility": 0.342
                },
                "keltner_channels": {
                    "middle_line": 245.00,
                    "upper_channel": 262.00,
                    "lower_channel": 228.00
                },
                "volatility_regime": "normal"
            }]
        }
    }
