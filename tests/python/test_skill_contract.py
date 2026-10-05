"""Contract tests for how the analysis skills route and what they return."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

SKILLS_DIR = Path(__file__).resolve().parents[2] / ".claude" / "skills"

ANALYSIS_SKILLS = (
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


@pytest.mark.parametrize("skill", ANALYSIS_SKILLS)
def test_description_says_when_to_route_and_where_else_to_go(skill: str) -> None:
    description = _frontmatter(skill)["description"]

    assert "Use when" in description, skill
    not_for = description.split("Not for", 1)
    assert len(not_for) == 2, skill
    alternatives = re.findall(r"use ([a-z][a-z0-9-]+)", not_for[1])
    assert alternatives, skill
    assert set(alternatives) <= _skill_names(), skill
