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
- IV expansion uses a VIX-SPX regression table calibrated from historical crashes
  (2008 GFC, 2018 Volmageddon, 2020 COVID, 2025 Tariffs).

Author: Finance Guru Development Team
Created: 2026-02-18
"""

from typing import Literal

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

# --- Module-level constants ---

SQQQ_EXPENSE_RATIO = (
    0.0095  # 0.95% annual (ProShares net, with fee waiver through Sep 2026)
)
SQQQ_DAILY_FEE = SQQQ_EXPENSE_RATIO / 252  # ~0.00377% per trading day
SQQQ_LEVERAGE = -3  # -3x daily target

# VIX-SPX regression table: conservative estimates from historical crash data
# Sources: 2008 GFC (VIX 80-89), 2018 Volmageddon (VIX 37), 2020 COVID (VIX 82), 2025 Tariffs (VIX ~45)
# See: 09-RESEARCH.md for full calibration data
VIX_SPX_TABLE: dict[float, float] = {
    0.00: 18.0,  # Normal baseline (long-term VIX median ~17-19)
    -0.05: 28.0,  # Mild correction
    -0.10: 38.0,  # Moderate correction
    -0.20: 55.0,  # Bear market territory
    -0.40: 80.0,  # Crisis (2008/2020 levels)
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

# Scenario labels for common market drops
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
        avg_final = max(avg_final, 0.0)

        actual_return = (avg_final - initial_value) / initial_value
        naive_return = -3.0 * scenario.market_drop_pct
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

        # Price the put at new spot with expanded IV
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

        # SQQQ breakeven: find drop where position value == initial allocation
        # Use gradual decline path (conservative) for breakeven calculation
        def sqqq_pnl_at_drop(drop: float) -> float:
            """SQQQ PnL as function of market drop (for root finding)."""
            days = self.holding_days
            # Gradual path for breakeven (deterministic, no path noise)
            daily_r = (1.0 + drop) ** (1.0 / days) - 1.0
            daily_returns = [daily_r] * days
            final = self._simulate_sqqq_single_path(daily_returns, self.sqqq_allocation)
            return final - self.sqqq_allocation

        try:
            sqqq_be = brentq(sqqq_pnl_at_drop, -0.50, -0.001, xtol=1e-6)
        except ValueError:
            # If no root in range, SQQQ is always profitable in this range
            # or never profitable -- return boundary
            sqqq_be = -0.001 if sqqq_pnl_at_drop(-0.001) >= 0 else -0.50

        # Put breakeven (analytical): spot must drop enough for put to be worth more than premium
        # breakeven_spot = strike - premium, then drop = (breakeven_spot - spot) / spot
        breakeven_spot = self.put_strike - self.put_premium
        put_be = (breakeven_spot - self.spot_price) / self.spot_price

        return (sqqq_be, put_be)

    def compare_all(self, scenarios: list[float]) -> ComparisonOutput:
        """Run full comparison across multiple market drop scenarios.

        WHAT: Main entry point for SQQQ vs puts comparison
        WHY: Produces complete side-by-side analysis for all scenario levels
        HOW: Simulate SQQQ + price puts for each drop, determine winner, find breakevens

        Args:
            scenarios: List of market drops as negative decimals, e.g. [-0.05, -0.10, -0.20, -0.40]

        Returns:
            ComparisonOutput with all scenario rows, breakevens, disclaimers, and parameters
        """
        rows: list[ComparisonRow] = []

        for drop in scenarios:
            scenario = ScenarioInput(
                market_drop_pct=drop,
                holding_days=self.holding_days,
                daily_volatility=self.daily_volatility,
            )

            sqqq_result = self.simulate_sqqq(scenario)
            put_result = self.calculate_put_payoff(scenario)

            # Determine winner by comparing return percentages
            # SQQQ return % is sqqq_return_pct
            # Put return % is pnl_pct (pnl / premium)
            # For fair comparison, normalize: SQQQ uses % return on allocation,
            # Put uses % return on premium invested
            sqqq_pnl = sqqq_result.final_value - sqqq_result.initial_value
            put_pnl = put_result.pnl

            winner: Literal["sqqq", "put", "neither"]
            if sqqq_pnl <= 0 and put_pnl <= 0:
                winner = "neither"
            elif sqqq_pnl > put_pnl:
                winner = "sqqq"
            elif put_pnl > sqqq_pnl:
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

    # --- Private helpers ---

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
            value = max(value, 0.0)
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
        # Path 1: Gradual decline -- uniform daily drops
        daily_r = (1.0 + target_drop_pct) ** (1.0 / days) - 1.0
        path_gradual = [daily_r] * days

        # Path 2: Crash-then-flat -- sharp drop in first few days, then 0
        crash_days = min(5, days)
        if crash_days > 0:
            crash_daily_r = (1.0 + target_drop_pct) ** (1.0 / crash_days) - 1.0
            path_crash = [crash_daily_r] * crash_days + [0.0] * (days - crash_days)
        else:
            path_crash = path_gradual[:]

        # Path 3: Volatile -- random walk conditioned on matching target
        # Generate random noise, then adjust final day to hit target
        rng = np.random.default_rng(seed=42)
        noise = rng.normal(0, daily_volatility, days)

        # Start with gradual base, add noise
        base_returns = np.full(days, daily_r)
        volatile_returns = base_returns + noise

        # Adjust so cumulative product matches target
        # Current cumulative product
        current_cum = float(np.prod(1.0 + volatile_returns))
        target_cum = 1.0 + target_drop_pct

        if current_cum > 0 and target_cum > 0:
            # Multiplicative adjustment spread across all days
            adjustment = (target_cum / current_cum) ** (1.0 / days)
            adjusted = [(1.0 + r) * adjustment - 1.0 for r in volatile_returns]
            path_volatile = adjusted
        else:
            # Fallback to gradual if adjustment would produce invalid values
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
        # Guard: drops above 0 return baseline
        if drop >= 0:
            return self.baseline_vix

        keys = sorted(VIX_SPX_TABLE.keys(), reverse=True)  # [0.00, -0.05, -0.10, ...]

        # If drop is less extreme than smallest key, interpolate toward baseline
        if drop > keys[0]:
            return VIX_SPX_TABLE[keys[0]]

        # Find bounding keys
        for i in range(len(keys) - 1):
            upper = keys[i]
            lower = keys[i + 1]
            if lower <= drop <= upper:
                # Linear interpolation
                frac = (drop - upper) / (lower - upper)
                vix_upper = VIX_SPX_TABLE[upper]
                vix_lower = VIX_SPX_TABLE[lower]
                return vix_upper + frac * (vix_lower - vix_upper)

        # Extrapolate beyond table (more extreme than -0.40)
        # Use last two keys for slope
        k1, k2 = keys[-2], keys[-1]
        v1, v2 = VIX_SPX_TABLE[k1], VIX_SPX_TABLE[k2]
        slope = (v2 - v1) / (k2 - k1)
        extrapolated = v2 + slope * (drop - k2)
        return max(extrapolated, v2)  # Don't go below crisis VIX


# Type exports
__all__ = [
    "HedgeComparisonCalculator",
    "DEFAULT_DISCLAIMERS",
    "SQQQ_EXPENSE_RATIO",
    "SQQQ_DAILY_FEE",
    "SQQQ_LEVERAGE",
    "VIX_SPX_TABLE",
]
