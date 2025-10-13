#!/usr/bin/env python3
"""
Momentum Indicators CLI for Finance Guru™ Agents

This module provides a command-line interface for calculating momentum indicators.
Designed for easy integration with Finance Guru agents.

ARCHITECTURE NOTE:
This is Layer 3 of our 3-layer architecture:
    Layer 1: Pydantic Models - Data validation
    Layer 2: Calculator Classes - Business logic
    Layer 3: CLI Interface (THIS FILE) - Agent integration

AGENT USAGE:
    # Basic usage (calculate all momentum indicators)
    uv run python src/utils/momentum_cli.py TSLA --days 90

    # Specific indicator only
    uv run python src/utils/momentum_cli.py TSLA --days 90 --indicator rsi

    # Custom configuration
    uv run python src/utils/momentum_cli.py TSLA --days 90 \\
        --rsi-period 21 \\
        --macd-fast 8 \\
        --macd-slow 21

    # JSON output
    uv run python src/utils/momentum_cli.py TSLA --days 90 --output json

    # Save to file
    uv run python src/utils/momentum_cli.py TSLA --days 90 \\
        --output json \\
        --save-to analysis/tsla-momentum-2025-10-13.json

EDUCATIONAL NOTE:
Momentum indicators help time entry/exit points by showing:
- Overbought/oversold conditions (RSI, Stochastic, Williams %R)
- Trend changes (MACD)
- Momentum strength (ROC)

Author: Finance Guru™ Development Team
Created: 2025-10-13
"""

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.models.momentum_inputs import (
    MomentumDataInput,
    MomentumConfig,
    AllMomentumOutput,
    RSIOutput,
    MACDOutput,
    StochasticOutput,
    WilliamsROutput,
    ROCOutput,
)
from src.utils.momentum import MomentumIndicators


def fetch_momentum_data(ticker: str, days: int) -> MomentumDataInput:
    """
    Fetch historical OHLC data for momentum calculations.

    Args:
        ticker: Stock ticker symbol
        days: Number of days of historical data

    Returns:
        MomentumDataInput: Validated OHLC data

    Raises:
        ValueError: If unable to fetch data or insufficient data points
    """
    try:
        import yfinance as yf

        # Calculate date range
        end_date = date.today()
        start_date = end_date - timedelta(days=days + 30)

        # Fetch data
        ticker_obj = yf.Ticker(ticker)
        hist = ticker_obj.history(start=start_date, end=end_date)

        if hist.empty:
            raise ValueError(f"No data found for ticker {ticker}")

        # Extract OHLC data
        dates_list = [d.date() for d in hist.index]
        close_list = hist['Close'].tolist()
        high_list = hist['High'].tolist()
        low_list = hist['Low'].tolist()

        # Ensure minimum data points
        if len(dates_list) < 14:
            raise ValueError(
                f"Insufficient data: got {len(dates_list)} days, need at least 14. "
                "Try increasing --days parameter."
            )

        # Create validated model
        return MomentumDataInput(
            ticker=ticker.upper(),
            dates=dates_list,
            close=close_list,
            high=high_list,
            low=low_list,
        )

    except ImportError:
        print("ERROR: yfinance not installed. Run: uv add yfinance", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR fetching data for {ticker}: {e}", file=sys.stderr)
        sys.exit(1)


def format_rsi_output(rsi: RSIOutput) -> str:
    """Format RSI results for human reading."""
    output = []
    output.append("=" * 70)
    output.append(f"📈 RSI ANALYSIS: {rsi.ticker}")
    output.append(f"📅 Data Through: {rsi.calculation_date} (most recent market close)")
    output.append("=" * 70)
    output.append("")
    output.append("📊 RELATIVE STRENGTH INDEX (RSI)")
    output.append("-" * 70)
    output.append(f"  Current RSI:              {rsi.current_rsi:>10.2f}")
    output.append(f"  Signal:                   {rsi.rsi_signal:>10}")
    output.append(f"  Period:                   {rsi.period:>10} days")
    output.append("")

    # Interpretation
    if rsi.rsi_signal == "overbought":
        output.append("  🔴 OVERBOUGHT: RSI above 70 suggests potential selling pressure")
    elif rsi.rsi_signal == "oversold":
        output.append("  🟢 OVERSOLD: RSI below 30 suggests potential buying opportunity")
    else:
        output.append("  ⚪ NEUTRAL: RSI between 30-70, no extreme condition")

    output.append("")
    output.append("=" * 70)
    output.append("⚠️  DISCLAIMER: For educational purposes only. Not investment advice.")
    output.append("=" * 70)
    return "\n".join(output)


def format_all_output(results: AllMomentumOutput) -> str:
    """Format all momentum indicators for human reading."""
    output = []
    output.append("=" * 70)
    output.append(f"📊 MOMENTUM ANALYSIS: {results.ticker}")
    output.append(f"📅 Data Through: {results.calculation_date} (most recent market close)")
    output.append("=" * 70)
    output.append("")

    # RSI Section
    output.append("📈 RELATIVE STRENGTH INDEX (RSI)")
    output.append("-" * 70)
    output.append(f"  Current RSI:              {results.rsi.current_rsi:>10.2f}")
    output.append(f"  Signal:                   {results.rsi.rsi_signal:>10}")
    if results.rsi.rsi_signal == "overbought":
        output.append("  💡 Overbought: Potential sell signal")
    elif results.rsi.rsi_signal == "oversold":
        output.append("  💡 Oversold: Potential buy signal")
    else:
        output.append("  💡 Neutral: No extreme condition")
    output.append("")

    # MACD Section
    output.append("📉 MACD (Moving Average Convergence Divergence)")
    output.append("-" * 70)
    output.append(f"  MACD Line:                {results.macd.macd_line:>10.2f}")
    output.append(f"  Signal Line:              {results.macd.signal_line:>10.2f}")
    output.append(f"  Histogram:                {results.macd.histogram:>10.2f}")
    output.append(f"  Trend:                    {results.macd.signal:>10}")
    if results.macd.signal == "bullish":
        output.append("  💡 Bullish: MACD above signal line (upward momentum)")
    else:
        output.append("  💡 Bearish: MACD below signal line (downward momentum)")
    output.append("")

    # Stochastic Section
    output.append("🎯 STOCHASTIC OSCILLATOR")
    output.append("-" * 70)
    output.append(f"  %K (Fast):                {results.stochastic.k_value:>10.2f}")
    output.append(f"  %D (Slow):                {results.stochastic.d_value:>10.2f}")
    output.append(f"  Signal:                   {results.stochastic.signal:>10}")
    if results.stochastic.signal == "overbought":
        output.append("  💡 Overbought: %K > 80, potential reversal down")
    elif results.stochastic.signal == "oversold":
        output.append("  💡 Oversold: %K < 20, potential reversal up")
    else:
        output.append("  💡 Neutral: %K between 20-80")
    output.append("")

    # Williams %R Section
    output.append("📊 WILLIAMS %R")
    output.append("-" * 70)
    output.append(f"  Williams %R:              {results.williams_r.williams_r:>10.2f}")
    output.append(f"  Signal:                   {results.williams_r.signal:>10}")
    if results.williams_r.signal == "overbought":
        output.append("  💡 Overbought: %R > -20, potential sell signal")
    elif results.williams_r.signal == "oversold":
        output.append("  💡 Oversold: %R < -80, potential buy signal")
    else:
        output.append("  💡 Neutral: %R between -20 and -80")
    output.append("")

    # ROC Section
    output.append("🚀 RATE OF CHANGE (ROC)")
    output.append("-" * 70)
    output.append(f"  ROC:                      {results.roc.roc:>9.2f}%")
    output.append(f"  Signal:                   {results.roc.signal:>10}")
    if results.roc.signal == "bullish":
        output.append(f"  💡 Bullish: Positive momentum ({results.roc.roc:.2f}% gain)")
    elif results.roc.signal == "bearish":
        output.append(f"  💡 Bearish: Negative momentum ({abs(results.roc.roc):.2f}% loss)")
    else:
        output.append("  💡 Neutral: No significant change")
    output.append("")

    # Confluence Analysis
    output.append("🎯 MOMENTUM CONFLUENCE")
    output.append("-" * 70)

    # Count bullish/bearish signals
    bullish_count = 0
    bearish_count = 0

    if results.rsi.rsi_signal == "oversold":
        bullish_count += 1
    elif results.rsi.rsi_signal == "overbought":
        bearish_count += 1

    if results.macd.signal == "bullish":
        bullish_count += 1
    else:
        bearish_count += 1

    if results.stochastic.signal == "oversold":
        bullish_count += 1
    elif results.stochastic.signal == "overbought":
        bearish_count += 1

    if results.williams_r.signal == "oversold":
        bullish_count += 1
    elif results.williams_r.signal == "overbought":
        bearish_count += 1

    if results.roc.signal == "bullish":
        bullish_count += 1
    elif results.roc.signal == "bearish":
        bearish_count += 1

    output.append(f"  Bullish Signals:          {bullish_count:>10}/5")
    output.append(f"  Bearish Signals:          {bearish_count:>10}/5")
    output.append("")

    if bullish_count >= 3:
        output.append(f"  ✅ STRONG BULLISH CONFLUENCE ({bullish_count}/5 indicators)")
    elif bearish_count >= 3:
        output.append(f"  ❌ STRONG BEARISH CONFLUENCE ({bearish_count}/5 indicators)")
    else:
        output.append("  ⚠️  MIXED SIGNALS: No clear confluence")

    output.append("")
    output.append("=" * 70)
    output.append("⚠️  DISCLAIMER: For educational purposes only. Not investment advice.")
    output.append("=" * 70)

    return "\n".join(output)


def format_json_output(
    results: AllMomentumOutput | RSIOutput | MACDOutput | StochasticOutput | WilliamsROutput | ROCOutput
) -> str:
    """Format results as JSON."""
    return results.model_dump_json(indent=2)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Calculate momentum indicators for Finance Guru™",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # All indicators
  %(prog)s TSLA --days 90

  # Specific indicator only
  %(prog)s TSLA --days 90 --indicator rsi

  # Custom RSI period
  %(prog)s TSLA --days 90 --rsi-period 21

  # JSON output
  %(prog)s TSLA --days 90 --output json

  # Save to file
  %(prog)s TSLA --days 90 --output json --save-to analysis/momentum.json
        """
    )

    # Required arguments
    parser.add_argument(
        "ticker",
        type=str,
        help="Stock ticker symbol (e.g., TSLA, AAPL)"
    )

    # Data parameters
    parser.add_argument(
        "--days",
        type=int,
        default=90,
        help="Number of days of historical data (default: 90, minimum: 30)"
    )

    parser.add_argument(
        "--indicator",
        type=str,
        choices=["all", "rsi", "macd", "stochastic", "williams", "roc"],
        default="all",
        help="Calculate specific indicator or all (default: all)"
    )

    # Configuration parameters
    parser.add_argument(
        "--rsi-period",
        type=int,
        default=14,
        help="RSI period (default: 14)"
    )

    parser.add_argument(
        "--macd-fast",
        type=int,
        default=12,
        help="MACD fast period (default: 12)"
    )

    parser.add_argument(
        "--macd-slow",
        type=int,
        default=26,
        help="MACD slow period (default: 26)"
    )

    parser.add_argument(
        "--macd-signal",
        type=int,
        default=9,
        help="MACD signal period (default: 9)"
    )

    parser.add_argument(
        "--stoch-k",
        type=int,
        default=14,
        help="Stochastic %K period (default: 14)"
    )

    parser.add_argument(
        "--stoch-d",
        type=int,
        default=3,
        help="Stochastic %D period (default: 3)"
    )

    parser.add_argument(
        "--williams-period",
        type=int,
        default=14,
        help="Williams %R period (default: 14)"
    )

    parser.add_argument(
        "--roc-period",
        type=int,
        default=12,
        help="ROC period (default: 12)"
    )

    # Output parameters
    parser.add_argument(
        "--output",
        type=str,
        choices=["human", "json"],
        default="human",
        help="Output format (default: human)"
    )

    parser.add_argument(
        "--save-to",
        type=str,
        default=None,
        help="Save output to file (optional)"
    )

    # Parse arguments
    args = parser.parse_args()

    # Validate days parameter
    if args.days < 30:
        print("ERROR: --days must be at least 30", file=sys.stderr)
        sys.exit(1)

    try:
        # Step 1: Fetch data
        print(f"📥 Fetching {args.days} days of data for {args.ticker}...", file=sys.stderr)
        momentum_data = fetch_momentum_data(args.ticker, args.days)
        print(f"✅ Fetched {len(momentum_data.dates)} data points", file=sys.stderr)
        print(f"📅 Latest data: {momentum_data.dates[-1]} (most recent market close)", file=sys.stderr)

        # Step 2: Create configuration
        config = MomentumConfig(
            rsi_period=args.rsi_period,
            macd_fast=args.macd_fast,
            macd_slow=args.macd_slow,
            macd_signal=args.macd_signal,
            stoch_k_period=args.stoch_k,
            stoch_d_period=args.stoch_d,
            williams_period=args.williams_period,
            roc_period=args.roc_period,
        )

        # Step 3: Calculate indicators
        print("🧮 Calculating momentum indicators...", file=sys.stderr)
        calculator = MomentumIndicators(config)

        if args.indicator == "all":
            results = calculator.calculate_all(momentum_data)
        elif args.indicator == "rsi":
            results = calculator.calculate_rsi(momentum_data)
        elif args.indicator == "macd":
            results = calculator.calculate_macd(momentum_data)
        elif args.indicator == "stochastic":
            results = calculator.calculate_stochastic(momentum_data)
        elif args.indicator == "williams":
            results = calculator.calculate_williams_r(momentum_data)
        else:  # roc
            results = calculator.calculate_roc(momentum_data)

        print("✅ Calculation complete!", file=sys.stderr)
        print("", file=sys.stderr)

        # Step 4: Format output
        if args.output == "json":
            output = format_json_output(results)
        else:
            if isinstance(results, AllMomentumOutput):
                output = format_all_output(results)
            elif isinstance(results, RSIOutput):
                output = format_rsi_output(results)
            else:
                # For other individual indicators, fall back to JSON-style output
                output = format_json_output(results)

        # Step 5: Display or save
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
