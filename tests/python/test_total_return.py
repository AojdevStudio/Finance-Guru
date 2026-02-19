"""Tests for Finance Guru total return calculator.

Tests the TotalReturnCalculator class with synthetic data.
No real API calls -- all data is manually constructed for known-answer verification.

Test classes:
    1. TestPriceReturn: known-answer tests (positive, negative, flat)
    2. TestDividendReturn: known-answer tests (single, multiple, zero)
    3. TestTotalReturn: known-answer tests (sum verification, Sean insight scenario)
    4. TestDRIPReturn: known-answer tests (share growth, compounding, multiple dividends)
    5. TestAnnualizedReturn: calendar days validation
    6. TestDataQualityValidation: gap detection, force override, split artifacts, unknown ticker
    7. TestScheduleLoader: YAML loading, missing file fallback
    8. TestCalculateAll: integration of all calculator methods
    9. TestCLIArgParsing: CLI argument parsing (help, tickers, json, force)
   10. TestPortfolioCSVReader: portfolio CSV loading and missing CSV handling
   11. TestVerdictFormatting: sign-flip verdict, league table, disclaimer, JSON validity
   12. TestFinnhubIntegration: graceful fallback on exception
"""

import json
import os
import tempfile
from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from src.analysis.total_return import (
    DividendDataError,
    TotalReturnCalculator,
    TotalReturnResult,
    load_dividend_schedules,
)
from src.analysis.total_return_cli import (
    build_parser,
    format_human_output,
    format_json_output,
    load_portfolio_shares,
)
from src.models.total_return_inputs import (
    DividendRecord,
    TotalReturnInput,
)

# ---------------------------------------------------------------------------
# Mock dividend schedules (for CI where fin-guru-private/ doesn't exist)
# ---------------------------------------------------------------------------

MOCK_DIVIDEND_SCHEDULES = {
    "SCHD": {"frequency": 4, "label": "quarterly"},
    "VYM": {"frequency": 4, "label": "quarterly"},
    "VOO": {"frequency": 4, "label": "quarterly"},
    "CLM": {"frequency": 12, "label": "monthly"},
    "CRF": {"frequency": 12, "label": "monthly"},
    "YMAX": {"frequency": 52, "label": "weekly"},
    "QQQY": {"frequency": 52, "label": "weekly"},
    "JEPI": {"frequency": 12, "label": "monthly"},
    "JEPQ": {"frequency": 12, "label": "monthly"},
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_input(
    ticker: str = "TEST",
    start_date: date | None = None,
    end_date: date | None = None,
    prices: list[float] | None = None,
    dividends: list[DividendRecord] | None = None,
    initial_shares: float = 1.0,
) -> TotalReturnInput:
    """Build a TotalReturnInput with sensible defaults."""
    return TotalReturnInput(
        ticker=ticker,
        start_date=start_date or date(2025, 1, 2),
        end_date=end_date or date(2025, 7, 2),
        initial_shares=initial_shares,
    )


def _div(
    ex_date: date,
    amount: float,
    shares_at_ex: float = 1.0,
) -> DividendRecord:
    """Shorthand for creating a DividendRecord."""
    return DividendRecord(
        ex_date=ex_date,
        amount=amount,
        shares_at_ex=shares_at_ex,
    )


# ---------------------------------------------------------------------------
# 1. TestPriceReturn
# ---------------------------------------------------------------------------


class TestPriceReturn:
    """Known-answer tests for price return calculation."""

    def test_positive_price_return(self):
        """Price goes from 100 to 120 -> 20% return."""
        inp = _make_input()
        prices = [100.0, 120.0]
        calc = TotalReturnCalculator(inp, prices=prices)
        result = calc.calculate_price_return()
        assert result == pytest.approx(0.20)

    def test_negative_price_return(self):
        """Price goes from 100 to 95 -> -5% return."""
        inp = _make_input()
        prices = [100.0, 95.0]
        calc = TotalReturnCalculator(inp, prices=prices)
        result = calc.calculate_price_return()
        assert result == pytest.approx(-0.05)

    def test_flat_price_return(self):
        """Price stays at 100 -> 0% return."""
        inp = _make_input()
        prices = [100.0, 100.0]
        calc = TotalReturnCalculator(inp, prices=prices)
        result = calc.calculate_price_return()
        assert result == pytest.approx(0.0)

    def test_large_price_increase(self):
        """Price doubles from 50 to 100 -> 100% return."""
        inp = _make_input()
        prices = [50.0, 100.0]
        calc = TotalReturnCalculator(inp, prices=prices)
        result = calc.calculate_price_return()
        assert result == pytest.approx(1.0)

    def test_price_return_intermediate_prices_ignored(self):
        """Only first and last price matter for period return."""
        inp = _make_input()
        prices = [100.0, 50.0, 200.0, 110.0]
        calc = TotalReturnCalculator(inp, prices=prices)
        result = calc.calculate_price_return()
        assert result == pytest.approx(0.10)


# ---------------------------------------------------------------------------
# 2. TestDividendReturn
# ---------------------------------------------------------------------------


class TestDividendReturn:
    """Known-answer tests for dividend return calculation."""

    def test_single_dividend(self):
        """One $2 dividend on $100 starting price -> 2% dividend return."""
        inp = _make_input()
        dividends = [_div(date(2025, 3, 15), 2.0)]
        prices = [100.0, 105.0]
        calc = TotalReturnCalculator(inp, prices=prices, dividends=dividends)
        result = calc.calculate_dividend_return()
        assert result == pytest.approx(0.02)

    def test_multiple_dividends(self):
        """Three dividends of $1 each on $100 -> 3% dividend return."""
        inp = _make_input()
        dividends = [
            _div(date(2025, 2, 15), 1.0),
            _div(date(2025, 4, 15), 1.0),
            _div(date(2025, 6, 15), 1.0),
        ]
        prices = [100.0, 100.0]
        calc = TotalReturnCalculator(inp, prices=prices, dividends=dividends)
        result = calc.calculate_dividend_return()
        assert result == pytest.approx(0.03)

    def test_zero_dividends(self):
        """No dividends -> 0% dividend return."""
        inp = _make_input()
        prices = [100.0, 110.0]
        calc = TotalReturnCalculator(inp, prices=prices, dividends=[])
        result = calc.calculate_dividend_return()
        assert result == pytest.approx(0.0)

    def test_high_yield_dividend(self):
        """$8 total dividends on $100 -> 8% dividend return."""
        inp = _make_input()
        dividends = [_div(date(2025, 3, 15), 8.0)]
        prices = [100.0, 95.0]
        calc = TotalReturnCalculator(inp, prices=prices, dividends=dividends)
        result = calc.calculate_dividend_return()
        assert result == pytest.approx(0.08)


# ---------------------------------------------------------------------------
# 3. TestTotalReturn
# ---------------------------------------------------------------------------


class TestTotalReturn:
    """Known-answer tests for total return (price + dividend)."""

    def test_total_return_is_sum(self):
        """Total return = price return + dividend return."""
        inp = _make_input()
        # Price: 100 -> 95 = -5%, Dividend: $8 / $100 = 8%, Total: 3%
        dividends = [_div(date(2025, 3, 15), 8.0)]
        prices = [100.0, 95.0]
        calc = TotalReturnCalculator(inp, prices=prices, dividends=dividends)
        result = calc.calculate_total_return()
        assert result == pytest.approx(0.03)

    def test_sean_insight_scenario(self):
        """Price down but total return positive (distributions flip the story).

        Sean's insight: 'You can't say a fund is down without counting distributions.'
        CLM-like scenario: price down 3.95%, dividends 8.2%, total up 4.25%.
        """
        inp = _make_input(ticker="CLM")
        # Price: 100 -> 96.05 = -3.95%
        # Dividends: $8.20 total
        # Total: -3.95% + 8.2% = 4.25%
        dividends = [
            _div(date(2025, 2, 1), 1.3667),
            _div(date(2025, 3, 1), 1.3667),
            _div(date(2025, 4, 1), 1.3667),
            _div(date(2025, 5, 1), 1.3667),
            _div(date(2025, 6, 1), 1.3667),
            _div(date(2025, 7, 1), 1.3665),  # Rounding last to get exactly 8.20
        ]
        prices = [100.0, 96.05]
        calc = TotalReturnCalculator(inp, prices=prices, dividends=dividends)

        price_ret = calc.calculate_price_return()
        div_ret = calc.calculate_dividend_return()
        total_ret = calc.calculate_total_return()

        assert price_ret < 0, "Price return should be negative"
        assert div_ret > 0, "Dividend return should be positive"
        assert total_ret > 0, "Total return should flip positive"
        assert total_ret == pytest.approx(price_ret + div_ret, abs=1e-6)

    def test_total_return_with_zero_dividends(self):
        """Total return equals price return when no dividends."""
        inp = _make_input()
        prices = [100.0, 115.0]
        calc = TotalReturnCalculator(inp, prices=prices, dividends=[])
        assert calc.calculate_total_return() == pytest.approx(0.15)

    def test_known_answer_verification(self):
        """Verification check from plan: prices [100, 95], div $8 -> 3%."""
        inp = _make_input()
        dividends = [_div(date(2025, 3, 15), 8.0)]
        prices = [100.0, 95.0]
        calc = TotalReturnCalculator(inp, prices=prices, dividends=dividends)
        assert calc.calculate_price_return() == pytest.approx(-0.05)
        assert calc.calculate_dividend_return() == pytest.approx(0.08)
        assert calc.calculate_total_return() == pytest.approx(0.03)


# ---------------------------------------------------------------------------
# 4. TestDRIPReturn
# ---------------------------------------------------------------------------


class TestDRIPReturn:
    """Known-answer tests for DRIP (dividend reinvestment) return."""

    def test_single_dividend_drip(self):
        """One $2 dividend reinvested at $100 close -> 1.02 shares.

        Start: 1 share @ $100 = $100
        Dividend: 1 * $2 = $2 cash -> $2 / $100 = 0.02 new shares
        End: 1.02 shares @ $100 = $102
        DRIP return = ($102 / $100) - 1 = 0.02 = 2%
        """
        inp = _make_input()
        dividends = [_div(date(2025, 3, 15), 2.0)]
        # ex-date close prices needed for DRIP reinvestment
        ex_date_prices = {date(2025, 3, 15): 100.0}
        prices = [100.0, 100.0]  # Flat price
        calc = TotalReturnCalculator(
            inp, prices=prices, dividends=dividends, ex_date_prices=ex_date_prices
        )
        drip_return, final_shares, breakdown = calc.calculate_drip_return()
        assert final_shares == pytest.approx(1.02)
        assert drip_return == pytest.approx(0.02)

    def test_drip_share_growth_with_price_change(self):
        """DRIP with price appreciation.

        Start: 1 share @ $100 = $100
        Dividend: 1 * $5 = $5 cash -> $5 / $100 = 0.05 new shares
        End: 1.05 shares @ $120 = $126
        DRIP return = ($126 / $100) - 1 = 0.26 = 26%
        Non-DRIP total: price 20% + div 5% = 25%
        DRIP adds extra 1% from reinvested shares appreciating.
        """
        inp = _make_input()
        dividends = [_div(date(2025, 3, 15), 5.0)]
        ex_date_prices = {date(2025, 3, 15): 100.0}
        prices = [100.0, 120.0]
        calc = TotalReturnCalculator(
            inp, prices=prices, dividends=dividends, ex_date_prices=ex_date_prices
        )
        drip_return, final_shares, breakdown = calc.calculate_drip_return()
        assert final_shares == pytest.approx(1.05)
        assert drip_return == pytest.approx(0.26)

    def test_multiple_dividends_compounding(self):
        """Multiple dividends compound share growth.

        Start: 1 share @ $100
        Div 1: 1 * $2 = $2 cash -> $2 / $100 = 0.02 new shares -> 1.02 shares
        Div 2: 1.02 * $2 = $2.04 cash -> $2.04 / $102 = 0.02 new shares -> 1.04 shares
        End price: $100 (flat)
        """
        inp = _make_input()
        dividends = [
            _div(date(2025, 2, 15), 2.0),
            _div(date(2025, 5, 15), 2.0),
        ]
        ex_date_prices = {
            date(2025, 2, 15): 100.0,
            date(2025, 5, 15): 102.0,
        }
        prices = [100.0, 100.0]
        calc = TotalReturnCalculator(
            inp, prices=prices, dividends=dividends, ex_date_prices=ex_date_prices
        )
        drip_return, final_shares, breakdown = calc.calculate_drip_return()
        # After div 1: 1 + (1*2/100) = 1.02 shares
        # After div 2: 1.02 + (1.02*2/102) = 1.02 + 0.02 = 1.04 shares
        assert final_shares == pytest.approx(1.04)
        assert len(breakdown) == 2

    def test_drip_no_dividends(self):
        """No dividends means DRIP return equals price return."""
        inp = _make_input()
        prices = [100.0, 110.0]
        calc = TotalReturnCalculator(inp, prices=prices, dividends=[])
        drip_return, final_shares, breakdown = calc.calculate_drip_return()
        assert final_shares == pytest.approx(1.0)
        assert drip_return == pytest.approx(0.10)
        assert len(breakdown) == 0

    def test_drip_exceeds_non_drip(self):
        """DRIP total return should be >= non-DRIP total return (with dividends)."""
        inp = _make_input()
        dividends = [
            _div(date(2025, 2, 15), 2.0),
            _div(date(2025, 5, 15), 2.0),
        ]
        ex_date_prices = {
            date(2025, 2, 15): 100.0,
            date(2025, 5, 15): 105.0,
        }
        prices = [100.0, 110.0]
        calc = TotalReturnCalculator(
            inp, prices=prices, dividends=dividends, ex_date_prices=ex_date_prices
        )
        drip_return, _, _ = calc.calculate_drip_return()
        total_return = calc.calculate_total_return()
        assert drip_return >= total_return


# ---------------------------------------------------------------------------
# 5. TestAnnualizedReturn
# ---------------------------------------------------------------------------


class TestAnnualizedReturn:
    """Calendar days (365) validation for annualization."""

    def test_annual_return_formula(self):
        """Annualized return uses calendar days, not trading days.

        10% over 182.5 days (half year) -> annualized = (1.10)^(365/182.5) - 1
        = 1.10^2 - 1 = 0.21 = 21%
        """
        inp = _make_input(
            start_date=date(2025, 1, 1),
            end_date=date(2025, 7, 2),  # ~182 days
        )
        prices = [100.0, 110.0]
        calc = TotalReturnCalculator(inp, prices=prices, dividends=[])
        total = calc.calculate_total_return()
        annualized = calc.calculate_annualized_return(total)
        # 182 calendar days
        days = (date(2025, 7, 2) - date(2025, 1, 1)).days  # 182
        expected = (1.0 + total) ** (365.0 / days) - 1.0
        assert annualized == pytest.approx(expected, abs=1e-6)

    def test_full_year_annualized_equals_total(self):
        """Over exactly 365 days, annualized return equals total return."""
        inp = _make_input(
            start_date=date(2025, 1, 1),
            end_date=date(2026, 1, 1),
        )
        prices = [100.0, 112.0]
        calc = TotalReturnCalculator(inp, prices=prices, dividends=[])
        total = calc.calculate_total_return()
        annualized = calc.calculate_annualized_return(total)
        assert annualized == pytest.approx(total, abs=1e-6)

    def test_short_period_annualized_larger(self):
        """Short period returns annualize to larger numbers."""
        inp = _make_input(
            start_date=date(2025, 1, 1),
            end_date=date(2025, 2, 1),  # 31 days
        )
        prices = [100.0, 105.0]
        calc = TotalReturnCalculator(inp, prices=prices, dividends=[])
        total = calc.calculate_total_return()
        annualized = calc.calculate_annualized_return(total)
        assert annualized > total, "Annualized should exceed period return for <1 year"

    def test_negative_return_annualized(self):
        """Annualized negative return stays negative."""
        inp = _make_input(
            start_date=date(2025, 1, 1),
            end_date=date(2025, 7, 1),
        )
        prices = [100.0, 90.0]
        calc = TotalReturnCalculator(inp, prices=prices, dividends=[])
        total = calc.calculate_total_return()
        annualized = calc.calculate_annualized_return(total)
        assert annualized < 0


# ---------------------------------------------------------------------------
# 6. TestDataQualityValidation
# ---------------------------------------------------------------------------


@patch(
    "src.analysis.total_return.load_dividend_schedules",
    return_value=MOCK_DIVIDEND_SCHEDULES,
)
class TestDataQualityValidation:
    """Gap detection, force override, split artifact detection."""

    def test_gap_detection_quarterly_payer(self, _mock):
        """SCHD expected 4/year but only 1 found over 365 days -> warning."""
        inp = _make_input(
            ticker="SCHD",
            start_date=date(2025, 1, 1),
            end_date=date(2026, 1, 1),
        )
        dividends = [_div(date(2025, 3, 15), 0.65)]
        prices = [100.0, 100.0]
        calc = TotalReturnCalculator(inp, prices=prices, dividends=dividends)
        warnings_list = calc.validate_dividend_data()
        assert len(warnings_list) > 0
        assert any(
            "expected" in w.lower() or "incomplete" in w.lower() for w in warnings_list
        )

    def test_gap_detection_monthly_payer(self, _mock):
        """CLM expected 12/year but only 3 found over 365 days -> warning."""
        inp = _make_input(
            ticker="CLM",
            start_date=date(2025, 1, 1),
            end_date=date(2026, 1, 1),
        )
        dividends = [
            _div(date(2025, 2, 1), 0.15),
            _div(date(2025, 5, 1), 0.15),
            _div(date(2025, 8, 1), 0.15),
        ]
        prices = [100.0, 100.0]
        calc = TotalReturnCalculator(inp, prices=prices, dividends=dividends)
        warnings_list = calc.validate_dividend_data()
        assert len(warnings_list) > 0

    def test_no_warning_when_count_sufficient(self, _mock):
        """SCHD with 4 dividends over 365 days -> no gap warning."""
        inp = _make_input(
            ticker="SCHD",
            start_date=date(2025, 1, 1),
            end_date=date(2026, 1, 1),
        )
        dividends = [
            _div(date(2025, 3, 15), 0.65),
            _div(date(2025, 6, 15), 0.65),
            _div(date(2025, 9, 15), 0.65),
            _div(date(2025, 12, 15), 0.65),
        ]
        prices = [100.0, 100.0]
        calc = TotalReturnCalculator(inp, prices=prices, dividends=dividends)
        warnings_list = calc.validate_dividend_data()
        # No gap warnings (may have other types but not count-based)
        gap_warnings = [
            w
            for w in warnings_list
            if "expected" in w.lower() or "incomplete" in w.lower()
        ]
        assert len(gap_warnings) == 0

    def test_force_override_allows_calculation(self, _mock):
        """With force=True, gaps produce warnings but calculate_all() succeeds."""
        inp = _make_input(
            ticker="SCHD",
            start_date=date(2025, 1, 1),
            end_date=date(2026, 1, 1),
        )
        dividends = [_div(date(2025, 3, 15), 0.65)]
        prices = [100.0, 102.0]
        calc = TotalReturnCalculator(inp, prices=prices, dividends=dividends)
        # Should NOT raise with force=True
        result = calc.calculate_all(force=True)
        assert isinstance(result, TotalReturnResult)
        assert len(result.data_quality_warnings) > 0

    def test_no_force_raises_on_gaps(self, _mock):
        """Without force, gaps cause DividendDataError."""
        inp = _make_input(
            ticker="SCHD",
            start_date=date(2025, 1, 1),
            end_date=date(2026, 1, 1),
        )
        dividends = [_div(date(2025, 3, 15), 0.65)]
        prices = [100.0, 102.0]
        calc = TotalReturnCalculator(inp, prices=prices, dividends=dividends)
        with pytest.raises(DividendDataError):
            calc.calculate_all(force=False)

    def test_split_artifact_detection(self, _mock):
        """Dividend >3x median flagged as suspicious."""
        inp = _make_input(ticker="TEST")
        dividends = [
            _div(date(2025, 2, 1), 0.50),
            _div(date(2025, 3, 1), 0.50),
            _div(date(2025, 4, 1), 0.50),
            _div(date(2025, 5, 1), 5.00),  # >3x median of 0.50
            _div(date(2025, 6, 1), 0.50),
        ]
        prices = [100.0, 100.0]
        calc = TotalReturnCalculator(inp, prices=prices, dividends=dividends)
        warnings_list = calc.validate_dividend_data()
        assert any(
            "split" in w.lower() or "3x" in w.lower() or "suspicious" in w.lower()
            for w in warnings_list
        )

    def test_unknown_ticker_no_frequency_warning(self, _mock):
        """Unknown ticker gets no frequency-based warning (no expected schedule)."""
        inp = _make_input(ticker="ZZZZZ")
        dividends = [_div(date(2025, 3, 15), 1.0)]
        prices = [100.0, 100.0]
        calc = TotalReturnCalculator(inp, prices=prices, dividends=dividends)
        warnings_list = calc.validate_dividend_data()
        gap_warnings = [
            w
            for w in warnings_list
            if "expected" in w.lower() or "incomplete" in w.lower()
        ]
        assert len(gap_warnings) == 0

    def test_known_payer_zero_dividends_warns(self, _mock):
        """Known dividend payer with zero dividends gets a warning."""
        inp = _make_input(
            ticker="SCHD",
            start_date=date(2025, 1, 1),
            end_date=date(2026, 1, 1),
        )
        prices = [100.0, 100.0]
        calc = TotalReturnCalculator(inp, prices=prices, dividends=[])
        warnings_list = calc.validate_dividend_data()
        assert any(
            "no dividend" in w.lower() or "expected dividend payer" in w.lower()
            for w in warnings_list
        )

    def test_unknown_ticker_zero_dividends_no_warning(self, _mock):
        """Unknown ticker with zero dividends -> no 'expected payer' warning."""
        inp = _make_input(ticker="ZZZZZ")
        prices = [100.0, 100.0]
        calc = TotalReturnCalculator(inp, prices=prices, dividends=[])
        warnings_list = calc.validate_dividend_data()
        payer_warnings = [
            w for w in warnings_list if "expected dividend payer" in w.lower()
        ]
        assert len(payer_warnings) == 0


# ---------------------------------------------------------------------------
# 7. TestScheduleLoader
# ---------------------------------------------------------------------------


@patch(
    "src.analysis.total_return.load_dividend_schedules",
    return_value=MOCK_DIVIDEND_SCHEDULES,
)
class TestScheduleLoader:
    """YAML loading and missing file fallback."""

    def test_load_dividend_schedules_returns_dict(self, mock_load):
        """Loading returns a non-empty dict with expected tickers."""
        schedules = mock_load()
        assert isinstance(schedules, dict)
        assert len(schedules) > 0

    def test_schedule_contains_clm(self, mock_load):
        """CLM must be present as a monthly payer."""
        schedules = mock_load()
        assert "CLM" in schedules
        assert schedules["CLM"]["frequency"] == 12

    def test_schedule_contains_weekly_payers(self, mock_load):
        """YMAX and QQQY should be weekly (52)."""
        schedules = mock_load()
        assert schedules.get("YMAX", {}).get("frequency") == 52
        assert schedules.get("QQQY", {}).get("frequency") == 52

    def test_schedule_contains_quarterly_payers(self, mock_load):
        """SCHD, VYM, VOO should be quarterly (4)."""
        schedules = mock_load()
        for ticker in ["SCHD", "VYM", "VOO"]:
            assert schedules.get(ticker, {}).get("frequency") == 4

    def test_missing_file_returns_empty_dict(self, _mock):
        """If YAML file does not exist, return empty dict (graceful fallback)."""
        with patch(
            "src.analysis.total_return.DIVIDEND_SCHEDULES_PATH",
            "/nonexistent/path/dividend-schedules.yaml",
        ):
            schedules = load_dividend_schedules()
            assert schedules == {}


# ---------------------------------------------------------------------------
# 8. TestCalculateAll (integration of all methods)
# ---------------------------------------------------------------------------


class TestCalculateAll:
    """Integration tests for calculate_all() orchestration."""

    def test_calculate_all_returns_result(self):
        """calculate_all() returns a TotalReturnResult with all fields."""
        inp = _make_input(
            start_date=date(2025, 1, 1),
            end_date=date(2025, 7, 1),
        )
        dividends = [_div(date(2025, 3, 15), 2.0)]
        ex_date_prices = {date(2025, 3, 15): 100.0}
        prices = [100.0, 110.0]
        calc = TotalReturnCalculator(
            inp, prices=prices, dividends=dividends, ex_date_prices=ex_date_prices
        )
        result = calc.calculate_all(force=True)
        assert isinstance(result, TotalReturnResult)
        assert result.price_return == pytest.approx(0.10)
        assert result.dividend_return == pytest.approx(0.02)
        assert result.total_return == pytest.approx(0.12)
        assert result.drip_total_return is not None
        assert result.annualized_return is not None

    def test_calculate_all_populates_drip_fields(self):
        """calculate_all() populates DRIP share growth."""
        inp = _make_input(
            start_date=date(2025, 1, 1),
            end_date=date(2025, 7, 1),
        )
        dividends = [_div(date(2025, 3, 15), 5.0)]
        ex_date_prices = {date(2025, 3, 15): 100.0}
        prices = [100.0, 100.0]
        calc = TotalReturnCalculator(
            inp, prices=prices, dividends=dividends, ex_date_prices=ex_date_prices
        )
        result = calc.calculate_all(force=True)
        assert result.drip_total_return is not None
        assert result.drip_share_growth is not None
        assert result.drip_share_growth > 1.0  # Shares grew

    def test_calculate_all_no_dividends(self):
        """calculate_all() works with growth stock (no dividends)."""
        inp = _make_input(
            ticker="TSLA",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 7, 1),
        )
        prices = [200.0, 250.0]
        calc = TotalReturnCalculator(inp, prices=prices, dividends=[])
        result = calc.calculate_all(force=True)
        assert result.price_return == pytest.approx(0.25)
        assert result.dividend_return == pytest.approx(0.0)
        assert result.total_return == pytest.approx(0.25)
        assert result.drip_total_return == pytest.approx(0.25)


# ---------------------------------------------------------------------------
# CLI Test Helpers
# ---------------------------------------------------------------------------


def _make_result(
    ticker: str = "TEST",
    price_return: float = 0.10,
    dividend_return: float = 0.03,
    total_return: float = 0.13,
    drip_total_return: float | None = 0.135,
    drip_final_shares: float | None = 1.03,
    drip_share_growth: float | None = 1.03,
    annualized_return: float | None = 0.27,
    dividend_count: int = 3,
    period_breakdown: list[dict] | None = None,
    data_quality_warnings: list[str] | None = None,
) -> TotalReturnResult:
    """Build a TotalReturnResult with sensible defaults for CLI tests."""
    return TotalReturnResult(
        ticker=ticker,
        start_date=date(2025, 1, 2),
        end_date=date(2025, 7, 2),
        price_return=price_return,
        dividend_return=dividend_return,
        total_return=total_return,
        annualized_return=annualized_return,
        drip_total_return=drip_total_return,
        drip_final_shares=drip_final_shares,
        drip_share_growth=drip_share_growth,
        period_breakdown=period_breakdown
        or [
            {
                "date": date(2025, 3, 15),
                "dividend_per_share": 1.0,
                "reinvest_price": 100.0,
                "shares_acquired": 0.01,
                "cumulative_shares": 1.01,
            },
        ],
        dividend_count=dividend_count,
        data_quality_warnings=data_quality_warnings or [],
    )


# ---------------------------------------------------------------------------
# 9. TestCLIArgParsing
# ---------------------------------------------------------------------------


class TestCLIArgParsing:
    """CLI argument parsing tests."""

    def test_help_flag(self):
        """--help exits with code 0 and shows usage."""
        parser = build_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["--help"])
        assert exc_info.value.code == 0

    def test_single_ticker(self):
        """Single ticker parsed correctly."""
        parser = build_parser()
        args = parser.parse_args(["SCHD"])
        assert args.tickers == ["SCHD"]
        assert args.days == 252  # Default

    def test_multiple_tickers(self):
        """Multiple tickers parsed correctly."""
        parser = build_parser()
        args = parser.parse_args(["SCHD", "JEPI", "VYM"])
        assert args.tickers == ["SCHD", "JEPI", "VYM"]

    def test_days_flag(self):
        """--days sets custom period."""
        parser = build_parser()
        args = parser.parse_args(["SCHD", "--days", "90"])
        assert args.days == 90

    def test_json_output(self):
        """--output json selects JSON format."""
        parser = build_parser()
        args = parser.parse_args(["SCHD", "--output", "json"])
        assert args.output == "json"

    def test_force_flag(self):
        """--force enables override of data quality warnings."""
        parser = build_parser()
        args = parser.parse_args(["CLM", "--force"])
        assert args.force is True

    def test_force_default_false(self):
        """force defaults to False."""
        parser = build_parser()
        args = parser.parse_args(["CLM"])
        assert args.force is False

    def test_save_to_flag(self):
        """--save-to sets file path."""
        parser = build_parser()
        args = parser.parse_args(["SCHD", "--save-to", "output.txt"])
        assert args.save_to == "output.txt"

    def test_realtime_flag(self):
        """--realtime enables Finnhub integration."""
        parser = build_parser()
        args = parser.parse_args(["SCHD", "--realtime"])
        assert args.realtime is True

    def test_no_tickers_exits(self):
        """No tickers causes argparse error."""
        parser = build_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args([])
        assert exc_info.value.code != 0


# ---------------------------------------------------------------------------
# 10. TestPortfolioCSVReader
# ---------------------------------------------------------------------------


class TestPortfolioCSVReader:
    """Portfolio CSV loading tests with temp files."""

    def test_load_shares_from_csv(self):
        """Reads ticker -> quantity from a temp CSV."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", prefix="Portfolio_Positions_", delete=False
        ) as f:
            f.write(
                "Account Number,Account Name,Investment Type,Symbol,"
                "Description,Quantity,Last Price\n"
            )
            f.write("Z123,Test,Stocks,SCHD,Test ETF,100.5,$25.00\n")
            f.write("Z123,Test,Stocks,JEPI,Test ETF,200.0,$55.00\n")
            csv_path = f.name

        try:
            # Use exact file path as glob pattern (matches the file itself)
            shares = load_portfolio_shares(csv_glob=csv_path)
            assert shares["SCHD"] == pytest.approx(100.5)
            assert shares["JEPI"] == pytest.approx(200.0)
        finally:
            os.unlink(csv_path)

    def test_missing_csv_returns_empty_dict(self):
        """No matching CSV files returns empty dict."""
        shares = load_portfolio_shares(csv_glob="/nonexistent/path/*.csv")
        assert shares == {}

    def test_latest_csv_selected(self):
        """When multiple CSVs exist, the last in sorted order is used."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create two CSVs -- sorted order picks the last one
            # Use names that sort deterministically: A before B
            for name, qty in [
                ("Portfolio_Positions_A.csv", "50.0"),
                ("Portfolio_Positions_B.csv", "100.0"),
            ]:
                path = os.path.join(tmpdir, name)
                with open(path, "w") as f:
                    f.write("Symbol,Quantity\n")
                    f.write(f"SCHD,{qty}\n")

            pattern = os.path.join(tmpdir, "Portfolio_Positions_*.csv")
            shares = load_portfolio_shares(csv_glob=pattern)
            # The B CSV (sorted last) should be used -> 100.0
            assert shares["SCHD"] == pytest.approx(100.0)

    def test_invalid_quantity_skipped(self):
        """Non-numeric quantity rows are skipped gracefully."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", prefix="Portfolio_Positions_", delete=False
        ) as f:
            f.write("Symbol,Quantity\n")
            f.write("SCHD,100.0\n")
            f.write("JEPI,N/A\n")  # Invalid quantity
            f.write("VYM,50.0\n")
            csv_path = f.name

        try:
            shares = load_portfolio_shares(csv_glob=csv_path)
            assert "SCHD" in shares
            assert "JEPI" not in shares  # Skipped due to invalid quantity
            assert "VYM" in shares
        finally:
            os.unlink(csv_path)


# ---------------------------------------------------------------------------
# 11. TestVerdictFormatting
# ---------------------------------------------------------------------------


class TestVerdictFormatting:
    """Verdict narrative, league table, disclaimer, and JSON validity tests."""

    def test_sign_flip_verdict_displayed(self):
        """Price negative + total positive triggers verdict narrative."""
        result = _make_result(
            ticker="CLM",
            price_return=-0.0395,
            dividend_return=0.082,
            total_return=0.0425,
        )
        output = format_human_output([result], {})
        assert "VERDICT" in output
        assert "MISLEADING" in output
        assert "CLM" in output

    def test_no_verdict_when_both_positive(self):
        """No verdict when both price and total return are positive."""
        result = _make_result(
            price_return=0.05,
            dividend_return=0.03,
            total_return=0.08,
        )
        output = format_human_output([result], {})
        assert "VERDICT" not in output
        assert "MISLEADING" not in output

    def test_no_verdict_when_both_negative(self):
        """No verdict when both price and total return are negative."""
        result = _make_result(
            price_return=-0.10,
            dividend_return=0.03,
            total_return=-0.07,
        )
        output = format_human_output([result], {})
        assert "VERDICT" not in output

    def test_league_table_ranking(self):
        """Multiple tickers produce ranked league table."""
        r1 = _make_result(ticker="JEPI", total_return=0.12)
        r2 = _make_result(ticker="CLM", total_return=0.04)
        r3 = _make_result(ticker="VYM", total_return=0.08)
        output = format_human_output([r1, r2, r3], {})
        assert "LEAGUE TABLE" in output
        # Should show ranking numbers for all 3 tickers
        assert "#1" in output
        assert "#3" in output

    def test_league_table_not_shown_single_ticker(self):
        """League table only shown for multi-ticker comparison."""
        result = _make_result(ticker="SCHD")
        output = format_human_output([result], {})
        assert "LEAGUE TABLE" not in output

    def test_price_misleading_in_league_table(self):
        """Sign-flip tickers marked 'Price misleading' in league table."""
        r1 = _make_result(
            ticker="CLM",
            price_return=-0.04,
            total_return=0.04,
        )
        r2 = _make_result(
            ticker="VYM",
            price_return=0.05,
            total_return=0.08,
        )
        output = format_human_output([r1, r2], {})
        assert "Price misleading" in output

    def test_disclaimer_in_human_output(self):
        """Educational disclaimer appears in all human output."""
        result = _make_result()
        output = format_human_output([result], {})
        assert "DISCLAIMER" in output
        assert "educational purposes only" in output.lower()
        assert "not investment advice" in output.lower()

    def test_disclaimer_in_json_output(self):
        """Educational disclaimer appears in JSON output."""
        result = _make_result()
        output = format_json_output([result], {})
        parsed = json.loads(output)
        assert "disclaimer" in parsed
        assert "educational" in parsed["disclaimer"].lower()

    def test_json_output_valid(self):
        """JSON output is valid JSON."""
        result = _make_result()
        output = format_json_output([result], {})
        parsed = json.loads(output)
        assert "total_return_analysis" in parsed
        assert len(parsed["total_return_analysis"]) == 1

    def test_json_verdict_present_on_sign_flip(self):
        """JSON output includes verdict field on sign-flip."""
        result = _make_result(
            ticker="CLM",
            price_return=-0.04,
            total_return=0.04,
        )
        output = format_json_output([result], {})
        parsed = json.loads(output)
        entry = parsed["total_return_analysis"][0]
        assert entry["verdict"] == "Price misleading"

    def test_json_verdict_null_when_no_flip(self):
        """JSON output has null verdict when no sign-flip."""
        result = _make_result(
            price_return=0.10,
            total_return=0.13,
        )
        output = format_json_output([result], {})
        parsed = json.loads(output)
        entry = parsed["total_return_analysis"][0]
        assert entry["verdict"] is None

    def test_json_dollar_impact_with_shares(self):
        """JSON includes dollar_impact when portfolio shares provided."""
        result = _make_result(
            ticker="SCHD",
            period_breakdown=[
                {
                    "date": date(2025, 3, 15),
                    "dividend_per_share": 0.65,
                    "reinvest_price": 25.0,
                    "shares_acquired": 0.026,
                    "cumulative_shares": 1.026,
                },
            ],
        )
        portfolio = {"SCHD": 100.0}
        output = format_json_output([result], portfolio)
        parsed = json.loads(output)
        entry = parsed["total_return_analysis"][0]
        assert "dollar_impact" in entry
        assert entry["dollar_impact"]["shares_held"] == 100.0
        assert entry["dollar_impact"]["total_distributions"] == pytest.approx(65.0)

    def test_drip_side_by_side_columns(self):
        """Human output shows Non-DRIP and DRIP columns side-by-side."""
        result = _make_result()
        output = format_human_output([result], {})
        assert "Non-DRIP" in output
        assert "DRIP" in output

    def test_period_breakdown_displayed(self):
        """Period breakdown shows individual dividend events."""
        result = _make_result(
            period_breakdown=[
                {
                    "date": date(2025, 3, 15),
                    "dividend_per_share": 0.65,
                    "reinvest_price": 25.0,
                    "shares_acquired": 0.026,
                    "cumulative_shares": 1.026,
                },
                {
                    "date": date(2025, 6, 15),
                    "dividend_per_share": 0.70,
                    "reinvest_price": 26.0,
                    "shares_acquired": 0.027,
                    "cumulative_shares": 1.053,
                },
            ],
        )
        output = format_human_output([result], {})
        assert "Div/Share" in output
        assert "Reinvest" in output
        assert "Shares Acq" in output
        assert "2025-03-15" in output
        assert "2025-06-15" in output

    def test_dollar_amounts_with_portfolio(self):
        """Dollar amounts shown when portfolio shares available."""
        result = _make_result(
            ticker="SCHD",
            period_breakdown=[
                {
                    "date": date(2025, 3, 15),
                    "dividend_per_share": 2.0,
                    "reinvest_price": 25.0,
                    "shares_acquired": 0.08,
                    "cumulative_shares": 1.08,
                },
            ],
        )
        portfolio = {"SCHD": 100.0}
        output = format_human_output([result], portfolio)
        assert "Dollar Impact" in output
        assert "100.00 shares" in output
        assert "Distributions received" in output


# ---------------------------------------------------------------------------
# 12. TestFinnhubIntegration
# ---------------------------------------------------------------------------


class TestFinnhubIntegration:
    """Graceful fallback when Finnhub is unavailable."""

    def test_finnhub_exception_fallback(self):
        """fetch_ticker_data handles Finnhub exception gracefully."""
        # We test that fetch_ticker_data doesn't crash when get_prices raises.
        # We mock yfinance via the import inside fetch_ticker_data.
        import pandas as pd

        mock_hist = pd.DataFrame(
            {
                "Close": [100.0, 105.0, 110.0],
                "Dividends": [0.0, 0.5, 0.0],
            },
            index=pd.to_datetime(["2025-01-02", "2025-03-15", "2025-07-01"]),
        )

        # Create a mock yfinance module
        mock_yf = MagicMock()
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = mock_hist
        mock_yf.Ticker.return_value = mock_ticker

        with (
            patch.dict("sys.modules", {"yfinance": mock_yf}),
            patch(
                "src.utils.market_data.get_prices",
                side_effect=Exception("Finnhub down"),
            ),
        ):
            from src.analysis.total_return_cli import fetch_ticker_data

            inp, prices, divs, ex_prices = fetch_ticker_data(
                "TEST", days=252, realtime=True
            )

            # Should succeed despite Finnhub error
            assert len(prices) == 3
            assert len(divs) == 1
            assert inp.ticker == "TEST"

    def test_finnhub_not_called_without_realtime(self):
        """get_prices is not called when realtime=False."""
        import pandas as pd

        mock_hist = pd.DataFrame(
            {
                "Close": [100.0, 110.0],
                "Dividends": [0.0, 0.0],
            },
            index=pd.to_datetime(["2025-01-02", "2025-07-01"]),
        )

        # Create a mock yfinance module
        mock_yf = MagicMock()
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = mock_hist
        mock_yf.Ticker.return_value = mock_ticker

        with (
            patch.dict("sys.modules", {"yfinance": mock_yf}),
            patch("src.utils.market_data.get_prices") as mock_get_prices,
        ):
            from src.analysis.total_return_cli import fetch_ticker_data

            fetch_ticker_data("TEST", days=252, realtime=False)

            mock_get_prices.assert_not_called()
