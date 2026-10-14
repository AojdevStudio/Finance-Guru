set dotenv-load := false

cc := "claude --dangerously-skip-permissions"

persona := quote(justfile_directory() / "scripts/launch-persona.sh") + " " + quote(invocation_directory()) + " " + cc

diagrams := ".dev/specs/backlog/diagrams"

# List all recipes
default:
  @just --list

# Load all mermaid diagrams as system context
[group('context')]
load-diagrams:
  {{cc}} --append-system-prompt "$(cat {{diagrams}}/*.mmd)"

# Load hedging integration architecture diagram
[group('context')]
load-hedging:
  {{cc}} --append-system-prompt "$(cat {{diagrams}}/finance-guru-hedging-integration-arch.mmd)"

# Load interactive knowledge explorer architecture diagram
[group('context')]
load-explorer:
  {{cc}} --append-system-prompt "$(cat {{diagrams}}/finance-guru-interactive-knowledge-explorer-arch.mmd)"

# Load standalone SDK TUI architecture decision doc
[group('context')]
tui:
  {{cc}} --append-system-prompt "$(cat .dev/sdk-notes.md)"

# Load a specific diagram by keyword (e.g., just load hedging)
[group('context')]
load keyword:
  {{cc}} --append-system-prompt "$(cat {{diagrams}}/*{{keyword}}*.mmd 2>/dev/null)"

# Launch Claude Code as Finance Orchestrator (Cassandra Holt)
[group('personas')]
orchestrator:
  {{persona}} --agent fg-finance-orchestrator

# Launch Claude Code as Quant Analyst
[group('personas')]
quant:
  {{persona}} --agent fg-quant-analyst

# Launch Claude Code as Strategy Advisor
[group('personas')]
strategy:
  {{persona}} --agent fg-strategy-advisor

# Launch Claude Code as Market Researcher
[group('personas')]
market:
  {{persona}} --agent fg-market-researcher

# Launch Claude Code as Compliance Officer
[group('personas')]
compliance:
  {{persona}} --agent fg-compliance-officer

# Launch Claude Code as Margin Specialist
[group('personas')]
margin:
  {{persona}} --agent fg-margin-specialist

# Launch Claude Code as Dividend Specialist
[group('personas')]
dividend:
  {{persona}} --agent fg-dividend-specialist

# Launch Claude Code as Teaching Specialist
[group('personas')]
teaching:
  {{persona}} --agent fg-teaching-specialist

# Launch Claude Code as Builder
[group('personas')]
builder:
  {{persona}} --agent fg-builder

# Launch Claude Code as QA Advisor
[group('personas')]
qa:
  {{persona}} --agent fg-qa-advisor

# Verify fin-guru/data/definitions.md stays in sync with src/ constants and skill files
[group('quality')]
check-definitions:
  uv run pytest tests/python/test_definitions_sync.py -v --no-cov

# Score the plugin against its eval suite, with and without the plugin (spends model usage).
[group('quality')]
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
