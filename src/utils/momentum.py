"""Momentum Indicators Calculator for Finance Guru™.

This module implements comprehensive momentum indicator calculations using validated
Pydantic models. All calculations follow industry-standard technical analysis formulas.

ARCHITECTURE NOTE:
This is Layer 2 of our 3-layer architecture:
    Layer 1: Pydantic Models - Data validation (momentum_inputs.py)
    Layer 2: Calculator Classes (THIS FILE) - Business logic
    Layer 3: CLI Interface - Agent integration

EDUCATIONAL CONTEXT:
Momentum indicators measure the rate of change in prices. They help identify:
- Overbought/oversold conditions (when to sell/buy)
- Trend changes (when momentum shifts direction)
- Strength of trends (strong vs weak momentum)

These are critical for timing entry/exit points in aggressive strategies.

INDICATORS IMPLEMENTED:
1. RSI (Relative Strength Index) - 0-100 scale momentum
2. MACD (Moving Average Convergence Divergence) - Trend momentum
3. Stochastic Oscillator - Price range momentum
4. Williams %R - Inverted momentum oscillator
5. ROC (Rate of Change) - Percentage momentum

Author: Finance Guru™ Development Team
Created: 2025-10-13
"""

from typing import Literal

import pandas as pd

from src.models.momentum_inputs import (
    AllMomentumOutput,
    MACDOutput,
    MomentumConfig,
    MomentumDataInput,
    ROCOutput,
    RSIOutput,
    StochasticOutput,
    WilliamsROutput,
)


class MomentumIndicators:
    """Comprehensive momentum indicators calculator.

    WHAT: Calculates all major momentum indicators for Finance Guru agents
    WHY: Provides validated, type-safe momentum analysis for trading decisions
    HOW: Uses Pydantic models for I/O, pandas for calculations

    USAGE EXAMPLE:
        # Create configuration
        config = MomentumConfig(
            rsi_period=14,
            macd_fast=12,
            macd_slow=26
        )

        # Create calculator
        calculator = MomentumIndicators(config)

        # Calculate specific indicator
        rsi_result = calculator.calculate_rsi(momentum_data)

        # Or calculate all at once
        all_results = calculator.calculate_all(momentum_data)
    """

    def __init__(self, config: MomentumConfig):
        """Initialize calculator with configuration.

        Args:
            config: Validated configuration (Pydantic model ensures correctness)

        EDUCATIONAL NOTE:
        By accepting a Pydantic model, we KNOW the config is valid.
        We don't need to check if periods are positive or if MACD fast < slow.
        Pydantic already validated everything.
        """
        self.config = config

    def calculate_rsi(self, data: MomentumDataInput) -> RSIOutput:
        """Calculate Relative Strength Index.

        WHAT: RSI measures momentum on 0-100 scale
        WHY: Identifies overbought (>70) and oversold (<30) conditions
        HOW: Compares average gains to average losses over period

        FORMULA:
            RS = Average Gain / Average Loss
            RSI = 100 - (100 / (1 + RS))

        INTERPRETATION:
            RSI > 70: Overbought (potential sell signal)
            RSI < 30: Oversold (potential buy signal)
            RSI = 50: Neutral momentum

        EDUCATIONAL NOTE:
        RSI uses Wilder's smoothing (EMA-like but different):
        - First average: Simple average of gains/losses
        - Subsequent: (Previous Average * (n-1) + Current) / n

        This makes RSI smoother than simple moving averages.

        Args:
            data: Historical price data (validated by Pydantic)

        Returns:
            RSIOutput: Current RSI value and signal

        Raises:
            ValueError: If insufficient data for calculation
        """
        prices = pd.Series(data.close, index=data.dates)

        # Need at least period + 1 data points
        if len(prices) < self.config.rsi_period + 1:
            raise ValueError(
                f"Need at least {self.config.rsi_period + 1} data points for RSI, "
                f"got {len(prices)}"
            )

        # Calculate price changes
        delta = prices.diff()

        # Separate gains and losses
        gains = delta.where(delta > 0, 0)
        losses = -delta.where(delta < 0, 0)

        # Calculate average gains and losses using Wilder's smoothing
        # First value is simple average
        avg_gain = gains.rolling(window=self.config.rsi_period).mean()
        avg_loss = losses.rolling(window=self.config.rsi_period).mean()

        # Apply Wilder's smoothing to subsequent values
        for i in range(self.config.rsi_period, len(prices)):
            avg_gain.iloc[i] = (
                avg_gain.iloc[i - 1] * (self.config.rsi_period - 1) + gains.iloc[i]
            ) / self.config.rsi_period
            avg_loss.iloc[i] = (
                avg_loss.iloc[i - 1] * (self.config.rsi_period - 1) + losses.iloc[i]
            ) / self.config.rsi_period

        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        # Get current RSI (last value)
        current_rsi = float(rsi.iloc[-1])

        # Determine signal
        if current_rsi > 70:
            signal: Literal["overbought", "oversold", "neutral"] = "overbought"
        elif current_rsi < 30:
            signal = "oversold"
        else:
            signal = "neutral"

        return RSIOutput(
            ticker=data.ticker,
            calculation_date=data.dates[-1],
            current_rsi=current_rsi,
            rsi_signal=signal,
            period=self.config.rsi_period,
        )

    def calculate_macd(self, data: MomentumDataInput) -> MACDOutput:
        """Calculate MACD (Moving Average Convergence Divergence).

        WHAT: MACD shows relationship between two exponential moving averages
        WHY: Identifies trend changes and momentum strength
        HOW: Subtracts slow EMA from fast EMA, then smooths with signal line

        FORMULA:
            MACD Line = EMA(fast) - EMA(slow)
            Signal Line = EMA(MACD Line, signal_period)
            Histogram = MACD Line - Signal Line

        INTERPRETATION:
            MACD > Signal: Bullish (buy signal)
            MACD < Signal: Bearish (sell signal)
            Histogram increasing: Strengthening trend
            Histogram decreasing: Weakening trend

        EDUCATIONAL NOTE:
        Three key signals to watch:
        1. Crossovers: When MACD crosses signal line
        2. Divergences: Price makes new high/low but MACD doesn't
        3. Rapid rises/falls: Overbought/oversold conditions

        Args:
            data: Historical price data

        Returns:
            MACDOutput: MACD, signal, and histogram values
        """
        prices = pd.Series(data.close, index=data.dates)

        # Need enough data for slow EMA + signal EMA
        min_periods = self.config.macd_slow + self.config.macd_signal
        if len(prices) < min_periods:
            raise ValueError(
                f"Need at least {min_periods} data points for MACD, got {len(prices)}"
            )

        # Calculate EMAs
        ema_fast = prices.ewm(span=self.config.macd_fast, adjust=False).mean()
        ema_slow = prices.ewm(span=self.config.macd_slow, adjust=False).mean()

        # Calculate MACD line
        macd_line = ema_fast - ema_slow

        # Calculate signal line (EMA of MACD)
        signal_line = macd_line.ewm(span=self.config.macd_signal, adjust=False).mean()

        # Calculate histogram
        histogram = macd_line - signal_line

        # Get current values
        current_macd = float(macd_line.iloc[-1])
        current_signal = float(signal_line.iloc[-1])
        current_histogram = float(histogram.iloc[-1])

        # Determine signal
        signal_type: Literal["bullish", "bearish"] = (
            "bullish" if current_macd > current_signal else "bearish"
        )

        return MACDOutput(
            ticker=data.ticker,
            calculation_date=data.dates[-1],
            macd_line=current_macd,
            signal_line=current_signal,
            histogram=current_histogram,
            signal=signal_type,
            fast_period=self.config.macd_fast,
            slow_period=self.config.macd_slow,
            signal_period=self.config.macd_signal,
        )

    def calculate_stochastic(self, data: MomentumDataInput) -> StochasticOutput:
        """Calculate Stochastic Oscillator.

        WHAT: Compares closing price to price range over time
        WHY: Identifies overbought/oversold and potential reversals
        HOW: Calculates where close is within high-low range

        FORMULA:
            %K = 100 * (Close - Low_n) / (High_n - Low_n)
            %D = SMA(%K, d_period)

            where:
            - Low_n: Lowest low over n periods
            - High_n: Highest high over n periods

        INTERPRETATION:
            %K > 80: Overbought
            %K < 20: Oversold
            %K crosses above %D: Bullish
            %K crosses below %D: Bearish

        EDUCATIONAL NOTE:
        Stochastic is based on the observation that:
        - In uptrends: Prices close near the high
        - In downtrends: Prices close near the low

        Two versions:
        - Fast Stochastic: Just %K (more responsive, noisier)
        - Slow Stochastic: %K and %D (smoother, fewer signals)

        Args:
            data: Historical price data (must include high/low)

        Returns:
            StochasticOutput: %K, %D, and signal
        """
        # Stochastic requires high/low data
        if data.high is None or data.low is None:
            raise ValueError(
                "Stochastic Oscillator requires high and low price data. "
                "Provide high/low arrays in MomentumDataInput."
            )

        # Create DataFrame with all price data
        df = pd.DataFrame(
            {
                "high": data.high,
                "low": data.low,
                "close": data.close,
            },
            index=data.dates,
        )

        # Need enough data for calculation
        if len(df) < self.config.stoch_k_period:
            raise ValueError(
                f"Need at least {self.config.stoch_k_period} data points for Stochastic, "
                f"got {len(df)}"
            )

        # Calculate rolling high and low
        rolling_high = df["high"].rolling(window=self.config.stoch_k_period).max()
        rolling_low = df["low"].rolling(window=self.config.stoch_k_period).min()

        # Calculate %K
        k_values = 100 * ((df["close"] - rolling_low) / (rolling_high - rolling_low))

        # Calculate %D (SMA of %K)
        d_values = k_values.rolling(window=self.config.stoch_d_period).mean()

        # Get current values
        current_k = float(k_values.iloc[-1])
        current_d = float(d_values.iloc[-1])

        # Determine signal
        if current_k > 80:
            signal: Literal["overbought", "oversold", "neutral"] = "overbought"
        elif current_k < 20:
            signal = "oversold"
        else:
            signal = "neutral"

        return StochasticOutput(
            ticker=data.ticker,
            calculation_date=data.dates[-1],
            k_value=current_k,
            d_value=current_d,
            signal=signal,
            k_period=self.config.stoch_k_period,
            d_period=self.config.stoch_d_period,
        )

    def calculate_williams_r(self, data: MomentumDataInput) -> WilliamsROutput:
        """Calculate Williams %R.

        WHAT: Momentum indicator with inverted scale (-100 to 0)
        WHY: Shows overbought/oversold similar to Stochastic
        HOW: Measures where close is within high-low range (inverted)

        FORMULA:
            Williams %R = -100 * (High_n - Close) / (High_n - Low_n)

            where:
            - High_n: Highest high over n periods
            - Low_n: Lowest low over n periods

        INTERPRETATION:
            %R > -20: Overbought (sell signal)
            %R < -80: Oversold (buy signal)
            %R between -20 and -80: Neutral

        EDUCATIONAL NOTE:
        Williams %R is essentially an inverted Stochastic %K:
        - Stochastic: 0 to 100 (oversold to overbought)
        - Williams %R: -100 to 0 (oversold to overbought)

        Some traders prefer Williams %R because:
        - Negative numbers match "oversold" psychology
        - More responsive to recent highs/lows
        - Works well in strong trends

        Args:
            data: Historical price data (must include high/low)

        Returns:
            WilliamsROutput: %R value and signal
        """
        # Williams %R requires high/low data
        if data.high is None or data.low is None:
            raise ValueError(
                "Williams %R requires high and low price data. "
                "Provide high/low arrays in MomentumDataInput."
            )

        # Create DataFrame
        df = pd.DataFrame(
            {
                "high": data.high,
                "low": data.low,
                "close": data.close,
            },
            index=data.dates,
        )

        # Need enough data
        if len(df) < self.config.williams_period:
            raise ValueError(
                f"Need at least {self.config.williams_period} data points for Williams %R, "
                f"got {len(df)}"
            )

        # Calculate rolling high and low
        rolling_high = df["high"].rolling(window=self.config.williams_period).max()
        rolling_low = df["low"].rolling(window=self.config.williams_period).min()

        # Calculate Williams %R
        williams_r = -100 * (
            (rolling_high - df["close"]) / (rolling_high - rolling_low)
        )

        # Get current value
        current_wr = float(williams_r.iloc[-1])

        # Determine signal
        if current_wr > -20:
            signal: Literal["overbought", "oversold", "neutral"] = "overbought"
        elif current_wr < -80:
            signal = "oversold"
        else:
            signal = "neutral"

        return WilliamsROutput(
            ticker=data.ticker,
            calculation_date=data.dates[-1],
            williams_r=current_wr,
            signal=signal,
            period=self.config.williams_period,
        )

    def calculate_roc(self, data: MomentumDataInput) -> ROCOutput:
        """Calculate Rate of Change.

        WHAT: Measures percentage change over a period
        WHY: Shows velocity and direction of price changes
        HOW: Compares current price to price n periods ago

        FORMULA:
            ROC = ((Close - Close_n) / Close_n) * 100

            where Close_n is the closing price n periods ago

        INTERPRETATION:
            ROC > 0: Bullish momentum (price increasing)
            ROC < 0: Bearish momentum (price decreasing)
            Large ROC: Strong momentum
            Small ROC: Weak momentum
            ROC = 0: No change

        EDUCATIONAL NOTE:
        ROC is one of the simplest momentum indicators:
        - No smoothing (shows raw momentum)
        - Easy to interpret (just % change)
        - Can be choppy (sensitive to outliers)

        Trading signals:
        - ROC crossing above 0: Buy signal
        - ROC crossing below 0: Sell signal
        - ROC divergence from price: Potential reversal

        Args:
            data: Historical price data

        Returns:
            ROCOutput: ROC value and signal
        """
        prices = pd.Series(data.close, index=data.dates)

        # Need at least period + 1 data points
        if len(prices) < self.config.roc_period + 1:
            raise ValueError(
                f"Need at least {self.config.roc_period + 1} data points for ROC, "
                f"got {len(prices)}"
            )

        # Calculate ROC
        # pct_change with periods parameter gives us exactly what we need
        roc_series = prices.pct_change(periods=self.config.roc_period) * 100

        # Get current ROC
        current_roc = float(roc_series.iloc[-1])

        # Determine signal
        if current_roc > 0:
            signal: Literal["bullish", "bearish", "neutral"] = "bullish"
        elif current_roc < 0:
            signal = "bearish"
        else:
            signal = "neutral"

        return ROCOutput(
            ticker=data.ticker,
            calculation_date=data.dates[-1],
            roc=current_roc,
            signal=signal,
            period=self.config.roc_period,
        )

    def calculate_all(self, data: MomentumDataInput) -> AllMomentumOutput:
        """Calculate all momentum indicators at once.

        WHAT: Comprehensive momentum analysis
        WHY: Convenient for comparing multiple signals
        HOW: Runs all indicator calculations and combines results

        EDUCATIONAL NOTE:
        Using multiple indicators together is called "confluence":
        - 1 indicator says buy: Weak signal
        - 2-3 indicators agree: Moderate signal
        - 4-5 indicators agree: Strong signal

        Example confluence:
        - RSI < 30 (oversold)
        - MACD bullish crossover
        - Stochastic < 20 (oversold)
        - Williams %R < -80 (oversold)
        - ROC turning positive
        = Strong buy signal!

        Args:
            data: Historical price data

        Returns:
            AllMomentumOutput: All indicators combined

        Raises:
            ValueError: If data insufficient for any indicator
        """
        # Calculate each indicator
        rsi_result = self.calculate_rsi(data)
        macd_result = self.calculate_macd(data)
        stoch_result = self.calculate_stochastic(data)
        williams_result = self.calculate_williams_r(data)
        roc_result = self.calculate_roc(data)

        return AllMomentumOutput(
            ticker=data.ticker,
            calculation_date=data.dates[-1],
            rsi=rsi_result,
            macd=macd_result,
            stochastic=stoch_result,
            williams_r=williams_result,
            roc=roc_result,
        )


# Convenience function for quick calculations
def calculate_momentum(
    ticker: str,
    dates: list[str],
    close: list[float],
    high: list[float] | None = None,
    low: list[float] | None = None,
    **config_kwargs,
) -> AllMomentumOutput:
    """Convenience function for calculating all momentum indicators.

    EDUCATIONAL NOTE:
    This wrapper handles Pydantic model creation for you.
    For production code, prefer creating models explicitly
    (better type checking and IDE support).

    Args:
        ticker: Stock ticker symbol
        dates: List of dates (YYYY-MM-DD format)
        close: List of closing prices
        high: Optional list of high prices (required for Stochastic, Williams %R)
        low: Optional list of low prices (required for Stochastic, Williams %R)
        **config_kwargs: Additional config options (rsi_period, macd_fast, etc.)

    Returns:
        AllMomentumOutput: All momentum indicators

    Example:
        results = calculate_momentum(
            ticker="TSLA",
            dates=["2025-09-01", "2025-09-02", ...],
            close=[250.0, 252.5, ...],
            high=[252.0, 254.0, ...],
            low=[248.0, 251.0, ...],
            rsi_period=14
        )
    """
    from datetime import date as date_type

    # Convert string dates to date objects
    date_objects = [date_type.fromisoformat(d) for d in dates]

    # Create input model
    momentum_data = MomentumDataInput(
        ticker=ticker,
        dates=date_objects,
        close=close,
        high=high,
        low=low,
    )

    # Create config
    config = MomentumConfig(**config_kwargs)

    # Calculate
    calculator = MomentumIndicators(config)
    return calculator.calculate_all(momentum_data)


# Type exports
__all__ = [
    "MomentumIndicators",
    "calculate_momentum",
]
