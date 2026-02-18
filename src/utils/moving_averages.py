"""Moving Average Calculator for Finance Guru™.

This module implements comprehensive moving average calculations using validated
Pydantic models. All calculations follow industry-standard technical analysis formulas.

ARCHITECTURE NOTE:
This is Layer 2 of our 3-layer architecture:
    Layer 1: Pydantic Models - Data validation (moving_avg_inputs.py)
    Layer 2: Calculator Classes (THIS FILE) - Business logic
    Layer 3: CLI Interface - Agent integration

EDUCATIONAL CONTEXT:
Moving averages are the foundation of technical analysis. They:
- Smooth price data to identify trends
- Act as dynamic support/resistance levels
- Generate trading signals through crossovers
- Reduce noise in volatile markets

Four types implemented:
1. SMA (Simple Moving Average) - Equal weight, easy to understand
2. EMA (Exponential Moving Average) - More weight to recent prices
3. WMA (Weighted Moving Average) - Linear increasing weights
4. HMA (Hull Moving Average) - Smoothest with least lag

INDICATORS IMPLEMENTED:
1. All four MA types with configurable periods
2. Crossover detection (Golden Cross/Death Cross)
3. Trend identification (price vs MA position)
4. Full MA series output for charting

Author: Finance Guru™ Development Team
Created: 2025-10-13
"""

from datetime import date
from typing import Literal

import numpy as np
import pandas as pd

from src.models.moving_avg_inputs import (
    CrossoverOutput,
    MovingAverageAnalysis,
    MovingAverageConfig,
    MovingAverageDataInput,
    MovingAverageOutput,
)


class MovingAverageCalculator:
    """Comprehensive moving average calculator.

    WHAT: Calculates all major moving average types for Finance Guru agents
    WHY: Provides validated, type-safe trend analysis for trading decisions
    HOW: Uses Pydantic models for I/O, pandas/numpy for calculations

    USAGE EXAMPLE:
        # Create configuration
        config = MovingAverageConfig(
            ma_type="SMA",
            period=50,
            secondary_ma_type="SMA",
            secondary_period=200
        )

        # Create calculator
        calculator = MovingAverageCalculator(config)

        # Calculate single MA
        ma_result = calculator.calculate_ma(data)

        # Calculate with crossover
        full_analysis = calculator.calculate_with_crossover(data)
    """

    def __init__(self, config: MovingAverageConfig):
        """Initialize calculator with configuration.

        Args:
            config: Validated configuration (Pydantic model ensures correctness)

        EDUCATIONAL NOTE:
        By accepting a Pydantic model, we KNOW the config is valid.
        We don't need to check if periods are positive or if crossover config is correct.
        Pydantic already validated everything.
        """
        self.config = config

    def calculate_sma(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate Simple Moving Average.

        WHAT: Average of last N prices
        WHY: Smooths price data, identifies trend direction
        HOW: Sum last N prices, divide by N

        FORMULA:
            SMA = (P1 + P2 + ... + Pn) / n

        INTERPRETATION:
            - Equal weight to all prices in period
            - Most basic and widely understood MA
            - Good for identifying clear trends
            - Lags price action more than EMA/WMA

        EDUCATIONAL NOTE:
        SMA advantages:
        - Simple to calculate and understand
        - Smooth, reliable trend indication
        - Less prone to false signals (whipsaws)

        SMA disadvantages:
        - Slower to react to price changes
        - Can lag significantly in volatile markets
        - Old data has same weight as recent data

        Args:
            prices: Price series
            period: Number of days for average

        Returns:
            pd.Series: SMA values (NaN for first period-1 values)
        """
        return prices.rolling(window=period).mean()

    def calculate_ema(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average.

        WHAT: Weighted average giving more importance to recent prices
        WHY: More responsive to recent price changes than SMA
        HOW: Uses exponential weighting factor (smoothing)

        FORMULA:
            EMA_today = (Price_today × α) + (EMA_yesterday × (1 - α))

            where α (smoothing factor) = 2 / (period + 1)

        INTERPRETATION:
            - Recent prices have more impact
            - Responds faster to price changes
            - Popular among day traders
            - Can generate more signals (good and false)

        EDUCATIONAL NOTE:
        EMA advantages:
        - More responsive to recent changes
        - Reduces lag compared to SMA
        - Better for volatile markets
        - Used in MACD indicator

        EMA disadvantages:
        - More complex calculation
        - Can generate false signals in choppy markets
        - More prone to whipsaws

        COMMON PERIODS:
        - 12/26: MACD components
        - 20: Short-term trend
        - 50: Intermediate trend
        - 200: Long-term trend

        Args:
            prices: Price series
            period: Number of days for EMA

        Returns:
            pd.Series: EMA values
        """
        return prices.ewm(span=period, adjust=False).mean()

    def calculate_wma(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate Weighted Moving Average.

        WHAT: Average with linearly increasing weights
        WHY: Balances responsiveness and smoothness
        HOW: Most recent price gets highest weight, oldest gets weight of 1

        FORMULA:
            WMA = (P1×1 + P2×2 + P3×3 + ... + Pn×n) / (1+2+3+...+n)

            where:
            - P1 is oldest price (weight = 1)
            - Pn is newest price (weight = n)
            - Denominator is sum of weights = n(n+1)/2

        INTERPRETATION:
            - Recent prices matter more (but not exponentially)
            - Smoother than EMA, faster than SMA
            - Good compromise between SMA and EMA
            - Less common but useful for intermediate timeframes

        EDUCATIONAL NOTE:
        WMA advantages:
        - More responsive than SMA
        - Smoother than EMA
        - Intuitive linear weighting
        - Good for swing trading

        WMA disadvantages:
        - More complex than SMA
        - Less popular (fewer traders watching it)
        - Still lags in fast markets

        COMPARISON:
        For 5-day period with prices [10, 11, 12, 13, 14]:
        - SMA: (10+11+12+13+14)/5 = 12.0
        - WMA: (10×1 + 11×2 + 12×3 + 13×4 + 14×5) / 15 = 12.67
        (WMA higher because recent prices weighted more)

        Args:
            prices: Price series
            period: Number of days for WMA

        Returns:
            pd.Series: WMA values
        """
        # Create weight array: [1, 2, 3, ..., period]
        weights = np.arange(1, period + 1)

        # Calculate weighted sum using rolling window
        def weighted_mean(window):
            return np.dot(window, weights) / weights.sum()

        return prices.rolling(window=period).apply(weighted_mean, raw=True)

    def calculate_hma(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate Hull Moving Average.

        WHAT: Advanced MA with minimal lag and maximum smoothness
        WHY: Eliminates lag while maintaining smoothness
        HOW: Uses nested WMAs to reduce lag, then smooths result

        FORMULA:
            HMA = WMA(2×WMA(period/2) - WMA(period), sqrt(period))

        INTERPRETATION:
            - Smoothest MA with least lag
            - Best trend indicator for fast markets
            - Excellent for dynamic support/resistance
            - Requires more data than other MAs

        EDUCATIONAL NOTE:
        HMA advantages:
        - Minimal lag (responds quickly)
        - Maximum smoothness (filters noise)
        - Best of both worlds (responsive + smooth)
        - Excellent for trend identification

        HMA disadvantages:
        - Complex calculation
        - Less widely known/used
        - Requires more data points
        - Can overshoot in some conditions

        HOW IT WORKS:
        1. Calculate WMA of half-period: WMA(n/2)
        2. Calculate WMA of full period: WMA(n)
        3. Double the half-period WMA: 2×WMA(n/2)
        4. Subtract full-period WMA: 2×WMA(n/2) - WMA(n)
        5. Smooth result with WMA of sqrt(n)

        This eliminates lag from step 4, then smooths in step 5.

        DISCOVERED BY:
        Alan Hull in 2005. Designed specifically to solve the
        "lag vs smoothness" tradeoff in moving averages.

        Args:
            prices: Price series
            period: Number of days for HMA

        Returns:
            pd.Series: HMA values
        """
        # Calculate half-period and sqrt-period
        half_period = period // 2
        sqrt_period = int(np.sqrt(period))

        # Step 1: WMA of half period
        wma_half = self.calculate_wma(prices, half_period)

        # Step 2: WMA of full period
        wma_full = self.calculate_wma(prices, period)

        # Step 3-4: 2×WMA(n/2) - WMA(n)
        raw_hma = 2 * wma_half - wma_full

        # Step 5: Smooth with WMA of sqrt(n)
        hma = self.calculate_wma(raw_hma, sqrt_period)

        return hma

    def calculate_ma(self, data: MovingAverageDataInput) -> MovingAverageOutput:
        """Calculate primary moving average.

        WHAT: Calculate specified MA type for given data
        WHY: Provides trend analysis and support/resistance levels
        HOW: Routes to appropriate MA calculation method

        Args:
            data: Historical price data (validated by Pydantic)

        Returns:
            MovingAverageOutput: MA values and analysis

        Raises:
            ValueError: If insufficient data for calculation
        """
        prices = pd.Series(data.prices, index=data.dates)

        # Verify sufficient data
        min_required = self.config.period
        if self.config.ma_type == "HMA":
            # HMA needs more data due to nested calculations
            min_required = self.config.period + int(np.sqrt(self.config.period))

        if len(prices) < min_required:
            raise ValueError(
                f"Need at least {min_required} data points for {self.config.ma_type}"
                f"({self.config.period}), got {len(prices)}"
            )

        # Calculate appropriate MA type
        if self.config.ma_type == "SMA":
            ma_series = self.calculate_sma(prices, self.config.period)
        elif self.config.ma_type == "EMA":
            ma_series = self.calculate_ema(prices, self.config.period)
        elif self.config.ma_type == "WMA":
            ma_series = self.calculate_wma(prices, self.config.period)
        else:  # HMA
            ma_series = self.calculate_hma(prices, self.config.period)

        # Get current values
        current_ma = float(ma_series.iloc[-1])
        current_price = float(prices.iloc[-1])

        # Determine price vs MA position
        price_diff_pct = ((current_price - current_ma) / current_ma) * 100
        if abs(price_diff_pct) < 0.1:  # Within 0.1%
            price_vs_ma: Literal["ABOVE", "BELOW", "AT"] = "AT"
        elif current_price > current_ma:
            price_vs_ma = "ABOVE"
        else:
            price_vs_ma = "BELOW"

        return MovingAverageOutput(
            ticker=data.ticker,
            calculation_date=data.dates[-1],
            ma_type=self.config.ma_type,
            period=self.config.period,
            current_value=current_ma,
            current_price=current_price,
            price_vs_ma=price_vs_ma,
            ma_values=ma_series.dropna().tolist(),
        )

    def detect_crossover(
        self,
        fast_ma: pd.Series,
        slow_ma: pd.Series,
        dates: list,
    ) -> tuple[str, date | None, int | None]:
        """Detect MA crossover and determine signal.

        WHAT: Identifies when fast MA crosses slow MA
        WHY: Crossovers are powerful trading signals
        HOW: Compares current/previous positions of MAs

        LOGIC:
            - Fast > Slow AND was Fast <= Slow yesterday: BULLISH (Golden Cross)
            - Fast < Slow AND was Fast >= Slow yesterday: BEARISH (Death Cross)
            - Otherwise: NEUTRAL (no recent crossover)

        Args:
            fast_ma: Fast (shorter period) MA series
            slow_ma: Slow (longer period) MA series
            dates: Date series

        Returns:
            tuple: (signal, last_crossover_date, days_since_crossover)
        """
        # Get current relationship
        current_fast = fast_ma.iloc[-1]
        current_slow = slow_ma.iloc[-1]

        # Find most recent crossover
        last_crossover_date = None
        days_since = None

        # Look back through history for crossovers
        # A crossover occurs when the relationship changes
        for i in range(len(fast_ma) - 1, 0, -1):
            if pd.isna(fast_ma.iloc[i]) or pd.isna(slow_ma.iloc[i]):
                continue
            if pd.isna(fast_ma.iloc[i - 1]) or pd.isna(slow_ma.iloc[i - 1]):
                continue

            # Check if relationship changed (crossover)
            current_relationship = fast_ma.iloc[i] > slow_ma.iloc[i]
            previous_relationship = fast_ma.iloc[i - 1] > slow_ma.iloc[i - 1]

            if current_relationship != previous_relationship:
                # Found most recent crossover
                last_crossover_date = dates[i]
                days_since = len(dates) - 1 - i
                break

        # Determine current signal
        if current_fast > current_slow:
            signal = "BULLISH"
        elif current_fast < current_slow:
            signal = "BEARISH"
        else:
            signal = "NEUTRAL"

        return signal, last_crossover_date, days_since

    def calculate_with_crossover(
        self, data: MovingAverageDataInput
    ) -> MovingAverageAnalysis:
        """Calculate MAs with crossover analysis.

        WHAT: Calculate two MAs and analyze their crossover
        WHY: Crossovers provide actionable trading signals
        HOW: Calculate both MAs, compare positions, detect crossovers

        EDUCATIONAL NOTE:
        Famous crossover strategies:
        - 50/200 SMA: Golden Cross/Death Cross (institutional favorite)
        - 20/50 SMA: Intermediate trend changes
        - 10/30 EMA: Short-term trading signals
        - 12/26 EMA: Used in MACD indicator

        Args:
            data: Historical price data

        Returns:
            MovingAverageAnalysis: Complete analysis with crossover signals

        Raises:
            ValueError: If crossover config not provided or insufficient data
        """
        if self.config.secondary_ma_type is None:
            raise ValueError(
                "Crossover analysis requires secondary_ma_type and secondary_period "
                "in configuration. Use calculate_ma() for single MA analysis."
            )

        prices = pd.Series(data.prices, index=data.dates)

        # Calculate primary MA
        primary_output = self.calculate_ma(data)

        # Calculate secondary MA
        if self.config.secondary_ma_type == "SMA":
            secondary_ma = self.calculate_sma(prices, self.config.secondary_period)
        elif self.config.secondary_ma_type == "EMA":
            secondary_ma = self.calculate_ema(prices, self.config.secondary_period)
        elif self.config.secondary_ma_type == "WMA":
            secondary_ma = self.calculate_wma(prices, self.config.secondary_period)
        else:  # HMA
            secondary_ma = self.calculate_hma(prices, self.config.secondary_period)

        # Determine which is fast/slow
        if self.config.period < self.config.secondary_period:
            fast_ma = pd.Series(
                primary_output.ma_values,
                index=data.dates[-len(primary_output.ma_values) :],
            )
            slow_ma = secondary_ma
            fast_is_primary = True
        else:
            fast_ma = secondary_ma
            slow_ma = pd.Series(
                primary_output.ma_values,
                index=data.dates[-len(primary_output.ma_values) :],
            )
            fast_is_primary = False

        # Create secondary output
        secondary_output = MovingAverageOutput(
            ticker=data.ticker,
            calculation_date=data.dates[-1],
            ma_type=self.config.secondary_ma_type,
            period=self.config.secondary_period,
            current_value=float(secondary_ma.iloc[-1]),
            current_price=float(prices.iloc[-1]),
            price_vs_ma="ABOVE"
            if float(prices.iloc[-1]) > float(secondary_ma.iloc[-1])
            else "BELOW",
            ma_values=secondary_ma.dropna().tolist(),
        )

        # Detect crossover
        # Align series for comparison
        min_length = min(len(fast_ma.dropna()), len(slow_ma.dropna()))
        fast_aligned = fast_ma.dropna().iloc[-min_length:]
        slow_aligned = slow_ma.dropna().iloc[-min_length:]
        dates_aligned = data.dates[-min_length:]

        signal, last_crossover_date, days_since = self.detect_crossover(
            fast_aligned, slow_aligned, dates_aligned
        )

        # Determine crossover type (Golden Cross/Death Cross only for 50/200 SMA)
        crossover_type: Literal["GOLDEN_CROSS", "DEATH_CROSS", "NONE"] = "NONE"
        fast_period = (
            self.config.period if fast_is_primary else self.config.secondary_period
        )
        slow_period = (
            self.config.secondary_period if fast_is_primary else self.config.period
        )
        fast_type = (
            self.config.ma_type if fast_is_primary else self.config.secondary_ma_type
        )
        slow_type = (
            self.config.secondary_ma_type if fast_is_primary else self.config.ma_type
        )

        if (
            fast_period == 50
            and slow_period == 200
            and fast_type == "SMA"
            and slow_type == "SMA"
            and last_crossover_date is not None
        ):
            if signal == "BULLISH":
                crossover_type = "GOLDEN_CROSS"
            elif signal == "BEARISH":
                crossover_type = "DEATH_CROSS"

        # Create crossover output
        crossover_output = CrossoverOutput(
            ticker=data.ticker,
            calculation_date=data.dates[-1],
            fast_ma_type=fast_type,
            fast_period=fast_period,
            fast_value=float(fast_aligned.iloc[-1]),
            slow_ma_type=slow_type,
            slow_period=slow_period,
            slow_value=float(slow_aligned.iloc[-1]),
            current_signal=signal,
            last_crossover_date=last_crossover_date,
            crossover_type=crossover_type,
            days_since_crossover=days_since,
        )

        return MovingAverageAnalysis(
            ticker=data.ticker,
            calculation_date=data.dates[-1],
            primary_ma=primary_output if fast_is_primary else secondary_output,
            secondary_ma=secondary_output if fast_is_primary else primary_output,
            crossover_analysis=crossover_output,
        )


# Convenience function for quick calculations
def calculate_moving_average(
    ticker: str,
    dates: list[str],
    prices: list[float],
    ma_type: str = "SMA",
    period: int = 50,
    secondary_ma_type: str | None = None,
    secondary_period: int | None = None,
) -> MovingAverageAnalysis:
    """Convenience function for calculating moving averages.

    EDUCATIONAL NOTE:
    This wrapper handles Pydantic model creation for you.
    For production code, prefer creating models explicitly
    (better type checking and IDE support).

    Args:
        ticker: Stock ticker symbol
        dates: List of dates (YYYY-MM-DD format)
        prices: List of closing prices
        ma_type: MA type ("SMA", "EMA", "WMA", "HMA")
        period: MA period in days
        secondary_ma_type: Optional second MA type for crossover
        secondary_period: Optional second MA period for crossover

    Returns:
        MovingAverageAnalysis: MA analysis with optional crossover

    Example:
        # Single MA
        results = calculate_moving_average(
            ticker="TSLA",
            dates=["2025-09-01", "2025-09-02", ...],
            prices=[250.0, 252.5, ...],
            ma_type="SMA",
            period=50
        )

        # Crossover analysis
        results = calculate_moving_average(
            ticker="TSLA",
            dates=["2025-01-01", ...],
            prices=[250.0, ...],
            ma_type="SMA",
            period=50,
            secondary_ma_type="SMA",
            secondary_period=200
        )
    """
    from datetime import date as date_type

    # Convert string dates to date objects
    date_objects = [date_type.fromisoformat(d) for d in dates]

    # Create input model
    ma_data = MovingAverageDataInput(
        ticker=ticker,
        dates=date_objects,
        prices=prices,
    )

    # Create config
    config = MovingAverageConfig(
        ma_type=ma_type,
        period=period,
        secondary_ma_type=secondary_ma_type,
        secondary_period=secondary_period,
    )

    # Calculate
    calculator = MovingAverageCalculator(config)

    if secondary_ma_type and secondary_period:
        return calculator.calculate_with_crossover(ma_data)
    else:
        # Single MA analysis
        primary_ma = calculator.calculate_ma(ma_data)
        return MovingAverageAnalysis(
            ticker=ma_data.ticker,
            calculation_date=ma_data.dates[-1],
            primary_ma=primary_ma,
            secondary_ma=None,
            crossover_analysis=None,
        )


# Type exports
__all__ = [
    "MovingAverageCalculator",
    "calculate_moving_average",
]
