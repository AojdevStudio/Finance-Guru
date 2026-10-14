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
4. Required Servers Tests - Verify exa, perplexity, and context7 are always present
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


def test_generated_mcp_json_is_valid_json(
    generator: YAMLGenerator, valid_user_data_with_all_mcp: UserDataInput
):
    """Test that generated MCP JSON is valid, parseable JSON."""
    result = generator.generate_mcp_json(valid_user_data_with_all_mcp)

    try:
        parsed = json.loads(result)
    except json.JSONDecodeError as e:
        pytest.fail(f"Generated MCP JSON is not valid JSON: {e}")

    assert "mcpServers" in parsed, "Generated JSON missing 'mcpServers' key"
    assert isinstance(parsed["mcpServers"], dict), "'mcpServers' should be a dictionary"


def test_generated_mcp_json_has_metadata(
    generator: YAMLGenerator, valid_user_data_with_all_mcp: UserDataInput
):
    """Test that generated MCP JSON includes metadata section."""
    result = generator.generate_mcp_json(valid_user_data_with_all_mcp)
    parsed = json.loads(result)

    assert "_meta" in parsed, "Generated JSON missing '_meta' section"
    meta = parsed["_meta"]

    assert "generated_by" in meta, "Metadata missing 'generated_by'"
    assert "generated_at" in meta, "Metadata missing 'generated_at'"
    assert "user" in meta, "Metadata missing 'user'"
    assert "version" in meta, "Metadata missing 'version'"

    assert meta["user"] == "Alex", f"Expected user 'Alex', got '{meta['user']}'"


def test_required_mcp_servers_always_present(
    generator: YAMLGenerator, valid_user_data_no_optional_mcp: UserDataInput
):
    """Test that required MCP servers are always included."""
    result = generator.generate_mcp_json(valid_user_data_no_optional_mcp)
    parsed = json.loads(result)

    mcp_servers = parsed["mcpServers"]

    required_servers = ["exa", "perplexity", "context7"]

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

    exa = mcp_servers["exa"]
    assert "command" in exa, "exa missing 'command' field"
    assert "args" in exa, "exa missing 'args' field"
    assert exa["command"] == "npx", "exa command should be 'npx'"
    assert isinstance(exa["args"], list), "exa args should be a list"


def test_retired_gdrive_server_is_absent(
    generator: YAMLGenerator,
    valid_user_data_with_all_mcp: UserDataInput,
    valid_user_data_no_optional_mcp: UserDataInput,
):
    """Onboarding must not configure or document the retired gdrive MCP server.

    The Google Sheets DataHub is retired. Generated mcp.json stays valid JSON
    with the remaining required servers, and generated CLAUDE.md does not list
    gdrive as a required server.
    """
    template_path = (
        Path(__file__).parent.parent.parent
        / "scripts/onboarding/modules/templates/mcp.template.json"
    )
    template = template_path.read_text()
    assert "gdrive" not in template
    assert "@google/gdrive-mcp" not in template

    claude_template = (
        Path(__file__).parent.parent.parent
        / "scripts/onboarding/modules/templates/CLAUDE.template.md"
    ).read_text()
    assert "gdrive" not in claude_template

    for user_data in (valid_user_data_with_all_mcp, valid_user_data_no_optional_mcp):
        result = generator.generate_mcp_json(user_data)
        parsed = json.loads(result)
        servers = parsed["mcpServers"]

        assert "gdrive" not in servers
        assert "@google/gdrive-mcp" not in result
        for server in ("exa", "perplexity", "context7"):
            assert server in servers
            assert servers[server]["command"] == "npx"
            assert isinstance(servers[server]["args"], list)

        claude_md = generator.generate_claude_md(user_data)
        assert "gdrive" not in claude_md
        assert "MCP Servers Required" in claude_md


def test_alphavantage_included_when_has_key(
    generator: YAMLGenerator, valid_user_data_with_all_mcp: UserDataInput
):
    """Test that financial-datasets server is included when Alpha Vantage key provided."""
    result = generator.generate_mcp_json(valid_user_data_with_all_mcp)
    parsed = json.loads(result)

    mcp_servers = parsed["mcpServers"]

    assert "financial-datasets" in mcp_servers, (
        "financial-datasets should be present when has_alphavantage=True"
    )

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

    assert "bright-data" in mcp_servers, (
        "bright-data should be present when has_brightdata=True"
    )

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

    assert "financial-datasets" in mcp_servers, "financial-datasets should be present"

    assert "bright-data" not in mcp_servers, "bright-data should be excluded"


def test_user_name_substitution_in_metadata(
    generator: YAMLGenerator, valid_user_data_with_all_mcp: UserDataInput
):
    """Test that {{user_name}} is replaced in metadata."""
    result = generator.generate_mcp_json(valid_user_data_with_all_mcp)
    parsed = json.loads(result)

    assert parsed["_meta"]["user"] == "Alex", "User name not substituted correctly"

    assert "{{user_name}}" not in result, (
        "Generated JSON contains unreplaced {{user_name}}"
    )


def test_timestamp_substitution(
    generator: YAMLGenerator, valid_user_data_with_all_mcp: UserDataInput
):
    """Test that {{timestamp}} is replaced with actual date."""
    result = generator.generate_mcp_json(valid_user_data_with_all_mcp)
    parsed = json.loads(result)

    generated_at = parsed["_meta"]["generated_at"]
    assert len(generated_at) > 0, "generated_at is empty"
    assert "-" in generated_at, "generated_at should be ISO format (YYYY-MM-DD)"

    assert "{{timestamp}}" not in result, (
        "Generated JSON contains unreplaced {{timestamp}}"
    )


def test_no_unreplaced_variables(
    generator: YAMLGenerator, valid_user_data_with_all_mcp: UserDataInput
):
    """Test that no template variables remain unreplaced."""
    result = generator.generate_mcp_json(valid_user_data_with_all_mcp)

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


def test_full_mcp_generation_workflow(
    generator: YAMLGenerator, valid_user_data_with_all_mcp: UserDataInput
):
    """Test complete MCP JSON generation workflow end-to-end."""
    result = generator.generate_mcp_json(valid_user_data_with_all_mcp)

    parsed = json.loads(result)
    assert "mcpServers" in parsed, "Missing mcpServers"
    assert "_meta" in parsed, "Missing _meta"

    required = ["exa", "perplexity", "context7"]
    for server in required:
        assert server in parsed["mcpServers"], f"Missing required server: {server}"

    assert "financial-datasets" in parsed["mcpServers"], "Missing financial-datasets"
    assert "bright-data" in parsed["mcpServers"], "Missing bright-data"

    assert parsed["_meta"]["user"] == "Alex"
    assert parsed["_meta"]["generated_by"] == "Finance Guru™ Onboarding"

    assert "{{" not in result, "Contains unreplaced template variables"
    assert "}}" not in result, "Contains unreplaced template variables"


def test_different_users_generate_different_mcp_configs(
    generator: YAMLGenerator,
):
    """Test that different users get personalized MCP configs."""
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

    result1 = generator.generate_mcp_json(user1)
    result2 = generator.generate_mcp_json(user2)

    assert result1 != result2, "Different users generated identical MCP JSON"

    parsed1 = json.loads(result1)
    parsed2 = json.loads(result2)

    assert "financial-datasets" in parsed1["mcpServers"]
    assert "bright-data" in parsed1["mcpServers"]
    assert parsed1["_meta"]["user"] == "Alex"

    assert "financial-datasets" not in parsed2["mcpServers"]
    assert "bright-data" not in parsed2["mcpServers"]
    assert parsed2["_meta"]["user"] == "Sarah"
