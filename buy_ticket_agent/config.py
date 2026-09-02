"""Configuration helpers for the buy-ticket agent smoke path."""

from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from src.analysis.margin_metrics import parse_rate
from src.config.instance_paths import InstancePaths, load_instance_env


class SmokePaths(BaseModel):
    """Filesystem destinations used by the smoke path."""

    model_config = ConfigDict(frozen=True)

    instance_root: Path
    project_root: Path
    drafts_dir: Path
    runs_dir: Path
    bundles_dir: Path
    state_db: Path

    @classmethod
    def from_instance(cls, paths: InstancePaths | None = None) -> SmokePaths:
        """Build smoke output paths from one resolved instance layout."""
        instance_paths = paths or InstancePaths.resolve()
        return cls(
            instance_root=instance_paths.root,
            project_root=Path(__file__).resolve().parent.parent,
            drafts_dir=instance_paths.tickets / "auto-drafts",
            runs_dir=instance_paths.auto_tickets / "runs",
            bundles_dir=instance_paths.auto_tickets / "bundles",
            state_db=instance_paths.auto_tickets / "state.db",
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


def resolve_annual_margin_rate(paths: InstancePaths | None = None) -> float | None:
    """Load the authoritative annual margin rate from the instance environment."""
    instance_paths = paths or InstancePaths.resolve()
    load_instance_env(instance_paths, override=False)
    configured_rate = get_env("FG_MARGIN_INTEREST_RATE_DECIMAL") or get_env(
        "FG_MARGIN_INTEREST_RATE"
    )
    return parse_rate(configured_rate) if configured_rate is not None else None
