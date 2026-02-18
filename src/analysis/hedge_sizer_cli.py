#!/usr/bin/env python3
"""Hedge Sizer CLI for Finance Guru Agents.

This module provides a command-line interface for determining how many hedge
contracts to buy, across which underlyings, and whether the cost fits the
monthly budget.

ARCHITECTURE NOTE:
This is Layer 3 of our 3-layer architecture:
    Layer 1: Pydantic Models (hedging_inputs.py) - Data validation
    Layer 2: Calculator Classes (hedge_sizer.py) - Business logic
    Layer 3: CLI Interface (THIS FILE) - Agent integration

AGENT USAGE:
    # Basic sizing with portfolio value and underlyings
    uv run python src/analysis/hedge_sizer_cli.py --portfolio 200000 --underlyings QQQ,SPY

    # Custom ratio (dollars per contract)
    uv run python src/analysis/hedge_sizer_cli.py --portfolio 200000 --underlyings QQQ,SPY --ratio 40000

    # Skip budget validation (no API calls)
    uv run python src/analysis/hedge_sizer_cli.py --portfolio 200000 --underlyings QQQ --skip-budget

    # JSON output for programmatic parsing
    uv run python src/analysis/hedge_sizer_cli.py --portfolio 200000 --underlyings QQQ --output json

    # Auto-read portfolio value from Fidelity CSV
    uv run python src/analysis/hedge_sizer_cli.py --underlyings QQQ,SPY --skip-budget

EDUCATIONAL NOTE:
Hedge sizing determines how many put option contracts to buy for portfolio
protection.  The default formula is 1 contract per $50,000 of portfolio value
(configurable via --ratio).  Contracts are allocated across underlyings by
weight (from config or equal weighting).  Budget validation warns when
estimated costs exceed the monthly budget but does NOT scale down the
recommendation.

Author: Finance Guru Development Team
Created: 2026-02-18
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.analysis.hedge_sizer import HedgeSizer
from src.config.config_loader import load_hedge_config

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DISCLAIMER = (
    "DISCLAIMER: For educational purposes only. Not investment advice.\n"
    "Consult a qualified financial professional before executing any trades."
)

# ---------------------------------------------------------------------------
# Human Output Formatting
# ---------------------------------------------------------------------------


def format_human_output(  # noqa: C901
    sizing: dict,
    source: str,
    budget: dict | None = None,
) -> str:
    """Format sizing and budget results in human-readable format.

    Shows contract allocation, coverage ratio, and budget analysis when
    available.  Warns but does NOT scale down when over budget.

    Args:
        sizing: Dict from HedgeSizer.calculate().
        source: Portfolio value source label (e.g., "cli_flag").
        budget: Optional dict from HedgeSizer.validate_budget().

    Returns:
        Formatted string for terminal display.
    """
    lines: list[str] = []

    portfolio_value = sizing["portfolio_value"]
    ratio = sizing["ratio_per_contract"]
    total = sizing["total_contracts"]
    allocations = sizing["allocations"]
    weights = sizing["weights_used"]
    notional = sizing["notional_coverage"]
    coverage_pct = sizing["coverage_pct"]

    lines.append("")
    lines.append("Hedge Sizer - Contract Sizing Recommendation")
    lines.append("=" * 50)
    lines.append(f"Portfolio Value: ${portfolio_value:,.2f} (source: {source})")
    lines.append(f"Sizing Ratio: 1 contract per ${ratio:,.0f}")
    lines.append(f"Total Contracts: {total}")

    # Allocation table
    lines.append("")
    lines.append("Allocation:")
    for ticker, count in allocations.items():
        weight = weights.get(ticker, 0.0)
        label = "contract" if count == 1 else "contracts"
        lines.append(f"  {ticker}: {count} {label} (weight: {weight * 100:.1f}%)")

    # Coverage ratio
    lines.append("")
    lines.append(
        f"Coverage: {total} contracts cover ~${notional:,.0f} notional "
        f"({coverage_pct:.1f}% of ${portfolio_value:,.0f} portfolio)"
    )

    # Budget analysis
    if budget is not None:
        lines.append("")
        lines.append("Budget Analysis:")
        monthly_cost = budget["total_estimated_monthly_cost"]
        monthly_budget = budget["monthly_budget"]
        utilization = budget["utilization_pct"]

        lines.append(f"  Estimated Monthly Cost: ${monthly_cost:,.2f}")
        lines.append(f"  Monthly Budget: ${monthly_budget:,.2f}")
        lines.append(f"  Utilization: {utilization:.1f}%")

        if not budget["within_budget"]:
            overage = monthly_cost - monthly_budget
            overage_pct = (overage / monthly_budget * 100) if monthly_budget > 0 else 0
            lines.append(
                f"  WARNING: Recommended cost exceeds budget "
                f"by ${overage:,.2f} ({overage_pct:.1f}% over)"
            )

        # Per-underlying breakdown
        per_ul = budget.get("per_underlying", [])
        if per_ul:
            lines.append("")
            lines.append("  Per Underlying:")
            for entry in per_ul:
                ticker = entry["ticker"]
                contracts = entry["contracts"]
                premium = entry["estimated_premium"]
                cost = entry["estimated_cost"]

                if premium == "estimate_unavailable":
                    lines.append(
                        f"    {ticker}: {contracts} contracts -- estimate unavailable"
                    )
                elif contracts > 0:
                    label = "contract" if contracts == 1 else "contracts"
                    lines.append(
                        f"    {ticker}: {contracts} {label} x "
                        f"${premium:.2f} premium = ${cost:,.2f}/mo"
                    )

        if budget.get("budget_warning"):
            # Only show general note warnings here (not the main warning
            # which is already shown above)
            warning = budget["budget_warning"]
            if "could not be priced" in warning or "Note:" in warning:
                lines.append("")
                lines.append(f"  Note: {warning}")

        lines.append("")
        lines.append(
            "Note: Premium estimates based on current mid-prices. "
            "Actual costs may vary."
        )

    # Disclaimer
    lines.append("")
    lines.append(DISCLAIMER)
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# JSON Output Formatting
# ---------------------------------------------------------------------------


def format_json_output(
    sizing: dict,
    source: str,
    budget: dict | None = None,
) -> str:
    """Format sizing and budget results as structured JSON.

    Merges sizing result and budget result into a single envelope with
    source and disclaimer fields.

    Args:
        sizing: Dict from HedgeSizer.calculate().
        source: Portfolio value source label.
        budget: Optional dict from HedgeSizer.validate_budget().

    Returns:
        JSON string with indent=2.
    """
    output: dict = {
        "portfolio_value": sizing["portfolio_value"],
        "portfolio_value_source": source,
        "ratio_per_contract": sizing["ratio_per_contract"],
        "total_contracts": sizing["total_contracts"],
        "allocations": sizing["allocations"],
        "weights_used": sizing["weights_used"],
        "underlyings": sizing["underlyings"],
        "notional_coverage": sizing["notional_coverage"],
        "coverage_pct": sizing["coverage_pct"],
    }

    if budget is not None:
        output["budget"] = budget

    output["disclaimer"] = DISCLAIMER

    return json.dumps(output, indent=2, default=str)


# ---------------------------------------------------------------------------
# Main CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the hedge sizer CLI.

    Returns:
        Configured ArgumentParser with all flags.
    """
    parser = argparse.ArgumentParser(
        description="Size hedge contracts for portfolio protection. "
        "Determines contract count, allocation, and budget fit.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --portfolio 200000 --underlyings QQQ,SPY
  %(prog)s --portfolio 200000 --underlyings QQQ,SPY,IWM --ratio 40000
  %(prog)s --portfolio 200000 --underlyings QQQ --budget 800
  %(prog)s --output json
  %(prog)s --skip-budget
        """,
    )

    # Portfolio value
    parser.add_argument(
        "--portfolio",
        "--portfolio-value",
        type=float,
        default=None,
        dest="portfolio",
        help="Portfolio value to protect in dollars. "
        "If omitted, reads from Fidelity CSV.",
    )

    # Underlyings
    parser.add_argument(
        "--underlyings",
        type=str,
        default=None,
        help="Comma-separated tickers to hedge (e.g., QQQ,SPY). "
        "Defaults to config underlying_weights.",
    )

    # Sizing ratio
    parser.add_argument(
        "--ratio",
        type=float,
        default=None,
        help="Dollars per contract (default: 50000 from config).",
    )

    # Budget override
    parser.add_argument(
        "--budget",
        type=float,
        default=None,
        help="Monthly hedge budget override in dollars.",
    )

    # Output format
    parser.add_argument(
        "--output",
        type=str,
        choices=["human", "json"],
        default="human",
        help="Output format (default: human).",
    )

    # Config path
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to user-profile.yaml (default: auto-detect).",
    )

    # Skip budget validation
    parser.add_argument(
        "--skip-budget",
        action="store_true",
        help="Skip live budget validation (no API calls).",
    )

    return parser


def main() -> int:
    """Main CLI entry point.

    Resolves portfolio value, calculates sizing and allocation, optionally
    validates budget, and formats output. Returns exit code.

    Returns:
        int: Exit code (0 success, 1 error, 130 user cancellation).
    """
    parser = build_parser()
    args = parser.parse_args()

    try:
        # Step 1: Load config with CLI overrides
        config_path = Path(args.config) if args.config else None
        cli_overrides: dict = {}
        if args.budget is not None:
            cli_overrides["monthly_budget"] = args.budget

        config = load_hedge_config(
            profile_path=config_path,
            cli_overrides=cli_overrides if cli_overrides else None,
        )

        # Step 2: Resolve portfolio value
        sizer = HedgeSizer(config)
        try:
            portfolio_value, source = sizer.resolve_portfolio_value(args.portfolio)
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            print(
                "Provide --portfolio flag or ensure a Fidelity balance CSV "
                "exists at notebooks/updates/Balances_for_Account_*.csv",
                file=sys.stderr,
            )
            return 1

        print(
            f"Portfolio value: ${portfolio_value:,.2f} (source: {source})",
            file=sys.stderr,
        )

        # Step 3: Parse underlyings
        underlyings: list[str] | None = None
        if args.underlyings:
            underlyings = [t.strip() for t in args.underlyings.upper().split(",")]
            underlyings = [t for t in underlyings if t]  # drop empties
            print(f"Underlyings: {', '.join(underlyings)}", file=sys.stderr)
        else:
            print(
                f"Underlyings: using config defaults "
                f"({', '.join(config.underlying_weights.keys())})",
                file=sys.stderr,
            )

        # Step 4: Calculate sizing
        result = sizer.calculate(portfolio_value, underlyings, args.ratio)
        print(
            f"Sizing: {result['total_contracts']} contracts",
            file=sys.stderr,
        )

        # Step 5: Optionally validate budget
        budget: dict | None = None
        if not args.skip_budget:
            print("Validating budget with live premiums...", file=sys.stderr)
            budget = sizer.validate_budget(result["allocations"], config)
            if budget["within_budget"]:
                print("Budget: within limits", file=sys.stderr)
            else:
                print(
                    f"Budget: WARNING - {budget['utilization_pct']:.1f}% utilization",
                    file=sys.stderr,
                )
        else:
            print("Budget validation: skipped (--skip-budget)", file=sys.stderr)

        # Step 6: Format output
        if args.output == "json":
            output = format_json_output(result, source, budget)
        else:
            output = format_human_output(result, source, budget)

        print(output)
        return 0

    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        import traceback

        traceback.print_exc(file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
