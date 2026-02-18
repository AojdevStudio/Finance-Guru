"""Hedging Position Pydantic Models for Finance Guru.

This module defines type-safe data structures for portfolio hedging,
including hedge positions, roll suggestions, and sizing requests.

ARCHITECTURE NOTE:
These models represent Layer 1 of our 3-layer architecture:
    Layer 1: Pydantic Models (THIS FILE) - Data validation
    Layer 2: Calculator Classes - Business logic (hedge sizer, roll tracker)
    Layer 3: CLI Interface - Agent integration

EDUCATIONAL CONTEXT:
Hedging protects a portfolio against downside risk. Two common approaches:

PUT OPTIONS:
- Buy put options on held positions or indices (QQQ, SPY)
- Puts gain value when the underlying drops, offsetting portfolio losses
- Require strike price, expiry date, and contract specification
- Cost = premium paid per contract (each contract = 100 shares)

INVERSE ETFs:
- Buy shares of inverse ETFs (e.g., SQQQ = 3x inverse QQQ)
- Gain value when the tracked index drops
- No strike/expiry -- simpler but less precise than options
- Cost = share price x quantity

ROLLING:
- When a put option approaches expiry, "roll" it to a new expiry/strike
- Maintains protection without gaps in coverage
- RollSuggestion captures the proposed new position parameters

SIZING:
- Determining how many contracts/shares to buy for adequate coverage
- Based on portfolio value, budget, and target protection level

Author: Finance Guru Development Team
Created: 2026-02-17
"""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class HedgePosition(BaseModel):
    """A single hedge position (put option or inverse ETF).

    WHAT: Represents an active hedge in the portfolio
    WHY: Standard format for tracking all hedges regardless of type
    VALIDATES:
        - Ticker is uppercase (market convention)
        - Hedge type is put or inverse_etf
        - Strike and expiry required for puts, optional for inverse ETFs
        - Quantity and premium are positive
    """

    ticker: str = Field(
        ...,
        description="Underlying or hedge ticker symbol (e.g., QQQ, SQQQ)",
        min_length=1,
        max_length=10,
    )

    hedge_type: Literal["put", "inverse_etf"] = Field(
        ...,
        description="Type of hedge: put option or inverse ETF",
    )

    strike: float | None = Field(
        default=None,
        gt=0.0,
        description="Strike price for put options (None for inverse ETFs)",
    )

    expiry: date | None = Field(
        default=None,
        description="Expiration date for put options (None for inverse ETFs)",
    )

    quantity: int = Field(
        ...,
        gt=0,
        description="Number of contracts (puts) or shares (inverse ETFs)",
    )

    premium_paid: float = Field(
        ...,
        ge=0.0,
        description="Premium paid per contract (puts) or price per share (ETFs)",
    )

    entry_date: date = Field(
        ...,
        description="Date the hedge position was opened",
    )

    contract_symbol: str | None = Field(
        default=None,
        description="OCC contract symbol for puts (e.g., QQQ260417P00420000)",
        max_length=30,
    )

    @field_validator("ticker")
    @classmethod
    def ticker_must_be_uppercase(cls, v: str) -> str:
        """Ensure ticker is uppercase."""
        if not v.isupper():
            raise ValueError(f"Ticker '{v}' must be uppercase")
        return v

    @model_validator(mode="after")
    def put_requires_strike_and_expiry(self) -> "HedgePosition":
        """Ensure put options have strike and expiry set.

        WHY: A put option without strike/expiry is meaningless --
        these define the contract terms.
        """
        if self.hedge_type == "put":
            if self.strike is None:
                raise ValueError(
                    "Put options require a strike price (strike must not be None)"
                )
            if self.expiry is None:
                raise ValueError(
                    "Put options require an expiry date (expiry must not be None)"
                )
        return self

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "ticker": "QQQ",
                    "hedge_type": "put",
                    "strike": 420.0,
                    "expiry": "2026-04-17",
                    "quantity": 2,
                    "premium_paid": 8.50,
                    "entry_date": "2026-02-01",
                    "contract_symbol": "QQQ260417P00420000",
                }
            ]
        }
    }


class RollSuggestion(BaseModel):
    """A suggestion to roll an existing hedge to new terms.

    WHAT: Proposed replacement parameters for an expiring hedge position
    WHY: Hedges expire -- rolling maintains continuous protection
    VALIDATES:
        - Suggested expiry is in the future
        - Strike and cost are positive
        - Reason is provided (audit trail for decisions)
    """

    current_position: HedgePosition = Field(
        ...,
        description="The existing hedge position to be rolled",
    )

    suggested_strike: float = Field(
        ...,
        gt=0.0,
        description="Recommended new strike price",
    )

    suggested_expiry: date = Field(
        ...,
        description="Recommended new expiration date",
    )

    estimated_cost: float = Field(
        ...,
        ge=0.0,
        description="Estimated premium per contract for the new position",
    )

    reason: str = Field(
        ...,
        description="Rationale for this roll suggestion",
        min_length=1,
    )

    @field_validator("suggested_expiry")
    @classmethod
    def expiry_must_be_future(cls, v: date) -> date:
        """Ensure suggested expiry is in the future."""
        if v <= date.today():
            raise ValueError(
                f"Suggested expiry {v} must be in the future (today is {date.today()})"
            )
        return v


class HedgeSizeRequest(BaseModel):
    """Request parameters for calculating hedge size.

    WHAT: Inputs for determining how many contracts/shares to buy
    WHY: Proper sizing ensures adequate protection without overspending
    VALIDATES:
        - Portfolio value and budget are positive
        - At least one underlying ticker provided
        - All tickers are uppercase
        - Target contracts (if set) is positive
    """

    portfolio_value: float = Field(
        ...,
        gt=0.0,
        description="Total portfolio value to protect",
    )

    underlyings: list[str] = Field(
        ...,
        description="Tickers of positions to hedge (e.g., ['QQQ', 'SPY'])",
        min_length=1,
    )

    budget: float = Field(
        ...,
        gt=0.0,
        description="Total budget allocated for this hedge",
    )

    target_contracts: int | None = Field(
        default=None,
        gt=0,
        description="Desired number of contracts (None = auto-calculate)",
    )

    @field_validator("underlyings")
    @classmethod
    def underlyings_must_be_uppercase(cls, v: list[str]) -> list[str]:
        """Ensure all underlying tickers are uppercase and valid length.

        EDUCATIONAL NOTE:
        Standard convention is uppercase ticker symbols (TSLA not tsla).
        This prevents matching errors when comparing tickers.
        """
        for ticker in v:
            if len(ticker) < 1 or len(ticker) > 10:
                raise ValueError(f"Ticker '{ticker}' must be 1-10 characters")
            if not ticker.isupper():
                raise ValueError(f"Ticker '{ticker}' must be uppercase")
        return v


# Type exports
__all__ = [
    "HedgePosition",
    "RollSuggestion",
    "HedgeSizeRequest",
]
