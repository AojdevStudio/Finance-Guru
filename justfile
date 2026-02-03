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
