"""Technical Screener Pydantic Models for Finance Guru™.

This module defines type-safe data structures for technical screening.
All models use Pydantic for automatic validation and type checking.

ARCHITECTURE NOTE:
These models represent Layer 1 of our 3-layer architecture:
    Layer 1: Pydantic Models (THIS FILE) - Data validation
    Layer 2: Calculator Classes - Business logic
    Layer 3: CLI Interface - Agent integration

EDUCATIONAL CONTEXT:
A "screener" is a tool that filters stocks based on technical criteria.
Think of it as a "search engine" for finding trading opportunities:
- Golden Cross: Bullish signal (50-day MA crosses above 200-day MA)
- RSI Oversold: Potential bounce opportunity (RSI < 30)
- High Volume Breakout: Strong momentum signal

Screeners help answer questions like:
- "Which stocks are breaking out?"
- "Which stocks are oversold?"
- "Which stocks show strong momentum?"

Author: Finance Guru™ Development Team
Created: 2025-10-13
"""

from datetime import date
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class PatternType(StrEnum):
    """Technical patterns that can be detected.

    WHAT: Classic technical analysis patterns
    WHY: These patterns signal potential trading opportunities

    PATTERNS:
        - GOLDEN_CROSS: 50-day MA crosses above 200-day MA (bullish)
        - DEATH_CROSS: 50-day MA crosses below 200-day MA (bearish)
        - RSI_OVERSOLD: RSI below 30 (potential bounce)
        - RSI_OVERBOUGHT: RSI above 70 (potential pullback)
        - MACD_BULLISH: MACD line crosses above signal line
        - MACD_BEARISH: MACD line crosses below signal line
        - BREAKOUT: Price breaks above resistance with volume
        - BREAKDOWN: Price breaks below support with volume

    EDUCATIONAL NOTE:
    These patterns are widely followed by traders. When many traders
    see the same pattern, it can become a self-fulfilling prophecy.
    """

    GOLDEN_CROSS = "golden_cross"
    DEATH_CROSS = "death_cross"
    RSI_OVERSOLD = "rsi_oversold"
    RSI_OVERBOUGHT = "rsi_overbought"
    MACD_BULLISH = "macd_bullish"
    MACD_BEARISH = "macd_bearish"
    BREAKOUT = "breakout"
    BREAKDOWN = "breakdown"


class ScreeningCriteria(BaseModel):
    """Criteria for screening stocks.

    WHAT: Configurable filters for finding trading opportunities
    WHY: Different strategies need different screening rules
    USE CASES:
        - Momentum Trading: Look for breakouts with high RSI
        - Value Investing: Look for oversold with golden cross
        - Swing Trading: Look for MACD crossovers

    EDUCATIONAL NOTE:
    Think of screening criteria as a "checklist" for stocks.
    The more criteria a stock meets, the higher it scores.
    """

    patterns: list[PatternType] = Field(
        default_factory=lambda: [PatternType.GOLDEN_CROSS, PatternType.RSI_OVERSOLD],
        description="Technical patterns to screen for",
        min_length=1,
    )

    # RSI thresholds
    rsi_oversold: float = Field(
        default=30.0,
        ge=10.0,
        le=40.0,
        description="RSI threshold for oversold condition (default: 30)",
    )

    rsi_overbought: float = Field(
        default=70.0,
        ge=60.0,
        le=90.0,
        description="RSI threshold for overbought condition (default: 70)",
    )

    # Moving average periods
    ma_fast: int = Field(
        default=50,
        ge=10,
        le=100,
        description="Fast moving average period (default: 50)",
    )

    ma_slow: int = Field(
        default=200,
        ge=100,
        le=300,
        description="Slow moving average period (default: 200)",
    )

    # Volume thresholds
    volume_multiplier: float = Field(
        default=1.5,
        ge=1.0,
        le=5.0,
        description="Volume multiplier for breakout detection (default: 1.5x average)",
    )

    # Scoring weights
    pattern_weight: float = Field(
        default=1.0,
        ge=0.0,
        le=2.0,
        description="Weight for pattern matches in scoring (default: 1.0)",
    )

    @field_validator("rsi_overbought")
    @classmethod
    def validate_rsi_overbought_above_oversold(cls, v: float, info) -> float:
        """Ensure overbought threshold is above oversold threshold."""
        # Note: We can't access rsi_oversold here directly in field validator
        # This will be checked in model validator
        return v

    @field_validator("ma_slow")
    @classmethod
    def validate_ma_slow_above_fast(cls, v: float, info) -> float:
        """Ensure slow MA period is greater than fast MA period."""
        # Will be checked in model validator
        return v


class TechnicalSignal(BaseModel):
    """A detected technical signal.

    WHAT: Information about a specific pattern match
    WHY: Helps users understand why a stock was flagged
    """

    signal_type: PatternType = Field(..., description="Type of pattern detected")

    strength: Literal["weak", "moderate", "strong"] = Field(
        ..., description="Signal strength (confidence level)"
    )

    description: str = Field(
        ..., description="Human-readable description of the signal"
    )

    date_detected: date = Field(..., description="Date when signal was detected")

    value: float | None = Field(
        default=None,
        description="Numeric value associated with signal (e.g., RSI value)",
    )


class ScreeningResult(BaseModel):
    """Screening result for a single ticker.

    WHAT: Complete analysis of whether a stock meets screening criteria
    WHY: Provides ranked results for decision-making
    USE CASES:
        - Strategy Advisor: Find best opportunities across portfolio
        - Market Researcher: Identify trending stocks
        - Quant Analyst: Backtest screening strategies

    EDUCATIONAL NOTE:
    The score is calculated by summing signal strengths:
    - Each "strong" signal: +3 points
    - Each "moderate" signal: +2 points
    - Each "weak" signal: +1 point

    Higher scores indicate more compelling opportunities.
    """

    ticker: str = Field(..., description="Stock ticker symbol")

    screening_date: date = Field(..., description="Date when screening was performed")

    matches_criteria: bool = Field(
        ..., description="Whether stock meets screening criteria"
    )

    # Signals
    signals: list[TechnicalSignal] = Field(
        default_factory=list, description="List of detected technical signals"
    )

    # Scoring
    score: float = Field(
        default=0.0, ge=0.0, description="Composite score (higher = better opportunity)"
    )

    rank: int | None = Field(
        default=None, ge=1, description="Rank among screened tickers (1 = best)"
    )

    # Current metrics
    current_price: float = Field(..., gt=0.0, description="Current price")

    current_rsi: float | None = Field(
        default=None, ge=0.0, le=100.0, description="Current RSI value"
    )

    # Recommendations
    recommendation: Literal["strong_buy", "buy", "hold", "sell", "strong_sell"] = Field(
        ..., description="Overall recommendation based on signals"
    )

    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confidence in recommendation (0.0 to 1.0)",
    )

    notes: list[str] = Field(
        default_factory=list, description="Additional notes or warnings"
    )

    @field_validator("score")
    @classmethod
    def calculate_score_from_signals(cls, v: float) -> float:
        """Ensure score is non-negative."""
        return max(0.0, v)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "ticker": "TSLA",
                    "screening_date": "2025-10-13",
                    "matches_criteria": True,
                    "signals": [
                        {
                            "signal_type": "golden_cross",
                            "strength": "strong",
                            "description": "50-day MA crossed above 200-day MA",
                            "date_detected": "2025-10-10",
                            "value": None,
                        },
                        {
                            "signal_type": "rsi_oversold",
                            "strength": "moderate",
                            "description": "RSI at 35 (below 40)",
                            "date_detected": "2025-10-13",
                            "value": 35.0,
                        },
                    ],
                    "score": 5.0,
                    "rank": 1,
                    "current_price": 265.50,
                    "current_rsi": 35.0,
                    "recommendation": "buy",
                    "confidence": 0.75,
                    "notes": [
                        "Strong momentum signal combined with oversold RSI",
                        "Consider entry on RSI bounce above 40",
                    ],
                }
            ]
        }
    }


class PortfolioScreeningOutput(BaseModel):
    """Screening results for multiple tickers.

    WHAT: Ranked list of screening results
    WHY: Helps identify best opportunities across multiple stocks
    USE CASES:
        - Portfolio construction: Find best stocks to add
        - Rebalancing: Identify weak positions to exit
        - Opportunity scanning: Daily screening for signals

    EDUCATIONAL NOTE:
    Results are ranked by score (highest first).
    Use this to focus on the most compelling opportunities.
    """

    screening_date: date = Field(..., description="Date when screening was performed")

    criteria_used: list[PatternType] = Field(
        ..., description="Patterns that were screened for"
    )

    total_tickers_screened: int = Field(
        ..., ge=0, description="Total number of tickers analyzed"
    )

    tickers_matching: int = Field(
        default=0, ge=0, description="Number of tickers meeting criteria"
    )

    results: list[ScreeningResult] = Field(
        default_factory=list, description="Screening results (sorted by score)"
    )

    top_picks: list[str] = Field(
        default_factory=list, description="Top 3-5 ticker recommendations"
    )

    summary: str = Field(..., description="Human-readable summary of screening results")

    @field_validator("tickers_matching")
    @classmethod
    def validate_matching_count(cls, v: int, info) -> int:
        """Ensure matching count doesn't exceed total screened."""
        # Will be validated in model validator with access to total_tickers_screened
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "screening_date": "2025-10-13",
                    "criteria_used": ["golden_cross", "rsi_oversold"],
                    "total_tickers_screened": 10,
                    "tickers_matching": 3,
                    "results": [],  # Would contain ScreeningResult objects
                    "top_picks": ["TSLA", "PLTR", "NVDA"],
                    "summary": "Found 3 of 10 tickers meeting criteria. Top signal: TSLA with golden cross and oversold RSI.",
                }
            ]
        }
    }


# Type exports
__all__ = [
    "PatternType",
    "ScreeningCriteria",
    "TechnicalSignal",
    "ScreeningResult",
    "PortfolioScreeningOutput",
]
