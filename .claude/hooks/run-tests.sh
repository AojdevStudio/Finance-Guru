#!/bin/bash
#
# Bun Hook Test Suite Runner
#
# This script runs the self-testing Bun test suite for Claude Code hooks.
# It validates that the test infrastructure is functional and all hooks
# are tested correctly.
#
# Usage:
#   ./run-tests.sh              # Run all tests
#   ./run-tests.sh --watch      # Run tests in watch mode
#   ./run-tests.sh --coverage   # Run tests with coverage
#   ./run-tests.sh --suite-only # Run only the self-testing suite
#

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🧪 Bun Hook Test Suite Runner${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check if bun is installed
if ! command -v bun &> /dev/null; then
    echo -e "${RED}❌ Error: Bun is not installed${NC}"
    echo ""
    echo "Install Bun with:"
    echo "  curl -fsSL https://bun.sh/install | bash"
    exit 1
fi

echo -e "${GREEN}✓ Bun runtime detected: $(bun --version)${NC}"
echo ""

# Parse command line arguments
WATCH_MODE=false
COVERAGE_MODE=false
SUITE_ONLY=false

for arg in "$@"; do
    case $arg in
        --watch)
            WATCH_MODE=true
            shift
            ;;
        --coverage)
            COVERAGE_MODE=true
            shift
            ;;
        --suite-only)
            SUITE_ONLY=true
            shift
            ;;
        *)
            # Unknown option
            ;;
    esac
done

# Build test command
TEST_CMD="bun test"

if [ "$SUITE_ONLY" = true ]; then
    echo -e "${YELLOW}Running self-testing suite only...${NC}"
    TEST_CMD="$TEST_CMD tests/test_suite.test.ts"
else
    echo -e "${YELLOW}Running all tests...${NC}"
    TEST_CMD="$TEST_CMD tests/"
fi

if [ "$COVERAGE_MODE" = true ]; then
    TEST_CMD="$TEST_CMD --coverage"
fi

echo ""
echo -e "${BLUE}Command: ${TEST_CMD}${NC}"
echo ""

# Run tests
if eval "$TEST_CMD"; then
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}❌ Tests failed${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    exit 1
fi
