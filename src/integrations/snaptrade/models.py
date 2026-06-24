"""Pydantic models for the read-only SnapTrade integration."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Self

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_serializer


class SnapTradeCredentials(BaseModel):
    """Credential bundle required for read-only SnapTrade calls."""

    client_id: SecretStr = Field(min_length=1)
    consumer_key: SecretStr = Field(min_length=1)
    user_id: SecretStr = Field(min_length=1)
    user_secret: SecretStr = Field(min_length=1)

    @classmethod
    def from_env(cls) -> Self:
        """Load SnapTrade credentials from the local `.env`/process environment."""
        load_dotenv()
        required = {
            "client_id": "SNAPTRADE_CLIENT_ID",
            "consumer_key": "SNAPTRADE_CONSUMER_KEY",
            "user_id": "SNAPTRADE_USER_ID",
            "user_secret": "SNAPTRADE_USER_SECRET",
        }
        values: dict[str, str] = {}
        missing: list[str] = []
        for field_name, env_name in required.items():
            value = os.getenv(env_name)
            if value is None or value.strip() == "":
                missing.append(env_name)
            else:
                values[field_name] = value.strip()
        if missing:
            missing_keys = ", ".join(missing)
            raise ValueError(
                f"Missing required SnapTrade environment keys: {missing_keys}"
            )
        return cls(
            client_id=SecretStr(values["client_id"]),
            consumer_key=SecretStr(values["consumer_key"]),
            user_id=SecretStr(values["user_id"]),
            user_secret=SecretStr(values["user_secret"]),
        )

    @field_serializer("client_id", "consumer_key", "user_id", "user_secret")
    def _serialize_secret(self, value: SecretStr) -> str:
        """Prevent accidental secret disclosure in JSON/log output."""
        return "**********" if value.get_secret_value() else ""

    @property
    def client_id_value(self) -> str:
        """Return raw client id for SDK initialization."""
        return self.client_id.get_secret_value()

    @property
    def consumer_key_value(self) -> str:
        """Return raw consumer key for SDK initialization."""
        return self.consumer_key.get_secret_value()

    @property
    def user_id_value(self) -> str:
        """Return raw user id for SDK requests."""
        return self.user_id.get_secret_value()

    @property
    def user_secret_value(self) -> str:
        """Return raw user secret for SDK requests."""
        return self.user_secret.get_secret_value()


class SnapTradeAccount(BaseModel):
    """Normalized SnapTrade account used by Finance Guru skills."""

    id: str
    name: str = ""
    institution_name: str = ""
    type: str = ""
    currency: str | None = None
    number_masked: str | None = None
    balance_total: float | None = None
    raw: dict[str, Any] = Field(default_factory=dict, exclude=True)


class AccountRole(StrEnum):
    """Explicit Finance Guru routing roles for SnapTrade accounts."""

    UNASSIGNED = "unassigned"
    TAXABLE_CASH = "taxable_cash"
    TAXABLE_MARGIN = "taxable_margin"
    RETIREMENT = "retirement"
    WATCH_ONLY = "watch_only"


class SnapTradeAccountConfig(BaseModel):
    """Local account routing config for future Sheet sync phases."""

    snaptrade_account_id: str
    name: str = ""
    institution: str = ""
    role: AccountRole = AccountRole.UNASSIGNED
    enabled: bool = False
    notes: str = "Set role and enabled=true only after CSV-vs-SnapTrade verification."

    @property
    def refusal_reason(self) -> str | None:
        """Return why this account must not live-sync, or None if it may.

        Implements the issue-71 guardrail: an account syncs only after it has
        been verified and routed. ``enabled=false`` or ``role=unassigned`` both
        keep it out of live sync.
        """
        reasons: list[str] = []
        if not self.enabled:
            reasons.append("enabled=false")
        if self.role == AccountRole.UNASSIGNED:
            reasons.append("role=unassigned")
        return ", ".join(reasons) if reasons else None

    @property
    def is_syncable(self) -> bool:
        """Whether the account is verified-and-routed for live sync."""
        return self.refusal_reason is None


class SnapTradeAccountsConfig(BaseModel):
    """Config file mapping SnapTrade accounts to Finance Guru Sheet roles."""

    model_config = ConfigDict(use_enum_values=True)

    generated_at: str = Field(
        default_factory=lambda: datetime.now(UTC).replace(microsecond=0).isoformat()
    )
    accounts: list[SnapTradeAccountConfig]

    @classmethod
    def from_accounts(cls, accounts: list[SnapTradeAccount]) -> Self:
        """Create a conservative local config from discovered accounts."""
        return cls(
            accounts=[
                SnapTradeAccountConfig(
                    snaptrade_account_id=account.id,
                    name=_safe_config_account_name(account),
                    institution=account.institution_name,
                )
                for account in accounts
            ]
        )

    @classmethod
    def from_path(cls, path: Path) -> Self:
        """Load and validate the account routing config from a YAML file."""
        if not path.exists():
            raise FileNotFoundError(f"SnapTrade routing config not found: {path}")
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return cls.model_validate(data)

    @property
    def syncable(self) -> list[SnapTradeAccountConfig]:
        """Accounts cleared for live sync (enabled and role-assigned)."""
        return [account for account in self.accounts if account.is_syncable]


def _safe_config_account_name(account: SnapTradeAccount) -> str:
    """Avoid persisting personal brokerage display names in local config."""
    suffix = account.id[-6:] if len(account.id) >= 6 else account.id
    prefix = account.institution_name or "SnapTrade"
    return f"{prefix} account ...{suffix}"
