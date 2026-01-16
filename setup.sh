#!/bin/bash

# Finance Guru Setup Script
# Run this after cloning the repository to set up your private data directories

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"  # Script is in project root

echo "=========================================="
echo "  Finance Guru™ Setup Script"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to create directory and report
create_dir() {
    if [ ! -d "$1" ]; then
        mkdir -p "$1"
        echo -e "${GREEN}Created:${NC} $1"
    else
        echo -e "${YELLOW}Exists:${NC} $1"
    fi
}

echo "Step 1: Creating private documentation structure..."
echo ""

# Create fin-guru-private directory structure
create_dir "$PROJECT_ROOT/fin-guru-private"
create_dir "$PROJECT_ROOT/fin-guru-private/fin-guru"
create_dir "$PROJECT_ROOT/fin-guru-private/fin-guru/strategies"
create_dir "$PROJECT_ROOT/fin-guru-private/fin-guru/strategies/active"
create_dir "$PROJECT_ROOT/fin-guru-private/fin-guru/strategies/archive"
create_dir "$PROJECT_ROOT/fin-guru-private/fin-guru/strategies/risk-management"
create_dir "$PROJECT_ROOT/fin-guru-private/fin-guru/tickets"
create_dir "$PROJECT_ROOT/fin-guru-private/fin-guru/analysis"
create_dir "$PROJECT_ROOT/fin-guru-private/fin-guru/analysis/reports"
create_dir "$PROJECT_ROOT/fin-guru-private/fin-guru/reports"
create_dir "$PROJECT_ROOT/fin-guru-private/fin-guru/archive"
create_dir "$PROJECT_ROOT/fin-guru-private/guides"

echo ""
echo "Step 2: Creating portfolio data directories..."
echo ""

# Create notebooks structure for CSV exports and analysis
create_dir "$PROJECT_ROOT/notebooks"
create_dir "$PROJECT_ROOT/notebooks/updates"
create_dir "$PROJECT_ROOT/notebooks/retirement-accounts"
create_dir "$PROJECT_ROOT/notebooks/transactions"
create_dir "$PROJECT_ROOT/notebooks/tools-needed"
create_dir "$PROJECT_ROOT/notebooks/tools-needed/done"

echo ""
echo "Step 3: Creating Finance Guru data directory..."
echo ""

# Create fin-guru/data directory (required for user profile)
create_dir "$PROJECT_ROOT/fin-guru/data"

echo ""
echo "Step 4: Creating user profile template..."
echo ""

# Create user profile template if it doesn't exist
USER_PROFILE="$PROJECT_ROOT/fin-guru/data/user-profile.yaml"
if [ ! -f "$USER_PROFILE" ]; then
    cat > "$USER_PROFILE" << 'EOF'
# Finance Guru™ User Profile Configuration
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

# Google Sheets Integration (optional)
google_sheets:
  portfolio_tracker:
    spreadsheet_id: ""
    url: ""
    purpose: "Finance Guru portfolio tracking"

EOF
    echo -e "${GREEN}Created:${NC} $USER_PROFILE"
else
    echo -e "${YELLOW}Exists:${NC} $USER_PROFILE"
fi

echo ""
echo "Step 5: Creating README for private directory..."
echo ""

# Create README for fin-guru-private
PRIVATE_README="$PROJECT_ROOT/fin-guru-private/README.md"
if [ ! -f "$PRIVATE_README" ]; then
    cat > "$PRIVATE_README" << 'EOF'
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
/fin-guru:agents:onboarding-specialist
```

The specialist will guide you through:
1. Financial assessment
2. Portfolio profile creation
3. Strategy recommendations

Once onboarding is complete, you can use the Finance Orchestrator:

```
/finance-orchestrator
```
EOF
    echo -e "${GREEN}Created:${NC} $PRIVATE_README"
else
    echo -e "${YELLOW}Exists:${NC} $PRIVATE_README"
fi

echo ""
echo "Step 6: Setting up environment..."
echo ""

# Create .env from example if it doesn't exist
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    if [ -f "$PROJECT_ROOT/.env.example" ]; then
        cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
        echo -e "${GREEN}Created:${NC} .env from .env.example"
        echo -e "${YELLOW}Note:${NC} Edit .env to add your API keys"
    fi
else
    echo -e "${YELLOW}Exists:${NC} .env"
fi

echo ""
echo "Step 7: Installing Python dependencies..."
echo ""

# Check if uv is installed
if command -v uv &> /dev/null; then
    cd "$PROJECT_ROOT"
    uv sync
    echo -e "${GREEN}Dependencies installed via uv${NC}"
else
    echo -e "${YELLOW}Warning:${NC} uv not found. Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo "Then run: uv sync"
fi

echo ""
echo "Step 8: Loading Finance Guru agent commands..."
echo ""

# Create ~/.claude/commands if it doesn't exist
GLOBAL_COMMANDS_DIR="$HOME/.claude/commands"
create_dir "$GLOBAL_COMMANDS_DIR"

# Create symlink to Finance Guru agent commands
FIN_GURU_COMMANDS="$PROJECT_ROOT/.claude/commands/fin-guru"
GLOBAL_FIN_GURU_LINK="$GLOBAL_COMMANDS_DIR/fin-guru"

if [ -d "$FIN_GURU_COMMANDS" ]; then
    if [ -L "$GLOBAL_FIN_GURU_LINK" ]; then
        echo -e "${YELLOW}Exists:${NC} Finance Guru commands symlink"
    elif [ -d "$GLOBAL_FIN_GURU_LINK" ]; then
        echo -e "${YELLOW}Warning:${NC} $GLOBAL_FIN_GURU_LINK exists but is not a symlink"
        echo "Skipping symlink creation (manual cleanup needed)"
    else
        ln -s "$FIN_GURU_COMMANDS" "$GLOBAL_FIN_GURU_LINK"
        echo -e "${GREEN}Linked:${NC} Finance Guru agent commands → ~/.claude/commands/fin-guru"
    fi
else
    echo -e "${YELLOW}Warning:${NC} Finance Guru commands not found at $FIN_GURU_COMMANDS"
fi

echo ""
echo "Step 9: Loading Finance Guru skills..."
echo ""

# Create ~/.claude/skills if it doesn't exist
GLOBAL_SKILLS_DIR="$HOME/.claude/skills"
create_dir "$GLOBAL_SKILLS_DIR"

# List of Finance Guru skills to symlink
FIN_GURU_SKILLS=(
    "fin-core"
    "margin-management"
    "PortfolioSyncing"
    "MonteCarlo"
    "retirement-syncing"
    "dividend-tracking"
    "FinanceReport"
    "TransactionSyncing"
    "formula-protection"
)

# Create symlinks for each skill
for skill in "${FIN_GURU_SKILLS[@]}"; do
    SKILL_SOURCE="$PROJECT_ROOT/.claude/skills/$skill"
    SKILL_LINK="$GLOBAL_SKILLS_DIR/$skill"

    if [ -d "$SKILL_SOURCE" ]; then
        if [ -L "$SKILL_LINK" ]; then
            echo -e "${YELLOW}Exists:${NC} $skill skill symlink"
        elif [ -d "$SKILL_LINK" ]; then
            echo -e "${YELLOW}Warning:${NC} $SKILL_LINK exists but is not a symlink"
            echo "Skipping $skill symlink creation (manual cleanup needed)"
        else
            ln -s "$SKILL_SOURCE" "$SKILL_LINK"
            echo -e "${GREEN}Linked:${NC} $skill skill → ~/.claude/skills/$skill"
        fi
    else
        echo -e "${YELLOW}Warning:${NC} Skill not found at $SKILL_SOURCE"
    fi
done

echo ""
echo "Step 10: Running onboarding wizard..."
echo ""

# Check if bun is installed
if command -v bun &> /dev/null; then
    cd "$PROJECT_ROOT"

    # Check if onboarding has already been completed
    if [ -f ".onboarding-state.json" ]; then
        echo -e "${YELLOW}Onboarding state detected.${NC} Resuming..."
        bun run scripts/onboarding/index.ts --resume
    else
        echo "Starting fresh onboarding..."
        bun run scripts/onboarding/index.ts
    fi
else
    echo -e "${YELLOW}Warning:${NC} bun not found. Install with: curl -fsSL https://bun.sh/install | bash"
    echo "Then run: bun run scripts/onboarding/index.ts"
    echo ""
    echo "Skipping onboarding wizard for now."
fi

echo ""
echo "Step 11: Verifying MCP Launchpad setup..."
echo ""

# Check if mcpl is installed
if command -v mcpl &> /dev/null; then
    MCPL_VERSION=$(mcpl --version 2>&1 | head -n1)
    echo -e "${GREEN}Found:${NC} $MCPL_VERSION"
    echo ""

    # Run mcpl verify to check server connections
    echo "Checking MCP server connections..."
    mcpl verify
    echo ""

    # Check for Finance Guru required servers
    echo "Checking Finance Guru required MCP servers..."

    MISSING_SERVERS=()
    SERVER_LIST=$(mcpl list 2>&1)

    # Check for required servers by looking for server name at start of line with bracket
    if ! echo "$SERVER_LIST" | grep -q "^\s*\[exa\]"; then
        MISSING_SERVERS+=("exa")
    fi

    if ! echo "$SERVER_LIST" | grep -q "^\s*\[bright-data\]"; then
        MISSING_SERVERS+=("bright-data")
    fi

    if ! echo "$SERVER_LIST" | grep -q "^\s*\[sequential-thinking\]"; then
        MISSING_SERVERS+=("sequential-thinking")
    fi

    if [ ${#MISSING_SERVERS[@]} -gt 0 ]; then
        echo -e "${YELLOW}Warning:${NC} Missing required MCP servers: ${MISSING_SERVERS[*]}"
        echo "Finance Guru requires these servers for full functionality."
        echo "Configure them in your MCP config (~/.claude/mcp.json or ./mcp.json)"
        echo "See docs/SETUP.md for configuration examples."
        echo ""
    else
        echo -e "${GREEN}All required MCP servers configured!${NC}"
        echo ""
    fi
else
    echo -e "${YELLOW}MCP Launchpad not found${NC}"
    echo ""
    echo "MCP Launchpad (mcpl) provides unified access to all MCP servers."
    echo "Finance Guru uses it for market research, data extraction, and analysis."
    echo ""
    echo "To install mcpl:"
    echo -e "  ${BLUE}uv tool install https://github.com/kenneth-liao/mcp-launchpad.git${NC}"
    echo ""
    echo "After installation, configure required MCP servers:"
    echo "  - exa (market intelligence)"
    echo "  - bright-data (web scraping)"
    echo "  - sequential-thinking (complex reasoning)"
    echo ""
    echo "See docs/SETUP.md for detailed MCP configuration instructions."
    echo ""
fi

echo ""
echo "=========================================="
echo -e "${GREEN}  Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo -e "  1. ${BLUE}Edit .env${NC} to add your API keys (optional):"
echo "     - FINNHUB_API_KEY (for real-time prices)"
echo "     - ITC_API_KEY (for external risk scores)"
echo "     Note: yfinance works without API keys for basic market data."
echo ""
echo -e "  2. ${BLUE}Install MCP Launchpad${NC} if not already installed:"
echo "     uv tool install https://github.com/kenneth-liao/mcp-launchpad.git"
echo ""
echo -e "  3. ${BLUE}Configure MCP servers${NC} in MCP config file"
echo "     Required: exa, bright-data, sequential-thinking"
echo "     Optional: gdrive, perplexity, financial-datasets"
echo "     See docs/SETUP.md for configuration examples."
echo ""
echo -e "  4. ${BLUE}If you skipped onboarding, run it manually${NC}:"
echo "     bun run scripts/onboarding/index.ts"
echo ""
echo "  5. After onboarding, use the Finance Orchestrator:"
echo "     /finance-orchestrator"
echo ""
echo "See docs/index.md for full documentation."
echo ""
