"""
Finance Guru™ Configuration Module

WHAT: Central configuration management for Finance Guru TUI
WHY: Abstraction layer for paths and settings, no hard-coded values
ARCHITECTURE: Configuration layer for all Finance Guru components

Author: Finance Guru™ Development Team
Created: 2025-11-17
"""

from pathlib import Path
import os
import yaml


class FinGuruConfig:
    """
    Central configuration for Finance Guru TUI Dashboard.
    
    Provides paths, settings, and layer mappings with safe fallbacks.
    """
    
    PROJECT_ROOT = Path(__file__).parent.parent
    PORTFOLIO_DIR = Path(
        os.getenv(
            "FIN_GURU_PORTFOLIO_DIR",
            PROJECT_ROOT / "notebooks" / "updates"
        )
    )
    CONFIG_DIR = Path.home() / ".config" / "finance-guru"
    LAYERS_FILE = CONFIG_DIR / "layers.yaml"

    @classmethod
    def load_layers(cls) -> dict[str, list[str]]:
        """
        Load layer configuration with safe fallback to defaults.
        
        Reads from ~/.config/finance-guru/layers.yaml if it exists,
        otherwise uses hard-coded defaults from user profile.
        
        Returns:
            Dictionary mapping layer names to lists of ticker symbols
            
        EDUCATIONAL NOTE:
        Layer classification determines portfolio strategy:
        - Layer 1: Growth stocks (PLTR, TSLA, NVDA) - HOLD 100%, never touch
        - Layer 2: Income funds (JEPI, JEPQ, etc.) - Build with W2 income
        - Layer 3: Hedges (SQQQ) - Downside protection
        """
        default_layers = {
            "layer1": ["PLTR", "TSLA", "NVDA", "AAPL", "GOOGL", "COIN", "MSTR", "SOFI"],
            "layer2": [
                "JEPI", "JEPQ", "QQQI", "SPYI", "QQQY", "YMAX", "MSTY", "AMZY",
                "CLM", "CRF", "BDJ", "ETY", "ETV", "ECAT", "UTG", "BST"
            ],
            "layer3": ["SQQQ"],
        }

        if not cls.LAYERS_FILE.exists():
            return default_layers

        try:
            with open(cls.LAYERS_FILE) as f:
                data = yaml.safe_load(f) or {}
        except Exception:
            # On any parse error, fall back to defaults
            return default_layers

        if not isinstance(data, dict):
            return default_layers

        # Normalize keys and ensure values are lists of symbols
        normalized: dict[str, list[str]] = {}
        for layer, symbols in data.items():
            if not isinstance(symbols, (list, tuple)):
                continue
            normalized[layer] = [str(sym).upper() for sym in symbols]

        return normalized or default_layers


