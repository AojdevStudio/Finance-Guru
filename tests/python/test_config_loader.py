"""Tests for config loader (Phase 6, CFG-01/02/03).

Validates HedgeConfig model constraints and the load_hedge_config()
function including YAML loading, graceful fallback on missing/malformed
files, and the CLI override priority chain.

Author: Finance Guru Development Team
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

# Add project root for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config.config_loader import HedgeConfig, load_hedge_config


def _write_profile(tmp_path: Path, hedging_data: dict | None = None) -> Path:
    """Write a user-profile.yaml with optional hedging section.

    Args:
        tmp_path: pytest tmp_path fixture directory.
        hedging_data: Dict of hedging config values. If None, the hedging
            section is omitted entirely from the YAML.

    Returns:
        Path to the written user-profile.yaml file.
    """
    profile: dict = {}
    if hedging_data is not None:
        profile["hedging"] = hedging_data
    path = tmp_path / "user-profile.yaml"
    with open(path, "w") as f:
        yaml.dump(profile, f)
    return path


class TestHedgeConfig:
    """Validate HedgeConfig Pydantic model constraints."""

    def test_defaults(self):
        """HedgeConfig() with no args should give sane defaults."""
        config = HedgeConfig()

        assert config.monthly_budget == 500.0
        assert config.roll_window_days == 7
        assert config.underlying_weights == {"QQQ": 1.0}
        assert config.target_dte_min == 60
        assert config.target_dte_max == 90
        assert config.min_otm_pct == 10.0
        assert config.max_otm_pct == 15.0
        assert config.sqqq_allocation_pct == 0.06

    def test_custom_values(self):
        """Passing explicit values should override all defaults."""
        config = HedgeConfig(
            monthly_budget=1200.0,
            roll_window_days=14,
            underlying_weights={"QQQ": 0.7, "SPY": 0.3},
            max_otm_pct=20.0,
            min_otm_pct=5.0,
            target_dte_min=30,
            target_dte_max=60,
            sqqq_allocation_pct=0.10,
        )

        assert config.monthly_budget == 1200.0
        assert config.roll_window_days == 14
        assert config.underlying_weights == {"QQQ": 0.7, "SPY": 0.3}
        assert config.max_otm_pct == 20.0
        assert config.min_otm_pct == 5.0
        assert config.target_dte_min == 30
        assert config.target_dte_max == 60
        assert config.sqqq_allocation_pct == 0.10

    def test_dte_min_must_be_less_than_max(self):
        """dte_min >= dte_max should raise ValidationError."""
        with pytest.raises(ValidationError, match="target_dte_min"):
            HedgeConfig(target_dte_min=100, target_dte_max=50)

        # Equal values should also fail
        with pytest.raises(ValidationError, match="target_dte_min"):
            HedgeConfig(target_dte_min=60, target_dte_max=60)

    def test_otm_min_must_be_less_than_max(self):
        """min_otm_pct >= max_otm_pct should raise ValidationError."""
        with pytest.raises(ValidationError, match="min_otm_pct"):
            HedgeConfig(min_otm_pct=20.0, max_otm_pct=10.0)

    def test_underlying_weights_must_be_uppercase(self):
        """Lowercase ticker keys should be auto-uppercased by validator."""
        # The validator uppercases keys, so {"qqq": 1.0} becomes {"QQQ": 1.0}
        config = HedgeConfig(underlying_weights={"qqq": 1.0})
        assert "QQQ" in config.underlying_weights

    def test_underlying_weights_must_sum_near_one(self):
        """Weights summing far from 1.0 should raise ValidationError."""
        with pytest.raises(ValidationError, match="sum"):
            HedgeConfig(underlying_weights={"QQQ": 0.5, "SPY": 0.3})

    def test_sqqq_allocation_range(self):
        """Valid sqqq_allocation_pct should pass; >1.0 should raise."""
        config = HedgeConfig(sqqq_allocation_pct=0.06)
        assert config.sqqq_allocation_pct == 0.06

        with pytest.raises(ValidationError):
            HedgeConfig(sqqq_allocation_pct=1.5)

    def test_negative_monthly_budget_rejected(self):
        """Negative monthly_budget should raise ValidationError."""
        with pytest.raises(ValidationError):
            HedgeConfig(monthly_budget=-100.0)


class TestLoadHedgeConfig:
    """Validate load_hedge_config() YAML loading and override chain."""

    def test_returns_defaults_when_no_yaml(self, tmp_path: Path):
        """Passing nonexistent path should return defaults (not crash)."""
        nonexistent = tmp_path / "does-not-exist.yaml"
        config = load_hedge_config(profile_path=nonexistent)

        assert config.monthly_budget == 500.0
        assert config.roll_window_days == 7

    def test_loads_from_yaml(self, tmp_path: Path):
        """YAML hedging section values should override defaults."""
        path = _write_profile(tmp_path, {"monthly_budget": 800})
        config = load_hedge_config(profile_path=path)

        assert config.monthly_budget == 800.0
        # Other fields should still use defaults
        assert config.roll_window_days == 7

    def test_ignores_missing_hedging_section(self, tmp_path: Path):
        """YAML without hedging section should return defaults (not crash)."""
        path = _write_profile(tmp_path, hedging_data=None)
        config = load_hedge_config(profile_path=path)

        assert config.monthly_budget == 500.0

    def test_handles_malformed_yaml(self, tmp_path: Path):
        """Invalid YAML content should return defaults (not crash)."""
        path = tmp_path / "user-profile.yaml"
        with open(path, "w") as f:
            f.write(": : : [invalid yaml\n{{{not closed")
        config = load_hedge_config(profile_path=path)

        assert config.monthly_budget == 500.0

    def test_cli_overrides_take_priority(self, tmp_path: Path):
        """CLI overrides should win over YAML values."""
        path = _write_profile(tmp_path, {"monthly_budget": 800})
        config = load_hedge_config(
            profile_path=path,
            cli_overrides={"monthly_budget": 1000},
        )

        assert config.monthly_budget == 1000.0

    def test_none_cli_overrides_are_ignored(self, tmp_path: Path):
        """None values in cli_overrides should be filtered out, keeping YAML values."""
        path = _write_profile(tmp_path, {"monthly_budget": 800})
        config = load_hedge_config(
            profile_path=path,
            cli_overrides={"monthly_budget": None, "roll_window_days": 14},
        )

        # None override ignored -- YAML value kept
        assert config.monthly_budget == 800.0
        # Non-None override applied
        assert config.roll_window_days == 14

    def test_cli_overrides_with_no_yaml(self):
        """CLI overrides should work even when no YAML file exists."""
        config = load_hedge_config(
            profile_path=Path("/nonexistent/path/user-profile.yaml"),
            cli_overrides={"monthly_budget": 1200},
        )

        assert config.monthly_budget == 1200.0

    def test_yaml_loads_multiple_fields(self, tmp_path: Path):
        """YAML with multiple hedging fields should all be loaded."""
        path = _write_profile(
            tmp_path,
            {
                "monthly_budget": 1000,
                "roll_window_days": 10,
                "sqqq_allocation_pct": 0.08,
            },
        )
        config = load_hedge_config(profile_path=path)

        assert config.monthly_budget == 1000.0
        assert config.roll_window_days == 10
        assert config.sqqq_allocation_pct == 0.08

    def test_yaml_with_underlying_weights(self, tmp_path: Path):
        """YAML underlying_weights should be loaded and validated."""
        path = _write_profile(
            tmp_path,
            {
                "underlying_weights": {"QQQ": 0.6, "SPY": 0.4},
            },
        )
        config = load_hedge_config(profile_path=path)

        assert config.underlying_weights == {"QQQ": 0.6, "SPY": 0.4}

    def test_empty_cli_overrides_dict(self, tmp_path: Path):
        """Empty cli_overrides dict should not affect YAML values."""
        path = _write_profile(tmp_path, {"monthly_budget": 750})
        config = load_hedge_config(
            profile_path=path,
            cli_overrides={},
        )

        assert config.monthly_budget == 750.0

    def test_full_override_chain(self, tmp_path: Path):
        """Full chain: default < YAML < CLI for same field."""
        # Default monthly_budget = 500
        # YAML monthly_budget = 800
        # CLI monthly_budget = 1500
        path = _write_profile(tmp_path, {"monthly_budget": 800})
        config = load_hedge_config(
            profile_path=path,
            cli_overrides={"monthly_budget": 1500},
        )

        # CLI wins
        assert config.monthly_budget == 1500.0
