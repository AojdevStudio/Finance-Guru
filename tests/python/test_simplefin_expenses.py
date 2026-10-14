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
                    "description": "H-E-B #063 ANYTOWN TX",
                    "amount": "12.34",
                },
            ],
        }
    ]
}


@pytest.mark.parametrize(
    ("text", "amount", "expected"),
    [
        pytest.param("H-E-B #063 ANYTOWN TX", None, "Groceries", id="heb"),
        pytest.param("CHUCK E CHEESE 578", None, "Dining Out", id="chuck-e-cheese"),
        pytest.param("Tesla SUPERCHA 123", None, "Auto & Transport", id="supercharger"),
        pytest.param("OPENAI *CHATGPT SUBSCR", None, "Business Expense", id="openai"),
        pytest.param("aMaZoN marketplace", None, "Shopping", id="mixed-case"),
        pytest.param("MERCHANT STARBUCKS123", None, "Dining Out", id="substring"),
        pytest.param("anything", -0.50, "Exempt", id="sub-dollar"),
        pytest.param("WELLS FARGO IFACCTVERIFY", None, "Exempt", id="verification"),
        pytest.param("ZZZ UNKNOWN MERCHANT", None, "Uncategorized", id="unknown"),
        pytest.param(None, None, "Uncategorized", id="no-text"),
    ],
)
def test_categorize_expense_patterns_and_exemptions(
    text: str | None, amount: float | None, expected: str
) -> None:
    assert categorize_expense(text, amount) == expected


@pytest.mark.parametrize(
    ("text", "amount", "expected"),
    [
        pytest.param(
            "DIRECT DEPOSIT ACME STAFFINGDIR DEP (Cash)",
            -1428.61,
            "credit",
            id="negative-dir-dep",
        ),
        pytest.param(
            "DIRECT DEPOSIT Ridgeline SerPAYROLL (Cash)",
            -2300.00,
            "credit",
            id="negative-payroll",
        ),
        pytest.param(
            "DIRECT DEBIT AMEX EPAYMENT ACH PMT (Cash)",
            -9402.47,
            "debit",
            id="direct-debit",
        ),
        pytest.param(
            "DIRECT DEBIT CHASE CREDIT CAUTOPAY", 600.00, "debit", id="positive-debit"
        ),
        pytest.param("H-E-B #063 ANYTOWN TX", -54.13, "debit", id="sign-negative"),
        pytest.param("Capital One", 2000.00, "credit", id="sign-positive"),
        pytest.param(None, None, "credit", id="nothing-known"),
    ],
)
def test_resolve_direction_prefers_feed_wording_over_sign(
    text: str | None, amount: float | None, expected: str
) -> None:
    """Fidelity's CMA reports inbound payroll negative, so wording must win."""
    assert resolve_direction(text, amount) == expected


@pytest.mark.parametrize(
    ("description", "expected_direction", "expected_amount"),
    [
        pytest.param(
            "DIRECT DEPOSIT ACME STAFFINGDIR DEP (Cash)",
            "credit",
            1428.61,
            id="deposit",
        ),
        pytest.param("DIRECT DEBIT AMEX EPAYMENT", "debit", -1428.61, id="withdrawal"),
    ],
)
def test_normalize_transaction_signs_amount_to_match_direction(
    description: str, expected_direction: str, expected_amount: float
) -> None:
    account = {"id": "ACT-cma", "name": "Cash Management", "org": {"name": "Fidelity"}}
    txn = {
        "id": "TXN-1",
        "posted": 1704067200,
        "payee": None,
        "description": description,
        "amount": "-1428.61",
    }
    row = normalize_transaction(account, txn, "2026-07-31T00:00:00Z")
    amount, direction = row[8], row[9]
    assert direction == expected_direction
    assert amount == expected_amount


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


@pytest.mark.parametrize(
    ("text", "amount", "expected"),
    [
        pytest.param(
            "CASH ADVANCE *LAKESIDE ANYTOWN TX 081826 AUTHID:624330 (Cash)",
            654.00,
            "debit",
            id="cash-advance",
        ),
        pytest.param(
            "DEBIT CARD PURCHASE GUMROAD* SHAWN GRADY GUMROAD.COM NY 082226",
            21.60,
            "debit",
            id="card-purchase",
        ),
        pytest.param(
            "DEBIT CARD PURCHASE CASH APP*FIRST CHURCH cash.app TX 082726",
            20.00,
            "debit",
            id="card-purchase-cash-app",
        ),
        pytest.param(
            "TRANSFERRED FROM VS ZXX-XXX752-1 (Cash)",
            -650.00,
            "credit",
            id="transferred-from",
        ),
        pytest.param(
            "TRANSFERRED TO VS ZXX-XXX592-1 (Cash)",
            -650.00,
            "debit",
            id="transferred-to",
        ),
        pytest.param(
            "TRANSFER WITHDRAWAL To ....2222 (Cash)",
            650.00,
            "debit",
            id="transfer-withdrawal",
        ),
        pytest.param(
            "DIRECT DEBIT CHASE CREDIT CAUTOPAYBUS (Cash)",
            -477.33,
            "debit",
            id="direct-debit",
        ),
    ],
)
def test_resolve_direction_handles_fidelity_card_and_transfer_wording(
    text: str, amount: float, expected: str
) -> None:
    """Fidelity's sign is unreliable in BOTH directions, so wording must win.

    Every case is a real row from the Fidelity brokerage feed whose SimpleFIN
    sign contradicts the authoritative SnapTrade `transactions` row for the same
    transaction (verified 2026-08-31).
    """
    assert resolve_direction(text, amount) == expected


def test_retirement_account_activity_is_not_household_spending() -> None:
    """401(k) contributions are savings, not consumption.

    The 401(k) feed reports biweekly contributions as debits with the bare
    memo "contribution", which the text table reads as Uncategorized and books
    as household spend. Verified 2026-08-31: $307.70 of phantom August spend.
    The account name is the only reliable signal, since "contribution" alone is
    too generic to match on (a charitable contribution is real spending).
    """
    retirement = "EXAMPLE EMPLOYER 401(K) RETIREMENT PLAN"
    assert categorize_expense("contribution", -120.00, retirement) == "Retirement"
    assert categorize_expense("contribution", -30.00, retirement) == "Retirement"
    assert categorize_expense("dividend", 8.00, retirement) == "Retirement"
    assert "Retirement" in NON_SPEND_CATEGORIES
    assert (
        categorize_expense("CONTRIBUTION TO CHURCH", -100.00, "Platinum Card® (3333)")
        != "Retirement"
    )


@pytest.mark.parametrize(
    ("memo", "amount", "expected"),
    [
        pytest.param(
            "DIRECT DEPOSIT ACME STAFFINGDIR DEP (Cash)",
            2200.00,
            "Payroll",
            id="dir-dep",
        ),
        pytest.param(
            "DIRECT DEPOSIT Ridgeline SerACH (Cash)", 2300.00, "Payroll", id="ach"
        ),
        pytest.param(
            "DIRECT DEPOSIT NORTHFIELD COLLPAYROLL (Cash)",
            2400.00,
            "Payroll",
            id="payroll",
        ),
        pytest.param(
            "DIRECT DEPOSIT WELLS FARGO ACCTVERIFY",
            0.25,
            "Exempt",
            id="verification-deposit",
        ),
    ],
)
def test_inbound_direct_deposits_are_payroll_regardless_of_employer_memo(
    memo: str, amount: float, expected: str
) -> None:
    """Employers vary the memo suffix; the deposit is payroll either way.

    Verified 2026-08-31 against a real feed: payers whose memo ends in "PAYROLL"
    tagged correctly, while payers ending in "DIR DEP" or a plain "ACH" variant
    fell through to Uncategorized, leaving a large share of income untagged. The
    verification micro-deposits must stay Exempt.

    Employer names and amounts are placeholders; the memo SHAPE is what is
    under test, and real payer names do not belong in a public repository.
    """
    cma = "Cash Management (Joint WROS) (0001)"
    assert categorize_expense(memo, amount, cma) == expected


def test_sync_applies_household_merchant_rules(tmp_path) -> None:
    """A merchant known only to merchant-rules.yaml reaches the database with
    its household category; without the file it stays Uncategorized."""
    rules = tmp_path / "merchant-rules.yaml"
    rules.write_text("Family Care:\n  - little sprouts\n", encoding="utf-8")
    database_url = f"sqlite:///{tmp_path / 'fo.db'}"

    def fake_dump(months: int, app_dir) -> dict:
        return {
            "accounts": [
                {
                    "id": "acct-1",
                    "name": "Rewards Card (5555)",
                    "org": {"name": "Any Bank"},
                    "transactions": [
                        {
                            "id": "t1",
                            "posted": 1755000000,
                            "amount": "-40.00",
                            "payee": "Little Sprouts",
                            "description": "LITTLE SPROUTS ANYTOWN TX",
                        }
                    ],
                }
            ]
        }

    sync(database_url, dump_provider=fake_dump)
    conn = sqlite3.connect(tmp_path / "fo.db")
    assert conn.execute("SELECT category FROM bank_transactions").fetchone() == (
        "Uncategorized",
    )
    sync(database_url, dump_provider=fake_dump, merchant_rules=rules)
    assert conn.execute("SELECT category FROM bank_transactions").fetchone() == (
        "Family Care",
    )
