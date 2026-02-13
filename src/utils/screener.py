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

from datetime import date

import pandas as pd

# Import existing momentum and MA calculators
from src.models.momentum_inputs import MomentumConfig, MomentumDataInput
from src.models.screener_inputs import (
    PatternType,
    PortfolioScreeningOutput,
    ScreeningCriteria,
    ScreeningResult,
    TechnicalSignal,
)
from src.utils.momentum import MomentumIndicators


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

        # Create momentum calculator
        self.momentum_config = MomentumConfig(
            rsi_period=14,  # Standard RSI period
            macd_fast=12,
            macd_slow=26,
            macd_signal=9,
        )
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
        # Convert to pandas for easier analysis
        df = pd.DataFrame(
            {
                "date": dates,
                "price": prices,
            }
        )
        if volumes:
            df["volume"] = volumes
        df = df.set_index("date")

        # Initialize signals list
        signals: list[TechnicalSignal] = []

        # Check each pattern in criteria
        for pattern in self.criteria.patterns:
            signal = self._detect_pattern(ticker, pattern, df)
            if signal:
                signals.append(signal)

        # Calculate score
        score = self._calculate_score(signals)

        # Determine if matches criteria (needs at least 1 strong or 2 moderate signals)
        matches = self._matches_criteria(signals)

        # Generate recommendation
        recommendation, confidence = self._generate_recommendation(signals, score)

        # Get current metrics
        current_price = float(df["price"].iloc[-1])
        current_rsi = self._get_current_rsi(df)

        # Generate notes
        notes = self._generate_notes(signals, df)

        return ScreeningResult(
            ticker=ticker,
            screening_date=dates[-1] if dates else date.today(),
            matches_criteria=matches,
            signals=signals,
            score=score,
            rank=None,  # Will be set when ranking multiple tickers
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

        # Screen each ticker
        for ticker, (prices, dates, volumes) in tickers_data.items():
            try:
                result = self.screen_ticker(ticker, prices, dates, volumes)
                results.append(result)
            except Exception as e:
                # Skip tickers that fail to screen
                print(f"Warning: Skipping {ticker} - {e}")
                continue

        # Sort by score (descending)
        results.sort(key=lambda r: r.score, reverse=True)

        # Assign ranks
        for rank, result in enumerate(results, start=1):
            result.rank = rank

        # Count matching
        matching_count = sum(1 for r in results if r.matches_criteria)

        # Get top picks (top 5 or fewer)
        top_picks = [r.ticker for r in results[:5] if r.matches_criteria]

        # Generate summary
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
            if pattern == PatternType.GOLDEN_CROSS:
                return self._detect_golden_cross(df)
            elif pattern == PatternType.DEATH_CROSS:
                return self._detect_death_cross(df)
            elif pattern == PatternType.RSI_OVERSOLD:
                return self._detect_rsi_oversold(df)
            elif pattern == PatternType.RSI_OVERBOUGHT:
                return self._detect_rsi_overbought(df)
            elif pattern == PatternType.MACD_BULLISH:
                return self._detect_macd_bullish(df)
            elif pattern == PatternType.MACD_BEARISH:
                return self._detect_macd_bearish(df)
            elif pattern == PatternType.BREAKOUT:
                return self._detect_breakout(df)
            elif pattern == PatternType.BREAKDOWN:
                return self._detect_breakdown(df)
            else:
                return None
        except Exception as e:
            # If detection fails, log for debugging (in production, would use logging module)
            # For now, silently skip failed patterns but allow non-failing ones to proceed
            import sys

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

        # Calculate moving averages
        ma50 = df["price"].rolling(window=self.criteria.ma_fast).mean()
        ma200 = df["price"].rolling(window=self.criteria.ma_slow).mean()

        # Check for recent crossover (within last 10 days)
        recent_df = df.iloc[-10:]
        recent_ma50 = ma50.iloc[-10:]
        recent_ma200 = ma200.iloc[-10:]

        # Look for crossover: MA50 was below MA200, now above
        for i in range(1, len(recent_df)):
            prev_below = recent_ma50.iloc[i - 1] < recent_ma200.iloc[i - 1]
            now_above = recent_ma50.iloc[i] > recent_ma200.iloc[i]

            if prev_below and now_above:
                # Golden cross detected!
                crossover_date = recent_df.index[i]

                # Determine strength based on how decisive the cross was
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
                    strength=strength,  # type: ignore
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
                    strength=strength,  # type: ignore
                    description=f"Death Cross: {self.criteria.ma_fast}MA crossed below {self.criteria.ma_slow}MA",
                    date_detected=crossover_date,
                    value=float(separation_pct),
                )

        return None

    def _detect_rsi_oversold(self, df: pd.DataFrame) -> TechnicalSignal | None:
        """Detect RSI oversold condition."""
        if len(df) < 14:
            return None

        # Calculate RSI using existing momentum calculator
        try:
            momentum_data = MomentumDataInput(
                ticker="TEMP",
                prices=df["price"].tolist(),
                dates=df.index.tolist(),
            )
            rsi_result = self.momentum_calc.calculate_rsi(momentum_data)

            current_rsi = rsi_result.current_rsi

            if current_rsi < self.criteria.rsi_oversold:
                # Determine strength based on how oversold
                if current_rsi < 20:
                    strength = "strong"
                elif current_rsi < 25:
                    strength = "moderate"
                else:
                    strength = "weak"

                return TechnicalSignal(
                    signal_type=PatternType.RSI_OVERSOLD,
                    strength=strength,  # type: ignore
                    description=f"RSI Oversold: RSI at {current_rsi:.1f} (below {self.criteria.rsi_oversold})",
                    date_detected=df.index[-1],
                    value=float(current_rsi),
                )
        except Exception:
            pass

        return None

    def _detect_rsi_overbought(self, df: pd.DataFrame) -> TechnicalSignal | None:
        """Detect RSI overbought condition."""
        if len(df) < 14:
            return None

        try:
            momentum_data = MomentumDataInput(
                ticker="TEMP",
                prices=df["price"].tolist(),
                dates=df.index.tolist(),
            )
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
                    strength=strength,  # type: ignore
                    description=f"RSI Overbought: RSI at {current_rsi:.1f} (above {self.criteria.rsi_overbought})",
                    date_detected=df.index[-1],
                    value=float(current_rsi),
                )
        except Exception:
            pass

        return None

    def _detect_macd_bullish(self, df: pd.DataFrame) -> TechnicalSignal | None:
        """Detect MACD bullish crossover."""
        if len(df) < 26:
            return None

        try:
            momentum_data = MomentumDataInput(
                ticker="TEMP",
                prices=df["price"].tolist(),
                dates=df.index.tolist(),
            )
            macd_result = self.momentum_calc.calculate_macd(momentum_data)

            # Check if MACD line recently crossed above signal line
            if (
                macd_result.signal == "bullish"
                or macd_result.signal == "strong_bullish"
            ):
                strength = (
                    "strong" if macd_result.signal == "strong_bullish" else "moderate"
                )

                return TechnicalSignal(
                    signal_type=PatternType.MACD_BULLISH,
                    strength=strength,  # type: ignore
                    description="MACD Bullish: MACD line crossed above signal line",
                    date_detected=df.index[-1],
                    value=float(macd_result.macd_line),
                )
        except Exception:
            pass

        return None

    def _detect_macd_bearish(self, df: pd.DataFrame) -> TechnicalSignal | None:
        """Detect MACD bearish crossover."""
        if len(df) < 26:
            return None

        try:
            momentum_data = MomentumDataInput(
                ticker="TEMP",
                prices=df["price"].tolist(),
                dates=df.index.tolist(),
            )
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
                    strength=strength,  # type: ignore
                    description="MACD Bearish: MACD line crossed below signal line",
                    date_detected=df.index[-1],
                    value=float(macd_result.macd_line),
                )
        except Exception:
            pass

        return None

    def _detect_breakout(self, df: pd.DataFrame) -> TechnicalSignal | None:
        """Detect price breakout with volume confirmation."""
        if "volume" not in df.columns or len(df) < 20:
            return None

        # Calculate 20-day high and average volume
        high_20d = df["price"].rolling(window=20).max()
        avg_volume = df["volume"].rolling(window=20).mean()

        current_price = df["price"].iloc[-1]
        recent_high = high_20d.iloc[-2]  # High before today
        current_volume = df["volume"].iloc[-1]
        recent_avg_volume = avg_volume.iloc[-1]

        # Check if price broke above recent high with volume
        if current_price > recent_high * 1.01:  # 1% above high
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
                    strength=strength,  # type: ignore
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

        if current_price < recent_low * 0.99:  # 1% below low
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
                    strength=strength,  # type: ignore
                    description=f"Breakdown: Price broke below 20-day low with {volume_multiplier:.1f}x volume",
                    date_detected=df.index[-1],
                    value=float(volume_multiplier),
                )

        return None

    def _get_current_rsi(self, df: pd.DataFrame) -> float | None:
        """Get current RSI value."""
        if len(df) < 14:
            return None

        try:
            momentum_data = MomentumDataInput(
                ticker="TEMP",
                prices=df["price"].tolist(),
                dates=df.index.tolist(),
            )
            rsi_result = self.momentum_calc.calculate_rsi(momentum_data)
            return float(rsi_result.current_rsi)
        except Exception:
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
        score = 0.0
        for signal in signals:
            if signal.strength == "strong":
                score += 3.0
            elif signal.strength == "moderate":
                score += 2.0
            else:  # weak
                score += 1.0

        return score * self.criteria.pattern_weight

    def _matches_criteria(self, signals: list[TechnicalSignal]) -> bool:
        """Determine if signals meet screening criteria.

        CRITERIA FOR MATCH:
        - At least 1 strong signal, OR
        - At least 2 moderate signals, OR
        - At least 3 weak signals

        EDUCATIONAL NOTE:
        These thresholds balance between finding opportunities
        and avoiding too many false signals.
        """
        if not signals:
            return False

        strong_count = sum(1 for s in signals if s.strength == "strong")
        moderate_count = sum(1 for s in signals if s.strength == "moderate")
        weak_count = sum(1 for s in signals if s.strength == "weak")

        return (strong_count >= 1) or (moderate_count >= 2) or (weak_count >= 3)

    def _generate_recommendation(
        self, signals: list[TechnicalSignal], score: float
    ) -> tuple[str, float]:
        """Generate recommendation based on signals.

        Returns:
            (recommendation, confidence)

        LOGIC:
        - Score >= 6: Strong Buy (high confidence)
        - Score >= 4: Buy (moderate confidence)
        - Score >= 2: Hold (low confidence)
        - Score < 2: Sell/Strong Sell
        """
        if not signals:
            return ("hold", 0.5)

        # Count bullish vs bearish signals
        bullish_patterns = {
            PatternType.GOLDEN_CROSS,
            PatternType.RSI_OVERSOLD,
            PatternType.MACD_BULLISH,
            PatternType.BREAKOUT,
        }
        bearish_patterns = {
            PatternType.DEATH_CROSS,
            PatternType.RSI_OVERBOUGHT,
            PatternType.MACD_BEARISH,
            PatternType.BREAKDOWN,
        }

        bullish_score = (
            sum(
                s.strength == "strong" and s.signal_type in bullish_patterns
                for s in signals
            )
            * 3
        )
        bearish_score = (
            sum(
                s.strength == "strong" and s.signal_type in bearish_patterns
                for s in signals
            )
            * 3
        )

        net_score = bullish_score - bearish_score

        if score >= 6:
            return ("strong_buy", 0.85)
        elif score >= 4:
            return ("buy", 0.70)
        elif score >= 2:
            return ("hold", 0.55)
        elif net_score < -2:
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

        # Group signals by type
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


# Type exports
__all__ = [
    "TechnicalScreener",
]
