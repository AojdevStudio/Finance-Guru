"""Contract tests for how the analysis skills route and what they return."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

SKILLS_DIR = Path(__file__).resolve().parents[2] / ".claude" / "skills"

ROUTED_SKILLS = (
    "fin-guru-checklist",
    "fin-guru-compliance-review",
    "fin-guru-create-doc",
    "fin-guru-learner-profile",
    "fin-guru-quant-analysis",
    "fin-guru-research",
    "fin-guru-strategize",
)


def _frontmatter(skill: str) -> dict[str, str]:
    text = (SKILLS_DIR / skill / "SKILL.md").read_text(encoding="utf-8")
    _, frontmatter, _ = text.split("---\n", 2)
    return yaml.safe_load(frontmatter)


def _skill_names() -> set[str]:
    return {
        _frontmatter(path.parent.name)["name"] for path in SKILLS_DIR.glob("*/SKILL.md")
    }


@pytest.mark.parametrize("skill", ROUTED_SKILLS)
def test_description_says_when_to_route_and_where_else_to_go(skill: str) -> None:
    description = _frontmatter(skill)["description"]

    assert "Use when" in description, skill
    not_for = description.split("Not for", 1)
    assert len(not_for) == 2, skill
    alternatives = _fallback_targets(not_for[1])
    assert alternatives, skill
    assert alternatives <= _skill_names(), skill


def _fallback_targets(text: str) -> set[str]:
    """Every skill named in a "(use a or b)" clause, not only the first."""
    return {
        name
        for clause in re.findall(r"\(use ([^)]*)\)", text)
        for name in re.split(r"\s+or\s+|,\s*", clause.strip())
    }


def test_fallback_targets_include_every_alternative() -> None:
    text = "the analysis itself (use fin-guru-research or nonexistent-skill)"

    assert _fallback_targets(text) == {"fin-guru-research", "nonexistent-skill"}
    assert not _fallback_targets(text) <= _skill_names()


REPO_ROOT = SKILLS_DIR.parents[1]
OUTPUT_CONTRACT_SKILLS = (
    "fin-guru-compliance-review",
    "fin-guru-quant-analysis",
    "fin-guru-research",
    "fin-guru-strategize",
)
OUTPUT_JSON_FLAG = re.compile(r'"--output",[^)]*choices=\[[^\]]*"json"', re.S)
CLI_CALL = re.compile(r"uv run python -m (src(?:\.\w+)+)([^\n`]*)")


@pytest.mark.parametrize("skill", OUTPUT_CONTRACT_SKILLS)
def test_analysis_skill_links_the_shared_output_contract(skill: str) -> None:
    text = (SKILLS_DIR / skill / "SKILL.md").read_text(encoding="utf-8")

    assert "](../_shared/AnalysisOutput.md)" in text, skill


def test_every_skill_cli_call_names_a_real_module_and_flag() -> None:
    calls = [
        (path, match)
        for path in SKILLS_DIR.rglob("*.md")
        for match in CLI_CALL.finditer(path.read_text(encoding="utf-8"))
    ]
    assert calls

    for path, match in calls:
        module = REPO_ROOT / Path(*match.group(1).split("."))
        source = module.with_suffix(".py")
        if not source.is_file():
            source = module / "__main__.py"
        assert source.is_file(), f"{path}: {match.group(0)}"
        if "--output json" in match.group(2):
            assert OUTPUT_JSON_FLAG.search(source.read_text(encoding="utf-8")), (
                f"{path}: {match.group(1)} has no --output json choice"
            )


def test_fin_core_lists_every_calculator_cli() -> None:
    fin_core = (SKILLS_DIR / "fin-core" / "SKILL.md").read_text(encoding="utf-8")
    clis = sorted((REPO_ROOT / "src").rglob("*_cli.py"))
    assert clis

    modules = [
        "`" + ".".join(cli.relative_to(REPO_ROOT).with_suffix("").parts) + "`"
        for cli in clis
    ]
    missing = [module for module in modules if module not in fin_core]
    assert not missing, missing
