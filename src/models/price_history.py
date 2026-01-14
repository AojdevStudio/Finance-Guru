"""
Price History Pydantic Models for Finance Guru™

WHAT: Data models for historical price tracking and portfolio value snapshots
WHY: Enable time-series analysis of holdings and portfolio value for charting
ARCHITECTURE: Layer 1 of 3-layer type-safe architecture

Used by: Price History Service, CLI, Google Sheets Sync, Frontend UI

Author: Finance Guru™ Development Team
Created: 2026-01-14
"""

from __future__ import annotations

from datetime import datetime, date
from typing import Literal, Optional
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator, computed_field


class PriceSnapshotInput(BaseModel):
    """
    Individual price snapshot for a single ticker.

    WHAT: Captures price data for one ticker at a specific point in time
    WHY: Builds historical record for charting and analysis
    VALIDATES:
        - Symbol is uppercase and valid format
        - Prices are non-negative
        - Timestamp is not in future

    USAGE EXAMPLE:
        snapshot = PriceSnapshotInput(
            symbol="PLTR",
            price=75.42,
            open_price=74.50,
            high_price=76.10,
            low_price=74.20,
            previous_close=74.85,
            volume=45000000,
            snapshot_date=date.today(),
            timestamp=datetime.now(),
            source="yfinance"
        )
    """

    symbol: str = Field(
        ...,
        description="Stock ticker symbol (e.g., 'PLTR', 'JEPI')",
        min_length=1,
        max_length=10,
    )

    price: float = Field(
        ...,
        ge=0.0,
        description="Current/closing price in USD"
    )

    open_price: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Opening price for the day"
    )

    high_price: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="High price for the day"
    )

    low_price: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Low price for the day"
    )

    previous_close: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Previous day's closing price"
    )

    volume: Optional[int] = Field(
        default=None,
        ge=0,
        description="Trading volume for the day"
    )

    snapshot_date: date = Field(
        ...,
        description="Date of the price snapshot (YYYY-MM-DD)"
    )

    timestamp: datetime = Field(
        ...,
        description="Exact timestamp when snapshot was captured"
    )

    source: Literal["yfinance", "finnhub", "manual"] = Field(
        default="yfinance",
        description="Data source for the price"
    )

    @field_validator("symbol")
    @classmethod
    def symbol_must_be_uppercase(cls, v: str) -> str:
        """Ensure ticker symbol is uppercase."""
        return v.upper()

    @computed_field
    @property
    def day_change(self) -> Optional[float]:
        """Calculate day change if previous_close available."""
        if self.previous_close and self.previous_close > 0:
            return round(self.price - self.previous_close, 2)
        return None

    @computed_field
    @property
    def day_change_pct(self) -> Optional[float]:
        """Calculate day change percentage if previous_close available."""
        if self.previous_close and self.previous_close > 0:
            return round((self.price - self.previous_close) / self.previous_close * 100, 2)
        return None

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "symbol": "PLTR",
                "price": 75.42,
                "open_price": 74.50,
                "high_price": 76.10,
                "low_price": 74.20,
                "previous_close": 74.85,
                "volume": 45000000,
                "snapshot_date": "2026-01-14",
                "timestamp": "2026-01-14T16:00:00",
                "source": "yfinance"
            }]
        }
    }


class HoldingSnapshotInput(BaseModel):
    """
    Holding value snapshot combining price with quantity.

    WHAT: Captures value of a specific holding at a point in time
    WHY: Tracks position value over time (price × quantity)
    """

    symbol: str = Field(
        ...,
        description="Stock ticker symbol"
    )

    quantity: float = Field(
        ...,
        ge=0.0,
        description="Number of shares/units held"
    )

    price: float = Field(
        ...,
        ge=0.0,
        description="Price per share at snapshot time"
    )

    layer: Literal["layer1", "layer2", "layer3", "unknown"] = Field(
        default="unknown",
        description="Portfolio layer classification"
    )

    snapshot_date: date = Field(
        ...,
        description="Date of the snapshot"
    )

    @field_validator("symbol")
    @classmethod
    def symbol_must_be_uppercase(cls, v: str) -> str:
        return v.upper()

    @computed_field
    @property
    def value(self) -> float:
        """Calculate total value (price × quantity)."""
        return round(self.price * self.quantity, 2)

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "symbol": "PLTR",
                "quantity": 369.746,
                "price": 75.42,
                "layer": "layer1",
                "snapshot_date": "2026-01-14"
            }]
        }
    }


class PortfolioValueSnapshotInput(BaseModel):
    """
    Complete portfolio value snapshot.

    WHAT: Aggregated portfolio value at a specific point in time
    WHY: Enables portfolio value charting and performance tracking
    VALIDATES:
        - At least one holding present
        - Total value matches sum of holdings
        - Timestamp is reasonable

    USAGE EXAMPLE:
        snapshot = PortfolioValueSnapshotInput(
            total_value=250000.00,
            holdings=[holding1, holding2, ...],
            snapshot_date=date.today(),
            timestamp=datetime.now()
        )
    """

    total_value: float = Field(
        ...,
        ge=0.0,
        description="Total portfolio value in USD"
    )

    holdings: list[HoldingSnapshotInput] = Field(
        ...,
        min_length=1,
        description="List of all holding snapshots"
    )

    snapshot_date: date = Field(
        ...,
        description="Date of the portfolio snapshot"
    )

    timestamp: datetime = Field(
        ...,
        description="Exact timestamp when snapshot was captured"
    )

    cash_balance: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Cash balance (SPAXX or similar)"
    )

    margin_balance: Optional[float] = Field(
        default=None,
        description="Margin debt (negative value)"
    )

    @computed_field
    @property
    def layer1_value(self) -> float:
        """Total value of Layer 1 (growth) holdings."""
        return sum(h.value for h in self.holdings if h.layer == "layer1")

    @computed_field
    @property
    def layer2_value(self) -> float:
        """Total value of Layer 2 (income) holdings."""
        return sum(h.value for h in self.holdings if h.layer == "layer2")

    @computed_field
    @property
    def layer3_value(self) -> float:
        """Total value of Layer 3 (hedge) holdings."""
        return sum(h.value for h in self.holdings if h.layer == "layer3")

    @computed_field
    @property
    def holding_count(self) -> int:
        """Number of holdings in snapshot."""
        return len(self.holdings)

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "total_value": 250000.00,
                "holdings": [
                    {"symbol": "PLTR", "quantity": 369.746, "price": 75.42, "layer": "layer1", "snapshot_date": "2026-01-14"},
                    {"symbol": "JEPI", "quantity": 61.342, "price": 56.80, "layer": "layer2", "snapshot_date": "2026-01-14"}
                ],
                "snapshot_date": "2026-01-14",
                "timestamp": "2026-01-14T16:00:00",
                "cash_balance": 5000.00,
                "margin_balance": -15000.00
            }]
        }
    }


class PriceHistoryQuery(BaseModel):
    """
    Query parameters for retrieving price history.

    WHAT: Filter and pagination options for history queries
    WHY: Enables flexible data retrieval for different use cases
    """

    symbols: Optional[list[str]] = Field(
        default=None,
        description="List of ticker symbols to query (None = all)"
    )

    start_date: Optional[date] = Field(
        default=None,
        description="Start date for history (inclusive)"
    )

    end_date: Optional[date] = Field(
        default=None,
        description="End date for history (inclusive)"
    )

    limit: int = Field(
        default=365,
        ge=1,
        le=3650,
        description="Maximum number of records to return"
    )

    @field_validator("symbols")
    @classmethod
    def symbols_must_be_uppercase(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        if v is None:
            return None
        return [s.upper() for s in v]


class PriceHistoryOutput(BaseModel):
    """
    Output model for price history query results.

    WHAT: Container for historical price data with metadata
    WHY: Provides structured response for UI and exports
    """

    symbol: str = Field(
        ...,
        description="Ticker symbol"
    )

    snapshots: list[PriceSnapshotInput] = Field(
        ...,
        description="List of price snapshots ordered by date"
    )

    start_date: date = Field(
        ...,
        description="Earliest date in results"
    )

    end_date: date = Field(
        ...,
        description="Latest date in results"
    )

    @computed_field
    @property
    def record_count(self) -> int:
        """Number of snapshots returned."""
        return len(self.snapshots)

    @computed_field
    @property
    def price_change(self) -> Optional[float]:
        """Price change from first to last snapshot."""
        if len(self.snapshots) >= 2:
            return round(self.snapshots[-1].price - self.snapshots[0].price, 2)
        return None

    @computed_field
    @property
    def price_change_pct(self) -> Optional[float]:
        """Percentage change from first to last snapshot."""
        if len(self.snapshots) >= 2 and self.snapshots[0].price > 0:
            change = self.snapshots[-1].price - self.snapshots[0].price
            return round(change / self.snapshots[0].price * 100, 2)
        return None


class PortfolioHistoryOutput(BaseModel):
    """
    Output model for portfolio value history.

    WHAT: Time series of portfolio values with layer breakdowns
    WHY: Enables portfolio performance charting
    """

    snapshots: list[PortfolioValueSnapshotInput] = Field(
        ...,
        description="List of portfolio snapshots ordered by date"
    )

    start_date: date = Field(
        ...,
        description="Earliest date in results"
    )

    end_date: date = Field(
        ...,
        description="Latest date in results"
    )

    @computed_field
    @property
    def record_count(self) -> int:
        """Number of snapshots returned."""
        return len(self.snapshots)

    @computed_field
    @property
    def value_change(self) -> Optional[float]:
        """Portfolio value change from first to last snapshot."""
        if len(self.snapshots) >= 2:
            return round(self.snapshots[-1].total_value - self.snapshots[0].total_value, 2)
        return None

    @computed_field
    @property
    def value_change_pct(self) -> Optional[float]:
        """Percentage change from first to last snapshot."""
        if len(self.snapshots) >= 2 and self.snapshots[0].total_value > 0:
            change = self.snapshots[-1].total_value - self.snapshots[0].total_value
            return round(change / self.snapshots[0].total_value * 100, 2)
        return None


# Type exports for convenience
__all__ = [
    "PriceSnapshotInput",
    "HoldingSnapshotInput",
    "PortfolioValueSnapshotInput",
    "PriceHistoryQuery",
    "PriceHistoryOutput",
    "PortfolioHistoryOutput",
]
