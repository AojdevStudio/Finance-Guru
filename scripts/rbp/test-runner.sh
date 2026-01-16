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
#   --help          Show this help message
#
# Examples:
#   ./test-runner.sh                    # Run all tests
#   ./test-runner.sh --unit             # Run only unit tests
#   ./test-runner.sh --coverage         # Run with coverage
#   ./test-runner.sh --integration      # Run integration tests only

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
  echo "  --help          Show this help message"
  echo ""
  echo "Examples:"
  echo "  $0                    # Run all tests"
  echo "  $0 --unit             # Run only unit tests"
  echo "  $0 --coverage         # Run with coverage"
  echo "  $0 --integration      # Run integration tests only"
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
