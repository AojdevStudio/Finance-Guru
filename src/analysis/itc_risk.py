"""
ITC Risk Calculator for Finance Guru™

This module implements the calculator layer for ITC (Into The Cryptoverse)
Risk Models API integration.

ARCHITECTURE NOTE:
This is Layer 2 of our 3-layer architecture:
    Layer 1: Pydantic Models - Data validation (src/models/itc_risk_inputs.py)
    Layer 2: Calculator Classes (THIS FILE) - Business logic
    Layer 3: CLI Interface - Agent integration (src/analysis/itc_risk_cli.py)

EDUCATIONAL CONTEXT:
The ITCRiskCalculator handles:
- API communication with exponential backoff retry logic
- Response parsing and conversion to validated Pydantic models
- Current price enrichment from yfinance (for tradfi assets)
- Graceful error handling when API or external data unavailable

SUPPORTED ASSETS:
    TradFi (13): TSLA, AAPL, MSTR, NFLX, SP500, DXY, XAUUSD, XAGUSD, XPDUSD, PL, HG, NICKEL
    Crypto (29): BTC, ETH, BNB, SOL, XRP, ADA, DOGE, LINK, and 21 others

Author: Finance Guru™ Development Team
Created: 2026-01-09
"""

import os
import time
import warnings
from datetime import datetime
from typing import Optional, Dict, Any, List

import requests
import yfinance as yf

from src.models.itc_risk_inputs import ITCRiskRequest, ITCRiskResponse, RiskBand


class ITCRiskCalculator:
    """
    Calculator for ITC Risk Models API integration.

    WHAT: Fetches market-implied risk scores from Into The Cryptoverse
    WHY: Provides a "second opinion" on risk that complements internal metrics
    HOW: Makes authenticated API calls, parses responses, enriches with prices

    EDUCATIONAL CONTEXT:
    ITC Risk provides price-based risk scores (0-1) reflecting:
    - Market sentiment patterns
    - Historical price action
    - Technical risk levels

    This is NOT a replacement for VaR/Sharpe - it's complementary data.
    When ITC and internal metrics diverge, that's a signal to investigate.

    USAGE EXAMPLE:
        # Initialize calculator (uses ITC_API_KEY from environment)
        calculator = ITCRiskCalculator()

        # Get risk for a single ticker
        result = calculator.get_risk_score("TSLA", "tradfi")

        # Access results
        print(f"Risk Score: {result.current_risk_score:.2f}")
        print(f"Risk Level: {result.get_risk_interpretation()}")

        # Get nearest bands around current price
        for band in result.get_nearest_bands(5):
            print(f"${band.price:.2f}: {band.risk_score:.2f}")

    RETRY LOGIC:
        Uses exponential backoff (1s, 2s, 4s delays) for transient errors.
        After 3 failed attempts, raises exception for caller to handle.
    """

    # ITC Risk Models API base URL
    BASE_URL = "https://app.intothecryptoverse.com/api/v2"

    # Supported assets for each universe
    # NOTE: These are the ONLY assets ITC covers. For others, use risk_metrics_cli.py
    SUPPORTED_TRADFI: List[str] = [
        # Stocks (4)
        "TSLA", "AAPL", "MSTR", "NFLX",
        # Index (1)
        "SP500",
        # Currency (1)
        "DXY",
        # Commodities (7)
        "XAUUSD", "XAGUSD", "XPDUSD", "PL", "HG", "NICKEL",
    ]

    SUPPORTED_CRYPTO: List[str] = [
        # Major coins
        "BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "DOGE", "LINK",
        "AVAX", "DOT", "SHIB", "LTC", "AAVE", "ATOM", "POL", "ALGO",
        "HBAR", "RENDER", "VET", "TRX", "TON", "SUI", "XLM", "XMR",
        "XTZ", "SKY",
        # Meta metrics
        "BTC.D", "TOTAL", "TOTAL6",
    ]

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize calculator with API key.

        Args:
            api_key: ITC API key. If None, loads from ITC_API_KEY env var.

        Raises:
            ValueError: If API key not provided and not in environment.

        EDUCATIONAL NOTE:
        We require an API key because:
        1. ITC API is a paid service
        2. Rate limits are per-key (10 requests per window)
        3. No key = no access (unlike free APIs like yfinance)

        SECURITY NOTE:
        Never log or display the API key. It's stored securely in .env
        and loaded here via environment variable.
        """
        self.api_key = api_key or os.getenv("ITC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "ITC API key required. Set ITC_API_KEY in .env file.\n"
                "Get your key at: https://app.intothecryptoverse.com/api\n"
                "Example: Add 'ITC_API_KEY=your_key_here' to .env"
            )

    def validate_ticker(self, symbol: str, universe: str) -> None:
        """
        Validate ticker is supported by ITC API.

        Args:
            symbol: Ticker symbol (case-insensitive, will be normalized)
            universe: "crypto" or "tradfi"

        Raises:
            ValueError: If ticker not supported, with helpful message.

        EDUCATIONAL NOTE:
        ITC only covers a subset of assets. If you need risk analysis for
        unsupported tickers (PLTR, NVDA, GOOGL, etc.), use:
            uv run python src/analysis/risk_metrics_cli.py TICKER --days 90

        WHY FAIL FAST:
        We validate before making API calls to:
        1. Save rate limit quota
        2. Give user immediate feedback
        3. Provide clear guidance on alternatives
        """
        # Normalize symbol to uppercase
        symbol_upper = symbol.upper().strip()

        # Select correct supported list
        if universe == "crypto":
            supported = self.SUPPORTED_CRYPTO
        else:
            supported = self.SUPPORTED_TRADFI

        if symbol_upper not in supported:
            raise ValueError(
                f"{symbol_upper} not supported by ITC API.\n"
                f"Supported {universe} assets: {', '.join(sorted(supported))}\n\n"
                f"For unsupported tickers, use internal risk analysis:\n"
                f"  uv run python src/analysis/risk_metrics_cli.py {symbol_upper} --days 90"
            )

    def get_risk_score(
        self,
        symbol: str,
        universe: str,
        enrich_with_price: bool = True,
        retry_count: int = 3,
    ) -> ITCRiskResponse:
        """
        Fetch risk score and bands for a ticker.

        Args:
            symbol: Ticker symbol (e.g., TSLA, BTC)
            universe: "crypto" or "tradfi"
            enrich_with_price: If True, fetch current price from yfinance
            retry_count: Number of retry attempts for transient errors

        Returns:
            ITCRiskResponse with validated risk data

        Raises:
            ValueError: If ticker not supported
            requests.RequestException: If API call fails after all retries

        EDUCATIONAL NOTE:
        The retry logic uses exponential backoff:
        - Attempt 1: Immediate
        - Attempt 2: Wait 1 second
        - Attempt 3: Wait 2 seconds
        - Attempt 4: Wait 4 seconds (if configured)

        This pattern is standard for handling transient network errors
        and rate limiting without overwhelming the server.

        PRICE ENRICHMENT:
        For tradfi assets, we fetch the current market price from yfinance.
        This allows the output to show:
        - Current price context
        - Distance from high-risk zones
        - "← CURRENT" marker in risk band table

        Price enrichment is optional and fails gracefully (returns None).
        """
        # Normalize symbol to uppercase
        symbol_upper = symbol.upper().strip()

        # Validate ticker before making API call
        self.validate_ticker(symbol_upper, universe)

        # Build API request
        url = f"{self.BASE_URL}/risk-models/price-based/{universe}/{symbol_upper}"
        params = {
            "apikey": self.api_key,
            "format": "json",
        }

        # Retry logic with exponential backoff
        last_exception: Optional[Exception] = None
        for attempt in range(retry_count):
            try:
                # Make API request with timeout
                response = requests.get(url, params=params, timeout=10)

                # Handle HTTP errors
                if response.status_code == 429:
                    # Rate limit hit - log and retry
                    warnings.warn(
                        f"ITC API rate limit hit (attempt {attempt + 1}/{retry_count}). "
                        f"Retrying in {2 ** attempt} seconds..."
                    )
                    if attempt < retry_count - 1:
                        time.sleep(2 ** attempt)
                        continue
                    else:
                        raise requests.RequestException(
                            f"ITC API rate limit exceeded after {retry_count} attempts. "
                            "Try again in a few minutes."
                        )

                # Raise for other HTTP errors
                response.raise_for_status()

                # Parse JSON response
                data = response.json()
                break

            except requests.Timeout as e:
                last_exception = e
                warnings.warn(
                    f"ITC API timeout (attempt {attempt + 1}/{retry_count}). "
                    f"Retrying in {2 ** attempt} seconds..."
                )
                if attempt < retry_count - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise requests.RequestException(
                        f"ITC API timed out after {retry_count} attempts. "
                        "Check your network connection."
                    ) from e

            except requests.RequestException as e:
                last_exception = e
                # Network or HTTP error
                if attempt < retry_count - 1:
                    warnings.warn(
                        f"ITC API error (attempt {attempt + 1}/{retry_count}): {e}. "
                        f"Retrying in {2 ** attempt} seconds..."
                    )
                    time.sleep(2 ** attempt)
                else:
                    raise requests.RequestException(
                        f"Unable to reach ITC API after {retry_count} attempts: {e}\n"
                        "Use risk_metrics_cli.py for internal risk analysis."
                    ) from e

        # Parse risk bands from response
        risk_bands = self._parse_risk_bands(data)

        # Get current risk score
        current_risk = data.get("current_risk_score", 0.0)

        # Ensure current_risk is a valid float between 0 and 1
        try:
            current_risk = float(current_risk)
            current_risk = max(0.0, min(1.0, current_risk))  # Clamp to [0, 1]
        except (TypeError, ValueError):
            warnings.warn(
                f"Invalid current_risk_score from ITC API: {current_risk}. "
                "Defaulting to 0.0."
            )
            current_risk = 0.0

        # Enrich with current price from yfinance (tradfi only)
        current_price = None
        if enrich_with_price and universe == "tradfi":
            current_price = self._fetch_current_price(symbol_upper)

        # Build and return validated response
        return ITCRiskResponse(
            symbol=symbol_upper,
            universe=universe,
            current_price=current_price,
            current_risk_score=current_risk,
            risk_bands=risk_bands,
            timestamp=datetime.now(),
            source="Into The Cryptoverse API",
        )

    def get_all_risks(self, universe: str) -> Dict[str, Any]:
        """
        Get risk scores for all assets in a universe.

        Args:
            universe: "crypto" or "tradfi"

        Returns:
            Dict mapping symbols to current risk scores

        Raises:
            requests.RequestException: If API call fails

        EDUCATIONAL NOTE:
        This endpoint returns a summary of ALL assets in the universe.
        Useful for:
        - Portfolio-wide risk checks
        - Finding lowest/highest risk assets
        - Building heatmaps or dashboards

        Unlike get_risk_score(), this does NOT return detailed risk bands.
        For full analysis of a specific ticker, use get_risk_score().
        """
        url = f"{self.BASE_URL}/risk-models/price-based/{universe}"
        params = {"apikey": self.api_key}

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        return response.json()

    def _parse_risk_bands(self, data: Dict[str, Any]) -> List[RiskBand]:
        """
        Parse risk bands from ITC API response.

        Args:
            data: Raw JSON response from ITC API

        Returns:
            List of validated RiskBand objects

        EDUCATIONAL NOTE:
        The ITC API returns a "risk_table" array with objects like:
            {"price": 450.15, "risk": 0.489}

        We convert these to Pydantic RiskBand models for:
        1. Type safety
        2. Validation (price > 0, risk in [0, 1])
        3. Consistent interface across the codebase
        """
        risk_table = data.get("risk_table", [])

        risk_bands = []
        for entry in risk_table:
            try:
                price = entry.get("price")
                risk_score = entry.get("risk")

                # Skip invalid entries
                if price is None or risk_score is None:
                    continue

                # Convert to floats
                price = float(price)
                risk_score = float(risk_score)

                # Validate price is positive
                if price <= 0:
                    continue

                # Clamp risk score to [0, 1]
                risk_score = max(0.0, min(1.0, risk_score))

                risk_bands.append(RiskBand(price=price, risk_score=risk_score))

            except (TypeError, ValueError) as e:
                # Skip malformed entries, log warning
                warnings.warn(f"Skipping invalid risk band entry: {entry}. Error: {e}")
                continue

        # Sort by price ascending
        risk_bands.sort(key=lambda b: b.price)

        return risk_bands

    def _fetch_current_price(self, symbol: str) -> Optional[float]:
        """
        Fetch current market price from yfinance.

        Args:
            symbol: Ticker symbol (uppercase)

        Returns:
            Current price as float, or None if unavailable

        EDUCATIONAL NOTE:
        yfinance provides free access to Yahoo Finance data.
        We use it to enrich ITC risk data with current prices.

        GRACEFUL DEGRADATION:
        If yfinance fails (network error, unsupported ticker, etc.),
        we return None and continue. The risk score is still valid;
        we just won't have the price context.

        WHY USE YFINANCE:
        - Free (no API key required)
        - Fast (usually < 1 second)
        - Reliable for major US stocks
        - Already in our dependencies
        """
        try:
            ticker_obj = yf.Ticker(symbol)

            # Try multiple price fields (different availability)
            info = ticker_obj.info
            price = info.get("currentPrice")
            if price is None:
                price = info.get("regularMarketPrice")
            if price is None:
                price = info.get("previousClose")

            if price is not None:
                return float(price)

        except Exception as e:
            # Fail gracefully - price enrichment is optional
            warnings.warn(
                f"Could not fetch current price for {symbol} from yfinance: {e}. "
                "Risk data will be displayed without current price context."
            )

        return None

    def is_ticker_supported(self, symbol: str, universe: str) -> bool:
        """
        Check if a ticker is supported without raising an exception.

        Args:
            symbol: Ticker symbol (case-insensitive)
            universe: "crypto" or "tradfi"

        Returns:
            True if supported, False otherwise

        USAGE:
            if calculator.is_ticker_supported("TSLA", "tradfi"):
                result = calculator.get_risk_score("TSLA", "tradfi")
            else:
                print("Use risk_metrics_cli.py instead")
        """
        symbol_upper = symbol.upper().strip()
        if universe == "crypto":
            return symbol_upper in self.SUPPORTED_CRYPTO
        else:
            return symbol_upper in self.SUPPORTED_TRADFI

    def get_supported_tickers(self, universe: str) -> List[str]:
        """
        Get list of supported tickers for a universe.

        Args:
            universe: "crypto" or "tradfi"

        Returns:
            List of supported ticker symbols (sorted alphabetically)
        """
        if universe == "crypto":
            return sorted(self.SUPPORTED_CRYPTO)
        else:
            return sorted(self.SUPPORTED_TRADFI)


# Type exports for convenience
__all__ = [
    "ITCRiskCalculator",
]
