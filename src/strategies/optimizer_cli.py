#!/usr/bin/env python3
"""
CLI interface for portfolio optimization.

WHAT: Command-line tool for Finance Guru agents to optimize portfolio allocation
WHY: Simple interface for Strategy Advisor, Quant Analyst, and Compliance Officer workflows
ARCHITECTURE: Layer 3 of 3-layer type-safe architecture

USAGE:
    # Maximum Sharpe ratio optimization
    uv run python src/strategies/optimizer_cli.py TSLA PLTR NVDA SPY --days 252 --method max_sharpe

    # Risk parity allocation (all-weather portfolio)
    uv run python src/strategies/optimizer_cli.py TSLA PLTR NVDA SPY --days 252 --method risk_parity

    # Minimum variance (defensive)
    uv run python src/strategies/optimizer_cli.py TSLA PLTR NVDA SPY --days 252 --method min_variance

    # With position limits (max 30% per position)
    uv run python src/strategies/optimizer_cli.py TSLA PLTR NVDA SPY --days 252 --method max_sharpe --max-position 0.30

    # Black-Litterman with views
    uv run python src/strategies/optimizer_cli.py TSLA PLTR NVDA --days 252 --method black_litterman \
        --view TSLA:0.15 --view PLTR:0.20

    # JSON output
    uv run python src/strategies/optimizer_cli.py TSLA PLTR NVDA SPY --days 252 --method max_sharpe --output json

AGENT USE CASES:
- Strategy Advisor: Generate optimal allocation for $500k capital deployment
- Quant Analyst: Compare different optimization methods
- Compliance Officer: Verify position limits and concentration risk
- Risk Assessment: Evaluate portfolio expected risk-return profile

EDUCATIONAL NOTE:
This tool is HIGHEST VALUE for your $500k portfolio management.
Use it monthly to:
1. Optimize new capital deployment ($5-10k per month)
2. Rebalance existing holdings when drift occurs
3. Compare methods (Max Sharpe vs Risk Parity for your goals)
4. Assess impact of position limits on returns
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import yfinance as yf

from src.models.portfolio_inputs import (
    OptimizationConfig,
    PortfolioDataInput,
)
from src.strategies.optimizer import optimize_portfolio


def fetch_portfolio_data(tickers: list[str], days: int) -> PortfolioDataInput:
    """
    Fetch synchronized price data for portfolio optimization.

    EDUCATIONAL NOTE:
    Portfolio optimization requires:
    1. Synchronized data (same dates for all assets)
    2. Sufficient history (minimum 1 year = 252 trading days)
    3. Recent data (optimization uses recent correlations)

    Args:
        tickers: List of ticker symbols
        days: Number of days of historical data

    Returns:
        PortfolioDataInput with synchronized prices

    Raises:
        ValueError: If data cannot be fetched or insufficient overlap
    """
    # Fetch extra days to account for weekends/holidays
    # Need ~1.5x calendar days to get requested trading days (accounts for weekends/holidays)
    start_date = datetime.now() - timedelta(days=int(days * 1.5))
    end_date = datetime.now()

    print(f"Fetching {days} days of data for {len(tickers)} assets...", file=sys.stderr)

    # Download all tickers at once for alignment
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
            min_required = min(days, 30)  # At least 30 days, or requested days if less
            if len(closes) < min_required:
                raise ValueError(
                    f"Insufficient data for {ticker}. Need at least {min_required} days, got {len(closes)}"
                )

            prices_dict[ticker] = closes.tolist()

        # Get common dates (intersection across all tickers)
        common_index = data[tickers[0]]['Close'].dropna().index
        for ticker in tickers[1:]:
            ticker_index = data[ticker]['Close'].dropna().index
            common_index = common_index.intersection(ticker_index)

        min_required = min(days, 30)
        if len(common_index) < min_required:
            raise ValueError(
                f"Insufficient overlapping dates. Need at least {min_required}, got {len(common_index)}"
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

    print(
        f"Data fetched: {len(tickers)} assets, {len(dates)} days ({dates[0]} to {dates[-1]})",
        file=sys.stderr
    )

    return PortfolioDataInput(
        tickers=tickers,
        dates=dates,
        prices=prices_dict,
    )


def format_human_output(result, capital: float = 500000.0) -> str:
    """
    Format optimization results for human-readable display.

    EDUCATIONAL NOTE:
    This output shows:
    1. Optimal weights (percentages)
    2. Dollar allocation (for your $500k)
    3. Expected risk-return metrics
    4. Rebalancing guidance

    Args:
        result: OptimizationOutput
        capital: Portfolio capital (default: $500k)

    Returns:
        Formatted string output
    """
    lines = []
    lines.append(f"\n{'='*70}")
    lines.append("PORTFOLIO OPTIMIZATION RESULTS")
    lines.append(f"Method: {result.method.upper().replace('_', ' ')}")
    lines.append(f"Assets: {', '.join(result.tickers)}")
    lines.append(f"Capital: ${capital:,.0f}")
    lines.append(f"{'='*70}\n")

    # Portfolio metrics
    lines.append("PORTFOLIO METRICS")
    lines.append("-" * 70)
    lines.append(f"Expected Annual Return:     {result.expected_return:>8.2%}")
    lines.append(f"Expected Annual Volatility: {result.expected_volatility:>8.2%}")
    lines.append(f"Sharpe Ratio:               {result.sharpe_ratio:>8.2f}")
    lines.append(f"Diversification Ratio:      {result.diversification_ratio:>8.2f}")
    lines.append("")

    # Interpret Sharpe ratio
    if result.sharpe_ratio > 2.0:
        sharpe_label = "EXCELLENT - Outstanding risk-adjusted returns"
    elif result.sharpe_ratio > 1.0:
        sharpe_label = "GOOD - Solid risk-adjusted returns"
    elif result.sharpe_ratio > 0.5:
        sharpe_label = "FAIR - Acceptable but could improve"
    else:
        sharpe_label = "POOR - Not enough return for risk taken"

    lines.append(f"Sharpe Interpretation: {sharpe_label}")
    lines.append("")

    # Interpret diversification ratio
    if result.diversification_ratio > 1.8:
        div_label = "EXCELLENT - Strong diversification benefit"
    elif result.diversification_ratio > 1.4:
        div_label = "GOOD - Meaningful diversification"
    elif result.diversification_ratio > 1.2:
        div_label = "MODERATE - Some diversification"
    else:
        div_label = "POOR - Limited diversification benefit"

    lines.append(f"Diversification Interpretation: {div_label}")
    lines.append("")

    # Optimal allocation
    lines.append("OPTIMAL ALLOCATION")
    lines.append("-" * 70)
    lines.append(f"{'Asset':<10} {'Weight':>10} {'Dollar Amount':>18}")
    lines.append("-" * 70)

    # Sort by weight (largest first)
    sorted_assets = sorted(
        result.optimal_weights.items(),
        key=lambda x: x[1],
        reverse=True
    )

    for ticker, weight in sorted_assets:
        dollar_amount = capital * weight
        lines.append(
            f"{ticker:<10} {weight:>9.2%} ${dollar_amount:>17,.0f}"
        )

    lines.append("-" * 70)
    lines.append(f"{'TOTAL':<10} {sum(result.optimal_weights.values()):>9.2%} ${capital:>17,.0f}")
    lines.append("")

    # Action plan
    lines.append("ACTION PLAN FOR DEPLOYMENT")
    lines.append("-" * 70)

    # Check for concentrated positions
    max_weight = max(result.optimal_weights.values())
    if max_weight > 0.40:
        lines.append("WARNING: CONCENTRATION RISK")
        lines.append(f"   Largest position is {max_weight:.1%} of portfolio.")
        lines.append("   Consider position limits (--max-position) for risk control.")
        lines.append("")

    # Deployment steps
    lines.append("1. Review allocation aligns with your risk tolerance")
    lines.append("2. Check current prices before executing trades")
    lines.append("3. Use limit orders to avoid slippage on large positions")
    lines.append("4. Consider tax implications (wash sales, capital gains)")
    lines.append("5. Set calendar reminder to rebalance quarterly")
    lines.append("")

    # Method-specific guidance
    lines.append("METHOD NOTES")
    lines.append("-" * 70)

    if result.method == "max_sharpe":
        lines.append("Maximum Sharpe seeks best risk-adjusted returns.")
        lines.append("Characteristics:")
        lines.append("  - Aggressive growth orientation")
        lines.append("  - May be concentrated (fewer holdings)")
        lines.append("  - Sensitive to return estimates")
        lines.append("Best for: Growth-oriented investors comfortable with concentration")

    elif result.method == "risk_parity":
        lines.append("Risk Parity equalizes risk contribution across assets.")
        lines.append("Characteristics:")
        lines.append("  - All-weather portfolio approach")
        lines.append("  - No return forecasts needed")
        lines.append("  - More stable allocations")
        lines.append("Best for: Diversified exposure across market regimes")

    elif result.method == "min_variance":
        lines.append("Minimum Variance seeks lowest-risk allocation.")
        lines.append("Characteristics:")
        lines.append("  - Maximum capital preservation")
        lines.append("  - Ignores return expectations")
        lines.append("  - Favors low-volatility assets")
        lines.append("Best for: Conservative investors, volatile markets")

    elif result.method == "mean_variance":
        lines.append("Mean-Variance balances return target vs risk.")
        lines.append("Characteristics:")
        lines.append("  - Classic Markowitz approach")
        lines.append("  - Targets specific return level")
        lines.append("  - Requires return forecasts")
        lines.append("Best for: Investors with specific return goals")

    elif result.method == "black_litterman":
        lines.append("Black-Litterman blends market equilibrium with your views.")
        lines.append("Characteristics:")
        lines.append("  - Incorporates specific investment opinions")
        lines.append("  - More stable than pure Markowitz")
        lines.append("  - Accounts for uncertainty")
        lines.append("Best for: Investors with strong conviction on certain assets")

    lines.append("")
    lines.append(f"{'='*70}\n")

    return "\n".join(lines)


def format_json_output(result) -> str:
    """
    Format optimization results as JSON.

    Args:
        result: OptimizationOutput

    Returns:
        JSON string
    """
    # Convert Pydantic model to dict, then to JSON
    return json.dumps(result.model_dump(), indent=2, default=str)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Optimize portfolio allocation for Finance Guru agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Maximum Sharpe ratio (best risk-adjusted returns)
  uv run python src/strategies/optimizer_cli.py TSLA PLTR NVDA SPY --days 252 --method max_sharpe

  # Risk parity (all-weather portfolio)
  uv run python src/strategies/optimizer_cli.py TSLA PLTR NVDA SPY --days 252 --method risk_parity

  # Minimum variance (defensive)
  uv run python src/strategies/optimizer_cli.py TSLA PLTR NVDA SPY --days 252 --method min_variance

  # With position limits (max 30% per stock)
  uv run python src/strategies/optimizer_cli.py TSLA PLTR NVDA SPY --days 252 --method max_sharpe --max-position 0.30

  # Black-Litterman with views
  uv run python src/strategies/optimizer_cli.py TSLA PLTR NVDA --days 252 --method black_litterman \
      --view TSLA:0.15 --view PLTR:0.20

  # JSON output
  uv run python src/strategies/optimizer_cli.py TSLA PLTR NVDA SPY --days 252 --method max_sharpe --output json

Agent Use Cases:
  - Strategy Advisor: Generate deployment plan for $500k capital
  - Quant Analyst: Compare optimization methods
  - Compliance Officer: Verify position limits
  - Risk Assessment: Evaluate expected risk-return profile
        """,
    )

    # Required arguments
    parser.add_argument(
        'tickers',
        type=str,
        nargs='+',
        help='Stock ticker symbols (minimum 2 required, e.g., TSLA PLTR NVDA SPY)'
    )

    parser.add_argument(
        '--days',
        type=int,
        default=252,
        help='Number of days of historical data (default: 252 = 1 year, minimum: 252)'
    )

    # Optimization configuration
    parser.add_argument(
        '--method',
        choices=['mean_variance', 'risk_parity', 'min_variance', 'max_sharpe', 'black_litterman'],
        default='max_sharpe',
        help='Optimization method (default: max_sharpe)'
    )

    parser.add_argument(
        '--risk-free-rate',
        type=float,
        default=0.045,
        help='Annual risk-free rate for Sharpe calculation (default: 0.045 = 4.5%%)'
    )

    parser.add_argument(
        '--target-return',
        type=float,
        default=None,
        help='Target annual return for mean-variance (e.g., 0.12 = 12%%)'
    )

    parser.add_argument(
        '--max-position',
        type=float,
        default=1.0,
        help='Maximum position size per asset (default: 1.0 = 100%%, e.g., 0.30 = 30%% max)'
    )

    parser.add_argument(
        '--view',
        type=str,
        action='append',
        help='Black-Litterman view in format TICKER:RETURN (e.g., TSLA:0.15 for 15%% expected)'
    )

    parser.add_argument(
        '--capital',
        type=float,
        default=500000.0,
        help='Portfolio capital for dollar allocation (default: 500000 = $500k)'
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
        print("Error: At least 2 tickers required for portfolio optimization", file=sys.stderr)
        return 1

    # Validate days
    if args.days < 252:
        print(
            f"Warning: {args.days} days is less than recommended minimum (252 days = 1 year)",
            file=sys.stderr
        )
        print("Optimization quality may be poor with insufficient data.", file=sys.stderr)

    try:
        # Fetch portfolio data
        print(f"Starting optimization: method={args.method}, assets={len(args.tickers)}", file=sys.stderr)
        data = fetch_portfolio_data(args.tickers, args.days)

        # Parse views for Black-Litterman
        views = None
        if args.view:
            views = {}
            for view_str in args.view:
                try:
                    ticker, return_str = view_str.split(':')
                    views[ticker.upper()] = float(return_str)
                except ValueError:
                    print(
                        f"Error: Invalid view format '{view_str}'. Use TICKER:RETURN (e.g., TSLA:0.15)",
                        file=sys.stderr
                    )
                    return 1

        # Create configuration
        config = OptimizationConfig(
            method=args.method,
            risk_free_rate=args.risk_free_rate,
            target_return=args.target_return,
            allow_short=False,  # Long-only for retail investors
            position_limits=(0.0, args.max_position),
            views=views,
        )

        # Optimize portfolio
        print("Running optimization...", file=sys.stderr)
        result = optimize_portfolio(data, config)
        print(f"Optimization complete: Sharpe={result.sharpe_ratio:.2f}", file=sys.stderr)

        # Output results
        if args.output == 'json':
            print(format_json_output(result))
        else:
            print(format_human_output(result, capital=args.capital))

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
