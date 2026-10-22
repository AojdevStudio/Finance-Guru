"""The repair baseline supports package resolution without running builds."""

import subprocess
import sys
import tomllib
from pathlib import Path

import pytest


@pytest.mark.parametrize("name", ["peewee", "multitasking"])
def test_yfinance_cache_dependencies_have_universal_wheels(name):
    lock = Path(__file__).resolve().parents[2] / "uv.lock"
    packages = tomllib.loads(lock.read_text())["package"]
    package = next(package for package in packages if package["name"] == name)
    assert any(
        wheel["url"].endswith("-py3-none-any.whl")
        for wheel in package.get("wheels", [])
    ), f"{name} requires a source build and blocks safe dependency repair"


def test_yfinance_cache_and_tasks_work_without_extension_modules(tmp_path):
    probe = """
import sys
import threading
import multitasking
import yfinance
import yfinance.cache

yfinance.set_tz_cache_location(sys.argv[1])
cache = yfinance.cache.get_tz_cache()
cache.store('SYNTHETIC', 'UTC')
assert cache.lookup('SYNTHETIC') == 'UTC'
cache.store('SYNTHETIC', None)
assert cache.lookup('SYNTHETIC') is None

finished = threading.Event()
@multitasking.task
def task():
    finished.set()
task()
assert finished.wait(3)
"""
    subprocess.run([sys.executable, "-c", probe, str(tmp_path)], check=True)
