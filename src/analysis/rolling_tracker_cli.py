#!/usr/bin/env python3
"""Rolling Tracker CLI for Finance Guru Agents.

This module provides a subcommand-based CLI for monitoring and managing hedge
positions: status display with live pricing, roll suggestions, roll logging,
and history viewing.

ARCHITECTURE NOTE:
This is Layer 3 of our 3-layer architecture:
    Layer 1: Pydantic Models (hedging_inputs.py) - Data validation
    Layer 2: Calculator Classes (rolling_tracker.py) - Business logic
    Layer 3: CLI Interface (THIS FILE) - Agent integration

This is the first argparse subcommand CLI in the codebase (HEDG-04).

AGENT USAGE:
    # View all hedge positions with live pricing and P&L
    uv run python src/analysis/rolling_tracker_cli.py status

    # JSON output for programmatic parsing
    uv run python src/analysis/rolling_tracker_cli.py status --output json

    # Get roll suggestions for expiring positions (DTE <= 7)
    uv run python src/analysis/rolling_tracker_cli.py suggest-roll

    # Log a completed roll
    uv run python src/analysis/rolling_tracker_cli.py log-roll \
        --ticker QQQ --strike 440 --expiry 2026-06-19 --premium 8.50

    # View roll history
    uv run python src/analysis/rolling_tracker_cli.py history

EDUCATIONAL NOTE:
Rolling is the process of closing an expiring options position and opening a
new one with a later expiration date, potentially at a different strike price.
This maintains continuous portfolio protection without coverage gaps.

DTE COLOR CODING:
    Red   (< 7 days):   [ROLL]     - Immediate action needed
    Yellow (7-14 days):  [EXPIRING] - Plan roll soon
    Green  (> 14 days):  (blank)    - No action needed

Text markers are included alongside colors for accessibility when output is
piped or redirected (colors stripped but markers remain).

DISCLAIMER:
For educational purposes only. Not investment advice. Options involve
significant risk. Consult a qualified financial professional before trading.

Author: Finance Guru Development Team
Created: 2026-02-18
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.analysis.rolling_tracker import RollingTracker
from src.config.config_loader import load_hedge_config

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DISCLAIMER = (
    "DISCLAIMER: For educational purposes only. Not investment advice. "
    "Consult a qualified financial advisor before making investment decisions."
)

# ANSI color codes for DTE status
COLOR_RED = "\033[91m"
COLOR_YELLOW = "\033[93m"
COLOR_GREEN = "\033[92m"
COLOR_RESET = "\033[0m"

DTE_COLORS = {
    "red": COLOR_RED,
    "yellow": COLOR_YELLOW,
    "green": COLOR_GREEN,
}


# ---------------------------------------------------------------------------
# Formatting Helpers
# ---------------------------------------------------------------------------


def _colorize(text: str, color: str) -> str:
    """Wrap text in ANSI color codes.

    Args:
        text: The text to colorize.
        color: Color key ('red', 'yellow', 'green').

    Returns:
        Colorized string with reset at the end.
    """
    ansi = DTE_COLORS.get(color, "")
    if not ansi:
        return text
    return f"{ansi}{text}{COLOR_RESET}"


def _dte_marker(status: str) -> str:
    """Return text marker for DTE status (accessibility for piped output).

    Args:
        status: Status label from RollingTracker ('ROLL', 'EXPIRING', 'OK').

    Returns:
        Text marker string: '[ROLL]', '[EXPIRING]', or empty string.
    """
    if status == "ROLL":
        return "[ROLL]"
    if status == "EXPIRING":
        return "[EXPIRING]"
    return ""


def _format_currency(value: float) -> str:
    """Format a float as currency with sign.

    Args:
        value: Dollar amount.

    Returns:
        Formatted string like '$1,234.56' or '-$1,234.56'.
    """
    if value < 0:
        return f"-${abs(value):,.2f}"
    return f"${value:,.2f}"


# ---------------------------------------------------------------------------
# Subcommand Handlers
# ---------------------------------------------------------------------------


def handle_status(args: argparse.Namespace, tracker: RollingTracker) -> int:  # noqa: C901
    """Handle the 'status' subcommand: display all hedge positions.

    Args:
        args: Parsed CLI arguments.
        tracker: Initialized RollingTracker instance.

    Returns:
        Exit code (0 success, 1 error).
    """
    status = tracker.get_status()

    if args.output == "json":
        print(json.dumps(status, indent=2, default=str))
        return 0

    positions = status["positions"]
    summary = status["summary"]

    lines: list[str] = []
    lines.append("")
    lines.append("=" * 80)
    lines.append("HEDGE POSITION STATUS")
    lines.append("=" * 80)

    if not positions:
        lines.append("")
        lines.append("  No active hedge positions.")
        lines.append("  Add positions to fin-guru-private/hedging/positions.yaml")
    else:
        # Table header
        lines.append("")
        lines.append(
            f"  {'Ticker':<8} {'Type':<12} {'Strike':>8} {'Expiry':<12} "
            f"{'DTE':>5} {'Entry$':>10} {'Current$':>10} {'P&L':>10} {'Status':<12}"
        )
        lines.append(f"  {'-' * 78}")

        # Table rows
        for pos in positions:
            ticker = pos["ticker"]
            hedge_type = pos["hedge_type"]
            strike = f"${pos['strike']:,.0f}" if pos.get("strike") else "--"
            expiry = pos.get("expiry", "--") or "--"
            dte = pos.get("dte")
            dte_str = str(dte) if dte is not None else "--"
            entry_premium = pos.get("entry_premium", 0.0)
            current_value = pos.get("current_value", 0.0)
            pnl = pos.get("p_and_l", 0.0)
            status_label = pos.get("status", "OK")
            dte_color = pos.get("dte_color", "green")

            # Format entry cost based on hedge type
            if hedge_type == "put":
                entry_str = f"${entry_premium:,.2f}"
            else:
                entry_str = f"${entry_premium:,.2f}"

            current_str = _format_currency(current_value)
            pnl_str = _format_currency(pnl)

            # Apply DTE color and text marker
            marker = _dte_marker(status_label)
            colored_dte = _colorize(dte_str, dte_color)
            status_display = _colorize(f"{status_label} {marker}".strip(), dte_color)

            lines.append(
                f"  {ticker:<8} {hedge_type:<12} {strike:>8} {expiry:<12} "
                f"{colored_dte:>5} {entry_str:>10} {current_str:>10} "
                f"{pnl_str:>10} {status_display:<12}"
            )

    # Summary row
    lines.append("")
    lines.append("-" * 80)
    lines.append(
        f"  Total: {summary['position_count']} positions | "
        f"Cost: {_format_currency(summary['total_hedge_cost'])} | "
        f"Value: {_format_currency(summary['total_current_value'])} | "
        f"P&L: {_format_currency(summary['total_pnl'])}"
    )
    lines.append("-" * 80)

    # Disclaimer
    lines.append("")
    lines.append(DISCLAIMER)
    lines.append("")

    print("\n".join(lines))
    return 0


def handle_suggest_roll(args: argparse.Namespace, tracker: RollingTracker) -> int:
    """Handle the 'suggest-roll' subcommand: identify positions needing rolls.

    Args:
        args: Parsed CLI arguments.
        tracker: Initialized RollingTracker instance.

    Returns:
        Exit code (0 success, 1 error).
    """
    suggestions = tracker.suggest_rolls()

    if args.output == "json":
        print(json.dumps(suggestions, indent=2, default=str))
        return 0

    lines: list[str] = []
    lines.append("")
    lines.append("=" * 80)
    lines.append("ROLL SUGGESTIONS")
    lines.append("=" * 80)

    if not suggestions:
        lines.append("")
        lines.append("  No positions within the 7-day roll window.")
    else:
        for suggestion in suggestions:
            current = suggestion["current_position"]
            lines.append("")
            lines.append(
                f"  --- Roll Needed: {current['ticker']} Put "
                f"${current.get('strike', 0):,.0f} "
                f"exp {current.get('expiry', 'N/A')} "
                f"(DTE: {current.get('dte', 'N/A')}) ---"
            )

            if suggestion.get("suggested"):
                s = suggestion["suggested"]
                symbol = s.get("contract_symbol", "N/A")
                strike = s.get("strike", 0)
                expiry = s.get("expiry", "N/A")
                dte = s.get("days_to_expiry", "N/A")
                new_premium = suggestion.get("new_premium", 0)
                remaining = suggestion.get("remaining_value", 0)
                roll_cost = suggestion.get("estimated_roll_cost", 0)

                lines.append(
                    f"  Suggested: {symbol} | "
                    f"Strike: ${strike:,.0f} | "
                    f"Expiry: {expiry} | "
                    f"DTE: {dte}"
                )
                lines.append(
                    f"  Roll cost: {_format_currency(roll_cost)} "
                    f"(new premium ${new_premium:,.2f} - "
                    f"remaining value ${remaining:,.2f})"
                )
            else:
                message = suggestion.get("message", "no candidates found")
                lines.append(f"  {message}")

    # Disclaimer
    lines.append("")
    lines.append("-" * 80)
    lines.append(DISCLAIMER)
    lines.append("")

    print("\n".join(lines))
    return 0


def handle_log_roll(args: argparse.Namespace, tracker: RollingTracker) -> int:
    """Handle the 'log-roll' subcommand: record a completed roll.

    Args:
        args: Parsed CLI arguments.
        tracker: Initialized RollingTracker instance.

    Returns:
        Exit code (0 success, 1 error).
    """
    try:
        expiry_date = datetime.strptime(args.expiry, "%Y-%m-%d").date()
    except ValueError:
        print(
            f"ERROR: Invalid date format '{args.expiry}'. Use YYYY-MM-DD.",
            file=sys.stderr,
        )
        return 1

    try:
        result = tracker.log_roll(
            ticker=args.ticker.upper(),
            new_strike=args.strike,
            new_expiry=expiry_date,
            new_premium=args.premium,
        )
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    if args.output == "json":
        print(json.dumps(result, indent=2, default=str))
        return 0

    old = result["old_position"]
    new = result["new_position"]

    lines: list[str] = []
    lines.append("")
    lines.append("=" * 80)
    lines.append("ROLL LOGGED")
    lines.append("=" * 80)
    lines.append("")
    lines.append(
        f"  Rolled {args.ticker.upper()} put: "
        f"${old.get('strike', 0):,.0f} exp {old.get('expiry', 'N/A')} -> "
        f"${new.get('strike', 0):,.0f} exp {new.get('expiry', 'N/A')} "
        f"(premium: ${args.premium:,.2f})"
    )
    lines.append("")
    lines.append(DISCLAIMER)
    lines.append("")

    print("\n".join(lines))
    return 0


def handle_history(args: argparse.Namespace, tracker: RollingTracker) -> int:
    """Handle the 'history' subcommand: display roll history.

    Args:
        args: Parsed CLI arguments.
        tracker: Initialized RollingTracker instance.

    Returns:
        Exit code (0 success, 1 error).
    """
    history = tracker.get_history()

    if args.output == "json":
        print(json.dumps(history, indent=2, default=str))
        return 0

    lines: list[str] = []
    lines.append("")
    lines.append("=" * 80)
    lines.append("ROLL HISTORY")
    lines.append("=" * 80)

    if not history:
        lines.append("")
        lines.append("  No roll history found.")
    else:
        # Table header
        lines.append("")
        lines.append(
            f"  {'Date':<12} {'Ticker':<8} {'Old Strike':>10} "
            f"{'New Strike':>10} {'Old Expiry':<12} {'New Expiry':<12} {'Reason':<10}"
        )
        lines.append(f"  {'-' * 76}")

        for record in history:
            roll_date = record.get("roll_date", "--")
            reason = record.get("reason", "--")

            old_pos = record.get("old_position", {})
            new_pos = record.get("new_position", {})

            ticker = old_pos.get("ticker", "--")
            old_strike = old_pos.get("strike")
            new_strike = new_pos.get("strike")
            old_expiry = old_pos.get("expiry", "--")
            new_expiry = new_pos.get("expiry", "--")

            old_strike_str = f"${old_strike:,.0f}" if old_strike else "--"
            new_strike_str = f"${new_strike:,.0f}" if new_strike else "--"

            lines.append(
                f"  {str(roll_date):<12} {ticker:<8} {old_strike_str:>10} "
                f"{new_strike_str:>10} {str(old_expiry):<12} "
                f"{str(new_expiry):<12} {reason:<10}"
            )

    # Disclaimer
    lines.append("")
    lines.append("-" * 80)
    lines.append(DISCLAIMER)
    lines.append("")

    print("\n".join(lines))
    return 0


# ---------------------------------------------------------------------------
# Parser Construction
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser with subcommands for the rolling tracker CLI.

    Uses a shared parent parser so --output and --config work when placed
    after the subcommand name (e.g., ``status --output json``).

    Returns:
        Configured ArgumentParser with status, suggest-roll, log-roll,
        and history subcommands.
    """
    # Shared arguments inherited by every subcommand
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument(
        "--output",
        choices=["human", "json"],
        default="human",
        help="Output format (default: human)",
    )
    shared.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to user-profile.yaml (default: auto-detect)",
    )

    parser = argparse.ArgumentParser(
        description=(
            "Rolling Tracker - Monitor and manage hedge positions. "
            "First subcommand-based CLI in the Finance Guru toolchain (HEDG-04)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  # View all hedge positions with live pricing and P&L
  %(prog)s status

  # JSON output for programmatic parsing
  %(prog)s status --output json

  # Get roll suggestions for expiring positions (DTE <= 7)
  %(prog)s suggest-roll

  # Log a completed roll
  %(prog)s log-roll --ticker QQQ --strike 440 --expiry 2026-06-19 --premium 8.50

  # View roll history
  %(prog)s history

  # Use a custom config file
  %(prog)s status --config path/to/user-profile.yaml

DTE Color Coding:
  Green  (> 14 days)  - No action needed
  Yellow (7-14 days)  - [EXPIRING] Plan roll soon
  Red    (< 7 days)   - [ROLL] Immediate action needed

Agent Use Cases:
  - Strategy Advisor: Monitor hedge coverage, plan roll schedule
  - Compliance Officer: Verify position limits and roll timeliness
  - Margin Specialist: Track hedge costs against budget
""",
    )

    # Subcommands
    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        help="Available commands",
    )

    # --- status ---
    status_parser = subparsers.add_parser(
        "status",
        parents=[shared],
        help="Display all hedge positions with live pricing, P&L, and DTE status",
        description=(
            "Show all active hedge positions enriched with live market pricing, "
            "unrealized P&L, days to expiry, and roll status indicators."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  %(prog)s
  %(prog)s --output json
""",
    )
    status_parser.set_defaults(func=handle_status)

    # --- suggest-roll ---
    suggest_parser = subparsers.add_parser(
        "suggest-roll",
        parents=[shared],
        help="Identify positions within 7-day DTE window and suggest replacements",
        description=(
            "Scan active put positions for those expiring within 7 days and "
            "suggest replacement contracts from the options chain."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  %(prog)s
  %(prog)s --output json
""",
    )
    suggest_parser.set_defaults(func=handle_suggest_roll)

    # --- log-roll ---
    log_parser = subparsers.add_parser(
        "log-roll",
        parents=[shared],
        help="Record a completed roll (archives old position, creates new one)",
        description=(
            "Log a roll transaction: auto-detects the old position by ticker, "
            "archives it to roll history, and creates a new position with the "
            "specified strike, expiry, and premium."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  %(prog)s --ticker QQQ --strike 440 --expiry 2026-06-19 --premium 8.50
  %(prog)s --ticker SPY --strike 520 --expiry 2026-07-17 --premium 12.00 --output json
""",
    )
    log_parser.add_argument(
        "--ticker",
        type=str,
        required=True,
        help="Ticker of the position to roll (e.g., QQQ)",
    )
    log_parser.add_argument(
        "--strike",
        type=float,
        required=True,
        help="New strike price (e.g., 440)",
    )
    log_parser.add_argument(
        "--expiry",
        type=str,
        required=True,
        help="New expiry date in YYYY-MM-DD format (e.g., 2026-06-19)",
    )
    log_parser.add_argument(
        "--premium",
        type=float,
        required=True,
        help="Premium paid per contract for the new position (e.g., 8.50)",
    )
    log_parser.set_defaults(func=handle_log_roll)

    # --- history ---
    history_parser = subparsers.add_parser(
        "history",
        parents=[shared],
        help="Display roll history from past rolls and expired positions",
        description=(
            "Show all past roll transactions and expired positions from "
            "roll-history.yaml."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  %(prog)s
  %(prog)s --output json
""",
    )
    history_parser.set_defaults(func=handle_history)

    return parser


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------


def main() -> int:
    """Main CLI entry point.

    Parses arguments, loads hedge configuration, initializes the
    RollingTracker, and dispatches to the appropriate subcommand handler.

    Returns:
        int: Exit code (0 success, 1 error, 130 user cancellation).
    """
    parser = build_parser()
    args = parser.parse_args()

    try:
        # Load hedge config with priority chain: CLI > YAML > defaults
        cli_overrides: dict = {}  # No config-overrideable CLI flags currently
        config_path = Path(args.config) if args.config else None
        config = load_hedge_config(
            profile_path=config_path,
            cli_overrides=cli_overrides,
        )

        tracker = RollingTracker(config)

        # Dispatch to subcommand handler
        result: int = args.func(args, tracker)
        return result

    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
