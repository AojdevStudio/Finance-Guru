import sqlite3
from copy import deepcopy

from src.integrations.simplefin.categorize import categorize_expense
from src.integrations.simplefin.sync_expenses_db import (
    normalize_transaction,
    resolve_direction,
    sync,
)

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
        resolve_direction("DIRECT DEPOSIT APEX SYSTEMSDIR DEP (Cash)", -1428.61)
        == "credit"
    )
    assert (
        resolve_direction("DIRECT DEPOSIT Actalent SerPAYROLL (Cash)", -2273.03)
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
        "description": "DIRECT DEPOSIT APEX SYSTEMSDIR DEP (Cash)",
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
