---
title: "Troubleshooting Guide"
description: "Comprehensive troubleshooting for installation, configuration, and operational issues"
category: setup
---

# Troubleshooting Guide

Comprehensive troubleshooting for Finance Guru™ installation, configuration, and operational issues.

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Python & Dependencies](#python--dependencies)
3. [MCP Server Issues](#mcp-server-issues)
4. [Claude Code Integration](#claude-code-integration)
5. [Hooks & Skills](#hooks--skills)
6. [API & Data Issues](#api--data-issues)
7. [Onboarding Wizard](#onboarding-wizard)
8. [Git & Privacy](#git--privacy)
9. [Performance & Limits](#performance--limits)
10. [Testing & Development](#testing--development)
11. [Common Error Messages](#common-error-messages)

---

## Installation Issues

### Setup Script Fails

**Problem**: `./setup.sh` exits with errors

**Symptoms**:
```bash
./setup.sh: line 42: uv: command not found
# OR
Permission denied: ./setup.sh
# OR
setup.sh: No such file or directory
```

**Solutions**:

**Missing `uv` command**:
```bash
# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add to PATH (if needed)
export PATH="$HOME/.cargo/bin:$PATH"

# Verify installation
uv --version

# Re-run setup
./setup.sh
```

**Permission denied**:
```bash
# Make setup script executable
chmod +x setup.sh

# Run setup
./setup.sh
```

**File not found**:
```bash
# Verify you're in project root
pwd
# Should show: /path/to/family-office

# List files to confirm setup.sh exists
ls -la setup.sh

# If missing, you may have cloned incorrectly
git clone https://github.com/YOUR-USERNAME/family-office.git
cd family-office
./setup.sh
```

---

### Directory Structure Not Created

**Problem**: `fin-guru-private/` or `notebooks/updates/` missing after setup

**Check creation manually**:
```bash
# Check if directories exist
ls -la fin-guru-private/
ls -la notebooks/updates/

# If missing, create manually
mkdir -p fin-guru-private/fin-guru/analysis
mkdir -p notebooks/updates

# Verify .gitignore protection
git check-ignore fin-guru-private/
# Should output: fin-guru-private/
```

**Re-run setup sections**:
```bash
# If only directories are missing, create them manually
# Then continue with onboarding
bun run scripts/onboarding/index.ts
```

---

### .env File Not Created

**Problem**: `.env` file missing after setup

**Check and fix**:
```bash
# Verify .env.example exists
ls -la .env.example

# Copy template to .env
cp .env.example .env

# Verify creation
ls -la .env

# Edit to add API keys
nano .env
```

**Verify .env is gitignored**:
```bash
# Check .env is in .gitignore
cat .gitignore | grep "^\.env$"

# Verify git ignores it
git check-ignore .env
# Should output: .env

# If not ignored, add to .gitignore
echo ".env" >> .gitignore
```

---

## Python & Dependencies

### ModuleNotFoundError

**Problem**: Python can't find installed packages

**Symptoms**:
```bash
uv run python src/analysis/risk_metrics_cli.py TSLA
# ModuleNotFoundError: No module named 'pandas'
```

**Solutions**:

**Check Python version**:
```bash
# Verify Python 3.12+
python --version
uv run python --version

# If wrong version, install Python 3.12+
# macOS: brew install python@3.12
# Linux: sudo apt install python3.12
```

**Reinstall dependencies**:
```bash
# Sync dependencies
uv sync

# Force refresh
uv sync --refresh

# Verify pandas is installed
uv run python -c "import pandas; print(pandas.__version__)"
```

**Check virtual environment**:
```bash
# Verify .venv exists
ls -la .venv/

# If missing, recreate
uv sync

# Always run with uv
uv run python src/analysis/risk_metrics_cli.py TSLA
```

---

### yfinance Returns No Data

**Problem**: Market data tools return empty results

**Symptoms**:
```bash
uv run python src/utils/market_data.py AAPL
# No data returned for AAPL
# OR
# Empty DataFrame
```

**Diagnose the issue**:
```bash
# Test yfinance directly
uv run python -c "
import yfinance as yf
ticker = yf.Ticker('AAPL')
hist = ticker.history(period='5d')
print(hist)
"

# If empty, check internet connection
ping yahoo.com

# Try different ticker
uv run python src/utils/market_data.py SPY
```

**Common causes & fixes**:

**Rate limiting**:
```bash
# yfinance may be rate-limited
# Wait 5-10 minutes and retry
sleep 600 && uv run python src/utils/market_data.py AAPL
```

**Invalid ticker symbol**:
```bash
# Verify ticker on Yahoo Finance
# Visit: https://finance.yahoo.com/quote/AAPL

# Try alternate symbol
# E.g., BRK.B instead of BRKB
uv run python src/utils/market_data.py BRK.B
```

**Network/proxy issues**:
```bash
# Check network connectivity
curl -I https://query1.finance.yahoo.com/v8/finance/chart/AAPL

# If proxy required, set environment
export HTTP_PROXY=http://proxy.example.com:8080
export HTTPS_PROXY=http://proxy.example.com:8080
```

---

### Import Errors for Custom Modules

**Problem**: Can't import Finance Guru modules

**Symptoms**:
```bash
uv run python -c "from src.analysis.risk_metrics import RiskMetrics"
# ModuleNotFoundError: No module named 'src'
```

**Solutions**:

**Run from project root**:
```bash
# Verify current directory
pwd
# Should be: /path/to/family-office

# If in wrong directory, navigate to root
cd /path/to/family-office

# Retry import
uv run python -c "from src.analysis.risk_metrics import RiskMetrics"
```

**Check PYTHONPATH**:
```bash
# Add project root to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/path/to/family-office"

# Or run with uv (handles paths automatically)
uv run python src/analysis/risk_metrics_cli.py TSLA
```

---

## MCP Server Issues

### MCP Launchpad Not Working

**Problem**: `mcpl` command not found or not working

**Symptoms**:
```
bash: mcpl: command not found
# OR
Error: Cannot connect to MCP daemon
```

**Solutions**:

**Check if MCP Launchpad is installed**:
```bash
# Test mcpl command
mcpl --help

# If not found, check installation location
which mcpl

# Typical installation paths:
# - /usr/local/bin/mcpl
# - ~/.local/bin/mcpl
# - ~/bin/mcpl
```

**Verify MCP servers in settings.json**:
```bash
# MCP Launchpad reads from Claude Code settings
cat .claude/settings.json | grep -A 20 mcpServers

# Should show configured servers like:
# "mcpServers": {
#   "exa": { ... },
#   "gdrive": { ... }
# }
```

**Test MCP connection**:
```bash
# Verify all MCP servers are working
mcpl verify

# Should show connection status for each server
# ✓ exa - Connected
# ✓ gdrive - Connected
# ✗ finnhub - Connection failed
```

**Search for available tools**:
```bash
# Find tools across all MCP servers
mcpl search "list projects"

# Should return relevant tools with descriptions
```

**Restart MCP daemon**:
```bash
# Stop MCP daemon
mcpl session stop

# Daemon will auto-restart on next mcpl command
mcpl verify
```

---

### MCP Server Not Connected

**Problem**: Claude Code can't connect to MCP servers

**Symptoms**:
```
Error: MCP server 'exa' not responding
# OR
Failed to initialize MCP server
# OR
Connection timeout
```

**Diagnose connection**:
```bash
# Test MCP server command manually
npx -y @exa-labs/mcp-server-exa

# Should not error (may hang waiting for input - that's OK)
# Press Ctrl+C to exit

# Check if command is in PATH
which npx
# Should show path to npx
```

**Use MCP Launchpad to diagnose**:
```bash
# Verify which servers are connected
mcpl verify

# Check server configuration
mcpl config

# Test specific server
mcpl list exa

# Should list all exa tools if connected
```

**Verify settings.json syntax**:
```bash
# Validate JSON syntax
cat .claude/settings.json | python -m json.tool

# Should output valid JSON
# If syntax error, fix manually

# Example valid configuration:
# {
#   "mcpServers": {
#     "exa": {
#       "command": "npx",
#       "args": ["-y", "@exa-labs/mcp-server-exa"],
#       "env": {
#         "EXA_API_KEY": "your_key_here"
#       }
#     }
#   }
# }
```

**Restart Claude Code**:
```bash
# Exit Claude Code (Ctrl+C or /exit)
# Re-launch
claude

# MCP servers reconnect on startup
```

---

### Invalid API Key for MCP Server

**Problem**: MCP server rejects API key

**Symptoms**:
```
Error: Invalid EXA_API_KEY
# OR
401 Unauthorized
# OR
403 Forbidden
```

**Verify API key**:
```bash
# Check .env or settings.json for key
cat .env | grep EXA_API_KEY
cat .claude/settings.json | grep EXA_API_KEY

# Remove extra spaces, quotes, or newlines
# WRONG: EXA_API_KEY=" abc123 "
# RIGHT: EXA_API_KEY=abc123
```

**Test key directly**:
```bash
# Test Exa API key
curl -X POST https://api.exa.ai/search \
  -H "x-api-key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'

# Should return JSON response, not 401/403
```

**Regenerate key**:
```bash
# If key invalid, regenerate on provider dashboard
# Exa: https://dashboard.exa.ai/
# Finnhub: https://finnhub.io/dashboard
# OpenAI: https://platform.openai.com/api-keys

# Update .claude/settings.json or .env
nano .env

# Restart Claude Code
```

---

### MCP Server Timeout

**Problem**: MCP server connection times out

**Increase timeout**:
```bash
# Set environment variable for longer timeout
export MCP_TIMEOUT=120  # 120 seconds

# Restart Claude Code
claude
```

**Check network**:
```bash
# Test network latency
ping api.exa.ai

# Test HTTPS connectivity
curl -I https://api.exa.ai

# If behind proxy, configure
export HTTP_PROXY=http://proxy.example.com:8080
export HTTPS_PROXY=http://proxy.example.com:8080
```

---

## Claude Code Integration

### "Claude Code command not found"

**Problem**: `claude` command not available

**Install/reinstall Claude Code**:
```bash
# Install Claude Code CLI
curl -fsSL https://claude.ai/install.sh | bash

# Add to PATH (if needed)
export PATH="$HOME/.local/bin:$PATH"

# Add to shell profile for persistence
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
# OR (for bash)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc

# Reload shell
source ~/.zshrc  # or source ~/.bashrc

# Verify installation
claude --version
```

---

### Context Overload / Token Limit Errors

**Problem**: "Token limit exceeded" or context too large

**Symptoms**:
```
Error: Context window exceeded
# OR
Request too large (>200k tokens)
```

**Clear old session data**:
```bash
# Remove old conversation data
rm -rf .claude/data/sessions/*

# Restart Claude Code
claude

# Finance Guru typically uses ~25% of 200k context
```

**Check for runaway hooks**:
```bash
# Test hooks individually
bun .claude/hooks/load-fin-core-config.ts
# Should output reasonable amount of context

bash .claude/hooks/skill-activation-prompt.sh "test"
# Should output activation message, not walls of text

# If hook outputs too much, debug it
cat .claude/hooks/load-fin-core-config.ts
```

**Optimize context usage**:
```bash
# Use focused queries
# GOOD: "Analyze TSLA risk"
# BAD: "Analyze everything about TSLA NVDA PLTR AAPL including all metrics"

# Close and reopen Claude Code periodically
# to clear conversation history
```

---

### Skills Not Appearing in /help

**Problem**: Finance Guru agents don't show up in Claude Code

**Check skill files exist**:
```bash
# List agent skill files
ls -la .claude/commands/fin-guru/agents/

# Should show:
# - finance-orchestrator.md
# - market-researcher.md
# - quant-analyst.md
# - strategy-advisor.md
# - etc.
```

**Verify CLAUDE.md references skills**:
```bash
# Check CLAUDE.md mentions agents
cat CLAUDE.md | grep -i agent

# Should reference .claude/commands/fin-guru/agents/
```

**Restart Claude Code**:
```bash
# Skills are loaded on startup
# Exit and re-enter
claude

# Type /help to verify skills appear
```

---

## Hooks & Skills

### TypeScript Hooks Failing

**Problem**: Hooks written in TypeScript/Bun not executing

**Symptoms**:
```
Error: Cannot find module 'tsx'
# OR
Error: bun: command not found
# OR
Hook execution failed with exit code 1
```

**Solutions**:

**Install tsx (for npx tsx execution)**:
```bash
# Install tsx globally
npm install -g tsx

# Verify installation
npx tsx --version

# Test hook manually
npx tsx .claude/hooks/load-fin-core-config.ts
```

**Install bun (for bun execution)**:
```bash
# Install bun
curl -fsSL https://bun.sh/install | bash

# Add to PATH (if needed)
export PATH="$HOME/.local/bin:$PATH"

# Reload shell
source ~/.zshrc  # or source ~/.bashrc

# Verify installation
bun --version

# Test hook manually
bun .claude/hooks/load-fin-core-config.ts
```

**Check hook file permissions**:
```bash
# Hooks must be executable
ls -la .claude/hooks/*.ts
ls -la .claude/hooks/*.sh

# If not executable (missing x flag)
chmod +x .claude/hooks/load-fin-core-config.ts
chmod +x .claude/hooks/skill-activation-prompt.ts
chmod +x .claude/hooks/post-tool-use-tracker.ts
chmod +x .claude/hooks/skill-activation-prompt.sh
```

**Verify settings.json format** (New Format):
```bash
# Check settings.json structure
cat .claude/settings.json

# Should use new nested hooks format:
# "SessionStart": [
#   {
#     "hooks": [
#       {
#         "type": "command",
#         "command": "npx tsx $CLAUDE_PROJECT_DIR/.claude/hooks/load-fin-core-config.ts"
#       }
#     ]
#   }
# ]

# NOT the old format:
# "SessionStart": {
#   "command": "bun",
#   "args": [".claude/hooks/load-fin-core-config.ts"]
# }
```

---

### SessionStart Hook Not Running

**Problem**: Finance core context doesn't load on startup

**Expected behavior**:
```
✅ PAI Context successfully loaded...
```

**If missing**:
```bash
# Check hook file exists
ls -la .claude/hooks/load-fin-core-config.ts

# Run hook manually to test
npx tsx .claude/hooks/load-fin-core-config.ts
# OR
bun .claude/hooks/load-fin-core-config.ts

# Should output PAI CORE CONTEXT message
```

**Verify tsx/bun is installed**:
```bash
# Check tsx
npx tsx --version

# If missing tsx
npm install -g tsx

# Check bun version
bun --version

# If missing bun, install
curl -fsSL https://bun.sh/install | bash

# Re-run hook
npx tsx .claude/hooks/load-fin-core-config.ts
```

**Check settings.json hook configuration**:
```bash
# Verify hooks section (new format)
cat .claude/settings.json | grep -A 10 SessionStart

# Should show (NEW FORMAT):
# "SessionStart": [
#   {
#     "hooks": [
#       {
#         "type": "command",
#         "command": "npx tsx $CLAUDE_PROJECT_DIR/.claude/hooks/load-fin-core-config.ts"
#       }
#     ]
#   }
# ]
```

---

### Skill Activation Hook Not Triggering

**Problem**: Skills don't activate on keywords

**Test hook manually**:
```bash
# Run hook with test prompt
bash .claude/hooks/skill-activation-prompt.sh "analyze TSLA"

# Should output skill activation message
```

**Verify hook permissions**:
```bash
# Check executable permission
ls -la .claude/hooks/skill-activation-prompt.sh

# Should show: -rwxr-xr-x (executable)

# If not executable
chmod +x .claude/hooks/skill-activation-prompt.sh
```

**Check settings.json**:
```bash
# Verify UserPromptSubmit hook
cat .claude/settings.json | grep -A 5 UserPromptSubmit

# Should show:
# "UserPromptSubmit": {
#   "command": "bash",
#   "args": [".claude/hooks/skill-activation-prompt.sh", "{prompt}"]
# }
```

---

## API & Data Issues

### Finnhub Rate Limit Exceeded

**Problem**: "429 Too Many Requests" from Finnhub

**Rate limits**:
- Free tier: 60 API calls per minute
- Finance Guru batches calls efficiently

**Strategies**:

**Batch ticker requests**:
```bash
# Instead of individual calls
uv run python src/utils/market_data.py TSLA --realtime
uv run python src/utils/market_data.py PLTR --realtime

# Batch into single call
uv run python src/utils/market_data.py TSLA PLTR NVDA --realtime
```

**Add delays between calls**:
```bash
# For portfolio loops
for ticker in TSLA PLTR NVDA AAPL GOOGL; do
    uv run python src/utils/market_data.py $ticker --realtime
    sleep 2  # 2-second delay
done
```

**Upgrade to paid tier** (if needed):
- Visit [finnhub.io/pricing](https://finnhub.io/pricing)
- Paid tiers: 300-600 calls/minute

---

### ITC Risk API Returns Unsupported Asset

**Problem**: "Asset not supported by ITC Risk Models"

**Supported assets**:

**TradFi (13 assets)**:
```
TSLA, AAPL, MSTR, NFLX, SP500, DXY,
XAUUSD, XAGUSD, XPDUSD, PL, HG, NICKEL
```

**Crypto (29 assets)**:
```
BTC, ETH, SOL, XRP, ADA, DOGE, LINK,
MATIC, DOT, AVAX, UNI, ATOM, LTC, etc.
```

**Check supported tickers**:
```bash
# List all supported tickers
uv run python src/analysis/itc_risk_cli.py --list-supported

# Verify universe
uv run python src/analysis/itc_risk_cli.py TSLA --universe tradfi
```

**Fallback for unsupported assets**:
```bash
# Use internal risk metrics instead
uv run python src/analysis/risk_metrics_cli.py GOOGL --days 90 --benchmark SPY

# Provides VaR, CVaR, Sharpe, Sortino, Max Drawdown
```

---

### Environment Variables Not Loading

**Problem**: API keys in `.env` but code can't access them

**Verify .env location**:
```bash
# .env MUST be in project root
ls -la .env

# Should show: /path/to/family-office/.env
```

**Test environment loading**:
```bash
# Verify dotenv installed
uv sync

# Test loading
uv run python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('FINNHUB_API_KEY:', os.getenv('FINNHUB_API_KEY'))
"

# Should print your API key (or None if not set)
```

**Check .env syntax**:
```bash
# Verify no extra spaces or quotes
cat .env

# WRONG: FINNHUB_API_KEY = " abc123 "
# RIGHT: FINNHUB_API_KEY=abc123
```

---

## Onboarding Wizard

### Wizard Crashes on Startup

**Problem**: Onboarding wizard exits immediately

**Check state file**:
```bash
# Check for corrupted state
cat .onboarding-state.json

# If JSON invalid, delete and restart
rm .onboarding-state.json

# Re-run onboarding
bun run scripts/onboarding/index.ts
```

**Verify bun is working**:
```bash
# Test bun installation
bun --version

# Test wizard script exists
ls -la scripts/onboarding/index.ts

# Run with debug output
DEBUG=* bun run scripts/onboarding/index.ts
```

---

### user-profile.yaml Not Generated

**Problem**: Onboarding completes but profile file missing

**Check output directory**:
```bash
# Verify fin-guru/data/ exists
ls -la fin-guru/data/

# If missing, create manually
mkdir -p fin-guru/data

# Re-run onboarding
bun run scripts/onboarding/index.ts
```

**Check file permissions**:
```bash
# Verify write permissions
touch fin-guru/data/test.yaml
rm fin-guru/data/test.yaml

# If permission denied, fix permissions
chmod -R u+w fin-guru/data/
```

**Manual creation**:
```bash
# If wizard fails, create template manually
cp fin-guru/data/user-profile.template.yaml fin-guru/data/user-profile.yaml

# Edit manually
nano fin-guru/data/user-profile.yaml
```

---

### Wizard Prompts Don't Appear

**Problem**: Onboarding runs but shows no questions

**Check terminal compatibility**:
```bash
# Verify terminal supports interactive prompts
echo $TERM
# Should show: xterm-256color, screen-256color, etc.

# Try different terminal
# macOS: Terminal.app, iTerm2
# Linux: gnome-terminal, konsole
```

**Run in verbose mode**:
```bash
# Debug onboarding script
bun run scripts/onboarding/index.ts --verbose
```

---

## Git & Privacy

### Accidentally Committed Private Data

**DANGER**: If sensitive data was pushed to GitHub, act immediately

**Assess damage**:
```bash
# Check what was committed
git log --all --full-history -- fin-guru/data/user-profile.yaml

# If found in history, data was exposed
```

**Immediate actions**:

1. **Contact GitHub support** - Request repository deletion if data highly sensitive
2. **Revoke exposed API keys** - Rotate all keys immediately
3. **Force-remove from history**:

```bash
# NUCLEAR OPTION: Rewrites git history
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch fin-guru/data/user-profile.yaml" \
  --prune-empty --tag-name-filter cat -- --all

# Force push (DANGER: breaks collaborators' repos)
git push origin --force --all
```

**Prevention checklist**:
```bash
# Before every commit
git status --ignored

# Verify .gitignore working
git check-ignore .env
git check-ignore fin-guru/data/user-profile.yaml
git check-ignore fin-guru-private/

# Check staged files
git diff --cached

# Verify no sensitive data
git diff --cached | grep -i "api_key\|password\|balance"
```

---

### Can't Pull Upstream Updates

**Problem**: Forked repo can't sync with original

**Setup upstream remote** (one-time):
```bash
# Add original repo as upstream
git remote add upstream https://github.com/ORIGINAL-AUTHOR/family-office.git

# Verify remotes
git remote -v
# Should show:
# origin    https://github.com/YOUR-USERNAME/family-office.git
# upstream  https://github.com/ORIGINAL-AUTHOR/family-office.git
```

**Pull and merge updates**:
```bash
# Fetch upstream changes
git fetch upstream

# Merge into your main branch
git checkout main
git merge upstream/main

# Your .gitignore prevents private data conflicts
```

**Resolve merge conflicts**:
```bash
# If conflicts occur
git status

# Resolve conflicts manually
# IMPORTANT: Never accept upstream changes to:
# - .env
# - fin-guru/data/user-profile.yaml
# - fin-guru-private/*

# Keep your version for private files
git checkout --ours .env
git checkout --ours fin-guru/data/user-profile.yaml

# Complete merge
git add .
git commit -m "Merge upstream updates"
```

---

### .gitignore Not Working

**Problem**: Git tracks files that should be ignored

**Check .gitignore syntax**:
```bash
# View .gitignore
cat .gitignore

# Should include:
# .env
# fin-guru/data/user-profile.yaml
# fin-guru-private/
# notebooks/updates/*.csv
```

**Untrack files already committed**:
```bash
# Remove from git index (keeps local file)
git rm --cached .env
git rm --cached fin-guru/data/user-profile.yaml
git rm --cached -r fin-guru-private/

# Commit removal
git commit -m "Remove private files from tracking"

# Verify ignored
git status --ignored
```

**Test .gitignore**:
```bash
# Check specific files
git check-ignore .env
git check-ignore fin-guru/data/user-profile.yaml

# Should output file path (confirmed ignored)
```

---

## Performance & Limits

### Slow Tool Execution

**Problem**: CLI tools take too long

**Expected performance**:
- Risk metrics: 2-5 seconds (90-day period)
- Momentum analysis: 1-3 seconds
- Correlation matrix: 3-8 seconds (4-5 tickers)

**If significantly slower**:

**Check network latency**:
```bash
# yfinance fetches data from Yahoo Finance
time curl -I https://query1.finance.yahoo.com/v8/finance/chart/AAPL

# Should complete in < 1 second
```

**Reduce data period**:
```bash
# Instead of 252 days (1 year)
uv run python src/analysis/risk_metrics_cli.py TSLA --days 252

# Use 90 days (quarter) for faster results
uv run python src/analysis/risk_metrics_cli.py TSLA --days 90
```

**Profile Python execution**:
```bash
# Run with profiling
uv run python -m cProfile src/analysis/risk_metrics_cli.py TSLA --days 90

# Identify bottlenecks in output
```

---

### High Memory Usage

**Problem**: Python processes use too much RAM

**Check memory usage**:
```bash
# Monitor during execution
top -o MEM

# Or use htop
htop
```

**Optimize for large datasets**:
```bash
# Reduce historical period
uv run python src/analysis/risk_metrics_cli.py TSLA --days 90  # Instead of 252

# Process tickers sequentially instead of parallel
for ticker in TSLA PLTR NVDA; do
    uv run python src/analysis/risk_metrics_cli.py $ticker --days 90
done
```

---

### Disk Space Issues

**Problem**: Running out of storage

**Check space usage**:
```bash
# Check project size
du -sh /path/to/family-office

# Identify large directories
du -sh * | sort -h

# Common culprits:
# - node_modules/
# - .venv/
# - .claude/data/sessions/
```

**Clean up**:
```bash
# Remove old Python cache
find . -type d -name "__pycache__" -exec rm -rf {} +

# Remove old Claude Code sessions
rm -rf .claude/data/sessions/*

# Re-install dependencies (if needed)
uv sync
```

---

## Common Error Messages

### Error: "Ticker not found"

**Problem**: yfinance can't find ticker symbol

**Solutions**:
```bash
# Verify ticker on Yahoo Finance
# Visit: https://finance.yahoo.com/quote/AAPL

# Try alternate symbol format
# E.g., BRK.B instead of BRKB
uv run python src/utils/market_data.py BRK.B

# For international stocks, add exchange suffix
# E.g., Toyota: 7203.T (Tokyo)
uv run python src/utils/market_data.py 7203.T
```

---

### Error: "division by zero"

**Problem**: Calculations fail on insufficient data

**Cause**: Stock has < required data points (e.g., newly IPO'd)

**Solutions**:
```bash
# Reduce period for new stocks
uv run python src/analysis/risk_metrics_cli.py NEWCO --days 30

# Or check if ticker is valid
uv run python src/utils/market_data.py NEWCO
```

---

### Error: "JSON decode error"

**Problem**: MCP server or API returns invalid JSON

**Diagnose**:
```bash
# Test API directly
curl -X POST https://api.exa.ai/search \
  -H "x-api-key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}' | jq .

# Should output valid JSON

# If invalid, check API key or service status
```

---

### Error: "Permission denied"

**Problem**: Can't write to file or directory

**Fix permissions**:
```bash
# Check permissions
ls -la fin-guru/data/

# Fix ownership
chmod -R u+w fin-guru/data/

# Verify write access
touch fin-guru/data/test.txt
rm fin-guru/data/test.txt
```

---

### Error: "Command not found: uv"

**Problem**: `uv` package manager not in PATH

**Install uv**:
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add to PATH
export PATH="$HOME/.cargo/bin:$PATH"

# Add to shell profile
echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.zshrc

# Reload shell
source ~/.zshrc

# Verify
uv --version
```

---

## Testing & Development

### Test Suite Failing

**Problem**: Tests fail when running test suite

**Symptoms**:
```bash
bun test
# Some tests failing
```

**Common test failures**:

**1. Python tests failing**:
```bash
# Run Python tests separately
uv run pytest tests/python/

# If ModuleNotFoundError
uv sync

# If specific test fails
uv run pytest tests/python/test_yaml_generation.py -v
```

**2. Onboarding tests failing**:
```bash
# Run onboarding tests
bun test tests/onboarding/

# Clean up test artifacts
rm -rf .onboarding-state.json
rm -rf .env.test

# Re-run tests
bun test tests/onboarding/
```

**3. Hook tests failing**:
```bash
# Run hook tests
bun test .claude/hooks/tests/

# Verify hooks are executable
chmod +x .claude/hooks/*.ts
chmod +x .claude/hooks/*.sh

# Test hooks manually
npx tsx .claude/hooks/load-fin-core-config.ts
bun .claude/hooks/skill-activation-prompt.ts
```

---

---

## Getting Help

If your issue isn't covered here:

### 1. Check Other Documentation
- [SETUP.md](SETUP.md) - Installation guide
- [api-keys.md](api-keys.md) - API key configuration
- [hooks.md](../reference/hooks.md) - Hook system details
- [api.md](../reference/api.md) - API reference

### 2. Search GitHub Issues
- Visit: [GitHub Issues](https://github.com/YOUR-USERNAME/family-office/issues)
- Search for your error message
- Check closed issues for solutions

### 3. Open a New Issue

Include the following information:

```bash
# System info
uname -a
python --version
uv --version
bun --version
claude --version

# Error message (full output)
# [Paste error here]

# Steps to reproduce
# 1. ...
# 2. ...

# Expected behavior
# [What should happen]

# Actual behavior
# [What actually happens]
```

### 4. Community Resources
- Finance Guru Discord: [Link TBD]
- BMAD-CORE™ Documentation: [Link TBD]
- Claude Code Docs: [claude.ai/docs](https://claude.ai/docs)

---

<p align="center">
  <strong>Finance Guru™ v2.0.0</strong><br>
  Your AI-powered private family office.
</p>
