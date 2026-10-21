#!/usr/bin/env python3
"""
Moving Average CLI for Finance Guru™ Agents

This module provides a command-line interface for calculating moving averages.
Designed for easy integration with Finance Guru agents.

ARCHITECTURE NOTE:
This is Layer 3 of our 3-layer architecture:
    Layer 1: Pydantic Models - Data validation
    Layer 2: Calculator Classes - Business logic
    Layer 3: CLI Interface (THIS FILE) - Agent integration

AGENT USAGE:
    # Single MA calculation
    uv run python -m src.utils.moving_averages_cli TSLA --days 200 --ma-type SMA --period 50

    # Real-time MA with Finnhub (RECOMMENDED for live trend analysis!)
    uv run python -m src.utils.moving_averages_cli TSLA --days 200 --ma-type SMA --period 50 --realtime

    # Crossover detection (50/200 Golden Cross) - real-time!
    uv run python -m src.utils.moving_averages_cli TSLA --days 252 --fast 50 --slow 200 --realtime

    # Multiple MA types comparison
    uv run python -m src.utils.moving_averages_cli TSLA --days 200 \\
        --ma-type SMA --period 20 \\
        --secondary-ma-type EMA --secondary-period 50

    # EMA crossover with real-time data
    uv run python -m src.utils.moving_averages_cli TSLA --days 252 \\
        --ma-type EMA --fast 12 --slow 26 --realtime

    # JSON output
    uv run python -m src.utils.moving_averages_cli TSLA --days 200 --ma-type SMA --period 50 --output json

    # Save to file
    uv run python -m src.utils.moving_averages_cli TSLA --days 252 --fast 50 --slow 200 \\
        --output json \\
        --save-to analysis/tsla-golden-cross-2025-10-13.json

EDUCATIONAL NOTE:
Moving averages help identify trends and generate trading signals:
- Single MA: Trend direction (price above/below MA)
- Crossovers: Entry/exit signals (Golden Cross = bullish, Death Cross = bearish)
- Support/Resistance: MAs act as dynamic price levels

Author: Finance Guru™ Development Team
Created: 2025-10-13
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import assert_never

from src.models.moving_avg_inputs import (
    DEFAULT_MA_PERIOD,
    MovingAverageAnalysis,
    MovingAverageConfig,
    MovingAverageDataInput,
)
from src.utils.market_data import append_live_quote
from src.utils.moving_averages import MovingAverageCalculator
from src.utils.trading_calendar import calendar_days_for


def fetch_ma_data(
    ticker: str, days: int, realtime: bool = False
) -> MovingAverageDataInput:
    """
    Fetch historical price data for MA calculations, optionally with real-time Finnhub data.

    Args:
        ticker: Stock ticker symbol
        days: Number of days of historical data
        realtime: If True, append current intraday price from Finnhub (default: False)

    Returns:
        MovingAverageDataInput: Validated price data

    Raises:
        ValueError: If unable to fetch data or insufficient data points
    """
    try:
        import yfinance as yf

        end_date = date.today()
        start_date = end_date - timedelta(days=calendar_days_for(days))

        ticker_obj = yf.Ticker(ticker)
        hist = ticker_obj.history(start=start_date, end=end_date)

        if hist.empty:
            raise ValueError(f"No data found for ticker {ticker}")

        dates_list = [d.date() for d in hist.index]
        prices_list = hist["Close"].tolist()

        if realtime:
            append_live_quote(ticker, dates_list, prices_list)

        if len(dates_list) < DEFAULT_MA_PERIOD:
            raise ValueError(
                f"Insufficient data: got {len(dates_list)} days, need at least {DEFAULT_MA_PERIOD}. "
                "Try increasing --days parameter."
            )

        return MovingAverageDataInput(
            ticker=ticker.upper(),
            dates=dates_list,
            prices=prices_list,
        )

    except ImportError as e:
        raise ImportError("yfinance not installed. Run: uv add yfinance") from e
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Failed to fetch data for {ticker}: {e}") from e


def format_single_ma_output(analysis: MovingAverageAnalysis) -> str:
    """Format single MA results for human reading."""
    ma = analysis.primary_ma
    if ma.current_value is None:
        raise ValueError("Moving average is unavailable for this lookback")
    output = []

    output.append("=" * 70)
    output.append(f"📈 MOVING AVERAGE ANALYSIS: {ma.ticker}")
    output.append(f"📅 Data Through: {ma.calculation_date} (most recent market close)")
    output.append("=" * 70)
    output.append("")

    output.append(f"📊 {ma.ma_type} ({ma.period}-DAY)")
    output.append("-" * 70)
    output.append(f"  Current Price:            ${ma.current_price:>12,.2f}")
    output.append(f"  Current MA:               ${ma.current_value:>12,.2f}")
    output.append(f"  Price vs MA:              {ma.price_vs_ma:>12}")
    output.append("")

    pct_diff = ((ma.current_price - ma.current_value) / ma.current_value) * 100

    if ma.price_vs_ma == "ABOVE":
        output.append(
            f"  🟢 BULLISH: Price is {pct_diff:.2f}% above {ma.ma_type}({ma.period})"
        )
        output.append("     → Uptrend confirmed")
        output.append("     → MA acting as support level")
        output.append("     → Consider long positions or hold")
    elif ma.price_vs_ma == "BELOW":
        output.append(
            f"  🔴 BEARISH: Price is {abs(pct_diff):.2f}% below {ma.ma_type}({ma.period})"
        )
        output.append("     → Downtrend confirmed")
        output.append("     → MA acting as resistance level")
        output.append("     → Consider short positions or exit longs")
    else:
        output.append("  ⚪ NEUTRAL: Price at MA level")
        output.append("     → Price testing MA support/resistance")
        output.append("     → Watch for breakout direction")
        output.append("     → Wait for confirmation before trading")

    output.append("")

    output.append("💡 MA CHARACTERISTICS")
    output.append("-" * 70)
    match ma.ma_type:
        case "SMA":
            output.append("  Type: Simple Moving Average")
            output.append("  → Equal weight to all prices in period")
            output.append("  → Most widely used and understood")
            output.append("  → Good for identifying clear trends")
            output.append("  → Can lag in fast-moving markets")
        case "EMA":
            output.append("  Type: Exponential Moving Average")
            output.append("  → More weight to recent prices")
            output.append("  → Responds faster to price changes")
            output.append("  → Popular among day traders")
            output.append("  → Can generate more false signals")
        case "WMA":
            output.append("  Type: Weighted Moving Average")
            output.append("  → Linear increasing weights")
            output.append("  → Balances responsiveness and smoothness")
            output.append("  → Good for swing trading")
            output.append("  → Less common than SMA/EMA")
        case "HMA":
            output.append("  Type: Hull Moving Average")
            output.append("  → Minimal lag with maximum smoothness")
            output.append("  → Best trend indicator for fast markets")
            output.append("  → Excellent for dynamic support/resistance")
            output.append("  → Most advanced MA calculation")
        case _:
            assert_never(ma.ma_type)

    output.append("")
    output.append("=" * 70)
    output.append(
        "⚠️  DISCLAIMER: For educational purposes only. Not investment advice."
    )
    output.append("=" * 70)

    return "\n".join(output)


def format_crossover_output(analysis: MovingAverageAnalysis) -> str:  # noqa: C901
    """Format crossover analysis for human reading."""
    if not analysis.crossover_analysis:
        return format_single_ma_output(analysis)

    cross = analysis.crossover_analysis
    output = []

    output.append("=" * 70)
    output.append(f"📊 MA CROSSOVER ANALYSIS: {cross.ticker}")
    output.append(
        f"📅 Data Through: {cross.calculation_date} (most recent market close)"
    )
    output.append("=" * 70)
    output.append("")

    output.append("📈 CURRENT MOVING AVERAGES")
    output.append("-" * 70)
    output.append(
        f"  Fast MA ({cross.fast_ma_type} {cross.fast_period}):    ${cross.fast_value:>12,.2f}"
    )
    output.append(
        f"  Slow MA ({cross.slow_ma_type} {cross.slow_period}):   ${cross.slow_value:>12,.2f}"
    )
    output.append(
        f"  Current Price:            ${analysis.primary_ma.current_price:>12,.2f}"
    )
    output.append("")

    output.append("🎯 CROSSOVER SIGNAL")
    output.append("-" * 70)

    if cross.current_signal == "BULLISH":
        output.append("  Signal:                   🟢 BULLISH")
        output.append(
            f"  Fast MA > Slow MA:        Fast is {((cross.fast_value / cross.slow_value - 1) * 100):.2f}% above slow"
        )
    elif cross.current_signal == "BEARISH":
        output.append("  Signal:                   🔴 BEARISH")
        output.append(
            f"  Fast MA < Slow MA:        Fast is {((1 - cross.fast_value / cross.slow_value) * 100):.2f}% below slow"
        )
    else:
        output.append("  Signal:                   ⚪ NEUTRAL")
        output.append("  Fast MA ≈ Slow MA:        MAs converging")

    output.append("")

    if cross.last_crossover_date:
        output.append("📅 LAST CROSSOVER")
        output.append("-" * 70)
        output.append(f"  Date:                     {cross.last_crossover_date}")
        output.append(f"  Days Ago:                 {cross.days_since_crossover} days")

        if cross.crossover_type == "GOLDEN_CROSS":
            output.append("  Type:                     ✨ GOLDEN CROSS")
            output.append("")
            output.append("  💡 INTERPRETATION:")
            output.append("     → Bullish signal: 50-day SMA crossed above 200-day SMA")
            output.append("     → Indicates potential start of bull market")
            output.append("     → Most reliable after extended downtrend")
            output.append("     → Confirm with volume increase and other indicators")
        elif cross.crossover_type == "DEATH_CROSS":
            output.append("  Type:                     ☠️  DEATH CROSS")
            output.append("")
            output.append("  💡 INTERPRETATION:")
            output.append("     → Bearish signal: 50-day SMA crossed below 200-day SMA")
            output.append("     → Indicates potential start of bear market")
            output.append("     → Most reliable after extended uptrend")
            output.append("     → Consider protective measures or exit positions")
        else:
            output.append("  Type:                     Standard Crossover")
            output.append("")
            output.append("  💡 INTERPRETATION:")
            if cross.current_signal == "BULLISH":
                output.append("     → Bullish crossover occurred")
                output.append("     → Consider long positions or hold")
                output.append("     → Watch for trend confirmation")
            else:
                output.append("     → Bearish crossover occurred")
                output.append("     → Consider short positions or exit longs")
                output.append("     → Watch for trend confirmation")

        output.append("")
        if cross.days_since_crossover is None:
            raise ValueError("A crossover date requires its age in days")
        if cross.days_since_crossover <= 5:
            output.append(
                f"  🔥 FRESH SIGNAL: Crossover just {cross.days_since_crossover} days ago - signal very recent!"
            )
        elif cross.days_since_crossover <= 20:
            output.append(
                f"  ✅ RECENT SIGNAL: Crossover {cross.days_since_crossover} days ago - signal still valid"
            )
        elif cross.days_since_crossover <= 60:
            output.append(
                f"  ⏳ AGING SIGNAL: Crossover {cross.days_since_crossover} days ago - trend maturing"
            )
        else:
            output.append(
                f"  ⚠️  OLD SIGNAL: Crossover {cross.days_since_crossover} days ago - watch for new crossover"
            )

    else:
        output.append("📅 CROSSOVER HISTORY")
        output.append("-" * 70)
        output.append("  No crossover detected in available data")
        output.append("  → MAs have maintained current relationship throughout period")
        if cross.current_signal == "BULLISH":
            output.append("  → Sustained uptrend (fast MA consistently above slow MA)")
        elif cross.current_signal == "BEARISH":
            output.append(
                "  → Sustained downtrend (fast MA consistently below slow MA)"
            )

    output.append("")

    output.append("💼 TRADING IMPLICATIONS")
    output.append("-" * 70)
    if cross.current_signal == "BULLISH":
        if cross.crossover_type == "GOLDEN_CROSS":
            output.append("  📈 STRONG BUY SIGNAL:")
            output.append("     → Golden Cross is one of most bullish indicators")
            output.append("     → Consider accumulating long positions")
            output.append("     → Set stop-loss below slow MA")
            output.append("     → Target: Previous highs or technical resistance")
        else:
            output.append("  📈 BULLISH SIGNAL:")
            output.append("     → Fast MA above slow MA indicates uptrend")
            output.append("     → Consider long positions on pullbacks")
            output.append("     → Use slow MA as support level")
            output.append("     → Watch for fast MA to maintain position above slow MA")
    elif cross.current_signal == "BEARISH":
        if cross.crossover_type == "DEATH_CROSS":
            output.append("  📉 STRONG SELL SIGNAL:")
            output.append("     → Death Cross is one of most bearish indicators")
            output.append("     → Consider reducing or exiting long positions")
            output.append("     → Set stop-loss above slow MA if shorting")
            output.append("     → Target: Previous lows or technical support")
        else:
            output.append("  📉 BEARISH SIGNAL:")
            output.append("     → Fast MA below slow MA indicates downtrend")
            output.append("     → Consider short positions on rallies")
            output.append("     → Use slow MA as resistance level")
            output.append("     → Watch for fast MA to maintain position below slow MA")
    else:
        output.append("  ⚪ NEUTRAL:")
        output.append("     → MAs converging - trend unclear")
        output.append("     → Wait for clear crossover before acting")
        output.append("     → Consider reducing position size until clarity")
        output.append("     → Watch for breakout in either direction")

    output.append("")

    output.append("⚠️  RISK CONSIDERATIONS")
    output.append("-" * 70)
    output.append(
        "  • Crossovers are lagging indicators (confirm trends, don't predict)"
    )
    output.append("  • False signals (whipsaws) can occur in choppy markets")
    output.append(
        "  • Use additional confirmation: volume, RSI, MACD, support/resistance"
    )
    output.append("  • Always use stop-losses to protect against reversal")
    output.append("  • Consider overall market context and fundamentals")

    output.append("")
    output.append("=" * 70)
    output.append(
        "⚠️  DISCLAIMER: For educational purposes only. Not investment advice."
    )
    output.append("=" * 70)

    return "\n".join(output)


def format_json_output(analysis: MovingAverageAnalysis) -> str:
    """Format results as JSON."""
    return analysis.model_dump_json(indent=2)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Calculate moving averages for Finance Guru™",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single MA
  %(prog)s TSLA --days 200 --ma-type SMA --period 50

  # Golden Cross check (50/200 SMA)
  %(prog)s TSLA --days 252 --fast 50 --slow 200

  # EMA crossover (12/26 for MACD)
  %(prog)s TSLA --days 252 --ma-type EMA --fast 12 --slow 26

  # Hull MA for responsive trend
  %(prog)s TSLA --days 200 --ma-type HMA --period 50

  # JSON output
  %(prog)s TSLA --days 200 --ma-type SMA --period 50 --output json

  # Save to file
  %(prog)s TSLA --days 252 --fast 50 --slow 200 --save-to analysis/tsla-golden-cross.json
        """,
    )

    parser.add_argument(
        "ticker", type=str, help="Stock ticker symbol (e.g., TSLA, AAPL)"
    )

    parser.add_argument(
        "--days",
        type=int,
        default=200,
        help="Number of days of historical data (default: 200, minimum: 50)",
    )

    parser.add_argument(
        "--realtime",
        action="store_true",
        help="Append current intraday price from Finnhub for real-time MA analysis",
    )

    parser.add_argument(
        "--ma-type",
        type=str,
        choices=["SMA", "EMA", "WMA", "HMA"],
        default="SMA",
        help="Type of moving average (default: SMA)",
    )

    parser.add_argument(
        "--period",
        type=int,
        default=None,
        help="MA period in days (default: 50 for single MA, or use --fast/--slow)",
    )

    parser.add_argument(
        "--fast",
        type=int,
        default=None,
        help="Fast MA period for crossover (e.g., 50 for Golden Cross)",
    )

    parser.add_argument(
        "--slow",
        type=int,
        default=None,
        help="Slow MA period for crossover (e.g., 200 for Golden Cross)",
    )

    parser.add_argument(
        "--secondary-ma-type",
        type=str,
        choices=["SMA", "EMA", "WMA", "HMA"],
        default=None,
        help="Type of secondary MA for crossover (default: same as --ma-type)",
    )

    parser.add_argument(
        "--secondary-period",
        type=int,
        default=None,
        help="Secondary MA period (alternative to --slow)",
    )

    parser.add_argument(
        "--output",
        type=str,
        choices=["human", "json"],
        default="human",
        help="Output format (default: human)",
    )

    parser.add_argument(
        "--save-to", type=str, default=None, help="Save output to file (optional)"
    )

    args = parser.parse_args()

    if args.days < DEFAULT_MA_PERIOD:
        print(f"ERROR: --days must be at least {DEFAULT_MA_PERIOD}", file=sys.stderr)
        sys.exit(1)

    if args.fast and args.slow:
        primary_period = args.fast
        secondary_period = args.slow
        secondary_ma_type = args.secondary_ma_type or args.ma_type
    elif args.period and args.secondary_period:
        primary_period = args.period
        secondary_period = args.secondary_period
        secondary_ma_type = args.secondary_ma_type or args.ma_type
    elif args.period:
        primary_period = args.period
        secondary_period = None
        secondary_ma_type = None
    elif args.secondary_period:
        print("ERROR: --secondary-period requires --period", file=sys.stderr)
        sys.exit(1)
    else:
        primary_period = 50
        secondary_period = None
        secondary_ma_type = None

    try:
        data_source = (
            "real-time (Finnhub + yfinance)"
            if args.realtime
            else "end-of-day (yfinance)"
        )
        print(
            f"📥 Fetching {args.days} days of data for {args.ticker} ({data_source})...",
            file=sys.stderr,
        )
        ma_data = fetch_ma_data(args.ticker, args.days, realtime=args.realtime)
        print(f"✅ Fetched {len(ma_data.dates)} data points", file=sys.stderr)
        print(f"📅 Latest data: {ma_data.dates[-1]}", file=sys.stderr)

        config = MovingAverageConfig(
            ma_type=args.ma_type,
            period=primary_period,
            secondary_ma_type=secondary_ma_type,
            secondary_period=secondary_period,
        )

        if secondary_period:
            print(
                f"🧮 Calculating {args.ma_type}({primary_period}) and {secondary_ma_type}({secondary_period})...",
                file=sys.stderr,
            )
        else:
            print(
                f"🧮 Calculating {args.ma_type}({primary_period})...", file=sys.stderr
            )

        calculator = MovingAverageCalculator(config)

        if secondary_period:
            analysis = calculator.calculate_with_crossover(ma_data)
            print("✅ Crossover analysis complete!", file=sys.stderr)
        else:
            ma_output = calculator.calculate_ma(ma_data)
            analysis = MovingAverageAnalysis(
                ticker=ma_data.ticker,
                calculation_date=ma_data.dates[-1],
                primary_ma=ma_output,
                secondary_ma=None,
                crossover_analysis=None,
            )
            print("✅ MA calculation complete!", file=sys.stderr)

        print("", file=sys.stderr)

        if args.output == "json":
            output = format_json_output(analysis)
        else:
            if analysis.crossover_analysis:
                output = format_crossover_output(analysis)
            else:
                output = format_single_ma_output(analysis)

        if args.save_to:
            save_path = Path(args.save_to)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            save_path.write_text(output)
            print(f"💾 Saved to: {save_path}", file=sys.stderr)
        else:
            print(output)

    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"❌ ERROR: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
