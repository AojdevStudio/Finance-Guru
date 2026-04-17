---
title: Dev Container
last-reviewed: 2026-04-17
---

# Finance Guru Dev Container

A reproducible dev environment — Python 3.12 + uv + Node LTS + Bun + GitHub CLI — for Codespaces or local VS Code.

## Use in GitHub Codespaces

1. Open the repo on GitHub
2. Click **Code → Codespaces → Create codespace on main**
3. Wait for `postCreateCommand` to finish (installs Bun, runs `uv sync --dev`)
4. Verify: `uv run pytest -m "not integration"`

## Use locally (VS Code + Docker)

1. Install the _Dev Containers_ extension for VS Code
2. `File → Open Folder` on the cloned repo
3. `F1 → Dev Containers: Reopen in Container`
4. First build takes a few minutes; subsequent opens are cached

## What you get

| Tool | Version | Notes |
|------|---------|-------|
| Python | 3.12 | `.venv` at `/workspaces/family-office/.venv` |
| uv | latest | Package manager |
| Node | LTS | For `apps/plaid-dashboard` (Next.js) |
| Bun | latest | For `apps/simplefin-sync` and hooks |
| GitHub CLI | latest | Pre-authenticated via Codespace token |

## Extensions pre-installed

Ruff, Python, mypy, Even Better TOML, YAML, Markdown All-in-One.

## Troubleshooting

- _`uv` command not found_ — the `ghcr.io/va-h/devcontainers-features/uv:1` feature needs Codespace rebuild; try `F1 → Dev Containers: Rebuild Container`
- _Tests fail on parallel import_ — `pytest-xdist` is configured for `-n auto`; reduce with `uv run pytest -n 1` if you see race conditions
