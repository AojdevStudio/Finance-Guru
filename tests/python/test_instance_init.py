"""Behavior tests for the local Finance Guru instance initializer."""

from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import tomllib
import traceback
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

import pytest
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
    for directory in ("skills/fin-core", "skills/_shared", "agents", "hooks"):
        (repo / ".claude" / directory).mkdir(parents=True)
    (repo / ".claude/skills/fin-core/SKILL.md").write_text("finance context\n")
    (repo / ".claude/agents/fg-finance-orchestrator.md").write_text("finance agent\n")
    (repo / ".claude/hooks/load-fin-core-config.ts").write_text("finance hook\n")
    (repo / "hooks").mkdir()
    (repo / "hooks/hooks.json").write_text(
        json.dumps(
            {
                "hooks": {
                    "SessionStart": [
                        {
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": "bun",
                                    "args": [
                                        "run",
                                        "${CLAUDE_PLUGIN_ROOT}/.claude/hooks/load-fin-core-config.ts",
                                    ],
                                }
                            ]
                        }
                    ]
                }
            }
        )
    )
    (repo / ".env.example").write_text(
        "FIN_GURU_DATA_ROOT=/replace/me\nEXAMPLE_SETTING=\n",
        encoding="utf-8",
    )
    (repo / "CLAUDE.md").write_text("# Engine instructions\n", encoding="utf-8")
    (repo / "AGENTS.md").write_text("# Engine agent instructions\n", encoding="utf-8")
    return repo


def test_checkout_runtime_keeps_developer_settings_and_tools_in_the_repo(
    tmp_path: Path,
) -> None:
    repo = _fake_repo(tmp_path)
    root = tmp_path / "instance"
    developer_settings = (
        '{"hooks":{"PreToolUse":[{"hooks":[{"command":"developer gate"}]}]}}\n'
    )
    (repo / ".claude/settings.json").write_text(developer_settings)
    (repo / ".dev/pr-kit/open-pr").mkdir(parents=True)
    (repo / ".dev/pr-kit/open-pr/SKILL.md").write_text("developer tool\n")

    result = _run_init(root, repo)

    assert result.returncode == 0, result.stderr
    assert not (root / ".claude").is_symlink()
    assert (root / ".agents").resolve() == root / ".claude"
    assert (
        root / ".agents/skills/fin-core/SKILL.md"
    ).read_text() == "finance context\n"
    assert not (root / ".agents/skills/open-pr").exists()
    settings = (root / ".claude/settings.json").read_text()
    assert set(json.loads(settings)["hooks"]) == {"SessionStart"}
    assert "developer" not in settings
    assert (repo / ".claude/settings.json").read_text() == developer_settings
    assert (
        (root / "CLAUDE.md")
        .read_text()
        .startswith(f"@{repo / '.claude/skills/fin-core/SKILL.md'}\n")
    )
    assert str(repo / "AGENTS.md") not in (root / "AGENTS.md").read_text()
    assert str(repo / "CLAUDE.md") not in (root / "CLAUDE.md").read_text()


def test_checkout_migrates_known_legacy_links_without_changing_shared_settings(
    tmp_path: Path,
) -> None:
    repo = _fake_repo(tmp_path)
    root = tmp_path / "instance"
    root.mkdir()
    for name in (".claude", ".agents"):
        (root / name).symlink_to(repo / ".claude", target_is_directory=True)
    shared = '{"hooks":{"PreToolUse":[]}}\n'
    (repo / ".claude/settings.json").write_text(shared)
    (root / "CLAUDE.md").write_text(f"""@{repo / "CLAUDE.md"}

# Instance

This directory is a Finance Guru instance, and the engine lives at `{repo}`.

Command form: `uv run python -m src.<tool>`

Example: `uv run python -m src.integrations.refresh_all --show`
""")
    (root / "AGENTS.md").write_text(f"""# Finance Guru instance

Before doing Finance Guru work, read `{repo / "AGENTS.md"}` in full.

The engine lives at `{repo}`.

This instance's `.agents` symlink points to
`{repo / ".claude"}`, so Codex discovers the canonical skills under
`.agents/skills/`. Read a skill's complete `SKILL.md` before using it. Do not
copy or fork skill content into this instance.


Run engine commands from this instance as `uv run python -m src.<tool>` so all
private paths resolve from the current directory.
""")

    result = _run_init(root, repo)

    assert result.returncode == 0, result.stderr
    assert not (root / ".claude").is_symlink()
    assert (root / ".agents").resolve() == root / ".claude"
    assert (repo / ".claude/settings.json").read_text() == shared
    assert (
        (root / "CLAUDE.md")
        .read_text()
        .startswith(f"@{repo / '.claude/skills/fin-core/SKILL.md'}\n")
    )
    assert str(repo / "AGENTS.md") not in (root / "AGENTS.md").read_text()
    assert _run_init(root, repo).returncode == 0


@pytest.mark.parametrize("name", ["AGENTS.md", "CLAUDE.md"])
def test_legacy_instruction_edits_block_migration_before_any_write(
    tmp_path: Path, name: str
) -> None:
    repo = _fake_repo(tmp_path)
    root = tmp_path / "instance"
    root.mkdir()
    for link in (".claude", ".agents"):
        (root / link).symlink_to(repo / ".claude", target_is_directory=True)
    text = f"@{repo / name}\nMy private notes\n"
    (root / name).write_text(text)

    result = _run_init(root, repo)

    assert result.returncode != 0
    assert name in result.stderr
    assert (root / name).read_text() == text
    assert (root / ".claude").is_symlink()
    assert (root / ".agents").resolve() == repo / ".claude"
    assert {path.name for path in root.iterdir()} == {".claude", ".agents", name}


def test_plugin_refuses_checkout_runtime_before_changing_files(tmp_path: Path) -> None:
    repo = _fake_repo(tmp_path)
    root = tmp_path / "instance"
    assert _run_init(root, repo).returncode == 0
    before = _managed_file_mtimes(root)

    result = _run_init(root, repo, plugin=True)

    assert result.returncode != 0
    assert ".claude" in result.stderr or ".agents" in result.stderr
    assert _managed_file_mtimes(root) == before


def test_plugin_refuses_a_real_discovery_tree_before_writing(tmp_path: Path) -> None:
    repo = _fake_repo(tmp_path)
    root = tmp_path / "instance"
    (root / ".agents/skills").mkdir(parents=True)
    (root / ".agents/skills/local.md").write_text("local discovery\n")
    before = _managed_file_mtimes(root)

    result = _run_init(root, repo, plugin=True)

    assert result.returncode != 0
    assert ".agents" in result.stderr
    assert _managed_file_mtimes(root) == before


@pytest.mark.parametrize("name", ["AGENTS.md", "CLAUDE.md"])
def test_checkout_rerun_keeps_owner_notes(tmp_path: Path, name: str) -> None:
    repo = _fake_repo(tmp_path)
    root = tmp_path / "instance"
    assert _run_init(root, repo).returncode == 0
    path = root / name
    notes = path.read_text() + "\n## Household notes\nKeep these notes.\n"
    path.write_text(notes)
    before = _managed_file_mtimes(root)

    result = _run_init(root, repo)

    assert result.returncode == 0, result.stderr
    assert path.read_text() == notes
    assert _managed_file_mtimes(root) == before


def test_checkout_refuses_foreign_links_before_writing_instance_files(
    tmp_path: Path,
) -> None:
    repo = _fake_repo(tmp_path)
    root = tmp_path / "instance"
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    root.mkdir()
    (root / ".agents").symlink_to(foreign, target_is_directory=True)

    result = _run_init(root, repo)

    assert result.returncode != 0
    assert ".agents" in result.stderr
    assert list(foreign.iterdir()) == []
    assert {path.name for path in root.iterdir()} == {".agents"}


def _run_init(
    root: Path,
    repo: Path,
    *,
    configure_git_identity: bool = True,
    plugin: bool = False,
    plugin_root: Path | None = None,
    sync_roots: list[Path] | None = None,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if plugin_root is None:
        env.pop("CLAUDE_PLUGIN_ROOT", None)
    else:
        env["CLAUDE_PLUGIN_ROOT"] = str(plugin_root)
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
    if plugin:
        args.append("--plugin")
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
        env={
            name: value
            for name, value in os.environ.items()
            if not name.startswith("GIT_")
        },
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
        paths.merchant_rules,
        root / "AGENTS.md",
        root / "CLAUDE.md",
    )
    assert all(path.is_file() for path in expected_files)
    assert (root / ".gitignore").read_text(encoding="utf-8") == (
        ".env\n.DS_Store\n*.db-journal\n*.db-wal\n*.db-shm\n.agents\n"
        ".claude\n.venv/\n"
        "__pycache__/\n"
    )
    assert (root / ".agents").is_symlink()
    assert (root / ".agents").resolve() == root / ".claude"
    assert (root / ".agents" / "skills").resolve() == (
        repo / ".claude" / "skills"
    ).resolve()
    assert not (root / ".claude").is_symlink()
    assert (root / ".claude/skills").resolve() == (repo / ".claude/skills").resolve()
    assert (root / ".git").is_dir()

    env_lines = paths.env_file.read_text(encoding="utf-8").splitlines()
    assert "# FIN_GURU_DATA_ROOT=" in env_lines
    assert "FIN_GURU_DATA_ROOT=/replace/me" not in env_lines
    assert "# EXAMPLE_SETTING=" in env_lines

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

    assert claude_text.splitlines()[0] == (
        f"@{repo / '.claude/skills/fin-core/SKILL.md'}"
    )
    assert claude_text.index("# Instance") < claude_text.index(
        "This directory is a Finance Guru instance"
    )
    agents_text = (root / "AGENTS.md").read_text(encoding="utf-8")
    assert str(repo / ".claude/skills/fin-core/SKILL.md") in agents_text
    assert ".agents/skills/" in agents_text
    assert "Do not\ncopy or fork skill content" in agents_text

    assert _git(root, "rev-list", "--count", "HEAD") == "1"
    assert _git(root, "log", "-1", "--format=%s") == "scaffold instance"
    assert _git(root, "remote") == ""


def test_plugin_flag_omits_harness_symlinks(tmp_path: Path) -> None:
    repo = _fake_repo(tmp_path)
    root = tmp_path / "instance"

    result = _run_init(root, repo, plugin=True)

    assert result.returncode == 0, result.stderr
    assert not (root / ".claude").is_symlink()
    assert not (root / ".agents").exists()
    settings = json.loads((root / ".claude" / "settings.json").read_text("utf-8"))
    assert settings == {"agent": "finance-guru:fg-finance-orchestrator"}
    agent_instructions = (root / "AGENTS.md").read_text(encoding="utf-8")
    assert "plugin is the source of truth for agents, skills, and hooks" in (
        agent_instructions
    )


def test_plugin_flag_refuses_a_checkout_mode_claude_symlink(tmp_path: Path) -> None:
    repo = _fake_repo(tmp_path)
    root = tmp_path / "instance"
    root.mkdir()
    (root / ".claude").symlink_to(repo / ".claude", target_is_directory=True)

    result = _run_init(root, repo, plugin=True)

    assert result.returncode != 0
    assert "symlink from a checkout-mode scaffold" in result.stderr
    assert (root / ".claude").is_symlink()


def test_plugin_flag_refuses_a_leftover_agents_symlink(tmp_path: Path) -> None:
    repo = _fake_repo(tmp_path)
    root = tmp_path / "instance"
    assert _run_init(root, repo).returncode == 0
    shutil.rmtree(root / ".claude")

    result = _run_init(root, repo, plugin=True)

    assert result.returncode != 0
    assert ".agents" in result.stderr
    assert not (root / ".claude").exists()


def test_plugin_flag_adds_the_agent_to_existing_settings(tmp_path: Path) -> None:
    repo = _fake_repo(tmp_path)
    root = tmp_path / "instance"
    (root / ".claude").mkdir(parents=True)
    (root / ".claude" / "settings.json").write_text(
        '{"permissions": {"allow": ["Read"]}}\n', encoding="utf-8"
    )

    result = _run_init(root, repo, plugin=True)

    assert result.returncode == 0, result.stderr
    settings = json.loads((root / ".claude" / "settings.json").read_text("utf-8"))
    assert settings == {
        "permissions": {"allow": ["Read"]},
        "agent": "finance-guru:fg-finance-orchestrator",
    }


def test_plugin_flag_converts_a_checkout_scaffold_end_to_end(tmp_path: Path) -> None:
    repo = _fake_repo(tmp_path)
    root = tmp_path / "instance"
    assert _run_init(root, repo).returncode == 0
    shutil.rmtree(root / ".claude")
    (root / ".agents").unlink()

    result = _run_init(root, repo, plugin=True)

    assert result.returncode == 0, result.stderr
    agents_text = (root / "AGENTS.md").read_text(encoding="utf-8")
    assert "plugin is the source of truth for agents, skills, and hooks" in agents_text
    assert ".agents/skills/" not in agents_text
    settings = json.loads((root / ".claude" / "settings.json").read_text("utf-8"))
    assert settings["agent"] == "finance-guru:fg-finance-orchestrator"


def test_plugin_flag_keeps_an_owner_edited_agents_file(tmp_path: Path) -> None:
    repo = _fake_repo(tmp_path)
    root = tmp_path / "instance"
    assert _run_init(root, repo).returncode == 0
    shutil.rmtree(root / ".claude")
    (root / ".agents").unlink()
    agents = root / "AGENTS.md"
    edited = agents.read_text(encoding="utf-8") + "\n## My household notes\n"
    agents.write_text(edited, encoding="utf-8")

    result = _run_init(root, repo, plugin=True)

    assert result.returncode != 0
    assert "AGENTS.md" in result.stderr
    assert agents.read_text(encoding="utf-8") == edited


def test_plugin_flag_refuses_a_symlinked_settings_file(tmp_path: Path) -> None:
    repo = _fake_repo(tmp_path)
    root = tmp_path / "instance"
    shared = tmp_path / "shared-settings.json"
    shared.write_text("{}\n", encoding="utf-8")
    (root / ".claude").mkdir(parents=True)
    (root / ".claude" / "settings.json").symlink_to(shared)

    result = _run_init(root, repo, plugin=True)

    assert result.returncode != 0
    assert "settings.json is a symlink" in result.stderr
    assert shared.read_text(encoding="utf-8") == "{}\n"


def test_matching_plugin_root_omits_harness_symlinks(tmp_path: Path) -> None:
    repo = _fake_repo(tmp_path)
    root = tmp_path / "instance"

    result = _run_init(root, repo, plugin_root=repo)

    assert result.returncode == 0, result.stderr
    assert not (root / ".claude").is_symlink()
    assert not (root / ".agents").exists()


@pytest.mark.parametrize("empty_value", ['""', "''", "   "])
def test_scaffolded_env_comments_empty_and_placeholder_values(
    tmp_path: Path, empty_value: str
) -> None:
    repo = _fake_repo(tmp_path)
    (repo / ".env.example").write_text(
        "FIN_GURU_DATA_ROOT=/replace/me\n"
        "SIMPLEFIN_ACCESS_URL=\n"
        f"QUOTED_OR_BLANK_SETTING={empty_value}\n"
        "SNAPTRADE_CLIENT_ID=your_snaptrade_client_id_here\n"
        "SIMPLEFIN_SETUP_TOKEN=${SIMPLEFIN_SETUP_TOKEN}\n"
        "LEGACY_SECRET=credential_here\n"
        "SMTP_PORT=587\n"
        "DEFAULT_RISK_TOLERANCE=aggressive\n"
        "DATABASE_URL=sqlite:///family_office.db\n",
        encoding="utf-8",
    )
    root = tmp_path / "instance"

    result = _run_init(root, repo)

    assert result.returncode == 0, result.stderr
    env_text = (root / ".env").read_text(encoding="utf-8")
    env_lines = env_text.splitlines()
    assert "_here" not in env_text
    assert "your_" not in env_text
    assert env_lines.count("# SIMPLEFIN_ACCESS_URL=") == 1
    assert not any(line.startswith("SIMPLEFIN_ACCESS_URL=") for line in env_lines)
    assert env_lines.count("# QUOTED_OR_BLANK_SETTING=") == 1
    assert not any(line.startswith("QUOTED_OR_BLANK_SETTING=") for line in env_lines)
    assert "# SNAPTRADE_CLIENT_ID=" in env_lines
    assert "# SIMPLEFIN_SETUP_TOKEN=" in env_lines
    assert "# LEGACY_SECRET=" in env_lines
    assert "SMTP_PORT=587" in env_lines
    assert "DEFAULT_RISK_TOLERANCE=aggressive" in env_lines
    assert "DATABASE_URL=sqlite:///family_office.db" in env_lines


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


def test_existing_repo_with_remote_is_rejected_before_scaffolding(
    tmp_path: Path,
) -> None:
    repo = _fake_repo(tmp_path)
    root = tmp_path / "instance"
    remote = tmp_path / "remote.git"
    subprocess.run(
        ["git", "init", str(root)],
        check=True,
        capture_output=True,
        text=True,
        env={
            name: value
            for name, value in os.environ.items()
            if not name.startswith("GIT_")
        },
    )
    _git(root, "remote", "add", "origin", str(remote))

    result = _run_init(root, repo)

    assert result.returncode != 0
    assert str(root) in result.stderr
    assert "origin" in result.stderr
    assert "must have no remote" in result.stderr
    assert {path.name for path in root.iterdir()} == {".git"}
    assert _git(root, "rev-list", "--count", "--all") == "0"


def test_real_claude_directory_fails_and_names_path(tmp_path: Path) -> None:
    repo = _fake_repo(tmp_path)
    root = tmp_path / "instance"
    conflict = root / ".claude"
    conflict.mkdir(parents=True)

    result = _run_init(root, repo)

    assert result.returncode != 0
    assert str(conflict) in result.stderr


def test_real_agents_directory_fails_and_names_path(tmp_path: Path) -> None:
    repo = _fake_repo(tmp_path)
    root = tmp_path / "instance"
    conflict = root / ".agents"
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


def test_scaffold_commit_ignores_inherited_git_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    hook_repo = tmp_path / "hook-repo"
    clean_env = {
        name: value for name, value in os.environ.items() if not name.startswith("GIT_")
    }
    subprocess.run(
        ["git", "init", str(hook_repo)],
        check=True,
        capture_output=True,
        text=True,
        env=clean_env,
    )
    (hook_repo / "outer.txt").write_text("outer\n", encoding="utf-8")
    subprocess.run(
        ["git", "-C", str(hook_repo), "add", "outer.txt"],
        check=True,
        capture_output=True,
        text=True,
        env=clean_env,
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(hook_repo),
            "-c",
            "user.name=Hook Repo",
            "-c",
            "user.email=hook@example.invalid",
            "commit",
            "-m",
            "outer commit",
        ],
        check=True,
        capture_output=True,
        text=True,
        env=clean_env,
    )
    git_dir = hook_repo / ".git"
    monkeypatch.setenv("GIT_DIR", str(git_dir))
    monkeypatch.setenv("GIT_INDEX_FILE", str(git_dir / "index"))
    repo = _fake_repo(tmp_path)
    root = tmp_path / "instance"

    result = _run_init(root, repo)

    git_log = subprocess.run(
        ["git", "-C", str(root), "log", "-1", "--format=%s"],
        capture_output=True,
        text=True,
        env=clean_env,
    )
    assert result.returncode == 0, result.stderr
    assert git_log.stdout.strip() == "scaffold instance"
