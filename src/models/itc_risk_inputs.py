"""ITC Risk Models Pydantic Models for Finance Guru™.

This module defines type-safe data structures for ITC (Into The Cryptoverse)
Risk API integration.

ARCHITECTURE NOTE:
These models represent Layer 1 of our 3-layer architecture:
    Layer 1: Pydantic Models (THIS FILE) - Data validation
    Layer 2: Calculator Classes - Business logic (src/analysis/itc_risk.py)
    Layer 3: CLI Interface - Agent integration (src/analysis/itc_risk_cli.py)

EDUCATIONAL CONTEXT:
- ITC Risk provides market-implied risk scores (0-1) based on price action
- Risk bands show how risk changes at different price levels
- This complements our internal VaR/Sharpe metrics with external perspective
- Think of ITC as a "second opinion" on risk from market sentiment

SUPPORTED TICKERS:
    TradFi: TSLA, AAPL, MSTR, NFLX, SP500, DXY, XAUUSD, XAGUSD, XPDUSD, PL, HG, NICKEL
    Crypto: BTC, ETH, BNB, SOL, XRP, ADA, DOGE, LINK, and 21 others

Author: Finance Guru™ Development Team
Created: 2026-01-09
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ITCRiskRequest(BaseModel):
    """Request model for ITC Risk API calls.

    WHAT: Encapsulates parameters needed to query ITC Risk API
    WHY: Ensures request parameters are validated before making API calls
    VALIDATES:
        - Symbol is uppercase and properly formatted
        - Universe is either "crypto" or "tradfi"
        - API key is provided

    USAGE EXAMPLE:
        request = ITCRiskRequest(
            symbol="TSLA",
            universe="tradfi",
            api_key="your_api_key_here"
        )
    """

    symbol: str = Field(
        ...,
        description="Asset symbol (e.g., TSLA, BTC, AAPL)",
        min_length=1,
        max_length=20,
    )

    universe: Literal["crypto", "tradfi"] = Field(
        ...,
        description=(
            "Asset universe for the ITC API:\n"
            "  - 'tradfi': Traditional finance (stocks, indices, commodities)\n"
            "  - 'crypto': Cryptocurrency assets"
        ),
    )

    api_key: str = Field(
        ...,
        description="ITC API key from environment (ITC_API_KEY)",
        min_length=1,
    )

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, v: str) -> str:
        """Normalize symbol to uppercase.

        EDUCATIONAL NOTE:
        ITC API expects uppercase symbols. We normalize to avoid
        case-sensitivity issues (e.g., "tsla" → "TSLA").
        """
        return v.upper().strip()

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"symbol": "TSLA", "universe": "tradfi", "api_key": "your_itc_api_key"},
                {"symbol": "BTC", "universe": "crypto", "api_key": "your_itc_api_key"},
            ]
        }
    }


class RiskBand(BaseModel):
    """Individual price band with associated risk score.

    WHAT: Maps a price level to its corresponding risk score
    WHY: ITC provides a table of price → risk mappings to understand
         how risk changes as price moves up or down

    EDUCATIONAL NOTE:
    Risk bands help answer: "If the price moves to $X, what's the risk?"
    - Low prices often have low risk scores (buying dips is lower risk)
    - High prices often have high risk scores (buying near ATH is higher risk)
    - But this varies by asset and market conditions!

    USAGE EXAMPLE:
        band = RiskBand(price=450.15, risk_score=0.489)
        # At $450.15, TSLA has ~49% risk level
    """

    price: float = Field(
        ...,
        description="Price level for this risk band",
        gt=0.0,  # Prices must be positive
    )

    risk_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description=(
            "Risk score at this price level (0-1 scale):\n"
            "  - 0.0-0.3: Low risk (green zone)\n"
            "  - 0.3-0.7: Medium risk (yellow zone)\n"
            "  - 0.7-1.0: High risk (red zone)"
        ),
    )

    @field_validator("price")
    @classmethod
    def validate_price_positive(cls, v: float) -> float:
        """Ensure price is a positive value.

        WHY: Prices cannot be zero or negative. A zero price would
        indicate a delisted asset or data error.
        """
        if v <= 0:
            raise ValueError(
                f"Price must be positive (got {v}). Check your data source for errors."
            )
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"price": 221.90, "risk_score": 0.0},
                {"price": 450.15, "risk_score": 0.489},
                {"price": 1526.19, "risk_score": 0.991},
            ]
        }
    }


class ITCRiskResponse(BaseModel):
    """Response from ITC API with comprehensive risk data.

    WHAT: Complete risk analysis result including current risk and price bands
    WHY: Provides structured, validated output for agents to consume
    USE CASES:
        - Market Researcher: Quick risk check before analysis
        - Strategy Advisor: Pre-trade risk validation
        - Quant Analyst: Cross-reference with internal metrics
        - Compliance Officer: Risk limit monitoring

    EDUCATIONAL NOTE:
    The response includes:
    - current_risk_score: Where we are NOW on the risk scale
    - risk_bands: The full price→risk mapping table
    - current_price: Live price from yfinance (for context)

    Key interpretation:
    - current_risk_score < 0.3: Lower risk entry zone
    - current_risk_score 0.3-0.7: Neutral, use other signals
    - current_risk_score > 0.7: HIGH RISK - caution advised!

    USAGE EXAMPLE:
        response = ITCRiskResponse(
            symbol="TSLA",
            universe="tradfi",
            current_price=450.0,
            current_risk_score=0.49,
            risk_bands=[...],
            timestamp=datetime.now()
        )

        # Get nearest bands to current price
        nearest = response.get_nearest_bands(5)

        # Find high risk threshold
        high_risk = response.get_high_risk_threshold()
    """

    symbol: str = Field(..., description="Asset symbol (uppercase)")

    universe: str = Field(..., description="Asset universe ('crypto' or 'tradfi')")

    current_price: float | None = Field(
        default=None,
        description=(
            "Current market price from yfinance (for tradfi assets). "
            "May be None if price enrichment is disabled or fails."
        ),
        gt=0.0,
    )

    current_risk_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description=(
            "Current risk score from ITC (0-1 scale). "
            "This is the PRIMARY output - the risk level right now.\n"
            "  < 0.3: LOW risk\n"
            "  0.3-0.7: MEDIUM risk\n"
            "  > 0.7: HIGH risk - exercise caution!"
        ),
    )

    risk_bands: list[RiskBand] = Field(
        default_factory=list,
        description="List of price levels with associated risk scores",
    )

    timestamp: datetime = Field(..., description="Timestamp when data was fetched")

    source: str = Field(
        default="Into The Cryptoverse API", description="Data source identifier"
    )

    @field_validator("symbol")
    @classmethod
    def normalize_symbol_upper(cls, v: str) -> str:
        """Ensure symbol is uppercase."""
        return v.upper()

    def get_nearest_bands(self, n: int = 5) -> list[RiskBand]:
        """Get n nearest bands around current price.

        This helps answer: "What does risk look like around the current price?"
        Useful for understanding immediate up/down risk changes.

        Args:
            n: Number of bands to return (default: 5)

        Returns:
            List of n RiskBand objects closest to current_price,
            sorted by distance. If no current_price, returns first n bands.

        EDUCATIONAL NOTE:
        Nearest bands show the local risk landscape. If you see:
        - Lower bands with LOW risk → room to fall before risk increases
        - Higher bands with HIGH risk → approaching danger zone

        USAGE:
            nearest = response.get_nearest_bands(5)
            for band in nearest:
                print(f"${band.price:.2f}: {band.risk_score:.2f}")
        """
        if not self.current_price or not self.risk_bands:
            return self.risk_bands[:n]

        # Sort by distance from current price
        sorted_bands = sorted(
            self.risk_bands, key=lambda b: abs(b.price - self.current_price)
        )
        return sorted_bands[:n]

    def get_high_risk_threshold(self) -> RiskBand | None:
        """Find price where risk exceeds 0.7 (high risk zone).

        This answers: "At what price does this become HIGH RISK?"
        Critical for setting alerts and understanding upside limits.

        Returns:
            The first RiskBand where risk_score >= 0.7,
            sorted by price (lowest high-risk price first).
            Returns None if no high-risk bands exist.

        EDUCATIONAL NOTE:
        Use this to:
        - Set price alerts ("warn me when approaching high risk")
        - Calculate distance to danger zone
        - Plan exit strategies before risk becomes extreme

        USAGE:
            high_risk = response.get_high_risk_threshold()
            if high_risk and response.current_price:
                distance = (high_risk.price / response.current_price - 1) * 100
                print(f"High risk zone is {distance:.1f}% away")
        """
        high_risk_bands = [band for band in self.risk_bands if band.risk_score >= 0.7]

        if not high_risk_bands:
            return None

        # Return the lowest price that's high risk
        return min(high_risk_bands, key=lambda b: b.price)

    def get_risk_interpretation(self) -> str:
        """Get human-readable interpretation of current risk level.

        Returns:
            String description of risk level with guidance.

        EDUCATIONAL NOTE:
        Provides actionable context for the raw risk score.
        """
        score = self.current_risk_score

        if score < 0.3:
            return "LOW RISK - Favorable entry zone, lower probability of significant decline"
        elif score < 0.7:
            return (
                "MEDIUM RISK - Neutral zone, use additional signals for decision making"
            )
        else:
            return "HIGH RISK - Elevated risk of decline, consider waiting for pullback"

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "symbol": "TSLA",
                    "universe": "tradfi",
                    "current_price": 441.87,
                    "current_risk_score": 0.489,
                    "risk_bands": [
                        {"price": 221.90, "risk_score": 0.0},
                        {"price": 450.15, "risk_score": 0.489},
                        {"price": 1526.19, "risk_score": 0.991},
                    ],
                    "timestamp": "2026-01-09T12:00:00",
                    "source": "Into The Cryptoverse API",
                }
            ]
        }
    }


# Type exports for convenience
__all__ = [
    "ITCRiskRequest",
    "RiskBand",
    "ITCRiskResponse",
]
