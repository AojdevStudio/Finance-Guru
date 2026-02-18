# Phase 5: Agent Readiness Hardening - Research

**Researched:** 2026-02-13
**Domain:** Python linting, pre-commit hooks, GitHub templates, test coverage, code ownership
**Confidence:** HIGH

## Summary

This phase hardens the repository's tooling to reach L2 agent readiness. The agent-readiness report (2026-02-02) scored the repo at L1 with a 36.5% pass rate. The five quick wins identified -- linter config, pre-commit hooks, issue/PR templates, test coverage thresholds, and CODEOWNERS -- are exactly what this phase delivers.

The standard stack is well-established: ruff for linting (already available locally at v0.12.3), the pre-commit framework for hook management, pytest-cov for coverage enforcement, and gitleaks for secret scanning (already installed at v8.28.0). All tools have mature pre-commit integrations with pinned versions available.

A critical finding: **current test coverage is 26%**, far below the 80% floor target. The context decision says "80% floor enforced in BOTH pre-commit and CI." Enforcing 80% immediately will break every commit until coverage is raised from 26% to 80%. The planner must sequence this carefully -- the lint cleanup and coverage ramp are the two heaviest lifts in this phase.

**Primary recommendation:** Split the phase into a lint/hooks setup pass (ruff + pre-commit + templates + CODEOWNERS), then a coverage ramp pass (write missing tests, then enforce the 80% threshold). Enforce linting immediately but defer coverage enforcement until tests exist.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| ruff | 0.15.x (pre-commit mirror) | Linter + formatter (replaces flake8, isort, pyupgrade, pydocstyle) | 10-100x faster than alternatives, single tool replaces 5+, Astral-backed |
| pre-commit | framework v4.x | Git hook management | De facto standard, language-agnostic, isolated environments per hook |
| pytest-cov | 7.0.0 (already installed) | Coverage measurement + enforcement | Built on coverage.py, integrates with pytest addopts, --cov-fail-under |
| gitleaks | v8.24.2+ (pre-commit hook) | Secret scanning | Industry standard, pre-commit native support, catches API keys/tokens |
| mypy | 1.19.1 (already installed) | Type checking | Already in dev deps, mirrors-mypy v1.19.1 available for pre-commit |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pre-commit-hooks | v5.0.0 | Utility hooks (trailing-whitespace, end-of-file-fixer, check-yaml) | Always -- baseline hygiene hooks |
| tj-actions/coverage-badge-py | v2 | Generate SVG coverage badge in CI | On pushes to main branch |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| ruff | flake8 + isort + pyupgrade | ruff replaces all three, 100x faster, single config |
| pre-commit framework | raw git hooks / bd hooks | pre-commit has isolated envs, version pinning, auto-update |
| gitleaks | truffleHog | gitleaks has better pre-commit integration, simpler config |

**Installation:**

```bash
# Add ruff to dev dependencies
uv add --dev ruff

# Install pre-commit globally (or via uv/pipx)
uv tool install pre-commit
# OR
pipx install pre-commit

# Install hooks after .pre-commit-config.yaml exists
pre-commit install
```

## Architecture Patterns

### Configuration Layout

All tool configuration lives in `pyproject.toml` (no separate .ruff.toml, .coveragerc, or mypy.ini files). This is the modern Python convention for single-file config.

```
pyproject.toml          # All tool config: ruff, mypy, pytest, coverage
.pre-commit-config.yaml # Hook definitions (versions, args)
.github/
├── ISSUE_TEMPLATE/
│   ├── bug-report.yml      # YAML form format
│   └── feature-request.yml # YAML form format
├── pull_request_template.md # PR template (markdown)
├── CODEOWNERS              # Review routing
└── workflows/
    ├── ci.yml              # NEW: lint + test + coverage
    ├── claude.yml          # Existing
    └── claude-code-review.yml # Existing
```

### Pattern 1: Ruff Config in pyproject.toml

**What:** Aggressive rule set with convention-based docstring style and per-file ignores for tests and CLI wrappers.
**When to use:** Always -- this is the single source of truth for lint rules.

```toml
# Source: Context7 /websites/astral_sh_ruff + official docs
[tool.ruff]
target-version = "py312"
line-length = 88  # Match existing black config
exclude = [".venv", "build", "dist", "node_modules", ".claude/hooks"]

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "F",    # pyflakes
    "I",    # isort (import sorting)
    "UP",   # pyupgrade (modernize syntax)
    "W",    # pycodestyle warnings
    "B",    # flake8-bugbear (common bugs)
    "SIM",  # flake8-simplify
    "C90",  # mccabe complexity
    "N",    # pep8-naming
    "D",    # pydocstyle (docstrings)
]
# Safe auto-fix rules (applied on commit via pre-commit)
fixable = ["I", "F401", "UP", "W", "D"]
unfixable = ["B"]  # Bugbear fixes require human judgment

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["D", "S101"]  # No docstrings required in tests
"*_cli.py" = ["D"]  # CLI wrappers are thin argparse; docstrings optional
"__init__.py" = ["F401", "D"]  # Re-exports and package docstrings

[tool.ruff.lint.pydocstyle]
convention = "google"  # Resolves D203/D211/D212/D213 conflicts

[tool.ruff.lint.mccabe]
max-complexity = 15  # Start generous, ratchet down later

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

### Pattern 2: Pre-commit Config with bd Hook Coexistence

**What:** Pre-commit framework config that coexists with existing `bd` (beads) git hooks.
**When to use:** This repo has `bd` shim hooks (pre-commit, post-merge, pre-push, post-checkout, prepare-commit-msg) that manage JSONL database sync. The `pre-commit` framework must NOT overwrite these with `--overwrite`.

**CRITICAL INTEGRATION DETAIL:** The existing `.git/hooks/pre-commit` is a `bd` shim that delegates to `bd hooks run pre-commit`. Running `pre-commit install` in default (migration) mode will:
1. Back up the existing hook as `.git/hooks/pre-commit.legacy`
2. Install the pre-commit framework hook
3. The framework hook will call `.legacy` after running its own hooks

This migration mode preserves `bd` hook functionality. However, the `bd` shim itself is thin and `bd` gracefully handles missing commands. The recommended approach is:

```yaml
# .pre-commit-config.yaml
# Source: Context7 /pre-commit/pre-commit.com + ruff-pre-commit README
repos:
  # Baseline hygiene
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: ['--maxkb=500']

  # Ruff linter (with auto-fix) + formatter
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.15.1
    hooks:
      - id: ruff-check
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  # Type checking (standard mode, changed files only)
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.19.1
    hooks:
      - id: mypy
        additional_dependencies:
          - pydantic>=2.10.6
          - types-requests
          - types-PyYAML
        args: [--config-file=pyproject.toml]

  # Secret scanning
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.24.2
    hooks:
      - id: gitleaks
```

### Pattern 3: Coverage Configuration

**What:** pytest-cov config with exclusions and fail-under threshold.

```toml
# Source: Context7 /pytest-dev/pytest-cov
[tool.pytest.ini_options]
testpaths = ["tests/python"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
addopts = "-v --tb=short --cov=src --cov-report=term-missing --cov-fail-under=80"
pythonpath = ["."]
markers = [
    "integration: marks tests as integration tests (require real API keys)",
]

[tool.coverage.run]
branch = true
source = ["src"]
omit = [
    "src/*_cli.py",      # Thin CLI wrappers (user decision)
    "src/ui/*",          # TUI components (hard to unit test)
]

[tool.coverage.report]
precision = 1
show_missing = true
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
```

### Pattern 4: GitHub Issue Templates (YAML Form Format)

**What:** Structured YAML forms with dropdowns, required fields, textareas.

```yaml
# .github/ISSUE_TEMPLATE/bug-report.yml
name: Bug Report
description: Report a bug or unexpected behavior
labels: ["bug"]
body:
  - type: textarea
    id: description
    attributes:
      label: Description
      description: What happened?
      placeholder: Describe the bug clearly
    validations:
      required: true
  - type: textarea
    id: steps
    attributes:
      label: Steps to Reproduce
      value: |
        1.
        2.
        3.
  - type: textarea
    id: expected
    attributes:
      label: Expected Behavior
      placeholder: What should have happened?
    validations:
      required: true
  - type: textarea
    id: actual
    attributes:
      label: Actual Behavior
      placeholder: What actually happened?
    validations:
      required: true
  - type: dropdown
    id: python-version
    attributes:
      label: Python Version
      options:
        - "3.12"
        - "3.13"
        - Other
  - type: dropdown
    id: os
    attributes:
      label: Operating System
      options:
        - macOS
        - Linux
        - WSL
        - Other
```

### Anti-Patterns to Avoid

- **Running tests in pre-commit:** Tests should run in CI, not on every commit. Pre-commit hooks must be fast (<10s) to avoid developer friction. User explicitly deferred tests to CI.
- **Using `--strict` mode for mypy in pre-commit:** Standard mode catches obvious type errors without requiring full annotations on every function. Strict mode would generate hundreds of errors on a 23k-line codebase that was not written with it.
- **Overwriting bd hooks with `pre-commit install --overwrite`:** This would destroy the JSONL sync hooks that `bd` manages. Use default migration mode.
- **Enforcing 80% coverage before tests exist:** Current coverage is 26%. Enforcing 80% immediately blocks all commits.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Import sorting | Custom script | ruff `I` rules | Handles stdlib/third-party/local classification |
| Docstring style checking | Manual review | ruff `D` rules with google convention | 200+ rules, conflict resolution via convention |
| Secret detection | grep for API keys | gitleaks pre-commit hook | Regex patterns maintained by community, low false positives |
| Hook environment isolation | virtualenv per hook | pre-commit framework | Automatic env creation, caching, version pinning |
| Coverage badge | Custom SVG generation | tj-actions/coverage-badge-py | Reads coverage.xml, generates standard badge |
| Git hook chaining | Manual script composition | pre-commit migration mode | Backs up existing hooks, chains them automatically |

**Key insight:** Every tool in this phase has a mature pre-commit integration. The entire hook pipeline can be declared in a single `.pre-commit-config.yaml` without writing any custom shell scripts.

## Common Pitfalls

### Pitfall 1: D Rule Conflicts in Pydocstyle

**What goes wrong:** Enabling `"D"` without setting a convention causes D203 and D211 (blank line before/after class docstring) and D212 and D213 (multi-line summary position) to conflict -- violations of one rule ARE compliance with the other.
**Why it happens:** pydocstyle supports multiple conventions (Google, NumPy, PEP257) with mutually exclusive rules.
**How to avoid:** Always set `convention = "google"` (or "numpy") in `[tool.ruff.lint.pydocstyle]`. This automatically disables conflicting rules.
**Warning signs:** Ruff reports "conflicting rules" or the same line triggers two opposing violations.

### Pitfall 2: Coverage Cliff at 26% vs 80% Target

**What goes wrong:** Enabling `--cov-fail-under=80` with current 26% coverage blocks every single commit and CI run.
**Why it happens:** The decision says "80% floor enforced in BOTH pre-commit and CI." But coverage is 54 points below target.
**How to avoid:** Phase the rollout:
  1. Add coverage _reporting_ first (no enforcement)
  2. Write tests to reach 80%
  3. Enable `--cov-fail-under=80` only after coverage exceeds 80%
  4. Consider: exclude more paths (UI, untested CLI tools) to start, then expand coverage scope
**Warning signs:** Every commit fails coverage check; developers start using `--no-verify`.

### Pitfall 3: pre-commit Install Destroys bd Hooks

**What goes wrong:** Running `pre-commit install --overwrite` replaces the existing `bd` shim hooks, breaking JSONL database sync.
**Why it happens:** `bd` hooks (pre-commit, post-merge, pre-push, post-checkout, prepare-commit-msg) are thin shims that delegate to `bd hooks run`. The `pre-commit` framework only manages the `pre-commit` hook type by default.
**How to avoid:** Use `pre-commit install` WITHOUT `--overwrite`. Default migration mode chains the existing bd hook as `.legacy`. Test that both pre-commit framework hooks AND bd hooks run after installation.
**Warning signs:** After installing pre-commit, `bd hooks list` shows hooks as "not installed" or JSONL sync stops working.

### Pitfall 4: mypy in Pre-commit is Slow and Noisy

**What goes wrong:** mypy in pre-commit runs in an isolated virtualenv without project dependencies, causing import errors and false positives. It also runs on ALL files, not just changed ones.
**Why it happens:** pre-commit creates isolated environments per hook. mypy needs type stubs for third-party libraries to be useful.
**How to avoid:**
  1. List critical type stubs in `additional_dependencies` (pydantic, types-requests, types-PyYAML)
  2. Do NOT use `--install-types` (mutates pre-commit environment, breaks cache)
  3. Consider using `--warn-unused-ignores` but NOT `--strict`
  4. Accept that pre-commit mypy will be less thorough than a full `uv run mypy src/` -- that is fine for commit-time
**Warning signs:** mypy reports "Cannot find implementation or library stub" for every import.

### Pitfall 5: Ruff One-Time Cleanup Creates Massive Diff

**What goes wrong:** First `ruff check --fix` on 23k lines of uninlinted code produces hundreds of changes across every file.
**Why it happens:** The codebase has never had ruff, so every existing style violation is caught at once.
**How to avoid:**
  1. Run `ruff check --fix` and `ruff format` as a dedicated "lint cleanup" commit
  2. Keep this as a single, well-labeled commit (e.g., "style: ruff lint cleanup pass")
  3. Do NOT mix lint fixes with functional changes
  4. Review the diff -- some auto-fixes may change semantics (rare but possible with bugbear)
**Warning signs:** PR reviewer sees 200+ file changes; auto-fix silently changes behavior.

### Pitfall 6: Coverage Measured in Pre-commit Adds Commit Latency

**What goes wrong:** Running `pytest --cov` in pre-commit takes 7+ seconds (440 tests), making every commit slow.
**Why it happens:** User decided "80% floor enforced in BOTH pre-commit and CI."
**How to avoid:** This is an accepted tradeoff per user decision. However, consider:
  1. Use `--cov-fail-under` but skip `--cov-report=term-missing` in pre-commit (reporting is CI's job)
  2. Use `pre-commit` local hook (not a repo hook) so pytest runs in project venv with all deps
  3. Accept the latency or revisit the decision if it causes friction

## Code Examples

### Ruff Configuration (Complete pyproject.toml Section)

```toml
# Source: Context7 /websites/astral_sh_ruff, verified against ruff 0.12.3
[tool.ruff]
target-version = "py312"
line-length = 88
exclude = [
    ".venv",
    "build",
    "dist",
    "node_modules",
    ".claude/hooks",
    ".eggs",
    "__pypackages__",
]

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "W", "B", "SIM", "C90", "N", "D"]
fixable = ["I", "F401", "UP", "W", "D", "SIM"]
unfixable = ["B"]
ignore = [
    "E501",   # Line length handled by formatter
]

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["D", "S101", "B011"]
"*_cli.py" = ["D"]
"__init__.py" = ["F401", "D104"]
"scripts/**/*.py" = ["D"]

[tool.ruff.lint.pydocstyle]
convention = "google"

[tool.ruff.lint.mccabe]
max-complexity = 15

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
```

### mypy Configuration (pyproject.toml Section)

```toml
# Source: mypy docs, standard mode (not strict)
[tool.mypy]
python_version = "3.12"
warn_return_any = true
warn_unused_configs = true
warn_unused_ignores = true
disallow_untyped_defs = false  # Standard mode, not strict
check_untyped_defs = true
ignore_missing_imports = false

[[tool.mypy.overrides]]
module = [
    "yfinance.*",
    "streamlit.*",
    "textual.*",
    "sklearn.*",
    "scipy.*",
    "matplotlib.*",
    "plotly.*",
    "reportlab.*",
    "openpyxl.*",
    "xlsxwriter.*",
    "questionary.*",
]
ignore_missing_imports = true
```

### CODEOWNERS File

```
# Source: GitHub docs
# CODEOWNERS - Review routing for the Finance Guru repository
# Default owner for everything
* @AojdevStudio

# Core source code
/src/ @AojdevStudio
/tests/ @AojdevStudio

# Infrastructure and config
/setup.sh @AojdevStudio
/pyproject.toml @AojdevStudio
/.pre-commit-config.yaml @AojdevStudio
/.github/ @AojdevStudio
```

### PR Template

```markdown
<!-- .github/pull_request_template.md -->
## Summary

- [ ] What changed and why

## Test Plan

- [ ] Tests pass (`uv run pytest`)
- [ ] Lint clean (`uv run ruff check .`)
- [ ] Types clean (`uv run mypy src/`)

## Review Checklist

- [ ] No secrets or PII in diff
- [ ] Documentation updated (if applicable)
- [ ] Coverage maintained or improved
```

### CI Workflow (Lint + Test + Coverage)

```yaml
# .github/workflows/ci.yml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v6
      - run: uv sync --dev
      - name: Ruff lint
        run: uv run ruff check .
      - name: Ruff format check
        run: uv run ruff format --check .
      - name: mypy
        run: uv run mypy src/
      - name: Tests with coverage
        run: uv run pytest --cov=src --cov-report=xml:coverage.xml --cov-report=term-missing --cov-fail-under=80
      - name: Coverage badge
        if: github.ref == 'refs/heads/main'
        uses: tj-actions/coverage-badge-py@v2
        with:
          output: coverage.svg
```

### setup.sh Integration (Pre-commit Auto-Install)

```bash
# Add to setup.sh after Python deps are installed
install_pre_commit_hooks() {
  if [ ! -f "$PROJECT_ROOT/.pre-commit-config.yaml" ]; then
    warn ".pre-commit-config.yaml not found -- skipping hook install"
    return 0
  fi

  if ! command -v pre-commit &>/dev/null; then
    # Try uv tool
    if command -v uv &>/dev/null; then
      info "Installing pre-commit via uv tool..."
      uv tool install pre-commit
    else
      warn "pre-commit not found. Install with: pipx install pre-commit"
      return 0
    fi
  fi

  info "Installing pre-commit hooks..."
  (cd "$PROJECT_ROOT" && pre-commit install)
  success "Pre-commit hooks installed"
  CREATED_ITEMS+=("pre-commit hooks")
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| flake8 + isort + pyupgrade + pydocstyle (4 tools) | ruff (single tool) | 2023-2024 | One config, 100x faster, single dependency |
| .pre-commit-config.yaml with black | ruff-pre-commit (lint + format) | 2024 | Replaces both black and flake8 in hook pipeline |
| .coveragerc file | [tool.coverage.*] in pyproject.toml | 2022+ | Single config file, TOML standard |
| GitHub issue templates (markdown) | YAML form format | 2021+ | Structured dropdowns, required fields, validation |
| Raw git hooks in .git/hooks/ | pre-commit framework | 2016+ | Isolated envs, version pinning, shareable config |

**Deprecated/outdated:**
- **black as a separate tool:** ruff format is a drop-in replacement. This repo has black in dev deps -- ruff format can replace it, removing a dependency.
- **flake8 with plugins:** ruff implements 800+ rules from 50+ flake8 plugins natively.

## Open Questions

1. **bd hook coexistence verification**
   - What we know: pre-commit migration mode chains existing hooks as `.legacy`. bd hooks are thin shims that delegate to `bd hooks run`.
   - What's unclear: Whether the `.legacy` chain works correctly with bd shims that use `exec`. The `exec` call replaces the process, which should be fine as a chained hook, but needs testing.
   - Recommendation: Test manually after `pre-commit install`. If bd hooks break, consider wrapping both in a custom `.git/hooks/pre-commit` that calls pre-commit first, then bd.

2. **Coverage scope with 15 untested CLI wrappers**
   - What we know: 15 `*_cli.py` files are excluded from coverage (user decision). Many core modules (momentum.py, volatility.py, moving_averages.py, etc.) are at 0% coverage.
   - What's unclear: Whether excluding CLI files AND all 0%-coverage modules brings reachable coverage close enough to 80%. Currently src/ has 6453 statements total, 4766 uncovered (26%). CLI files alone may account for ~2000 statements.
   - Recommendation: After excluding `*_cli.py` and `src/ui/*`, recalculate effective coverage. If remaining code is still far from 80%, significant test writing is needed. This is the biggest work item in the phase.

3. **Ruff replacing black**
   - What we know: ruff format is a drop-in for black. Black is currently in dev deps. Both use line-length 88 by default.
   - What's unclear: Whether removing black would break any existing CI or developer workflows.
   - Recommendation: Replace black with ruff format in this phase. Remove black from dev deps. This simplifies the toolchain.

4. **Pre-commit coverage hook feasibility**
   - What we know: User wants coverage enforcement in pre-commit too. Running 440 tests on every commit takes ~7 seconds.
   - What's unclear: Whether 7-second hook latency is acceptable long-term as test count grows.
   - Recommendation: Implement as user decided. Use a `local` hook type (runs in project venv) to avoid dependency isolation issues. Monitor latency.

## Sources

### Primary (HIGH confidence)

- Context7 `/websites/astral_sh_ruff` - Rule configuration, pyproject.toml format, auto-fix settings, per-file ignores
- Context7 `/pre-commit/pre-commit.com` - Hook config YAML, install commands, migration mode behavior
- Context7 `/pytest-dev/pytest-cov` - Coverage config, fail-under, omit patterns, pyproject.toml format
- Context7 `/gitleaks/gitleaks` - Pre-commit integration, version v8.24.2
- GitHub ruff-pre-commit README (WebFetch) - Latest version v0.15.1, hook IDs: ruff-check, ruff-format
- GitHub mirrors-mypy tags (WebFetch) - Latest version v1.19.1
- GitHub form schema docs (WebFetch) - YAML form syntax for issue templates

### Secondary (MEDIUM confidence)

- Perplexity search - pre-commit migration mode behavior with existing hooks
- Perplexity search - tj-actions/coverage-badge-py for CI badge generation
- Perplexity search - ruff pydocstyle D rule conflicts and convention setting

### Tertiary (LOW confidence)

- pre-commit-hooks rev v5.0.0 -- version from Context7 example; verify with `pre-commit autoupdate`

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH - All tools verified via Context7 with current versions
- Architecture: HIGH - Configuration patterns verified against official docs
- Pitfalls: HIGH - bd hook coexistence verified by reading actual .git/hooks/ files; coverage gap verified by running pytest
- Coverage gap: HIGH - Measured directly: 26% current vs 80% target

**Codebase measurements (verified):**

- Total Python source: 23,635 lines across ~63 files in src/
- Total statements (coverage.py): 6,453
- Current coverage: 26% (1,687 of 6,453 statements covered)
- Test count: 440 tests (438 pass, 2 skip)
- CLI wrappers to exclude: 15 files (*_cli.py)
- Existing git hooks: bd shims (pre-commit, post-merge, pre-push, post-checkout, prepare-commit-msg)
- Existing CI: claude.yml (code action) + claude-code-review.yml (PR review) -- no lint/test CI yet
- GitHub owner: AojdevStudio
- Remote: https://github.com/AojdevStudio/Finance-Guru.git

**Research date:** 2026-02-13
**Valid until:** 2026-03-13 (stable domain, tools change slowly)
