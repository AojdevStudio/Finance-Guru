"""
Tests for Finance Guru CLAUDE.md template generation.

This test suite validates the CLAUDE.md markdown file generation:
- Template variable substitution ({{user_name}}, {{possessive_name}}, etc.)
- Portfolio overview section with formatted currency values
- Personalization (possessive pronouns, user-specific data)
- Completeness of generated documentation
- Template consistency with current CLAUDE.md structure

Test Categories:
1. Template Loading Tests - Verify template file loads correctly
2. Variable Substitution Tests - Test all template variables
3. Possessive Name Tests - Handle names ending in 's' correctly
4. Currency Formatting Tests - Verify dollar amount formatting
5. Content Completeness Tests - Ensure all sections are present
6. Integration Tests - Full generation workflow
"""

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
)
from src.utils.yaml_generator import YAMLGenerator


# Test fixtures
@pytest.fixture
def valid_user_data() -> UserDataInput:
    """Create valid user data for testing CLAUDE.md generation."""
    return UserDataInput(
        identity=UserIdentityInput(user_name="Alex", language="English"),
        liquid_assets=LiquidAssetsInput(
            total=50000.0,
            accounts_count=5,
            average_yield=0.045,
            structure="2 checking, 2 savings, 1 business",
        ),
        portfolio=InvestmentPortfolioInput(
            total_value=500000.0,
            brokerage="Fidelity",
            has_retirement=True,
            retirement_value=300000.0,
            allocation_strategy=AllocationStrategy.AGGRESSIVE_GROWTH,
            risk_tolerance=RiskTolerance.AGGRESSIVE,
            google_sheets_id="test-sheet-123",
            account_number="Z12345678",
        ),
        cash_flow=CashFlowInput(
            monthly_income=25000.0,
            fixed_expenses=4500.0,
            variable_expenses=10000.0,
            current_savings=5000.0,
            investment_capacity=10500.0,
        ),
        debt=DebtProfileInput(
            has_mortgage=True,
            mortgage_balance=365000.0,
            mortgage_payment=1700.0,
            has_student_loans=True,
            student_loan_balance=50000.0,
            student_loan_rate=0.08,
            has_auto_loans=False,
            has_credit_cards=False,
        ),
        preferences=UserPreferencesInput(
            investment_philosophy=InvestmentPhilosophy.AGGRESSIVE_GROWTH_PLUS_INCOME,
            focus_areas=["dividend_portfolio", "margin_strategies", "tax_efficiency"],
            emergency_fund_months=0,
        ),
        mcp=MCPConfigInput(
            has_alphavantage=True,
            alphavantage_key="test-key-123",
            has_brightdata=False,
        ),
    )


@pytest.fixture
def user_data_name_ending_in_s() -> UserDataInput:
    """User data with name ending in 's' to test possessive handling."""
    return UserDataInput(
        identity=UserIdentityInput(user_name="James", language="English"),
        liquid_assets=LiquidAssetsInput(
            total=10000.0, accounts_count=2, average_yield=0.03
        ),
        portfolio=InvestmentPortfolioInput(
            total_value=100000.0,
            brokerage="Schwab",
            has_retirement=False,
            allocation_strategy=AllocationStrategy.HYBRID,
            risk_tolerance=RiskTolerance.MODERATE,
        ),
        cash_flow=CashFlowInput(
            monthly_income=10000.0,
            fixed_expenses=3000.0,
            variable_expenses=2000.0,
            current_savings=2000.0,
            investment_capacity=3000.0,
        ),
        debt=DebtProfileInput(
            has_mortgage=False,
            has_student_loans=False,
            has_auto_loans=False,
            has_credit_cards=False,
        ),
        preferences=UserPreferencesInput(
            investment_philosophy=InvestmentPhilosophy.GROWTH,
            focus_areas=["portfolio_optimization"],
            emergency_fund_months=6,
        ),
        mcp=MCPConfigInput(has_alphavantage=False, has_brightdata=False),
    )


@pytest.fixture
def generator() -> YAMLGenerator:
    """Create YAMLGenerator instance with template directory."""
    template_dir = (
        Path(__file__).parent.parent.parent / "scripts/onboarding/modules/templates"
    )
    return YAMLGenerator(str(template_dir))


# ============================================================================
# Template Loading Tests
# ============================================================================


def test_claude_md_template_exists(generator: YAMLGenerator):
    """Test that CLAUDE.template.md exists and is readable."""
    template_path = (
        Path(__file__).parent.parent.parent
        / "scripts/onboarding/modules/templates/CLAUDE.template.md"
    )
    assert template_path.exists(), "CLAUDE.template.md not found"
    assert template_path.is_file(), "CLAUDE.template.md is not a file"

    content = template_path.read_text()
    assert len(content) > 0, "CLAUDE.template.md is empty"
    # Template uses possessive_name throughout (not user_name directly)
    assert "{{possessive_name}}" in content, (
        "Template missing {{possessive_name}} variable"
    )


def test_claude_md_generation_succeeds(
    generator: YAMLGenerator, valid_user_data: UserDataInput
):
    """Test that CLAUDE.md generation completes without errors."""
    result = generator.generate_claude_md(valid_user_data)
    assert result is not None
    assert len(result) > 0
    assert isinstance(result, str)


# ============================================================================
# Variable Substitution Tests
# ============================================================================


def test_user_name_substitution(
    generator: YAMLGenerator, valid_user_data: UserDataInput
):
    """Test that {{user_name}} is replaced with actual user name."""
    result = generator.generate_claude_md(valid_user_data)

    # Should contain actual name
    assert "Alex" in result, "Generated CLAUDE.md missing user name 'Alex'"

    # Should NOT contain template variable
    assert "{{user_name}}" not in result, (
        "Generated CLAUDE.md contains unreplaced {{user_name}}"
    )


def test_possessive_name_substitution(
    generator: YAMLGenerator, valid_user_data: UserDataInput
):
    """Test that {{possessive_name}} is replaced correctly."""
    result = generator.generate_claude_md(valid_user_data)

    # For "Alex" -> "Alex's"
    assert "Alex's" in result, "Generated CLAUDE.md missing possessive form 'Alex's'"

    # Should NOT contain template variable
    assert "{{possessive_name}}" not in result, (
        "Generated CLAUDE.md contains unreplaced {{possessive_name}}"
    )


def test_possessive_name_ending_in_s(
    generator: YAMLGenerator, user_data_name_ending_in_s: UserDataInput
):
    """Test possessive handling for names ending in 's' (James -> James')."""
    result = generator.generate_claude_md(user_data_name_ending_in_s)

    # For "James" -> "James'"
    assert "James'" in result, "Generated CLAUDE.md should use James' (not James's)"

    # Should not have double possessive
    assert "James's" not in result, (
        "Generated CLAUDE.md incorrectly uses James's instead of James'"
    )


def test_risk_tolerance_substitution(
    generator: YAMLGenerator, valid_user_data: UserDataInput
):
    """Test that {{risk_tolerance}} is replaced with actual value."""
    result = generator.generate_claude_md(valid_user_data)

    # Should contain the risk tolerance value
    assert "aggressive" in result.lower(), "Generated CLAUDE.md missing risk tolerance"

    # Should NOT contain template variable
    assert "{{risk_tolerance}}" not in result, (
        "Generated CLAUDE.md contains unreplaced {{risk_tolerance}}"
    )


def test_brokerage_substitution(
    generator: YAMLGenerator, valid_user_data: UserDataInput
):
    """Test that {{brokerage}} is replaced with actual brokerage name."""
    result = generator.generate_claude_md(valid_user_data)

    # Should contain the brokerage name
    assert "Fidelity" in result, "Generated CLAUDE.md missing brokerage name"

    # Should NOT contain template variable
    assert "{{brokerage}}" not in result, (
        "Generated CLAUDE.md contains unreplaced {{brokerage}}"
    )


# ============================================================================
# Currency Formatting Tests
# ============================================================================


def test_portfolio_value_formatting(
    generator: YAMLGenerator, valid_user_data: UserDataInput
):
    """Test that portfolio value is formatted as currency with commas."""
    result = generator.generate_claude_md(valid_user_data)

    # For $500,000 -> should show "$500,000"
    assert "$500,000" in result, "Generated CLAUDE.md missing formatted portfolio value"

    # Should NOT contain unformatted value
    assert "500000" not in result, "Generated CLAUDE.md contains unformatted value"

    # Should NOT contain template variable
    assert "{{portfolio_value_formatted}}" not in result, (
        "Generated CLAUDE.md contains unreplaced {{portfolio_value_formatted}}"
    )


def test_monthly_income_formatting(
    generator: YAMLGenerator, valid_user_data: UserDataInput
):
    """Test that monthly income is formatted as currency."""
    result = generator.generate_claude_md(valid_user_data)

    # For $25,000 -> should show "$25,000"
    assert "$25,000" in result, "Generated CLAUDE.md missing formatted monthly income"

    # Should NOT contain template variable
    assert "{{monthly_income_formatted}}" not in result, (
        "Generated CLAUDE.md contains unreplaced {{monthly_income_formatted}}"
    )


def test_investment_capacity_formatting(
    generator: YAMLGenerator, valid_user_data: UserDataInput
):
    """Test that investment capacity is formatted as currency."""
    result = generator.generate_claude_md(valid_user_data)

    # For $10,500 -> should show "$10,500"
    assert "$10,500" in result, (
        "Generated CLAUDE.md missing formatted investment capacity"
    )

    # Should NOT contain template variable
    assert "{{investment_capacity_formatted}}" not in result, (
        "Generated CLAUDE.md contains unreplaced {{investment_capacity_formatted}}"
    )


# ============================================================================
# Content Completeness Tests
# ============================================================================


def test_required_sections_present(
    generator: YAMLGenerator, valid_user_data: UserDataInput
):
    """Test that all required sections are present in generated CLAUDE.md."""
    result = generator.generate_claude_md(valid_user_data)

    required_sections = [
        "# CLAUDE.md",
        "## Architecture",
        "## Technology Stack",
        "## CLI Command Patterns",
        "## Financial Analysis Tools",
        "## Agent-Tool Matrix",
        "## Output & Validation",
        "## Version Info",
        "## Landing the Plane",
    ]

    for section in required_sections:
        assert section in result, (
            f"Generated CLAUDE.md missing required section: {section}"
        )


def test_key_principle_personalized(
    generator: YAMLGenerator, valid_user_data: UserDataInput
):
    """Test that the Key Principle statement is personalized."""
    result = generator.generate_claude_md(valid_user_data)

    # Should contain personalized key principle
    assert "Alex's" in result, "Key Principle not personalized with possessive name"
    assert "Finance Guru" in result, "Key Principle missing 'Finance Guru' reference"


def test_portfolio_overview_section_complete(
    generator: YAMLGenerator, valid_user_data: UserDataInput
):
    """Test that Portfolio Overview section contains all user-specific data."""
    result = generator.generate_claude_md(valid_user_data)

    # Check for all portfolio overview fields
    assert "$500,000" in result, "Portfolio Overview missing portfolio value"
    assert "$25,000" in result, "Portfolio Overview missing monthly income"
    assert "$10,500" in result, "Portfolio Overview missing investment capacity"
    assert "aggressive" in result.lower(), "Portfolio Overview missing risk profile"
    assert "Fidelity" in result, "Portfolio Overview missing brokerage"


def test_tools_table_present(generator: YAMLGenerator, valid_user_data: UserDataInput):
    """Test that Financial Analysis Tools table is present and complete."""
    result = generator.generate_claude_md(valid_user_data)

    # Check for key tools in the table
    tools = [
        "Risk Metrics",
        "Momentum",
        "Volatility",
        "Correlation",
        "Backtesting",
        "Moving Averages",
        "Portfolio Optimizer",
        "ITC Risk",
    ]

    for tool in tools:
        assert tool in result, f"Financial Analysis Tools table missing {tool}"


def test_agent_tool_matrix_present(
    generator: YAMLGenerator, valid_user_data: UserDataInput
):
    """Test that Agent-Tool Matrix is present with all agents."""
    result = generator.generate_claude_md(valid_user_data)

    # Check for all agents
    agents = [
        "Market Researcher",
        "Quant Analyst",
        "Strategy Advisor",
        "Compliance Officer",
        "Margin Specialist",
    ]

    for agent in agents:
        assert agent in result, f"Agent-Tool Matrix missing {agent}"


def test_landing_the_plane_section(
    generator: YAMLGenerator, valid_user_data: UserDataInput
):
    """Test that Landing the Plane section is complete with all steps."""
    result = generator.generate_claude_md(valid_user_data)

    # Check for critical workflow steps
    assert "git pull --rebase" in result, "Landing the Plane missing git commands"
    assert "bd sync" in result, "Landing the Plane missing bd sync"
    assert "git push" in result, "Landing the Plane missing git push"
    assert "MANDATORY WORKFLOW" in result, (
        "Landing the Plane missing mandatory workflow section"
    )


# ============================================================================
# Template Consistency Tests
# ============================================================================


def test_no_unreplaced_variables(
    generator: YAMLGenerator, valid_user_data: UserDataInput
):
    """Test that no template variables remain unreplaced."""
    result = generator.generate_claude_md(valid_user_data)

    # Common template variable patterns
    template_vars = [
        "{{user_name}}",
        "{{possessive_name}}",
        "{{language}}",
        "{{portfolio_value_formatted}}",
        "{{monthly_income_formatted}}",
        "{{investment_capacity_formatted}}",
        "{{risk_tolerance}}",
        "{{brokerage}}",
        "{{timestamp}}",
        "{{date}}",
    ]

    for var in template_vars:
        assert var not in result, (
            f"Generated CLAUDE.md contains unreplaced variable: {var}"
        )


def test_timestamp_and_date_present(
    generator: YAMLGenerator, valid_user_data: UserDataInput
):
    """Test that timestamp and date are generated and included."""
    result = generator.generate_claude_md(valid_user_data)

    # Should contain "Generated:" footer
    assert "**Generated**:" in result, "Generated CLAUDE.md missing timestamp footer"

    # Should NOT contain template variables
    assert "{{timestamp}}" not in result, (
        "Generated CLAUDE.md contains unreplaced {{timestamp}}"
    )
    assert "{{date}}" not in result, "Generated CLAUDE.md contains unreplaced {{date}}"


# ============================================================================
# Integration Tests
# ============================================================================


def test_full_generation_workflow(
    generator: YAMLGenerator, valid_user_data: UserDataInput
):
    """Test complete CLAUDE.md generation workflow end-to-end."""
    # Generate CLAUDE.md
    result = generator.generate_claude_md(valid_user_data)

    # Validate basic structure
    assert result.startswith("# CLAUDE.md"), "Generated file doesn't start with header"
    assert len(result) > 1000, "Generated CLAUDE.md seems too short"

    # Validate personalization
    assert "Alex's" in result, "Missing personalization"
    assert "$500,000" in result, "Missing portfolio value"
    assert "Fidelity" in result, "Missing brokerage"

    # Validate completeness
    assert "## Architecture" in result, "Missing Architecture section"
    assert "## Financial Analysis Tools" in result, "Missing Tools section"
    assert "## Landing the Plane" in result, "Missing Landing section"

    # Validate no template variables
    assert "{{" not in result, "Contains unreplaced template variables"
    assert "}}" not in result, "Contains unreplaced template variables"


def test_different_user_generates_different_claude_md(generator: YAMLGenerator):
    """Test that different users get personalized CLAUDE.md files."""
    # User 1: Alex with $500k portfolio
    user1 = UserDataInput(
        identity=UserIdentityInput(user_name="Alex", language="English"),
        liquid_assets=LiquidAssetsInput(
            total=50000.0, accounts_count=5, average_yield=0.045
        ),
        portfolio=InvestmentPortfolioInput(
            total_value=500000.0,
            brokerage="Fidelity",
            has_retirement=True,
            retirement_value=300000.0,
            allocation_strategy=AllocationStrategy.AGGRESSIVE_GROWTH,
            risk_tolerance=RiskTolerance.AGGRESSIVE,
        ),
        cash_flow=CashFlowInput(
            monthly_income=25000.0,
            fixed_expenses=4500.0,
            variable_expenses=10000.0,
            current_savings=5000.0,
            investment_capacity=10500.0,
        ),
        debt=DebtProfileInput(
            has_mortgage=True,
            mortgage_balance=365000.0,
            mortgage_payment=1700.0,
            has_student_loans=False,
            has_auto_loans=False,
            has_credit_cards=False,
        ),
        preferences=UserPreferencesInput(
            investment_philosophy=InvestmentPhilosophy.AGGRESSIVE_GROWTH_PLUS_INCOME,
            focus_areas=["dividend_portfolio"],
            emergency_fund_months=0,
        ),
        mcp=MCPConfigInput(has_alphavantage=True, alphavantage_key="key1"),
    )

    # User 2: Sarah with $100k portfolio
    user2 = UserDataInput(
        identity=UserIdentityInput(user_name="Sarah", language="English"),
        liquid_assets=LiquidAssetsInput(
            total=10000.0, accounts_count=2, average_yield=0.03
        ),
        portfolio=InvestmentPortfolioInput(
            total_value=100000.0,
            brokerage="Schwab",
            has_retirement=False,
            allocation_strategy=AllocationStrategy.HYBRID,
            risk_tolerance=RiskTolerance.MODERATE,
        ),
        cash_flow=CashFlowInput(
            monthly_income=10000.0,
            fixed_expenses=3000.0,
            variable_expenses=2000.0,
            current_savings=2000.0,
            investment_capacity=3000.0,
        ),
        debt=DebtProfileInput(
            has_mortgage=False,
            has_student_loans=False,
            has_auto_loans=False,
            has_credit_cards=False,
        ),
        preferences=UserPreferencesInput(
            investment_philosophy=InvestmentPhilosophy.GROWTH,
            focus_areas=["portfolio_optimization"],
            emergency_fund_months=6,
        ),
        mcp=MCPConfigInput(has_alphavantage=False, has_brightdata=False),
    )

    # Generate both
    result1 = generator.generate_claude_md(user1)
    result2 = generator.generate_claude_md(user2)

    # They should be different
    assert result1 != result2, "Different users generated identical CLAUDE.md"

    # User 1 specific
    assert "Alex's" in result1 and "Alex's" not in result2
    assert "$500,000" in result1 and "$500,000" not in result2
    assert "Fidelity" in result1 and "Schwab" in result2

    # User 2 specific
    assert "Sarah's" in result2 and "Sarah's" not in result1
    assert "$100,000" in result2 and "$100,000" not in result1
