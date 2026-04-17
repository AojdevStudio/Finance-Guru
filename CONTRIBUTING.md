# Contributing to Finance Guru

The full contributing guide lives at [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md).

Short version — before you open a pull request:

1. Read [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) end-to-end
2. Fork, clone, run `./setup.sh`
3. Create a feature branch off `main`
4. Run `uv run ruff format .`, `uv run ruff check .`, `uv run mypy src/`, `uv run pytest`
5. Open a PR — CodeRabbit and the Claude review bot will comment automatically

## Filing issues

- Use the [bug report](.github/ISSUE_TEMPLATE/bug-report.yml), [feature request](.github/ISSUE_TEMPLATE/feature-request.yml), or [question](.github/ISSUE_TEMPLATE/question.md) templates
- New issues start with `needs-triage` — an owner will re-label within 72 hours
- Backlog is groomed during the quarterly review (see [docs/runbooks/quarterly-review.md](docs/runbooks/quarterly-review.md))

## Style

- Python — ruff (format + lint) + mypy strict
- Markdown — MD049 enforced; use underscores `_text_` not asterisks for emphasis
- Commits — conventional commits (`feat:`, `fix:`, `docs:`, `chore:`, `security:`) so release-please can cut versions

See [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) for everything else.
