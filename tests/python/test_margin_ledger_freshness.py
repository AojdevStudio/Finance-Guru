"""Reject obsolete margin balance generations using synthetic local ledgers."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime

import pytest

from src.analysis import margin_metrics as mm

NOW = datetime(2026, 1, 2, 12, tzinfo=UTC)


@pytest.fixture
def margin_ledger(tmp_path, monkeypatch):
    class FixedDatetime(datetime):
        @classmethod
        def now(cls, tz):
            return NOW.astimezone(tz)

    monkeypatch.setattr(mm, "datetime", FixedDatetime)
    monkeypatch.setenv("FIN_GURU_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'family_office.db'}")
    (tmp_path / "snaptrade-accounts.yaml").write_text(
        json.dumps(
            {
                "generated_at": "2026-01-01T00:00:00Z",
                "accounts": [
                    {
                        "snaptrade_account_id": "synthetic-margin",
                        "role": "taxable_margin",
                        "enabled": True,
                    }
                ],
            }
        )
    )
    with sqlite3.connect(tmp_path / "family_office.db") as connection:
        connection.execute(
            "CREATE TABLE balances (account_id TEXT PRIMARY KEY, currency TEXT, "
            "buying_power REAL, account_equity REAL, margin_debt REAL, synced_at TEXT)"
        )
        connection.execute(
            "INSERT INTO balances VALUES ('synthetic-margin', 'USD', 50000, "
            "100000, 10000, '2001-01-01T00:00:00Z')"
        )
    return tmp_path / "family_office.db"


@pytest.mark.parametrize(
    "synced_at",
    [
        "2001-01-01T00:00:00Z",
        "2026-01-01T11:59:59.999999Z",
        "2026-01-02T12:05:00.000001Z",
        "2026-01-02T12:00:00",
        "not-a-timestamp",
        "2026-01-01T13:00:00+02:00",
    ],
    ids=[
        "old-ledger",
        "past-age-limit",
        "future",
        "missing-timezone",
        "malformed",
        "stale-in-utc",
    ],
)
def test_margin_ledger_refuses_stale_or_unverifiable_generation(
    margin_ledger, synced_at
):
    with sqlite3.connect(margin_ledger) as connection:
        connection.execute("UPDATE balances SET synced_at = ?", (synced_at,))

    with pytest.raises(mm.StaleBalanceSnapshotError, match="sync-first refresh"):
        mm.read_db_balances()


@pytest.mark.parametrize(
    "synced_at",
    [
        "2026-01-01T12:00:00Z",
        "2026-01-02T12:05:00Z",
        "2026-01-01T07:00:00-05:00",
    ],
    ids=["age-limit", "clock-skew-limit", "equivalent-offset"],
)
def test_margin_ledger_accepts_fresh_generation_and_boundary(margin_ledger, synced_at):
    with sqlite3.connect(margin_ledger) as connection:
        connection.execute("UPDATE balances SET synced_at = ?", (synced_at,))

    balances = mm.read_db_balances()

    assert balances.total_account_value == 100000
    assert balances.margin_debt == 10000
    assert balances.margin_buying_power == 50000


def test_margin_cli_refuses_wholly_stale_ledger(margin_ledger, monkeypatch, capsys):
    monkeypatch.setenv("FG_MARGIN_JUMP_ALERT_THRESHOLD", "5000")

    with pytest.raises(mm.StaleBalanceSnapshotError, match="sync-first refresh"):
        mm.main(["--annual-rate", "0.12"])

    assert capsys.readouterr().out == ""
