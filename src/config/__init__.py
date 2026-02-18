"""Finance Guru Config Package.

Provides validated configuration loading for hedging and portfolio tools.

Re-exports:
    FinGuruConfig: TUI dashboard configuration (layers, paths)
    HedgeConfig: Hedging strategy configuration model
    load_hedge_config: Load and merge hedging config from YAML + CLI overrides
"""

from src.config.fin_guru_config import FinGuruConfig

__all__: list[str] = ["FinGuruConfig"]

# HedgeConfig and load_hedge_config from config_loader.py.
# Conditionally imported to avoid breaking when config_loader doesn't exist yet.
try:
    from src.config.config_loader import HedgeConfig, load_hedge_config

    __all__ += ["HedgeConfig", "load_hedge_config"]
except ImportError:
    pass
