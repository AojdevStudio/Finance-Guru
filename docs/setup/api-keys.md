---
title: "API Key Acquisition Guide"
description: "How to obtain and configure API keys for Finance Guru integrations"
category: setup
---

# API Key Acquisition Guide

Complete guide for obtaining and configuring API keys for Finance Guru™.

## Overview

Finance Guru™ works out-of-the-box with **zero API keys** using `yfinance` for market data. API keys enhance functionality but are entirely optional.

### Quick Reference

| API | Required? | Free Tier | Purpose |
|-----|-----------|-----------|---------|
| **None (yfinance)** | ✅ Default | ✅ Unlimited | End-of-day market data |
| **Finnhub** | Optional | ✅ 60 calls/min | Real-time prices during market hours |
| **ITC Risk Models** | Optional | ❌ Paid | External risk intelligence |
| **OpenAI** | Optional | ❌ Paid | Alternative LLM for specific tasks |
| **Exa (MCP)** | Recommended | ❌ Paid | Market research, web intelligence |
| **Bright Data (MCP)** | Recommended | ❌ Trial | Web scraping, data extraction |

---

## Market Data APIs

### yfinance (Default - No Key Required)

**Status**: Built-in, always works, no configuration needed

**What it provides**:
- End-of-day stock prices
- Historical price data
- Basic company info
- Options data
- Dividend history

**Limitations**:
- Data delayed 15-20 minutes during market hours
- No intraday real-time quotes
- Rate limits (usually not an issue for personal use)

**Setup**: None required - Finance Guru uses yfinance by default

**Example usage**:
```bash
# All CLI tools work with yfinance by default
uv run python src/utils/market_data.py TSLA
uv run python src/analysis/risk_metrics_cli.py AAPL --days 90
```

---

### Finnhub (Real-Time Market Data)

**Status**: Optional enhancement for real-time prices

**What it provides**:
- Real-time stock quotes during market hours
- Minimal delay (< 1 second)
- 60 API calls per minute (free tier)
- News and sentiment data

**Why you might want it**:
- Day trading or active management
- Real-time portfolio valuation
- Intraday price alerts

**Why you might NOT need it**:
- Long-term investing (end-of-day is fine)
- Portfolio rebalancing (daily data sufficient)
- Backtesting (historical data only)

#### Obtaining a Finnhub API Key

**Step 1: Sign Up**
1. Visit [finnhub.io](https://finnhub.io/)
2. Click "Get free API key" (top right)
3. Enter your email address
4. Confirm email verification

**Step 2: Access Dashboard**
1. Log in to [finnhub.io/dashboard](https://finnhub.io/dashboard)
2. Copy your API key (shown immediately after signup)
3. Key format: `c1a2b3c4d5e6f7g8h9i0` (20 alphanumeric characters)

**Step 3: Add to .env**
```bash
# Open .env in your editor
nano .env

# Add this line:
FINNHUB_API_KEY=your_actual_key_here

# Save and exit
```

**Step 4: Test the Key**
```bash
# Test with market_data CLI
uv run python src/utils/market_data.py TSLA --realtime

# Expected output:
# ✓ TSLA: $XXX.XX (+X.XX%)
# Source: Finnhub (real-time)
```

#### Finnhub Free Tier Limits

| Metric | Free Tier | Notes |
|--------|-----------|-------|
| API Calls | 60/min | Enough for 60 tickers every minute |
| Data Delay | < 1 sec | Real-time during market hours |
| Historical Data | ✅ Included | Limited to recent history |
| News/Sentiment | ✅ Included | Basic news headlines |
| Cost | $0/month | Forever free |

**Rate Limit Strategy**:
```bash
# Fetch entire portfolio in one call (under 60/min limit)
uv run python src/utils/market_data.py TSLA PLTR NVDA AAPL GOOGL --realtime

# Finance Guru automatically batches calls
# No need to worry about rate limits for typical portfolios
```

---

## Risk Intelligence APIs

### ITC Risk Models API

**Status**: Optional, proprietary (paid service)

**What it provides**:
- Market-implied risk scores (0-1 scale)
- Risk bands for 42 assets (TradFi + Crypto)
- External validation of internal risk metrics
- Historical risk patterns

**Why you might want it**:
- Hedge fund-grade risk intelligence
- Second opinion on portfolio risk
- Early warning signals for high-risk entries

**Why you might NOT need it**:
- Finance Guru's internal risk metrics (VaR, CVaR, Sharpe) are robust
- ITC is complementary, not required
- Proprietary API with limited availability

#### Obtaining an ITC Risk Models API Key

**Step 1: Contact ITC**

ITC Risk Models is a proprietary service from Into The Cryptoverse. Access is not publicly available via self-service signup.

**Contact Options**:
- Email: [Contact form at intothecryptoverse.com](https://intothecryptoverse.com/contact)
- Twitter: [@intocryptoverse](https://twitter.com/intocryptoverse)
- Mention you're using Finance Guru™ for personal portfolio analysis

**What to include in your request**:
- Use case: "Personal portfolio risk analysis"
- Assets of interest: "TradFi (TSLA, AAPL, MSTR, NFLX, SP500)"
- Frequency: "Daily portfolio checks, ~10-20 API calls/day"

**Expected Response Time**: 1-3 business days

**Step 2: Pricing Inquiry**

ITC Risk Models pricing is not publicly listed. Expect:
- Subscription-based pricing (monthly or annual)
- Tiered access based on API call volume
- Potential enterprise vs. personal tiers

**Budget Guidance**: Set aside $50-200/month for personal use (estimate)

**Step 3: Add to .env**

Once you receive your API key:

```bash
# Open .env
nano .env

# Add this line:
ITC_API_KEY=your_itc_api_key_here

# Save and exit
```

**Step 4: Test the Key**

```bash
# Test with ITC Risk CLI
uv run python src/analysis/itc_risk_cli.py TSLA --universe tradfi

# Expected output:
# ITC Risk Score for TSLA
# Current Price: $XXX.XX
# Risk Score: 0.XX (Low/Medium/High/Very High)
# Risk Bands:
#   $XXX.XX: 0.XX (Low)
#   $XXX.XX: 0.XX (Medium)
```

#### ITC Supported Assets

**TradFi Universe (13 assets)**:
```
TSLA, AAPL, MSTR, NFLX, SP500, DXY,
XAUUSD (Gold), XAGUSD (Silver), XPDUSD (Palladium),
PL (Platinum), HG (Copper), NICKEL
```

**Crypto Universe (29 assets)**:
```
BTC, ETH, BNB, SOL, XRP, ADA, DOGE, LINK,
MATIC, DOT, AVAX, UNI, ATOM, LTC, BCH,
XLM, ALGO, VET, FIL, TRX, ETC, THETA,
XMR, ZEC, DASH, COMP, YFI, SNX, MKR
```

**Fallback Strategy**: If you don't have ITC access, Finance Guru's internal risk tools provide comprehensive coverage:
- `risk_metrics_cli.py` - VaR, CVaR, Sharpe, Sortino, Max Drawdown
- `volatility_cli.py` - ATR, Bollinger Bands, Historical Volatility
- `correlation_cli.py` - Portfolio diversification metrics

---

## MCP Server APIs

MCP servers provide external integrations for Claude Code. These are **recommended** for full Finance Guru functionality.

### Exa (Market Research & Web Intelligence)

**Status**: Recommended for Market Researcher agent

**What it provides**:
- Semantic web search optimized for finance
- Real-time news and sentiment
- Company filings and earnings reports
- Alternative data sources

**Why you need it**:
- Market Researcher agent relies on Exa for intelligence gathering
- Enables "what's happening with TSLA?" queries
- Provides context for quantitative analysis

#### Obtaining an Exa API Key

**Step 1: Sign Up**
1. Visit [exa.ai](https://exa.ai/)
2. Click "Get API Access"
3. Sign up with email or Google
4. Confirm email verification

**Step 2: Access Dashboard**
1. Log in to [dashboard.exa.ai](https://dashboard.exa.ai/)
2. Navigate to "API Keys" section
3. Click "Create New Key"
4. Copy the generated key

**Step 3: Configure MCP Server**

Edit `.claude/settings.json`:

```json
{
  "mcpServers": {
    "exa": {
      "command": "npx",
      "args": ["-y", "@exa-labs/mcp-server-exa"],
      "env": {
        "EXA_API_KEY": "your_exa_api_key_here"
      }
    }
  }
}
```

**Step 4: Test Integration**

```bash
# Start Claude Code
claude

# Test Exa search
# (In Claude Code session): "Search Exa for TSLA earnings news"
```

#### Exa Pricing

| Tier | Cost | API Calls | Best For |
|------|------|-----------|----------|
| **Free** | $0/month | 100/month | Testing |
| **Starter** | $20/month | 1,000/month | Personal use |
| **Pro** | $80/month | 5,000/month | Active traders |

**Recommendation**: Start with Starter tier ($20/month) for personal portfolio analysis

---

### Bright Data (Web Scraping & Data Extraction)

**Status**: Recommended for alternative data sources

**What it provides**:
- Web scraping infrastructure
- Proxy network for data collection
- JavaScript rendering for dynamic sites
- Structured data extraction

**Why you might need it**:
- Alternative data signals (Reddit sentiment, insider trading)
- Earnings call transcripts
- SEC filings analysis
- News aggregation from paywalled sources

**Why you might NOT need it**:
- Exa covers most research needs
- Expensive for casual use
- Overkill for basic portfolio management

#### Obtaining a Bright Data API Key

**Step 1: Sign Up**
1. Visit [brightdata.com](https://brightdata.com/)
2. Click "Start Free Trial"
3. Enter business email (required)
4. Phone verification

**Step 2: Create API Token**
1. Log in to [brightdata.com/cp](https://brightdata.com/cp)
2. Navigate to "Zones" → "Proxies"
3. Create a new proxy zone
4. Generate API credentials (username + password)

**Step 3: Configure MCP Server**

Edit `.claude/settings.json`:

```json
{
  "mcpServers": {
    "bright-data": {
      "command": "npx",
      "args": ["-y", "@brightdata/mcp-server"],
      "env": {
        "BRIGHT_DATA_API_KEY": "your_bright_data_key"
      }
    }
  }
}
```

**Step 4: Test Integration**

```bash
# Start Claude Code
claude

# Test Bright Data scraping
# (In Claude Code): "Scrape latest TSLA news from Yahoo Finance"
```

#### Bright Data Pricing

| Tier | Cost | Notes |
|------|------|-------|
| **Free Trial** | $0 | Limited credits for testing |
| **Pay As You Go** | ~$0.50-2.00 per GB | Flexible, no commitment |
| **Enterprise** | Custom | High-volume users |

**Warning**: Bright Data is expensive. Budget $50-100/month for active use.

**Recommendation**: Use free trial first. Only upgrade if you need specific data sources Exa can't provide.

---

## Optional APIs

### OpenAI (Alternative LLM)

**Status**: Optional, rarely needed

**What it provides**:
- GPT-4 access for specific agent tasks
- Text embeddings for semantic search
- Fine-tuned models for financial analysis

**Why you might NOT need it**:
- Finance Guru runs on Claude Code (Claude Sonnet)
- OpenAI is only used for specific tasks where GPT-4 excels
- Most workflows don't require it

**When you might need it**:
- Comparing Claude vs GPT-4 outputs
- Using GPT-4 for specific research tasks
- Fine-tuning custom financial models

#### Obtaining an OpenAI API Key

**Step 1: Sign Up**
1. Visit [platform.openai.com/signup](https://platform.openai.com/signup)
2. Sign up with email or Google
3. Phone verification required
4. Add billing info (credit card)

**Step 2: Create API Key**
1. Log in to [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Click "Create new secret key"
3. Name it (e.g., "Finance Guru")
4. Copy the key immediately (shown only once)

**Step 3: Add to .env**

```bash
# Open .env
nano .env

# Add this line:
OPENAI_API_KEY=sk-proj-...your_key_here

# Save and exit
```

**Step 4: Set Usage Limits** (Recommended)

1. Navigate to [platform.openai.com/account/limits](https://platform.openai.com/account/limits)
2. Set "Monthly budget" (e.g., $20)
3. Enable "Email alerts" at 75% and 90%

#### OpenAI Pricing

| Model | Cost | Best For |
|-------|------|----------|
| **GPT-4 Turbo** | $10 / 1M input tokens | Complex reasoning |
| **GPT-3.5 Turbo** | $0.50 / 1M input tokens | Simple tasks |
| **Text Embeddings** | $0.13 / 1M tokens | Semantic search |

**Budget Guidance**: Set $10-20/month limit for personal use

---

## Configuration Summary

### Recommended Minimal Setup

**For basic portfolio analysis**:
```bash
# .env file
# No API keys needed - yfinance works out of the box
```

**MCP Servers** (if using Claude Code):
- Sequential Thinking (no key required)

**Cost**: $0/month

---

### Recommended Standard Setup

**For active portfolio management**:
```bash
# .env file
FINNHUB_API_KEY=your_finnhub_key_here
```

**MCP Servers**:
- Exa ($20/month)
- Sequential Thinking (free)

**Cost**: ~$20/month

---

### Recommended Advanced Setup

**For hedge fund-grade analysis**:
```bash
# .env file
FINNHUB_API_KEY=your_finnhub_key_here
ITC_API_KEY=your_itc_key_here
OPENAI_API_KEY=your_openai_key_here
```

**MCP Servers**:
- Exa ($20-80/month)
- Bright Data ($50-100/month)
- Sequential Thinking (free)

**Cost**: ~$100-250/month

---

## Troubleshooting

### API Key Not Working

**Problem**: "Invalid API key" error

**Solutions**:
```bash
# 1. Verify key is in .env (not .env.example)
cat .env | grep API_KEY

# 2. Check for extra spaces or quotes
# WRONG: FINNHUB_API_KEY=" abc123 "
# RIGHT: FINNHUB_API_KEY=abc123

# 3. Reload environment variables
# Restart Python script or Claude Code session

# 4. Test key directly
curl -X GET "https://finnhub.io/api/v1/quote?symbol=AAPL&token=YOUR_KEY"
```

---

### Rate Limit Errors

**Problem**: "Rate limit exceeded" or "429 Too Many Requests"

**Solutions**:

**For Finnhub (60/min limit)**:
```bash
# Batch multiple tickers in one call
uv run python src/utils/market_data.py TSLA PLTR NVDA --realtime

# Add delay between calls (if needed)
for ticker in TSLA PLTR NVDA; do
    uv run python src/utils/market_data.py $ticker --realtime
    sleep 2  # 2-second delay
done
```

**For Exa (1,000/month on Starter)**:
- Use web search sparingly
- Cache results locally
- Upgrade to Pro tier ($80/month for 5,000 calls)

**For Bright Data**:
- Monitor credit usage in dashboard
- Use pay-as-you-go to avoid unexpected bills
- Only scrape when necessary (data changes)

---

### MCP Server Connection Issues

**Problem**: "MCP server not responding"

**Solutions**:
```bash
# 1. Verify MCP server command works
npx -y @exa-labs/mcp-server-exa

# Should not error (may hang waiting for stdin - that's OK)

# 2. Check settings.json syntax
cat .claude/settings.json | python -m json.tool

# Should output valid JSON (no syntax errors)

# 3. Restart Claude Code
# Exit and re-run: claude

# 4. Check MCP logs (if available)
# Logs usually in .claude/logs/
```

---

### Environment Variables Not Loading

**Problem**: API key in .env but code can't find it

**Solutions**:

**Check file location**:
```bash
# .env MUST be in project root
ls -la .env

# If in wrong location, move it:
mv /wrong/path/.env /Users/ossieirondi/Documents/Irondi-Household/family-office/.env
```

**Check Python is loading dotenv**:
```bash
# Verify dotenv is installed
uv sync

# Test environment loading
uv run python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('FINNHUB_API_KEY'))"

# Should print your API key (or None if not set)
```

**Verify .env is not gitignored accidentally**:
```bash
# .env should exist locally
ls -la .env

# But be gitignored
git check-ignore .env  # Should output ".env"
```

---

## Security Best Practices

### Never Commit API Keys to Git

**Verification checklist before git push**:

```bash
# 1. Verify .env is gitignored
git check-ignore .env
# Output: .env (confirmed ignored)

# 2. Check staged files for keys
git diff --cached | grep -i "api_key"
# Should return nothing

# 3. Verify .gitignore includes .env
cat .gitignore | grep .env
# Output: .env

# 4. Check git history for leaks (if paranoid)
git log --all --full-history --source -- .env
# Should be empty (file never tracked)
```

---

### Rotate Keys Regularly

**Recommended schedule**:
- **Every 90 days**: Rotate all API keys
- **Immediately**: If key compromised or shared accidentally
- **After team changes**: If someone leaves project

**How to rotate**:

**Finnhub**:
1. Log in to [finnhub.io/dashboard](https://finnhub.io/dashboard)
2. Revoke old key
3. Generate new key
4. Update `.env`

**Exa**:
1. Log in to [dashboard.exa.ai](https://dashboard.exa.ai/)
2. Delete old key
3. Create new key
4. Update `.claude/settings.json`

**OpenAI**:
1. Log in to [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Revoke old key
3. Create new key
4. Update `.env`

---

### Use Environment-Specific Keys

**Best practice**: Separate keys for dev/test/prod

```bash
# .env.development
FINNHUB_API_KEY=dev_key_here

# .env.production
FINNHUB_API_KEY=prod_key_here
```

**Load appropriate env**:
```python
# In your Python scripts
from dotenv import load_dotenv
import os

# Load development env
env = os.getenv("ENV", "development")
load_dotenv(f".env.{env}")
```

---

### Monitor API Usage

**Set up alerts**:

**Finnhub**:
- Dashboard shows usage automatically
- No billing alerts (free tier)

**Exa**:
- Enable email alerts at 75% usage
- Monitor in dashboard.exa.ai

**Bright Data**:
- Set credit alerts in dashboard
- Enable "Stop at budget limit"

**OpenAI**:
- Set monthly budget limit
- Enable email alerts at 75% and 90%

---

## Next Steps

1. ✅ Decide which APIs you need (start with Minimal Setup)
2. ✅ Obtain API keys following guides above
3. ✅ Add keys to `.env` file
4. ✅ Configure MCP servers in `.claude/settings.json`
5. ✅ Test each API with provided commands
6. ✅ Verify `.env` is gitignored
7. ✅ Run Finance Guru with `/finance-orchestrator`

---

## Additional Resources

| Resource | Link |
|----------|------|
| **Setup Guide** | [SETUP.md](SETUP.md) |
| **API Reference** | [api.md](../reference/api.md) |
| **Hooks Documentation** | [hooks.md](../reference/hooks.md) |
| **Main README** | [README.md](../../README.md) |

---

## Support

If you encounter API key issues:

1. Check this guide's [Troubleshooting](#troubleshooting) section
2. Verify API provider's status page (e.g., [finnhub.io/status](https://finnhub.io/status))
3. Review [SETUP.md](SETUP.md) for general setup issues
4. Open an issue: [GitHub Issues](https://github.com/YOUR-USERNAME/family-office/issues)

---

<p align="center">
  <strong>Finance Guru™ v2.0.0</strong><br>
  Your AI-powered private family office.
</p>
