"""
Test: Verify No Hardcoded "Ossie" References

This test ensures that Finance Guru has been properly genericized
and does not contain hardcoded references to "Ossie" that would
prevent distribution to other users.

Acceptance Criteria:
- Config files use template variables ({user_name}) instead of "Ossie"
- README and docs use placeholders for author name
- Only allowed locations: LICENSE, git history, migration specs
"""

import os
import re
from pathlib import Path


# Files/directories that are ALLOWED to contain "Ossie"
ALLOWED_FILES = {
    "LICENSE",  # Copyright holder
    ".git/",  # Git history
    ".beads/specs/",  # Migration specs documenting the transition
    "specs/",  # Spec docs describing migration process
    "fin-guru/distribution-plan.md",  # Distribution planning doc
    "fin-guru/tasks/",  # Task files with examples
    "specs/archive/",  # Archived specs
    "fin-guru-private/",  # Private data directory (not distributed)
    "notebooks/",  # Private notebooks (not distributed)
}

# Files that MUST NOT contain "Ossie"
CRITICAL_FILES = [
    "fin-guru/config.yaml",
    "fin-guru/workflows/workflow.yaml",
    "fin-guru/README.md",
]


def is_allowed_file(file_path: str) -> bool:
    """Check if a file is allowed to contain 'Ossie'."""
    for allowed in ALLOWED_FILES:
        if allowed in file_path:
            return True
    return False


def test_no_hardcoded_ossie_in_critical_files():
    """Verify critical config files use template variables, not 'Ossie'."""
    project_root = Path(__file__).parent.parent.parent

    for file_path in CRITICAL_FILES:
        full_path = project_root / file_path

        if not full_path.exists():
            continue

        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for "Ossie" (case-sensitive)
        if "Ossie" in content:
            # Find line numbers
            lines_with_ossie = []
            for i, line in enumerate(content.split('\n'), 1):
                if "Ossie" in line:
                    lines_with_ossie.append((i, line.strip()))

            error_msg = f"\n❌ Found hardcoded 'Ossie' in {file_path}:\n"
            for line_num, line_content in lines_with_ossie:
                error_msg += f"  Line {line_num}: {line_content}\n"
            error_msg += "\n💡 Replace with template variable: {user_name}\n"

            raise AssertionError(error_msg)


def test_config_uses_template_variables():
    """Verify config.yaml uses {user_name} template variable."""
    project_root = Path(__file__).parent.parent.parent
    config_path = project_root / "fin-guru/config.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Should contain template variable
    assert "{user_name}" in content or "user_name:" in content, \
        "config.yaml should use {user_name} template variable"

    # Should NOT contain hardcoded "Ossie"
    assert "Ossie" not in content, \
        "config.yaml should not contain hardcoded 'Ossie'"


def test_workflow_yaml_generic():
    """Verify workflow.yaml does not hardcode 'Ossie'."""
    project_root = Path(__file__).parent.parent.parent
    workflow_path = project_root / "fin-guru/workflows/workflow.yaml"

    if not workflow_path.exists():
        return  # Skip if file doesn't exist

    with open(workflow_path, 'r', encoding='utf-8') as f:
        content = f.read()

    assert "Ossie" not in content, \
        "workflow.yaml should not contain hardcoded 'Ossie'"


def test_readme_generic_author():
    """Verify README uses generic author placeholder."""
    project_root = Path(__file__).parent.parent.parent
    readme_path = project_root / "fin-guru/README.md"

    if not readme_path.exists():
        return  # Skip if file doesn't exist

    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Should use template variable or placeholder
    assert "{user_name}" in content or "[Your Name]" in content or "[User Name]" in content, \
        "README should use template variable for author"

    # Should NOT contain hardcoded "Ossie"
    assert "Ossie" not in content, \
        "README should not contain hardcoded 'Ossie'"


def test_scan_codebase_for_hardcoded_names():
    """Comprehensive scan of codebase for 'Ossie' references."""
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
            if file_path.name in ["test_no_hardcoded_references.py", "fix_hardcoded_names.py"]:
                continue

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                if "Ossie" in content:
                    violations.append(relative_path)
            except Exception:
                # Skip files that can't be read
                continue

    if violations:
        error_msg = "\n❌ Found hardcoded 'Ossie' in the following files:\n"
        for file_path in violations:
            error_msg += f"  • {file_path}\n"
        error_msg += "\n💡 Use template variables like {user_name} instead\n"
        raise AssertionError(error_msg)


if __name__ == "__main__":
    print("🧪 Testing for hardcoded 'Ossie' references...")

    try:
        test_no_hardcoded_ossie_in_critical_files()
        print("✅ Critical files are clean")
    except AssertionError as e:
        print(f"❌ Critical files check failed:\n{e}")
        exit(1)

    try:
        test_config_uses_template_variables()
        print("✅ Config uses template variables")
    except AssertionError as e:
        print(f"❌ Config check failed:\n{e}")
        exit(1)

    try:
        test_workflow_yaml_generic()
        print("✅ Workflow YAML is generic")
    except AssertionError as e:
        print(f"❌ Workflow YAML check failed:\n{e}")
        exit(1)

    try:
        test_readme_generic_author()
        print("✅ README uses generic author")
    except AssertionError as e:
        print(f"❌ README check failed:\n{e}")
        exit(1)

    try:
        test_scan_codebase_for_hardcoded_names()
        print("✅ Full codebase scan clean")
    except AssertionError as e:
        print(f"❌ Codebase scan found violations:\n{e}")
        exit(1)

    print("\n✅ All tests passed! No hardcoded references found.")
