# Phase 5: Agent Readiness Hardening - Context

**Gathered:** 2026-02-12
**Status:** Ready for planning

<domain>
## Phase Boundary

Elevate the repository to L2 agent readiness with linter enforcement, expanded pre-commit hooks (via pre-commit framework), GitHub issue/PR templates, test coverage thresholds, and a CODEOWNERS file. Derived from the agent-readiness report (2026-02-02). This phase hardens tooling — no new features, no setup.sh rewrites, no new CLI tools.

</domain>

<decisions>
## Implementation Decisions

### Linter strictness
- Aggressive ruff rule set: E + F + I + UP + W + B + SIM + C90 + N + D
- Full docstring and naming enforcement — one-time cleanup pass, then enforced forever
- Auto-fix safe rules on commit (import sorting, unused imports, simple style)
- Line length: Claude's discretion (will match existing black config)

### Pre-commit hook scope
- Use the `pre-commit` framework (`.pre-commit-config.yaml`), not raw git hooks
- Hooks on every commit: ruff (with auto-fix), mypy (standard mode on changed files), gitleaks
- mypy configured in standard mode everywhere (not strict) — catches obvious type errors without requiring full annotations
- setup.sh auto-installs hooks via `pre-commit install` during first-run setup
- Tests do NOT run in pre-commit — reserved for CI

### GitHub templates & workflow
- Bug report template: YAML form format with steps to reproduce, expected vs actual behavior, environment (Python version, OS)
- Feature request template: YAML form format with problem statement, proposed solution, alternatives considered (simple)
- PR template: summary bullets + test plan + review checklist (tests pass, lint clean, docs updated)

### Coverage strategy
- 80% floor enforced in BOTH pre-commit and CI (`pytest --cov=src --cov-fail-under=80`)
- Exclude CLI entry points (`*_cli.py`) from coverage measurement — thin argparse wrappers, not core logic
- Ratchet vs floor: Claude's discretion based on current coverage level
- CI generates a coverage badge for the README

### Claude's Discretion
- Line length for ruff (likely 88 to match existing black config)
- Coverage ratchet decision based on where current coverage sits
- mypy per-module overrides if specific modules cause noise
- CODEOWNERS mapping strategy (simple owner for src/ and tests/)
- Exact pre-commit hook versions and parallel execution config

</decisions>

<specifics>
## Specific Ideas

- User wants aggressive linting — "if Opus can handle it, go aggressive"
- Coverage enforcement on pre-commit too, not just CI — higher friction accepted for stronger guarantees
- YAML form format for GitHub templates (structured dropdowns, required fields)
- Auto-fix safe lint rules to reduce developer friction on commits

</specifics>

<deferred>
## Deferred Ideas

- Port setup.sh to TypeScript (Bun) — suggested during discussion, captured for future phase or backlog
- CI/CD pipeline beyond linting (deployment, release automation) — out of scope

</deferred>

---

_Phase: 05-agent-readiness-hardening_
_Context gathered: 2026-02-12_
