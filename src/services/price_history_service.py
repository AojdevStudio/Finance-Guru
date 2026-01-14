"""
Price History Service for Finance Guru™

WHAT: Business logic for capturing, storing, and retrieving price history
WHY: Centralizes price tracking operations for CLI, API, and Google Sheets sync
ARCHITECTURE: Service layer between CLI/API and database

Author: Finance Guru™ Development Team
Created: 2026-01-14
"""

from datetime import datetime, date, timedelta
from typing import Optional
from pathlib import Path

import yfinance as yf

from src.config import FinGuruConfig
from src.models.price_history import (
    PriceSnapshotInput,
    HoldingSnapshotInput,
    PortfolioValueSnapshotInput,
    PriceHistoryOutput,
    PortfolioHistoryOutput,
)
from src.services.price_history_db import PriceHistoryDB
from src.ui.services.portfolio_loader import PortfolioLoader


class PriceHistoryService:
    """
    Service for managing price and portfolio history.

    Provides operations for:
    - Capturing daily price snapshots for all holdings
    - Importing historical data from yfinance
    - Creating portfolio value snapshots
    - Exporting data for Google Sheets charting
    """

    def __init__(self, db: Optional[PriceHistoryDB] = None):
        """
        Initialize service with database connection.

        Args:
            db: PriceHistoryDB instance (creates default if None)
        """
        self.db = db or PriceHistoryDB()
        self._layer_map = None

    @property
    def layer_map(self) -> dict[str, str]:
        """Lazy-load layer mappings."""
        if self._layer_map is None:
            layers = FinGuruConfig.load_layers()
            self._layer_map = {}
            for layer, symbols in layers.items():
                for symbol in symbols:
                    self._layer_map[symbol.upper()] = layer
        return self._layer_map

    def capture_daily_snapshot(
        self,
        symbols: Optional[list[str]] = None,
        snapshot_date: Optional[date] = None
    ) -> dict:
        """
        Capture price snapshot for specified symbols (or all holdings).

        This is the primary method for daily price tracking. It:
        1. Fetches current prices from yfinance
        2. Stores individual price snapshots
        3. If portfolio CSV exists, also creates a portfolio value snapshot

        Args:
            symbols: List of symbols to capture (None = load from portfolio CSV)
            snapshot_date: Date to record (defaults to today)

        Returns:
            Dict with capture results and statistics
        """
        snapshot_date = snapshot_date or date.today()
        now = datetime.now()

        # Get symbols from portfolio if not specified
        if symbols is None:
            portfolio = PortfolioLoader.load_latest()
            if portfolio:
                symbols = [h.symbol for h in portfolio.holdings]
            else:
                # Fall back to all layer symbols
                symbols = list(self.layer_map.keys())

        if not symbols:
            return {
                "success": False,
                "error": "No symbols to capture",
                "captured": 0,
            }

        # Fetch prices from yfinance
        price_snapshots = []
        errors = []

        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info

                current_price = info.get('currentPrice') or info.get('regularMarketPrice', 0)
                if not current_price or current_price == 0:
                    errors.append(f"{symbol}: No price data")
                    continue

                snapshot = PriceSnapshotInput(
                    symbol=symbol.upper(),
                    price=round(current_price, 2),
                    open_price=info.get('regularMarketOpen'),
                    high_price=info.get('regularMarketDayHigh'),
                    low_price=info.get('regularMarketDayLow'),
                    previous_close=info.get('previousClose'),
                    volume=info.get('regularMarketVolume'),
                    snapshot_date=snapshot_date,
                    timestamp=now,
                    source="yfinance",
                )
                price_snapshots.append(snapshot)

            except Exception as e:
                errors.append(f"{symbol}: {str(e)}")

        # Save price snapshots
        if price_snapshots:
            self.db.save_price_snapshots_bulk(price_snapshots)

        # Create portfolio snapshot if we have portfolio data
        portfolio_result = None
        portfolio = PortfolioLoader.load_latest()
        if portfolio:
            portfolio_result = self._create_portfolio_snapshot(
                portfolio, price_snapshots, snapshot_date, now
            )

        return {
            "success": True,
            "snapshot_date": snapshot_date.isoformat(),
            "captured": len(price_snapshots),
            "errors": errors if errors else None,
            "symbols": [s.symbol for s in price_snapshots],
            "portfolio_snapshot": portfolio_result,
        }

    def _create_portfolio_snapshot(
        self,
        portfolio,
        price_snapshots: list[PriceSnapshotInput],
        snapshot_date: date,
        timestamp: datetime
    ) -> dict:
        """Create and save portfolio value snapshot."""
        # Create price lookup from snapshots
        price_lookup = {s.symbol: s.price for s in price_snapshots}

        # Build holding snapshots
        holdings = []
        total_value = 0.0

        for holding in portfolio.holdings:
            # Use captured price or fall back to portfolio's current value
            price = price_lookup.get(holding.symbol, holding.current_value / holding.quantity if holding.quantity > 0 else 0)
            value = price * holding.quantity

            holdings.append(HoldingSnapshotInput(
                symbol=holding.symbol,
                quantity=holding.quantity,
                price=round(price, 2),
                layer=holding.layer,
                snapshot_date=snapshot_date,
            ))
            total_value += value

        if not holdings:
            return {"error": "No holdings to snapshot"}

        portfolio_snapshot = PortfolioValueSnapshotInput(
            total_value=round(total_value, 2),
            holdings=holdings,
            snapshot_date=snapshot_date,
            timestamp=timestamp,
            cash_balance=None,  # Could parse from balances file
            margin_balance=None,
        )

        self.db.save_portfolio_snapshot(portfolio_snapshot)

        return {
            "total_value": portfolio_snapshot.total_value,
            "layer1_value": portfolio_snapshot.layer1_value,
            "layer2_value": portfolio_snapshot.layer2_value,
            "layer3_value": portfolio_snapshot.layer3_value,
            "holding_count": portfolio_snapshot.holding_count,
        }

    def import_historical_data(
        self,
        symbols: list[str],
        days: int = 365,
        end_date: Optional[date] = None
    ) -> dict:
        """
        Import historical price data from yfinance.

        Backfills price history for specified symbols. Useful for:
        - Initial setup with historical data
        - Filling gaps in daily captures

        Args:
            symbols: List of ticker symbols
            days: Number of days of history to import
            end_date: End date (defaults to today)

        Returns:
            Dict with import results
        """
        end_date = end_date or date.today()
        start_date = end_date - timedelta(days=days)

        total_imported = 0
        results = {}

        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(
                    start=start_date.isoformat(),
                    end=end_date.isoformat()
                )

                if hist.empty:
                    results[symbol] = {"error": "No historical data"}
                    continue

                snapshots = []
                for idx, row in hist.iterrows():
                    snapshot_dt = idx.to_pydatetime()
                    snapshots.append(PriceSnapshotInput(
                        symbol=symbol.upper(),
                        price=round(row['Close'], 2),
                        open_price=round(row['Open'], 2) if 'Open' in row else None,
                        high_price=round(row['High'], 2) if 'High' in row else None,
                        low_price=round(row['Low'], 2) if 'Low' in row else None,
                        previous_close=None,
                        volume=int(row['Volume']) if 'Volume' in row else None,
                        snapshot_date=snapshot_dt.date(),
                        timestamp=snapshot_dt,
                        source="yfinance",
                    ))

                self.db.save_price_snapshots_bulk(snapshots)
                total_imported += len(snapshots)
                results[symbol] = {"imported": len(snapshots)}

            except Exception as e:
                results[symbol] = {"error": str(e)}

        return {
            "success": True,
            "total_imported": total_imported,
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "results": results,
        }

    def get_price_history(
        self,
        symbol: str,
        days: int = 90,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> PriceHistoryOutput:
        """
        Retrieve price history for a symbol.

        Args:
            symbol: Ticker symbol
            days: Number of days (used if start_date not specified)
            start_date: Start date (overrides days)
            end_date: End date (defaults to today)

        Returns:
            PriceHistoryOutput with snapshots and statistics
        """
        end_date = end_date or date.today()
        start_date = start_date or (end_date - timedelta(days=days))

        snapshots = self.db.get_price_history(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date
        )

        if not snapshots:
            return PriceHistoryOutput(
                symbol=symbol.upper(),
                snapshots=[],
                start_date=start_date,
                end_date=end_date,
            )

        return PriceHistoryOutput(
            symbol=symbol.upper(),
            snapshots=snapshots,
            start_date=snapshots[0].snapshot_date,
            end_date=snapshots[-1].snapshot_date,
        )

    def get_portfolio_history(
        self,
        days: int = 90,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> PortfolioHistoryOutput:
        """
        Retrieve portfolio value history.

        Args:
            days: Number of days (used if start_date not specified)
            start_date: Start date (overrides days)
            end_date: End date (defaults to today)

        Returns:
            PortfolioHistoryOutput with snapshots and statistics
        """
        end_date = end_date or date.today()
        start_date = start_date or (end_date - timedelta(days=days))

        snapshots = self.db.get_portfolio_history(
            start_date=start_date,
            end_date=end_date
        )

        if not snapshots:
            return PortfolioHistoryOutput(
                snapshots=[],
                start_date=start_date,
                end_date=end_date,
            )

        return PortfolioHistoryOutput(
            snapshots=snapshots,
            start_date=snapshots[0].snapshot_date,
            end_date=snapshots[-1].snapshot_date,
        )

    def export_for_sheets(
        self,
        export_type: str = "portfolio",
        days: int = 90
    ) -> list[list]:
        """
        Export data formatted for Google Sheets.

        Returns data as 2D array ready for sheets update.

        Args:
            export_type: "portfolio" or "prices"
            days: Number of days of history

        Returns:
            2D list suitable for Google Sheets API
        """
        if export_type == "portfolio":
            return self._export_portfolio_for_sheets(days)
        else:
            return self._export_prices_for_sheets(days)

    def _export_portfolio_for_sheets(self, days: int) -> list[list]:
        """Export portfolio history for sheets."""
        history = self.get_portfolio_history(days=days)

        # Header row
        rows = [["Date", "Total Value", "Layer 1 (Growth)", "Layer 2 (Income)", "Layer 3 (Hedge)"]]

        # Data rows
        for snapshot in history.snapshots:
            rows.append([
                snapshot.snapshot_date.isoformat(),
                snapshot.total_value,
                snapshot.layer1_value,
                snapshot.layer2_value,
                snapshot.layer3_value,
            ])

        return rows

    def _export_prices_for_sheets(self, days: int) -> list[list]:
        """Export price history for all symbols for sheets."""
        symbols = self.db.get_all_symbols()

        if not symbols:
            return [["No price data available"]]

        # Get history for all symbols
        all_data = {}
        all_dates = set()

        for symbol in symbols:
            history = self.get_price_history(symbol=symbol, days=days)
            for snapshot in history.snapshots:
                all_dates.add(snapshot.snapshot_date)
                if snapshot.snapshot_date not in all_data:
                    all_data[snapshot.snapshot_date] = {}
                all_data[snapshot.snapshot_date][symbol] = snapshot.price

        # Sort dates
        sorted_dates = sorted(all_dates)

        # Header row
        rows = [["Date"] + symbols]

        # Data rows
        for d in sorted_dates:
            row = [d.isoformat()]
            for symbol in symbols:
                row.append(all_data[d].get(symbol, ""))
            rows.append(row)

        return rows

    def get_stats(self) -> dict:
        """Get service statistics including database info."""
        db_stats = self.db.get_stats()

        # Add latest prices info
        latest = self.db.get_latest_prices()
        db_stats["latest_prices"] = {
            symbol: {"price": snap.price, "date": snap.snapshot_date.isoformat()}
            for symbol, snap in latest.items()
        }

        # Add latest portfolio value
        latest_portfolio = self.db.get_latest_portfolio_snapshot()
        if latest_portfolio:
            db_stats["latest_portfolio"] = {
                "total_value": latest_portfolio.total_value,
                "date": latest_portfolio.snapshot_date.isoformat(),
            }

        return db_stats
