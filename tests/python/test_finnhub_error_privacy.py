"""Synthetic credential markers must stay out of provider diagnostics."""

from __future__ import annotations

import io
import logging
import runpy
import sys
from datetime import date
from types import SimpleNamespace
from typing import Any

import pytest
import requests
from urllib3.connection import HTTPSConnection

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


@pytest.mark.parametrize("status", [200, 403])
@pytest.mark.parametrize("surface", ["quote", "candle", "cli"])
def test_finnhub_transport_logs_hide_token(
    status: int,
    surface: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setenv("FINNHUB_API_KEY", SENTINEL)
    caplog.set_level(logging.DEBUG, logger="urllib3.connectionpool")
    sent: list[bytes] = []
    body = b'{"c":11,"d":1,"dp":10,"t":1792162800}'
    response = (
        f"HTTP/1.1 {status} Synthetic\r\nContent-Length: {len(body)}\r\n"
        "Connection: close\r\n\r\n"
    ).encode() + body

    class SyntheticSocket:
        def settimeout(self, timeout: float | None) -> None:
            pass

        def sendall(self, content: bytes) -> None:
            sent.append(content)

        def makefile(self, *args: object, **kwargs: object) -> io.BytesIO:
            return io.BytesIO(response)

        def close(self) -> None:
            pass

    def connect(connection: HTTPSConnection) -> None:
        connection.sock = SyntheticSocket()
        connection.is_verified = True
        connection.proxy_is_verified = True

    session = requests.Session()
    session.trust_env = False
    monkeypatch.setattr(HTTPSConnection, "connect", connect)
    monkeypatch.setattr(market_data.requests, "get", session.get)
    monkeypatch.setattr(
        market_data.yf,
        "Ticker",
        lambda symbol: SimpleNamespace(
            info={
                "currentPrice": 10,
                "previousClose": 10,
                "regularMarketTime": 1792162800,
            }
        ),
    )
    expected_price = 11 if status == 200 else 10
    if surface == "quote":
        result = market_data.get_prices("TEST", realtime=True)["TEST"]
        assert result.price == expected_price
        assert result.source == ("finnhub" if status == 200 else "yfinance")
    elif surface == "candle":
        dates, high, low, close = [date(2026, 10, 15)], [12.0], [8.0], [10.0]
        market_data.append_live_quote("TEST", dates, high, low, close)
        assert dates == [date(2026, 10, 15), date(2026, 10, 16)]
        assert high[-1] == low[-1] == close[-1] == expected_price
    else:
        monkeypatch.setattr(sys, "argv", ["market_data", "TEST", "--realtime"])
        runpy.run_path(market_data.__file__, run_name="__main__")
    captured = capsys.readouterr()
    if surface == "cli":
        source = "FINNHUB" if status == 200 else "YFINANCE"
        assert f"[{source}]" in captured.out
        assert f"${expected_price:8.2f}" in captured.out
    assert SENTINEL not in captured.out + captured.err + caplog.text
    request = b"".join(sent)
    assert f"X-Finnhub-Token: {SENTINEL}".encode() in request
    assert b"token=" not in request.split(b"\r\n", 1)[0]
