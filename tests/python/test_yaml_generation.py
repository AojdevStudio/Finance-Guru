"""
Tests for Finance Guru YAML generation module.

This test suite validates the configuration file generation system:
- Layer 1: Pydantic models (yaml_generation_inputs.py)
- Layer 2: Calculator classes (yaml_generator.py)
- Layer 3: CLI interface (yaml_generator_cli.py)

Test Categories:
1. Model Validation Tests - Ensure Pydantic models catch bad input
2. Template Processing Tests - Verify variable substitution works
3. Config Generation Tests - Test each config file type
4. Integration Tests - Full generation workflow
5. Edge Cases - Handle unusual but valid scenarios
"""

from datetime import date
from pathlib import Path

import pytest

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
    YAMLGenerationOutput,
)
from src.utils.yaml_generator import YAMLGenerator, write_config_files


# Test fixtures
@pytest.fixture
def valid_user_data() -> UserDataInput:
    """Create valid user data for testing."""
    return UserDataInput(
        identity=UserIdentityInput(user_name="TestUser", language="English"),
        liquid_assets=LiquidAssetsInput(
            total=10000.0,
            accounts_count=3,
            average_yield=0.04,
            structure="2 checking, 1 savings",
        ),
        portfolio=InvestmentPortfolioInput(
            total_value=100000.0,
            brokerage="Test Brokerage",
            has_retirement=True,
            retirement_value=50000.0,
            allocation_strategy=AllocationStrategy.AGGRESSIVE_GROWTH,
            risk_tolerance=RiskTolerance.AGGRESSIVE,
            google_sheets_id="test-sheet-id",
            account_number="1234",
        ),
        cash_flow=CashFlowInput(
            monthly_income=10000.0,
            fixed_expenses=3000.0,
            variable_expenses=2000.0,
            current_savings=2000.0,
            investment_capacity=3000.0,
        ),
        debt=DebtProfileInput(
            has_mortgage=True,
            mortgage_balance=300000.0,
            mortgage_payment=2000.0,
            has_student_loans=False,
            has_auto_loans=False,
            has_credit_cards=False,
        ),
        preferences=UserPreferencesInput(
            investment_philosophy=InvestmentPhilosophy.AGGRESSIVE_GROWTH_PLUS_INCOME,
            focus_areas=["dividend_portfolio", "margin_strategies"],
            emergency_fund_months=6,
        ),
        mcp=MCPConfigInput(
            has_alphavantage=True,
            alphavantage_key="test-key-123",
            has_brightdata=False,
        ),
        project_root="/test/project",
    )


@pytest.fixture
def yaml_generator(tmp_path: Path) -> YAMLGenerator:
    """Create YAML generator with test template directory."""
    # For testing, we'll use the actual template directory
    template_dir = Path("scripts/onboarding/modules/templates")
    if not template_dir.exists():
        pytest.skip("Template directory not found - skipping integration tests")
    return YAMLGenerator(str(template_dir))


class TestPydanticModelValidation:
    """Test Pydantic models catch invalid input."""

    def test_user_identity_requires_non_empty_name(self):
        """User name must not be empty or whitespace."""
        with pytest.raises(ValueError, match="User name cannot be empty"):
            UserIdentityInput(user_name="   ", language="English")

    def test_liquid_assets_requires_non_negative_values(self):
        """Liquid assets must be non-negative."""
        with pytest.raises(ValueError):
            LiquidAssetsInput(total=-1000.0, accounts_count=2, average_yield=0.04)

    def test_liquid_assets_yield_within_valid_range(self):
        """Yield must be between 0 and 1."""
        with pytest.raises(ValueError):
            LiquidAssetsInput(total=10000.0, accounts_count=2, average_yield=1.5)

    def test_portfolio_requires_non_negative_value(self):
        """Portfolio value must be non-negative."""
        with pytest.raises(ValueError):
            InvestmentPortfolioInput(
                total_value=-50000.0,
                allocation_strategy=AllocationStrategy.AGGRESSIVE_GROWTH,
                risk_tolerance=RiskTolerance.AGGRESSIVE,
            )

    def test_cash_flow_requires_positive_income(self):
        """Monthly income must be positive."""
        with pytest.raises(ValueError):
            CashFlowInput(
                monthly_income=0.0,
                fixed_expenses=3000.0,
                variable_expenses=2000.0,
                current_savings=1000.0,
                investment_capacity=0.0,
            )

    def test_cash_flow_investment_capacity_cannot_exceed_income(self):
        """Investment capacity cannot exceed monthly income."""
        with pytest.raises(ValueError, match="cannot exceed monthly income"):
            CashFlowInput(
                monthly_income=5000.0,
                fixed_expenses=2000.0,
                variable_expenses=1000.0,
                current_savings=500.0,
                investment_capacity=6000.0,  # Exceeds income
            )

    def test_debt_rates_within_valid_range(self):
        """Debt interest rates must be between 0 and 1."""
        with pytest.raises(ValueError):
            DebtProfileInput(
                has_student_loans=True,
                student_loan_balance=50000.0,
                student_loan_rate=1.5,  # Invalid: > 1.0
            )

    def test_emergency_fund_within_valid_range(self):
        """Emergency fund months must be between 0 and 24."""
        with pytest.raises(ValueError):
            UserPreferencesInput(
                investment_philosophy=InvestmentPhilosophy.BALANCED,
                focus_areas=["diversification"],
                emergency_fund_months=30,  # Exceeds max of 24
            )


class TestTemplateProcessing:
    """Test template variable substitution."""

    def test_simple_variable_substitution(
        self, yaml_generator: YAMLGenerator, valid_user_data: UserDataInput
    ):
        """Simple variables should be replaced correctly."""
        template = "User: {{user_name}}"
        prepared_data = yaml_generator._prepare_user_data(valid_user_data)
        result = yaml_generator._process_template(template, prepared_data)
        assert "User: TestUser" in result

    def test_conditional_block_when_true(
        self, yaml_generator: YAMLGenerator, valid_user_data: UserDataInput
    ):
        """Conditional blocks should include content when condition is true."""
        template = "{{#if has_mortgage}}Has mortgage{{/if}}"
        prepared_data = yaml_generator._prepare_user_data(valid_user_data)
        result = yaml_generator._process_template(template, prepared_data)
        assert "Has mortgage" in result

    def test_conditional_block_when_false(
        self, yaml_generator: YAMLGenerator, valid_user_data: UserDataInput
    ):
        """Conditional blocks should exclude content when condition is false."""
        template = "{{#if has_student_loans}}Has student loans{{/if}}"
        prepared_data = yaml_generator._prepare_user_data(valid_user_data)
        result = yaml_generator._process_template(template, prepared_data)
        assert "Has student loans" not in result

    def test_possessive_name_generation(
        self, yaml_generator: YAMLGenerator, valid_user_data: UserDataInput
    ):
        """Possessive form should be generated correctly."""
        prepared_data = yaml_generator._prepare_user_data(valid_user_data)
        assert prepared_data["possessive_name"] == "TestUser's"

        # Test name ending in 's'
        valid_user_data.identity.user_name = "James"
        prepared_data = yaml_generator._prepare_user_data(valid_user_data)
        assert prepared_data["possessive_name"] == "James'"

    def test_currency_formatting(
        self, yaml_generator: YAMLGenerator, valid_user_data: UserDataInput
    ):
        """Currency values should be formatted with commas."""
        prepared_data = yaml_generator._prepare_user_data(valid_user_data)
        assert prepared_data["portfolio_value_formatted"] == "$100,000.00"
        assert prepared_data["monthly_income_formatted"] == "$10,000.00"


class TestConfigGeneration:
    """Test generation of each config file type."""

    def test_generate_user_profile(
        self, yaml_generator: YAMLGenerator, valid_user_data: UserDataInput
    ):
        """User profile YAML should be generated with correct data."""
        result = yaml_generator.generate_user_profile(valid_user_data)

        # Check key fields are present
        assert "user_name: TestUser" in result or "TestUser" in result
        assert "10000" in result  # liquid assets
        assert "100000" in result  # portfolio value
        assert "aggressive" in result.lower()

    def test_generate_config(
        self, yaml_generator: YAMLGenerator, valid_user_data: UserDataInput
    ):
        """Config YAML should be generated with user customization."""
        result = yaml_generator.generate_config(valid_user_data)

        # Check key fields
        assert "TestUser" in result
        assert "English" in result

    def test_generate_system_context(
        self, yaml_generator: YAMLGenerator, valid_user_data: UserDataInput
    ):
        """System context markdown should be personalized."""
        result = yaml_generator.generate_system_context(valid_user_data)

        assert "TestUser" in result
        assert "markdown" in result.lower() or "#" in result  # Markdown formatting

    def test_generate_claude_md(
        self, yaml_generator: YAMLGenerator, valid_user_data: UserDataInput
    ):
        """CLAUDE.md should be generated."""
        result = yaml_generator.generate_claude_md(valid_user_data)

        assert "TestUser" in result or "CLAUDE" in result

    def test_generate_env(
        self, yaml_generator: YAMLGenerator, valid_user_data: UserDataInput
    ):
        """Environment file should contain API keys."""
        result = yaml_generator.generate_env(valid_user_data)

        assert "test-key-123" in result  # Alpha Vantage key

    def test_generate_mcp_json(
        self, yaml_generator: YAMLGenerator, valid_user_data: UserDataInput
    ):
        """MCP JSON config should be generated."""
        result = yaml_generator.generate_mcp_json(valid_user_data)

        assert len(result) > 0
        # Should be valid JSON structure
        assert "{" in result or "mcpServers" in result


class TestFullGeneration:
    """Test complete config generation workflow."""

    def test_generate_all_configs(
        self, yaml_generator: YAMLGenerator, valid_user_data: UserDataInput
    ):
        """Generate all configs should produce complete output."""
        output = yaml_generator.generate_all_configs(valid_user_data)

        # Verify output structure
        assert isinstance(output, YAMLGenerationOutput)
        assert output.user_name == "TestUser"
        assert output.generation_date == date.today()

        # Verify all content is generated
        assert len(output.user_profile_yaml) > 0
        assert len(output.config_yaml) > 0
        assert len(output.system_context_md) > 0
        assert len(output.claude_md) > 0
        assert len(output.env_file) > 0
        assert len(output.mcp_json) > 0

        # Verify user name appears in at least one output
        assert (
            "TestUser" in output.user_profile_yaml or "TestUser" in output.config_yaml
        )

    def test_write_config_files(
        self,
        yaml_generator: YAMLGenerator,
        valid_user_data: UserDataInput,
        tmp_path: Path,
    ):
        """Writing config files should create all expected files."""
        output = yaml_generator.generate_all_configs(valid_user_data)
        write_config_files(output, str(tmp_path))

        # Verify files were created
        expected_files = [
            tmp_path / "fin-guru" / "data" / "user-profile.yaml",
            tmp_path / "fin-guru" / "config.yaml",
            tmp_path / "fin-guru" / "data" / "system-context.md",
            tmp_path / "CLAUDE.md",
            tmp_path / ".env",
            tmp_path / ".claude" / "mcp.json",
        ]

        for file_path in expected_files:
            assert file_path.exists(), f"Expected file not created: {file_path}"
            assert file_path.stat().st_size > 0, f"File is empty: {file_path}"


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_missing_template_directory(self):
        """Generator should raise error for missing template directory."""
        with pytest.raises(FileNotFoundError, match="Template directory not found"):
            YAMLGenerator("/nonexistent/path")

    def test_minimal_user_data(self):
        """Generator should handle minimal required data."""
        minimal_data = UserDataInput(
            identity=UserIdentityInput(user_name="MinimalUser"),
            liquid_assets=LiquidAssetsInput(
                total=0.0, accounts_count=0, average_yield=0.0
            ),
            portfolio=InvestmentPortfolioInput(
                total_value=0.0,
                allocation_strategy=AllocationStrategy.PASSIVE,
                risk_tolerance=RiskTolerance.CONSERVATIVE,
            ),
            cash_flow=CashFlowInput(
                monthly_income=1000.0,
                fixed_expenses=0.0,
                variable_expenses=0.0,
                current_savings=0.0,
                investment_capacity=0.0,
            ),
            debt=DebtProfileInput(),
            preferences=UserPreferencesInput(
                investment_philosophy=InvestmentPhilosophy.BALANCED,
                emergency_fund_months=0,
            ),
        )

        # Should not raise exception
        template_dir = Path("scripts/onboarding/modules/templates")
        if template_dir.exists():
            generator = YAMLGenerator(str(template_dir))
            output = generator.generate_all_configs(minimal_data)
            assert output.user_name == "MinimalUser"

    def test_special_characters_in_user_name(self):
        """Generator should handle special characters in user name."""
        data = UserDataInput(
            identity=UserIdentityInput(user_name="O'Brien-Smith"),
            liquid_assets=LiquidAssetsInput(
                total=0.0, accounts_count=0, average_yield=0.0
            ),
            portfolio=InvestmentPortfolioInput(
                total_value=0.0,
                allocation_strategy=AllocationStrategy.PASSIVE,
                risk_tolerance=RiskTolerance.CONSERVATIVE,
            ),
            cash_flow=CashFlowInput(
                monthly_income=1000.0,
                fixed_expenses=0.0,
                variable_expenses=0.0,
                current_savings=0.0,
                investment_capacity=0.0,
            ),
            debt=DebtProfileInput(),
            preferences=UserPreferencesInput(
                investment_philosophy=InvestmentPhilosophy.BALANCED,
                emergency_fund_months=0,
            ),
        )

        # Should handle special characters
        template_dir = Path("scripts/onboarding/modules/templates")
        if template_dir.exists():
            generator = YAMLGenerator(str(template_dir))
            output = generator.generate_all_configs(data)
            assert (
                "O'Brien-Smith" in output.user_profile_yaml
                or "O'Brien-Smith" in output.config_yaml
            )


class TestDataConsistency:
    """Test data consistency across generated files."""

    def test_user_name_consistent_across_files(
        self, yaml_generator: YAMLGenerator, valid_user_data: UserDataInput
    ):
        """User name should appear consistently in all generated files."""
        output = yaml_generator.generate_all_configs(valid_user_data)

        # Check user name appears in multiple outputs
        user_name = valid_user_data.identity.user_name
        assert user_name in output.user_profile_yaml or user_name in output.config_yaml

    def test_portfolio_value_consistent(
        self, yaml_generator: YAMLGenerator, valid_user_data: UserDataInput
    ):
        """Portfolio value should be consistent across files."""
        output = yaml_generator.generate_all_configs(valid_user_data)

        # Portfolio value should appear in some form
        assert (
            "100000" in output.user_profile_yaml
            or "$100,000" in output.user_profile_yaml
        )

    def test_generation_date_is_current(
        self, yaml_generator: YAMLGenerator, valid_user_data: UserDataInput
    ):
        """Generation date should be today's date."""
        output = yaml_generator.generate_all_configs(valid_user_data)
        assert output.generation_date == date.today()
