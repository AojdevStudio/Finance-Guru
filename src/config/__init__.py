"""Finance Guru Config Package.

Provides validated configuration loading for hedging and portfolio tools.

Re-exports:
    FinGuruConfig: TUI dashboard configuration (layers, paths)
    HedgeConfig: Hedging strategy configuration model
    InstancePaths: Resolved private instance layout
    load_hedge_config: Load and merge hedging config from YAML + CLI overrides
    load_instance_env: Load the instance-specific .env file
"""

from src.config.config_loader import HedgeConfig, load_hedge_config
from src.config.fin_guru_config import FinGuruConfig
from src.config.instance_paths import InstancePaths, load_instance_env

__all__ = [
    "FinGuruConfig",
    "HedgeConfig",
    "InstancePaths",
    "load_hedge_config",
    "load_instance_env",
]
