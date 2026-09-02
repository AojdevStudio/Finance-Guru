import tomllib
from pathlib import Path

from packaging.requirements import Requirement
from packaging.version import Version


def test_snaptrade_sdk_stays_on_supported_major_version() -> None:
    pyproject_path = Path(__file__).parents[2] / "pyproject.toml"
    pyproject = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    requirement = next(
        Requirement(dependency)
        for dependency in pyproject["project"]["dependencies"]
        if Requirement(dependency).name == "snaptrade-python-sdk"
    )

    assert Version("11.0.197") in requirement.specifier
    assert Version("11.999.999") in requirement.specifier
    assert Version("12.0.0") not in requirement.specifier
