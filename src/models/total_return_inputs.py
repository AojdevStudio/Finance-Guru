"""Total Return Pydantic Models for Finance Guru.

This module defines type-safe data structures for total return calculations,
including dividend records, return inputs, and return outputs.

ARCHITECTURE NOTE:
These models represent Layer 1 of our 3-layer architecture:
    Layer 1: Pydantic Models (THIS FILE) - Data validation
    Layer 2: Calculator Classes - Business logic (total return calculator)
    Layer 3: CLI Interface - Agent integration

EDUCATIONAL CONTEXT:
Total return measures the complete performance of an investment, capturing
both price appreciation and income (dividends).

TOTAL RETURN FORMULA:
    Total Return = Price Return + Dividend Return

WHERE:
- Price Return = (End Price - Start Price) / Start Price
- Dividend Return = Sum of dividends received / Start Price

DRIP (Dividend Reinvestment Plan):
- Automatically reinvests dividends to buy more shares
- Compounds returns over time (shares grow, future dividends are larger)
- DRIP total return > non-DRIP total return over long periods
- Tracking requires knowing shares_at_ex for each dividend payment

WHY THIS MATTERS:
- Price-only returns UNDERSTATE true performance of dividend stocks
- SCHD might show 5% price return but 8.5% total return (3.5% from dividends)
- Comparing SQQQ (no dividends) vs puts (no dividends) is price-only
- Comparing QQQ vs SCHD REQUIRES total return for fair comparison

Author: Finance Guru Development Team
Created: 2026-02-17
"""

import warnings
from datetime import date

from pydantic import BaseModel, Field, field_validator, model_validator


class DividendRecord(BaseModel):
    """A single dividend payment record.

    WHAT: Captures one dividend event for a position
    WHY: Building block for calculating dividend return and DRIP shares
    VALIDATES:
        - Amount is positive (dividends are always positive cash flows)
        - Shares at ex-date is positive (must hold shares to receive dividend)
    """

    ex_date: date = Field(
        ...,
        description="Ex-dividend date (must own shares before this date)",
    )

    payment_date: date | None = Field(
        default=None,
        description="Date dividend was actually paid (may not always be available)",
    )

    amount: float = Field(
        ...,
        gt=0.0,
        description="Per-share dividend amount in dollars",
    )

    shares_at_ex: float = Field(
        ...,
        gt=0.0,
        description="Shares held at ex-date (fractional for DRIP positions)",
    )


class TotalReturnInput(BaseModel):
    """Input parameters for calculating total return.

    WHAT: Defines the calculation window and parameters for total return
    WHY: Standardizes inputs so calculator receives validated, typed data
    VALIDATES:
        - Ticker is uppercase (market convention)
        - End date is after start date (valid time window)
        - Initial shares is positive
    """

    ticker: str = Field(
        ...,
        description="Ticker symbol to calculate total return for",
        min_length=1,
        max_length=10,
    )

    start_date: date = Field(
        ...,
        description="Start of measurement period",
    )

    end_date: date = Field(
        ...,
        description="End of measurement period",
    )

    include_drip: bool = Field(
        default=True,
        description="Whether to model dividend reinvestment (DRIP)",
    )

    initial_shares: float = Field(
        default=1.0,
        gt=0.0,
        description="Starting share count for the calculation",
    )

    @field_validator("ticker")
    @classmethod
    def ticker_must_be_uppercase(cls, v: str) -> str:
        """Ensure ticker is uppercase."""
        if not v.isupper():
            raise ValueError(f"Ticker '{v}' must be uppercase")
        return v

    @model_validator(mode="after")
    def end_date_after_start_date(self) -> "TotalReturnInput":
        """Ensure end_date is after start_date.

        WHY: A measurement period requires a valid time window.
        Zero or negative duration is meaningless for return calculation.
        """
        if self.end_date <= self.start_date:
            raise ValueError(
                f"end_date ({self.end_date}) must be after start_date ({self.start_date})"
            )
        return self

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "ticker": "SCHD",
                    "start_date": "2025-01-01",
                    "end_date": "2026-01-01",
                    "include_drip": True,
                    "initial_shares": 100.0,
                }
            ]
        }
    }


class TickerReturn(BaseModel):
    """Calculated total return output for a single ticker.

    WHAT: Complete return breakdown with price, dividend, and total components
    WHY: Separating return components enables fair comparisons and attribution
    VALIDATES:
        - Total return approximately equals price_return + dividend_return
        - Final shares is positive (cannot end with negative shares)
    """

    ticker: str = Field(
        ...,
        description="Ticker symbol this return was calculated for",
    )

    start_date: date = Field(
        ...,
        description="Start of measurement period",
    )

    end_date: date = Field(
        ...,
        description="End of measurement period",
    )

    price_return: float = Field(
        ...,
        description="Price-only return as decimal (0.15 = 15%)",
    )

    dividend_return: float = Field(
        ...,
        description="Dividend contribution to return as decimal (0.035 = 3.5%)",
    )

    total_return: float = Field(
        ...,
        description="Total return as decimal (price_return + dividend_return)",
    )

    dividends: list[DividendRecord] = Field(
        default_factory=list,
        description="Individual dividend records during the period",
    )

    final_shares: float = Field(
        default=1.0,
        gt=0.0,
        description="Shares held at end of period (reflects DRIP accumulation)",
    )

    data_quality_warnings: list[str] = Field(
        default_factory=list,
        description="Warnings about data gaps, missing dividends, or approximations",
    )

    @model_validator(mode="after")
    def total_return_consistency_check(self) -> "TickerReturn":
        """Warn if total_return deviates from price_return + dividend_return.

        WHY: Total return should be the sum of its components. A significant
        deviation suggests a calculation error or rounding issue.
        Does NOT reject -- just warns, since floating point can cause small diffs.
        """
        expected = self.price_return + self.dividend_return
        diff = abs(self.total_return - expected)
        if diff > 0.01:
            warnings.warn(
                f"total_return ({self.total_return:.4f}) deviates from "
                f"price_return + dividend_return ({expected:.4f}) by {diff:.4f}. "
                f"This may indicate a calculation issue.",
                stacklevel=2,
            )
        return self


# Type exports
__all__ = [
    "TotalReturnInput",
    "DividendRecord",
    "TickerReturn",
]
