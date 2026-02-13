#!/usr/bin/env python3
"""
Factor Analysis CLI for Finance Guru™ Agents

Command-line interface for Fama-French factor analysis.

AGENT USAGE:
    # CAPM (1-factor) analysis
    uv run python src/analysis/factors_cli.py TSLA --days 252 --benchmark SPY

    # 3-factor analysis (requires Fama-French data)
    uv run python src/analysis/factors_cli.py TSLA --days 252 --benchmark SPY \\
        --smb-ticker SMBTICKER --hml-ticker HMLTICKER

    # JSON output
    uv run python src/analysis/factors_cli.py TSLA --days 252 --benchmark SPY --output json

EDUCATIONAL NOTE:
This tool requires market factor data. For full Fama-French analysis,
you need SMB and HML factor returns (typically from Kenneth French's data library).

Author: Finance Guru™ Development Team
Created: 2025-10-13
"""

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.analysis.factors import FactorAnalyzer
from src.models.factors_inputs import FactorDataInput


def fetch_returns(ticker: str, days: int) -> list[float]:
    """Fetch returns for a ticker."""
    try:
        import pandas as pd  # noqa: F401
        import yfinance as yf

        end_date = date.today()
        # Need ~1.5x calendar days to get requested trading days (accounts for weekends/holidays)
        start_date = end_date - timedelta(days=int(days * 1.5))

        ticker_obj = yf.Ticker(ticker)
        hist = ticker_obj.history(start=start_date, end=end_date)

        if hist.empty:
            raise ValueError(f"No data found for {ticker}")

        returns = hist["Close"].pct_change().dropna().tolist()
        return returns

    except ImportError:
        print("ERROR: yfinance not installed", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR fetching {ticker}: {e}", file=sys.stderr)
        raise


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Perform factor analysis on a stock",
        epilog="""
Examples:
  # CAPM analysis (market factor only)
  %(prog)s TSLA --days 252 --benchmark SPY

  # JSON output
  %(prog)s TSLA --days 252 --benchmark SPY --output json
        """,
    )

    parser.add_argument("ticker", type=str, help="Stock ticker to analyze")
    parser.add_argument(
        "--days", type=int, default=252, help="Days of data (default: 252)"
    )
    parser.add_argument(
        "--benchmark", type=str, default="SPY", help="Market benchmark (default: SPY)"
    )
    parser.add_argument(
        "--risk-free-rate",
        type=float,
        default=0.045,
        help="Annual risk-free rate (default: 4.5%%)",
    )
    parser.add_argument(
        "--output", choices=["human", "json"], default="human", help="Output format"
    )
    parser.add_argument("--save-to", type=str, default=None, help="Save to file")

    args = parser.parse_args()

    try:
        print(
            f"📥 Fetching data for {args.ticker} and {args.benchmark}...",
            file=sys.stderr,
        )

        asset_returns = fetch_returns(args.ticker, args.days)
        market_returns = fetch_returns(args.benchmark, args.days)

        # Align lengths
        min_len = min(len(asset_returns), len(market_returns))
        asset_returns = asset_returns[-min_len:]
        market_returns = market_returns[-min_len:]

        print(f"✅ Fetched {len(asset_returns)} returns", file=sys.stderr)

        # Create factor data
        factor_data = FactorDataInput(
            ticker=args.ticker,
            asset_returns=asset_returns,
            market_returns=market_returns,
            risk_free_rate=args.risk_free_rate,
        )

        print("🧮 Running factor analysis...", file=sys.stderr)
        analyzer = FactorAnalyzer()
        results = analyzer.analyze(factor_data)

        print("✅ Analysis complete!\n", file=sys.stderr)

        if args.output == "json":
            output_text = results.model_dump_json(indent=2)
        else:
            output_text = format_human(results)

        if args.save_to:
            Path(args.save_to).parent.mkdir(parents=True, exist_ok=True)
            Path(args.save_to).write_text(output_text)
            print(f"💾 Saved to: {args.save_to}", file=sys.stderr)
        else:
            print(output_text)

    except Exception as e:
        print(f"❌ ERROR: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


def format_human(results) -> str:
    """Format results in human-readable format."""
    output = []
    output.append("=" * 70)
    output.append(f"📊 FACTOR ANALYSIS: {results.exposure.ticker}")
    output.append("=" * 70)
    output.append("")

    output.append("🎯 FACTOR EXPOSURES (Betas)")
    output.append("-" * 70)
    output.append(
        f"  Market Beta:              {results.exposure.market_beta:>10.2f}  (t-stat: {results.exposure.market_beta_tstat:.2f})"
    )
    output.append(
        f"  Alpha (Annual):           {results.exposure.alpha:>10.1%}  (t-stat: {results.exposure.alpha_tstat:.2f})"
    )
    output.append(f"  R-squared:                {results.exposure.r_squared:>10.1%}")
    output.append("")

    if results.exposure.alpha_tstat > 2.0:
        output.append("  ✅ Alpha is statistically significant (t-stat > 2.0)")
    elif results.exposure.alpha_tstat < -2.0:
        output.append("  ⚠️  Negative alpha is statistically significant")
    else:
        output.append("  ℹ️  Alpha is not statistically significant")
    output.append("")

    output.append("💰 RETURN ATTRIBUTION")
    output.append("-" * 70)
    output.append(
        f"  Total Return (Annual):    {results.attribution.total_return:>10.1%}"
    )
    output.append(
        f"  Market Attribution:       {results.attribution.market_attribution:>10.1%}  ({results.attribution.market_importance:.0%} of total)"
    )
    output.append(
        f"  Alpha Attribution:        {results.attribution.alpha_attribution:>10.1%}  ({results.attribution.alpha_importance:.0%} of total)"
    )
    output.append(f"  Residual:                 {results.attribution.residual:>10.1%}")
    output.append("")

    output.append("💡 SUMMARY")
    output.append("-" * 70)
    for line in results.summary.split("\n"):
        output.append(f"  {line}")
    output.append("")

    if results.recommendations:
        output.append("🎯 RECOMMENDATIONS")
        output.append("-" * 70)
        for i, rec in enumerate(results.recommendations, 1):
            output.append(f"  {i}. {rec}")
        output.append("")

    output.append("=" * 70)
    return "\n".join(output)


if __name__ == "__main__":
    main()
