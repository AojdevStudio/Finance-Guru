"""Create a local Finance Guru instance without overwriting existing files.

The scaffold commit runs before uv sync so it cannot include a partial virtual
environment, and the later migration commit owns ``uv.lock``.
"""

from __future__ import annotations

import argparse
import os
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from src.config import InstancePaths

GITIGNORE = """.env
.DS_Store
*.db-journal
*.db-wal
*.db-shm
.claude
.venv/
__pycache__/
"""

USER_PROFILE = """# Add instance-specific values after creating the instance.
system_ownership: {}
orientation_status: {}
user_profile:
  liquid_assets: {}
  investment_portfolio: {}
  cash_flow: {}
  debt_profile: {}
  preferences: {}
hedging: {}
opportunities: {}
recommended_workflows: {}
session_context: {}
"""
SCAFFOLD_GIT_NAME = "Finance Guru"
SCAFFOLD_GIT_EMAIL = "finance-guru@example.invalid"

type StepResult = Literal["created", "exists"]
type StepAction = Callable[[Path], StepResult]


@dataclass(frozen=True)
class PlanStep:
    """One convergent filesystem operation in the instance plan."""

    target: Path
    action: StepAction


def _create_directory(path: Path) -> StepResult:
    if path.exists():
        if not path.is_dir():
            raise FileExistsError(f"{path} exists and is not a directory")
        return "exists"
    path.mkdir(parents=True)
    return "created"


def _write_text(content: str) -> StepAction:
    def write(path: Path) -> StepResult:
        if path.exists() or path.is_symlink():
            return "exists"
        path.write_text(content, encoding="utf-8")
        return "created"

    return write


def _create_symlink(source: Path) -> StepAction:
    def create(path: Path) -> StepResult:
        if path.is_symlink():
            return "exists"
        if path.exists():
            raise FileExistsError(f"{path} exists and is not a symlink")
        path.symlink_to(source, target_is_directory=True)
        return "created"

    return create


def _git_env() -> dict[str, str]:
    return {
        name: value for name, value in os.environ.items() if not name.startswith("GIT_")
    }


def _run_git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=True,
        env=_git_env(),
    )


def _initialize_git(path: Path) -> StepResult:
    existed = path.exists()
    root = path.parent
    if not existed:
        subprocess.run(
            ["git", "init", str(root)],
            check=True,
            capture_output=True,
            text=True,
            env=_git_env(),
        )

    commit_count = int(_run_git(root, "rev-list", "--count", "--all").stdout)
    if commit_count == 0:
        _run_git(root, "add", "-A")
        _run_git(
            root,
            "-c",
            f"user.name={SCAFFOLD_GIT_NAME}",
            "-c",
            f"user.email={SCAFFOLD_GIT_EMAIL}",
            "commit",
            "-m",
            "scaffold instance",
        )

    return "exists" if existed else "created"


def _instance_env(example: str) -> str:
    lines = example.splitlines()
    for index, line in enumerate(lines):
        if line.startswith("FIN_GURU_DATA_ROOT="):
            lines[index] = "FIN_GURU_DATA_ROOT="
            break
    else:
        lines.append("FIN_GURU_DATA_ROOT=")
    return "\n".join(lines) + "\n"


def _instance_instructions(repo: Path) -> str:
    project_file = repo / "CLAUDE.md"
    return f"""@{project_file}

# Instance

This directory is a Finance Guru instance, and the engine lives at `{repo}`.

Command form: `uv run python -m src.<tool>`

Example: `uv run python -m src.integrations.refresh_all --show`
"""


def _instance_pyproject(repo: Path) -> str:
    return f"""[project]
name = "finance-guru-instance"
version = "0.0.0"
requires-python = ">=3.12"
dependencies = ["family-office"]

[tool.uv.sources]
family-office = {{ path = "{repo}", editable = true }}
"""


def _run_uv_sync(root: Path) -> None:
    subprocess.run(["uv", "sync", "--quiet"], cwd=root, check=True)


def _sync_environment(path: Path) -> StepResult:
    existed = path.exists()
    _run_uv_sync(path.parent)
    return "exists" if existed else "created"


def _build_plan(paths: InstancePaths, repo: Path) -> list[PlanStep]:
    directory_paths = (
        paths.imports,
        paths.analysis,
        paths.tickets,
        paths.strategies,
        paths.hedging,
        paths.reports,
        paths.auto_tickets,
        paths.notes,
    )
    env_content = _instance_env((repo / ".env.example").read_text(encoding="utf-8"))

    plan = [PlanStep(paths.root, _create_directory)]
    plan.extend(PlanStep(path, _create_directory) for path in directory_paths)
    plan.extend(
        (
            PlanStep(paths.root / ".gitignore", _write_text(GITIGNORE)),
            PlanStep(
                paths.root / "pyproject.toml",
                _write_text(_instance_pyproject(repo)),
            ),
            PlanStep(paths.env_file, _write_text(env_content)),
            PlanStep(paths.profile, _write_text(USER_PROFILE)),
            PlanStep(paths.root / ".claude", _create_symlink(repo / ".claude")),
            PlanStep(
                paths.root / "CLAUDE.md",
                _write_text(_instance_instructions(repo)),
            ),
            PlanStep(paths.root / ".git", _initialize_git),
            PlanStep(paths.root / ".venv", _sync_environment),
        )
    )
    return plan


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="Instance directory to create")
    parser.add_argument(
        "--repo",
        type=Path,
        required=True,
        help="Finance Guru engine checkout",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Create or complete one Finance Guru instance."""
    args = _parse_args(argv)
    paths = InstancePaths(root=args.root.expanduser().resolve())
    repo = args.repo.expanduser().resolve()

    for step in _build_plan(paths, repo):
        result = step.action(step.target)
        print(f"{result} {step.target}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
