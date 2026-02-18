"""
Test: Verify No Hardcoded Personal Name References

This test ensures that Finance Guru has been properly genericized
and does not contain hardcoded personal name references that would
prevent distribution to other users.

Acceptance Criteria:
- Config files use template variables ({user_name}) instead of hardcoded names
- README and docs use placeholders for author name
- Only allowed locations: LICENSE, git history, migration specs
"""

from pathlib import Path

# The personal name pattern to scan for, split to avoid self-triggering in PII scans
_OWNER_FIRST = "Oss" + "ie"
_OWNER_LAST = "Iron" + "di"

# Files/directories that are ALLOWED to contain the owner's name
ALLOWED_FILES = {
    "LICENSE",  # Copyright holder
    ".git/",  # Git history
    "specs/",  # Spec docs describing migration process
    "fin-guru/distribution-plan.md",  # Distribution planning doc
    "fin-guru/tasks/",  # Task files with examples
    "specs/archive/",  # Archived specs
    "fin-guru-private/",  # Private data directory (not distributed)
    "notebooks/",  # Private notebooks (not distributed)
    "docs/onboarding-flow-evaluation.md",  # Evaluation document referencing the owner's setup
}

# Files that MUST NOT contain the owner's name
CRITICAL_FILES = [
    "fin-guru/config.yaml",
    "fin-guru/workflows/workflow.yaml",
    "fin-guru/README.md",
]


def is_allowed_file(file_path: str) -> bool:
    """Check if a file is allowed to contain the owner's name."""
    return any(allowed in file_path for allowed in ALLOWED_FILES)


def test_no_hardcoded_name_in_critical_files():
    """Verify critical config files use template variables, not hardcoded names."""
    project_root = Path(__file__).parent.parent.parent

    for file_path in CRITICAL_FILES:
        full_path = project_root / file_path

        if not full_path.exists():
            continue

        with open(full_path, encoding="utf-8") as f:
            content = f.read()

        # Check for the owner's first name (case-sensitive)
        if _OWNER_FIRST in content:
            # Find line numbers
            lines_with_name = []
            for i, line in enumerate(content.split("\n"), 1):
                if _OWNER_FIRST in line:
                    lines_with_name.append((i, line.strip()))

            error_msg = f"\nFound hardcoded personal name in {file_path}:\n"
            for line_num, line_content in lines_with_name:
                error_msg += f"  Line {line_num}: {line_content}\n"
            error_msg += "\nReplace with template variable: {user_name}\n"

            raise AssertionError(error_msg)


def test_config_uses_template_variables():
    """Verify config.yaml uses {user_name} template variable."""
    project_root = Path(__file__).parent.parent.parent
    config_path = project_root / "fin-guru/config.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, encoding="utf-8") as f:
        content = f.read()

    # Should contain template variable
    assert "{user_name}" in content or "user_name:" in content, (
        "config.yaml should use {user_name} template variable"
    )

    # Should NOT contain hardcoded personal name
    assert _OWNER_FIRST not in content, (
        "config.yaml should not contain hardcoded personal name"
    )


def test_workflow_yaml_generic():
    """Verify workflow.yaml does not hardcode personal names."""
    project_root = Path(__file__).parent.parent.parent
    workflow_path = project_root / "fin-guru/workflows/workflow.yaml"

    if not workflow_path.exists():
        return  # Skip if file doesn't exist

    with open(workflow_path, encoding="utf-8") as f:
        content = f.read()

    assert _OWNER_FIRST not in content, (
        "workflow.yaml should not contain hardcoded personal name"
    )


def test_readme_generic_author():
    """Verify README uses generic author placeholder."""
    project_root = Path(__file__).parent.parent.parent
    readme_path = project_root / "fin-guru/README.md"

    if not readme_path.exists():
        return  # Skip if file doesn't exist

    with open(readme_path, encoding="utf-8") as f:
        content = f.read()

    # Should use template variable or placeholder
    assert (
        "{user_name}" in content or "[Your Name]" in content or "[User Name]" in content
    ), "README should use template variable for author"

    # Should NOT contain hardcoded personal name
    assert _OWNER_FIRST not in content, (
        "README should not contain hardcoded personal name"
    )


def test_scan_codebase_for_hardcoded_names():
    """Comprehensive scan of codebase for personal name references."""
    project_root = Path(__file__).parent.parent.parent
    violations = []

    # Scan all Python, YAML, MD files
    for ext in ["*.py", "*.yaml", "*.yml", "*.md"]:
        for file_path in project_root.rglob(ext):
            # Skip allowed files
            relative_path = str(file_path.relative_to(project_root))
            if is_allowed_file(relative_path):
                continue

            # Skip this test file itself and the fix script
            if file_path.name in [
                "test_no_hardcoded_references.py",
                "fix_hardcoded_names.py",
            ]:
                continue

            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()

                if _OWNER_FIRST in content:
                    violations.append(relative_path)
            except Exception:
                # Skip files that can't be read
                continue

    if violations:
        error_msg = "\nFound hardcoded personal name in the following files:\n"
        for file_path in violations:
            error_msg += f"  - {file_path}\n"
        error_msg += "\nUse template variables like {user_name} instead\n"
        raise AssertionError(error_msg)


if __name__ == "__main__":
    print("Testing for hardcoded personal name references...")

    try:
        test_no_hardcoded_name_in_critical_files()
        print("PASS: Critical files are clean")
    except AssertionError as e:
        print(f"FAIL: Critical files check failed:\n{e}")
        exit(1)

    try:
        test_config_uses_template_variables()
        print("PASS: Config uses template variables")
    except AssertionError as e:
        print(f"FAIL: Config check failed:\n{e}")
        exit(1)

    try:
        test_workflow_yaml_generic()
        print("PASS: Workflow YAML is generic")
    except AssertionError as e:
        print(f"FAIL: Workflow YAML check failed:\n{e}")
        exit(1)

    try:
        test_readme_generic_author()
        print("PASS: README uses generic author")
    except AssertionError as e:
        print(f"FAIL: README check failed:\n{e}")
        exit(1)

    try:
        test_scan_codebase_for_hardcoded_names()
        print("PASS: Full codebase scan clean")
    except AssertionError as e:
        print(f"FAIL: Codebase scan found violations:\n{e}")
        exit(1)

    print("\nAll tests passed! No hardcoded references found.")
