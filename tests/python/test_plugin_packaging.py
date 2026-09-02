"""Contract tests for the Claude Code marketplace and shared skill surfaces."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGIN_MANIFEST = REPO_ROOT / ".claude-plugin" / "plugin.json"
MARKETPLACE_MANIFEST = REPO_ROOT / ".claude-plugin" / "marketplace.json"
SHARED_PROBE = (
    REPO_ROOT / ".claude" / "skills" / "_shared" / "PaidMcpCapabilityProbe.md"
)

MCP_SKILLS = {
    "FinanceReport",
    "fin-guru-compliance-review",
    "fin-guru-create-doc",
    "fin-guru-quant-analysis",
    "fin-guru-research",
    "fin-guru-strategize",
}
MCP_AGENTS = {
    "fg-builder.md",
    "fg-compliance-officer.md",
    "fg-dividend-specialist.md",
    "fg-market-researcher.md",
    "fg-quant-analyst.md",
    "fg-strategy-advisor.md",
}


def _json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_plugin_manifest_exposes_the_canonical_component_trees() -> None:
    manifest = _json(PLUGIN_MANIFEST)

    assert manifest["name"] == "finance-guru"
    assert manifest["version"] == "2.3.0"
    assert manifest["license"] == "AGPL-3.0-only"
    expected_commands = {
        f"./{path.relative_to(REPO_ROOT)}"
        for path in (REPO_ROOT / ".claude" / "commands").rglob("*.md")
    }
    expected_agents = {
        f"./{path.relative_to(REPO_ROOT)}"
        for path in (REPO_ROOT / ".claude" / "agents").glob("*.md")
    }
    assert set(manifest["commands"]) == expected_commands
    assert set(manifest["agents"]) == expected_agents

    skill_paths = set(manifest["skills"])
    expected_paths = {
        f"./.claude/skills/{path.parent.name}"
        for path in (REPO_ROOT / ".claude" / "skills").glob("*/SKILL.md")
    }
    assert skill_paths == expected_paths
    for relative_path in skill_paths:
        assert (REPO_ROOT / relative_path / "SKILL.md").is_file()


def test_marketplace_points_at_the_same_root_and_version() -> None:
    marketplace = _json(MARKETPLACE_MANIFEST)
    plugins = marketplace["plugins"]

    assert marketplace["name"] == "finance-guru"
    assert len(plugins) == 1
    assert plugins[0]["name"] == "finance-guru"
    assert plugins[0]["source"] == "."
    assert plugins[0]["version"] == "2.3.0"


def test_six_skills_and_six_agents_run_the_shared_capability_probe() -> None:
    assert SHARED_PROBE.is_file()
    assert "Never omit a research step silently" in SHARED_PROBE.read_text(
        encoding="utf-8"
    )

    for skill in MCP_SKILLS:
        content = (REPO_ROOT / ".claude" / "skills" / skill / "SKILL.md").read_text(
            encoding="utf-8"
        )
        assert "capability probe" in content.lower()
        assert "../_shared/PaidMcpCapabilityProbe.md" in content

    for agent in MCP_AGENTS:
        content = (REPO_ROOT / ".claude" / "agents" / agent).read_text(encoding="utf-8")
        assert "capability probe" in content.lower()
        assert "../skills/_shared/PaidMcpCapabilityProbe.md" in content


def test_onboarding_skill_covers_the_first_instance_run() -> None:
    content = (
        REPO_ROOT / ".claude" / "skills" / "instance-onboarding" / "SKILL.md"
    ).read_text(encoding="utf-8")

    required_fragments = (
        "uv run python -m src.cli.instance_init",
        '--repo "${CLAUDE_PLUGIN_ROOT}"',
        "user-profile.yaml",
        '"<instance-root>/imports/"',
        "uv run python -m src.integrations.refresh_all --show",
        "start every future Finance Guru session from the instance",
    )
    for fragment in required_fragments:
        assert fragment in content


def test_root_agents_instructions_explain_instance_skill_discovery() -> None:
    content = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")

    assert "[Codex Instance Skill Discovery]" in content
    assert "./.agents/skills" in content
    assert "single `.claude` tree" in content
