# Finance Guru™ Setup Guide

Complete installation and configuration guide for Finance Guru™ - your AI-powered private family office.

## Quick Start (5 Minutes)

**Already have the prerequisites?** Jump straight to setup:

```bash
# 1. Fork and clone
git clone https://github.com/YOUR-USERNAME/family-office.git
cd family-office

# 2. Run setup
./setup.sh

# 3. Start Claude Code
claude

# 4. Run onboarding
/fin-guru:agents:onboarding-specialist
```

See [Prerequisites](#prerequisites) below if you need to install tools first.

---

## Table of Contents

1. [Quick Start](#quick-start-5-minutes)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Verification](#verification)
6. [First Use](#first-use)
7. [Troubleshooting](#troubleshooting)
8. [Post-Installation Checklist](#post-installation-checklist)
9. [Security Checklist](#security-checklist)
10. [Next Steps](#next-steps)

---

## Prerequisites

Before installing Finance Guru, ensure you have the following tools installed on your machine.

### Required Tools

| Tool | Version | Installation | Verify |
|------|---------|-------------|---------|
| **Python** | 3.12+ | [python.org/downloads](https://www.python.org/downloads/) | `python --version` |
| **uv** | Latest | `curl -LsSf https://astral.sh/uv/install.sh \| sh` | `uv --version` |
| **Claude Code** | Latest | `curl -fsSL https://claude.ai/install.sh \| bash` | `claude --version` |
| **Bun** | Latest | `curl -fsSL https://bun.sh/install \| bash` | `bun --version` |
| **Git** | 2.0+ | [git-scm.com](https://git-scm.com/) | `git --version` |

### Optional (Recommended)

| Tool | Purpose | Installation |
|------|---------|-------------|
| **Docker** | For Google Drive MCP (portfolio syncing) | [docs.docker.com/get-docker](https://docs.docker.com/get-docker/) |

### System Requirements

- **OS**: macOS, Linux, or WSL2 on Windows
- **RAM**: 4GB minimum, 8GB+ recommended
- **Disk Space**: 2GB for dependencies and data
- **Network**: Internet connection for market data APIs

---

## Installation

### Step 1: Fork the Repository (Recommended)

**Important**: Finance Guru is designed to be forked for privacy.

```bash
# 1. Fork the repository on GitHub
# Visit: https://github.com/ORIGINAL-AUTHOR/family-office
# Click "Fork" → Select your account

# 2. Clone YOUR fork (not the original)
git clone https://github.com/YOUR-USERNAME/family-office.git
cd family-office
```

**Why fork?**
- Your financial data stays in your private fork
- Pull upstream updates without exposing personal info
- Maintain separate development branches safely

### Step 2: Run Setup Script

The setup script creates directories, templates, and installs dependencies.

```bash
# Make setup script executable (if needed)
chmod +x setup.sh

# Run setup
./setup.sh
```

**What `setup.sh` does:**
1. ✅ Creates `fin-guru-private/` directory structure (gitignored)
2. ✅ Creates `notebooks/updates/` for CSV imports (gitignored)
3. ✅ Creates `fin-guru/data/` for user profile (gitignored)
4. ✅ Generates `user-profile.yaml` template
5. ✅ Copies `.env.example` → `.env`
6. ✅ Installs Python dependencies via `uv sync`
7. ✅ Runs onboarding wizard (interactive)

### Step 3: Verify Installation

```bash
# Check Python dependencies
uv sync
uv run python --version  # Should show 3.12+

# Check project structure
tree -L 2 -I 'node_modules|__pycache__|.venv'

# Expected output:
# family-office/
# ├── .claude/
# │   ├── hooks/
# │   └── settings.json
# ├── fin-guru/
# │   ├── agents/
# │   ├── data/              # Created by setup.sh
# │   └── config.yaml
# ├── fin-guru-private/      # Created by setup.sh (gitignored)
# │   └── fin-guru/
# ├── notebooks/
# │   └── updates/           # Created by setup.sh (gitignored)
# ├── src/
# │   ├── analysis/
# │   ├── strategies/
# │   └── utils/
# └── tests/
```

---

## Configuration

### MCP Servers

Finance Guru requires MCP servers for external integrations. Configure them in Claude Code settings.

**Using MCP Launchpad**: Finance Guru includes MCP Launchpad (`mcpl`), a unified CLI for managing all MCP servers. Always use `mcpl search "<query>"` to discover available tools before calling them manually.

```bash
# Search for tools across all MCP servers
mcpl search "list projects"

# Verify all MCP servers are connected
mcpl verify

# Check server status
mcpl session status
```

See [CLAUDE.md](../CLAUDE.md) for complete MCP Launchpad documentation.

#### Installing MCP Launchpad

MCP Launchpad is installed globally using uv tool:

```bash
# Install mcpl (one-time setup)
uv tool install https://github.com/kenneth-liao/mcp-launchpad.git

# Verify installation
mcpl --version

# Check which servers are configured
mcpl list

# Test all server connections
mcpl verify
```

#### MCP Configuration Files

mcpl reads configuration from these locations (in order):

1. `./mcp.json` (project-level, recommended for Finance Guru)
2. `./.claude/mcp.json` (project-level)
3. `~/.claude/mcp.json` (global user-level)

**For Finance Guru**, create `mcp.json` in the project root or use your global `~/.claude/mcp.json`.

#### Required MCP Servers

| Server | Purpose | Setup Instructions |
|--------|---------|-------------------|
| **exa** | Market research, web intelligence | See [MCP Exa Setup](#mcp-exa-setup) |
| **bright-data** | Web scraping, data extraction | See [MCP Bright Data Setup](#mcp-bright-data-setup) |
| **sequential-thinking** | Multi-step financial reasoning | See [MCP Sequential Thinking Setup](#mcp-sequential-thinking-setup) |

#### Optional MCP Servers

| Server | Purpose | When to Use |
|--------|---------|------------|
| **gdrive** | Google Sheets portfolio sync | If you use Google Sheets DataHub |
| **perplexity** | AI-powered research | For deep market analysis |
| **financial-datasets** | Real-time market data | Alternative to yfinance |
| **context7** | Documentation lookup | For framework reference |

#### MCP Exa Setup

Exa provides AI-powered web search and content extraction for market intelligence.

**Configuration** (`mcp.json` or `~/.claude/mcp.json`):

```json
{
  "mcpServers": {
    "exa": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://mcp.exa.ai/mcp?exaApiKey=${EXA_API_KEY}"]
    }
  }
}
```

**Or use the HTTP transport**:

```json
{
  "mcpServers": {
    "exa": {
      "type": "http",
      "url": "https://mcp.exa.ai/mcp?exaApiKey=${EXA_API_KEY}"
    }
  }
}
```

**Setup Steps**:
1. Get your Exa API key: [exa.ai/api](https://exa.ai/api)
2. Add `EXA_API_KEY=your_key` to `~/.claude/.env` or `./.env`
3. Test: `mcpl list exa --refresh`

#### MCP Bright Data Setup

Bright Data provides web scraping and data extraction for financial data gathering.

**Configuration** (`mcp.json` or `~/.claude/mcp.json`):

```json
{
  "mcpServers": {
    "bright-data": {
      "command": "npx",
      "args": ["-y", "@brightdata/mcp-server"],
      "env": {
        "BRIGHT_DATA_API_KEY": "${BRIGHT_DATA_API_KEY}"
      }
    }
  }
}
```

**Setup Steps**:
1. Get your Bright Data key: [brightdata.com](https://brightdata.com/)
2. Add `BRIGHT_DATA_API_KEY=your_key` to `~/.claude/.env` or `./.env`
3. Test: `mcpl list bright-data --refresh`

#### MCP Sequential Thinking Setup

Sequential Thinking provides multi-step reasoning for complex financial analysis.

**Configuration** (`mcp.json` or `~/.claude/mcp.json`):

```json
{
  "mcpServers": {
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
    }
  }
}
```

**Setup Steps**:
1. No API key required
2. Test: `mcpl list sequential-thinking --refresh`

**Note**: This server provides tools for breaking down complex financial problems into sequential steps.

#### MCP Google Drive Setup (Optional)

**Only needed if syncing portfolio data to Google Sheets.**

```bash
# Clone and install gdrive MCP
git clone https://github.com/AojdevStudio/gdrive.git
cd gdrive
bun install
bun run build

# Add to Claude Code settings
{
  "mcpServers": {
    "gdrive": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-v", "/path/to/gdrive:/app",
        "gdrive-mcp"
      ],
      "env": {
        "GOOGLE_APPLICATION_CREDENTIALS": "/app/credentials.json"
      }
    }
  }
}
```

See [Google Drive MCP Docs](https://github.com/AojdevStudio/gdrive) for OAuth setup.

### API Keys (.env)

Edit `.env` to add your API keys (all optional - yfinance works without keys):

```bash
# Open .env in your editor
nano .env
```

**Recommended API Keys:**

```bash
# ITC Risk Models (external risk intelligence)
ITC_API_KEY=your_itc_api_key_here

# Finnhub (real-time prices, optional)
FINNHUB_API_KEY=your_finnhub_key_here

# OpenAI (for specific agent tasks, optional)
OPENAI_API_KEY=your_openai_key_here
```

**Where to get keys:**

- **ITC Risk Models**: Contact ITC directly (proprietary API)
- **Finnhub**: [finnhub.io](https://finnhub.io/) - Free tier: 60 calls/min
- **OpenAI**: [platform.openai.com](https://platform.openai.com/)

**Note**: Finance Guru uses `yfinance` for market data by default. API keys enhance functionality but are not required.

**For comprehensive API key setup instructions**, see the [API Key Acquisition Guide](api-keys.md).

### Hooks Verification

Finance Guru uses hooks to auto-load context and activate skills. Verify hooks are configured:

```bash
# Check hooks directory
ls -la .claude/hooks/

# Expected files:
# - load-fin-core-config.ts       (SessionStart hook)
# - skill-activation-prompt.sh    (UserPromptSubmit hook)
# - post-tool-use-tracker.ts      (PostToolUse hook)
# - run-tests.sh                  (Stop hook)

# Verify hooks in settings
cat .claude/settings.json | grep -A 5 hooks
```

**Expected output:**

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "npx tsx $CLAUDE_PROJECT_DIR/.claude/hooks/load-fin-core-config.ts"
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/skill-activation-prompt.sh"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|MultiEdit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/post-tool-use-tracker.ts"
          }
        ]
      }
    ]
  }
}
```

If hooks are missing, they should have been created during setup. Check `.claude/hooks/` exists.

**Note**: Hooks use the newer array-based format with `$CLAUDE_PROJECT_DIR` environment variable for portability.

---

## Verification

### Test Python CLI Tools

```bash
# Test risk metrics tool
uv run python src/analysis/risk_metrics_cli.py TSLA --days 90

# Expected output:
# Risk Metrics for TSLA
# Period: 90 days
# VaR (95%): -X.XX%
# CVaR (95%): -X.XX%
# Sharpe Ratio: X.XX
# ...

# Test momentum tool
uv run python src/utils/momentum_cli.py AAPL --days 90

# Expected output:
# Momentum Analysis for AAPL
# RSI: XX.XX (Neutral/Overbought/Oversold)
# MACD: X.XX
# ...
```

### Test Onboarding Wizard

If you skipped onboarding during setup:

```bash
# Run onboarding wizard
bun run scripts/onboarding/index.ts

# Follow prompts to enter:
# - Liquid assets
# - Investment portfolio
# - Cash flow
# - Debt profile
# - Risk preferences

# Creates fin-guru/data/user-profile.yaml
```

### Test Claude Code Integration

```bash
# Start Claude Code in project directory
cd family-office
claude

# Test that SessionStart hook loaded context
# You should see: "✅ PAI Context successfully loaded..."

# Type: /help
# Should show Finance Guru agents in skill list
```

---

## First Use

### Onboarding (First-Time Users)

**IMPORTANT**: Run onboarding before using Finance Guru.

```bash
# In Claude Code
claude

# Activate Onboarding Specialist
/fin-guru:agents:onboarding-specialist

# Follow the guided questionnaire
```

The Onboarding Specialist will:
1. ✅ Assess your financial situation
2. ✅ Create your portfolio profile
3. ✅ Configure risk tolerance
4. ✅ Recommend strategies
5. ✅ Generate `user-profile.yaml`

### Using Finance Guru

After onboarding, activate the Finance Orchestrator:

```bash
# In Claude Code
/finance-orchestrator

# Or use direct shortcuts:
*quant            # Quant Analyst
*strategy         # Strategy Advisor
*market-research  # Market Researcher
```

**About Skills**: The `/finance-orchestrator` and other commands are "skills" - specialized Claude Code commands that activate Finance Guru agents. Skills are automatically discovered via hooks when you type their names. The full skill name is `/fin-guru:agents:finance-orchestrator`, but shortcuts work too.

**Example workflows:**

```bash
# Risk analysis
"Analyze TSLA risk profile compared to my portfolio"

# Portfolio optimization
"Should I add more tech stocks? Check correlation with existing holdings"

# Market research
"What's the momentum on NVDA? Is now a good entry?"

# Strategy validation
"Review my hybrid DRIP strategy for compliance"
```

### Sample Tasks

Try these to verify everything works:

```bash
# 1. Market momentum check
"Check momentum on SPY for the last 90 days"

# 2. Risk metrics
"Calculate risk metrics for AAPL vs SPY benchmark"

# 3. Correlation analysis
"Analyze correlation between TSLA, NVDA, and PLTR"

# 4. Portfolio optimization
"Optimize my portfolio for max Sharpe ratio"
```

---

## Troubleshooting

**Note**: This section covers common quick fixes. For comprehensive troubleshooting, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

### Common Issues Quick Reference

| Problem | Quick Fix | Full Details |
|---------|-----------|--------------|
| Module not found | `uv sync --refresh` | [Python Tool Errors](#python-tool-errors) |
| MCP not connected | Check `.claude/settings.json` and API keys | [MCP Server Issues](#mcp-server-issues) |
| Hooks not running | Verify `.claude/hooks/` exists, run manually to test | [Hooks Not Running](#hooks-not-running) |
| yfinance no data | Check internet, wait 5 min (rate limit) | [Python Tool Errors](#python-tool-errors) |
| Onboarding crash | Delete `.onboarding-state.json` and restart | [Onboarding Wizard Errors](#onboarding-wizard-errors) |
| Git can't pull | Add upstream remote, fetch, merge | [Git/Fork Issues](#gitfork-issues) |

### Python Tool Errors

**Problem**: `ModuleNotFoundError` when running CLI tools

```bash
# Solution: Reinstall dependencies
uv sync

# If still broken, check Python version
python --version  # Must be 3.12+

# Try forcing reinstall
uv sync --refresh
```

**Problem**: `yfinance` returns no data

```bash
# Check internet connection
ping yahoo.com

# Try fetching data manually
uv run python -c "import yfinance as yf; print(yf.Ticker('AAPL').history(period='5d'))"

# If empty, yfinance may be rate-limited
# Wait 5 minutes and retry
```

### MCP Server Issues

**Problem**: "MCP server not connected"

```bash
# Check MCP configuration
cat .claude/settings.json | grep -A 10 mcpServers

# Verify server command works standalone
npx -y @exa-labs/mcp-server-exa  # Should not error

# Check API keys in .env
cat .env | grep API_KEY

# Restart Claude Code
# Exit and re-run: claude
```

**Problem**: "Exa API key invalid"

```bash
# Verify key in .env
echo $EXA_API_KEY

# Test key directly
curl -X POST https://api.exa.ai/search \
  -H "x-api-key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'

# Should return JSON, not 401/403
```

### Hooks Not Running

**Problem**: SessionStart hook doesn't load context

```bash
# Check hooks directory
ls -la .claude/hooks/load-fin-core-config.ts

# Run hook manually
bun .claude/hooks/load-fin-core-config.ts

# Should output: "PAI CORE CONTEXT (Auto-loaded at Session Start)"

# If error, check bun is installed
bun --version
```

**Problem**: Skills not activating

```bash
# Check skill-activation-prompt.sh exists
ls -la .claude/hooks/skill-activation-prompt.sh

# Test hook manually
bash .claude/hooks/skill-activation-prompt.sh "analyze TSLA"

# Should output skill activation message
```

### Onboarding Wizard Errors

**Problem**: Wizard crashes during startup

```bash
# Check .onboarding-state.json for corruption
cat .onboarding-state.json

# If corrupted, delete and restart
rm .onboarding-state.json
bun run scripts/onboarding/index.ts
```

**Problem**: `user-profile.yaml` not generated

```bash
# Check fin-guru/data/ exists
ls -la fin-guru/data/

# If missing, create it
mkdir -p fin-guru/data

# Re-run onboarding
bun run scripts/onboarding/index.ts
```

### Git/Fork Issues

**Problem**: Can't pull upstream updates

```bash
# Add upstream remote (one-time)
git remote add upstream https://github.com/ORIGINAL-AUTHOR/family-office.git

# Fetch updates
git fetch upstream

# Merge updates (preserves your private data)
git merge upstream/main

# Your .gitignore prevents private data from merging
```

**Problem**: Accidentally committed private data

```bash
# DANGER: If you pushed sensitive data to GitHub, contact support immediately
# GitHub Support: https://support.github.com/

# Remove file from git history
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch fin-guru/data/user-profile.yaml" \
  --prune-empty --tag-name-filter cat -- --all

# Force push (DANGER: rewrites history)
git push origin --force --all
```

### Claude Code Startup Errors

**Problem**: "Claude Code command not found"

```bash
# Reinstall Claude Code
curl -fsSL https://claude.ai/install.sh | bash

# Add to PATH (if needed)
export PATH="$HOME/.local/bin:$PATH"

# Verify installation
claude --version
```

**Problem**: Context overload / token limit errors

```bash
# Clear old session data
rm -rf .claude/data/sessions/*

# Restart Claude Code
claude

# Finance Guru uses only ~25% of 200k context
# If hitting limits, check for runaway hooks
```

### Need More Help?

For comprehensive troubleshooting coverage including:
- Detailed diagnostics and fixes
- Common error messages explained
- Performance optimization
- Git and privacy issues
- MCP server debugging

See the complete [Troubleshooting Guide](TROUBLESHOOTING.md).

### Common Gotchas

**First-time setup mistakes** that trip up new users:

1. **Forgetting to fork** - Always fork the repository first, don't clone the original directly
2. **Skipping onboarding** - Run `/fin-guru:agents:onboarding-specialist` before using Finance Guru
3. **Missing .env file** - Copy `.env.example` to `.env` (setup.sh does this automatically)
4. **Wrong Python version** - Must be 3.12+, check with `python --version`
5. **Not configuring MCP servers** - At minimum, configure exa, bright-data, and sequential-thinking
6. **Using commands outside project directory** - Always `cd family-office` before running CLI tools
7. **Expecting instant market data** - yfinance can be slow/rate-limited, be patient
8. **Committing private data** - Always verify with `git status --ignored` before pushing

---

## Security Checklist

Before pushing to GitHub or sharing your fork:

### Pre-Push Verification

```bash
# 1. Verify .gitignore is working
git status --ignored

# Should show:
# - .env (ignored)
# - fin-guru/data/user-profile.yaml (ignored)
# - fin-guru-private/ (ignored)
# - notebooks/updates/*.csv (ignored)

# 2. Check staged files for sensitive data
git diff --cached

# Should NOT include:
# - API keys
# - Portfolio balances
# - Personal financial data

# 3. Verify .env is ignored
ls -la .env                    # File exists locally
git check-ignore .env          # Should output ".env"

# 4. Check user-profile.yaml is ignored
git check-ignore fin-guru/data/user-profile.yaml
# Should output: "fin-guru/data/user-profile.yaml"
```

### Safe Files to Commit

✅ **Safe (tracked in git):**
- `src/` - Python analysis tools
- `fin-guru/agents/` - Agent definitions
- `scripts/onboarding/` - Onboarding wizard
- `docs/` - Documentation
- `README.md`, `CLAUDE.md` - Project info
- `pyproject.toml`, `package.json` - Dependencies
- `.gitignore` - Privacy rules

🔒 **Private (gitignored):**
- `.env` - API keys
- `fin-guru/data/user-profile.yaml` - Your financial data
- `fin-guru-private/` - Your strategies and analysis
- `notebooks/updates/*.csv` - Account exports
- `.beads/issues.jsonl` - Private task tracking
- `scripts/` (most files) - Private automation

### Updating Your Fork

```bash
# Pull upstream updates safely
git fetch upstream
git merge upstream/main

# Your private configs stay untouched (gitignored)
# Verify no conflicts with private data
git status
```

---

## Post-Installation Checklist

After running `setup.sh`, verify everything is working:

```bash
# ✅ 1. Python environment
uv run python --version  # Should show 3.12+

# ✅ 2. Directory structure
ls -la fin-guru-private/  # Should exist (gitignored)
ls -la notebooks/updates/  # Should exist (gitignored)
ls -la fin-guru/data/user-profile.yaml  # Should exist (gitignored)

# ✅ 3. Dependencies installed
uv run python -c "import pandas, numpy, yfinance; print('OK')"  # Should print OK

# ✅ 4. CLI tools work
uv run python src/analysis/risk_metrics_cli.py AAPL --days 90  # Should output metrics

# ✅ 5. Hooks configured
cat .claude/settings.json | grep SessionStart  # Should show hook

# ✅ 6. Environment file
ls -la .env  # Should exist (gitignored)

# ✅ 7. Git ignores working
git check-ignore .env  # Should output ".env"
git check-ignore fin-guru/data/user-profile.yaml  # Should output path
```

If all checks pass, you're ready to run onboarding!

---

## Next Steps

1. ✅ **Complete onboarding**: Run `/fin-guru:agents:onboarding-specialist`
2. ✅ **Import portfolio data**: Export CSV from Fidelity → `notebooks/updates/`
3. ✅ **Sync to Google Sheets** (optional): Use `/portfolio-sync` skill
4. ✅ **Run first analysis**: Try "*quant Analyze TSLA risk profile"
5. ✅ **Review documentation**: See [docs/index.md](index.md)

---

## Additional Resources

| Resource | Link |
|----------|------|
| **Main README** | [README.md](../README.md) |
| **API Reference** | [docs/api.md](api.md) |
| **Hooks Documentation** | [docs/hooks.md](hooks.md) |
| **Finance Guru Module** | [fin-guru/README.md](../fin-guru/README.md) |
| **Contributing Guide** | [docs/contributing.md](contributing.md) |

---

## Support

If you encounter issues not covered here:

1. Check [Troubleshooting](#troubleshooting) section above
2. Review [docs/index.md](index.md) for architecture details
3. Search issues: [GitHub Issues](https://github.com/YOUR-USERNAME/family-office/issues)
4. Open a new issue with:
   - Error message
   - Steps to reproduce
   - System info (`uv --version`, `python --version`, `bun --version`)

---

<p align="center">
  <strong>Finance Guru™ v2.0.0</strong><br>
  Your AI-powered private family office.
</p>
