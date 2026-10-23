"""A positions generation becomes visible only after every account succeeds."""

import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import yaml

from src.integrations.snaptrade import sync_db
from src.integrations.snaptrade.client import SnapTradeAPIError, SnapTradeClientWrapper
from src.integrations.snaptrade.models import SnapTradeCredentials


def _snapshot(database: Path):
    with sqlite3.connect(database) as connection:
        return tuple(
            connection.execute(f"SELECT * FROM {table} ORDER BY account_id").fetchall()
            for table in ("positions", "balances")
        )


@pytest.fixture
def generation_store(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("FIN_GURU_DATA_ROOT", str(tmp_path))
    config = tmp_path / "snaptrade-accounts.yaml"
    config.write_text(
        yaml.safe_dump(
            {
                "accounts": [
                    {
                        "snaptrade_account_id": account,
                        "name": "Synthetic account",
                        "role": "taxable_margin",
                        "enabled": True,
                    }
                    for account in ("acct-first", "acct-second")
                ]
            }
        )
    )
    database = tmp_path / "family_office.db"
    with sqlite3.connect(database) as connection:
        connection.executescript(sync_db._SCHEMA)
        for account in ("acct-first", "acct-second"):
            connection.execute(
                "INSERT INTO positions VALUES (?,?,?,?,?,?,?)",
                (
                    account,
                    "ABC",
                    "equity",
                    1.0,
                    100.0,
                    100.0,
                    "2020-01-01T00:00:00+00:00",
                ),
            )
            connection.execute(
                "INSERT INTO balances VALUES (?,?,?,?,?,?,?,?)",
                (
                    account,
                    "USD",
                    0.0,
                    0.0,
                    100.0,
                    100.0,
                    0.0,
                    "2020-01-01T00:00:00+00:00",
                ),
            )
    sdk = MagicMock()
    sdk.account_information.get_all_account_positions.return_value = {
        "results": [
            {
                "instrument": {"kind": "stock", "symbol": "ABC"},
                "units": 2.0,
                "price": 100.0,
                "cost_basis": 100.0,
            }
        ]
    }
    sdk.account_information.get_user_account_balance.return_value = [
        {"currency": {"code": "USD"}, "cash": 0.0, "buying_power": 0.0}
    ]
    sdk.account_information.get_user_account_details.return_value = {
        "balance": {"total": {"amount": 200.0}},
        "sync_status": {
            "holdings": {"last_successful_sync": datetime.now(UTC).isoformat()}
        },
    }
    client = SnapTradeClientWrapper(
        SnapTradeCredentials(
            client_id="synthetic-client",
            consumer_key="synthetic-consumer",
            user_id="synthetic-owner",
            user_secret="synthetic-secret",
        ),
        sdk_client=sdk,
    )
    monkeypatch.setattr(
        SnapTradeClientWrapper, "from_env", classmethod(lambda cls: client)
    )
    return config, database, sdk


@pytest.mark.parametrize("failure", ["provider", "write"])
def test_failed_account_preserves_complete_generation(generation_store, failure):
    config, database, sdk = generation_store
    before = _snapshot(database)
    if failure == "provider":
        positions = sdk.account_information.get_all_account_positions.return_value

        def fetch_positions(*, account_id, **kwargs):
            if account_id == "acct-second":
                raise RuntimeError("synthetic provider failure")
            return positions

        sdk.account_information.get_all_account_positions.side_effect = fetch_positions
        error = SnapTradeAPIError
    else:
        with sqlite3.connect(database) as connection:
            connection.executescript("""
                CREATE TRIGGER reject_second BEFORE INSERT ON balances
                WHEN NEW.account_id = 'acct-second'
                BEGIN SELECT RAISE(ABORT, 'synthetic write failure'); END;
            """)
        error = sqlite3.IntegrityError

    with pytest.raises(error):
        sync_db.sync(config, str(database))

    assert _snapshot(database) == before


def test_reader_sees_complete_generation_during_sync(generation_store):
    config, database, sdk = generation_store
    before = _snapshot(database)
    positions = sdk.account_information.get_all_account_positions.return_value
    observations = []

    def fetch_positions(*, account_id, **kwargs):
        if account_id == "acct-second":
            with sqlite3.connect(database, timeout=0) as writer:
                writer.execute("BEGIN IMMEDIATE")
                writer.rollback()
            observations.append(_snapshot(database))
        return positions

    sdk.account_information.get_all_account_positions.side_effect = fetch_positions

    summary = sync_db.sync(config, str(database))

    assert observations and all(snapshot == before for snapshot in observations)
    current_positions, current_balances = _snapshot(database)
    assert (
        len(current_positions) == len(current_balances) == len(summary["accounts"]) == 2
    )
    assert {row[-1] for row in current_positions + current_balances} == {
        summary["synced_at"]
    }
    assert {row[3] for row in current_positions} == {2.0}


def test_same_second_syncs_remain_distinct_generations(
    generation_store, monkeypatch, capsys
):
    config, database, _ = generation_store
    times = iter(
        [
            datetime(2026, 10, 22, 12, 0, 0, 100000, tzinfo=UTC),
            datetime(2026, 10, 22, 12, 0, 0, 900000, tzinfo=UTC),
        ]
    )

    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return next(times)

    monkeypatch.setattr(sync_db, "datetime", Clock)

    first = sync_db.sync(config, str(database))
    routing = yaml.safe_load(config.read_text())
    routing["accounts"][1]["enabled"] = False
    config.write_text(yaml.safe_dump(routing))
    second = sync_db.sync(config, str(database))
    sync_db.show(str(database))

    output = capsys.readouterr().out
    assert "[acct-first]" in output and "[acct-second]" not in output
    assert first["synced_at"] != second["synced_at"]
