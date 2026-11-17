"""Hedge trigger models for Finance Guru.

Layer 1 of the three-layer pattern for the hedge-trigger check. The rules
come from the instance profile's ``hedge_triggers:`` section, with no
defaults here, so a missing threshold fails closed instead of guessing.

The check suggests a triggered inverse-ETF hedge: start one when markets or
leverage turn risky, exit it when they recover or the position pays off. It
never trades.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Action = Literal["START", "HOLD", "EXIT", "NO_VERDICT"]


class HedgeTriggerRules(BaseModel):
    """Thresholds for starting and exiting a triggered hedge.

    Ratios are gross holdings divided by margin debt. Percentages are
    decimals (0.10 is 10%).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    hedge_symbol: str = Field(min_length=1, description="Inverse ETF held as the hedge")
    index_symbol: str = Field(min_length=1, description="Index ETF the hedge tracks")
    volatility_symbol: str = Field(min_length=1, description="Volatility index symbol")
    moving_average_days: int = Field(
        ge=2, description="Days in the index moving average"
    )
    start_ratio_below: float = Field(
        gt=0, description="START when holdings/debt is below this"
    )
    start_drawdown_at_least: float = Field(
        gt=0,
        lt=1,
        description="START when the index is this far below its 52-week high and below its average",
    )
    start_volatility_at_least: float = Field(
        gt=0, description="START when the volatility close is at least this"
    )
    exit_gain_at_least: float = Field(
        gt=0, description="EXIT when the hedge is up this much"
    )
    exit_within_high: float = Field(
        gt=0, lt=1, description="EXIT when the index is within this of its 52-week high"
    )
    exit_closes_above_average: int = Field(
        ge=1, description="EXIT after this many straight closes above the average"
    )
    exit_ratio_above: float = Field(
        gt=0, description="EXIT when holdings/debt is above this"
    )
    exit_after_days: int = Field(
        ge=1, description="EXIT this many calendar days after entry"
    )
    max_size_of_holdings: float = Field(
        gt=0, le=1, description="Largest hedge as a share of gross holdings"
    )


class IndexSnapshot(BaseModel):
    """The index and volatility numbers the rules read, from completed sessions."""

    model_config = ConfigDict(frozen=True)

    session_date: date
    close: float = Field(gt=0)
    high_52_week: float = Field(gt=0)
    moving_average: float = Field(gt=0)
    closes_above_average: int = Field(
        ge=0, description="Straight closes above the average, newest first"
    )
    volatility_session_date: date
    volatility_close: float = Field(gt=0)


class HeldHedge(BaseModel):
    """The hedge position held in the ledger."""

    model_config = ConfigDict(frozen=True)

    quantity: float = Field(gt=0)
    average_cost: float = Field(gt=0)
    price: float = Field(gt=0)
    entry_date: date


class HedgeTriggerInputs(BaseModel):
    """Everything one evaluation reads."""

    model_config = ConfigDict(frozen=True)

    as_of: date
    gross_holdings: float = Field(gt=0)
    margin_debt: float = Field(ge=0)
    ledger_synced_at: datetime | None
    index: IndexSnapshot
    position: HeldHedge | None


DATA_SOURCES = (
    "Margin, holdings, and hedge position: local SQLite ledger (SnapTrade sync)",
    "Index and volatility closes: Yahoo Finance via yfinance",
)


class RuleResult(BaseModel):
    """One rule, its measured value, and whether it fired."""

    model_config = ConfigDict(frozen=True)

    rule: str
    kind: Literal["start", "exit"]
    fired: bool
    detail: str


class HedgeTriggerResult(BaseModel):
    """One suggested action with the inputs and rules behind it."""

    model_config = ConfigDict(frozen=True)

    as_of: date
    action: Action
    summary: str
    size_dollars: float | None = None
    failed_input: str | None = None
    holdings_to_debt: float | None = None
    index_below_high: float | None = None
    position_gain: float | None = None
    days_since_entry: int | None = None
    rules: list[RuleResult] = Field(default_factory=list)
    inputs: HedgeTriggerInputs | None = None
    rule_config: HedgeTriggerRules | None = None
    data_sources: tuple[str, ...] = DATA_SOURCES
    disclaimer: str
