"""``src.utils.log`` falls back to stdlib logging when structlog is absent.

structlog is a dev-only dependency, so an end-user install runs this branch.
"""

import importlib
import logging
import sys
from collections.abc import Iterator
from types import ModuleType

import pytest

import src.utils.log


@pytest.fixture
def log_without_structlog(monkeypatch: pytest.MonkeyPatch) -> Iterator[ModuleType]:
    monkeypatch.setitem(sys.modules, "structlog", None)
    yield importlib.reload(src.utils.log)
    monkeypatch.undo()
    importlib.reload(src.utils.log)


def test_get_logger_returns_stdlib_logger(log_without_structlog: ModuleType) -> None:
    logger = log_without_structlog.get_logger("finance_guru.test")

    assert log_without_structlog.structlog is None
    assert isinstance(logger, logging.Logger)
    assert logger.name == "finance_guru.test"


def test_configure_logging_sets_up_stdlib(
    log_without_structlog: ModuleType, mocker
) -> None:
    basic_config = mocker.patch("logging.basicConfig")

    log_without_structlog.configure_logging(logging.WARNING)

    basic_config.assert_called_once_with(level=logging.WARNING, stream=sys.stderr)
