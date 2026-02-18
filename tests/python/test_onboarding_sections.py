"""
Tests for onboarding wizard section runners with mocked questionary.

Each section runner collects data via interactive prompts and stores
raw values in OnboardingState.data[section_name]. These tests mock
questionary at the function level (NOT stdin) to simulate user input.

Author: Finance Guru Development Team
Created: 2026-02-05
"""

import pytest

from src.models.onboarding_inputs import OnboardingState, SectionName
from src.utils.onboarding_sections import (
    run_cash_flow_section,
    run_env_setup_section,
    run_investments_section,
    run_liquid_assets_section,
    run_preferences_section,
    run_summary_section,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fresh_state() -> OnboardingState:
    """Create a fresh OnboardingState for testing."""
    return OnboardingState.create_new()


def _prepopulated_state() -> OnboardingState:
    """Create an OnboardingState with all sections populated (for summary test)."""
    state = OnboardingState.create_new()
    state.data[SectionName.LIQUID_ASSETS.value] = {
        "total": 15000.0,
        "accounts_count": 3,
        "average_yield": 0.045,
        "structure": "2 checking, 1 savings",
    }
    state.data[SectionName.INVESTMENTS.value] = {
        "total_value": 100000.0,
        "brokerage": "Fidelity",
        "has_retirement": True,
        "retirement_value": 50000.0,
        "allocation_strategy": "aggressive_growth",
        "risk_tolerance": "aggressive",
        "google_sheets_id": None,
        "account_number": None,
    }
    state.data[SectionName.CASH_FLOW.value] = {
        "monthly_income": 8000.0,
        "fixed_expenses": 3000.0,
        "variable_expenses": 2000.0,
        "current_savings": 1000.0,
        "investment_capacity": 2000.0,
    }
    state.data[SectionName.DEBT.value] = {
        "has_mortgage": False,
        "mortgage_balance": None,
        "mortgage_payment": None,
        "has_student_loans": False,
        "student_loan_balance": None,
        "student_loan_rate": None,
        "has_auto_loans": False,
        "auto_loan_balance": None,
        "auto_loan_rate": None,
        "has_credit_cards": False,
        "credit_card_balance": None,
        "weighted_rate": None,
        "other_debt": None,
    }
    state.data[SectionName.PREFERENCES.value] = {
        "investment_philosophy": "growth",
        "focus_areas": ["Dividend income", "Growth investing"],
        "emergency_fund_months": 6,
    }
    state.data[SectionName.BROKER.value] = {
        "brokerage": "Fidelity",
    }
    state.data[SectionName.ENV_SETUP.value] = {
        "user_name": "TestUser",
        "language": "English",
        "has_alphavantage": False,
        "alphavantage_key": None,
        "has_brightdata": False,
        "brightdata_key": None,
        "google_sheets_credentials": None,
    }
    # Mark all prior sections complete
    for section in [
        SectionName.LIQUID_ASSETS,
        SectionName.INVESTMENTS,
        SectionName.CASH_FLOW,
        SectionName.DEBT,
        SectionName.PREFERENCES,
        SectionName.BROKER,
        SectionName.ENV_SETUP,
    ]:
        state.completed_sections.append(section)
    return state


# ---------------------------------------------------------------------------
# Section 1: Liquid Assets
# ---------------------------------------------------------------------------


class TestLiquidAssetsSection:
    """Test liquid assets section runner."""

    def test_collects_all_fields(self, mocker):
        """Section stores total, accounts_count, average_yield, structure."""
        mock_text = mocker.patch("src.utils.onboarding_sections.questionary.text")
        # Responses: total, accounts_count, yield, structure
        mock_text.return_value.ask.side_effect = [
            "15000",  # total
            "3",  # accounts_count
            "4.5",  # average_yield (%)
            "",  # structure (skip)
        ]

        state = _fresh_state()
        result = run_liquid_assets_section(state)

        data = result.data[SectionName.LIQUID_ASSETS.value]
        assert data["total"] == 15000.0
        assert data["accounts_count"] == 3
        assert data["average_yield"] == pytest.approx(0.045)  # decimal
        assert data["structure"] is None  # empty string -> None

    def test_marks_section_complete(self, mocker):
        """Section marks liquid_assets as complete."""
        mock_text = mocker.patch("src.utils.onboarding_sections.questionary.text")
        mock_text.return_value.ask.side_effect = ["15000", "3", "4.5", ""]

        state = _fresh_state()
        result = run_liquid_assets_section(state)

        assert result.is_section_complete(SectionName.LIQUID_ASSETS)

    def test_with_structure(self, mocker):
        """Section stores structure when provided."""
        mock_text = mocker.patch("src.utils.onboarding_sections.questionary.text")
        mock_text.return_value.ask.side_effect = [
            "25000",
            "2",
            "3.0",
            "1 checking, 1 HYSA",
        ]

        state = _fresh_state()
        result = run_liquid_assets_section(state)

        data = result.data[SectionName.LIQUID_ASSETS.value]
        assert data["structure"] == "1 checking, 1 HYSA"


# ---------------------------------------------------------------------------
# Section 2: Investments
# ---------------------------------------------------------------------------


class TestInvestmentsSection:
    """Test investments section runner."""

    def test_collects_all_fields(self, mocker):
        """Section stores investment portfolio data with string enum values."""
        mock_text = mocker.patch("src.utils.onboarding_sections.questionary.text")
        mock_confirm = mocker.patch("src.utils.onboarding_sections.questionary.confirm")
        mock_select = mocker.patch("src.utils.onboarding_sections.questionary.select")

        # text: total_value, brokerage, retirement_value, sheets_id, account_num
        mock_text.return_value.ask.side_effect = [
            "100000",  # total_value
            "Fidelity",  # brokerage
            "50000",  # retirement_value
            "",  # google_sheets_id (skip)
            "",  # account_number (skip)
        ]
        # confirm: has_retirement
        mock_confirm.return_value.ask.return_value = True
        # select: allocation_strategy, risk_tolerance (called twice)
        mock_select.return_value.ask.side_effect = [
            "aggressive_growth",  # allocation_strategy
            "aggressive",  # risk_tolerance
        ]

        state = _fresh_state()
        result = run_investments_section(state)

        data = result.data[SectionName.INVESTMENTS.value]
        assert data["total_value"] == 100000.0
        assert data["brokerage"] == "Fidelity"
        assert data["has_retirement"] is True
        assert data["retirement_value"] == 50000.0
        # Enum fields stored as strings (NOT enum instances)
        assert data["allocation_strategy"] == "aggressive_growth"
        assert data["risk_tolerance"] == "aggressive"
        assert result.is_section_complete(SectionName.INVESTMENTS)


# ---------------------------------------------------------------------------
# Section 3: Cash Flow
# ---------------------------------------------------------------------------


class TestCashFlowSection:
    """Test cash flow section runner."""

    def test_collects_five_fields(self, mocker):
        """Section stores all 5 cash flow fields correctly."""
        mock_text = mocker.patch("src.utils.onboarding_sections.questionary.text")
        mock_text.return_value.ask.side_effect = [
            "8000",  # monthly_income
            "3000",  # fixed_expenses
            "2000",  # variable_expenses
            "1000",  # current_savings
            "2000",  # investment_capacity
        ]

        state = _fresh_state()
        result = run_cash_flow_section(state)

        data = result.data[SectionName.CASH_FLOW.value]
        assert data["monthly_income"] == 8000.0
        assert data["fixed_expenses"] == 3000.0
        assert data["variable_expenses"] == 2000.0
        assert data["current_savings"] == 1000.0
        assert data["investment_capacity"] == 2000.0
        assert result.is_section_complete(SectionName.CASH_FLOW)


# ---------------------------------------------------------------------------
# Section 5: Preferences
# ---------------------------------------------------------------------------


class TestPreferencesSection:
    """Test preferences section runner."""

    def test_collects_preferences(self, mocker):
        """Section stores philosophy string, focus areas list, emergency months."""
        mock_text = mocker.patch("src.utils.onboarding_sections.questionary.text")
        mock_select = mocker.patch("src.utils.onboarding_sections.questionary.select")
        mock_checkbox = mocker.patch(
            "src.utils.onboarding_sections.questionary.checkbox"
        )

        # select: investment_philosophy
        mock_select.return_value.ask.return_value = "growth"
        # checkbox: focus_areas
        mock_checkbox.return_value.ask.return_value = [
            "Dividend income",
            "Growth investing",
        ]
        # text: emergency_fund_months
        mock_text.return_value.ask.return_value = "6"

        state = _fresh_state()
        result = run_preferences_section(state)

        data = result.data[SectionName.PREFERENCES.value]
        # Philosophy stored as string (NOT enum instance)
        assert data["investment_philosophy"] == "growth"
        assert data["focus_areas"] == ["Dividend income", "Growth investing"]
        assert data["emergency_fund_months"] == 6
        assert result.is_section_complete(SectionName.PREFERENCES)


# ---------------------------------------------------------------------------
# Section 7: Environment Setup
# ---------------------------------------------------------------------------


class TestEnvSetupSection:
    """Test environment setup section runner."""

    def test_all_api_keys_skipped(self, mocker):
        """Section stores user_name and language with all APIs skipped."""
        mock_text = mocker.patch("src.utils.onboarding_sections.questionary.text")
        mock_confirm = mocker.patch("src.utils.onboarding_sections.questionary.confirm")

        # text: user_name, language, google_sheets_credentials
        mock_text.return_value.ask.side_effect = [
            "Alex",  # user_name
            "English",  # language
            "",  # google_sheets_credentials (skip)
        ]
        # confirm: has_alphavantage, has_brightdata (both False)
        mock_confirm.return_value.ask.return_value = False

        state = _fresh_state()
        result = run_env_setup_section(state)

        data = result.data[SectionName.ENV_SETUP.value]
        assert data["user_name"] == "Alex"
        assert data["language"] == "English"
        assert data["has_alphavantage"] is False
        assert data["alphavantage_key"] is None
        assert data["has_brightdata"] is False
        assert data["brightdata_key"] is None
        assert result.is_section_complete(SectionName.ENV_SETUP)

    def test_with_api_keys(self, mocker):
        """Section stores API keys when user provides them."""
        mock_text = mocker.patch("src.utils.onboarding_sections.questionary.text")
        mock_confirm = mocker.patch("src.utils.onboarding_sections.questionary.confirm")

        # text: user_name, language, av_key, bd_key, gs_creds
        mock_text.return_value.ask.side_effect = [
            "Alex",
            "English",
            "my-av-key-123",  # alphavantage_key
            "my-bd-key-456",  # brightdata_key
            "/path/to/creds",  # google_sheets_credentials
        ]
        # confirm: has_alphavantage=True, has_brightdata=True
        mock_confirm.return_value.ask.return_value = True

        state = _fresh_state()
        result = run_env_setup_section(state)

        data = result.data[SectionName.ENV_SETUP.value]
        assert data["has_alphavantage"] is True
        assert data["alphavantage_key"] == "my-av-key-123"
        assert data["has_brightdata"] is True
        assert data["brightdata_key"] == "my-bd-key-456"
        assert data["google_sheets_credentials"] == "/path/to/creds"


# ---------------------------------------------------------------------------
# Section 8: Summary
# ---------------------------------------------------------------------------


class TestSummarySection:
    """Test summary confirmation section."""

    def test_confirmed(self, mocker):
        """Summary confirmed stores confirmed=True and marks complete."""
        mock_confirm = mocker.patch("src.utils.onboarding_sections.questionary.confirm")
        mock_confirm.return_value.ask.return_value = True

        state = _prepopulated_state()
        result = run_summary_section(state)

        assert result.data[SectionName.SUMMARY.value]["confirmed"] is True
        assert result.is_section_complete(SectionName.SUMMARY)

    def test_declined_no_restart(self, mocker):
        """Summary declined without restart stores confirmed=False."""
        mock_confirm = mocker.patch("src.utils.onboarding_sections.questionary.confirm")
        # First call: confirm save (False), second call: restart (False)
        mock_confirm.return_value.ask.side_effect = [False, False]

        state = _prepopulated_state()
        result = run_summary_section(state)

        assert result.data[SectionName.SUMMARY.value]["confirmed"] is False

    def test_declined_with_restart(self, mocker):
        """Summary declined with restart clears state."""
        mock_confirm = mocker.patch("src.utils.onboarding_sections.questionary.confirm")
        # First call: confirm save (False), second call: restart (True)
        mock_confirm.return_value.ask.side_effect = [False, True]

        state = _prepopulated_state()
        result = run_summary_section(state)

        # State should be cleared on restart
        assert len(result.completed_sections) == 0
        assert result.current_section == SectionName.LIQUID_ASSETS
