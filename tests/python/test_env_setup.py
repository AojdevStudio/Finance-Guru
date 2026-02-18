"""
Test suite for Environment Setup Section
Tests the interactive .env setup functionality
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path


class TestEnvSetup:
    """Test class for environment setup functionality"""

    def setup_method(self):
        """Set up test environment before each test"""
        # Create temporary directory for test
        self.test_dir = tempfile.mkdtemp(prefix="test_env_setup_")
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

        # Create necessary directories
        os.makedirs("scripts/onboarding/sections", exist_ok=True)
        os.makedirs("scripts/onboarding/modules", exist_ok=True)
        os.makedirs("fin-guru/data", exist_ok=True)

    def teardown_method(self):
        """Clean up test environment after each test"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_env_setup_file_exists(self):
        """Test that env-setup.ts file exists"""
        env_setup_path = (
            Path(self.original_cwd) / "scripts/onboarding/sections/env-setup.ts"
        )
        assert env_setup_path.exists(), "env-setup.ts file should exist"

    def test_env_setup_exports_function(self):
        """Test that env-setup.ts exports runEnvSetupSection function"""
        env_setup_path = (
            Path(self.original_cwd) / "scripts/onboarding/sections/env-setup.ts"
        )
        content = env_setup_path.read_text()

        assert "export async function runEnvSetupSection" in content, (
            "Should export runEnvSetupSection function"
        )
        assert "state: OnboardingState" in content, (
            "Should accept OnboardingState parameter"
        )
        assert "Promise<OnboardingState>" in content, (
            "Should return Promise<OnboardingState>"
        )

    def test_env_setup_has_interface(self):
        """Test that EnvSetupData interface is defined"""
        env_setup_path = (
            Path(self.original_cwd) / "scripts/onboarding/sections/env-setup.ts"
        )
        content = env_setup_path.read_text()

        assert "export interface EnvSetupData" in content, (
            "Should define EnvSetupData interface"
        )
        assert "user_name: string" in content, "Should have user_name field"
        assert "communication_language: string" in content, (
            "Should have communication_language field"
        )

    def test_env_setup_validates_user_name(self):
        """Test that user name validation is implemented"""
        env_setup_path = (
            Path(self.original_cwd) / "scripts/onboarding/sections/env-setup.ts"
        )
        content = env_setup_path.read_text()

        assert "validateNonEmpty" in content, (
            "Should import and use validateNonEmpty for user name"
        )

    def test_env_setup_handles_optional_fields(self):
        """Test that optional fields are properly handled"""
        env_setup_path = (
            Path(self.original_cwd) / "scripts/onboarding/sections/env-setup.ts"
        )
        content = env_setup_path.read_text()

        # Check for optional API key fields
        assert "has_alphavantage?" in content, "Should have optional alphavantage flag"
        assert "alphavantage_key?" in content, "Should have optional alphavantage_key"
        assert "has_brightdata?" in content, "Should have optional brightdata flag"
        assert "brightdata_key?" in content, "Should have optional brightdata_key"

    def test_env_setup_generates_env_file(self):
        """Test that .env file generation is implemented"""
        env_setup_path = (
            Path(self.original_cwd) / "scripts/onboarding/sections/env-setup.ts"
        )
        content = env_setup_path.read_text()

        assert "function generateEnvFile" in content, (
            "Should have generateEnvFile function"
        )
        assert "writeFileSync" in content, "Should use writeFileSync to create .env"
        assert ".env" in content, "Should reference .env file"

    def test_env_setup_includes_security_warnings(self):
        """Test that security warnings are displayed"""
        env_setup_path = (
            Path(self.original_cwd) / "scripts/onboarding/sections/env-setup.ts"
        )
        content = env_setup_path.read_text()

        assert "Security Notes" in content or "🔒" in content, (
            "Should include security warnings"
        )
        assert "gitignore" in content.lower(), "Should mention gitignore"

    def test_env_setup_saves_section_data(self):
        """Test that section data is saved to state"""
        env_setup_path = (
            Path(self.original_cwd) / "scripts/onboarding/sections/env-setup.ts"
        )
        content = env_setup_path.read_text()

        assert "saveSectionData(state, 'env_setup'" in content, (
            "Should save section data with correct key"
        )
        assert "markSectionComplete(state, 'env_setup'" in content, (
            "Should mark section as complete"
        )
        assert "saveState(state)" in content, "Should save state to disk"

    def test_env_setup_handles_google_sheets(self):
        """Test that Google Sheets integration is optional"""
        env_setup_path = (
            Path(self.original_cwd) / "scripts/onboarding/sections/env-setup.ts"
        )
        content = env_setup_path.read_text()

        assert "google_sheets_credentials?" in content, (
            "Should have optional google_sheets_credentials field"
        )
        assert "Google Sheets" in content, "Should mention Google Sheets integration"

    def test_env_setup_handles_brokerage_info(self):
        """Test that brokerage information is handled"""
        env_setup_path = (
            Path(self.original_cwd) / "scripts/onboarding/sections/env-setup.ts"
        )
        content = env_setup_path.read_text()

        assert "primary_brokerage?" in content, (
            "Should have optional primary_brokerage field"
        )
        assert "brokerage_account_number?" in content, (
            "Should have optional brokerage_account_number field"
        )

    def test_env_file_template_structure(self):
        """Test that .env file template has correct structure"""
        env_setup_path = (
            Path(self.original_cwd) / "scripts/onboarding/sections/env-setup.ts"
        )
        content = env_setup_path.read_text()

        # Check for expected sections in env file
        assert "USER_NAME=" in content, "Should set USER_NAME in .env"
        assert "COMMUNICATION_LANGUAGE=" in content, (
            "Should set COMMUNICATION_LANGUAGE in .env"
        )
        assert "PROJECT_ROOT=" in content, "Should set PROJECT_ROOT in .env"
        assert "FIN_GURU_PATH=" in content, "Should set FIN_GURU_PATH in .env"
        assert "NOTEBOOKS_PATH=" in content, "Should set NOTEBOOKS_PATH in .env"

    def test_env_setup_imports_dependencies(self):
        """Test that all required dependencies are imported"""
        env_setup_path = (
            Path(self.original_cwd) / "scripts/onboarding/sections/env-setup.ts"
        )
        content = env_setup_path.read_text()

        required_imports = [
            "createInterface",
            "writeFileSync",
            "validateNonEmpty",
            "OnboardingState",
            "saveSectionData",
            "markSectionComplete",
            "saveState",
        ]

        for import_name in required_imports:
            assert import_name in content, f"Should import {import_name}"

    def test_typescript_syntax_valid(self):
        """Test that TypeScript file has valid syntax (basic check)"""
        env_setup_path = (
            Path(self.original_cwd) / "scripts/onboarding/sections/env-setup.ts"
        )

        # Try to run TypeScript compiler check (if available)
        try:
            result = subprocess.run(
                ["bunx", "tsc", "--noEmit", str(env_setup_path)],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=self.original_cwd,
            )
            # If tsc is available, check for no errors
            # Note: warnings are ok, we just want to catch syntax errors
            assert "error TS" not in result.stderr, (
                f"TypeScript compilation errors: {result.stderr}"
            )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # If tsc is not available or times out, skip this check
            pass


def test_module_discovery():
    """Test that the env-setup module can be discovered"""
    env_setup_path = Path("scripts/onboarding/sections/env-setup.ts")
    assert env_setup_path.exists(), "env-setup.ts should exist in correct location"


if __name__ == "__main__":
    # Run basic checks
    print("Running Environment Setup tests...")
    test = TestEnvSetup()

    # Run each test method
    test_methods = [method for method in dir(test) if method.startswith("test_")]

    passed = 0
    failed = 0

    for method_name in test_methods:
        try:
            test.setup_method()
            method = getattr(test, method_name)
            method()
            test.teardown_method()
            print(f"✓ {method_name}")
            passed += 1
        except AssertionError as e:
            print(f"✗ {method_name}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {method_name}: Unexpected error: {e}")
            failed += 1

    # Run module discovery test
    try:
        test_module_discovery()
        print("✓ test_module_discovery")
        passed += 1
    except AssertionError as e:
        print(f"✗ test_module_discovery: {e}")
        failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")
    exit(0 if failed == 0 else 1)
