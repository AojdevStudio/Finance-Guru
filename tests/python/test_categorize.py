"""Tests for SimpleFIN expense categorization.

Covers the patterns added 2026-08-04 after a spending review found 72% of
30-day debit volume landing in Uncategorized, and the ordering bug that sent
credit card payments to Loan Payment.
"""

import pytest

from src.integrations.simplefin.categorize import (
    BUSINESS_CATEGORIES,
    NON_SPEND_CATEGORIES,
    categorize_expense,
    is_business_account,
)


class TestBusinessPayroll:
    """A written check means employee payroll on a business account and
    something unknown on a household one. Confirmed by the account owner
    2026-08-04: the two $2,400 checks on Business Basic Checking (5468) are
    employee payroll, and were landing in Transfer and Uncategorized."""

    BIZ = "Business Basic Checking (5468)"
    PERSONAL = "360 Checking (6851)"

    @pytest.mark.parametrize("memo", ["Paid Check", "Cashed Check", "Check paid"])
    def test_check_on_business_account_is_payroll(self, memo: str) -> None:
        assert categorize_expense(memo, -2400.00, self.BIZ) == "Payroll"

    @pytest.mark.parametrize("memo", ["Paid Check", "Cashed Check"])
    def test_check_on_personal_account_is_not_payroll(self, memo: str) -> None:
        assert categorize_expense(memo, -2400.00, self.PERSONAL) != "Payroll"

    def test_missing_account_never_guesses_payroll(self) -> None:
        assert categorize_expense("Paid Check", -2400.00, None) != "Payroll"

    @pytest.mark.parametrize(
        "memo", ["Gusto payroll", "ADP Payroll Fees", "Paychex", "payroll run"]
    )
    def test_explicit_payroll_needs_no_account(self, memo: str) -> None:
        assert categorize_expense(memo, -2400.00, None) == "Payroll"

    @pytest.mark.parametrize(
        ("name", "expected"),
        [
            ("Business Basic Checking (5468)", True),
            ("Example Consulting Group LLC", True),
            ("Placeholder LLC Operating", True),
            ("360 Checking (6851)", False),
            ("Platinum Card® (1006)", False),
            (None, False),
        ],
    )
    def test_business_account_detection(self, name: str | None, expected: bool) -> None:
        assert is_business_account(name) is expected

    def test_env_hints_extend_business_detection(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Entity names are private, so operators add them via the environment.

        Without the env hint the account reads as personal, and a check on it is
        not payroll; with it, the same account and memo resolve to Payroll.
        """
        account = "Northwind Operating"
        assert is_business_account(account) is False
        assert categorize_expense("Paid Check", -2400.00, account) != "Payroll"

        monkeypatch.setenv("FG_BUSINESS_ACCOUNT_HINTS", "northwind, acme")
        assert is_business_account(account) is True
        assert is_business_account("ACME Holdings") is True
        assert categorize_expense("Paid Check", -2400.00, account) == "Payroll"

    def test_blank_env_hints_do_not_match_everything(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An empty or whitespace-only setting must not turn every account business."""
        monkeypatch.setenv("FG_BUSINESS_ACCOUNT_HINTS", " , ,")
        assert is_business_account("360 Checking (6851)") is False

    def test_payroll_is_a_business_category(self) -> None:
        assert "Payroll" in BUSINESS_CATEGORIES
        assert "Groceries" not in BUSINESS_CATEGORIES


class TestCardFees:
    """Annual card fees were falling through to Uncategorized."""

    @pytest.mark.parametrize(
        "memo",
        [
            "Membership Fee",
            "Annual Membership Fee",
            "Maintenance Charge",
            "Overdraft Charge",
            "Late Fee",
            "Interest Charge",
        ],
    )
    def test_fees_are_categorized(self, memo: str) -> None:
        assert categorize_expense(memo, -895.00) == "Fees & Interest"


class TestExemptions:
    """Sub-dollar and verification rows never reach the pattern table."""

    @pytest.mark.parametrize("amount", [0.0, 0.45, -0.99])
    def test_sub_dollar_amounts_are_exempt(self, amount: float) -> None:
        assert categorize_expense("H-E-B Curbside", amount) == "Exempt"

    @pytest.mark.parametrize(
        "text",
        ["Direct Debit Wells Fargo Ifacctverify", "micro verification deposit"],
    )
    def test_verification_rows_are_exempt(self, text: str) -> None:
        assert categorize_expense(text, -50.00) == "Exempt"

    def test_none_text_is_uncategorized(self) -> None:
        assert categorize_expense(None, -50.00) == "Uncategorized"


class TestTransfers:
    """Regression: own-account movement was inflating the expense review."""

    @pytest.mark.parametrize(
        "text",
        [
            "Transferred to Z Cash",
            "Transfer to brokerage",
            "DIRECT DEBIT BMOBNK CK WEBXTRANSFER",
            "Outgoing wire transfer",
        ],
    )
    def test_account_movement_is_a_transfer(self, text: str) -> None:
        assert categorize_expense(text, -900.00) == "Transfer"

    def test_taptap_send_still_matches(self) -> None:
        assert categorize_expense("TapTap Send US", -800.00) == "Transfer"


class TestCreditCardPayments:
    """Regression: 'credit card payment' lived in Loan Payment, which is
    matched first, so card payments were bucketed as loan repayment."""

    @pytest.mark.parametrize(
        "text",
        [
            "American Express Credit Card",
            "Direct Debit Chase Credit Cautopay Cash",
            "Apple Credit Card",
            "WF Credit Card auto pay",
            "Credit card payment",
        ],
    )
    def test_card_payments_are_credit_card_payment(self, text: str) -> None:
        assert categorize_expense(text, -9402.47) == "Credit Card Payment"

    def test_real_loans_still_route_to_loan_payment(self) -> None:
        assert categorize_expense("DIRECT DEBIT AES STDNT LOAN", -4169.25) == (
            "Loan Payment"
        )
        assert categorize_expense("TRUIST MORTG TEL MTGPMT", -1500.00) == (
            "Loan Payment"
        )

    def test_amex_travel_still_beats_card_payment(self) -> None:
        """Travel is matched before Credit Card Payment on purpose."""
        assert categorize_expense("American Express Travel", -813.44) == "Travel"


class TestNewCategories:
    def test_church_giving(self) -> None:
        assert categorize_expense("Anglicanchurchofpentx", -100.00) == "Giving"

    def test_interest_charge_is_a_fee(self) -> None:
        assert categorize_expense("Interest Charge", -267.86) == "Fees & Interest"

    def test_vehicle_registration_is_transport(self) -> None:
        assert (
            categorize_expense("State of Texas Vehicle Registration", -272.00)
            == "Auto & Transport"
        )

    def test_ai_tooling_is_a_business_expense(self) -> None:
        assert categorize_expense("Anthropic", -210.80) == "Business Expense"


class TestRawBankMemos:
    """The sync feeds payee + description joined. Raw bank memos are terse and
    abbreviated, so patterns must match those forms too, not just the clean
    payee name. Every case below is a real row that stayed Uncategorized until
    2026-08-04."""

    @pytest.mark.parametrize(
        ("payee", "description", "expected"),
        [
            (
                "American Express Credit Card",
                "DIRECT DEBIT AMEX EPAYMENT ACH PMT (Cash)",
                "Credit Card Payment",
            ),
            ("Transfer", "TRANSFER WITHDRAWAL To ....6851", "Transfer"),
            (
                "State of Texas Vehicle Registration",
                "BRAZORIA VEHREG 1302ANGLETON TX",
                "Auto & Transport",
            ),
        ],
    )
    def test_joined_payee_and_description(
        self, payee: str, description: str, expected: str
    ) -> None:
        assert categorize_expense(f"{payee} {description}", -500.00) == expected

    def test_raw_memo_alone_still_matches(self) -> None:
        """Even without the payee, the abbreviated memo must categorize."""
        assert categorize_expense("DIRECT DEBIT AMEX EPAYMENT ACH PMT", -9402.47) == (
            "Credit Card Payment"
        )
        assert categorize_expense("BRAZORIA VEHREG 1302ANGLETON TX", -272.00) == (
            "Auto & Transport"
        )


class TestNonSpendSet:
    """Expense totals must be able to exclude money movement."""

    def test_membership(self) -> None:
        assert "Transfer" in NON_SPEND_CATEGORIES
        assert "Credit Card Payment" in NON_SPEND_CATEGORIES
        assert "Groceries" not in NON_SPEND_CATEGORIES

    def test_double_count_case_is_excluded(self) -> None:
        """An Amex purchase and the Amex bill payment must not both count."""
        purchase = categorize_expense("Amazon", -329.83)
        bill = categorize_expense("American Express Credit Card", -9402.47)
        assert purchase not in NON_SPEND_CATEGORIES
        assert bill in NON_SPEND_CATEGORIES


class TestUnchangedBehaviour:
    """Existing patterns must keep working."""

    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("H-E-B CURBSIDE", "Groceries"),
            ("Starbucks", "Dining Out"),
            ("Tesla Supercharger", "Auto & Transport"),
            ("CVS Pharmacy", "Health & Wellness"),
            ("Amazon", "Shopping"),
            ("Brightwheel", "Family Care"),
            ("Netflix subscription", "Bills & Utilities"),
            ("ATM cash withdrawal", "Cash Withdrawal"),
        ],
    )
    def test_known_merchants(self, text: str, expected: str) -> None:
        assert categorize_expense(text, -50.00) == expected

    def test_unknown_merchant_stays_uncategorized(self) -> None:
        assert categorize_expense("Zzyzx Novelty Co", -50.00) == "Uncategorized"
