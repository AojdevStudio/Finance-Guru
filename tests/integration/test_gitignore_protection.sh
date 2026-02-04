#!/bin/bash

# Integration Test: .gitignore Private Data Protection
# Verifies that sensitive financial data is properly ignored by git

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test directory
TEST_DIR="/tmp/finance-guru-gitignore-test-$(date +%s)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 Integration Test: .gitignore Private Data Protection"
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

# Test 1: Create test git repository
log_step "Test 1: Setting up test git repository"
mkdir -p "$TEST_DIR"
cd "$TEST_DIR"
git init -q
cp "$PROJECT_ROOT/.gitignore" "$TEST_DIR/"
log_success "Test repository created with .gitignore"

# Test 2: Create sensitive financial files
log_step "Test 2: Creating sensitive test files"

# Create directory structure
mkdir -p notebooks/updates
mkdir -p notebooks/retirement-accounts
mkdir -p notebooks/transactions
mkdir -p fin-guru-private/fin-guru/analysis
mkdir -p fin-guru-private/fin-guru/strategies
mkdir -p fin-guru/data
mkdir -p research/finance
mkdir -p private
mkdir -p sensitive
mkdir -p credentials

# Create test CSV files (portfolio positions)
echo "Date,Ticker,Shares,Price,Value" > notebooks/updates/Portfolio_Positions_Jan-12-2026.csv
echo "2026-01-12,TSLA,100,350.00,35000.00" >> notebooks/updates/Portfolio_Positions_Jan-12-2026.csv

echo "Date,Ticker,Shares,Price,Value" > notebooks/updates/dividend.csv
echo "2026-01-12,SCHD,500,75.00,37500.00" >> notebooks/updates/dividend.csv

echo "Date,Account,Type,Amount" > notebooks/retirement-accounts/OfxDownload.csv
echo "2026-01-12,401k,Vanguard,125000.00" >> notebooks/retirement-accounts/OfxDownload.csv

echo "Date,Description,Amount" > notebooks/transactions/History_for_Account_EXAMPLE123.csv
echo "2026-01-12,Margin Interest,-125.50" >> notebooks/transactions/History_for_Account_EXAMPLE123.csv

# Create test analysis files
echo "ticker,score,recommendation" > fin-guru-private/fin-guru/analysis/watchlist.csv
echo "PLTR,8.5,BUY" >> fin-guru-private/fin-guru/analysis/watchlist.csv

echo "# Buy Ticket - TSLA Position" > fin-guru-private/fin-guru/strategies/buy-ticket-2026-01-12.md
echo "Entry: $350, Target: $400" >> fin-guru-private/fin-guru/strategies/buy-ticket-2026-01-12.md

# Create user profile
cat > fin-guru/data/user-profile.yaml << 'EOF'
user:
  name: Test User
  risk_tolerance: moderate
assets:
  liquid: 100000
  investments: 500000
debt:
  margin_balance: 50000
EOF

# Create environment files
echo "API_KEY=secret123456" > .env
echo "PLAID_CLIENT_ID=test_client_id" > .env.local
echo "FIDELITY_PASSWORD=supersecret" > credentials.env

# Create private research
echo "# Market Analysis - TSLA" > research/finance/tsla-analysis.md

# Create private directories
echo "sensitive data" > private/account-details.txt
echo "sensitive data" > sensitive/portfolio.txt
echo "api_key=secret" > credentials/fidelity.key

log_success "Sensitive test files created"

# Test 3: Verify CSV files are ignored
log_step "Test 3: Verifying CSV files are ignored"

csv_files=(
    "notebooks/updates/Portfolio_Positions_Jan-12-2026.csv"
    "notebooks/updates/dividend.csv"
    "notebooks/retirement-accounts/OfxDownload.csv"
    "notebooks/transactions/History_for_Account_EXAMPLE123.csv"
    "fin-guru-private/fin-guru/analysis/watchlist.csv"
)

for file in "${csv_files[@]}"; do
    if git check-ignore -q "$file"; then
        log_success "CSV ignored: $file"
    else
        log_error "CSV NOT ignored: $file"
    fi
done

# Test 4: Verify environment files are ignored
log_step "Test 4: Verifying environment files are ignored"

env_files=(
    ".env"
    ".env.local"
    "credentials.env"
)

for file in "${env_files[@]}"; do
    if git check-ignore -q "$file"; then
        log_success "Env file ignored: $file"
    else
        log_error "Env file NOT ignored: $file"
    fi
done

# Test 5: Verify fin-guru-private directory is ignored
log_step "Test 5: Verifying fin-guru-private directory is ignored"

private_files=(
    "fin-guru-private/fin-guru/analysis/watchlist.csv"
    "fin-guru-private/fin-guru/strategies/buy-ticket-2026-01-12.md"
)

for file in "${private_files[@]}"; do
    if git check-ignore -q "$file"; then
        log_success "Private file ignored: $file"
    else
        log_error "Private file NOT ignored: $file"
    fi
done

# Test 6: Verify notebooks directory is ignored
log_step "Test 6: Verifying notebooks directory is ignored"

notebook_dirs=(
    "notebooks/updates"
    "notebooks/retirement-accounts"
    "notebooks/transactions"
)

for dir in "${notebook_dirs[@]}"; do
    if git check-ignore -q "$dir"; then
        log_success "Notebook dir ignored: $dir"
    else
        log_error "Notebook dir NOT ignored: $dir"
    fi
done

# Test 7: Verify user profile is ignored
log_step "Test 7: Verifying user profile is ignored"

if git check-ignore -q "fin-guru/data/user-profile.yaml"; then
    log_success "User profile ignored"
else
    log_error "User profile NOT ignored"
fi

# Test 8: Verify research directory is ignored
log_step "Test 8: Verifying research directory is ignored"

if git check-ignore -q "research/finance/tsla-analysis.md"; then
    log_success "Research files ignored"
else
    log_error "Research files NOT ignored"
fi

# Test 9: Verify private directories are ignored
log_step "Test 9: Verifying private/sensitive/credentials directories are ignored"

private_dirs=(
    "private/account-details.txt"
    "sensitive/portfolio.txt"
    "credentials/fidelity.key"
)

for file in "${private_dirs[@]}"; do
    if git check-ignore -q "$file"; then
        log_success "Private dir file ignored: $file"
    else
        log_error "Private dir file NOT ignored: $file"
    fi
done

# Test 10: Verify .gitignore itself is tracked
log_step "Test 10: Verifying .gitignore is tracked"

git add .gitignore
if git ls-files --error-unmatch .gitignore > /dev/null 2>&1; then
    log_success ".gitignore is tracked by git"
else
    log_error ".gitignore is NOT tracked by git"
fi

# Test 11: Verify git status shows no sensitive files
log_step "Test 11: Verifying git status shows no sensitive files"

git add -A 2>/dev/null || true
tracked_files=$(git ls-files)

# Check that no sensitive patterns are in tracked files
if echo "$tracked_files" | grep -E '\.(csv|env)$' > /dev/null; then
    log_error "Sensitive files found in git tracking"
fi

if echo "$tracked_files" | grep -E 'notebooks/|fin-guru-private/|research/|private/|sensitive/|credentials/' > /dev/null; then
    log_error "Sensitive directories found in git tracking"
fi

log_success "No sensitive files tracked by git"

# Test 12: Verify beads data is ignored
log_step "Test 12: Verifying beads tracking data is ignored"

mkdir -p .beads
echo '{"id":"test-1"}' > .beads/issues.jsonl
echo '{"type":"interaction"}' > .beads/interactions.jsonl

beads_files=(
    ".beads/issues.jsonl"
    ".beads/interactions.jsonl"
)

for file in "${beads_files[@]}"; do
    if git check-ignore -q "$file"; then
        log_success "Beads data ignored: $file"
    else
        log_error "Beads data NOT ignored: $file"
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✓ All tests passed!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Summary:"
echo "  ✓ CSV files (portfolio positions, dividends, transactions) are ignored"
echo "  ✓ Environment files (.env, .env.local, *.env) are ignored"
echo "  ✓ fin-guru-private directory (strategies, analysis) is ignored"
echo "  ✓ notebooks directory (all financial data) is ignored"
echo "  ✓ User profile (fin-guru/data/user-profile.yaml) is ignored"
echo "  ✓ Research directory is ignored"
echo "  ✓ Private directories (private/, sensitive/, credentials/) are ignored"
echo "  ✓ Beads tracking data (.beads/issues.jsonl, interactions.jsonl) is ignored"
echo "  ✓ .gitignore itself is properly tracked"
echo ""
echo "Protected file types:"
echo "  - Portfolio CSV exports (Fidelity, Vanguard)"
echo "  - Transaction history"
echo "  - Dividend tracking"
echo "  - User financial profile"
echo "  - API keys and credentials"
echo "  - Private analysis and strategies"
echo "  - Research documents"
echo "  - Issue tracking data"
echo ""

# Cleanup will run automatically via trap
exit 0
