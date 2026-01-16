#!/usr/bin/env bash
# test-runner.sh - Master test runner for Finance Guru
# Usage: ./test-runner.sh [options]
#
# This script consolidates all test execution for the Finance Guru project.
# It runs Python tests using pytest via uv.
#
# Options:
#   --all           Run all tests (default)
#   --unit          Run only unit tests (non-integration)
#   --integration   Run only integration tests (requires API keys)
#   --coverage      Run tests with coverage report
#   --verbose       Extra verbose output
#   --self-test     Run self-diagnostic checks only
#   --help          Show this help message
#
# Examples:
#   ./test-runner.sh                    # Run all tests
#   ./test-runner.sh --unit             # Run only unit tests
#   ./test-runner.sh --coverage         # Run with coverage
#   ./test-runner.sh --integration      # Run integration tests only
#   ./test-runner.sh --self-test        # Validate test runner setup

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

# Default options
RUN_MODE="all"
WITH_COVERAGE=false
VERBOSE=false
SELF_TEST_ONLY=false

# Parse arguments
show_help() {
  echo -e "${CYAN}Finance Guru Master Test Runner${NC}"
  echo ""
  echo "Usage: $0 [options]"
  echo ""
  echo "Options:"
  echo "  --all           Run all tests (default)"
  echo "  --unit          Run only unit tests (non-integration)"
  echo "  --integration   Run only integration tests (requires API keys)"
  echo "  --coverage      Run tests with coverage report"
  echo "  --verbose       Extra verbose output"
  echo "  --self-test     Run self-diagnostic checks only"
  echo "  --help          Show this help message"
  echo ""
  echo "Examples:"
  echo "  $0                    # Run all tests"
  echo "  $0 --unit             # Run only unit tests"
  echo "  $0 --coverage         # Run with coverage"
  echo "  $0 --integration      # Run integration tests only"
  echo "  $0 --self-test        # Validate test runner setup"
  exit 0
}

for arg in "$@"; do
  case $arg in
    --all)
      RUN_MODE="all"
      shift
      ;;
    --unit)
      RUN_MODE="unit"
      shift
      ;;
    --integration)
      RUN_MODE="integration"
      shift
      ;;
    --coverage)
      WITH_COVERAGE=true
      shift
      ;;
    --verbose)
      VERBOSE=true
      shift
      ;;
    --self-test)
      SELF_TEST_ONLY=true
      shift
      ;;
    --help)
      show_help
      ;;
    *)
      echo -e "${RED}Unknown option: $arg${NC}"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

# Change to project root
cd "$PROJECT_ROOT"

# Self-test function
run_self_test() {
  # Temporarily disable exit on error for diagnostic checks
  set +e

  echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
  echo -e "${CYAN}  Test Runner Self-Diagnostic${NC}"
  echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
  echo ""

  local checks_passed=0
  local checks_failed=0

  # Check 1: Verify project root
  echo -e "${BLUE}Check 1: Project root directory${NC}"
  if [ -d "$PROJECT_ROOT" ]; then
    echo -e "${GREEN}✓ Project root exists: $PROJECT_ROOT${NC}"
    ((checks_passed++))
  else
    echo -e "${RED}✗ Project root not found: $PROJECT_ROOT${NC}"
    ((checks_failed++))
  fi

  # Check 2: Verify Python environment
  echo -e "${BLUE}Check 2: Python environment (uv)${NC}"
  if command -v uv &> /dev/null; then
    UV_VERSION=$(uv --version 2>&1 | head -n1)
    echo -e "${GREEN}✓ uv is available: $UV_VERSION${NC}"
    ((checks_passed++))
  else
    echo -e "${RED}✗ uv not found - Python tests will fail${NC}"
    ((checks_failed++))
  fi

  # Check 3: Verify pytest availability
  echo -e "${BLUE}Check 3: pytest availability${NC}"
  if uv run pytest --version &> /dev/null; then
    PYTEST_VERSION=$(uv run pytest --version 2>&1)
    echo -e "${GREEN}✓ pytest is available: $PYTEST_VERSION${NC}"
    ((checks_passed++))
  else
    echo -e "${RED}✗ pytest not available via uv${NC}"
    ((checks_failed++))
  fi

  # Check 4: Verify test directory structure
  echo -e "${BLUE}Check 4: Test directory structure${NC}"
  if [ -d "$PROJECT_ROOT/tests/python" ]; then
    TEST_COUNT=$(find "$PROJECT_ROOT/tests/python" -name "test_*.py" | wc -l | tr -d ' ')
    echo -e "${GREEN}✓ Python test directory exists: $TEST_COUNT test files found${NC}"
    ((checks_passed++))
  else
    echo -e "${RED}✗ Python test directory not found${NC}"
    ((checks_failed++))
  fi

  # Check 5: Verify pyproject.toml
  echo -e "${BLUE}Check 5: pyproject.toml configuration${NC}"
  if [ -f "$PROJECT_ROOT/pyproject.toml" ]; then
    if grep -q "pytest" "$PROJECT_ROOT/pyproject.toml"; then
      echo -e "${GREEN}✓ pyproject.toml exists with pytest config${NC}"
      ((checks_passed++))
    else
      echo -e "${YELLOW}⚠ pyproject.toml exists but no pytest config found${NC}"
      ((checks_passed++))
    fi
  else
    echo -e "${RED}✗ pyproject.toml not found${NC}"
    ((checks_failed++))
  fi

  # Check 6: Verify src directory
  echo -e "${BLUE}Check 6: Source code directory${NC}"
  if [ -d "$PROJECT_ROOT/src" ]; then
    PY_FILES=$(find "$PROJECT_ROOT/src" -name "*.py" | wc -l | tr -d ' ')
    echo -e "${GREEN}✓ Source directory exists: $PY_FILES Python files found${NC}"
    ((checks_passed++))
  else
    echo -e "${RED}✗ Source directory not found${NC}"
    ((checks_failed++))
  fi

  # Check 7: Verify integration test scripts
  echo -e "${BLUE}Check 7: Integration test scripts${NC}"
  if [ -d "$PROJECT_ROOT/tests/integration" ]; then
    INTEGRATION_COUNT=$(find "$PROJECT_ROOT/tests/integration" -name "test_*.sh" | wc -l | tr -d ' ')
    echo -e "${GREEN}✓ Integration test directory exists: $INTEGRATION_COUNT bash test scripts found${NC}"
    ((checks_passed++))
  else
    echo -e "${YELLOW}⚠ Integration test directory not found (optional)${NC}"
    ((checks_passed++))
  fi

  # Check 8: Verify this script is executable
  echo -e "${BLUE}Check 8: Test runner permissions${NC}"
  if [ -x "$SCRIPT_DIR/test-runner.sh" ]; then
    echo -e "${GREEN}✓ Test runner is executable${NC}"
    ((checks_passed++))
  else
    echo -e "${YELLOW}⚠ Test runner is not executable (still works via bash)${NC}"
    ((checks_passed++))
  fi

  # Summary
  echo ""
  echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"

  local total_checks=$((checks_passed + checks_failed))
  if [ $checks_failed -eq 0 ]; then
    echo -e "${GREEN}✓ Self-test PASSED: $checks_passed/$total_checks checks passed${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
    # Re-enable exit on error before returning
    set -e
    return 0
  else
    echo -e "${RED}✗ Self-test FAILED: $checks_failed/$total_checks checks failed${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
    # Re-enable exit on error before returning
    set -e
    return 1
  fi
}

# Run self-test if requested
if [ "$SELF_TEST_ONLY" = true ]; then
  run_self_test
  exit $?
fi

# Header
echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  Finance Guru Master Test Runner${NC}"
echo -e "${CYAN}  Mode: $RUN_MODE${NC}"
if [ "$WITH_COVERAGE" = true ]; then
  echo -e "${CYAN}  Coverage: enabled${NC}"
fi
echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
echo ""

# Build pytest command as array
PYTEST_CMD=(uv run pytest tests/python/)

# Add verbosity
if [ "$VERBOSE" = true ]; then
  PYTEST_CMD+=(-vv)
else
  PYTEST_CMD+=(-v)
fi

# Add test selection based on mode
case $RUN_MODE in
  unit)
    echo -e "${BLUE}Running unit tests only (excluding integration)${NC}"
    PYTEST_CMD+=(-m "not integration")
    ;;
  integration)
    echo -e "${BLUE}Running integration tests only${NC}"
    PYTEST_CMD+=(-m "integration")
    ;;
  all)
    echo -e "${BLUE}Running all tests${NC}"
    ;;
esac

# Add coverage if requested
if [ "$WITH_COVERAGE" = true ]; then
  PYTEST_CMD+=(--cov=src --cov-report=term-missing --cov-report=html)
fi

# Show command being run
if [ "$VERBOSE" = true ]; then
  echo -e "${YELLOW}Command: ${PYTEST_CMD[*]}${NC}"
  echo ""
fi

# Run tests
echo -e "${YELLOW}Executing tests...${NC}"
echo ""

# Capture both output and exit code
set +e
TEST_OUTPUT=$("${PYTEST_CMD[@]}" 2>&1)
TEST_EXIT_CODE=$?
set -e

# Print output
echo "$TEST_OUTPUT"

# Report results
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"

if [ $TEST_EXIT_CODE -eq 0 ]; then
  echo -e "${GREEN}✓ All tests passed${NC}"

  if [ "$WITH_COVERAGE" = true ]; then
    echo -e "${GREEN}Coverage report generated: htmlcov/index.html${NC}"
  fi

  echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
  exit 0
else
  echo -e "${RED}✗ Tests failed (exit code $TEST_EXIT_CODE)${NC}"
  echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
  exit $TEST_EXIT_CODE
fi
