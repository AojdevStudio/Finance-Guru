"""
Test suite for onboarding CLI structure
Validates that all required files and modules exist
"""

import os
import pytest
from pathlib import Path


class TestOnboardingStructure:
    """Test the basic structure of the onboarding CLI"""

    @pytest.fixture
    def project_root(self):
        """Get project root directory"""
        return Path(__file__).parent.parent.parent

    @pytest.fixture
    def onboarding_dir(self, project_root):
        """Get onboarding directory"""
        return project_root / "scripts" / "onboarding"

    def test_onboarding_directory_exists(self, onboarding_dir):
        """Test that onboarding directory exists"""
        assert onboarding_dir.exists(), "scripts/onboarding directory should exist"
        assert onboarding_dir.is_dir(), "scripts/onboarding should be a directory"

    def test_main_entry_point_exists(self, onboarding_dir):
        """Test that index.ts exists"""
        index_file = onboarding_dir / "index.ts"
        assert index_file.exists(), "index.ts should exist"
        assert index_file.is_file(), "index.ts should be a file"

    def test_modules_directory_exists(self, onboarding_dir):
        """Test that modules directory exists"""
        modules_dir = onboarding_dir / "modules"
        assert modules_dir.exists(), "modules directory should exist"
        assert modules_dir.is_dir(), "modules should be a directory"

    def test_input_validator_module_exists(self, onboarding_dir):
        """Test that input-validator.ts exists"""
        validator_file = onboarding_dir / "modules" / "input-validator.ts"
        assert validator_file.exists(), "input-validator.ts should exist"
        assert validator_file.is_file(), "input-validator.ts should be a file"

    def test_progress_module_exists(self, onboarding_dir):
        """Test that progress.ts exists"""
        progress_file = onboarding_dir / "modules" / "progress.ts"
        assert progress_file.exists(), "progress.ts should exist"
        assert progress_file.is_file(), "progress.ts should be a file"

    def test_yaml_generator_module_exists(self, onboarding_dir):
        """Test that yaml-generator.ts exists"""
        generator_file = onboarding_dir / "modules" / "yaml-generator.ts"
        assert generator_file.exists(), "yaml-generator.ts should exist"
        assert generator_file.is_file(), "yaml-generator.ts should be a file"

    def test_templates_directory_exists(self, onboarding_dir):
        """Test that templates directory exists"""
        templates_dir = onboarding_dir / "modules" / "templates"
        assert templates_dir.exists(), "templates directory should exist"
        assert templates_dir.is_dir(), "templates should be a directory"

    def test_template_files_exist(self, onboarding_dir):
        """Test that all template files exist"""
        templates_dir = onboarding_dir / "modules" / "templates"

        expected_templates = [
            "user-profile.template.yaml",
            "config.template.yaml",
            "system-context.template.md",
            "CLAUDE.template.md",
            "env.template"
        ]

        for template_name in expected_templates:
            template_file = templates_dir / template_name
            assert template_file.exists(), f"{template_name} should exist"
            assert template_file.is_file(), f"{template_name} should be a file"

    def test_sections_directory_exists(self, onboarding_dir):
        """Test that sections directory exists (for future implementation)"""
        sections_dir = onboarding_dir / "sections"
        assert sections_dir.exists(), "sections directory should exist"
        assert sections_dir.is_dir(), "sections should be a directory"

    def test_tests_directory_exists(self, onboarding_dir):
        """Test that tests directory exists (for future implementation)"""
        tests_dir = onboarding_dir / "tests"
        assert tests_dir.exists(), "tests directory should exist"
        assert tests_dir.is_dir(), "tests should be a directory"

    def test_module_content_validation(self, onboarding_dir):
        """Test that modules contain expected exports"""
        # Test input-validator.ts has validation functions
        validator_file = onboarding_dir / "modules" / "input-validator.ts"
        content = validator_file.read_text()

        expected_functions = [
            "validateCurrency",
            "validatePercentage",
            "validatePositiveInteger",
            "validateNonEmpty",
            "validateEmail",
            "validateSpreadsheetId",
            "validateRiskTolerance",
            "validateInvestmentPhilosophy",
            "validateBrokerage"
        ]

        for func_name in expected_functions:
            assert func_name in content, f"input-validator.ts should export {func_name}"

    def test_progress_module_content(self, onboarding_dir):
        """Test that progress.ts has state management functions"""
        progress_file = onboarding_dir / "modules" / "progress.ts"
        content = progress_file.read_text()

        expected_functions = [
            "hasExistingState",
            "loadState",
            "saveState",
            "createNewState",
            "markSectionComplete",
            "saveSectionData",
            "getSectionData",
            "clearState",
            "getNextSection",
            "isComplete"
        ]

        for func_name in expected_functions:
            assert func_name in content, f"progress.ts should export {func_name}"

    def test_yaml_generator_content(self, onboarding_dir):
        """Test that yaml-generator.ts has generation functions"""
        generator_file = onboarding_dir / "modules" / "yaml-generator.ts"
        content = generator_file.read_text()

        expected_functions = [
            "generateUserProfile",
            "generateConfig",
            "generateSystemContext",
            "generateClaudeMd",
            "generateEnv",
            "generateAllConfigs"
        ]

        for func_name in expected_functions:
            assert func_name in content, f"yaml-generator.ts should export {func_name}"

    def test_index_entry_point_content(self, onboarding_dir):
        """Test that index.ts has main function and displays"""
        index_file = onboarding_dir / "index.ts"
        content = index_file.read_text()

        # Check for shebang
        assert content.startswith("#!/usr/bin/env bun"), "index.ts should have bun shebang"

        # Check for key functions
        expected_functions = [
            "displayWelcome",
            "displayResume",
            "displayComplete",
            "main"
        ]

        for func_name in expected_functions:
            assert func_name in content, f"index.ts should have {func_name} function"

        # Check for imports from modules
        assert "from './modules/progress'" in content, "index.ts should import from progress module"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
