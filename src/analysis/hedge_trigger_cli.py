"""CLI for the hedge-trigger check.

Layer 3 of the three-layer pattern. It reads the rules from the instance
profile's ``hedge_triggers:`` section, margin numbers from the ledger through
``margin_metrics``, the hedge position from the ledger, and daily index and
volatility closes from yfinance. ``hedge_trigger`` does every calculation.

A missing or stale input gives NO_VERDICT with the input named, never a pass.
A missing or invalid ``hedge_triggers:`` section exits 1. While a hedge is
held, ``--activity-synced-at`` must name an activity sync at or after the
positions snapshot, so the entry date is current.

    uv run python -m src.analysis.hedge_trigger_cli --output json

Run it after the US close. A bar dated today counts only after 4:30 PM ET.
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from datetime import UTC, date, datetime
from pathlib import Path

import pandas as pd
import yaml
import yfinance as yf
from pydantic import ValidationError
from yfinance.exceptions import YFException

from src.analysis.hedge_trigger import (
    HedgeTriggerCalculator,
    completed_sessions,
    entry_date_from_activity,
    no_verdict,
    require_current_activity,
    summarize_index,
)
from src.analysis.margin_metrics import _resolve_margin_routing, metrics_from_runtime
from src.config.instance_paths import InstancePaths, _db_path
from src.models.hedge_trigger_inputs import (
    HedgeTriggerInputs,
    HedgeTriggerResult,
    HedgeTriggerRules,
    HeldHedge,
)

PROFILE_SECTION = "hedge_triggers"


def load_rules(profile: Path) -> HedgeTriggerRules:
    """Read the ``hedge_triggers:`` section. No defaults: every threshold is required."""
    data = yaml.safe_load(profile.read_text(encoding="utf-8"))
    section = data.get(PROFILE_SECTION) if isinstance(data, dict) else None
    if not isinstance(section, dict):
        msg = f"{profile} has no {PROFILE_SECTION}: section"
        raise ValueError(msg)
    return HedgeTriggerRules.model_validate(section)


def _daily_bars(symbol: str, period: str, now: datetime) -> pd.DataFrame:
    bars = yf.Ticker(symbol).history(period=period, interval="1d", auto_adjust=False)
    if bars.empty:
        msg = f"yfinance returned no daily history for {symbol}"
        raise ValueError(msg)
    return completed_sessions(bars[["High", "Close"]].dropna(), now)


def read_position(db: Path, account_id: str, symbol: str) -> HeldHedge | None:
    """Read the hedge held in the margin account, with its entry date from activity."""
    conn = sqlite3.connect(db)
    try:
        rows = conn.execute(
            "SELECT quantity, avg_cost, price FROM positions "
            "WHERE account_id = ? AND symbol = ? AND quantity > 0",
            (account_id, symbol),
        ).fetchall()
        if not rows:
            return None
        if len(rows) > 1:
            msg = f"{symbol} is held in {len(rows)} ledger rows; the check reads one position"
            raise ValueError(msg)
        activity = conn.execute(
            "SELECT date, type, quantity FROM transactions WHERE account_id = ? AND symbol = ? "
            "AND quantity IS NOT NULL AND quantity != 0 AND date IS NOT NULL "
            "ORDER BY date, rowid",
            (account_id, symbol),
        ).fetchall()
    finally:
        conn.close()
    quantity, average_cost, price = rows[0]
    entry = entry_date_from_activity(
        ((date.fromisoformat(day[:10]), kind, qty) for day, kind, qty in activity),
        quantity,
    )
    return HeldHedge(
        quantity=quantity, average_cost=average_cost, price=price, entry_date=entry
    )


def evaluate(
    rules: HedgeTriggerRules, now: datetime, activity_synced_at: datetime | None
) -> HedgeTriggerResult:
    """Gather every input. A failed input becomes NO_VERDICT naming it."""
    today = now.astimezone().date()
    try:
        metrics = metrics_from_runtime(source="db")
    except (ValueError, OSError, sqlite3.Error) as error:
        return no_verdict(today, f"margin metrics: {error}")
    try:
        index = summarize_index(
            _daily_bars(rules.index_symbol, "2y", now),
            _daily_bars(rules.volatility_symbol, "1mo", now),
            rules.moving_average_days,
            today,
        )
    except (ValueError, OSError, YFException) as error:
        return no_verdict(today, f"market data: {error}")
    try:
        # The hedge lives in the margin account, the one its sale repays.
        account_id, _, _ = _resolve_margin_routing()
        position = read_position(_db_path(), account_id, rules.hedge_symbol)
        if position is not None:
            require_current_activity(activity_synced_at, metrics.ledger_synced_at)
    except (ValueError, sqlite3.Error) as error:
        return no_verdict(today, f"{rules.hedge_symbol} position: {error}")
    inputs = HedgeTriggerInputs(
        as_of=today,
        # The ledger derives margin debt as gross market value minus equity.
        gross_holdings=metrics.portfolio_value + metrics.margin_balance,
        margin_debt=metrics.margin_balance,
        ledger_synced_at=metrics.ledger_synced_at,
        index=index,
        position=position,
    )
    return HedgeTriggerCalculator(inputs, rules).calculate_all()


def _aware_datetime(text: str) -> datetime:
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        msg = f"{text!r} has no time zone; pass an offset such as +00:00"
        raise argparse.ArgumentTypeError(msg)
    return parsed


def format_text(result: HedgeTriggerResult) -> str:
    """Render the result for a person."""
    lines = [f"Hedge trigger check, {result.as_of}", result.summary, ""]
    lines += [
        f"  [{'x' if r.fired else ' '}] {r.rule}: {r.detail}" for r in result.rules
    ]
    lines += ["", result.disclaimer]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """Print the suggested hedge action."""
    parser = argparse.ArgumentParser(
        description="Suggest a hedge START, HOLD, or EXIT from the profile's rules"
    )
    parser.add_argument(
        "--profile",
        type=Path,
        help="Profile YAML with hedge_triggers:; defaults to the instance's",
    )
    parser.add_argument("--output", choices=("text", "json"), default="text")
    parser.add_argument(
        "--activity-synced-at",
        type=_aware_datetime,
        help="ISO time of the last SnapTrade activities sync; required while a hedge is held",
    )
    args = parser.parse_args(argv)

    profile = args.profile or InstancePaths.resolve().profile
    try:
        rules = load_rules(profile)
    except (OSError, ValueError, ValidationError) as error:
        print(f"Invalid hedge trigger rules in {profile}: {error}", file=sys.stderr)
        return 1
    result = evaluate(rules, datetime.now(UTC), args.activity_synced_at)
    print(
        result.model_dump_json(indent=2)
        if args.output == "json"
        else format_text(result)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
