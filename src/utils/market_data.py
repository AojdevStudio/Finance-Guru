"""Market Data Utility Module
Provides real-time and end-of-day stock price data for Finance Guru system.

USAGE:
    # End-of-day data (yfinance - free, always works)
    uv run python src/utils/market_data.py TSLA

    # Real-time data (Finnhub - 60 calls/min, unlimited!)
    uv run python src/utils/market_data.py TSLA --realtime

    # Multiple tickers (60/min rate limit - entire portfolio in seconds!)
    uv run python src/utils/market_data.py TSLA PLTR NVDA --realtime
"""

import argparse
import os
from datetime import datetime
from typing import Any

import requests
import yfinance as yf
from dotenv import load_dotenv
from pydantic import BaseModel

# Load environment variables from .env file
load_dotenv()


class PriceData(BaseModel):
    """Market price data for a single security."""

    symbol: str
    price: float
    change: float
    change_percent: float
    timestamp: str
    source: str = "yfinance"  # Track data source


def get_prices(
    symbols: str | list[str], realtime: bool = False
) -> dict[str, PriceData]:
    """Get current prices for one or more stock symbols.

    Unified function handling both single and multiple tickers.
    Supports both yfinance (free, end-of-day) and Finnhub (free, real-time, 60/min).

    Args:
        symbols: Single ticker symbol (str) or list of ticker symbols
        realtime: If True, use Polygon.io API for real-time data during market hours
                  If False (default), use yfinance for end-of-day data

    Returns:
        Dict mapping symbols to their PriceData objects

    Examples:
        >>> get_prices("TSLA")  # Single ticker, end-of-day
        {'TSLA': PriceData(...)}

        >>> get_prices(["TSLA", "PLTR"], realtime=True)  # Multiple, real-time
        {'TSLA': PriceData(...), 'PLTR': PriceData(...)}
    """
    # Normalize input to list
    if isinstance(symbols, str):
        symbols = [symbols]

    if realtime:
        return _get_prices_polygon(symbols)
    else:
        return _get_prices_yfinance(symbols)


def _get_prices_yfinance(symbols: list[str]) -> dict[str, PriceData]:
    """Get prices using yfinance (free, end-of-day data)."""
    results = {}

    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            current_price = info.get("currentPrice") or info.get(
                "regularMarketPrice", 0
            )
            previous_close = info.get("previousClose", 0)
            change = current_price - previous_close
            change_percent = (change / previous_close * 100) if previous_close else 0

            results[symbol.upper()] = PriceData(
                symbol=symbol.upper(),
                price=round(current_price, 2),
                change=round(change, 2),
                change_percent=round(change_percent, 2),
                timestamp=datetime.now().isoformat(),
                source="yfinance",
            )
        except Exception as e:
            print(f"⚠️  Error fetching {symbol} from yfinance: {e}")
            continue

    return results


def _get_prices_polygon(symbols: list[str]) -> dict[str, PriceData]:
    """Get prices using Finnhub API (60 calls/min, unlimited daily!)."""
    api_key = os.getenv("FINNHUB_API_KEY")

    if not api_key or api_key == "your_finnhub_api_key_here":
        print("⚠️  FINNHUB_API_KEY not configured in .env - falling back to yfinance")
        return _get_prices_yfinance(symbols)

    results = {}

    for symbol in symbols:
        try:
            # Finnhub quote endpoint (real-time data, 60 calls/min!)
            url = "https://finnhub.io/api/v1/quote"
            params = {"symbol": symbol.upper(), "token": api_key}

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            # Check for API error
            if "error" in data:
                raise ValueError(f"Finnhub error: {data['error']}")

            # Finnhub returns empty dict {} for invalid symbols
            if not data or data.get("c") == 0:
                raise ValueError(f"No quote data returned for {symbol}")

            # Finnhub quote structure
            # c = current price, d = change, dp = change percent
            # h = high, l = low, o = open, pc = previous close
            current_price = float(data.get("c", 0))
            change = float(data.get("d", 0))
            change_percent = float(data.get("dp", 0))

            results[symbol.upper()] = PriceData(
                symbol=symbol.upper(),
                price=round(current_price, 2),
                change=round(change, 2),
                change_percent=round(change_percent, 2),
                timestamp=datetime.now().isoformat(),
                source="finnhub",
            )

        except requests.exceptions.RequestException as e:
            print(f"⚠️  Network error fetching {symbol} from Finnhub: {e}")
            print(f"   Falling back to yfinance for {symbol}")
            fallback = _get_prices_yfinance([symbol])
            if fallback:
                results.update(fallback)
        except Exception as e:
            print(f"⚠️  Error fetching {symbol} from Finnhub: {e}")
            print(f"   Falling back to yfinance for {symbol}")
            fallback = _get_prices_yfinance([symbol])
            if fallback:
                results.update(fallback)

    return results


def get_option_chain(symbol: str, expiration: str | None = None) -> dict[str, Any]:
    """Get option chain data for a symbol.

    Args:
        symbol: Stock ticker symbol
        expiration: Expiration date (YYYY-MM-DD), or None for nearest expiration

    Returns:
        Dict with calls and puts data
    """
    ticker = yf.Ticker(symbol)

    if expiration is None:
        expiration = ticker.options[0]  # Get nearest expiration

    opt = ticker.option_chain(expiration)

    return {
        "expiration": expiration,
        "calls": opt.calls.to_dict("records"),
        "puts": opt.puts.to_dict("records"),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Finance Guru™ Market Data Utility - Get stock prices",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single ticker, end-of-day data (yfinance)
  uv run python src/utils/market_data.py TSLA

  # Multiple tickers, end-of-day data
  uv run python src/utils/market_data.py TSLA PLTR NVDA

  # Real-time data (Finnhub - FREE, 60 calls/min!)
  uv run python src/utils/market_data.py TSLA --realtime

  # Multiple tickers, real-time (60/min - scan entire portfolio fast!)
  uv run python src/utils/market_data.py TSLA PLTR NVDA --realtime

  # Entire portfolio scan (15-20 tickers in ~20 seconds!)
  uv run python src/utils/market_data.py PLTR TSLA COIN NVDA AAPL GOOGL VOO JEPI JEPQ --realtime
        """,
    )

    parser.add_argument(
        "symbols", nargs="+", help="Stock ticker symbols (e.g., TSLA PLTR NVDA)"
    )

    parser.add_argument(
        "--realtime",
        action="store_true",
        help="Use Finnhub API for real-time data (requires FINNHUB_API_KEY in .env, 60 calls/min!)",
    )

    args = parser.parse_args()

    # Fetch prices
    print(f"\n{'=' * 60}")
    if args.realtime:
        print("📊 REAL-TIME MARKET DATA (Finnhub - 60 calls/min)")
    else:
        print("📊 END-OF-DAY MARKET DATA (yfinance)")
    print(f"{'=' * 60}\n")

    data = get_prices(args.symbols, realtime=args.realtime)

    if not data:
        print("❌ No data retrieved. Check ticker symbols and try again.")
        exit(1)

    # Display results
    for symbol, price_info in data.items():
        source_label = f"[{price_info.source.upper()}]"
        change_symbol = "📈" if price_info.change >= 0 else "📉"

        print(
            f"{change_symbol} {source_label:15} {symbol:6} ${price_info.price:8.2f} "
            f"({price_info.change:+7.2f}, {price_info.change_percent:+6.2f}%)"
        )

    print(f"\n{'=' * 60}")
    print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %I:%M:%S %p %Z')}")
    print(f"{'=' * 60}\n")
