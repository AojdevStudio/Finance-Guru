"""Structured logging with PII scrubbing for Finance Guru.

This module wraps _structlog_ to give every Finance Guru script a
consistent, machine-parseable log format. A small processor pipeline
redacts / scrubs common forms of PII (SSN, credit cards, API tokens,
email local parts) before events ever reach stdout or a log sink.

Usage:
    from src.utils.logging import get_logger

    log = get_logger(__name__)
    log.info("analysis_started", ticker="TSLA", days=90)

In a TTY the logger renders in a human-friendly dev format; in CI or
when stderr is redirected it emits JSON for log aggregators.
"""

from __future__ import annotations

import logging
import re
import sys
from collections.abc import Mapping
from typing import Any

structlog: Any
try:
    import structlog as _structlog  # third-party, comes from dev deps

    structlog = _structlog
except ImportError:  # pragma: no cover - import-time guard
    structlog = None

__all__ = ["get_logger", "scrub_pii", "ScrubPIIProcessor", "configure_logging"]


_SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_CARD_RE = re.compile(r"\b\d{13,19}\b")
_API_TOKEN_RE = re.compile(r"\b(sk|pk|ghp|ghs)[-_][A-Za-z0-9]{4,}\b")
_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")


def scrub_pii(value: str) -> str:
    """Redact common PII patterns from a free-form string.

    Patterns handled:
        - SSN (NNN-NN-NNNN) → ``***-**-****``
        - 13-19 digit sequences (credit cards) → ``****``
        - API tokens prefixed with sk/pk/ghp/ghs → prefix + ``***``
        - Email addresses → ``***@domain.tld`` (local part redacted)

    Args:
        value: Arbitrary text that may contain PII.

    Returns:
        The same text with matches scrubbed.
    """
    if not isinstance(value, str):
        return value
    redacted = _SSN_RE.sub("***-**-****", value)
    redacted = _CARD_RE.sub("****", redacted)
    redacted = _API_TOKEN_RE.sub(lambda m: f"{m.group(0)[:4]}***", redacted)
    redacted = _EMAIL_RE.sub(lambda m: "***@" + m.group(0).split("@", 1)[1], redacted)
    return redacted


class ScrubPIIProcessor:
    """Structlog processor that scrubs PII from every event dict value."""

    def __call__(
        self,
        logger: Any,
        method_name: str,
        event_dict: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Walk the event dict and scrub all string leaves."""
        scrubbed: dict[str, Any] = {}
        for key, val in event_dict.items():
            if isinstance(val, str):
                scrubbed[key] = scrub_pii(val)
            elif isinstance(val, Mapping):
                scrubbed[key] = {
                    k: scrub_pii(v) if isinstance(v, str) else v for k, v in val.items()
                }
            else:
                scrubbed[key] = val
        return scrubbed


def configure_logging(level: int = logging.INFO) -> None:
    """Configure structlog + stdlib logging.

    Chooses JSON output when stderr is not a TTY (CI, redirected logs)
    and pretty console output otherwise.
    """
    if structlog is None:  # pragma: no cover
        logging.basicConfig(level=level, stream=sys.stderr)
        return

    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        ScrubPIIProcessor(),
    ]

    if sys.stderr.isatty():
        renderer: Any = structlog.dev.ConsoleRenderer(colors=True)
    else:
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> Any:
    """Return a configured structured logger.

    Args:
        name: Usually ``__name__`` of the calling module.

    Returns:
        A bound structlog logger, or the stdlib logger as a fallback
        if structlog is not installed.
    """
    if structlog is None:  # pragma: no cover
        return logging.getLogger(name)
    configure_logging()
    return structlog.get_logger(name)
