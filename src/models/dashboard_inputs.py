"""Dashboard Pydantic Models for Finance Guru™ TUI.

WHAT: Data models for TUI dashboard portfolio display and analysis
WHY: Type-safe portfolio snapshots and holdings for real-time dashboard updates
ARCHITECTURE: Layer 1 of 3-layer type-safe architecture

Used by: TUI Dashboard (portfolio header, results panel), Portfolio Loader (CSV parsing)

Author: Finance Guru™ Development Team
Created: 2025-11-17
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, computed_field, field_validator


class HoldingInput(BaseModel):
    """Individual portfolio holding from Fidelity CSV.

    WHAT: Single stock/ETF/fund position in portfolio
    WHY: Represents one row from Fidelity CSV with layer classification
    VALIDATES:
        - Symbol is uppercase and valid ticker format
        - Quantities and values are non-negative
        - Layer is one of: layer1, layer2, layer3, unknown

    EDUCATIONAL NOTE:
    Layer classification determines portfolio strategy:
    - Layer 1: Growth stocks (PLTR, TSLA, NVDA) - HOLD 100%, never touch
    - Layer 2: Income funds (JEPI, JEPQ, etc.) - Build with W2 income
    - Layer 3: Hedges (SQQQ) - Downside protection

    USAGE EXAMPLE:
        holding = HoldingInput(
            symbol="PLTR",
            quantity=369.746,
            current_value=64583.53,
            day_change=935.45,
            day_change_pct=1.46,
            layer="layer1"
        )
    """

    symbol: str = Field(
        ...,
        description="Stock ticker symbol (e.g., 'PLTR', 'JEPI')",
        min_length=1,
        max_length=10,
    )

    quantity: float = Field(..., ge=0.0, description="Number of shares/units held")

    current_value: float = Field(..., ge=0.0, description="Current market value in USD")

    day_change: float = Field(
        ..., description="Today's gain/loss in USD (can be negative)"
    )

    day_change_pct: float = Field(..., description="Today's gain/loss as percentage")

    layer: Literal["layer1", "layer2", "layer3", "unknown"] = Field(
        ..., description="Portfolio layer classification"
    )

    @field_validator("symbol")
    @classmethod
    def symbol_must_be_uppercase(cls, v: str) -> str:
        """Ensure ticker symbol is uppercase and valid format.

        WHY: Standard convention for ticker symbols. Prevents matching
        errors when comparing tickers across different data sources.

        EDUCATIONAL NOTE:
        Ticker symbols are always uppercase by convention:
        - PLTR (correct)
        - pltr (incorrect)
        - PLTR123 (invalid - contains numbers)
        """
        if not v.isupper():
            raise ValueError(
                f"Ticker symbol '{v}' must be uppercase (e.g., 'PLTR' not 'pltr')"
            )

        if not v.isalpha():
            raise ValueError(
                f"Ticker symbol '{v}' must contain only letters (no numbers or symbols)"
            )

        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "symbol": "PLTR",
                    "quantity": 369.746,
                    "current_value": 64583.53,
                    "day_change": 935.45,
                    "day_change_pct": 1.46,
                    "layer": "layer1",
                },
                {
                    "symbol": "JEPI",
                    "quantity": 72.942,
                    "current_value": 4142.64,
                    "day_change": -4.03,
                    "day_change_pct": -0.10,
                    "layer": "layer2",
                },
            ]
        }
    }


class PortfolioSnapshotInput(BaseModel):
    """Complete portfolio snapshot from Fidelity CSV.

    WHAT: Aggregated portfolio data with all holdings and totals
    WHY: Provides dashboard header data and layer breakdown
    VALIDATES:
        - Total value matches sum of holdings
        - Day change matches sum of holding changes
        - At least one holding present
        - Timestamp is reasonable (not in future)

    EDUCATIONAL NOTE:
    This model represents the entire portfolio at a point in time.
    Dashboard displays this in the header:
        "Portfolio: $222,214.99 | Day: -$4,091 (-1.80%) | Nov 17, 2025 3:33pm"

    Layer breakdowns show allocation strategy:
        - Layer 1: $180,536 (81%) - Growth (keep 100%)
        - Layer 2:  $28,732 (13%) - Income (building)
        - Layer 3:  $12,947  (6%) - Hedge (protection)

    USAGE EXAMPLE:
        snapshot = PortfolioSnapshotInput(
            total_value=222214.99,
            day_change=-4091.32,
            day_change_pct=-1.80,
            holdings=[holding1, holding2, ...],
            timestamp=datetime.now()
        )
    """

    total_value: float = Field(..., ge=0.0, description="Total portfolio value in USD")

    day_change: float = Field(
        ..., description="Total day change in USD (can be negative)"
    )

    day_change_pct: float = Field(..., description="Total day change as percentage")

    holdings: list[HoldingInput] = Field(
        ..., min_length=1, description="List of all portfolio holdings"
    )

    timestamp: datetime = Field(..., description="When this snapshot was created")

    @field_validator("holdings")
    @classmethod
    def holdings_must_not_be_empty(cls, v: list[HoldingInput]) -> list[HoldingInput]:
        """Ensure at least one holding exists.

        WHY: Empty portfolio doesn't make sense for dashboard display.
        If portfolio is truly empty, we should show a different view.

        EDUCATIONAL NOTE:
        An empty holdings list indicates either:
        1. CSV parsing failed
        2. Portfolio was liquidated (unlikely)
        3. Data source error

        Dashboard should handle this gracefully.
        """
        if not v:
            raise ValueError(
                "Portfolio snapshot must contain at least one holding. "
                "Check Fidelity CSV data."
            )
        return v

    @field_validator("timestamp")
    @classmethod
    def timestamp_must_be_reasonable(cls, v: datetime) -> datetime:
        """Ensure timestamp is not in the future.

        WHY: Future timestamps indicate system clock issues or data errors.
        A snapshot from "tomorrow" doesn't make sense.

        EDUCATIONAL NOTE:
        We allow timestamps up to 1 minute in the future to handle
        clock skew between systems, but anything more is suspicious.
        """
        now = datetime.now()
        future_threshold = 60  # 1 minute

        if (v - now).total_seconds() > future_threshold:
            raise ValueError(
                f"Timestamp {v} is in the future (now: {now}). "
                "Check system clock or data source."
            )

        return v

    @computed_field
    @property
    def layer1_value(self) -> float:
        """Calculate total value of Layer 1 (growth) holdings."""
        return sum(h.current_value for h in self.holdings if h.layer == "layer1")

    @computed_field
    @property
    def layer2_value(self) -> float:
        """Calculate total value of Layer 2 (income) holdings."""
        return sum(h.current_value for h in self.holdings if h.layer == "layer2")

    @computed_field
    @property
    def layer3_value(self) -> float:
        """Calculate total value of Layer 3 (hedge) holdings."""
        return sum(h.current_value for h in self.holdings if h.layer == "layer3")

    @computed_field
    @property
    def layer1_pct(self) -> float:
        """Layer 1 as percentage of total portfolio."""
        return (self.layer1_value / self.total_value * 100) if self.total_value else 0.0

    @computed_field
    @property
    def layer2_pct(self) -> float:
        """Layer 2 as percentage of total portfolio."""
        return (self.layer2_value / self.total_value * 100) if self.total_value else 0.0

    @computed_field
    @property
    def layer3_pct(self) -> float:
        """Layer 3 as percentage of total portfolio."""
        return (self.layer3_value / self.total_value * 100) if self.total_value else 0.0

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "total_value": 222214.99,
                    "day_change": -4091.32,
                    "day_change_pct": -1.80,
                    "holdings": [
                        {
                            "symbol": "PLTR",
                            "quantity": 369.746,
                            "current_value": 64583.53,
                            "day_change": 935.45,
                            "day_change_pct": 1.46,
                            "layer": "layer1",
                        },
                        {
                            "symbol": "JEPI",
                            "quantity": 72.942,
                            "current_value": 4142.64,
                            "day_change": -4.03,
                            "day_change_pct": -0.10,
                            "layer": "layer2",
                        },
                    ],
                    "timestamp": "2025-11-17T15:33:00",
                }
            ]
        }
    }


class AnalysisResultsInput(BaseModel):
    """Combined analysis results for dashboard display.

    WHAT: Aggregated output from all 4 analysis tools
    WHY: Single model for ResultsPanel to display multi-tool analysis
    VALIDATES:
        - Ticker symbol is valid
        - At least one analysis result present
        - No duplicate tools in results

    EDUCATIONAL NOTE:
    This model combines results from:
    1. Momentum (RSI, MACD, Stochastic, Williams %R, ROC)
    2. Volatility (ATR, Bollinger Bands, regime assessment)
    3. Risk Metrics (VaR, Sharpe, Sortino, Max Drawdown)
    4. Moving Averages (SMA/EMA, Golden/Death Cross)

    Dashboard displays these side-by-side for quick assessment.

    USAGE EXAMPLE:
        results = AnalysisResultsInput(
            ticker="TSLA",
            timeframe=90,
            timestamp=datetime.now(),
            momentum={...},
            volatility={...},
            risk={...},
            moving_averages={...}
        )
    """

    ticker: str = Field(
        ...,
        description="Ticker symbol analyzed (e.g., 'TSLA', 'BRK-B')",
        min_length=1,
        max_length=10,
        pattern=r"^[A-Z\-\.]+$",  # Uppercase letters, hyphens, and dots (e.g., BRK-B, BRK.B)
    )

    timeframe: int = Field(..., ge=30, le=1000, description="Number of days analyzed")

    timestamp: datetime = Field(..., description="When analysis was run")

    momentum: dict | None = Field(
        default=None, description="Momentum indicators output (RSI, MACD, etc.)"
    )

    volatility: dict | None = Field(
        default=None, description="Volatility metrics output (ATR, Bollinger, etc.)"
    )

    risk: dict | None = Field(
        default=None, description="Risk metrics output (VaR, Sharpe, etc.)"
    )

    moving_averages: dict | None = Field(
        default=None, description="Moving average output (SMA, EMA, crossovers)"
    )

    @field_validator("ticker")
    @classmethod
    def ticker_must_be_uppercase(cls, v: str) -> str:
        """Ensure ticker is uppercase."""
        if not v.isupper():
            raise ValueError(f"Ticker '{v}' must be uppercase")
        return v

    @computed_field
    @property
    def tools_run(self) -> list[str]:
        """List of analysis tools that were executed."""
        tools = []
        if self.momentum:
            tools.append("momentum")
        if self.volatility:
            tools.append("volatility")
        if self.risk:
            tools.append("risk")
        if self.moving_averages:
            tools.append("moving_averages")
        return tools

    @computed_field
    @property
    def has_errors(self) -> bool:
        """Check if any analysis tool returned an error."""
        results = [self.momentum, self.volatility, self.risk, self.moving_averages]
        return any(r and "error" in r for r in results if r)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "ticker": "TSLA",
                    "timeframe": 90,
                    "timestamp": "2025-11-17T15:35:00",
                    "momentum": {
                        "rsi": {"current_rsi": 42.65, "rsi_signal": "neutral"},
                        "macd": {"signal": "bullish"},
                    },
                    "volatility": {
                        "atr": {"atr": 18.36, "atr_percent": 5.36},
                        "volatility_regime": "high",
                    },
                    "risk": {"sharpe_ratio": 1.25, "var_95": -4.2},
                    "moving_averages": {"primary_ma": {"price_vs_ma": "above"}},
                }
            ]
        }
    }


# Type exports for convenience
__all__ = [
    "HoldingInput",
    "PortfolioSnapshotInput",
    "AnalysisResultsInput",
]
