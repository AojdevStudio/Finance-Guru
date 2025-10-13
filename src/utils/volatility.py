"""
Volatility metrics calculator for Finance Guru.

WHAT: Calculates 5 essential volatility indicators for position sizing and risk management
WHY: Provides type-safe volatility analysis for Compliance Officer, Margin Specialist, and agents
ARCHITECTURE: Layer 2 of 3-layer type-safe architecture

INDICATORS:
- Bollinger Bands: Price volatility channels
- ATR: Average True Range for stop-loss sizing
- Standard Deviation: Statistical volatility
- Historical Volatility: Annualized volatility measure
- Keltner Channels: ATR-based channels

Used by: Compliance Officer (position limits), Margin Specialist (leverage), Risk Assessment
"""

import numpy as np
import pandas as pd

from src.models.volatility_inputs import (
    ATROutput,
    BollingerBandsOutput,
    HistoricalVolatilityOutput,
    KeltnerChannelsOutput,
    VolatilityConfig,
    VolatilityDataInput,
    VolatilityMetricsOutput,
)


class VolatilityCalculator:
    """
    WHAT: Calculates comprehensive volatility metrics for Finance Guru agents
    WHY: Provides validated, type-safe volatility analysis for position sizing and risk management
    HOW: Uses Pydantic models for inputs/outputs, pandas/numpy for calculations

    EDUCATIONAL NOTE:
    This calculator implements industry-standard volatility indicators used by professional traders:

    1. Bollinger Bands: John Bollinger's volatility channel system
    2. ATR: Welles Wilder's Average True Range
    3. Historical Volatility: Standard deviation of log returns (annualized)
    4. Keltner Channels: Chester Keltner's ATR-based channel system

    All calculations follow standard financial formulas used across the industry.
    """

    def __init__(self, config: VolatilityConfig):
        """
        Initialize calculator with configuration.

        Args:
            config: VolatilityConfig with all indicator settings
        """
        self.config = config

    def calculate_all_metrics(
        self,
        data: VolatilityDataInput,
    ) -> VolatilityMetricsOutput:
        """
        Calculate all volatility metrics for the given price data.

        EXPLANATION:
        This is the main entry point. It orchestrates all volatility calculations
        and returns a complete volatility profile. Because we use Pydantic models,
        we KNOW the inputs are valid before we start calculating.

        Args:
            data: VolatilityDataInput with OHLC price data

        Returns:
            VolatilityMetricsOutput with all indicators and volatility regime
        """
        # Convert to DataFrame for calculations
        df = pd.DataFrame({
            'date': data.dates,
            'high': data.high,
            'low': data.low,
            'close': data.close,
        })
        df = df.set_index('date')

        # Calculate all indicators
        bb = self._calculate_bollinger_bands(df['close'])
        atr = self._calculate_atr(df)
        hvol = self._calculate_historical_volatility(df['close'])
        kc = self._calculate_keltner_channels(df)

        # Determine volatility regime
        regime = self._assess_volatility_regime(hvol, atr)

        return VolatilityMetricsOutput(
            ticker=data.ticker,
            calculation_date=data.dates[-1],
            current_price=float(data.close[-1]),
            bollinger_bands=bb,
            atr=atr,
            historical_volatility=hvol,
            keltner_channels=kc,
            volatility_regime=regime,
        )

    def _calculate_bollinger_bands(self, closes: pd.Series) -> BollingerBandsOutput:
        """
        Calculate Bollinger Bands indicator.

        FORMULA:
        - Middle Band = SMA(close, period)
        - Upper Band = Middle + (std_dev × standard_deviation)
        - Lower Band = Middle - (std_dev × standard_deviation)
        - %B = (close - lower) / (upper - lower)
        - Bandwidth = (upper - lower) / middle × 100

        EDUCATIONAL NOTE:
        Bollinger Bands expand during volatile periods and contract during calm periods.
        - Price touching upper band in uptrend = strength (not necessarily overbought)
        - Price touching lower band in downtrend = weakness (not necessarily oversold)
        - Narrow bands (low bandwidth) often precede big moves ("the squeeze")

        Args:
            closes: Series of closing prices

        Returns:
            BollingerBandsOutput with all band values and indicators
        """
        period = self.config.bb_period
        std_multiplier = self.config.bb_std_dev

        # Calculate middle band (SMA)
        middle = closes.rolling(window=period).mean()

        # Calculate standard deviation
        std = closes.rolling(window=period).std()

        # Calculate upper and lower bands
        upper = middle + (std * std_multiplier)
        lower = middle - (std * std_multiplier)

        # Get latest values
        current_close = float(closes.iloc[-1])
        middle_val = float(middle.iloc[-1])
        upper_val = float(upper.iloc[-1])
        lower_val = float(lower.iloc[-1])

        # Calculate %B (position within bands)
        # %B = 1.0 means price is at upper band
        # %B = 0.0 means price is at lower band
        # %B = 0.5 means price is at middle band
        band_width = upper_val - lower_val
        percent_b = (current_close - lower_val) / band_width if band_width > 0 else 0.5

        # Calculate bandwidth (band width as % of middle band)
        bandwidth = (band_width / middle_val * 100) if middle_val > 0 else 0.0

        return BollingerBandsOutput(
            middle_band=middle_val,
            upper_band=upper_val,
            lower_band=lower_val,
            percent_b=percent_b,
            bandwidth=bandwidth,
        )

    def _calculate_atr(self, df: pd.DataFrame) -> ATROutput:
        """
        Calculate Average True Range (ATR).

        FORMULA:
        True Range = max of:
          1. High - Low
          2. |High - Previous Close|
          3. |Low - Previous Close|

        ATR = EMA(True Range, period)

        EDUCATIONAL NOTE:
        ATR is THE standard measure for volatility in dollars (not percentages).
        Created by Welles Wilder for commodity trading.

        WHY IT MATTERS:
        - Setting stop losses: Use 2×ATR below entry to avoid noise
        - Position sizing: Higher ATR = smaller position (more risk per share)
        - Breakout confirmation: Strong moves should have expanding ATR

        Example: TSLA with ATR = $8.50
        - Set stop loss $17 below entry (2×ATR)
        - If you have $500k and want 1% risk = $5k risk budget
        - Position size = $5k / $17 = 294 shares

        Args:
            df: DataFrame with high, low, close columns

        Returns:
            ATROutput with ATR value and ATR as % of price
        """
        period = self.config.atr_period

        # Calculate True Range components
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift(1))
        low_close = abs(df['low'] - df['close'].shift(1))

        # True Range is the maximum of the three
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)

        # Calculate ATR as EMA of True Range
        atr = true_range.ewm(span=period, adjust=False).mean()

        # Get latest values
        atr_val = float(atr.iloc[-1])
        current_price = float(df['close'].iloc[-1])

        # Calculate ATR as percentage of current price
        atr_percent = (atr_val / current_price * 100) if current_price > 0 else 0.0

        return ATROutput(
            atr=atr_val,
            atr_percent=atr_percent,
        )

    def _calculate_historical_volatility(
        self,
        closes: pd.Series,
    ) -> HistoricalVolatilityOutput:
        """
        Calculate historical volatility (standard deviation of returns).

        FORMULA:
        - Daily Returns = log(close_t / close_t-1)
        - Daily Volatility = std_dev(daily_returns)
        - Annual Volatility = daily_vol × sqrt(252)

        EDUCATIONAL NOTE:
        This is the SAME volatility calculation used in your Risk Metrics tool.
        The difference here is we're looking at a rolling window to see CURRENT volatility,
        while Risk Metrics looks at the full historical period.

        INTERPRETATION:
        - 20% annual vol = Low volatility (like SPY or large-cap stocks)
        - 40% annual vol = Moderate volatility (like individual tech stocks)
        - 60%+ annual vol = High volatility (like small-cap or meme stocks)
        - 100%+ annual vol = Extreme volatility (crypto-level)

        USE FOR YOUR $500K PORTFOLIO:
        Higher volatility = smaller position size to maintain same risk level

        Args:
            closes: Series of closing prices

        Returns:
            HistoricalVolatilityOutput with daily and annualized volatility
        """
        period = self.config.hvol_period
        annualization_factor = self.config.hvol_annualization_factor

        # Calculate log returns (more accurate for compounding)
        returns = np.log(closes / closes.shift(1))

        # Calculate rolling standard deviation
        rolling_vol = returns.rolling(window=period).std()

        # Get latest daily volatility
        daily_vol = float(rolling_vol.iloc[-1])

        # Annualize the volatility
        # We multiply by sqrt(252) because variance scales linearly with time
        # and std dev is sqrt(variance)
        annual_vol = daily_vol * np.sqrt(annualization_factor)

        return HistoricalVolatilityOutput(
            daily_volatility=daily_vol,
            annual_volatility=annual_vol,
        )

    def _calculate_keltner_channels(self, df: pd.DataFrame) -> KeltnerChannelsOutput:
        """
        Calculate Keltner Channels indicator.

        FORMULA:
        - Middle Line = EMA(close, period)
        - Upper Channel = Middle + (ATR × multiplier)
        - Lower Channel = Middle - (ATR × multiplier)

        EDUCATIONAL NOTE:
        Keltner Channels are similar to Bollinger Bands but use ATR instead of
        standard deviation. This makes them:
        - More responsive to actual price movement
        - Less affected by volatility "squeezes"
        - Better for trending markets

        TRADING WITH BOTH INDICATORS:
        - Price between Bollinger and Keltner = normal volatility expansion
        - Price outside BOTH = extreme move (high conviction signal)
        - Bollinger wider than Keltner = high volatility regime

        Args:
            df: DataFrame with high, low, close columns

        Returns:
            KeltnerChannelsOutput with channel values
        """
        period = self.config.kc_period
        atr_multiplier = self.config.kc_atr_multiplier

        # Calculate middle line (EMA of close)
        middle = df['close'].ewm(span=period, adjust=False).mean()

        # Calculate ATR for channel width
        atr_result = self._calculate_atr(df)
        atr_value = atr_result.atr

        # Calculate upper and lower channels
        middle_val = float(middle.iloc[-1])
        upper_val = middle_val + (atr_value * atr_multiplier)
        lower_val = middle_val - (atr_value * atr_multiplier)

        return KeltnerChannelsOutput(
            middle_line=middle_val,
            upper_channel=upper_val,
            lower_channel=lower_val,
        )

    def _assess_volatility_regime(
        self,
        hvol: HistoricalVolatilityOutput,
        atr: ATROutput,
    ) -> str:
        """
        Assess overall volatility regime based on multiple indicators.

        LOGIC:
        - Low: Annual vol < 25% AND ATR% < 2.5%
        - Normal: Annual vol 25-50% AND ATR% 2.5-5%
        - High: Annual vol 50-75% OR ATR% 5-7.5%
        - Extreme: Annual vol > 75% OR ATR% > 7.5%

        EDUCATIONAL NOTE:
        The volatility regime helps agents make quick decisions:
        - Low: Safe to use higher leverage, larger positions
        - Normal: Standard position sizing rules apply
        - High: Reduce position sizes, tighter stops
        - Extreme: Maximum caution - very small positions or wait

        FOR YOUR $500K PORTFOLIO:
        - Low regime: Can allocate 10-20% per position
        - Normal regime: 5-10% per position
        - High regime: 2-5% per position
        - Extreme regime: 1-2% per position (or sit in cash)

        Args:
            hvol: Historical volatility output
            atr: ATR output

        Returns:
            Volatility regime classification
        """
        annual_vol = hvol.annual_volatility
        atr_pct = atr.atr_percent

        # Check for extreme conditions first
        if annual_vol > 0.75 or atr_pct > 7.5:
            return "extreme"

        # Check for high volatility
        if annual_vol > 0.50 or atr_pct > 5.0:
            return "high"

        # Check for low volatility
        if annual_vol < 0.25 and atr_pct < 2.5:
            return "low"

        # Default to normal
        return "normal"


# Convenience function for quick calculations
def calculate_volatility(
    data: VolatilityDataInput,
    config: VolatilityConfig | None = None,
) -> VolatilityMetricsOutput:
    """
    Convenience function to calculate volatility metrics with default or custom config.

    EDUCATIONAL NOTE:
    This function provides a simple interface for agents to calculate volatility
    without needing to instantiate the calculator class. Use this for quick
    one-off calculations.

    Args:
        data: VolatilityDataInput with OHLC price data
        config: Optional custom configuration (uses defaults if not provided)

    Returns:
        VolatilityMetricsOutput with all indicators

    Example:
        >>> from src.models.volatility_inputs import VolatilityDataInput
        >>> from src.utils.volatility import calculate_volatility
        >>>
        >>> data = VolatilityDataInput(
        ...     ticker="TSLA",
        ...     dates=[...],
        ...     high=[...],
        ...     low=[...],
        ...     close=[...]
        ... )
        >>> result = calculate_volatility(data)
        >>> print(f"ATR: ${result.atr.atr:.2f}")
        >>> print(f"Regime: {result.volatility_regime}")
    """
    if config is None:
        config = VolatilityConfig()

    calculator = VolatilityCalculator(config)
    return calculator.calculate_all_metrics(data)
