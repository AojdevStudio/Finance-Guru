#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

if [ -t 1 ] && [ "${TERM:-dumb}" != "dumb" ]; then
  GREEN='\033[0;32m'
  RED='\033[0;31m'
  YELLOW='\033[1;33m'
  BOLD='\033[1m'
  NC='\033[0m'
else
  GREEN=''
  RED=''
  YELLOW=''
  BOLD=''
  NC=''
fi

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

version_gte() {
  [ "$(printf '%s\n' "$1" "$2" | sort -V | head -1)" = "$2" ]
}

get_install_command() {
  case "$1" in
    python3)
      case "$PKG_MANAGER" in
        brew) printf "brew install python@3.12" ;;
        apt)  printf "sudo apt update && sudo apt install python3.12" ;;
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

get_manual_install_steps() {
  if [ "$1" != "python3" ]; then
    return
  fi
  if [ "$DETECTED_OS" = "macos" ]; then
    printf 'Install Homebrew first:\n  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"\nThen:\n  brew install python@3.12\n'
  else
    printf "Visit https://www.python.org/downloads/\n"
  fi
}

print_install_hint() {
  local install_cmd
  install_cmd=$(get_install_command "$1")
  if [ -n "$install_cmd" ]; then
    info "Install with: $install_cmd"
  else
    info "Install manually:"
    get_manual_install_steps "$1" | while IFS= read -r line; do
      printf "    %s\n" "$line"
    done
  fi
}

prompt_install() {
  local dep_name="$1"
  local dep_cmd="$2"
  local install_cmd
  install_cmd=$(get_install_command "$dep_cmd")

  if [ ! -t 0 ]; then
    warn "Skipped: $dep_name (non-interactive)"
    return 1
  fi

  if [ -z "$install_cmd" ]; then
    info "$dep_name requires manual installation:"
    get_manual_install_steps "$dep_cmd" | while IFS= read -r line; do
      printf "    %s\n" "$line"
    done
    return 1
  fi

  printf "  %s not found. Install now? [y/N] " "$dep_name"
  read -r response
  if [[ "$response" =~ ^[Yy]$ ]]; then
    info "Installing $dep_name..."
    if ! eval "$install_cmd"; then
      error "Install command failed for $dep_name"
      return 1
    fi
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

check_dependency() {
  local cmd="$1"
  local name="$2"
  local min_version="$3"

  if [ "$cmd" != "python3" ] && ! command -v "$cmd" &>/dev/null; then
    printf "  ${RED}[MISSING]${NC} %s (not found)\n" "$name"
    print_install_hint "$cmd"
    return 1
  fi

  local found_version
  case "$cmd" in
    python3)
      local python_version
      if ! python_version=$(uv run --no-project --python '>=3.12' --no-python-downloads python --version 2>&1); then
        printf "  ${RED}[MISSING]${NC} Python >= 3.12 through uv\n"
        return 1
      fi
      found_version=$(printf '%s' "$python_version" | grep -oE '[0-9]+\.[0-9]+' | head -1)
      ;;
    *)       found_version=$("$cmd" --version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1) ;;
  esac
  if [ -z "$found_version" ]; then
    found_version="0.0"
  fi

  if [ -n "$min_version" ] && ! version_gte "$found_version" "$min_version"; then
    printf "  ${RED}[MISSING]${NC} %s %s (>= %s required)\n" "$name" "$found_version" "$min_version"
    print_install_hint "$cmd"
    return 1
  fi

  if [ -n "$min_version" ]; then
    printf "  ${GREEN}[OK]${NC} %s %s (>= %s required)\n" "$name" "$found_version" "$min_version"
  else
    printf "  ${GREEN}[OK]${NC} %s %s\n" "$name" "$found_version"
  fi
  return 0
}

FAILED_DEPS=()
FAILED_NAMES=()

check_all_deps() {
  local missing=0
  FAILED_DEPS=()
  FAILED_NAMES=()

  # Python is found through uv, so a missing uv says nothing about Python.
  if check_dependency "uv" "uv" ""; then
    check_dependency "python3" "Python" "3.12" || { missing=$((missing + 1)); FAILED_DEPS+=("python3"); FAILED_NAMES+=("Python"); }
  else
    missing=$((missing + 1)); FAILED_DEPS+=("uv"); FAILED_NAMES+=("uv")
  fi
  check_dependency "bun" "Bun" "" || { missing=$((missing + 1)); FAILED_DEPS+=("bun"); FAILED_NAMES+=("Bun"); }

  if [ "$missing" -gt 0 ]; then
    printf "\n  ${RED}%d dependency(ies) missing${NC}\n" "$missing"
    return 1
  fi

  printf "\n  ${GREEN}All dependencies satisfied${NC}\n"
  return 0
}

CREATED_ITEMS=()
SKIPPED_ITEMS=()

PROGRESS_FILE="$PROJECT_ROOT/.setup-progress"
SETUP_STEPS=(
  deps_checked
  dirs_created
  dirs_verified
  config_scaffolded
  python_deps_installed
  precommit_installed
)
TOTAL_STEPS=${#SETUP_STEPS[@]}

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

SETUP_DIRS=(
  fin-guru-private
  fin-guru-private/fin-guru
  fin-guru-private/fin-guru/strategies
  fin-guru-private/fin-guru/strategies/active
  fin-guru-private/fin-guru/strategies/archive
  fin-guru-private/fin-guru/strategies/risk-management
  fin-guru-private/fin-guru/tickets
  fin-guru-private/fin-guru/analysis
  fin-guru-private/fin-guru/analysis/reports
  fin-guru-private/fin-guru/reports
  fin-guru-private/fin-guru/archive
  fin-guru-private/guides
  fin-guru-private/hedging
  notebooks
  notebooks/updates
  notebooks/retirement-accounts
  notebooks/transactions
  notebooks/tools-needed
  notebooks/tools-needed/done
  fin-guru/data
  imports
  imports/transactions
  imports/retirement
)

create_directory_structure() {
  local dir
  for dir in "${SETUP_DIRS[@]}"; do
    create_dir "$PROJECT_ROOT/$dir"
  done
}

verify_directory_structure() {
  local missing=0
  local dir
  for dir in "${SETUP_DIRS[@]}"; do
    dir="$PROJECT_ROOT/$dir"
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

should_write_file() {
  local target="$1"
  local description="$2"
  local basename_target
  basename_target=$(basename "$target")

  if [ -f "$target" ]; then
    if [ -t 0 ]; then
      printf "  %s (%s) already exists. Overwrite? [y/N] " "$basename_target" "$description"
      read -r response
      if [[ "$response" =~ ^[Yy]$ ]]; then
        return 0
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

  return 0
}

scaffold_user_profile() {
  local user_profile="$PROJECT_ROOT/user-profile.yaml"
  if should_write_file "$user_profile" "user profile template"; then
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
PROFILE_EOF
    printf "  ${GREEN}Created:${NC} %s\n" "$user_profile"
    CREATED_ITEMS+=("file: $user_profile")
  fi
}

scaffold_env_file() {
  local env_file="$PROJECT_ROOT/.env"
  if [ -f "$PROJECT_ROOT/.env.example" ]; then
    if should_write_file "$env_file" "environment config"; then
      cp "$PROJECT_ROOT/.env.example" "$env_file"
      printf "  ${GREEN}Created:${NC} %s (from .env.example)\n" "$env_file"
      CREATED_ITEMS+=("file: $env_file")
    fi
  else
    warn ".env.example not found -- skipping .env creation"
  fi
}

scaffold_private_readme() {
  local private_readme="$PROJECT_ROOT/fin-guru-private/README.md"
  if should_write_file "$private_readme" "private directory README"; then
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
claude --agent fg-onboarding-specialist
```

The specialist will guide you through:
1. Financial assessment
2. Portfolio profile creation
3. Strategy recommendations

Once onboarding is complete, you can use the Finance Orchestrator:

```
claude --agent fg-finance-orchestrator
```
README_EOF
    printf "  ${GREEN}Created:${NC} %s\n" "$private_readme"
    CREATED_ITEMS+=("file: $private_readme")
  fi
}

scaffold_config_files() {
  scaffold_user_profile
  scaffold_env_file
  scaffold_private_readme
}

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

install_pre_commit_hooks() {
  if [ ! -f "$PROJECT_ROOT/.pre-commit-config.yaml" ]; then
    info "No .pre-commit-config.yaml found -- skipping pre-commit setup"
    return 0
  fi

  if ! command -v pre-commit &>/dev/null; then
    info "Installing pre-commit via uv tool..."
    if ! uv tool install pre-commit; then
      warn "Failed to install pre-commit -- you can install manually: uv tool install pre-commit"
      return 0
    fi
  fi

  # Install hooks (default migration mode preserves existing hooks as .legacy)
  if (cd "$PROJECT_ROOT" && pre-commit install); then
    success "Pre-commit hooks installed"
    CREATED_ITEMS+=("Pre-commit hooks (pre-commit install)")
  else
    warn "pre-commit install failed -- you can retry with: cd $PROJECT_ROOT && pre-commit install"
  fi
}

print_summary() {
  printf "\n"
  printf "==========================================\n"
  printf "  ${GREEN}${BOLD}Setup Complete!${NC}\n"
  printf "==========================================\n"
  printf "\n"

  if [ ${#CREATED_ITEMS[@]} -gt 0 ]; then
    printf "  ${BOLD}Created:${NC}\n"
    for item in "${CREATED_ITEMS[@]}"; do
      printf "    - %s\n" "$item"
    done
    printf "\n"
  fi

  if [ ${#SKIPPED_ITEMS[@]} -gt 0 ]; then
    printf "  ${BOLD}Skipped (already existed):${NC}\n"
    for item in "${SKIPPED_ITEMS[@]}"; do
      printf "    - %s\n" "$item"
    done
    printf "\n"
  fi

  printf "  ${BOLD}Next steps:${NC}\n"
  printf "\n"
  printf "  1. Edit .env to add your API keys (optional)\n"
  printf "     yfinance works without API keys for basic market data.\n"
  printf "\n"
  printf "  2. Set FIN_GURU_DATA_ROOT to your instance, or run from that instance.\n"
  printf "     uv run python -m src.cli.onboarding_wizard\n"
  printf "\n"
  printf "  3. After onboarding: claude --agent fg-finance-orchestrator\n"
  printf "\n"
}

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

printf "\n"
printf "==========================================\n"
printf "  ${BOLD}Finance Guru Setup${NC}\n"
printf "==========================================\n"
printf "\n"

show_progress

detect_os
info "Detected OS: $DETECTED_OS (package manager: $PKG_MANAGER)"

header "Checking dependencies..."

if check_all_deps; then
  if [ "$CHECK_DEPS_ONLY" = true ]; then
    printf "\n"
    header "Dependency check complete"
    info "All dependencies are installed and meet version requirements."
    exit 0
  fi
else
  if [ "$CHECK_DEPS_ONLY" = true ]; then
    printf "\n"
    header "Dependency check complete"
    error "Some dependencies are missing. Install them and re-run."
    exit 1
  fi

  printf "\n"
  header "Auto-install missing dependencies"

  for i in "${!FAILED_NAMES[@]}"; do
    prompt_install "${FAILED_NAMES[$i]}" "${FAILED_DEPS[$i]}" || true
  done

  printf "\n"
  header "Re-checking dependencies..."

  if ! check_all_deps; then
    printf "\n"
    error "Please install missing dependencies and re-run setup.sh"
    exit 1
  fi
fi

mark_step_complete "deps_checked"

if is_step_complete "dirs_created"; then
  header "Verifying directory structure..."
  verify_directory_structure
  mark_step_complete "dirs_verified"
else
  header "Creating directory structure..."
  create_directory_structure
  header "Validating directory structure..."
  verify_directory_structure
  mark_step_complete "dirs_created"
  mark_step_complete "dirs_verified"
fi

if is_step_complete "config_scaffolded"; then
  header "Verifying config files..."
  scaffold_config_files
else
  header "Scaffolding config files..."
  scaffold_config_files
  mark_step_complete "config_scaffolded"
fi

if is_step_complete "python_deps_installed"; then
  header "Python dependencies..."
  printf "  ${GREEN}[done]${NC} Python dependencies already installed\n"
else
  header "Installing Python dependencies..."
  install_python_deps
  mark_step_complete "python_deps_installed"
fi

if is_step_complete "precommit_installed"; then
  header "Pre-commit hooks..."
  printf "  ${GREEN}[done]${NC} Pre-commit hooks already installed\n"
else
  header "Installing pre-commit hooks..."
  install_pre_commit_hooks
  mark_step_complete "precommit_installed"
fi

print_summary
