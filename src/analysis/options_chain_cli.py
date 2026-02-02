#!/usr/bin/env python3
"""
Options Chain Scanner CLI for Finance Guru Agents

This module scans live options chains from yfinance, filters by OTM% and
days-to-expiry criteria, calculates Greeks via Black-Scholes, and sizes
positions against a budget.

ARCHITECTURE NOTE:
This is Layer 3 of our 3-layer architecture:
    Layer 1: Pydantic Models - Data validation (options_inputs.py)
    Layer 2: Calculator Classes - Business logic (options.py)
    Layer 3: CLI Interface (THIS FILE) - Agent integration

AGENT USAGE:
    # Scan for QQQ puts, 10-20% OTM, 60-90 days out, $4407 budget
    uv run python src/analysis/options_chain_cli.py QQQ --type put \\
        --otm-min 10 --otm-max 20 --days-min 60 --days-max 90 \\
        --budget 4407 --contracts 4

    # List available expiration dates
    uv run python src/analysis/options_chain_cli.py QQQ --list-expiries

    # JSON output
    uv run python src/analysis/options_chain_cli.py QQQ --type put \\
        --otm-min 10 --otm-max 20 --output json

    # Save to file
    uv run python src/analysis/options_chain_cli.py QQQ --type put \\
        --otm-min 5 --otm-max 15 --output json \\
        --save-to analysis/qqq-puts-2026-02-02.json

EDUCATIONAL NOTE:
This tool helps identify options contracts that match specific criteria:
- OTM% filters for protective puts or speculative calls at desired distance
- Days-to-expiry filters for optimal theta decay characteristics
- Budget sizing shows how many contracts fit your allocation
- Greeks help assess sensitivity and risk before entering a position

Author: Finance Guru Development Team
Created: 2026-02-02
"""

from __future__ import annotations

import argparse
import math
import sys
from datetime import date
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Constants
DEFAULT_RISK_FREE_RATE = 0.045  # 4.5% risk-free rate for Black-Scholes
MAX_TICKER_LENGTH = 5  # Maximum length for stock ticker symbols

import yfinance as yf

from src.analysis.options import price_option
from src.models.options_inputs import (
    OptionContractData,
    OptionsChainOutput,
)
from src.utils.market_data import get_prices


def list_expiries(ticker: str) -> list[str]:
    """
    List all available expiration dates for a ticker.

    Args:
        ticker: Stock ticker symbol

    Returns:
        List of expiration date strings (YYYY-MM-DD)
    """
    try:
        t = yf.Ticker(ticker)
        expirations = list(t.options)
        return expirations
    except Exception as e:
        print(f"Error fetching expirations for {ticker}: {e}", file=sys.stderr)
        return []


def filter_expirations(
    expirations: list[str],
    days_min: int,
    days_max: int,
    today: date | None = None,
) -> list[str]:
    """
    Filter expiration dates to those within the specified days range.

    Args:
        expirations: List of expiration date strings
        days_min: Minimum days to expiry
        days_max: Maximum days to expiry
        today: Reference date (defaults to today)

    Returns:
        Filtered list of expiration date strings
    """
    if today is None:
        today = date.today()

    filtered = []
    for exp_str in expirations:
        try:
            exp_date = date.fromisoformat(exp_str)
            days_out = (exp_date - today).days
            if days_min <= days_out <= days_max:
                filtered.append(exp_str)
        except ValueError:
            continue

    return filtered


def calculate_otm_pct(
    spot: float,
    strike: float,
    option_type: str,
) -> float:
    """
    Calculate out-of-the-money percentage.

    For puts:  OTM% = ((spot - strike) / spot) * 100
    For calls: OTM% = ((strike - spot) / spot) * 100

    Args:
        spot: Current spot price
        strike: Option strike price
        option_type: "call" or "put"

    Returns:
        OTM percentage (negative means ITM)
    """
    if option_type == "put":
        return ((spot - strike) / spot) * 100
    else:
        return ((strike - spot) / spot) * 100


def calculate_mid_price(bid: float, ask: float, last_price: float) -> float:
    """
    Calculate mid price with fallback logic.

    If bid and ask are both 0, fall back to last_price.

    Args:
        bid: Bid price
        ask: Ask price
        last_price: Last traded price

    Returns:
        Mid price
    """
    if bid == 0.0 and ask == 0.0:
        return last_price
    return (bid + ask) / 2


def should_skip_greeks(iv: float) -> bool:
    """
    Determine if Greeks calculation should be skipped.

    Skip when implied volatility is zero, negative, or NaN.

    Args:
        iv: Implied volatility value

    Returns:
        True if Greeks should be skipped
    """
    if math.isnan(iv) or iv <= 0.0:
        return True
    return False


def scan_chain(
    ticker: str,
    option_type: str,
    otm_min: float,
    otm_max: float,
    days_min: int,
    days_max: int,
    budget: float | None,
    target_contracts: int,
) -> OptionsChainOutput:
    """
    Scan options chain and return filtered, enriched results.

    This is the core scanning logic that:
    1. Gets spot price
    2. Fetches available expirations
    3. Filters expirations by days range
    4. For each expiration, fetches the chain
    5. Filters by OTM%
    6. Calculates Greeks for each contract
    7. Sizes against budget

    Args:
        ticker: Stock ticker symbol
        option_type: "call" or "put"
        otm_min: Minimum OTM percentage
        otm_max: Maximum OTM percentage
        days_min: Minimum days to expiry
        days_max: Maximum days to expiry
        budget: Budget for position sizing (None to skip)
        target_contracts: Target number of contracts

    Returns:
        OptionsChainOutput with all matching contracts
    """
    today = date.today()

    # Step 1: Get spot price
    print(f"Fetching spot price for {ticker}...", file=sys.stderr)
    try:
        price_data = get_prices(ticker)
        spot_price = price_data[ticker.upper()].price
        print(f"Spot price: ${spot_price:.2f}", file=sys.stderr)
    except Exception as e:
        print(f"Error getting spot price: {e}", file=sys.stderr)
        raise ValueError(f"Could not get spot price for {ticker}: {e}") from e

    # Step 2: Get available expirations
    print("Fetching available expirations...", file=sys.stderr)
    all_expirations = list_expiries(ticker)
    if not all_expirations:
        raise ValueError(f"No options expirations found for {ticker}")

    print(f"Found {len(all_expirations)} expiration dates", file=sys.stderr)

    # Step 3: Filter expirations by days range
    matching_expirations = filter_expirations(
        all_expirations, days_min, days_max, today
    )
    print(
        f"Expirations in {days_min}-{days_max} day range: "
        f"{len(matching_expirations)}",
        file=sys.stderr,
    )

    if not matching_expirations:
        print(
            f"No expirations found between {days_min} and {days_max} days out.",
            file=sys.stderr,
        )
        return OptionsChainOutput(
            ticker=ticker.upper(),
            spot_price=spot_price,
            scan_date=today.isoformat(),
            option_type=option_type,
            otm_range=(otm_min, otm_max),
            days_range=(days_min, days_max),
            budget=budget,
            target_contracts=target_contracts,
            expirations_available=all_expirations,
            expirations_scanned=[],
            contracts=[],
            total_found=0,
        )

    # Step 4: Scan each matching expiration
    contracts: list[OptionContractData] = []

    for exp_str in matching_expirations:
        exp_date = date.fromisoformat(exp_str)
        days_to_expiry = (exp_date - today).days
        print(f"Scanning {exp_str} ({days_to_expiry} days out)...", file=sys.stderr)

        try:
            t = yf.Ticker(ticker)
            chain = t.option_chain(exp_str)

            # Select calls or puts
            if option_type == "put":
                df = chain.puts
            else:
                df = chain.calls

            if df.empty:
                print(f"  No {option_type}s found for {exp_str}", file=sys.stderr)
                continue

            # Step 5: Filter by OTM%
            for _, row in df.iterrows():
                strike = float(row.get("strike", 0))
                if strike <= 0:
                    continue

                otm_pct = calculate_otm_pct(spot_price, strike, option_type)

                # Only keep contracts in OTM range
                if otm_pct < otm_min or otm_pct > otm_max:
                    continue

                # Extract market data (handle NaN values from yfinance)
                contract_symbol = str(row.get("contractSymbol", ""))
                last_price = float(row.get("lastPrice", 0.0) or 0.0)
                bid = float(row.get("bid", 0.0) or 0.0)
                ask = float(row.get("ask", 0.0) or 0.0)
                iv = float(row.get("impliedVolatility", 0.0) or 0.0)

                # Volume and OI can be NaN from yfinance — safe convert
                raw_vol = row.get("volume", 0)
                raw_oi = row.get("openInterest", 0)
                try:
                    volume = int(raw_vol) if raw_vol is not None and not math.isnan(float(raw_vol)) else 0
                except (ValueError, TypeError):
                    volume = 0
                try:
                    open_interest = int(raw_oi) if raw_oi is not None and not math.isnan(float(raw_oi)) else 0
                except (ValueError, TypeError):
                    open_interest = 0

                # Sanitize any NaN floats
                if math.isnan(last_price):
                    last_price = 0.0
                if math.isnan(bid):
                    bid = 0.0
                if math.isnan(ask):
                    ask = 0.0
                if math.isnan(iv):
                    iv = 0.0

                # Calculate mid price
                mid = calculate_mid_price(bid, ask, last_price)

                # Calculate total cost per contract
                price_for_cost = last_price if last_price > 0 else mid
                total_cost = price_for_cost * 100

                # Calculate contracts in budget
                contracts_in_budget = None
                if budget is not None and total_cost > 0:
                    contracts_in_budget = math.floor(budget / total_cost)

                # Step 6: Calculate Greeks (skip if IV is bad)
                delta = None
                gamma = None
                theta = None
                vega = None

                if not should_skip_greeks(iv):
                    try:
                        greeks = price_option(
                            spot=spot_price,
                            strike=strike,
                            days_to_expiry=days_to_expiry,
                            volatility=iv,
                            option_type=option_type,
                            risk_free_rate=DEFAULT_RISK_FREE_RATE,
                            dividend_yield=0.0,
                        )
                        delta = greeks.delta
                        gamma = greeks.gamma
                        theta = greeks.theta
                        vega = greeks.vega
                    except Exception as e:
                        print(
                            f"  Greeks calc failed for {contract_symbol}: {e}",
                            file=sys.stderr,
                        )

                # Build contract data
                contract = OptionContractData(
                    contract_symbol=contract_symbol,
                    expiration=exp_str,
                    strike=strike,
                    otm_pct=round(otm_pct, 2),
                    days_to_expiry=days_to_expiry,
                    last_price=last_price,
                    bid=bid,
                    ask=ask,
                    mid=round(mid, 2),
                    volume=volume,
                    open_interest=open_interest,
                    implied_volatility=round(iv, 4),
                    delta=round(delta, 4) if delta is not None else None,
                    gamma=round(gamma, 4) if gamma is not None else None,
                    theta=round(theta, 4) if theta is not None else None,
                    vega=round(vega, 4) if vega is not None else None,
                    total_cost=round(total_cost, 2),
                    contracts_in_budget=contracts_in_budget,
                )
                contracts.append(contract)

        except Exception as e:
            print(f"  Error scanning {exp_str}: {e}", file=sys.stderr)
            continue

    # Step 7: Sort by expiration then strike
    contracts.sort(key=lambda c: (c.expiration, c.strike))

    print(f"Found {len(contracts)} matching contracts", file=sys.stderr)

    return OptionsChainOutput(
        ticker=ticker.upper(),
        spot_price=spot_price,
        scan_date=today.isoformat(),
        option_type=option_type,
        otm_range=(otm_min, otm_max),
        days_range=(days_min, days_max),
        budget=budget,
        target_contracts=target_contracts,
        expirations_available=all_expirations,
        expirations_scanned=matching_expirations,
        contracts=contracts,
        total_found=len(contracts),
    )


def format_output_human(result: OptionsChainOutput) -> str:
    """
    Format scan results in a human-readable table.

    Args:
        result: The scan output to format

    Returns:
        Formatted string for terminal display
    """
    output = []
    output.append("=" * 120)
    output.append(
        f"OPTIONS CHAIN SCAN: {result.ticker} "
        f"{result.option_type.upper()}S"
    )
    output.append(f"Spot Price: ${result.spot_price:.2f}")
    output.append(f"Scan Date: {result.scan_date}")
    output.append(
        f"Filters: {result.otm_range[0]:.0f}-{result.otm_range[1]:.0f}% OTM, "
        f"{result.days_range[0]}-{result.days_range[1]} days to expiry"
    )

    if result.budget is not None:
        output.append(
            f"Budget: ${result.budget:,.2f} | "
            f"Target: {result.target_contracts} contracts"
        )

    output.append("=" * 120)
    output.append("")

    if not result.contracts:
        output.append(
            "No contracts found matching your criteria. "
            "Try widening the OTM% range or days-to-expiry window."
        )
        output.append("")
        output.append(
            f"Available expirations: "
            f"{', '.join(result.expirations_available[:10])}"
        )
        if len(result.expirations_available) > 10:
            output.append(
                f"  ... and {len(result.expirations_available) - 10} more"
            )
    else:
        # Table header
        header = (
            f"{'Expiry':<12} {'Strike':>8} {'OTM%':>6} "
            f"{'Bid':>7} {'Ask':>7} {'Mid':>7} {'Last':>7} "
            f"{'Vol':>6} {'OI':>7} {'IV':>6} "
            f"{'Delta':>7} {'Theta':>7} "
            f"{'Cost':>10}"
        )

        if result.budget is not None:
            header += f" {'Fits':>5}"

        output.append(header)
        output.append("-" * len(header))

        for c in result.contracts:
            delta_str = f"{c.delta:.3f}" if c.delta is not None else "  N/A"
            theta_str = f"{c.theta:.3f}" if c.theta is not None else "  N/A"

            row = (
                f"{c.expiration:<12} {c.strike:>8.2f} {c.otm_pct:>5.1f}% "
                f"{c.bid:>7.2f} {c.ask:>7.2f} {c.mid:>7.2f} {c.last_price:>7.2f} "
                f"{c.volume:>6} {c.open_interest:>7} {c.implied_volatility:>5.1%} "
                f"{delta_str:>7} {theta_str:>7} "
                f"${c.total_cost:>9,.2f}"
            )

            if result.budget is not None:
                fits = c.contracts_in_budget if c.contracts_in_budget is not None else 0
                row += f" {fits:>5}"

            output.append(row)

        output.append("")
        output.append(f"Total contracts found: {result.total_found}")
        output.append(
            f"Expirations scanned: {', '.join(result.expirations_scanned)}"
        )

    output.append("")
    output.append("=" * 120)
    output.append(
        "DISCLAIMER: For educational purposes only. Not investment advice. "
        "Consult a qualified financial professional before trading options."
    )
    output.append("=" * 120)

    return "\n".join(output)


def format_output_json(result: OptionsChainOutput) -> str:
    """
    Format scan results as JSON.

    Args:
        result: The scan output to format

    Returns:
        JSON string
    """
    return result.model_dump_json(indent=2)


def main() -> int:
    """
    Main CLI entry point.

    Returns:
        int: Exit code (0 for success, 1 for error)
    """
    parser = argparse.ArgumentParser(
        description="Scan options chains for Finance Guru",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan for QQQ puts, 10-20%% OTM, 60-90 days out
  %(prog)s QQQ --type put --otm-min 10 --otm-max 20 --days-min 60 --days-max 90

  # With budget sizing
  %(prog)s QQQ --type put --otm-min 10 --otm-max 20 --budget 4407 --contracts 4

  # List available expiration dates
  %(prog)s QQQ --list-expiries

  # JSON output
  %(prog)s QQQ --type put --otm-min 10 --otm-max 20 --output json

  # Save to file
  %(prog)s QQQ --type put --output json --save-to analysis/qqq-puts.json
        """
    )

    # Required arguments
    parser.add_argument(
        "ticker",
        type=str,
        help="Stock ticker symbol (e.g., QQQ, SPY, TSLA)"
    )

    # Option type
    parser.add_argument(
        "--type",
        type=str,
        choices=["call", "put"],
        default="put",
        dest="option_type",
        help="Option type to scan (default: put)"
    )

    # OTM filters
    parser.add_argument(
        "--otm-min",
        type=float,
        default=10.0,
        help="Minimum OTM percentage (default: 10.0)"
    )

    parser.add_argument(
        "--otm-max",
        type=float,
        default=20.0,
        help="Maximum OTM percentage (default: 20.0)"
    )

    # Days to expiry filters
    parser.add_argument(
        "--days-min",
        type=int,
        default=30,
        help="Minimum days to expiration (default: 30)"
    )

    parser.add_argument(
        "--days-max",
        type=int,
        default=90,
        help="Maximum days to expiration (default: 90)"
    )

    # Budget sizing
    parser.add_argument(
        "--budget",
        type=float,
        default=None,
        help="Budget for position sizing (optional)"
    )

    parser.add_argument(
        "--contracts",
        type=int,
        default=1,
        help="Target number of contracts (default: 1)"
    )

    # List expiries mode
    parser.add_argument(
        "--list-expiries",
        action="store_true",
        help="Just list available expiration dates and exit"
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

    # Validate ticker format
    ticker = args.ticker.strip().upper()
    if not ticker.isalpha() or len(ticker) > MAX_TICKER_LENGTH or len(ticker) == 0:
        print(
            f"ERROR: Invalid ticker '{args.ticker}'. "
            f"Must be 1-{MAX_TICKER_LENGTH} alphabetic characters.",
            file=sys.stderr,
        )
        return 1

    try:
        # Handle --list-expiries mode
        if args.list_expiries:
            print(
                f"Fetching expiration dates for {args.ticker}...",
                file=sys.stderr,
            )
            expirations = list_expiries(args.ticker)

            if not expirations:
                print(
                    f"No options expirations found for {args.ticker}",
                    file=sys.stderr,
                )
                return 1

            today = date.today()
            print(f"\nAvailable expirations for {args.ticker.upper()}:")
            print("-" * 40)

            for exp_str in expirations:
                try:
                    exp_date = date.fromisoformat(exp_str)
                    days_out = (exp_date - today).days
                    print(f"  {exp_str}  ({days_out:>4} days)")
                except ValueError:
                    print(f"  {exp_str}")

            print(f"\nTotal: {len(expirations)} expiration dates")
            print("")
            print(
                "DISCLAIMER: For educational purposes only. "
                "Not investment advice."
            )
            return 0

        # Validate numeric parameter bounds
        if args.otm_min < 0 or args.otm_max < 0:
            print(
                "ERROR: OTM percentages must be non-negative",
                file=sys.stderr,
            )
            return 1

        if args.days_min < 0 or args.days_max < 0:
            print(
                "ERROR: Days values must be non-negative",
                file=sys.stderr,
            )
            return 1

        if args.budget is not None and args.budget <= 0:
            print(
                "ERROR: Budget must be a positive number",
                file=sys.stderr,
            )
            return 1

        if args.contracts < 1:
            print(
                "ERROR: Target contracts must be at least 1",
                file=sys.stderr,
            )
            return 1

        # Validate parameter combinations
        if args.otm_min >= args.otm_max:
            print(
                "ERROR: --otm-min must be less than --otm-max",
                file=sys.stderr,
            )
            return 1

        if args.days_min >= args.days_max:
            print(
                "ERROR: --days-min must be less than --days-max",
                file=sys.stderr,
            )
            return 1

        # Run the scan
        print(
            f"Scanning {args.ticker} {args.option_type}s...",
            file=sys.stderr,
        )
        result = scan_chain(
            ticker=args.ticker,
            option_type=args.option_type,
            otm_min=args.otm_min,
            otm_max=args.otm_max,
            days_min=args.days_min,
            days_max=args.days_max,
            budget=args.budget,
            target_contracts=args.contracts,
        )

        # Format output
        if args.output == "json":
            output_str = format_output_json(result)
        else:
            output_str = format_output_human(result)

        # Display or save
        if args.save_to:
            save_path = Path(args.save_to).resolve()
            project_dir = project_root.resolve()
            if not str(save_path).startswith(str(project_dir)):
                print(
                    f"ERROR: Save path must be within the project directory: "
                    f"{project_dir}",
                    file=sys.stderr,
                )
                return 1
            save_path.parent.mkdir(parents=True, exist_ok=True)
            save_path.write_text(output_str)
            print(f"Saved to: {save_path}", file=sys.stderr)
        else:
            print(output_str)

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
