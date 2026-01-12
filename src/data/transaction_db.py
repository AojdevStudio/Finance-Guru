"""
SQLite Database Module for Fidelity Transaction Persistence

Provides persistent storage for classified transactions with:
    - Deduplication via unique transaction IDs
    - Import history tracking
    - Category override management
    - Query and export capabilities

SCHEMA:
    transactions - All classified transactions
    category_overrides - User-defined category mappings
    imports - Import history and metadata

Author: Finance Guru™ Development Team
Created: 2026-01-12
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path
from typing import Generator, Optional

from src.models.transaction_inputs import (
    ClassifiedTransaction,
    TransactionBatch,
    TransactionType,
    ExpenseCategory,
)


class TransactionDatabase:
    """
    SQLite database for transaction storage and retrieval.

    WHAT: Persistent storage for classified brokerage transactions
    WHY: Track spending over time, prevent duplicate imports
    """

    # Default database location
    DEFAULT_DB_PATH = Path("data/transactions.db")

    # Schema version for migrations
    SCHEMA_VERSION = 1

    def __init__(self, db_path: Optional[Path | str] = None):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file (creates if not exists)
        """
        self.db_path = Path(db_path) if db_path else self.DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def _connection(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Context manager for database connections.

        Yields:
            SQLite connection with row factory configured
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_schema(self) -> None:
        """Initialize database schema if not exists."""
        with self._connection() as conn:
            cursor = conn.cursor()

            # Transactions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id TEXT PRIMARY KEY,
                    date DATE NOT NULL,
                    original_action TEXT NOT NULL,
                    original_description TEXT NOT NULL,
                    transaction_type TEXT NOT NULL,
                    category TEXT,
                    merchant TEXT,
                    amount TEXT NOT NULL,
                    is_margin BOOLEAN NOT NULL,
                    symbol TEXT,
                    raw_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Category overrides table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS category_overrides (
                    merchant_pattern TEXT PRIMARY KEY,
                    category TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Imports table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS imports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    transaction_count INTEGER NOT NULL,
                    new_count INTEGER NOT NULL,
                    duplicate_count INTEGER NOT NULL,
                    date_range_start DATE,
                    date_range_end DATE
                )
            """)

            # Schema version tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY
                )
            """)

            # Set initial schema version
            cursor.execute(
                "INSERT OR IGNORE INTO schema_version (version) VALUES (?)",
                (self.SCHEMA_VERSION,)
            )

            # Indexes for common queries
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_transactions_merchant ON transactions(merchant)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(transaction_type)"
            )

    def insert_batch(self, batch: TransactionBatch) -> tuple[int, int]:
        """
        Insert a batch of transactions, skipping duplicates.

        Args:
            batch: TransactionBatch to insert

        Returns:
            Tuple of (new_count, duplicate_count)
        """
        new_count = 0
        duplicate_count = 0

        with self._connection() as conn:
            cursor = conn.cursor()

            for tx in batch.transactions:
                # Check if exists
                cursor.execute(
                    "SELECT id FROM transactions WHERE id = ?",
                    (tx.id,)
                )
                if cursor.fetchone():
                    duplicate_count += 1
                    continue

                # Insert new transaction
                cursor.execute("""
                    INSERT INTO transactions (
                        id, date, original_action, original_description,
                        transaction_type, category, merchant, amount,
                        is_margin, symbol, raw_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    tx.id,
                    tx.date.isoformat(),
                    tx.original_action,
                    tx.original_description,
                    tx.transaction_type.value,
                    tx.category.value if tx.category else None,
                    tx.merchant,
                    str(tx.amount),
                    tx.is_margin,
                    tx.symbol,
                    json.dumps(tx.raw_data),
                ))
                new_count += 1

            # Record import
            cursor.execute("""
                INSERT INTO imports (
                    filename, transaction_count, new_count, duplicate_count,
                    date_range_start, date_range_end
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                batch.source_file or "unknown",
                len(batch.transactions),
                new_count,
                duplicate_count,
                batch.date_range_start.isoformat() if batch.date_range_start else None,
                batch.date_range_end.isoformat() if batch.date_range_end else None,
            ))

        return new_count, duplicate_count

    def get_transactions(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        tx_type: Optional[TransactionType] = None,
        category: Optional[ExpenseCategory] = None,
        merchant: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> list[ClassifiedTransaction]:
        """
        Query transactions with optional filters.

        Args:
            start_date: Filter by minimum date
            end_date: Filter by maximum date
            tx_type: Filter by transaction type
            category: Filter by expense category
            merchant: Filter by merchant name (partial match)
            limit: Maximum number of results

        Returns:
            List of matching ClassifiedTransaction objects
        """
        query = "SELECT * FROM transactions WHERE 1=1"
        params = []

        if start_date:
            query += " AND date >= ?"
            params.append(start_date.isoformat())

        if end_date:
            query += " AND date <= ?"
            params.append(end_date.isoformat())

        if tx_type:
            query += " AND transaction_type = ?"
            params.append(tx_type.value)

        if category:
            query += " AND category = ?"
            params.append(category.value)

        if merchant:
            query += " AND merchant LIKE ?"
            params.append(f"%{merchant}%")

        query += " ORDER BY date DESC"

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

        return [self._row_to_transaction(row) for row in rows]

    def get_transactions_by_month(self, month: str) -> list[ClassifiedTransaction]:
        """
        Get all transactions for a specific month.

        Args:
            month: Month in YYYY-MM format

        Returns:
            List of transactions in that month
        """
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM transactions WHERE strftime('%Y-%m', date) = ? ORDER BY date",
                (month,)
            )
            rows = cursor.fetchall()

        return [self._row_to_transaction(row) for row in rows]

    def get_unique_merchants(self) -> list[tuple[str, int]]:
        """
        Get list of unique merchants with transaction counts.

        Returns:
            List of (merchant, count) tuples sorted by count descending
        """
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT merchant, COUNT(*) as count
                FROM transactions
                WHERE merchant IS NOT NULL
                GROUP BY merchant
                ORDER BY count DESC
            """)
            return [(row["merchant"], row["count"]) for row in cursor.fetchall()]

    def get_expense_categories(self) -> list[tuple[str, Decimal]]:
        """
        Get expense totals by category.

        Returns:
            List of (category, total) tuples sorted by total descending
        """
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT category, SUM(CAST(amount AS REAL)) as total
                FROM transactions
                WHERE transaction_type = 'expense' AND category IS NOT NULL
                GROUP BY category
                ORDER BY total ASC
            """)
            return [
                (row["category"], Decimal(str(row["total"])))
                for row in cursor.fetchall()
            ]

    def set_category_override(
        self,
        merchant_pattern: str,
        category: ExpenseCategory,
    ) -> None:
        """
        Set a category override for a merchant pattern.

        Args:
            merchant_pattern: Merchant name or pattern to match
            category: Category to assign
        """
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO category_overrides (merchant_pattern, category)
                VALUES (?, ?)
            """, (merchant_pattern, category.value))

    def get_category_overrides(self) -> dict[str, ExpenseCategory]:
        """
        Get all category overrides.

        Returns:
            Dict mapping merchant patterns to categories
        """
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT merchant_pattern, category FROM category_overrides")
            return {
                row["merchant_pattern"]: ExpenseCategory(row["category"])
                for row in cursor.fetchall()
            }

    def apply_category_overrides(self) -> int:
        """
        Apply all category overrides to existing transactions.

        Returns:
            Number of transactions updated
        """
        overrides = self.get_category_overrides()
        updated = 0

        with self._connection() as conn:
            cursor = conn.cursor()

            for pattern, category in overrides.items():
                cursor.execute("""
                    UPDATE transactions
                    SET category = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE merchant LIKE ? AND category != ?
                """, (category.value, f"%{pattern}%", category.value))
                updated += cursor.rowcount

        return updated

    def get_import_history(self, limit: int = 10) -> list[dict]:
        """
        Get recent import history.

        Args:
            limit: Maximum number of imports to return

        Returns:
            List of import records
        """
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM imports ORDER BY imported_at DESC LIMIT ?",
                (limit,)
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_stats(self) -> dict:
        """
        Get database statistics.

        Returns:
            Dict with transaction counts, date range, etc.
        """
        with self._connection() as conn:
            cursor = conn.cursor()

            # Total transactions
            cursor.execute("SELECT COUNT(*) FROM transactions")
            total = cursor.fetchone()[0]

            # Date range
            cursor.execute("SELECT MIN(date), MAX(date) FROM transactions")
            row = cursor.fetchone()
            date_range = (row[0], row[1]) if row[0] else (None, None)

            # Counts by type
            cursor.execute("""
                SELECT transaction_type, COUNT(*) as count
                FROM transactions GROUP BY transaction_type
            """)
            by_type = {row["transaction_type"]: row["count"] for row in cursor.fetchall()}

            # Total imports
            cursor.execute("SELECT COUNT(*) FROM imports")
            import_count = cursor.fetchone()[0]

        return {
            "total_transactions": total,
            "date_range_start": date_range[0],
            "date_range_end": date_range[1],
            "by_type": by_type,
            "import_count": import_count,
        }

    def _row_to_transaction(self, row: sqlite3.Row) -> ClassifiedTransaction:
        """
        Convert database row to ClassifiedTransaction.

        Args:
            row: SQLite row

        Returns:
            ClassifiedTransaction object
        """
        return ClassifiedTransaction(
            id=row["id"],
            date=date.fromisoformat(row["date"]),
            original_action=row["original_action"],
            original_description=row["original_description"],
            transaction_type=TransactionType(row["transaction_type"]),
            category=ExpenseCategory(row["category"]) if row["category"] else None,
            merchant=row["merchant"],
            amount=Decimal(row["amount"]),
            is_margin=bool(row["is_margin"]),
            symbol=row["symbol"],
            raw_data=json.loads(row["raw_data"]),
        )

    def export_csv(
        self,
        output_path: Path | str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        include_raw: bool = False,
    ) -> int:
        """
        Export transactions to CSV file.

        Args:
            output_path: Path for output CSV
            start_date: Filter by minimum date
            end_date: Filter by maximum date
            include_raw: Include raw_data column

        Returns:
            Number of transactions exported
        """
        transactions = self.get_transactions(
            start_date=start_date,
            end_date=end_date,
        )

        import csv
        with open(output_path, "w", newline="") as f:
            fieldnames = [
                "Date", "Description", "Category", "Amount",
                "Type", "Merchant", "Is Margin", "Original Action"
            ]
            if include_raw:
                fieldnames.append("Raw Data")

            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for tx in transactions:
                row = {
                    "Date": tx.date.isoformat(),
                    "Description": tx.original_description,
                    "Category": tx.category.value if tx.category else "",
                    "Amount": str(tx.amount),
                    "Type": tx.transaction_type.value,
                    "Merchant": tx.merchant or "",
                    "Is Margin": tx.is_margin,
                    "Original Action": tx.original_action,
                }
                if include_raw:
                    row["Raw Data"] = json.dumps(tx.raw_data)
                writer.writerow(row)

        return len(transactions)

    def export_json(
        self,
        output_path: Path | str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> int:
        """
        Export transactions to JSON file.

        Args:
            output_path: Path for output JSON
            start_date: Filter by minimum date
            end_date: Filter by maximum date

        Returns:
            Number of transactions exported
        """
        transactions = self.get_transactions(
            start_date=start_date,
            end_date=end_date,
        )

        data = {
            "transactions": [
                {
                    "id": tx.id,
                    "date": tx.date.isoformat(),
                    "description": tx.original_description,
                    "category": tx.category.value if tx.category else None,
                    "amount": float(tx.amount),
                    "type": tx.transaction_type.value,
                    "merchant": tx.merchant,
                    "is_margin": tx.is_margin,
                    "original_action": tx.original_action,
                }
                for tx in transactions
            ],
            "exported_at": datetime.now().isoformat(),
            "count": len(transactions),
        }

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

        return len(transactions)


# Export all
__all__ = ["TransactionDatabase"]
