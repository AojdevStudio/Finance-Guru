#!/usr/bin/env python3
"""
Options Analytics CLI for Finance Guru™ Agents

Command-line interface for Black-Scholes options pricing and Greeks.

AGENT USAGE:
    # Price an option
    uv run python src/analysis/options_cli.py --ticker TSLA \\
        --spot 265 --strike 250 --days 90 --volatility 0.45 --type call

    # Calculate implied volatility
    uv run python src/analysis/options_cli.py --ticker TSLA \\
        --spot 265 --strike 250 --days 90 --market-price 25.50 --type call --implied-vol

    # JSON output
    uv run python src/analysis/options_cli.py --ticker TSLA \\
        --spot 265 --strike 250 --days 90 --volatility 0.45 --type call --output json

EDUCATIONAL NOTE:
This tool uses the Black-Scholes model for European options.
American options (can exercise early) may have higher prices.

Author: Finance Guru™ Development Team
Created: 2025-10-13
"""

import argparse
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.analysis.options import OptionsCalculator
from src.models.options_inputs import BlackScholesInput, ImpliedVolInput


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Calculate option prices and Greeks using Black-Scholes",
        epilog="""
Examples:
  # Price a call option
  %(prog)s --ticker TSLA --spot 265 --strike 250 --days 90 --volatility 0.45 --type call

  # Price a put option
  %(prog)s --ticker TSLA --spot 265 --strike 270 --days 30 --volatility 0.50 --type put

  # Calculate implied volatility
  %(prog)s --ticker TSLA --spot 265 --strike 250 --days 90 --market-price 25.50 --type call --implied-vol

  # JSON output
  %(prog)s --ticker TSLA --spot 265 --strike 250 --days 90 --volatility 0.45 --type call --output json
        """,
    )

    # Required parameters
    parser.add_argument("--ticker", type=str, required=True, help="Underlying ticker")
    parser.add_argument("--spot", type=float, required=True, help="Current stock price")
    parser.add_argument(
        "--strike", type=float, required=True, help="Option strike price"
    )
    parser.add_argument("--days", type=int, required=True, help="Days to expiration")
    parser.add_argument(
        "--type", type=str, required=True, choices=["call", "put"], help="Option type"
    )

    # Pricing vs Implied Vol
    parser.add_argument(
        "--volatility",
        type=float,
        default=None,
        help="Annual volatility (e.g., 0.45 = 45%%)",
    )
    parser.add_argument(
        "--market-price",
        type=float,
        default=None,
        help="Market price for implied vol calculation",
    )
    parser.add_argument(
        "--implied-vol", action="store_true", help="Calculate implied volatility"
    )

    # Optional parameters
    parser.add_argument(
        "--risk-free-rate",
        type=float,
        default=0.045,
        help="Annual risk-free rate (default: 4.5%%)",
    )
    parser.add_argument(
        "--dividend-yield",
        type=float,
        default=0.0,
        help="Annual dividend yield (default: 0%%)",
    )

    # Output
    parser.add_argument(
        "--output", choices=["human", "json"], default="human", help="Output format"
    )
    parser.add_argument("--save-to", type=str, default=None, help="Save output to file")

    args = parser.parse_args()

    # Validate inputs
    if args.implied_vol:
        if args.market_price is None:
            print(
                "ERROR: --market-price required for implied volatility calculation",
                file=sys.stderr,
            )
            sys.exit(1)
    else:
        if args.volatility is None:
            print("ERROR: --volatility required for option pricing", file=sys.stderr)
            sys.exit(1)

    try:
        calculator = OptionsCalculator()

        if args.implied_vol:
            # Calculate implied volatility
            print("🔍 Calculating implied volatility...", file=sys.stderr)

            iv_input = ImpliedVolInput(
                spot_price=args.spot,
                strike=args.strike,
                time_to_expiry=args.days / 365,
                market_price=args.market_price,
                option_type=args.type,
                risk_free_rate=args.risk_free_rate,
                dividend_yield=args.dividend_yield,
            )

            iv_result = calculator.calculate_implied_vol(iv_input)
            iv_result.ticker = args.ticker

            print(
                f"✅ Converged in {iv_result.iterations} iterations\n", file=sys.stderr
            )

            if args.output == "json":
                output_text = iv_result.model_dump_json(indent=2)
            else:
                output_text = format_implied_vol(iv_result, args)

        else:
            # Price option and calculate Greeks
            print("🧮 Calculating option price and Greeks...", file=sys.stderr)

            bs_input = BlackScholesInput(
                spot_price=args.spot,
                strike=args.strike,
                time_to_expiry=args.days / 365,
                volatility=args.volatility,
                risk_free_rate=args.risk_free_rate,
                dividend_yield=args.dividend_yield,
                option_type=args.type,
            )

            greeks = calculator.price_option(bs_input)
            greeks.ticker = args.ticker

            print("✅ Calculation complete!\n", file=sys.stderr)

            if args.output == "json":
                output_text = greeks.model_dump_json(indent=2)
            else:
                output_text = format_greeks(greeks, args)

        # Output results
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


def format_greeks(greeks, args) -> str:
    """Format Greeks output in human-readable format."""
    output = []
    output.append("=" * 70)
    output.append(f"📊 OPTIONS ANALYTICS: {greeks.ticker} {greeks.option_type.upper()}")
    output.append("=" * 70)
    output.append("")

    # Contract Details
    output.append("📋 CONTRACT DETAILS")
    output.append("-" * 70)
    output.append(f"  Type:                     {greeks.option_type.upper()}")
    output.append(f"  Strike:                   ${greeks.strike:>10.2f}")
    output.append(f"  Spot Price:               ${greeks.spot_price:>10.2f}")
    output.append(
        f"  Time to Expiry:           {greeks.time_to_expiry * 365:>10.0f} days ({greeks.time_to_expiry:.3f} years)"
    )
    output.append(f"  Volatility:               {greeks.volatility:>10.1%}")
    output.append(f"  Risk-free Rate:           {args.risk_free_rate:>10.1%}")
    output.append(f"  Moneyness:                {greeks.moneyness:>10}")
    output.append("")

    # Pricing
    output.append("💰 THEORETICAL PRICING")
    output.append("-" * 70)
    output.append(f"  Option Price:             ${greeks.option_price:>10.2f}")
    output.append(f"  Intrinsic Value:          ${greeks.intrinsic_value:>10.2f}")
    output.append(f"  Time Value:               ${greeks.time_value:>10.2f}")
    output.append("")

    # Greeks
    output.append("📈 THE GREEKS (Risk Sensitivities)")
    output.append("-" * 70)
    output.append(f"  Delta (Δ):                {greeks.delta:>10.4f}")
    output.append(f"    → $1 stock move = ${abs(greeks.delta):.2f} option move")
    output.append("")
    output.append(f"  Gamma (Γ):                {greeks.gamma:>10.4f}")
    output.append(f"    → $1 stock move = Delta changes by {greeks.gamma:.4f}")
    output.append("")
    output.append(f"  Theta (Θ):                ${greeks.theta:>10.2f} per day")
    output.append(f"    → Daily time decay = ${abs(greeks.theta):.2f}")
    output.append("")
    output.append(f"  Vega (ν):                 ${greeks.vega:>10.2f} per 1% vol")
    output.append(f"    → 1% volatility up = ${greeks.vega:.2f} option up")
    output.append("")
    output.append(f"  Rho (ρ):                  ${greeks.rho:>10.2f} per 1% rate")
    output.append(f"    → 1% interest rate up = ${abs(greeks.rho):.2f} option move")
    output.append("")

    # Interpretation
    output.append("💡 INTERPRETATION")
    output.append("-" * 70)

    if greeks.moneyness == "ITM":
        output.append(
            f"  • Option is IN THE MONEY (intrinsic value: ${greeks.intrinsic_value:.2f})"
        )
    elif greeks.moneyness == "ATM":
        output.append("  • Option is AT THE MONEY (near strike price)")
    else:
        output.append("  • Option is OUT OF THE MONEY (no intrinsic value)")

    if abs(greeks.delta) > 0.7:
        output.append(f"  • High delta ({greeks.delta:.2f}) - behaves like stock")
    elif abs(greeks.delta) < 0.3:
        output.append(
            f"  • Low delta ({greeks.delta:.2f}) - low probability of expiring ITM"
        )
    else:
        output.append(f"  • Moderate delta ({greeks.delta:.2f}) - balanced risk/reward")

    if greeks.gamma > 0.05:
        output.append(f"  • High gamma ({greeks.gamma:.4f}) - delta changes rapidly")

    output.append(f"  • Losing ${abs(greeks.theta):.2f} per day to time decay")

    if greeks.time_to_expiry < 0.1:  # Less than ~36 days
        output.append("  ⚠️  WARNING: Option near expiry - theta decay accelerating")

    output.append("")
    output.append("=" * 70)
    output.append("⚠️  DISCLAIMER: Black-Scholes model for European options.")
    output.append("    Real market prices may differ. Not investment advice.")
    output.append("=" * 70)

    return "\n".join(output)


def format_implied_vol(iv_result, args) -> str:
    """Format implied volatility output."""
    output = []
    output.append("=" * 70)
    output.append(f"📊 IMPLIED VOLATILITY: {iv_result.ticker}")
    output.append("=" * 70)
    output.append("")

    output.append("🔍 IMPLIED VOLATILITY CALCULATION")
    output.append("-" * 70)
    output.append(f"  Market Price:             ${iv_result.market_price:>10.2f}")
    output.append(f"  Calculated Price:         ${iv_result.calculated_price:>10.2f}")
    output.append(f"  Pricing Error:            ${iv_result.pricing_error:>10.4f}")
    output.append("")
    output.append(f"  IMPLIED VOLATILITY:       {iv_result.implied_volatility:>10.1%}")
    output.append("")
    output.append(f"  Solver Iterations:        {iv_result.iterations:>10}")
    output.append(
        f"  Converged:                {'Yes' if iv_result.converged else 'No':>10}"
    )
    output.append("")

    if iv_result.converged:
        output.append("  ✅ Solution converged successfully")
    else:
        output.append(
            "  ⚠️  WARNING: Solver did not converge - results may be unreliable"
        )

    output.append("")

    # Interpretation
    output.append("💡 INTERPRETATION")
    output.append("-" * 70)
    if iv_result.implied_volatility > 0.60:
        output.append(
            f"  • Very high IV ({iv_result.implied_volatility:.0%}) - market expects extreme volatility"
        )
    elif iv_result.implied_volatility > 0.40:
        output.append(
            f"  • High IV ({iv_result.implied_volatility:.0%}) - elevated uncertainty"
        )
    elif iv_result.implied_volatility > 0.20:
        output.append(
            f"  • Moderate IV ({iv_result.implied_volatility:.0%}) - normal volatility"
        )
    else:
        output.append(
            f"  • Low IV ({iv_result.implied_volatility:.0%}) - market expects stability"
        )

    output.append("")
    output.append("  💡 Compare implied volatility to historical volatility:")
    output.append("     - IV > historical → Market expects more volatility")
    output.append("     - IV < historical → Market expects less volatility")

    output.append("")
    output.append("=" * 70)
    return "\n".join(output)


if __name__ == "__main__":
    main()
