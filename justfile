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

# Load a specific diagram by keyword (e.g., just load hedging)
load keyword:
  {{cc}} --append-system-prompt "$(cat {{diagrams}}/*{{keyword}}*.mmd 2>/dev/null)"

# --- Agent Personas ---

# Launch Claude Code as Finance Orchestrator (Cassandra Holt)
orchestrator:
  {{cc}} --append-system-prompt "$(cat .claude/agents/fg-finance-orchestrator.md)"

# Launch Claude Code as Quant Analyst
quant:
  {{cc}} --append-system-prompt "$(cat .claude/agents/fg-quant-analyst.md)"

# Launch Claude Code as Strategy Advisor
strategy:
  {{cc}} --append-system-prompt "$(cat .claude/agents/fg-strategy-advisor.md)"

# Launch Claude Code as Market Researcher
market:
  {{cc}} --append-system-prompt "$(cat .claude/agents/fg-market-researcher.md)"

# Launch Claude Code as Compliance Officer
compliance:
  {{cc}} --append-system-prompt "$(cat .claude/agents/fg-compliance-officer.md)"

# Launch Claude Code as Margin Specialist
margin:
  {{cc}} --append-system-prompt "$(cat .claude/agents/fg-margin-specialist.md)"

# Launch Claude Code as Dividend Specialist
dividend:
  {{cc}} --append-system-prompt "$(cat .claude/agents/fg-dividend-specialist.md)"

# Launch Claude Code as Teaching Specialist
teaching:
  {{cc}} --append-system-prompt "$(cat .claude/agents/fg-teaching-specialist.md)"

# Launch Claude Code as Builder
builder:
  {{cc}} --append-system-prompt "$(cat .claude/agents/fg-builder.md)"

# Launch Claude Code as QA Advisor
qa:
  {{cc}} --append-system-prompt "$(cat .claude/agents/fg-qa-advisor.md)"
