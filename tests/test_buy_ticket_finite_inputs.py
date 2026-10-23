"""Nonfinite numbers must not enter order fields or hard guardrails."""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from buy_ticket_agent.guardrails import check
from buy_ticket_agent.ticket_models import (
    PortfolioState,
    TicketAllocation,
    TicketProposal,
)


@pytest.fixture
def proposal() -> dict[str, Any]:
    return {
        "strategy_name": "Synthetic boundary check",
        "generated_on": "2026-10-22",
        "generated_by": "synthetic-test",
        "portfolio_context_date": "2026-10-22",
        "deployment_amount": 1000,
        "cash_available": 1000,
        "remaining_cash_buffer": 0,
        "price_snapshot_as_of": "2026-10-22T15:00:00Z",
        "allocations": [
            {"ticker": "TEST", "category": "Growth", "weight": 1, "amount": 1000}
        ],
        "strategy_rationale": ["Synthetic test."],
        "risk_notes": ["Synthetic test."],
        "sources": ["Offline fixture."],
        "assumptions": ["Synthetic test."],
        "progress_tracking": "Synthetic test.",
        "educational_notice": "Educational only, not investment advice.",
    }


@pytest.fixture
def portfolio() -> dict[str, Any]:
    return {
        "portfolio_value": 100000,
        "cash_available": 1000,
        "monthly_dividend_income": 500,
        "monthly_margin_interest": 200,
        "current_positions": {},
        "context_date": "2026-10-22",
    }


def test_nan_position_cannot_reach_guardrail_acceptance(
    proposal: dict[str, Any], portfolio: dict[str, Any]
) -> None:
    portfolio["current_positions"] = {"TEST": float("nan")}

    with pytest.raises(ValidationError, match="finite"):
        check(proposal, {"portfolio": portfolio, "itc_risk_score": 0.42})


@pytest.mark.parametrize(
    "field", ["cash_available", "monthly_dividend_income", "monthly_margin_interest"]
)
def test_portfolio_rejects_infinite_inputs(
    portfolio: dict[str, Any], field: str
) -> None:
    portfolio[field] = float("inf")

    with pytest.raises(ValidationError, match="finite"):
        PortfolioState.model_validate(portfolio)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_ticket_rejects_nonfinite_cash_buffer(
    proposal: dict[str, Any], value: float
) -> None:
    proposal["remaining_cash_buffer"] = value

    with pytest.raises(ValidationError, match="finite"):
        TicketProposal.model_validate(proposal)


@pytest.mark.parametrize("field", ["amount", "price", "shares"])
def test_allocation_rejects_infinite_order_numbers(field: str) -> None:
    allocation = {"ticker": "TEST", "category": "Growth", "weight": 1, "amount": 1000}
    allocation[field] = float("inf")

    with pytest.raises(ValidationError, match="finite"):
        TicketAllocation.model_validate(allocation)


def test_finite_inputs_keep_the_accepted_outcome(
    proposal: dict[str, Any], portfolio: dict[str, Any]
) -> None:
    assert check(proposal, {"portfolio": portfolio, "itc_risk_score": 0.42}).status == (
        "accepted"
    )
