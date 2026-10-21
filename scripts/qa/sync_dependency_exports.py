"""Reconcile every requested dependency pin, then export the canonical uv lock."""

import argparse
import re
import subprocess
import sys
import tomllib
from pathlib import Path

_PIN = re.compile(r"([A-Za-z0-9][A-Za-z0-9_.-]*)==([^\s;]+)(?:\s*;.*)?")


class LockDriftError(RuntimeError):
    """The resolver changed the lock in a way the pull request did not request."""


def _canonical(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name.lower())


def locked_versions(lock: str) -> dict[str, frozenset[str]]:
    """Map each package to every version the lock holds for it."""
    versions: dict[str, set[str]] = {}
    for package in tomllib.loads(lock).get("package", []):
        versions.setdefault(_canonical(package["name"]), set()).add(
            package.get("version", "")
        )
    return {name: frozenset(found) for name, found in versions.items()}


def lock_drift(before: str, after: str, requested: dict[str, str]) -> list[str]:
    """List every lock change that is not exactly one of the requested pins."""
    old, new = locked_versions(before), locked_versions(after)
    drift = [
        f"{name} {', '.join(sorted(old.get(name, ()))) or 'none'} -> "
        f"{', '.join(sorted(new.get(name, ()))) or 'none'}"
        for name in sorted(old.keys() | new.keys())
        if name not in requested and old.get(name) != new.get(name)
    ]
    drift.extend(
        f"{name} requested {version}, lock has {', '.join(sorted(new.get(name, ()))) or 'none'}"
        for name, version in requested.items()
        if new.get(name) != {version}
    )
    return drift


def requested_upgrades(diff: str) -> dict[str, str]:
    """Read all added pins without treating a grouped update as one package."""
    requested: dict[str, str] = {}
    for line in diff.splitlines():
        if not line.startswith("+") or line.startswith("+++"):
            continue
        requirement = line[1:].strip()
        if not requirement or requirement.startswith("#"):
            continue
        match = _PIN.fullmatch(requirement)
        if match is None:
            raise ValueError("Dependency repair requires exact package pins")
        name, version = match.groups()
        name = _canonical(name)
        if name in requested and requested[name] != version:
            raise ValueError("Dependency repair cannot choose between conflicting pins")
        requested[name] = version
    return requested


def synchronize(base: str) -> None:
    """Resolve the requested pins together and write only a successful export.

    ``--no-build`` keeps the resolver from running package build code, but it also
    makes uv silently move any sdist-only locked package to a version with wheels.
    """
    root = Path.cwd()
    lock = root / "uv.lock"
    diff = subprocess.run(
        ["git", "diff", "--unified=0", f"{base}...HEAD", "--", "requirements.txt"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    requested = requested_upgrades(diff)
    command = ["uv", "lock", "--no-build"]
    for name, version in requested.items():
        command.extend(["--upgrade-package", f"{name}=={version}"])
    before = lock.read_text(encoding="utf-8")
    subprocess.run(command, check=True)
    drift = lock_drift(before, lock.read_text(encoding="utf-8"), requested)
    if drift:
        lock.write_text(before, encoding="utf-8")
        raise LockDriftError(
            "Unrequested lock changes need human review: " + "; ".join(drift)
        )
    exported = subprocess.run(
        [
            "uv",
            "export",
            "--format",
            "requirements.txt",
            "--no-hashes",
            "--no-emit-project",
            "--frozen",
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    (root / "requirements.txt").write_text(exported, encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    try:
        synchronize(parser.parse_args().base)
    except LockDriftError as error:
        sys.exit(str(error))
