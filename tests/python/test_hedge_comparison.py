"""
Tests for Hedge Comparison Calculator (SQQQ vs Protective Puts).

These tests verify the HedgeComparisonCalculator functionality including:
- SQQQ day-by-day simulation with volatility drag
- Protective put payoff with IV expansion
- Breakeven analysis for both strategies
- Full comparison output structure and winner logic

All tests use known-answer methodology (STD-04):
- Constant daily returns produce analytically deterministic SQQQ values
- Flat markets isolate fee drag from volatility drag
- Deep ITM puts have analytically predictable intrinsic value
- ATM put breakeven is calculable from strike and premium

RUNNING TESTS:
    # Run all hedge comparison tests
    uv run pytest tests/python/test_hedge_comparison.py -v

    # Run only SQQQ simulation tests
    uv run pytest tests/python/test_hedge_comparison.py::TestSQQQSimulation -v

NOTE: Full HEDG-12 integration (all 4 CLIs) requires Phase 7 and Phase 8
complete. This file tests Phase 9 (hedge_comparison) in isolation.

Author: Finance Guru Development Team
Created: 2026-02-18
"""

import pytest

from src.analysis.hedge_comparison import (
    SQQQ_DAILY_FEE,
    SQQQ_EXPENSE_RATIO,
    SQQQ_LEVERAGE,
    HedgeComparisonCalculator,
)
from src.models.hedge_comparison_inputs import (
    ComparisonRow,
    ScenarioInput,
)


class TestSQQQSimulation:
    """Known-answer tests for SQQQ day-by-day simulation.

    WHAT: Verifies SQQQ compounding, fee erosion, and volatility drag
    WHY: SQQQ returns are path-dependent; must validate against analytical answers
    """

    def test_constant_daily_return(self):
        """Constant daily QQQ return of -1% produces deterministic SQQQ value.

        With constant daily return r = -0.01:
          SQQQ daily multiplier = 1 + (-3)*(-0.01) - daily_fee
                                = 1 + 0.03 - daily_fee
          After 10 days: initial * multiplier^10
        """
        calc = HedgeComparisonCalculator(
            spot_price=100.0,
            sqqq_allocation=10000.0,
            holding_days=10,
            daily_volatility=0.0,  # No noise
        )

        # Manually calculate expected value for constant -1% daily
        daily_r = -0.01
        multiplier = 1.0 + SQQQ_LEVERAGE * daily_r - SQQQ_DAILY_FEE
        expected = 10000.0 * (multiplier**10)

        # Use the internal single-path method with constant returns
        daily_returns = [daily_r] * 10
        actual = calc._simulate_sqqq_single_path(daily_returns, 10000.0)

        assert actual == pytest.approx(expected, abs=0.01)

    def test_flat_market_loses_to_fees(self):
        """252 days of 0% daily returns loses approximately the expense ratio.

        SQQQ charges 0.95% annually. Over 252 trading days of flat market,
        the position should lose close to that amount from daily fee erosion.
        """
        calc = HedgeComparisonCalculator(
            spot_price=100.0,
            sqqq_allocation=10000.0,
            holding_days=252,
        )

        # Simulate flat market: 0% daily return for 252 days
        daily_returns = [0.0] * 252
        final = calc._simulate_sqqq_single_path(daily_returns, 10000.0)

        # Loss should be approximately expense ratio
        actual_loss = 10000.0 - final
        expected_loss = 10000.0 * SQQQ_EXPENSE_RATIO

        # Allow $5 tolerance (compounding vs simple interest difference)
        assert actual_loss == pytest.approx(expected_loss, abs=5.0)

    def test_volatile_flat_market_has_drag(self):
        """Alternating +2%/-2% daily returns create volatility drag.

        QQQ is approximately flat after 20 days of alternating +2%/-2%,
        but SQQQ should lose more than just fees due to volatility drag.
        Daily leverage amplifies the zigzag pattern, eroding value.
        """
        calc = HedgeComparisonCalculator(
            spot_price=100.0,
            sqqq_allocation=10000.0,
        )

        # Alternating +2%, -2% for 20 days
        daily_returns = [0.02, -0.02] * 10
        final = calc._simulate_sqqq_single_path(daily_returns, 10000.0)

        # QQQ is nearly flat: (1.02 * 0.98)^10 ~ 0.996
        # But SQQQ should lose at least 2% from drag
        sqqq_return = (final - 10000.0) / 10000.0
        assert sqqq_return < -0.02, "Volatile flat market should cause > 2% drag"
        assert sqqq_return > -0.10, "Drag should not exceed 10% for 20 days"

    def test_sqqq_cannot_go_negative(self):
        """SQQQ position value is floored at zero even with extreme moves.

        A +40% single-day QQQ move would imply -120% SQQQ move, but
        the position value cannot go below zero (fund would liquidate).
        """
        calc = HedgeComparisonCalculator(
            spot_price=100.0,
            sqqq_allocation=10000.0,
        )

        # Single +40% daily QQQ return (extreme, tests zero floor)
        daily_returns = [0.40]
        final = calc._simulate_sqqq_single_path(daily_returns, 10000.0)

        assert final >= 0.0, "SQQQ value cannot go negative"

    def test_sqqq_returns_differ_from_naive_3x(self):
        """For -20% drop, simulated SQQQ return diverges from naive -3x.

        Naive -3x of -20% = +60%. But day-by-day simulation with
        volatility drag produces a different (lower) return.
        """
        calc = HedgeComparisonCalculator(
            spot_price=100.0,
            sqqq_allocation=10000.0,
            holding_days=30,
            daily_volatility=0.015,
        )
        scenario = ScenarioInput(
            market_drop_pct=-0.20,
            holding_days=30,
            daily_volatility=0.015,
        )

        result = calc.simulate_sqqq(scenario)

        naive = result.naive_3x_return_pct  # Should be +0.60
        actual = result.sqqq_return_pct

        assert naive == pytest.approx(0.60, abs=0.001)
        assert abs(naive - actual) > 0.001, (
            "Simulated return should diverge from naive -3x by > 0.1%"
        )

    def test_small_drop_sqqq_profitable(self):
        """For a -5% QQQ drop, SQQQ should have a positive return.

        Basic inverse leverage: QQQ down means SQQQ up (before drag).
        A -5% drop should produce a positive SQQQ return.
        """
        calc = HedgeComparisonCalculator(
            spot_price=100.0,
            sqqq_allocation=10000.0,
            holding_days=30,
            daily_volatility=0.015,
        )
        scenario = ScenarioInput(
            market_drop_pct=-0.05,
            holding_days=30,
            daily_volatility=0.015,
        )

        result = calc.simulate_sqqq(scenario)
        assert result.sqqq_return_pct > 0, "SQQQ should profit from -5% QQQ drop"


class TestPutPayoff:
    """Known-answer tests for protective put payoff calculation.

    WHAT: Verifies put pricing with IV expansion during market drops
    WHY: Put value depends on both intrinsic value and IV expansion
    """

    def test_deep_itm_put_profitable(self):
        """ATM put with -20% drop should be deep ITM and profitable.

        spot=100, strike=100 (ATM), premium=3, drop=-20%.
        New spot = 80, intrinsic = 100 - 80 = 20.
        Put value > $20 due to IV expansion. PnL > 0.
        """
        calc = HedgeComparisonCalculator(
            spot_price=100.0,
            put_strike=100.0,
            put_premium=3.0,
            baseline_iv=0.20,
        )
        scenario = ScenarioInput(
            market_drop_pct=-0.20,
            holding_days=30,
            daily_volatility=0.015,
        )

        result = calc.calculate_put_payoff(scenario)

        assert result.intrinsic == pytest.approx(20.0, abs=0.01)
        assert result.put_value_after > 20.0, "IV expansion adds time value"
        assert result.pnl > 0, "Deep ITM put should be profitable"

    def test_otm_put_no_drop_loses_premium(self):
        """OTM put with no market drop loses the premium paid.

        spot=100, strike=90 (10% OTM), premium=2, drop~0%.
        No intrinsic value. Put is worth near-zero time value only.
        PnL should be negative (lost premium).
        """
        calc = HedgeComparisonCalculator(
            spot_price=100.0,
            put_strike=90.0,
            put_premium=2.0,
            baseline_iv=0.20,
        )
        # Use a very small drop to avoid ScenarioInput lt=0 constraint
        scenario = ScenarioInput(
            market_drop_pct=-0.001,
            holding_days=30,
            daily_volatility=0.015,
        )

        result = calc.calculate_put_payoff(scenario)

        assert result.intrinsic == pytest.approx(0.0, abs=0.01)
        assert result.pnl < 0, "OTM put with no drop should lose premium"

    def test_iv_expansion_increases_with_drop_severity(self):
        """Larger market drops produce higher IV (from VIX-SPX regression).

        IV after -20% drop should be higher than IV after -5% drop.
        This verifies the VIX-SPX interpolation table is working.
        """
        calc = HedgeComparisonCalculator(
            spot_price=100.0,
            put_strike=90.0,
            put_premium=3.0,
            baseline_iv=0.20,
        )

        scenario_mild = ScenarioInput(
            market_drop_pct=-0.05,
            holding_days=30,
            daily_volatility=0.015,
        )
        scenario_severe = ScenarioInput(
            market_drop_pct=-0.20,
            holding_days=30,
            daily_volatility=0.015,
        )

        result_mild = calc.calculate_put_payoff(scenario_mild)
        result_severe = calc.calculate_put_payoff(scenario_severe)

        assert result_severe.iv_after > result_mild.iv_after, (
            "IV should be higher for -20% drop than -5% drop"
        )
        assert result_mild.iv_after > result_mild.iv_before, (
            "Even -5% drop should expand IV above baseline"
        )


class TestBreakeven:
    """Known-answer tests for breakeven analysis.

    WHAT: Verifies breakeven market drop thresholds for both strategies
    WHY: Breakevens show at which point each hedge "kicks in"
    """

    def test_put_breakeven_atm(self):
        """ATM put breakeven: spot=100, strike=100, premium=5.

        Analytical breakeven: spot must drop to strike - premium = 95.
        Breakeven drop = (95 - 100) / 100 = -5% (ignoring time value).
        """
        calc = HedgeComparisonCalculator(
            spot_price=100.0,
            put_strike=100.0,
            put_premium=5.0,
        )

        _sqqq_be, put_be = calc.find_breakevens()

        # Analytical: (100 - 5 - 100) / 100 = -0.05
        assert put_be == pytest.approx(-0.05, abs=0.001)

    def test_sqqq_breakeven_is_small_drop(self):
        """SQQQ breakeven should be a very small negative drop.

        SQQQ only needs to overcome daily fees to be profitable.
        Breakeven should be between -0.1% and -5%.
        """
        calc = HedgeComparisonCalculator(
            spot_price=100.0,
            sqqq_allocation=10000.0,
            holding_days=30,
        )

        sqqq_be, _put_be = calc.find_breakevens()

        assert sqqq_be < 0, "SQQQ breakeven should be negative (need a drop)"
        assert sqqq_be > -0.05, "SQQQ breakeven should be > -5%"
        assert sqqq_be <= -0.001, "SQQQ breakeven should be <= -0.1%"


class TestComparisonOutput:
    """Tests for full comparison output structure and logic.

    WHAT: Verifies compare_all() output structure, disclaimers, and winner logic
    WHY: Ensures the full pipeline produces correct structured output
    """

    def test_compare_all_returns_correct_scenario_count(self):
        """compare_all with 4 scenarios returns exactly 4 ComparisonRow objects."""
        calc = HedgeComparisonCalculator(spot_price=480.0)
        result = calc.compare_all([-0.05, -0.10, -0.20, -0.40])

        assert len(result.scenarios) == 4
        assert all(isinstance(row, ComparisonRow) for row in result.scenarios)

    def test_disclaimers_present(self):
        """Output must contain at least 3 disclaimers, one with 'path-dependent'.

        HC-05 requirement: path-dependent disclaimer must be present.
        """
        calc = HedgeComparisonCalculator(spot_price=480.0)
        result = calc.compare_all([-0.10])

        assert len(result.disclaimers) >= 3
        path_dep = [d for d in result.disclaimers if "path-dependent" in d.lower()]
        assert len(path_dep) >= 1, "Must include path-dependent disclaimer (HC-05)"

    def test_parameters_snapshot_present(self):
        """Output.parameters dict must contain spot_price key."""
        calc = HedgeComparisonCalculator(spot_price=480.0)
        result = calc.compare_all([-0.10])

        assert result.parameters is not None
        assert len(result.parameters) > 0
        assert "spot_price" in result.parameters
        assert result.parameters["spot_price"] == pytest.approx(480.0)

    def test_winner_logic(self):
        """Winner field must be one of sqqq, put, or neither.

        Verify that the winner field is logically consistent:
        - If both PnL values are negative, winner should be 'neither'
        - Otherwise winner should match the higher PnL strategy
        """
        calc = HedgeComparisonCalculator(
            spot_price=480.0,
            sqqq_allocation=10000.0,
        )
        result = calc.compare_all([-0.05, -0.10, -0.20, -0.40])

        for row in result.scenarios:
            assert row.winner in {"sqqq", "put", "neither"}

            sqqq_pnl = row.sqqq.final_value - row.sqqq.initial_value
            put_pnl = row.put.pnl

            if row.winner == "sqqq":
                assert sqqq_pnl > put_pnl, (
                    f"SQQQ declared winner but PnL ({sqqq_pnl}) <= put PnL ({put_pnl})"
                )
            elif row.winner == "put":
                assert put_pnl > sqqq_pnl, (
                    f"Put declared winner but PnL ({put_pnl}) <= SQQQ PnL ({sqqq_pnl})"
                )
            elif row.winner == "neither":
                assert sqqq_pnl <= 0 and put_pnl <= 0, (
                    "Neither should only be set when both PnLs are non-positive"
                )
