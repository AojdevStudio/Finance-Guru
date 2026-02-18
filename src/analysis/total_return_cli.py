#!/usr/bin/env python3
"""Total Return CLI for Finance Guru Agents.

This module provides a command-line interface for calculating total returns
(price + dividends) with DRIP modeling and multi-ticker comparison.

ARCHITECTURE NOTE:
This is Layer 3 of our 3-layer architecture:
    Layer 1: Pydantic Models (total_return_inputs.py) - Data validation
    Layer 2: Calculator Classes (total_return.py) - Business logic
    Layer 3: CLI Interface (THIS FILE) - Agent integration

AGENT USAGE:
    # Single ticker total return (1 year)
    uv run python src/analysis/total_return_cli.py SCHD --days 252

    # Multi-ticker comparison ranked by total return
    uv run python src/analysis/total_return_cli.py SCHD JEPI VYM --days 252

    # JSON output for programmatic parsing
    uv run python src/analysis/total_return_cli.py SCHD --days 252 --output json

    # Override data quality warnings
    uv run python src/analysis/total_return_cli.py CLM --days 252 --force

    # Save results to file
    uv run python src/analysis/total_return_cli.py SCHD JEPI --days 252 --save-to analysis/returns.txt

EDUCATIONAL NOTE:
Total return measures the COMPLETE performance of an investment:
    Total Return = Price Return + Dividend Return

Sean's insight: "You can't say a fund is down without counting distributions."
A fund showing -3.95% price return might be +4.25% total return once distributions
are counted. This tool reveals the true story.

Author: Finance Guru Development Team
Created: 2026-02-17
"""

from __future__ import annotations

import argparse
import glob
import json
import sys
from datetime import date, timedelta
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.analysis.total_return import (
    DividendDataError,
    TotalReturnCalculator,
    TotalReturnResult,
)
from src.models.total_return_inputs import (
    DividendRecord,
    TotalReturnInput,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PORTFOLIO_CSV_GLOB = str(
    project_root / "notebooks" / "updates" / "Portfolio_Positions_*.csv"
)

DISCLAIMER = (
    "DISCLAIMER: For educational purposes only. Not investment advice. "
    "Consult a qualified financial advisor before making investment decisions."
)

# ---------------------------------------------------------------------------
# Data Fetching
# ---------------------------------------------------------------------------


def fetch_ticker_data(
    ticker: str, days: int, realtime: bool = False
) -> tuple[TotalReturnInput, list[float], list[DividendRecord], dict[date, float]]:
    """Fetch price and dividend data for total return calculation.

    Uses yf.Ticker(symbol).history() for synchronized price+dividend data
    (raw Close, NOT Adj Close). Optionally appends Finnhub real-time price.

    Args:
        ticker: Stock ticker symbol (e.g., SCHD, JEPI).
        days: Number of calendar days of history.
        realtime: If True, try Finnhub for current price.

    Returns:
        Tuple of (TotalReturnInput, prices, dividends, ex_date_prices).

    Raises:
        ValueError: If no data found or insufficient data points.
    """
    import yfinance as yf

    # Fetch extra days to account for weekends/holidays
    start_date = date.today() - timedelta(days=int(days * 1.5))
    end_date = date.today()

    stock = yf.Ticker(ticker)
    hist = stock.history(start=str(start_date), end=str(end_date))

    if hist.empty:
        raise ValueError(f"No data found for ticker {ticker}")

    # Extract prices and dates (raw Close, NOT Adj Close)
    prices = hist["Close"].tolist()
    dates_list = [d.date() for d in hist.index]

    if len(prices) < 2:
        raise ValueError(
            f"Insufficient data for {ticker}: got {len(prices)} day(s), need at least 2. "
            f"Try increasing --days parameter."
        )

    # Trim to requested number of trading days
    if len(prices) > days:
        prices = prices[-days:]
        dates_list = dates_list[-days:]
        # Re-filter hist for dividend extraction below
        hist = hist.iloc[-days:]

    # Extract non-zero dividend records and ex-date close prices
    dividends: list[DividendRecord] = []
    ex_date_prices: dict[date, float] = {}
    div_mask = hist["Dividends"] > 0
    for idx, row in hist[div_mask].iterrows():
        ex_dt = idx.date()
        dividends.append(
            DividendRecord(
                ex_date=ex_dt,
                amount=float(row["Dividends"]),
                shares_at_ex=1.0,  # Per-share basis; scaled later by portfolio shares
            )
        )
        ex_date_prices[ex_dt] = float(row["Close"])

    # Optionally append Finnhub real-time price
    if realtime:
        try:
            from src.utils.market_data import get_prices

            rt_data = get_prices(ticker, realtime=True)
            if ticker.upper() in rt_data:
                current_price = rt_data[ticker.upper()].price
                prices[-1] = current_price
                print(
                    f"  Real-time price for {ticker}: ${current_price:.2f} (Finnhub)",
                    file=sys.stderr,
                )
        except Exception as e:
            print(
                f"  Real-time price unavailable for {ticker}, using EOD: {e}",
                file=sys.stderr,
            )

    # Build validated input model
    inp = TotalReturnInput(
        ticker=ticker.upper(),
        start_date=dates_list[0],
        end_date=dates_list[-1],
        initial_shares=1.0,
    )

    return inp, prices, dividends, ex_date_prices


# ---------------------------------------------------------------------------
# Portfolio CSV Reader
# ---------------------------------------------------------------------------


def load_portfolio_shares(csv_glob: str = PORTFOLIO_CSV_GLOB) -> dict[str, float]:
    """Load share counts from the latest Portfolio_Positions CSV.

    Reads the most recently dated CSV from notebooks/updates/ and extracts
    ticker -> share count mapping.

    Args:
        csv_glob: Glob pattern for CSV files.

    Returns:
        Dict mapping ticker -> quantity of shares. Empty dict if no CSV found.
    """
    files = sorted(glob.glob(csv_glob))
    if not files:
        return {}

    latest = files[-1]
    shares: dict[str, float] = {}

    try:
        import csv

        with open(latest) as f:
            reader = csv.DictReader(f)
            for row in reader:
                symbol = row.get("Symbol", "").strip()
                qty_str = row.get("Quantity", "0").strip()
                if symbol and qty_str:
                    try:
                        shares[symbol.upper()] = float(qty_str)
                    except ValueError:
                        continue
    except Exception:
        return {}

    return shares


# ---------------------------------------------------------------------------
# Human Output Formatting
# ---------------------------------------------------------------------------


def format_human_output(  # noqa: C901
    results: list[TotalReturnResult],
    portfolio_shares: dict[str, float],
) -> str:
    """Format results in human-readable format with DRIP comparison and league table.

    Shows side-by-side DRIP/non-DRIP columns, verdict narratives for sign-flip
    tickers, dollar amounts when portfolio CSV is available, period breakdown
    for each dividend event, and a league table ranking.

    Args:
        results: List of TotalReturnResult from calculator.
        portfolio_shares: Dict of ticker -> share count from portfolio CSV.

    Returns:
        Formatted string for terminal display.
    """
    lines: list[str] = []
    period_label = ""
    if results:
        period_label = f"{results[0].start_date} to {results[0].end_date}"

    lines.append("")
    lines.append("=" * 70)
    lines.append("TOTAL RETURN ANALYSIS")
    lines.append(f"Period: {period_label}")
    lines.append("=" * 70)

    # ---- Per-ticker detail ----
    for r in results:
        lines.append("")
        lines.append("-" * 70)

        shares = portfolio_shares.get(r.ticker)
        shares_label = f" ({shares:.2f} shares)" if shares else ""
        lines.append(f"  {r.ticker}{shares_label}")
        lines.append("-" * 70)

        # Side-by-side: non-DRIP | DRIP
        lines.append(f"  {'Metric':<25} {'Non-DRIP':>12}  {'DRIP':>12}")
        lines.append(f"  {'-' * 51}")

        lines.append(
            f"  {'Price Return':<25} {r.price_return:>11.2%}   {r.price_return:>11.2%}"
        )
        lines.append(
            f"  {'Dividend Return':<25} {r.dividend_return:>11.2%}   {'--':>11}"
        )
        lines.append(
            f"  {'Total Return':<25} {r.total_return:>11.2%}   "
            f"{(r.drip_total_return if r.drip_total_return is not None else r.total_return):>11.2%}"
        )

        if r.annualized_return is not None:
            lines.append(
                f"  {'Annualized Return':<25} {r.annualized_return:>11.2%}   {'--':>11}"
            )

        if r.drip_share_growth is not None:
            lines.append(
                f"  {'DRIP Share Growth':<25} {'--':>11}   {r.drip_share_growth:>11.2%}"
            )
        if r.drip_final_shares is not None:
            lines.append(
                f"  {'Final Shares (from 1)':<25} {'1.0000':>11}   "
                f"{r.drip_final_shares:>11.4f}"
            )

        # Dollar amounts if portfolio shares known
        if shares:
            lines.append("")
            lines.append(f"  Dollar Impact ({shares:.2f} shares):")
            total_divs = sum(
                d.get("dividend_per_share", 0.0) for d in r.period_breakdown
            )
            if total_divs > 0:
                lines.append(
                    f"    Distributions received: ${total_divs * shares:.2f} "
                    f"(${total_divs:.4f}/share x {shares:.2f})"
                )

        # Verdict narrative (sign-flip detection)
        if r.price_return < 0 and r.total_return > 0:
            lines.append("")
            lines.append(
                f"  >>> VERDICT: {r.ticker} price return is {r.price_return:.2%}, "
                f"but total return flips to {r.total_return:+.2%} after "
                f"distributions. Price is MISLEADING."
            )

        # Data quality warnings
        if r.data_quality_warnings:
            lines.append("")
            for w in r.data_quality_warnings:
                lines.append(f"  WARNING: {w}")

        # Period breakdown (every dividend event)
        if r.period_breakdown:
            lines.append("")
            lines.append(
                f"  {'Date':<12} {'Div/Share':>10} {'Reinvest $':>11} "
                f"{'Shares Acq':>11} {'Cumul Shares':>13}"
            )
            lines.append(f"  {'-' * 59}")
            for event in r.period_breakdown:
                evt_date = event.get("date", "")
                div_ps = event.get("dividend_per_share", 0.0)
                reinvest = event.get("reinvest_price", 0.0)
                acq = event.get("shares_acquired", 0.0)
                cumul = event.get("cumulative_shares", 0.0)
                lines.append(
                    f"  {str(evt_date):<12} ${div_ps:>9.4f} ${reinvest:>10.2f} "
                    f"{acq:>11.6f} {cumul:>13.6f}"
                )

        lines.append(f"  Dividends in period: {r.dividend_count}")

    # ---- League Table ----
    if len(results) > 1:
        lines.append("")
        lines.append("=" * 70)
        lines.append("LEAGUE TABLE (ranked by total return)")
        lines.append("-" * 70)

        ranked = sorted(results, key=lambda r: r.total_return, reverse=True)
        for i, r in enumerate(ranked, 1):
            sign_flip = ""
            if r.price_return < 0 and r.total_return > 0:
                sign_flip = " [Price misleading]"
            lines.append(
                f"  #{i}  {r.ticker:<8} {r.total_return:>+8.2%}  "
                f"(price: {r.price_return:>+7.2%}, "
                f"div: {r.dividend_return:>+7.2%}){sign_flip}"
            )

        lines.append("-" * 70)

    # ---- Disclaimer ----
    lines.append("")
    lines.append("=" * 70)
    lines.append(DISCLAIMER)
    lines.append("=" * 70)
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# JSON Output Formatting
# ---------------------------------------------------------------------------


def format_json_output(
    results: list[TotalReturnResult],
    portfolio_shares: dict[str, float],
) -> str:
    """Format results as structured JSON.

    Includes all fields plus verdict and dollar_impact when portfolio shares known.

    Args:
        results: List of TotalReturnResult from calculator.
        portfolio_shares: Dict of ticker -> share count from portfolio CSV.

    Returns:
        JSON string.
    """
    output_list = []
    for r in results:
        entry: dict = {
            "ticker": r.ticker,
            "start_date": str(r.start_date),
            "end_date": str(r.end_date),
            "price_return": round(r.price_return, 6),
            "dividend_return": round(r.dividend_return, 6),
            "total_return": round(r.total_return, 6),
            "annualized_return": (
                round(r.annualized_return, 6)
                if r.annualized_return is not None
                else None
            ),
            "drip_total_return": (
                round(r.drip_total_return, 6)
                if r.drip_total_return is not None
                else None
            ),
            "drip_final_shares": (
                round(r.drip_final_shares, 6)
                if r.drip_final_shares is not None
                else None
            ),
            "drip_share_growth": (
                round(r.drip_share_growth, 6)
                if r.drip_share_growth is not None
                else None
            ),
            "dividend_count": r.dividend_count,
            "data_quality_warnings": r.data_quality_warnings,
            "period_breakdown": [
                {k: str(v) if isinstance(v, date) else v for k, v in evt.items()}
                for evt in r.period_breakdown
            ],
        }

        # Verdict flag
        entry["verdict"] = (
            "Price misleading" if r.price_return < 0 and r.total_return > 0 else None
        )

        # Dollar impact
        shares = portfolio_shares.get(r.ticker)
        if shares:
            total_divs = sum(
                evt.get("dividend_per_share", 0.0) for evt in r.period_breakdown
            )
            entry["dollar_impact"] = {
                "shares_held": shares,
                "total_distributions": round(total_divs * shares, 2),
                "distributions_per_share": round(total_divs, 4),
            }

        output_list.append(entry)

    wrapper = {
        "total_return_analysis": output_list,
        "disclaimer": DISCLAIMER,
    }
    return json.dumps(wrapper, indent=2, default=str)


# ---------------------------------------------------------------------------
# Main CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the total return CLI.

    Returns:
        Configured ArgumentParser.
    """
    parser = argparse.ArgumentParser(
        description="Calculate total returns (price + dividends) with DRIP modeling "
        "for Finance Guru agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single ticker, 1 year of data
  %(prog)s SCHD --days 252

  # Multi-ticker comparison ranked by total return
  %(prog)s SCHD JEPI VYM CLM --days 252

  # JSON output for programmatic parsing
  %(prog)s SCHD --days 252 --output json

  # Override data quality warnings
  %(prog)s CLM --days 252 --force

  # Save to file
  %(prog)s SCHD JEPI --days 252 --save-to analysis/returns.txt

  # With real-time Finnhub prices
  %(prog)s SCHD --days 252 --realtime

Agent Use Cases:
  - Market Researcher: Quick total return scan across income tickers
  - Quant Analyst: DRIP vs non-DRIP comparison, annualized return analysis
  - Strategy Advisor: Compare dividend strategies, identify misleading price returns

Key Insight:
  Sean's rule: "You can't say a fund is down without counting distributions."
  This tool reveals whether price-only returns are telling the full story.
        """,
    )

    # Positional: ticker(s)
    parser.add_argument(
        "tickers",
        type=str,
        nargs="+",
        help="Stock ticker symbols (e.g., SCHD JEPI VYM CLM)",
    )

    # Data parameters
    parser.add_argument(
        "--days",
        type=int,
        default=252,
        help="Number of days of historical data (default: 252 = 1 year)",
    )

    parser.add_argument(
        "--realtime",
        action="store_true",
        help="Use Finnhub for real-time current price (requires FINNHUB_API_KEY)",
    )

    # Control flags
    parser.add_argument(
        "--force",
        action="store_true",
        help="Calculate despite data quality warnings (missing dividends, gaps)",
    )

    # Output parameters
    parser.add_argument(
        "--output",
        type=str,
        choices=["human", "json"],
        default="human",
        help="Output format (default: human)",
    )

    parser.add_argument(
        "--save-to",
        type=str,
        default=None,
        help="Save output to file (optional)",
    )

    return parser


def main() -> int:
    """Main CLI entry point.

    Fetches data for each ticker, calculates total return with DRIP,
    formats and displays results. Returns exit code.

    Returns:
        int: Exit code (0 success, 1 error, 130 user cancellation).
    """
    parser = build_parser()
    args = parser.parse_args()

    try:
        # Load portfolio shares for dollar amounts
        portfolio_shares = load_portfolio_shares()
        if portfolio_shares:
            print(
                f"Portfolio CSV found: {len(portfolio_shares)} positions loaded",
                file=sys.stderr,
            )
        else:
            print(
                "No Portfolio CSV found in notebooks/updates/ -- "
                "showing per-share amounts only",
                file=sys.stderr,
            )

        # Fetch and calculate for each ticker
        results: list[TotalReturnResult] = []
        for ticker in args.tickers:
            ticker = ticker.upper()
            print(f"Fetching {args.days} days of data for {ticker}...", file=sys.stderr)

            try:
                inp, prices, dividends, ex_date_prices = fetch_ticker_data(
                    ticker, args.days, realtime=args.realtime
                )

                calc = TotalReturnCalculator(
                    data=inp,
                    prices=prices,
                    dividends=dividends,
                    ex_date_prices=ex_date_prices,
                )

                inp_with_shares = TotalReturnInput(
                    ticker=ticker,
                    start_date=inp.start_date,
                    end_date=inp.end_date,
                    initial_shares=1.0,  # Always calculate per-share
                )
                calc = TotalReturnCalculator(
                    data=inp_with_shares,
                    prices=prices,
                    dividends=dividends,
                    ex_date_prices=ex_date_prices,
                )

                result = calc.calculate_all(force=args.force)
                results.append(result)
                print(
                    f"  {ticker}: total return {result.total_return:+.2%}",
                    file=sys.stderr,
                )

            except DividendDataError as e:
                print(
                    f"  ERROR for {ticker}: {e}\n"
                    f"  Hint: Use --force to calculate despite data quality issues.",
                    file=sys.stderr,
                )
                continue

            except ValueError as e:
                print(f"  ERROR for {ticker}: {e}", file=sys.stderr)
                continue

        if not results:
            print(
                "No results to display. All tickers failed.",
                file=sys.stderr,
            )
            return 1

        # Format output
        if args.output == "json":
            output = format_json_output(results, portfolio_shares)
        else:
            output = format_human_output(results, portfolio_shares)

        # Display or save
        if args.save_to:
            save_path = Path(args.save_to)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            save_path.write_text(output)
            print(f"Saved to: {save_path}", file=sys.stderr)
        else:
            print(output)

        return 0

    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc(file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
