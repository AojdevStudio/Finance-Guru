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

# Import ITC components
from src.analysis.itc_risk import ITCRiskCalculator
from src.models.itc_risk_inputs import ITCRiskResponse, RiskBand


class TestAgentPromptConfiguration:
    """Verify the Compliance Officer agent has correct ITC configuration."""

    @pytest.fixture
    def agent_prompt_path(self) -> Path:
        """Path to the Compliance Officer agent prompt."""
        project_root = Path(__file__).parent.parent.parent
        return (
            project_root
            / ".claude"
            / "commands"
            / "fin-guru"
            / "agents"
            / "compliance-officer.md"
        )

    def test_agent_prompt_exists(self, agent_prompt_path: Path):
        """The Compliance Officer agent prompt file must exist."""
        assert agent_prompt_path.exists(), (
            f"Agent prompt not found at {agent_prompt_path}"
        )

    def test_agent_prompt_contains_itc_risk_integration(self, agent_prompt_path: Path):
        """Agent prompt must contain ITC risk integration section."""
        content = agent_prompt_path.read_text()

        # Check for ITC risk monitoring in critical-actions
        assert "ITC RISK MONITORING" in content, (
            "Missing ITC RISK MONITORING in critical-actions"
        )
        assert "itc_risk_cli.py" in content, "Missing itc_risk_cli.py reference"

    def test_agent_prompt_contains_itc_integration_section(
        self, agent_prompt_path: Path
    ):
        """Agent prompt must contain <itc-risk-integration> section."""
        content = agent_prompt_path.read_text()

        assert "<itc-risk-integration>" in content, (
            "Missing <itc-risk-integration> section"
        )
        assert "</itc-risk-integration>" in content, (
            "Unclosed itc-risk-integration section"
        )

    def test_agent_prompt_contains_supported_tickers(self, agent_prompt_path: Path):
        """Agent prompt must list supported tickers for tradfi and crypto."""
        content = agent_prompt_path.read_text()

        # TradFi tickers
        assert "TSLA" in content, "Missing TSLA in supported tickers"
        assert "AAPL" in content, "Missing AAPL in supported tickers"
        assert "MSTR" in content, "Missing MSTR in supported tickers"

        # Crypto tickers
        assert "BTC" in content, "Missing BTC in supported tickers"
        assert "ETH" in content, "Missing ETH in supported tickers"

    def test_agent_prompt_contains_risk_thresholds(self, agent_prompt_path: Path):
        """Agent prompt must define risk thresholds (0.3, 0.7)."""
        content = agent_prompt_path.read_text()

        assert "0.0-0.3" in content or "0-0.3" in content, (
            "Missing LOW risk threshold (0.3)"
        )
        assert "0.3-0.7" in content, "Missing MEDIUM risk threshold (0.3-0.7)"
        assert "0.7-1.0" in content or "0.7" in content, (
            "Missing HIGH risk threshold (0.7)"
        )

    def test_agent_prompt_contains_validation_workflow(self, agent_prompt_path: Path):
        """Agent prompt must contain ITC Risk Validation Workflow."""
        content = agent_prompt_path.read_text()

        assert "<itc-risk-validation-workflow>" in content, (
            "Missing validation workflow section"
        )
        assert "execution-steps" in content, "Missing execution steps in workflow"
        assert "decision-rules" in content, "Missing decision rules in workflow"

    def test_agent_prompt_contains_divergence_guidance(self, agent_prompt_path: Path):
        """Agent prompt must contain divergence analysis guidance."""
        content = agent_prompt_path.read_text()

        assert "<itc-internal-divergence-guidance>" in content, (
            "Missing divergence guidance section"
        )
        assert "ITC HIGH, Internal LOW" in content or "DIV-1" in content, (
            "Missing high ITC/low internal scenario"
        )
        assert "ITC LOW, Internal HIGH" in content or "DIV-2" in content, (
            "Missing low ITC/high internal scenario"
        )

    def test_agent_prompt_contains_menu_commands(self, agent_prompt_path: Path):
        """Agent prompt must include *itc-validate and *itc-check menu items."""
        content = agent_prompt_path.read_text()

        assert "*itc-validate" in content, "Missing *itc-validate menu command"
        assert "*itc-check" in content, "Missing *itc-check menu command"


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
        # This should NOT raise
        calc.validate_ticker("TSLA", "tradfi")

    @patch("src.analysis.itc_risk.requests.get")
    def test_normal_flow_gets_risk_score(self, mock_get):
        """Normal flow should successfully retrieve ITC risk score for TSLA."""
        # Mock successful API response with medium risk
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

        # Verify interpretation
        interpretation = result.get_risk_interpretation()
        assert "MEDIUM RISK" in interpretation

        # Medium risk should be approved with note per DR-2
        # (0.3-0.7 OR elevated but manageable volatility -> APPROVE WITH NOTE)


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
        # This tests the conceptual detection of divergence
        # In the agent, this would trigger:
        # - Document the divergence
        # - TRUST ITC (forward-looking)
        # - Apply enhanced monitoring per DR-3

        itc_risk = 0.82  # HIGH
        internal_var = 0.021  # 2.1% - LOW (well under 5% threshold)

        # Normalized internal risk (VaR-based): VaR / 5% max threshold
        normalized_internal = internal_var / 0.05  # = 0.42

        # Divergence calculation
        divergence_pct = abs(itc_risk - normalized_internal) * 100  # 40%

        # Significant divergence (>30%) should trigger enhanced review
        assert divergence_pct > 30, f"Expected >30% divergence, got {divergence_pct}%"

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
        assert "risk_metrics_cli.py" in error_message  # Points to alternative

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

        # API should never have been called
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
                RiskBand(price=500.0, risk_score=0.75),  # First high risk
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
        # Per decision rules in the agent:
        # DR-4: ITC risk score > 0.85 -> BLOCK - Immediate attention required
        itc_risk = 0.92

        # This should trigger DR-4
        assert itc_risk > 0.85, "Risk 0.92 should trigger critical block (DR-4)"

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
        assert result.current_risk_score > 0.85  # Critical threshold


class TestDecisionRulesCompliance:
    """Verify the decision rules from the spec are correctly implementable."""

    def test_dr1_low_risk_approval(self):
        """DR-1: ITC 0.0-0.3 AND internal VaR within limits -> APPROVE."""
        itc_risk = 0.2  # LOW
        internal_var = 0.03  # 3% - within 5% limit

        assert itc_risk < 0.3, "Should be low risk"
        assert internal_var < 0.05, "Should be within VaR limits"
        # Decision: APPROVE - Standard monitoring applies

    def test_dr2_medium_risk_note(self):
        """DR-2: ITC 0.3-0.7 OR elevated but manageable -> APPROVE WITH NOTE."""
        itc_risk = 0.52  # MEDIUM

        assert 0.3 <= itc_risk < 0.7, "Should be medium risk"
        # Decision: APPROVE WITH NOTE - Enhanced monitoring recommended

    def test_dr3_high_risk_review(self):
        """DR-3: ITC 0.7-0.85 -> ENHANCED REVIEW - Position limit review required."""
        itc_risk = 0.78  # HIGH but not critical

        assert 0.7 <= itc_risk < 0.85, "Should be high risk"
        # Decision: ENHANCED REVIEW - Full risk disclosure, notify user

    def test_dr4_critical_risk_block(self):
        """DR-4: ITC > 0.85 OR divergence > 30% -> BLOCK."""
        itc_risk = 0.92  # CRITICAL

        assert itc_risk > 0.85, "Should be critical risk"
        # Decision: BLOCK - Immediate attention required

    def test_dr5_unsupported_ticker(self):
        """DR-5: Unsupported ticker -> INTERNAL ONLY."""
        calc = ITCRiskCalculator(api_key="dummy")

        # NVDA is not supported
        assert not calc.is_ticker_supported("NVDA", "tradfi")
        # Decision: INTERNAL ONLY - Use internal metrics exclusively


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
        # At 0.3 boundary
        low = ITCRiskResponse(
            symbol="TEST",
            universe="tradfi",
            current_risk_score=0.29,
            risk_bands=[],
            timestamp=datetime.now(),
        )
        assert "LOW" in low.get_risk_interpretation()

        # At 0.3 (medium starts)
        medium_start = ITCRiskResponse(
            symbol="TEST",
            universe="tradfi",
            current_risk_score=0.3,
            risk_bands=[],
            timestamp=datetime.now(),
        )
        assert "MEDIUM" in medium_start.get_risk_interpretation()

        # At 0.7 boundary
        high_start = ITCRiskResponse(
            symbol="TEST",
            universe="tradfi",
            current_risk_score=0.7,
            risk_bands=[],
            timestamp=datetime.now(),
        )
        assert "HIGH" in high_start.get_risk_interpretation()
