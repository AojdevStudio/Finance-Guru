# Finance Guru - Command Launchpad
set dotenv-load := false

# Claude Code with skip permissions (mirrors `cc` shell alias)
cc := "claude --dangerously-skip-permissions"

# Persona sessions read the instance named by FIN_GURU_DATA_ROOT, never this checkout.
persona := 'test -n "${FIN_GURU_DATA_ROOT:-}" || { echo "Export FIN_GURU_DATA_ROOT=<your instance> first, so the agent reads your instance, not this checkout." >&2; exit 1; } && ' + cc

# Diagram paths
diagrams := ".dev/specs/backlog/diagrams"

# List all recipes
default:
  @just --list

# --- Context Loading ---

# Load all mermaid diagrams as system context
load-diagrams:
  {{cc}} --append-system-prompt "$(cat {{diagrams}}/*.mmd)"

# Load hedging integration architecture diagram
load-hedging:
  {{cc}} --append-system-prompt "$(cat {{diagrams}}/finance-guru-hedging-integration-arch.mmd)"

# Load interactive knowledge explorer architecture diagram
load-explorer:
  {{cc}} --append-system-prompt "$(cat {{diagrams}}/finance-guru-interactive-knowledge-explorer-arch.mmd)"

# Load standalone SDK TUI architecture decision doc
tui:
  {{cc}} --append-system-prompt "$(cat .dev/sdk-notes.md)"

# Load a specific diagram by keyword (e.g., just load hedging)
load keyword:
  {{cc}} --append-system-prompt "$(cat {{diagrams}}/*{{keyword}}*.mmd 2>/dev/null)"

# --- Agent Personas ---

# Launch Claude Code as Finance Orchestrator (Cassandra Holt)
orchestrator:
  {{persona}} --agent fg-finance-orchestrator

# Launch Claude Code as Quant Analyst
quant:
  {{persona}} --agent fg-quant-analyst

# Launch Claude Code as Strategy Advisor
strategy:
  {{persona}} --agent fg-strategy-advisor

# Launch Claude Code as Market Researcher
market:
  {{persona}} --agent fg-market-researcher

# Launch Claude Code as Compliance Officer
compliance:
  {{persona}} --agent fg-compliance-officer

# Launch Claude Code as Margin Specialist
margin:
  {{persona}} --agent fg-margin-specialist

# Launch Claude Code as Dividend Specialist
dividend:
  {{persona}} --agent fg-dividend-specialist

# Launch Claude Code as Teaching Specialist
teaching:
  {{persona}} --agent fg-teaching-specialist

# Launch Claude Code as Builder
builder:
  {{persona}} --agent fg-builder

# Launch Claude Code as QA Advisor
qa:
  {{persona}} --agent fg-qa-advisor

# --- Quality gates ---

# Verify fin-guru/data/definitions.md stays in sync with src/ constants and skill files
check-definitions:
  uv run pytest tests/python/test_definitions_sync.py -v --no-cov

# Score the plugin against its eval suite, with and without the plugin (spends model usage).
# The eval runner refuses a plugin directory over 20000 entries, so it scores a copy of the tracked files.
eval runs="1":
  #!/usr/bin/env bash
  set -euo pipefail
  scratch="$(mktemp -d)"
  trap 'rm -rf "$scratch"' EXIT
  export_dir="$scratch/finance-guru"
  results="$PWD/evals/results/$(date +%Y%m%dT%H%M%S)"
  mkdir -p "$export_dir" "$results"
  git ls-files -z --cached \
    | while IFS= read -r -d '' path; do [ -e "$path" ] && printf '%s\0' "$path"; done \
    | rsync -a --from0 --files-from=- ./ "$export_dir/"
  claude plugin eval "$export_dir" --trust-plugin --runs {{runs}} --judge-model sonnet --max-cost-usd 10 --no-publish --output-dir "$results" --report "$results/report.html"
