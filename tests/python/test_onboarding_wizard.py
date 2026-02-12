"""
Integration tests for the onboarding wizard CLI.

Tests the complete pipeline:
- State-to-model conversion (string-to-enum mapping)
- Config file generation to correct paths
- Backup of existing files
- SECTION_ORDER structure
- Save/resume progress persistence (Phase 4)

Author: Finance Guru Development Team
Created: 2026-02-05
"""

import json

import pytest
from pathlib import Path

from src.cli.onboarding_wizard import (
    PROGRESS_FILE,
    SECTION_ORDER,
    convert_state_to_user_data,
    delete_progress,
    generate_config_files,
    load_progress,
    save_progress,
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


# ---------------------------------------------------------------------------
# Save/Resume progress persistence (Phase 4)
# ---------------------------------------------------------------------------


@pytest.fixture
def progress_file(tmp_path, monkeypatch):
    """Override PROGRESS_FILE to use a temp directory."""
    progress_path = tmp_path / ".onboarding-progress.json"
    monkeypatch.setattr(
        "src.cli.onboarding_wizard.PROGRESS_FILE", progress_path
    )
    return progress_path


@pytest.fixture
def partial_state() -> OnboardingState:
    """Create an OnboardingState with 2 sections completed."""
    state = OnboardingState.create_new()
    state.data[SectionName.LIQUID_ASSETS.value] = {
        "total": 25000.0,
        "accounts_count": 3,
        "average_yield": 0.045,
        "structure": "2 checking, 1 HYSA",
    }
    state.data[SectionName.INVESTMENTS.value] = {
        "total_value": 150000.0,
        "brokerage": "Fidelity",
        "has_retirement": True,
        "retirement_value": 60000.0,
        "allocation_strategy": "aggressive_growth",
        "risk_tolerance": "aggressive",
        "google_sheets_id": "abc123",
        "account_number": "4567",
    }
    state.completed_sections = [
        SectionName.LIQUID_ASSETS,
        SectionName.INVESTMENTS,
    ]
    state.current_section = SectionName.CASH_FLOW
    return state


class TestSaveProgress:
    """Test save_progress writes valid JSON."""

    def test_creates_valid_json(self, progress_file, partial_state):
        """save_progress creates a readable JSON file."""
        save_progress(partial_state)
        assert progress_file.exists()
        data = json.loads(progress_file.read_text())
        assert data["current_section"] == "cash_flow"
        assert len(data["completed_sections"]) == 2

    def test_round_trips_to_equivalent_state(self, progress_file, partial_state):
        """Saved state can be loaded back into an equivalent OnboardingState."""
        save_progress(partial_state)
        data = json.loads(progress_file.read_text())
        restored = OnboardingState.model_validate(data)
        assert restored.current_section == partial_state.current_section
        assert restored.completed_sections == partial_state.completed_sections
        assert restored.data == partial_state.data

    def test_atomic_write_no_partial_on_error(self, tmp_path, monkeypatch):
        """If JSON serialization fails, no progress file is left behind."""
        progress_path = tmp_path / ".onboarding-progress.json"
        monkeypatch.setattr(
            "src.cli.onboarding_wizard.PROGRESS_FILE", progress_path
        )
        state = OnboardingState.create_new()
        # Inject an unserializable object to force an error
        state.data["bad"] = {"value": object()}
        with pytest.raises(Exception):
            save_progress(state)
        assert not progress_path.exists()


class TestLoadProgress:
    """Test load_progress with various file states."""

    def test_returns_saved_state(self, progress_file, partial_state):
        """load_progress returns a state matching what was saved."""
        save_progress(partial_state)
        loaded = load_progress()
        assert loaded is not None
        assert loaded.current_section == SectionName.CASH_FLOW
        assert len(loaded.completed_sections) == 2
        assert loaded.data[SectionName.LIQUID_ASSETS.value]["total"] == 25000.0

    def test_returns_none_for_missing_file(self, progress_file):
        """load_progress returns None when no progress file exists."""
        assert not progress_file.exists()
        result = load_progress()
        assert result is None

    def test_returns_none_for_corrupt_json(self, progress_file):
        """load_progress returns None for invalid JSON (no crash)."""
        progress_file.write_text("not valid json {{{")
        result = load_progress()
        assert result is None

    def test_returns_none_for_invalid_schema(self, progress_file):
        """load_progress returns None when JSON has wrong schema that fails validation."""
        # current_section must be a valid SectionName enum value;
        # an invalid value triggers a Pydantic ValidationError.
        progress_file.write_text(
            json.dumps({"current_section": "nonexistent_section_xyz"})
        )
        result = load_progress()
        assert result is None


class TestDeleteProgress:
    """Test delete_progress file cleanup."""

    def test_removes_existing_file(self, progress_file, partial_state):
        """delete_progress removes the progress file."""
        save_progress(partial_state)
        assert progress_file.exists()
        delete_progress()
        assert not progress_file.exists()

    def test_noop_if_no_file(self, progress_file):
        """delete_progress does not raise when no file exists."""
        assert not progress_file.exists()
        delete_progress()  # Should not raise


class TestWizardSaveResume:
    """Integration tests for wizard save/resume behavior."""

    def test_wizard_saves_progress_after_section(
        self, progress_file, monkeypatch
    ):
        """Progress file is created after completing sections."""
        from unittest.mock import MagicMock, patch

        from src.cli.onboarding_wizard import run_wizard

        # Track section calls
        call_count = 0
        sections_completed = 0

        def mock_section_runner(state):
            nonlocal call_count, sections_completed
            call_count += 1
            section_name = SECTION_ORDER[sections_completed][0]

            # Simulate filling in data
            state.data[section_name.value] = {"mock": True}
            next_idx = sections_completed + 1
            next_section = (
                SECTION_ORDER[next_idx][0]
                if next_idx < len(SECTION_ORDER)
                else None
            )
            state.mark_complete(section_name, next_section)
            sections_completed += 1

            # After 2 sections, simulate Ctrl+C by raising KeyboardInterrupt
            if sections_completed == 2:
                raise KeyboardInterrupt()
            return state

        # Patch all section runners
        with patch(
            "src.cli.onboarding_wizard.SECTION_ORDER",
            [(name, mock_section_runner) for name, _ in SECTION_ORDER],
        ):
            # Patch load_progress to return None (fresh start)
            with patch("src.cli.onboarding_wizard.load_progress", return_value=None):
                run_wizard()

        # Verify progress file was created with 2 completed sections
        assert progress_file.exists()
        data = json.loads(progress_file.read_text())
        assert len(data["completed_sections"]) == 2

    def test_wizard_resumes_from_saved_progress(
        self, progress_file, partial_state, monkeypatch
    ):
        """Wizard resumes from saved progress when user confirms."""
        from unittest.mock import MagicMock, patch

        from src.cli.onboarding_wizard import run_wizard

        # Save the partial state
        save_progress(partial_state)

        # Track which sections get executed
        executed_sections = []

        def mock_section_runner(state):
            # Find which section this is by looking at current_section
            section_name = state.current_section
            executed_sections.append(section_name)
            state.data[section_name.value] = {"mock": True}
            # Mark complete and advance
            section_names = [name for name, _ in SECTION_ORDER]
            idx = section_names.index(section_name)
            next_section = (
                SECTION_ORDER[idx + 1][0]
                if idx + 1 < len(SECTION_ORDER)
                else None
            )
            state.mark_complete(section_name, next_section)

            # On summary section, mark confirmed
            if section_name == SectionName.SUMMARY:
                state.data[SectionName.SUMMARY.value] = {"confirmed": False}
            return state

        # Patch questionary.confirm to return True (resume)
        mock_confirm = MagicMock()
        mock_confirm.ask.return_value = True

        with patch("src.cli.onboarding_wizard.questionary") as mock_q:
            mock_q.confirm.return_value = mock_confirm
            with patch(
                "src.cli.onboarding_wizard.SECTION_ORDER",
                [(name, mock_section_runner) for name, _ in SECTION_ORDER],
            ):
                run_wizard()

        # Should have skipped the first 2 sections (LIQUID_ASSETS, INVESTMENTS)
        assert SectionName.LIQUID_ASSETS not in executed_sections
        assert SectionName.INVESTMENTS not in executed_sections
        # Should have executed remaining 6 sections starting from CASH_FLOW
        assert SectionName.CASH_FLOW in executed_sections

    def test_wizard_deletes_progress_on_completion(
        self, progress_file, completed_state, monkeypatch
    ):
        """Progress file is deleted after successful wizard completion."""
        from unittest.mock import MagicMock, patch

        from src.cli.onboarding_wizard import run_wizard

        # Save progress first
        save_progress(completed_state)
        assert progress_file.exists()

        # Mock all sections to just pass through (already complete)
        def passthrough(state):
            return state

        # Patch load_progress to return None so it starts fresh,
        # and mock all sections to fill data and confirm
        section_index = 0

        def mock_runner(state):
            nonlocal section_index
            sname = SECTION_ORDER[section_index][0]
            if sname == SectionName.SUMMARY:
                state.data[sname.value] = {"confirmed": True}
            else:
                state.data[sname.value] = {"mock": True}
            next_idx = section_index + 1
            next_section = (
                SECTION_ORDER[next_idx][0]
                if next_idx < len(SECTION_ORDER)
                else None
            )
            state.mark_complete(sname, next_section)
            section_index += 1
            return state

        with patch("src.cli.onboarding_wizard.load_progress", return_value=None):
            with patch(
                "src.cli.onboarding_wizard.SECTION_ORDER",
                [(name, mock_runner) for name, _ in SECTION_ORDER],
            ):
                with patch(
                    "src.cli.onboarding_wizard.convert_state_to_user_data"
                ) as mock_convert:
                    with patch(
                        "src.cli.onboarding_wizard.generate_config_files"
                    ):
                        mock_convert.return_value = MagicMock()
                        run_wizard()

        # Progress file should be deleted after completion
        assert not progress_file.exists()
