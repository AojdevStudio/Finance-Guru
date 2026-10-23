"""Product context shared by instance scaffolding and onboarding writers."""

from pathlib import Path

FINANCE_RULES = """Run `date` before analysis. Quote calculator output and pass `--output json`
where offered. Fail closed on missing inputs. Every financial output needs an
educational-only disclaimer, a not investment advice statement, a recommendation
to consult licensed professionals, a risk disclosure, a date and its data source.
Speak to the owner in the second person. Keep private data in this instance."""

LEGACY_SESSION_RULES = """
## Landing the Plane (Session Completion)

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds

Use GitHub Issues or repo docs for follow-up tracking

---
"""


def product_instructions(repo: Path) -> str:
    """Load finance context and retain the instance's financial guardrails."""
    return f"@{repo / '.claude/skills/fin-core/SKILL.md'}\n\n{FINANCE_RULES}"


def migrate_generated_instructions(content: str, repo: Path) -> str | None:
    """Replace a known wizard import while retaining its profile and owner notes."""
    prefix = f"@{repo / 'CLAUDE.md'}\n\n"
    if not content.startswith(prefix + "# CLAUDE.md\n"):
        return None
    heading = "\n## Landing the Plane (Session Completion)\n"
    if heading in content:
        if content.count(heading) != 1 or LEGACY_SESSION_RULES not in content:
            raise FileExistsError(
                "CLAUDE.md has edited legacy developer instructions; "
                "move those instructions aside before rerunning"
            )
        content = content.replace(LEGACY_SESSION_RULES, "", 1)
    return f"{product_instructions(repo)}\n\n{content.removeprefix(prefix)}"
