"""Shared ticker symbol type for the input models."""

from typing import Annotated

from pydantic import Field

Ticker = Annotated[str, Field(min_length=1, max_length=10, pattern=r"^[A-Z\-\.]+$")]
"""An uppercase exchange ticker such as "TSLA" or "BRK-B"."""
