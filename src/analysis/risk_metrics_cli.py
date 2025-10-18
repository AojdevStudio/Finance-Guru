#!/usr/bin/env python3
"""
Risk Metrics CLI for Finance Guru™ Agents

This module provides a command-line interface for calculating risk metrics.
Designed for easy integration with Finance Guru agents.

ARCHITECTURE NOTE:
This is Layer 3 of our 3-layer architecture:
    Layer 1: Pydantic Models - Data validation
    Layer 2: Calculator Classes - Business logic
    Layer 3: CLI Interface (THIS FILE) - Agent integration

AGENT USAGE:
    # Basic usage (30 days of data required)
    uv run python src/analysis/risk_metrics_cli.py TSLA --days 90

    # With benchmark (calculate beta/alpha)
    uv run python src/analysis/risk_metrics_cli.py TSLA --days 90 --benchmark SPY

    # Custom configuration
    uv run python src/analysis/risk_metrics_cli.py TSLA --days 252 \\
        --confidence 0.99 \\
        --var-method parametric \\
        --risk-free-rate 0.05

    # JSON output (for programmatic parsing)
    uv run python src/analysis/risk_metrics_cli.py TSLA --days 90 --output json

    # Save to file
    uv run python src/analysis/risk_metrics_cli.py TSLA --days 90 \\
        --output json \\
        --save-to analysis/tsla-risk-2025-10-13.json

EDUCATIONAL NOTE:
This CLI makes it easy for agents to calculate risk metrics without
writing Python code. The tool:
1. Fetches price data automatically (uses market_data.py)
2. Validates all inputs (Pydantic models)
3. Calculates all metrics (RiskCalculator)
4. Formats output (human-readable or JSON)
5. Optionally saves results to file

Author: Finance Guru™ Development Team
Created: 2025-10-13
"""

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import our type-safe components
from src.models.risk_inputs import (
    PriceDataInput,
    RiskCalculationConfig,
    RiskMetricsOutput,
)
from src.analysis.risk_metrics import RiskCalculator


def fetch_price_data(ticker: str, days: int) -> PriceDataInput:
    """
    Fetch historical price data for a ticker.

    EDUCATIONAL NOTE:
    This function integrates with your existing market_data.py utility.
    It fetches price data and converts it to our validated PriceDataInput model.

    Args:
        ticker: Stock ticker symbol
        days: Number of days of historical data

    Returns:
        PriceDataInput: Validated price data

    Raises:
        ValueError: If unable to fetch data or insufficient data points
    """
    try:
        # Import yfinance for data fetching
        import yfinance as yf

        # Calculate date range
        end_date = date.today()
        # Need ~1.5x calendar days to get requested trading days (accounts for weekends/holidays)
        start_date = end_date - timedelta(days=int(days * 1.5))

        # Fetch data
        ticker_obj = yf.Ticker(ticker)
        hist = ticker_obj.history(start=start_date, end=end_date)

        if hist.empty:
            raise ValueError(f"No data found for ticker {ticker}")

        # Extract prices and dates
        prices = hist['Close'].tolist()
        dates = [d.date() for d in hist.index]

        # Ensure we have minimum required data points
        if len(prices) < 30:
            raise ValueError(
                f"Insufficient data: got {len(prices)} days, need at least 30. "
                f"Try increasing --days parameter."
            )

        # Create validated model
        return PriceDataInput(
            ticker=ticker.upper(),
            prices=prices,
            dates=dates,
        )

    except ImportError:
        print("ERROR: yfinance not installed. Run: uv add yfinance", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR fetching data for {ticker}: {e}", file=sys.stderr)
        sys.exit(1)


def format_output_human(results: RiskMetricsOutput) -> str:
    """
    Format results in human-readable format.

    EDUCATIONAL NOTE:
    This creates a nicely formatted report that's easy to read in the terminal.
    Uses emojis and colors (if terminal supports it) for visual appeal.

    Args:
        results: Calculated risk metrics

    Returns:
        Formatted string for display
    """
    from datetime import date as date_type

    output = []
    output.append("=" * 70)
    output.append(f"📊 RISK ANALYSIS: {results.ticker}")
    output.append(f"📅 Data Through: {results.calculation_date} (most recent market close)")

    # Show if data is stale (more than 3 days old)
    days_old = (date_type.today() - results.calculation_date).days
    if days_old > 3:
        output.append(f"⚠️  Note: Data is {days_old} days old - market may be closed or data delayed")

    output.append("=" * 70)
    output.append("")

    # Value at Risk Section
    output.append("📉 VALUE AT RISK (VaR)")
    output.append("-" * 70)
    output.append(f"  95% VaR (Daily):          {results.var_95:>10.2%}")
    output.append(f"  95% CVaR (Daily):         {results.cvar_95:>10.2%}")
    output.append("")
    output.append(f"  💡 Interpretation: 95% of days, losses won't exceed {abs(results.var_95):.2%}")
    output.append(f"     When losses DO exceed VaR, average loss is {abs(results.cvar_95):.2%}")
    output.append("")

    # Risk-Adjusted Returns Section
    output.append("📈 RISK-ADJUSTED RETURNS")
    output.append("-" * 70)
    output.append(f"  Sharpe Ratio:             {results.sharpe_ratio:>10.2f}")
    output.append(f"  Sortino Ratio:            {results.sortino_ratio:>10.2f}")
    output.append("")

    # Interpret Sharpe Ratio
    if results.sharpe_ratio < 1.0:
        sharpe_interpretation = "Poor (< 1.0)"
    elif results.sharpe_ratio < 2.0:
        sharpe_interpretation = "Good (1.0-2.0)"
    else:
        sharpe_interpretation = "Excellent (> 2.0)"
    output.append(f"  💡 Sharpe Rating: {sharpe_interpretation}")
    output.append("")

    # Drawdown Section
    output.append("📊 DRAWDOWN ANALYSIS")
    output.append("-" * 70)
    output.append(f"  Maximum Drawdown:         {results.max_drawdown:>10.2%}")
    output.append(f"  Calmar Ratio:             {results.calmar_ratio:>10.2f}")
    output.append("")
    output.append(f"  💡 Worst peak-to-trough decline was {abs(results.max_drawdown):.2%}")
    output.append("")

    # Volatility Section
    output.append("🎢 VOLATILITY")
    output.append("-" * 70)
    output.append(f"  Annual Volatility:        {results.annual_volatility:>10.2%}")
    output.append("")

    # Interpret volatility
    if results.annual_volatility < 0.20:
        vol_interpretation = "Low (< 20%)"
    elif results.annual_volatility < 0.40:
        vol_interpretation = "Medium (20%-40%)"
    elif results.annual_volatility < 0.80:
        vol_interpretation = "High (40%-80%)"
    else:
        vol_interpretation = "Extreme (> 80%)"
    output.append(f"  💡 Volatility Level: {vol_interpretation}")
    output.append("")

    # Beta/Alpha Section (if available)
    if results.beta is not None and results.alpha is not None:
        output.append("🎯 MARKET RELATIONSHIP")
        output.append("-" * 70)
        output.append(f"  Beta (vs Benchmark):      {results.beta:>10.2f}")
        output.append(f"  Alpha (vs Benchmark):     {results.alpha:>10.2%}")
        output.append("")

        # Interpret Beta
        if results.beta < 0.5:
            beta_interpretation = "Low systematic risk (defensive)"
        elif results.beta < 1.5:
            beta_interpretation = "Average systematic risk"
        else:
            beta_interpretation = "High systematic risk (aggressive)"
        output.append(f"  💡 Beta Category: {beta_interpretation}")

        # Interpret Alpha
        if results.alpha > 0:
            output.append(f"     Alpha: Outperforming by {results.alpha:.2%} annually")
        else:
            output.append(f"     Alpha: Underperforming by {abs(results.alpha):.2%} annually")
        output.append("")

    # Footer
    output.append("=" * 70)
    output.append("⚠️  DISCLAIMER: For educational purposes only. Not investment advice.")
    output.append("=" * 70)

    return "\n".join(output)


def format_output_json(results: RiskMetricsOutput) -> str:
    """
    Format results as JSON.

    EDUCATIONAL NOTE:
    JSON output is perfect for programmatic parsing by agents.
    The Pydantic model has a .model_dump_json() method that handles
    serialization (including date objects) automatically.

    Args:
        results: Calculated risk metrics

    Returns:
        JSON string
    """
    return results.model_dump_json(indent=2)


def main():
    """
    Main CLI entry point.

    EDUCATIONAL NOTE:
    This function:
    1. Parses command-line arguments
    2. Fetches price data
    3. Creates configuration
    4. Runs calculations
    5. Formats and displays/saves output
    """
    # Create argument parser
    parser = argparse.ArgumentParser(
        description="Calculate risk metrics for Finance Guru™",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage (30 days required minimum)
  %(prog)s TSLA --days 90

  # With benchmark for beta/alpha
  %(prog)s TSLA --days 90 --benchmark SPY

  # Custom configuration
  %(prog)s TSLA --days 252 --confidence 0.99 --var-method parametric

  # JSON output
  %(prog)s TSLA --days 90 --output json

  # Save to file
  %(prog)s TSLA --days 90 --output json --save-to analysis/risk.json
        """
    )

    # Required arguments
    parser.add_argument(
        "ticker",
        type=str,
        help="Stock ticker symbol (e.g., TSLA, AAPL, SPY)"
    )

    # Data parameters
    parser.add_argument(
        "--days",
        type=int,
        default=252,
        help="Number of days of historical data (default: 252 = 1 year)"
    )

    parser.add_argument(
        "--benchmark",
        type=str,
        default=None,
        help="Benchmark ticker for beta/alpha calculation (e.g., SPY)"
    )

    # Risk calculation parameters
    parser.add_argument(
        "--confidence",
        type=float,
        default=0.95,
        help="Confidence level for VaR (default: 0.95 = 95%%)"
    )

    parser.add_argument(
        "--var-method",
        type=str,
        choices=["historical", "parametric"],
        default="historical",
        help="VaR calculation method (default: historical)"
    )

    parser.add_argument(
        "--risk-free-rate",
        type=float,
        default=0.045,
        help="Annual risk-free rate (default: 0.045 = 4.5%%)"
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
        print("ERROR: --days must be at least 30 for statistical validity", file=sys.stderr)
        sys.exit(1)

    try:
        # Step 1: Fetch price data
        print(f"📥 Fetching {args.days} days of data for {args.ticker}...", file=sys.stderr)
        price_data = fetch_price_data(args.ticker, args.days)
        print(f"✅ Fetched {len(price_data.prices)} data points", file=sys.stderr)
        print(f"📅 Latest data: {price_data.dates[-1]} (most recent market close)", file=sys.stderr)

        # Step 2: Fetch benchmark data (if requested)
        benchmark_data = None
        if args.benchmark:
            print(f"📥 Fetching benchmark data for {args.benchmark}...", file=sys.stderr)
            benchmark_data = fetch_price_data(args.benchmark, args.days)
            print(f"✅ Fetched {len(benchmark_data.prices)} benchmark points", file=sys.stderr)

        # Step 3: Create configuration
        config = RiskCalculationConfig(
            confidence_level=args.confidence,
            var_method=args.var_method,
            rolling_window=min(args.days, 252),  # Cap at 1 year
            risk_free_rate=args.risk_free_rate,
        )

        # Step 4: Calculate risk metrics
        print("🧮 Calculating risk metrics...", file=sys.stderr)
        calculator = RiskCalculator(config)
        results = calculator.calculate_risk_metrics(price_data, benchmark_data)
        print("✅ Calculation complete!", file=sys.stderr)
        print("", file=sys.stderr)  # Blank line before output

        # Step 5: Format output
        if args.output == "json":
            output = format_output_json(results)
        else:
            output = format_output_human(results)

        # Step 6: Display or save
        if args.save_to:
            # Save to file
            save_path = Path(args.save_to)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            save_path.write_text(output)
            print(f"💾 Saved to: {save_path}", file=sys.stderr)
        else:
            # Print to stdout
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
