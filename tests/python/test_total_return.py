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
"""

from datetime import date
from unittest.mock import patch

import pytest
from src.analysis.total_return import (
    DividendDataError,
    TotalReturnCalculator,
    TotalReturnResult,
    load_dividend_schedules,
)

from src.models.total_return_inputs import (
    DividendRecord,
    TotalReturnInput,
)

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


class TestDataQualityValidation:
    """Gap detection, force override, split artifact detection."""

    def test_gap_detection_quarterly_payer(self):
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

    def test_gap_detection_monthly_payer(self):
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

    def test_no_warning_when_count_sufficient(self):
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

    def test_force_override_allows_calculation(self):
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

    def test_no_force_raises_on_gaps(self):
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

    def test_split_artifact_detection(self):
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

    def test_unknown_ticker_no_frequency_warning(self):
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

    def test_known_payer_zero_dividends_warns(self):
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

    def test_unknown_ticker_zero_dividends_no_warning(self):
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


class TestScheduleLoader:
    """YAML loading and missing file fallback."""

    def test_load_dividend_schedules_returns_dict(self):
        """Loading existing YAML returns a non-empty dict."""
        schedules = load_dividend_schedules()
        assert isinstance(schedules, dict)
        # Should have at least one ticker
        assert len(schedules) > 0

    def test_schedule_contains_clm(self):
        """CLM must be present as a monthly payer."""
        schedules = load_dividend_schedules()
        assert "CLM" in schedules
        assert schedules["CLM"]["frequency"] == 12

    def test_schedule_contains_weekly_payers(self):
        """YMAX and QQQY should be weekly (52)."""
        schedules = load_dividend_schedules()
        assert schedules.get("YMAX", {}).get("frequency") == 52
        assert schedules.get("QQQY", {}).get("frequency") == 52

    def test_schedule_contains_quarterly_payers(self):
        """SCHD, VYM, VOO should be quarterly (4)."""
        schedules = load_dividend_schedules()
        for ticker in ["SCHD", "VYM", "VOO"]:
            assert schedules.get(ticker, {}).get("frequency") == 4

    def test_missing_file_returns_empty_dict(self):
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
