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

# --- Phase functions (Plan 02) ---
# create_directory_structure
# scaffold_config_files
# install_python_deps
# print_summary

printf "\n"
header "Next steps"
info "Dependencies verified. Directory creation and config scaffolding coming in next plan."
printf "\n"
