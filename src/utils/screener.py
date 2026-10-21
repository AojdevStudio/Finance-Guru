"""Technical Screener Engine for Finance Guru™.

This module implements multi-criteria technical screening for finding trading opportunities.
Integrates with existing momentum and moving average tools.

ARCHITECTURE NOTE:
This is Layer 2 of our 3-layer architecture:
    Layer 1: Pydantic Models - Data validation (screener_inputs.py)
    Layer 2: Calculator Classes (THIS FILE) - Business logic
    Layer 3: CLI Interface - Agent integration

EDUCATIONAL CONTEXT:
A technical screener automates the process of finding stocks that meet
specific technical criteria. Instead of manually checking charts for
dozens of stocks, the screener does it automatically.

THINK OF IT AS:
- A "search engine" for technical patterns
- An automated assistant that watches the market 24/7
- A filter that finds needles (opportunities) in haystacks (market noise)

WORKFLOW:
1. Define criteria (golden cross, RSI oversold, etc.)
2. Analyze each stock against criteria
3. Score stocks based on signal strength
4. Rank results from best to worst
5. Generate actionable recommendations

Author: Finance Guru™ Development Team
Created: 2025-10-13
"""

import sys
from collections import Counter
from datetime import date
from typing import assert_never

import pandas as pd

from src.models.momentum_inputs import MomentumConfig, MomentumDataInput
from src.models.screener_inputs import (
    PatternType,
    PortfolioScreeningOutput,
    ScreeningCriteria,
    ScreeningResult,
    SignalStrength,
    TechnicalSignal,
)
from src.utils.momentum import MomentumIndicators

_BREAKOUT_FACTOR = 1.01
_BREAKDOWN_FACTOR = 0.99

_SIGNAL_POINTS: dict[SignalStrength, float] = {
    "strong": 3.0,
    "moderate": 2.0,
    "weak": 1.0,
}

_MIN_SIGNALS_TO_MATCH: dict[SignalStrength, int] = {
    "strong": 1,
    "moderate": 2,
    "weak": 3,
}


_BULLISH_PATTERNS = frozenset(
    {
        PatternType.GOLDEN_CROSS,
        PatternType.RSI_OVERSOLD,
        PatternType.MACD_BULLISH,
        PatternType.BREAKOUT,
    }
)


def _signed_points(signal: TechnicalSignal) -> float:
    """Strength points, negative for a bearish pattern."""
    points = _SIGNAL_POINTS[signal.strength]
    return points if signal.signal_type in _BULLISH_PATTERNS else -points


def _momentum_input(df: pd.DataFrame) -> MomentumDataInput:
    """Wrap a screener price frame as close-only momentum input."""
    return MomentumDataInput(
        ticker="TEMP",
        close=df["price"].tolist(),
        dates=df.index.tolist(),
    )


class TechnicalScreener:
    """Multi-criteria technical screening engine.

    WHAT: Screens stocks for technical trading opportunities
    WHY: Automates pattern detection across multiple stocks
    HOW: Combines momentum, moving averages, and volume analysis

    USAGE EXAMPLE:
        # Create criteria
        criteria = ScreeningCriteria(
            patterns=[PatternType.GOLDEN_CROSS, PatternType.RSI_OVERSOLD],
            rsi_oversold=35.0,
            ma_fast=50,
            ma_slow=200
        )

        # Create screener
        screener = TechnicalScreener(criteria)

        # Screen single ticker
        result = screener.screen_ticker("TSLA", prices, dates, volumes)

        # Check result
        if result.matches_criteria:
            print(f"Found {len(result.signals)} signals - Score: {result.score}")
    """

    def __init__(self, criteria: ScreeningCriteria):
        """Initialize screener with criteria.

        Args:
            criteria: Validated screening criteria (Pydantic model)

        EDUCATIONAL NOTE:
        The criteria define what patterns we're looking for.
        Think of it as programming the screener's "eyes" to
        recognize specific patterns.
        """
        self.criteria = criteria

        self.momentum_config = MomentumConfig()
        self.momentum_calc = MomentumIndicators(self.momentum_config)

    def screen_ticker(
        self,
        ticker: str,
        prices: list[float],
        dates: list[date],
        volumes: list[float] | None = None,
    ) -> ScreeningResult:
        """Screen a single ticker against criteria.

        Args:
            ticker: Stock ticker symbol
            prices: Historical prices (need at least 200 for MA200)
            dates: Corresponding dates
            volumes: Optional volume data for breakout detection

        Returns:
            ScreeningResult: Complete screening analysis

        EDUCATIONAL NOTE:
        This method checks the stock against ALL patterns in the criteria.
        Each pattern match generates a TechnicalSignal with a strength rating.
        The overall score is the sum of all signal strengths.
        """
        df = pd.DataFrame(
            {
                "date": dates,
                "price": prices,
            }
        )
        if volumes:
            df["volume"] = volumes
        df = df.set_index("date")

        signals: list[TechnicalSignal] = []

        for pattern in self.criteria.patterns:
            signal = self._detect_pattern(ticker, pattern, df)
            if signal:
                signals.append(signal)

        score = self._calculate_score(signals)

        matches = self._meets_criteria(signals)

        recommendation, confidence = self._generate_recommendation(signals)

        current_price = float(df["price"].iloc[-1])
        current_rsi = self._get_current_rsi(df)

        notes = self._generate_notes(signals, df)

        return ScreeningResult(
            ticker=ticker,
            screening_date=dates[-1] if dates else date.today(),
            matches_criteria=matches,
            signals=signals,
            score=score,
            current_price=current_price,
            current_rsi=current_rsi,
            recommendation=recommendation,
            confidence=confidence,
            notes=notes,
        )

    def screen_portfolio(
        self,
        tickers_data: dict[str, tuple[list[float], list[date], list[float] | None]],
    ) -> PortfolioScreeningOutput:
        """Screen multiple tickers and rank results.

        Args:
            tickers_data: Dict mapping ticker -> (prices, dates, volumes)

        Returns:
            PortfolioScreeningOutput: Ranked screening results

        EDUCATIONAL NOTE:
        This method screens all tickers and ranks them by score.
        Use this to find the best opportunities across your watchlist.
        """
        results: list[ScreeningResult] = []

        for ticker, (prices, dates, volumes) in tickers_data.items():
            result = self.screen_ticker(ticker, prices, dates, volumes)
            results.append(result)

        results.sort(key=lambda r: r.score, reverse=True)

        for rank, result in enumerate(results, start=1):
            result.rank = rank

        matching_count = sum(1 for r in results if r.matches_criteria)

        top_picks = [r.ticker for r in results[:5] if r.matches_criteria]

        summary = self._generate_summary(results, matching_count)

        return PortfolioScreeningOutput(
            screening_date=date.today(),
            criteria_used=self.criteria.patterns,
            total_tickers_screened=len(results),
            tickers_matching=matching_count,
            results=results,
            top_picks=top_picks,
            summary=summary,
        )

    def _detect_pattern(
        self, ticker: str, pattern: PatternType, df: pd.DataFrame
    ) -> TechnicalSignal | None:
        """Detect a specific technical pattern.

        EDUCATIONAL NOTE:
        Each pattern has specific detection logic:
        - Golden Cross: Check if MA50 recently crossed above MA200
        - RSI Oversold: Check if RSI < threshold
        - MACD Bullish: Check if MACD line crossed above signal line

        Returns None if pattern not detected.
        """
        try:
            match pattern:
                case PatternType.GOLDEN_CROSS:
                    return self._detect_golden_cross(df)
                case PatternType.DEATH_CROSS:
                    return self._detect_death_cross(df)
                case PatternType.RSI_OVERSOLD:
                    return self._detect_rsi_oversold(df)
                case PatternType.RSI_OVERBOUGHT:
                    return self._detect_rsi_overbought(df)
                case PatternType.MACD_BULLISH:
                    return self._detect_macd_bullish(df)
                case PatternType.MACD_BEARISH:
                    return self._detect_macd_bearish(df)
                case PatternType.BREAKOUT:
                    return self._detect_breakout(df)
                case PatternType.BREAKDOWN:
                    return self._detect_breakdown(df)
                case _:
                    assert_never(pattern)
        except ValueError as e:
            print(
                f"⚠️  Pattern detection failed for {pattern.value}: {e}", file=sys.stderr
            )
            return None

    def _detect_golden_cross(self, df: pd.DataFrame) -> TechnicalSignal | None:
        """Detect golden cross pattern.

        WHAT: 50-day MA crosses above 200-day MA
        WHY: Classic bullish signal used by institutional traders
        """
        if len(df) < 200:
            return None

        ma50 = df["price"].rolling(window=self.criteria.ma_fast).mean()
        ma200 = df["price"].rolling(window=self.criteria.ma_slow).mean()

        recent_df = df.iloc[-10:]
        recent_ma50 = ma50.iloc[-10:]
        recent_ma200 = ma200.iloc[-10:]

        for i in range(1, len(recent_df)):
            prev_below = recent_ma50.iloc[i - 1] < recent_ma200.iloc[i - 1]
            now_above = recent_ma50.iloc[i] > recent_ma200.iloc[i]

            if prev_below and now_above:
                crossover_date = recent_df.index[i]

                separation = abs(recent_ma50.iloc[i] - recent_ma200.iloc[i])
                avg_price = df["price"].mean()
                separation_pct = separation / avg_price

                if separation_pct > 0.05:
                    strength = "strong"
                elif separation_pct > 0.02:
                    strength = "moderate"
                else:
                    strength = "weak"

                return TechnicalSignal(
                    signal_type=PatternType.GOLDEN_CROSS,
                    strength=strength,
                    description=f"Golden Cross: {self.criteria.ma_fast}MA crossed above {self.criteria.ma_slow}MA",
                    date_detected=crossover_date,
                    value=float(separation_pct),
                )

        return None

    def _detect_death_cross(self, df: pd.DataFrame) -> TechnicalSignal | None:
        """Detect death cross pattern (opposite of golden cross)."""
        if len(df) < 200:
            return None

        ma50 = df["price"].rolling(window=self.criteria.ma_fast).mean()
        ma200 = df["price"].rolling(window=self.criteria.ma_slow).mean()

        recent_df = df.iloc[-10:]
        recent_ma50 = ma50.iloc[-10:]
        recent_ma200 = ma200.iloc[-10:]

        for i in range(1, len(recent_df)):
            prev_above = recent_ma50.iloc[i - 1] > recent_ma200.iloc[i - 1]
            now_below = recent_ma50.iloc[i] < recent_ma200.iloc[i]

            if prev_above and now_below:
                crossover_date = recent_df.index[i]
                separation = abs(recent_ma50.iloc[i] - recent_ma200.iloc[i])
                separation_pct = separation / df["price"].mean()

                strength = (
                    "strong"
                    if separation_pct > 0.05
                    else "moderate"
                    if separation_pct > 0.02
                    else "weak"
                )

                return TechnicalSignal(
                    signal_type=PatternType.DEATH_CROSS,
                    strength=strength,
                    description=f"Death Cross: {self.criteria.ma_fast}MA crossed below {self.criteria.ma_slow}MA",
                    date_detected=crossover_date,
                    value=float(separation_pct),
                )

        return None

    def _detect_rsi_oversold(self, df: pd.DataFrame) -> TechnicalSignal | None:
        """Detect RSI oversold condition."""
        if len(df) < self.momentum_config.rsi_period:
            return None

        try:
            momentum_data = _momentum_input(df)
            rsi_result = self.momentum_calc.calculate_rsi(momentum_data)

            current_rsi = rsi_result.current_rsi

            if current_rsi < self.criteria.rsi_oversold:
                if current_rsi < 20:
                    strength = "strong"
                elif current_rsi < 25:
                    strength = "moderate"
                else:
                    strength = "weak"

                return TechnicalSignal(
                    signal_type=PatternType.RSI_OVERSOLD,
                    strength=strength,
                    description=f"RSI Oversold: RSI at {current_rsi:.1f} (below {self.criteria.rsi_oversold})",
                    date_detected=df.index[-1],
                    value=float(current_rsi),
                )
        except ValueError:
            pass

        return None

    def _detect_rsi_overbought(self, df: pd.DataFrame) -> TechnicalSignal | None:
        """Detect RSI overbought condition."""
        if len(df) < self.momentum_config.rsi_period:
            return None

        try:
            momentum_data = _momentum_input(df)
            rsi_result = self.momentum_calc.calculate_rsi(momentum_data)
            current_rsi = rsi_result.current_rsi

            if current_rsi > self.criteria.rsi_overbought:
                if current_rsi > 80:
                    strength = "strong"
                elif current_rsi > 75:
                    strength = "moderate"
                else:
                    strength = "weak"

                return TechnicalSignal(
                    signal_type=PatternType.RSI_OVERBOUGHT,
                    strength=strength,
                    description=f"RSI Overbought: RSI at {current_rsi:.1f} (above {self.criteria.rsi_overbought})",
                    date_detected=df.index[-1],
                    value=float(current_rsi),
                )
        except ValueError:
            pass

        return None

    def _detect_macd_bullish(self, df: pd.DataFrame) -> TechnicalSignal | None:
        """Detect MACD bullish crossover."""
        if len(df) < self.momentum_config.macd_slow:
            return None

        try:
            momentum_data = _momentum_input(df)
            macd_result = self.momentum_calc.calculate_macd(momentum_data)

            if (
                macd_result.signal == "bullish"
                or macd_result.signal == "strong_bullish"
            ):
                strength = (
                    "strong" if macd_result.signal == "strong_bullish" else "moderate"
                )

                return TechnicalSignal(
                    signal_type=PatternType.MACD_BULLISH,
                    strength=strength,
                    description="MACD Bullish: MACD line crossed above signal line",
                    date_detected=df.index[-1],
                    value=float(macd_result.macd_line),
                )
        except ValueError:
            pass

        return None

    def _detect_macd_bearish(self, df: pd.DataFrame) -> TechnicalSignal | None:
        """Detect MACD bearish crossover."""
        if len(df) < self.momentum_config.macd_slow:
            return None

        try:
            momentum_data = _momentum_input(df)
            macd_result = self.momentum_calc.calculate_macd(momentum_data)

            if (
                macd_result.signal == "bearish"
                or macd_result.signal == "strong_bearish"
            ):
                strength = (
                    "strong" if macd_result.signal == "strong_bearish" else "moderate"
                )

                return TechnicalSignal(
                    signal_type=PatternType.MACD_BEARISH,
                    strength=strength,
                    description="MACD Bearish: MACD line crossed below signal line",
                    date_detected=df.index[-1],
                    value=float(macd_result.macd_line),
                )
        except ValueError:
            pass

        return None

    def _detect_breakout(self, df: pd.DataFrame) -> TechnicalSignal | None:
        """Detect price breakout with volume confirmation."""
        if "volume" not in df.columns or len(df) < 20:
            return None

        high_20d = df["price"].rolling(window=20).max()
        avg_volume = df["volume"].rolling(window=20).mean()

        current_price = df["price"].iloc[-1]
        recent_high = high_20d.iloc[-2]
        current_volume = df["volume"].iloc[-1]
        recent_avg_volume = avg_volume.iloc[-1]

        if current_price > recent_high * _BREAKOUT_FACTOR:
            volume_multiplier = current_volume / recent_avg_volume

            if volume_multiplier > self.criteria.volume_multiplier:
                if volume_multiplier > 2.5:
                    strength = "strong"
                elif volume_multiplier > 2.0:
                    strength = "moderate"
                else:
                    strength = "weak"

                return TechnicalSignal(
                    signal_type=PatternType.BREAKOUT,
                    strength=strength,
                    description=f"Breakout: Price broke above 20-day high with {volume_multiplier:.1f}x volume",
                    date_detected=df.index[-1],
                    value=float(volume_multiplier),
                )

        return None

    def _detect_breakdown(self, df: pd.DataFrame) -> TechnicalSignal | None:
        """Detect price breakdown with volume confirmation."""
        if "volume" not in df.columns or len(df) < 20:
            return None

        low_20d = df["price"].rolling(window=20).min()
        avg_volume = df["volume"].rolling(window=20).mean()

        current_price = df["price"].iloc[-1]
        recent_low = low_20d.iloc[-2]
        current_volume = df["volume"].iloc[-1]
        recent_avg_volume = avg_volume.iloc[-1]

        if current_price < recent_low * _BREAKDOWN_FACTOR:
            volume_multiplier = current_volume / recent_avg_volume

            if volume_multiplier > self.criteria.volume_multiplier:
                if volume_multiplier > 2.5:
                    strength = "strong"
                elif volume_multiplier > 2.0:
                    strength = "moderate"
                else:
                    strength = "weak"

                return TechnicalSignal(
                    signal_type=PatternType.BREAKDOWN,
                    strength=strength,
                    description=f"Breakdown: Price broke below 20-day low with {volume_multiplier:.1f}x volume",
                    date_detected=df.index[-1],
                    value=float(volume_multiplier),
                )

        return None

    def _get_current_rsi(self, df: pd.DataFrame) -> float | None:
        """Get current RSI value."""
        if len(df) < self.momentum_config.rsi_period:
            return None

        try:
            momentum_data = _momentum_input(df)
            rsi_result = self.momentum_calc.calculate_rsi(momentum_data)
            return float(rsi_result.current_rsi)
        except ValueError:
            return None

    def _calculate_score(self, signals: list[TechnicalSignal]) -> float:
        """Calculate composite score from signals.

        SCORING:
        - Strong signal: +3 points
        - Moderate signal: +2 points
        - Weak signal: +1 point

        EDUCATIONAL NOTE:
        Higher scores indicate more compelling opportunities.
        A score of 6+ typically indicates multiple strong signals.
        """
        score = sum(_SIGNAL_POINTS[signal.strength] for signal in signals)
        return score * self.criteria.pattern_weight

    def _meets_criteria(self, signals: list[TechnicalSignal]) -> bool:
        """Determine if signals meet screening criteria.

        CRITERIA FOR MATCH:
        - At least 1 strong signal, OR
        - At least 2 moderate signals, OR
        - At least 3 weak signals

        EDUCATIONAL NOTE:
        These thresholds balance between finding opportunities
        and avoiding too many false signals.
        """
        counts = Counter(signal.strength for signal in signals)
        return any(
            counts[strength] >= minimum
            for strength, minimum in _MIN_SIGNALS_TO_MATCH.items()
        )

    def _generate_recommendation(
        self, signals: list[TechnicalSignal]
    ) -> tuple[str, float]:
        """Generate a recommendation from the direction of the signals.

        Bullish signals add their strength points and bearish signals subtract
        them, so bearish evidence never reads as a reason to buy.

        Returns:
            (recommendation, confidence)

        LOGIC (signed, weighted score):
        - >= 6: Strong Buy
        - >= 4: Buy
        - >= 2: Hold
        - < 2: Sell, or Strong Sell when a strong bearish signal dominates
        """
        if not signals:
            return ("hold", 0.5)

        directional_score = (
            sum(_signed_points(signal) for signal in signals)
            * self.criteria.pattern_weight
        )
        strong_net = sum(
            _signed_points(signal) for signal in signals if signal.strength == "strong"
        )

        if directional_score >= 6:
            return ("strong_buy", 0.85)
        elif directional_score >= 4:
            return ("buy", 0.70)
        elif directional_score >= 2:
            return ("hold", 0.55)
        elif strong_net < -2:
            return ("strong_sell", 0.75)
        else:
            return ("sell", 0.60)

    def _generate_notes(
        self, signals: list[TechnicalSignal], df: pd.DataFrame
    ) -> list[str]:
        """Generate helpful notes about the signals."""
        notes = []

        if not signals:
            notes.append("No technical signals detected")
            return notes

        signal_types = [s.signal_type for s in signals]

        if (
            PatternType.GOLDEN_CROSS in signal_types
            and PatternType.RSI_OVERSOLD in signal_types
        ):
            notes.append(
                "Strong setup: Golden cross combined with oversold RSI suggests bullish reversal"
            )

        if PatternType.BREAKOUT in signal_types:
            notes.append(
                "Volume-confirmed breakout increases probability of continuation"
            )

        if len([s for s in signals if s.strength == "strong"]) >= 2:
            notes.append("Multiple strong signals increase conviction")

        return notes

    def _generate_summary(
        self, results: list[ScreeningResult], matching_count: int
    ) -> str:
        """Generate human-readable summary."""
        total = len(results)

        if matching_count == 0:
            return f"Screened {total} tickers. No stocks met criteria."

        top_result = results[0] if results else None
        if not top_result:
            return f"Screened {total} tickers."

        return (
            f"Found {matching_count} of {total} tickers meeting criteria. "
            f"Top pick: {top_result.ticker} (score {top_result.score:.1f}, "
            f"{len(top_result.signals)} signals)"
        )


__all__ = [
    "TechnicalScreener",
]
