#!/bin/bash

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🧪 Bun Hook Test Suite Runner${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if ! command -v bun &> /dev/null; then
    echo -e "${RED}❌ Error: Bun is not installed${NC}"
    echo ""
    echo "Install Bun with:"
    echo "  curl -fsSL https://bun.sh/install | bash"
    exit 1
fi

echo -e "${GREEN}✓ Bun runtime detected: $(bun --version)${NC}"
echo ""

COVERAGE_MODE=false

for arg in "$@"; do
    case $arg in
        --coverage)
            COVERAGE_MODE=true
            ;;
        *)
            echo -e "${RED}❌ Unknown option: ${arg}${NC}" >&2
            echo "Usage: $0 [--coverage]" >&2
            exit 2
            ;;
    esac
done

echo -e "${YELLOW}Running all tests...${NC}"
TEST_CMD="bun test tests/"

if [ "$COVERAGE_MODE" = true ]; then
    TEST_CMD="$TEST_CMD --coverage"
fi

echo ""
echo -e "${BLUE}Command: ${TEST_CMD}${NC}"
echo ""

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
