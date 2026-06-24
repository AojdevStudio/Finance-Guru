"""Hard post-LLM guardrails for generated buy tickets."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

from buy_ticket_agent.ticket_models import BuyTicket, PortfolioState

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


def _deployment_by_ticker(ticket: BuyTicket) -> dict[str, float]:
    deployments: dict[str, float] = {}
    for allocation in ticket.allocations:
        deployments[allocation.ticker] = (
            deployments.get(allocation.ticker, 0.0) + allocation.amount
        )
    return deployments


def _post_deployment_portfolio_value(
    ticket: BuyTicket,
    portfolio: PortfolioState,
) -> float:
    externally_funded_deployment = max(
        ticket.deployment_amount - portfolio.cash_available,
        0.0,
    )
    return portfolio.portfolio_value + externally_funded_deployment


def _first_concentration_violation(
    ticket: BuyTicket,
    portfolio: PortfolioState,
) -> str | None:
    portfolio_after = _post_deployment_portfolio_value(ticket, portfolio)
    if portfolio_after <= 0.0:
        return None

    for ticker, deployment in _deployment_by_ticker(ticket).items():
        existing = portfolio.current_positions.get(ticker, 0.0)
        concentration = (existing + deployment) / portfolio_after
        if concentration > CONCENTRATION_LIMIT:
            return "concentration>30%"
    return None


def _margin_coverage_violation(portfolio: PortfolioState) -> str | None:
    if portfolio.monthly_margin_interest == 0.0:
        return None
    coverage = portfolio.monthly_dividend_income / portfolio.monthly_margin_interest
    if coverage < MIN_MARGIN_COVERAGE:
        return "coverage<2x"
    return None


def _itc_risk_violation(ticket: BuyTicket) -> str | None:
    if ticket.itc_applicability == "supported" and ticket.itc_risk_score is None:
        # ITC was declared applicable but no score arrived (e.g. ITC CLI failure).
        # Fail-safe: block rather than silently skip the guardrail.
        return "itc_risk_score_missing"
    if ticket.itc_risk_score is None:
        return None
    if ticket.itc_risk_score >= MAX_ITC_RISK:
        return "itc_risk>=0.7"
    return None


def check(
    ticket: BuyTicket | dict,
    portfolio: PortfolioState | dict,
) -> GuardrailResult:
    """Evaluate non-negotiable post-LLM guardrails against a generated ticket."""
    parsed_ticket = BuyTicket.model_validate(ticket)
    parsed_portfolio = PortfolioState.model_validate(portfolio)

    violations = [
        violation
        for violation in (
            _first_concentration_violation(parsed_ticket, parsed_portfolio),
            _margin_coverage_violation(parsed_portfolio),
            _itc_risk_violation(parsed_ticket),
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
