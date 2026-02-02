#!/usr/bin/env python3
"""
Report Generator for Agent Readiness

Generates formatted markdown reports from analysis JSON.

Usage:
    python generate_report.py --analysis-file /tmp/readiness_analysis.json
    python generate_report.py --analysis-file /tmp/readiness_analysis.json --format markdown
"""

import argparse
import json
from pathlib import Path


def format_level_bar(level_scores: dict, achieved: int) -> str:
    """Generate a visual level progress bar."""
    bars = []
    for level in range(1, 6):
        score = level_scores.get(str(level), level_scores.get(level, 0))
        if level <= achieved:
            indicator = "█" * 4
            status = f"L{level} {score:.0f}%"
        else:
            indicator = "░" * 4
            status = f"L{level} {score:.0f}%"
        bars.append(f"{indicator} {status}")
    return " | ".join(bars)


def format_criterion_row(criterion: dict) -> str:
    """Format a single criterion as a table row."""
    status = criterion["status"]
    crit_id = criterion["id"]
    score = criterion["score"]
    reason = criterion["reason"]
    
    if status == "pass":
        icon = "✓"
    elif status == "fail":
        icon = "✗"
    else:  # skip
        icon = "—"
    
    return f"{icon} `{crit_id}` | {score} | {reason}"


def get_top_strengths(data: dict, n: int = 3) -> list[tuple[str, int, list[str]]]:
    """Get top performing pillars with example passing criteria."""
    pillar_scores = []
    for pillar_name, pillar in data["pillars"].items():
        if pillar["total"] > 0:
            pct = pillar["percentage"]
            passing = [c["id"] for c in pillar["criteria"] if c["status"] == "pass"][:3]
            pillar_scores.append((pillar_name, pct, passing))
    
    # Sort by percentage descending
    pillar_scores.sort(key=lambda x: x[1], reverse=True)
    return pillar_scores[:n]


def get_top_opportunities(data: dict, n: int = 5) -> list[tuple[str, str, str]]:
    """Get highest priority improvement opportunities."""
    opportunities = []
    
    # Prioritize by level (lower levels first), then by pillar importance
    for pillar_name, pillar in data["pillars"].items():
        for criterion in pillar["criteria"]:
            if criterion["status"] == "fail":
                opportunities.append((
                    criterion["id"],
                    criterion["level"],
                    criterion["reason"],
                    pillar_name
                ))
    
    # Sort by level (ascending) to prioritize foundational issues
    opportunities.sort(key=lambda x: x[1])
    return [(o[0], o[2], o[3]) for o in opportunities[:n]]


def generate_markdown_report(data: dict) -> str:
    """Generate a full markdown report from analysis data."""
    repo_name = data["repo_name"]
    pass_rate = data["pass_rate"]
    achieved = data["achieved_level"]
    total_passed = data["total_passed"]
    total = data["total_criteria"]
    languages = data.get("languages", ["Unknown"])
    repo_type = data.get("repo_type", "application")
    level_scores = data["level_scores"]
    
    lines = []
    
    # Header
    lines.append(f"# Agent Readiness Report: {repo_name}")
    lines.append("")
    lines.append(f"**Languages**: {', '.join(languages)}  ")
    lines.append(f"**Repository Type**: {repo_type}  ")
    lines.append(f"**Pass Rate**: {pass_rate}% ({total_passed}/{total} criteria)  ")
    if achieved > 0:
        lines.append(f"**Achieved Level**: **L{achieved}**")
    else:
        lines.append(f"**Achieved Level**: **Not yet L1** (need 80% at L1)")
    lines.append("")
    
    # Level Progress
    lines.append("## Level Progress")
    lines.append("")
    lines.append("| Level | Score | Status |")
    lines.append("|-------|-------|--------|")
    for level in range(1, 6):
        score = level_scores.get(str(level), level_scores.get(level, 0))
        if achieved > 0 and level <= achieved:
            status = "✅ Achieved"
        elif score >= 80:
            status = "✅ Passed"
        else:
            status = f"⬜ {100-score:.0f}% to go"
        lines.append(f"| L{level} | {score:.0f}% | {status} |")
    lines.append("")
    
    # Summary
    lines.append("## Summary")
    lines.append("")
    
    # Strengths
    strengths = get_top_strengths(data)
    if strengths:
        lines.append("### Strengths")
        lines.append("")
        for pillar_name, pct, passing in strengths:
            if passing:
                passing_str = ", ".join(f"`{p}`" for p in passing)
                lines.append(f"- **{pillar_name}** ({pct}%): {passing_str}")
            else:
                lines.append(f"- **{pillar_name}** ({pct}%)")
        lines.append("")
    
    # Opportunities
    opportunities = get_top_opportunities(data)
    if opportunities:
        lines.append("### Priority Improvements")
        lines.append("")
        lines.append("| Criterion | Issue | Pillar |")
        lines.append("|-----------|-------|--------|")
        for crit_id, reason, pillar in opportunities:
            lines.append(f"| `{crit_id}` | {reason} | {pillar} |")
        lines.append("")
    
    # Detailed Results
    lines.append("## Detailed Results")
    lines.append("")
    
    for pillar_name, pillar in data["pillars"].items():
        pct = pillar["percentage"]
        passed = pillar["passed"]
        total = pillar["total"]
        
        lines.append(f"### {pillar_name}")
        lines.append(f"**Score**: {passed}/{total} ({pct}%)")
        lines.append("")
        lines.append("| Status | Criterion | Score | Details |")
        lines.append("|--------|-----------|-------|---------|")
        
        for criterion in pillar["criteria"]:
            status = criterion["status"]
            if status == "pass":
                icon = "✓"
            elif status == "fail":
                icon = "✗"
            else:
                icon = "—"
            
            crit_id = criterion["id"]
            score = criterion["score"]
            reason = criterion["reason"]
            lines.append(f"| {icon} | `{crit_id}` | {score} | {reason} |")
        
        lines.append("")
    
    # Recommendations
    lines.append("## Recommended Next Steps")
    lines.append("")
    
    if achieved < 2:
        lines.append("**Focus on L1/L2 Foundations:**")
        lines.append("1. Add missing linter and formatter configurations")
        lines.append("2. Document build and test commands in README")
        lines.append("3. Set up pre-commit hooks for fast feedback")
        lines.append("4. Create AGENTS.md with project context for AI agents")
    elif achieved < 3:
        lines.append("**Progress to L3 (Production Ready):**")
        lines.append("1. Add integration/E2E tests")
        lines.append("2. Set up test coverage thresholds")
        lines.append("3. Configure devcontainer for reproducible environments")
        lines.append("4. Add automated PR review tooling")
    else:
        lines.append("**Optimize for L4+:**")
        lines.append("1. Implement complexity analysis and dead code detection")
        lines.append("2. Set up flaky test detection and quarantine")
        lines.append("3. Add security scanning (CodeQL, Snyk)")
        lines.append("4. Configure deployment observability")
    
    lines.append("")
    lines.append("---")
    lines.append(f"*Report generated from repository analysis*")
    
    return "\n".join(lines)


def generate_brief_report(data: dict) -> str:
    """Generate a brief summary report."""
    repo_name = data["repo_name"]
    pass_rate = data["pass_rate"]
    achieved = data["achieved_level"]
    total_passed = data["total_passed"]
    total = data["total_criteria"]
    
    lines = []
    lines.append(f"## Agent Readiness: {repo_name}")
    lines.append("")
    level_str = f"Level {achieved}" if achieved > 0 else "Not yet L1"
    lines.append(f"**{level_str}** | {pass_rate}% ({total_passed}/{total})")
    lines.append("")
    
    # Quick level summary
    for level in range(1, 6):
        score = data["level_scores"].get(str(level), data["level_scores"].get(level, 0))
        bar = "█" * int(score / 10) + "░" * (10 - int(score / 10))
        check = "✅" if achieved > 0 and level <= achieved else "⬜"
        lines.append(f"L{level} {check} [{bar}] {score:.0f}%")
    
    lines.append("")
    
    # Top opportunities
    opps = get_top_opportunities(data, 3)
    if opps:
        lines.append("**Quick Wins:**")
        for crit_id, reason, _ in opps:
            lines.append(f"- {crit_id}: {reason}")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Generate Agent Readiness report from analysis"
    )
    parser.add_argument(
        "--analysis-file", "-a",
        default="/tmp/readiness_analysis.json",
        help="Path to analysis JSON file"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file (default: stdout)"
    )
    parser.add_argument(
        "--format", "-f",
        choices=["markdown", "brief", "json"],
        default="markdown",
        help="Output format"
    )
    
    args = parser.parse_args()
    
    # Load analysis
    analysis_path = Path(args.analysis_file)
    if not analysis_path.exists():
        print(f"❌ Analysis file not found: {args.analysis_file}")
        print("Run analyze_repo.py first to generate the analysis.")
        return 1
    
    data = json.loads(analysis_path.read_text())
    
    # Generate report
    if args.format == "markdown":
        report = generate_markdown_report(data)
    elif args.format == "brief":
        report = generate_brief_report(data)
    else:  # json
        report = json.dumps(data, indent=2)
    
    # Output
    if args.output:
        Path(args.output).write_text(report)
        print(f"✅ Report saved to: {args.output}")
    else:
        print(report)
    
    return 0


if __name__ == "__main__":
    exit(main())
