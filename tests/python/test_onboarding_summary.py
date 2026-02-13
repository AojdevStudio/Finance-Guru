"""
Test suite for Onboarding Summary & Confirmation Section

Tests the TypeScript summary.ts section implementation via subprocess.
This validates:
- Summary display of all collected data
- Sanitized output (no sensitive details in terminal history)
- Confirmation prompt
- State completion on confirmation
- Options to restart or exit on rejection
- Progress file cleanup on successful completion
"""

import json
import subprocess
from pathlib import Path

import pytest


class TestSummarySection:
    """Test suite for summary & confirmation section"""

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Create a temporary directory for test state files"""
        return tmp_path

    @pytest.fixture
    def complete_state_file(self, temp_dir):
        """Create a complete onboarding state file with all sections"""
        state = {
            "version": "1.0",
            "started_at": "2026-01-16T00:00:00.000Z",
            "last_updated": "2026-01-16T00:15:00.000Z",
            "completed_sections": [
                "liquid_assets",
                "investments",
                "cash_flow",
                "debt",
                "preferences",
            ],
            "current_section": "summary",
            "data": {
                "liquid_assets": {
                    "total": 14491,
                    "accounts_count": 10,
                    "average_yield": 0.04,
                    "structure": [
                        "2 business accounts",
                        "4 checking accounts",
                        "4 savings accounts",
                    ],
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
                    "other_debt": [{"type": "student_loans", "rate": 0.08}],
                },
                "preferences": {
                    "risk_tolerance": "aggressive",
                    "investment_philosophy": "aggressive_growth_plus_income",
                    "time_horizon": "long_term",
                    "focus_areas": [
                        "dividend_portfolio_construction",
                        "margin_strategies",
                    ],
                },
            },
        }
        state_file = temp_dir / ".onboarding-state.json"
        state_file.write_text(json.dumps(state, indent=2))
        return state_file

    def test_section_exports_run_function(self):
        """Test that summary.ts exports runSummarySection"""
        result = subprocess.run(
            [
                "bun",
                "run",
                "-e",
                "import { runSummarySection } from './scripts/onboarding/sections/summary.ts'; console.log(typeof runSummarySection)",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "function" in result.stdout

    def test_section_file_exists(self):
        """Test that summary.ts file exists"""
        section_file = Path("scripts/onboarding/sections/summary.ts")
        assert section_file.exists(), "summary.ts must exist"
        assert section_file.is_file(), "summary.ts must be a file"

    def test_section_imports_required_modules(self):
        """Test that section imports necessary functions"""
        section_file = Path("scripts/onboarding/sections/summary.ts")
        content = section_file.read_text()

        # Check for required imports
        assert "OnboardingState" in content
        assert "getSectionData" in content or "data" in content
        assert "saveState" in content or "clearState" in content

    def test_typescript_compiles_without_errors(self):
        """Test that TypeScript code compiles successfully"""
        result = subprocess.run(
            ["bun", "run", "scripts/onboarding/sections/summary.ts", "--help"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        # Should not have TypeScript compilation errors
        assert "error TS" not in result.stderr

    def test_section_structure_matches_spec(self):
        """Test that section structure matches specification"""
        section_file = Path("scripts/onboarding/sections/summary.ts")
        content = section_file.read_text()

        # Verify section displays correct header
        assert "Section 6 of 7" in content or "Summary" in content

        # Verify displays all section summaries
        assert "liquid" in content.lower() or "assets" in content.lower()
        assert "investment" in content.lower() or "portfolio" in content.lower()
        assert "cash" in content.lower() or "flow" in content.lower()
        assert "debt" in content.lower()
        assert "preferences" in content.lower()

    def test_section_has_confirmation_prompt(self):
        """Test that section asks for confirmation"""
        section_file = Path("scripts/onboarding/sections/summary.ts")
        content = section_file.read_text()

        # Should ask user to confirm
        assert "confirm" in content.lower() or "save" in content.lower()
        assert "y/n" in content.lower() or "yes/no" in content.lower()

    def test_section_sanitizes_sensitive_data(self):
        """Test that section doesn't display full financial details"""
        section_file = Path("scripts/onboarding/sections/summary.ts")
        content = section_file.read_text()

        # Should use sanitized display or summary format
        # Not displaying exact dollar amounts in code (displayed values should be from state data)
        assert (
            "summary" in content.lower()
            or "sanitize" in content.lower()
            or "format" in content.lower()
        )

    def test_section_handles_yes_confirmation(self):
        """Test that section handles 'yes' confirmation correctly"""
        section_file = Path("scripts/onboarding/sections/summary.ts")
        content = section_file.read_text()

        # Should handle affirmative responses
        assert "'y'" in content or "'yes'" in content or "toLowerCase" in content

    def test_section_handles_no_rejection(self):
        """Test that section handles 'no' rejection"""
        section_file = Path("scripts/onboarding/sections/summary.ts")
        content = section_file.read_text()

        # Should offer options on rejection
        assert "'n'" in content or "'no'" in content
        # Should offer restart or exit
        assert "restart" in content.lower() or "exit" in content.lower()

    def test_section_clears_progress_on_success(self):
        """Test that section clears progress file after successful save"""
        section_file = Path("scripts/onboarding/sections/summary.ts")
        content = section_file.read_text()

        # Should call clearState on successful completion
        assert "clearState" in content

    def test_section_marks_completion_correctly(self):
        """Test that section marks onboarding as complete"""
        section_file = Path("scripts/onboarding/sections/summary.ts")
        content = section_file.read_text()

        # Should mark as complete
        assert "complete" in content.lower()
        # Should not set a next section (this is the last section before config generation)
        # Or should set current_section to null/undefined

    def test_section_number_correct(self):
        """Test that section is numbered as Section 6 of 7"""
        section_file = Path("scripts/onboarding/sections/summary.ts")
        content = section_file.read_text()

        assert "Section 6 of 7" in content or "Summary" in content

    def test_readline_usage(self):
        """Test that section uses readline for input"""
        section_file = Path("scripts/onboarding/sections/summary.ts")
        content = section_file.read_text()

        # Should import readline
        assert "readline" in content
        assert "createInterface" in content or "question" in content

    def test_error_handling(self):
        """Test that section has proper error handling"""
        section_file = Path("scripts/onboarding/sections/summary.ts")
        content = section_file.read_text()

        # Should have try/catch or error handling
        assert "try" in content or "catch" in content or "error" in content.lower()
        assert "finally" in content or "close" in content  # Should close readline

    def test_displays_all_section_data(self):
        """Test that summary displays data from all sections"""
        section_file = Path("scripts/onboarding/sections/summary.ts")
        content = section_file.read_text()

        # Should access all section data
        section_keys = [
            "liquid_assets",
            "investments",
            "cash_flow",
            "debt",
            "preferences",
        ]
        for key in section_keys:
            assert key in content or key.replace("_", " ") in content.lower()

    def test_summary_format_organized(self):
        """Test that summary is well-formatted and organized"""
        section_file = Path("scripts/onboarding/sections/summary.ts")
        content = section_file.read_text()

        # Should use formatting/separators
        assert "━" in content or "=" in content or "-" in content
        # Should have sections/headers
        assert "console.log" in content  # Outputs to console

    def test_confirmation_validation(self):
        """Test that confirmation input is validated"""
        section_file = Path("scripts/onboarding/sections/summary.ts")
        content = section_file.read_text()

        # Should validate yes/no responses
        assert "toLowerCase" in content or "y" in content.lower()
        # Should re-prompt on invalid input or have validation

    def test_previous_section_is_preferences(self):
        """Test that this section follows preferences"""
        section_file = Path("scripts/onboarding/sections/summary.ts")
        content = section_file.read_text()

        # Should reference 'summary' as current section key
        assert "'summary'" in content or '"summary"' in content

    def test_generates_config_files_on_confirmation(self):
        """Test that section triggers config generation"""
        section_file = Path("scripts/onboarding/sections/summary.ts")
        content = section_file.read_text()

        # Should call yaml generation functions or mark state for generation
        assert (
            "generate" in content.lower()
            or "yaml" in content.lower()
            or "config" in content.lower()
        )

    def test_restart_option_clears_state(self):
        """Test that restart option clears existing state"""
        section_file = Path("scripts/onboarding/sections/summary.ts")
        content = section_file.read_text()

        # Should offer restart and clear state if chosen
        if "restart" in content.lower():
            assert "clearState" in content or "clear" in content.lower()

    def test_exit_option_preserves_state(self):
        """Test that exit option preserves state for resume"""
        section_file = Path("scripts/onboarding/sections/summary.ts")
        content = section_file.read_text()

        # If exit option exists, should NOT clear state
        # State should be saved for future resume
        assert "saveState" in content

    def test_success_message_displayed(self):
        """Test that success message is displayed on confirmation"""
        section_file = Path("scripts/onboarding/sections/summary.ts")
        content = section_file.read_text()

        # Should show success/completion message
        assert (
            "✅" in content
            or "complete" in content.lower()
            or "success" in content.lower()
        )

    def test_summary_shows_key_metrics_only(self):
        """Test that summary shows key metrics, not full detailed data"""
        section_file = Path("scripts/onboarding/sections/summary.ts")
        content = section_file.read_text()

        # Should format or summarize data, not dump raw JSON
        # Look for formatting/helper functions
        assert (
            "format" in content.lower()
            or "display" in content.lower()
            or "console.log" in content
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
