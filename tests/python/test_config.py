"""Tests for FinGuruConfig module.

Tests cover:
- Default layer configuration
- Path constants
- YAML layer loading with fallbacks

RUNNING TESTS:
    uv run pytest tests/python/test_config.py -v
"""

from unittest.mock import mock_open, patch

from src.config import FinGuruConfig


class TestFinGuruConfig:
    def test_default_layers_have_three_layers(self):
        # When no YAML exists, load_layers returns defaults
        with patch.object(FinGuruConfig, "LAYERS_FILE") as mock_file:
            mock_file.exists.return_value = False
            layers = FinGuruConfig.load_layers()

        assert "layer1" in layers
        assert "layer2" in layers
        assert "layer3" in layers

    def test_default_layer1_has_growth_stocks(self):
        with patch.object(FinGuruConfig, "LAYERS_FILE") as mock_file:
            mock_file.exists.return_value = False
            layers = FinGuruConfig.load_layers()

        assert "PLTR" in layers["layer1"]
        assert "TSLA" in layers["layer1"]

    def test_default_layer3_is_hedge(self):
        with patch.object(FinGuruConfig, "LAYERS_FILE") as mock_file:
            mock_file.exists.return_value = False
            layers = FinGuruConfig.load_layers()

        assert "SQQQ" in layers["layer3"]

    def test_loads_custom_yaml(self):
        yaml_content = "layer1:\n  - nvda\n  - amd\nlayer2:\n  - spy\n"
        with patch.object(FinGuruConfig, "LAYERS_FILE") as mock_file:
            mock_file.exists.return_value = True
            with patch("builtins.open", mock_open(read_data=yaml_content)):
                layers = FinGuruConfig.load_layers()

        assert "NVDA" in layers["layer1"]
        assert "AMD" in layers["layer1"]
        assert "SPY" in layers["layer2"]

    def test_falls_back_on_invalid_yaml(self):
        with patch.object(FinGuruConfig, "LAYERS_FILE") as mock_file:
            mock_file.exists.return_value = True
            with patch("builtins.open", side_effect=OSError("file error")):
                layers = FinGuruConfig.load_layers()

        # Should return defaults
        assert "layer1" in layers
        assert "PLTR" in layers["layer1"]

    def test_falls_back_on_non_dict_yaml(self):
        yaml_content = "just a string\n"
        with patch.object(FinGuruConfig, "LAYERS_FILE") as mock_file:
            mock_file.exists.return_value = True
            with patch("builtins.open", mock_open(read_data=yaml_content)):
                layers = FinGuruConfig.load_layers()

        assert "layer1" in layers
        assert "PLTR" in layers["layer1"]

    def test_skips_non_list_values(self):
        yaml_content = "layer1:\n  - nvda\nlayer2: not_a_list\n"
        with patch.object(FinGuruConfig, "LAYERS_FILE") as mock_file:
            mock_file.exists.return_value = True
            with patch("builtins.open", mock_open(read_data=yaml_content)):
                layers = FinGuruConfig.load_layers()

        assert "layer1" in layers
        assert "NVDA" in layers["layer1"]
        assert "layer2" not in layers

    def test_project_root_path_exists(self):
        assert FinGuruConfig.PROJECT_ROOT.exists()
