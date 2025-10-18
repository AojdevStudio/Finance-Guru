#!/usr/bin/env python3
"""
Data Validation CLI for Finance Guru™ Agents

This module provides a command-line interface for validating data quality.
Designed for easy integration with Finance Guru agents.

ARCHITECTURE NOTE:
This is Layer 3 of our 3-layer architecture:
    Layer 1: Pydantic Models - Data validation
    Layer 2: Calculator Classes - Business logic
    Layer 3: CLI Interface (THIS FILE) - Agent integration

AGENT USAGE:
    # Basic validation
    uv run python src/utils/data_validator_cli.py TSLA --days 90

    # Custom outlier detection
    uv run python src/utils/data_validator_cli.py TSLA --days 252 \\
        --outlier-method iqr \\
        --outlier-threshold 2.5

    # Strict validation (Compliance Officer mode)
    uv run python src/utils/data_validator_cli.py TSLA --days 90 \\
        --missing-threshold 0.01 \\
        --max-gap 5

    # JSON output
    uv run python src/utils/data_validator_cli.py TSLA --days 90 --output json

    # Save report
    uv run python src/utils/data_validator_cli.py TSLA --days 90 \\
        --save-to docs/fin-guru/data-validation-tsla-2025-10-13.json

EDUCATIONAL NOTE:
This CLI helps agents verify data quality before analysis.
Use it as the first step in any workflow to catch data issues early.

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
from src.models.validation_inputs import (
    OutlierMethod,
    PriceSeriesInput,
    ValidationConfig,
    ValidationOutput,
)
from src.utils.data_validator import DataValidator


def fetch_price_data(ticker: str, days: int) -> PriceSeriesInput:
    """
    Fetch historical price data for validation.

    EDUCATIONAL NOTE:
    This function fetches price data using yfinance and converts it
    to our validated PriceSeriesInput model.

    Args:
        ticker: Stock ticker symbol
        days: Number of days of historical data

    Returns:
        PriceSeriesInput: Validated price data

    Raises:
        ValueError: If unable to fetch data
    """
    try:
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

        # Extract prices, dates, volumes
        prices = hist['Close'].tolist()
        dates = [d.date() for d in hist.index]
        volumes = hist['Volume'].tolist()

        # Ensure minimum data points
        if len(prices) < 10:
            raise ValueError(
                f"Insufficient data: got {len(prices)} days, need at least 10."
            )

        # Create validated model
        return PriceSeriesInput(
            ticker=ticker.upper(),
            prices=prices,
            dates=dates,
            volumes=volumes,
        )

    except ImportError:
        print("ERROR: yfinance not installed. Run: uv add yfinance", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR fetching data for {ticker}: {e}", file=sys.stderr)
        sys.exit(1)


def format_output_human(results: ValidationOutput) -> str:
    """
    Format validation results in human-readable format.

    Args:
        results: Validation results

    Returns:
        Formatted string for display
    """
    output = []
    output.append("=" * 70)
    output.append(f"🔍 DATA VALIDATION REPORT: {results.ticker}")
    output.append(f"📅 Validation Date: {results.validation_date}")
    output.append("=" * 70)
    output.append("")

    # Overall Status
    if results.is_valid:
        output.append("✅ OVERALL STATUS: VALID - Data is suitable for analysis")
    else:
        output.append("❌ OVERALL STATUS: INVALID - Data has critical issues")
    output.append("")

    # Quality Scores
    output.append("📊 QUALITY SCORES")
    output.append("-" * 70)
    output.append(f"  Completeness:             {results.completeness_score:>10.1%}")
    output.append(f"  Consistency:              {results.consistency_score:>10.1%}")
    output.append(f"  Overall Reliability:      {results.reliability_score:>10.1%}")
    output.append("")

    # Interpret reliability score
    if results.reliability_score >= 0.99:
        reliability_rating = "Excellent"
    elif results.reliability_score >= 0.95:
        reliability_rating = "Good"
    elif results.reliability_score >= 0.90:
        reliability_rating = "Fair"
    else:
        reliability_rating = "Poor"
    output.append(f"  💡 Quality Rating: {reliability_rating}")
    output.append("")

    # Data Summary
    output.append("📈 DATA SUMMARY")
    output.append("-" * 70)
    output.append(f"  Total Data Points:        {results.total_points:>10,}")
    output.append(f"  Missing Points:           {results.missing_count:>10,}")
    output.append(f"  Outliers Detected:        {results.outlier_count:>10,}")
    output.append(f"  Date Gaps:                {results.gap_count:>10,}")
    output.append(f"  Potential Splits:         {results.potential_splits:>10,}")
    output.append("")

    # Anomalies (if any)
    if results.anomalies:
        output.append("🚨 ANOMALIES DETECTED")
        output.append("-" * 70)

        # Group by severity
        critical = [a for a in results.anomalies if a.severity == "critical"]
        high = [a for a in results.anomalies if a.severity == "high"]
        medium = [a for a in results.anomalies if a.severity == "medium"]
        low = [a for a in results.anomalies if a.severity == "low"]

        if critical:
            output.append(f"  🔴 CRITICAL ({len(critical)} issues):")
            for i, anomaly in enumerate(critical[:5], 1):  # Show max 5
                output.append(f"     {i}. {anomaly.description}")
                if anomaly.location:
                    output.append(f"        Location: {anomaly.location}")
                output.append(f"        → {anomaly.recommendation}")
            if len(critical) > 5:
                output.append(f"     ... and {len(critical) - 5} more critical issues")

        if high:
            output.append(f"  🟠 HIGH ({len(high)} issues):")
            for i, anomaly in enumerate(high[:3], 1):  # Show max 3
                output.append(f"     {i}. {anomaly.description}")
                if anomaly.location:
                    output.append(f"        Location: {anomaly.location}")
            if len(high) > 3:
                output.append(f"     ... and {len(high) - 3} more high-severity issues")

        if medium:
            output.append(f"  🟡 MEDIUM ({len(medium)} issues) - Review recommended")

        if low:
            output.append(f"  🟢 LOW ({len(low)} issues) - Minor concerns")

        output.append("")

    # Warnings
    if results.warnings:
        output.append("⚠️  WARNINGS")
        output.append("-" * 70)
        for warning in results.warnings:
            output.append(f"  • {warning}")
        output.append("")

    # Recommendations
    if results.recommendations:
        output.append("💡 RECOMMENDATIONS")
        output.append("-" * 70)
        for i, rec in enumerate(results.recommendations, 1):
            output.append(f"  {i}. {rec}")
        output.append("")

    # Footer
    output.append("=" * 70)
    output.append("ℹ️  Use --output json for machine-readable format")
    output.append("=" * 70)

    return "\n".join(output)


def format_output_json(results: ValidationOutput) -> str:
    """
    Format validation results as JSON.

    Args:
        results: Validation results

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
    3. Creates validation configuration
    4. Runs validation checks
    5. Formats and displays/saves results
    """
    # Create argument parser
    parser = argparse.ArgumentParser(
        description="Validate data quality for Finance Guru™",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic validation
  %(prog)s TSLA --days 90

  # Custom outlier detection (IQR method, more robust)
  %(prog)s TSLA --days 252 --outlier-method iqr --outlier-threshold 2.5

  # Strict validation (Compliance Officer mode)
  %(prog)s TSLA --days 90 --missing-threshold 0.01 --max-gap 5

  # Check for stock splits
  %(prog)s TSLA --days 252 --check-splits --split-threshold 0.30

  # JSON output for programmatic use
  %(prog)s TSLA --days 90 --output json

  # Save validation report
  %(prog)s TSLA --days 90 --save-to docs/validation-report.json
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
        default=90,
        help="Number of days of historical data (default: 90)"
    )

    # Validation parameters
    parser.add_argument(
        "--outlier-method",
        type=str,
        choices=["z_score", "iqr", "modified_z"],
        default="z_score",
        help="Outlier detection method (default: z_score)"
    )

    parser.add_argument(
        "--outlier-threshold",
        type=float,
        default=3.0,
        help="Outlier detection threshold (default: 3.0)"
    )

    parser.add_argument(
        "--missing-threshold",
        type=float,
        default=0.05,
        help="Maximum acceptable missing data ratio (default: 0.05 = 5%%)"
    )

    parser.add_argument(
        "--max-gap",
        type=int,
        default=10,
        help="Maximum acceptable gap between dates in days (default: 10)"
    )

    parser.add_argument(
        "--check-splits",
        action="store_true",
        default=True,
        help="Check for potential stock splits (default: enabled)"
    )

    parser.add_argument(
        "--no-check-splits",
        action="store_false",
        dest="check_splits",
        help="Disable stock split checking"
    )

    parser.add_argument(
        "--split-threshold",
        type=float,
        default=0.25,
        help="Price change threshold for split detection (default: 0.25 = 25%%)"
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

    # Validate parameters
    if args.days < 10:
        print("ERROR: --days must be at least 10", file=sys.stderr)
        sys.exit(1)

    if not (1.5 <= args.outlier_threshold <= 5.0):
        print("ERROR: --outlier-threshold must be between 1.5 and 5.0", file=sys.stderr)
        sys.exit(1)

    if not (0.0 <= args.missing_threshold <= 0.50):
        print("ERROR: --missing-threshold must be between 0.0 and 0.50", file=sys.stderr)
        sys.exit(1)

    try:
        # Step 1: Fetch price data
        print(f"📥 Fetching {args.days} days of data for {args.ticker}...", file=sys.stderr)
        price_series = fetch_price_data(args.ticker, args.days)
        print(f"✅ Fetched {len(price_series.prices)} data points", file=sys.stderr)
        print(f"📅 Date range: {price_series.dates[0]} to {price_series.dates[-1]}", file=sys.stderr)

        # Step 2: Create configuration
        config = ValidationConfig(
            outlier_method=OutlierMethod(args.outlier_method),
            outlier_threshold=args.outlier_threshold,
            missing_data_threshold=args.missing_threshold,
            max_gap_days=args.max_gap,
            check_splits=args.check_splits,
            split_threshold=args.split_threshold,
        )

        # Step 3: Run validation
        print("🔍 Running data quality checks...", file=sys.stderr)
        validator = DataValidator(config)
        results = validator.validate(price_series)

        # Show quick status
        if results.is_valid:
            print("✅ Validation complete - Data is VALID", file=sys.stderr)
        else:
            print("❌ Validation complete - Data has ISSUES", file=sys.stderr)
        print("", file=sys.stderr)  # Blank line before output

        # Step 4: Format output
        if args.output == "json":
            output = format_output_json(results)
        else:
            output = format_output_human(results)

        # Step 5: Display or save
        if args.save_to:
            save_path = Path(args.save_to)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            save_path.write_text(output)
            print(f"💾 Saved to: {save_path}", file=sys.stderr)
        else:
            print(output)

        # Exit with appropriate code
        sys.exit(0 if results.is_valid else 1)

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
