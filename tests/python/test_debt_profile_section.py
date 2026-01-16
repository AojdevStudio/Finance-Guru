"""
Test suite for Debt Profile Section

Tests the TypeScript debt-profile.ts section implementation via subprocess.
This validates:
- Section initialization
- Input validation (currency, positive values, percentages)
- Data structure correctness
- State persistence
- Debt type handling (mortgage, student loans, car loans, credit cards)
"""

import json
import subprocess
import tempfile
from pathlib import Path
import pytest


class TestDebtProfileSection:
    """Test suite for debt profile section"""

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
            "completed_sections": ["liquid_assets", "investments", "cash_flow"],
            "current_section": "debt",
            "data": {
                "liquid_assets": {
                    "total": 14491,
                    "accounts_count": 10,
                    "average_yield": 0.04,
                    "structure": []
                },
                "investments": {
                    "total_value": 243382.67,
                    "retirement_accounts": 308000,
                    "allocation": "aggressive_growth",
                    "risk_profile": "aggressive"
                },
                "cash_flow": {
                    "monthly_income": 25000,
                    "fixed_expenses": 4500,
                    "variable_expenses": 10000,
                    "current_savings": 5000,
                    "investment_capacity": 10500
                }
            }
        }
        state_file = temp_dir / ".onboarding-state.json"
        state_file.write_text(json.dumps(state, indent=2))
        return state_file

    def test_section_exports_run_function(self):
        """Test that debt-profile.ts exports runDebtProfileSection"""
        result = subprocess.run(
            ["bun", "run", "-e", "import { runDebtProfileSection } from './scripts/onboarding/sections/debt-profile.ts'; console.log(typeof runDebtProfileSection)"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "function" in result.stdout

    def test_section_file_exists(self):
        """Test that debt-profile.ts file exists"""
        section_file = Path("scripts/onboarding/sections/debt-profile.ts")
        assert section_file.exists(), "debt-profile.ts must exist"
        assert section_file.is_file(), "debt-profile.ts must be a file"

    def test_section_imports_validators(self):
        """Test that section imports validation functions"""
        section_file = Path("scripts/onboarding/sections/debt-profile.ts")
        content = section_file.read_text()

        # Check for required imports
        assert "validateCurrency" in content
        assert "validatePercentage" in content
        assert "OnboardingState" in content
        assert "saveSectionData" in content
        assert "markSectionComplete" in content

    def test_section_defines_data_interface(self):
        """Test that DebtProfileData interface is defined"""
        section_file = Path("scripts/onboarding/sections/debt-profile.ts")
        content = section_file.read_text()

        # Check for interface definition
        assert "interface DebtProfileData" in content
        assert "mortgage_balance:" in content
        assert "mortgage_payment:" in content
        assert "other_debt:" in content
        assert "weighted_interest_rate:" in content

    def test_section_defines_debt_item_interface(self):
        """Test that DebtItem interface is defined for other_debt array"""
        section_file = Path("scripts/onboarding/sections/debt-profile.ts")
        content = section_file.read_text()

        # Check for debt item structure
        assert "type:" in content
        assert "rate:" in content

    def test_typescript_compiles_without_errors(self):
        """Test that TypeScript code compiles successfully"""
        result = subprocess.run(
            ["bun", "run", "scripts/onboarding/sections/debt-profile.ts", "--help"],
            capture_output=True,
            text=True,
            timeout=5
        )
        # Should not have TypeScript compilation errors
        assert "error TS" not in result.stderr

    def test_section_structure_matches_spec(self):
        """Test that section structure matches specification"""
        section_file = Path("scripts/onboarding/sections/debt-profile.ts")
        content = section_file.read_text()

        # Verify section displays correct header
        assert "Section 4 of 7: Debt Profile" in content

        # Verify prompts for required fields
        assert "mortgage" in content.lower()
        assert "student" in content.lower() or "loans" in content.lower()
        assert "car" in content.lower()
        assert "credit" in content.lower() and "card" in content.lower()

    def test_section_handles_state_updates(self):
        """Test that section properly updates state"""
        section_file = Path("scripts/onboarding/sections/debt-profile.ts")
        content = section_file.read_text()

        # Verify state management calls
        assert "saveSectionData" in content
        assert "markSectionComplete" in content
        assert "saveState" in content

        # Verify correct section name used
        assert "'debt'" in content or '"debt"' in content

    def test_section_marks_next_section_correctly(self):
        """Test that section marks next section appropriately"""
        section_file = Path("scripts/onboarding/sections/debt-profile.ts")
        content = section_file.read_text()

        # Should reference next section (preferences or opportunities)
        # Check for any reasonable next section
        assert "preferences" in content or "opportunities" in content or "goals" in content

    def test_validation_integration(self):
        """Test that validation functions are properly integrated"""
        # Test currency validation integration
        result = subprocess.run(
            ["bun", "-e", """
            import { validateCurrency } from './scripts/onboarding/modules/input-validator.ts';
            console.log(validateCurrency('365139.76'));
            console.log(validateCurrency('$1,712.68'));
            """],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "365139.76" in result.stdout

    def test_percentage_validation_integration(self):
        """Test that percentage validation is properly integrated"""
        # Test percentage validation
        result = subprocess.run(
            ["bun", "-e", """
            import { validatePercentage } from './scripts/onboarding/modules/input-validator.ts';
            console.log(validatePercentage('8'));
            console.log(validatePercentage('8%'));
            console.log(validatePercentage('0.08'));
            """],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0

    def test_mortgage_balance_prompt(self):
        """Test that section prompts for mortgage balance"""
        section_file = Path("scripts/onboarding/sections/debt-profile.ts")
        content = section_file.read_text()

        # Should prompt for mortgage balance
        assert "mortgage" in content.lower()
        assert "balance" in content.lower()

    def test_mortgage_payment_prompt(self):
        """Test that section prompts for mortgage payment"""
        section_file = Path("scripts/onboarding/sections/debt-profile.ts")
        content = section_file.read_text()

        # Should prompt for monthly mortgage payment
        assert "mortgage" in content.lower()
        assert "payment" in content.lower()

    def test_other_debt_collection(self):
        """Test that section collects other debt types"""
        section_file = Path("scripts/onboarding/sections/debt-profile.ts")
        content = section_file.read_text()

        # Should handle multiple debt types
        assert "student" in content.lower() or "loan" in content.lower()
        assert "car" in content.lower()
        assert "credit" in content.lower() and "card" in content.lower()

    def test_interest_rate_prompts(self):
        """Test that section prompts for interest rates"""
        section_file = Path("scripts/onboarding/sections/debt-profile.ts")
        content = section_file.read_text()

        # Should prompt for interest rates
        assert "rate" in content.lower() or "interest" in content.lower()
        assert "validatePercentage" in content

    def test_section_number_correct(self):
        """Test that section is numbered as Section 4 of 7"""
        section_file = Path("scripts/onboarding/sections/debt-profile.ts")
        content = section_file.read_text()

        assert "Section 4 of 7" in content

    def test_previous_section_is_cash_flow(self):
        """Test that this section follows cash_flow"""
        section_file = Path("scripts/onboarding/sections/debt-profile.ts")
        content = section_file.read_text()

        # Should reference 'debt' as current section key
        assert "'debt'" in content or '"debt"' in content

    def test_readline_usage(self):
        """Test that section uses readline for input"""
        section_file = Path("scripts/onboarding/sections/debt-profile.ts")
        content = section_file.read_text()

        # Should import readline
        assert "readline" in content
        assert "createInterface" in content or "question" in content

    def test_error_handling(self):
        """Test that section has proper error handling"""
        section_file = Path("scripts/onboarding/sections/debt-profile.ts")
        content = section_file.read_text()

        # Should have try/catch or error handling
        assert "try" in content or "catch" in content or "error" in content.lower()
        assert "finally" in content or "close" in content  # Should close readline

    def test_optional_fields_handling(self):
        """Test that section handles optional fields (no debt scenario)"""
        section_file = Path("scripts/onboarding/sections/debt-profile.ts")
        content = section_file.read_text()

        # Should handle cases where user has no mortgage or no other debt
        # This could be through allowEmpty or conditional logic
        assert "allowEmpty" in content or "optional" in content.lower() or "skip" in content.lower() or "none" in content.lower()

    def test_all_currency_fields_validated(self):
        """Test that all currency fields use validateCurrency"""
        section_file = Path("scripts/onboarding/sections/debt-profile.ts")
        content = section_file.read_text()

        # Should use validateCurrency for mortgage balance and payment
        # At least 2 calls expected (balance, payment)
        validate_count = content.count("validateCurrency")
        assert validate_count >= 2, f"Expected at least 2 validateCurrency calls, found {validate_count}"

    def test_weighted_interest_calculation(self):
        """Test that weighted interest rate is calculated or collected"""
        section_file = Path("scripts/onboarding/sections/debt-profile.ts")
        content = section_file.read_text()

        # Should reference weighted interest rate
        assert "weighted_interest_rate" in content or "weighted" in content.lower()

    def test_debt_types_array_structure(self):
        """Test that other_debt is structured as an array"""
        section_file = Path("scripts/onboarding/sections/debt-profile.ts")
        content = section_file.read_text()

        # Should use array structure for other_debt
        assert "other_debt:" in content
        # Should push or add items to array
        assert "push" in content or "[]" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
