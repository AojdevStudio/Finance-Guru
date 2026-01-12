"""
Data management and processing modules.

This package contains data loading, parsing, and persistence modules.

Available Modules:
    - fidelity_parser: Parse Fidelity brokerage CSV transaction exports
    - transaction_db: SQLite persistence for classified transactions
    - reports: Generate budget summaries and spending analytics
    - constants: Transaction type mappings and category patterns
"""

from src.data.fidelity_parser import FidelityTransactionParser, TransactionClassifier
from src.data.transaction_db import TransactionDatabase
from src.data.reports import (
    TransactionReporter,
    format_monthly_summary,
    format_category_breakdown,
    format_merchant_ranking,
)
from src.data.constants import (
    get_transaction_type,
    extract_merchant,
    categorize_expense,
)

__all__ = [
    # Parser
    "FidelityTransactionParser",
    "TransactionClassifier",
    # Database
    "TransactionDatabase",
    # Reports
    "TransactionReporter",
    "format_monthly_summary",
    "format_category_breakdown",
    "format_merchant_ranking",
    # Constants/utilities
    "get_transaction_type",
    "extract_merchant",
    "categorize_expense",
]