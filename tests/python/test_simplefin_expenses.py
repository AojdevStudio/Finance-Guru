import sqlite3
from copy import deepcopy
from pathlib import Path

import pytest

from src.integrations.simplefin import sync_expenses_db
from src.integrations.simplefin.categorize import (
    NON_SPEND_CATEGORIES,
    categorize_expense,
)
from src.integrations.simplefin.sync_expenses_db import (
    SimpleFinSyncError,
    normalize_transaction,
    resolve_direction,
    sync,
)


def test_default_app_dir_is_checkout_owned(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    repo_root = Path(sync_expenses_db.__file__).resolve().parents[3]
    expected_app_dir = repo_root / "apps" / "simplefin-sync"

    assert expected_app_dir == sync_expenses_db.DEFAULT_APP_DIR
    assert sync_expenses_db.DEFAULT_APP_DIR.is_absolute()


SFIN_ACCOUNT_SET = {
    "accounts": [
        {
            "id": "ACT-x",
            "name": "Household Checking",
            "org": {"name": "Example Bank"},
            "transactions": [
                {
                    "id": "TXN-debit",
                    "posted": 1704067200,
                    "payee": "OpenAI",
                    "description": "OPENAI *CHATGPT SUBSCR",
                    "amount": "-20.00",
                },
                {
                    "id": "TXN-pending",
                    "posted": 0,
                    "payee": "H-E-B",
                    "description": "H-E-B #063 PEARLAND TX",
                    "amount": "12.34",
                },
            ],
        }
    ]
}


def test_categorize_expense_patterns_and_exemptions() -> None:
    assert categorize_expense("H-E-B #063 PEARLAND TX") == "Groceries"
    assert categorize_expense("CHUCK E CHEESE 578") == "Dining Out"
    assert categorize_expense("Tesla SUPERCHA 123") == "Auto & Transport"
    assert categorize_expense("OPENAI *CHATGPT SUBSCR") == "Business Expense"
    assert categorize_expense("aMaZoN marketplace") == "Shopping"
    assert categorize_expense("MERCHANT STARBUCKS123") == "Dining Out"
    assert categorize_expense("anything", -0.50) == "Exempt"
    assert categorize_expense("WELLS FARGO IFACCTVERIFY") == "Exempt"
    assert categorize_expense("ZZZ UNKNOWN MERCHANT") == "Uncategorized"
    assert categorize_expense(None) == "Uncategorized"


def test_resolve_direction_prefers_feed_wording_over_sign() -> None:
    # Fidelity's CMA reports inbound payroll negative; wording must win.
    assert (
        resolve_direction("DIRECT DEPOSIT ACME STAFFINGDIR DEP (Cash)", -1428.61)
        == "credit"
    )
    assert (
        resolve_direction("DIRECT DEPOSIT Ridgeline SerPAYROLL (Cash)", -2273.03)
        == "credit"
    )
    assert (
        resolve_direction("DIRECT DEBIT AMEX EPAYMENT ACH PMT (Cash)", -9402.47)
        == "debit"
    )
    # A debit marker with an unexpectedly positive amount still reads as outflow.
    assert resolve_direction("DIRECT DEBIT CHASE CREDIT CAUTOPAY", 600.00) == "debit"
    # No marker falls back to sign.
    assert resolve_direction("H-E-B #063 PEARLAND TX", -54.13) == "debit"
    assert resolve_direction("Capital One", 2000.00) == "credit"
    assert resolve_direction(None, None) == "credit"


def test_normalize_transaction_signs_amount_to_match_direction() -> None:
    account = {"id": "ACT-cma", "name": "Cash Management", "org": {"name": "Fidelity"}}
    deposit = {
        "id": "TXN-payroll",
        "posted": 1704067200,
        "payee": None,
        "description": "DIRECT DEPOSIT ACME STAFFINGDIR DEP (Cash)",
        "amount": "-1428.61",
    }
    row = normalize_transaction(account, deposit, "2026-07-31T00:00:00Z")
    amount, direction = row[8], row[9]
    assert direction == "credit"
    assert amount == 1428.61

    withdrawal = dict(deposit, id="TXN-amex", description="DIRECT DEBIT AMEX EPAYMENT")
    row = normalize_transaction(account, withdrawal, "2026-07-31T00:00:00Z")
    assert row[9] == "debit"
    assert row[8] == -1428.61


def test_sync_inserts_updates_and_promotes_pending_transaction(tmp_path) -> None:
    database_url = f"sqlite:///{tmp_path}/t.db"
    fixture = deepcopy(SFIN_ACCOUNT_SET)

    def fake_dump(months, app_dir):
        return fixture

    first = sync(database_url, dump_provider=fake_dump)
    assert first["inserted"] == 2
    assert first["updated"] == 0

    with sqlite3.connect(tmp_path / "t.db") as conn:
        rows = conn.execute(
            "SELECT txn_id, direction, amount, date, category "
            "FROM bank_transactions ORDER BY txn_id"
        ).fetchall()
    assert rows == [
        ("TXN-debit", "debit", -20.0, "2024-01-01", "Business Expense"),
        ("TXN-pending", "credit", 12.34, None, "Groceries"),
    ]

    second = sync(database_url, dump_provider=fake_dump)
    assert second["inserted"] == 0
    assert second["updated"] == 2

    fixture = deepcopy(SFIN_ACCOUNT_SET)
    fixture["accounts"][0]["transactions"][1]["posted"] = 1704153600
    third = sync(database_url, dump_provider=fake_dump)
    assert third["inserted"] == 0
    assert third["updated"] == 2

    with sqlite3.connect(tmp_path / "t.db") as conn:
        pending_date = conn.execute(
            "SELECT date FROM bank_transactions WHERE txn_id = 'TXN-pending'"
        ).fetchone()[0]
        count = conn.execute("SELECT COUNT(*) FROM bank_transactions").fetchone()[0]
    assert pending_date == "2024-01-02"
    assert count == 2


def test_sync_rejects_partial_failure_payload_before_writing(tmp_path) -> None:
    database_url = f"sqlite:///{tmp_path}/t.db"
    payload = {
        "errors": [
            {
                "code": "act.failed",
                "msg": "Account temporarily unavailable",
                "account_id": "ACT-failed",
            }
        ],
        "errlist": ["Connection refresh failed"],
        "accounts": deepcopy(SFIN_ACCOUNT_SET["accounts"]),
    }

    def fake_dump(months, app_dir):
        return payload

    with pytest.raises(SimpleFinSyncError, match="2 partial account error"):
        sync(database_url, dump_provider=fake_dump)

    assert not (tmp_path / "t.db").exists()


def test_resolve_direction_handles_fidelity_card_and_transfer_wording() -> None:
    """Fidelity's sign is unreliable in BOTH directions, so wording must win.

    Every case below is a real row from the Fidelity brokerage feed whose
    SimpleFIN sign contradicts the authoritative SnapTrade `transactions` row
    for the same transaction (verified 2026-08-31).
    """
    # Outflows the feed reported as positive.
    assert (
        resolve_direction(
            "CASH ADVANCE *SEDONA LAKES MANVEL TX 081826 AUTHID:624330 (Cash)", 654.00
        )
        == "debit"
    )
    assert (
        resolve_direction(
            "DEBIT CARD PURCHASE GUMROAD* SHAWN GRADY GUMROAD.COM NY 082226", 21.60
        )
        == "debit"
    )
    assert (
        resolve_direction(
            "DEBIT CARD PURCHASE CASH APP*ANGLICAN CHUR cash.app TX 082726", 20.00
        )
        == "debit"
    )
    # An inflow the feed reported as negative: SnapTrade books it CONTRIBUTION +650.
    assert (
        resolve_direction("TRANSFERRED FROM VS ZXX-XXX752-1 (Cash)", -650.00)
        == "credit"
    )
    # The outbound leg on the CMA side stays an outflow.
    assert (
        resolve_direction("TRANSFERRED TO VS ZXX-XXX592-1 (Cash)", -650.00) == "debit"
    )
    # An outbound transfer's own wording is a debit even when signed positive.
    assert (
        resolve_direction("TRANSFER WITHDRAWAL To ....2222 (Cash)", 650.00) == "debit"
    )
    # "direct debit" must still win over the newer, less specific markers.
    assert (
        resolve_direction("DIRECT DEBIT CHASE CREDIT CAUTOPAYBUS (Cash)", -477.33)
        == "debit"
    )


def test_retirement_account_activity_is_not_household_spending() -> None:
    """401(k) contributions are savings, not consumption.

    The 401(k) feed reports biweekly contributions as debits with the bare
    memo "contribution", which the text table reads as Uncategorized and books
    as household spend. Verified 2026-08-31: $307.70 of phantom August spend.
    The account name is the only reliable signal, since "contribution" alone is
    too generic to match on (a charitable contribution is real spending).
    """
    retirement = "EXAMPLE EMPLOYER 401(K) RETIREMENT PLAN"
    assert categorize_expense("contribution", -123.08, retirement) == "Retirement"
    assert categorize_expense("contribution", -30.77, retirement) == "Retirement"
    assert categorize_expense("dividend", 7.84, retirement) == "Retirement"
    # Retirement must be excluded from household spending totals.
    assert "Retirement" in NON_SPEND_CATEGORIES
    # A contribution on a normal account is still ordinary spending, not Retirement.
    assert (
        categorize_expense("CONTRIBUTION TO CHURCH", -100.00, "Platinum Card® (3333)")
        != "Retirement"
    )


def test_inbound_direct_deposits_are_payroll_regardless_of_employer_memo() -> None:
    """Employers vary the memo suffix; the deposit is payroll either way.

    Verified 2026-08-31 against a real feed: payers whose memo ends in "PAYROLL"
    tagged correctly, while payers ending in "DIR DEP" or a plain "ACH" variant
    fell through to Uncategorized, leaving a large share of income untagged. The
    verification micro-deposits must stay Exempt.

    Employer names and amounts below are placeholders; the memo SHAPE is what is
    under test, and real payer names do not belong in a public repository.
    """
    cma = "Cash Management (Joint WROS) (0001)"
    assert (
        categorize_expense("DIRECT DEPOSIT ACME STAFFINGDIR DEP (Cash)", 2207.38, cma)
        == "Payroll"
    )
    assert (
        categorize_expense("DIRECT DEPOSIT Ridgeline SerACH (Cash)", 2273.03, cma)
        == "Payroll"
    )
    # Already-working variants must not regress.
    assert (
        categorize_expense("DIRECT DEPOSIT NORTHFIELD COLLPAYROLL (Cash)", 2431.51, cma)
        == "Payroll"
    )
    # Sub-dollar bank verification deposits stay Exempt, not payroll.
    assert (
        categorize_expense("DIRECT DEPOSIT WELLS FARGO ACCTVERIFY", 0.29, cma)
        == "Exempt"
    )
