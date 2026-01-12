"""
Fidelity Transaction CSV Parser

Layer 2 of the 3-layer architecture - Business logic for parsing
and classifying Fidelity brokerage transaction CSV exports.

ARCHITECTURE NOTE:
    Layer 1: Pydantic Models (transaction_inputs.py) - Data validation
    Layer 2: Parser/Classifier Classes (THIS FILE) - Business logic
    Layer 3: CLI Interface (fidelity_parser_cli.py) - User integration

USAGE:
    parser = FidelityTransactionParser()
    batch = parser.parse_csv("/path/to/transactions.csv")

    for tx in batch.transactions:
        print(f"{tx.date}: {tx.merchant} - ${tx.amount}")

Author: Finance Guru™ Development Team
Created: 2026-01-12
"""

from __future__ import annotations

import math
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Optional

import pandas as pd

from src.models.transaction_inputs import (
    RawFidelityTransaction,
    ClassifiedTransaction,
    TransactionBatch,
    TransactionType,
    ExpenseCategory,
    ParserConfig,
)
from src.data.constants import (
    FIDELITY_CSV_COLUMNS,
    get_transaction_type,
    extract_merchant,
    categorize_expense,
)


class FidelityTransactionParser:
    """
    Parser for Fidelity brokerage transaction CSV exports.

    Handles the full pipeline:
        1. Load CSV with proper handling of Fidelity format
        2. Parse rows into RawFidelityTransaction models
        3. Classify transactions into budget categories
        4. Extract merchant names from descriptions
        5. Generate unique IDs for deduplication

    WHAT: Converts raw Fidelity CSV data into classified, budget-ready transactions
    WHY: Traditional budgeting apps can't parse brokerage transaction data
    """

    def __init__(self, config: Optional[ParserConfig] = None):
        """
        Initialize parser with optional configuration.

        Args:
            config: Parser configuration (uses defaults if not provided)
        """
        self.config = config or ParserConfig()

    def parse_csv(self, file_path: str | Path) -> TransactionBatch:
        """
        Parse a Fidelity transaction history CSV file.

        Args:
            file_path: Path to the CSV file

        Returns:
            TransactionBatch containing classified transactions

        Raises:
            FileNotFoundError: If CSV file doesn't exist
            ValueError: If CSV format is invalid
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {path}")

        # Load CSV, skipping Fidelity header rows
        try:
            df = pd.read_csv(
                path,
                skiprows=self.config.skip_rows,
                encoding="utf-8",
            )
        except Exception as e:
            raise ValueError(f"Failed to read CSV: {e}")

        # Validate required columns
        self._validate_columns(df)

        # Parse each row
        transactions = []
        for idx, row in df.iterrows():
            try:
                # Skip empty rows
                if pd.isna(row.get("Run Date")) or pd.isna(row.get("Action")):
                    continue

                # Skip Fidelity footer/summary rows
                action = str(row.get("Action", "")).strip()
                if not action or action.lower() in ("", "total", "pending"):
                    continue

                # Parse raw transaction
                raw = self._parse_row(row)
                if raw is None:
                    continue

                # Classify transaction
                classified = self._classify_transaction(raw, row.to_dict())
                transactions.append(classified)

            except Exception as e:
                # Log error but continue processing
                print(f"Warning: Skipping row {idx}: {e}")
                continue

        return TransactionBatch(
            transactions=transactions,
            source_file=str(path.name),
        )

    def _validate_columns(self, df: pd.DataFrame) -> None:
        """
        Validate that required columns exist in the CSV.

        Args:
            df: Pandas DataFrame from CSV

        Raises:
            ValueError: If required columns are missing
        """
        required = ["Run Date", "Action", "Description", "Amount ($)"]
        missing = [col for col in required if col not in df.columns]

        if missing:
            # Try alternative column names
            alternatives = {
                "Run Date": ["Date", "Transaction Date"],
                "Amount ($)": ["Amount", "Amount($)"],
            }
            for col in missing[:]:
                for alt in alternatives.get(col, []):
                    if alt in df.columns:
                        df.rename(columns={alt: col}, inplace=True)
                        missing.remove(col)
                        break

        if missing:
            raise ValueError(
                f"Missing required columns: {missing}. "
                f"Available columns: {list(df.columns)}"
            )

    def _parse_row(self, row: pd.Series) -> Optional[RawFidelityTransaction]:
        """
        Parse a single CSV row into RawFidelityTransaction.

        Args:
            row: Pandas Series representing a CSV row

        Returns:
            RawFidelityTransaction or None if row should be skipped
        """
        # Parse date
        run_date = self._parse_date(row.get("Run Date"))
        if run_date is None:
            return None

        # Parse amount
        amount = self._parse_currency(row.get("Amount ($)"))
        if amount is None:
            return None

        # Build transaction
        try:
            return RawFidelityTransaction(
                run_date=run_date,
                action=str(row.get("Action", "")).strip(),
                symbol=self._clean_string(row.get("Symbol")),
                description=str(row.get("Description", "")).strip(),
                type=str(row.get("Type", "")).strip(),
                quantity=self._parse_decimal(row.get("Quantity")),
                price=self._parse_currency(row.get("Price ($)")),
                commission=self._parse_currency(row.get("Commission ($)")) or Decimal("0"),
                fees=self._parse_currency(row.get("Fees ($)")) or Decimal("0"),
                accrued_interest=self._parse_currency(row.get("Accrued Interest ($)")) or Decimal("0"),
                amount=amount,
                cash_balance=self._parse_currency(row.get("Cash Balance ($)")),
                settlement_date=self._parse_date(row.get("Settlement Date")),
            )
        except Exception as e:
            print(f"Warning: Failed to parse transaction: {e}")
            return None

    def _classify_transaction(
        self,
        raw: RawFidelityTransaction,
        raw_dict: dict,
    ) -> ClassifiedTransaction:
        """
        Classify a raw transaction into budget categories.

        Args:
            raw: Parsed raw transaction
            raw_dict: Original row data for preservation

        Returns:
            ClassifiedTransaction with type, category, and merchant
        """
        # Determine transaction type
        tx_type = get_transaction_type(raw.action)

        # Extract merchant and categorize (only for expenses)
        merchant = None
        category = None

        if tx_type == TransactionType.EXPENSE:
            merchant = extract_merchant(raw.description)
            category = categorize_expense(raw.description, merchant)
        elif tx_type == TransactionType.INCOME:
            # Extract source for income
            merchant = extract_merchant(raw.description)

        # Generate unique ID
        tx_id = ClassifiedTransaction.generate_id(
            raw.run_date,
            raw.action,
            raw.description,
            raw.amount,
        )

        # Determine if margin transaction
        is_margin = raw.type.upper() == "MARGIN"

        return ClassifiedTransaction(
            id=tx_id,
            date=raw.run_date,
            original_action=raw.action,
            original_description=raw.description,
            transaction_type=tx_type,
            category=category,
            merchant=merchant,
            amount=raw.amount,
            is_margin=is_margin,
            symbol=raw.symbol,
            raw_data=self._clean_raw_data(raw_dict),
        )

    def _parse_date(self, value) -> Optional[date]:
        """
        Parse date from various formats.

        Handles:
            - MM/DD/YYYY (Fidelity standard)
            - YYYY-MM-DD (ISO)
            - datetime objects

        Args:
            value: Date value from CSV

        Returns:
            date object or None if unparseable
        """
        if pd.isna(value):
            return None

        if isinstance(value, date):
            return value

        if isinstance(value, datetime):
            return value.date()

        try:
            # Try Fidelity format first
            return datetime.strptime(str(value).strip(), self.config.date_format).date()
        except ValueError:
            pass

        try:
            # Try ISO format
            return datetime.strptime(str(value).strip(), "%Y-%m-%d").date()
        except ValueError:
            pass

        try:
            # Try pandas parsing
            return pd.to_datetime(value).date()
        except Exception:
            return None

    def _parse_currency(self, value) -> Optional[Decimal]:
        """
        Parse currency string to Decimal.

        Handles:
            - "$1,234.56" or "-$1,234.56"
            - "1234.56" or "-1234.56"
            - Already numeric values

        Args:
            value: Currency value from CSV

        Returns:
            Decimal or None if unparseable
        """
        if pd.isna(value):
            return None

        if isinstance(value, (int, float)):
            if math.isnan(value):
                return None
            return Decimal(str(value))

        try:
            # Clean currency string
            cleaned = str(value).strip()
            cleaned = cleaned.replace("$", "").replace(",", "").replace("+", "")

            # Handle special values
            if not cleaned or cleaned == "-" or cleaned.upper() in ("ERROR", "N/A", "NAN", "--"):
                return None

            return Decimal(cleaned)
        except (InvalidOperation, ValueError):
            return None

    def _parse_decimal(self, value) -> Optional[Decimal]:
        """
        Parse numeric string to Decimal.

        Args:
            value: Numeric value from CSV

        Returns:
            Decimal or None if unparseable
        """
        if pd.isna(value):
            return None

        if isinstance(value, (int, float)):
            if math.isnan(value):
                return None
            return Decimal(str(value))

        try:
            cleaned = str(value).strip().replace(",", "")
            if not cleaned:
                return None
            return Decimal(cleaned)
        except (InvalidOperation, ValueError):
            return None

    def _clean_string(self, value) -> Optional[str]:
        """
        Clean string value, returning None for empty/nan.

        Args:
            value: String value from CSV

        Returns:
            Cleaned string or None
        """
        if pd.isna(value):
            return None
        cleaned = str(value).strip()
        return cleaned if cleaned else None

    def _clean_raw_data(self, raw_dict: dict) -> dict:
        """
        Clean raw data dict for storage (remove NaN values).

        Args:
            raw_dict: Original row dict

        Returns:
            Cleaned dict safe for JSON serialization
        """
        cleaned = {}
        for key, value in raw_dict.items():
            if pd.isna(value):
                cleaned[key] = None
            elif isinstance(value, float) and math.isnan(value):
                cleaned[key] = None
            elif isinstance(value, Decimal):
                cleaned[key] = str(value)
            elif isinstance(value, (date, datetime)):
                cleaned[key] = value.isoformat()
            else:
                cleaned[key] = value
        return cleaned


class TransactionClassifier:
    """
    Utility class for re-classifying or batch-classifying transactions.

    Useful for:
        - Applying category overrides
        - Reclassifying after pattern updates
        - Bulk category updates
    """

    @staticmethod
    def reclassify_batch(
        transactions: list[ClassifiedTransaction],
        category_overrides: Optional[dict[str, ExpenseCategory]] = None,
    ) -> list[ClassifiedTransaction]:
        """
        Reclassify a batch of transactions with optional overrides.

        Args:
            transactions: List of classified transactions
            category_overrides: Merchant name → category mappings

        Returns:
            List of reclassified transactions
        """
        overrides = category_overrides or {}
        result = []

        for tx in transactions:
            if tx.merchant and tx.merchant in overrides:
                # Apply override
                tx.category = overrides[tx.merchant]
            result.append(tx)

        return result

    @staticmethod
    def filter_by_type(
        transactions: list[ClassifiedTransaction],
        tx_type: TransactionType,
    ) -> list[ClassifiedTransaction]:
        """
        Filter transactions by type.

        Args:
            transactions: List of classified transactions
            tx_type: Transaction type to filter for

        Returns:
            Filtered list of transactions
        """
        return [tx for tx in transactions if tx.transaction_type == tx_type]

    @staticmethod
    def filter_expenses(
        transactions: list[ClassifiedTransaction],
    ) -> list[ClassifiedTransaction]:
        """
        Get only expense transactions.

        Args:
            transactions: List of classified transactions

        Returns:
            List of expense transactions only
        """
        return TransactionClassifier.filter_by_type(
            transactions, TransactionType.EXPENSE
        )

    @staticmethod
    def filter_income(
        transactions: list[ClassifiedTransaction],
    ) -> list[ClassifiedTransaction]:
        """
        Get only income transactions.

        Args:
            transactions: List of classified transactions

        Returns:
            List of income transactions only
        """
        return TransactionClassifier.filter_by_type(
            transactions, TransactionType.INCOME
        )


# Export all
__all__ = [
    "FidelityTransactionParser",
    "TransactionClassifier",
]
