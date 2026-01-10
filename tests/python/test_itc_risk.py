"""
Tests for ITC Risk Calculator.

These tests verify the ITCRiskCalculator functionality including:
- Ticker validation (supported vs unsupported)
- API key requirements
- Response parsing
- Risk band methods
- Error handling

RUNNING TESTS:
    # Run all ITC risk tests
    uv run pytest tests/python/test_itc_risk.py -v

    # Run only calculator tests
    uv run pytest tests/python/test_itc_risk.py::TestITCRiskCalculator -v

    # Run integration tests (requires ITC_API_KEY)
    uv run pytest tests/python/test_itc_risk.py -v -m integration

Author: Finance Guru Development Team
Created: 2026-01-09
"""

import os
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from src.models.itc_risk_inputs import ITCRiskResponse, RiskBand


class TestITCRiskCalculatorInit:
    """Tests for ITCRiskCalculator initialization."""

    def test_calculator_requires_api_key(self):
        """Calculator should raise error without API key."""
        # Ensure environment variable is not set
        original_key = os.environ.pop("ITC_API_KEY", None)

        try:
            from src.analysis.itc_risk import ITCRiskCalculator

            with pytest.raises(ValueError, match="ITC API key required"):
                ITCRiskCalculator()
        finally:
            # Restore original key if it existed
            if original_key:
                os.environ["ITC_API_KEY"] = original_key

    def test_calculator_accepts_explicit_api_key(self):
        """Calculator should accept API key as argument."""
        from src.analysis.itc_risk import ITCRiskCalculator

        calc = ITCRiskCalculator(api_key="test_key_12345")
        assert calc.api_key == "test_key_12345"

    def test_calculator_uses_env_variable(self):
        """Calculator should load API key from environment."""
        os.environ["ITC_API_KEY"] = "env_test_key"

        try:
            from src.analysis.itc_risk import ITCRiskCalculator

            calc = ITCRiskCalculator()
            assert calc.api_key == "env_test_key"
        finally:
            del os.environ["ITC_API_KEY"]


class TestITCRiskCalculatorValidation:
    """Tests for ticker validation logic."""

    def test_validate_ticker_passes_for_supported_tradfi(self):
        """Supported tradfi tickers should pass validation."""
        from src.analysis.itc_risk import ITCRiskCalculator

        calc = ITCRiskCalculator(api_key="dummy")

        # These should NOT raise
        calc.validate_ticker("TSLA", "tradfi")
        calc.validate_ticker("AAPL", "tradfi")
        calc.validate_ticker("MSTR", "tradfi")
        calc.validate_ticker("NFLX", "tradfi")
        calc.validate_ticker("SP500", "tradfi")

    def test_validate_ticker_passes_for_supported_crypto(self):
        """Supported crypto tickers should pass validation."""
        from src.analysis.itc_risk import ITCRiskCalculator

        calc = ITCRiskCalculator(api_key="dummy")

        # These should NOT raise
        calc.validate_ticker("BTC", "crypto")
        calc.validate_ticker("ETH", "crypto")
        calc.validate_ticker("SOL", "crypto")

    def test_validate_ticker_fails_for_unsupported(self):
        """Unsupported tickers should raise clear error."""
        from src.analysis.itc_risk import ITCRiskCalculator

        calc = ITCRiskCalculator(api_key="dummy")

        with pytest.raises(ValueError, match="PLTR not supported"):
            calc.validate_ticker("PLTR", "tradfi")

        with pytest.raises(ValueError, match="NVDA not supported"):
            calc.validate_ticker("NVDA", "tradfi")

        with pytest.raises(ValueError, match="GOOGL not supported"):
            calc.validate_ticker("GOOGL", "tradfi")

    def test_validate_ticker_case_insensitive(self):
        """Ticker validation should be case-insensitive."""
        from src.analysis.itc_risk import ITCRiskCalculator

        calc = ITCRiskCalculator(api_key="dummy")

        # Lowercase should work
        calc.validate_ticker("tsla", "tradfi")
        calc.validate_ticker("btc", "crypto")

        # Mixed case should work
        calc.validate_ticker("TsLa", "tradfi")

    def test_is_ticker_supported_returns_boolean(self):
        """is_ticker_supported should return True/False without raising."""
        from src.analysis.itc_risk import ITCRiskCalculator

        calc = ITCRiskCalculator(api_key="dummy")

        assert calc.is_ticker_supported("TSLA", "tradfi") is True
        assert calc.is_ticker_supported("PLTR", "tradfi") is False
        assert calc.is_ticker_supported("BTC", "crypto") is True
        assert calc.is_ticker_supported("UNKNOWN", "crypto") is False

    def test_get_supported_tickers_returns_sorted_list(self):
        """get_supported_tickers should return sorted list."""
        from src.analysis.itc_risk import ITCRiskCalculator

        calc = ITCRiskCalculator(api_key="dummy")

        tradfi_tickers = calc.get_supported_tickers("tradfi")
        assert "TSLA" in tradfi_tickers
        assert "AAPL" in tradfi_tickers
        assert tradfi_tickers == sorted(tradfi_tickers)

        crypto_tickers = calc.get_supported_tickers("crypto")
        assert "BTC" in crypto_tickers
        assert "ETH" in crypto_tickers
        assert crypto_tickers == sorted(crypto_tickers)


class TestITCRiskCalculatorParsing:
    """Tests for response parsing logic."""

    def test_parse_risk_bands_valid_data(self):
        """Risk bands should be parsed from valid API response."""
        from src.analysis.itc_risk import ITCRiskCalculator

        calc = ITCRiskCalculator(api_key="dummy")

        data = {
            "risk_table": [
                {"price": 100.0, "risk": 0.1},
                {"price": 200.0, "risk": 0.5},
                {"price": 300.0, "risk": 0.9},
            ]
        }

        bands = calc._parse_risk_bands(data)

        assert len(bands) == 3
        assert bands[0].price == 100.0
        assert bands[0].risk_score == 0.1
        assert bands[2].risk_score == 0.9

    def test_parse_risk_bands_empty_table(self):
        """Empty risk table should return empty list."""
        from src.analysis.itc_risk import ITCRiskCalculator

        calc = ITCRiskCalculator(api_key="dummy")

        data = {"risk_table": []}
        bands = calc._parse_risk_bands(data)
        assert bands == []

        data = {}
        bands = calc._parse_risk_bands(data)
        assert bands == []

    def test_parse_risk_bands_skips_invalid_entries(self):
        """Invalid entries should be skipped, not raise."""
        from src.analysis.itc_risk import ITCRiskCalculator

        calc = ITCRiskCalculator(api_key="dummy")

        data = {
            "risk_table": [
                {"price": 100.0, "risk": 0.1},  # Valid
                {"price": None, "risk": 0.5},  # Invalid - no price
                {"price": -50.0, "risk": 0.3},  # Invalid - negative price
                {"price": 200.0, "risk": None},  # Invalid - no risk
                {"price": 300.0, "risk": 0.9},  # Valid
            ]
        }

        bands = calc._parse_risk_bands(data)

        assert len(bands) == 2
        assert bands[0].price == 100.0
        assert bands[1].price == 300.0

    def test_parse_risk_bands_clamps_risk_score(self):
        """Risk scores outside [0, 1] should be clamped."""
        from src.analysis.itc_risk import ITCRiskCalculator

        calc = ITCRiskCalculator(api_key="dummy")

        data = {
            "risk_table": [
                {"price": 100.0, "risk": -0.5},  # Below 0
                {"price": 200.0, "risk": 1.5},  # Above 1
            ]
        }

        bands = calc._parse_risk_bands(data)

        assert bands[0].risk_score == 0.0  # Clamped to 0
        assert bands[1].risk_score == 1.0  # Clamped to 1


class TestITCRiskResponse:
    """Tests for ITCRiskResponse model methods."""

    def test_get_nearest_bands(self):
        """get_nearest_bands should return bands closest to current price."""
        response = ITCRiskResponse(
            symbol="TSLA",
            universe="tradfi",
            current_price=450.0,
            current_risk_score=0.5,
            risk_bands=[
                RiskBand(price=100.0, risk_score=0.0),
                RiskBand(price=200.0, risk_score=0.2),
                RiskBand(price=400.0, risk_score=0.4),
                RiskBand(price=500.0, risk_score=0.6),
                RiskBand(price=600.0, risk_score=0.7),
                RiskBand(price=1000.0, risk_score=0.9),
            ],
            timestamp=datetime.now(),
        )

        nearest = response.get_nearest_bands(3)

        assert len(nearest) == 3
        # Should be 400, 500, and one other near 450
        prices = [b.price for b in nearest]
        assert 400.0 in prices
        assert 500.0 in prices

    def test_get_nearest_bands_no_current_price(self):
        """get_nearest_bands should return first n bands if no current price."""
        response = ITCRiskResponse(
            symbol="TSLA",
            universe="tradfi",
            current_price=None,
            current_risk_score=0.5,
            risk_bands=[
                RiskBand(price=100.0, risk_score=0.0),
                RiskBand(price=200.0, risk_score=0.2),
                RiskBand(price=300.0, risk_score=0.4),
            ],
            timestamp=datetime.now(),
        )

        nearest = response.get_nearest_bands(2)

        assert len(nearest) == 2
        assert nearest[0].price == 100.0
        assert nearest[1].price == 200.0

    def test_get_high_risk_threshold(self):
        """get_high_risk_threshold should return first band with risk >= 0.7."""
        response = ITCRiskResponse(
            symbol="TSLA",
            universe="tradfi",
            current_price=450.0,
            current_risk_score=0.5,
            risk_bands=[
                RiskBand(price=100.0, risk_score=0.0),
                RiskBand(price=500.0, risk_score=0.65),
                RiskBand(price=700.0, risk_score=0.72),  # First high risk
                RiskBand(price=1000.0, risk_score=0.9),
            ],
            timestamp=datetime.now(),
        )

        high_risk = response.get_high_risk_threshold()

        assert high_risk is not None
        assert high_risk.price == 700.0
        assert high_risk.risk_score == 0.72

    def test_get_high_risk_threshold_none_when_no_high_risk(self):
        """get_high_risk_threshold should return None if no high risk bands."""
        response = ITCRiskResponse(
            symbol="TSLA",
            universe="tradfi",
            current_price=450.0,
            current_risk_score=0.3,
            risk_bands=[
                RiskBand(price=100.0, risk_score=0.0),
                RiskBand(price=500.0, risk_score=0.5),
                RiskBand(price=700.0, risk_score=0.65),  # Still below 0.7
            ],
            timestamp=datetime.now(),
        )

        high_risk = response.get_high_risk_threshold()
        assert high_risk is None

    def test_get_risk_interpretation(self):
        """get_risk_interpretation should return correct interpretation."""
        # Low risk
        low_risk = ITCRiskResponse(
            symbol="TSLA",
            universe="tradfi",
            current_risk_score=0.2,
            risk_bands=[],
            timestamp=datetime.now(),
        )
        assert "LOW RISK" in low_risk.get_risk_interpretation()

        # Medium risk
        medium_risk = ITCRiskResponse(
            symbol="TSLA",
            universe="tradfi",
            current_risk_score=0.5,
            risk_bands=[],
            timestamp=datetime.now(),
        )
        assert "MEDIUM RISK" in medium_risk.get_risk_interpretation()

        # High risk
        high_risk = ITCRiskResponse(
            symbol="TSLA",
            universe="tradfi",
            current_risk_score=0.85,
            risk_bands=[],
            timestamp=datetime.now(),
        )
        assert "HIGH RISK" in high_risk.get_risk_interpretation()


class TestITCRiskCalculatorAPI:
    """Tests for API interaction (mocked)."""

    @patch("src.analysis.itc_risk.requests.get")
    def test_get_risk_score_success(self, mock_get):
        """Successful API call should return valid ITCRiskResponse."""
        from src.analysis.itc_risk import ITCRiskCalculator

        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "current_risk_score": 0.45,
            "risk_table": [
                {"price": 100.0, "risk": 0.1},
                {"price": 450.0, "risk": 0.45},
                {"price": 1000.0, "risk": 0.9},
            ],
        }
        mock_get.return_value = mock_response

        calc = ITCRiskCalculator(api_key="test_key")

        # Disable price enrichment for test
        result = calc.get_risk_score("TSLA", "tradfi", enrich_with_price=False)

        assert isinstance(result, ITCRiskResponse)
        assert result.symbol == "TSLA"
        assert result.universe == "tradfi"
        assert result.current_risk_score == 0.45
        assert len(result.risk_bands) == 3

    @patch("src.analysis.itc_risk.requests.get")
    def test_get_risk_score_validates_ticker_first(self, mock_get):
        """Unsupported ticker should fail before making API call."""
        from src.analysis.itc_risk import ITCRiskCalculator

        calc = ITCRiskCalculator(api_key="test_key")

        with pytest.raises(ValueError, match="PLTR not supported"):
            calc.get_risk_score("PLTR", "tradfi")

        # API should NOT have been called
        mock_get.assert_not_called()

    @patch("src.analysis.itc_risk.requests.get")
    @patch("src.analysis.itc_risk.time.sleep")
    def test_get_risk_score_retries_on_timeout(self, mock_sleep, mock_get):
        """Calculator should retry with backoff on timeout."""
        import requests

        from src.analysis.itc_risk import ITCRiskCalculator

        # First two calls timeout, third succeeds
        mock_get.side_effect = [
            requests.Timeout("Connection timed out"),
            requests.Timeout("Connection timed out"),
            MagicMock(
                status_code=200,
                json=lambda: {"current_risk_score": 0.5, "risk_table": []},
            ),
        ]

        calc = ITCRiskCalculator(api_key="test_key")
        result = calc.get_risk_score("TSLA", "tradfi", enrich_with_price=False)

        # Should have retried and eventually succeeded
        assert mock_get.call_count == 3
        assert result.current_risk_score == 0.5

    @patch("src.analysis.itc_risk.requests.get")
    def test_get_risk_score_handles_rate_limit(self, mock_get):
        """Calculator should handle 429 rate limit response."""
        import requests

        from src.analysis.itc_risk import ITCRiskCalculator

        # All calls return 429
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_get.return_value = mock_response

        calc = ITCRiskCalculator(api_key="test_key")

        with pytest.raises(requests.RequestException, match="rate limit exceeded"):
            calc.get_risk_score("TSLA", "tradfi", enrich_with_price=False, retry_count=2)


# Integration tests (require actual API key)
@pytest.mark.integration
class TestITCRiskCalculatorIntegration:
    """
    Integration tests that call the real ITC API.

    These tests require a valid ITC_API_KEY environment variable.
    Run with: uv run pytest tests/python/test_itc_risk.py -v -m integration
    """

    @pytest.fixture
    def api_key(self):
        """Get API key from environment."""
        key = os.environ.get("ITC_API_KEY")
        if not key:
            pytest.skip("ITC_API_KEY not set - skipping integration tests")
        return key

    def test_live_tsla_risk_score(self, api_key):
        """Integration test: Fetch TSLA risk from live API."""
        from src.analysis.itc_risk import ITCRiskCalculator

        calc = ITCRiskCalculator(api_key=api_key)
        result = calc.get_risk_score("TSLA", "tradfi")

        assert isinstance(result, ITCRiskResponse)
        assert result.symbol == "TSLA"
        assert 0 <= result.current_risk_score <= 1
        assert len(result.risk_bands) > 0

    def test_live_btc_risk_score(self, api_key):
        """Integration test: Fetch BTC risk from live API."""
        from src.analysis.itc_risk import ITCRiskCalculator

        calc = ITCRiskCalculator(api_key=api_key)
        result = calc.get_risk_score("BTC", "crypto", enrich_with_price=False)

        assert isinstance(result, ITCRiskResponse)
        assert result.symbol == "BTC"
        assert 0 <= result.current_risk_score <= 1
