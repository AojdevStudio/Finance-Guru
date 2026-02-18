#!/usr/bin/env python3
"""
ITC Risk CLI for Finance Guru™ Agents

This module provides a command-line interface for the ITC (Into The Cryptoverse)
Risk Models API integration.

ARCHITECTURE NOTE:
This is Layer 3 of our 3-layer architecture:
    Layer 1: Pydantic Models - Data validation (src/models/itc_risk_inputs.py)
    Layer 2: Calculator Classes - Business logic (src/analysis/itc_risk.py)
    Layer 3: CLI Interface (THIS FILE) - Agent integration

AGENT USAGE:
    # Single ticker analysis (tradfi)
    uv run python src/analysis/itc_risk_cli.py TSLA --universe tradfi

    # Crypto asset
    uv run python src/analysis/itc_risk_cli.py BTC --universe crypto

    # Batch processing (multiple tickers)
    uv run python src/analysis/itc_risk_cli.py TSLA AAPL MSTR --universe tradfi

    # JSON output (for programmatic parsing)
    uv run python src/analysis/itc_risk_cli.py TSLA --universe tradfi --output json

    # Full risk band table
    uv run python src/analysis/itc_risk_cli.py TSLA --universe tradfi --full-table

    # List supported tickers
    uv run python src/analysis/itc_risk_cli.py --list-supported tradfi

EDUCATIONAL NOTE:
This CLI makes it easy for agents to query ITC Risk without writing Python code.
The tool:
1. Validates all inputs (Pydantic models)
2. Handles API communication with retry logic
3. Enriches tradfi assets with current prices from yfinance
4. Formats output (human-readable or JSON)

REQUIRES:
    ITC_API_KEY environment variable (set in .env file)

Author: Finance Guru™ Development Team
Created: 2026-01-09
"""

import argparse
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import our type-safe components
from src.analysis.itc_risk import ITCRiskCalculator
from src.models.itc_risk_inputs import ITCRiskResponse


def format_output_human(result: ITCRiskResponse, full_table: bool = False) -> str:  # noqa: C901
    """
    Format a single result in human-readable format.

    EDUCATIONAL NOTE:
    Creates a nicely formatted report with:
    - Current risk score and interpretation
    - Current price (if available)
    - Nearest risk bands around current price
    - Distance to high risk zone

    Args:
        result: ITCRiskResponse with risk data
        full_table: If True, show complete risk band table

    Returns:
        Formatted string for display
    """
    output = []
    output.append("=" * 70)
    output.append(f"📊 ITC RISK ANALYSIS: {result.symbol}")
    output.append(f"🌐 Universe: {result.universe.upper()}")
    output.append(f"📅 Fetched: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    output.append("=" * 70)
    output.append("")

    # Current Risk Score Section
    output.append("🎯 CURRENT RISK LEVEL")
    output.append("-" * 70)

    # Risk score with visual indicator
    score = result.current_risk_score
    if score < 0.3:
        risk_emoji = "🟢"
        risk_bar = "█" * int(score * 20) + "░" * (20 - int(score * 20))
    elif score < 0.7:
        risk_emoji = "🟡"
        risk_bar = "█" * int(score * 20) + "░" * (20 - int(score * 20))
    else:
        risk_emoji = "🔴"
        risk_bar = "█" * int(score * 20) + "░" * (20 - int(score * 20))

    output.append(f"  Risk Score:    {risk_emoji} {score:.3f} [{risk_bar}]")
    output.append(f"  Interpretation: {result.get_risk_interpretation()}")
    output.append("")

    # Current Price Section (if available)
    if result.current_price:
        output.append("💵 CURRENT PRICE")
        output.append("-" * 70)
        output.append(f"  Market Price:  ${result.current_price:,.2f}")

        # Calculate distance to high risk zone
        high_risk = result.get_high_risk_threshold()
        if high_risk:
            distance_pct = ((high_risk.price / result.current_price) - 1) * 100
            if distance_pct > 0:
                output.append(
                    f"  High Risk at:  ${high_risk.price:,.2f} "
                    f"({distance_pct:+.1f}% from current)"
                )
            else:
                output.append(
                    f"  ⚠️  ALREADY IN HIGH RISK ZONE "
                    f"(threshold was ${high_risk.price:,.2f})"
                )
        output.append("")

    # Risk Bands Section
    if result.risk_bands:
        if full_table:
            output.append("📈 FULL RISK BAND TABLE")
            output.append("-" * 70)
            output.append(
                f"  {'PRICE':>12}  {'RISK':>8}  {'LEVEL':>12}  {'MARKER':<10}"
            )
            output.append(f"  {'-' * 12}  {'-' * 8}  {'-' * 12}  {'-' * 10}")

            for band in result.risk_bands:
                # Determine risk level label
                if band.risk_score < 0.3:
                    level = "LOW"
                elif band.risk_score < 0.7:
                    level = "MEDIUM"
                else:
                    level = "HIGH"

                # Mark current price location
                marker = ""
                if result.current_price and (
                    abs(band.price - result.current_price) / result.current_price < 0.02
                ):
                    marker = "← CURRENT"

                output.append(
                    f"  ${band.price:>11,.2f}  {band.risk_score:>8.3f}  {level:>12}  {marker:<10}"
                )
        else:
            output.append("📈 NEAREST RISK BANDS (use --full-table for complete list)")
            output.append("-" * 70)
            output.append(
                f"  {'PRICE':>12}  {'RISK':>8}  {'LEVEL':>12}  {'MARKER':<10}"
            )
            output.append(f"  {'-' * 12}  {'-' * 8}  {'-' * 12}  {'-' * 10}")

            nearest = result.get_nearest_bands(7)
            # Sort by price for display
            nearest_sorted = sorted(nearest, key=lambda b: b.price)

            for band in nearest_sorted:
                if band.risk_score < 0.3:
                    level = "LOW"
                elif band.risk_score < 0.7:
                    level = "MEDIUM"
                else:
                    level = "HIGH"

                marker = ""
                if result.current_price and (
                    abs(band.price - result.current_price) / result.current_price < 0.02
                ):
                    marker = "← CURRENT"

                output.append(
                    f"  ${band.price:>11,.2f}  {band.risk_score:>8.3f}  {level:>12}  {marker:<10}"
                )

        output.append("")

    # Footer
    output.append("=" * 70)
    output.append(f"📡 Source: {result.source}")
    output.append(
        "⚠️  DISCLAIMER: For educational purposes only. Not investment advice."
    )
    output.append("=" * 70)

    return "\n".join(output)


def format_output_json(results: list[ITCRiskResponse]) -> str:
    """
    Format results as JSON.

    EDUCATIONAL NOTE:
    JSON output is perfect for programmatic parsing by agents.
    For batch processing, returns an array of results.
    For single ticker, returns just that result.

    Args:
        results: List of ITCRiskResponse objects

    Returns:
        JSON string
    """
    import json

    if len(results) == 1:
        # Single result - return just the object
        return results[0].model_dump_json(indent=2)
    else:
        # Multiple results - return array
        data = [result.model_dump(mode="json") for result in results]
        return json.dumps(data, indent=2, default=str)


def list_supported_tickers(universe: str) -> None:
    """
    Display supported tickers for a universe.

    Args:
        universe: "crypto" or "tradfi"
    """
    # Use class attributes directly without instantiation (no API key needed)
    if universe == "crypto":
        tickers = sorted(ITCRiskCalculator.SUPPORTED_CRYPTO)
        title = "CRYPTO"
    else:
        tickers = sorted(ITCRiskCalculator.SUPPORTED_TRADFI)
        title = "TRADFI"

    print("=" * 70)
    print(f"📋 SUPPORTED {title} TICKERS FOR ITC RISK API")
    print("=" * 70)
    print("")
    print(f"  Total: {len(tickers)} assets")
    print("")

    # Display in columns
    cols = 6
    for i in range(0, len(tickers), cols):
        row = tickers[i : i + cols]
        print("  " + "  ".join(f"{t:<8}" for t in row))

    print("")
    print("=" * 70)
    print("💡 For unsupported tickers, use: risk_metrics_cli.py TICKER --days 90")
    print("=" * 70)


def main():  # noqa: C901
    """
    Main CLI entry point.

    EDUCATIONAL NOTE:
    This function:
    1. Parses command-line arguments
    2. Validates inputs
    3. Fetches risk data from ITC API
    4. Formats and displays output
    """
    parser = argparse.ArgumentParser(
        description="Query ITC Risk Models API for Finance Guru™",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single ticker (tradfi)
  %(prog)s TSLA --universe tradfi

  # Crypto asset
  %(prog)s BTC --universe crypto

  # Batch processing
  %(prog)s TSLA AAPL MSTR --universe tradfi

  # JSON output
  %(prog)s TSLA --universe tradfi --output json

  # Full risk band table
  %(prog)s TSLA --universe tradfi --full-table

  # List supported tickers
  %(prog)s --list-supported tradfi

Note: Requires ITC_API_KEY environment variable.
For unsupported tickers, use risk_metrics_cli.py instead.
        """,
    )

    # Positional arguments - tickers (optional if using --list-supported)
    parser.add_argument(
        "tickers",
        nargs="*",
        type=str,
        help="Ticker symbol(s) to analyze (e.g., TSLA BTC AAPL)",
    )

    # Universe selection
    parser.add_argument(
        "--universe",
        "-u",
        type=str,
        choices=["crypto", "tradfi"],
        default="tradfi",
        help="Asset universe: 'crypto' or 'tradfi' (default: tradfi)",
    )

    # Output format
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        choices=["human", "json"],
        default="human",
        help="Output format (default: human)",
    )

    # Full table flag
    parser.add_argument(
        "--full-table",
        action="store_true",
        help="Show complete risk band table (default: show nearest bands only)",
    )

    # List supported tickers
    parser.add_argument(
        "--list-supported",
        type=str,
        choices=["crypto", "tradfi"],
        metavar="UNIVERSE",
        help="List supported tickers for a universe and exit",
    )

    # Skip price enrichment
    parser.add_argument(
        "--no-price",
        action="store_true",
        help="Skip current price enrichment from yfinance (faster, but no price context)",
    )

    # Parse arguments
    args = parser.parse_args()

    # Handle --list-supported
    if args.list_supported:
        list_supported_tickers(args.list_supported)
        sys.exit(0)

    # Validate that tickers were provided
    if not args.tickers:
        print("❌ ERROR: No tickers provided.", file=sys.stderr)
        print("", file=sys.stderr)
        print(
            "Usage: itc_risk_cli.py TICKER [TICKER ...] --universe <crypto|tradfi>",
            file=sys.stderr,
        )
        print("", file=sys.stderr)
        print("Examples:", file=sys.stderr)
        print("  itc_risk_cli.py TSLA --universe tradfi", file=sys.stderr)
        print("  itc_risk_cli.py BTC ETH --universe crypto", file=sys.stderr)
        print("", file=sys.stderr)
        print(
            "Use --list-supported <universe> to see available tickers.", file=sys.stderr
        )
        sys.exit(1)

    try:
        # Initialize calculator
        print("🔑 Initializing ITC Risk Calculator...", file=sys.stderr)
        calculator = ITCRiskCalculator()
        print("✅ API key loaded", file=sys.stderr)

        # Process each ticker
        results: list[ITCRiskResponse] = []
        errors: list[str] = []

        for ticker in args.tickers:
            ticker_upper = ticker.upper().strip()
            print(f"📥 Fetching risk data for {ticker_upper}...", file=sys.stderr)

            try:
                # Check if ticker is supported before API call
                if not calculator.is_ticker_supported(ticker_upper, args.universe):
                    supported = calculator.get_supported_tickers(args.universe)
                    errors.append(
                        f"❌ {ticker_upper}: Not supported by ITC API.\n"
                        f"   Supported {args.universe} assets: {', '.join(supported[:10])}..."
                        f"\n   Use risk_metrics_cli.py {ticker_upper} --days 90 instead."
                    )
                    continue

                # Fetch risk data
                result = calculator.get_risk_score(
                    symbol=ticker_upper,
                    universe=args.universe,
                    enrich_with_price=not args.no_price,
                )
                results.append(result)
                print(
                    f"✅ {ticker_upper}: Risk score = {result.current_risk_score:.3f}",
                    file=sys.stderr,
                )

            except ValueError as e:
                errors.append(f"❌ {ticker_upper}: {e}")
            except Exception as e:
                errors.append(f"❌ {ticker_upper}: API error - {e}")

        print("", file=sys.stderr)

        # Display errors if any
        if errors:
            for error in errors:
                print(error, file=sys.stderr)
            print("", file=sys.stderr)

        # Exit if no successful results
        if not results:
            print("❌ No valid results to display.", file=sys.stderr)
            sys.exit(1)

        # Format and display output
        if args.output == "json":
            output = format_output_json(results)
            print(output)
        else:
            # Human format - display each result
            for i, result in enumerate(results):
                if i > 0:
                    print("")  # Separator between results
                output = format_output_human(result, full_table=args.full_table)
                print(output)

    except ValueError as e:
        # API key missing or invalid
        print(f"❌ CONFIGURATION ERROR: {e}", file=sys.stderr)
        sys.exit(1)
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
