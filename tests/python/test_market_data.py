"""Tests for Finance Guru market data utility.

Tests the get_prices function with mocked yfinance and API calls.
No real API calls -- all external calls are mocked.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.utils.market_data import PriceData, get_prices

# ---------------------------------------------------------------------------
# PriceData model
# ---------------------------------------------------------------------------


class TestPriceDataModel:
    """Tests for the PriceData Pydantic model."""

    def test_create_price_data(self):
        pd_obj = PriceData(
            symbol="TSLA",
            price=250.50,
            change=5.25,
            change_percent=2.14,
            timestamp="2025-01-02T10:00:00",
            source="yfinance",
        )
        assert pd_obj.symbol == "TSLA"
        assert pd_obj.price == 250.50

    def test_default_source_is_yfinance(self):
        pd_obj = PriceData(
            symbol="AAPL",
            price=180.0,
            change=-1.0,
            change_percent=-0.55,
            timestamp="2025-01-02T10:00:00",
        )
        assert pd_obj.source == "yfinance"


# ---------------------------------------------------------------------------
# get_prices -- yfinance path
# ---------------------------------------------------------------------------


class TestGetPricesYfinance:
    """Tests for get_prices with yfinance (default path)."""

    @patch("src.utils.market_data.yf")
    def test_single_ticker(self, mock_yf: MagicMock):
        """get_prices with single string ticker should return dict."""
        mock_ticker = MagicMock()
        mock_ticker.info = {
            "currentPrice": 250.50,
            "previousClose": 245.25,
        }
        mock_yf.Ticker.return_value = mock_ticker

        result = get_prices("TSLA")
        assert "TSLA" in result
        assert result["TSLA"].price == 250.50
        assert result["TSLA"].source == "yfinance"

    @patch("src.utils.market_data.yf")
    def test_multiple_tickers(self, mock_yf: MagicMock):
        """get_prices with list of tickers should return dict per ticker."""

        def make_ticker(price: float, prev: float) -> MagicMock:
            t = MagicMock()
            t.info = {"currentPrice": price, "previousClose": prev}
            return t

        mock_yf.Ticker.side_effect = [
            make_ticker(250.0, 245.0),
            make_ticker(40.0, 39.0),
        ]

        result = get_prices(["TSLA", "PLTR"])
        assert len(result) == 2
        assert "TSLA" in result
        assert "PLTR" in result

    @patch("src.utils.market_data.yf")
    def test_change_calculated_correctly(self, mock_yf: MagicMock):
        mock_ticker = MagicMock()
        mock_ticker.info = {
            "currentPrice": 100.0,
            "previousClose": 95.0,
        }
        mock_yf.Ticker.return_value = mock_ticker

        result = get_prices("ABC")
        pd_obj = result["ABC"]
        assert pd_obj.change == pytest.approx(5.0, abs=0.01)
        assert pd_obj.change_percent == pytest.approx(5.26, abs=0.1)

    @patch("src.utils.market_data.yf")
    def test_fallback_to_regular_market_price(self, mock_yf: MagicMock):
        """Should use regularMarketPrice when currentPrice is missing."""
        mock_ticker = MagicMock()
        mock_ticker.info = {
            "regularMarketPrice": 180.0,
            "previousClose": 175.0,
        }
        mock_yf.Ticker.return_value = mock_ticker

        result = get_prices("AAPL")
        assert result["AAPL"].price == 180.0

    @patch("src.utils.market_data.yf")
    def test_error_handling_returns_empty(self, mock_yf: MagicMock):
        """When yfinance raises, ticker should be skipped."""
        mock_yf.Ticker.side_effect = Exception("API error")

        result = get_prices("BAD")
        assert result == {}

    @patch("src.utils.market_data.yf")
    def test_zero_previous_close_no_division_error(self, mock_yf: MagicMock):
        """Should handle zero previousClose without ZeroDivisionError."""
        mock_ticker = MagicMock()
        mock_ticker.info = {
            "currentPrice": 100.0,
            "previousClose": 0,
        }
        mock_yf.Ticker.return_value = mock_ticker

        result = get_prices("ZERO")
        assert "ZERO" in result
        assert result["ZERO"].change_percent == 0


# ---------------------------------------------------------------------------
# get_prices -- Finnhub/realtime path
# ---------------------------------------------------------------------------


class TestGetPricesRealtime:
    """Tests for get_prices with realtime=True (Finnhub)."""

    @patch("src.utils.market_data.requests")
    @patch.dict("os.environ", {"FINNHUB_API_KEY": "test_key_123"})
    def test_realtime_finnhub_success(self, mock_requests: MagicMock):
        """Realtime call should use Finnhub API."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "c": 250.50,
            "d": 5.25,
            "dp": 2.14,
        }
        mock_response.raise_for_status = MagicMock()
        mock_requests.get.return_value = mock_response

        result = get_prices("TSLA", realtime=True)
        assert "TSLA" in result
        assert result["TSLA"].price == 250.50
        assert result["TSLA"].source == "finnhub"

    @patch("src.utils.market_data._get_prices_yfinance")
    @patch.dict("os.environ", {"FINNHUB_API_KEY": ""})
    def test_realtime_falls_back_without_api_key(self, mock_yf_fn: MagicMock):
        """Without FINNHUB_API_KEY, should fall back to yfinance."""
        mock_yf_fn.return_value = {
            "TSLA": PriceData(
                symbol="TSLA",
                price=250.0,
                change=5.0,
                change_percent=2.0,
                timestamp="2025-01-02T10:00:00",
                source="yfinance",
            )
        }
        result = get_prices("TSLA", realtime=True)
        assert "TSLA" in result
        assert result["TSLA"].source == "yfinance"

    @patch("src.utils.market_data.requests")
    @patch("src.utils.market_data._get_prices_yfinance")
    @patch.dict("os.environ", {"FINNHUB_API_KEY": "test_key_123"})
    def test_realtime_network_error_falls_back(
        self, mock_yf_fn: MagicMock, mock_requests: MagicMock
    ):
        """Network error on Finnhub should fall back to yfinance."""
        import requests as real_requests

        mock_requests.get.side_effect = real_requests.exceptions.ConnectionError(
            "timeout"
        )
        mock_requests.exceptions = real_requests.exceptions
        mock_yf_fn.return_value = {
            "TSLA": PriceData(
                symbol="TSLA",
                price=249.0,
                change=4.0,
                change_percent=1.6,
                timestamp="2025-01-02T10:00:00",
                source="yfinance",
            )
        }
        result = get_prices("TSLA", realtime=True)
        assert "TSLA" in result


# ---------------------------------------------------------------------------
# Input normalization
# ---------------------------------------------------------------------------


class TestInputNormalization:
    """Tests for input handling."""

    @patch("src.utils.market_data.yf")
    def test_string_input_normalized_to_list(self, mock_yf: MagicMock):
        """Single string should be treated as single-element list."""
        mock_ticker = MagicMock()
        mock_ticker.info = {"currentPrice": 100.0, "previousClose": 95.0}
        mock_yf.Ticker.return_value = mock_ticker

        result = get_prices("AAPL")
        assert isinstance(result, dict)
        assert len(result) == 1

    @patch("src.utils.market_data.yf")
    def test_ticker_uppercased(self, mock_yf: MagicMock):
        """Result keys should be uppercased."""
        mock_ticker = MagicMock()
        mock_ticker.info = {"currentPrice": 100.0, "previousClose": 95.0}
        mock_yf.Ticker.return_value = mock_ticker

        result = get_prices("aapl")
        assert "AAPL" in result
