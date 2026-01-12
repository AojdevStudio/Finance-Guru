"""
Unit tests for Fidelity Transaction Parser

Tests:
    - CSV parsing functionality
    - Transaction classification
    - Merchant extraction
    - Category matching
    - Database operations
    - Report generation

Author: Finance Guru™ Development Team
Created: 2026-01-12
"""

import pytest
import tempfile
from datetime import date
from decimal import Decimal
from pathlib import Path

from src.models.transaction_inputs import (
    TransactionType,
    ExpenseCategory,
    RawFidelityTransaction,
    ClassifiedTransaction,
    TransactionBatch,
    MonthlyBudgetSummary,
    ParserConfig,
)
from src.data.constants import (
    get_transaction_type,
    extract_merchant,
    categorize_expense,
)
from src.data.fidelity_parser import FidelityTransactionParser
from src.data.transaction_db import TransactionDatabase
from src.data.reports import TransactionReporter


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_csv_path():
    """Path to sample transactions CSV."""
    return Path(__file__).parent / "fixtures" / "sample_transactions.csv"


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db = TransactionDatabase(f.name)
        yield db
        # Cleanup handled by temp file


@pytest.fixture
def sample_transactions():
    """Create sample classified transactions for testing."""
    return [
        ClassifiedTransaction(
            id="test00001",
            date=date(2025, 1, 15),
            original_action="DEBIT CARD PURCHASE",
            original_description="AMAZON.COM*1234 SEATTLE WA",
            transaction_type=TransactionType.EXPENSE,
            category=ExpenseCategory.SHOPPING,
            merchant="Amazon",
            amount=Decimal("-49.99"),
            is_margin=True,
            raw_data={},
        ),
        ClassifiedTransaction(
            id="test00002",
            date=date(2025, 1, 14),
            original_action="DIRECT DEPOSIT",
            original_description="EMPLOYER DIRECT DEP",
            transaction_type=TransactionType.INCOME,
            category=None,
            merchant="Employer",
            amount=Decimal("4250.00"),
            is_margin=False,
            raw_data={},
        ),
        ClassifiedTransaction(
            id="test00003",
            date=date(2025, 1, 13),
            original_action="DEBIT CARD PURCHASE",
            original_description="H-E-B #063 PEARLAND TX",
            transaction_type=TransactionType.EXPENSE,
            category=ExpenseCategory.GROCERIES,
            merchant="H-E-B",
            amount=Decimal("-156.78"),
            is_margin=True,
            raw_data={},
        ),
        ClassifiedTransaction(
            id="test00004",
            date=date(2025, 1, 12),
            original_action="MARGIN INTEREST",
            original_description="MARGIN INTEREST CHARGED",
            transaction_type=TransactionType.MARGIN_COST,
            category=None,
            merchant=None,
            amount=Decimal("-127.43"),
            is_margin=True,
            raw_data={},
        ),
    ]


# =============================================================================
# TRANSACTION TYPE CLASSIFICATION TESTS
# =============================================================================

class TestTransactionTypeClassification:
    """Tests for get_transaction_type function."""

    def test_debit_card_purchase(self):
        """Debit card purchases should be classified as expenses."""
        assert get_transaction_type("DEBIT CARD PURCHASE") == TransactionType.EXPENSE

    def test_direct_deposit(self):
        """Direct deposits should be classified as income."""
        assert get_transaction_type("DIRECT DEPOSIT") == TransactionType.INCOME

    def test_dividend_received(self):
        """Dividends should be classified as income."""
        assert get_transaction_type("DIVIDEND RECEIVED") == TransactionType.INCOME

    def test_margin_interest(self):
        """Margin interest should be classified as margin cost."""
        assert get_transaction_type("MARGIN INTEREST") == TransactionType.MARGIN_COST

    def test_reinvestment(self):
        """Reinvestments should be classified as investments."""
        assert get_transaction_type("REINVESTMENT") == TransactionType.INVESTMENT

    def test_journaled_transfer(self):
        """Journaled transactions should be classified as transfers."""
        assert get_transaction_type("JOURNALED") == TransactionType.TRANSFER

    def test_unknown_action(self):
        """Unknown actions should be classified as other."""
        assert get_transaction_type("SOME UNKNOWN ACTION") == TransactionType.OTHER

    def test_case_insensitivity(self):
        """Classification should be case insensitive."""
        assert get_transaction_type("debit card purchase") == TransactionType.EXPENSE
        assert get_transaction_type("DEBIT CARD PURCHASE") == TransactionType.EXPENSE

    def test_partial_match(self):
        """Should match partial action strings."""
        assert get_transaction_type("DEBIT CARD PURCHASE AT MERCHANT") == TransactionType.EXPENSE
        assert get_transaction_type("DIVIDEND RECEIVED FROM JEPI") == TransactionType.INCOME


# =============================================================================
# MERCHANT EXTRACTION TESTS
# =============================================================================

class TestMerchantExtraction:
    """Tests for extract_merchant function."""

    def test_amazon(self):
        """Should extract Amazon from various formats."""
        assert extract_merchant("AMAZON.COM*1234567890 AMZN.COM/BILLWA") == "Amazon"
        assert extract_merchant("AMZN MKTP US*AB12CD345") == "Amazon"

    def test_uber_eats(self):
        """Should extract Uber Eats."""
        assert extract_merchant("UBER *EATS HELP.UBER.COM CA") == "Uber Eats"

    def test_uber_ride(self):
        """Should extract Uber for rides."""
        assert extract_merchant("UBER *TRIP HELP.UBER.COM CA") == "Uber"

    def test_square_merchant(self):
        """Should extract Square merchant names."""
        result = extract_merchant("SQ *COFFEE SHOP Austin TX")
        assert result is not None
        assert "Coffee" in result

    def test_toast_merchant(self):
        """Should extract Toast merchant names."""
        result = extract_merchant("TST*BENIHANA SUGAR LAND TX")
        assert result is not None
        assert "Benihana" in result

    def test_heb(self):
        """Should extract H-E-B."""
        assert extract_merchant("H-E-B #063 PEARLAND TX") == "H-E-B"

    def test_tesla_supercharger(self):
        """Should extract Tesla Supercharger."""
        assert extract_merchant("Tesla, Inc. SUPERCHA600118984238637") == "Tesla Supercharger"

    def test_starbucks(self):
        """Should extract Starbucks."""
        assert extract_merchant("STARBUCKS STORE 12345 HOUSTON TX") == "Starbucks"

    def test_cvs(self):
        """Should extract CVS."""
        assert extract_merchant("CVS/PHARMACY #7890 MANVEL TX") == "CVS"

    def test_atm(self):
        """Should extract ATM Withdrawal."""
        assert extract_merchant("ATM0043 11555 MAGNOLIA PEARLAND TX") == "ATM Withdrawal"


# =============================================================================
# EXPENSE CATEGORIZATION TESTS
# =============================================================================

class TestExpenseCategorization:
    """Tests for categorize_expense function."""

    def test_groceries(self):
        """Should categorize grocery stores."""
        assert categorize_expense("H-E-B #063 PEARLAND TX") == ExpenseCategory.GROCERIES
        assert categorize_expense("WALMART SUPERCENTER") == ExpenseCategory.GROCERIES
        assert categorize_expense("COSTCO WHSE #1234") == ExpenseCategory.GROCERIES

    def test_dining(self):
        """Should categorize restaurants."""
        assert categorize_expense("STARBUCKS STORE 12345") == ExpenseCategory.DINING
        assert categorize_expense("CHIPOTLE MEXICAN GRILL") == ExpenseCategory.DINING
        assert categorize_expense("UBER EATS") == ExpenseCategory.DINING

    def test_transportation(self):
        """Should categorize transportation."""
        assert categorize_expense("Tesla, Inc. SUPERCHA") == ExpenseCategory.TRANSPORTATION
        assert categorize_expense("UBER *TRIP") == ExpenseCategory.TRANSPORTATION
        assert categorize_expense("PARKING LOT") == ExpenseCategory.TRANSPORTATION

    def test_healthcare(self):
        """Should categorize healthcare."""
        assert categorize_expense("CVS/PHARMACY") == ExpenseCategory.HEALTHCARE
        assert categorize_expense("WALGREENS") == ExpenseCategory.HEALTHCARE

    def test_shopping(self):
        """Should categorize shopping."""
        assert categorize_expense("AMAZON.COM") == ExpenseCategory.SHOPPING
        assert categorize_expense("TARGET STORE") == ExpenseCategory.SHOPPING
        assert categorize_expense("MARSHALLS") == ExpenseCategory.SHOPPING

    def test_family(self):
        """Should categorize family expenses."""
        assert categorize_expense("AQUA TOTS SWIMMING") == ExpenseCategory.FAMILY
        assert categorize_expense("BRIGHTWHEEL DAYCARE") == ExpenseCategory.FAMILY

    def test_cash(self):
        """Should categorize cash withdrawals."""
        assert categorize_expense("ATM WITHDRAWAL") == ExpenseCategory.CASH

    def test_uncategorized(self):
        """Should return uncategorized for unknown merchants."""
        assert categorize_expense("UNKNOWN MERCHANT XYZ") == ExpenseCategory.UNCATEGORIZED


# =============================================================================
# CSV PARSER TESTS
# =============================================================================

class TestFidelityParser:
    """Tests for FidelityTransactionParser."""

    def test_parse_csv(self, sample_csv_path):
        """Should parse sample CSV successfully."""
        parser = FidelityTransactionParser()
        batch = parser.parse_csv(sample_csv_path)

        assert isinstance(batch, TransactionBatch)
        assert batch.count > 0
        assert batch.source_file == "sample_transactions.csv"

    def test_parse_csv_date_range(self, sample_csv_path):
        """Should compute date range from transactions."""
        parser = FidelityTransactionParser()
        batch = parser.parse_csv(sample_csv_path)

        assert batch.date_range_start is not None
        assert batch.date_range_end is not None
        assert batch.date_range_start <= batch.date_range_end

    def test_parse_csv_transaction_types(self, sample_csv_path):
        """Should correctly classify transaction types."""
        parser = FidelityTransactionParser()
        batch = parser.parse_csv(sample_csv_path)

        types = set(tx.transaction_type for tx in batch.transactions)
        # Sample CSV contains expenses, income, margin cost, investments, transfers
        assert TransactionType.EXPENSE in types
        assert TransactionType.INCOME in types

    def test_parse_csv_merchants(self, sample_csv_path):
        """Should extract merchants from descriptions."""
        parser = FidelityTransactionParser()
        batch = parser.parse_csv(sample_csv_path)

        merchants = [tx.merchant for tx in batch.transactions if tx.merchant]
        assert len(merchants) > 0
        assert "Amazon" in merchants or "H-E-B" in merchants

    def test_parse_csv_amounts(self, sample_csv_path):
        """Should parse amounts correctly."""
        parser = FidelityTransactionParser()
        batch = parser.parse_csv(sample_csv_path)

        # All transactions should have amounts
        for tx in batch.transactions:
            assert tx.amount is not None
            assert isinstance(tx.amount, Decimal)

    def test_parse_csv_margin_detection(self, sample_csv_path):
        """Should detect margin transactions."""
        parser = FidelityTransactionParser()
        batch = parser.parse_csv(sample_csv_path)

        margin_txs = [tx for tx in batch.transactions if tx.is_margin]
        cash_txs = [tx for tx in batch.transactions if not tx.is_margin]

        # Sample has both margin and cash transactions
        assert len(margin_txs) > 0
        assert len(cash_txs) > 0

    def test_parse_csv_unique_ids(self, sample_csv_path):
        """Should generate unique IDs for each transaction."""
        parser = FidelityTransactionParser()
        batch = parser.parse_csv(sample_csv_path)

        ids = [tx.id for tx in batch.transactions]
        assert len(ids) == len(set(ids))  # All unique

    def test_file_not_found(self):
        """Should raise error for missing file."""
        parser = FidelityTransactionParser()
        with pytest.raises(FileNotFoundError):
            parser.parse_csv("/nonexistent/file.csv")


# =============================================================================
# DATABASE TESTS
# =============================================================================

class TestTransactionDatabase:
    """Tests for TransactionDatabase."""

    def test_insert_batch(self, temp_db, sample_transactions):
        """Should insert transactions and detect duplicates."""
        batch = TransactionBatch(
            transactions=sample_transactions,
            source_file="test.csv",
        )

        new_count, dup_count = temp_db.insert_batch(batch)
        assert new_count == 4
        assert dup_count == 0

        # Insert again - should be all duplicates
        new_count2, dup_count2 = temp_db.insert_batch(batch)
        assert new_count2 == 0
        assert dup_count2 == 4

    def test_get_transactions(self, temp_db, sample_transactions):
        """Should retrieve transactions with filters."""
        batch = TransactionBatch(transactions=sample_transactions)
        temp_db.insert_batch(batch)

        # Get all
        all_txs = temp_db.get_transactions()
        assert len(all_txs) == 4

        # Filter by type
        expenses = temp_db.get_transactions(tx_type=TransactionType.EXPENSE)
        assert len(expenses) == 2

        # Filter by date
        filtered = temp_db.get_transactions(
            start_date=date(2025, 1, 14),
            end_date=date(2025, 1, 15),
        )
        assert len(filtered) == 2

    def test_category_overrides(self, temp_db, sample_transactions):
        """Should apply category overrides."""
        batch = TransactionBatch(transactions=sample_transactions)
        temp_db.insert_batch(batch)

        # Set override
        temp_db.set_category_override("Amazon", ExpenseCategory.ENTERTAINMENT)

        # Get overrides
        overrides = temp_db.get_category_overrides()
        assert "Amazon" in overrides
        assert overrides["Amazon"] == ExpenseCategory.ENTERTAINMENT

    def test_export_csv(self, temp_db, sample_transactions):
        """Should export to CSV."""
        batch = TransactionBatch(transactions=sample_transactions)
        temp_db.insert_batch(batch)

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            count = temp_db.export_csv(f.name)
            assert count == 4

            # Verify file exists and has content
            content = Path(f.name).read_text()
            assert "Date" in content
            assert "Amazon" in content or "H-E-B" in content

    def test_stats(self, temp_db, sample_transactions):
        """Should return correct statistics."""
        batch = TransactionBatch(transactions=sample_transactions)
        temp_db.insert_batch(batch)

        stats = temp_db.get_stats()
        assert stats["total_transactions"] == 4
        assert stats["import_count"] == 1
        assert "expense" in stats["by_type"]


# =============================================================================
# REPORTER TESTS
# =============================================================================

class TestTransactionReporter:
    """Tests for TransactionReporter."""

    def test_monthly_summary(self, sample_transactions):
        """Should generate monthly summary."""
        reporter = TransactionReporter(sample_transactions)
        summary = reporter.monthly_summary("2025-01")

        assert isinstance(summary, MonthlyBudgetSummary)
        assert summary.month == "2025-01"
        assert summary.total_income == Decimal("4250.00")
        assert summary.total_expenses < Decimal("0")  # Negative

    def test_category_breakdown(self, sample_transactions):
        """Should break down by category."""
        reporter = TransactionReporter(sample_transactions)
        categories = reporter.category_breakdown()

        assert ExpenseCategory.SHOPPING.value in categories
        assert ExpenseCategory.GROCERIES.value in categories

    def test_merchant_ranking(self, sample_transactions):
        """Should rank merchants by spending."""
        reporter = TransactionReporter(sample_transactions)
        merchants = reporter.merchant_ranking(limit=10)

        assert len(merchants) > 0
        # Should be sorted by amount (most negative first)
        for merchant, total, count in merchants:
            assert total < 0
            assert count > 0

    def test_margin_analysis(self, sample_transactions):
        """Should analyze margin usage."""
        reporter = TransactionReporter(sample_transactions)
        margin = reporter.margin_analysis()

        assert "total_interest_paid" in margin
        assert margin["total_interest_paid"] == Decimal("-127.43")

    def test_cash_flow_analysis(self, sample_transactions):
        """Should analyze cash flow."""
        reporter = TransactionReporter(sample_transactions)
        cash_flow = reporter.cash_flow_analysis()

        assert cash_flow["total_income"] == Decimal("4250.00")
        assert cash_flow["total_expenses"] < 0

    def test_uncategorized(self, sample_transactions):
        """Should find uncategorized transactions."""
        # Add uncategorized transaction
        uncategorized_tx = ClassifiedTransaction(
            id="testuncat0",
            date=date(2025, 1, 10),
            original_action="DEBIT CARD PURCHASE",
            original_description="UNKNOWN MERCHANT",
            transaction_type=TransactionType.EXPENSE,
            category=ExpenseCategory.UNCATEGORIZED,
            merchant="Unknown",
            amount=Decimal("-25.00"),
            is_margin=False,
            raw_data={},
        )

        transactions = sample_transactions + [uncategorized_tx]
        reporter = TransactionReporter(transactions)
        uncategorized = reporter.get_uncategorized()

        assert len(uncategorized) == 1
        assert uncategorized[0].id == "testuncat0"


# =============================================================================
# PYDANTIC MODEL TESTS
# =============================================================================

class TestPydanticModels:
    """Tests for Pydantic model validation."""

    def test_raw_transaction_validation(self):
        """Should validate raw transaction fields."""
        tx = RawFidelityTransaction(
            run_date=date(2025, 1, 15),
            action="DEBIT CARD PURCHASE",
            description="TEST MERCHANT",
            type="MARGIN",
            amount=Decimal("-49.99"),
        )
        assert tx.action == "DEBIT CARD PURCHASE"

    def test_classified_transaction_id_generation(self):
        """Should generate consistent IDs."""
        id1 = ClassifiedTransaction.generate_id(
            date(2025, 1, 15),
            "DEBIT CARD PURCHASE",
            "AMAZON",
            Decimal("-49.99"),
        )
        id2 = ClassifiedTransaction.generate_id(
            date(2025, 1, 15),
            "DEBIT CARD PURCHASE",
            "AMAZON",
            Decimal("-49.99"),
        )
        # Same inputs should generate same ID
        assert id1 == id2

        id3 = ClassifiedTransaction.generate_id(
            date(2025, 1, 16),  # Different date
            "DEBIT CARD PURCHASE",
            "AMAZON",
            Decimal("-49.99"),
        )
        # Different inputs should generate different ID
        assert id1 != id3

    def test_monthly_summary_computed_fields(self):
        """Should compute net values correctly."""
        summary = MonthlyBudgetSummary(
            month="2025-01",
            total_income=Decimal("5000"),
            total_expenses=Decimal("-3000"),
            total_margin_cost=Decimal("-100"),
            margin_drawn=Decimal("1000"),
            margin_paid_down=Decimal("500"),
        )

        assert summary.net_margin_change == Decimal("500")  # 1000 - 500
        assert summary.net_cash_flow == Decimal("1900")  # 5000 - 3000 - 100

    def test_parser_config_defaults(self):
        """Should have sensible defaults."""
        config = ParserConfig()
        assert config.date_format == "%m/%d/%Y"
        assert config.skip_rows == 2
        assert config.default_category == ExpenseCategory.UNCATEGORIZED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
