"""Tests for the instance data-root model."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest

from src.analysis.margin_metrics import FidelityBalances
from src.analysis.margin_metrics_cli import main as margin_metrics_main
from src.config import InstancePaths
from src.config.instance_paths import _db_path, load_instance_env
from src.integrations import refresh_all


def test_default_root_is_current_working_directory(tmp_path: Path) -> None:
    paths = InstancePaths.resolve(env={}, cwd=tmp_path)

    assert paths.root == tmp_path.resolve()


def test_data_root_environment_variable_wins(tmp_path: Path) -> None:
    cwd = tmp_path / "cwd"
    root = tmp_path / "instance"

    paths = InstancePaths.resolve(
        env={"FIN_GURU_DATA_ROOT": str(root)},
        cwd=cwd,
    )

    assert paths.root == root.resolve()


def test_relative_data_root_becomes_absolute(tmp_path: Path) -> None:
    paths = InstancePaths.resolve(
        env={"FIN_GURU_DATA_ROOT": "instance"},
        cwd=tmp_path,
    )

    assert paths.root == (tmp_path / "instance").resolve()
    assert paths.root.is_absolute()


def test_database_url_defaults_to_database_under_root(tmp_path: Path) -> None:
    paths = InstancePaths(root=tmp_path)

    assert paths.database_url(env={}) == f"sqlite:///{tmp_path / 'family_office.db'}"


def test_relative_sqlite_database_url_resolves_under_root(tmp_path: Path) -> None:
    paths = InstancePaths(root=tmp_path)

    assert paths.database_url(env={"DATABASE_URL": "sqlite:///relative.db"}) == (
        f"sqlite:///{tmp_path / 'relative.db'}"
    )


def test_absolute_sqlite_database_url_is_preserved(tmp_path: Path) -> None:
    paths = InstancePaths(root=tmp_path)

    assert paths.database_url(env={"DATABASE_URL": "sqlite:////abs.db"}) == (
        "sqlite:////abs.db"
    )


def test_bare_database_path_resolves_under_root(tmp_path: Path) -> None:
    paths = InstancePaths(root=tmp_path)

    assert paths.database_url(env={"DATABASE_URL": "relative.db"}) == (
        f"sqlite:///{tmp_path / 'relative.db'}"
    )


@pytest.mark.parametrize("configured_url", ["sqlite:///:memory:", ":memory:"])
def test_memory_database_url_is_preserved(configured_url: str, tmp_path: Path) -> None:
    paths = InstancePaths(root=tmp_path)

    assert paths.database_url(env={"DATABASE_URL": configured_url}) == (
        "sqlite:///:memory:"
    )
    assert _db_path(configured_url, paths) == Path(":memory:")


def test_db_path_rejects_non_sqlite_urls(tmp_path: Path) -> None:
    paths = InstancePaths(root=tmp_path)

    with pytest.raises(
        ValueError,
        match=r"^Finance Guru only supports sqlite databases, got postgresql://$",
    ):
        _db_path("postgresql://database.example/finance", paths)


def test_load_instance_env_lets_the_file_replace_the_process(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A key in the instance file wins, and a key the file omits stays put."""
    paths = InstancePaths(root=tmp_path)
    paths.env_file.write_text("DATABASE_URL=sqlite:///instance.db\n", encoding="utf-8")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///process.db")
    monkeypatch.setenv("FG_MARGIN_JUMP_ALERT_THRESHOLD", "5000")

    load_instance_env(paths)

    assert os.environ["DATABASE_URL"] == "sqlite:///instance.db"
    assert os.environ["FG_MARGIN_JUMP_ALERT_THRESHOLD"] == "5000"


def test_load_instance_env_empty_value_replaces_the_process(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An empty assignment still counts as set, matching the session-start hook."""
    paths = InstancePaths(root=tmp_path)
    paths.env_file.write_text("DATABASE_URL=\n", encoding="utf-8")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///process.db")

    load_instance_env(paths)

    assert os.environ["DATABASE_URL"] == ""


def test_load_instance_env_keeps_the_process_when_the_file_is_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = InstancePaths(root=tmp_path)
    monkeypatch.setenv("DATABASE_URL", "sqlite:///process.db")

    load_instance_env(paths)

    assert os.environ["DATABASE_URL"] == "sqlite:///process.db"


def _refresh_ledger(monkeypatch: pytest.MonkeyPatch, process_url: str) -> Path:
    """Return the ledger ``refresh_all`` would write, from a fresh process env."""
    monkeypatch.setenv("DATABASE_URL", process_url)
    found: list[Path] = []

    def fake_refresh(database_url: str | None, *, months: int = 12) -> dict[str, Any]:
        found.append(_db_path(database_url))
        return {"synced_at": "2026-10-06T00:00:00+00:00", "sources": []}

    monkeypatch.setattr(refresh_all, "refresh", fake_refresh)
    assert refresh_all.main([]) == 0
    return found[0]


def _margin_ledger(monkeypatch: pytest.MonkeyPatch, process_url: str) -> Path:
    """Return the ledger ``margin_metrics_cli`` would read, from a fresh process env."""
    monkeypatch.setenv("DATABASE_URL", process_url)
    found: list[Path] = []

    def fake_read_db_balances(
        database_url: str | None = None,
        config_path: str | Path | None = None,
    ) -> FidelityBalances:
        ledger = _db_path(database_url)
        found.append(ledger)
        return FidelityBalances(
            source_file=f"db:{ledger}",
            total_account_value=100_000.0,
            total_account_day_change=None,
            margin_buying_power=1_000.0,
            margin_buying_power_day_change=None,
            net_debit=-10_000.0,
            net_debit_day_change=None,
            margin_interest_accrued_this_month=None,
        )

    monkeypatch.setattr(
        "src.analysis.margin_metrics.read_db_balances", fake_read_db_balances
    )
    assert margin_metrics_main([]) == 0
    return found[0]


@pytest.mark.parametrize(
    ("env_line", "expected_relative"),
    [
        ("DATABASE_URL=sqlite:///from-env-file.db", "from-env-file.db"),
        ("DATABASE_URL=", "family_office.db"),
        ("OTHER=1", None),
    ],
)
def test_refresh_all_and_margin_metrics_cli_resolve_the_same_ledger(
    env_line: str,
    expected_relative: str | None,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Sync and margin metrics share one ledger when the process env disagrees."""
    process_ledger = tmp_path / "from-process.db"
    (tmp_path / ".env").write_text(f"{env_line}\n", encoding="utf-8")
    # load_dotenv can add OTHER. delenv(raising=False) does not record a missing
    # key, so setenv records the prior value or its absence before the removal.
    monkeypatch.setenv("OTHER", os.environ.get("OTHER", ""))
    monkeypatch.delenv("OTHER", raising=False)
    monkeypatch.setenv("FIN_GURU_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("FG_MARGIN_INTEREST_RATE_DECIMAL", "0.12")
    monkeypatch.setenv("FG_MARGIN_JUMP_ALERT_THRESHOLD", "5000")
    process_url = f"sqlite:///{process_ledger}"
    expected = (
        process_ledger if expected_relative is None else tmp_path / expected_relative
    )

    sync_ledger = _refresh_ledger(monkeypatch, process_url)
    margin_ledger = _margin_ledger(monkeypatch, process_url)

    assert sync_ledger.resolve() == margin_ledger.resolve() == expected.resolve()


def test_snaptrade_accounts_file_is_under_instance_root(tmp_path: Path) -> None:
    paths = InstancePaths(root=tmp_path)

    assert paths.snaptrade_accounts == tmp_path / "snaptrade-accounts.yaml"
