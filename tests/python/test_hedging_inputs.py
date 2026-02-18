"""Tests for hedging Pydantic models (Phase 6, HEDG-02).

Validates HedgePosition, RollSuggestion, and HedgeSizeRequest models
including valid construction, field-level constraints, and cross-field
model validators.

Author: Finance Guru Development Team
"""

from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

# Add project root for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.models.hedging_inputs import HedgePosition, HedgeSizeRequest, RollSuggestion


class TestHedgePosition:
    """Validate HedgePosition Pydantic model constraints."""

    def test_valid_put_position(self):
        """A fully populated put option position should instantiate."""
        pos = HedgePosition(
            ticker="QQQ",
            hedge_type="put",
            strike=420.0,
            expiry=date(2026, 4, 17),
            quantity=2,
            premium_paid=8.50,
            entry_date=date(2026, 2, 1),
            contract_symbol="QQQ260417P00420000",
        )

        assert pos.ticker == "QQQ"
        assert pos.strike == 420.0
        assert pos.hedge_type == "put"
        assert pos.quantity == 2
        assert pos.premium_paid == 8.50

    def test_valid_inverse_etf_position(self):
        """An inverse ETF position with no strike/expiry should instantiate."""
        pos = HedgePosition(
            ticker="SQQQ",
            hedge_type="inverse_etf",
            strike=None,
            expiry=None,
            quantity=50,
            premium_paid=12.30,
            entry_date=date(2026, 2, 10),
        )

        assert pos.ticker == "SQQQ"
        assert pos.hedge_type == "inverse_etf"
        assert pos.strike is None
        assert pos.expiry is None

    def test_ticker_must_be_uppercase(self):
        """Lowercase ticker should raise ValidationError."""
        with pytest.raises(ValidationError, match="uppercase"):
            HedgePosition(
                ticker="qqq",
                hedge_type="put",
                strike=400.0,
                expiry=date(2026, 4, 17),
                quantity=1,
                premium_paid=5.0,
                entry_date=date(2026, 2, 1),
            )

    def test_strike_must_be_positive(self):
        """Zero or negative strike should raise ValidationError."""
        with pytest.raises(ValidationError):
            HedgePosition(
                ticker="QQQ",
                hedge_type="put",
                strike=0.0,
                expiry=date(2026, 4, 17),
                quantity=1,
                premium_paid=5.0,
                entry_date=date(2026, 2, 1),
            )

        with pytest.raises(ValidationError):
            HedgePosition(
                ticker="QQQ",
                hedge_type="put",
                strike=-1.0,
                expiry=date(2026, 4, 17),
                quantity=1,
                premium_paid=5.0,
                entry_date=date(2026, 2, 1),
            )

    def test_put_requires_strike_and_expiry(self):
        """Put option with strike=None should raise ValidationError."""
        with pytest.raises(ValidationError, match="strike"):
            HedgePosition(
                ticker="QQQ",
                hedge_type="put",
                strike=None,
                expiry=date(2026, 4, 17),
                quantity=1,
                premium_paid=5.0,
                entry_date=date(2026, 2, 1),
            )

    def test_put_requires_expiry(self):
        """Put option with expiry=None should raise ValidationError."""
        with pytest.raises(ValidationError, match="expiry"):
            HedgePosition(
                ticker="QQQ",
                hedge_type="put",
                strike=400.0,
                expiry=None,
                quantity=1,
                premium_paid=5.0,
                entry_date=date(2026, 2, 1),
            )

    def test_inverse_etf_allows_none_strike(self):
        """Inverse ETF with strike=None should pass (no contract terms)."""
        pos = HedgePosition(
            ticker="SQQQ",
            hedge_type="inverse_etf",
            strike=None,
            expiry=None,
            quantity=100,
            premium_paid=11.50,
            entry_date=date(2026, 2, 1),
        )

        assert pos.strike is None
        assert pos.expiry is None

    def test_quantity_must_be_positive(self):
        """Zero quantity should raise ValidationError."""
        with pytest.raises(ValidationError):
            HedgePosition(
                ticker="SQQQ",
                hedge_type="inverse_etf",
                quantity=0,
                premium_paid=10.0,
                entry_date=date(2026, 2, 1),
            )

    def test_premium_paid_allows_zero(self):
        """Premium of 0.0 should be valid (free positions exist)."""
        pos = HedgePosition(
            ticker="SQQQ",
            hedge_type="inverse_etf",
            quantity=10,
            premium_paid=0.0,
            entry_date=date(2026, 2, 1),
        )

        assert pos.premium_paid == 0.0


class TestRollSuggestion:
    """Validate RollSuggestion Pydantic model constraints."""

    def _make_put_position(self) -> HedgePosition:
        """Helper: create a valid put position for use in roll suggestions."""
        return HedgePosition(
            ticker="QQQ",
            hedge_type="put",
            strike=420.0,
            expiry=date(2026, 4, 17),
            quantity=2,
            premium_paid=8.50,
            entry_date=date(2026, 2, 1),
        )

    def test_valid_roll_suggestion(self):
        """A roll suggestion with valid future expiry should instantiate."""
        pos = self._make_put_position()
        future_expiry = date.today() + timedelta(days=90)
        roll = RollSuggestion(
            current_position=pos,
            suggested_strike=410.0,
            suggested_expiry=future_expiry,
            estimated_cost=7.25,
            reason="Approaching expiry, roll to maintain coverage",
        )

        assert roll.suggested_strike == 410.0
        assert roll.suggested_expiry == future_expiry
        assert roll.estimated_cost == 7.25
        assert "coverage" in roll.reason

    def test_suggested_expiry_must_be_future(self):
        """Past suggested_expiry should raise ValidationError."""
        pos = self._make_put_position()
        past_date = date.today() - timedelta(days=1)
        with pytest.raises(ValidationError, match="future"):
            RollSuggestion(
                current_position=pos,
                suggested_strike=410.0,
                suggested_expiry=past_date,
                estimated_cost=7.25,
                reason="Roll to new expiry",
            )

    def test_estimated_cost_must_be_non_negative(self):
        """Negative estimated cost should raise ValidationError."""
        pos = self._make_put_position()
        future_expiry = date.today() + timedelta(days=60)
        with pytest.raises(ValidationError):
            RollSuggestion(
                current_position=pos,
                suggested_strike=410.0,
                suggested_expiry=future_expiry,
                estimated_cost=-1.0,
                reason="Roll to new expiry",
            )

    def test_reason_must_not_be_empty(self):
        """Empty reason string should raise ValidationError."""
        pos = self._make_put_position()
        future_expiry = date.today() + timedelta(days=60)
        with pytest.raises(ValidationError):
            RollSuggestion(
                current_position=pos,
                suggested_strike=410.0,
                suggested_expiry=future_expiry,
                estimated_cost=7.25,
                reason="",
            )


class TestHedgeSizeRequest:
    """Validate HedgeSizeRequest Pydantic model constraints."""

    def test_valid_size_request(self):
        """A valid sizing request should instantiate with correct fields."""
        req = HedgeSizeRequest(
            portfolio_value=200000.0,
            underlyings=["QQQ", "SPY"],
            budget=500.0,
        )

        assert req.portfolio_value == 200000.0
        assert req.underlyings == ["QQQ", "SPY"]
        assert req.budget == 500.0
        assert req.target_contracts is None

    def test_underlyings_must_be_uppercase(self):
        """Lowercase tickers in underlyings should raise ValidationError."""
        with pytest.raises(ValidationError, match="uppercase"):
            HedgeSizeRequest(
                portfolio_value=200000.0,
                underlyings=["qqq"],
                budget=500.0,
            )

    def test_underlyings_must_not_be_empty(self):
        """Empty underlyings list should raise ValidationError."""
        with pytest.raises(ValidationError):
            HedgeSizeRequest(
                portfolio_value=200000.0,
                underlyings=[],
                budget=500.0,
            )

    def test_portfolio_value_must_be_positive(self):
        """Zero or negative portfolio value should raise ValidationError."""
        with pytest.raises(ValidationError):
            HedgeSizeRequest(
                portfolio_value=0.0,
                underlyings=["QQQ"],
                budget=500.0,
            )

        with pytest.raises(ValidationError):
            HedgeSizeRequest(
                portfolio_value=-100000.0,
                underlyings=["QQQ"],
                budget=500.0,
            )

    def test_target_contracts_optional(self):
        """target_contracts=None should be valid; positive int should work."""
        req_none = HedgeSizeRequest(
            portfolio_value=200000.0,
            underlyings=["QQQ"],
            budget=500.0,
            target_contracts=None,
        )
        assert req_none.target_contracts is None

        req_set = HedgeSizeRequest(
            portfolio_value=200000.0,
            underlyings=["QQQ"],
            budget=500.0,
            target_contracts=4,
        )
        assert req_set.target_contracts == 4
