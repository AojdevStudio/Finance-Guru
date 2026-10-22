"""Trading-calendar constants shared by every calculator and CLI."""

from math import ceil

TRADING_DAYS_PER_YEAR = 252

_CALENDAR_DAYS_PER_TRADING_DAY = 1.5


def calendar_days_for(trading_days: int) -> int:
    """Return the calendar-day lookback that covers ``trading_days`` sessions.

    A calendar year holds about 1.45 calendar days per trading day once
    weekends and market holidays are removed. The 1.5 ratio rounds that up so
    fractional lookbacks round up.

    Args:
        trading_days: Number of trading sessions the caller needs.

    Returns:
        Calendar days to request from a market data provider.
    """
    return ceil(trading_days * _CALENDAR_DAYS_PER_TRADING_DAY)
