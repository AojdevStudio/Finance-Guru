# Domain Pitfalls

**Domain:** Private-to-public financial CLI system + options hedging tools + interactive knowledge explorer
**Researched:** 2026-02-02
**Overall confidence:** HIGH (codebase inspection) / MEDIUM (web research verified with multiple sources)

---

## Critical Pitfalls

Mistakes that cause data exposure, incorrect financial calculations, or system rewrites.

---

### Pitfall 1: Private Financial Data Leaking into Git History

**Severity:** CRITICAL
**Milestone:** M1 (Onboarding/Public Release)

**What goes wrong:** The repo currently contains `fin-guru/data/user-profile.yaml` with real financial data ($243K brokerage value, $551K net worth, margin strategies, specific holdings like PLTR at $67K). Even though `.gitignore` covers this file now, if it was EVER committed before the gitignore entry existed, the data persists in git history forever. Simply adding a gitignore entry does not remove data from prior commits. Git history is immutable -- a `git clone` followed by `git log --all -p` exposes everything ever committed.

**Why it happens:** Developers add gitignore rules retroactively and assume the problem is solved. GitHub's 2024 report found 23.8 million secrets leaked on public repos, with 70% of secrets leaked in 2022 still active in 2024 (GitGuardian State of Secrets Sprawl 2025).

**Warning signs:**
- Running `git log --all -p -- fin-guru/data/user-profile.yaml` returns content
- Running `git log --all -p -- .mcp.json` returns API keys
- Any file currently in `.gitignore` that was committed before the rule was added
- `Balances_for_Account_{account_id}.csv` pattern in hook code reveals real account numbers

**Prevention:**
1. Before making the repo public, run `git filter-repo` or BFG Repo Cleaner to scrub ALL sensitive files from ALL history
2. Audit every commit with: `git log --all --diff-filter=A --name-only` to find all files ever added
3. After scrubbing, force-push to create clean history (this is a one-way operation)
4. Run a secrets scanner (gitleaks, truffleHog) on the ENTIRE repo history, not just HEAD
5. Rotate any API keys that were ever committed -- they are compromised regardless of scrubbing

**Detection:** Run `gitleaks detect --source . --verbose` against full history before any public release. Also search for: account numbers ({account_id}), dollar amounts from user-profile.yaml, Google Sheets spreadsheet IDs, personal names.

**Consequence of failure:** Personal financial data, brokerage account numbers, portfolio positions, and investment strategies exposed publicly. Cannot be undone once repo is cloned by anyone.

---

### Pitfall 2: Hardcoded Personal References Beyond the Owner's Name

**Severity:** CRITICAL
**Milestone:** M1 (Onboarding/Public Release)

**What goes wrong:** The existing `test_no_hardcoded_references.py` only searches for the owner's name but the codebase contains far more personal data that would identify the owner. The hook `load-fin-core-config.ts` hardcodes `Balances_for_Account_{account_id}.csv` (real Fidelity account number). The `user-profile.yaml` contains Google Sheets spreadsheet IDs, LLC names ("{llc_name}", "{llc_name}"), specific employer names ("{employer_name}", "CBN"), and Bitcoin holdings details.

**Why it happens:** Teams search for obvious markers (name) but miss indirect PII: account numbers, employer names, business entity names, dollar amounts that fingerprint the individual, spreadsheet URLs that are publicly accessible.

**Warning signs:**
- The grep for personal name patterns returns 18 files in current codebase
- Hook code references specific account number patterns
- Agent markdown files reference personal meeting notes
- `setup.sh` hardcodes skill names tied to personal workflows (e.g., "PortfolioSyncing", "retirement-syncing")

**Prevention:**
1. Expand the hardcoded references test to search for: account numbers, LLC names, employer names, email patterns, spreadsheet IDs, dollar amounts matching the real profile
2. Create a `SCRUB_PATTERNS.txt` file listing all strings that must not appear in public code
3. Add a pre-commit hook that blocks commits containing any scrub pattern
4. Audit `.claude/hooks/load-fin-core-config.ts` line 178 (`Balances_for_Account_{account_id}`) -- this must be parameterized
5. Review ALL `.dev/meeting-notes/` and `.dev/specs/` files for personal details before making public

**Detection:** grep -r for patterns: `Z0\d+`, `LLC`, `{employer_name}`, `CBN`, `{llc_name}`, specific dollar amounts from user-profile.yaml.

---

### Pitfall 3: SQQQ Modeling Treats -3x as Simple Multiplication

**Severity:** CRITICAL
**Milestone:** M2 (Hedging)

**What goes wrong:** Developers model SQQQ returns as `underlying_return * -3` over multi-day periods. This is fundamentally wrong. SQQQ is a *daily-rebalanced* -3x ETF. Over any period longer than one day, the actual return diverges from -3x due to volatility drag (also called "path dependency" or "beta slippage"). In a sideways market, SQQQ loses value even if the underlying is flat. In a trending down market, SQQQ can return MORE than -3x. The 30-day modeling period in the hedging spec makes this error extremely consequential.

**Why it happens:** The -3x label is misleading. Most developers (and many investors) assume SQQQ will return -3x of QQQ's 30-day return. Academic research (Wang 2025, SSRN 5119860) confirms that while deviations can be modest for short periods, they become significant under high volatility -- precisely the scenario where hedging matters most.

**Warning signs:**
- `hedge_comparison.py` uses a simple multiplier without day-by-day simulation
- No volatility drag calculation or compounding simulation in the model
- Comparison table shows symmetric P&L between SQQQ and puts for identical scenarios
- Test cases pass with simple multiplication but diverge from real SQQQ returns by 5-20% over 30 days

**Prevention:**
1. Model SQQQ returns with daily-step simulation: each day, calculate `daily_return = underlying_daily_return * -3`, then compound: `cumulative = product(1 + daily_returns) - 1`
2. For scenario analysis, use Monte Carlo paths with the specified total drawdown distributed across the holding period using realistic daily volatility
3. Include volatility drag estimate: `drag ~= leverage^2 * variance * time` (from leveraged ETF prospectus math)
4. Add educational output explaining why the realized return differs from `-3 * underlying_return`
5. Validate against historical data: compare modeled vs actual SQQQ returns for known periods
6. Include the ProShares prospectus return table as a reference validation target

**Detection:** Compare `SQQQ_modeled_return` vs `actual_SQQQ_return` for any historical 30-day period. If they match within 0.5%, the model is likely using simple multiplication. Real divergence should be 2-15% depending on volatility.

---

### Pitfall 4: Black-Scholes Applied to American-Style Options Without Adjustment

**Severity:** CRITICAL
**Milestone:** M2 (Hedging)

**What goes wrong:** The existing `options.py` uses Black-Scholes (designed for European options) to price American-style options (which is what QQQ and SPY options are). For puts specifically, early exercise can have meaningful value, especially for deep ITM puts or near expiration. The hedging spec's rolling strategy targets 10-20% OTM puts at 30 DTE -- at this range the error is moderate but non-trivial. More importantly, if a user holds puts that move deep ITM during a crash, the Black-Scholes valuation will understate the option's value.

**Why it happens:** Black-Scholes is the "default" model taught everywhere. Most Python options libraries implement it. The error is small enough for ATM/OTM calls that it goes unnoticed, but widens for puts (especially ITM puts and dividend-paying underlyings like SPY).

**Warning signs:**
- `options.py` has a single `price_option()` function with no early exercise adjustment
- Greeks calculated are European-style Greeks
- No mention of binomial tree or Barone-Adesi-Whaley approximation anywhere in codebase
- Put valuations systematically understate market prices for ITM puts

**Prevention:**
1. For the 10-20% OTM puts in the hedging strategy, Black-Scholes error is typically <5% -- document this limitation prominently in CLI output
2. Add a disclaimer: "Greeks calculated using Black-Scholes (European model). American-style options may differ, especially for ITM puts."
3. For hedge comparison scenarios where puts go deep ITM (the -20% and -40% scenarios), apply Bjerksund-Stensland or Barone-Adesi-Whaley approximation
4. At minimum, add intrinsic value floor: `american_put_value = max(BS_value, max(strike - spot, 0))`
5. Long-term: implement binomial tree pricer for American options (already referenced in codebase research as `amoszczynski/American-Option-Pricing` on GitHub)

**Detection:** Compare `price_option()` output vs actual market mid-price for SPY puts at various strikes. Systematic underpricing of ITM puts indicates missing early exercise premium.

---

### Pitfall 5: Financial Calculator Output Used for Real Investment Decisions

**Severity:** CRITICAL
**Milestone:** M2 (Hedging)

**What goes wrong:** The hedge sizer, rolling tracker, and total return calculator will produce numbers that users treat as actionable. A rounding error, timezone issue, or stale cache in market data can cause a hedge sizer to recommend 3 contracts instead of 6, or a total return calculator to show -15% when the real return is +5% (because dividends were missed). Unlike a game or dashboard, errors in financial calculators directly affect money.

**Why it happens:** Financial software has an implicit trust contract. When a tool says "buy 4 contracts of QQQ $480 put," the user acts on it. The standard disclaimer ("not investment advice") provides legal cover but does not prevent real losses.

**Warning signs:**
- No validation layer comparing tool output against a known reference
- Edge case tests missing: zero dividends, stock splits during period, ex-dividend dates, options on expiration day
- Market data fetched once and cached without staleness checks
- No rounding-mode specification (financial calculations typically require `ROUND_HALF_UP`, Python default is `ROUND_HALF_EVEN`)

**Prevention:**
1. Every financial calculator must have a "known answer" test: pick a specific historical period with a known outcome and verify the tool reproduces it
2. Add data freshness indicators: "Prices as of: 2026-02-02 16:00 EST (15 minutes delayed)"
3. Show confidence bands, not single numbers: "Estimated monthly cost: $480-$620" rather than "$550"
4. For position sizing, always round DOWN (conservative): `math.floor()` not `round()`
5. Include sanity checks: if hedge cost exceeds budget by 50%+, warn loudly
6. Add a `--dry-run` flag that shows what would be recommended without executing
7. Test edge cases: market closed (stale prices), stock split date, ex-dividend date, options expiration day, zero-volume options

**Detection:** Run the same calculation with the tool and manually in a spreadsheet. If results differ by more than 1%, investigate.

---

## High Pitfalls

Mistakes that cause significant rework, user frustration, or degraded functionality.

---

### Pitfall 6: yfinance Dividend Data Gaps and Adjusted Close Errors

**Severity:** HIGH
**Milestone:** M2 (Hedging -- Total Return Calculator)

**What goes wrong:** yfinance has well-documented issues with dividend data: intermittent missing dividends (GitHub issue #930), incorrect dividend-adjusted prices for weekly/monthly intervals (issue #1273), and Adjusted Close values that don't match Yahoo Finance's own total return calculations (issue #2070). Building a "total return" calculator on unreliable dividend data produces misleading results -- the exact opposite of what the tool promises.

**Why it happens:** yfinance scrapes Yahoo Finance, which itself has data quality issues. Yahoo's dividend adjustment algorithm has known bugs for non-daily intervals. Special dividends, return-of-capital distributions, and foreign withholding taxes are frequently miscategorized or missing.

**Warning signs:**
- Total return for a high-yield fund (e.g., YMAX, MSTY) shows negative when it should be positive
- Dividend history has gaps (months with no dividends for a monthly-paying fund)
- `Adj Close` values change between API calls (Yahoo recalculates retroactively)
- Results differ between `yf.download()` and `yf.Ticker().history()`

**Prevention:**
1. Never trust yfinance dividend data blindly -- cross-validate against a second source (e.g., the fund's own distribution history page)
2. Add a data quality indicator to total return output: "Dividends found: 8 of expected 12 for monthly payer -- DATA MAY BE INCOMPLETE"
3. For high-conviction accuracy, allow users to supply their own dividend CSV as override
4. Use daily intervals only when fetching adjusted prices (weekly/monthly adjustment is known-broken)
5. Cache dividend history and flag when it changes between fetches
6. Add specific tests for known high-yield ETFs: JEPI, JEPQ, YMAX, MSTY -- compare against published distribution schedules
7. Document the limitation: "Dividend data sourced from Yahoo Finance via yfinance. Special distributions and return-of-capital classifications may be inaccurate."

**Detection:** For any ticker with known dividends, compare `ticker.dividends` count against the fund's published distribution schedule. If counts differ, data is unreliable.

---

### Pitfall 7: setup.sh Fails on Fresh Machine Due to Undeclared Dependencies

**Severity:** HIGH
**Milestone:** M1 (Onboarding/Public Release)

**What goes wrong:** The current `setup.sh` assumes `uv`, `bun`, and `mcpl` are installed, and gracefully warns if missing. But the onboarding flow in Step 10 calls `bun run scripts/onboarding/index.ts` -- if Bun is not installed, setup crashes. The script also symlinks to `~/.claude/commands` and `~/.claude/skills` which may not exist on machines without Claude Code. The hook directory contains a mix of `.sh`, `.ts`, and `.cjs` files requiring different runtimes.

**Why it happens:** Single-user tools never encounter "fresh machine" scenarios. The developer's machine always has everything installed. The setup script was written incrementally as new tools were added, never tested from a cold start.

**Warning signs:**
- `setup.sh` has no `set -euo pipefail` after the initial `set -e` (missing undefined variable checking)
- No check for minimum Python version (3.12+ required)
- `.claude/hooks/` contains `.sh`, `.ts`, and `.cjs` files -- three different runtimes required
- `package.json` and `package-lock.json` in hooks directory, but `node_modules` is gitignored (needs `npm install` or `bun install` first)
- No verification step that installed hooks actually execute

**Prevention:**
1. Add dependency checks at the TOP of setup.sh before any work: `python3 --version`, `uv --version`, `bun --version`
2. Fail fast with clear instructions: "Python 3.12+ required, found 3.9. Install: ..."
3. Add a `--check-deps-only` flag to verify prerequisites without installing
4. Make hooks runtime consistent: decide on Bun-only and migrate all `.sh` and `.cjs` files
5. Add a post-setup verification: run each hook with a test input and verify exit code 0
6. Test on CI with a bare Docker image: `FROM python:3.12-slim` with nothing pre-installed
7. Pin minimum tool versions: `uv >= 0.4`, `bun >= 1.1`

**Detection:** Run `./setup.sh` in a fresh Docker container. If it fails or hangs, the script has undeclared dependencies.

---

### Pitfall 8: Canvas Knowledge Graph Broken on Mobile Safari

**Severity:** HIGH
**Milestone:** M3 (Explorer)

**What goes wrong:** HTML Canvas rendering has significant cross-browser issues, especially on mobile Safari (iOS). The "Fifty problems with standard web APIs in 2025" article documents that over half of development time was spent on cross-browser rework for a single-page HTML application. Specific issues include: touch event handling differs between Safari and Chrome (Safari uses `touchstart`/`touchmove`/`touchend` with different coordinate systems), `devicePixelRatio` handling on Retina displays, canvas context loss on iOS when backgrounding the app, and text rendering differences (font metrics, emoji rendering).

**Why it happens:** Developers test on desktop Chrome and assume mobile works. Canvas is a pixel-level API with no cross-browser abstraction layer (unlike DOM elements which browsers normalize). Touch events are standardized but implemented inconsistently across WebKit and Blink.

**Warning signs:**
- Graph works on desktop Chrome but nodes are mis-positioned or tiny on iPhone
- Touch-to-click mapping is offset (user taps node but adjacent node activates)
- Canvas appears blurry on Retina/HiDPI displays
- Graph state lost when user switches apps and returns on iOS
- Pinch-to-zoom zooms the entire page instead of the graph

**Prevention:**
1. Set canvas dimensions accounting for `devicePixelRatio`: `canvas.width = canvas.clientWidth * window.devicePixelRatio`
2. Use `pointer events` API instead of separate mouse/touch handlers -- broader browser support and unified coordinate system
3. Prevent default touch behaviors: `touch-action: none` on the canvas element
4. Handle canvas context loss with `webglcontextlost` / periodic context checks
5. Test on REAL iOS Safari (not iOS simulator) early -- Phase 1 Sprint 1, not Phase 4
6. Set minimum viewport: `<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">`
7. Consider using SVG instead of Canvas for the graph -- SVG handles text, accessibility, and touch natively

**Detection:** Open the prototype on an iPhone (any model). If touch targets are wrong, display is blurry, or scroll interferes with graph interaction, this pitfall has materialized.

---

### Pitfall 9: localStorage Persistence Creates False Confidence in Data Safety

**Severity:** HIGH
**Milestone:** M3 (Explorer)

**What goes wrong:** The explorer spec uses `localStorage` for persisting knowledge state. But localStorage has hard limits (5-10MB per origin depending on browser), can be cleared by the browser without notice (especially on mobile Safari in "private" or when storage is under pressure), and does not work in incognito/private browsing. Users complete a 20-minute self-assessment, close the browser, return the next day, and their progress is gone.

**Why it happens:** localStorage appears reliable on desktop browsers in normal mode. The failure modes are all on mobile: iOS Safari aggressively evicts localStorage under storage pressure, and some browsers clear it after 7 days of inactivity. The MDN Storage Quotas documentation confirms browsers manage stored data per-origin with eviction policies that vary by browser.

**Warning signs:**
- Assessment data disappears on mobile Safari after a few days
- Private/incognito browsing shows empty state
- No error message when localStorage write fails (it silently fails or throws a QuotaExceededError)
- User has two different knowledge states on phone vs desktop with no sync

**Prevention:**
1. Always wrap `localStorage.setItem()` in try/catch -- it throws `QuotaExceededError` when full
2. Show explicit save status: "Progress saved locally" with a timestamp
3. Add a "Download Progress" button that exports to JSON file (guaranteed persistence)
4. Warn users on private browsing: detect with `navigator.storage.estimate()` or try-catch on localStorage
5. Keep assessment data small (JSON with node IDs and status, not full graph data) -- under 10KB
6. Add a "Restore from file" option alongside localStorage auto-load
7. Display last-saved timestamp prominently so users know if data is current

**Detection:** Complete an assessment on iOS Safari, close ALL Safari tabs (not just the tab), wait 24 hours, reopen. If data is gone, localStorage eviction has occurred.

---

### Pitfall 10: Single-File HTML Becomes Unmaintainable Beyond 2000 Lines

**Severity:** HIGH
**Milestone:** M3 (Explorer)

**What goes wrong:** The spec calls for "single HTML file per topic (generated from JSON + template)" to maintain zero-dependency philosophy. The existing `dividend-strategy-explorer.html` prototype is likely already 1500+ lines. Adding touch support, accessibility, learning mode selector, Maya export, responsive layout, and preset filters will push it past 3000 lines. At this size, a single file becomes nearly impossible to debug, test, or modify without breaking something.

**Why it happens:** "Zero dependency" sounds elegant but conflicts with "maintainable." The file grows organically -- each feature adds 100-200 lines of JS, CSS, and HTML interleaved in a way that makes isolation impossible.

**Warning signs:**
- CSS rules conflict because everything shares one global scope
- JavaScript variables collide between the graph renderer, UI logic, and data management
- Bug fixes in one area break another (no modularity)
- No way to unit test any component in isolation
- Merge conflicts on every change because all code is in one file

**Prevention:**
1. Develop with separate files (`graph.js`, `ui.js`, `data.js`, `styles.css`, `template.html`) during development
2. Use the Bun build script to concatenate/bundle into a single distributable HTML file at build time
3. This gives you: modular development + zero-dependency distribution
4. Use CSS custom properties (variables) to namespace styles per component
5. Use JavaScript modules (IIFE pattern) to avoid global scope pollution
6. Set a hard line limit per source file: 500 lines max
7. The build pipeline is: `src/explorer/*.js + template.html + topic.json -> dist/explorer-{topic}.html`

**Detection:** If you cannot modify the graph rendering without checking whether it breaks the UI sidebar, the file is too monolithic.

---

## Moderate Pitfalls

Mistakes that cause delays, user confusion, or technical debt.

---

### Pitfall 11: Options Rolling Tracker Has No Concept of Market Hours

**Severity:** MEDIUM
**Milestone:** M2 (Hedging)

**What goes wrong:** The rolling tracker suggests rolls based on days-to-expiry. But options expire at specific times (typically 4:00 PM ET on expiration Friday, though some have AM settlement). If a user runs `suggest-roll` on Friday evening after market close, the tool may suggest rolling a position that has already expired. Worse, it may price replacement positions using after-hours data or stale Friday close data.

**Prevention:**
1. Add market hours awareness: distinguish between "trading days remaining" and "calendar days remaining"
2. Flag weekend/holiday runs: "Market is closed. Prices shown are from last close (Friday 4:00 PM ET)"
3. Use `pandas_market_calendars` or a hardcoded NYSE holiday list to calculate actual trading days
4. For expiration-day logic: if today IS expiration day and time > 16:00 ET, mark position as expired

---

### Pitfall 12: Hedge Comparison Ignores IV Expansion During Crashes

**Severity:** MEDIUM
**Milestone:** M2 (Hedging)

**What goes wrong:** The spec mentions "IV expansion estimate uses historical VIX correlation (simplified)" but this is where most of the put's hedge value comes from. During a -20% market drop, VIX typically spikes from 15 to 35+, roughly doubling IV. A put that was worth $3 at IV=20% might be worth $12 at IV=45%, independent of the strike/spot relationship. Ignoring IV expansion makes puts look worse than SQQQ in the comparison, which is the opposite of reality.

**Prevention:**
1. Model IV expansion as a function of market drop: `IV_new = IV_base * (1 + abs(drop_pct) * expansion_factor)` where expansion_factor is calibrated from historical VIX-SPX relationship (roughly 2-4x)
2. Use the VIX-to-SPX regression from historical data as the basis
3. Include IV expansion in the "notes" column of the comparison table
4. Show put value with and without IV expansion so users understand the impact
5. Add a `--vix` flag to set current VIX level for more accurate modeling

---

### Pitfall 13: Onboarding Asks Too Many Questions Before Delivering Value

**Severity:** MEDIUM
**Milestone:** M1 (Onboarding/Public Release)

**What goes wrong:** The onboarding spec describes a 15-20 minute comprehensive assessment with 8 sections. New users cloning an open-source repo expect to see value within 5 minutes. A 15-minute interrogation about personal finances before ANY tool works will cause abandonment. The spec even acknowledges "CLI-Only Onboarding (No Web UI)" as technical debt.

**Prevention:**
1. Make onboarding OPTIONAL for the public release: all CLI tools should work with zero config (they already use argparse defaults)
2. Provide a "quick start" path: `uv run python src/analysis/risk_metrics_cli.py TSLA` should work immediately
3. Only require onboarding for personalized features (hedge sizing from portfolio value, margin strategies)
4. Add sample data / demo mode: ship a `user-profile-demo.yaml` with fictional data so agents work out-of-the-box
5. Structure onboarding as "enhance, not gate": "Want personalized recommendations? Run setup.sh to configure your profile."

---

### Pitfall 14: MCP Server Configuration Creates Confusing Setup for Public Users

**Severity:** MEDIUM
**Milestone:** M1 (Onboarding/Public Release)

**What goes wrong:** The system requires 6 MCP servers (exa, bright-data, sequential-thinking, financial-datasets, gdrive, web-search). Public users cloning this repo likely use Claude Code but may not have ANY of these configured. If the setup creates an MCP.json template with servers the user cannot connect to, Claude Code sessions will be littered with MCP connection errors.

**Prevention:**
1. Make ALL MCP servers optional -- document which features require which servers
2. Do NOT create `.mcp.json` by default -- let users opt-in
3. In CLAUDE.md, list MCP servers as "enhances" not "requires"
4. If a CLI tool needs market data, use yfinance (no MCP required) as the primary source
5. Add a `--mcp-check` flag to setup.sh that tests which servers are available

---

### Pitfall 15: Canvas-Based Explorer is Inaccessible to Screen Readers

**Severity:** MEDIUM
**Milestone:** M3 (Explorer)

**What goes wrong:** HTML Canvas content is invisible to screen readers and keyboard navigation. The knowledge explorer as designed (canvas-rendered node graph with click-to-cycle interaction) will be completely unusable for visually impaired users. This is not just an ethics issue -- it may violate accessibility laws depending on distribution context (e.g., educational institution use).

**Prevention:**
1. Add a parallel text-based representation of the graph as `aria-label` content or hidden DOM elements
2. Make nodes keyboard-focusable with `tabindex` on invisible overlay elements positioned over canvas nodes
3. Announce state changes: when a node status changes to "know," announce it via `aria-live` region
4. Provide an alternative "list view" mode (pure HTML/CSS) for accessibility
5. Add `role="img"` and `aria-label` to the canvas element describing the graph at a high level
6. Test with VoiceOver (macOS/iOS) before Phase 2

---

### Pitfall 16: Pre-commit Hook Missing for Secrets in Public Release

**Severity:** MEDIUM
**Milestone:** M1 (Onboarding/Public Release)

**What goes wrong:** The gitignore rules prevent TRACKED files from being committed, but new sensitive files (e.g., a user creates `my-portfolio.csv` in the root) will not be caught. The onboarding spec mentions a pre-commit hook as "optional future enhancement" but this is needed for a public repo where users WILL accidentally try to commit sensitive data.

**Prevention:**
1. Ship a pre-commit hook that scans for: API key patterns, dollar amounts over $1000, account numbers, SSN patterns, and files matching `*.csv` outside of test directories
2. Use `pre-commit` framework with `detect-secrets` or `gitleaks` as a hook
3. Add to setup.sh: `pre-commit install` if the framework is available
4. At minimum, add a `.gitattributes` with diff filters that warn about common sensitive patterns

---

## Minor Pitfalls

Mistakes that cause annoyance but are fixable without major rework.

---

### Pitfall 17: Timezone Mismatches in Financial Data Timestamps

**Severity:** LOW
**Milestone:** M2 (Hedging)

**What goes wrong:** yfinance returns timestamps in various timezones depending on the exchange. US market data comes in US/Eastern, but `date.today()` returns the local date. A user in UTC+10 running the rolling tracker at 8 AM their time (still previous trading day in US) gets stale data or incorrect days-to-expiry calculations.

**Prevention:**
1. Always convert market timestamps to US/Eastern for US equities/options
2. Use `pytz` or `zoneinfo` (stdlib in 3.9+) for timezone-aware datetime operations
3. Display the effective market date in all output: "Market date: 2026-02-02 (US/Eastern)"

---

### Pitfall 18: Python sys.path Manipulation in CLI Scripts

**Severity:** LOW
**Milestone:** M2 (Hedging)

**What goes wrong:** Every CLI file (e.g., `options_chain_cli.py` line 53-54) manually inserts the project root into `sys.path`. This is fragile -- it breaks if the file is moved, if the project structure changes, or if there are naming conflicts. It also makes imports non-standard, confusing for contributors.

**Prevention:**
1. Configure `pyproject.toml` with proper package structure so `uv run` resolves imports automatically
2. Use `uv run python -m src.analysis.options_chain_cli` instead of direct script execution
3. Or add `src` as a package with `__init__.py` and install in development mode: `uv pip install -e .`

---

### Pitfall 19: Topic JSON Schema Drift Between Explorer Versions

**Severity:** LOW
**Milestone:** M3 (Explorer)

**What goes wrong:** The spec defines a topic JSON schema, but without validation, the schema evolves as features are added. Topic files created in Phase 1 may not work with the template engine modified in Phase 3. The `maya_teaching_level` field, `presets` object, and `prompt_template` structure are all likely to change.

**Prevention:**
1. Create a JSON Schema file (`topic-schema.json`) and validate all topic files against it in CI
2. Version the schema: include `"schema_version": "1.0"` in every topic file
3. Add migration scripts when schema changes
4. Validate topic files in the build pipeline before generating HTML

---

## Phase-Specific Warnings

| Milestone | Phase | Likely Pitfall | Severity | Mitigation |
|-----------|-------|---------------|----------|------------|
| M1 | Pre-public scrub | Git history contains financial PII (Pitfall 1) | CRITICAL | Run git filter-repo BEFORE making public, rotate all exposed keys |
| M1 | Hardcoded refs | Account numbers and LLC names not caught by existing tests (Pitfall 2) | CRITICAL | Expand scrub patterns beyond just the owner's name |
| M1 | Setup.sh | Script fails on machines without Bun or older Python (Pitfall 7) | HIGH | Test in bare Docker container, add version checks |
| M1 | Onboarding | 15-min questionnaire causes abandonment for open-source users (Pitfall 13) | MEDIUM | Make onboarding optional, tools work without it |
| M1 | MCP config | MCP.json created with servers user cannot connect to (Pitfall 14) | MEDIUM | Make MCP optional, use yfinance as primary data source |
| M1 | Pre-commit | No automated block for accidental secret commits (Pitfall 16) | MEDIUM | Ship pre-commit hook with secrets detection |
| M2 | SQQQ modeling | Simple -3x multiplication instead of daily compounding (Pitfall 3) | CRITICAL | Day-by-day simulation with volatility drag |
| M2 | Options pricing | Black-Scholes on American options without adjustment (Pitfall 4) | CRITICAL | Document limitation, add intrinsic value floor |
| M2 | Accuracy | Financial output treated as actionable without validation (Pitfall 5) | CRITICAL | Known-answer tests, confidence bands, freshness indicators |
| M2 | Dividends | yfinance dividend data gaps corrupt total return (Pitfall 6) | HIGH | Cross-validate, allow user-supplied CSV override |
| M2 | Rolling tracker | No market hours awareness (Pitfall 11) | MEDIUM | Add NYSE calendar, flag after-hours runs |
| M2 | Comparison | IV expansion ignored makes puts look worse than SQQQ (Pitfall 12) | MEDIUM | Model VIX-SPX relationship for IV adjustment |
| M2 | Timestamps | Timezone mismatches in market data (Pitfall 17) | LOW | Convert all timestamps to US/Eastern |
| M2 | Imports | sys.path manipulation is fragile (Pitfall 18) | LOW | Proper package configuration in pyproject.toml |
| M3 | Mobile | Canvas broken on iOS Safari (Pitfall 8) | HIGH | Test on real iPhone in Phase 1, use pointer events |
| M3 | Persistence | localStorage evicted without warning (Pitfall 9) | HIGH | Add JSON export/import, wrap in try/catch |
| M3 | Architecture | Single HTML file unmaintainable beyond 2000 lines (Pitfall 10) | HIGH | Develop modular, bundle to single file at build |
| M3 | Accessibility | Canvas invisible to screen readers (Pitfall 15) | MEDIUM | Add ARIA labels, keyboard navigation, list view fallback |
| M3 | Schema | Topic JSON drifts without validation (Pitfall 19) | LOW | JSON Schema validation in build pipeline |

---

## Sources

### Codebase Inspection (HIGH confidence)
- `/Users/ossieirondi/Documents/Irondi-Household/family-office/fin-guru/data/user-profile.yaml` -- Contains real financial data (PII)
- `/Users/ossieirondi/Documents/Irondi-Household/family-office/.claude/hooks/load-fin-core-config.ts` -- Hardcoded account number on line 178
- `/Users/ossieirondi/Documents/Irondi-Household/family-office/.gitignore` -- Current protection rules
- `/Users/ossieirondi/Documents/Irondi-Household/family-office/tests/python/test_no_hardcoded_references.py` -- Only checks for the owner's name
- `/Users/ossieirondi/Documents/Irondi-Household/family-office/src/analysis/options_chain_cli.py` -- Black-Scholes pricing without American option adjustment
- `/Users/ossieirondi/Documents/Irondi-Household/family-office/.claude/hooks/` -- Mixed runtimes: .sh, .ts, .cjs files

### External Research (MEDIUM confidence, multiple sources agree)
- GitGuardian State of Secrets Sprawl 2025: 23.8M secrets leaked on public GitHub, 70% from 2022 still active
- GitHub Docs: Remediating leaked secrets -- confirms git history persistence
- yfinance GitHub issues #930, #1273, #2070 -- documented dividend data reliability problems
- SSRN 5119860 (Wang 2025): Multi-day return properties of leveraged ETFs -- confirms path dependency
- Seeking Alpha (Piard 2025): SQQQ risks -- confirms decay and path dependency for leveraged inverse ETFs
- Quant StackExchange: Mathematical solution to leveraged ETF decay -- confirms volatility drag formula
- "Fifty problems with standard web APIs in 2025" (zerotrickpony.com): >50% rework time for cross-browser HTML5
- MDN Storage Quotas documentation: localStorage limits and eviction criteria per browser
- WHATWG Storage Standard: Persistent vs. best-effort storage buckets
