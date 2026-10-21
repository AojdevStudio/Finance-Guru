"""
Tests for Compliance Officer Agent ITC Integration.

These tests verify the 4 scenarios from the agent-itc-integration-compliance spec:
1. Normal Flow - ITC supported ticker (TSLA)
2. Divergence Detection - ITC high risk with low internal VaR
3. Unsupported Ticker - NVDA (should skip ITC, use internal metrics)
4. High Risk Scenario - ITC risk > 0.7 (should apply position reduction)

RUNNING TESTS:
    # Run all Compliance Officer integration tests
    uv run pytest tests/python/test_compliance_officer_itc_integration.py -v

    # Run specific scenario
    uv run pytest tests/python/test_compliance_officer_itc_integration.py::TestScenarioNormalFlow -v

Author: Finance Guru Development Team
Created: 2026-01-09
Bead: family-office-578
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.analysis.itc_risk import (
    CRITICAL_RISK_FLOOR,
    MAX_DIVERGENCE_PCT,
    ITCRiskCalculator,
    evaluate_var_compliance,
)
from src.models.itc_risk_inputs import ITCComplianceInput, ITCRiskResponse, RiskBand

PROJECT_ROOT = Path(__file__).parent.parent.parent
ITC_REFERENCE = (
    PROJECT_ROOT
    / ".claude"
    / "skills"
    / "fin-guru-compliance-review"
    / "itc-divergence.md"
)


class TestAgentPromptConfiguration:
    """Verify the Compliance Officer agent has correct ITC configuration."""

    @pytest.fixture
    def agent_prompt_path(self) -> Path:
        """Path to the Compliance Officer agent prompt."""
        return PROJECT_ROOT / ".claude" / "agents" / "fg-compliance-officer.md"

    @pytest.fixture
    def content(self, agent_prompt_path: Path) -> str:
        """The agent prompt plus the ITC reference it links."""
        return agent_prompt_path.read_text() + ITC_REFERENCE.read_text()

    def test_agent_prompt_exists(self, agent_prompt_path: Path):
        """The Compliance Officer agent prompt file must exist."""
        assert agent_prompt_path.exists(), (
            f"Agent prompt not found at {agent_prompt_path}"
        )

    def test_agent_prompt_links_the_itc_reference(self, agent_prompt_path: Path):
        """The agent must link the ITC rules it no longer restates."""
        assert "fin-guru-compliance-review/itc-divergence.md" in (
            agent_prompt_path.read_text()
        )
        assert ITC_REFERENCE.is_file()

    def test_agent_prompt_contains_itc_risk_integration(self, content: str):
        """The ITC rules must name the market-implied check and its CLI."""
        assert "market-implied" in content, "Missing the ITC risk monitoring rule"
        assert "itc_risk_cli" in content, "Missing itc_risk_cli reference"

    def test_agent_prompt_reads_supported_tickers_from_the_cli(self, content: str):
        """Supported tickers come from itc_risk_cli, not a copied list."""
        assert "itc_risk_cli --list-supported tradfi" in content
        assert "itc_risk_cli --list-supported crypto" in content
        assert "TSLA, AAPL, MSTR" not in content

    def test_agent_prompt_contains_risk_thresholds(self, content: str):
        """The ITC rules must define risk thresholds (0.3, 0.7)."""
        assert "0.0-0.3" in content or "0-0.3" in content, (
            "Missing LOW risk threshold (0.3)"
        )
        assert "0.3-0.7" in content, "Missing MEDIUM risk threshold (0.3-0.7)"
        assert "0.7-1.0" in content or "0.7" in content, (
            "Missing HIGH risk threshold (0.7)"
        )

    def test_agent_prompt_contains_validation_workflow(self, content: str):
        """The ITC rules must contain the validation workflow."""
        assert "## ITC risk validation workflow" in content
        assert "### Steps" in content, "Missing steps in workflow"
        assert "## Decision rules" in content, "Missing decision rules"
        for rule in ("DR-1", "DR-2", "DR-3", "DR-4", "DR-5"):
            assert rule in content, f"Missing {rule}"

    def test_agent_prompt_contains_divergence_guidance(self, content: str):
        """The ITC rules must contain divergence analysis guidance."""
        assert "## Divergence between ITC and internal metrics" in content
        assert "DIV-1" in content, "Missing high ITC/low internal scenario"
        assert "DIV-2" in content, "Missing low ITC/high internal scenario"


class TestScenarioNormalFlow:
    """
    Test Scenario 1: Normal Flow - ITC Supported Ticker

    Given: User requests review of TSLA buy ticket
    When: Compliance Officer checks ITC risk for TSLA
    Then: Agent runs ITC check, interprets risk, applies decision rule
    """

    def test_tsla_is_supported_tradfi_ticker(self):
        """TSLA must be in the ITC supported tradfi list."""
        calc = ITCRiskCalculator(api_key="dummy")
        assert calc.is_ticker_supported("TSLA", "tradfi") is True

    def test_tsla_validation_passes(self):
        """Ticker validation for TSLA should not raise."""
        calc = ITCRiskCalculator(api_key="dummy")
        calc.validate_ticker("TSLA", "tradfi")

    @patch("src.analysis.itc_risk.requests.get")
    def test_normal_flow_gets_risk_score(self, mock_get):
        """Normal flow should successfully retrieve ITC risk score for TSLA."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "current_risk_score": 0.52,
            "risk_table": [
                {"price": 400.0, "risk": 0.4},
                {"price": 450.0, "risk": 0.52},
                {"price": 600.0, "risk": 0.75},
            ],
        }
        mock_get.return_value = mock_response

        calc = ITCRiskCalculator(api_key="test_key")
        result = calc.get_risk_score("TSLA", "tradfi", enrich_with_price=False)

        assert result.symbol == "TSLA"
        assert result.universe == "tradfi"
        assert result.current_risk_score == 0.52
        assert len(result.risk_bands) == 3

    @patch("src.analysis.itc_risk.requests.get")
    def test_normal_flow_applies_correct_decision_rule(self, mock_get):
        """Medium risk (0.3-0.7) should trigger APPROVE WITH NOTE decision."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "current_risk_score": 0.52,
            "risk_table": [],
        }
        mock_get.return_value = mock_response

        calc = ITCRiskCalculator(api_key="test_key")
        result = calc.get_risk_score("TSLA", "tradfi", enrich_with_price=False)

        interpretation = result.get_risk_interpretation()
        assert "MEDIUM RISK" in interpretation


class TestScenarioDivergenceDetection:
    """
    Test Scenario 2: Divergence Detection

    Given: User provides TSLA buy ticket with internal VaR 2.1% (low)
    When: Compliance Officer runs ITC check and gets high risk (e.g., 0.82)
    Then: Agent detects divergence, recommends investigation, conditional approval
    """

    def test_high_risk_detected_when_score_above_07(self):
        """ITC risk score > 0.7 should be classified as HIGH RISK."""
        response = ITCRiskResponse(
            symbol="TSLA",
            universe="tradfi",
            current_risk_score=0.82,
            risk_bands=[],
            timestamp=datetime.now(),
        )

        interpretation = response.get_risk_interpretation()
        assert "HIGH RISK" in interpretation

    def test_divergence_scenario_identified(self):
        """High ITC (0.82) + Low internal VaR (2.1%) = Divergence scenario DIV-1."""

        decision = evaluate_var_compliance(
            ITCComplianceInput(
                itc_supported=True,
                itc_risk=0.82,
                daily_var=-0.021,
            )
        )
        assert decision.divergence_pct is not None
        assert decision.divergence_pct > MAX_DIVERGENCE_PCT
        assert (decision.rule, decision.action) == ("DR-4", "BLOCK")

    @patch("src.analysis.itc_risk.requests.get")
    def test_divergence_flow_returns_high_risk(self, mock_get):
        """When ITC returns high risk, response should reflect HIGH status."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "current_risk_score": 0.82,
            "risk_table": [
                {"price": 400.0, "risk": 0.5},
                {"price": 500.0, "risk": 0.82},
            ],
        }
        mock_get.return_value = mock_response

        calc = ITCRiskCalculator(api_key="test_key")
        result = calc.get_risk_score("TSLA", "tradfi", enrich_with_price=False)

        assert result.current_risk_score == 0.82
        assert "HIGH RISK" in result.get_risk_interpretation()


class TestScenarioUnsupportedTicker:
    """
    Test Scenario 3: Unsupported Ticker

    Given: User provides NVDA buy ticket (not ITC-supported)
    When: Compliance Officer attempts ITC check
    Then: CLI returns error, agent proceeds with internal metrics only
    """

    def test_nvda_is_not_supported(self):
        """NVDA must NOT be in the ITC supported tradfi list."""
        calc = ITCRiskCalculator(api_key="dummy")
        assert calc.is_ticker_supported("NVDA", "tradfi") is False

    def test_nvda_validation_fails_with_clear_message(self):
        """Validation for NVDA should raise with helpful message."""
        calc = ITCRiskCalculator(api_key="dummy")

        with pytest.raises(ValueError) as exc_info:
            calc.validate_ticker("NVDA", "tradfi")

        error_message = str(exc_info.value)
        assert "NVDA not supported" in error_message
        assert "risk_metrics_cli" in error_message

    def test_pltr_is_not_supported(self):
        """PLTR must NOT be in the ITC supported tradfi list."""
        calc = ITCRiskCalculator(api_key="dummy")
        assert calc.is_ticker_supported("PLTR", "tradfi") is False

    def test_googl_is_not_supported(self):
        """GOOGL must NOT be in the ITC supported tradfi list."""
        calc = ITCRiskCalculator(api_key="dummy")
        assert calc.is_ticker_supported("GOOGL", "tradfi") is False

    @patch("src.analysis.itc_risk.requests.get")
    def test_unsupported_ticker_does_not_call_api(self, mock_get):
        """API should NOT be called for unsupported tickers."""
        calc = ITCRiskCalculator(api_key="test_key")

        with pytest.raises(ValueError, match="NVDA not supported"):
            calc.get_risk_score("NVDA", "tradfi")

        mock_get.assert_not_called()


class TestScenarioHighRisk:
    """
    Test Scenario 4: High Risk Scenario

    Given: TSLA ITC risk = 0.92 (very high)
    When: Compliance Officer reviews buy ticket
    Then: Agent blocks or heavily reduces allocation, requires phased entry
    """

    def test_very_high_risk_score_detected(self):
        """Risk score > 0.85 should be classified as very high risk."""
        response = ITCRiskResponse(
            symbol="TSLA",
            universe="tradfi",
            current_risk_score=0.92,
            risk_bands=[],
            timestamp=datetime.now(),
        )

        interpretation = response.get_risk_interpretation()
        assert "HIGH RISK" in interpretation

    def test_high_risk_threshold_identified(self):
        """get_high_risk_threshold should return the first band >= 0.7."""
        response = ITCRiskResponse(
            symbol="TSLA",
            universe="tradfi",
            current_price=450.0,
            current_risk_score=0.92,
            risk_bands=[
                RiskBand(price=400.0, risk_score=0.5),
                RiskBand(price=500.0, risk_score=0.75),
                RiskBand(price=600.0, risk_score=0.9),
            ],
            timestamp=datetime.now(),
        )

        threshold = response.get_high_risk_threshold()

        assert threshold is not None
        assert threshold.price == 500.0
        assert threshold.risk_score == 0.75

    def test_critical_risk_triggers_dr4(self):
        """Risk > 0.85 should trigger DR-4 (Critical Risk Block)."""
        decision = evaluate_var_compliance(
            ITCComplianceInput(
                itc_supported=True,
                itc_risk=0.92,
                daily_var=-0.046,
            )
        )
        assert (decision.rule, decision.action) == ("DR-4", "BLOCK")

    @patch("src.analysis.itc_risk.requests.get")
    def test_high_risk_flow_returns_very_high_score(self, mock_get):
        """When ITC returns very high risk, response should reflect critical status."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "current_risk_score": 0.92,
            "risk_table": [
                {"price": 500.0, "risk": 0.75},
                {"price": 550.0, "risk": 0.85},
                {"price": 600.0, "risk": 0.92},
            ],
        }
        mock_get.return_value = mock_response

        calc = ITCRiskCalculator(api_key="test_key")
        result = calc.get_risk_score("TSLA", "tradfi", enrich_with_price=False)

        assert result.current_risk_score == 0.92
        assert result.current_risk_score > CRITICAL_RISK_FLOOR


class TestDecisionRulesCompliance:
    """The typed decision function applies the documented rules in precedence order."""

    @pytest.mark.parametrize(
        ("score", "daily_var", "rule", "action"),
        [
            (0.2, -0.01, "DR-1", "APPROVE"),
            (0.52, -0.026, "DR-2", "APPROVE WITH NOTE"),
            (0.78, -0.039, "DR-3", "ENHANCED REVIEW"),
            (0.92, -0.046, "DR-4", "BLOCK"),
            (0.82, -0.021, "DR-4", "BLOCK"),
            (0.3, -0.015, "DR-2", "APPROVE WITH NOTE"),
            (0.7, -0.035, "DR-3", "ENHANCED REVIEW"),
            (0.85, -0.0425, "DR-3", "ENHANCED REVIEW"),
            (0.5, -0.01, "DR-2", "APPROVE WITH NOTE"),
            (0.8, -0.025, "DR-3", "ENHANCED REVIEW"),
            (0.8001, -0.025, "DR-4", "BLOCK"),
        ],
    )
    def test_documented_rules(self, score, daily_var, rule, action):
        result = evaluate_var_compliance(
            ITCComplianceInput(itc_supported=True, itc_risk=score, daily_var=daily_var)
        )
        assert (result.rule, result.action) == (rule, action)

    @pytest.mark.parametrize(
        ("supported", "score", "daily_var", "action"),
        [
            (False, None, None, "INTERNAL ONLY"),
            (True, None, -0.01, "BLOCK"),
            (True, 0.2, None, "BLOCK"),
            (True, 0.8, -0.06, "BLOCK"),
        ],
    )
    def test_unsupported_missing_and_over_limit_inputs(
        self, supported, score, daily_var, action
    ):
        result = evaluate_var_compliance(
            ITCComplianceInput(
                itc_supported=supported, itc_risk=score, daily_var=daily_var
            )
        )
        assert result.action == action
        assert result.reason


class TestCLIOutputFormats:
    """Verify CLI output formats support agent parsing."""

    def test_json_output_parseable(self):
        """JSON output should be parseable for programmatic use."""
        import json

        from src.analysis.itc_risk_cli import format_output_json

        response = ITCRiskResponse(
            symbol="TSLA",
            universe="tradfi",
            current_risk_score=0.52,
            risk_bands=[
                RiskBand(price=400.0, risk_score=0.4),
                RiskBand(price=500.0, risk_score=0.6),
            ],
            timestamp=datetime.now(),
        )

        output = format_output_json([response])
        parsed = json.loads(output)

        assert parsed["symbol"] == "TSLA"
        assert parsed["current_risk_score"] == 0.52
        assert len(parsed["risk_bands"]) == 2

    def test_human_output_includes_risk_level(self):
        """Human-readable output should include risk level interpretation."""
        from src.analysis.itc_risk_cli import format_output_human

        response = ITCRiskResponse(
            symbol="TSLA",
            universe="tradfi",
            current_risk_score=0.82,
            risk_bands=[],
            timestamp=datetime.now(),
        )

        output = format_output_human(response)

        assert "TSLA" in output
        assert "HIGH RISK" in output
        assert "0.82" in output or "0.820" in output


class TestEndToEndIntegration:
    """End-to-end integration tests for the complete workflow."""

    def test_supported_tickers_list_complete(self):
        """Verify all expected tradfi tickers are supported."""
        calc = ITCRiskCalculator(api_key="dummy")
        supported = calc.get_supported_tickers("tradfi")

        expected = ["TSLA", "AAPL", "MSTR", "NFLX", "SP500"]
        for ticker in expected:
            assert ticker in supported, f"{ticker} should be in supported list"

    def test_unsupported_common_tickers(self):
        """Verify common portfolio tickers are correctly identified as unsupported."""
        calc = ITCRiskCalculator(api_key="dummy")

        unsupported = ["NVDA", "PLTR", "GOOGL", "MSFT", "AMZN", "META"]
        for ticker in unsupported:
            assert not calc.is_ticker_supported(ticker, "tradfi"), (
                f"{ticker} should be unsupported"
            )

    def test_crypto_universe_supported(self):
        """Verify crypto universe has expected tickers."""
        calc = ITCRiskCalculator(api_key="dummy")
        supported = calc.get_supported_tickers("crypto")

        expected = ["BTC", "ETH", "SOL"]
        for ticker in expected:
            assert ticker in supported, f"{ticker} should be in crypto list"

    def test_risk_interpretation_boundaries(self):
        """Verify risk interpretation at exact boundaries."""
        low = ITCRiskResponse(
            symbol="TEST",
            universe="tradfi",
            current_risk_score=0.29,
            risk_bands=[],
            timestamp=datetime.now(),
        )
        assert "LOW" in low.get_risk_interpretation()

        medium_start = ITCRiskResponse(
            symbol="TEST",
            universe="tradfi",
            current_risk_score=0.3,
            risk_bands=[],
            timestamp=datetime.now(),
        )
        assert "MEDIUM" in medium_start.get_risk_interpretation()

        high_start = ITCRiskResponse(
            symbol="TEST",
            universe="tradfi",
            current_risk_score=0.7,
            risk_bands=[],
            timestamp=datetime.now(),
        )
        assert "HIGH" in high_start.get_risk_interpretation()


@pytest.mark.parametrize(
    ("inputs", "expected_rule"),
    [
        ({"itc_supported": True, "itc_risk": 0.8, "daily_var": -0.025}, "DR-3"),
        ({"itc_supported": True, "itc_risk": 0.8}, "GUARDRAIL"),
        ({"itc_supported": False}, "DR-5"),
    ],
)
def test_offline_compliance_cli(inputs, expected_rule):
    import json
    import subprocess
    import sys

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "src.analysis.itc_risk_cli",
            "--compliance-input",
            json.dumps(inputs),
            "--output",
            "json",
        ],
        text=True,
        capture_output=True,
        check=True,
    )
    output = json.loads(result.stdout)
    assert output["rule"] == expected_rule
    assert output["date"]
    assert "Supplied inputs" in output["source"]
    assert "Not investment advice" in output["disclaimer"]
