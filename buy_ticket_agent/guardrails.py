"""Hard post-LLM guardrails for generated buy tickets."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

from buy_ticket_agent.ticket_models import (
    BuyTicket,
    GuardrailContext,
    PortfolioState,
    TicketProposal,
)

CONCENTRATION_LIMIT = 0.30
MIN_MARGIN_COVERAGE = 2.0
MAX_ITC_RISK = 0.70


class GuardrailResult(BaseModel):
    """Outcome of hard guardrail evaluation."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["accepted", "blocked"]
    ticket: BuyTicket
    advisory_block: str | None
    violations: list[str]


def _deployment_by_ticker(ticket: TicketProposal) -> dict[str, float]:
    deployments: dict[str, float] = {}
    for allocation in ticket.allocations:
        deployments[allocation.ticker] = (
            deployments.get(allocation.ticker, 0.0) + allocation.amount
        )
    return deployments


def _pre_borrow_equity_nav(portfolio: PortfolioState) -> float | None:
    """Return the sole concentration denominator when it is authoritative."""
    nav = portfolio.portfolio_value
    return nav if nav is not None and nav > 0.0 else None


def _first_concentration_violation(
    ticket: TicketProposal,
    portfolio: PortfolioState,
) -> str | None:
    equity_nav = _pre_borrow_equity_nav(portfolio)
    if equity_nav is None:
        return "equity_nav_unavailable"

    for ticker, deployment in _deployment_by_ticker(ticket).items():
        existing = portfolio.current_positions.get(ticker, 0.0)
        concentration = (existing + deployment) / equity_nav
        if concentration > CONCENTRATION_LIMIT:
            return "concentration>30%"
    return None


def _projected_margin_borrowing(
    ticket: TicketProposal,
    portfolio: PortfolioState,
) -> float:
    return max(ticket.deployment_amount - portfolio.cash_available, 0.0)


def _margin_coverage_violation(
    ticket: TicketProposal,
    context: GuardrailContext,
) -> str | None:
    portfolio = context.portfolio
    projected_borrowing = _projected_margin_borrowing(ticket, portfolio)
    if projected_borrowing > 0.0 and context.annual_margin_rate is None:
        return "margin_rate_unavailable"

    projected_monthly_interest = portfolio.monthly_margin_interest
    if context.annual_margin_rate is not None:
        projected_monthly_interest += (
            projected_borrowing * context.annual_margin_rate / 12
        )
    if projected_monthly_interest == 0.0:
        return None
    coverage = portfolio.monthly_dividend_income / projected_monthly_interest
    if coverage < MIN_MARGIN_COVERAGE:
        return "coverage<2x"
    return None


def _itc_risk_violation(itc_risk_score: float) -> str | None:
    if itc_risk_score >= MAX_ITC_RISK:
        return "itc_risk>=0.7"
    return None


def check(
    ticket: TicketProposal | dict,
    context: GuardrailContext | dict,
) -> GuardrailResult:
    """Evaluate a model proposal using only trusted guardrail context."""
    proposal = TicketProposal.model_validate(ticket)
    parsed_context = GuardrailContext.model_validate(context)
    portfolio = parsed_context.portfolio
    parsed_ticket = BuyTicket.model_validate(
        {
            **proposal.model_dump(mode="python"),
            "itc_applicability": "supported",
            "itc_risk_score": parsed_context.itc_risk_score,
        }
    )

    violations = [
        violation
        for violation in (
            _first_concentration_violation(parsed_ticket, portfolio),
            _margin_coverage_violation(proposal, parsed_context),
            _itc_risk_violation(parsed_context.itc_risk_score),
        )
        if violation is not None
    ]
    if not violations:
        accepted_ticket = parsed_ticket.model_copy(update={"advisory_block": None})
        return GuardrailResult(
            status="accepted",
            ticket=accepted_ticket,
            advisory_block=None,
            violations=[],
        )

    advisory_block = violations[0]
    blocked_ticket = parsed_ticket.model_copy(update={"advisory_block": advisory_block})
    return GuardrailResult(
        status="blocked",
        ticket=blocked_ticket,
        advisory_block=advisory_block,
        violations=violations,
    )
