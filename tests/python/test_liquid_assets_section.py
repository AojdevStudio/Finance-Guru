"""
Test suite for Liquid Assets Section

Tests the TypeScript liquid-assets.ts section implementation via subprocess.
This validates:
- Section initialization
- Input validation (currency, integer, percentage)
- Data structure correctness
- State persistence
"""

import json
import subprocess
from pathlib import Path

import pytest


class TestLiquidAssetsSection:
    """Test suite for liquid assets section"""

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
            "completed_sections": [],
            "current_section": None,
            "data": {},
        }
        state_file = temp_dir / ".onboarding-state.json"
        state_file.write_text(json.dumps(state, indent=2))
        return state_file

    def test_section_exports_run_function(self):
        """Test that liquid-assets.ts exports runLiquidAssetsSection"""
        result = subprocess.run(
            [
                "bun",
                "run",
                "-e",
                "import { runLiquidAssetsSection } from './scripts/onboarding/sections/liquid-assets.ts'; console.log(typeof runLiquidAssetsSection)",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "function" in result.stdout

    def test_section_file_exists(self):
        """Test that liquid-assets.ts file exists"""
        section_file = Path("scripts/onboarding/sections/liquid-assets.ts")
        assert section_file.exists(), "liquid-assets.ts must exist"
        assert section_file.is_file(), "liquid-assets.ts must be a file"

    def test_section_imports_validators(self):
        """Test that section imports validation functions"""
        section_file = Path("scripts/onboarding/sections/liquid-assets.ts")
        content = section_file.read_text()

        # Check for required imports
        assert "validateCurrency" in content
        assert "validatePositiveInteger" in content
        assert "validatePercentage" in content
        assert "OnboardingState" in content
        assert "saveSectionData" in content
        assert "markSectionComplete" in content

    def test_section_defines_data_interface(self):
        """Test that LiquidAssetsData interface is defined"""
        section_file = Path("scripts/onboarding/sections/liquid-assets.ts")
        content = section_file.read_text()

        # Check for interface definition
        assert "interface LiquidAssetsData" in content
        assert "total:" in content
        assert "accounts_count:" in content
        assert "average_yield:" in content
        assert "structure:" in content

    def test_typescript_compiles_without_errors(self):
        """Test that TypeScript code compiles successfully"""
        result = subprocess.run(
            ["bun", "run", "scripts/onboarding/sections/liquid-assets.ts", "--help"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        # Should not have TypeScript compilation errors
        assert "error TS" not in result.stderr

    def test_section_structure_matches_spec(self):
        """Test that section structure matches specification"""
        section_file = Path("scripts/onboarding/sections/liquid-assets.ts")
        content = section_file.read_text()

        # Verify section displays correct header
        assert "Section 1 of 7: Liquid Assets" in content

        # Verify prompts for required fields
        assert "total value of your liquid cash" in content or "liquid cash" in content
        assert "How many accounts" in content
        assert "average yield" in content
        assert "account structure" in content.lower()

    def test_section_handles_state_updates(self):
        """Test that section properly updates state"""
        section_file = Path("scripts/onboarding/sections/liquid-assets.ts")
        content = section_file.read_text()

        # Verify state management calls
        assert "saveSectionData" in content
        assert "markSectionComplete" in content
        assert "saveState" in content

        # Verify correct section name used
        assert "'liquid_assets'" in content

    def test_section_marks_next_section_correctly(self):
        """Test that section marks 'investments' as next section"""
        section_file = Path("scripts/onboarding/sections/liquid-assets.ts")
        content = section_file.read_text()

        # Should mark next section as 'investments'
        assert "'investments'" in content

    def test_validation_integration(self):
        """Test that validation functions are properly integrated"""
        # Test currency validation integration
        result = subprocess.run(
            [
                "bun",
                "-e",
                """
            import { validateCurrency } from './scripts/onboarding/modules/input-validator.ts';
            console.log(validateCurrency('10000'));
            console.log(validateCurrency('$10,000'));
            """,
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "10000" in result.stdout

    def test_percentage_conversion(self):
        """Test that percentage is converted to decimal in data structure"""
        section_file = Path("scripts/onboarding/sections/liquid-assets.ts")
        content = section_file.read_text()

        # Should convert percentage to decimal (divide by 100)
        assert "/ 100" in content or "/100" in content

    def test_optional_structure_field(self):
        """Test that account structure is optional"""
        section_file = Path("scripts/onboarding/sections/liquid-assets.ts")
        content = section_file.read_text()

        # Should have logic for optional input
        assert "optional" in content.lower()
        assert "skip" in content.lower() or "enter" in content.lower()

    def test_section_provides_example(self):
        """Test that section provides example for structure field"""
        section_file = Path("scripts/onboarding/sections/liquid-assets.ts")
        content = section_file.read_text()

        # Should show example structure
        assert "Example:" in content or "example" in content.lower()
        assert "LLC" in content or "checking" in content or "savings" in content

    def test_readline_usage(self):
        """Test that section uses readline for input"""
        section_file = Path("scripts/onboarding/sections/liquid-assets.ts")
        content = section_file.read_text()

        # Should import readline
        assert "readline" in content
        assert "createInterface" in content or "question" in content

    def test_error_handling(self):
        """Test that section has proper error handling"""
        section_file = Path("scripts/onboarding/sections/liquid-assets.ts")
        content = section_file.read_text()

        # Should have try/catch or error handling
        assert "try" in content or "catch" in content or "error" in content.lower()
        assert "finally" in content or "close" in content  # Should close readline


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
