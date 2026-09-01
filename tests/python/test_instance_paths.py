"""Tests for the instance data-root model."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from src.config import InstancePaths
from src.config.instance_paths import _db_path, load_instance_env


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


def test_load_instance_env_preserves_process_values_by_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = InstancePaths(root=tmp_path)
    paths.env_file.write_text("DATABASE_URL=sqlite:///instance.db\n", encoding="utf-8")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///process.db")

    load_instance_env(paths)

    assert os.environ["DATABASE_URL"] == "sqlite:///process.db"

    load_instance_env(paths, override=True)

    assert os.environ["DATABASE_URL"] == "sqlite:///instance.db"


def test_snaptrade_accounts_file_is_under_instance_root(tmp_path: Path) -> None:
    paths = InstancePaths(root=tmp_path)

    assert paths.snaptrade_accounts == tmp_path / "snaptrade-accounts.yaml"
