# Phase 7: Total Return Calculator - Research

**Researched:** 2026-02-02
**Domain:** Total return calculation (price + dividends), DRIP modeling, yfinance dividend API
**Confidence:** HIGH (well-understood financial calculation; established codebase patterns; verified yfinance API)

## Summary

Phase 7 adds a total return calculator CLI that computes three distinct metrics per ticker -- price return, dividend return, and total return -- with optional DRIP (dividend reinvestment) modeling. The tool follows the established 3-layer architecture already used by 8 existing CLI tools in the codebase. Phase 6 creates the Pydantic models (`TotalReturnInput`, `DividendRecord`, `TickerReturn`) and `config_loader.py` that this phase consumes.

The primary technical risk is **yfinance dividend data quality**: Yahoo Finance has well-documented intermittent missing dividends, non-deterministic dividend retrieval, and inconsistent split-adjustment behavior. The mitigation is a data quality validation layer that detects gaps and warns the user (requirement TR-03). The DRIP calculation itself is straightforward: reinvest each dividend at the ex-date close price to accumulate fractional shares. The total return is final portfolio value (price * shares) versus initial investment.

The multi-ticker comparison pattern already exists in `correlation_cli.py` (uses `nargs='+'` for tickers, `yf.download()` for batch fetching). The total return CLI should follow the same approach but with per-ticker dividend data fetched via `yf.Ticker().dividends` since `yf.download()` dividend columns can be unreliable for multi-ticker batch calls.

**Primary recommendation:** Build `TotalReturnCalculator` as a single calculator class with `calculate_price_return()`, `calculate_dividend_return()`, `calculate_total_return()`, and `calculate_drip_return()` methods. Use `yf.Ticker(symbol).history()` with its built-in Dividends column for synchronized price+dividend data, and cross-validate against `yf.Ticker(symbol).dividends` to detect gaps.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| yfinance | >=0.2.66 (1.1.0 latest) | Historical prices and dividend data | Already in project, no breaking changes in 1.0/1.1 |
| pandas | >=2.3.2 | Time-series data manipulation, pct_change(), cumprod() | Already in project, handles all return calculations |
| pydantic | >=2.10.6 | Input/output model validation | Already in project, required by 3-layer architecture |
| numpy | >=2.3.3 | Numerical operations (annualization, cumulative products) | Already in project |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| argparse | stdlib | CLI argument parsing | Layer 3 CLI interface |
| json | stdlib | JSON output serialization | --output json flag |
| datetime | stdlib | Date manipulation | Period calculations |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| yfinance dividends | Financial Datasets MCP | MCP requires API key; yfinance is free and already integrated |
| Manual return calc | pandas-ta or quantlib | Over-engineered for simple return arithmetic |
| Ticker().history() | yf.download() | download() is better for batch price-only, but Ticker().history() includes dividends more reliably for single tickers |

**Installation:**
```bash
# No new dependencies needed -- all libraries already in pyproject.toml
uv sync
```

## Architecture Patterns

### Recommended Project Structure
```
src/
  models/
    total_return_inputs.py     # [Phase 6 creates] TotalReturnInput, DividendRecord, TickerReturn
  analysis/
    total_return.py            # [Phase 7] TotalReturnCalculator class (Layer 2)
    total_return_cli.py        # [Phase 7] CLI interface (Layer 3)
  utils/
    config_loader.py           # [Phase 6 creates] HedgeConfig from user-profile.yaml
tests/
  python/
    test_total_return.py       # [Phase 7] Known-answer tests
```

### Pattern 1: 3-Layer Architecture (Established)

**What:** Pydantic Models -> Calculator Classes -> CLI Interface
**When to use:** All financial analysis tools in this codebase
**Source:** Established pattern across 8 existing CLIs (see `src/CLAUDE.md`)

Layer 1 (Models -- created by Phase 6):
```python
# src/models/total_return_inputs.py (Phase 6 responsibility)
from pydantic import BaseModel, Field
from datetime import date

class DividendRecord(BaseModel):
    """Single dividend payment record."""
    ex_date: date
    amount: float = Field(..., gt=0, description="Dividend per share")
    close_price: float = Field(..., gt=0, description="Close price on ex-date")

class TotalReturnInput(BaseModel):
    """Input for total return calculation."""
    ticker: str = Field(..., pattern=r"^[A-Z\-\.]+$")
    prices: list[float] = Field(..., min_length=2)
    dates: list[date]
    dividends: list[DividendRecord] = Field(default_factory=list)
    initial_shares: float = Field(default=1.0, gt=0)

class TickerReturn(BaseModel):
    """Output for a single ticker's return analysis."""
    ticker: str
    period_start: date
    period_end: date
    price_return: float  # e.g., 0.12 for 12%
    dividend_return: float  # e.g., 0.04 for 4%
    total_return: float  # e.g., 0.16 for 16%
    annualized_return: float
    # DRIP fields
    drip_total_return: float | None = None
    drip_final_shares: float | None = None
    drip_share_growth: float | None = None  # e.g., 1.03 for 3% more shares
    # Data quality
    dividend_count: int = 0
    data_quality_warnings: list[str] = Field(default_factory=list)
```

Layer 2 (Calculator):
```python
# src/analysis/total_return.py
class TotalReturnCalculator:
    """Calculate price return, dividend return, total return, and DRIP return."""

    def __init__(self, data: TotalReturnInput):
        self.data = data

    def calculate_price_return(self) -> float:
        """(ending_price - starting_price) / starting_price"""

    def calculate_dividend_return(self) -> float:
        """sum(dividends) / starting_price"""

    def calculate_total_return(self) -> float:
        """price_return + dividend_return"""

    def calculate_drip_return(self) -> tuple[float, float]:
        """Reinvest each dividend at ex-date close price. Returns (total_return, final_shares)."""

    def validate_dividend_data(self) -> list[str]:
        """Check for gaps, missing expected dividends, split artifacts."""

    def calculate_all(self) -> TickerReturn:
        """Run all calculations and return validated output."""
```

Layer 3 (CLI):
```python
# src/analysis/total_return_cli.py
# Follows same pattern as risk_metrics_cli.py and correlation_cli.py
# argparse with ticker(s), --days, --output json/human, --drip flag
```

### Pattern 2: Multi-Ticker Comparison (Established in correlation_cli.py)

**What:** Accept multiple positional ticker args, fetch data for each, display side-by-side
**When to use:** `total_return_cli.py SCHD JEPI VYM --days 252`
**Source:** `src/analysis/correlation_cli.py` lines 329-335

```python
# Existing pattern from correlation_cli.py
parser.add_argument(
    'tickers',
    type=str,
    nargs='+',
    help='Stock ticker symbols (e.g., SCHD JEPI VYM)'
)
```

For total return, iterate per-ticker rather than using batch `yf.download()` because each ticker needs its own dividend history separately:
```python
results = []
for ticker in args.tickers:
    data = fetch_ticker_data(ticker, args.days)
    calculator = TotalReturnCalculator(data)
    result = calculator.calculate_all()
    results.append(result)
# Display side-by-side comparison table
```

### Pattern 3: Data Fetching (Established)

**What:** Use `yf.Ticker(symbol).history()` which returns DataFrame with Close and Dividends columns
**When to use:** Fetching synchronized price + dividend data for a single ticker
**Source:** yfinance API, already used throughout codebase

```python
import yfinance as yf
from datetime import datetime, timedelta

def fetch_ticker_data(ticker: str, days: int) -> TotalReturnInput:
    """Fetch price and dividend data for total return calculation."""
    start_date = datetime.now() - timedelta(days=int(days * 1.5))
    end_date = datetime.now()

    stock = yf.Ticker(ticker)
    hist = stock.history(start=start_date, end=end_date)
    # hist DataFrame columns: Open, High, Low, Close, Volume, Dividends, Stock Splits

    prices = hist['Close'].tolist()
    dates = [d.date() for d in hist.index]

    # Extract non-zero dividend records
    div_mask = hist['Dividends'] > 0
    dividends = [
        DividendRecord(
            ex_date=d.date(),
            amount=row['Dividends'],
            close_price=row['Close']
        )
        for d, row in hist[div_mask].iterrows()
    ]

    return TotalReturnInput(
        ticker=ticker.upper(),
        prices=prices,
        dates=dates,
        dividends=dividends,
    )
```

### Pattern 4: DRIP Calculation

**What:** Reinvest each dividend at ex-date close price, track growing share count
**When to use:** --drip flag or default DRIP mode
**Source:** Standard DRIP methodology (Charles Schwab, DRIPCalc, institutional tools)

```python
def calculate_drip_return(self) -> tuple[float, float]:
    """
    DRIP: reinvest dividends at ex-date close price.

    For each dividend:
      new_shares = (current_shares * dividend_per_share) / close_price_on_ex_date
      current_shares += new_shares

    Total return = (final_shares * final_price) / (initial_shares * initial_price) - 1
    """
    shares = self.data.initial_shares
    initial_value = shares * self.data.prices[0]

    for div in self.data.dividends:
        dividend_cash = shares * div.amount
        new_shares = dividend_cash / div.close_price
        shares += new_shares

    final_value = shares * self.data.prices[-1]
    drip_return = (final_value / initial_value) - 1.0
    return drip_return, shares
```

### Anti-Patterns to Avoid
- **Using Adjusted Close for total return with separate dividends**: Adjusted Close already factors in dividends. Adding dividends on top double-counts.
- **Using yf.download() for dividend data with multiple tickers**: The batch download Dividends column is less reliable than per-ticker Ticker().history(). Use per-ticker fetching for dividend data.
- **Assuming dividends are complete**: yfinance dividend data has known gaps. Always validate and warn.
- **Ignoring ex-date vs payment date**: yfinance returns ex-dividend dates, which is correct for DRIP modeling (shares are bought at ex-date price). Do not conflate with payment dates.
- **Hardcoding annualization as 252**: Trading days is correct for price return annualization, but dividend frequency varies (quarterly, monthly). Use calendar days for annualization: `annualized = (1 + total_return) ** (365 / calendar_days) - 1`.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Daily price returns | Manual loop over prices | `pd.Series(prices).pct_change()` | Vectorized, handles edge cases, standard |
| Cumulative returns | Running product loop | `(1 + returns).cumprod()` | pandas optimized, handles NaN properly |
| Annualized returns | Simple multiplication | `(1 + total_return) ** (365 / days) - 1` | Accounts for compounding correctly |
| Date alignment | Manual index matching | `pd.DataFrame` with DatetimeIndex | pandas handles gaps, weekends automatically |
| JSON serialization | Custom dict building | `model.model_dump_json(indent=2)` | Pydantic handles date serialization, validation |
| CLI argument parsing | Custom string parsing | `argparse` with epilog examples | Consistent with all 8 existing tools |

**Key insight:** The return calculations are trivial arithmetic. The complexity is in data quality (detecting gaps, handling splits) and presentation (side-by-side comparison formatting). Do not over-engineer the math; invest effort in validation and UX.

## Common Pitfalls

### Pitfall 1: Double-Counting Dividends with Adjusted Close
**What goes wrong:** Using Adj Close (which already accounts for dividends) AND adding dividend income produces inflated returns.
**Why it happens:** yfinance `history()` returns both `Close` and `Adj Close`. The difference is dividend/split adjustment.
**How to avoid:** Use raw `Close` prices when separately accounting for dividends. Never mix `Adj Close` with explicit dividend calculations.
**Warning signs:** Total return significantly higher than expected; DRIP return exceeds what dividend yield could justify.

### Pitfall 2: yfinance Non-Deterministic Missing Dividends
**What goes wrong:** Same query returns different dividend counts on different runs. Dividends silently missing.
**Why it happens:** Yahoo Finance upstream API is unreliable. Known GitHub issues #930, #984, #568.
**How to avoid:** Implement dividend gap detection: compare expected dividend frequency (quarterly/monthly based on ticker profile) against actual count. Warn when count is lower than expected.
**Warning signs:** Dividend count for SCHD showing 2 instead of 4 for a year period; dividend return suspiciously low for known high-yield ETFs.

### Pitfall 3: Stock Split Artifacts in Dividend Data
**What goes wrong:** Historical dividends not adjusted for splits, making pre-split dividends appear much larger.
**Why it happens:** yfinance sometimes adjusts dividends for splits and sometimes does not (GitHub issue #307). The behavior is inconsistent across runs.
**How to avoid:** Use `history()` which generally returns split-adjusted data. Cross-check: if a single dividend amount is >2x the median, flag it as a possible split artifact.
**Warning signs:** One dividend record showing $5.00 when others are $0.50; sudden spike in dividend return for a specific quarter.

### Pitfall 4: Timezone Inconsistencies in Date Comparison
**What goes wrong:** Comparing timezone-aware yfinance dates with timezone-naive dates raises errors or mismatches.
**Why it happens:** yfinance may return tz-aware DatetimeIndex. Different methods return different timezone handling.
**How to avoid:** Always normalize to timezone-naive dates with `.date()` conversion (already done in existing codebase -- see `risk_metrics_cli.py` line 108).
**Warning signs:** `TypeError: can't compare offset-naive and offset-aware datetimes`; dividend records not matching price dates.

### Pitfall 5: Insufficient Data Period for Dividend Tickers
**What goes wrong:** Short period (e.g., 30 days) may contain zero dividends, making dividend return appear as 0%.
**Why it happens:** Most dividend stocks pay quarterly. 30 days may fall between ex-dates.
**How to avoid:** Warn when period is too short to capture at least one dividend. Recommend minimum 90 days for dividend analysis, 252 days for meaningful comparison.
**Warning signs:** Dividend return showing 0% for known dividend-paying stocks.

### Pitfall 6: DRIP Fractional Share Precision
**What goes wrong:** Floating point accumulation errors over many reinvestment periods.
**Why it happens:** Each DRIP reinvestment adds a small fractional share. Over years of quarterly dividends, precision matters.
**How to avoid:** Use Python float (64-bit double) which has sufficient precision for this use case. Round final display values, not intermediate calculations.
**Warning signs:** Share count showing >15 decimal places; tiny discrepancies between calculated and expected values.

## Code Examples

Verified patterns from the existing codebase and yfinance documentation:

### Fetching Dividend Data from yfinance
```python
# Source: yfinance API, verified against codebase pattern in market_data.py
import yfinance as yf

stock = yf.Ticker("SCHD")

# Method 1: history() -- includes both Close and Dividends columns (RECOMMENDED)
hist = stock.history(start="2025-01-01", end="2026-01-01")
# Returns DataFrame: Open, High, Low, Close, Volume, Dividends, Stock Splits
# Dividends column is 0.0 on non-dividend dates, actual amount on ex-dates

# Method 2: dividends property -- returns only dividend dates/amounts
divs = stock.dividends
# Returns Series: index=ex-dividend dates, values=per-share amount

# Method 3: actions property -- returns both dividends and splits
actions = stock.actions
# Returns DataFrame: Dividends, Stock Splits columns
```

### Price Return Calculation
```python
# Source: Standard financial calculation, matches existing codebase pattern
def calculate_price_return(prices: list[float]) -> float:
    """Simple price return over the period."""
    if len(prices) < 2:
        raise ValueError("Need at least 2 price points")
    return (prices[-1] - prices[0]) / prices[0]
```

### Dividend Return Calculation
```python
# Source: Standard financial calculation
def calculate_dividend_return(dividends: list[DividendRecord], starting_price: float) -> float:
    """Total dividend income as percentage of starting investment."""
    total_dividends = sum(d.amount for d in dividends)
    return total_dividends / starting_price
```

### DRIP Return with Growing Share Count
```python
# Source: Standard DRIP methodology (Schwab, DRIPCalc)
def calculate_drip_return(
    prices: list[float],
    dividends: list[DividendRecord],
    initial_shares: float = 1.0,
) -> tuple[float, float, list[tuple[date, float]]]:
    """
    Returns: (drip_total_return, final_shares, share_history)
    share_history is list of (date, cumulative_shares) for display
    """
    shares = initial_shares
    initial_value = shares * prices[0]
    share_history = []

    for div in dividends:
        dividend_cash = shares * div.amount
        new_shares = dividend_cash / div.close_price
        shares += new_shares
        share_history.append((div.ex_date, shares))

    final_value = shares * prices[-1]
    drip_return = (final_value / initial_value) - 1.0
    return drip_return, shares, share_history
```

### Dividend Gap Detection (TR-03 Requirement)
```python
# Source: Designed for this project based on known yfinance issues
EXPECTED_FREQUENCIES = {
    # Monthly dividend ETFs
    "JEPI": 12, "JEPQ": 12, "QQQI": 12, "SPYI": 12,
    "YMAX": 12, "MSTY": 12, "AMZY": 12,
    # Quarterly dividend ETFs/stocks
    "SCHD": 4, "VYM": 4, "VOO": 4, "SPY": 4,
    "AAPL": 4, "MSFT": 4,
}

def validate_dividend_data(
    ticker: str,
    dividends: list[DividendRecord],
    period_days: int,
) -> list[str]:
    """Check for dividend data quality issues."""
    warnings = []

    # Check 1: Expected frequency vs actual
    expected_freq = EXPECTED_FREQUENCIES.get(ticker)
    if expected_freq:
        expected_count = max(1, int(expected_freq * period_days / 365))
        actual_count = len(dividends)
        if actual_count < expected_count * 0.75:  # 25% tolerance
            warnings.append(
                f"Expected ~{expected_count} dividends for {ticker} over "
                f"{period_days} days, found {actual_count}. "
                f"Dividend data may be incomplete."
            )

    # Check 2: Suspiciously large dividend (possible split artifact)
    if len(dividends) >= 2:
        amounts = [d.amount for d in dividends]
        median_amount = sorted(amounts)[len(amounts) // 2]
        for div in dividends:
            if div.amount > median_amount * 3:
                warnings.append(
                    f"Dividend on {div.ex_date} ({div.amount:.4f}) is >3x "
                    f"median ({median_amount:.4f}). Possible stock split artifact."
                )

    # Check 3: No dividends at all for known dividend payers
    if len(dividends) == 0 and ticker in EXPECTED_FREQUENCIES:
        warnings.append(
            f"No dividends found for {ticker} (expected dividend payer). "
            f"yfinance may have data gaps. Results show price return only."
        )

    return warnings
```

### Human-Readable Multi-Ticker Comparison Output
```python
# Source: Follows pattern from correlation_cli.py format_human_output()
def format_comparison_table(results: list[TickerReturn]) -> str:
    """Side-by-side comparison of total returns."""
    lines = []
    lines.append(f"\n{'='*70}")
    lines.append("TOTAL RETURN COMPARISON")
    lines.append(f"Period: {results[0].period_start} to {results[0].period_end}")
    lines.append(f"{'='*70}\n")

    # Header
    header = f"{'Metric':<25}" + "".join(f"{r.ticker:>12}" for r in results)
    lines.append(header)
    lines.append("-" * (25 + 12 * len(results)))

    # Rows
    lines.append(f"{'Price Return':<25}" + "".join(f"{r.price_return:>11.2%}" + " " for r in results))
    lines.append(f"{'Dividend Return':<25}" + "".join(f"{r.dividend_return:>11.2%}" + " " for r in results))
    lines.append(f"{'Total Return':<25}" + "".join(f"{r.total_return:>11.2%}" + " " for r in results))
    lines.append(f"{'Annualized Return':<25}" + "".join(f"{r.annualized_return:>11.2%}" + " " for r in results))

    if any(r.drip_total_return is not None for r in results):
        lines.append("")
        lines.append(f"{'DRIP Total Return':<25}" + "".join(
            f"{r.drip_total_return:>11.2%}" + " " if r.drip_total_return is not None else f"{'N/A':>12}"
            for r in results
        ))
        lines.append(f"{'DRIP Share Growth':<25}" + "".join(
            f"{r.drip_share_growth:>11.2%}" + " " if r.drip_share_growth is not None else f"{'N/A':>12}"
            for r in results
        ))

    lines.append(f"\n{'='*70}")
    lines.append("DISCLAIMER: For educational purposes only. Not investment advice.")
    lines.append(f"{'='*70}\n")

    return "\n".join(lines)
```

### JSON Output Pattern
```python
# Source: Matches existing pattern in risk_metrics_cli.py format_output_json()
import json

def format_json_output(results: list[TickerReturn]) -> str:
    """Format results as JSON array."""
    return json.dumps(
        [r.model_dump() for r in results],
        indent=2,
        default=str,  # Handles date serialization
    )
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| yfinance 0.2.x | yfinance 1.0/1.1 | Jan 2026 | No breaking changes; new `yf.config` class, better price repair |
| `auto_adjust=True` default | Explicit `auto_adjust` handling | yfinance 1.0 | Must be explicit about whether using adjusted or raw prices |
| Manual split adjustment | `repair=True` in history() | yfinance 0.2.x | Price repair available but inconsistent (GitHub #2643) |
| pandas 2.x | pandas 3.0 support | yfinance 1.1.0 | Timestamp.utcnow deprecation resolved |

**Deprecated/outdated:**
- `Timestamp.utcnow()`: Deprecated in pandas 3.0, fixed in yfinance 1.1.0
- Old yfinance config method: Deprecation warnings in 1.0, new `yf.config` class preferred

**Version note:** Project pinned at `yfinance>=0.2.66` in pyproject.toml. Both 0.2.66 and 1.1.0 work for this use case. No need to force upgrade for Phase 7; the dividend API is the same across versions.

## Open Questions

Things that couldn't be fully resolved:

1. **Phase 6 Model Exact Schema**
   - What we know: Phase 6 creates `TotalReturnInput`, `DividendRecord`, `TickerReturn` in `src/models/total_return_inputs.py`
   - What's unclear: Exact field names and validators (Phase 6 has no plans yet)
   - Recommendation: Phase 7 planner should define the ideal model shape and communicate to Phase 6 if Phase 6 has not yet been planned. The models shown in this research are the recommended shapes.

2. **Expected Dividend Frequency Database**
   - What we know: TR-03 requires data quality warnings for missing dividends
   - What's unclear: How comprehensive the expected-frequency lookup should be (just the user's portfolio tickers? All common ETFs?)
   - Recommendation: Start with a hardcoded dict of the user's portfolio tickers from `FinGuruConfig.load_layers()` (Layer 1 and Layer 2 tickers). Generic tickers get a simpler "no dividends found" warning without frequency comparison.

3. **DRIP Default Behavior**
   - What we know: Success criteria #3 says "DRIP mode shows growing share count"
   - What's unclear: Should DRIP be the default, or require a `--drip` flag?
   - Recommendation: Make DRIP the default (most users want total return including reinvestment). Add `--no-drip` flag to show simple total return without reinvestment. This matches how institutional tools like Morningstar default to DRIP.

## Sources

### Primary (HIGH confidence)
- Existing codebase: `src/analysis/risk_metrics_cli.py`, `src/analysis/correlation_cli.py`, `src/utils/market_data.py` -- verified 3-layer pattern, multi-ticker pattern, yfinance integration
- Existing codebase: `src/models/risk_inputs.py` -- verified Pydantic model pattern with validators
- Existing codebase: `src/CLAUDE.md` -- authoritative architecture guide for this project
- yfinance API: `ranaroussi.github.io/yfinance/reference/` -- Ticker.history(), Ticker.dividends, Ticker.actions confirmed
- [yfinance PyPI](https://pypi.org/project/yfinance/) -- version 1.0/1.1 release confirmed, no breaking changes
- [yfinance Release 1.0](https://github.com/ranaroussi/yfinance/releases/tag/1.0) -- confirmed no breaking changes, new config class

### Secondary (MEDIUM confidence)
- [Charles Schwab DRIP Guide](https://www.schwab.com/learn/story/how-dividend-reinvestment-plan-works) -- DRIP methodology: reinvest at payment date, fractional shares
- [DRIPCalc](https://www.dripcalc.com/) -- DRIP calculation methodology verified against institutional standard
- [DQYDJ Total Return Calculator](https://dqydj.com/stock-return-calculator/) -- Total return = price return + dividend return decomposition
- [yfinance GitHub Issue #930](https://github.com/ranaroussi/yfinance/issues/930) -- Missing dividend data confirmed non-deterministic
- [yfinance GitHub Issue #984](https://github.com/ranaroussi/yfinance/issues/984) -- Dividend dates randomly missing confirmed
- [yfinance GitHub Issue #568](https://github.com/ranaroussi/yfinance/issues/568) -- Only ex-dividend date returned (no payment date)
- [yfinance GitHub Issue #307](https://github.com/ranaroussi/yfinance/issues/307) -- Inconsistent split adjustment of dividends

### Tertiary (LOW confidence)
- [Coding Finance Returns Tutorial](https://www.codingfinance.com/post/2018-04-03-calc-returns-py/) -- Python return calculation patterns (blog post, cross-verified with pandas docs)
- [Analyzing Alpha yfinance Tutorial 2026](https://analyzingalpha.com/yfinance-python) -- yfinance usage patterns (tutorial site)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries already in project; no new dependencies
- Architecture: HIGH - Follows established 3-layer pattern across 8 existing tools; multi-ticker pattern from correlation_cli.py
- DRIP calculation: HIGH - Standard financial calculation, well-documented methodology from institutional sources
- yfinance dividend API: HIGH - Verified against official docs and existing codebase usage
- Dividend data quality issues: HIGH - Multiple GitHub issues confirm intermittent missing data; mitigation strategy defined
- Phase 6 dependency: MEDIUM - Model shapes recommended but Phase 6 not yet planned; exact field names may differ

**Research date:** 2026-02-02
**Valid until:** 2026-03-02 (stable domain -- yfinance dividend API unchanged; financial calculations are timeless)
