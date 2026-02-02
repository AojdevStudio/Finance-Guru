# Into The Cryptoverse (ITC) Risk Models API Integration Specification

**Generated:** 2026-01-09 16:51:03
**Status:** Ready for Implementation

## Problem Statement

### Why This Exists

The Finance Guru system currently relies solely on internal quantitative metrics (VaR, Sharpe, volatility) for risk assessment. These statistical models are backward-looking and may miss market-implied risk signals. The Into The Cryptoverse (ITC) Risk Models API provides complementary price-based risk scores that reflect market sentiment and price action patterns, offering a second opinion on risk levels.

**Who It's For:** Finance Guru agents (Market Researcher, Quant Analyst, Strategy Advisor, Compliance Officer) and direct CLI users analyzing supported tickers (TSLA, AAPL, MSTR, NFLX, SP500, commodities).

**Cost of NOT Doing This:** Missing divergence signals where internal metrics show low risk but market-implied risk is elevated (or vice versa), potentially leading to poorly timed entries or missed warning signs on high-conviction positions like TSLA.

### Use Cases (All Three)

1. **Pre-trade Validation:** Check ITC risk score before executing buy tickets to validate entry timing
2. **Ongoing Portfolio Monitoring:** Track risk levels of current holdings, especially Layer 1 Growth positions (TSLA primary focus)
3. **Educational Comparison:** Cross-reference quantitative tools with ITC's market-implied risk for validation and learning

## Technical Requirements

### Architecture Overview

**Pattern:** Follow Finance Guru's established 3-layer architecture:
- **Layer 1:** Pydantic Models (data validation)
- **Layer 2:** Calculator Class (business logic)
- **Layer 3:** CLI Interface (agent integration)

**Integration Point:** Standalone CLI tool (`src/analysis/itc_risk_cli.py`) that can be:
- Invoked directly by agents via command line
- Called programmatically by other Python modules
- Integrated into agent workflows via auto-detection

### Data Models (Layer 1)

**File:** `src/models/itc_risk_inputs.py`

```python
from pydantic import BaseModel, Field
from typing import Literal, Optional, List
from datetime import datetime

class ITCRiskRequest(BaseModel):
    """Request model for ITC Risk API calls"""
    symbol: str = Field(..., description="Asset symbol (e.g., TSLA, BTC)")
    universe: Literal["crypto", "tradfi"] = Field(..., description="Asset universe")
    api_key: str = Field(..., description="ITC API key from environment")

class RiskBand(BaseModel):
    """Individual price band with associated risk score"""
    price: float = Field(..., description="Price level")
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Risk score (0-1)")

class ITCRiskResponse(BaseModel):
    """Response from ITC API with risk data"""
    symbol: str
    universe: str
    current_price: Optional[float] = None  # From yfinance
    current_risk_score: float = Field(..., ge=0.0, le=1.0)
    risk_bands: List[RiskBand]
    timestamp: datetime
    source: str = "Into The Cryptoverse API"

    def get_nearest_bands(self, n: int = 5) -> List[RiskBand]:
        """Get n nearest bands around current price"""
        if not self.current_price or not self.risk_bands:
            return self.risk_bands[:n]

        # Sort by distance from current price
        sorted_bands = sorted(
            self.risk_bands,
            key=lambda b: abs(b.price - self.current_price)
        )
        return sorted_bands[:n]

    def get_high_risk_threshold(self) -> Optional[RiskBand]:
        """Find price where risk exceeds 0.7 (high risk)"""
        for band in sorted(self.risk_bands, key=lambda b: b.price):
            if band.risk_score >= 0.7:
                return band
        return None
```

### Calculator Class (Layer 2)

**File:** `src/analysis/itc_risk.py`

```python
import os
import requests
from typing import Optional
from datetime import datetime
from src.models.itc_risk_inputs import ITCRiskRequest, ITCRiskResponse, RiskBand
import yfinance as yf

class ITCRiskCalculator:
    """
    Calculator for ITC Risk Models API integration.

    Handles API communication, response parsing, and current price enrichment.
    Implements retry logic with exponential backoff and graceful degradation.
    """

    BASE_URL = "https://app.intothecryptoverse.com/api/v2"

    # Supported assets (ITC API coverage)
    SUPPORTED_TRADFI = [
        "TSLA", "AAPL", "MSTR", "NFLX",  # Stocks
        "SP500",  # Index
        "DXY",  # Currency
        "XAUUSD", "XAGUSD", "XPDUSD", "PL", "HG", "NICKEL"  # Commodities
    ]

    SUPPORTED_CRYPTO = [
        "BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "DOGE", "LINK",
        "AVAX", "DOT", "SHIB", "LTC", "AAVE", "ATOM", "POL", "ALGO",
        "HBAR", "RENDER", "VET", "TRX", "TON", "SUI", "XLM", "XMR",
        "XTZ", "SKY", "BTC.D", "TOTAL", "TOTAL6"
    ]

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize calculator with API key.

        Args:
            api_key: ITC API key. If None, loads from ITC_API_KEY env var.

        Raises:
            ValueError: If API key not provided and not in environment
        """
        self.api_key = api_key or os.getenv("ITC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "ITC API key required. Set ITC_API_KEY in .env file.\n"
                "Get your key at: https://app.intothecryptoverse.com/api"
            )

    def validate_ticker(self, symbol: str, universe: str) -> None:
        """
        Validate ticker is supported by ITC API.

        Args:
            symbol: Ticker symbol
            universe: "crypto" or "tradfi"

        Raises:
            ValueError: If ticker not supported
        """
        supported = self.SUPPORTED_CRYPTO if universe == "crypto" else self.SUPPORTED_TRADFI
        if symbol.upper() not in supported:
            raise ValueError(
                f"{symbol} not supported by ITC API.\n"
                f"Supported {universe} assets: {', '.join(supported)}\n"
                f"Use your internal risk_metrics_cli.py for this ticker."
            )

    def get_risk_score(
        self,
        symbol: str,
        universe: str,
        enrich_with_price: bool = True,
        retry_count: int = 3
    ) -> ITCRiskResponse:
        """
        Fetch risk score and bands for a ticker.

        Args:
            symbol: Ticker symbol (e.g., TSLA, BTC)
            universe: "crypto" or "tradfi"
            enrich_with_price: If True, fetch current price from yfinance
            retry_count: Number of retry attempts for transient errors

        Returns:
            ITCRiskResponse with risk data

        Raises:
            ValueError: If ticker not supported
            requests.RequestException: If API call fails after retries
        """
        # Validate ticker
        self.validate_ticker(symbol, universe)

        # Build request
        url = f"{self.BASE_URL}/risk-models/price-based/{universe}/{symbol}"
        params = {"apikey": self.api_key, "format": "json"}

        # Retry logic with exponential backoff
        for attempt in range(retry_count):
            try:
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                break
            except requests.RequestException as e:
                if attempt == retry_count - 1:
                    raise
                # Exponential backoff: 1s, 2s, 4s
                import time
                time.sleep(2 ** attempt)

        # Parse response
        risk_bands = [
            RiskBand(price=band["price"], risk_score=band["risk"])
            for band in data.get("risk_table", [])
        ]

        current_risk = data.get("current_risk_score", 0.0)

        # Enrich with current price from yfinance
        current_price = None
        if enrich_with_price and universe == "tradfi":
            try:
                ticker_obj = yf.Ticker(symbol)
                info = ticker_obj.info
                current_price = info.get('currentPrice') or info.get('regularMarketPrice')
            except Exception:
                pass  # Fail gracefully if yfinance unavailable

        return ITCRiskResponse(
            symbol=symbol.upper(),
            universe=universe,
            current_price=current_price,
            current_risk_score=current_risk,
            risk_bands=risk_bands,
            timestamp=datetime.now()
        )

    def get_all_risks(self, universe: str) -> dict:
        """
        Get risk scores for all assets in a universe.

        Args:
            universe: "crypto" or "tradfi"

        Returns:
            Dict mapping symbols to current risk scores
        """
        url = f"{self.BASE_URL}/risk-models/price-based/{universe}"
        params = {"apikey": self.api_key}

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        return response.json()
```

### CLI Interface (Layer 3)

**File:** `src/analysis/itc_risk_cli.py`

```python
#!/usr/bin/env python3
"""
ITC Risk Models CLI for Finance Guru™ Agents

Provides command-line interface for fetching and analyzing Into The Cryptoverse
risk scores. Designed for easy integration with Finance Guru agents.

AGENT USAGE:
    # Check TSLA risk before trade
    uv run python src/analysis/itc_risk_cli.py TSLA --universe tradfi

    # Compare with internal metrics
    uv run python src/analysis/risk_metrics_cli.py TSLA --days 90
    uv run python src/analysis/itc_risk_cli.py TSLA --universe tradfi

    # Show full risk table
    uv run python src/analysis/itc_risk_cli.py TSLA --universe tradfi --full-table

    # JSON output for programmatic parsing
    uv run python src/analysis/itc_risk_cli.py TSLA --universe tradfi --output json

    # Portfolio batch check (multiple tickers)
    uv run python src/analysis/itc_risk_cli.py TSLA AAPL MSTR --universe tradfi

Author: Finance Guru™ Development Team
Created: 2026-01-09
"""

import argparse
import sys
from pathlib import Path
from typing import List

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.analysis.itc_risk import ITCRiskCalculator
from src.models.itc_risk_inputs import ITCRiskResponse

def format_output_human(results: ITCRiskResponse, full_table: bool = False) -> str:
    """Format results in human-readable format"""
    output = []
    output.append("=" * 70)
    output.append(f"🎯 ITC RISK ANALYSIS: {results.symbol}")
    output.append(f"🕐 Timestamp: {results.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    output.append("=" * 70)
    output.append("")

    # Current Risk Score
    output.append("📊 CURRENT RISK SCORE")
    output.append("-" * 70)
    output.append(f"  Risk Score (0-1):         {results.current_risk_score:>10.3f}")

    # Interpret risk level
    if results.current_risk_score < 0.3:
        risk_level = "LOW (< 0.3)"
        emoji = "🟢"
    elif results.current_risk_score < 0.7:
        risk_level = "MEDIUM (0.3-0.7)"
        emoji = "🟡"
    else:
        risk_level = "HIGH (> 0.7)"
        emoji = "🔴"

    output.append(f"  {emoji} Risk Level: {risk_level}")

    if results.current_price:
        output.append(f"  Current Price:            ${results.current_price:>10.2f}")
    output.append("")

    # Risk Bands
    output.append("📈 RISK BANDS")
    output.append("-" * 70)

    bands_to_show = results.risk_bands if full_table else results.get_nearest_bands(5)

    output.append(f"  {'Price':>12}  {'Risk Score':>12}  {'Level':>10}")
    output.append("  " + "-" * 40)

    for band in bands_to_show:
        risk_emoji = "🔴" if band.risk_score >= 0.7 else "🟡" if band.risk_score >= 0.3 else "🟢"
        current_marker = " ← CURRENT" if results.current_price and abs(band.price - results.current_price) < 1 else ""
        output.append(f"  ${band.price:>11.2f}  {band.risk_score:>12.3f}  {risk_emoji}{current_marker}")

    if not full_table:
        output.append(f"\n  💡 Showing 5 nearest bands. Use --full-table for complete list.")

    output.append("")

    # High Risk Alert
    high_risk_band = results.get_high_risk_threshold()
    if high_risk_band:
        output.append("⚠️  HIGH RISK ALERT")
        output.append("-" * 70)
        output.append(f"  Risk exceeds 0.7 at: ${high_risk_band.price:.2f}")
        if results.current_price:
            pct_move = ((high_risk_band.price / results.current_price) - 1) * 100
            output.append(f"  Distance from current: {pct_move:+.1f}%")
        output.append("")

    # Footer
    output.append("=" * 70)
    output.append("📖 Source: Into The Cryptoverse Risk Models API")
    output.append("⚠️  DISCLAIMER: For educational purposes only. Not investment advice.")
    output.append("=" * 70)

    return "\n".join(output)

def format_output_json(results: ITCRiskResponse) -> str:
    """Format results as JSON"""
    return results.model_dump_json(indent=2)

def main():
    parser = argparse.ArgumentParser(
        description="Fetch ITC Risk Models for Finance Guru™",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single ticker risk check
  %(prog)s TSLA --universe tradfi

  # Portfolio batch check
  %(prog)s TSLA AAPL MSTR --universe tradfi

  # Show full risk table
  %(prog)s TSLA --universe tradfi --full-table

  # JSON output
  %(prog)s TSLA --universe tradfi --output json
        """
    )

    parser.add_argument(
        "tickers",
        type=str,
        nargs="+",
        help="Ticker symbol(s) (e.g., TSLA, BTC)"
    )

    parser.add_argument(
        "--universe",
        type=str,
        choices=["crypto", "tradfi"],
        default="tradfi",
        help="Asset universe (default: tradfi)"
    )

    parser.add_argument(
        "--full-table",
        action="store_true",
        help="Show complete risk band table (default: nearest 5)"
    )

    parser.add_argument(
        "--output",
        type=str,
        choices=["human", "json"],
        default="human",
        help="Output format (default: human)"
    )

    args = parser.parse_args()

    try:
        # Initialize calculator
        calculator = ITCRiskCalculator()

        # Process each ticker
        for ticker in args.tickers:
            try:
                print(f"📥 Fetching ITC risk data for {ticker}...", file=sys.stderr)
                result = calculator.get_risk_score(ticker, args.universe)
                print(f"✅ Data retrieved successfully", file=sys.stderr)
                print("", file=sys.stderr)

                # Format output
                if args.output == "json":
                    output = format_output_json(result)
                else:
                    output = format_output_human(result, args.full_table)

                print(output)

                if len(args.tickers) > 1:
                    print("\n")  # Separator between tickers

            except ValueError as e:
                print(f"❌ ERROR for {ticker}: {e}", file=sys.stderr)
                continue
            except Exception as e:
                print(f"❌ UNEXPECTED ERROR for {ticker}: {e}", file=sys.stderr)
                import traceback
                traceback.print_exc(file=sys.stderr)
                continue

    except ValueError as e:
        print(f"❌ CONFIGURATION ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user", file=sys.stderr)
        sys.exit(130)

if __name__ == "__main__":
    main()
```

### Environment Configuration

**File:** `.env.example` (add to existing)

```bash
# Into The Cryptoverse API
ITC_API_KEY=your_itc_api_key_here
```

**Setup Instructions (add to README.md):**

```markdown
### ITC Risk Models API Setup

1. Get API key: https://app.intothecryptoverse.com/api
2. Add to `.env`: `ITC_API_KEY=your_key_here`
3. Test: `uv run python src/analysis/itc_risk_cli.py TSLA --universe tradfi`
```

### Dependencies

**File:** `pyproject.toml` (already has `requests`)

No new dependencies required - `requests` already present.

## Edge Cases & Error Handling

### Unsupported Tickers

**Scenario:** User requests ITC risk for PLTR or NVDA (not in ITC coverage)

**Handling:**
```python
# Fail fast with clear message
raise ValueError(
    f"PLTR not supported by ITC API.\n"
    f"Supported tradfi assets: TSLA, AAPL, MSTR, NFLX, SP500, commodities\n"
    f"Use risk_metrics_cli.py for this ticker."
)
```

**Exit Code:** 1 (error)

### API Key Missing

**Scenario:** `.env` file missing `ITC_API_KEY`

**Handling:**
```python
if not self.api_key:
    raise ValueError(
        "ITC API key required. Set ITC_API_KEY in .env file.\n"
        "Get your key at: https://app.intothecryptoverse.com/api"
    )
```

**Exit Code:** 1 (error)

### Rate Limit Hit (10 req/window)

**Scenario:** User makes too many API calls in short time

**Handling:**
- Retry with exponential backoff (3 attempts: 1s, 2s, 4s delays)
- If all retries fail, raise `requests.RequestException`
- Log retry attempts to stderr
- User should see: "⚠️  Rate limit hit, retrying in 2s..."

### Network Error / API Unavailable

**Scenario:** ITC API is down or network unreachable

**Handling:**
- Retry 3 times with exponential backoff
- After exhausting retries, fail gracefully with:
  ```
  ❌ ERROR: Unable to reach ITC API after 3 attempts.
  Use risk_metrics_cli.py for internal risk analysis.
  ```
- Exit code 1 (error)
- Agent workflows should catch this and continue with internal metrics only

### Current Price Unavailable (yfinance fails)

**Scenario:** yfinance can't fetch current price

**Handling:**
- Log warning to stderr: "⚠️  Current price unavailable, showing risk bands only"
- Set `current_price = None` in response
- Risk band table still displays
- "← CURRENT" marker won't appear in output

### Empty Risk Bands

**Scenario:** ITC API returns risk score but no risk bands

**Handling:**
- Display current risk score only
- Show warning: "⚠️  Risk bands unavailable from API"
- Tool still completes successfully (current risk score is primary data)

## User Experience

### Mental Model

**User Perspective:** ITC provides a "second opinion" on risk that complements internal quantitative metrics. It's not a replacement but an additional data point.

**Key Principle:** When ITC and internal metrics diverge, that's a signal to investigate further (not to trust one over the other automatically).

### Confusion Points & Solutions

**1. Confusion: "Why does ITC say high risk but my VaR is low?"**

**Solution:** Add interpretation to output:
```
💡 DIVERGENCE DETECTED:
   ITC Risk: 0.82 (HIGH)
   Your VaR95: 2.1% (LOW)

   Possible reasons:
   - Price approaching resistance level (technical risk)
   - Recent volatility spike not yet in 90-day window
   - Market sentiment shift not captured by historical stats

   ⚠️  RECOMMENDATION: Investigate before entering position
```

**2. Confusion: "What do the risk bands mean?"**

**Solution:** Add explainer to first-time runs:
```
📚 UNDERSTANDING RISK BANDS:
   Risk bands show how risk changes with price movement.
   Example: TSLA at $450 = 0.49 risk, at $1526 = 0.99 risk

   Use this to:
   - Set alerts when approaching high-risk zones
   - Understand where price could become dangerous
   - Plan exit strategies based on risk thresholds
```

**3. Confusion: "Should I trust ITC or my own metrics?"**

**Solution:** CLI footer message:
```
💡 HOW TO USE THIS DATA:
   ✓ Use ITC as one input among many
   ✓ Investigate when ITC diverges from your metrics
   ✗ Never rely solely on ITC for trading decisions
   ✗ Don't ignore your quantitative analysis

   Best practice: Check both ITC and risk_metrics_cli.py
```

### Feedback Requirements

**At Each Step:**

1. **Command Start:** "📥 Fetching ITC risk data for TSLA..."
2. **API Call Success:** "✅ Data retrieved successfully"
3. **Retry Attempts:** "⚠️  Rate limit hit, retrying in 2s... (attempt 2/3)"
4. **Unsupported Ticker:** "❌ ERROR: NVDA not supported by ITC API. Supported: [list]"
5. **API Unavailable:** "❌ ERROR: Unable to reach ITC API after 3 attempts."
6. **Batch Progress:** "Processing 3 tickers: TSLA ✓ | AAPL ⏳ | MSTR ⏳"

## Scope & Tradeoffs

### In Scope (MVP - All Implemented)

✅ **Core Functionality:**
- Single ticker CLI (`itc_risk_cli.py TSLA`)
- Portfolio batch checking (`itc_risk_cli.py TSLA AAPL MSTR`)
- Human-readable and JSON output formats
- Risk band interpretation (smart nearest 5 + `--full-table` flag)
- Error handling with retry logic and graceful degradation

✅ **Agent Integration:**
- Market Researcher auto-checks ITC for supported tickers
- Strategy Advisor includes ITC in pre-trade analysis
- Quant Analyst can invoke for comparison studies
- All agents detect divergence and flag warnings

✅ **Quality Features:**
- Current price enrichment from yfinance
- High-risk threshold alerts
- Divergence detection (when implemented with internal metrics)
- Educational tooltips in output

### Out of Scope

❌ **Historical Data Storage:** No database of past ITC risk scores (CLI is on-demand only)
❌ **Automated Trading Triggers:** Display data only, never auto-execute trades based on ITC
❌ **Custom Risk Model Building:** Use ITC models as-is (but leave window open for future enhancement)
❌ **Caching:** No persistent cache (originally considered Beads, but simpler to run CLI on-demand)

### Technical Debt Knowingly Accepted

**1. No Rate Limit Tracking:**
- **Accepted:** CLI doesn't track how many calls made in current window
- **Why:** ITC's "10 requests per window" is vague - window size unknown
- **Mitigation:** Retry logic handles rate limit responses gracefully
- **Future:** Could add call counter if rate limits become problem

**2. No Historical ITC Risk Trends:**
- **Accepted:** Can't show "ITC risk was 0.3 yesterday, now 0.8 - big spike!"
- **Why:** Adds complexity of storage layer (database or files)
- **Mitigation:** Users can manually run CLI daily and compare
- **Future:** Could add simple CSV logging if users request trends

**3. Divergence Detection Requires Manual Comparison:**
- **Accepted:** CLI doesn't auto-compare with `risk_metrics_cli.py` output
- **Why:** Would require calling both tools and complex comparison logic
- **Mitigation:** Users run both CLIs sequentially and compare visually
- **Future:** Could create `compare_risk_cli.py` wrapper that runs both

## Integration Requirements

### Agent Workflow Integration

**Market Researcher Agent:** When analyzing TSLA/AAPL/MSTR/NFLX, automatically:
1. Check if ticker is ITC-supported
2. Run `itc_risk_cli.py TICKER --universe tradfi --output json`
3. Parse JSON response
4. Include ITC risk score in research summary
5. Flag if ITC risk > 0.7 (high risk zone)

**Strategy Advisor Agent:** Before creating buy tickets:
1. Run ITC risk check for target ticker
2. If ITC risk > 0.7, add warning to buy ticket:
   ```
   ⚠️  HIGH RISK SIGNAL (ITC): Risk score 0.82
   Price approaching high-risk zone. Consider:
   - Reducing position size
   - Waiting for pullback
   - Setting tighter stop-loss
   ```

**Quant Analyst Agent:** For comparison studies:
1. Run both `risk_metrics_cli.py` and `itc_risk_cli.py`
2. If divergence detected (VaR low but ITC high, or vice versa), create analysis:
   ```
   DIVERGENCE ANALYSIS: TSLA
   Internal VaR95: 2.1% (Low risk)
   ITC Risk Score: 0.82 (High risk)

   Investigation needed: Why does market-implied risk
   exceed statistical risk? Check recent price action,
   resistance levels, and sentiment indicators.
   ```

### File Modifications Required

**New Files:**
- `src/models/itc_risk_inputs.py` (data models)
- `src/analysis/itc_risk.py` (calculator class)
- `src/analysis/itc_risk_cli.py` (CLI interface)

**Modified Files:**
- `.env.example` (add `ITC_API_KEY` entry)
- `CLAUDE.md` (add ITC tool to Agent-Tool Matrix)
- Agent prompt files:
  - `.claude/commands/fin-guru/agents/market-researcher.md`
  - `.claude/commands/fin-guru/agents/strategy-advisor.md`
  - `.claude/commands/fin-guru/agents/quant-analyst.md`

### Agent Prompt Updates

**Add to Market Researcher Agent:**

```markdown
## ITC Risk Models Integration

When analyzing supported tickers (TSLA, AAPL, MSTR, NFLX, SP500),
automatically check ITC risk:

```bash
uv run python src/analysis/itc_risk_cli.py TICKER --universe tradfi --output json
```

Include ITC risk score in research summary. Flag if risk > 0.7.

**Supported Tickers:**
- TradFi: TSLA, AAPL, MSTR, NFLX, SP500, DXY, XAUUSD, XAGUSD, commodities
- Crypto: BTC, ETH, and 27 others (see calculator for full list)

**Divergence Detection:**
If ITC risk diverges from your sentiment analysis, investigate and report:
- ITC High + Sentiment Bullish → Caution: market pricing in risk
- ITC Low + Sentiment Bearish → Potential opportunity: market underpricing risk
```

**Add to Strategy Advisor Agent:**

```markdown
## Pre-Trade ITC Risk Check

Before creating buy tickets for supported tickers, check ITC risk:

```bash
uv run python src/analysis/itc_risk_cli.py TICKER --universe tradfi
```

Add risk advisory to buy ticket if ITC risk > 0.7:

```
⚠️  HIGH RISK SIGNAL (ITC): Risk score 0.XX
Recommendation: [Reduce size / Wait for pullback / Set tight stop]
```
```

## Security & Compliance

### Sensitive Data

**API Key Storage:**
- Store in `.env` file (git-ignored)
- Load via `python-dotenv` in calculator class
- Never log API key to stdout/stderr
- Never commit API key to repository

**User Data:**
- No PII transmitted to ITC API (only ticker symbols)
- No portfolio holdings shared with external service
- ITC only sees individual ticker requests, not full portfolio context

### API Key Security

**`.gitignore` (verify present):**
```
.env
.env.local
*.key
```

**Error Messages (sanitize):**
```python
# GOOD - no key exposure
print("❌ API key invalid. Check ITC_API_KEY in .env")

# BAD - exposes key
print(f"❌ API key {api_key} is invalid")
```

### Authentication Requirements

**ITC API:** Requires API key passed as query parameter:
```
GET https://app.intothecryptoverse.com/api/v2/risk-models/price-based/tradfi/TSLA?apikey=YOUR_KEY
```

**Rate Limiting:** 10 requests per window (window size undefined by ITC)

**No OAuth:** Simple API key authentication only

### Compliance Considerations

**Educational Use Only:**
- All outputs include disclaimer: "For educational purposes only. Not investment advice."
- ITC data is supplemental, not authoritative
- Users must consult financial professionals before trading

**No Automated Trading:**
- CLI display only - never auto-executes trades
- Agents cannot make trading decisions based solely on ITC risk scores
- Human review required for all position entries

**Data Privacy:**
- No logging of user portfolio composition
- No transmission of holdings to external services
- Ticker requests are anonymized (ITC doesn't know who's requesting)

## Success Criteria & Testing

### Acceptance Criteria

**Functional Requirements:**

✅ **FR1:** CLI successfully fetches ITC risk score for supported tickers (TSLA, AAPL, MSTR, NFLX)
- **Test:** `uv run python src/analysis/itc_risk_cli.py TSLA --universe tradfi`
- **Expected:** Human-readable output with risk score 0-1, risk bands, current price

✅ **FR2:** CLI errors immediately for unsupported tickers (PLTR, NVDA, etc.)
- **Test:** `uv run python src/analysis/itc_risk_cli.py PLTR --universe tradfi`
- **Expected:** Error message listing supported assets, exit code 1

✅ **FR3:** Portfolio batch checking works for multiple tickers
- **Test:** `uv run python src/analysis/itc_risk_cli.py TSLA AAPL MSTR --universe tradfi`
- **Expected:** Three separate reports output sequentially

✅ **FR4:** JSON output format for programmatic parsing
- **Test:** `uv run python src/analysis/itc_risk_cli.py TSLA --universe tradfi --output json | jq`
- **Expected:** Valid JSON with all fields parseable

✅ **FR5:** Risk bands display intelligently (nearest 5 by default, full with flag)
- **Test:** Compare output with/without `--full-table` flag
- **Expected:** Default shows 5 bands, `--full-table` shows all

✅ **FR6:** High-risk threshold alerts when risk > 0.7
- **Test:** Run on ticker with high risk score
- **Expected:** "⚠️ HIGH RISK ALERT" section in output

**Non-Functional Requirements:**

✅ **NFR1:** Tool fails gracefully when API unavailable
- **Test:** Disconnect network, run CLI
- **Expected:** Retry 3 times with delays, then clear error message

✅ **NFR2:** Missing API key produces clear error message
- **Test:** Unset `ITC_API_KEY` env var, run CLI
- **Expected:** Error with instructions to set key in .env

✅ **NFR3:** Rate limit handling with retry logic
- **Test:** Make 15+ rapid requests to trigger rate limit
- **Expected:** CLI retries with exponential backoff, eventually succeeds or fails gracefully

✅ **NFR4:** Current price enrichment from yfinance works
- **Test:** Check output includes "Current Price: $XXX.XX"
- **Expected:** Price fetched from yfinance and displayed

### Testing Strategy

**Unit Tests (pytest):**

**File:** `tests/test_itc_risk.py`

```python
import pytest
from src.analysis.itc_risk import ITCRiskCalculator
from src.models.itc_risk_inputs import ITCRiskResponse

def test_calculator_requires_api_key():
    """Test that calculator raises error without API key"""
    import os
    os.environ.pop("ITC_API_KEY", None)
    with pytest.raises(ValueError, match="ITC API key required"):
        ITCRiskCalculator()

def test_validate_ticker_fails_for_unsupported():
    """Test that unsupported tickers raise clear error"""
    calc = ITCRiskCalculator(api_key="dummy")
    with pytest.raises(ValueError, match="PLTR not supported"):
        calc.validate_ticker("PLTR", "tradfi")

def test_validate_ticker_passes_for_supported():
    """Test that supported tickers pass validation"""
    calc = ITCRiskCalculator(api_key="dummy")
    calc.validate_ticker("TSLA", "tradfi")  # Should not raise

@pytest.mark.integration
def test_get_risk_score_live(api_key):
    """Integration test with real API (requires key)"""
    calc = ITCRiskCalculator(api_key=api_key)
    result = calc.get_risk_score("TSLA", "tradfi")
    assert isinstance(result, ITCRiskResponse)
    assert 0 <= result.current_risk_score <= 1
    assert len(result.risk_bands) > 0

def test_get_nearest_bands():
    """Test risk band filtering logic"""
    response = ITCRiskResponse(
        symbol="TSLA",
        universe="tradfi",
        current_price=450.0,
        current_risk_score=0.5,
        risk_bands=[
            RiskBand(price=221.90, risk_score=0.0),
            RiskBand(price=450.15, risk_score=0.489),
            RiskBand(price=1526.19, risk_score=0.991),
        ],
        timestamp=datetime.now()
    )
    nearest = response.get_nearest_bands(2)
    assert len(nearest) == 2
    assert nearest[0].price == 450.15  # Closest to current price
```

**Integration Tests (manual for MVP):**

```bash
# Test 1: Supported ticker (TSLA)
uv run python src/analysis/itc_risk_cli.py TSLA --universe tradfi
# Expected: Risk score, bands, current price

# Test 2: Unsupported ticker (NVDA)
uv run python src/analysis/itc_risk_cli.py NVDA --universe tradfi
# Expected: Error message with supported assets list

# Test 3: Batch processing
uv run python src/analysis/itc_risk_cli.py TSLA AAPL MSTR --universe tradfi
# Expected: Three separate reports

# Test 4: JSON output
uv run python src/analysis/itc_risk_cli.py TSLA --universe tradfi --output json | jq
# Expected: Valid JSON

# Test 5: Full risk table
uv run python src/analysis/itc_risk_cli.py TSLA --universe tradfi --full-table
# Expected: Complete risk band table

# Test 6: Missing API key
unset ITC_API_KEY
uv run python src/analysis/itc_risk_cli.py TSLA --universe tradfi
# Expected: Clear error about missing key

# Test 7: Crypto universe
uv run python src/analysis/itc_risk_cli.py BTC --universe crypto
# Expected: BTC risk score and bands
```

**Agent Integration Tests:**

```bash
# Test: Market Researcher auto-invokes ITC
# Manually trigger Market Researcher on TSLA analysis
# Verify: Agent output includes "ITC Risk Score: X.XX"

# Test: Strategy Advisor pre-trade check
# Request buy ticket for TSLA
# Verify: Buy ticket includes ITC risk advisory if risk > 0.7

# Test: Quant Analyst comparison
# Request risk comparison for TSLA
# Verify: Agent runs both risk_metrics_cli.py and itc_risk_cli.py
```

### Performance Benchmarks

**Target Latencies:**
- Single ticker API call: < 2 seconds (p50), < 5 seconds (p99)
- Batch 10 tickers: < 20 seconds total (sequential calls)
- Retry with backoff: 1s + 2s + 4s = 7s max for 3 attempts

**Rate Limit Management:**
- CLI doesn't prevent user from hitting rate limits (accepted tradeoff)
- Retry logic handles 429 responses gracefully
- Future: Could add inter-request delays for batch mode

## Implementation Notes

### Codebase-Specific Guidance

**Files to Create:**

1. **`src/models/itc_risk_inputs.py`**
   - Follow existing model pattern from `src/models/risk_inputs.py`
   - Use Pydantic `BaseModel` with `Field` validators
   - Add docstrings for all model classes

2. **`src/analysis/itc_risk.py`**
   - Follow existing calculator pattern from `src/analysis/risk_metrics.py`
   - Class name: `ITCRiskCalculator`
   - Use `requests` library (already in dependencies)
   - Add retry logic with exponential backoff

3. **`src/analysis/itc_risk_cli.py`**
   - Follow existing CLI pattern from `src/analysis/risk_metrics_cli.py`
   - Use `argparse` for CLI interface
   - Add `#!/usr/bin/env python3` shebang
   - Make executable: `chmod +x src/analysis/itc_risk_cli.py`

**Files to Modify:**

1. **`.env.example`**
   - Add line: `ITC_API_KEY=your_itc_api_key_here`
   - Add comment: `# Into The Cryptoverse Risk Models API`

2. **`CLAUDE.md`**
   - Update Agent-Tool Matrix table
   - Add ITC risk CLI to Market Researcher, Strategy Advisor, Quant Analyst rows
   - Add new row for ITC risk tool with use cases

3. **Agent Prompt Files:**
   - `.claude/commands/fin-guru/agents/market-researcher.md`
   - `.claude/commands/fin-guru/agents/strategy-advisor.md`
   - `.claude/commands/fin-guru/agents/quant-analyst.md`
   - Add ITC integration section to each (see "Agent Prompt Updates" above)

### Patterns to Follow

**3-Layer Architecture (CRITICAL):**
```
Layer 1 (Models)     → src/models/itc_risk_inputs.py
Layer 2 (Calculator) → src/analysis/itc_risk.py
Layer 3 (CLI)        → src/analysis/itc_risk_cli.py
```

**Error Handling Pattern:**
```python
try:
    result = calculator.get_risk_score(ticker, universe)
except ValueError as e:
    # User error (bad input, unsupported ticker)
    print(f"❌ ERROR: {e}", file=sys.stderr)
    sys.exit(1)
except requests.RequestException as e:
    # API error (network, rate limit, etc.)
    print(f"❌ API ERROR: {e}", file=sys.stderr)
    sys.exit(1)
```

**CLI Output Pattern:**
```python
# Status messages → stderr (so JSON output stays clean)
print("📥 Fetching data...", file=sys.stderr)

# Actual output → stdout
print(formatted_result)
```

**Agent Integration Pattern:**
```python
# In agent workflows, prefer JSON output
result = subprocess.run([
    "uv", "run", "python", "src/analysis/itc_risk_cli.py",
    ticker, "--universe", "tradfi", "--output", "json"
], capture_output=True, text=True)

data = json.loads(result.stdout)
risk_score = data["current_risk_score"]
```

### Testing Workflow

**Pre-Implementation:**
1. Create `.env` file with test ITC API key
2. Manually test API with `curl`:
   ```bash
   curl "https://app.intothecryptoverse.com/api/v2/risk-models/price-based/tradfi/TSLA?apikey=YOUR_KEY"
   ```
3. Verify response structure matches expected format

**During Implementation:**
1. Create models first (TDD approach)
2. Write calculator class with unit tests
3. Create CLI and test manually
4. Add agent integration last (after CLI validated)

**Post-Implementation:**
1. Run full integration test suite
2. Test with Market Researcher agent on TSLA
3. Create example buy ticket with ITC risk advisory
4. Update documentation in `CLAUDE.md`

### Dependencies Already Present

✅ `requests` - HTTP client for API calls
✅ `pydantic` - Data validation models
✅ `python-dotenv` - Environment variable loading
✅ `yfinance` - Current price enrichment

**No new dependencies needed!**

### Example Usage After Implementation

```bash
# Basic usage
uv run python src/analysis/itc_risk_cli.py TSLA --universe tradfi

# Compare with internal metrics
uv run python src/analysis/risk_metrics_cli.py TSLA --days 90
uv run python src/analysis/itc_risk_cli.py TSLA --universe tradfi

# Portfolio health check (supported positions only)
for ticker in TSLA AAPL MSTR; do
    uv run python src/analysis/itc_risk_cli.py $ticker --universe tradfi
done

# JSON for agent parsing
uv run python src/analysis/itc_risk_cli.py TSLA --universe tradfi --output json | jq '.current_risk_score'
```

## Appendix: ITC API Coverage

### Supported TradFi Assets (13)

**Stocks (4):**
- TSLA (Tesla)
- AAPL (Apple)
- MSTR (MicroStrategy)
- NFLX (Netflix)

**Indices (1):**
- SP500 (S&P 500 Index)

**Currency (1):**
- DXY (U.S. Dollar Index)

**Commodities (7):**
- XAUUSD (Gold Spot)
- XAGUSD (Silver Spot)
- XPDUSD (Palladium)
- PL (Platinum)
- HG (Copper)
- NICKEL (Nickel)

### Supported Crypto Assets (29)

**Major Coins:**
BTC, ETH, BNB, SOL, XRP, ADA, DOGE, LINK, AVAX, DOT, SHIB, LTC, AAVE, ATOM, POL, ALGO, HBAR, RENDER, VET, TRX, TON, SUI, XLM, XMR, XTZ, SKY

**Meta Metrics:**
- BTC.D (Bitcoin Dominance)
- TOTAL (Total Market Cap)
- TOTAL6 (Total Market Cap Excl. BTC, ETH, Stables)

### Coverage Gaps (Notable Omissions)

**Finance Guru Portfolio Tickers NOT Covered:**
- PLTR (Palantir) ❌
- NVDA (NVIDIA) ❌
- COIN (Coinbase) ❌
- SPY (as ETF - use SP500 proxy) ⚠️
- SOFI (SoFi) ❌
- VOO (Vanguard ETF) ❌
- GOOGL (Alphabet) ❌
- And all dividend CEFs/ETFs (JEPI, JEPQ, etc.) ❌

**Implication:** ITC integration most valuable for TSLA monitoring (your largest growth position), with SP500 for market context.

---

## Implementation Tasks

<!-- RBP-TASKS-START -->

### Task 1: Create ITC Risk Data Models (Layer 1)
- **ID:** itc-001
- **Dependencies:** none
- **Files:** `src/models/itc_risk_inputs.py`
- **Acceptance:** Pydantic models validate correctly, all fields documented
- **Tests:** `uv run pytest tests/test_itc_risk.py::test_models -v`

### Task 2: Create ITC Risk Calculator (Layer 2)
- **ID:** itc-002
- **Dependencies:** itc-001
- **Files:** `src/analysis/itc_risk.py`
- **Acceptance:** Calculator fetches data from ITC API, handles errors gracefully, retry logic works
- **Tests:** `uv run pytest tests/test_itc_risk.py::test_calculator -v`

### Task 3: Create ITC Risk CLI (Layer 3)
- **ID:** itc-003
- **Dependencies:** itc-002
- **Files:** `src/analysis/itc_risk_cli.py`
- **Acceptance:** CLI outputs human and JSON formats, batch processing works, error messages clear
- **Tests:** `uv run python src/analysis/itc_risk_cli.py TSLA --universe tradfi`

### Task 4: Update Environment Configuration
- **ID:** itc-004
- **Dependencies:** none
- **Files:** `.env.example`
- **Acceptance:** ITC_API_KEY entry added with comment
- **Tests:** `grep ITC_API_KEY .env.example`

### Task 5: Create Unit Tests
- **ID:** itc-005
- **Dependencies:** itc-003
- **Files:** `tests/test_itc_risk.py`
- **Acceptance:** All unit tests pass, covers models, calculator, and CLI
- **Tests:** `uv run pytest tests/test_itc_risk.py -v`

### Task 6: Update Agent Prompts
- **ID:** itc-006
- **Dependencies:** itc-003
- **Files:** `.claude/commands/fin-guru/agents/market-researcher.md`, `.claude/commands/fin-guru/agents/strategy-advisor.md`, `.claude/commands/fin-guru/agents/quant-analyst.md`
- **Acceptance:** All three agent prompts include ITC integration section
- **Tests:** `grep -l "ITC Risk" .claude/commands/fin-guru/agents/*.md | wc -l` (should be 3)

### Task 7: Update CLAUDE.md Tool Matrix
- **ID:** itc-007
- **Dependencies:** itc-006
- **Files:** `CLAUDE.md`
- **Acceptance:** Agent-Tool Matrix includes ITC risk CLI entries
- **Tests:** `grep -q "itc_risk_cli" CLAUDE.md`

<!-- RBP-TASKS-END -->

### Test Command

```bash
uv run pytest tests/test_itc_risk.py -v
```

---

**End of Specification**

**Status:** ✅ Ready for Implementation - Zero Open Questions
