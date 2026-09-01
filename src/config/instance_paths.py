"""Resolve every private Finance Guru path from one instance root."""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict


class InstancePaths(BaseModel):
    """Every file the engine reads or writes for one family office instance."""

    model_config = ConfigDict(frozen=True)

    root: Path

    @classmethod
    def resolve(
        cls,
        env: Mapping[str, str] | None = None,
        cwd: Path | None = None,
    ) -> InstancePaths:
        """Resolve an absolute instance root from the environment or cwd."""
        environment = os.environ if env is None else env
        working_directory = (cwd or Path.cwd()).expanduser().resolve()
        configured_root = environment.get("FIN_GURU_DATA_ROOT", "").strip()
        root = (
            Path(configured_root).expanduser() if configured_root else working_directory
        )
        if not root.is_absolute():
            root = working_directory / root
        return cls(root=root.resolve())

    @property
    def env_file(self) -> Path:
        """Return the instance environment file."""
        return self.root / ".env"

    @property
    def profile(self) -> Path:
        """Return the user profile path."""
        return self.root / "user-profile.yaml"

    @property
    def config(self) -> Path:
        """Return the instance configuration path."""
        return self.root / "config.yaml"

    @property
    def snaptrade_accounts(self) -> Path:
        """Return the SnapTrade account-routing configuration path."""
        return self.root / "snaptrade-accounts.yaml"

    @property
    def system_context(self) -> Path:
        """Return the generated system context path."""
        return self.root / "system-context.md"

    @property
    def db(self) -> Path:
        """Return the default family-office database path."""
        return self.root / "family_office.db"

    @property
    def imports(self) -> Path:
        """Return the broker CSV import directory."""
        return self.root / "imports"

    @property
    def analysis(self) -> Path:
        """Return the analysis artifact directory."""
        return self.root / "analysis"

    @property
    def tickets(self) -> Path:
        """Return the buy-ticket directory."""
        return self.root / "tickets"

    @property
    def strategies(self) -> Path:
        """Return the strategy document directory."""
        return self.root / "strategies"

    @property
    def hedging(self) -> Path:
        """Return the hedge position and history directory."""
        return self.root / "hedging"

    @property
    def reports(self) -> Path:
        """Return the report artifact directory."""
        return self.root / "reports"

    @property
    def dividend_schedules(self) -> Path:
        """Return the dividend schedule file path."""
        return self.root / "dividend-schedules.yaml"

    @property
    def auto_tickets(self) -> Path:
        """Return the automated-ticket runtime directory."""
        return self.root / "auto-tickets"

    def database_url(self, env: Mapping[str, str] | None = None) -> str:
        """Return the configured database URL with relative paths under root."""
        environment = os.environ if env is None else env
        configured_url = environment.get("DATABASE_URL", "").strip()
        if not configured_url:
            return _sqlite_url(self.db)
        if configured_url in {":memory:", "sqlite:///:memory:"}:
            return "sqlite:///:memory:"
        if configured_url.startswith("sqlite:///"):
            database_path = Path(configured_url.removeprefix("sqlite:///"))
        elif "://" in configured_url:
            return configured_url
        else:
            database_path = Path(configured_url).expanduser()
        if not database_path.is_absolute():
            database_path = self.root / database_path
        return _sqlite_url(database_path.resolve())


def _sqlite_url(path: Path) -> str:
    """Format a filesystem path as a SQLite URL."""
    return f"sqlite:///{path}"


def _db_path(
    database_url: str | None = None,
    paths: InstancePaths | None = None,
) -> Path:
    """Resolve a SQLite URL or bare path to one absolute filesystem path."""
    instance_paths = paths or InstancePaths.resolve()
    environment = None if database_url is None else {"DATABASE_URL": database_url}
    resolved_url = instance_paths.database_url(environment)
    if resolved_url == "sqlite:///:memory:":
        return Path(":memory:")
    if resolved_url.startswith("sqlite:///"):
        return Path(resolved_url.removeprefix("sqlite:///"))
    scheme, separator, _ = resolved_url.partition("://")
    if separator and scheme != "sqlite":
        raise ValueError(
            f"Finance Guru only supports sqlite databases, got {scheme}://"
        )
    raise ValueError(f"Invalid SQLite database URL: {resolved_url}")


def load_instance_env(paths: InstancePaths, override: bool = False) -> None:
    """Load the instance's environment file into the process environment."""
    load_dotenv(paths.env_file, override=override)
