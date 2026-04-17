"""Environment-variable-driven feature flag system for Finance Guru.

A tiny, dependency-free feature flag layer that reads boolean flags
from environment variables prefixed ``FG_FLAG_``. Useful for gating
experimental CLIs, alternative calculation paths, or Desktop preview
features without shipping a full feature_flag platform.

Usage:
    from src.utils.feature_flags import flags

    if flags.enabled("NEW_HEDGING_MODEL"):
        run_new_hedging_model()
    else:
        run_stable_hedging_model()

Set the env var to enable: ``export FG_FLAG_NEW_HEDGING_MODEL=true``.
Truthy values: ``1``, ``true``, ``yes``, ``on`` (case-insensitive).
"""

from __future__ import annotations

import os
from typing import Final

__all__ = ["FeatureFlag", "flags"]

_PREFIX: Final[str] = "FG_FLAG_"
_TRUTHY: Final[frozenset[str]] = frozenset({"1", "true", "yes", "on"})


class FeatureFlag:
    """Reads feature flags from the process environment.

    Keep it boring: one flag = one env var. No remote config, no
    rollout percentages — if you need those, graduate to LaunchDarkly,
    Statsig, or Unleash.
    """

    prefix: str = _PREFIX

    def enabled(self, name: str, default: bool = False) -> bool:
        """Return True if the given feature flag is enabled.

        Args:
            name: Flag name without the ``FG_FLAG_`` prefix.
                Case-insensitive (internally upper-cased).
            default: Value to return when the env var is not set.

        Returns:
            True if the flag is set to a truthy value, else ``default``.
        """
        env_key = f"{self.prefix}{name.upper()}"
        raw = os.environ.get(env_key)
        if raw is None:
            return default
        return raw.strip().lower() in _TRUTHY

    def all_enabled(self) -> dict[str, bool]:
        """Return a snapshot of all currently-set feature flags."""
        return {
            key[len(self.prefix) :].lower(): val.strip().lower() in _TRUTHY
            for key, val in os.environ.items()
            if key.startswith(self.prefix)
        }


flags = FeatureFlag()
