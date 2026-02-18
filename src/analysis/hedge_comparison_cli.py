#!/usr/bin/env python3
"""
SQQQ vs Protective Puts Hedge Comparison CLI for Finance Guru

This module provides a command-line interface for comparing SQQQ leveraged ETF
hedging against protective put hedging across multiple market drop scenarios.

ARCHITECTURE NOTE:
This is Layer 3 of our 3-layer architecture:
    Layer 1: Pydantic Models - Data validation (hedge_comparison_inputs.py)
    Layer 2: Calculator Classes - Business logic (hedge_comparison.py)
    Layer 3: CLI Interface (THIS FILE) - Agent integration

AGENT USAGE:
    # Compare hedge strategies across common market drop scenarios
    uv run python src/analysis/hedge_comparison_cli.py --scenarios -5,-10,-20,-40

    # JSON output for programmatic parsing
    uv run python src/analysis/hedge_comparison_cli.py --scenarios -5,-10,-20,-40 --output json

    # Custom QQQ spot and put parameters
    uv run python src/analysis/hedge_comparison_cli.py --scenarios -5,-10,-20,-40 \\
        --spot 500 --strike 450 --premium 8 --days 60

    # Adjust SQQQ allocation and volatility assumptions
    uv run python src/analysis/hedge_comparison_cli.py --scenarios -5,-10,-20,-40 \\
        --sqqq-allocation 25000 --daily-vol 0.02 --baseline-iv 0.25

EDUCATIONAL NOTE:
This CLI makes it easy for agents to compare two hedging strategies without
writing Python code. The tool:
1. Simulates SQQQ day-by-day with volatility drag and expense ratio
2. Prices protective puts with IV expansion during crashes
3. Shows side-by-side comparison at each market drop level
4. Finds breakeven points for both strategies
5. Includes required educational disclaimers

SQQQ decay is path-dependent: the same total market drop can produce very
different SQQQ outcomes depending on HOW the market gets there (gradual vs
crash vs volatile). This tool averages 3 representative paths.

Author: Finance Guru Development Team
Created: 2026-02-18
"""

import argparse
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.analysis.hedge_comparison import HedgeComparisonCalculator
from src.models.hedge_comparison_inputs import ComparisonOutput


def _preprocess_argv(argv: list[str]) -> list[str]:
    """Fix argv so --scenarios -5,-10,-20,-40 is parsed correctly.

    argparse treats values starting with '-' as flag names. We convert
    ``--scenarios -5,-10,-20,-40`` into ``--scenarios=-5,-10,-20,-40``
    so argparse sees it as a single option=value pair.

    Args:
        argv: Raw sys.argv[1:] list

    Returns:
        Cleaned argument list safe for argparse
    """
    cleaned: list[str] = []
    i = 0
    while i < len(argv):
        if argv[i] == "--scenarios" and i + 1 < len(argv):
            cleaned.append(f"--scenarios={argv[i + 1]}")
            i += 2
        else:
            cleaned.append(argv[i])
            i += 1
    return cleaned


def format_comparison_human(result: ComparisonOutput) -> str:
    """Format comparison results in human-readable table format.

    EDUCATIONAL NOTE:
    This creates a nicely formatted comparison table showing SQQQ vs put
    performance at each market drop scenario. Includes breakeven analysis
    and required disclaimers.

    Args:
        result: Full comparison output from HedgeComparisonCalculator

    Returns:
        Formatted string for terminal display
    """
    output: list[str] = []
    params = result.parameters

    output.append("=" * 70)
    output.append("SQQQ vs PROTECTIVE PUTS - HEDGE COMPARISON")
    output.append("=" * 70)
    output.append("")

    # Parameters section
    strike = params.get("put_strike", 0.0)
    spot = params.get("spot_price", 0.0)
    otm_pct = ((spot - strike) / spot * 100) if spot > 0 else 0.0
    output.append("Parameters:")
    output.append(
        f"  QQQ Spot: ${spot:,.2f} | "
        f"Put Strike: ${strike:,.2f} ({otm_pct:.0f}% OTM) | "
        f"Premium: ${params.get('put_premium', 0.0):,.2f}"
    )
    output.append(
        f"  SQQQ Allocation: ${params.get('sqqq_allocation', 0.0):,.0f} | "
        f"Holding Period: {params.get('holding_days', 0)} days | "
        f"Baseline IV: {params.get('baseline_iv', 0.0):.0%}"
    )
    output.append("")

    # Table header
    header = (
        f"{'Scenario':<20} {'SQQQ Return':>12} {'Naive -3x':>10} "
        f"{'Drag':>7} {'Put PnL':>10} {'Put PnL%':>10} {'Winner':>8}"
    )
    output.append(header)
    output.append("-" * len(header))

    # Table rows
    for row in result.scenarios:
        sqqq = row.sqqq
        put = row.put

        sqqq_return_str = f"{sqqq.sqqq_return_pct:+.1%}"
        naive_str = f"{sqqq.naive_3x_return_pct:+.1%}"
        drag_str = f"{sqqq.volatility_drag_pct:.1%}"
        put_pnl_str = f"${put.pnl:+,.2f}"
        put_pnl_pct_str = f"{put.pnl_pct:+,.1%}"
        winner_str = row.winner

        output.append(
            f"{row.scenario_label:<20} {sqqq_return_str:>12} {naive_str:>10} "
            f"{drag_str:>7} {put_pnl_str:>10} {put_pnl_pct_str:>10} {winner_str:>8}"
        )

    output.append("")

    # Breakeven analysis
    output.append("Breakeven Analysis:")
    output.append(
        f"  SQQQ: Profitable when QQQ drops > {abs(result.sqqq_breakeven_drop):.1%} "
        f"(covers fees + drag)"
    )
    output.append(
        f"  Put:  Profitable when QQQ drops > {abs(result.put_breakeven_drop):.1%} "
        f"(covers premium)"
    )
    output.append("")

    # Disclaimers
    output.append("=" * 70)
    output.append("DISCLAIMERS:")
    for disclaimer in result.disclaimers:
        output.append(f"  * {disclaimer}")
    output.append("=" * 70)

    return "\n".join(output)


def main() -> int:
    """Main CLI entry point for hedge comparison.

    EDUCATIONAL NOTE:
    This function:
    1. Parses command-line arguments
    2. Validates scenario inputs (must be negative, > -100%)
    3. Creates HedgeComparisonCalculator with user parameters
    4. Runs comparison across all scenarios
    5. Formats and displays output (human-readable or JSON)

    Returns:
        int: Exit code (0 for success, 1 for error, 130 for user cancellation)
    """
    parser = argparse.ArgumentParser(
        description="Compare SQQQ vs protective puts hedging strategies for Finance Guru",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic comparison across common market drops
  %(prog)s --scenarios -5,-10,-20,-40

  # JSON output for agent parsing
  %(prog)s --scenarios -5,-10,-20,-40 --output json

  # Custom QQQ spot and put parameters
  %(prog)s --scenarios -5,-10,-20,-40 --spot 500 --strike 450 --premium 8

  # Longer holding period with higher volatility
  %(prog)s --scenarios -5,-10,-20,-40 --days 60 --daily-vol 0.02

  # Larger SQQQ hedge allocation
  %(prog)s --scenarios -5,-10,-20,-40 --sqqq-allocation 25000

  # Full custom configuration
  %(prog)s --scenarios -5,-10,-20,-40 \\
      --spot 500 --strike 450 --premium 8 --days 60 \\
      --sqqq-allocation 25000 --baseline-iv 0.25 --daily-vol 0.02
        """,
    )

    # Required arguments
    parser.add_argument(
        "--scenarios",
        type=str,
        required=True,
        help=(
            "Comma-separated market drop percentages. "
            "Example: -5,-10,-20,-40 (interpreted as -5%%, -10%%, etc.)"
        ),
    )

    # QQQ / Put parameters
    parser.add_argument(
        "--spot",
        type=float,
        default=480.0,
        help="Current QQQ spot price (default: 480.0)",
    )
    parser.add_argument(
        "--strike",
        type=float,
        default=None,
        help="Put strike price (default: 10%% OTM = spot * 0.90)",
    )
    parser.add_argument(
        "--premium",
        type=float,
        default=5.0,
        help="Put premium paid per share (default: 5.0)",
    )

    # SQQQ parameters
    parser.add_argument(
        "--sqqq-allocation",
        type=float,
        default=10000.0,
        help="Dollar amount allocated to SQQQ (default: 10000.0)",
    )

    # Volatility / IV parameters
    parser.add_argument(
        "--baseline-iv",
        type=float,
        default=0.20,
        help="Baseline implied volatility (default: 0.20 = 20%%)",
    )
    parser.add_argument(
        "--daily-vol",
        type=float,
        default=0.015,
        help="Expected daily QQQ volatility (default: 0.015 = 1.5%%)",
    )

    # Holding period
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Holding period in trading days (default: 30)",
    )

    # Output format
    parser.add_argument(
        "--output",
        type=str,
        choices=["human", "json"],
        default="human",
        help="Output format (default: human)",
    )

    args = parser.parse_args(_preprocess_argv(sys.argv[1:]))

    try:
        # Step 1: Parse scenarios
        raw_scenarios = args.scenarios.split(",")
        scenarios: list[float] = []
        for s in raw_scenarios:
            s = s.strip()
            val = float(s) / 100.0  # -5 becomes -0.05
            scenarios.append(val)

        # Step 2: Validate scenarios
        for val in scenarios:
            if val >= 0:
                print(
                    f"ERROR: Scenario {val * 100:.0f}% is not negative. "
                    "Scenarios must be negative market drops (e.g., -5,-10,-20).",
                    file=sys.stderr,
                )
                return 1
            if val <= -1.0:
                print(
                    f"ERROR: Scenario {val * 100:.0f}% exceeds -100%. "
                    "Market cannot drop more than 99%.",
                    file=sys.stderr,
                )
                return 1

        # Step 3: Determine strike
        strike = args.strike if args.strike is not None else args.spot * 0.90

        # Step 4: Create calculator
        print(
            f"Analyzing {len(scenarios)} market drop scenarios...",
            file=sys.stderr,
        )
        print(
            f"QQQ Spot: ${args.spot:,.2f} | "
            f"Put Strike: ${strike:,.2f} | "
            f"SQQQ: ${args.sqqq_allocation:,.0f}",
            file=sys.stderr,
        )

        calc = HedgeComparisonCalculator(
            spot_price=args.spot,
            put_strike=strike,
            put_premium=args.premium,
            sqqq_allocation=args.sqqq_allocation,
            baseline_iv=args.baseline_iv,
            holding_days=args.days,
            daily_volatility=args.daily_vol,
        )

        # Step 5: Run comparison
        result = calc.compare_all(scenarios)
        print("Comparison complete.", file=sys.stderr)
        print("", file=sys.stderr)

        # Step 6: Format output
        if args.output == "json":
            output_text = result.model_dump_json(indent=2)
        else:
            output_text = format_comparison_human(result)

        # Step 7: Print to stdout
        print(output_text)

        return 0

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc(file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
