"""Behavior tests for the local Finance Guru instance initializer."""

from __future__ import annotations

import io
import os
import subprocess
import tomllib
import traceback
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

import yaml

from src.cli import instance_init
from src.config import InstancePaths

GIT_ENV = {
    "GIT_AUTHOR_NAME": "Finance Guru Test",
    "GIT_AUTHOR_EMAIL": "finance-guru@example.invalid",
    "GIT_COMMITTER_NAME": "Finance Guru Test",
    "GIT_COMMITTER_EMAIL": "finance-guru@example.invalid",
}


def _fake_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "engine"
    (repo / ".claude").mkdir(parents=True)
    (repo / ".env.example").write_text(
        "FIN_GURU_DATA_ROOT=/replace/me\nEXAMPLE_SETTING=\n",
        encoding="utf-8",
    )
    (repo / "CLAUDE.md").write_text("# Engine instructions\n", encoding="utf-8")
    return repo


def _run_init(
    root: Path,
    repo: Path,
    *,
    configure_git_identity: bool = True,
    sync_roots: list[Path] | None = None,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if configure_git_identity:
        env.update(GIT_ENV)
    else:
        for name in GIT_ENV:
            env.pop(name, None)
        env["GIT_CONFIG_GLOBAL"] = os.devnull
        env["GIT_CONFIG_NOSYSTEM"] = "1"
        env["GIT_CONFIG_COUNT"] = "1"
        env["GIT_CONFIG_KEY_0"] = "user.useConfigOnly"
        env["GIT_CONFIG_VALUE_0"] = "true"

    args = [str(root), "--repo", str(repo)]
    stdout = io.StringIO()
    stderr = io.StringIO()
    with (
        mock.patch.dict(os.environ, env, clear=True),
        mock.patch.object(instance_init, "_run_uv_sync", autospec=True) as sync,
        redirect_stdout(stdout),
        redirect_stderr(stderr),
    ):
        try:
            returncode = instance_init.main(args)
        except Exception:
            traceback.print_exc()
            returncode = 1

    if sync_roots is not None:
        sync_roots.extend(Path(call.args[0]) for call in sync.call_args_list)

    return subprocess.CompletedProcess(
        args=args,
        returncode=returncode,
        stdout=stdout.getvalue(),
        stderr=stderr.getvalue(),
    )


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _managed_file_mtimes(root: Path) -> dict[Path, int]:
    return {
        path.relative_to(root): path.lstat().st_mtime_ns
        for path in root.rglob("*")
        if ".git" not in path.relative_to(root).parts
        and (path.is_file() or path.is_symlink())
    }


def test_fresh_root_creates_complete_instance(tmp_path: Path) -> None:
    repo = _fake_repo(tmp_path)
    root = tmp_path / "instance"
    sync_roots: list[Path] = []

    result = _run_init(root, repo, sync_roots=sync_roots)

    claude_text = (root / "CLAUDE.md").read_text(encoding="utf-8")
    assert (
        "Command form: `uv run python -m src.<tool>`" in claude_text
        and "Example: `uv run python -m src.integrations.refresh_all --show`"
        in claude_text
        and "--project" not in claude_text
    )
    pyproject_path = root / "pyproject.toml"
    pyproject = (
        tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
        if pyproject_path.is_file()
        else None
    )
    assert pyproject == {
        "project": {
            "name": "finance-guru-instance",
            "version": "0.0.0",
            "requires-python": ">=3.12",
            "dependencies": ["family-office"],
        },
        "tool": {
            "uv": {
                "sources": {
                    "family-office": {"path": str(repo), "editable": True},
                }
            }
        },
    }
    assert sync_roots == [root]
    assert result.returncode == 0, result.stderr
    assert all(line.startswith("created ") for line in result.stdout.splitlines())

    paths = InstancePaths(root=root)
    directories = (
        paths.imports,
        paths.analysis,
        paths.tickets,
        paths.strategies,
        paths.hedging,
        paths.reports,
        paths.auto_tickets,
        paths.notes,
    )
    assert all(path.is_dir() for path in directories)

    expected_files = (
        root / ".gitignore",
        paths.env_file,
        paths.profile,
        root / "CLAUDE.md",
    )
    assert all(path.is_file() for path in expected_files)
    assert (root / ".gitignore").read_text(encoding="utf-8") == (
        ".env\n.DS_Store\n*.db-journal\n*.db-wal\n*.db-shm\n.claude\n.venv/\n"
        "__pycache__/\n"
    )
    assert (root / ".claude").is_symlink()
    assert (root / ".claude").resolve() == (repo / ".claude").resolve()
    assert (root / ".git").is_dir()

    env_lines = paths.env_file.read_text(encoding="utf-8").splitlines()
    assert "FIN_GURU_DATA_ROOT=" in env_lines
    assert "FIN_GURU_DATA_ROOT=/replace/me" not in env_lines
    assert "EXAMPLE_SETTING=" in env_lines

    profile = yaml.safe_load(paths.profile.read_text(encoding="utf-8"))
    assert set(profile) == {
        "system_ownership",
        "orientation_status",
        "user_profile",
        "hedging",
        "opportunities",
        "recommended_workflows",
        "session_context",
    }

    assert claude_text.splitlines()[0] == f"@{repo / 'CLAUDE.md'}"
    assert claude_text.index("# Instance") < claude_text.index(
        "This directory is a Finance Guru instance"
    )

    assert _git(root, "rev-list", "--count", "HEAD") == "1"
    assert _git(root, "log", "-1", "--format=%s") == "scaffold instance"
    assert _git(root, "remote") == ""


def test_second_run_is_a_no_op(tmp_path: Path) -> None:
    repo = _fake_repo(tmp_path)
    root = tmp_path / "instance"
    first = _run_init(root, repo)
    (root / ".venv").mkdir()
    before = _managed_file_mtimes(root) if first.returncode == 0 else {}

    second = _run_init(root, repo)

    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    assert f"exists {root / '.venv'}" in second.stdout.splitlines()
    assert all(line.startswith("exists ") for line in second.stdout.splitlines())
    assert _managed_file_mtimes(root) == before
    assert _git(root, "rev-list", "--count", "HEAD") == "1"


def test_existing_profile_is_preserved_byte_for_byte(tmp_path: Path) -> None:
    repo = _fake_repo(tmp_path)
    root = tmp_path / "instance"
    root.mkdir()
    profile = root / "user-profile.yaml"
    original = b"user_profile:\n  custom: preserved\n"
    profile.write_bytes(original)

    result = _run_init(root, repo)

    assert result.returncode == 0, result.stderr
    assert profile.read_bytes() == original
    assert f"exists {profile}" in result.stdout.splitlines()


def test_real_claude_directory_fails_and_names_path(tmp_path: Path) -> None:
    repo = _fake_repo(tmp_path)
    root = tmp_path / "instance"
    conflict = root / ".claude"
    conflict.mkdir(parents=True)

    result = _run_init(root, repo)

    assert result.returncode != 0
    assert str(conflict) in result.stderr


def test_scaffold_commit_does_not_require_user_git_identity(tmp_path: Path) -> None:
    repo = _fake_repo(tmp_path)
    root = tmp_path / "instance"

    result = _run_init(root, repo, configure_git_identity=False)

    assert result.returncode == 0, result.stderr
    assert _git(root, "log", "-1", "--format=%s") == "scaffold instance"
    assert _git(root, "log", "-1", "--format=%an <%ae>") == (
        "Finance Guru <finance-guru@example.invalid>"
    )
