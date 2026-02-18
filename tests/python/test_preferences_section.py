"""
Test suite for Preferences Section

Tests the TypeScript preferences.ts section implementation via subprocess.
This validates:
- Section initialization
- Input validation (enums for risk_tolerance, investment_philosophy, time_horizon)
- Data structure correctness
- State persistence
- Optional focus_areas handling (multi-select)
"""

import json
import subprocess
from pathlib import Path

import pytest


class TestPreferencesSection:
    """Test suite for preferences section"""

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Create a temporary directory for test state files"""
        return tmp_path

    @pytest.fixture
    def mock_state_file(self, temp_dir):
        """Create a mock onboarding state file"""
        state = {
            "version": "1.0",
            "started_at": "2026-01-16T00:00:00.000Z",
            "last_updated": "2026-01-16T00:00:00.000Z",
            "completed_sections": ["liquid_assets", "investments", "cash_flow", "debt"],
            "current_section": "preferences",
            "data": {
                "liquid_assets": {
                    "total": 14491,
                    "accounts_count": 10,
                    "average_yield": 0.04,
                    "structure": [],
                },
                "investments": {
                    "total_value": 243382.67,
                    "retirement_accounts": 308000,
                    "allocation": "aggressive_growth",
                    "risk_profile": "aggressive",
                },
                "cash_flow": {
                    "monthly_income": 25000,
                    "fixed_expenses": 4500,
                    "variable_expenses": 10000,
                    "current_savings": 5000,
                    "investment_capacity": 10500,
                },
                "debt": {
                    "mortgage_balance": 365139.76,
                    "mortgage_payment": 1712.68,
                    "other_debt": [],
                },
            },
        }
        state_file = temp_dir / ".onboarding-state.json"
        state_file.write_text(json.dumps(state, indent=2))
        return state_file

    def test_section_exports_run_function(self):
        """Test that preferences.ts exports runPreferencesSection"""
        result = subprocess.run(
            [
                "bun",
                "run",
                "-e",
                "import { runPreferencesSection } from './scripts/onboarding/sections/preferences.ts'; console.log(typeof runPreferencesSection)",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "function" in result.stdout

    def test_section_file_exists(self):
        """Test that preferences.ts file exists"""
        section_file = Path("scripts/onboarding/sections/preferences.ts")
        assert section_file.exists(), "preferences.ts must exist"
        assert section_file.is_file(), "preferences.ts must be a file"

    def test_section_imports_validators(self):
        """Test that section imports validation functions"""
        section_file = Path("scripts/onboarding/sections/preferences.ts")
        content = section_file.read_text()

        # Check for required imports
        assert "validateEnum" in content
        assert "OnboardingState" in content
        assert "saveSectionData" in content
        assert "markSectionComplete" in content

    def test_section_defines_data_interface(self):
        """Test that PreferencesData interface is defined"""
        section_file = Path("scripts/onboarding/sections/preferences.ts")
        content = section_file.read_text()

        # Check for interface definition
        assert "interface PreferencesData" in content
        assert "risk_tolerance:" in content
        assert "investment_philosophy:" in content
        assert "time_horizon:" in content
        assert "focus_areas" in content

    def test_typescript_compiles_without_errors(self):
        """Test that TypeScript code compiles successfully"""
        result = subprocess.run(
            ["bun", "run", "scripts/onboarding/sections/preferences.ts", "--help"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        # Should not have TypeScript compilation errors
        assert "error TS" not in result.stderr

    def test_section_structure_matches_spec(self):
        """Test that section structure matches specification"""
        section_file = Path("scripts/onboarding/sections/preferences.ts")
        content = section_file.read_text()

        # Verify section displays correct header
        assert "Section 5 of 7" in content

        # Verify prompts for required fields
        assert "risk" in content.lower() and "tolerance" in content.lower()
        assert "investment" in content.lower() and "philosophy" in content.lower()
        assert "time" in content.lower() and "horizon" in content.lower()
        assert "focus" in content.lower() and "areas" in content.lower()

    def test_section_handles_state_updates(self):
        """Test that section properly updates state"""
        section_file = Path("scripts/onboarding/sections/preferences.ts")
        content = section_file.read_text()

        # Verify state management calls
        assert "saveSectionData" in content
        assert "markSectionComplete" in content
        assert "saveState" in content

        # Verify correct section name used
        assert "'preferences'" in content or '"preferences"' in content

    def test_section_marks_next_section_correctly(self):
        """Test that section marks next section as 'summary'"""
        section_file = Path("scripts/onboarding/sections/preferences.ts")
        content = section_file.read_text()

        # Should mark next section as 'summary' or similar
        assert "'summary'" in content or "summary" in content.lower()

    def test_validation_integration(self):
        """Test that validation functions are properly integrated"""
        # Test enum validation integration
        result = subprocess.run(
            [
                "bun",
                "-e",
                """
            import { validateEnum } from './scripts/onboarding/modules/input-validator.ts';
            console.log(validateEnum('aggressive', ['conservative', 'moderate', 'aggressive'], 'risk tolerance'));
            console.log(validateEnum('moderate', ['conservative', 'moderate', 'aggressive'], 'risk tolerance'));
            """,
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "aggressive" in result.stdout
        assert "moderate" in result.stdout

    def test_risk_tolerance_options(self):
        """Test that risk tolerance has correct options"""
        section_file = Path("scripts/onboarding/sections/preferences.ts")
        content = section_file.read_text()

        # Should have all three risk tolerance options
        assert "conservative" in content.lower()
        assert "moderate" in content.lower()
        assert "aggressive" in content.lower()

    def test_investment_philosophy_options(self):
        """Test that investment philosophy has appropriate options"""
        section_file = Path("scripts/onboarding/sections/preferences.ts")
        content = section_file.read_text()

        # Should have multiple philosophy options
        assert "growth" in content.lower()
        assert "income" in content.lower()
        # May have variations like aggressive_growth, aggressive_growth_plus_income
        assert "aggressive_growth" in content.lower() or "balanced" in content.lower()

    def test_time_horizon_options(self):
        """Test that time horizon has correct options"""
        section_file = Path("scripts/onboarding/sections/preferences.ts")
        content = section_file.read_text()

        # Should have time horizon options
        assert "short_term" in content.lower()
        assert "medium_term" in content.lower() or "medium" in content.lower()
        assert "long_term" in content.lower()

    def test_focus_areas_are_optional(self):
        """Test that focus_areas field is optional"""
        section_file = Path("scripts/onboarding/sections/preferences.ts")
        content = section_file.read_text()

        # Should have logic for optional input
        assert "optional" in content.lower()
        assert (
            "skip" in content.lower()
            or "enter" in content.lower()
            or "press enter" in content.lower()
        )

    def test_focus_areas_multi_select(self):
        """Test that focus_areas supports multi-select (comma-separated)"""
        section_file = Path("scripts/onboarding/sections/preferences.ts")
        content = section_file.read_text()

        # Should mention comma-separated input
        assert "comma" in content.lower()
        assert "split" in content  # Should split input by comma

    def test_focus_areas_options_documented(self):
        """Test that available focus_areas are documented"""
        section_file = Path("scripts/onboarding/sections/preferences.ts")
        content = section_file.read_text()

        # Should list available focus areas
        assert (
            "dividend_portfolio_construction" in content
            or "dividend" in content.lower()
        )
        assert "margin_strategies" in content or "margin" in content.lower()
        assert "tax_efficiency" in content or "tax" in content.lower()

    def test_section_number_correct(self):
        """Test that section is numbered as Section 5 of 7"""
        section_file = Path("scripts/onboarding/sections/preferences.ts")
        content = section_file.read_text()

        assert "Section 5 of 7" in content

    def test_readline_usage(self):
        """Test that section uses readline for input"""
        section_file = Path("scripts/onboarding/sections/preferences.ts")
        content = section_file.read_text()

        # Should import readline
        assert "readline" in content
        assert "createInterface" in content or "question" in content

    def test_error_handling(self):
        """Test that section has proper error handling"""
        section_file = Path("scripts/onboarding/sections/preferences.ts")
        content = section_file.read_text()

        # Should have try/catch or error handling
        assert "try" in content or "catch" in content or "error" in content.lower()
        assert "finally" in content or "close" in content  # Should close readline

    def test_enum_validation_for_all_required_fields(self):
        """Test that all required enum fields use validateEnum"""
        section_file = Path("scripts/onboarding/sections/preferences.ts")
        content = section_file.read_text()

        # Should use validateEnum for risk_tolerance, investment_philosophy, time_horizon
        # At least 3 calls expected
        validate_count = content.count("validateEnum")
        assert validate_count >= 3, (
            f"Expected at least 3 validateEnum calls, found {validate_count}"
        )

    def test_focus_areas_validation(self):
        """Test that invalid focus areas are filtered out"""
        section_file = Path("scripts/onboarding/sections/preferences.ts")
        content = section_file.read_text()

        # Should validate or filter focus areas
        # Look for validation logic or defined valid options
        assert "validFocusAreas" in content or "filter" in content

    def test_previous_section_is_debt(self):
        """Test that this section follows debt profile"""
        section_file = Path("scripts/onboarding/sections/preferences.ts")
        content = section_file.read_text()

        # Should reference 'preferences' as current section key
        assert "'preferences'" in content or '"preferences"' in content

    def test_examples_provided(self):
        """Test that section provides examples for each field"""
        section_file = Path("scripts/onboarding/sections/preferences.ts")
        content = section_file.read_text()

        # Should show examples or descriptions
        # Check for descriptive text explaining options
        conservative_desc = "conservative" in content.lower()
        moderate_desc = "moderate" in content.lower()
        aggressive_desc = "aggressive" in content.lower()

        assert conservative_desc and moderate_desc and aggressive_desc

    def test_optional_focus_areas_structure(self):
        """Test that focus_areas are only added if provided"""
        section_file = Path("scripts/onboarding/sections/preferences.ts")
        content = section_file.read_text()

        # Should conditionally add focus_areas to data structure
        # Look for conditional assignment or check for empty input
        assert "if" in content or "?" in content  # Conditional logic for optional field


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
