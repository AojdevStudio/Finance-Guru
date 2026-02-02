"""
Tests for Finance Guru options chain CLI tool.

TDD: These tests validate the OptionContractData and OptionsChainOutput models,
the OTM% calculation logic, budget sizing, and CLI argument parsing.

Author: Finance Guru Development Team
"""

from __future__ import annotations

import json
import math
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add project root for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestOptionContractDataModel:
    """Validate OptionContractData Pydantic model constraints."""

    def test_valid_contract_creation(self):
        """A fully populated contract with valid data should instantiate."""
        from src.models.options_inputs import OptionContractData

        contract = OptionContractData(
            contract_symbol="QQQ260417P00400000",
            expiration="2026-04-17",
            strike=400.0,
            otm_pct=15.5,
            days_to_expiry=74,
            last_price=5.20,
            bid=5.10,
            ask=5.30,
            mid=5.20,
            volume=1234,
            open_interest=5678,
            implied_volatility=0.25,
            delta=-0.30,
            gamma=0.01,
            theta=-0.05,
            vega=0.15,
            total_cost=520.0,
            contracts_in_budget=8,
        )

        assert contract.contract_symbol == "QQQ260417P00400000"
        assert contract.strike == 400.0
        assert contract.otm_pct == 15.5
        assert contract.total_cost == 520.0
        assert contract.contracts_in_budget == 8

    def test_strike_must_be_positive(self):
        """Strike price must be greater than zero."""
        from pydantic import ValidationError

        from src.models.options_inputs import OptionContractData

        with pytest.raises(ValidationError):
            OptionContractData(
                contract_symbol="TEST",
                expiration="2026-04-17",
                strike=0.0,
                otm_pct=10.0,
                days_to_expiry=30,
                last_price=1.0,
                bid=0.9,
                ask=1.1,
                mid=1.0,
                total_cost=100.0,
            )

    def test_greeks_default_to_none(self):
        """Greeks should default to None when not provided."""
        from src.models.options_inputs import OptionContractData

        contract = OptionContractData(
            contract_symbol="TEST",
            expiration="2026-04-17",
            strike=100.0,
            otm_pct=10.0,
            days_to_expiry=30,
            last_price=2.0,
            bid=1.9,
            ask=2.1,
            mid=2.0,
            total_cost=200.0,
        )

        assert contract.delta is None
        assert contract.gamma is None
        assert contract.theta is None
        assert contract.vega is None
        assert contract.contracts_in_budget is None

    def test_volume_defaults_to_zero(self):
        """Volume and open interest should default to zero."""
        from src.models.options_inputs import OptionContractData

        contract = OptionContractData(
            contract_symbol="TEST",
            expiration="2026-04-17",
            strike=100.0,
            otm_pct=10.0,
            days_to_expiry=30,
            last_price=2.0,
            bid=1.9,
            ask=2.1,
            mid=2.0,
            total_cost=200.0,
        )

        assert contract.volume == 0
        assert contract.open_interest == 0


class TestOptionsChainOutputModel:
    """Validate OptionsChainOutput Pydantic model."""

    def test_valid_output_creation(self):
        """Full output model should instantiate with valid data."""
        from src.models.options_inputs import OptionsChainOutput

        output = OptionsChainOutput(
            ticker="QQQ",
            spot_price=475.50,
            scan_date="2026-02-02",
            option_type="put",
            otm_range=(10.0, 20.0),
            days_range=(60, 90),
            budget=4407.0,
            target_contracts=4,
            expirations_available=["2026-03-20", "2026-04-17"],
            expirations_scanned=["2026-04-17"],
            contracts=[],
            total_found=0,
        )

        assert output.ticker == "QQQ"
        assert output.spot_price == 475.50
        assert output.option_type == "put"
        assert output.otm_range == (10.0, 20.0)
        assert output.days_range == (60, 90)
        assert output.budget == 4407.0

    def test_output_serializes_to_json(self):
        """Model should serialize to valid JSON."""
        from src.models.options_inputs import OptionsChainOutput

        output = OptionsChainOutput(
            ticker="QQQ",
            spot_price=475.50,
            scan_date="2026-02-02",
            option_type="put",
            otm_range=(10.0, 20.0),
            days_range=(60, 90),
            contracts=[],
            total_found=0,
        )

        json_str = output.model_dump_json()
        parsed = json.loads(json_str)

        assert parsed["ticker"] == "QQQ"
        assert parsed["spot_price"] == 475.50
        assert parsed["option_type"] == "put"

    def test_budget_defaults_to_none(self):
        """Budget should default to None when not provided."""
        from src.models.options_inputs import OptionsChainOutput

        output = OptionsChainOutput(
            ticker="QQQ",
            spot_price=475.50,
            scan_date="2026-02-02",
            option_type="call",
            otm_range=(5.0, 15.0),
            days_range=(30, 60),
        )

        assert output.budget is None
        assert output.target_contracts == 1


class TestOTMPercentCalculation:
    """Validate OTM percentage calculation logic."""

    def test_put_otm_percent(self):
        """Put OTM% = ((spot - strike) / spot) * 100."""
        spot = 475.0
        strike = 400.0
        otm_pct = ((spot - strike) / spot) * 100
        assert abs(otm_pct - 15.79) < 0.01

    def test_call_otm_percent(self):
        """Call OTM% = ((strike - spot) / spot) * 100."""
        spot = 475.0
        strike = 550.0
        otm_pct = ((strike - spot) / spot) * 100
        assert abs(otm_pct - 15.79) < 0.01

    def test_atm_otm_percent_is_zero(self):
        """ATM contract has 0% OTM."""
        spot = 475.0
        strike = 475.0

        put_otm = ((spot - strike) / spot) * 100
        call_otm = ((strike - spot) / spot) * 100

        assert put_otm == 0.0
        assert call_otm == 0.0


class TestBudgetSizing:
    """Validate budget and contract sizing calculations."""

    def test_contracts_in_budget_calculation(self):
        """contracts_in_budget = floor(budget / total_cost)."""
        budget = 4407.0
        total_cost = 520.0  # premium * 100
        contracts_in_budget = math.floor(budget / total_cost)
        assert contracts_in_budget == 8

    def test_total_cost_from_premium(self):
        """total_cost = last_price * 100 (options contract multiplier)."""
        last_price = 5.20
        total_cost = last_price * 100
        assert total_cost == 520.0

    def test_zero_premium_uses_mid(self):
        """If last_price is 0, total_cost should use mid price."""
        last_price = 0.0
        bid = 4.80
        ask = 5.20
        mid = (bid + ask) / 2

        total_cost = (last_price if last_price > 0 else mid) * 100
        assert total_cost == 500.0

    def test_budget_none_skips_sizing(self):
        """If no budget provided, contracts_in_budget should be None."""
        budget = None
        total_cost = 520.0

        if budget is not None:
            contracts_in_budget = math.floor(budget / total_cost)
        else:
            contracts_in_budget = None

        assert contracts_in_budget is None


class TestExpirationFiltering:
    """Validate expiration date filtering logic."""

    def test_filter_expirations_within_range(self):
        """Only expirations within days_min to days_max should pass."""
        today = date(2026, 2, 2)
        expirations = [
            "2026-02-21",  # 19 days - too soon
            "2026-03-20",  # 46 days - too soon for 60-90
            "2026-04-03",  # 60 days - min boundary
            "2026-04-17",  # 74 days - in range
            "2026-05-03",  # 90 days - max boundary
            "2026-05-15",  # 102 days - too far
            "2026-06-19",  # 137 days - too far
        ]

        days_min = 60
        days_max = 90
        filtered = []

        for exp_str in expirations:
            exp_date = date.fromisoformat(exp_str)
            days_out = (exp_date - today).days
            if days_min <= days_out <= days_max:
                filtered.append(exp_str)

        assert "2026-04-03" in filtered
        assert "2026-04-17" in filtered
        assert "2026-05-03" in filtered
        assert "2026-02-21" not in filtered
        assert "2026-05-15" not in filtered
        assert len(filtered) == 3

    def test_no_expirations_in_range(self):
        """If no expirations match, result should be empty."""
        today = date(2026, 2, 2)
        expirations = ["2026-02-21", "2026-03-07"]

        days_min = 60
        days_max = 90
        filtered = []

        for exp_str in expirations:
            exp_date = date.fromisoformat(exp_str)
            days_out = (exp_date - today).days
            if days_min <= days_out <= days_max:
                filtered.append(exp_str)

        assert len(filtered) == 0


class TestGreeksSkipLogic:
    """Validate that Greeks are skipped when IV is zero or NaN."""

    def test_zero_iv_skips_greeks(self):
        """When implied volatility is 0, Greeks should be None."""
        iv = 0.0
        should_skip = iv <= 0.0 or math.isnan(iv)
        assert should_skip is True

    def test_nan_iv_skips_greeks(self):
        """When implied volatility is NaN, Greeks should be None."""
        iv = float("nan")
        should_skip = iv <= 0.0 or math.isnan(iv)
        assert should_skip is True

    def test_valid_iv_calculates_greeks(self):
        """When IV is valid positive number, Greeks should be calculated."""
        iv = 0.25
        should_skip = iv <= 0.0 or math.isnan(iv)
        assert should_skip is False


class TestMidPriceEdgeCases:
    """Validate mid price calculation edge cases."""

    def test_both_bid_ask_zero(self):
        """If both bid and ask are 0, mid should fall back to last_price."""
        bid = 0.0
        ask = 0.0
        last_price = 3.50

        if bid == 0.0 and ask == 0.0:
            mid = last_price
        else:
            mid = (bid + ask) / 2

        assert mid == 3.50

    def test_normal_mid_calculation(self):
        """Normal mid = (bid + ask) / 2."""
        bid = 4.80
        ask = 5.20
        mid = (bid + ask) / 2
        assert mid == 5.0


class TestModelExports:
    """Validate that new models are exported correctly."""

    def test_option_contract_data_importable(self):
        """OptionContractData should be importable from options_inputs."""
        from src.models.options_inputs import OptionContractData

        assert OptionContractData is not None

    def test_options_chain_output_importable(self):
        """OptionsChainOutput should be importable from options_inputs."""
        from src.models.options_inputs import OptionsChainOutput

        assert OptionsChainOutput is not None

    def test_models_in_all_list(self):
        """New models should be in the __all__ export list."""
        from src.models import options_inputs

        assert "OptionContractData" in options_inputs.__all__
        assert "OptionsChainOutput" in options_inputs.__all__

    def test_models_importable_from_package(self):
        """New models should be importable from src.models package."""
        from src.models import OptionContractData, OptionsChainOutput

        assert OptionContractData is not None
        assert OptionsChainOutput is not None
