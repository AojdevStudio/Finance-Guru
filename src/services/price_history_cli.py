#!/usr/bin/env python3
"""
Price History CLI for Finance Guru™

USAGE:
    # Capture daily snapshot for all holdings
    uv run python src/services/price_history_cli.py capture

    # Capture specific symbols
    uv run python src/services/price_history_cli.py capture TSLA PLTR NVDA

    # Import historical data (backfill)
    uv run python src/services/price_history_cli.py import TSLA PLTR --days 365

    # View price history
    uv run python src/services/price_history_cli.py history TSLA --days 30

    # View portfolio value history
    uv run python src/services/price_history_cli.py portfolio --days 90

    # Export for Google Sheets
    uv run python src/services/price_history_cli.py export --format csv

    # Show database stats
    uv run python src/services/price_history_cli.py stats

Author: Finance Guru™ Development Team
Created: 2026-01-14
"""

import argparse
import json
import sys
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.services.price_history_service import PriceHistoryService


def cmd_capture(args):
    """Capture daily price snapshot."""
    service = PriceHistoryService()

    symbols = args.symbols if args.symbols else None
    snapshot_date = None
    if args.date:
        snapshot_date = date.fromisoformat(args.date)

    print(f"\n{'='*60}")
    print("📸 CAPTURING PRICE SNAPSHOT")
    print(f"{'='*60}\n")

    result = service.capture_daily_snapshot(
        symbols=symbols,
        snapshot_date=snapshot_date
    )

    if result["success"]:
        print(f"✅ Captured {result['captured']} price snapshots for {result['snapshot_date']}")

        if result.get("symbols"):
            print(f"\n📊 Symbols: {', '.join(result['symbols'][:10])}")
            if len(result['symbols']) > 10:
                print(f"   ... and {len(result['symbols']) - 10} more")

        if result.get("portfolio_snapshot"):
            ps = result["portfolio_snapshot"]
            print(f"\n💼 Portfolio Snapshot:")
            print(f"   Total Value:  ${ps['total_value']:,.2f}")
            print(f"   Layer 1:      ${ps['layer1_value']:,.2f}")
            print(f"   Layer 2:      ${ps['layer2_value']:,.2f}")
            print(f"   Layer 3:      ${ps['layer3_value']:,.2f}")
            print(f"   Holdings:     {ps['holding_count']}")

        if result.get("errors"):
            print(f"\n⚠️  Errors ({len(result['errors'])}):")
            for err in result["errors"][:5]:
                print(f"   - {err}")
    else:
        print(f"❌ Error: {result.get('error', 'Unknown error')}")

    if args.output == "json":
        print(f"\n{json.dumps(result, indent=2, default=str)}")


def cmd_import(args):
    """Import historical price data."""
    service = PriceHistoryService()

    if not args.symbols:
        print("❌ Error: At least one symbol required for import")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"📥 IMPORTING HISTORICAL DATA ({args.days} days)")
    print(f"{'='*60}\n")

    result = service.import_historical_data(
        symbols=args.symbols,
        days=args.days
    )

    print(f"✅ Imported {result['total_imported']} records")
    print(f"   Date range: {result['date_range']['start']} to {result['date_range']['end']}")

    print("\n📊 Results by symbol:")
    for symbol, res in result["results"].items():
        if "imported" in res:
            print(f"   {symbol}: {res['imported']} records")
        else:
            print(f"   {symbol}: ❌ {res.get('error', 'Unknown error')}")

    if args.output == "json":
        print(f"\n{json.dumps(result, indent=2, default=str)}")


def cmd_history(args):
    """View price history for a symbol."""
    service = PriceHistoryService()

    print(f"\n{'='*60}")
    print(f"📈 PRICE HISTORY: {args.symbol.upper()}")
    print(f"{'='*60}\n")

    history = service.get_price_history(
        symbol=args.symbol,
        days=args.days
    )

    if history.record_count == 0:
        print(f"❌ No price history found for {args.symbol.upper()}")
        print(f"   Run 'capture' or 'import' first to populate data")
        return

    print(f"📊 {history.record_count} records from {history.start_date} to {history.end_date}")

    if history.price_change is not None:
        change_symbol = "📈" if history.price_change >= 0 else "📉"
        print(f"   {change_symbol} Change: ${history.price_change:+,.2f} ({history.price_change_pct:+.2f}%)")

    print(f"\n{'Date':<12} {'Price':>10} {'Change':>10} {'Volume':>15}")
    print("-" * 50)

    for snapshot in history.snapshots[-20:]:  # Show last 20
        change_str = ""
        if snapshot.day_change is not None:
            change_str = f"{snapshot.day_change:+.2f}"
        volume_str = f"{snapshot.volume:,}" if snapshot.volume else "-"

        print(f"{snapshot.snapshot_date.isoformat():<12} ${snapshot.price:>8.2f} {change_str:>10} {volume_str:>15}")

    if history.record_count > 20:
        print(f"\n... showing last 20 of {history.record_count} records")

    if args.output == "json":
        print(f"\n{json.dumps(history.model_dump(), indent=2, default=str)}")


def cmd_portfolio(args):
    """View portfolio value history."""
    service = PriceHistoryService()

    print(f"\n{'='*60}")
    print("💼 PORTFOLIO VALUE HISTORY")
    print(f"{'='*60}\n")

    history = service.get_portfolio_history(days=args.days)

    if history.record_count == 0:
        print("❌ No portfolio history found")
        print("   Run 'capture' first to start tracking portfolio value")
        return

    print(f"📊 {history.record_count} snapshots from {history.start_date} to {history.end_date}")

    if history.value_change is not None:
        change_symbol = "📈" if history.value_change >= 0 else "📉"
        print(f"   {change_symbol} Change: ${history.value_change:+,.2f} ({history.value_change_pct:+.2f}%)")

    print(f"\n{'Date':<12} {'Total':>14} {'Layer 1':>12} {'Layer 2':>12} {'Layer 3':>10}")
    print("-" * 65)

    for snapshot in history.snapshots[-20:]:  # Show last 20
        print(f"{snapshot.snapshot_date.isoformat():<12} "
              f"${snapshot.total_value:>12,.2f} "
              f"${snapshot.layer1_value:>10,.2f} "
              f"${snapshot.layer2_value:>10,.2f} "
              f"${snapshot.layer3_value:>8,.2f}")

    if history.record_count > 20:
        print(f"\n... showing last 20 of {history.record_count} records")

    if args.output == "json":
        print(f"\n{json.dumps(history.model_dump(), indent=2, default=str)}")


def cmd_export(args):
    """Export data for Google Sheets or other uses."""
    service = PriceHistoryService()

    print(f"\n{'='*60}")
    print(f"📤 EXPORTING DATA ({args.type})")
    print(f"{'='*60}\n")

    data = service.export_for_sheets(
        export_type=args.type,
        days=args.days
    )

    if args.format == "csv":
        for row in data:
            print(",".join(str(cell) for cell in row))
    else:  # json
        print(json.dumps(data, indent=2, default=str))

    print(f"\n✅ Exported {len(data) - 1} data rows")


def cmd_stats(args):
    """Show database statistics."""
    service = PriceHistoryService()

    print(f"\n{'='*60}")
    print("📊 PRICE HISTORY DATABASE STATS")
    print(f"{'='*60}\n")

    stats = service.get_stats()

    print(f"🗄️  Database: {stats['db_path']}")
    print(f"\n📈 Price Snapshots:")
    print(f"   Total records:   {stats['price_snapshots']:,}")
    print(f"   Unique symbols:  {stats['unique_symbols']}")

    if stats.get("date_range"):
        print(f"   Date range:      {stats['date_range']['start']} to {stats['date_range']['end']}")

    print(f"\n💼 Portfolio Snapshots: {stats['portfolio_snapshots']}")

    if stats.get("latest_portfolio"):
        lp = stats["latest_portfolio"]
        print(f"   Latest value:    ${lp['total_value']:,.2f} ({lp['date']})")

    if stats.get("latest_prices"):
        print(f"\n📊 Latest Prices ({len(stats['latest_prices'])} symbols):")
        for symbol, info in list(stats["latest_prices"].items())[:10]:
            print(f"   {symbol}: ${info['price']:.2f} ({info['date']})")
        if len(stats["latest_prices"]) > 10:
            print(f"   ... and {len(stats['latest_prices']) - 10} more")

    if args.output == "json":
        print(f"\n{json.dumps(stats, indent=2, default=str)}")


def cmd_cleanup(args):
    """Clean up old data."""
    from src.services.price_history_db import PriceHistoryDB
    db = PriceHistoryDB()

    print(f"\n{'='*60}")
    print(f"🧹 CLEANUP: Removing data older than {args.days} days")
    print(f"{'='*60}\n")

    deleted = db.delete_old_data(days_to_keep=args.days)
    print(f"✅ Deleted {deleted} old records")


def main():
    parser = argparse.ArgumentParser(
        description='Finance Guru™ Price History Tracking',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Capture today's prices for all holdings
  uv run python src/services/price_history_cli.py capture

  # Import 1 year of history for specific tickers
  uv run python src/services/price_history_cli.py import TSLA PLTR NVDA --days 365

  # View TSLA price history (last 30 days)
  uv run python src/services/price_history_cli.py history TSLA --days 30

  # View portfolio value over time
  uv run python src/services/price_history_cli.py portfolio --days 90

  # Export for Google Sheets (CSV format)
  uv run python src/services/price_history_cli.py export --type portfolio --format csv

  # Show database statistics
  uv run python src/services/price_history_cli.py stats
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # capture command
    capture_parser = subparsers.add_parser('capture', help='Capture daily price snapshot')
    capture_parser.add_argument('symbols', nargs='*', help='Symbols to capture (default: all holdings)')
    capture_parser.add_argument('--date', help='Snapshot date (YYYY-MM-DD, default: today)')
    capture_parser.add_argument('--output', choices=['text', 'json'], default='text')

    # import command
    import_parser = subparsers.add_parser('import', help='Import historical data from yfinance')
    import_parser.add_argument('symbols', nargs='+', help='Symbols to import')
    import_parser.add_argument('--days', type=int, default=365, help='Days of history (default: 365)')
    import_parser.add_argument('--output', choices=['text', 'json'], default='text')

    # history command
    history_parser = subparsers.add_parser('history', help='View price history for a symbol')
    history_parser.add_argument('symbol', help='Ticker symbol')
    history_parser.add_argument('--days', type=int, default=90, help='Days of history (default: 90)')
    history_parser.add_argument('--output', choices=['text', 'json'], default='text')

    # portfolio command
    portfolio_parser = subparsers.add_parser('portfolio', help='View portfolio value history')
    portfolio_parser.add_argument('--days', type=int, default=90, help='Days of history (default: 90)')
    portfolio_parser.add_argument('--output', choices=['text', 'json'], default='text')

    # export command
    export_parser = subparsers.add_parser('export', help='Export data for Google Sheets')
    export_parser.add_argument('--type', choices=['portfolio', 'prices'], default='portfolio', help='Export type')
    export_parser.add_argument('--format', choices=['csv', 'json'], default='csv', help='Output format')
    export_parser.add_argument('--days', type=int, default=90, help='Days of history (default: 90)')

    # stats command
    stats_parser = subparsers.add_parser('stats', help='Show database statistics')
    stats_parser.add_argument('--output', choices=['text', 'json'], default='text')

    # cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Remove old data')
    cleanup_parser.add_argument('--days', type=int, default=365, help='Days to keep (default: 365)')

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    commands = {
        'capture': cmd_capture,
        'import': cmd_import,
        'history': cmd_history,
        'portfolio': cmd_portfolio,
        'export': cmd_export,
        'stats': cmd_stats,
        'cleanup': cmd_cleanup,
    }

    commands[args.command](args)


if __name__ == '__main__':
    main()
