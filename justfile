# Finance Guru - Command Launchpad
set dotenv-load := false

# Claude Code with skip permissions (mirrors `cc` shell alias)
cc := "claude --dangerously-skip-permissions"

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
  {{cc}} --agent fg-finance-orchestrator

# Launch Claude Code as Quant Analyst
quant:
  {{cc}} --agent fg-quant-analyst

# Launch Claude Code as Strategy Advisor
strategy:
  {{cc}} --agent fg-strategy-advisor

# Launch Claude Code as Market Researcher
market:
  {{cc}} --agent fg-market-researcher

# Launch Claude Code as Compliance Officer
compliance:
  {{cc}} --agent fg-compliance-officer

# Launch Claude Code as Margin Specialist
margin:
  {{cc}} --agent fg-margin-specialist

# Launch Claude Code as Dividend Specialist
dividend:
  {{cc}} --agent fg-dividend-specialist

# Launch Claude Code as Teaching Specialist
teaching:
  {{cc}} --agent fg-teaching-specialist

# Launch Claude Code as Builder
builder:
  {{cc}} --agent fg-builder

# Launch Claude Code as QA Advisor
qa:
  {{cc}} --agent fg-qa-advisor

# --- Quality gates ---

# Verify fin-guru/data/definitions.md stays in sync with src/ constants and skill files
check-definitions:
  uv run pytest tests/python/test_definitions_sync.py -v --no-cov
