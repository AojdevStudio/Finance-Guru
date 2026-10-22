"""Create a local Finance Guru instance without overwriting existing files.

The scaffold commit runs before uv sync so it cannot include a partial virtual
environment, and the later migration commit owns ``uv.lock``.

An installed Finance Guru plugin is the source of truth for agents, skills, and
hooks, so plugin-mode instances omit ``.claude`` and ``.agents`` symlinks. They
get a real ``.claude/settings.json`` that makes the plugin's orchestrator the
main agent in that instance only.
Checkout-mode instances share finance assets through an instance-owned runtime
view and settings. Repository developer settings stay in the checkout.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
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
.agents
.claude
.venv/
__pycache__/
"""

MERCHANT_RULES = """# Household merchant patterns for expense categorization.
#
# The engine's public table only knows national brands. Your own merchants (the
# local dry cleaner, the daycare, the church) go here so they never leave this
# directory. Each key is a category from src/integrations/simplefin/categorize.py
# and each value is a list of lowercase substrings matched against the joined
# payee and bank memo. Within a category, order does not matter; across
# categories, the engine's table order decides ties.
#
# Groceries:
#   - corner market
# Family Care:
#   - little sprouts daycare
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
PLUGIN_AGENT = "finance-guru:fg-finance-orchestrator"
CHECKOUT_DISCOVERY_MARKER = "`.agents` symlink points to"
CHECKOUT_RUNTIME_MARKER = ".finance-guru-checkout"
SCAFFOLD_GIT_NAME = "Finance Guru"
SCAFFOLD_GIT_EMAIL = "finance-guru@example.invalid"

type StepResult = Literal["created", "exists", "updated"]
type StepAction = Callable[[Path], StepResult]


@dataclass(frozen=True)
class PlanStep:
    """One convergent filesystem operation in the instance plan."""

    target: Path
    action: StepAction


@dataclass(frozen=True)
class CheckoutRuntime:
    """Product assets and settings declared by the finance hook manifest."""

    links: dict[Path, Path]
    settings: str


def _checkout_runtime(repo: Path) -> CheckoutRuntime:
    links = {Path(name): repo / ".claude" / name for name in ("skills", "agents")}
    hooks = json.loads((repo / "hooks/hooks.json").read_text("utf-8"))["hooks"]
    prefix = "${CLAUDE_PLUGIN_ROOT}/"
    for groups in hooks.values():
        for group in groups:
            for hook in group["hooks"]:
                argv = [hook["command"], *hook.pop("args", [])]
                for arg in argv:
                    if arg.startswith(prefix + ".claude/hooks/"):
                        relative = Path(arg.removeprefix(prefix))
                        links[relative.relative_to(".claude")] = repo / relative
                hook["command"] = shlex.join(
                    arg.replace("${CLAUDE_PLUGIN_ROOT}", str(repo)) for arg in argv
                )
    settings = json.dumps({"hooks": hooks}, indent=2) + "\n"
    return CheckoutRuntime(links=links, settings=settings)


def _preflight_asset_links(claude: Path, runtime: CheckoutRuntime) -> None:
    for relative, source in runtime.links.items():
        path = claude / relative
        for parent in path.parents:
            if parent == claude:
                break
            if parent.is_symlink() or (parent.exists() and not parent.is_dir()):
                raise FileExistsError(f"{parent} is not a runtime directory")
        if path.is_symlink():
            if path.resolve() != source.resolve():
                raise FileExistsError(f"{path} points outside its finance asset")
        elif path.exists():
            raise FileExistsError(f"{path} exists and is not a symlink")


def _preflight_checkout(root: Path, repo: Path, runtime: CheckoutRuntime) -> None:
    claude = root / ".claude"
    agents = root / ".agents"
    if agents.is_symlink():
        if agents.resolve() not in {repo / ".claude", claude}:
            raise FileExistsError(f"{agents} points outside this checkout runtime")
    elif agents.exists():
        raise FileExistsError(f"{agents} exists and is not a symlink")
    if claude.is_symlink():
        if claude.resolve() != repo / ".claude":
            raise FileExistsError(f"{claude} points outside this engine checkout")
        return
    if not claude.exists():
        return
    marker = claude / CHECKOUT_RUNTIME_MARKER
    if (
        not claude.is_dir()
        or marker.is_symlink()
        or not marker.is_file()
        or marker.read_text("utf-8") != f"{repo}\n"
    ):
        raise FileExistsError(f"{claude} is not a managed checkout runtime")
    _preflight_asset_links(claude, runtime)


def _preflight_runtime(root: Path, repo: Path, runtime: CheckoutRuntime | None) -> None:
    claude = root / ".claude"
    agents = root / ".agents"
    if runtime is None:
        for path in (claude, agents):
            if path.is_symlink():
                raise FileExistsError(
                    f"{path} is a symlink from a checkout-mode scaffold; "
                    "remove .claude and .agents to use --plugin"
                )
        if agents.exists():
            raise FileExistsError(
                f"{agents} retains checkout discovery; move it before using --plugin"
            )
        if (claude / CHECKOUT_RUNTIME_MARKER).exists():
            raise FileExistsError(
                f"{claude} is a checkout-mode runtime; move .claude and "
                "remove .agents before using --plugin"
            )
    else:
        _preflight_checkout(root, repo, runtime)
    if not claude.is_symlink() and (claude / "settings.json").is_symlink():
        raise FileExistsError(f"{claude / 'settings.json'} is a symlink")
    _preflight_instructions(root, repo, plugin_mode=runtime is None)


def _preflight_instructions(root: Path, repo: Path, *, plugin_mode: bool) -> None:
    for name, marker in (
        ("AGENTS.md", str(repo / "AGENTS.md")),
        ("CLAUDE.md", f"@{repo / 'CLAUDE.md'}"),
    ):
        path = root / name
        if path.is_symlink():
            raise FileExistsError(f"{path} is a symlink")
        if not path.exists():
            continue
        old = (
            tuple(
                _instance_agent_instructions(repo, plugin_mode=mode, legacy=legacy)
                for mode, legacy in ((False, True), (True, True), (False, False))
            )
            if name == "AGENTS.md"
            else (_instance_instructions(repo, legacy=True),)
        )
        current = path.read_text("utf-8")
        inherited = marker in current or (
            plugin_mode and name == "AGENTS.md" and CHECKOUT_DISCOVERY_MARKER in current
        )
        if inherited and current not in old:
            raise FileExistsError(
                f"{path} has checkout-mode discovery text and your own edits; "
                "remove its repository instruction reference before rerunning"
            )


def _create_checkout_runtime(repo: Path, runtime: CheckoutRuntime) -> StepAction:
    def create(path: Path) -> StepResult:
        existed = path.exists() or path.is_symlink()
        replaced = path.is_symlink()
        if replaced:
            path.unlink()
        path.mkdir(exist_ok=True)
        results = [_write_text(f"{repo}\n")(path / CHECKOUT_RUNTIME_MARKER)]
        for relative, source in runtime.links.items():
            destination = path / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            results.append(_create_symlink(source)(destination))
        results.append(_write_text(runtime.settings)(path / "settings.json"))
        if not existed:
            return "created"
        return "updated" if replaced or "created" in results else "exists"

    return create


def _link_checkout_discovery(repo: Path) -> StepAction:
    def create(path: Path) -> StepResult:
        source = path.parent / ".claude"
        if path.is_symlink() and path.resolve() == repo / ".claude":
            path.unlink()
            path.symlink_to(source, target_is_directory=True)
            return "updated"
        return _create_symlink(source)(path)

    return create


def _create_directory(path: Path) -> StepResult:
    if path.exists():
        if not path.is_dir():
            raise FileExistsError(f"{path} exists and is not a directory")
        return "exists"
    path.mkdir(parents=True)
    return "created"


def _create_real_directory(path: Path) -> StepResult:
    for leftover in (path, path.parent / ".agents"):
        if leftover.is_symlink():
            raise FileExistsError(
                f"{leftover} is a symlink from a checkout-mode scaffold; "
                "remove .claude and .agents to use --plugin"
            )
    return _create_directory(path)


def _merge_agent_setting(path: Path) -> StepResult:
    """Add the orchestrator as the main agent, keeping settings the owner already has."""
    if path.is_symlink():
        raise FileExistsError(
            f"{path} is a symlink; --plugin will not write through it to a shared file"
        )
    existed = path.exists()
    settings = json.loads(path.read_text(encoding="utf-8")) if existed else {}
    if "agent" in settings:
        return "exists"
    settings["agent"] = PLUGIN_AGENT
    path.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n", "utf-8")
    return "updated" if existed else "created"


def _replace_instance_instructions(
    content: str, previous: tuple[str, ...]
) -> StepAction:
    """Update recognized generated instructions and preserve other owner text."""

    def write(path: Path) -> StepResult:
        if path.is_symlink():
            return "exists"
        if not path.exists():
            path.write_text(content, encoding="utf-8")
            return "created"
        current = path.read_text(encoding="utf-8")
        if current != content and current in previous:
            path.write_text(content, encoding="utf-8")
            return "updated"
        return "exists"

    return write


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


def _reject_git_remotes(root: Path) -> None:
    remote_names = _run_git(root, "remote").stdout.splitlines()
    if remote_names:
        names = ", ".join(remote_names)
        raise RuntimeError(
            f"{root} has git remote(s): {names}; the instance must have no remote"
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

    _reject_git_remotes(root)
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
    lines: list[str] = []
    found_data_root = False
    for line in example.splitlines():
        if line.lstrip().startswith("#") or "=" not in line:
            lines.append(line)
            continue

        key, value = line.split("=", 1)
        normalized_value = value.strip()
        if (
            len(normalized_value) >= 2
            and normalized_value[0] == normalized_value[-1]
            and normalized_value[0] in {'"', "'"}
        ):
            normalized_value = normalized_value[1:-1]

        if key == "FIN_GURU_DATA_ROOT":
            value = ""
            found_data_root = True
        elif (
            not normalized_value
            or "your_" in normalized_value
            or normalized_value.endswith("_here")
            or (normalized_value.startswith("${") and normalized_value.endswith("}"))
        ):
            value = ""

        lines.append(f"{key}={value}" if value else f"# {key}=")

    if not found_data_root:
        lines.append("# FIN_GURU_DATA_ROOT=")
    return "\n".join(lines) + "\n"


def _instance_instructions(repo: Path, *, legacy: bool = False) -> str:
    project_file = repo / "CLAUDE.md" if legacy else Path("AGENTS.md")
    return f"""@{project_file}

# Instance

This directory is a Finance Guru instance, and the engine lives at `{repo}`.

Command form: `uv run python -m src.<tool>`

Example: `uv run python -m src.integrations.refresh_all --show`
"""


def _instance_agent_instructions(
    repo: Path, *, plugin_mode: bool, legacy: bool = False
) -> str:
    if plugin_mode:
        discovery_instructions = """The installed Finance Guru plugin is the source of truth for agents, skills, and hooks.
This instance intentionally omits `.claude` and `.agents` symlinks. Its
`.claude/settings.json` makes the plugin's finance orchestrator the main agent.
"""
    elif legacy:
        discovery_instructions = f"""This instance's `.agents` symlink points to
`{repo / ".claude"}`, so Codex discovers the canonical skills under
`.agents/skills/`. Read a skill's complete `SKILL.md` before using it. Do not
copy or fork skill content into this instance.
"""
    else:
        discovery_instructions = """This instance's `.agents` symlink points to its own `.claude` runtime view.
That view shares the canonical finance skills under `.agents/skills/` and the
finance agents. Its own settings run only the product session hook. Read a
skill's complete `SKILL.md` before using it. Do not
copy or fork skill content into this instance.
"""

    source = (
        f"Before doing Finance Guru work, read `{repo / 'AGENTS.md'}` in full."
        if legacy
        else f"Before doing Finance Guru work, read `{repo / '.claude/skills/fin-core/SKILL.md'}` in full."
    )
    rules = (
        ""
        if legacy
        else """
Run `date` before analysis. Quote calculator output and pass `--output json`
where offered. Fail closed on missing inputs. Every financial output needs an
educational-only disclaimer, a not investment advice statement, a recommendation
to consult licensed professionals, a risk disclosure, a date and its data source.
Speak to the owner in the second person. Keep private data in this instance.
"""
    )

    return (
        f"""# Finance Guru instance

{source}

The engine lives at `{repo}`.

{discovery_instructions}

Run engine commands from this instance as `uv run python -m src.<tool>` so all
private paths resolve from the current directory.
"""
        + rules
    )


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


def _build_plan(
    paths: InstancePaths, repo: Path, *, runtime: CheckoutRuntime | None
) -> list[PlanStep]:
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
            PlanStep(paths.merchant_rules, _write_text(MERCHANT_RULES)),
        )
    )
    if runtime is None:
        plan.extend(
            (
                PlanStep(paths.root / ".claude", _create_real_directory),
                PlanStep(
                    paths.root / ".claude" / "settings.json", _merge_agent_setting
                ),
            )
        )
    else:
        plan.extend(
            (
                PlanStep(
                    paths.root / ".claude", _create_checkout_runtime(repo, runtime)
                ),
                PlanStep(paths.root / ".agents", _link_checkout_discovery(repo)),
            )
        )
    plan.extend(
        (
            PlanStep(
                paths.root / "CLAUDE.md",
                _replace_instance_instructions(
                    _instance_instructions(repo),
                    (_instance_instructions(repo, legacy=True),),
                ),
            ),
            PlanStep(
                paths.root / "AGENTS.md",
                _replace_instance_instructions(
                    _instance_agent_instructions(repo, plugin_mode=runtime is None),
                    tuple(
                        _instance_agent_instructions(
                            repo, plugin_mode=mode, legacy=legacy
                        )
                        for mode, legacy in (
                            (False, True),
                            (True, True),
                            (False, False),
                        )
                    ),
                ),
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
    parser.add_argument(
        "--plugin",
        action="store_true",
        help="Use the installed plugin as the agent, skill, and hook source",
    )
    return parser.parse_args(argv)


def _uses_installed_plugin(repo: Path, *, explicit: bool) -> bool:
    if explicit:
        return True

    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if plugin_root is None:
        return False
    return Path(plugin_root).expanduser().resolve() == repo


def main(argv: Sequence[str] | None = None) -> int:
    """Create or complete one Finance Guru instance."""
    args = _parse_args(argv)
    paths = InstancePaths(root=args.root.expanduser().resolve())
    repo = args.repo.expanduser().resolve()
    plugin_mode = _uses_installed_plugin(repo, explicit=args.plugin)

    if (paths.root / ".git").exists():
        _reject_git_remotes(paths.root)

    runtime = None if plugin_mode else _checkout_runtime(repo)
    _preflight_runtime(paths.root, repo, runtime)
    for step in _build_plan(paths, repo, runtime=runtime):
        result = step.action(step.target)
        print(f"{result} {step.target}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
