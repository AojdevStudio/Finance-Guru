#!/usr/bin/env python3
"""
Fidelity Transaction Parser CLI

Layer 3 of the 3-layer architecture - Command-line interface for parsing
and analyzing Fidelity brokerage transaction CSV exports.

ARCHITECTURE NOTE:
    Layer 1: Pydantic Models (transaction_inputs.py) - Data validation
    Layer 2: Parser Classes (fidelity_parser.py, reports.py) - Business logic
    Layer 3: CLI Interface (THIS FILE) - User integration

USAGE:
    # Import transactions
    uv run python src/data/fidelity_parser_cli.py import transactions.csv

    # View monthly summary
    uv run python src/data/fidelity_parser_cli.py summary --month 2025-01

    # View category breakdown
    uv run python src/data/fidelity_parser_cli.py categories

    # Export to CSV
    uv run python src/data/fidelity_parser_cli.py export --format csv --output budget.csv

AGENT USAGE:
    Market Researcher: Quick transaction overview, spending patterns
    Strategy Advisor: Budget analysis, margin monitoring
    Compliance Officer: Transaction audit, margin utilization review

Author: Finance Guru™ Development Team
Created: 2026-01-12
"""

import argparse
import sys
from datetime import datetime, date
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.models.transaction_inputs import (
    TransactionType,
    ExpenseCategory,
    ParserConfig,
)
from src.data.fidelity_parser import FidelityTransactionParser
from src.data.transaction_db import TransactionDatabase
from src.data.reports import (
    TransactionReporter,
    format_monthly_summary,
    format_category_breakdown,
    format_merchant_ranking,
)


def cmd_import(args: argparse.Namespace) -> int:
    """
    Import transactions from Fidelity CSV.

    Returns:
        Exit code (0 = success, 1 = error)
    """
    csv_path = Path(args.csv_file)
    if not csv_path.exists():
        print(f"ERROR: File not found: {csv_path}", file=sys.stderr)
        return 1

    print(f"Importing transactions from: {csv_path}")
    print("=" * 60)

    try:
        # Parse CSV
        config = ParserConfig(skip_rows=args.skip_rows)
        parser = FidelityTransactionParser(config)
        batch = parser.parse_csv(csv_path)

        print(f"Parsed {batch.count} transactions")
        if batch.date_range_start and batch.date_range_end:
            print(f"Date range: {batch.date_range_start} to {batch.date_range_end}")

        # Store in database if requested
        if not args.no_store:
            db = TransactionDatabase(args.database)
            new_count, dup_count = db.insert_batch(batch)
            print(f"\nDatabase update:")
            print(f"  New transactions: {new_count}")
            print(f"  Duplicates skipped: {dup_count}")
        else:
            print("\n(--no-store specified, transactions not saved to database)")

        # Show summary
        print("\n" + "=" * 60)
        print("IMPORT SUMMARY")
        print("=" * 60)

        # Count by type
        type_counts = {}
        for tx in batch.transactions:
            tx_type = tx.transaction_type.value
            type_counts[tx_type] = type_counts.get(tx_type, 0) + 1

        for tx_type, count in sorted(type_counts.items()):
            print(f"  {tx_type:<20}: {count:>5}")

        # Show totals
        reporter = TransactionReporter.from_batch(batch)
        cash_flow = reporter.cash_flow_analysis()

        print("\nTOTALS:")
        print(f"  Income:    ${cash_flow['total_income']:>12,.2f}")
        print(f"  Expenses:  ${cash_flow['total_expenses']:>12,.2f}")
        print(f"  Net:       ${cash_flow['net_cash_flow']:>12,.2f}")

        # List uncategorized
        uncategorized = reporter.get_uncategorized()
        if uncategorized:
            print(f"\n⚠️  {len(uncategorized)} transactions need categorization:")
            for tx in uncategorized[:5]:
                print(f"    {tx.date}: {tx.original_description[:40]} (${tx.amount})")
            if len(uncategorized) > 5:
                print(f"    ... and {len(uncategorized) - 5} more")

        return 0

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


def cmd_summary(args: argparse.Namespace) -> int:
    """
    Show monthly budget summary.

    Returns:
        Exit code
    """
    db = TransactionDatabase(args.database)

    # Determine month
    if args.month:
        month = args.month
    else:
        # Default to current month
        month = datetime.now().strftime("%Y-%m")

    transactions = db.get_transactions_by_month(month)

    if not transactions:
        print(f"No transactions found for {month}")
        return 0

    reporter = TransactionReporter(transactions)
    summary = reporter.monthly_summary(month)

    if args.output == "json":
        import json
        print(json.dumps(summary.model_dump(), indent=2, default=str))
    else:
        print(format_monthly_summary(summary))

    return 0


def cmd_categories(args: argparse.Namespace) -> int:
    """
    Show expense breakdown by category.

    Returns:
        Exit code
    """
    db = TransactionDatabase(args.database)

    # Get date filters
    start_date = None
    end_date = None

    if args.month:
        # Parse month to date range
        year, month = map(int, args.month.split("-"))
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)

    transactions = db.get_transactions(
        start_date=start_date,
        end_date=end_date,
        tx_type=TransactionType.EXPENSE,
    )

    if not transactions:
        print("No expense transactions found")
        return 0

    reporter = TransactionReporter(transactions)
    categories = reporter.category_breakdown()

    if args.output == "json":
        import json
        print(json.dumps({k: float(v) for k, v in categories.items()}, indent=2))
    else:
        print(format_category_breakdown(categories))

    return 0


def cmd_merchants(args: argparse.Namespace) -> int:
    """
    Show merchant ranking by spending.

    Returns:
        Exit code
    """
    db = TransactionDatabase(args.database)
    transactions = db.get_transactions(tx_type=TransactionType.EXPENSE)

    if not transactions:
        print("No expense transactions found")
        return 0

    reporter = TransactionReporter(transactions)
    merchants = reporter.merchant_ranking(limit=args.limit)

    if args.output == "json":
        import json
        data = [
            {"merchant": m, "total": float(t), "count": c}
            for m, t, c in merchants
        ]
        print(json.dumps(data, indent=2))
    else:
        print(format_merchant_ranking(merchants))

    return 0


def cmd_margin(args: argparse.Namespace) -> int:
    """
    Show margin analysis.

    Returns:
        Exit code
    """
    db = TransactionDatabase(args.database)

    # Get date filters
    start_date = None
    end_date = None

    if args.month:
        year, month = map(int, args.month.split("-"))
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)

    transactions = db.get_transactions(
        start_date=start_date,
        end_date=end_date,
    )

    if not transactions:
        print("No transactions found")
        return 0

    reporter = TransactionReporter(transactions)
    margin = reporter.margin_analysis()

    if args.output == "json":
        import json
        print(json.dumps({k: float(v) if hasattr(v, '__float__') else v for k, v in margin.items()}, indent=2))
    else:
        print("Margin Analysis")
        print("=" * 50)
        print(f"Interest Paid:         ${margin['total_interest_paid']:>12,.2f}")
        print(f"Total Drawn:           ${margin['total_drawn']:>12,.2f}")
        print(f"Total Paid Down:       ${margin['total_paid_down']:>12,.2f}")
        print(f"Net Margin Change:     ${margin['net_margin_change']:>12,.2f}")
        print("-" * 50)
        print(f"Margin Expenses:       ${margin['margin_expense_total']:>12,.2f}")
        print(f"Margin Expense Count:  {margin['margin_expense_count']:>12}")

    return 0


def cmd_export(args: argparse.Namespace) -> int:
    """
    Export transactions to file.

    Returns:
        Exit code
    """
    db = TransactionDatabase(args.database)

    output_path = Path(args.output)

    if args.format == "csv":
        count = db.export_csv(output_path)
    else:  # json
        count = db.export_json(output_path)

    print(f"Exported {count} transactions to: {output_path}")
    return 0


def cmd_categorize(args: argparse.Namespace) -> int:
    """
    Set category override for a merchant.

    Returns:
        Exit code
    """
    db = TransactionDatabase(args.database)

    if args.interactive:
        # Interactive mode - show uncategorized and prompt
        transactions = db.get_transactions(tx_type=TransactionType.EXPENSE)
        uncategorized = [
            tx for tx in transactions
            if tx.category == ExpenseCategory.UNCATEGORIZED
        ]

        if not uncategorized:
            print("No uncategorized transactions")
            return 0

        print(f"Found {len(uncategorized)} uncategorized transactions")
        print("\nAvailable categories:")
        for cat in ExpenseCategory:
            print(f"  {cat.value}")

        print("\nFor each transaction, enter a category or 's' to skip:")

        for tx in uncategorized:
            print(f"\n{tx.date}: {tx.original_description}")
            print(f"  Merchant: {tx.merchant or 'Unknown'}")
            print(f"  Amount: ${tx.amount}")

            while True:
                response = input("Category (or 's' to skip): ").strip()
                if response.lower() == 's':
                    break

                # Try to match category
                matched = None
                for cat in ExpenseCategory:
                    if response.lower() == cat.value.lower():
                        matched = cat
                        break

                if matched:
                    if tx.merchant:
                        db.set_category_override(tx.merchant, matched)
                        print(f"  Set {tx.merchant} → {matched.value}")
                    break
                else:
                    print(f"  Unknown category: {response}")

        # Apply overrides
        updated = db.apply_category_overrides()
        print(f"\nApplied overrides to {updated} transactions")

    else:
        # Single override
        if not args.merchant or not args.category:
            print("ERROR: --merchant and --category required (or use --interactive)")
            return 1

        # Validate category
        try:
            category = ExpenseCategory(args.category)
        except ValueError:
            print(f"ERROR: Unknown category: {args.category}")
            print("Available categories:")
            for cat in ExpenseCategory:
                print(f"  {cat.value}")
            return 1

        db.set_category_override(args.merchant, category)
        updated = db.apply_category_overrides()
        print(f"Set {args.merchant} → {category.value}")
        print(f"Applied to {updated} existing transactions")

    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    """
    Show database statistics.

    Returns:
        Exit code
    """
    db = TransactionDatabase(args.database)
    stats = db.get_stats()

    print("Database Statistics")
    print("=" * 50)
    print(f"Total transactions:  {stats['total_transactions']:>10}")
    print(f"Date range:          {stats['date_range_start']} to {stats['date_range_end']}")
    print(f"Total imports:       {stats['import_count']:>10}")

    print("\nBy Transaction Type:")
    for tx_type, count in stats['by_type'].items():
        print(f"  {tx_type:<20}: {count:>8}")

    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Fidelity Transaction Parser - Parse and analyze brokerage transactions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s import History_for_Account.csv
  %(prog)s summary --month 2025-01
  %(prog)s categories --month 2025-01
  %(prog)s merchants --limit 10
  %(prog)s margin --month 2025-01
  %(prog)s export --format csv --output budget.csv
  %(prog)s categorize --merchant "STARBUCKS" --category "Dining Out"
  %(prog)s categorize --interactive
        """,
    )

    # Global options
    parser.add_argument(
        "--database", "-d",
        type=str,
        default="data/transactions.db",
        help="Path to SQLite database (default: data/transactions.db)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Import command
    import_parser = subparsers.add_parser(
        "import",
        help="Import transactions from Fidelity CSV",
    )
    import_parser.add_argument(
        "csv_file",
        help="Path to Fidelity CSV file",
    )
    import_parser.add_argument(
        "--skip-rows",
        type=int,
        default=2,
        help="Number of header rows to skip (default: 2)",
    )
    import_parser.add_argument(
        "--no-store",
        action="store_true",
        help="Parse only, don't store in database",
    )
    import_parser.set_defaults(func=cmd_import)

    # Summary command
    summary_parser = subparsers.add_parser(
        "summary",
        help="Show monthly budget summary",
    )
    summary_parser.add_argument(
        "--month", "-m",
        type=str,
        help="Month in YYYY-MM format (default: current month)",
    )
    summary_parser.add_argument(
        "--output", "-o",
        choices=["human", "json"],
        default="human",
        help="Output format (default: human)",
    )
    summary_parser.set_defaults(func=cmd_summary)

    # Categories command
    categories_parser = subparsers.add_parser(
        "categories",
        help="Show expense breakdown by category",
    )
    categories_parser.add_argument(
        "--month", "-m",
        type=str,
        help="Month in YYYY-MM format (default: all time)",
    )
    categories_parser.add_argument(
        "--output", "-o",
        choices=["human", "json"],
        default="human",
        help="Output format (default: human)",
    )
    categories_parser.set_defaults(func=cmd_categories)

    # Merchants command
    merchants_parser = subparsers.add_parser(
        "merchants",
        help="Show merchant ranking by spending",
    )
    merchants_parser.add_argument(
        "--limit", "-l",
        type=int,
        default=20,
        help="Number of merchants to show (default: 20)",
    )
    merchants_parser.add_argument(
        "--output", "-o",
        choices=["human", "json"],
        default="human",
        help="Output format (default: human)",
    )
    merchants_parser.set_defaults(func=cmd_merchants)

    # Margin command
    margin_parser = subparsers.add_parser(
        "margin",
        help="Show margin analysis",
    )
    margin_parser.add_argument(
        "--month", "-m",
        type=str,
        help="Month in YYYY-MM format (default: all time)",
    )
    margin_parser.add_argument(
        "--output", "-o",
        choices=["human", "json"],
        default="human",
        help="Output format (default: human)",
    )
    margin_parser.set_defaults(func=cmd_margin)

    # Export command
    export_parser = subparsers.add_parser(
        "export",
        help="Export transactions to file",
    )
    export_parser.add_argument(
        "--format", "-f",
        choices=["csv", "json"],
        default="csv",
        help="Output format (default: csv)",
    )
    export_parser.add_argument(
        "--output", "-o",
        type=str,
        required=True,
        help="Output file path",
    )
    export_parser.set_defaults(func=cmd_export)

    # Categorize command
    categorize_parser = subparsers.add_parser(
        "categorize",
        help="Set category override for merchant",
    )
    categorize_parser.add_argument(
        "--merchant",
        type=str,
        help="Merchant name or pattern",
    )
    categorize_parser.add_argument(
        "--category",
        type=str,
        help="Category to assign",
    )
    categorize_parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Interactive categorization mode",
    )
    categorize_parser.set_defaults(func=cmd_categorize)

    # Stats command
    stats_parser = subparsers.add_parser(
        "stats",
        help="Show database statistics",
    )
    stats_parser.set_defaults(func=cmd_stats)

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Execute command
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
