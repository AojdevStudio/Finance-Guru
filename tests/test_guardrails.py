"""Tests for hard post-LLM buy-ticket guardrails."""

from __future__ import annotations

from buy_ticket_agent.guardrails import check
from buy_ticket_agent.ticket_models import BuyTicket, PortfolioState, TicketAllocation


def _ticket_with_allocation(
    ticker: str,
    weight: float,
    amount: float,
) -> BuyTicket:
    return BuyTicket(
        strategy_name="AOJ-461 acceptance ticket",
        generated_on="2026-06-08",
        generated_by="strategy-advisor",
        portfolio_context_date="2026-06-08",
        deployment_amount=amount,
        cash_available=100000.0,
        remaining_cash_buffer=100000.0 - amount,
        price_snapshot_as_of="2026-06-08T15:00:00Z",
        itc_applicability="supported",
        itc_risk_score=0.42,
        allocations=[
            TicketAllocation(
                ticker=ticker,
                category="Growth",
                weight=weight,
                amount=amount,
                price=100.0,
                shares=amount / 100.0,
            )
        ],
        strategy_rationale=["Deploy only when hard guardrails pass."],
        risk_notes=["Concentration must stay within the hard limit."],
        sources=["Layer 3 deterministic bundle"],
        assumptions=["Fractional shares supported."],
        progress_tracking="Month 1",
        educational_notice=(
            "For educational purposes only; not investment advice. Consult a "
            "licensed financial professional before acting. Loss of principal "
            "is possible."
        ),
    )


def test_check_rejects_ticket_proposing_thirty_five_percent_concentration() -> None:
    """A ticket proposing 35% concentration is hard-blocked after LLM output."""
    ticket = _ticket_with_allocation("TSLA", weight=1.0, amount=35000.0)
    portfolio = PortfolioState(
        portfolio_value=100000.0,
        cash_available=100000.0,
        monthly_dividend_income=500.0,
        monthly_margin_interest=200.0,
        current_positions={},
        context_date="2026-06-08",
    )

    result = check(ticket, portfolio)

    assert result.status == "blocked"
    assert result.advisory_block == "concentration>30%"
    assert result.ticket.advisory_block == "concentration>30%"


def test_check_rejects_cash_funded_deployment_above_concentration_limit() -> None:
    """Cash-funded deployments do not inflate the concentration denominator."""
    ticket = _ticket_with_allocation("SPY", weight=1.0, amount=33000.0)
    portfolio = PortfolioState(
        portfolio_value=100000.0,
        cash_available=33000.0,
        monthly_dividend_income=500.0,
        monthly_margin_interest=200.0,
        current_positions={},
        context_date="2026-06-08",
    )

    result = check(ticket, portfolio)

    assert result.status == "blocked"
    assert result.advisory_block == "concentration>30%"


def test_check_sums_duplicate_normalized_positions_before_concentration() -> None:
    """Differently formatted duplicate position keys cannot hide concentration."""
    ticket = _ticket_with_allocation("TSLA", weight=1.0, amount=10000.0)
    portfolio = PortfolioState(
        portfolio_value=100000.0,
        cash_available=10000.0,
        monthly_dividend_income=500.0,
        monthly_margin_interest=200.0,
        current_positions={"TSLA": 20000.0, " tsla ": 5000.0},
        context_date="2026-06-08",
    )

    result = check(ticket, portfolio)

    assert result.status == "blocked"
    assert result.advisory_block == "concentration>30%"


def test_check_accepts_ticket_within_all_hard_limits() -> None:
    """A ticket within every hard threshold is accepted without violations."""
    ticket = _ticket_with_allocation("SPY", weight=1.0, amount=20000.0).model_copy(
        update={"advisory_block": "llm-authored advisory"}
    )
    portfolio = PortfolioState(
        portfolio_value=100000.0,
        cash_available=20000.0,
        monthly_dividend_income=500.0,
        monthly_margin_interest=200.0,
        current_positions={},
        context_date="2026-06-08",
    )

    result = check(ticket, portfolio)

    assert result.status == "accepted"
    assert result.advisory_block is None
    assert result.violations == []
    assert result.ticket.advisory_block is None


def test_check_rejects_ticket_when_margin_coverage_is_below_two_times() -> None:
    """Monthly dividend coverage below 2x margin interest is hard-blocked."""
    ticket = _ticket_with_allocation("SPY", weight=0.20, amount=20000.0)
    portfolio = PortfolioState(
        portfolio_value=100000.0,
        cash_available=100000.0,
        monthly_dividend_income=300.0,
        monthly_margin_interest=200.0,
        current_positions={},
        context_date="2026-06-08",
    )

    result = check(ticket, portfolio)

    assert result.status == "blocked"
    assert result.advisory_block == "coverage<2x"
    assert result.ticket.advisory_block == "coverage<2x"


def test_check_rejects_ticket_when_itc_risk_is_at_hard_limit() -> None:
    """ITC risk must stay below 0.7 after the LLM response."""
    ticket = _ticket_with_allocation("SPY", weight=0.20, amount=20000.0).model_copy(
        update={"itc_risk_score": 0.70}
    )
    portfolio = PortfolioState(
        portfolio_value=100000.0,
        cash_available=100000.0,
        monthly_dividend_income=500.0,
        monthly_margin_interest=200.0,
        current_positions={},
        context_date="2026-06-08",
    )

    result = check(ticket, portfolio)

    assert result.status == "blocked"
    assert result.advisory_block == "itc_risk>=0.7"
    assert result.ticket.advisory_block == "itc_risk>=0.7"
