"""Pydantic models for AOJ-461 buy-ticket generation."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

DISCLAIMER_REQUIRED_TEXT = "not investment advice"
DEPLOYMENT_AMOUNT_TOLERANCE = 0.01


class TicketAllocation(BaseModel):
    """One proposed ticker allocation in a generated buy ticket."""

    model_config = ConfigDict(extra="forbid")

    ticker: str
    category: str
    weight: float = Field(ge=0.0, le=1.0)
    amount: float = Field(ge=0.0)
    price: float | None = Field(default=None, gt=0.0)
    shares: float | None = Field(default=None, ge=0.0)

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, value: str) -> str:
        """Normalize ticker symbols to the repository's uppercase convention."""
        normalized = value.strip().upper()
        if not normalized:
            raise ValueError("ticker is required")
        return normalized


class BuyTicket(BaseModel):
    """Structured JSON representation of the buy-ticket template."""

    model_config = ConfigDict(extra="forbid")

    document_type: Literal["buy-ticket"] = "buy-ticket"
    strategy_name: str
    generated_on: str
    generated_by: str
    portfolio_context_date: str
    deployment_amount: float = Field(ge=0.0)
    cash_available: float = Field(ge=0.0)
    remaining_cash_buffer: float
    price_snapshot_as_of: str
    itc_applicability: Literal["supported", "unsupported", "not-run"]
    itc_risk_score: float | None = Field(default=None, ge=0.0, le=1.0)
    allocations: list[TicketAllocation]
    strategy_rationale: list[str]
    risk_notes: list[str]
    sources: list[str]
    assumptions: list[str]
    progress_tracking: str
    educational_notice: str
    advisory_block: str | None = None

    @field_validator(
        "strategy_name",
        "generated_on",
        "generated_by",
        "portfolio_context_date",
        "price_snapshot_as_of",
        "progress_tracking",
    )
    @classmethod
    def require_non_empty_text(cls, value: str) -> str:
        """Reject empty required text fields."""
        normalized = value.strip()
        if not normalized:
            raise ValueError("field cannot be empty")
        return normalized

    @field_validator("educational_notice")
    @classmethod
    def require_compliance_disclaimer(cls, value: str) -> str:
        """Every generated ticket must preserve the compliance disclaimer."""
        if DISCLAIMER_REQUIRED_TEXT not in value.lower():
            raise ValueError(
                "educational_notice must include not-investment-advice text"
            )
        return value

    @model_validator(mode="after")
    def require_allocations_and_notes(self) -> BuyTicket:
        """Ensure the ticket carries the minimum template sections."""
        if not self.allocations:
            raise ValueError("allocations are required")
        allocated_amount = sum(allocation.amount for allocation in self.allocations)
        if abs(allocated_amount - self.deployment_amount) > DEPLOYMENT_AMOUNT_TOLERANCE:
            raise ValueError("allocation amounts must equal deployment_amount")
        for field_name in (
            "strategy_rationale",
            "risk_notes",
            "sources",
            "assumptions",
        ):
            if not getattr(self, field_name):
                raise ValueError(f"{field_name} is required")
        return self


class PortfolioState(BaseModel):
    """Portfolio context needed for hard guardrail checks."""

    model_config = ConfigDict(extra="forbid")

    portfolio_value: float = Field(ge=0.0)
    cash_available: float = Field(ge=0.0)
    monthly_dividend_income: float = Field(ge=0.0)
    monthly_margin_interest: float = Field(ge=0.0)
    current_positions: dict[str, float] = Field(default_factory=dict)
    context_date: str

    @field_validator("current_positions")
    @classmethod
    def normalize_positions(cls, value: dict[str, float]) -> dict[str, float]:
        """Normalize position keys and reject negative market values."""
        normalized: dict[str, float] = {}
        for ticker, market_value in value.items():
            key = ticker.strip().upper()
            if not key:
                raise ValueError("position ticker is required")
            if market_value < 0.0:
                raise ValueError("position market value cannot be negative")
            normalized[key] = normalized.get(key, 0.0) + market_value
        return normalized
