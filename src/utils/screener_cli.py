#!/usr/bin/env python3
"""
Technical Screener CLI for Finance Guru™ Agents

This module provides a command-line interface for screening stocks.
Designed for easy integration with Finance Guru agents.

ARCHITECTURE NOTE:
This is Layer 3 of our 3-layer architecture:
    Layer 1: Pydantic Models - Data validation
    Layer 2: Calculator Classes - Business logic
    Layer 3: CLI Interface (THIS FILE) - Agent integration

AGENT USAGE:
    # Screen single ticker
    uv run python src/utils/screener_cli.py TSLA --days 252

    # Screen multiple tickers (portfolio mode)
    uv run python src/utils/screener_cli.py TSLA PLTR NVDA AAPL --days 252

    # Custom criteria
    uv run python src/utils/screener_cli.py TSLA PLTR --days 252 \\
        --patterns golden_cross rsi_oversold breakout \\
        --rsi-oversold 35

    # JSON output
    uv run python src/utils/screener_cli.py TSLA PLTR --days 252 --output json

EDUCATIONAL NOTE:
Use this to find trading opportunities automatically.
The screener checks technical patterns and ranks stocks by signal strength.

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

from src.models.screener_inputs import (
    PatternType,
    ScreeningCriteria,
    ScreeningResult,
    PortfolioScreeningOutput,
)
from src.utils.screener import TechnicalScreener


def fetch_ticker_data(ticker: str, days: int) -> tuple[list[float], list[date], list[float]]:
    """Fetch price and volume data for a ticker."""
    try:
        import yfinance as yf

        end_date = date.today()
        # Need ~1.5x calendar days to get requested trading days (accounts for weekends/holidays)
        # Example: 252 trading days × 1.5 = 378 calendar days (~1 year with market closures)
        start_date = end_date - timedelta(days=int(days * 1.5))

        ticker_obj = yf.Ticker(ticker)
        hist = ticker_obj.history(start=start_date, end=end_date)

        if hist.empty:
            raise ValueError(f"No data found for {ticker}")

        prices = hist['Close'].tolist()
        dates = [d.date() for d in hist.index]
        volumes = hist['Volume'].tolist()

        if len(prices) < 200:
            print(f"⚠️  Warning: {ticker} only has {len(prices)} days (need 200 for MA200)", file=sys.stderr)

        return (prices, dates, volumes)

    except ImportError:
        print("ERROR: yfinance not installed. Run: uv add yfinance", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR fetching {ticker}: {e}", file=sys.stderr)
        raise


def format_single_result(result: ScreeningResult) -> str:
    """Format single ticker screening result."""
    output = []
    output.append("=" * 70)
    output.append(f"🎯 SCREENING RESULT: {result.ticker}")
    output.append(f"📅 Date: {result.screening_date}")
    output.append("=" * 70)
    output.append("")

    # Status
    if result.matches_criteria:
        output.append("✅ MATCHES CRITERIA - Signals detected")
    else:
        output.append("❌ DOES NOT MATCH - No significant signals")
    output.append("")

    # Recommendation
    rec_emoji = {"strong_buy": "🚀", "buy": "👍", "hold": "⏸️", "sell": "👎", "strong_sell": "🔻"}
    emoji = rec_emoji.get(result.recommendation, "")
    output.append(f"📊 RECOMMENDATION: {emoji} {result.recommendation.upper()}")
    output.append(f"   Confidence: {result.confidence:.0%}")
    output.append("")

    # Scores
    output.append("📈 SCORING")
    output.append("-" * 70)
    output.append(f"  Composite Score:          {result.score:>10.1f}")
    if result.rank:
        output.append(f"  Rank:                     {result.rank:>10}")
    output.append("")

    # Current Metrics
    output.append("💰 CURRENT METRICS")
    output.append("-" * 70)
    output.append(f"  Price:                    ${result.current_price:>10.2f}")
    if result.current_rsi:
        output.append(f"  RSI:                      {result.current_rsi:>10.1f}")
    output.append("")

    # Signals
    if result.signals:
        output.append("🔔 SIGNALS DETECTED")
        output.append("-" * 70)
        for i, signal in enumerate(result.signals, 1):
            strength_emoji = {"strong": "🔴", "moderate": "🟠", "weak": "🟡"}
            emoji = strength_emoji.get(signal.strength, "")
            output.append(f"  {i}. {emoji} {signal.signal_type.value.upper()} ({signal.strength})")
            output.append(f"     {signal.description}")
            output.append(f"     Detected: {signal.date_detected}")
            if signal.value is not None:
                output.append(f"     Value: {signal.value:.2f}")
        output.append("")

    # Notes
    if result.notes:
        output.append("💡 NOTES")
        output.append("-" * 70)
        for note in result.notes:
            output.append(f"  • {note}")
        output.append("")

    output.append("=" * 70)
    return "\n".join(output)


def format_portfolio_results(results: PortfolioScreeningOutput) -> str:
    """Format portfolio screening results."""
    output = []
    output.append("=" * 70)
    output.append("🎯 PORTFOLIO SCREENING RESULTS")
    output.append(f"📅 Date: {results.screening_date}")
    output.append("=" * 70)
    output.append("")

    # Summary
    output.append("📊 SUMMARY")
    output.append("-" * 70)
    output.append(f"  Total Screened:           {results.total_tickers_screened:>10}")
    output.append(f"  Matching Criteria:        {results.tickers_matching:>10}")
    output.append(f"  Match Rate:               {results.tickers_matching/max(results.total_tickers_screened,1):>9.0%}")
    output.append("")
    output.append(f"  {results.summary}")
    output.append("")

    # Top Picks
    if results.top_picks:
        output.append("🏆 TOP PICKS")
        output.append("-" * 70)
        for i, ticker in enumerate(results.top_picks, 1):
            # Find the result for this ticker
            ticker_result = next((r for r in results.results if r.ticker == ticker), None)
            if ticker_result:
                signal_count = len(ticker_result.signals)
                output.append(f"  {i}. {ticker:<6} - Score: {ticker_result.score:>5.1f} ({signal_count} signals) - {ticker_result.recommendation.upper()}")
        output.append("")

    # Detailed Results
    output.append("📋 DETAILED RESULTS (Ranked by Score)")
    output.append("=" * 70)
    output.append("")

    # Show ALL results, not just matches (for educational value)
    for result in results.results:
        rec_emoji = {"strong_buy": "🚀", "buy": "👍", "hold": "⏸️", "sell": "👎", "strong_sell": "🔻"}
        emoji = rec_emoji.get(result.recommendation, "")

        # Show ticker with match status
        match_status = "✅ MATCH" if result.matches_criteria else "❌ NO MATCH"
        rank_str = f"#{result.rank}" if result.rank else "N/A"
        output.append(f"{match_status} | Rank {rank_str}: {result.ticker} - Score {result.score:.1f} {emoji}")

        # Format RSI properly (avoid None formatting errors)
        rsi_str = f"{result.current_rsi:.1f}" if result.current_rsi is not None else "N/A"
        output.append(f"  Price: ${result.current_price:.2f} | RSI: {rsi_str}")

        # Show signals (or lack thereof)
        if result.signals:
            signals_str = ', '.join(s.signal_type.value for s in result.signals)
            output.append(f"  Signals: {signals_str}")
        else:
            output.append("  Signals: None detected")

        output.append(f"  Recommendation: {result.recommendation.upper()} (confidence: {result.confidence:.0%})")
        output.append("")

    output.append("=" * 70)
    output.append("ℹ️  Use --output json for machine-readable format")
    output.append("=" * 70)
    return "\n".join(output)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Screen stocks for technical opportunities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Screen single ticker
  %(prog)s TSLA --days 252

  # Screen multiple tickers (portfolio mode)
  %(prog)s TSLA PLTR NVDA AAPL --days 252

  # Custom patterns
  %(prog)s TSLA PLTR --days 252 --patterns golden_cross rsi_oversold breakout

  # Custom RSI thresholds
  %(prog)s TSLA --days 252 --rsi-oversold 35 --rsi-overbought 75

  # JSON output
  %(prog)s TSLA PLTR NVDA --days 252 --output json
        """
    )

    # Tickers to screen
    parser.add_argument(
        "tickers",
        nargs="+",
        type=str,
        help="One or more ticker symbols to screen"
    )

    # Data parameters
    parser.add_argument(
        "--days",
        type=int,
        default=252,
        help="Number of days of historical data (default: 252)"
    )

    # Pattern selection
    parser.add_argument(
        "--patterns",
        nargs="+",
        choices=[p.value for p in PatternType],
        default=None,  # None means "all patterns" - more useful default
        help="Technical patterns to screen for (default: all patterns)"
    )

    # RSI parameters
    parser.add_argument(
        "--rsi-oversold",
        type=float,
        default=30.0,
        help="RSI oversold threshold (default: 30)"
    )

    parser.add_argument(
        "--rsi-overbought",
        type=float,
        default=70.0,
        help="RSI overbought threshold (default: 70)"
    )

    # MA parameters
    parser.add_argument(
        "--ma-fast",
        type=int,
        default=50,
        help="Fast MA period (default: 50)"
    )

    parser.add_argument(
        "--ma-slow",
        type=int,
        default=200,
        help="Slow MA period (default: 200)"
    )

    # Volume parameters
    parser.add_argument(
        "--volume-multiplier",
        type=float,
        default=1.5,
        help="Volume multiplier for breakouts (default: 1.5)"
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

    args = parser.parse_args()

    # Validate parameters
    if args.days < 200:
        print("⚠️  Warning: Need at least 200 days for MA200 detection", file=sys.stderr)

    try:
        # Create screening criteria
        # If no patterns specified, use all patterns (most useful default)
        patterns_to_use = [PatternType(p) for p in args.patterns] if args.patterns else list(PatternType)

        criteria = ScreeningCriteria(
            patterns=patterns_to_use,
            rsi_oversold=args.rsi_oversold,
            rsi_overbought=args.rsi_overbought,
            ma_fast=args.ma_fast,
            ma_slow=args.ma_slow,
            volume_multiplier=args.volume_multiplier,
        )

        # Create screener
        screener = TechnicalScreener(criteria)

        if len(args.tickers) == 1:
            # Single ticker mode
            ticker = args.tickers[0].upper()
            print(f"📥 Fetching {args.days} days of data for {ticker}...", file=sys.stderr)

            prices, dates, volumes = fetch_ticker_data(ticker, args.days)
            print(f"✅ Fetched {len(prices)} data points", file=sys.stderr)

            print("🔍 Running screening analysis...", file=sys.stderr)
            result = screener.screen_ticker(ticker, prices, dates, volumes)

            if args.output == "json":
                output_text = result.model_dump_json(indent=2)
            else:
                output_text = format_single_result(result)

        else:
            # Portfolio mode
            print(f"📥 Fetching data for {len(args.tickers)} tickers...", file=sys.stderr)

            tickers_data = {}
            for ticker in args.tickers:
                ticker = ticker.upper()
                try:
                    data = fetch_ticker_data(ticker, args.days)
                    tickers_data[ticker] = data
                    print(f"  ✅ {ticker}: {len(data[0])} points", file=sys.stderr)
                except Exception as e:
                    print(f"  ❌ {ticker}: {e}", file=sys.stderr)

            if not tickers_data:
                print("ERROR: No valid data fetched", file=sys.stderr)
                sys.exit(1)

            print("🔍 Running portfolio screening...", file=sys.stderr)
            portfolio_results = screener.screen_portfolio(tickers_data)

            if args.output == "json":
                output_text = portfolio_results.model_dump_json(indent=2)
            else:
                output_text = format_portfolio_results(portfolio_results)

        # Output results
        print("", file=sys.stderr)
        if args.save_to:
            save_path = Path(args.save_to)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            save_path.write_text(output_text)
            print(f"💾 Saved to: {save_path}", file=sys.stderr)
        else:
            print(output_text)

    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"❌ ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
