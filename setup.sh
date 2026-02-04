#!/bin/bash

# Finance Guru Setup Script
# Checks dependencies, creates directories, scaffolds config files.
# Run this after cloning the repository to set up your environment.

set -e

# ============================================================
# Path Setup
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# ============================================================
# Terminal Color Detection
# ============================================================
# Detect whether stdout is an interactive terminal that supports
# color output. Fall back to plain text for pipes, CI, and cron.
# Use ${TERM:-dumb} to handle unset TERM (not just empty).

if [ -t 1 ] && [ "${TERM:-dumb}" != "dumb" ]; then
  GREEN='\033[0;32m'
  RED='\033[0;31m'
  YELLOW='\033[1;33m'
  BLUE='\033[0;34m'
  BOLD='\033[1m'
  NC='\033[0m'
else
  GREEN=''
  RED=''
  YELLOW=''
  BLUE=''
  BOLD=''
  NC=''
fi

# ============================================================
# Output Helper Functions
# ============================================================

info() {
  printf "  %s\n" "$1"
}

success() {
  printf "  ${GREEN}[OK]${NC} %s\n" "$1"
}

warn() {
  printf "  ${YELLOW}[WARN]${NC} %s\n" "$1"
}

error() {
  printf "  ${RED}[FAIL]${NC} %s\n" "$1"
}

header() {
  printf "\n${BOLD}%s${NC}\n" "$1"
}

# ============================================================
# OS Detection
# ============================================================
# Sets two globals: DETECTED_OS (macos/linux/wsl)
# and PKG_MANAGER (brew/apt/none)

DETECTED_OS=""
PKG_MANAGER=""

detect_os() {
  local kernel
  kernel=$(uname -s)
  case "$kernel" in
    Darwin)
      DETECTED_OS="macos"
      if command -v brew &>/dev/null; then
        PKG_MANAGER="brew"
      else
        PKG_MANAGER="none"
      fi
      ;;
    Linux)
      if grep -qi microsoft /proc/version 2>/dev/null; then
        DETECTED_OS="wsl"
      else
        DETECTED_OS="linux"
      fi
      if command -v apt &>/dev/null; then
        PKG_MANAGER="apt"
      else
        PKG_MANAGER="none"
      fi
      ;;
    *)
      DETECTED_OS="linux"
      PKG_MANAGER="none"
      ;;
  esac
}

# ============================================================
# Version Comparison
# ============================================================
# Returns 0 if $1 >= $2, 1 otherwise.
# Uses sort -V (verified on macOS Apple sort and GNU coreutils).

version_gte() {
  [ "$(printf '%s\n' "$1" "$2" | sort -V | head -1)" = "$2" ]
}

# ============================================================
# Install Command Lookup
# ============================================================
# Returns the OS-specific install command for a dependency.

get_install_command() {
  local dep_name="$1"

  case "$dep_name" in
    python3)
      case "$DETECTED_OS" in
        macos)
          if [ "$PKG_MANAGER" = "brew" ]; then
            printf "brew install python@3.12"
          else
            printf 'Install Homebrew first:\n  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"\nThen:\n  brew install python@3.12'
          fi
          ;;
        linux|wsl)
          if [ "$PKG_MANAGER" = "apt" ]; then
            printf "sudo apt update && sudo apt install python3.12"
          else
            printf "Visit https://www.python.org/downloads/"
          fi
          ;;
      esac
      ;;
    uv)
      printf "curl -LsSf https://astral.sh/uv/install.sh | sh"
      ;;
    bun)
      printf "curl -fsSL https://bun.sh/install | bash"
      ;;
  esac
}

# ============================================================
# Auto-Install Prompt
# ============================================================
# Prompts user to install a missing dependency. Only works in
# interactive mode (stdin is a tty). Skips in CI/pipes.

prompt_install() {
  local dep_name="$1"
  local install_cmd="$2"

  # Check if stdin is a tty before prompting
  if [ ! -t 0 ]; then
    warn "Skipped: $dep_name (non-interactive)"
    return 1
  fi

  printf "  %s not found. Install now? [y/N] " "$dep_name"
  read -r response
  if [[ "$response" =~ ^[Yy]$ ]]; then
    info "Installing $dep_name..."
    eval "$install_cmd"
    # Re-check if install succeeded
    case "$dep_name" in
      Python)  command -v python3 &>/dev/null && success "Installed: $dep_name" && return 0 ;;
      uv)     command -v uv &>/dev/null && success "Installed: $dep_name" && return 0 ;;
      Bun)    command -v bun &>/dev/null && success "Installed: $dep_name" && return 0 ;;
    esac
    error "Installation may have failed for $dep_name"
    return 1
  else
    printf "  ${YELLOW}Skipped:${NC} %s (user declined)\n" "$dep_name"
    return 1
  fi
}

# ============================================================
# Single Dependency Check
# ============================================================
# Checks if a command exists and optionally verifies minimum version.
# Returns 0 on success, 1 on failure.

check_dependency() {
  local cmd="$1"
  local name="$2"
  local min_version="$3"

  # Check if command exists
  if ! command -v "$cmd" &>/dev/null; then
    local install_cmd
    install_cmd=$(get_install_command "$cmd")
    printf "  ${RED}[MISSING]${NC} %s (not found)\n" "$name"
    info "Install with: $install_cmd"
    return 1
  fi

  # Extract version
  local found_version=""
  case "$cmd" in
    python3) found_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1) ;;
    uv)      found_version=$(uv --version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1) ;;
    bun)     found_version=$(bun --version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1) ;;
  esac

  # Check minimum version if specified
  if [ -n "$min_version" ] && [ -n "$found_version" ]; then
    if ! version_gte "$found_version" "$min_version"; then
      local install_cmd
      install_cmd=$(get_install_command "$cmd")
      printf "  ${RED}[MISSING]${NC} %s %s (>= %s required)\n" "$name" "$found_version" "$min_version"
      info "Install with: $install_cmd"
      return 1
    fi
  fi

  # Success
  if [ -n "$min_version" ]; then
    printf "  ${GREEN}[OK]${NC} %s %s (>= %s required)\n" "$name" "$found_version" "$min_version"
  else
    printf "  ${GREEN}[OK]${NC} %s %s\n" "$name" "$found_version"
  fi
  return 0
}

# ============================================================
# Check All Dependencies
# ============================================================
# Checks all dependencies in a single pass, accumulating failures
# without triggering set -e. Reports all results before failing.

# Arrays to track failed deps for auto-install
FAILED_DEPS=()
FAILED_NAMES=()
FAILED_CMDS=()

check_all_deps() {
  local missing=0
  FAILED_DEPS=()
  FAILED_NAMES=()
  FAILED_CMDS=()

  check_dependency "python3" "Python" "3.12" || { missing=$((missing + 1)); FAILED_DEPS+=("python3"); FAILED_NAMES+=("Python"); FAILED_CMDS+=("$(get_install_command python3)"); }
  check_dependency "uv" "uv" "" || { missing=$((missing + 1)); FAILED_DEPS+=("uv"); FAILED_NAMES+=("uv"); FAILED_CMDS+=("$(get_install_command uv)"); }
  check_dependency "bun" "Bun" "" || { missing=$((missing + 1)); FAILED_DEPS+=("bun"); FAILED_NAMES+=("Bun"); FAILED_CMDS+=("$(get_install_command bun)"); }

  if [ "$missing" -gt 0 ]; then
    printf "\n  ${RED}%d dependency(ies) missing${NC}\n" "$missing"
    return 1
  fi

  printf "\n  ${GREEN}All dependencies satisfied${NC}\n"
  return 0
}

# ============================================================
# Summary Tracking
# ============================================================
# Track items for the final summary report.

CREATED_ITEMS=()
SKIPPED_ITEMS=()

# ============================================================
# Progress Tracking
# ============================================================
# Tracks completed setup steps in .setup-progress for resumable re-runs.
# Step names: deps_checked, dirs_created, dirs_verified, config_scaffolded,
# python_deps_installed

PROGRESS_FILE="$PROJECT_ROOT/.setup-progress"
TOTAL_STEPS=5

is_step_complete() {
  [ -f "$PROGRESS_FILE" ] && grep -q "^$1$" "$PROGRESS_FILE"
}

mark_step_complete() {
  if ! is_step_complete "$1"; then
    echo "$1" >> "$PROGRESS_FILE"
  fi
}

show_progress() {
  if [ -f "$PROGRESS_FILE" ]; then
    local completed
    completed=$(wc -l < "$PROGRESS_FILE" | tr -d ' ')
    printf "\n  ${YELLOW}Resuming setup...${NC} (%s/%s steps completed)\n" "$completed" "$TOTAL_STEPS"
    while IFS= read -r step; do
      printf "  ${GREEN}[done]${NC} %s\n" "$step"
    done < "$PROGRESS_FILE"
    printf "\n"
  fi
}

# ============================================================
# Directory Functions
# ============================================================

create_dir() {
  if [ ! -d "$1" ]; then
    mkdir -p "$1"
    printf "  ${GREEN}Created:${NC} %s\n" "$1"
    CREATED_ITEMS+=("dir: $1")
  else
    printf "  ${YELLOW}Already exists:${NC} %s\n" "$1"
    SKIPPED_ITEMS+=("dir: $1")
  fi
}

create_directory_structure() {
  # fin-guru-private tree
  create_dir "$PROJECT_ROOT/fin-guru-private"
  create_dir "$PROJECT_ROOT/fin-guru-private/fin-guru"
  create_dir "$PROJECT_ROOT/fin-guru-private/fin-guru/strategies"
  create_dir "$PROJECT_ROOT/fin-guru-private/fin-guru/strategies/active"
  create_dir "$PROJECT_ROOT/fin-guru-private/fin-guru/strategies/archive"
  create_dir "$PROJECT_ROOT/fin-guru-private/fin-guru/strategies/risk-management"
  create_dir "$PROJECT_ROOT/fin-guru-private/fin-guru/tickets"
  create_dir "$PROJECT_ROOT/fin-guru-private/fin-guru/analysis"
  create_dir "$PROJECT_ROOT/fin-guru-private/fin-guru/analysis/reports"
  create_dir "$PROJECT_ROOT/fin-guru-private/fin-guru/reports"
  create_dir "$PROJECT_ROOT/fin-guru-private/fin-guru/archive"
  create_dir "$PROJECT_ROOT/fin-guru-private/guides"
  create_dir "$PROJECT_ROOT/fin-guru-private/hedging"

  # Portfolio data directories
  create_dir "$PROJECT_ROOT/notebooks"
  create_dir "$PROJECT_ROOT/notebooks/updates"
  create_dir "$PROJECT_ROOT/notebooks/retirement-accounts"
  create_dir "$PROJECT_ROOT/notebooks/transactions"
  create_dir "$PROJECT_ROOT/notebooks/tools-needed"
  create_dir "$PROJECT_ROOT/notebooks/tools-needed/done"

  # Finance Guru data directory
  create_dir "$PROJECT_ROOT/fin-guru/data"
}

verify_directory_structure() {
  local missing=0
  local dirs=(
    "$PROJECT_ROOT/fin-guru-private"
    "$PROJECT_ROOT/fin-guru-private/fin-guru"
    "$PROJECT_ROOT/fin-guru-private/fin-guru/strategies"
    "$PROJECT_ROOT/fin-guru-private/fin-guru/strategies/active"
    "$PROJECT_ROOT/fin-guru-private/fin-guru/strategies/archive"
    "$PROJECT_ROOT/fin-guru-private/fin-guru/strategies/risk-management"
    "$PROJECT_ROOT/fin-guru-private/fin-guru/tickets"
    "$PROJECT_ROOT/fin-guru-private/fin-guru/analysis"
    "$PROJECT_ROOT/fin-guru-private/fin-guru/analysis/reports"
    "$PROJECT_ROOT/fin-guru-private/fin-guru/reports"
    "$PROJECT_ROOT/fin-guru-private/fin-guru/archive"
    "$PROJECT_ROOT/fin-guru-private/guides"
    "$PROJECT_ROOT/fin-guru-private/hedging"
    "$PROJECT_ROOT/notebooks"
    "$PROJECT_ROOT/notebooks/updates"
    "$PROJECT_ROOT/notebooks/retirement-accounts"
    "$PROJECT_ROOT/notebooks/transactions"
    "$PROJECT_ROOT/notebooks/tools-needed"
    "$PROJECT_ROOT/notebooks/tools-needed/done"
    "$PROJECT_ROOT/fin-guru/data"
  )

  for dir in "${dirs[@]}"; do
    if [ ! -d "$dir" ]; then
      mkdir -p "$dir"
      printf "  ${GREEN}Recreated:${NC} %s\n" "$dir"
      CREATED_ITEMS+=("dir (recreated): $dir")
      missing=$((missing + 1))
    fi
  done

  if [ "$missing" -eq 0 ]; then
    printf "  ${GREEN}[OK]${NC} All directories verified\n"
  else
    printf "  ${YELLOW}Recreated %d missing directory(ies)${NC}\n" "$missing"
  fi
}

# ============================================================
# Config Scaffolding
# ============================================================

scaffold_file() {
  local target="$1"
  local description="$2"
  local basename_target
  basename_target=$(basename "$target")

  if [ -f "$target" ]; then
    if [ -t 0 ]; then
      printf "  %s already exists. Overwrite? [y/N] " "$basename_target"
      read -r response
      if [[ "$response" =~ ^[Yy]$ ]]; then
        return 0  # Caller writes content
      else
        printf "  ${YELLOW}Kept existing:${NC} %s\n" "$target"
        SKIPPED_ITEMS+=("file: $target")
        return 1
      fi
    else
      printf "  ${YELLOW}Kept existing:${NC} %s (non-interactive)\n" "$target"
      SKIPPED_ITEMS+=("file: $target")
      return 1
    fi
  fi

  # File doesn't exist -- caller will write it
  return 0
}

scaffold_config_files() {
  # 1. user-profile.yaml
  local user_profile="$PROJECT_ROOT/fin-guru/data/user-profile.yaml"
  if scaffold_file "$user_profile" "user profile template"; then
    cat > "$user_profile" << 'PROFILE_EOF'
# Finance Guru User Profile Configuration
# Complete this profile during onboarding with the Onboarding Specialist

system_ownership:
  type: "private_family_office"
  owner: "sole_client"
  mode: "exclusive_service"
  data_location: "local_only"

orientation_status:
  completed: false
  assessment_path: ""
  last_updated: ""
  onboarding_phase: "pending"  # pending | assessment | profiled | active

user_profile:
  # Will be populated during onboarding
  liquid_assets:
    total: 0
    accounts_count: 0
    average_yield: 0.0

  investment_portfolio:
    total_value: 0
    retirement_accounts: 0
    allocation: ""
    risk_profile: ""

  cash_flow:
    monthly_income: 0
    fixed_expenses: 0
    variable_expenses: 0
    investment_capacity: 0

  debt_profile:
    mortgage_balance: 0
    mortgage_payment: 0
    weighted_interest_rate: 0.0

  preferences:
    risk_tolerance: ""
    investment_philosophy: ""
    time_horizon: ""

# Google Sheets Integration (optional)
google_sheets:
  portfolio_tracker:
    spreadsheet_id: ""
    url: ""
    purpose: "Finance Guru portfolio tracking"
PROFILE_EOF
    printf "  ${GREEN}Created:${NC} %s\n" "$user_profile"
    CREATED_ITEMS+=("file: $user_profile")
  fi

  # 2. .env from .env.example
  local env_file="$PROJECT_ROOT/.env"
  if [ -f "$PROJECT_ROOT/.env.example" ]; then
    if scaffold_file "$env_file" "environment config"; then
      cp "$PROJECT_ROOT/.env.example" "$env_file"
      printf "  ${GREEN}Created:${NC} %s (from .env.example)\n" "$env_file"
      CREATED_ITEMS+=("file: $env_file")
    fi
  else
    warn ".env.example not found -- skipping .env creation"
  fi

  # 3. fin-guru-private/README.md
  local private_readme="$PROJECT_ROOT/fin-guru-private/README.md"
  if scaffold_file "$private_readme" "private directory README"; then
    cat > "$private_readme" << 'README_EOF'
# Finance Guru Private Documentation

This directory contains your personal Finance Guru documentation:

- **fin-guru/strategies/** - Your portfolio strategies
- **fin-guru/tickets/** - Buy/sell execution tickets
- **fin-guru/analysis/** - Deep research and modeling
- **fin-guru/reports/** - Monthly market reviews
- **guides/** - Tool usage guides

## Important

This directory is gitignored and will not be committed to version control.
Your financial data stays private on your local machine.

## Getting Started

After running the setup script, activate the Onboarding Specialist:

```
/fin-guru:agents:onboarding-specialist
```

The specialist will guide you through:
1. Financial assessment
2. Portfolio profile creation
3. Strategy recommendations

Once onboarding is complete, you can use the Finance Orchestrator:

```
/finance-orchestrator
```
README_EOF
    printf "  ${GREEN}Created:${NC} %s\n" "$private_readme"
    CREATED_ITEMS+=("file: $private_readme")
  fi
}

# ============================================================
# Python Dependencies
# ============================================================

install_python_deps() {
  if [ ! -f "$PROJECT_ROOT/pyproject.toml" ]; then
    warn "pyproject.toml not found -- skipping Python dependency install"
    return 0
  fi

  if (cd "$PROJECT_ROOT" && uv sync); then
    success "Python dependencies installed via uv sync"
    CREATED_ITEMS+=("Python dependencies (uv sync)")
  else
    error "uv sync failed -- you can retry with: cd $PROJECT_ROOT && uv sync"
    return 1
  fi
}

# ============================================================
# Summary
# ============================================================

print_summary() {
  printf "\n"
  printf "==========================================\n"
  printf "  ${GREEN}${BOLD}Setup Complete!${NC}\n"
  printf "==========================================\n"
  printf "\n"

  # Created section
  if [ ${#CREATED_ITEMS[@]} -gt 0 ]; then
    printf "  ${BOLD}Created:${NC}\n"
    for item in "${CREATED_ITEMS[@]}"; do
      printf "    - %s\n" "$item"
    done
    printf "\n"
  fi

  # Skipped section
  if [ ${#SKIPPED_ITEMS[@]} -gt 0 ]; then
    printf "  ${BOLD}Skipped (already existed):${NC}\n"
    for item in "${SKIPPED_ITEMS[@]}"; do
      printf "    - %s\n" "$item"
    done
    printf "\n"
  fi

  # Next steps
  printf "  ${BOLD}Next steps:${NC}\n"
  printf "\n"
  printf "  1. Edit .env to add your API keys (optional)\n"
  printf "     yfinance works without API keys for basic market data.\n"
  printf "\n"
  printf "  2. Run the onboarding wizard:\n"
  printf "     uv run python scripts/onboarding/main.py\n"
  printf "\n"
  printf "  3. After onboarding: /finance-orchestrator\n"
  printf "\n"
}

# ============================================================
# CLI Argument Parsing
# ============================================================

CHECK_DEPS_ONLY=false

show_usage() {
  printf "Usage: ./setup.sh [OPTIONS]\n"
  printf "\n"
  printf "Options:\n"
  printf "  --check-deps-only    Check dependencies without modifying anything\n"
  printf "  --help, -h           Show this help message\n"
  printf "\n"
  printf "Setup creates fin-guru-private/ directory structure, scaffolds config\n"
  printf "files, and installs Python dependencies. Run after cloning the repo.\n"
}

while [ $# -gt 0 ]; do
  case "$1" in
    --check-deps-only)
      CHECK_DEPS_ONLY=true
      shift
      ;;
    --help|-h)
      show_usage
      exit 0
      ;;
    *)
      printf "Unknown option: %s\n" "$1"
      printf "Run './setup.sh --help' for usage information.\n"
      exit 1
      ;;
  esac
done

# ============================================================
# Main Flow
# ============================================================

# Banner
printf "\n"
printf "==========================================\n"
printf "  ${BOLD}Finance Guru Setup${NC}\n"
printf "==========================================\n"
printf "\n"

# Show resume status if re-running
show_progress

# Detect OS
detect_os
info "Detected OS: $DETECTED_OS (package manager: $PKG_MANAGER)"

# Check dependencies
header "Checking dependencies..."

if check_all_deps; then
  # All deps present
  if [ "$CHECK_DEPS_ONLY" = true ]; then
    printf "\n"
    header "Dependency check complete"
    info "All dependencies are installed and meet version requirements."
    exit 0
  fi
else
  # Some deps missing
  if [ "$CHECK_DEPS_ONLY" = true ]; then
    printf "\n"
    header "Dependency check complete"
    error "Some dependencies are missing. Install them and re-run."
    exit 1
  fi

  # Offer auto-install for each missing dep
  printf "\n"
  header "Auto-install missing dependencies"

  for i in "${!FAILED_NAMES[@]}"; do
    prompt_install "${FAILED_NAMES[$i]}" "${FAILED_CMDS[$i]}" || true
  done

  # Re-check all deps after install attempts
  printf "\n"
  header "Re-checking dependencies..."

  if ! check_all_deps; then
    printf "\n"
    error "Please install missing dependencies and re-run setup.sh"
    exit 1
  fi
fi

mark_step_complete "deps_checked"

# Step 2: Create directory structure + ALWAYS validate
# NOTE: verify_directory_structure runs on EVERY path (first run AND re-run).
# On first run with pre-existing dirs, mkdir -p is idempotent but we must still
# validate expected structure. On re-run, we skip creation but still validate.
# This satisfies CONTEXT.md decision: "Verify state of skipped items -- not just
# existence but expected structure."
if is_step_complete "dirs_created"; then
  header "Verifying directory structure..."
  verify_directory_structure
  mark_step_complete "dirs_verified"
else
  header "Creating directory structure..."
  create_directory_structure
  # Always validate after creation -- catches pre-existing dirs with missing subdirs
  header "Validating directory structure..."
  verify_directory_structure
  mark_step_complete "dirs_created"
  mark_step_complete "dirs_verified"
fi

# Step 3: Scaffold config files
if is_step_complete "config_scaffolded"; then
  header "Verifying config files..."
  # Still run scaffold_config_files -- it handles overwrite prompts internally
  scaffold_config_files
else
  header "Scaffolding config files..."
  scaffold_config_files
  mark_step_complete "config_scaffolded"
fi

# Step 4: Install Python dependencies
if is_step_complete "python_deps_installed"; then
  header "Python dependencies..."
  printf "  ${GREEN}[done]${NC} Python dependencies already installed\n"
else
  header "Installing Python dependencies..."
  install_python_deps
  mark_step_complete "python_deps_installed"
fi

# Step 5: Summary
print_summary
