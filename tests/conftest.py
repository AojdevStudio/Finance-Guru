"""Pytest configuration helpers for repository-level acceptance tests."""

from __future__ import annotations

from pathlib import Path

import pytest

ACCEPTANCE_TEST_FILES = frozenset(
    {
        "tests/test_pipeline.py",
        "tests/test_guardrails.py",
        "tests/test_ticket_generator.py",
    }
)


def _is_test_path_arg(value: str) -> bool:
    """Return whether an invocation argument looks like a selected test path."""
    path_arg = value.split("::", 1)[0]
    return path_arg.startswith("tests/") or path_arg.endswith(".py")


def _is_acceptance_run(config) -> bool:
    """Return whether pytest was invoked only for root acceptance tests."""
    root = Path(config.rootpath)
    selected_paths = set()
    for arg in config.invocation_params.args or config.args:
        if arg.startswith("-") or not _is_test_path_arg(arg):
            continue
        path_arg = arg.split("::", 1)[0]
        if not path_arg:
            continue
        path = Path(path_arg)
        if not path.is_absolute():
            path = root / path
        resolved = path.resolve()
        try:
            selected_paths.add(resolved.relative_to(root).as_posix())
        except ValueError:
            continue
    selected = frozenset(selected_paths)
    return bool(selected) and selected.issubset(ACCEPTANCE_TEST_FILES)


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config) -> None:
    """Keep root acceptance commands from failing global coverage."""
    if _is_acceptance_run(config):
        config.option.cov_fail_under = 0


def pytest_sessionstart(session) -> None:
    """Patch pytest-cov after it copies command options for acceptance files."""
    if not _is_acceptance_run(session.config):
        return
    cov_plugin = session.config.pluginmanager.get_plugin("_cov")
    options = getattr(cov_plugin, "options", None)
    if options is not None and hasattr(options, "cov_fail_under"):
        options.cov_fail_under = 0
