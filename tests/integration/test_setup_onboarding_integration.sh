#!/bin/bash

# Integration Test: setup.sh
# Verifies directory creation, config scaffolding, idempotent re-runs,
# --check-deps-only flag, and --help flag.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TEST_DIR="/tmp/finance-guru-test-$(date +%s)"
TEST_DIR_DEPS="/tmp/finance-guru-test-deps-$(date +%s)"
PASS_COUNT=0
FAIL_COUNT=0

printf "====================================================\n"
printf "  Integration Test: setup.sh\n"
printf "====================================================\n"
printf "\n"
printf "Test directory: %s\n" "$TEST_DIR"
printf "Project root:   %s\n" "$PROJECT_ROOT"
printf "\n"

# ============================================================
# Test Helpers
# ============================================================

log_step() {
  printf "${BLUE}>> %s${NC}\n" "$1"
}

log_pass() {
  printf "  ${GREEN}[PASS]${NC} %s\n" "$1"
  PASS_COUNT=$((PASS_COUNT + 1))
}

log_fail() {
  printf "  ${RED}[FAIL]${NC} %s\n" "$1"
  FAIL_COUNT=$((FAIL_COUNT + 1))
}

assert_dir_exists() {
  if [ -d "$1" ]; then
    log_pass "Directory exists: $1"
  else
    log_fail "Directory missing: $1"
  fi
}

assert_file_exists() {
  if [ -f "$1" ]; then
    log_pass "File exists: $1"
  else
    log_fail "File missing: $1"
  fi
}

assert_file_not_exists() {
  if [ ! -f "$1" ]; then
    log_pass "File correctly absent: $1"
  else
    log_fail "File should not exist: $1"
  fi
}

assert_dir_not_exists() {
  if [ ! -d "$1" ]; then
    log_pass "Directory correctly absent: $1"
  else
    log_fail "Directory should not exist: $1"
  fi
}

assert_grep() {
  local file="$1"
  local pattern="$2"
  local description="$3"
  if grep -q "$pattern" "$file" 2>/dev/null; then
    log_pass "$description"
  else
    log_fail "$description (pattern '$pattern' not found in $file)"
  fi
}

assert_no_grep() {
  local file="$1"
  local pattern="$2"
  local description="$3"
  if ! grep -q "$pattern" "$file" 2>/dev/null; then
    log_pass "$description"
  else
    log_fail "$description (pattern '$pattern' found in $file)"
  fi
}

# ============================================================
# Cleanup
# ============================================================

cleanup() {
  printf "\nCleaning up...\n"
  rm -rf "$TEST_DIR" "$TEST_DIR_DEPS" 2>/dev/null
  printf "Done.\n"
}

trap cleanup EXIT

# ============================================================
# PATH Setup
# ============================================================
# If python3 does not meet 3.12+, check for python3.12 and create
# a PATH override so setup.sh's dependency check passes.

TMPBIN=""
PYTHON3_VERSION=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
PYTHON3_MAJOR=$(echo "$PYTHON3_VERSION" | cut -d. -f1)
PYTHON3_MINOR=$(echo "$PYTHON3_VERSION" | cut -d. -f2)

if [ "$PYTHON3_MAJOR" -lt 3 ] || { [ "$PYTHON3_MAJOR" -eq 3 ] && [ "$PYTHON3_MINOR" -lt 12 ]; }; then
  if command -v python3.12 &>/dev/null; then
    TMPBIN=$(mktemp -d)
    ln -s "$(command -v python3.12)" "$TMPBIN/python3"
    export PATH="$TMPBIN:$PATH"
    printf "  Note: python3 is %s, using python3.12 via PATH override\n\n" "$PYTHON3_VERSION"
  else
    printf "  ${RED}Error: python3 is %s and python3.12 not found. Cannot run tests.${NC}\n" "$PYTHON3_VERSION"
    exit 1
  fi
fi

# ============================================================
# Test Setup: Create temp directory with required files
# ============================================================

log_step "Setting up test environment"

mkdir -p "$TEST_DIR"
cp "$PROJECT_ROOT/setup.sh" "$TEST_DIR/"
cp "$PROJECT_ROOT/pyproject.toml" "$TEST_DIR/" 2>/dev/null || true
cp "$PROJECT_ROOT/uv.lock" "$TEST_DIR/" 2>/dev/null || true
cp "$PROJECT_ROOT/.env.example" "$TEST_DIR/" 2>/dev/null || true

# Create minimal src/ structure so uv sync can find the project
if [ -d "$PROJECT_ROOT/src" ]; then
  mkdir -p "$TEST_DIR/src"
  # Copy only __init__.py files to satisfy package discovery
  find "$PROJECT_ROOT/src" -name "__init__.py" | while read -r f; do
    local_path="${f#$PROJECT_ROOT/}"
    mkdir -p "$TEST_DIR/$(dirname "$local_path")"
    cp "$f" "$TEST_DIR/$local_path"
  done
fi

log_pass "Test environment created at $TEST_DIR"

# ============================================================
# Test 1: First run creates everything
# ============================================================

log_step "Test 1: First run creates everything"

(cd "$TEST_DIR" && bash setup.sh < /dev/null > /tmp/setup-test-first.log 2>&1) || {
  log_fail "First run of setup.sh failed (exit code $?)"
  printf "  Log: /tmp/setup-test-first.log\n"
}

# Verify directories
assert_dir_exists "$TEST_DIR/fin-guru-private"
assert_dir_exists "$TEST_DIR/fin-guru-private/fin-guru/strategies/active"
assert_dir_exists "$TEST_DIR/fin-guru-private/fin-guru/strategies/archive"
assert_dir_exists "$TEST_DIR/fin-guru-private/fin-guru/strategies/risk-management"
assert_dir_exists "$TEST_DIR/fin-guru-private/fin-guru/tickets"
assert_dir_exists "$TEST_DIR/fin-guru-private/fin-guru/analysis"
assert_dir_exists "$TEST_DIR/fin-guru-private/fin-guru/analysis/reports"
assert_dir_exists "$TEST_DIR/fin-guru-private/fin-guru/reports"
assert_dir_exists "$TEST_DIR/fin-guru-private/fin-guru/archive"
assert_dir_exists "$TEST_DIR/fin-guru-private/guides"
assert_dir_exists "$TEST_DIR/fin-guru-private/hedging"
assert_dir_exists "$TEST_DIR/notebooks"
assert_dir_exists "$TEST_DIR/notebooks/updates"
assert_dir_exists "$TEST_DIR/notebooks/retirement-accounts"
assert_dir_exists "$TEST_DIR/notebooks/transactions"
assert_dir_exists "$TEST_DIR/notebooks/tools-needed"
assert_dir_exists "$TEST_DIR/notebooks/tools-needed/done"
assert_dir_exists "$TEST_DIR/fin-guru/data"

# Verify config files
assert_file_exists "$TEST_DIR/fin-guru/data/user-profile.yaml"
assert_file_exists "$TEST_DIR/fin-guru-private/README.md"

# Verify .env created (if .env.example was present)
if [ -f "$TEST_DIR/.env.example" ]; then
  assert_file_exists "$TEST_DIR/.env"
fi

# Verify .setup-progress
assert_file_exists "$TEST_DIR/.setup-progress"
assert_grep "$TEST_DIR/.setup-progress" "^deps_checked$" ".setup-progress contains deps_checked"
assert_grep "$TEST_DIR/.setup-progress" "^dirs_created$" ".setup-progress contains dirs_created"
assert_grep "$TEST_DIR/.setup-progress" "^dirs_verified$" ".setup-progress contains dirs_verified"
assert_grep "$TEST_DIR/.setup-progress" "^config_scaffolded$" ".setup-progress contains config_scaffolded"
assert_grep "$TEST_DIR/.setup-progress" "^python_deps_installed$" ".setup-progress contains python_deps_installed"

# Verify summary printed
assert_grep "/tmp/setup-test-first.log" "Setup Complete" "Summary printed on first run"

printf "\n"

# ============================================================
# Test 2: --check-deps-only does not modify filesystem
# ============================================================

log_step "Test 2: --check-deps-only does not modify filesystem"

mkdir -p "$TEST_DIR_DEPS"
cp "$PROJECT_ROOT/setup.sh" "$TEST_DIR_DEPS/"

(cd "$TEST_DIR_DEPS" && bash setup.sh --check-deps-only < /dev/null > /tmp/setup-test-deps.log 2>&1)
DEPS_EXIT=$?

if [ "$DEPS_EXIT" -eq 0 ]; then
  log_pass "--check-deps-only exited with code 0"
else
  log_fail "--check-deps-only exited with code $DEPS_EXIT (expected 0)"
fi

assert_dir_not_exists "$TEST_DIR_DEPS/fin-guru-private"
assert_file_not_exists "$TEST_DIR_DEPS/.setup-progress"
assert_file_not_exists "$TEST_DIR_DEPS/.env"

printf "\n"

# ============================================================
# Test 3: Idempotent re-run
# ============================================================

log_step "Test 3: Idempotent re-run"

(cd "$TEST_DIR" && bash setup.sh < /dev/null > /tmp/setup-test-second.log 2>&1) || {
  log_fail "Second run of setup.sh failed"
}

assert_grep "/tmp/setup-test-second.log" "Resuming" "Output contains 'Resuming' on second run"
assert_no_grep "/tmp/setup-test-second.log" "FAIL" "No FAIL messages in second run"

# Verify directory structure still intact
assert_dir_exists "$TEST_DIR/fin-guru-private/fin-guru/strategies/active"
assert_dir_exists "$TEST_DIR/fin-guru-private/hedging"
assert_dir_exists "$TEST_DIR/fin-guru/data"

# Verify no duplicate entries in .setup-progress
DUP_COUNT=$(sort "$TEST_DIR/.setup-progress" | uniq -d | wc -l | tr -d ' ')
if [ "$DUP_COUNT" -eq 0 ]; then
  log_pass "No duplicate entries in .setup-progress"
else
  log_fail ".setup-progress has $DUP_COUNT duplicate entries"
fi

printf "\n"

# ============================================================
# Test 4: Missing directory detected on re-run
# ============================================================

log_step "Test 4: Missing directory detected on re-run"

rm -rf "$TEST_DIR/fin-guru-private/hedging"

(cd "$TEST_DIR" && bash setup.sh < /dev/null > /tmp/setup-test-missing.log 2>&1) || {
  log_fail "Re-run with missing directory failed"
}

assert_dir_exists "$TEST_DIR/fin-guru-private/hedging"
assert_grep "/tmp/setup-test-missing.log" "Recreated.*hedging" "Output shows hedging was recreated"

# Verify other directories still exist
assert_dir_exists "$TEST_DIR/fin-guru-private/fin-guru/strategies/active"
assert_dir_exists "$TEST_DIR/fin-guru-private/guides"

printf "\n"

# ============================================================
# Test 5: --help flag
# ============================================================

log_step "Test 5: --help flag"

HELP_OUTPUT=$(bash "$TEST_DIR/setup.sh" --help 2>&1)
HELP_EXIT=$?

if [ "$HELP_EXIT" -eq 0 ]; then
  log_pass "--help exited with code 0"
else
  log_fail "--help exited with code $HELP_EXIT"
fi

if echo "$HELP_OUTPUT" | grep -q "Usage:"; then
  log_pass "--help output contains 'Usage:'"
else
  log_fail "--help output missing 'Usage:'"
fi

if echo "$HELP_OUTPUT" | grep -q "check-deps-only"; then
  log_pass "--help mentions --check-deps-only"
else
  log_fail "--help missing --check-deps-only mention"
fi

printf "\n"

# ============================================================
# Results
# ============================================================

TOTAL=$((PASS_COUNT + FAIL_COUNT))

printf "====================================================\n"
if [ "$FAIL_COUNT" -eq 0 ]; then
  printf "  ${GREEN}All %d assertions passed${NC}\n" "$TOTAL"
else
  printf "  ${RED}%d of %d assertions failed${NC}\n" "$FAIL_COUNT" "$TOTAL"
fi
printf "====================================================\n"
printf "\n"
printf "Summary:\n"
printf "  Passed: %d\n" "$PASS_COUNT"
printf "  Failed: %d\n" "$FAIL_COUNT"
printf "\n"
printf "Test logs:\n"
printf "  First run:   /tmp/setup-test-first.log\n"
printf "  Deps only:   /tmp/setup-test-deps.log\n"
printf "  Second run:  /tmp/setup-test-second.log\n"
printf "  Missing dir: /tmp/setup-test-missing.log\n"
printf "\n"

# Clean up tmpbin if created
[ -n "$TMPBIN" ] && rm -rf "$TMPBIN"

if [ "$FAIL_COUNT" -gt 0 ]; then
  exit 1
fi

exit 0
