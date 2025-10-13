#!/usr/bin/env python3
"""
CLI interface for correlation and covariance analysis.

WHAT: Command-line tool for Finance Guru agents to analyze portfolio diversification
WHY: Simple interface for Strategy Advisor, Quant Analyst, and Risk Assessment workflows
ARCHITECTURE: Layer 3 of 3-layer type-safe architecture

USAGE:
    # Basic correlation analysis (2+ tickers required)
    uv run python src/analysis/correlation_cli.py TSLA PLTR NVDA --days 90

    # Rolling correlation analysis
    uv run python src/analysis/correlation_cli.py TSLA SPY --days 252 --rolling 60

    # JSON output for programmatic use
    uv run python src/analysis/correlation_cli.py TSLA PLTR NVDA --days 90 --output json

    # Quick pairwise correlation check
    uv run python src/analysis/correlation_cli.py TSLA SPY --days 90

AGENT USE CASES:
- Strategy Advisor: Portfolio diversification assessment and rebalancing signals
- Quant Analyst: Correlation matrices for optimization, factor analysis
- Market Researcher: Identify hedge opportunities (negative correlations)
- Risk Assessment: Concentration risk monitoring, correlation regime shifts
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

from src.models.correlation_inputs import (
    CorrelationConfig,
    PortfolioPriceData,
)
from src.analysis.correlation import calculate_correlation


def fetch_portfolio_data(tickers: list[str], days: int) -> PortfolioPriceData:
    """
    Fetch synchronized price data for multiple assets.

    EDUCATIONAL NOTE:
    For correlation analysis, we need SYNCHRONIZED data - same dates for all assets.
    We fetch all tickers together and align them to ensure apples-to-apples comparison.

    Args:
        tickers: List of ticker symbols
        days: Number of days of historical data

    Returns:
        PortfolioPriceData with synchronized prices

    Raises:
        ValueError: If data cannot be fetched or tickers have insufficient overlap
    """
    # Fetch extra days to account for weekends/holidays
    start_date = datetime.now() - timedelta(days=days + 30)
    end_date = datetime.now()

    # Download all tickers at once for alignment
    print(f"Fetching {days} days of data for {len(tickers)} assets...", file=sys.stderr)
    data = yf.download(
        tickers,
        start=start_date,
        end=end_date,
        progress=False,
        group_by='ticker'
    )

    if data.empty:
        raise ValueError(f"No data found for tickers: {tickers}")

    # Extract close prices for each ticker
    prices_dict = {}

    if len(tickers) == 1:
        # Single ticker - yfinance returns different structure
        ticker = tickers[0]
        if 'Close' not in data.columns:
            raise ValueError(f"No close price data for {ticker}")
        prices_dict[ticker] = data['Close'].dropna().tolist()
        dates = data['Close'].dropna().index.tolist()
    else:
        # Multiple tickers
        for ticker in tickers:
            if ticker not in data:
                raise ValueError(f"No data found for {ticker}")

            closes = data[ticker]['Close'].dropna()
            if len(closes) < 30:
                raise ValueError(
                    f"Insufficient data for {ticker}. Need at least 30 days, got {len(closes)}"
                )

            prices_dict[ticker] = closes.tolist()

        # Get common dates (intersection across all tickers)
        # This ensures synchronized data
        common_index = data[tickers[0]]['Close'].dropna().index
        for ticker in tickers[1:]:
            ticker_index = data[ticker]['Close'].dropna().index
            common_index = common_index.intersection(ticker_index)

        if len(common_index) < 30:
            raise ValueError(
                f"Insufficient overlapping dates. Need at least 30, got {len(common_index)}"
            )

        # Truncate to common dates
        dates = common_index[-days:].tolist()
        for ticker in tickers:
            prices_dict[ticker] = data[ticker]['Close'].loc[dates].tolist()

    # Take only requested number of days
    if len(tickers) == 1:
        dates = dates[-days:]
        prices_dict[tickers[0]] = prices_dict[tickers[0]][-days:]
    else:
        dates = dates[-days:]

    # Convert datetime to date
    dates = [d.date() for d in dates]

    return PortfolioPriceData(
        tickers=tickers,
        dates=dates,
        prices=prices_dict,
    )


def format_human_output(result) -> str:
    """
    Format correlation analysis for human-readable display.

    EDUCATIONAL NOTE:
    This output is designed to give agents (and you) quick insights into:
    - Overall portfolio diversification quality
    - Specific pairwise correlations
    - Concentration risk warnings
    - Hedge opportunities (negative correlations)

    Args:
        result: PortfolioCorrelationOutput

    Returns:
        Formatted string output
    """
    lines = []
    lines.append(f"\n{'='*60}")
    lines.append("CORRELATION ANALYSIS")
    lines.append(f"Date: {result.calculation_date}")
    lines.append(f"Assets: {', '.join(result.tickers)}")
    lines.append(f"{'='*60}\n")

    # Diversification Score (most important summary)
    score = result.diversification_score
    if score > 0.6:
        score_emoji = "🟢"
        score_label = "EXCELLENT"
    elif score > 0.4:
        score_emoji = "🔵"
        score_label = "GOOD"
    elif score > 0.2:
        score_emoji = "🟡"
        score_label = "MODERATE"
    else:
        score_emoji = "🔴"
        score_label = "POOR"

    lines.append(f"DIVERSIFICATION SCORE: {score_emoji} {score:.3f} ({score_label})")
    lines.append(
        f"Average Correlation: {result.correlation_matrix.average_correlation:.3f}"
    )

    if result.concentration_warning:
        lines.append("⚠️  CONCENTRATION RISK WARNING: Average correlation > 0.7")

    lines.append("")

    # Position sizing guidance
    if score > 0.6:
        guidance = "Portfolio is well diversified - standard position sizing applies"
    elif score > 0.4:
        guidance = "Moderate diversification - consider adding uncorrelated assets"
    elif score > 0.2:
        guidance = "Limited diversification - reduce position sizes or add hedges"
    else:
        guidance = "⚠️  HIGH CONCENTRATION - holdings are highly correlated!"

    lines.append(f"💡 Portfolio Guidance: {guidance}")
    lines.append("")

    # Correlation Matrix
    lines.append("CORRELATION MATRIX")
    lines.append("-" * 60)

    # Header row
    header = "        " + "  ".join(f"{t:>8}" for t in result.tickers)
    lines.append(header)

    # Matrix rows
    corr_matrix = result.correlation_matrix.correlation_matrix
    for ticker1 in result.tickers:
        row_values = []
        for ticker2 in result.tickers:
            corr_val = corr_matrix[ticker1][ticker2]
            row_values.append(f"{corr_val:8.3f}")
        row_line = f"{ticker1:>8}" + "  ".join(row_values)
        lines.append(row_line)

    lines.append("")

    # Highlight interesting pairs
    lines.append("KEY INSIGHTS")
    lines.append("-" * 60)

    # Find strongest positive correlations (excluding diagonal)
    correlations_list = []
    for i, ticker1 in enumerate(result.tickers):
        for j, ticker2 in enumerate(result.tickers):
            if i < j:  # Upper triangle only
                corr = corr_matrix[ticker1][ticker2]
                correlations_list.append((ticker1, ticker2, corr))

    # Sort by absolute correlation (strongest relationships first)
    correlations_list.sort(key=lambda x: abs(x[2]), reverse=True)

    # Show top correlations
    for ticker1, ticker2, corr in correlations_list[:5]:
        if corr > 0.7:
            emoji = "🔴"
            label = "VERY HIGH"
        elif corr > 0.5:
            emoji = "🟡"
            label = "HIGH"
        elif corr > 0.3:
            emoji = "🔵"
            label = "MODERATE"
        elif corr > 0:
            emoji = "🟢"
            label = "LOW"
        else:
            emoji = "✅"
            label = "HEDGE"

        lines.append(f"{emoji} {ticker1} / {ticker2}: {corr:+.3f} ({label})")

    lines.append("")

    # Rolling correlations summary (if available)
    if result.rolling_correlations:
        lines.append("ROLLING CORRELATION ANALYSIS")
        lines.append("-" * 60)

        for rolling in result.rolling_correlations[:3]:  # Show first 3 pairs
            corr_min, corr_max = rolling.correlation_range
            range_width = corr_max - corr_min

            lines.append(f"\n{rolling.ticker_1} / {rolling.ticker_2}:")
            lines.append(f"  Current: {rolling.current_correlation:+.3f}")
            lines.append(f"  Average: {rolling.average_correlation:+.3f}")
            lines.append(f"  Range: {corr_min:+.3f} to {corr_max:+.3f} (width: {range_width:.3f})")

            if range_width > 0.5:
                lines.append("  ⚠️  High variability - correlation is unstable")
            if rolling.current_correlation > rolling.average_correlation + 0.2:
                lines.append("  📈 Correlation increasing (diversification weakening)")
            elif rolling.current_correlation < rolling.average_correlation - 0.2:
                lines.append("  📉 Correlation decreasing (diversification improving)")

        lines.append("")

    lines.append(f"{'='*60}\n")

    return "\n".join(lines)


def format_json_output(result) -> str:
    """
    Format correlation analysis as JSON.

    Args:
        result: PortfolioCorrelationOutput

    Returns:
        JSON string
    """
    # Convert Pydantic model to dict, then to JSON
    return json.dumps(result.model_dump(), indent=2, default=str)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Calculate correlation and covariance for Finance Guru agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic portfolio correlation
  uv run python src/analysis/correlation_cli.py TSLA PLTR NVDA --days 90

  # Pairwise correlation check
  uv run python src/analysis/correlation_cli.py TSLA SPY --days 90

  # Rolling correlation (time-varying)
  uv run python src/analysis/correlation_cli.py TSLA SPY --days 252 --rolling 60

  # JSON output
  uv run python src/analysis/correlation_cli.py TSLA PLTR NVDA --days 90 --output json

Agent Use Cases:
  - Strategy Advisor: Diversification assessment, rebalancing signals
  - Quant Analyst: Correlation matrices for optimization
  - Risk Assessment: Concentration risk, correlation regime shifts
        """,
    )

    # Required arguments
    parser.add_argument(
        'tickers',
        type=str,
        nargs='+',
        help='Stock ticker symbols (minimum 2 required, e.g., TSLA PLTR NVDA)'
    )

    parser.add_argument(
        '--days',
        type=int,
        default=90,
        help='Number of days of historical data (default: 90)'
    )

    # Correlation configuration
    parser.add_argument(
        '--method',
        choices=['pearson', 'spearman'],
        default='pearson',
        help='Correlation method (default: pearson)'
    )

    parser.add_argument(
        '--rolling',
        type=int,
        default=None,
        help='Rolling window for time-varying correlation (e.g., 60 for 60-day rolling)'
    )

    parser.add_argument(
        '--min-periods',
        type=int,
        default=30,
        help='Minimum periods for rolling correlation (default: 30)'
    )

    # Output format
    parser.add_argument(
        '--output',
        choices=['human', 'json'],
        default='human',
        help='Output format (default: human)'
    )

    args = parser.parse_args()

    # Validate minimum tickers
    if len(args.tickers) < 2:
        print("Error: At least 2 tickers required for correlation analysis", file=sys.stderr)
        return 1

    try:
        # Fetch portfolio data
        print(
            f"Fetching synchronized data for {len(args.tickers)} assets...",
            file=sys.stderr
        )
        data = fetch_portfolio_data(args.tickers, args.days)

        # Create configuration
        config = CorrelationConfig(
            method=args.method,
            rolling_window=args.rolling,
            min_periods=args.min_periods,
        )

        # Calculate correlation
        print("Calculating correlation analysis...", file=sys.stderr)
        result = calculate_correlation(data, config)

        # Output results
        if args.output == 'json':
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


if __name__ == '__main__':
    sys.exit(main())
