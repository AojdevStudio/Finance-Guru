"""Hedge Comparison Engine for Finance Guru.

This module implements the SQQQ vs protective puts comparison calculator.
It simulates day-by-day SQQQ compounding with volatility drag, calculates
put payoffs with IV expansion, and finds breakeven points for each strategy.

ARCHITECTURE NOTE:
This is Layer 2 of our 3-layer architecture:
    Layer 1: Pydantic Models - Data validation (hedge_comparison_inputs.py)
    Layer 2: Calculator Classes (THIS FILE) - Business logic
    Layer 3: CLI Interface - Agent integration

CRITICAL DESIGN DECISIONS:
- SQQQ simulation uses day-by-day compounding, NOT simple -3x multiplication.
  Leveraged ETFs reset daily, so the cumulative return depends on the path taken.
- Three representative paths (gradual, crash-then-flat, volatile) capture
  the range of outcomes for any given total market decline.
- IV expansion interpolates ``VIX_CALIBRATION_POINTS``, conservative VIX levels
  from historical crashes (2008 GFC, 2018 Volmageddon, 2020 COVID, 2025 Tariffs).

Author: Finance Guru Development Team
Created: 2026-02-18
"""

from collections.abc import Callable
from datetime import date
from math import isfinite
from typing import Literal, NamedTuple

import numpy as np
from scipy.optimize import brentq

from src.analysis.options import OptionsCalculator
from src.models.hedge_comparison_inputs import (
    ComparisonOutput,
    ComparisonRow,
    PutResult,
    ScenarioInput,
    SQQQResult,
)
from src.models.options_inputs import BlackScholesInput
from src.utils.trading_calendar import TRADING_DAYS_PER_YEAR

SQQQ_EXPENSE_RATIO = 0.0095
"""ProShares SQQQ net expense ratio, which includes a fee waiver."""

SQQQ_EXPENSE_RATIO_AS_OF = date(2026, 2, 2)
"""Date ``SQQQ_EXPENSE_RATIO`` was sourced."""

SQQQ_FEE_WAIVER_THROUGH = date(2026, 9, 30)
"""Last day of the fee waiver that ``SQQQ_EXPENSE_RATIO`` assumes."""

SQQQ_DAILY_FEE = SQQQ_EXPENSE_RATIO / TRADING_DAYS_PER_YEAR
SQQQ_LEVERAGE = -3

SQQQ_VALUE_FLOOR = 0.0
"""A long SQQQ position cannot lose more than the cash put into it."""

BREAKEVEN_SEARCH_SHALLOWEST_DROP = -0.001
BREAKEVEN_SEARCH_DEEPEST_DROP = -0.50


class VixCalibrationPoint(NamedTuple):
    """One market drop paired with the VIX level seen at that drop."""

    market_drop: float
    vix: float
    regime: str


VIX_CALIBRATION_POINTS: tuple[VixCalibrationPoint, ...] = (
    VixCalibrationPoint(0.00, 18.0, "normal baseline, long-term VIX median 17 to 19"),
    VixCalibrationPoint(-0.05, 28.0, "mild correction"),
    VixCalibrationPoint(-0.10, 38.0, "moderate correction"),
    VixCalibrationPoint(-0.20, 55.0, "bear market territory"),
    VixCalibrationPoint(-0.40, 80.0, "crisis, 2008 and 2020 levels"),
)

VIX_SPX_TABLE: dict[float, float] = {
    point.market_drop: point.vix for point in VIX_CALIBRATION_POINTS
}

DEFAULT_DISCLAIMERS: list[str] = [
    "EDUCATIONAL ONLY. Not investment advice. Consult a licensed financial professional.",
    "SQQQ decay is path-dependent. Results are approximate and vary with the price path taken.",
    (
        "IV expansion estimates use a simplified VIX-SPX regression model. "
        "Actual IV behavior depends on regime, speed of decline, and market microstructure."
    ),
    "Past VIX-SPX relationships may not hold in future crises.",
    "SQQQ simulation assumes perfect daily rebalancing. Actual SQQQ may deviate during extreme volatility.",
]

_SCENARIO_LABELS: dict[float, str] = {
    -0.05: "-5% correction",
    -0.10: "-10% correction",
    -0.15: "-15% pullback",
    -0.20: "-20% bear market",
    -0.25: "-25% bear market",
    -0.30: "-30% crash",
    -0.35: "-35% crash",
    -0.40: "-40% crash",
    -0.50: "-50% crash",
}


class HedgeComparisonCalculator:
    """SQQQ vs protective puts comparison calculator.

    WHAT: Compares SQQQ leveraged ETF hedging vs protective put hedging
    WHY: Each strategy has different risk/reward profiles depending on
         market path, speed of decline, and holding period
    HOW: Day-by-day SQQQ simulation + Black-Scholes put pricing with IV expansion

    USAGE EXAMPLE:
        calc = HedgeComparisonCalculator(spot_price=480.0)
        result = calc.compare_all([-0.05, -0.10, -0.20, -0.40])
        for row in result.scenarios:
            print(f"{row.scenario_label}: Winner={row.winner}")
    """

    def __init__(
        self,
        spot_price: float = 480.0,
        put_strike: float | None = None,
        put_premium: float = 5.0,
        sqqq_allocation: float = 10000.0,
        baseline_iv: float = 0.20,
        baseline_vix: float = 18.0,
        time_to_expiry: float = 0.20,
        risk_free_rate: float = 0.045,
        holding_days: int = 30,
        daily_volatility: float = 0.015,
    ) -> None:
        """Initialize with comparison parameters.

        Args:
            spot_price: Current QQQ price (default 480.0)
            put_strike: Put strike price (default: 10% OTM = spot * 0.90)
            put_premium: Per-share put premium paid (default 5.0)
            sqqq_allocation: Dollar amount allocated to SQQQ (default 10000.0)
            baseline_iv: Baseline implied volatility (default 0.20 = 20%)
            baseline_vix: Baseline VIX level (default 18.0)
            time_to_expiry: Time to put expiry in years (default 0.20 = ~73 days)
            risk_free_rate: Annual risk-free rate (default 0.045 = 4.5%)
            holding_days: Holding period in trading days (default 30)
            daily_volatility: Expected daily QQQ volatility (default 0.015)
        """
        self.spot_price = spot_price
        self.put_strike = put_strike if put_strike is not None else spot_price * 0.90
        self.put_premium = put_premium
        self.sqqq_allocation = sqqq_allocation
        self.baseline_iv = baseline_iv
        self.baseline_vix = baseline_vix
        self.time_to_expiry = time_to_expiry
        self.risk_free_rate = risk_free_rate
        self.holding_days = holding_days
        self.daily_volatility = daily_volatility
        self.options_calc = OptionsCalculator()

    def simulate_sqqq(self, scenario: ScenarioInput) -> SQQQResult:
        """Simulate SQQQ position value across 3 representative paths.

        WHAT: Day-by-day SQQQ compounding with volatility drag
        WHY: Leveraged ETFs reset daily -- cumulative return is path-dependent
        HOW: Generate 3 paths (gradual, crash-then-flat, volatile), average results

        Args:
            scenario: Market drop scenario parameters

        Returns:
            SQQQResult with actual return, naive return, and drag quantification
        """
        paths = self._generate_scenario_paths(
            scenario.market_drop_pct, scenario.holding_days, scenario.daily_volatility
        )

        initial_value = self.sqqq_allocation
        final_values = [
            self._simulate_sqqq_single_path(path, initial_value) for path in paths
        ]
        avg_final = sum(final_values) / len(final_values)

        actual_return = (avg_final - initial_value) / initial_value
        naive_return = SQQQ_LEVERAGE * scenario.market_drop_pct
        drag = naive_return - actual_return

        return SQQQResult(
            market_drop_pct=scenario.market_drop_pct,
            sqqq_return_pct=actual_return,
            naive_3x_return_pct=naive_return,
            volatility_drag_pct=drag,
            final_value=avg_final,
            initial_value=initial_value,
        )

    def calculate_put_payoff(self, scenario: ScenarioInput) -> PutResult:
        """Calculate protective put payoff with IV expansion.

        WHAT: Put value at new spot price with crash-expanded implied volatility
        WHY: IV spikes during crashes, increasing put value beyond intrinsic
        HOW: VIX-SPX regression for new IV, then Black-Scholes repricing

        Args:
            scenario: Market drop scenario parameters

        Returns:
            PutResult with put value, PnL, IV before/after, and breakdown
        """
        new_spot = self.spot_price * (1.0 + scenario.market_drop_pct)
        new_iv = self._estimate_iv_at_drop(scenario.market_drop_pct)

        bs_input = BlackScholesInput(
            spot_price=new_spot,
            strike=self.put_strike,
            time_to_expiry=self.time_to_expiry,
            volatility=new_iv,
            risk_free_rate=self.risk_free_rate,
            option_type="put",
        )
        greeks = self.options_calc.price_option(bs_input)
        put_value = greeks.option_price

        intrinsic = max(self.put_strike - new_spot, 0.0)
        time_val = put_value - intrinsic
        pnl = put_value - self.put_premium
        pnl_pct = pnl / self.put_premium if self.put_premium > 0 else 0.0

        return PutResult(
            market_drop_pct=scenario.market_drop_pct,
            put_value_after=put_value,
            premium_paid=self.put_premium,
            pnl=pnl,
            pnl_pct=pnl_pct,
            iv_before=self.baseline_iv,
            iv_after=new_iv,
            intrinsic=intrinsic,
            time_value=time_val,
        )

    def find_breakevens(self) -> tuple[float, float]:
        """Find breakeven market drops for both strategies.

        WHAT: Exact market drop at which each hedge becomes profitable
        WHY: Helps compare at which point each strategy "kicks in"
        HOW: brentq root-finding for SQQQ; analytical for put

        Returns:
            Tuple of (sqqq_breakeven_drop, put_breakeven_drop)
        """

        def sqqq_pnl_at_drop(drop: float) -> float:
            """SQQQ PnL as function of market drop (for root finding)."""
            days = self.holding_days
            daily_r = (1.0 + drop) ** (1.0 / days) - 1.0
            daily_returns = [daily_r] * days
            final = self._simulate_sqqq_single_path(daily_returns, self.sqqq_allocation)
            return final - self.sqqq_allocation

        try:
            sqqq_be = brentq(
                sqqq_pnl_at_drop,
                BREAKEVEN_SEARCH_DEEPEST_DROP,
                BREAKEVEN_SEARCH_SHALLOWEST_DROP,
                xtol=1e-6,
            )
        except ValueError:
            sqqq_be = _breakeven_without_sign_change(sqqq_pnl_at_drop)

        breakeven_spot = self.put_strike - self.put_premium
        put_be = (breakeven_spot - self.spot_price) / self.spot_price

        return (sqqq_be, put_be)

    def compare_all(self, scenarios: list[float]) -> ComparisonOutput:
        """Run full comparison across multiple market drop scenarios.

        WHAT: Main entry point for SQQQ vs puts comparison
        WHY: Produces complete side-by-side analysis for all scenario levels
        HOW: Simulate SQQQ + price puts, compare returns per dollar invested, find breakevens

        Args:
            scenarios: List of market drops as negative decimals, e.g. [-0.05, -0.10, -0.20, -0.40]

        Returns:
            ComparisonOutput with all scenario rows, breakevens, disclaimers, and parameters
        """
        if not isfinite(self.put_premium) or self.put_premium <= 0:
            raise ValueError(
                "Put premium must be positive and finite to compare investment returns"
            )
        if not isfinite(self.sqqq_allocation) or self.sqqq_allocation <= 0:
            raise ValueError(
                "SQQQ allocation must be positive and finite to compare investment returns"
            )

        rows: list[ComparisonRow] = []

        for drop in scenarios:
            scenario = ScenarioInput(
                market_drop_pct=drop,
                holding_days=self.holding_days,
                daily_volatility=self.daily_volatility,
            )

            sqqq_result = self.simulate_sqqq(scenario)
            put_result = self.calculate_put_payoff(scenario)

            sqqq_return = sqqq_result.sqqq_return_pct
            put_return = put_result.pnl_pct

            winner: Literal["sqqq", "put", "neither"]
            if sqqq_return <= 0 and put_return <= 0:
                winner = "neither"
            elif sqqq_return > put_return:
                winner = "sqqq"
            elif put_return > sqqq_return:
                winner = "put"
            else:
                winner = "neither"

            label = _SCENARIO_LABELS.get(drop, f"-{int(abs(drop * 100))}% decline")

            rows.append(
                ComparisonRow(
                    scenario_label=label,
                    market_drop_pct=drop,
                    sqqq=sqqq_result,
                    put=put_result,
                    winner=winner,
                )
            )

        sqqq_be, put_be = self.find_breakevens()

        parameters = {
            "spot_price": self.spot_price,
            "put_strike": self.put_strike,
            "put_premium": self.put_premium,
            "sqqq_allocation": self.sqqq_allocation,
            "baseline_iv": self.baseline_iv,
            "baseline_vix": self.baseline_vix,
            "time_to_expiry": self.time_to_expiry,
            "risk_free_rate": self.risk_free_rate,
            "holding_days": self.holding_days,
            "daily_volatility": self.daily_volatility,
        }

        return ComparisonOutput(
            scenarios=rows,
            sqqq_breakeven_drop=sqqq_be,
            put_breakeven_drop=put_be,
            disclaimers=DEFAULT_DISCLAIMERS,
            parameters=parameters,
        )

    def _simulate_sqqq_single_path(
        self, daily_qqq_returns: list[float], initial_value: float
    ) -> float:
        """Simulate SQQQ value along a single path of daily QQQ returns.

        WHAT: Day-by-day SQQQ compounding with leverage and fees
        WHY: Leveraged ETFs compound daily, causing volatility drag
        HOW: value *= (1 + LEVERAGE * daily_return - daily_fee), floor at 0

        CRITICAL: This is NOT simple -3x multiplication. Each day's return
        compounds independently, and the expense ratio erodes value daily.

        Args:
            daily_qqq_returns: List of daily QQQ returns (e.g., -0.01 for -1% day)
            initial_value: Starting SQQQ position value

        Returns:
            Final SQQQ position value (floored at 0.0)
        """
        value = initial_value
        for r in daily_qqq_returns:
            value *= 1.0 + SQQQ_LEVERAGE * r - SQQQ_DAILY_FEE
            value = max(value, SQQQ_VALUE_FLOOR)
        return value

    def _generate_scenario_paths(
        self, target_drop_pct: float, days: int, daily_volatility: float
    ) -> list[list[float]]:
        """Generate 3 representative daily return paths for a target market drop.

        WHAT: Three deterministic-ish paths that all end at the same total drop
        WHY: SQQQ returns are path-dependent -- same total drop can yield very
             different SQQQ outcomes depending on how the market gets there
        HOW:
            Path 1 (gradual): Uniform daily drops
            Path 2 (crash-then-flat): Sharp front-loaded drop, then flat
            Path 3 (volatile): Random walk conditioned on target final value

        Args:
            target_drop_pct: Target cumulative drop (negative, e.g., -0.20)
            days: Number of trading days
            daily_volatility: Daily QQQ volatility for path 3 noise

        Returns:
            List of 3 paths, each a list of daily returns
        """
        daily_r = (1.0 + target_drop_pct) ** (1.0 / days) - 1.0
        path_gradual = [daily_r] * days

        crash_days = min(5, days)
        if crash_days > 0:
            crash_daily_r = (1.0 + target_drop_pct) ** (1.0 / crash_days) - 1.0
            path_crash = [crash_daily_r] * crash_days + [0.0] * (days - crash_days)
        else:
            path_crash = path_gradual[:]

        rng = np.random.default_rng(seed=42)
        noise = rng.normal(0, daily_volatility, days)

        base_returns = np.full(days, daily_r)
        volatile_returns = base_returns + noise

        current_cum = float(np.prod(1.0 + volatile_returns))
        target_cum = 1.0 + target_drop_pct

        rescalable_to_target = current_cum > 0 and target_cum > 0
        if rescalable_to_target:
            adjustment = (target_cum / current_cum) ** (1.0 / days)
            path_volatile = [(1.0 + r) * adjustment - 1.0 for r in volatile_returns]
        else:
            path_volatile = path_gradual[:]

        return [path_gradual, path_crash, path_volatile]

    def _estimate_iv_at_drop(self, market_drop_pct: float) -> float:
        """Estimate implied volatility at a given market drop level.

        WHAT: New IV after market drops by a given percentage
        WHY: IV expands during crashes -- puts become more valuable
        HOW: Interpolate VIX from table, then scale baseline IV proportionally

        Args:
            market_drop_pct: Market drop as negative decimal

        Returns:
            Estimated IV at the given drop level
        """
        vix_at_drop = self._interpolate_vix(market_drop_pct)
        new_iv = self.baseline_iv * (vix_at_drop / self.baseline_vix)
        return new_iv

    def _interpolate_vix(self, drop: float) -> float:
        """Piecewise linear interpolation on VIX-SPX table.

        WHAT: Estimate VIX level for a given market drop
        WHY: VIX and market drops have a well-documented inverse relationship
        HOW: Sort table keys, find bounding pair, linearly interpolate

        Args:
            drop: Market drop as negative decimal (e.g., -0.15)

        Returns:
            Estimated VIX level
        """
        if drop >= 0:
            return self.baseline_vix

        keys = sorted(VIX_SPX_TABLE.keys(), reverse=True)

        if drop > keys[0]:
            return VIX_SPX_TABLE[keys[0]]

        for i in range(len(keys) - 1):
            upper = keys[i]
            lower = keys[i + 1]
            if lower <= drop <= upper:
                frac = (drop - upper) / (lower - upper)
                vix_upper = VIX_SPX_TABLE[upper]
                vix_lower = VIX_SPX_TABLE[lower]
                return vix_upper + frac * (vix_lower - vix_upper)

        k1, k2 = keys[-2], keys[-1]
        v1, v2 = VIX_SPX_TABLE[k1], VIX_SPX_TABLE[k2]
        slope = (v2 - v1) / (k2 - k1)
        extrapolated = v2 + slope * (drop - k2)
        return max(extrapolated, v2)


def _breakeven_without_sign_change(pnl_at_drop: Callable[[float], float]) -> float:
    """Return the search boundary when SQQQ P&L keeps one sign over the range.

    ``brentq`` needs a sign change. Without one, SQQQ either pays from the
    shallowest drop searched or never pays inside the range, so the result is
    the boundary on that side.
    """
    if pnl_at_drop(BREAKEVEN_SEARCH_SHALLOWEST_DROP) >= 0:
        return BREAKEVEN_SEARCH_SHALLOWEST_DROP
    return BREAKEVEN_SEARCH_DEEPEST_DROP


__all__ = [
    "HedgeComparisonCalculator",
    "DEFAULT_DISCLAIMERS",
    "SQQQ_EXPENSE_RATIO",
    "SQQQ_EXPENSE_RATIO_AS_OF",
    "SQQQ_FEE_WAIVER_THROUGH",
    "SQQQ_DAILY_FEE",
    "SQQQ_LEVERAGE",
    "VIX_CALIBRATION_POINTS",
    "VIX_SPX_TABLE",
]
