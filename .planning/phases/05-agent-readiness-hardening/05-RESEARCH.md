# Phase 5: Agent Readiness Hardening - Research

**Researched:** 2026-02-05
**Domain:** Python linting, pre-commit hooks, GitHub templates, test coverage, CODEOWNERS
**Confidence:** HIGH

## Summary

Phase 5 adds five standard DevOps/DX tooling components: ruff linter configuration, pre-commit hooks (ruff + mypy + gitleaks), GitHub issue/PR templates, pytest coverage thresholds, and a CODEOWNERS file. All five are well-documented, standard-pattern tools with no ambiguity in implementation.

The codebase currently has 84 ruff lint errors (60 in src/, 24 in tests/), 50 mypy errors, and _20% test coverage_ against an 80% target. The coverage gap is the dominant challenge of this phase -- closing it from 20% to 80% requires covering approximately 3,400 additional statements across ~25 uncovered modules. Lint errors are mostly auto-fixable (F401 unused imports) or suppressible via per-file-ignores (E402 in CLI scripts that use sys.path manipulation).

The project uses `uv` for package management. Pre-commit should be installed via `uv tool install pre-commit --with pre-commit-uv` for optimal integration. Mypy pre-commit hooks should use the `local` hook pattern with `language: system` to avoid maintaining duplicate dependency lists.

**Primary recommendation:** Tackle coverage gap first (largest effort), then configure ruff + pre-commit (most auto-fixable), then templates and CODEOWNERS (copy-paste patterns).

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| ruff | >=0.14.14 | Python linter (replaces flake8/isort/pyflakes) | Astral-maintained, extremely fast, all-in-one linter |
| pre-commit | latest | Git hook framework | De facto standard for Python projects |
| pre-commit-uv | latest | uv integration for pre-commit | Speeds up hook installs, uses uv resolver |
| pytest-cov | >=7.0.0 | Coverage measurement | Already in dev deps, wraps coverage.py |
| mypy | >=1.13.0 | Static type checking | Already in dev deps (v1.19.1 available) |
| gitleaks | v8.30.0 | Secret scanning | Standard secret detection tool |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| ruff-pre-commit | v0.15.0 | Pre-commit hook for ruff | In .pre-commit-config.yaml for ruff linting |
| mirrors-mypy | v1.19.1 | Pre-commit mirror for mypy | NOT recommended -- use local hook instead |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| ruff | flake8 + isort + pyflakes | ruff replaces all three, 10-100x faster |
| pre-commit-uv | plain pre-commit | pre-commit-uv uses uv for faster installs |
| local mypy hook | mirrors-mypy | Local hook avoids maintaining additional_dependencies |
| ruff formatter | black | Keep black -- project already uses it, ruff format is not byte-identical |

**Installation:**
```bash
# Add ruff to dev dependencies
uv add --dev ruff

# Install pre-commit globally with uv integration
uv tool install pre-commit --with pre-commit-uv --force-reinstall

# Install hooks after config is written
pre-commit install
```

## Architecture Patterns

### File Structure for New Files
```
.github/
  ISSUE_TEMPLATE/
    bug-report.yml         # Bug report issue form
    feature-request.yml    # Feature request issue form
    config.yml             # Template chooser configuration
  pull_request_template.md # PR template
  CODEOWNERS               # Or place in repo root
.pre-commit-config.yaml    # Pre-commit hook configuration
pyproject.toml             # Add [tool.ruff] and [tool.ruff.lint] sections
```

### Pattern 1: Ruff Configuration in pyproject.toml
**What:** Configure ruff linting rules alongside existing tool configs
**When to use:** Always -- pyproject.toml is the standard location for Python tool config
**Example:**
```toml
# Source: https://docs.astral.sh/ruff/configuration/
[tool.ruff]
target-version = "py312"
line-length = 88

[tool.ruff.lint]
select = ["E", "F", "W", "I", "UP", "B"]
ignore = []

[tool.ruff.lint.per-file-ignores]
"src/*_cli.py" = ["E402"]  # CLI scripts use sys.path before imports
"tests/**" = ["E402"]
```

### Pattern 2: Local Mypy Hook (Not mirrors-mypy)
**What:** Use `language: system` to run mypy from the project venv
**When to use:** When your project has many typed dependencies (pydantic, etc.)
**Why:** Avoids maintaining a parallel `additional_dependencies` list in pre-commit config
**Example:**
```yaml
# Source: https://jaredkhan.com/blog/mypy-pre-commit
- repo: local
  hooks:
    - id: mypy
      name: mypy
      entry: uv run mypy
      language: system
      types: [python]
      args: ["--ignore-missing-imports"]
```

### Pattern 3: GitHub Issue Forms (YAML, not Markdown)
**What:** YAML-based issue templates with structured form fields
**When to use:** For bug reports and feature requests (modern GitHub approach)
**Why:** YAML forms produce structured, consistent issues vs freeform markdown
**Example:**
```yaml
# Source: https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms
name: Bug Report
description: File a bug report
title: "[Bug]: "
labels: ["bug", "triage"]
body:
  - type: textarea
    id: what-happened
    attributes:
      label: What happened?
    validations:
      required: true
```

### Anti-Patterns to Avoid
- **Using mirrors-mypy with additional_dependencies:** Maintaining a duplicate dependency list that drifts from pyproject.toml. Use local hook with `language: system` instead.
- **Running ruff format alongside black:** They produce near-identical but not byte-identical output. Keep black for formatting, use ruff only for linting.
- **Ignoring E402 globally:** Only suppress in files that genuinely need sys.path manipulation (CLI scripts). Do not blanket-ignore.
- **Setting coverage threshold without actually having coverage:** Configure the threshold but also write the tests -- do not just set `--cov-fail-under=80` without closing the gap.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Linting | Custom flake8 + isort + pyflakes config | ruff with single config | ruff replaces them all, single tool, faster |
| Git hooks | Shell scripts in .git/hooks/ | pre-commit framework | Portable, versionable, auto-installs tools |
| Secret scanning | grep for patterns | gitleaks | Comprehensive pattern database, maintained |
| Coverage enforcement | CI scripts checking numbers | pytest-cov `--cov-fail-under` | Built-in, exits non-zero on failure |
| Issue templates | Markdown templates | YAML issue forms | Structured fields, validation, dropdowns |

**Key insight:** All five components in this phase are solved problems with standard tools. The effort is in configuration and test writing, not tool selection.

## Common Pitfalls

### Pitfall 1: E402 in CLI Scripts
**What goes wrong:** ruff reports `E402 module-import-not-at-top-of-file` in every CLI script
**Why it happens:** CLI files use `sys.path.insert(0, str(project_root))` before imports
**How to avoid:** Use `per-file-ignores` in ruff config to suppress E402 for `*_cli.py` patterns
**Warning signs:** 42 E402 errors in src/ -- all from CLI scripts
**Current state:** 42 E402 errors in src/analysis/*_cli.py, src/utils/*_cli.py, src/strategies/*_cli.py

### Pitfall 2: Coverage Gap Underestimation
**What goes wrong:** Setting `--cov-fail-under=80` when coverage is only 20%
**Why it happens:** Assumes existing tests cover enough, or that the threshold is "just config"
**How to avoid:** Plan substantial test writing effort _before_ enabling the threshold
**Warning signs:** Current coverage is 20% (1,184 of 5,779 statements). Need ~3,400 more covered statements.
**Coverage breakdown of 0% modules:**
- `backtester.py` (148 stmts), `backtester_cli.py` (188 stmts)
- `optimizer.py` (208 stmts), `optimizer_cli.py` (199 stmts)
- `data_validator.py` (156 stmts), `data_validator_cli.py` (166 stmts)
- `market_data.py` (98 stmts), `momentum.py` (103 stmts), `momentum_cli.py` (228 stmts)
- `moving_averages.py` (118 stmts), `moving_averages_cli.py` (296 stmts)
- `screener.py` (267 stmts), `screener_cli.py` (186 stmts)
- `volatility.py` (74 stmts), `volatility_cli.py` (131 stmts)
- `yaml_generator_cli.py` (91 stmts), `input_validation_cli.py` (105 stmts)
- `correlation.py`, `correlation_cli.py`, `risk_metrics.py`, `risk_metrics_cli.py`, `itc_risk_cli.py`
- `ui/app.py` (222 stmts)

### Pitfall 3: Pre-commit + Mypy Isolated Environment
**What goes wrong:** Mypy hook fails because it cannot import project dependencies (pydantic, pandas, etc.)
**Why it happens:** pre-commit runs hooks in isolated virtualenvs by default
**How to avoid:** Use `repo: local` with `language: system` for mypy hook, so it runs from the project venv
**Warning signs:** mypy errors like "Cannot find implementation or library stub for module X"

### Pitfall 4: Pre-commit Not Installed in Git Hooks
**What goes wrong:** .pre-commit-config.yaml exists but hooks never run
**Why it happens:** `pre-commit install` was never run, or was run before config existed
**How to avoid:** Run `pre-commit install` after writing config. Verify `.git/hooks/pre-commit` exists and is not a `.sample` file. Document this in setup instructions.
**Warning signs:** All .git/hooks/ files currently end in `.sample`

### Pitfall 5: Ruff + Black Conflict
**What goes wrong:** ruff and black disagree on formatting, causing endless reformatting loops
**Why it happens:** Both tools have formatting opinions; ruff linting rules like quote-style or trailing commas can conflict with black
**How to avoid:** Use ruff ONLY for linting, not formatting. Keep black as the formatter. Ruff docs confirm they are "not intended to be used interchangeably."
**Warning signs:** If `ruff format` is added to pre-commit alongside black

### Pitfall 6: CODEOWNERS Pattern Matching
**What goes wrong:** CODEOWNERS patterns do not match expected files
**Why it happens:** Last matching pattern wins (not first). Patterns are case-sensitive. Must use GitHub usernames/teams.
**How to avoid:** Keep patterns simple. Test by checking PR auto-assignment after creating the file.
**Warning signs:** PRs not auto-assigning reviewers

## Code Examples

Verified patterns from official sources:

### Ruff Configuration in pyproject.toml
```toml
# Source: https://docs.astral.sh/ruff/configuration/
[tool.ruff]
target-version = "py312"
line-length = 88
exclude = [
    ".venv",
    "notebooks",
    ".claude",
]

[tool.ruff.lint]
# E = pycodestyle errors, F = pyflakes, W = warnings, I = isort, UP = pyupgrade, B = bugbear
select = ["E", "F", "W", "I", "UP", "B"]
ignore = [
    "E501",  # line too long (handled by black)
]

[tool.ruff.lint.per-file-ignores]
# CLI scripts use sys.path.insert before imports
"src/**/*_cli.py" = ["E402"]
"tests/**" = ["E402"]
```

### .pre-commit-config.yaml
```yaml
# Source: https://pre-commit.com/ and https://docs.astral.sh/ruff/integrations/
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.15.0
    hooks:
      - id: ruff
        args: [--fix]

  - repo: local
    hooks:
      - id: mypy
        name: mypy
        entry: uv run mypy
        language: system
        types: [python]
        args: ["--ignore-missing-imports"]
        pass_filenames: false

  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.30.0
    hooks:
      - id: gitleaks
```

### pytest Coverage Configuration in pyproject.toml
```toml
# Source: pytest-cov documentation
[tool.pytest.ini_options]
testpaths = ["tests/python"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
addopts = "-v --tb=short --cov=src --cov-fail-under=80 --cov-report=term-missing"
pythonpath = ["."]
markers = [
    "integration: marks tests as integration tests (require real API keys)",
]
```

### Bug Report Issue Template (.github/ISSUE_TEMPLATE/bug-report.yml)
```yaml
# Source: https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms
name: Bug Report
description: File a bug report
title: "[Bug]: "
labels: ["bug", "triage"]
body:
  - type: markdown
    attributes:
      value: |
        Thank you for reporting a bug. Please fill out the information below.
  - type: textarea
    id: what-happened
    attributes:
      label: What happened?
      description: Describe the bug clearly.
      placeholder: A clear description of the issue...
    validations:
      required: true
  - type: textarea
    id: expected-behavior
    attributes:
      label: Expected behavior
      description: What did you expect to happen?
    validations:
      required: true
  - type: textarea
    id: reproduction
    attributes:
      label: Steps to reproduce
      description: How can we reproduce this issue?
      placeholder: |
        1. Run '...'
        2. See error...
    validations:
      required: true
  - type: input
    id: version
    attributes:
      label: Python version
      placeholder: "3.12"
  - type: textarea
    id: logs
    attributes:
      label: Relevant log output
      render: shell
```

### Feature Request Issue Template (.github/ISSUE_TEMPLATE/feature-request.yml)
```yaml
name: Feature Request
description: Suggest a new feature or enhancement
title: "[Feature]: "
labels: ["enhancement"]
body:
  - type: textarea
    id: problem
    attributes:
      label: Problem or motivation
      description: What problem does this solve?
    validations:
      required: true
  - type: textarea
    id: solution
    attributes:
      label: Proposed solution
      description: How should this work?
    validations:
      required: true
  - type: textarea
    id: alternatives
    attributes:
      label: Alternatives considered
      description: What alternatives have you considered?
```

### PR Template (.github/pull_request_template.md)
```markdown
## Description

<!-- What does this PR do? Why? -->

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Enhancement to existing feature
- [ ] Refactoring
- [ ] Documentation
- [ ] Tests

## Test Plan

<!-- How did you test this? -->

- [ ] Unit tests added/updated
- [ ] Manual testing performed
- [ ] Existing tests pass (`uv run pytest`)

## Checklist

- [ ] Code follows project conventions
- [ ] Linter passes (`uv run ruff check src/ tests/`)
- [ ] Type checker passes (`uv run mypy src/`)
- [ ] Tests pass (`uv run pytest`)
- [ ] Documentation updated (if needed)
```

### CODEOWNERS
```
# Source: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners
# Default owner for everything
* @AojdevStudio

# Source code
/src/ @AojdevStudio
/tests/ @AojdevStudio
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| flake8 + isort + pyflakes | ruff | 2023+ | Single tool, 10-100x faster, unified config |
| Markdown issue templates | YAML issue forms | 2021+ | Structured inputs, validation, better UX |
| .git/hooks/ shell scripts | pre-commit framework | 2017+ | Portable, versionable, language-agnostic |
| pip install pre-commit | uv tool install pre-commit --with pre-commit-uv | 2024+ | Faster installs, uv-native resolution |

**Deprecated/outdated:**
- flake8: Replaced by ruff for new projects. ruff implements all flake8 rules natively.
- Markdown issue templates (.md files in ISSUE_TEMPLATE/): Still work, but YAML forms (.yml) are preferred for structured input.
- mirrors-mypy pre-commit hook: Works but forces maintaining additional_dependencies. Local hook with `language: system` is simpler.

## Open Questions

Things that could not be fully resolved:

1. **Coverage strategy for 20% to 80%**
   - What we know: 3,400+ statements need coverage across ~25 modules with 0% coverage. Most are CLI scripts and analysis tools that call external APIs (yfinance, market data).
   - What is unclear: Whether to mock external calls, test CLI scripts via subprocess, or focus on core library functions. Whether some modules should be excluded from coverage (e.g., ui/app.py which is a Streamlit app).
   - Recommendation: Focus on testing core library modules first (analysis/, strategies/, utils/), mock external API calls, consider excluding `ui/app.py` and pure-CLI entrypoints from coverage with `--cov-config` omit patterns. If 80% remains unreachable, the planner should flag this as a potential scope issue.

2. **Pre-commit installation in CI**
   - What we know: pre-commit must be installed locally for git hooks and can also run in CI.
   - What is unclear: Whether to add a CI workflow that runs `pre-commit run --all-files`, or rely solely on local hooks.
   - Recommendation: Local hooks are sufficient for Phase 5. CI integration is a future enhancement.

3. **Mypy strictness level for pre-commit**
   - What we know: mypy currently finds 50 errors with `--ignore-missing-imports`. Pre-commit hook should match current strictness.
   - What is unclear: Whether to fix all 50 errors in this phase or suppress them.
   - Recommendation: Start with `--ignore-missing-imports` flag in the hook. Fixing mypy errors is separate from configuring the hook to run.

## Sources

### Primary (HIGH confidence)
- Ruff official docs: https://docs.astral.sh/ruff/configuration/ -- configuration format, rule categories, per-file-ignores
- Ruff official docs: https://docs.astral.sh/ruff/rules/ -- rule prefix codes (E, F, W, I, UP, B, S)
- Ruff official docs: https://docs.astral.sh/ruff/formatter/#black-compatibility -- ruff vs black compatibility
- GitHub Docs: https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms -- YAML issue form syntax
- GitHub Docs: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners -- CODEOWNERS syntax
- GitHub Docs: https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/creating-a-pull-request-template-for-your-repository -- PR template format
- pre-commit.com: https://pre-commit.com/ -- .pre-commit-config.yaml format, hook installation
- uv integration: https://docs.astral.sh/uv/guides/integration/pre-commit/ -- uv + pre-commit patterns

### Secondary (MEDIUM confidence)
- Ruff pre-commit releases: https://github.com/astral-sh/ruff-pre-commit/releases -- v0.15.0 is latest (Feb 3, 2025)
- Gitleaks releases: https://github.com/gitleaks/gitleaks/releases -- v8.30.0 is latest (Nov 26, 2025)
- mirrors-mypy tags: https://github.com/pre-commit/mirrors-mypy/tags -- v1.19.1 is latest (Dec 15, 2025)
- pre-commit-uv: https://pypi.org/project/pre-commit-uv/ -- uv plugin for pre-commit
- Adam Johnson blog: https://adamj.eu/tech/2025/05/07/pre-commit-install-uv/ -- uv + pre-commit setup
- Jared Khan blog: https://jaredkhan.com/blog/mypy-pre-commit -- local mypy hook rationale

### Tertiary (LOW confidence)
- None -- all findings verified against primary or secondary sources

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All tools are well-documented, versions verified against official releases
- Architecture: HIGH - Configuration patterns verified against official documentation
- Pitfalls: HIGH - Verified by running ruff/mypy against actual codebase (84 lint errors, 50 type errors, 20% coverage)
- Coverage gap: HIGH - Measured directly from `pytest --cov` output (5779 total, 4595 uncovered)

**Research date:** 2026-02-05
**Valid until:** 2026-03-07 (30 days -- all tools are stable, patterns well-established)

## Appendix: Current Codebase Measurements

### Ruff Errors (84 total)
| Rule | Count | Location | Auto-fixable |
|------|-------|----------|--------------|
| E402 | 42 | src/ CLI scripts | No (suppress via per-file-ignores) |
| F401 | 31 | 7 in src/, 24 in tests/ | Yes (`--fix`) |
| F541 | 5 | src/ | Yes (`--fix`) |
| F841 | 5 | src/ | No (need manual review) |
| E741 | 1 | src/ | No (rename variable) |

### Mypy Errors (50 in 18 files)
Primary error types: `arg-type` (literal vs str), `var-annotated`, `operator` (None checks), `attr-defined`, `assignment`

### Test Coverage (20%)
| Metric | Value |
|--------|-------|
| Total statements | 5,779 |
| Covered | 1,184 |
| Uncovered | 4,595 |
| Current coverage | 20% |
| Target | 80% |
| Gap (statements) | ~3,400 |

### Existing Tool Versions
| Tool | Installed | In pyproject.toml |
|------|-----------|-------------------|
| ruff | 0.14.14 (global) | NOT in deps |
| mypy | 1.19.1 | >=1.13.0 (dev) |
| black | 25.12.0 | >=24.10.0 (dev) |
| pytest | 9.0.2 | >=9.0.2 (dev) |
| pytest-cov | 7.0.0 | >=7.0.0 (dev) |
| pre-commit | not installed | NOT in deps |
| gitleaks | not checked | NOT in deps |
