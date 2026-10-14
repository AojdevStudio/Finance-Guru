#!/bin/bash

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RESET='\033[0m'

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

log_step() {
    echo -e "${BLUE}▶ $1${RESET}"
}

log_success() {
    echo -e "${GREEN}✓ $1${RESET}"
}

log_error() {
    echo -e "${RED}✗ $1${RESET}"
    cleanup
    exit 1
}

cleanup() {
    echo ""
    echo "Cleaning up test directory..."
    if [ -d "$TEST_DIR" ]; then
        rm -rf "$TEST_DIR"
        log_success "Test directory removed"
    fi
}

trap cleanup EXIT

log_step "Test 1: Setting up test git repository"
mkdir -p "$TEST_DIR"
cd "$TEST_DIR"
git init -q
cp "$PROJECT_ROOT/.gitignore" "$TEST_DIR/"
log_success "Test repository created with .gitignore"

log_step "Test 2: Creating sensitive test files"

mkdir -p notebooks/updates
mkdir -p notebooks/retirement-accounts
mkdir -p notebooks/transactions
mkdir -p fin-guru-private/fin-guru/analysis
mkdir -p fin-guru-private/fin-guru/tickets
mkdir -p fin-guru/data
mkdir -p research/finance
mkdir -p private
mkdir -p sensitive
mkdir -p credentials

echo "Date,Ticker,Shares,Price,Value" > notebooks/updates/Portfolio_Positions_SAMPLE.csv
echo "2026-01-12,TSLA,100,350.00,35000.00" >> notebooks/updates/Portfolio_Positions_SAMPLE.csv

echo "Date,Ticker,Shares,Price,Value" > notebooks/updates/dividend.csv
echo "2026-01-12,SCHD,500,75.00,37500.00" >> notebooks/updates/dividend.csv

echo "Date,Account,Type,Amount" > notebooks/retirement-accounts/OfxDownload.csv
echo "2026-01-12,401k,Vanguard,125000.00" >> notebooks/retirement-accounts/OfxDownload.csv

echo "Date,Description,Amount" > notebooks/transactions/History_for_Account_EXAMPLE123.csv
echo "2026-01-12,Margin Interest,-125.50" >> notebooks/transactions/History_for_Account_EXAMPLE123.csv

echo "ticker,score,recommendation" > fin-guru-private/fin-guru/analysis/watchlist.csv
echo "PLTR,8.5,BUY" >> fin-guru-private/fin-guru/analysis/watchlist.csv

echo "# Buy Ticket - TSLA Position" > fin-guru-private/fin-guru/tickets/buy-ticket-2026-01-12.md
echo "Entry: $350, Target: $400" >> fin-guru-private/fin-guru/tickets/buy-ticket-2026-01-12.md

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

echo "API_KEY=secret123456" > .env
echo "PLAID_CLIENT_ID=test_client_id" > .env.local
echo "FIDELITY_PASSWORD=supersecret" > credentials.env

echo "# Market Analysis - TSLA" > research/finance/tsla-analysis.md

echo "sensitive data" > private/account-details.txt
echo "sensitive data" > sensitive/portfolio.txt
echo "api_key=secret" > credentials/fidelity.key

log_success "Sensitive test files created"

log_step "Test 3: Verifying CSV files are ignored"

csv_files=(
    "notebooks/updates/Portfolio_Positions_SAMPLE.csv"
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

log_step "Test 5: Verifying fin-guru-private directory is ignored"

private_files=(
    "fin-guru-private/fin-guru/analysis/watchlist.csv"
    "fin-guru-private/fin-guru/tickets/buy-ticket-2026-01-12.md"
)

for file in "${private_files[@]}"; do
    if git check-ignore -q "$file"; then
        log_success "Private file ignored: $file"
    else
        log_error "Private file NOT ignored: $file"
    fi
done

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

log_step "Test 7: Verifying user profile is ignored"

if git check-ignore -q "fin-guru/data/user-profile.yaml"; then
    log_success "User profile ignored"
else
    log_error "User profile NOT ignored"
fi

log_step "Test 8: Verifying research directory is ignored"

if git check-ignore -q "research/finance/tsla-analysis.md"; then
    log_success "Research files ignored"
else
    log_error "Research files NOT ignored"
fi

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

log_step "Test 10: Verifying .gitignore is tracked"

git add .gitignore
if git ls-files --error-unmatch .gitignore > /dev/null 2>&1; then
    log_success ".gitignore is tracked by git"
else
    log_error ".gitignore is NOT tracked by git"
fi

log_step "Test 11: Verifying git status shows no sensitive files"

git add -A 2>/dev/null || true
tracked_files=$(git ls-files)

if echo "$tracked_files" | grep -E '\.(csv|env)$' > /dev/null; then
    log_error "Sensitive files found in git tracking"
fi

if echo "$tracked_files" | grep -E 'notebooks/|fin-guru-private/|research/|private/|sensitive/|credentials/' > /dev/null; then
    log_error "Sensitive directories found in git tracking"
fi

log_success "No sensitive files tracked by git"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✓ All tests passed!${RESET}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Summary:"
echo "  ✓ CSV files (portfolio positions, dividends, transactions) are ignored"
echo "  ✓ Environment files (.env, .env.local, *.env) are ignored"
echo "  ✓ fin-guru-private directory (tickets, analysis) is ignored"
echo "  ✓ notebooks directory (all financial data) is ignored"
echo "  ✓ User profile (fin-guru/data/user-profile.yaml) is ignored"
echo "  ✓ Research directory is ignored"
echo "  ✓ Private directories (private/, sensitive/, credentials/) are ignored"
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

exit 0
