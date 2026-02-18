#!/usr/bin/env python3
"""
CLI interface for volatility metrics calculator.

WHAT: Command-line tool for Finance Guru agents to calculate volatility indicators
WHY: Simple interface for Compliance Officer, Margin Specialist, and Risk Assessment workflows
ARCHITECTURE: Layer 3 of 3-layer type-safe architecture

USAGE:
    # Quick volatility scan (all indicators with defaults)
    uv run python src/utils/volatility_cli.py TSLA --days 90

    # Real-time volatility with Finnhub (RECOMMENDED for live analysis!)
    uv run python src/utils/volatility_cli.py TSLA --days 90 --realtime

    # Custom Bollinger Bands settings
    uv run python src/utils/volatility_cli.py TSLA --days 90 --bb-period 14 --bb-std 2.5

    # Custom ATR period with real-time data
    uv run python src/utils/volatility_cli.py TSLA --days 90 --atr-period 20 --realtime

    # JSON output for programmatic use
    uv run python src/utils/volatility_cli.py TSLA --days 90 --output json

    # Portfolio volatility comparison (real-time!)
    for ticker in TSLA PLTR NVDA; do
        uv run python src/utils/volatility_cli.py $ticker --days 90 --realtime
    done

AGENT USE CASES:
- Compliance Officer: Calculate position limits based on volatility regime
- Margin Specialist: Determine safe leverage ratios using ATR
- Market Researcher: Quick volatility scan for opportunity assessment
- Strategy Advisor: Compare volatility across portfolio holdings
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import yfinance as yf

from src.models.volatility_inputs import (
    VolatilityConfig,
    VolatilityDataInput,
)
from src.utils.market_data import get_prices  # Finnhub integration
from src.utils.volatility import calculate_volatility


def fetch_price_data(
    ticker: str, days: int, realtime: bool = False
) -> VolatilityDataInput:
    """
    Fetch OHLC price data from yfinance, optionally with real-time Finnhub data.

    EDUCATIONAL NOTE:
    We need High, Low, and Close prices (not just Close) because:
    - ATR uses the full daily range (high to low)
    - Keltner Channels need ATR
    - More complete picture of intraday volatility

    Args:
        ticker: Stock symbol
        days: Number of days of historical data
        realtime: If True, append current intraday price from Finnhub (default: False)

    Returns:
        VolatilityDataInput with OHLC data

    Raises:
        ValueError: If data cannot be fetched or is insufficient
    """
    # Fetch extra days to account for weekends/holidays
    # Need ~1.5x calendar days to get requested trading days (accounts for weekends/holidays)
    start_date = datetime.now() - timedelta(days=int(days * 1.5))
    end_date = datetime.now()

    stock = yf.Ticker(ticker)
    hist = stock.history(start=start_date, end=end_date)

    if hist.empty:
        raise ValueError(f"No data found for ticker {ticker}")

    # Take only the requested number of trading days
    hist = hist.tail(days)

    if len(hist) < 20:
        raise ValueError(
            f"Insufficient data for {ticker}. Need at least 20 days, got {len(hist)}"
        )

    # Extract OHLC data
    dates_list = [d.date() for d in hist.index]
    high_list = hist["High"].tolist()
    low_list = hist["Low"].tolist()
    close_list = hist["Close"].tolist()

    # FINNHUB INTEGRATION: Append real-time intraday price if requested
    if realtime:
        try:
            # Get real-time price from Finnhub
            rt_data = get_prices(ticker, realtime=True)
            if ticker.upper() in rt_data:
                price_data = rt_data[ticker.upper()]
                current_price = price_data.price
                # Append today's date and current price to the data
                # For volatility, we use current price for all OHLC values (conservative)
                from datetime import date

                dates_list.append(date.today())
                high_list.append(current_price)
                low_list.append(current_price)
                close_list.append(current_price)
                print(
                    f"✅ Real-time price appended: ${current_price:.2f} (Finnhub)",
                    file=sys.stderr,
                )
        except Exception as e:
            print(
                f"⚠️  Real-time price unavailable, using EOD data only: {e}",
                file=sys.stderr,
            )

    # Convert to VolatilityDataInput
    return VolatilityDataInput(
        ticker=ticker.upper(),
        dates=dates_list,
        high=high_list,
        low=low_list,
        close=close_list,
    )


def format_human_output(result) -> str:
    """
    Format volatility metrics for human-readable display.

    EDUCATIONAL NOTE:
    This output is designed to give agents (and you) a quick visual assessment
    of volatility conditions. Each section provides actionable information:
    - ATR for stop-loss sizing
    - Bollinger Bands for position relative to volatility channels
    - Regime for overall risk assessment

    Args:
        result: VolatilityMetricsOutput

    Returns:
        Formatted string output
    """
    lines = []
    lines.append(f"\n{'=' * 60}")
    lines.append(f"VOLATILITY ANALYSIS: {result.ticker}")
    lines.append(f"Date: {result.calculation_date}")
    lines.append(f"Current Price: ${result.current_price:.2f}")
    lines.append(f"{'=' * 60}\n")

    # Volatility Regime (most important summary)
    regime_emoji = {"low": "🟢", "normal": "🔵", "high": "🟡", "extreme": "🔴"}
    emoji = regime_emoji.get(result.volatility_regime, "⚪")
    lines.append(f"VOLATILITY REGIME: {emoji} {result.volatility_regime.upper()}")
    lines.append("")

    # Position sizing guidance based on regime
    position_guidance = {
        "low": "Can use larger positions (10-20% of portfolio)",
        "normal": "Standard position sizing (5-10% of portfolio)",
        "high": "Reduce position sizes (2-5% of portfolio)",
        "extreme": "Maximum caution (1-2% or stay in cash)",
    }
    lines.append(f"💡 Position Sizing: {position_guidance[result.volatility_regime]}")
    lines.append("")

    # ATR (for stop-loss calculation)
    lines.append("AVERAGE TRUE RANGE (ATR)")
    lines.append(f"  ATR Value: ${result.atr.atr:.2f}")
    lines.append(f"  ATR %: {result.atr.atr_percent:.2f}%")
    lines.append(f"  💡 Suggested Stop Loss: 2× ATR = ${result.atr.atr * 2:.2f}")
    lines.append("")

    # Historical Volatility
    lines.append("HISTORICAL VOLATILITY")
    lines.append(f"  Daily Vol: {result.historical_volatility.daily_volatility:.4f}")
    lines.append(
        f"  Annual Vol: {result.historical_volatility.annual_volatility * 100:.2f}%"
    )
    lines.append("")

    # Bollinger Bands
    bb = result.bollinger_bands
    lines.append("BOLLINGER BANDS")
    lines.append(f"  Upper Band: ${bb.upper_band:.2f}")
    lines.append(f"  Middle Band: ${bb.middle_band:.2f}")
    lines.append(f"  Lower Band: ${bb.lower_band:.2f}")
    lines.append(f"  %B: {bb.percent_b:.3f}")
    lines.append(f"  Bandwidth: {bb.bandwidth:.2f}%")

    # %B interpretation
    if bb.percent_b > 1.0:
        lines.append("  📊 Price above upper band (strong momentum or overbought)")
    elif bb.percent_b > 0.8:
        lines.append("  📊 Price near upper band (approaching resistance)")
    elif bb.percent_b < 0.0:
        lines.append("  📊 Price below lower band (weak momentum or oversold)")
    elif bb.percent_b < 0.2:
        lines.append("  📊 Price near lower band (approaching support)")
    else:
        lines.append("  📊 Price within normal range")

    # Bandwidth interpretation
    if bb.bandwidth < 10:
        lines.append("  🎯 Narrow bands - potential breakout setup ('the squeeze')")
    elif bb.bandwidth > 30:
        lines.append("  🎯 Wide bands - high volatility environment")

    lines.append("")

    # Keltner Channels
    kc = result.keltner_channels
    lines.append("KELTNER CHANNELS")
    lines.append(f"  Upper Channel: ${kc.upper_channel:.2f}")
    lines.append(f"  Middle Line: ${kc.middle_line:.2f}")
    lines.append(f"  Lower Channel: ${kc.lower_channel:.2f}")

    # Comparison with Bollinger Bands
    if result.current_price > bb.upper_band and result.current_price > kc.upper_channel:
        lines.append("  🔥 Price outside BOTH indicators - EXTREME move")
    elif result.current_price > bb.upper_band:
        lines.append("  ⚠️  Price outside Bollinger but inside Keltner - Strong move")

    lines.append(f"\n{'=' * 60}\n")

    return "\n".join(lines)


def format_json_output(result) -> str:
    """
    Format volatility metrics as JSON.

    Args:
        result: VolatilityMetricsOutput

    Returns:
        JSON string
    """
    # Convert Pydantic model to dict, then to JSON
    return json.dumps(result.model_dump(), indent=2, default=str)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Calculate volatility metrics for Finance Guru agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick volatility scan
  uv run python src/utils/volatility_cli.py TSLA --days 90

  # Custom Bollinger Bands settings
  uv run python src/utils/volatility_cli.py TSLA --days 90 --bb-period 14 --bb-std 2.5

  # JSON output for programmatic use
  uv run python src/utils/volatility_cli.py TSLA --days 90 --output json

  # Portfolio comparison
  for ticker in TSLA PLTR NVDA; do
      uv run python src/utils/volatility_cli.py $ticker --days 90
  done

Agent Use Cases:
  - Compliance Officer: Position limits based on volatility regime
  - Margin Specialist: Leverage ratios using ATR
  - Strategy Advisor: Volatility comparison across holdings
        """,
    )

    # Required arguments
    parser.add_argument(
        "ticker", type=str, help="Stock ticker symbol (e.g., TSLA, AAPL, SPY)"
    )

    parser.add_argument(
        "--days",
        type=int,
        default=90,
        help="Number of days of historical data (default: 90)",
    )

    parser.add_argument(
        "--realtime",
        action="store_true",
        help="Append current intraday price from Finnhub for real-time volatility analysis",
    )

    # Bollinger Bands configuration
    parser.add_argument(
        "--bb-period", type=int, default=20, help="Bollinger Bands period (default: 20)"
    )

    parser.add_argument(
        "--bb-std",
        type=float,
        default=2.0,
        help="Bollinger Bands standard deviation multiplier (default: 2.0)",
    )

    # ATR configuration
    parser.add_argument(
        "--atr-period", type=int, default=14, help="ATR period (default: 14)"
    )

    # Historical volatility configuration
    parser.add_argument(
        "--hvol-period",
        type=int,
        default=20,
        help="Historical volatility lookback period (default: 20)",
    )

    # Keltner Channels configuration
    parser.add_argument(
        "--kc-period",
        type=int,
        default=20,
        help="Keltner Channels EMA period (default: 20)",
    )

    parser.add_argument(
        "--kc-atr-mult",
        type=float,
        default=2.0,
        help="Keltner Channels ATR multiplier (default: 2.0)",
    )

    # Output format
    parser.add_argument(
        "--output",
        choices=["human", "json"],
        default="human",
        help="Output format (default: human)",
    )

    args = parser.parse_args()

    try:
        # Fetch price data
        data_source = (
            "real-time (Finnhub + yfinance)"
            if args.realtime
            else "end-of-day (yfinance)"
        )
        print(
            f"Fetching {args.days} days of price data for {args.ticker} ({data_source})...",
            file=sys.stderr,
        )
        data = fetch_price_data(args.ticker, args.days, realtime=args.realtime)

        # Create configuration
        config = VolatilityConfig(
            bb_period=args.bb_period,
            bb_std_dev=args.bb_std,
            atr_period=args.atr_period,
            hvol_period=args.hvol_period,
            kc_period=args.kc_period,
            kc_atr_multiplier=args.kc_atr_mult,
        )

        # Calculate volatility metrics
        print("Calculating volatility metrics...", file=sys.stderr)
        result = calculate_volatility(data, config)

        # Output results
        if args.output == "json":
            print(format_json_output(result))
        else:
            print(format_human_output(result))

        return 0

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc(file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
