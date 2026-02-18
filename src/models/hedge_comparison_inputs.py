"""Hedge Comparison Pydantic Models for Finance Guru.

This module defines type-safe data structures for SQQQ vs protective puts
comparison. Models capture scenario inputs, simulation results, and
full comparison output.

ARCHITECTURE NOTE:
These models represent Layer 1 of our 3-layer architecture:
    Layer 1: Pydantic Models (THIS FILE) - Data validation
    Layer 2: Calculator Classes - Business logic
    Layer 3: CLI Interface - Agent integration

EDUCATIONAL CONTEXT:
- SQQQ is a -3x leveraged ETF that targets 3x the inverse of QQQ daily returns
- Protective puts provide downside insurance with capped cost (premium paid)
- Comparing the two requires accounting for SQQQ volatility drag and IV expansion

Author: Finance Guru Development Team
Created: 2026-02-18
"""

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ScenarioInput(BaseModel):
    """Input for a single market drop scenario.

    WHAT: Parameters defining a hypothetical market decline
    WHY: Drives both SQQQ simulation and put payoff calculation
    VALIDATES:
        - Market drop is negative (must be a decline)
        - Holding period is within 1-252 trading days
        - Daily volatility is positive and reasonable
    """

    market_drop_pct: float = Field(
        ...,
        lt=0,
        ge=-0.99,
        description="Market drop as negative decimal, e.g. -0.20 for -20%",
    )

    holding_days: int = Field(
        default=30,
        ge=1,
        le=252,
        description="Holding period in trading days",
    )

    daily_volatility: float = Field(
        default=0.015,
        gt=0,
        le=0.10,
        description="Expected daily QQQ volatility",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "market_drop_pct": -0.20,
                    "holding_days": 30,
                    "daily_volatility": 0.015,
                }
            ]
        }
    }


class SQQQResult(BaseModel):
    """SQQQ simulation result for a scenario.

    WHAT: Day-by-day SQQQ compounding result with volatility drag
    WHY: Shows actual SQQQ return vs naive -3x, quantifying drag cost
    VALIDATES:
        - Final value is non-negative (SQQQ cannot go below zero)
        - Initial value is positive
    """

    market_drop_pct: float = Field(..., description="Market drop that was simulated")

    sqqq_return_pct: float = Field(
        ..., description="Actual SQQQ return after volatility drag"
    )

    naive_3x_return_pct: float = Field(
        ..., description="What simple -3x multiplication would give"
    )

    volatility_drag_pct: float = Field(
        ..., description="Difference (naive - actual) showing drag impact"
    )

    final_value: float = Field(
        ..., ge=0.0, description="Final SQQQ position value (zero floor)"
    )

    initial_value: float = Field(..., gt=0.0, description="Initial SQQQ allocation")

    @field_validator("final_value")
    @classmethod
    def final_value_zero_floor(cls, v: float) -> float:
        """Enforce zero floor on SQQQ position value.

        WHY: A leveraged ETF position cannot have negative value.
        The fund would be liquidated before reaching zero in practice.
        """
        if v < 0:
            return 0.0
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "market_drop_pct": -0.20,
                    "sqqq_return_pct": 0.52,
                    "naive_3x_return_pct": 0.60,
                    "volatility_drag_pct": 0.08,
                    "final_value": 15200.0,
                    "initial_value": 10000.0,
                }
            ]
        }
    }


class PutResult(BaseModel):
    """Protective put result for a scenario.

    WHAT: Put option payoff accounting for IV expansion during crash
    WHY: Shows put value with realistic IV behavior, not just intrinsic
    VALIDATES:
        - Premium paid is non-negative
    """

    market_drop_pct: float = Field(..., description="Market drop that was simulated")

    put_value_after: float = Field(
        ..., description="Put value at new spot with expanded IV"
    )

    premium_paid: float = Field(
        ..., ge=0.0, description="Premium paid to enter the put position"
    )

    pnl: float = Field(..., description="Profit/loss: put_value_after - premium_paid")

    pnl_pct: float = Field(..., description="PnL as percentage of premium paid")

    iv_before: float = Field(..., description="Baseline implied volatility")

    iv_after: float = Field(..., description="Implied volatility after IV expansion")

    intrinsic: float = Field(
        ..., ge=0.0, description="Intrinsic value: max(strike - new_spot, 0)"
    )

    time_value: float = Field(
        ..., description="Time value: put_value_after - intrinsic"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "market_drop_pct": -0.20,
                    "put_value_after": 58.50,
                    "premium_paid": 5.0,
                    "pnl": 53.50,
                    "pnl_pct": 10.70,
                    "iv_before": 0.20,
                    "iv_after": 0.61,
                    "intrinsic": 48.0,
                    "time_value": 10.50,
                }
            ]
        }
    }


class ComparisonRow(BaseModel):
    """One row of the comparison table.

    WHAT: Side-by-side SQQQ vs put result for a single scenario
    WHY: Enables apples-to-apples comparison at each market drop level
    """

    scenario_label: str = Field(
        ..., description="Human-readable label, e.g. '-5% correction'"
    )

    market_drop_pct: float = Field(..., description="Market drop for this scenario")

    sqqq: SQQQResult = Field(..., description="SQQQ simulation result")

    put: PutResult = Field(..., description="Protective put result")

    winner: Literal["sqqq", "put", "neither"] = Field(
        ..., description="Which strategy performed better in this scenario"
    )


class ComparisonOutput(BaseModel):
    """Full comparison output from HedgeComparisonCalculator.

    WHAT: Complete SQQQ vs puts comparison across all scenarios
    WHY: Single structured output for CLI formatting and agent consumption
    """

    scenarios: list[ComparisonRow] = Field(
        ..., description="Comparison rows for each market drop scenario"
    )

    sqqq_breakeven_drop: float = Field(
        ..., description="Market drop at which SQQQ position breaks even"
    )

    put_breakeven_drop: float = Field(
        ..., description="Market drop at which put position breaks even"
    )

    disclaimers: list[str] = Field(
        ..., description="Required disclaimers including path-dependency warning"
    )

    parameters: dict = Field(..., description="Config snapshot for reproducibility")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "scenarios": [],
                    "sqqq_breakeven_drop": -0.015,
                    "put_breakeven_drop": -0.112,
                    "disclaimers": [
                        "EDUCATIONAL ONLY. Not investment advice.",
                        "SQQQ decay is path-dependent.",
                    ],
                    "parameters": {
                        "spot_price": 480.0,
                        "put_strike": 432.0,
                        "sqqq_allocation": 10000.0,
                    },
                }
            ]
        }
    }


# Type exports
__all__ = [
    "ScenarioInput",
    "SQQQResult",
    "PutResult",
    "ComparisonRow",
    "ComparisonOutput",
]
