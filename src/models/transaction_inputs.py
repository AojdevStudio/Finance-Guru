"""
Fidelity Transaction Parser Pydantic Models for Finance Guru™

This module defines type-safe data structures for parsing and classifying
Fidelity brokerage transaction CSV exports.

ARCHITECTURE NOTE:
These models represent Layer 1 of our 3-layer architecture:
    Layer 1: Pydantic Models (THIS FILE) - Data validation
    Layer 2: Parser/Classifier Classes - Business logic
    Layer 3: CLI Interface - User integration

PROBLEM CONTEXT:
Users following the "Paycheck to Portfolio" method cannot use traditional
budgeting apps because:
- Aggregators classify all brokerage activity as "investments"
- Margin debits appear as loans, not purchases
- Debit card spending triggers SPAXX liquidation (shows as "sales")
- Paycheck deposits that pay down margin aren't "income"

SOLUTION:
Parse Fidelity CSV exports, reclassify transactions into standard budgeting
categories, and output clean data for financial analysis.

Author: Finance Guru™ Development Team
Created: 2026-01-12
"""

from __future__ import annotations

import hashlib
from datetime import date as date_type, datetime
from decimal import Decimal
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator, computed_field


class TransactionType(str, Enum):
    """
    Classified transaction types for budget analysis.

    These map Fidelity's raw "Action" field to budget-friendly categories.
    """
    EXPENSE = "expense"                    # Debit card purchases, EFT, checks
    INCOME = "income"                      # Direct deposits, ACH credits, dividends
    MARGIN_COST = "margin_cost"            # Margin interest charges
    MARGIN_DRAW = "margin_draw"            # Drawing margin (increasing debt)
    MARGIN_PAYDOWN = "margin_paydown"      # Paying down margin (reducing debt)
    INVESTMENT = "investment"              # Buy/sell/reinvestment activity
    TRANSFER = "transfer"                  # Account transfers
    AUTO_LIQUIDATION = "auto_liquidation"  # SPAXX redemption to cover debit
    AUTO_PURCHASE = "auto_purchase"        # Excess cash swept to SPAXX
    OTHER = "other"                        # Unclassified transactions


class ExpenseCategory(str, Enum):
    """
    Standard expense categories matching Budget Planner structure.

    These categories align with the Google Sheets Budget Planner
    for seamless integration with financial tracking.
    """
    HOUSING = "Housing"
    UTILITIES = "Bills & Utilities"
    GROCERIES = "Groceries"
    DINING = "Dining Out"
    TRANSPORTATION = "Auto & Transport"
    HEALTHCARE = "Health & Wellness"
    ENTERTAINMENT = "Entertainment"
    SHOPPING = "Shopping"
    SUBSCRIPTIONS = "Subscriptions"
    TRAVEL = "Travel"
    PERSONAL = "Personal Care"
    FAMILY = "Family Care"
    EDUCATION = "Tuition"
    BUSINESS = "Business Expense"
    LOAN_PAYMENT = "Loan Payment"
    HOME_GARDEN = "Home & Garden"
    CASH = "Cash Withdrawal"
    CRYPTO = "Crypto Deposit"
    CREDIT_CARD = "Credit Card Payment"
    GAS = "Gas"
    WATER = "Water"
    ELECTRIC = "Light Bill"
    MORTGAGE = "Mortgage"
    CELL_PHONE = "Cell Phone"
    SOFTWARE = "Software & Tech"
    EXEMPT = "Exempt"
    UNCATEGORIZED = "Uncategorized"


class RawFidelityTransaction(BaseModel):
    """
    Raw transaction as parsed from Fidelity CSV export.

    WHAT: Direct mapping of Fidelity CSV columns
    WHY: Preserves original data before classification
    VALIDATES:
        - Run date is valid
        - Amount is a valid decimal
        - Required fields are present

    CSV FORMAT (from Fidelity Activity & Orders → History → Download):
    Run Date, Action, Symbol, Description, Type, Price ($), Quantity,
    Commission ($), Fees ($), Accrued Interest ($), Amount ($),
    Cash Balance ($), Settlement Date

    NOTE: Fidelity CSVs have metadata rows - Row 3 contains headers.
    """

    run_date: date_type = Field(
        ...,
        description="Transaction date (from 'Run Date' column)"
    )

    action: str = Field(
        ...,
        min_length=1,
        description="Transaction type/action (e.g., 'DEBIT CARD PURCHASE', 'DIVIDEND RECEIVED')"
    )

    symbol: Optional[str] = Field(
        default=None,
        description="Ticker symbol if applicable (e.g., 'SPAXX', 'VOO')"
    )

    description: str = Field(
        ...,
        description="Full transaction description (contains merchant info for debit cards)"
    )

    type: str = Field(
        ...,
        description="Cash or Margin indicator"
    )

    quantity: Optional[Decimal] = Field(
        default=None,
        description="Number of shares if applicable"
    )

    price: Optional[Decimal] = Field(
        default=None,
        ge=0,
        description="Per-share price if applicable"
    )

    commission: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        description="Trading commission (typically $0 at Fidelity)"
    )

    fees: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        description="Other transaction fees"
    )

    accrued_interest: Decimal = Field(
        default=Decimal("0"),
        description="Accrued interest for bond transactions"
    )

    amount: Decimal = Field(
        ...,
        description="Total transaction amount (negative = outflow, positive = inflow)"
    )

    cash_balance: Optional[Decimal] = Field(
        default=None,
        description="Running cash balance after transaction"
    )

    settlement_date: Optional[date_type] = Field(
        default=None,
        description="Settlement date for the transaction"
    )

    @field_validator("action")
    @classmethod
    def action_must_not_be_empty(cls, v: str) -> str:
        """Ensure action field has meaningful content."""
        if not v.strip():
            raise ValueError("Action field cannot be empty or whitespace")
        return v.strip().upper()

    @field_validator("type")
    @classmethod
    def type_must_be_valid(cls, v: str) -> str:
        """Normalize type field (CASH or MARGIN)."""
        normalized = v.strip().upper()
        if normalized not in ("CASH", "MARGIN", ""):
            # Some transactions may have empty type
            pass
        return normalized

    @field_validator("symbol")
    @classmethod
    def clean_symbol(cls, v: Optional[str]) -> Optional[str]:
        """Clean and uppercase symbol if present."""
        if v is None or v.strip() == "":
            return None
        # Remove special characters like ** from SPAXX**
        cleaned = "".join(c for c in v.upper() if c.isalnum())
        return cleaned if cleaned else None

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "run_date": "2025-01-15",
                "action": "DEBIT CARD PURCHASE",
                "symbol": None,
                "description": "AMAZON.COM*1234567890 AMZN.COM/BILLWA",
                "type": "MARGIN",
                "quantity": None,
                "price": None,
                "commission": "0",
                "fees": "0",
                "accrued_interest": "0",
                "amount": "-49.99",
                "cash_balance": "1234.56",
                "settlement_date": "2025-01-17"
            }]
        }
    }


class ClassifiedTransaction(BaseModel):
    """
    Transaction after classification and enrichment.

    WHAT: Fully processed transaction with category, merchant, and type
    WHY: Ready for budget analysis, reporting, and export
    VALIDATES:
        - Transaction ID is generated correctly
        - Category is assigned for expenses
        - Original data preserved for audit

    USE CASES:
        - Budget tracking (expenses by category)
        - Cash flow analysis (income vs expenses)
        - Margin monitoring (draw, paydown, interest)
        - Merchant spending analysis
    """

    id: str = Field(
        ...,
        min_length=8,
        max_length=32,
        description="Unique hash-based ID for deduplication"
    )

    date: date_type = Field(
        ...,
        description="Transaction date"
    )

    original_action: str = Field(
        ...,
        description="Original Fidelity action field"
    )

    original_description: str = Field(
        ...,
        description="Original description for reference"
    )

    # Classification fields
    transaction_type: TransactionType = Field(
        ...,
        description="Classified transaction type"
    )

    category: Optional[ExpenseCategory] = Field(
        default=None,
        description="Expense category (only for expense transactions)"
    )

    merchant: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Extracted merchant name"
    )

    # Amount fields
    amount: Decimal = Field(
        ...,
        description="Transaction amount (negative = outflow)"
    )

    is_margin: bool = Field(
        ...,
        description="Whether this transaction used margin"
    )

    # Metadata
    symbol: Optional[str] = Field(
        default=None,
        description="Ticker symbol if applicable"
    )

    raw_data: dict = Field(
        ...,
        description="Original parsed row for debugging and audit"
    )

    @computed_field
    @property
    def is_expense(self) -> bool:
        """Check if transaction is an expense."""
        return self.transaction_type == TransactionType.EXPENSE

    @computed_field
    @property
    def is_income(self) -> bool:
        """Check if transaction is income."""
        return self.transaction_type == TransactionType.INCOME

    @computed_field
    @property
    def abs_amount(self) -> Decimal:
        """Absolute value of amount for display."""
        return abs(self.amount)

    @model_validator(mode="after")
    def validate_category_for_expenses(self) -> "ClassifiedTransaction":
        """Ensure expenses have a category assigned."""
        if self.transaction_type == TransactionType.EXPENSE:
            if self.category is None:
                self.category = ExpenseCategory.UNCATEGORIZED
        return self

    @staticmethod
    def generate_id(date: date_type, action: str, description: str, amount: Decimal) -> str:
        """
        Generate unique transaction ID for deduplication.

        Uses SHA256 hash of key fields truncated to 16 chars.
        Same transaction will always generate same ID.
        """
        unique_string = f"{date}|{action}|{description}|{amount}"
        return hashlib.sha256(unique_string.encode()).hexdigest()[:16]

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "id": "a1b2c3d4e5f6g7h8",
                "date": "2025-01-15",
                "original_action": "DEBIT CARD PURCHASE",
                "original_description": "AMAZON.COM*1234567890 AMZN.COM/BILLWA",
                "transaction_type": "expense",
                "category": "Shopping",
                "merchant": "Amazon",
                "amount": "-49.99",
                "is_margin": True,
                "symbol": None,
                "raw_data": {}
            }]
        }
    }


class TransactionBatch(BaseModel):
    """
    Collection of classified transactions from a single import.

    WHAT: Batch of transactions with import metadata
    WHY: Tracks import history and provides batch operations
    """

    transactions: list[ClassifiedTransaction] = Field(
        default_factory=list,
        description="List of classified transactions"
    )

    source_file: Optional[str] = Field(
        default=None,
        description="Source CSV filename"
    )

    import_timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When this batch was imported"
    )

    date_range_start: Optional[date_type] = Field(
        default=None,
        description="Earliest transaction date in batch"
    )

    date_range_end: Optional[date_type] = Field(
        default=None,
        description="Latest transaction date in batch"
    )

    @computed_field
    @property
    def count(self) -> int:
        """Number of transactions in batch."""
        return len(self.transactions)

    @computed_field
    @property
    def total_expenses(self) -> Decimal:
        """Sum of all expense transactions."""
        return sum(
            t.amount for t in self.transactions
            if t.transaction_type == TransactionType.EXPENSE
        )

    @computed_field
    @property
    def total_income(self) -> Decimal:
        """Sum of all income transactions."""
        return sum(
            t.amount for t in self.transactions
            if t.transaction_type == TransactionType.INCOME
        )

    @model_validator(mode="after")
    def compute_date_range(self) -> "TransactionBatch":
        """Automatically compute date range from transactions."""
        if self.transactions:
            dates = [t.date for t in self.transactions]
            self.date_range_start = min(dates)
            self.date_range_end = max(dates)
        return self


class MonthlyBudgetSummary(BaseModel):
    """
    Aggregated monthly budget view.

    WHAT: Summary statistics for a calendar month
    WHY: Enables monthly budget tracking and trend analysis

    Provides breakdown of:
        - Income vs expenses
        - Margin activity (cost, draw, paydown)
        - Expenses by category
        - Top merchants by spend
    """

    month: str = Field(
        ...,
        pattern=r"^\d{4}-\d{2}$",
        description="Month in YYYY-MM format"
    )

    total_income: Decimal = Field(
        default=Decimal("0"),
        description="Total income for the month"
    )

    total_expenses: Decimal = Field(
        default=Decimal("0"),
        description="Total expenses for the month (negative)"
    )

    total_margin_cost: Decimal = Field(
        default=Decimal("0"),
        description="Total margin interest paid"
    )

    margin_drawn: Decimal = Field(
        default=Decimal("0"),
        description="Amount drawn from margin"
    )

    margin_paid_down: Decimal = Field(
        default=Decimal("0"),
        description="Amount paid toward margin"
    )

    expenses_by_category: dict[str, Decimal] = Field(
        default_factory=dict,
        description="Expense totals by category"
    )

    top_merchants: list[tuple[str, Decimal]] = Field(
        default_factory=list,
        description="Top merchants by total spend (merchant, amount)"
    )

    transaction_count: int = Field(
        default=0,
        description="Total transactions in the month"
    )

    @computed_field
    @property
    def net_margin_change(self) -> Decimal:
        """Net change in margin balance (positive = increased debt)."""
        return self.margin_drawn - self.margin_paid_down

    @computed_field
    @property
    def net_cash_flow(self) -> Decimal:
        """Net cash flow (income - expenses - margin cost)."""
        return self.total_income + self.total_expenses - abs(self.total_margin_cost)

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "month": "2025-01",
                "total_income": "8500.00",
                "total_expenses": "-5234.56",
                "total_margin_cost": "-127.43",
                "margin_drawn": "2500.00",
                "margin_paid_down": "4000.00",
                "expenses_by_category": {
                    "Housing": "-2100.00",
                    "Groceries": "-650.00",
                    "Dining Out": "-420.00"
                },
                "top_merchants": [
                    ["Amazon", "-350.00"],
                    ["H-E-B", "-280.00"],
                    ["Tesla Supercharger", "-150.00"]
                ],
                "transaction_count": 45
            }]
        }
    }


class ParserConfig(BaseModel):
    """
    Configuration for the Fidelity transaction parser.

    WHAT: Customizable parsing and categorization settings
    WHY: Allows users to adjust behavior without code changes
    """

    date_format: str = Field(
        default="%m/%d/%Y",
        description="Expected date format in Fidelity CSV"
    )

    skip_rows: int = Field(
        default=2,
        ge=0,
        description="Number of header rows to skip in CSV (Fidelity has 2)"
    )

    default_category: ExpenseCategory = Field(
        default=ExpenseCategory.UNCATEGORIZED,
        description="Default category for unmatched expenses"
    )

    include_investments: bool = Field(
        default=False,
        description="Include investment transactions in budget view"
    )

    margin_interest_rate: Decimal = Field(
        default=Decimal("0.0875"),
        ge=0,
        le=1,
        description="Annual margin interest rate for projections"
    )

    margin_warning_threshold: Decimal = Field(
        default=Decimal("0.5"),
        ge=0,
        le=1,
        description="Margin utilization level that triggers warnings"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "date_format": "%m/%d/%Y",
                "skip_rows": 2,
                "default_category": "Uncategorized",
                "include_investments": False,
                "margin_interest_rate": "0.0875",
                "margin_warning_threshold": "0.5"
            }]
        }
    }


# Type exports
__all__ = [
    "TransactionType",
    "ExpenseCategory",
    "RawFidelityTransaction",
    "ClassifiedTransaction",
    "TransactionBatch",
    "MonthlyBudgetSummary",
    "ParserConfig",
]
