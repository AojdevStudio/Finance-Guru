"""Finance Guru™ Configuration Module.

WHAT: Central configuration management for Finance Guru TUI
WHY: Abstraction layer for paths and settings, no hard-coded values
ARCHITECTURE: Configuration layer for all Finance Guru components

Author: Finance Guru™ Development Team
Created: 2025-11-17
"""

from pathlib import Path

import yaml


class LayersConfigError(ValueError):
    """The layers file exists but cannot be read as a layer-to-tickers mapping."""


class FinGuruConfig:
    """Central configuration for Finance Guru TUI Dashboard.

    Provides paths, settings, and layer mappings.
    """

    PROJECT_ROOT = Path(__file__).parent.parent.parent
    CONFIG_DIR = Path.home() / ".config" / "finance-guru"
    LAYERS_FILE = CONFIG_DIR / "layers.yaml"

    @classmethod
    def load_layers(cls) -> dict[str, list[str]]:
        """Load layer configuration, using defaults when no layers file exists.

        Reads from ~/.config/finance-guru/layers.yaml if it exists,
        otherwise uses hard-coded defaults from user profile.

        Returns:
            Dictionary mapping layer names to lists of ticker symbols

        Raises:
            LayersConfigError: If the layers file exists but cannot be read or
                is not a mapping.

        EDUCATIONAL NOTE:
        Layer classification determines portfolio strategy:
        - Layer 1: Growth stocks (PLTR, TSLA, NVDA) - HOLD 100%, never touch
        - Layer 2: Income funds (JEPI, JEPQ, etc.) - Build with W2 income
        - Layer 3: Hedges (SQQQ) - Downside protection
        """
        default_layers = {
            "layer1": ["PLTR", "TSLA", "NVDA", "AAPL", "GOOGL", "COIN", "MSTR", "SOFI"],
            "layer2": [
                "JEPI",
                "JEPQ",
                "QQQI",
                "SPYI",
                "QQQY",
                "YMAX",
                "MSTY",
                "AMZY",
                "CLM",
                "CRF",
                "BDJ",
                "ETY",
                "ETV",
                "ECAT",
                "UTG",
                "BST",
            ],
            "layer3": ["SQQQ"],
        }

        if not cls.LAYERS_FILE.exists():
            return default_layers

        try:
            with open(cls.LAYERS_FILE, encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
            msg = f"Cannot read layers file {cls.LAYERS_FILE}: {exc}"
            raise LayersConfigError(msg) from exc

        if data is None:
            return default_layers
        if not isinstance(data, dict):
            msg = (
                f"Layers file {cls.LAYERS_FILE} must be a mapping of layer name "
                f"to tickers, got {type(data).__name__}"
            )
            raise LayersConfigError(msg)

        normalized: dict[str, list[str]] = {}
        for layer, symbols in data.items():
            if not isinstance(symbols, (list, tuple)):
                continue
            normalized[layer] = [str(sym).upper() for sym in symbols]

        return normalized or default_layers
