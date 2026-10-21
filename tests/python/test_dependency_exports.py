"""Grouped dependency updates keep every requested package in the lock plan."""

import importlib.util
from pathlib import Path
from subprocess import CalledProcessError, CompletedProcess

import pytest


@pytest.fixture
def exports():
    path = Path(__file__).resolve().parents[2] / "scripts/qa/sync_dependency_exports.py"
    spec = importlib.util.spec_from_file_location("dependency_exports", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_every_grouped_pin_is_passed_to_the_canonical_lock(exports, mocker, tmp_path):
    diff = "+++ b/requirements.txt\n+gitpython==3.1.62\n+multidict==6.9.1\n+tornado==6.5.9\n+urllib3==2.8.0\n"
    calls = []

    def tool(command, **kwargs):
        calls.append(command)
        output = (
            diff
            if command[0] == "git"
            else "canonical export\n"
            if command[1] == "export"
            else ""
        )
        return CompletedProcess(command, 0, stdout=output)

    mocker.patch.object(exports.subprocess, "run", side_effect=tool)
    mocker.patch.object(exports.Path, "cwd", return_value=tmp_path)
    exports.synchronize("origin/main")
    lock = next(command for command in calls if command[:2] == ["uv", "lock"])
    for spec in [
        "gitpython==3.1.62",
        "multidict==6.9.1",
        "tornado==6.5.9",
        "urllib3==2.8.0",
    ]:
        assert lock[lock.index(spec) - 1] == "--upgrade-package"
    assert "--no-build" in lock
    export = next(command for command in calls if command[:2] == ["uv", "export"])
    assert "--frozen" in export
    assert (tmp_path / "requirements.txt").read_text() == "canonical export\n"


def test_lock_failure_does_not_replace_the_export(exports, mocker, tmp_path):
    requirements = tmp_path / "requirements.txt"
    requirements.write_text("original\n")
    mocker.patch.object(exports.Path, "cwd", return_value=tmp_path)

    def tool(command, **kwargs):
        if command[0] == "git":
            return CompletedProcess(command, 0, stdout="+first==2\n+second==3\n")
        raise CalledProcessError(1, command)

    mocker.patch.object(exports.subprocess, "run", side_effect=tool)
    with pytest.raises(CalledProcessError):
        exports.synchronize("origin/main")
    assert requirements.read_text() == "original\n"


@pytest.mark.parametrize(
    "diff", ["+same==1\n+same==2", "+package @ https://example.invalid/package.whl"]
)
def test_ambiguous_or_unpinned_requests_fail_closed(exports, diff):
    with pytest.raises(ValueError):
        exports.requested_upgrades(diff)
