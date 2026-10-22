"""Risk and return inputs keep the provider's quote session, even on fallback."""

from datetime import UTC, date, datetime

import pandas as pd
import pytest

from src.analysis import risk_metrics_cli, total_return_cli


class _Sunday(date):
    @classmethod
    def today(cls) -> date:
        return date(2026, 10, 18)


@pytest.fixture
def quote_history(mocker, monkeypatch):
    """Use real quote adapters with a synthetic Yahoo response and no credentials."""
    monkeypatch.setenv("FINNHUB_API_KEY", "")
    mocker.patch.object(risk_metrics_cli, "date", _Sunday)
    mocker.patch.object(total_return_cli, "date", _Sunday)
    ticker = mocker.patch("yfinance.Ticker").return_value
    dates = pd.bdate_range(end="2026-10-15", periods=30)
    prices = [100.0 + i for i in range(len(dates))]
    ticker.history.return_value = pd.DataFrame(
        {"Close": prices, "Dividends": [0.0] * len(dates)}, index=dates
    )
    ticker.info = {"currentPrice": 160.0, "previousClose": 129.0}
    return ticker, [d.date() for d in dates], prices


@pytest.mark.parametrize(
    "session",
    [None, date(2026, 10, 14), date(2026, 10, 15), date(2026, 10, 16)],
    ids=["unknown", "older", "same", "newer"],
)
def test_risk_realtime_preserves_quote_session(quote_history, session):
    ticker, dates, prices = quote_history
    if session is not None:
        ticker.info["regularMarketTime"] = (
            datetime.combine(session, datetime.min.time(), tzinfo=UTC)
            .replace(hour=20)
            .timestamp()
        )

    result = risk_metrics_cli.fetch_price_data("ABC", days=60, realtime=True)

    append = session is not None and session > dates[-1]
    assert result.dates == dates + ([session] if append else [])
    assert result.prices == prices + ([160.0] if append else [])


@pytest.mark.parametrize(
    "session",
    [None, date(2026, 10, 14), date(2026, 10, 15), date(2026, 10, 16)],
    ids=["unknown", "older", "same", "newer"],
)
def test_total_return_realtime_preserves_quote_session(quote_history, session):
    ticker, dates, historical_prices = quote_history
    if session is not None:
        ticker.info["regularMarketTime"] = (
            datetime.combine(session, datetime.min.time(), tzinfo=UTC)
            .replace(hour=20)
            .timestamp()
        )

    inputs, prices, _, _ = total_return_cli.fetch_ticker_data(
        "ABC", days=60, realtime=True
    )

    append = session is not None and session > dates[-1]
    assert prices == historical_prices + ([160.0] if append else [])
    assert inputs.end_date == (session if append else dates[-1])
