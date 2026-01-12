"""
Transaction Reports Module

Generates summary reports and analytics from classified transactions.

Report Types:
    - Monthly budget summary
    - Category breakdown
    - Merchant ranking
    - Margin analysis
    - Cash flow analysis

Author: Finance Guru™ Development Team
Created: 2026-01-12
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import Optional

from src.models.transaction_inputs import (
    ClassifiedTransaction,
    TransactionBatch,
    MonthlyBudgetSummary,
    TransactionType,
    ExpenseCategory,
)


class TransactionReporter:
    """
    Generate reports and summaries from transaction data.

    WHAT: Aggregates and analyzes transaction data
    WHY: Provides insights into spending patterns, cash flow, and margin usage
    """

    def __init__(self, transactions: list[ClassifiedTransaction]):
        """
        Initialize reporter with transactions.

        Args:
            transactions: List of classified transactions to analyze
        """
        self.transactions = transactions

    @classmethod
    def from_batch(cls, batch: TransactionBatch) -> "TransactionReporter":
        """
        Create reporter from a TransactionBatch.

        Args:
            batch: TransactionBatch to analyze

        Returns:
            TransactionReporter instance
        """
        return cls(batch.transactions)

    def monthly_summary(self, month: str) -> MonthlyBudgetSummary:
        """
        Generate monthly budget summary.

        Args:
            month: Month in YYYY-MM format

        Returns:
            MonthlyBudgetSummary with all metrics
        """
        # Filter transactions for the month
        month_txs = [
            tx for tx in self.transactions
            if tx.date.strftime("%Y-%m") == month
        ]

        # Calculate totals
        total_income = Decimal("0")
        total_expenses = Decimal("0")
        total_margin_cost = Decimal("0")
        margin_drawn = Decimal("0")
        margin_paid_down = Decimal("0")
        expenses_by_category: dict[str, Decimal] = defaultdict(Decimal)
        merchant_totals: dict[str, Decimal] = defaultdict(Decimal)

        for tx in month_txs:
            if tx.transaction_type == TransactionType.INCOME:
                total_income += tx.amount
            elif tx.transaction_type == TransactionType.EXPENSE:
                total_expenses += tx.amount
                if tx.category:
                    expenses_by_category[tx.category.value] += tx.amount
                if tx.merchant:
                    merchant_totals[tx.merchant] += tx.amount
            elif tx.transaction_type == TransactionType.MARGIN_COST:
                total_margin_cost += tx.amount
            elif tx.transaction_type == TransactionType.MARGIN_DRAW:
                margin_drawn += abs(tx.amount)
            elif tx.transaction_type == TransactionType.MARGIN_PAYDOWN:
                margin_paid_down += abs(tx.amount)

        # Sort merchants by spend (most negative first)
        top_merchants = sorted(
            merchant_totals.items(),
            key=lambda x: x[1],
        )[:10]

        return MonthlyBudgetSummary(
            month=month,
            total_income=total_income,
            total_expenses=total_expenses,
            total_margin_cost=total_margin_cost,
            margin_drawn=margin_drawn,
            margin_paid_down=margin_paid_down,
            expenses_by_category=dict(expenses_by_category),
            top_merchants=top_merchants,
            transaction_count=len(month_txs),
        )

    def category_breakdown(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> dict[str, Decimal]:
        """
        Get expense totals by category.

        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Dict mapping category names to total amounts
        """
        filtered = self._filter_by_date(start_date, end_date)
        expenses = [
            tx for tx in filtered
            if tx.transaction_type == TransactionType.EXPENSE
        ]

        totals: dict[str, Decimal] = defaultdict(Decimal)
        for tx in expenses:
            category = tx.category.value if tx.category else "Uncategorized"
            totals[category] += tx.amount

        # Sort by amount (most negative first)
        return dict(sorted(totals.items(), key=lambda x: x[1]))

    def merchant_ranking(
        self,
        limit: int = 20,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> list[tuple[str, Decimal, int]]:
        """
        Rank merchants by total spending.

        Args:
            limit: Maximum number of merchants to return
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            List of (merchant, total, count) tuples
        """
        filtered = self._filter_by_date(start_date, end_date)
        expenses = [
            tx for tx in filtered
            if tx.transaction_type == TransactionType.EXPENSE and tx.merchant
        ]

        # Aggregate by merchant
        totals: dict[str, Decimal] = defaultdict(Decimal)
        counts: dict[str, int] = defaultdict(int)

        for tx in expenses:
            totals[tx.merchant] += tx.amount
            counts[tx.merchant] += 1

        # Sort by total (most negative first)
        sorted_merchants = sorted(totals.items(), key=lambda x: x[1])

        return [
            (merchant, total, counts[merchant])
            for merchant, total in sorted_merchants[:limit]
        ]

    def margin_analysis(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> dict:
        """
        Analyze margin usage and costs.

        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Dict with margin metrics
        """
        filtered = self._filter_by_date(start_date, end_date)

        # Separate margin transactions
        margin_costs = [
            tx for tx in filtered
            if tx.transaction_type == TransactionType.MARGIN_COST
        ]
        margin_draws = [
            tx for tx in filtered
            if tx.transaction_type == TransactionType.MARGIN_DRAW
        ]
        margin_paydowns = [
            tx for tx in filtered
            if tx.transaction_type == TransactionType.MARGIN_PAYDOWN
        ]
        margin_expenses = [
            tx for tx in filtered
            if tx.transaction_type == TransactionType.EXPENSE and tx.is_margin
        ]

        total_interest = sum(tx.amount for tx in margin_costs)
        total_drawn = sum(abs(tx.amount) for tx in margin_draws)
        total_paid_down = sum(abs(tx.amount) for tx in margin_paydowns)
        total_margin_expenses = sum(tx.amount for tx in margin_expenses)

        return {
            "total_interest_paid": total_interest,
            "total_drawn": total_drawn,
            "total_paid_down": total_paid_down,
            "net_margin_change": total_drawn - total_paid_down,
            "margin_expense_total": total_margin_expenses,
            "interest_charge_count": len(margin_costs),
            "draw_count": len(margin_draws),
            "paydown_count": len(margin_paydowns),
            "margin_expense_count": len(margin_expenses),
        }

    def cash_flow_analysis(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> dict:
        """
        Analyze cash flow (income vs expenses).

        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Dict with cash flow metrics
        """
        filtered = self._filter_by_date(start_date, end_date)

        income_txs = [
            tx for tx in filtered
            if tx.transaction_type == TransactionType.INCOME
        ]
        expense_txs = [
            tx for tx in filtered
            if tx.transaction_type == TransactionType.EXPENSE
        ]

        total_income = sum(tx.amount for tx in income_txs)
        total_expenses = sum(tx.amount for tx in expense_txs)
        net_cash_flow = total_income + total_expenses  # expenses are negative

        # Income breakdown
        income_by_source: dict[str, Decimal] = defaultdict(Decimal)
        for tx in income_txs:
            source = tx.merchant or tx.original_action
            income_by_source[source] += tx.amount

        return {
            "total_income": total_income,
            "total_expenses": total_expenses,
            "net_cash_flow": net_cash_flow,
            "savings_rate": (
                (net_cash_flow / total_income * 100)
                if total_income > 0 else Decimal("0")
            ),
            "income_count": len(income_txs),
            "expense_count": len(expense_txs),
            "income_by_source": dict(income_by_source),
        }

    def get_available_months(self) -> list[str]:
        """
        Get list of months with transactions.

        Returns:
            List of month strings (YYYY-MM) in chronological order
        """
        months = set()
        for tx in self.transactions:
            months.add(tx.date.strftime("%Y-%m"))
        return sorted(months)

    def get_uncategorized(self) -> list[ClassifiedTransaction]:
        """
        Get transactions that need categorization.

        Returns:
            List of uncategorized expense transactions
        """
        return [
            tx for tx in self.transactions
            if (tx.transaction_type == TransactionType.EXPENSE and
                tx.category == ExpenseCategory.UNCATEGORIZED)
        ]

    def _filter_by_date(
        self,
        start_date: Optional[date],
        end_date: Optional[date],
    ) -> list[ClassifiedTransaction]:
        """
        Filter transactions by date range.

        Args:
            start_date: Minimum date (inclusive)
            end_date: Maximum date (inclusive)

        Returns:
            Filtered transaction list
        """
        result = self.transactions

        if start_date:
            result = [tx for tx in result if tx.date >= start_date]

        if end_date:
            result = [tx for tx in result if tx.date <= end_date]

        return result


def format_monthly_summary(summary: MonthlyBudgetSummary) -> str:
    """
    Format monthly summary for terminal display.

    Args:
        summary: MonthlyBudgetSummary to format

    Returns:
        Formatted string for display
    """
    lines = []

    # Header
    lines.append("╭─────────────────────────────────────────────────────────╮")
    lines.append(f"│{summary.month:^57}│")
    lines.append(f"│{'Monthly Budget Summary':^57}│")
    lines.append("├─────────────────────────────────────────────────────────┤")

    # Main metrics
    lines.append(f"│  Income                           {summary.total_income:>18,.2f} │")
    lines.append(f"│  Expenses                         {summary.total_expenses:>18,.2f} │")
    lines.append(f"│  Margin Interest                  {summary.total_margin_cost:>18,.2f} │")
    lines.append("│─────────────────────────────────────────────────────────│")
    lines.append(f"│  Net Cash Flow                    {summary.net_cash_flow:>18,.2f} │")
    lines.append("├─────────────────────────────────────────────────────────┤")

    # Margin activity
    lines.append("│  Margin Activity                                        │")
    lines.append(f"│    Drawn:                         {summary.margin_drawn:>18,.2f} │")
    lines.append(f"│    Paid Down:                     {summary.margin_paid_down:>18,.2f} │")
    lines.append(f"│    Net Change:                    {summary.net_margin_change:>18,.2f} │")
    lines.append("╰─────────────────────────────────────────────────────────╯")

    # Category breakdown
    if summary.expenses_by_category:
        lines.append("")
        lines.append("Top Expense Categories:")

        # Sort by amount (most negative first)
        sorted_cats = sorted(
            summary.expenses_by_category.items(),
            key=lambda x: x[1],
        )

        total_exp = abs(summary.total_expenses) if summary.total_expenses else Decimal("1")

        for i, (category, amount) in enumerate(sorted_cats[:5], 1):
            pct = abs(amount) / total_exp * 100 if total_exp else 0
            lines.append(f"  {i}. {category:<20} {amount:>10,.2f}  ({pct:>5.1f}%)")

    # Top merchants
    if summary.top_merchants:
        lines.append("")
        lines.append("Top Merchants:")

        for i, (merchant, amount) in enumerate(summary.top_merchants[:5], 1):
            lines.append(f"  {i}. {merchant:<25} {amount:>10,.2f}")

    return "\n".join(lines)


def format_category_breakdown(categories: dict[str, Decimal]) -> str:
    """
    Format category breakdown for terminal display.

    Args:
        categories: Dict of category → amount

    Returns:
        Formatted string
    """
    lines = []
    lines.append("Expenses by Category")
    lines.append("=" * 50)

    total = sum(abs(v) for v in categories.values())

    for category, amount in categories.items():
        pct = abs(amount) / total * 100 if total else 0
        bar_len = int(pct / 2)
        bar = "█" * bar_len
        lines.append(f"{category:<20} {amount:>10,.2f} {bar} {pct:.1f}%")

    lines.append("=" * 50)
    lines.append(f"{'TOTAL':<20} {-total:>10,.2f}")

    return "\n".join(lines)


def format_merchant_ranking(
    merchants: list[tuple[str, Decimal, int]],
) -> str:
    """
    Format merchant ranking for terminal display.

    Args:
        merchants: List of (merchant, total, count) tuples

    Returns:
        Formatted string
    """
    lines = []
    lines.append("Top Merchants by Spending")
    lines.append("=" * 60)
    lines.append(f"{'Rank':<6}{'Merchant':<25}{'Total':>12}{'Count':>8}")
    lines.append("-" * 60)

    for i, (merchant, total, count) in enumerate(merchants, 1):
        lines.append(f"{i:<6}{merchant:<25}{total:>12,.2f}{count:>8}")

    return "\n".join(lines)


# Export all
__all__ = [
    "TransactionReporter",
    "format_monthly_summary",
    "format_category_breakdown",
    "format_merchant_ranking",
]
