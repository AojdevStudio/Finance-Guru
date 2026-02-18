"""Tests for total return Pydantic models (Phase 6, HEDG-03).

Validates TotalReturnInput, DividendRecord, and TickerReturn models
including valid construction, field-level constraints, cross-field
model validators, and default behavior.

Author: Finance Guru Development Team
"""

from __future__ import annotations

import sys
import warnings
from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

# Add project root for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.models.total_return_inputs import (
    DividendRecord,
    TickerReturn,
    TotalReturnInput,
)


class TestDividendRecord:
    """Validate DividendRecord Pydantic model constraints."""

    def test_valid_dividend(self):
        """A fully populated dividend record should instantiate."""
        div = DividendRecord(
            ex_date=date(2025, 12, 15),
            amount=0.65,
            shares_at_ex=100.0,
        )

        assert div.ex_date == date(2025, 12, 15)
        assert div.amount == 0.65
        assert div.shares_at_ex == 100.0
        assert div.payment_date is None

    def test_amount_must_be_positive(self):
        """Zero or negative dividend amount should raise ValidationError."""
        with pytest.raises(ValidationError):
            DividendRecord(
                ex_date=date(2025, 12, 15),
                amount=0.0,
                shares_at_ex=100.0,
            )

        with pytest.raises(ValidationError):
            DividendRecord(
                ex_date=date(2025, 12, 15),
                amount=-0.50,
                shares_at_ex=100.0,
            )

    def test_shares_at_ex_must_be_positive(self):
        """Zero shares_at_ex should raise ValidationError."""
        with pytest.raises(ValidationError):
            DividendRecord(
                ex_date=date(2025, 12, 15),
                amount=0.65,
                shares_at_ex=0.0,
            )

    def test_payment_date_optional(self):
        """payment_date=None should be valid, explicit date should work."""
        div_no_date = DividendRecord(
            ex_date=date(2025, 12, 15),
            amount=0.65,
            shares_at_ex=100.0,
            payment_date=None,
        )
        assert div_no_date.payment_date is None

        div_with_date = DividendRecord(
            ex_date=date(2025, 12, 15),
            amount=0.65,
            shares_at_ex=100.0,
            payment_date=date(2025, 12, 20),
        )
        assert div_with_date.payment_date == date(2025, 12, 20)


class TestTotalReturnInput:
    """Validate TotalReturnInput Pydantic model constraints."""

    def test_valid_input(self):
        """A valid total return input should instantiate with correct fields."""
        inp = TotalReturnInput(
            ticker="SCHD",
            start_date=date(2025, 1, 1),
            end_date=date(2026, 1, 1),
            include_drip=True,
        )

        assert inp.ticker == "SCHD"
        assert inp.start_date == date(2025, 1, 1)
        assert inp.end_date == date(2026, 1, 1)
        assert inp.include_drip is True

    def test_ticker_must_be_uppercase(self):
        """Lowercase ticker should raise ValidationError."""
        with pytest.raises(ValidationError, match="uppercase"):
            TotalReturnInput(
                ticker="schd",
                start_date=date(2025, 1, 1),
                end_date=date(2026, 1, 1),
            )

    def test_end_date_must_be_after_start_date(self):
        """end_date equal to or before start_date should raise ValidationError."""
        with pytest.raises(ValidationError, match="end_date"):
            TotalReturnInput(
                ticker="SCHD",
                start_date=date(2026, 1, 1),
                end_date=date(2025, 1, 1),
            )

        with pytest.raises(ValidationError, match="end_date"):
            TotalReturnInput(
                ticker="SCHD",
                start_date=date(2025, 6, 15),
                end_date=date(2025, 6, 15),
            )

    def test_include_drip_defaults_true(self):
        """Omitting include_drip should default to True."""
        inp = TotalReturnInput(
            ticker="SCHD",
            start_date=date(2025, 1, 1),
            end_date=date(2026, 1, 1),
        )

        assert inp.include_drip is True

    def test_initial_shares_defaults_one(self):
        """Omitting initial_shares should default to 1.0."""
        inp = TotalReturnInput(
            ticker="SCHD",
            start_date=date(2025, 1, 1),
            end_date=date(2026, 1, 1),
        )

        assert inp.initial_shares == 1.0


class TestTickerReturn:
    """Validate TickerReturn Pydantic model constraints."""

    def test_valid_return(self):
        """A fully populated ticker return should instantiate with correct fields."""
        ret = TickerReturn(
            ticker="SCHD",
            start_date=date(2025, 1, 1),
            end_date=date(2026, 1, 1),
            price_return=0.05,
            dividend_return=0.035,
            total_return=0.085,
            final_shares=103.5,
        )

        assert ret.ticker == "SCHD"
        assert ret.total_return == 0.085
        assert ret.price_return == 0.05
        assert ret.dividend_return == 0.035
        assert ret.final_shares == 103.5

    def test_dividends_list_can_contain_records(self):
        """Passing a list of DividendRecord objects should work."""
        divs = [
            DividendRecord(
                ex_date=date(2025, 3, 15),
                amount=0.60,
                shares_at_ex=100.0,
            ),
            DividendRecord(
                ex_date=date(2025, 6, 15),
                amount=0.65,
                shares_at_ex=101.2,
            ),
        ]

        ret = TickerReturn(
            ticker="SCHD",
            start_date=date(2025, 1, 1),
            end_date=date(2026, 1, 1),
            price_return=0.05,
            dividend_return=0.035,
            total_return=0.085,
            dividends=divs,
        )

        assert len(ret.dividends) == 2
        assert ret.dividends[0].amount == 0.60
        assert ret.dividends[1].shares_at_ex == 101.2

    def test_data_quality_warnings_defaults_empty(self):
        """Omitting data_quality_warnings should give empty list."""
        ret = TickerReturn(
            ticker="SCHD",
            start_date=date(2025, 1, 1),
            end_date=date(2026, 1, 1),
            price_return=0.05,
            dividend_return=0.035,
            total_return=0.085,
        )

        assert ret.data_quality_warnings == []

    def test_final_shares_must_be_positive(self):
        """Zero final_shares should raise ValidationError."""
        with pytest.raises(ValidationError):
            TickerReturn(
                ticker="SCHD",
                start_date=date(2025, 1, 1),
                end_date=date(2026, 1, 1),
                price_return=0.05,
                dividend_return=0.035,
                total_return=0.085,
                final_shares=0.0,
            )

    def test_total_return_consistency_warns_on_mismatch(self):
        """Significant deviation from price+dividend should trigger warning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            TickerReturn(
                ticker="SCHD",
                start_date=date(2025, 1, 1),
                end_date=date(2026, 1, 1),
                price_return=0.05,
                dividend_return=0.035,
                total_return=0.15,  # 0.15 != 0.05 + 0.035 = 0.085
            )
            assert len(w) == 1
            assert "deviates" in str(w[0].message)

    def test_total_return_consistency_no_warning_when_close(self):
        """Small rounding difference should not trigger warning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            TickerReturn(
                ticker="SCHD",
                start_date=date(2025, 1, 1),
                end_date=date(2026, 1, 1),
                price_return=0.05,
                dividend_return=0.035,
                total_return=0.0851,  # Close enough (diff < 0.01)
            )
            # Filter only our specific warnings (not Pydantic internals)
            relevant = [x for x in w if "deviates" in str(x.message)]
            assert len(relevant) == 0
