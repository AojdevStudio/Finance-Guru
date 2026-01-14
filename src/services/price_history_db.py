"""
Price History Database Service for Finance Guru™

WHAT: SQLite database for persistent storage of price and portfolio history
WHY: Enables historical charting and performance tracking without API calls
ARCHITECTURE: Data persistence layer for price history feature

Author: Finance Guru™ Development Team
Created: 2026-01-14
"""

import sqlite3
from pathlib import Path
from datetime import datetime, date
from typing import Optional
from contextlib import contextmanager

from src.config import FinGuruConfig
from src.models.price_history import (
    PriceSnapshotInput,
    HoldingSnapshotInput,
    PortfolioValueSnapshotInput,
)


class PriceHistoryDB:
    """
    SQLite database manager for price history storage.

    Provides CRUD operations for:
    - Individual ticker price snapshots
    - Portfolio value snapshots with holdings breakdown

    Database location: ~/.config/finance-guru/price_history.db
    """

    DEFAULT_DB_PATH = FinGuruConfig.CONFIG_DIR / "price_history.db"

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file (defaults to ~/.config/finance-guru/price_history.db)
        """
        self.db_path = db_path or self.DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def _get_connection(self):
        """Get database connection with automatic cleanup."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_schema(self):
        """Initialize database schema if not exists."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Price snapshots table - individual ticker prices
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS price_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    price REAL NOT NULL,
                    open_price REAL,
                    high_price REAL,
                    low_price REAL,
                    previous_close REAL,
                    volume INTEGER,
                    snapshot_date TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    source TEXT DEFAULT 'yfinance',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol, snapshot_date)
                )
            """)

            # Portfolio snapshots table - aggregate portfolio values
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS portfolio_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    total_value REAL NOT NULL,
                    layer1_value REAL DEFAULT 0,
                    layer2_value REAL DEFAULT 0,
                    layer3_value REAL DEFAULT 0,
                    cash_balance REAL,
                    margin_balance REAL,
                    holding_count INTEGER,
                    snapshot_date TEXT NOT NULL UNIQUE,
                    timestamp TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Holding snapshots table - individual holdings within portfolio snapshot
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS holding_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    portfolio_snapshot_id INTEGER NOT NULL,
                    symbol TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    price REAL NOT NULL,
                    value REAL NOT NULL,
                    layer TEXT DEFAULT 'unknown',
                    snapshot_date TEXT NOT NULL,
                    FOREIGN KEY (portfolio_snapshot_id) REFERENCES portfolio_snapshots(id),
                    UNIQUE(portfolio_snapshot_id, symbol)
                )
            """)

            # Create indexes for performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_price_snapshots_symbol_date
                ON price_snapshots(symbol, snapshot_date)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_price_snapshots_date
                ON price_snapshots(snapshot_date)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_portfolio_snapshots_date
                ON portfolio_snapshots(snapshot_date)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_holding_snapshots_portfolio
                ON holding_snapshots(portfolio_snapshot_id)
            """)

            conn.commit()

    # ============ Price Snapshot Operations ============

    def save_price_snapshot(self, snapshot: PriceSnapshotInput) -> int:
        """
        Save a price snapshot, replacing if date already exists.

        Args:
            snapshot: PriceSnapshotInput model

        Returns:
            Row ID of inserted/updated record
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO price_snapshots
                (symbol, price, open_price, high_price, low_price, previous_close,
                 volume, snapshot_date, timestamp, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                snapshot.symbol.upper(),
                snapshot.price,
                snapshot.open_price,
                snapshot.high_price,
                snapshot.low_price,
                snapshot.previous_close,
                snapshot.volume,
                snapshot.snapshot_date.isoformat(),
                snapshot.timestamp.isoformat(),
                snapshot.source,
            ))

            conn.commit()
            return cursor.lastrowid

    def save_price_snapshots_bulk(self, snapshots: list[PriceSnapshotInput]) -> int:
        """
        Bulk save multiple price snapshots.

        Args:
            snapshots: List of PriceSnapshotInput models

        Returns:
            Number of records inserted/updated
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.executemany("""
                INSERT OR REPLACE INTO price_snapshots
                (symbol, price, open_price, high_price, low_price, previous_close,
                 volume, snapshot_date, timestamp, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                (
                    s.symbol.upper(),
                    s.price,
                    s.open_price,
                    s.high_price,
                    s.low_price,
                    s.previous_close,
                    s.volume,
                    s.snapshot_date.isoformat(),
                    s.timestamp.isoformat(),
                    s.source,
                )
                for s in snapshots
            ])

            conn.commit()
            return cursor.rowcount

    def get_price_history(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 365
    ) -> list[PriceSnapshotInput]:
        """
        Retrieve price history for a symbol.

        Args:
            symbol: Ticker symbol
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)
            limit: Maximum records to return

        Returns:
            List of PriceSnapshotInput models ordered by date ascending
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM price_snapshots WHERE symbol = ?"
            params = [symbol.upper()]

            if start_date:
                query += " AND snapshot_date >= ?"
                params.append(start_date.isoformat())

            if end_date:
                query += " AND snapshot_date <= ?"
                params.append(end_date.isoformat())

            query += " ORDER BY snapshot_date ASC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [self._row_to_price_snapshot(row) for row in rows]

    def get_all_symbols(self) -> list[str]:
        """Get list of all symbols with price history."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT symbol FROM price_snapshots ORDER BY symbol")
            return [row[0] for row in cursor.fetchall()]

    def get_latest_prices(self, symbols: Optional[list[str]] = None) -> dict[str, PriceSnapshotInput]:
        """
        Get most recent price snapshot for each symbol.

        Args:
            symbols: List of symbols to query (None = all)

        Returns:
            Dict mapping symbol to latest PriceSnapshotInput
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            if symbols:
                placeholders = ",".join("?" * len(symbols))
                query = f"""
                    SELECT * FROM price_snapshots p1
                    WHERE p1.symbol IN ({placeholders})
                    AND p1.snapshot_date = (
                        SELECT MAX(p2.snapshot_date)
                        FROM price_snapshots p2
                        WHERE p2.symbol = p1.symbol
                    )
                """
                cursor.execute(query, [s.upper() for s in symbols])
            else:
                cursor.execute("""
                    SELECT * FROM price_snapshots p1
                    WHERE p1.snapshot_date = (
                        SELECT MAX(p2.snapshot_date)
                        FROM price_snapshots p2
                        WHERE p2.symbol = p1.symbol
                    )
                """)

            rows = cursor.fetchall()
            return {row["symbol"]: self._row_to_price_snapshot(row) for row in rows}

    def _row_to_price_snapshot(self, row: sqlite3.Row) -> PriceSnapshotInput:
        """Convert database row to PriceSnapshotInput model."""
        return PriceSnapshotInput(
            symbol=row["symbol"],
            price=row["price"],
            open_price=row["open_price"],
            high_price=row["high_price"],
            low_price=row["low_price"],
            previous_close=row["previous_close"],
            volume=row["volume"],
            snapshot_date=date.fromisoformat(row["snapshot_date"]),
            timestamp=datetime.fromisoformat(row["timestamp"]),
            source=row["source"],
        )

    # ============ Portfolio Snapshot Operations ============

    def save_portfolio_snapshot(self, snapshot: PortfolioValueSnapshotInput) -> int:
        """
        Save a portfolio snapshot with all holdings.

        Args:
            snapshot: PortfolioValueSnapshotInput model

        Returns:
            Row ID of inserted portfolio record
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Insert or replace portfolio snapshot
            cursor.execute("""
                INSERT OR REPLACE INTO portfolio_snapshots
                (total_value, layer1_value, layer2_value, layer3_value,
                 cash_balance, margin_balance, holding_count, snapshot_date, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                snapshot.total_value,
                snapshot.layer1_value,
                snapshot.layer2_value,
                snapshot.layer3_value,
                snapshot.cash_balance,
                snapshot.margin_balance,
                snapshot.holding_count,
                snapshot.snapshot_date.isoformat(),
                snapshot.timestamp.isoformat(),
            ))

            portfolio_id = cursor.lastrowid

            # Delete existing holdings for this snapshot date (in case of replace)
            cursor.execute("""
                DELETE FROM holding_snapshots
                WHERE snapshot_date = ?
            """, (snapshot.snapshot_date.isoformat(),))

            # Insert holdings
            for holding in snapshot.holdings:
                cursor.execute("""
                    INSERT INTO holding_snapshots
                    (portfolio_snapshot_id, symbol, quantity, price, value, layer, snapshot_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    portfolio_id,
                    holding.symbol,
                    holding.quantity,
                    holding.price,
                    holding.value,
                    holding.layer,
                    holding.snapshot_date.isoformat(),
                ))

            conn.commit()
            return portfolio_id

    def get_portfolio_history(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 365
    ) -> list[PortfolioValueSnapshotInput]:
        """
        Retrieve portfolio value history.

        Args:
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)
            limit: Maximum records to return

        Returns:
            List of PortfolioValueSnapshotInput models ordered by date ascending
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Query portfolio snapshots
            query = "SELECT * FROM portfolio_snapshots WHERE 1=1"
            params = []

            if start_date:
                query += " AND snapshot_date >= ?"
                params.append(start_date.isoformat())

            if end_date:
                query += " AND snapshot_date <= ?"
                params.append(end_date.isoformat())

            query += " ORDER BY snapshot_date ASC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            portfolio_rows = cursor.fetchall()

            results = []
            for p_row in portfolio_rows:
                # Get holdings for this portfolio snapshot
                cursor.execute("""
                    SELECT * FROM holding_snapshots
                    WHERE portfolio_snapshot_id = ?
                """, (p_row["id"],))
                holding_rows = cursor.fetchall()

                holdings = [
                    HoldingSnapshotInput(
                        symbol=h["symbol"],
                        quantity=h["quantity"],
                        price=h["price"],
                        layer=h["layer"],
                        snapshot_date=date.fromisoformat(h["snapshot_date"]),
                    )
                    for h in holding_rows
                ]

                results.append(PortfolioValueSnapshotInput(
                    total_value=p_row["total_value"],
                    holdings=holdings if holdings else [
                        # Placeholder if no holdings (shouldn't happen)
                        HoldingSnapshotInput(
                            symbol="UNKNOWN",
                            quantity=0,
                            price=0,
                            layer="unknown",
                            snapshot_date=date.fromisoformat(p_row["snapshot_date"]),
                        )
                    ],
                    snapshot_date=date.fromisoformat(p_row["snapshot_date"]),
                    timestamp=datetime.fromisoformat(p_row["timestamp"]),
                    cash_balance=p_row["cash_balance"],
                    margin_balance=p_row["margin_balance"],
                ))

            return results

    def get_latest_portfolio_snapshot(self) -> Optional[PortfolioValueSnapshotInput]:
        """Get the most recent portfolio snapshot."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM portfolio_snapshots
                ORDER BY snapshot_date DESC LIMIT 1
            """)
            p_row = cursor.fetchone()

            if not p_row:
                return None

            cursor.execute("""
                SELECT * FROM holding_snapshots
                WHERE portfolio_snapshot_id = ?
            """, (p_row["id"],))
            holding_rows = cursor.fetchall()

            holdings = [
                HoldingSnapshotInput(
                    symbol=h["symbol"],
                    quantity=h["quantity"],
                    price=h["price"],
                    layer=h["layer"],
                    snapshot_date=date.fromisoformat(h["snapshot_date"]),
                )
                for h in holding_rows
            ]

            return PortfolioValueSnapshotInput(
                total_value=p_row["total_value"],
                holdings=holdings if holdings else [
                    HoldingSnapshotInput(
                        symbol="UNKNOWN",
                        quantity=0,
                        price=0,
                        layer="unknown",
                        snapshot_date=date.fromisoformat(p_row["snapshot_date"]),
                    )
                ],
                snapshot_date=date.fromisoformat(p_row["snapshot_date"]),
                timestamp=datetime.fromisoformat(p_row["timestamp"]),
                cash_balance=p_row["cash_balance"],
                margin_balance=p_row["margin_balance"],
            )

    # ============ Utility Operations ============

    def get_stats(self) -> dict:
        """Get database statistics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM price_snapshots")
            price_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(DISTINCT symbol) FROM price_snapshots")
            symbol_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM portfolio_snapshots")
            portfolio_count = cursor.fetchone()[0]

            cursor.execute("SELECT MIN(snapshot_date), MAX(snapshot_date) FROM price_snapshots")
            date_range = cursor.fetchone()

            return {
                "price_snapshots": price_count,
                "unique_symbols": symbol_count,
                "portfolio_snapshots": portfolio_count,
                "date_range": {
                    "start": date_range[0],
                    "end": date_range[1],
                } if date_range[0] else None,
                "db_path": str(self.db_path),
            }

    def delete_old_data(self, days_to_keep: int = 365) -> int:
        """
        Delete price history older than specified days.

        Args:
            days_to_keep: Number of days of history to retain

        Returns:
            Number of records deleted
        """
        from datetime import timedelta
        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).date()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Delete old price snapshots
            cursor.execute("""
                DELETE FROM price_snapshots
                WHERE snapshot_date < ?
            """, (cutoff_date.isoformat(),))
            price_deleted = cursor.rowcount

            # Delete old holding snapshots first (foreign key)
            cursor.execute("""
                DELETE FROM holding_snapshots
                WHERE snapshot_date < ?
            """, (cutoff_date.isoformat(),))

            # Delete old portfolio snapshots
            cursor.execute("""
                DELETE FROM portfolio_snapshots
                WHERE snapshot_date < ?
            """, (cutoff_date.isoformat(),))
            portfolio_deleted = cursor.rowcount

            conn.commit()
            return price_deleted + portfolio_deleted
