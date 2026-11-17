"""Hedge trigger calculator for Finance Guru.

Layer 2 of the three-layer pattern. It turns ledger and market inputs into one
suggested action for a triggered inverse-ETF hedge: START, HOLD, EXIT, or
NO_VERDICT. It suggests only. It never trades.

Holdings/debt here is gross holdings (account equity plus margin debt) divided
by margin debt. ``margin_metrics_cli`` reports equity/debt as
``portfolio_margin_ratio``, which is a different number.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date, datetime, time, timedelta
from itertools import groupby
from zoneinfo import ZoneInfo

import pandas as pd
from pandas.tseries.holiday import (
    AbstractHolidayCalendar,
    GoodFriday,
    Holiday,
    USLaborDay,
    USMartinLutherKingJr,
    USMemorialDay,
    USPresidentsDay,
    USThanksgivingDay,
    nearest_workday,
    sunday_to_monday,
)
from pandas.tseries.offsets import CustomBusinessDay

from src.analysis.margin_metrics import EDUCATIONAL_DISCLAIMER
from src.models.hedge_trigger_inputs import (
    Action,
    HedgeTriggerInputs,
    HedgeTriggerResult,
    HedgeTriggerRules,
    IndexSnapshot,
    RuleResult,
)

MARKET_TZ = ZoneInfo("America/New_York")
# A bar dated today is final only after the close settles.
SESSION_FINAL_AT = time(16, 30)


class NyseHolidays(AbstractHolidayCalendar):
    """Full-day NYSE closures. A special closure missing here gives NO_VERDICT."""

    rules = [
        # NYSE moves a Sunday New Year to Monday, but never closes the Friday before.
        Holiday("New Year's Day", month=1, day=1, observance=sunday_to_monday),
        USMartinLutherKingJr,
        USPresidentsDay,
        GoodFriday,
        USMemorialDay,
        Holiday(
            "Juneteenth",
            month=6,
            day=19,
            start_date="2022-01-01",
            observance=nearest_workday,
        ),
        Holiday("Independence Day", month=7, day=4, observance=nearest_workday),
        USLaborDay,
        USThanksgivingDay,
        Holiday("Christmas", month=12, day=25, observance=nearest_workday),
        Holiday("National Day of Mourning", year=2025, month=1, day=9),
    ]


WEEKS_52 = timedelta(days=365)
# Share counts that differ by less than this match.
SHARE_TOLERANCE = 0.01
# Rule inputs are compared at six decimals, so an exact 10.0% is 10.0%.
RULE_DECIMALS = 6


def completed_sessions(bars: pd.DataFrame, now: datetime) -> pd.DataFrame:
    """Drop today's bar while that session is still open or settling."""
    now_market = now.astimezone(MARKET_TZ)
    if bars.empty or now_market.time() >= SESSION_FINAL_AT:
        return bars
    is_closed = [ts.date() < now_market.date() for ts in bars.index]
    return bars.loc[is_closed]


def latest_completed_session(now: datetime) -> date:
    """Return the newest NYSE session whose close has settled at ``now``."""
    now_market = now.astimezone(MARKET_TZ)
    day = now_market.date()
    if now_market.time() < SESSION_FINAL_AT:
        day -= timedelta(days=1)
    holidays = set(NyseHolidays().holidays(day - timedelta(days=14), day).date)
    while day.weekday() >= 5 or day in holidays:
        day -= timedelta(days=1)
    return day


def _require_session(session: date, expected: date, label: str) -> None:
    if session != expected:
        msg = f"{label} newest completed close is {session}, but the latest completed session is {expected}"
        raise ValueError(msg)


def summarize_index(
    index_bars: pd.DataFrame,
    volatility_bars: pd.DataFrame,
    moving_average_days: int,
    expected_session: date,
    *,
    streak_days: int,
) -> IndexSnapshot:
    """Read the close, 52-week high, moving average, and streak from daily bars.

    Both frames hold completed daily sessions with ``High`` and ``Close``
    columns, oldest first. The 52-week high is the highest intraday high in
    the 365 days that end at the newest session. The newest bar must be
    ``expected_session``, so a feed missing a completed session is refused.
    """
    if len(index_bars) < moving_average_days:
        msg = f"index history has {len(index_bars)} sessions, fewer than the {moving_average_days}-day average needs"
        raise ValueError(msg)
    if volatility_bars.empty:
        msg = "volatility history is empty"
        raise ValueError(msg)
    closes = index_bars["Close"]
    last_ts = index_bars.index[-1]
    session = last_ts.date()
    _require_session(session, expected_session, "index")
    volatility_session = volatility_bars.index[-1].date()
    if volatility_session != session:
        msg = f"index newest close is {session} but volatility newest close is {volatility_session}"
        raise ValueError(msg)
    if index_bars.index[0] > last_ts - WEEKS_52:
        msg = f"index history starts {index_bars.index[0].date()}, short of the 52 weeks before {session}"
        raise ValueError(msg)

    window = index_bars[index_bars.index > last_ts - WEEKS_52]
    # Every session the 52-week high reads must be present. So must every
    # session behind the streak: it counts at most ``streak_days`` closes, enough
    # to decide the exit rule, and each one's average reads
    # ``moving_average_days`` sessions back. A special NYSE closure missing
    # from NyseHolidays gives NO_VERDICT here, naming the date.
    trading_day = CustomBusinessDay(calendar=NyseHolidays())
    streak_start = pd.date_range(
        end=pd.Timestamp(expected_session),
        periods=moving_average_days + streak_days - 1,
        freq=trading_day,
    )[0]
    start = min(
        streak_start, pd.Timestamp(expected_session) - WEEKS_52 + timedelta(days=1)
    )
    sessions = pd.date_range(
        start=start, end=pd.Timestamp(expected_session), freq=trading_day
    ).date
    recent = index_bars[[ts.date() >= sessions[0] for ts in index_bars.index]]
    missing = sorted(set(sessions) - {ts.date() for ts in recent.index})
    if missing or recent["Close"].isna().any():
        msg = f"index history is missing sessions or closes {', '.join(map(str, missing))}"
        raise ValueError(msg)
    if window[["High", "Close"]].isna().any().any():
        msg = "index history is missing a high or close inside the 52 weeks"
        raise ValueError(msg)
    if pd.isna(volatility_bars["Close"].iloc[-1]):
        msg = "volatility history is missing its newest close"
        raise ValueError(msg)
    average = closes.rolling(moving_average_days).mean()
    above = (closes > average).to_list()[-streak_days:]
    streak = 0
    for is_above in reversed(above):
        if not is_above:
            break
        streak += 1

    return IndexSnapshot(
        session_date=session,
        close=float(closes.iloc[-1]),
        high_52_week=float(window["High"].max()),
        moving_average=float(average.iloc[-1]),
        closes_above_average=streak,
        volatility_session_date=volatility_session,
        volatility_close=float(volatility_bars["Close"].iloc[-1]),
    )


def entry_date_from_activity(
    activity: Iterable[tuple[date, str, float]], held_quantity: float
) -> date:
    """Return the date the held position opened, from signed share changes.

    ``activity`` is (date, type, signed quantity) rows, oldest first: buys and
    split additions are positive, sells and split removals negative. The entry
    date is the first day the running total rose above zero after it was last
    flat. It raises when the entry date cannot be trusted:

    - The activity does not add up to ``held_quantity``, so it is stale.
    - A day in the open position has a real sell and a real buy, and its
      negative rows reach zero. The ledger does not keep the order within a
      day, so either day could be the entry. Split rows alone never make a day
      ambiguous, because a split never closes a position.
    """
    total = 0.0
    entry: date | None = None
    ambiguous: date | None = None
    for day, rows in groupby(activity, key=lambda row: row[0]):
        changes = [(kind, quantity) for _, kind, quantity in rows]
        opening = total
        total += sum(quantity for _, quantity in changes)
        sold = sum(quantity for _, quantity in changes if quantity < 0)
        traded_both = any(q > 0 and kind != "SPLIT" for kind, q in changes) and any(
            q < 0 and kind != "SPLIT" for kind, q in changes
        )
        if total <= SHARE_TOLERANCE:
            entry, ambiguous = None, None
        elif opening <= SHARE_TOLERANCE:
            entry = day
        elif traded_both and opening + sold <= SHARE_TOLERANCE:
            ambiguous = day
    if entry is None or abs(total - held_quantity) >= SHARE_TOLERANCE:
        msg = (
            f"ledger activity adds up to {total:g} shares but {held_quantity:g} are held; "
            "sync transactions first"
        )
        raise ValueError(msg)
    if ambiguous is not None:
        msg = f"activity on {ambiguous} sells the whole position and buys again; the entry date is ambiguous"
        raise ValueError(msg)
    return entry


def require_current_activity(
    activity_synced_at: datetime | None, ledger_synced_at: datetime | None
) -> None:
    """Refuse an activity sync older than the positions snapshot it must explain."""
    if activity_synced_at is None or ledger_synced_at is None:
        msg = "no activity sync time was given; run the activity sync and pass --activity-synced-at"
        raise ValueError(msg)
    if activity_synced_at < ledger_synced_at:
        msg = (
            f"activity was last synced at {activity_synced_at.isoformat()}, before the "
            f"positions snapshot at {ledger_synced_at.isoformat()}; sync transactions first"
        )
        raise ValueError(msg)


def no_verdict(as_of: date, failed_input: str) -> HedgeTriggerResult:
    """The result when an input is missing or stale. Never a pass."""
    return HedgeTriggerResult(
        as_of=as_of,
        action="NO_VERDICT",
        summary=f"NO VERDICT: {failed_input}",
        failed_input=failed_input,
        disclaimer=EDUCATIONAL_DISCLAIMER,
    )


class HedgeTriggerCalculator:
    """Evaluate the start and exit rules for one day's inputs."""

    def __init__(self, inputs: HedgeTriggerInputs, rules: HedgeTriggerRules):
        self.inputs = inputs
        self.rules = rules

    def calculate_all(self) -> HedgeTriggerResult:
        """Return the suggested action and every rule's result."""
        inputs, rules = self.inputs, self.rules
        index = inputs.index
        ratio = (
            inputs.gross_holdings / inputs.margin_debt
            if inputs.margin_debt > 0
            else None
        )
        below_high = round(1 - index.close / index.high_52_week, RULE_DECIMALS)
        position = inputs.position
        gain = position.price / position.average_cost - 1 if position else None
        days_held = (inputs.as_of - position.entry_date).days if position else None
        ratio_text = f"{ratio:.2f}" if ratio is not None else "no margin debt"

        start = [
            RuleResult(
                rule="start_ratio",
                kind="start",
                fired=ratio is not None and ratio < rules.start_ratio_below,
                detail=f"holdings/debt {ratio_text}, start below {rules.start_ratio_below}",
            ),
            RuleResult(
                rule="start_drawdown",
                kind="start",
                fired=below_high >= rules.start_drawdown_at_least
                and index.close < index.moving_average,
                detail=(
                    f"{rules.index_symbol} {below_high:.2%} below its 52-week high "
                    f"(start at {rules.start_drawdown_at_least:.0%}), close {index.close:.2f} vs "
                    f"{rules.moving_average_days}-day average {index.moving_average:.2f}"
                ),
            ),
            RuleResult(
                rule="start_volatility",
                kind="start",
                fired=index.volatility_close >= rules.start_volatility_at_least,
                detail=(
                    f"{rules.volatility_symbol} close {index.volatility_close:.2f}, "
                    f"start at {rules.start_volatility_at_least}"
                ),
            ),
        ]
        exit_ = [
            RuleResult(
                rule="exit_gain",
                kind="exit",
                fired=gain is not None and gain >= rules.exit_gain_at_least,
                detail=(
                    f"{rules.hedge_symbol} gain {gain:.2%}, exit at {rules.exit_gain_at_least:.0%}"
                    if gain is not None
                    else f"no {rules.hedge_symbol} position"
                ),
            ),
            RuleResult(
                rule="exit_near_high",
                kind="exit",
                fired=below_high <= rules.exit_within_high,
                detail=f"{rules.index_symbol} {below_high:.2%} below its high, exit within {rules.exit_within_high:.0%}",
            ),
            RuleResult(
                rule="exit_above_average",
                kind="exit",
                fired=index.closes_above_average >= rules.exit_closes_above_average,
                detail=(
                    f"{index.closes_above_average} straight closes above the {rules.moving_average_days}-day "
                    f"average, exit at {rules.exit_closes_above_average}"
                ),
            ),
            RuleResult(
                rule="exit_ratio",
                kind="exit",
                fired=ratio is None or ratio > rules.exit_ratio_above,
                detail=f"holdings/debt {ratio_text}, exit above {rules.exit_ratio_above}",
            ),
            RuleResult(
                rule="exit_time",
                kind="exit",
                fired=days_held is not None and days_held >= rules.exit_after_days,
                detail=(
                    f"held {days_held} days since {position.entry_date}, exit at {rules.exit_after_days}"
                    if position is not None
                    else f"no {rules.hedge_symbol} position"
                ),
            ),
        ]

        fired = [r.rule for r in (exit_ if position else start) if r.fired]
        size: float | None = None
        action: Action
        if position is None and fired:
            action = "START"
            size = round(inputs.gross_holdings * rules.max_size_of_holdings, 2)
            summary = (
                f"START a hedge: buy up to ${size:,.2f} of {rules.hedge_symbol} "
                f"({rules.max_size_of_holdings:.0%} of gross holdings). Fired: {', '.join(fired)}."
            )
        elif position is None:
            action = "HOLD"
            summary = f"HOLD: no hedge. No start rule fired. {rules.index_symbol} {below_high:.2%} below its high."
        elif fired == ["exit_gain"]:
            action = "EXIT"
            summary = f"EXIT half: {rules.hedge_symbol} is up {gain:.2%}. Sell half and repay margin."
        elif fired:
            action = "EXIT"
            summary = f"EXIT: sell the {rules.hedge_symbol} hedge and repay margin. Fired: {', '.join(fired)}."
        else:
            action = "HOLD"
            summary = f"HOLD the {rules.hedge_symbol} hedge. No exit rule fired."

        return HedgeTriggerResult(
            as_of=inputs.as_of,
            action=action,
            summary=summary,
            size_dollars=size,
            holdings_to_debt=round(ratio, 4) if ratio is not None else None,
            index_below_high=round(below_high, 4),
            position_gain=round(gain, 4) if gain is not None else None,
            days_since_entry=days_held,
            rules=start + exit_,
            inputs=inputs,
            rule_config=rules,
            disclaimer=EDUCATIONAL_DISCLAIMER,
        )
