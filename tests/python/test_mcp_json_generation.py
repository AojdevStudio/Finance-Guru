"""
Tests for Finance Guru MCP JSON configuration generation.

This test suite validates the MCP server configuration JSON file generation:
- Template variable substitution ({{user_name}}, {{timestamp}}, etc.)
- Conditional inclusion of optional MCP servers (Alpha Vantage, BrightData)
- Valid JSON structure
- Required vs optional server configuration
- API key inclusion based on user data

Test Categories:
1. Template Loading Tests - Verify template file loads correctly
2. Variable Substitution Tests - Test all template variables
3. JSON Validity Tests - Ensure generated content is valid JSON
4. Required Servers Tests - Verify exa, perplexity, gdrive, context7 are always present
5. Optional Servers Tests - Test conditional inclusion based on API keys
6. Integration Tests - Full generation workflow
"""

import json
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
def valid_user_data_with_all_mcp() -> UserDataInput:
    """Create valid user data with all MCP servers (Alpha Vantage + BrightData)."""
    return UserDataInput(
        identity=UserIdentityInput(user_name="Alex", language="English"),
        liquid_assets=LiquidAssetsInput(
            total=50000.0,
            accounts_count=5,
            average_yield=0.045,
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
        ),
        preferences=UserPreferencesInput(
            investment_philosophy=InvestmentPhilosophy.AGGRESSIVE_GROWTH_PLUS_INCOME,
            focus_areas=["dividend_portfolio"],
            emergency_fund_months=0,
        ),
        mcp=MCPConfigInput(
            has_alphavantage=True,
            alphavantage_key="test-alpha-key-123",
            has_brightdata=True,
            brightdata_key="test-bright-key-456",
        ),
    )


@pytest.fixture
def valid_user_data_no_optional_mcp() -> UserDataInput:
    """Create valid user data with NO optional MCP servers."""
    return UserDataInput(
        identity=UserIdentityInput(user_name="Sarah", language="English"),
        liquid_assets=LiquidAssetsInput(
            total=10000.0,
            accounts_count=2,
            average_yield=0.03,
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
        ),
        preferences=UserPreferencesInput(
            investment_philosophy=InvestmentPhilosophy.GROWTH,
            focus_areas=["portfolio_optimization"],
            emergency_fund_months=6,
        ),
        mcp=MCPConfigInput(
            has_alphavantage=False,
            has_brightdata=False,
        ),
    )


@pytest.fixture
def valid_user_data_only_alphavantage() -> UserDataInput:
    """Create valid user data with ONLY Alpha Vantage (no BrightData)."""
    return UserDataInput(
        identity=UserIdentityInput(user_name="James", language="English"),
        liquid_assets=LiquidAssetsInput(
            total=25000.0,
            accounts_count=3,
            average_yield=0.04,
        ),
        portfolio=InvestmentPortfolioInput(
            total_value=250000.0,
            brokerage="Vanguard",
            has_retirement=True,
            retirement_value=150000.0,
            allocation_strategy=AllocationStrategy.PASSIVE,
            risk_tolerance=RiskTolerance.CONSERVATIVE,
        ),
        cash_flow=CashFlowInput(
            monthly_income=15000.0,
            fixed_expenses=5000.0,
            variable_expenses=3000.0,
            current_savings=3000.0,
            investment_capacity=4000.0,
        ),
        debt=DebtProfileInput(
            has_mortgage=True,
            mortgage_balance=200000.0,
            mortgage_payment=1200.0,
        ),
        preferences=UserPreferencesInput(
            investment_philosophy=InvestmentPhilosophy.BALANCED,
            focus_areas=["retirement_planning"],
            emergency_fund_months=12,
        ),
        mcp=MCPConfigInput(
            has_alphavantage=True,
            alphavantage_key="test-alpha-only-789",
            has_brightdata=False,
        ),
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


def test_mcp_json_template_exists(generator: YAMLGenerator):
    """Test that mcp.template.json exists and is readable."""
    template_path = (
        Path(__file__).parent.parent.parent
        / "scripts/onboarding/modules/templates/mcp.template.json"
    )
    assert template_path.exists(), "mcp.template.json not found"
    assert template_path.is_file(), "mcp.template.json is not a file"

    content = template_path.read_text()
    assert len(content) > 0, "mcp.template.json is empty"
    assert "mcpServers" in content, "Template missing mcpServers key"
    assert "{{user_name}}" in content, "Template missing {{user_name}} variable"


def test_mcp_json_generation_succeeds(
    generator: YAMLGenerator, valid_user_data_with_all_mcp: UserDataInput
):
    """Test that MCP JSON generation completes without errors."""
    result = generator.generate_mcp_json(valid_user_data_with_all_mcp)
    assert result is not None
    assert len(result) > 0
    assert isinstance(result, str)


# ============================================================================
# JSON Validity Tests
# ============================================================================


def test_generated_mcp_json_is_valid_json(
    generator: YAMLGenerator, valid_user_data_with_all_mcp: UserDataInput
):
    """Test that generated MCP JSON is valid, parseable JSON."""
    result = generator.generate_mcp_json(valid_user_data_with_all_mcp)

    # Should be parseable as JSON
    try:
        parsed = json.loads(result)
    except json.JSONDecodeError as e:
        pytest.fail(f"Generated MCP JSON is not valid JSON: {e}")

    # Should have top-level mcpServers key
    assert "mcpServers" in parsed, "Generated JSON missing 'mcpServers' key"
    assert isinstance(parsed["mcpServers"], dict), "'mcpServers' should be a dictionary"


def test_generated_mcp_json_has_metadata(
    generator: YAMLGenerator, valid_user_data_with_all_mcp: UserDataInput
):
    """Test that generated MCP JSON includes metadata section."""
    result = generator.generate_mcp_json(valid_user_data_with_all_mcp)
    parsed = json.loads(result)

    # Should have metadata
    assert "_meta" in parsed, "Generated JSON missing '_meta' section"
    meta = parsed["_meta"]

    # Metadata should have required fields
    assert "generated_by" in meta, "Metadata missing 'generated_by'"
    assert "generated_at" in meta, "Metadata missing 'generated_at'"
    assert "user" in meta, "Metadata missing 'user'"
    assert "version" in meta, "Metadata missing 'version'"

    # User should be correct
    assert meta["user"] == "Alex", f"Expected user 'Alex', got '{meta['user']}'"


# ============================================================================
# Required Servers Tests
# ============================================================================


def test_required_mcp_servers_always_present(
    generator: YAMLGenerator, valid_user_data_no_optional_mcp: UserDataInput
):
    """Test that required MCP servers are always included."""
    result = generator.generate_mcp_json(valid_user_data_no_optional_mcp)
    parsed = json.loads(result)

    mcp_servers = parsed["mcpServers"]

    # Required servers (always present)
    required_servers = ["exa", "perplexity", "gdrive", "context7"]

    for server in required_servers:
        assert server in mcp_servers, (
            f"Required server '{server}' missing from mcpServers"
        )


def test_required_servers_have_command_and_args(
    generator: YAMLGenerator, valid_user_data_no_optional_mcp: UserDataInput
):
    """Test that required servers have command and args fields."""
    result = generator.generate_mcp_json(valid_user_data_no_optional_mcp)
    parsed = json.loads(result)

    mcp_servers = parsed["mcpServers"]

    # Check exa as example
    exa = mcp_servers["exa"]
    assert "command" in exa, "exa missing 'command' field"
    assert "args" in exa, "exa missing 'args' field"
    assert exa["command"] == "npx", "exa command should be 'npx'"
    assert isinstance(exa["args"], list), "exa args should be a list"


# ============================================================================
# Optional Servers Tests (Conditional Inclusion)
# ============================================================================


def test_alphavantage_included_when_has_key(
    generator: YAMLGenerator, valid_user_data_with_all_mcp: UserDataInput
):
    """Test that financial-datasets server is included when Alpha Vantage key provided."""
    result = generator.generate_mcp_json(valid_user_data_with_all_mcp)
    parsed = json.loads(result)

    mcp_servers = parsed["mcpServers"]

    # Should have financial-datasets
    assert "financial-datasets" in mcp_servers, (
        "financial-datasets should be present when has_alphavantage=True"
    )

    # Should have env with API key
    financial_datasets = mcp_servers["financial-datasets"]
    assert "env" in financial_datasets, "financial-datasets missing 'env' section"
    assert "ALPHA_VANTAGE_API_KEY" in financial_datasets["env"], (
        "financial-datasets env missing ALPHA_VANTAGE_API_KEY"
    )
    assert financial_datasets["env"]["ALPHA_VANTAGE_API_KEY"] == "test-alpha-key-123", (
        "Alpha Vantage API key mismatch"
    )


def test_alphavantage_excluded_when_no_key(
    generator: YAMLGenerator, valid_user_data_no_optional_mcp: UserDataInput
):
    """Test that financial-datasets server is NOT included when no API key."""
    result = generator.generate_mcp_json(valid_user_data_no_optional_mcp)
    parsed = json.loads(result)

    mcp_servers = parsed["mcpServers"]

    # Should NOT have financial-datasets
    assert "financial-datasets" not in mcp_servers, (
        "financial-datasets should be excluded when has_alphavantage=False"
    )


def test_brightdata_included_when_has_key(
    generator: YAMLGenerator, valid_user_data_with_all_mcp: UserDataInput
):
    """Test that bright-data server is included when BrightData key provided."""
    result = generator.generate_mcp_json(valid_user_data_with_all_mcp)
    parsed = json.loads(result)

    mcp_servers = parsed["mcpServers"]

    # Should have bright-data
    assert "bright-data" in mcp_servers, (
        "bright-data should be present when has_brightdata=True"
    )

    # Should have env with API key
    bright_data = mcp_servers["bright-data"]
    assert "env" in bright_data, "bright-data missing 'env' section"
    assert "BRIGHT_DATA_API_KEY" in bright_data["env"], (
        "bright-data env missing BRIGHT_DATA_API_KEY"
    )
    assert bright_data["env"]["BRIGHT_DATA_API_KEY"] == "test-bright-key-456", (
        "BrightData API key mismatch"
    )


def test_brightdata_excluded_when_no_key(
    generator: YAMLGenerator, valid_user_data_no_optional_mcp: UserDataInput
):
    """Test that bright-data server is NOT included when no API key."""
    result = generator.generate_mcp_json(valid_user_data_no_optional_mcp)
    parsed = json.loads(result)

    mcp_servers = parsed["mcpServers"]

    # Should NOT have bright-data
    assert "bright-data" not in mcp_servers, (
        "bright-data should be excluded when has_brightdata=False"
    )


def test_only_alphavantage_no_brightdata(
    generator: YAMLGenerator, valid_user_data_only_alphavantage: UserDataInput
):
    """Test generation with only Alpha Vantage (no BrightData)."""
    result = generator.generate_mcp_json(valid_user_data_only_alphavantage)
    parsed = json.loads(result)

    mcp_servers = parsed["mcpServers"]

    # Should have financial-datasets
    assert "financial-datasets" in mcp_servers, "financial-datasets should be present"

    # Should NOT have bright-data
    assert "bright-data" not in mcp_servers, "bright-data should be excluded"


# ============================================================================
# Variable Substitution Tests
# ============================================================================


def test_user_name_substitution_in_metadata(
    generator: YAMLGenerator, valid_user_data_with_all_mcp: UserDataInput
):
    """Test that {{user_name}} is replaced in metadata."""
    result = generator.generate_mcp_json(valid_user_data_with_all_mcp)
    parsed = json.loads(result)

    # User name should be in metadata
    assert parsed["_meta"]["user"] == "Alex", "User name not substituted correctly"

    # Should NOT contain template variable
    assert "{{user_name}}" not in result, (
        "Generated JSON contains unreplaced {{user_name}}"
    )


def test_timestamp_substitution(
    generator: YAMLGenerator, valid_user_data_with_all_mcp: UserDataInput
):
    """Test that {{timestamp}} is replaced with actual date."""
    result = generator.generate_mcp_json(valid_user_data_with_all_mcp)
    parsed = json.loads(result)

    # Should have a generated_at timestamp
    generated_at = parsed["_meta"]["generated_at"]
    assert len(generated_at) > 0, "generated_at is empty"
    assert "-" in generated_at, "generated_at should be ISO format (YYYY-MM-DD)"

    # Should NOT contain template variable
    assert "{{timestamp}}" not in result, (
        "Generated JSON contains unreplaced {{timestamp}}"
    )


def test_no_unreplaced_variables(
    generator: YAMLGenerator, valid_user_data_with_all_mcp: UserDataInput
):
    """Test that no template variables remain unreplaced."""
    result = generator.generate_mcp_json(valid_user_data_with_all_mcp)

    # Common template variable patterns
    template_vars = [
        "{{user_name}}",
        "{{timestamp}}",
        "{{alphavantage_key}}",
        "{{brightdata_key}}",
    ]

    for var in template_vars:
        assert var not in result, (
            f"Generated MCP JSON contains unreplaced variable: {var}"
        )


# ============================================================================
# Integration Tests
# ============================================================================


def test_full_mcp_generation_workflow(
    generator: YAMLGenerator, valid_user_data_with_all_mcp: UserDataInput
):
    """Test complete MCP JSON generation workflow end-to-end."""
    # Generate MCP JSON
    result = generator.generate_mcp_json(valid_user_data_with_all_mcp)

    # Validate JSON structure
    parsed = json.loads(result)
    assert "mcpServers" in parsed, "Missing mcpServers"
    assert "_meta" in parsed, "Missing _meta"

    # Validate required servers
    required = ["exa", "perplexity", "gdrive", "context7"]
    for server in required:
        assert server in parsed["mcpServers"], f"Missing required server: {server}"

    # Validate optional servers (should be present)
    assert "financial-datasets" in parsed["mcpServers"], "Missing financial-datasets"
    assert "bright-data" in parsed["mcpServers"], "Missing bright-data"

    # Validate metadata
    assert parsed["_meta"]["user"] == "Alex"
    assert parsed["_meta"]["generated_by"] == "Finance Guru™ Onboarding"

    # Validate no template variables
    assert "{{" not in result, "Contains unreplaced template variables"
    assert "}}" not in result, "Contains unreplaced template variables"


def test_different_users_generate_different_mcp_configs(
    generator: YAMLGenerator,
):
    """Test that different users get personalized MCP configs."""
    # User 1: Alex with all MCP servers
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
        debt=DebtProfileInput(has_mortgage=True),
        preferences=UserPreferencesInput(
            investment_philosophy=InvestmentPhilosophy.AGGRESSIVE_GROWTH_PLUS_INCOME,
            focus_areas=["dividend_portfolio"],
            emergency_fund_months=0,
        ),
        mcp=MCPConfigInput(
            has_alphavantage=True,
            alphavantage_key="alex-key",
            has_brightdata=True,
            brightdata_key="alex-bright",
        ),
    )

    # User 2: Sarah with NO optional MCP servers
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
        debt=DebtProfileInput(has_mortgage=False),
        preferences=UserPreferencesInput(
            investment_philosophy=InvestmentPhilosophy.GROWTH,
            focus_areas=["portfolio_optimization"],
            emergency_fund_months=6,
        ),
        mcp=MCPConfigInput(has_alphavantage=False, has_brightdata=False),
    )

    # Generate both
    result1 = generator.generate_mcp_json(user1)
    result2 = generator.generate_mcp_json(user2)

    # They should be different
    assert result1 != result2, "Different users generated identical MCP JSON"

    # Parse
    parsed1 = json.loads(result1)
    parsed2 = json.loads(result2)

    # User 1 should have optional servers
    assert "financial-datasets" in parsed1["mcpServers"]
    assert "bright-data" in parsed1["mcpServers"]
    assert parsed1["_meta"]["user"] == "Alex"

    # User 2 should NOT have optional servers
    assert "financial-datasets" not in parsed2["mcpServers"]
    assert "bright-data" not in parsed2["mcpServers"]
    assert parsed2["_meta"]["user"] == "Sarah"
