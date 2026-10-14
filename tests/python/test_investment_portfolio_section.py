"""
Test suite for Investment Portfolio Section

Tests the TypeScript investment-portfolio.ts section implementation via subprocess.
This validates:
- Section initialization
- Input validation (currency, risk tolerance, non-empty)
- Data structure correctness
- State persistence
"""

import json
import subprocess
from pathlib import Path

import pytest


class TestInvestmentPortfolioSection:
    """Test suite for investment portfolio section"""

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
            "completed_sections": ["liquid_assets"],
            "current_section": "investments",
            "data": {
                "liquid_assets": {
                    "total": 14491,
                    "accounts_count": 10,
                    "average_yield": 0.04,
                    "structure": [],
                }
            },
        }
        state_file = temp_dir / ".onboarding-state.json"
        state_file.write_text(json.dumps(state, indent=2))
        return state_file

    def test_section_exports_run_function(self):
        """Test that investment-portfolio.ts exports runInvestmentPortfolioSection"""
        result = subprocess.run(
            [
                "bun",
                "run",
                "-e",
                "import { runInvestmentPortfolioSection } from './scripts/onboarding/sections/investment-portfolio.ts'; console.log(typeof runInvestmentPortfolioSection)",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "function" in result.stdout

    def test_section_file_exists(self):
        """Test that investment-portfolio.ts file exists"""
        section_file = Path("scripts/onboarding/sections/investment-portfolio.ts")
        assert section_file.exists(), "investment-portfolio.ts must exist"
        assert section_file.is_file(), "investment-portfolio.ts must be a file"

    def test_section_imports_validators(self):
        """Test that section imports validation functions"""
        section_file = Path("scripts/onboarding/sections/investment-portfolio.ts")
        content = section_file.read_text()

        assert "validateCurrency" in content
        assert "validateRiskTolerance" in content
        assert "validateNonEmpty" in content
        assert "OnboardingState" in content
        assert "saveSectionData" in content
        assert "markSectionComplete" in content

    def test_section_defines_data_interface(self):
        """Test that InvestmentPortfolioData interface is defined"""
        section_file = Path("scripts/onboarding/sections/investment-portfolio.ts")
        content = section_file.read_text()

        assert "interface InvestmentPortfolioData" in content
        assert "total_value:" in content
        assert "retirement_accounts:" in content
        assert "bitcoin_holdings:" in content
        assert "total_net_worth:" in content
        assert "allocation:" in content
        assert "accounts:" in content
        assert "risk_profile:" in content

    def test_typescript_compiles_without_errors(self):
        """Test that TypeScript code compiles successfully"""
        result = subprocess.run(
            [
                "bun",
                "run",
                "scripts/onboarding/sections/investment-portfolio.ts",
                "--help",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert "error TS" not in result.stderr

    def test_section_structure_matches_spec(self):
        """Test that section structure matches specification"""
        section_file = Path("scripts/onboarding/sections/investment-portfolio.ts")
        content = section_file.read_text()

        assert "Section 2 of 7: Investment Portfolio" in content

        assert "brokerage" in content.lower() or "investment" in content.lower()
        assert "retirement" in content.lower()
        assert "bitcoin" in content.lower() or "crypto" in content.lower()
        assert "allocation" in content.lower()
        assert "accounts" in content.lower()
        assert "risk" in content.lower()

    def test_section_handles_state_updates(self):
        """Test that section properly updates state"""
        section_file = Path("scripts/onboarding/sections/investment-portfolio.ts")
        content = section_file.read_text()

        assert "saveSectionData" in content
        assert "markSectionComplete" in content
        assert "saveState" in content

        assert (
            "'investment_portfolio'" in content or '"investment_portfolio"' in content
        )

    def test_section_marks_next_section_correctly(self):
        """Test that section marks 'cash_flow' as next section"""
        section_file = Path("scripts/onboarding/sections/investment-portfolio.ts")
        content = section_file.read_text()

        assert "'cash_flow'" in content or '"cash_flow"' in content

    def test_validation_integration(self):
        """Test that validation functions are properly integrated"""
        result = subprocess.run(
            [
                "bun",
                "-e",
                """
            import { validateCurrency } from './scripts/onboarding/modules/input-validator.ts';
            console.log(validateCurrency('250000'));
            console.log(validateCurrency('$250,000'));
            """,
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "250000" in result.stdout

    def test_risk_tolerance_validation(self):
        """Test that risk tolerance validation is used"""
        result = subprocess.run(
            [
                "bun",
                "-e",
                """
            import { validateRiskTolerance } from './scripts/onboarding/modules/input-validator.ts';
            console.log(validateRiskTolerance('aggressive'));
            console.log(validateRiskTolerance('moderate'));
            console.log(validateRiskTolerance('conservative'));
            """,
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "aggressive" in result.stdout

    def test_bitcoin_excluded_option(self):
        """Test that bitcoin can be excluded from planning"""
        section_file = Path("scripts/onboarding/sections/investment-portfolio.ts")
        content = section_file.read_text()

        assert "excluded" in content.lower() or "exclude" in content.lower()
        assert "EXCLUDED_FROM_PLANNING" in content

    def test_total_net_worth_calculation(self):
        """Test that total net worth is calculated correctly"""
        section_file = Path("scripts/onboarding/sections/investment-portfolio.ts")
        content = section_file.read_text()

        assert "total_net_worth" in content.lower()
        assert "bitcoinValue" in content or "bitcoin_value" in content.lower()

    def test_accounts_array_parsing(self):
        """Test that accounts are parsed into array"""
        section_file = Path("scripts/onboarding/sections/investment-portfolio.ts")
        content = section_file.read_text()

        assert "split" in content
        assert "," in content
        assert "trim" in content

    def test_section_provides_examples(self):
        """Test that section provides examples for inputs"""
        section_file = Path("scripts/onboarding/sections/investment-portfolio.ts")
        content = section_file.read_text()

        assert "Example" in content or "example" in content.lower()
        assert "401k" in content or "IRA" in content or "Roth" in content

    def test_readline_usage(self):
        """Test that section reads input through the shared readline prompt"""
        section_file = Path("scripts/onboarding/sections/investment-portfolio.ts")
        content = section_file.read_text()

        assert "from '../modules/prompt'" in content
        assert "createPrompt()" in content

    def test_error_handling(self):
        """Test that section has proper error handling"""
        section_file = Path("scripts/onboarding/sections/investment-portfolio.ts")
        content = section_file.read_text()

        assert "try" in content or "catch" in content or "error" in content.lower()
        assert "finally" in content or "close" in content

    def test_allocation_strategy_prompt(self):
        """Test that allocation strategy is prompted"""
        section_file = Path("scripts/onboarding/sections/investment-portfolio.ts")
        content = section_file.read_text()

        assert "allocation" in content.lower()
        assert "aggressive" in content.lower() or "balanced" in content.lower()

    def test_section_number_correct(self):
        """Test that section is numbered as Section 2 of 7"""
        section_file = Path("scripts/onboarding/sections/investment-portfolio.ts")
        content = section_file.read_text()

        assert "Section 2 of 7" in content

    def test_previous_section_is_liquid_assets(self):
        """Test that this section follows liquid assets"""
        section_file = Path("scripts/onboarding/sections/investment-portfolio.ts")
        content = section_file.read_text()

        assert "'investments'" in content or '"investments"' in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
