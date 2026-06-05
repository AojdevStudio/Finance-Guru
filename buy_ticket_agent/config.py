"""Configuration helpers for the buy-ticket agent smoke path."""

from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, ConfigDict


class SmokePaths(BaseModel):
    """Filesystem destinations used by the smoke path."""

    model_config = ConfigDict(frozen=True)

    project_root: Path
    drafts_dir: Path
    runs_dir: Path
    state_db: Path

    @classmethod
    def from_project_root(cls, project_root: Path | None = None) -> SmokePaths:
        """Build default smoke output paths from the repository root."""
        root = project_root or Path.cwd()
        return cls(
            project_root=root,
            drafts_dir=root
            / "fin-guru-private"
            / "fin-guru"
            / "tickets"
            / "auto-drafts",
            runs_dir=root / "notebooks" / "auto-tickets" / "runs",
            state_db=root / "notebooks" / "auto-tickets" / "state.db",
        )


class NotificationConfig(BaseModel):
    """ntfy configuration resolved from environment and Bitwarden."""

    model_config = ConfigDict(frozen=True)

    server_url: str
    topic: str
    source: str


def get_env(name: str, default: str | None = None) -> str | None:
    """Return an environment variable after trimming empty values."""
    value = os.getenv(name, default)
    if value is None:
        return None
    value = value.strip()
    return value or None
