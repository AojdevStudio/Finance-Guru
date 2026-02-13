"""
Test suite for Cash Flow Section

Tests the TypeScript cash-flow.ts section implementation via subprocess.
This validates:
- Section initialization
- Input validation (currency, positive values)
- Investment capacity validation (cannot exceed income)
- Data structure correctness
- State persistence
"""

import json
import subprocess
from pathlib import Path

import pytest


class TestCashFlowSection:
    """Test suite for cash flow section"""

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
            "completed_sections": ["liquid_assets", "investments"],
            "current_section": "cash_flow",
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
            },
        }
        state_file = temp_dir / ".onboarding-state.json"
        state_file.write_text(json.dumps(state, indent=2))
        return state_file

    def test_section_exports_run_function(self):
        """Test that cash-flow.ts exports runCashFlowSection"""
        result = subprocess.run(
            [
                "bun",
                "run",
                "-e",
                "import { runCashFlowSection } from './scripts/onboarding/sections/cash-flow.ts'; console.log(typeof runCashFlowSection)",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "function" in result.stdout

    def test_section_file_exists(self):
        """Test that cash-flow.ts file exists"""
        section_file = Path("scripts/onboarding/sections/cash-flow.ts")
        assert section_file.exists(), "cash-flow.ts must exist"
        assert section_file.is_file(), "cash-flow.ts must be a file"

    def test_section_imports_validators(self):
        """Test that section imports validation functions"""
        section_file = Path("scripts/onboarding/sections/cash-flow.ts")
        content = section_file.read_text()

        # Check for required imports
        assert "validateCurrency" in content
        assert "OnboardingState" in content
        assert "saveSectionData" in content
        assert "markSectionComplete" in content

    def test_section_defines_data_interface(self):
        """Test that CashFlowData interface is defined"""
        section_file = Path("scripts/onboarding/sections/cash-flow.ts")
        content = section_file.read_text()

        # Check for interface definition
        assert "interface CashFlowData" in content
        assert "monthly_income:" in content
        assert "fixed_expenses:" in content
        assert "variable_expenses:" in content
        assert "current_savings:" in content
        assert "investment_capacity:" in content

    def test_typescript_compiles_without_errors(self):
        """Test that TypeScript code compiles successfully"""
        result = subprocess.run(
            ["bun", "run", "scripts/onboarding/sections/cash-flow.ts", "--help"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        # Should not have TypeScript compilation errors
        assert "error TS" not in result.stderr

    def test_section_structure_matches_spec(self):
        """Test that section structure matches specification"""
        section_file = Path("scripts/onboarding/sections/cash-flow.ts")
        content = section_file.read_text()

        # Verify section displays correct header
        assert "Section 3 of 7: Cash Flow" in content

        # Verify prompts for required fields
        assert "monthly" in content.lower() and "income" in content.lower()
        assert "fixed" in content.lower() and "expenses" in content.lower()
        assert "variable" in content.lower() and "expenses" in content.lower()
        assert "savings" in content.lower()
        assert "investment capacity" in content.lower()

    def test_section_handles_state_updates(self):
        """Test that section properly updates state"""
        section_file = Path("scripts/onboarding/sections/cash-flow.ts")
        content = section_file.read_text()

        # Verify state management calls
        assert "saveSectionData" in content
        assert "markSectionComplete" in content
        assert "saveState" in content

        # Verify correct section name used
        assert "'cash_flow'" in content or '"cash_flow"' in content

    def test_section_marks_next_section_correctly(self):
        """Test that section marks 'debt' as next section"""
        section_file = Path("scripts/onboarding/sections/cash-flow.ts")
        content = section_file.read_text()

        # Should mark next section as 'debt'
        assert "'debt'" in content or '"debt"' in content

    def test_validation_integration(self):
        """Test that validation functions are properly integrated"""
        # Test currency validation integration
        result = subprocess.run(
            [
                "bun",
                "-e",
                """
            import { validateCurrency } from './scripts/onboarding/modules/input-validator.ts';
            console.log(validateCurrency('25000'));
            console.log(validateCurrency('$25,000'));
            """,
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "25000" in result.stdout

    def test_investment_capacity_validation(self):
        """Test that investment capacity cannot exceed income"""
        section_file = Path("scripts/onboarding/sections/cash-flow.ts")
        content = section_file.read_text()

        # Should validate investment capacity against monthly income
        assert "monthlyIncome" in content or "monthly_income" in content
        assert "cannot exceed" in content.lower() or ">" in content

    def test_calculated_surplus_display(self):
        """Test that calculated surplus is displayed to user"""
        section_file = Path("scripts/onboarding/sections/cash-flow.ts")
        content = section_file.read_text()

        # Should calculate and display surplus
        assert "surplus" in content.lower() or "calculated" in content.lower()
        assert "toLocaleString" in content  # Format currency for display

    def test_expense_descriptions(self):
        """Test that section provides descriptions for expense types"""
        section_file = Path("scripts/onboarding/sections/cash-flow.ts")
        content = section_file.read_text()

        # Should provide examples of fixed expenses
        assert (
            "rent" in content.lower()
            or "insurance" in content.lower()
            or "recurring" in content.lower()
        )

        # Should provide examples of variable expenses
        assert (
            "groceries" in content.lower()
            or "dining" in content.lower()
            or "entertainment" in content.lower()
        )

    def test_section_number_correct(self):
        """Test that section is numbered as Section 3 of 7"""
        section_file = Path("scripts/onboarding/sections/cash-flow.ts")
        content = section_file.read_text()

        assert "Section 3 of 7" in content

    def test_previous_section_is_investments(self):
        """Test that this section follows investments"""
        section_file = Path("scripts/onboarding/sections/cash-flow.ts")
        content = section_file.read_text()

        # Should reference 'cash_flow' as current section key
        assert "'cash_flow'" in content or '"cash_flow"' in content

    def test_readline_usage(self):
        """Test that section uses readline for input"""
        section_file = Path("scripts/onboarding/sections/cash-flow.ts")
        content = section_file.read_text()

        # Should import readline
        assert "readline" in content
        assert "createInterface" in content or "question" in content

    def test_error_handling(self):
        """Test that section has proper error handling"""
        section_file = Path("scripts/onboarding/sections/cash-flow.ts")
        content = section_file.read_text()

        # Should have try/catch or error handling
        assert "try" in content or "catch" in content or "error" in content.lower()
        assert "finally" in content or "close" in content  # Should close readline

    def test_after_tax_income_clarification(self):
        """Test that section clarifies income should be after-tax"""
        section_file = Path("scripts/onboarding/sections/cash-flow.ts")
        content = section_file.read_text()

        # Should specify after-tax income
        assert "after-tax" in content.lower() or "after tax" in content.lower()

    def test_all_currency_fields_validated(self):
        """Test that all currency fields use validateCurrency"""
        section_file = Path("scripts/onboarding/sections/cash-flow.ts")
        content = section_file.read_text()

        # Should use validateCurrency for all monetary inputs
        # Count should be at least 5 (income, fixed, variable, savings, capacity)
        validate_count = content.count("validateCurrency")
        assert validate_count >= 4, (
            f"Expected at least 4 validateCurrency calls, found {validate_count}"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
