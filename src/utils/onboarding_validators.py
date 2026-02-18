"""Onboarding Wizard Validation Utilities for Finance Guru.

Domain-specific validators for financial input (currency, percentage,
positive integer) and a retry-with-skip wrapper around questionary prompts
that implements the ONBD-02 requirement: after 3 failed validation attempts
the user is offered a skip option with a sensible default.

Author: Finance Guru Development Team
Created: 2026-02-05
"""

import re
from collections.abc import Callable
from typing import Any

import questionary

# ---------------------------------------------------------------------------
# Domain validators
# ---------------------------------------------------------------------------


def validate_currency(value: str) -> float:
    """Parse currency strings into a float.

    Accepted formats:
        "$10,000.50", "10000", "10,000", "$25k", "25K", "1.5m", "$1.5M"

    Args:
        value: Raw user input string.

    Returns:
        Parsed float value.

    Raises:
        ValueError: If the input cannot be parsed as a dollar amount.
    """
    cleaned = value.strip().lstrip("$").replace(",", "").strip()
    if not cleaned:
        raise ValueError("Please enter a dollar amount. Try: 25000, $25,000, or 25k")

    # Handle shorthand multipliers: 25k, 1.5m
    multiplier = 1.0
    suffix_match = re.match(r"^([0-9]*\.?[0-9]+)\s*([kKmM])$", cleaned)
    if suffix_match:
        cleaned = suffix_match.group(1)
        suffix = suffix_match.group(2).lower()
        if suffix == "k":
            multiplier = 1_000.0
        elif suffix == "m":
            multiplier = 1_000_000.0

    try:
        result = float(cleaned) * multiplier
    except ValueError as e:
        raise ValueError(
            f"'{value.strip()}' doesn't look like a dollar amount. "
            "Try: 25000, $25,000, or 25k"
        ) from e

    if result < 0:
        raise ValueError("Dollar amounts cannot be negative.")

    return result


def validate_percentage(value: str) -> float:
    """Parse percentage strings into a float (as percentage, not decimal).

    Accepted formats:
        "4.5%", "4.5", "0.045" (treated as 0.045% -- users should enter 4.5 for 4.5%)

    Args:
        value: Raw user input string.

    Returns:
        Percentage as a float (e.g., 4.5 for 4.5%).

    Raises:
        ValueError: If the input is not a valid percentage in 0-100.
    """
    cleaned = value.strip().rstrip("%").strip()
    if not cleaned:
        raise ValueError("Please enter a percentage. Try: 4.5 for 4.5%")

    try:
        result = float(cleaned)
    except ValueError as e:
        raise ValueError(
            f"'{value.strip()}' doesn't look like a percentage. Try: 4.5 for 4.5%"
        ) from e

    if result < 0 or result > 100:
        raise ValueError(
            f"Percentage must be between 0 and 100, got {result}. "
            "Enter 4.5 for 4.5%, not 0.045."
        )

    return result


def validate_positive_integer(value: str) -> int:
    """Parse a positive integer from user input.

    Args:
        value: Raw user input string.

    Returns:
        Parsed positive integer.

    Raises:
        ValueError: If the input is not a positive integer.
    """
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("Please enter a positive whole number.")

    try:
        result = int(cleaned)
    except ValueError as e:
        raise ValueError(
            f"'{cleaned}' is not a whole number. Please enter a positive integer."
        ) from e

    if result <= 0:
        raise ValueError(
            f"Expected a positive number, got {result}. Please enter a number greater than 0."
        )

    return result


# ---------------------------------------------------------------------------
# Retry-with-skip wrapper
# ---------------------------------------------------------------------------


def ask_with_retry(
    prompt_fn: Callable[[], Any],
    validator: Callable[[Any], Any] | None = None,
    default: Any = None,
    max_retries: int = 3,
) -> Any:
    """Prompt the user with automatic retry and skip-on-failure logic.

    Calls *prompt_fn* to collect user input. If *validator* is provided the
    raw value is passed through it. On validation failure the user gets a
    clear error message and another attempt (up to *max_retries*).

    After exhausting retries the user is offered a skip option via
    ``questionary.confirm`` with the supplied *default* value. If the user
    declines the skip they get one final attempt.

    Ctrl+C (None return from questionary) is handled gracefully by
    returning *default* immediately.

    Args:
        prompt_fn: Callable that invokes a questionary prompt and returns
            the raw value (e.g., ``lambda: questionary.text("Q").ask()``).
        validator: Optional callable that validates/transforms the raw value.
            Should raise ``ValueError`` on bad input.
        default: Fallback value returned when the user skips or cancels.
        max_retries: Maximum validation attempts before offering skip.

    Returns:
        The validated value, or *default* if the user skips/cancels.
    """
    attempts = 0

    while attempts < max_retries:
        raw = prompt_fn()

        # Ctrl+C returns None from questionary
        if raw is None:
            return default

        if validator is None:
            return raw

        try:
            return validator(raw)
        except (ValueError, TypeError) as exc:
            attempts += 1
            remaining = max_retries - attempts
            if remaining > 0:
                print(f"  Invalid input (attempt {attempts}/{max_retries}): {exc}")
            else:
                print(f"  Invalid input (attempt {attempts}/{max_retries}): {exc}")

    # All retries exhausted -- offer skip with default
    default_display = default if default is not None else "empty"
    skip = questionary.confirm(
        f"  Use default value ({default_display}) and continue?",
        default=True,
    ).ask()

    if skip is None:
        # Ctrl+C during skip prompt
        return default

    if skip:
        return default

    # User declined skip -- one more chance
    raw = prompt_fn()
    if raw is None:
        return default

    if validator is None:
        return raw

    try:
        return validator(raw)
    except (ValueError, TypeError):
        print(f"  Still invalid. Using default value ({default_display}).")
        return default
