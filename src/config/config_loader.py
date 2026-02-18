"""Finance Guru Hedge Configuration Loader.

WHAT: DRY bridge between user-profile.yaml and all hedging CLIs.
WHY: Prevents each CLI from duplicating YAML parsing, validation, and override
     logic. Every hedging tool (hedge_sizer, rolling_tracker, sqqq_comparison,
     total_return) calls load_hedge_config() instead of rolling its own parser.

ARCHITECTURE NOTE:
    Priority chain for every config field:
        CLI flags  >  YAML file  >  Pydantic defaults

    1. Pydantic defaults provide sane values out of the box.
    2. user-profile.yaml ``hedging:`` section overrides defaults.
    3. CLI flags (passed as cli_overrides dict) override everything.

    This means a user can run any hedging CLI with zero configuration and get
    reasonable behavior, or fine-tune via YAML, or one-shot override via flags.
"""

from __future__ import annotations

import logging
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent
"""Project root directory (three levels up from src/config/config_loader.py)."""

_PROFILE_SEARCH_PATHS = [
    PROJECT_ROOT / "fin-guru-private" / "data" / "user-profile.yaml",
    PROJECT_ROOT / "fin-guru" / "data" / "user-profile.yaml",
]
"""Ordered list of paths to search for user-profile.yaml."""


class HedgeConfig(BaseModel):
    """Validated hedging configuration shared by all hedging CLIs.

    WHAT: Pydantic model holding every tunable knob for the hedging subsystem.
    WHY: Single source of truth that each CLI imports instead of defining its
         own ad-hoc config parsing.
    VALIDATES: Field ranges, DTE ordering, OTM ordering, weight normalization.
    """

    monthly_budget: float = Field(
        default=500.0,
        ge=0.0,
        description="Monthly hedge budget in dollars",
    )
    roll_window_days: int = Field(
        default=7,
        ge=1,
        le=30,
        description="Days before expiry to trigger roll suggestion",
    )
    underlying_weights: dict[str, float] = Field(
        default_factory=lambda: {"QQQ": 1.0},
        description="Hedge allocation weights by underlying ticker",
    )
    max_otm_pct: float = Field(
        default=15.0,
        ge=1.0,
        le=50.0,
        description="Maximum out-of-the-money percentage",
    )
    min_otm_pct: float = Field(
        default=10.0,
        ge=0.0,
        le=50.0,
        description="Minimum out-of-the-money percentage",
    )
    target_dte_min: int = Field(
        default=60,
        ge=7,
        description="Minimum days to expiry for new positions",
    )
    target_dte_max: int = Field(
        default=90,
        ge=14,
        description="Maximum days to expiry for new positions",
    )
    sqqq_allocation_pct: float = Field(
        default=0.06,
        ge=0.0,
        le=1.0,
        description="SQQQ allocation as fraction of hedge budget",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "monthly_budget": 800.0,
                "roll_window_days": 7,
                "underlying_weights": {"QQQ": 0.7, "SPY": 0.3},
                "max_otm_pct": 15.0,
                "min_otm_pct": 10.0,
                "target_dte_min": 60,
                "target_dte_max": 90,
                "sqqq_allocation_pct": 0.06,
            }
        }
    )

    @field_validator("underlying_weights")
    @classmethod
    def validate_underlying_weights(cls, v: dict[str, float]) -> dict[str, float]:
        """Ensure all ticker keys are uppercase and values are positive.

        Warns if weights do not sum to approximately 1.0 (tolerance: 0.05).
        """
        normalized: dict[str, float] = {}
        for key, value in v.items():
            upper_key = key.upper()
            if value <= 0:
                msg = f"Weight for {upper_key} must be positive, got {value}"
                raise ValueError(msg)
            normalized[upper_key] = value

        weight_sum = sum(normalized.values())
        if abs(weight_sum - 1.0) > 0.05:
            msg = (
                f"underlying_weights sum to {weight_sum:.4f}, "
                f"expected ~1.0 (deviation > 0.05)"
            )
            raise ValueError(msg)

        return normalized

    @model_validator(mode="after")
    def validate_field_ordering(self) -> HedgeConfig:
        """Ensure DTE and OTM ranges are correctly ordered."""
        if self.target_dte_min >= self.target_dte_max:
            msg = (
                f"target_dte_min ({self.target_dte_min}) must be less than "
                f"target_dte_max ({self.target_dte_max})"
            )
            raise ValueError(msg)
        if self.min_otm_pct >= self.max_otm_pct:
            msg = (
                f"min_otm_pct ({self.min_otm_pct}) must be less than "
                f"max_otm_pct ({self.max_otm_pct})"
            )
            raise ValueError(msg)
        return self


def load_hedge_config(
    profile_path: Path | None = None,
    cli_overrides: dict | None = None,
) -> HedgeConfig:
    """Load hedging configuration with the priority chain: CLI > YAML > defaults.

    Args:
        profile_path: Explicit path to user-profile.yaml. If None, searches
            ``_PROFILE_SEARCH_PATHS`` for the first existing file.
        cli_overrides: Dict of CLI flag values. Keys with None values are
            ignored (only non-None values override).

    Returns:
        Validated HedgeConfig instance with merged configuration.

    Notes:
        This function NEVER raises on missing or malformed YAML. It always
        returns a valid HedgeConfig, falling back to Pydantic defaults when
        the YAML source is unavailable or unparseable (CFG-03).
    """
    config_data: dict = {}

    # --- Resolve profile path ---
    resolved_path = profile_path
    if resolved_path is None:
        for candidate in _PROFILE_SEARCH_PATHS:
            if candidate.exists():
                resolved_path = candidate
                break

    # --- Load YAML hedging section ---
    if resolved_path is not None and resolved_path.exists():
        try:
            with open(resolved_path) as f:
                data = yaml.safe_load(f)
            if isinstance(data, dict):
                config_data = data.get("hedging", {})
                if not isinstance(config_data, dict):
                    config_data = {}
        except Exception:
            logger.warning("Failed to parse %s, using defaults", resolved_path)
            config_data = {}

    # --- Apply CLI overrides (filter out None values) ---
    if cli_overrides:
        config_data.update({k: v for k, v in cli_overrides.items() if v is not None})

    return HedgeConfig(**config_data)
