"""Synthetic credential markers must stay out of provider diagnostics."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
import requests

from src.utils import market_data

SENTINEL = "SYNTHETIC_FINNHUB_SENTINEL"


@pytest.mark.parametrize("kind", ["http", "transport", "provider", "unexpected"])
def test_finnhub_failure_hides_private_details_and_preserves_fallback(
    kind: str, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("FINNHUB_API_KEY", SENTINEL)
    response = requests.Response()
    response.status_code = 403
    response.url = f"https://finnhub.example.test/quote?token={SENTINEL}"

    def get(*args: Any, **kwargs: Any) -> Any:
        if kind == "http":
            return response
        if kind == "transport":
            raise requests.ConnectionError(SENTINEL)
        if kind == "unexpected":
            raise RuntimeError(SENTINEL)
        return SimpleNamespace(
            raise_for_status=lambda: None, json=lambda: {"error": SENTINEL}
        )

    monkeypatch.setattr(market_data.requests, "get", get)
    monkeypatch.setattr(
        market_data.yf,
        "Ticker",
        lambda symbol: SimpleNamespace(info={"currentPrice": 10, "previousClose": 10}),
    )

    result = market_data.get_prices("TEST", realtime=True)

    output = capsys.readouterr()
    assert result["TEST"].source == "yfinance"
    assert result["TEST"].price == 10
    assert "Falling back to yfinance" in output.out
    assert SENTINEL not in output.out + output.err, "Diagnostic exposes synthetic key"
