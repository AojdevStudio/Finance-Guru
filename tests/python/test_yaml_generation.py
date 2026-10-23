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

from src.cli import instance_init
from src.cli.onboarding_wizard import generate_config_files
from src.config.instance_instructions import LEGACY_SESSION_RULES
from src.config.instance_paths import InstancePaths
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
from src.utils.yaml_generator import YAMLGenerator, possessive, write_config_files


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
    template_dir = Path("scripts/onboarding/modules/templates")
    if not template_dir.exists():
        pytest.skip("Template directory not found - skipping integration tests")
    return YAMLGenerator(str(template_dir))


@pytest.mark.parametrize("plugin", [False, True])
def test_scaffold_and_wizard_share_product_instructions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    valid_user_data: UserDataInput,
    plugin: bool,
) -> None:
    repo = Path(__file__).resolve().parents[2]
    root = tmp_path / "instance"
    monkeypatch.setattr(instance_init, "_run_uv_sync", lambda _root: None)
    args = [str(root), "--repo", str(repo), *(["--plugin"] if plugin else [])]
    assert instance_init.main(args) == 0
    initial_prefix = (root / "CLAUDE.md").read_text().splitlines()[0]
    agents = root / "AGENTS.md"
    owner_notes = agents.read_text() + "\n## Household notes\nPreserve this note.\n"
    agents.write_text(owner_notes)

    generate_config_files(valid_user_data, InstancePaths(root=root))

    claude = root / "CLAUDE.md"
    content = claude.read_text()
    assert (
        content.splitlines()[0]
        == initial_prefix
        == (f"@{repo / '.claude/skills/fin-core/SKILL.md'}")
    )
    for rule in (
        "Quote calculator output",
        "Fail closed",
        "not investment advice",
        "licensed professionals",
        "risk disclosure",
        "data source",
    ):
        assert rule in content
    assert f"@{repo / 'CLAUDE.md'}" not in content
    assert "git push" not in content
    claude_notes = content + "\n## Household notes\nPreserve this note too.\n"
    claude.write_text(claude_notes)
    private = {
        name: (root / name).read_bytes()
        for name in (".env", "user-profile.yaml", "config.yaml")
    }

    assert instance_init.main(args) == 0
    assert claude.read_text() == claude_notes
    assert agents.read_text() == owner_notes
    assert all((root / name).read_bytes() == data for name, data in private.items())


@pytest.mark.parametrize("plugin", [False, True])
def test_scaffold_migrates_wizard_import_without_losing_owner_content(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    yaml_generator: YAMLGenerator,
    valid_user_data: UserDataInput,
    plugin: bool,
) -> None:
    repo = Path(__file__).resolve().parents[2]
    root = tmp_path / "instance"
    monkeypatch.setattr(instance_init, "_run_uv_sync", lambda _root: None)
    args = [str(root), "--repo", str(repo), *(["--plugin"] if plugin else [])]
    assert instance_init.main(args) == 0
    generated = yaml_generator.generate_claude_md(valid_user_data)
    body = generated[generated.index("# CLAUDE.md\n") :]
    notes = "\n## Household notes\nPreserve this note.\n"
    (root / "CLAUDE.md").write_text(f"@{repo / 'CLAUDE.md'}\n\n{body}{notes}")
    private = {
        name: (root / name).read_bytes() for name in (".env", "user-profile.yaml")
    }

    assert instance_init.main(args) == 0

    migrated = (root / "CLAUDE.md").read_text()
    assert migrated.startswith(f"@{repo / '.claude/skills/fin-core/SKILL.md'}\n")
    assert body + notes in migrated
    assert all((root / name).read_bytes() == data for name, data in private.items())


def test_scaffold_refuses_edited_legacy_workflow_before_writing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = Path(__file__).resolve().parents[2]
    root = tmp_path / "instance"
    root.mkdir()
    content = (
        f"@{repo / 'CLAUDE.md'}\n\n# CLAUDE.md\n"
        "\n## Landing the Plane (Session Completion)\nMy own workflow.\n"
    )
    (root / "CLAUDE.md").write_text(content)
    monkeypatch.setattr(instance_init, "_run_uv_sync", lambda _root: None)

    with pytest.raises(FileExistsError, match="edited legacy developer instructions"):
        instance_init.main([str(root), "--repo", str(repo)])

    assert list(root.iterdir()) == [root / "CLAUDE.md"]
    assert (root / "CLAUDE.md").read_text() == content


@pytest.mark.parametrize("plugin", [False, True])
@pytest.mark.parametrize("heading", ["\n## Owner session rules\n", ""])
def test_scaffold_refuses_legacy_body_with_changed_heading_before_any_write(
    tmp_path: Path,
    yaml_generator: YAMLGenerator,
    valid_user_data: UserDataInput,
    plugin: bool,
    heading: str,
) -> None:
    repo = Path(__file__).resolve().parents[2]
    root = tmp_path / "instance"
    (root / "imports/empty").mkdir(parents=True)
    (root / ".env").write_bytes(b"# synthetic private environment\n")
    (root / "user-profile.yaml").write_bytes(b"user_profile: {}\n")
    (root / "imports/owner.bin").write_bytes(b"owner bytes\x00\xff")
    generated = yaml_generator.generate_claude_md(valid_user_data)
    body = generated[generated.index("# CLAUDE.md\n") :]
    legacy = LEGACY_SESSION_RULES.replace(
        "\n## Landing the Plane (Session Completion)\n", heading, 1
    )
    content = (
        f"@{repo / 'CLAUDE.md'}\n\n{body}{legacy}"
        "\n## Household notes\nPreserve this exact note.\n"
    )
    (root / "CLAUDE.md").write_text(content)
    before_paths = sorted(path.relative_to(root) for path in root.rglob("*"))
    before_bytes = {
        path: (root / path).read_bytes()
        for path in before_paths
        if (root / path).is_file()
    }

    with pytest.raises(FileExistsError, match="edited legacy developer instructions"):
        instance_init.main(
            [str(root), "--repo", str(repo), *(["--plugin"] if plugin else [])]
        )

    assert sorted(path.relative_to(root) for path in root.rglob("*")) == before_paths
    assert all(
        (root / path).read_bytes() == data for path, data in before_bytes.items()
    )


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
                investment_capacity=6000.0,
            )

    def test_debt_rates_within_valid_range(self):
        """Debt interest rates must be between 0 and 1."""
        with pytest.raises(ValueError):
            DebtProfileInput(
                has_student_loans=True,
                student_loan_balance=50000.0,
                student_loan_rate=1.5,
            )

    def test_emergency_fund_within_valid_range(self):
        """Emergency fund months must be between 0 and 24."""
        with pytest.raises(ValueError):
            UserPreferencesInput(
                investment_philosophy=InvestmentPhilosophy.BALANCED,
                focus_areas=["diversification"],
                emergency_fund_months=30,
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

        assert "user_name: TestUser" in result or "TestUser" in result
        assert "10000" in result
        assert "100000" in result
        assert "aggressive" in result.lower()

    def test_generate_config(
        self, yaml_generator: YAMLGenerator, valid_user_data: UserDataInput
    ):
        """Config YAML should be generated with user customization."""
        result = yaml_generator.generate_config(valid_user_data)

        assert "TestUser" in result
        assert "English" in result

    def test_generate_system_context(
        self, yaml_generator: YAMLGenerator, valid_user_data: UserDataInput
    ):
        """System context markdown should be personalized."""
        result = yaml_generator.generate_system_context(valid_user_data)

        assert "TestUser" in result
        assert "markdown" in result.lower() or "#" in result

    def test_generate_claude_md(
        self, yaml_generator: YAMLGenerator, valid_user_data: UserDataInput
    ):
        """CLAUDE.md should be generated."""
        result = yaml_generator.generate_claude_md(valid_user_data)

        assert "TestUser" in result or "CLAUDE" in result
        product_rules = (
            Path(__file__).resolve().parents[2] / ".claude/skills/fin-core/SKILL.md"
        )
        assert result.startswith(f"@{product_rules}\n")

    def test_generate_env(
        self, yaml_generator: YAMLGenerator, valid_user_data: UserDataInput
    ):
        """Environment file should contain API keys."""
        result = yaml_generator.generate_env(valid_user_data)

        assert "test-key-123" in result

    def test_generate_mcp_json(
        self, yaml_generator: YAMLGenerator, valid_user_data: UserDataInput
    ):
        """MCP JSON config should be generated."""
        result = yaml_generator.generate_mcp_json(valid_user_data)

        assert len(result) > 0
        assert "{" in result or "mcpServers" in result


class TestFullGeneration:
    """Test complete config generation workflow."""

    def test_generate_all_configs(
        self, yaml_generator: YAMLGenerator, valid_user_data: UserDataInput
    ):
        """Generate all configs should produce complete output."""
        output = yaml_generator.generate_all_configs(valid_user_data)

        assert isinstance(output, YAMLGenerationOutput)
        assert output.user_name == "TestUser"
        assert output.generation_date == date.today()

        assert len(output.user_profile_yaml) > 0
        assert len(output.config_yaml) > 0
        assert len(output.system_context_md) > 0
        assert len(output.claude_md) > 0
        assert len(output.env_file) > 0
        assert len(output.mcp_json) > 0

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

        expected_files = [
            tmp_path / "user-profile.yaml",
            tmp_path / "config.yaml",
            tmp_path / "system-context.md",
            tmp_path / "CLAUDE.md",
            tmp_path / ".env",
            tmp_path / ".mcp.json",
        ]

        for file_path in expected_files:
            assert file_path.exists(), f"Expected file not created: {file_path}"
            assert file_path.stat().st_size > 0, f"File is empty: {file_path}"

    def test_scaffolded_claude_symlink_keeps_mcp_in_instance(
        self,
        yaml_generator: YAMLGenerator,
        valid_user_data: UserDataInput,
        tmp_path: Path,
    ):
        """A checkout-mode .claude symlink never carries private MCP output to the engine."""
        engine_claude = tmp_path / "engine" / ".claude"
        engine_claude.mkdir(parents=True)
        instance = tmp_path / "instance"
        instance.mkdir()
        (instance / ".claude").symlink_to(engine_claude, target_is_directory=True)

        write_config_files(
            yaml_generator.generate_all_configs(valid_user_data), str(instance)
        )

        assert list(engine_claude.iterdir()) == []
        assert (instance / ".mcp.json").is_file()

    def test_escaped_target_blocks_every_write(
        self,
        yaml_generator: YAMLGenerator,
        valid_user_data: UserDataInput,
        tmp_path: Path,
    ):
        """A target that resolves outside the instance stops the run before any file is written."""
        engine_file = tmp_path / "engine" / "CLAUDE.md"
        engine_file.parent.mkdir()
        engine_file.write_text("tracked engine instructions\n")
        instance = tmp_path / "instance"
        instance.mkdir()
        (instance / "CLAUDE.md").symlink_to(engine_file)

        with pytest.raises(ValueError, match="outside the instance"):
            write_config_files(
                yaml_generator.generate_all_configs(valid_user_data), str(instance)
            )

        assert engine_file.read_text() == "tracked engine instructions\n"
        assert sorted(path.name for path in instance.iterdir()) == ["CLAUDE.md"]


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

        user_name = valid_user_data.identity.user_name
        assert user_name in output.user_profile_yaml or user_name in output.config_yaml

    def test_portfolio_value_consistent(
        self, yaml_generator: YAMLGenerator, valid_user_data: UserDataInput
    ):
        """Portfolio value should be consistent across files."""
        output = yaml_generator.generate_all_configs(valid_user_data)

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


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        pytest.param("Alex", "Alex's", id="plain"),
        pytest.param("James", "James'", id="ends-in-s"),
        pytest.param("JAMES", "JAMES'", id="ends-in-capital-s"),
    ],
)
def test_possessive(name: str, expected: str) -> None:
    assert possessive(name) == expected


def test_cli_generates_one_config_without_missing_output_fields(
    valid_user_data, tmp_path
):
    import subprocess
    import sys

    input_path = tmp_path / "synthetic-input.json"
    input_path.write_text(valid_user_data.model_dump_json())
    output_path = tmp_path / "generated"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "src.utils.yaml_generator_cli",
            "--input",
            str(input_path),
            "--output",
            str(output_path),
            "--type",
            "config",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert (output_path / "config.yaml").is_file()
    assert not (output_path / "user-profile.yaml").exists()
