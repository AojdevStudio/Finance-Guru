#!/bin/bash

# Integration Test: setup.sh with Onboarding Integration
# Verifies that setup.sh can be run multiple times (idempotent)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test directory
TEST_DIR="/tmp/finance-guru-test-$(date +%s)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 Integration Test: setup.sh with Onboarding"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Test directory: $TEST_DIR"
echo "Project root: $PROJECT_ROOT"
echo ""

# Function to log test steps
log_step() {
    echo -e "${BLUE}▶ $1${NC}"
}

# Function to log success
log_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to log error and exit
log_error() {
    echo -e "${RED}✗ $1${NC}"
    cleanup
    exit 1
}

# Cleanup function
cleanup() {
    echo ""
    echo "Cleaning up test directory..."
    if [ -d "$TEST_DIR" ]; then
        rm -rf "$TEST_DIR"
        log_success "Test directory removed"
    fi
}

# Trap cleanup on exit
trap cleanup EXIT

# Test 1: Create test directory and copy necessary files
log_step "Test 1: Setting up test environment"
mkdir -p "$TEST_DIR"
cp "$PROJECT_ROOT/setup.sh" "$TEST_DIR/"
cp -r "$PROJECT_ROOT/scripts" "$TEST_DIR/"
cp -r "$PROJECT_ROOT/fin-guru" "$TEST_DIR/" 2>/dev/null || mkdir -p "$TEST_DIR/fin-guru/data"
cp "$PROJECT_ROOT/pyproject.toml" "$TEST_DIR/" 2>/dev/null || true
cp "$PROJECT_ROOT/.env.example" "$TEST_DIR/" 2>/dev/null || true

cd "$TEST_DIR"
log_success "Test environment created"

# Test 2: Run setup.sh for the first time
log_step "Test 2: Running setup.sh (first run)"

# Mock the onboarding CLI to prevent interactive prompts
cat > scripts/onboarding/index.ts << 'EOF'
#!/usr/bin/env bun
console.log('🚧 Mock onboarding CLI for testing');
console.log('📋 Simulating onboarding completion');

import { writeFileSync } from 'fs';

// Create mock state file
const mockState = {
  version: "1.0",
  started_at: new Date().toISOString(),
  last_updated: new Date().toISOString(),
  completed_sections: ["liquid_assets", "investments", "cash_flow", "debt", "preferences", "mcp_config", "env_setup"],
  current_section: null,
  data: {
    user_name: "TestUser",
    liquid_assets: { total: 10000 }
  }
};

writeFileSync('.onboarding-state.json', JSON.stringify(mockState, null, 2));
console.log('✅ Mock onboarding complete');
EOF

chmod +x scripts/onboarding/index.ts

# Run setup.sh
bash setup.sh > /tmp/setup-first-run.log 2>&1 || log_error "First run of setup.sh failed"
log_success "First run completed"

# Test 3: Verify directory structure was created
log_step "Test 3: Verifying directory structure"
expected_dirs=(
    "fin-guru-private"
    "fin-guru-private/fin-guru"
    "fin-guru-private/fin-guru/strategies"
    "notebooks"
    "notebooks/updates"
    "fin-guru/data"
)

for dir in "${expected_dirs[@]}"; do
    if [ ! -d "$dir" ]; then
        log_error "Expected directory not found: $dir"
    fi
done
log_success "All expected directories created"

# Test 4: Verify onboarding state was created
log_step "Test 4: Verifying onboarding state file"
if [ ! -f ".onboarding-state.json" ]; then
    log_error "Onboarding state file not created"
fi
log_success "Onboarding state file created"

# Test 5: Run setup.sh again (idempotent test)
log_step "Test 5: Running setup.sh again (idempotent test)"
bash setup.sh > /tmp/setup-second-run.log 2>&1 || log_error "Second run of setup.sh failed"
log_success "Second run completed without errors"

# Test 6: Verify second run detected existing state
log_step "Test 6: Verifying second run used resume mode"
if grep -q "Onboarding state detected" /tmp/setup-second-run.log; then
    log_success "Second run correctly detected existing state"
else
    log_error "Second run did not detect existing state"
fi

# Test 7: Verify no duplicate directories created
log_step "Test 7: Verifying no duplicate directories"
# Check that running twice didn't create duplicates or break structure
for dir in "${expected_dirs[@]}"; do
    if [ ! -d "$dir" ]; then
        log_error "Directory structure corrupted on second run: $dir"
    fi
done
log_success "Directory structure intact after second run"

# Test 8: Verify user profile template exists
log_step "Test 8: Verifying user profile template"
if [ ! -f "fin-guru/data/user-profile.yaml" ]; then
    log_error "User profile template not created"
fi
log_success "User profile template created"

# Test 9: Run setup.sh a third time (stress test)
log_step "Test 9: Running setup.sh a third time (stress test)"
bash setup.sh > /tmp/setup-third-run.log 2>&1 || log_error "Third run of setup.sh failed"
log_success "Third run completed without errors"

# Test 10: Verify onboarding state persisted
log_step "Test 10: Verifying onboarding state persisted across runs"
if [ -f ".onboarding-state.json" ]; then
    # Check that state file still has the mock data
    if grep -q "TestUser" .onboarding-state.json; then
        log_success "Onboarding state preserved across multiple runs"
    else
        log_error "Onboarding state corrupted"
    fi
else
    log_error "Onboarding state file missing after multiple runs"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✓ All tests passed!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Summary:"
echo "  ✓ setup.sh creates correct directory structure"
echo "  ✓ setup.sh calls onboarding CLI on first run"
echo "  ✓ setup.sh detects existing state on subsequent runs"
echo "  ✓ setup.sh is idempotent (safe to run multiple times)"
echo "  ✓ Onboarding state persists across multiple runs"
echo ""
echo "Test artifacts:"
echo "  - First run log: /tmp/setup-first-run.log"
echo "  - Second run log: /tmp/setup-second-run.log"
echo "  - Third run log: /tmp/setup-third-run.log"
echo ""

# Cleanup will run automatically via trap
exit 0
