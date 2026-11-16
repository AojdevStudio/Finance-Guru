"""Tests for the hedge-trigger calculator. Synthetic data, no network."""

from __future__ import annotations

import sqlite3
from datetime import UTC, date, datetime
from pathlib import Path

import pandas as pd
import pytest

from src.analysis.hedge_trigger import (
    HedgeTriggerCalculator,
    completed_sessions,
    entry_date_from_activity,
    latest_completed_session,
    no_verdict,
    require_current_activity,
    summarize_index,
)
from src.analysis.hedge_trigger_cli import load_rules, main, read_position
from src.models.hedge_trigger_inputs import (
    HedgeTriggerInputs,
    HedgeTriggerRules,
    HeldHedge,
    IndexSnapshot,
)

RULES = HedgeTriggerRules(
    hedge_symbol="SQQQ",
    index_symbol="QQQ",
    volatility_symbol="^VIX",
    moving_average_days=50,
    start_ratio_below=3.0,
    start_drawdown_at_least=0.10,
    start_volatility_at_least=25,
    exit_gain_at_least=0.30,
    exit_within_high=0.05,
    exit_closes_above_average=3,
    exit_ratio_above=3.5,
    exit_after_days=30,
    max_size_of_holdings=0.06,
)
TODAY = date(2026, 11, 16)


def _index(
    close: float, high: float = 762.86, average: float = 716.72, streak: int = 0
) -> IndexSnapshot:
    return IndexSnapshot(
        session_date=TODAY,
        close=close,
        high_52_week=high,
        moving_average=average,
        closes_above_average=streak,
        volatility_session_date=TODAY,
        volatility_close=22.91,
    )


def _inputs(
    index: IndexSnapshot, position: HeldHedge | None = None, debt: float = 92811.52
) -> HedgeTriggerInputs:
    return HedgeTriggerInputs(
        as_of=TODAY,
        gross_holdings=286287.35,
        margin_debt=debt,
        ledger_synced_at=datetime(2026, 11, 16, 21, tzinfo=UTC),
        index=index,
        position=position,
    )


def test_drawdown_below_average_starts_a_hedge_sized_to_six_percent() -> None:
    result = HedgeTriggerCalculator(_inputs(_index(661.75)), RULES).calculate_all()

    assert result.action == "START"
    assert result.size_dollars == 17177.24
    assert [r.rule for r in result.rules if r.fired] == ["start_drawdown"]


def test_drawdown_above_its_average_does_not_start() -> None:
    result = HedgeTriggerCalculator(
        _inputs(_index(661.75, average=650.0)), RULES
    ).calculate_all()

    assert result.action == "HOLD"
    assert result.size_dollars is None


def test_a_thirty_percent_gain_alone_exits_half() -> None:
    position = HeldHedge(
        quantity=100, average_cost=50, price=66, entry_date=date(2026, 11, 2)
    )

    result = HedgeTriggerCalculator(
        _inputs(_index(661.75), position), RULES
    ).calculate_all()

    assert result.action == "EXIT"
    assert result.summary.startswith("EXIT half")


def test_thirty_days_held_exits_the_whole_hedge() -> None:
    position = HeldHedge(
        quantity=100, average_cost=50, price=51, entry_date=date(2026, 10, 17)
    )

    result = HedgeTriggerCalculator(
        _inputs(_index(661.75), position), RULES
    ).calculate_all()

    assert result.action == "EXIT"
    assert "exit_time" in result.summary


def test_entry_date_is_the_first_buy_after_the_position_was_last_flat() -> None:
    # A reverse split sells 900 and adds 180 on one day without closing.
    activity = [
        (date(2025, 11, 6), "BUY", 900.0),
        (date(2025, 11, 20), "SPLIT", -900.0),
        (date(2025, 11, 20), "SPLIT", 180.0),
        (date(2026, 3, 6), "SELL", -180.0),
        (date(2026, 11, 3), "BUY", 40.0),
        (date(2026, 11, 5), "BUY", 10.0),
    ]

    assert entry_date_from_activity(activity, 50.0) == date(2026, 11, 3)
    assert entry_date_from_activity(activity[:3], 180.0) == date(2025, 11, 6)


def test_selling_out_and_rebuying_on_one_day_is_ambiguous() -> None:
    # The ledger does not keep the order: the rebuy may predate the sell.
    activity = [
        (date(2026, 10, 1), "BUY", 100.0),
        (date(2026, 11, 13), "BUY", 50.0),
        (date(2026, 11, 13), "SELL", -100.0),
    ]

    with pytest.raises(ValueError, match="ambiguous"):
        entry_date_from_activity(activity, 50.0)


def test_a_split_day_with_a_sell_out_and_rebuy_is_ambiguous() -> None:
    activity = [
        (date(2026, 10, 1), "BUY", 100.0),
        (date(2026, 11, 13), "SPLIT", -100.0),
        (date(2026, 11, 13), "SPLIT", 20.0),
        (date(2026, 11, 13), "SELL", -20.0),
        (date(2026, 11, 13), "BUY", 20.0),
    ]

    with pytest.raises(ValueError, match="ambiguous"):
        entry_date_from_activity(activity, 20.0)


def test_a_sync_time_without_a_time_zone_is_rejected() -> None:
    with pytest.raises(SystemExit):
        main(["--activity-synced-at", "2026-11-16T22:00:00"])


def test_activity_synced_before_the_positions_snapshot_is_refused() -> None:
    snapshot = datetime(2026, 11, 16, 21, tzinfo=UTC)

    with pytest.raises(ValueError, match="before the positions snapshot"):
        require_current_activity(datetime(2026, 11, 13, 21, tzinfo=UTC), snapshot)
    with pytest.raises(ValueError, match="no activity sync time"):
        require_current_activity(None, snapshot)
    require_current_activity(datetime(2026, 11, 16, 21, 1, tzinfo=UTC), snapshot)


def test_activity_that_misses_a_reopened_position_is_refused() -> None:
    # Transactions not yet synced: the ledger holds 50 shares, activity shows 40.
    activity = [
        (date(2025, 11, 6), "BUY", 900.0),
        (date(2026, 3, 6), "SELL", -900.0),
        (date(2026, 11, 3), "BUY", 40.0),
    ]

    with pytest.raises(ValueError, match="sync transactions first"):
        entry_date_from_activity(activity, 50.0)


def test_exactly_ten_percent_below_the_high_starts() -> None:
    result = HedgeTriggerCalculator(
        _inputs(_index(90.0, high=100.0, average=95.0)), RULES
    ).calculate_all()

    assert result.action == "START"


def _bars(closes: list[float], end: str, tz: str = "America/New_York") -> pd.DataFrame:
    index = pd.bdate_range(end=end, periods=len(closes), tz=tz)
    return pd.DataFrame({"High": [c + 1 for c in closes], "Close": closes}, index=index)


def test_three_closes_over_a_rising_average_count_as_a_streak() -> None:
    closes = [100.0] * 260 + [90.0, 110.0, 111.0, 112.0]

    snapshot = summarize_index(
        _bars(closes, "2026-11-16"),
        _bars([20.0], "2026-11-16"),
        50,
        TODAY,
        streak_days=3,
    )

    assert snapshot.closes_above_average == 3
    assert snapshot.high_52_week == 113.0


def test_stale_market_data_is_refused() -> None:
    with pytest.raises(ValueError, match="newest completed close"):
        summarize_index(
            _bars([100.0] * 270, "2026-11-06"),
            _bars([20.0], "2026-11-16"),
            50,
            TODAY,
            streak_days=3,
        )


def test_index_and_volatility_from_different_sessions_are_refused() -> None:
    with pytest.raises(ValueError, match="volatility newest close"):
        summarize_index(
            _bars([100.0] * 270, "2026-11-16"),
            _bars([20.0], "2026-11-13"),
            50,
            TODAY,
            streak_days=3,
        )


def test_history_shorter_than_52_weeks_is_refused() -> None:
    # Starts five days inside the window, so a high on those days would be missed.
    days = pd.bdate_range(start="2025-11-21", end="2026-11-16", tz="America/New_York")
    bars = pd.DataFrame({"High": 101.0, "Close": 100.0}, index=days)

    with pytest.raises(ValueError, match="short of the 52 weeks"):
        summarize_index(bars, _bars([20.0], "2026-11-16"), 50, TODAY, streak_days=3)


def test_an_open_session_bar_is_dropped_until_the_close_settles() -> None:
    bars = _bars([100.0, 101.0], "2026-11-16")

    assert len(completed_sessions(bars, datetime(2026, 11, 16, 19, tzinfo=UTC))) == 1
    assert len(completed_sessions(bars, datetime(2026, 11, 16, 22, tzinfo=UTC))) == 2


def test_a_profile_without_hedge_triggers_fails_closed(tmp_path: Path) -> None:
    profile = tmp_path / "user-profile.yaml"
    profile.write_text("user_profile: {}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="no hedge_triggers"):
        load_rules(profile)


def test_a_hedge_in_another_account_does_not_set_the_entry_date(tmp_path: Path) -> None:
    db = tmp_path / "ledger.db"
    conn = sqlite3.connect(db)
    conn.executescript(
        "CREATE TABLE positions (account_id, symbol, instrument, quantity, avg_cost, price, synced_at);"
        "CREATE TABLE transactions (account_id, date, type, symbol, quantity);"
        "INSERT INTO positions VALUES ('margin', 'SQQQ', 'equity', 10, 50, 52, 'now');"
        "INSERT INTO positions VALUES ('ira', 'SQQQ', 'equity', 5, 40, 52, 'now');"
        "INSERT INTO transactions VALUES ('ira', '2026-01-02', 'BUY', 'SQQQ', 5);"
        "INSERT INTO transactions VALUES ('margin', '2026-11-13', 'BUY', 'SQQQ', 10);"
    )
    conn.commit()
    conn.close()

    held = read_position(db, "margin", "SQQQ")

    assert held is not None
    assert (held.quantity, held.entry_date) == (10, date(2026, 11, 13))


def test_a_dividend_with_units_does_not_change_the_share_count(tmp_path: Path) -> None:
    db = tmp_path / "ledger.db"
    conn = sqlite3.connect(db)
    conn.executescript(
        "CREATE TABLE positions (account_id, symbol, instrument, quantity, avg_cost, price, synced_at);"
        "CREATE TABLE transactions (account_id, date, type, symbol, quantity);"
        "INSERT INTO positions VALUES ('margin', 'SQQQ', 'equity', 10, 50, 52, 'now');"
        "INSERT INTO transactions VALUES ('margin', '2026-11-13', 'BUY', 'SQQQ', 10);"
        "INSERT INTO transactions VALUES ('margin', '2026-11-20', 'DIVIDEND', 'SQQQ', 10);"
    )
    conn.commit()
    conn.close()

    held = read_position(db, "margin", "SQQQ")

    assert held is not None
    assert (held.quantity, held.entry_date) == (10, date(2026, 11, 13))


def test_a_no_verdict_result_still_names_its_data_sources() -> None:
    result = no_verdict(date(2026, 11, 16), "market data: down")

    sources = result.model_dump(mode="json")["data_sources"]
    assert any("ledger" in source for source in sources)
    assert any("yfinance" in source for source in sources)


def _ledger(tmp_path: Path, held: float, rows: str) -> Path:
    db = tmp_path / "ledger.db"
    conn = sqlite3.connect(db)
    conn.executescript(
        "CREATE TABLE positions (account_id, symbol, instrument, quantity, avg_cost, price, synced_at);"
        "CREATE TABLE transactions (account_id, date, type, symbol, quantity);"
        f"INSERT INTO positions VALUES ('margin', 'SQQQ', 'equity', {held}, 50, 52, 'now');"
        + rows
    )
    conn.commit()
    conn.close()
    return db


def test_untyped_activity_still_counts_toward_the_entry_date(tmp_path: Path) -> None:
    db = _ledger(
        tmp_path,
        10,
        "INSERT INTO transactions VALUES ('margin', '2026-10-01', 'BUY', 'SQQQ', 10);"
        "INSERT INTO transactions VALUES ('margin', '2026-11-12', NULL, 'SQQQ', -10);"
        "INSERT INTO transactions VALUES ('margin', '2026-11-13', NULL, 'SQQQ', 10);",
    )

    held = read_position(db, "margin", "SQQQ")

    assert held is not None
    assert held.entry_date == date(2026, 11, 13)


def test_a_stock_dividend_adds_shares(tmp_path: Path) -> None:
    db = _ledger(
        tmp_path,
        11,
        "INSERT INTO transactions VALUES ('margin', '2026-11-13', 'BUY', 'SQQQ', 10);"
        "INSERT INTO transactions VALUES ('margin', '2026-11-20', 'STOCK_DIVIDEND', 'SQQQ', 1);",
    )

    held = read_position(db, "margin", "SQQQ")

    assert held is not None
    assert (held.quantity, held.entry_date) == (11, date(2026, 11, 13))


def test_aligned_feeds_missing_a_weekday_session_are_refused() -> None:
    # Monday Nov 16 after the close, both feeds end Thursday Nov 12: Friday and Monday are missing.
    with pytest.raises(ValueError, match="newest completed close"):
        summarize_index(
            _bars([100.0] * 270, "2026-11-12"),
            _bars([20.0], "2026-11-12"),
            50,
            TODAY,
            streak_days=3,
        )


def test_the_latest_completed_session_skips_weekends_holidays_and_open_sessions() -> (
    None
):
    # Monday before the close settles: Friday's session is the latest.
    assert latest_completed_session(datetime(2026, 11, 16, 19, tzinfo=UTC)) == date(
        2026, 11, 13
    )
    assert latest_completed_session(datetime(2026, 11, 16, 22, tzinfo=UTC)) == TODAY
    # Thanksgiving evening: Wednesday's session is the latest.
    assert latest_completed_session(datetime(2026, 11, 26, 23, tzinfo=UTC)) == date(
        2026, 11, 25
    )


def test_a_missing_close_inside_the_streak_is_refused() -> None:
    bars = _bars([100.0] * 260 + [110.0, 111.0, 112.0, 113.0], "2026-11-16")
    bars.loc[bars.index[-2], "Close"] = float("nan")

    with pytest.raises(ValueError, match="missing"):
        summarize_index(bars, _bars([20.0], "2026-11-16"), 50, TODAY, streak_days=3)


def test_a_dropped_session_inside_the_average_window_is_refused() -> None:
    bars = _bars([100.0] * 260 + [110.0, 111.0, 112.0, 113.0], "2026-11-16")

    with pytest.raises(ValueError, match="missing"):
        summarize_index(
            bars.drop(bars.index[-2]),
            _bars([20.0], "2026-11-16"),
            50,
            TODAY,
            streak_days=3,
        )


def test_new_year_on_a_saturday_leaves_the_friday_before_open() -> None:
    assert latest_completed_session(datetime(2027, 12, 31, 23, tzinfo=UTC)) == date(
        2027, 12, 31
    )


def test_a_substitute_dividend_with_units_is_cash(tmp_path: Path) -> None:
    db = _ledger(
        tmp_path,
        10,
        "INSERT INTO transactions VALUES ('margin', '2026-11-13', 'BUY', 'SQQQ', 10);"
        "INSERT INTO transactions VALUES ('margin', '2026-11-20', 'SUBSTITUTE_DIVIDEND', 'SQQQ', 10);",
    )

    held = read_position(db, "margin", "SQQQ")

    assert held is not None
    assert held.entry_date == date(2026, 11, 13)


def test_a_dropped_session_feeding_an_earlier_streak_average_is_refused() -> None:
    bars = _bars([100.0] * 260 + [110.0, 111.0, 112.0, 113.0], "2026-11-16")
    # Older than the newest 50 sessions, but inside the averages behind the streak.
    gap = bars.index[-52]

    with pytest.raises(ValueError, match="missing"):
        summarize_index(
            bars.drop(gap), _bars([20.0], "2026-11-16"), 50, TODAY, streak_days=3
        )


def test_a_streak_longer_than_the_average_window_can_still_exit() -> None:
    closes = [100.0] * 240 + [101.0 + i for i in range(30)]

    snapshot = summarize_index(
        _bars(closes, "2026-11-16"),
        _bars([20.0], "2026-11-16"),
        20,
        TODAY,
        streak_days=30,
    )

    assert snapshot.closes_above_average == 30
