"""Reconcile every requested dependency pin, then export the canonical uv lock."""

import argparse
import re
import subprocess
from pathlib import Path

_PIN = re.compile(r"([A-Za-z0-9][A-Za-z0-9_.-]*)==([^\s;]+)(?:\s*;.*)?")


def requested_upgrades(diff: str) -> list[str]:
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
        name = re.sub(r"[-_.]+", "-", name.lower())
        if name in requested and requested[name] != version:
            raise ValueError("Dependency repair cannot choose between conflicting pins")
        requested[name] = version
    return [f"{name}=={version}" for name, version in requested.items()]


def synchronize(base: str) -> None:
    """Resolve the requested pins together and write only a successful export."""
    root = Path.cwd()
    diff = subprocess.run(
        ["git", "diff", "--unified=0", f"{base}...HEAD", "--", "requirements.txt"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    command = ["uv", "lock", "--no-build"]
    for package in requested_upgrades(diff):
        command.extend(["--upgrade-package", package])
    subprocess.run(command, check=True)
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
    synchronize(parser.parse_args().base)
