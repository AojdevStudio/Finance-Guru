---

## title: "Contributing to Finance Guru"
description: "Contribution guidelines, scope boundaries, and quality gates for Finance Guru"
category: root

# Contributing to Finance Guru

Thanks for looking. Read the _Project State_ section below before investing time — it tells you which parts of this repo accept pull requests and which are issues-only for now.

---

## Project State (Read This First)

Finance Guru is being converted, in place, into an installable Claude Code and Codex plugin. Everything ships open under AGPL-3.0. The skills, agents, and Python engine are all part of the product; there is no withheld feature tier.

What this means for contributors today:


| Area                                   | State                                 | Safe to invest in?         |
| -------------------------------------- | ------------------------------------- | -------------------------- |
| Python analysis engine (`src/`)        | **Stable**                            | _Yes_                      |
| Claude Code skills (`.claude/skills/`) | **Active, mid plugin conversion**     | No — file an issue instead |
| BMAD-CORE agents (`fin-guru/agents/`)  | **Active, mid plugin conversion**     | No — file an issue instead |
| Documentation (`docs/`)                | **Always safe**                       | _Yes_                      |


While the plugin conversion is underway, changes to skills, agents, and hooks start as issues, not PRs. The maintainer is actively reshaping those surfaces and parallel PRs against them will conflict.

---

## Contribution Stance

This project is AGPLv3-licensed and open to contribution, but it is not actively recruiting contributors. We accept high-quality PRs that land on the repo; we do not maintain a roadmap of "good first issues" or guarantee rapid triage. Forks for private use are welcome and encouraged — see the README.

If you want something built and you are not sure we will merge it, open an issue first and ask.

---

## What We Accept

### Pull requests

Only these surfaces are in scope for PRs:

1. **Documentation** — Typo fixes, broken links, corrected API information, new MCP server entries in `docs/setup/api-keys.md`, clarified setup steps in `docs/setup/SETUP.md` and `TROUBLESHOOTING.md`, README polish.
2. **Python analysis engine** — Generic calculators and utilities under `src/analysis/`, `src/strategies/`, `src/utils/`, and their corresponding tests under `tests/python/`. Examples: `correlation.py`, `backtester.py`, `momentum.py`, `risk_metrics.py`, `screener.py`, `volatility.py`, `market_data.py`. Path-coupled calculators resolve every private file through `src/config/instance_paths.py`; contributors do not need access to private data to work on them.

### Issues only (no PRs)

Everything else is issues-only. We will evaluate bug reports and feature requests for these areas but will close PRs against them without review:

- Skills under `.claude/skills/`
- Agents under `fin-guru/agents/` or `.claude/commands/fin-guru/agents/`
- Hooks under `.claude/hooks/`
- `finance-guru-desktop/` (Electron POC, gitignored)

These surfaces are being reshaped by the plugin conversion, and outside PRs against them will conflict with that work.

---

## What We Reject

### Marketing or promotional content in documentation

PRs that swap neutral capability descriptions for vendor marketing copy (superlatives like "fastest," "most accurate," "best-in-class," or direct taglines from a vendor's homepage) are closed without merge. Documentation describes _what a tool does_, not _how good it is_.

Example of what we reject:

```
-- Semantic web search optimized for finance
++ Fastest and most accurate web search API for AI, optimized for finance
```

Example of what we accept:

```
-- Semantic web search optimized for finance
++ Neural search API designed for AI agents, optimized for finance
```

### AI-generated PRs without disclosure

AI-assisted contributions are welcome. Undisclosed AI-generated contributions are not. If you used Claude, GPT, Cursor, Copilot, or any other AI tool to write substantial portions of your PR, state that in the PR description:

```
Generated with [tool]; I reviewed, ran the tests, and verified behavior before submitting.
```

PRs that look AI-generated and carry no disclosure will be asked to either disclose or close.

### Changes to internal data or paths

Anything gitignored is internal. Do not reference gitignored paths, account identifiers, or dollar amounts in code you submit. If you need test data, use synthetic data (numpy / fixtures) under `tests/python/`.

---

## Data Classification (Public Repo Rule)

This is a public repository, and every tracked file is published the moment it is pushed. Code and documentation describe behaviour and never carry personal values, so evidence is written as a shape (a ratio, a percentage, a count) rather than an amount. The full policy is [DataClassification](../.claude/skills/compliance-scan/references/DataClassification.md).

Test fixtures use synthetic values that do not match the privacy scanner's patterns.

---

## How to Contribute

### For documentation PRs

1. Fork the repo.
2. Make your change.
3. Open a PR. No issue required for doc fixes.

### For code PRs

1. **Open an issue first.** Describe the bug or enhancement. Wait for acknowledgment before writing code. This protects you from investing in a PR we would reject.
2. Fork the repo and create a feature branch.
3. Make the change following the _Quality Gates_ below.
4. Open a PR referencing the issue (`Fixes #N`).

---

## Quality Gates

All code PRs must pass these checks locally before submission:

```bash
uv run pytest                  # All tests pass
uv run ruff format .           # Code is formatted
uv run ruff check .            # No lint errors
uv run mypy src/               # No type errors
```

Additionally:

- **New code requires new tests.** Any new CLI tool, calculator, or utility must ship with tests under `tests/python/` using synthetic data. Target coverage is 80%.
- **No real API calls in tests.** Tests must run offline. Mark network-dependent tests with `@pytest.mark.integration` (they are skipped by default in CI).
- **Three-layer pattern.** New financial tools follow the repo architecture: Pydantic input models in `src/models/`, calculator class in `src/analysis/` (or `strategies/` or `utils/`), CLI entry point as `{tool}_cli.py`. Reference implementation: `src/analysis/risk_metrics.py` + `src/models/risk_inputs.py` + `src/analysis/risk_metrics_cli.py`.

See `src/CLAUDE.md` for conventions (Pydantic + pandas gotchas, naming, typing, docstrings).

### Push gates

Two gates run before anything reaches GitHub. The pre-commit hooks (`.pre-commit-config.yaml`) run hygiene checks, ruff, mypy, pytest with coverage, and gitleaks. The privacy scanner (`.claude/skills/compliance-scan/scripts/scan.py`) runs in its `push` scope from the pre-push hook and also supports a `history` scope that scans every line a branch adds. A HIGH or CRITICAL finding blocks the push.

---

## Review Process

Every PR must pass:

1. **CodeRabbit review** — Automated; typically comments within minutes of opening.
2. **Maintainer review** — The maintainer reviews every PR personally before merge.

Both must approve. Respond to CodeRabbit's comments in the same way you respond to a human reviewer — accept valid feedback, push back on incorrect feedback with reasoning.

There is no SLA. If a PR sits without review for more than two weeks, ping the issue thread.

---

## Legal

This project is licensed under AGPLv3. By opening a PR, you agree that your contribution is licensed under AGPLv3 and that you have the right to license it. No separate CLA or DCO signoff is required at this time.

---

## Financial Disclaimer (Required in Analysis Output)

Finance Guru is educational software. Any new CLI tool that produces analysis output (PDF reports, Markdown analyses, buy tickets, etc.) must include the disclaimer block in its output. Reference: `fin-guru/templates/` and existing tools like `FinanceReport`. The disclaimer includes:

- "For educational purposes only; not investment advice."
- "Consult a licensed financial professional before acting on any analysis."
- An explicit risk disclosure appropriate to the strategy being discussed.

PRs that produce user-facing analysis output without the disclaimer will be asked to add it.

---

## Style Notes

- Markdown emphasis uses underscores (`_text_`), not asterisks (`*text`*). Enforced by markdownlint (MD049).
- Docstrings use Google style.
- Commit messages use Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`).

---

## Questions?

Open an issue. Tag it `question`.

---

_Last updated: 2026-09-02_
