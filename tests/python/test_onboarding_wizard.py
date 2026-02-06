"""
Integration tests for the onboarding wizard CLI.

Tests the complete pipeline:
- State-to-model conversion (string-to-enum mapping)
- Config file generation to correct paths
- Backup of existing files
- SECTION_ORDER structure

Author: Finance Guru Development Team
Created: 2026-02-05
"""

import pytest
from pathlib import Path

from src.cli.onboarding_wizard import (
    SECTION_ORDER,
    convert_state_to_user_data,
    generate_config_files,
)
from src.models.onboarding_inputs import OnboardingState, SectionName
from src.models.yaml_generation_inputs import (
    AllocationStrategy,
    CashFlowInput,
    DebtProfileInput,
    InvestmentPhilosophy,
    InvestmentPortfolioInput,
    LiquidAssetsInput,
    MCPConfigInput,
    RiskTolerance,
    UserDataInput,
    UserIdentityInput,
    UserPreferencesInput,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def completed_state() -> OnboardingState:
    """Create an OnboardingState simulating a fully completed wizard.

    Enum fields stored as raw strings -- matching what section runners
    produce from questionary prompts.
    """
    state = OnboardingState.create_new()
    state.data[SectionName.LIQUID_ASSETS.value] = {
        "total": 25000.0,
        "accounts_count": 3,
        "average_yield": 0.045,  # decimal (converted by section runner)
        "structure": "2 checking, 1 HYSA",
    }
    state.data[SectionName.INVESTMENTS.value] = {
        "total_value": 150000.0,
        "brokerage": "Fidelity",
        "has_retirement": True,
        "retirement_value": 60000.0,
        "allocation_strategy": "aggressive_growth",  # string, not enum
        "risk_tolerance": "aggressive",              # string, not enum
        "google_sheets_id": "abc123",
        "account_number": "4567",
    }
    state.data[SectionName.CASH_FLOW.value] = {
        "monthly_income": 10000.0,
        "fixed_expenses": 3500.0,
        "variable_expenses": 2000.0,
        "current_savings": 1500.0,
        "investment_capacity": 3000.0,
    }
    state.data[SectionName.DEBT.value] = {
        "has_mortgage": True,
        "mortgage_balance": 300000.0,
        "mortgage_payment": 2000.0,
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
        "investment_philosophy": "growth",  # string, not enum
        "focus_areas": ["Dividend income", "Growth investing"],
        "emergency_fund_months": 6,
    }
    state.data[SectionName.BROKER.value] = {
        "brokerage": "Fidelity",
    }
    state.data[SectionName.ENV_SETUP.value] = {
        "user_name": "TestUser",
        "language": "English",
        "has_alphavantage": True,
        "alphavantage_key": "test-av-key",
        "has_brightdata": False,
        "brightdata_key": None,
        "google_sheets_credentials": None,
    }
    state.data[SectionName.SUMMARY.value] = {"confirmed": True}
    return state


@pytest.fixture
def valid_user_data() -> UserDataInput:
    """Create a UserDataInput for config generation tests."""
    return UserDataInput(
        identity=UserIdentityInput(user_name="TestUser", language="English"),
        liquid_assets=LiquidAssetsInput(
            total=25000.0,
            accounts_count=3,
            average_yield=0.045,
            structure="2 checking, 1 HYSA",
        ),
        portfolio=InvestmentPortfolioInput(
            total_value=150000.0,
            brokerage="Fidelity",
            has_retirement=True,
            retirement_value=60000.0,
            allocation_strategy=AllocationStrategy.AGGRESSIVE_GROWTH,
            risk_tolerance=RiskTolerance.AGGRESSIVE,
            google_sheets_id="abc123",
            account_number="4567",
        ),
        cash_flow=CashFlowInput(
            monthly_income=10000.0,
            fixed_expenses=3500.0,
            variable_expenses=2000.0,
            current_savings=1500.0,
            investment_capacity=3000.0,
        ),
        debt=DebtProfileInput(
            has_mortgage=True,
            mortgage_balance=300000.0,
            mortgage_payment=2000.0,
        ),
        preferences=UserPreferencesInput(
            investment_philosophy=InvestmentPhilosophy.GROWTH,
            focus_areas=["Dividend income", "Growth investing"],
            emergency_fund_months=6,
        ),
        mcp=MCPConfigInput(
            has_alphavantage=True,
            alphavantage_key="test-av-key",
        ),
        project_root="/tmp/test-project",
    )


# ---------------------------------------------------------------------------
# SECTION_ORDER structure
# ---------------------------------------------------------------------------


class TestSectionOrder:
    """Test the SECTION_ORDER configuration."""

    def test_has_eight_entries(self):
        assert len(SECTION_ORDER) == 8

    def test_first_is_liquid_assets(self):
        assert SECTION_ORDER[0][0] == SectionName.LIQUID_ASSETS

    def test_last_is_summary(self):
        assert SECTION_ORDER[-1][0] == SectionName.SUMMARY

    def test_all_section_names_present(self):
        section_names = [name for name, _ in SECTION_ORDER]
        for section in SectionName:
            assert section in section_names, f"{section} missing from SECTION_ORDER"


# ---------------------------------------------------------------------------
# State-to-model conversion
# ---------------------------------------------------------------------------


class TestConvertStateToUserData:
    """Test convert_state_to_user_data with string-to-enum mapping."""

    def test_returns_valid_user_data(self, completed_state):
        """Produces a validated UserDataInput from completed wizard state."""
        result = convert_state_to_user_data(
            completed_state, "/tmp/test-project"
        )
        assert isinstance(result, UserDataInput)

    def test_identity_from_env_setup(self, completed_state):
        """User name and language come from env_setup section."""
        result = convert_state_to_user_data(completed_state, "/tmp/test")
        assert result.identity.user_name == "TestUser"
        assert result.identity.language == "English"

    def test_liquid_assets_mapping(self, completed_state):
        """Liquid assets mapped correctly with decimal yield."""
        result = convert_state_to_user_data(completed_state, "/tmp/test")
        assert result.liquid_assets.total == 25000.0
        assert result.liquid_assets.accounts_count == 3
        assert result.liquid_assets.average_yield == pytest.approx(0.045)
        assert result.liquid_assets.structure == "2 checking, 1 HYSA"

    def test_string_to_enum_conversion_risk_tolerance(self, completed_state):
        """Risk tolerance string 'aggressive' -> RiskTolerance.AGGRESSIVE."""
        result = convert_state_to_user_data(completed_state, "/tmp/test")
        assert isinstance(result.portfolio.risk_tolerance, RiskTolerance)
        assert result.portfolio.risk_tolerance == RiskTolerance.AGGRESSIVE

    def test_string_to_enum_conversion_allocation(self, completed_state):
        """Allocation string 'aggressive_growth' -> AllocationStrategy.AGGRESSIVE_GROWTH."""
        result = convert_state_to_user_data(completed_state, "/tmp/test")
        assert isinstance(
            result.portfolio.allocation_strategy, AllocationStrategy
        )
        assert (
            result.portfolio.allocation_strategy
            == AllocationStrategy.AGGRESSIVE_GROWTH
        )

    def test_string_to_enum_conversion_philosophy(self, completed_state):
        """Philosophy string 'growth' -> InvestmentPhilosophy.GROWTH."""
        result = convert_state_to_user_data(completed_state, "/tmp/test")
        assert isinstance(
            result.preferences.investment_philosophy, InvestmentPhilosophy
        )
        assert (
            result.preferences.investment_philosophy
            == InvestmentPhilosophy.GROWTH
        )

    def test_project_root_set(self, completed_state):
        """Project root is passed through."""
        result = convert_state_to_user_data(
            completed_state, "/custom/project/root"
        )
        assert result.project_root == "/custom/project/root"

    def test_mcp_config_from_env_setup(self, completed_state):
        """MCP config populated from env_setup section."""
        result = convert_state_to_user_data(completed_state, "/tmp/test")
        assert result.mcp.has_alphavantage is True
        assert result.mcp.alphavantage_key == "test-av-key"
        assert result.mcp.has_brightdata is False

    def test_unknown_enum_falls_back_to_default(self, completed_state):
        """Unknown enum string falls back gracefully."""
        completed_state.data[SectionName.INVESTMENTS.value][
            "risk_tolerance"
        ] = "extremely_risky"

        with pytest.warns(UserWarning, match="Unknown RiskTolerance"):
            result = convert_state_to_user_data(
                completed_state, "/tmp/test"
            )
        # Falls back to default (MODERATE)
        assert result.portfolio.risk_tolerance == RiskTolerance.MODERATE

    def test_missing_section_uses_defaults(self):
        """Missing section data uses sensible defaults."""
        state = OnboardingState.create_new()
        # Only provide env_setup (for identity) and minimal cash_flow
        state.data[SectionName.ENV_SETUP.value] = {
            "user_name": "Minimal",
            "language": "English",
        }
        state.data[SectionName.CASH_FLOW.value] = {
            "monthly_income": 1000.0,
            "fixed_expenses": 0.0,
            "variable_expenses": 0.0,
            "current_savings": 0.0,
            "investment_capacity": 0.0,
        }

        result = convert_state_to_user_data(state, "/tmp/test")
        assert result.identity.user_name == "Minimal"
        assert result.liquid_assets.total == 0.0
        assert result.portfolio.total_value == 0.0
        assert result.debt.has_mortgage is False


# ---------------------------------------------------------------------------
# Config file generation
# ---------------------------------------------------------------------------


class TestGenerateConfigFiles:
    """Test config file generation to correct paths."""

    def test_generates_all_files(self, valid_user_data, tmp_path):
        """All config files are created at correct locations."""
        # Copy templates to tmp_path so we can use it as project root
        import shutil

        template_src = Path("scripts/onboarding/modules/templates")
        if not template_src.exists():
            pytest.skip("Template directory not found")

        template_dest = tmp_path / "scripts" / "onboarding" / "modules" / "templates"
        shutil.copytree(template_src, template_dest)

        # Also create .claude dir
        (tmp_path / ".claude").mkdir(exist_ok=True)

        valid_user_data.project_root = str(tmp_path)
        generate_config_files(valid_user_data, tmp_path)

        # Verify private files
        assert (
            tmp_path / "fin-guru-private" / "fin-guru" / "data" / "user-profile.yaml"
        ).exists()
        assert (
            tmp_path / "fin-guru-private" / "fin-guru" / "config.yaml"
        ).exists()
        assert (
            tmp_path / "fin-guru-private" / "fin-guru" / "data" / "system-context.md"
        ).exists()

        # Verify project-root files
        assert (tmp_path / "CLAUDE.md").exists()
        assert (tmp_path / ".env").exists()
        assert (tmp_path / ".claude" / "mcp.json").exists()

    def test_generated_files_contain_user_name(self, valid_user_data, tmp_path):
        """Generated files contain actual user name, not template placeholders."""
        import shutil

        template_src = Path("scripts/onboarding/modules/templates")
        if not template_src.exists():
            pytest.skip("Template directory not found")

        template_dest = tmp_path / "scripts" / "onboarding" / "modules" / "templates"
        shutil.copytree(template_src, template_dest)
        (tmp_path / ".claude").mkdir(exist_ok=True)

        valid_user_data.project_root = str(tmp_path)
        generate_config_files(valid_user_data, tmp_path)

        profile = (
            tmp_path
            / "fin-guru-private"
            / "fin-guru"
            / "data"
            / "user-profile.yaml"
        ).read_text()
        assert "TestUser" in profile
        assert "{{user_name}}" not in profile

    def test_backs_up_existing_files(self, valid_user_data, tmp_path):
        """Existing CLAUDE.md, .env, and mcp.json are backed up."""
        import shutil

        template_src = Path("scripts/onboarding/modules/templates")
        if not template_src.exists():
            pytest.skip("Template directory not found")

        template_dest = tmp_path / "scripts" / "onboarding" / "modules" / "templates"
        shutil.copytree(template_src, template_dest)

        # Create fake existing files
        (tmp_path / "CLAUDE.md").write_text("existing claude", encoding="utf-8")
        (tmp_path / ".env").write_text("existing env", encoding="utf-8")
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir(exist_ok=True)
        (claude_dir / "mcp.json").write_text("existing mcp", encoding="utf-8")

        valid_user_data.project_root = str(tmp_path)
        generate_config_files(valid_user_data, tmp_path)

        # Verify backups exist
        assert (tmp_path / "CLAUDE.md.backup").exists()
        assert (tmp_path / ".env.backup").exists()
        assert (claude_dir / "mcp.json.backup").exists()

        # Verify backup contents are the old files
        assert (tmp_path / "CLAUDE.md.backup").read_text() == "existing claude"
        assert (tmp_path / ".env.backup").read_text() == "existing env"
        assert (claude_dir / "mcp.json.backup").read_text() == "existing mcp"

        # Verify new files overwrite the old
        new_claude = (tmp_path / "CLAUDE.md").read_text()
        assert new_claude != "existing claude"
        assert "TestUser" in new_claude

    def test_mcp_json_written_via_explicit_path(self, valid_user_data, tmp_path):
        """mcp.json is written to .claude/mcp.json at project root."""
        import shutil

        template_src = Path("scripts/onboarding/modules/templates")
        if not template_src.exists():
            pytest.skip("Template directory not found")

        template_dest = tmp_path / "scripts" / "onboarding" / "modules" / "templates"
        shutil.copytree(template_src, template_dest)
        (tmp_path / ".claude").mkdir(exist_ok=True)

        valid_user_data.project_root = str(tmp_path)
        generate_config_files(valid_user_data, tmp_path)

        mcp_path = tmp_path / ".claude" / "mcp.json"
        assert mcp_path.exists()
        content = mcp_path.read_text()
        assert len(content) > 0
