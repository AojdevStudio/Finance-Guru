#!/usr/bin/env python3
"""
Input Validation CLI for Finance Guru™

This module provides command-line access to data quality validation functionality.
Finance Guru agents use this CLI to validate data before performing analysis.

ARCHITECTURE NOTE:
This is Layer 3 of our 3-layer architecture:
    Layer 1: Pydantic Models - Data validation (validation_inputs.py)
    Layer 2: Calculator Classes - Business logic (input_validation.py)
    Layer 3: CLI Interface (THIS FILE) - Agent integration

USAGE:
    # Validate a single ticker
    uv run python src/utils/input_validation_cli.py TSLA --days 90

    # Use IQR method for outlier detection
    uv run python src/utils/input_validation_cli.py NVDA --outlier-method iqr

    # Strict validation (low thresholds)
    uv run python src/utils/input_validation_cli.py PLTR --outlier-threshold 2.0

    # JSON output for programmatic use
    uv run python src/utils/input_validation_cli.py AAPL --output json

AGENT USE CASES:
    - Quant Analyst: Validate data before running calculations
    - Market Researcher: Check data quality for new tickers
    - Compliance Officer: Verify data integrity for reports
    - Strategy Advisor: Ensure data reliability before backtesting

Author: Finance Guru™ Development Team
Created: 2026-01-16
"""

import argparse
import json
import sys
from datetime import date, timedelta

from src.models.validation_inputs import (
    OutlierMethod,
    PriceSeriesInput,
    ValidationConfig,
)
from src.utils.input_validation import InputValidator
from src.utils.market_data import MarketDataFetcher


def print_validation_summary(result, output_format: str = "text") -> None:
    """
    Print validation results in human-readable or JSON format.

    Args:
        result: ValidationOutput from validator
        output_format: "text" or "json"
    """
    if output_format == "json":
        # Convert to dict for JSON serialization
        print(json.dumps(result.model_dump(), indent=2, default=str))
        return

    # Text output for humans and Claude agents
    print(f"\n{'=' * 70}")
    print(f"DATA VALIDATION REPORT: {result.ticker}")
    print(f"{'=' * 70}")
    print(f"Validation Date: {result.validation_date}")
    print(f"Total Data Points: {result.total_points}")
    print()

    # Overall status
    status_symbol = "✓" if result.is_valid else "✗"
    status_text = "VALID" if result.is_valid else "INVALID"
    print(f"Overall Status: {status_symbol} {status_text}")
    print()

    # Quality scores
    print("Quality Scores:")
    print(
        f"  Completeness:  {result.completeness_score:>6.1%} ({_score_grade(result.completeness_score)})"
    )
    print(
        f"  Consistency:   {result.consistency_score:>6.1%} ({_score_grade(result.consistency_score)})"
    )
    print(
        f"  Reliability:   {result.reliability_score:>6.1%} ({_score_grade(result.reliability_score)})"
    )
    print()

    # Issue summary
    print("Issue Summary:")
    print(f"  Missing Data:     {result.missing_count:>4} points")
    print(f"  Outliers:         {result.outlier_count:>4} points")
    print(f"  Date Gaps:        {result.gap_count:>4} gaps")
    print(f"  Potential Splits: {result.potential_splits:>4} events")
    print()

    # Warnings
    if result.warnings:
        print("Warnings:")
        for warning in result.warnings:
            print(f"  ⚠  {warning}")
        print()

    # Detailed anomalies (show top 10)
    if result.anomalies:
        print(f"Anomalies Detected ({len(result.anomalies)} total):")
        display_anomalies = result.anomalies[:10]

        for i, anomaly in enumerate(display_anomalies, 1):
            severity_symbol = _severity_symbol(anomaly.severity)
            print(f"\n  {i}. {severity_symbol} {anomaly.description}")
            if anomaly.location:
                print(f"     Location: {anomaly.location}")
            if anomaly.value is not None:
                print(f"     Value: {anomaly.value}")
            print(f"     → {anomaly.recommendation}")

        if len(result.anomalies) > 10:
            print(f"\n  ... and {len(result.anomalies) - 10} more anomalies")
        print()

    # Recommendations
    print("Recommendations:")
    for rec in result.recommendations:
        print(f"  {rec}")

    print(f"{'=' * 70}\n")


def _score_grade(score: float) -> str:
    """Convert score to letter grade."""
    if score >= 0.98:
        return "A+"
    elif score >= 0.95:
        return "A"
    elif score >= 0.90:
        return "B"
    elif score >= 0.85:
        return "C"
    elif score >= 0.80:
        return "D"
    else:
        return "F"


def _severity_symbol(severity: str) -> str:
    """Get symbol for severity level."""
    symbols = {
        "low": "ℹ",
        "medium": "⚠",
        "high": "⚠⚠",
        "critical": "🚨",
    }
    return symbols.get(severity, "?")


def validate_ticker(
    ticker: str,
    days: int,
    outlier_method: str,
    outlier_threshold: float,
    missing_threshold: float,
    max_gap_days: int,
    check_splits: bool,
    split_threshold: float,
    output_format: str,
) -> int:
    """
    Validate data for a single ticker.

    Returns:
        0 if data is valid, 1 if invalid
    """
    print(f"Fetching {days} days of data for {ticker}...", file=sys.stderr)

    # Fetch market data
    fetcher = MarketDataFetcher()

    try:
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        # Get historical data
        data = fetcher.get_historical_data(
            ticker=ticker,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
        )

        if data is None or len(data) < 10:
            print(f"Error: Insufficient data for {ticker}", file=sys.stderr)
            return 1

        # Convert to PriceSeriesInput
        price_series = PriceSeriesInput(
            ticker=ticker,
            prices=data["Close"].tolist(),
            dates=[
                date.fromisoformat(d) for d in data.index.strftime("%Y-%m-%d").tolist()
            ],
            volumes=data["Volume"].tolist() if "Volume" in data.columns else None,
        )

    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}", file=sys.stderr)
        return 1

    # Create validation config
    config = ValidationConfig(
        outlier_method=OutlierMethod(outlier_method),
        outlier_threshold=outlier_threshold,
        missing_data_threshold=missing_threshold,
        max_gap_days=max_gap_days,
        check_splits=check_splits,
        split_threshold=split_threshold,
    )

    # Run validation
    validator = InputValidator(config)
    result = validator.validate_price_series(price_series)

    # Print results
    print_validation_summary(result, output_format)

    # Return exit code
    return 0 if result.is_valid else 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Validate data quality for financial time series",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate with default settings
  %(prog)s TSLA

  # Use 252 days (1 trading year)
  %(prog)s NVDA --days 252

  # Use IQR method for outlier detection
  %(prog)s PLTR --outlier-method iqr --outlier-threshold 2.5

  # Strict validation
  %(prog)s AAPL --outlier-threshold 2.0 --missing-threshold 0.02

  # JSON output for programmatic use
  %(prog)s SPY --output json

Agent Use Cases:
  Quant Analyst:       Validate before calculations
  Market Researcher:   Check new ticker data quality
  Compliance Officer:  Verify data integrity
  Strategy Advisor:    Ensure backtesting reliability
        """,
    )

    # Required arguments
    parser.add_argument(
        "ticker", type=str, help="Stock ticker symbol (e.g., TSLA, AAPL, SPY)"
    )

    # Optional arguments
    parser.add_argument(
        "--days",
        type=int,
        default=90,
        help="Number of days of history to validate (default: 90, quarter)",
    )

    parser.add_argument(
        "--outlier-method",
        type=str,
        choices=["z_score", "iqr", "modified_z"],
        default="z_score",
        help="Method for detecting outliers (default: z_score)",
    )

    parser.add_argument(
        "--outlier-threshold",
        type=float,
        default=3.0,
        help="Threshold for outlier detection (default: 3.0)",
    )

    parser.add_argument(
        "--missing-threshold",
        type=float,
        default=0.05,
        help="Maximum acceptable missing data ratio (default: 0.05 = 5%%)",
    )

    parser.add_argument(
        "--max-gap-days",
        type=int,
        default=10,
        help="Maximum acceptable gap between dates (default: 10 days)",
    )

    parser.add_argument(
        "--no-check-splits", action="store_true", help="Disable stock split detection"
    )

    parser.add_argument(
        "--split-threshold",
        type=float,
        default=0.25,
        help="Price change threshold for split detection (default: 0.25 = 25%%)",
    )

    parser.add_argument(
        "--output",
        type=str,
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    args = parser.parse_args()

    # Validate ticker
    exit_code = validate_ticker(
        ticker=args.ticker.upper(),
        days=args.days,
        outlier_method=args.outlier_method,
        outlier_threshold=args.outlier_threshold,
        missing_threshold=args.missing_threshold,
        max_gap_days=args.max_gap_days,
        check_splits=not args.no_check_splits,
        split_threshold=args.split_threshold,
        output_format=args.output,
    )

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
