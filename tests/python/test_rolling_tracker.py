"""Tests for RollingTracker calculator module.

Tests the pure functions and helpers in rolling_tracker.py using synthetic
data. No API calls are made -- all market data is mocked.
"""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from src.analysis.rolling_tracker import (
    RollingTracker,
    _dte_status,
    _rank_contract_score,
    load_positions,
    load_roll_history,
    price_american_put,
    save_positions,
    save_roll_history,
)
from src.config.config_loader import HedgeConfig
from src.models.hedging_inputs import HedgePosition

# ---------------------------------------------------------------------------
# price_american_put
# ---------------------------------------------------------------------------


class TestPriceAmericanPut:
    """Tests for the price_american_put helper function."""

    def test_deep_itm_returns_at_least_intrinsic(self):
        """Deep ITM put must be >= intrinsic value (strike - spot)."""
        result = price_american_put(100.0, 120.0, 30, 0.30)
        assert result >= 20.0, f"Expected >= 20.0, got {result}"

    def test_otm_put_returns_bs_price(self):
        """OTM put should return a small positive value from BS model."""
        result = price_american_put(100.0, 80.0, 30, 0.30)
        assert result > 0.0
        assert result < 5.0  # OTM put should be cheap

    def test_atm_put_has_time_value(self):
        """ATM put should have meaningful time value."""
        result = price_american_put(100.0, 100.0, 60, 0.30)
        assert result > 2.0  # ATM 60-day put should have decent value

    def test_zero_days_returns_intrinsic(self):
        """Put at expiry is worth only intrinsic value."""
        # DTE=0 causes BS to fail (time_to_expiry=0 not valid)
        # The function should gracefully handle this
        result = price_american_put(100.0, 120.0, 0, 0.30)
        # Should be at least intrinsic (20.0) via fallback
        assert result >= 20.0

    def test_far_otm_near_zero(self):
        """Far OTM put should be nearly worthless."""
        result = price_american_put(100.0, 50.0, 30, 0.30)
        assert result < 0.01


# ---------------------------------------------------------------------------
# _dte_status
# ---------------------------------------------------------------------------


class TestDteStatus:
    """Tests for the _dte_status helper function."""

    def test_none_dte_returns_ok(self):
        """No DTE (inverse ETF) should return OK/green."""
        label, color = _dte_status(None)
        assert label == "OK"
        assert color == "green"

    def test_roll_zone(self):
        """DTE <= 7 should trigger ROLL/red."""
        label, color = _dte_status(5)
        assert label == "ROLL"
        assert color == "red"

    def test_expiring_zone(self):
        """DTE 8-14 should trigger EXPIRING/yellow."""
        label, color = _dte_status(10)
        assert label == "EXPIRING"
        assert color == "yellow"

    def test_ok_zone(self):
        """DTE > 14 should be OK/green."""
        label, color = _dte_status(30)
        assert label == "OK"
        assert color == "green"

    def test_boundary_seven(self):
        """DTE exactly 7 should be ROLL."""
        label, color = _dte_status(7)
        assert label == "ROLL"
        assert color == "red"

    def test_boundary_fourteen(self):
        """DTE exactly 14 should be EXPIRING."""
        label, color = _dte_status(14)
        assert label == "EXPIRING"
        assert color == "yellow"

    def test_boundary_fifteen(self):
        """DTE 15 should be OK."""
        label, color = _dte_status(15)
        assert label == "OK"
        assert color == "green"


# ---------------------------------------------------------------------------
# _rank_contract_score
# ---------------------------------------------------------------------------


class TestRankContractScore:
    """Tests for the _rank_contract_score helper function."""

    def test_perfect_match_scores_zero(self):
        """Contract matching both midpoints exactly should score 0."""
        contract = MagicMock()
        contract.otm_pct = 12.5
        contract.days_to_expiry = 75
        score = _rank_contract_score(contract, 12.5, 75.0)
        assert score == 0.0

    def test_otm_distance_contributes(self):
        """OTM distance should increase score."""
        contract = MagicMock()
        contract.otm_pct = 15.0
        contract.days_to_expiry = 75
        score = _rank_contract_score(contract, 12.5, 75.0)
        assert score == pytest.approx(2.5)

    def test_dte_distance_normalized(self):
        """DTE distance is divided by 10 for normalization."""
        contract = MagicMock()
        contract.otm_pct = 12.5
        contract.days_to_expiry = 85
        score = _rank_contract_score(contract, 12.5, 75.0)
        assert score == pytest.approx(1.0)  # 10 / 10.0

    def test_closer_contract_scores_lower(self):
        """Contract closer to targets should score lower."""
        close = MagicMock()
        close.otm_pct = 13.0
        close.days_to_expiry = 76

        far = MagicMock()
        far.otm_pct = 18.0
        far.days_to_expiry = 95

        score_close = _rank_contract_score(close, 12.5, 75.0)
        score_far = _rank_contract_score(far, 12.5, 75.0)
        assert score_close < score_far


# ---------------------------------------------------------------------------
# load_positions / save_positions (filesystem tests)
# ---------------------------------------------------------------------------


class TestPositionPersistence:
    """Tests for position YAML load/save round-trip."""

    def test_load_empty_file(self, tmp_path: Path):
        """Empty positions file should return empty list."""
        positions_file = tmp_path / "positions.yaml"
        positions_file.write_text("positions: []\n")

        with patch("src.analysis.rolling_tracker.HEDGING_DIR", tmp_path):
            result = load_positions()
        assert result == []

    def test_load_nonexistent_file(self, tmp_path: Path):
        """Missing positions file should return empty list."""
        with patch("src.analysis.rolling_tracker.HEDGING_DIR", tmp_path):
            result = load_positions()
        assert result == []

    def test_load_valid_position(self, tmp_path: Path):
        """Valid position entry should parse correctly."""
        positions_file = tmp_path / "positions.yaml"
        data = {
            "positions": [
                {
                    "ticker": "QQQ",
                    "hedge_type": "put",
                    "strike": 420.0,
                    "expiry": "2026-06-19",
                    "quantity": 2,
                    "premium_paid": 8.50,
                    "entry_date": "2026-02-01",
                    "contract_symbol": "QQQ260619P00420000",
                }
            ]
        }
        positions_file.write_text(yaml.dump(data))

        with patch("src.analysis.rolling_tracker.HEDGING_DIR", tmp_path):
            result = load_positions()
        assert len(result) == 1
        assert result[0].ticker == "QQQ"
        assert result[0].strike == 420.0

    def test_load_skips_invalid_entry(self, tmp_path: Path):
        """Invalid entries should be skipped with warning."""
        positions_file = tmp_path / "positions.yaml"
        data = {
            "positions": [
                {"ticker": "QQQ", "hedge_type": "put"},  # missing required fields
                {
                    "ticker": "SPY",
                    "hedge_type": "put",
                    "strike": 500.0,
                    "expiry": "2026-06-19",
                    "quantity": 1,
                    "premium_paid": 5.0,
                    "entry_date": "2026-02-01",
                },
            ]
        }
        positions_file.write_text(yaml.dump(data))

        with patch("src.analysis.rolling_tracker.HEDGING_DIR", tmp_path):
            result = load_positions()
        assert len(result) == 1
        assert result[0].ticker == "SPY"

    def test_save_and_reload(self, tmp_path: Path):
        """Saved positions should round-trip through YAML."""
        pos = HedgePosition(
            ticker="QQQ",
            hedge_type="put",
            strike=420.0,
            expiry=date(2026, 6, 19),
            quantity=2,
            premium_paid=8.50,
            entry_date=date(2026, 2, 1),
        )

        with patch("src.analysis.rolling_tracker.HEDGING_DIR", tmp_path):
            save_positions([pos])
            reloaded = load_positions()

        assert len(reloaded) == 1
        assert reloaded[0].ticker == "QQQ"
        assert reloaded[0].strike == 420.0
        assert reloaded[0].quantity == 2

    def test_load_yaml_none_safety(self, tmp_path: Path):
        """Empty YAML file (None from safe_load) should return empty list."""
        positions_file = tmp_path / "positions.yaml"
        positions_file.write_text("")

        with patch("src.analysis.rolling_tracker.HEDGING_DIR", tmp_path):
            result = load_positions()
        assert result == []


# ---------------------------------------------------------------------------
# load_roll_history / save_roll_history
# ---------------------------------------------------------------------------


class TestRollHistoryPersistence:
    """Tests for roll history YAML load/save."""

    def test_load_empty_history(self, tmp_path: Path):
        """Empty roll history should return empty list."""
        history_file = tmp_path / "roll-history.yaml"
        history_file.write_text("rolls: []\n")

        with patch("src.analysis.rolling_tracker.HEDGING_DIR", tmp_path):
            result = load_roll_history()
        assert result == []

    def test_load_nonexistent_history(self, tmp_path: Path):
        """Missing history file should return empty list."""
        with patch("src.analysis.rolling_tracker.HEDGING_DIR", tmp_path):
            result = load_roll_history()
        assert result == []

    def test_save_and_reload_history(self, tmp_path: Path):
        """Saved history should round-trip correctly."""
        record = {
            "roll_date": "2026-02-01",
            "old_position": {"ticker": "QQQ", "strike": 400.0},
            "reason": "rolled",
        }

        with patch("src.analysis.rolling_tracker.HEDGING_DIR", tmp_path):
            save_roll_history([record])
            result = load_roll_history()

        assert len(result) == 1
        assert result[0]["reason"] == "rolled"


# ---------------------------------------------------------------------------
# RollingTracker.get_status
# ---------------------------------------------------------------------------


class TestRollingTrackerGetStatus:
    """Tests for RollingTracker.get_status method."""

    def test_empty_positions(self, tmp_path: Path):
        """Status with no positions should return empty lists."""
        positions_file = tmp_path / "positions.yaml"
        positions_file.write_text("positions: []\n")
        history_file = tmp_path / "roll-history.yaml"
        history_file.write_text("rolls: []\n")

        config = HedgeConfig()
        tracker = RollingTracker(config)

        with patch("src.analysis.rolling_tracker.HEDGING_DIR", tmp_path):
            status = tracker.get_status()

        assert status["positions"] == []
        assert status["summary"]["position_count"] == 0
        assert status["summary"]["total_hedge_cost"] == 0.0
        assert status["summary"]["total_pnl"] == 0.0

    def test_auto_archives_expired(self, tmp_path: Path):
        """Expired positions should be moved to roll history."""
        yesterday = date.today() - timedelta(days=1)
        data = {
            "positions": [
                {
                    "ticker": "QQQ",
                    "hedge_type": "put",
                    "strike": 420.0,
                    "expiry": yesterday.isoformat(),
                    "quantity": 2,
                    "premium_paid": 8.50,
                    "entry_date": "2026-01-01",
                }
            ]
        }
        positions_file = tmp_path / "positions.yaml"
        positions_file.write_text(yaml.dump(data))
        history_file = tmp_path / "roll-history.yaml"
        history_file.write_text("rolls: []\n")

        config = HedgeConfig()
        tracker = RollingTracker(config)

        with patch("src.analysis.rolling_tracker.HEDGING_DIR", tmp_path):
            status = tracker.get_status()

        # Position should be archived
        assert status["summary"]["position_count"] == 0

        # Check roll history was updated
        with open(tmp_path / "roll-history.yaml") as f:
            history_data = yaml.safe_load(f)
        assert len(history_data["rolls"]) == 1
        assert history_data["rolls"][0]["reason"] == "expired"

    def test_enriches_put_position(self, tmp_path: Path):
        """Active put position should be enriched with pricing and DTE."""
        future_date = date.today() + timedelta(days=30)
        data = {
            "positions": [
                {
                    "ticker": "QQQ",
                    "hedge_type": "put",
                    "strike": 420.0,
                    "expiry": future_date.isoformat(),
                    "quantity": 2,
                    "premium_paid": 8.50,
                    "entry_date": "2026-01-01",
                    "contract_symbol": "QQQ260619P00420000",
                }
            ]
        }
        positions_file = tmp_path / "positions.yaml"
        positions_file.write_text(yaml.dump(data))
        history_file = tmp_path / "roll-history.yaml"
        history_file.write_text("rolls: []\n")

        # Mock get_prices to return a known spot price
        mock_price = MagicMock()
        mock_price.price = 450.0

        config = HedgeConfig()
        tracker = RollingTracker(config)

        with (
            patch("src.analysis.rolling_tracker.HEDGING_DIR", tmp_path),
            patch(
                "src.analysis.rolling_tracker.get_prices",
                return_value={"QQQ": mock_price},
            ),
        ):
            status = tracker.get_status()

        assert status["summary"]["position_count"] == 1
        pos = status["positions"][0]
        assert pos["ticker"] == "QQQ"
        assert pos["dte"] == 30
        assert pos["status"] == "OK"
        assert pos["dte_color"] == "green"
        assert pos["quantity"] == 2

    def test_pricing_error_fallback(self, tmp_path: Path):
        """Pricing error should fall back to entry cost with error flag."""
        future_date = date.today() + timedelta(days=30)
        data = {
            "positions": [
                {
                    "ticker": "QQQ",
                    "hedge_type": "put",
                    "strike": 420.0,
                    "expiry": future_date.isoformat(),
                    "quantity": 1,
                    "premium_paid": 8.50,
                    "entry_date": "2026-01-01",
                }
            ]
        }
        positions_file = tmp_path / "positions.yaml"
        positions_file.write_text(yaml.dump(data))
        history_file = tmp_path / "roll-history.yaml"
        history_file.write_text("rolls: []\n")

        config = HedgeConfig()
        tracker = RollingTracker(config)

        with (
            patch("src.analysis.rolling_tracker.HEDGING_DIR", tmp_path),
            patch(
                "src.analysis.rolling_tracker.get_prices",
                side_effect=Exception("API error"),
            ),
        ):
            status = tracker.get_status()

        pos = status["positions"][0]
        assert pos.get("pricing_error") is True
        # Current value should be entry cost (fallback)
        assert pos["current_value"] == 850.0  # 8.50 * 100 * 1


# ---------------------------------------------------------------------------
# RollingTracker.log_roll
# ---------------------------------------------------------------------------


class TestRollingTrackerLogRoll:
    """Tests for RollingTracker.log_roll method."""

    def test_roll_creates_new_position(self, tmp_path: Path):
        """Logging a roll should archive old and create new position."""
        future_date = date.today() + timedelta(days=5)
        new_expiry = date.today() + timedelta(days=75)

        data = {
            "positions": [
                {
                    "ticker": "QQQ",
                    "hedge_type": "put",
                    "strike": 420.0,
                    "expiry": future_date.isoformat(),
                    "quantity": 2,
                    "premium_paid": 8.50,
                    "entry_date": "2026-01-01",
                }
            ]
        }
        positions_file = tmp_path / "positions.yaml"
        positions_file.write_text(yaml.dump(data))
        history_file = tmp_path / "roll-history.yaml"
        history_file.write_text("rolls: []\n")

        config = HedgeConfig()
        tracker = RollingTracker(config)

        with patch("src.analysis.rolling_tracker.HEDGING_DIR", tmp_path):
            result = tracker.log_roll("QQQ", 430.0, new_expiry, 9.00)

        assert result["old_position"]["strike"] == 420.0
        assert result["new_position"]["strike"] == 430.0
        assert result["new_position"]["quantity"] == 2  # inherited

        # Check files updated
        with open(tmp_path / "positions.yaml") as f:
            pos_data = yaml.safe_load(f)
        assert len(pos_data["positions"]) == 1
        assert pos_data["positions"][0]["strike"] == 430.0

        with open(tmp_path / "roll-history.yaml") as f:
            hist_data = yaml.safe_load(f)
        assert len(hist_data["rolls"]) == 1
        assert hist_data["rolls"][0]["reason"] == "rolled"

    def test_roll_nonexistent_ticker_raises(self, tmp_path: Path):
        """Rolling a ticker not in positions should raise ValueError."""
        positions_file = tmp_path / "positions.yaml"
        positions_file.write_text("positions: []\n")
        history_file = tmp_path / "roll-history.yaml"
        history_file.write_text("rolls: []\n")

        config = HedgeConfig()
        tracker = RollingTracker(config)

        with (
            patch("src.analysis.rolling_tracker.HEDGING_DIR", tmp_path),
            pytest.raises(ValueError, match="No active put position"),
        ):
            tracker.log_roll("QQQ", 430.0, date.today() + timedelta(days=75), 9.00)


# ---------------------------------------------------------------------------
# RollingTracker.get_history
# ---------------------------------------------------------------------------


class TestRollingTrackerGetHistory:
    """Tests for RollingTracker.get_history method."""

    def test_empty_history(self, tmp_path: Path):
        """Empty history file should return empty list."""
        history_file = tmp_path / "roll-history.yaml"
        history_file.write_text("rolls: []\n")

        config = HedgeConfig()
        tracker = RollingTracker(config)

        with patch("src.analysis.rolling_tracker.HEDGING_DIR", tmp_path):
            result = tracker.get_history()
        assert result == []

    def test_returns_history_records(self, tmp_path: Path):
        """History with records should be returned."""
        data = {
            "rolls": [
                {
                    "roll_date": "2026-02-01",
                    "old_position": {"ticker": "QQQ"},
                    "reason": "rolled",
                },
            ]
        }
        history_file = tmp_path / "roll-history.yaml"
        history_file.write_text(yaml.dump(data))

        config = HedgeConfig()
        tracker = RollingTracker(config)

        with patch("src.analysis.rolling_tracker.HEDGING_DIR", tmp_path):
            result = tracker.get_history()
        assert len(result) == 1
        assert result[0]["reason"] == "rolled"


# ---------------------------------------------------------------------------
# RollingTracker.suggest_rolls
# ---------------------------------------------------------------------------


class TestRollingTrackerSuggestRolls:
    """Tests for RollingTracker.suggest_rolls method."""

    def test_no_positions_returns_empty(self, tmp_path: Path):
        """No positions should return empty suggestions list."""
        positions_file = tmp_path / "positions.yaml"
        positions_file.write_text("positions: []\n")

        config = HedgeConfig()
        tracker = RollingTracker(config)

        with patch("src.analysis.rolling_tracker.HEDGING_DIR", tmp_path):
            result = tracker.suggest_rolls()
        assert result == []

    def test_non_expiring_positions_skipped(self, tmp_path: Path):
        """Positions with DTE > 7 should not generate suggestions."""
        future_date = date.today() + timedelta(days=30)
        data = {
            "positions": [
                {
                    "ticker": "QQQ",
                    "hedge_type": "put",
                    "strike": 420.0,
                    "expiry": future_date.isoformat(),
                    "quantity": 2,
                    "premium_paid": 8.50,
                    "entry_date": "2026-01-01",
                }
            ]
        }
        positions_file = tmp_path / "positions.yaml"
        positions_file.write_text(yaml.dump(data))

        config = HedgeConfig()
        tracker = RollingTracker(config)

        with patch("src.analysis.rolling_tracker.HEDGING_DIR", tmp_path):
            result = tracker.suggest_rolls()
        assert result == []

    def test_inverse_etf_positions_skipped(self, tmp_path: Path):
        """Inverse ETF positions should not generate roll suggestions."""
        data = {
            "positions": [
                {
                    "ticker": "SQQQ",
                    "hedge_type": "inverse_etf",
                    "quantity": 100,
                    "premium_paid": 15.0,
                    "entry_date": "2026-01-01",
                }
            ]
        }
        positions_file = tmp_path / "positions.yaml"
        positions_file.write_text(yaml.dump(data))

        config = HedgeConfig()
        tracker = RollingTracker(config)

        with patch("src.analysis.rolling_tracker.HEDGING_DIR", tmp_path):
            result = tracker.suggest_rolls()
        assert result == []
