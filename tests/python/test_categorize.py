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
    2026-08-04: the two $2,400 checks on Business Basic Checking (1111) are
    employee payroll, and were landing in Transfer and Uncategorized."""

    BIZ = "Business Basic Checking (1111)"
    PERSONAL = "360 Checking (2222)"

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
            ("Business Basic Checking (1111)", True),
            ("Example Consulting Group LLC", True),
            ("Placeholder LLC Operating", True),
            ("360 Checking (2222)", False),
            ("Platinum Card® (3333)", False),
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
        assert is_business_account("360 Checking (2222)") is False

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
            ("Transfer", "TRANSFER WITHDRAWAL To ....2222", "Transfer"),
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


class TestSubstringCollisions:
    """Three short patterns were matching inside longer, unrelated words and
    silently misfiling real money. Found 2026-09-08 while reviewing the
    categorized feed with the account owner."""

    @pytest.mark.parametrize(
        "memo",
        [
            "PURCHASE INTO CORE ACCOUNT FIDELITY GOVERNMENT MONEY MARKET (SPAXX) (Cash)",
            "REDEMPTION FROM CORE ACCOUNT FIDELITY GOVERNMENT MONEY MARKET (SPAXX) MORNING TRADE (Cash)",
        ],
    )
    def test_spaxx_sweep_is_exempt_not_personal_care(self, memo: str) -> None:
        """ "SPAXX" contains "spa", so every core sweep was booked as a spa visit."""
        assert categorize_expense(memo, 7716.47, "Cash Management (4444)") == "Exempt"

    def test_real_spa_still_reaches_personal_care(self) -> None:
        assert categorize_expense("SERENITY DAY SPA", -120.00, None) == "Personal Care"

    def test_store_purchase_is_not_a_card_payment(self) -> None:
        """SimpleFIN normalizes the payee to "Macy's Credit Card" for a purchase
        at the Macy's store. The old bare "credit card" pattern read that as a
        bill payment, which excluded a real purchase from spend totals."""
        assert (
            categorize_expense(
                "Macy's Credit Card MACYS PEARLAND TWN CTR",
                -255.42,
                "Sapphire Preferred (3333)",
            )
            == "Shopping"
        )

    def test_actual_card_payment_still_classified(self) -> None:
        assert (
            categorize_expense("Chase Credit Card CHASE CREDIT CRD", -38.19, None)
            == "Credit Card Payment"
        )

    def test_food_delivery_is_dining_not_rideshare(self) -> None:
        """ "Uber Eats" contains "uber"; Auto & Transport was claiming it."""
        assert categorize_expense("Uber Eats", -1.84, None) == "Dining Out"
        assert categorize_expense("Uber", -36.94, None) == "Auto & Transport"


class TestCardPaymentCreditLeg:
    """A bill payment posts twice: a debit on the funding account and a credit
    on the card. Only the debit was recognized, so the credit leg landed in
    Uncategorized and inflated any income total summed from credits."""

    @pytest.mark.parametrize(
        "memo",
        [
            "Payment Thank You - Web",
            "AUTOMATIC PAYMENT - THANK YOU",
            "ONLINE PAYMENT - THANK YOU",
            "AUTOPAY PAYMENT - THANK YOU",
        ],
    )
    def test_thank_you_credit_is_a_card_payment(self, memo: str) -> None:
        assert categorize_expense(memo, 20009.65, "Platinum Card® (3333)") == (
            "Credit Card Payment"
        )

    def test_card_payment_is_excluded_from_spend(self) -> None:
        assert "Credit Card Payment" in NON_SPEND_CATEGORIES


class TestBusinessIncome:
    """Consulting revenue had no category. The payer's name is private data and
    stays out of the repository, so the account carries the signal instead."""

    BIZ = "Business Basic Checking (1111)"
    PERSONAL = "360 Checking (2222)"

    def test_unmatched_credit_on_business_account_is_income(self) -> None:
        assert categorize_expense("CGSOPERATING", 12320.00, self.BIZ) == (
            "Business Income"
        )

    def test_unmatched_credit_on_personal_account_is_not_income(self) -> None:
        assert categorize_expense("SOME MERCHANT", 12320.00, self.PERSONAL) == (
            "Uncategorized"
        )

    def test_debit_on_business_account_is_never_income(self) -> None:
        assert (
            categorize_expense("SOME MERCHANT", -500.00, self.BIZ) != "Business Income"
        )

    def test_explicit_transfer_beats_the_income_fallback(self) -> None:
        """An inter-account move funded from the owner's other business account
        is not revenue, and the Transfer pattern must claim it first."""
        assert categorize_expense(
            "TRANSFER DEPOSIT FROM ...1111", 1000.00, self.BIZ
        ) == ("Transfer")

    def test_business_income_excluded_from_household(self) -> None:
        assert "Business Income" in BUSINESS_CATEGORIES


class TestEntertainment:
    """Recreation had no category and was scattered across Uncategorized."""

    @pytest.mark.parametrize(
        ("memo", "expected"),
        [
            ("PlayStation Network", "Entertainment"),
            ("CE ANDRETTIS", "Entertainment"),
            ("Bounce", "Entertainment"),
            # The account owner classified the PGA Frisco charge as a business
            # trip on 2026-09-08, so it belongs to the business bucket.
            ("PGA FRISCO FRONT", "Business Expense"),
        ],
    )
    def test_recreation_patterns(self, memo: str, expected: str) -> None:
        assert categorize_expense(memo, -292.24, None) == expected

    def test_bounced_check_fee_is_not_entertainment(self) -> None:
        """ "bounce" sits after the fee patterns for exactly this reason."""
        assert categorize_expense("OVERDRAFT ITEM FEE", -35.00, None) == (
            "Fees & Interest"
        )


class TestSpaPatternFallout:
    """Removing the bare "spa" pattern is only safe if every merchant it had
    been capturing gets an explicit pattern of its own."""

    @pytest.mark.parametrize(
        ("memo", "account", "expected"),
        [
            (
                "GOOGLE  WORKSPACE UNIF",
                "Business Basic Checking (1111)",
                "Business Expense",
            ),
            (
                "LIVING SPACES MOBILE",
                "Sapphire Preferred (3333)",
                "Home & Garden",
            ),
            ("CLOUD 9 SPA PEARLAND", "Rewards Card (5555)", "Personal Care"),
        ],
    )
    def test_merchants_the_spa_pattern_had_captured(
        self, memo: str, account: str, expected: str
    ) -> None:
        """Removing the bare "spa" pattern must not drop these into
        Uncategorized: each one needs its own explicit pattern."""
        assert categorize_expense(memo, -202.75, account) == expected

    def test_inbound_transfer_is_not_business_income(self) -> None:
        """ "Instant Transfer Received From ...." does not contain "transfer
        from", so it slipped past Transfer into the income fallback."""
        assert (
            categorize_expense(
                "Instant Transfer Received From ....0000",
                1000.00,
                "Business Basic Checking (1111)",
            )
            == "Transfer"
        )
