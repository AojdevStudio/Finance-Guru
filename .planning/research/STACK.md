# Technology Stack

**Project:** Finance Guru v3 (Public Release, Hedging CLIs, Knowledge Explorer)
**Researched:** 2026-02-02
**Overall Confidence:** HIGH

---

## Existing Stack (Baseline)

These are already installed and battle-tested. New work MUST integrate with them, not replace them.

| Technology | Current Version | Purpose | Status |
|---|---|---|---|
| Python | >=3.12 | Runtime | Locked |
| uv | latest | Package manager | Locked |
| Pydantic | >=2.10.6 | 3-layer architecture Layer 1 (models) | Locked |
| pandas | >=2.3.2 | Data manipulation | Locked |
| numpy | >=2.3.3 | Numerical computing | Locked |
| scipy | >=1.16.2 | Statistical functions, norm.cdf for Black-Scholes | Locked |
| yfinance | >=0.2.66 | Market data (options chains, dividends, prices) | Locked |
| argparse | stdlib | CLI argument parsing (all 8 existing CLIs) | Locked |
| pytest | >=9.0.2 | Testing (365+ tests) | Locked |
| Bun | latest | TypeScript hooks runner (.claude/hooks/) | Locked |
| Textual | >=6.6.0 | TUI framework (already a dependency) | Locked |
| PyYAML | >=6.0.3 | YAML generation | Locked |
| python-dotenv | >=1.1.1 | Environment variable loading | Locked |

**Critical constraint:** The 3-layer architecture (Pydantic Models -> Calculator Classes -> CLI) is non-negotiable. All new tools follow this pattern.

---

## M1: Public Release (Onboarding CLI + Setup Automation)

### Decision: Keep argparse + questionary for interactive prompts

**Existing state:** There is ALREADY a TypeScript/Bun onboarding wizard (`scripts/onboarding/index.ts`) and a Python progress persistence module (`src/utils/progress_persistence.py`) with Pydantic state models. The M1 work is about creating a PUBLIC-facing Python CLI that replaces the private TypeScript version.

### New Dependencies Needed

| Library | Version | Purpose | Confidence | Why This One |
|---|---|---|---|---|
| questionary | >=2.1.1 | Interactive CLI prompts (select, checkbox, confirm, text) | HIGH | Most popular Python prompt library. 2.1.1 released Aug 2025. MIT license. Built on prompt_toolkit. Supports async via `.ask_async()`. Python >=3.9. |

**Source:** PyPI (https://pypi.org/project/questionary/) -- verified 2.1.1 is latest as of Feb 2026.

### What NOT to Add

| Library | Why Not |
|---|---|
| InquirerPy 0.3.4 | Last release was 0.3.4 (stale since 2022). 444 GitHub stars vs questionary's much larger adoption. Functionally equivalent but less maintained. |
| rich (for prompts) | Already a transitive dependency via Textual, but rich.prompt is too basic for multi-step wizards. No select/checkbox. Use it for OUTPUT formatting only, not input collection. |
| Textual (for onboarding) | Overkill. Textual (v7.4.0, Jan 2026) is a full TUI framework. Onboarding needs simple sequential prompts, not a persistent UI app. Textual is already in deps for future dashboard use -- do not use it for the onboarding wizard. |
| click | Would require rewriting ALL existing CLIs. The project is standardized on argparse. Click adds decorator-based syntax that conflicts with the existing pattern. |
| typer | Same problem as click (built on click). Would fragment the CLI approach. |
| inquirer (python-inquirer 3.4.1) | Uses blessed/curses under the hood. Heavier than questionary. Less Pythonic API. |

### Integration Pattern

```
Existing argparse CLI pattern (kept):
    argparse handles: ticker args, --flags, --output json

New questionary layer (added for onboarding only):
    questionary handles: interactive prompts during wizard flow

Existing persistence (reused):
    src/utils/progress_persistence.py -> OnboardingState (Pydantic)
    .onboarding-state.json -> progress file
```

**Architecture for onboarding CLI:**
```
src/models/onboarding_inputs.py      <- Layer 1: Pydantic models (EXTEND existing)
src/utils/onboarding_wizard.py       <- Layer 2: Wizard logic + questionary prompts
src/utils/onboarding_cli.py          <- Layer 3: argparse entry point
src/utils/progress_persistence.py    <- REUSE existing module
```

### Setup Automation

No new dependencies needed. Use:
- `subprocess` (stdlib) for running `uv sync`, `bun install`, etc.
- `shutil` (stdlib) for file copying
- `os` / `pathlib` (stdlib) for environment detection
- `PyYAML` (already installed) for config generation
- `python-dotenv` (already installed) for .env template creation

The `setup.sh` bootstrap script uses only bash -- no Python dependencies required at that stage since it runs BEFORE `uv sync`.

### Installation Command

```bash
uv add questionary
```

One dependency. That is it.

---

## M2: Hedging CLI Tools (4 New CLIs)

### Decision: ZERO new dependencies

The existing stack already has everything needed for options hedging analysis:

| Capability | Existing Library | How It's Used |
|---|---|---|
| Black-Scholes pricing + Greeks | scipy (norm.cdf/pdf) | Already implemented in `src/analysis/options.py` -- `OptionsCalculator` class |
| Options chain data | yfinance | Already used in `src/analysis/options_chain_cli.py` -- `ticker.option_chain()` |
| Dividend data | yfinance | `ticker.dividends` returns dividend history |
| Total return calculation | pandas + numpy | Standard returns math, already used in risk_metrics.py |
| Pydantic models for options | pydantic | Already have `GreeksOutput`, `OptionContractData`, `OptionsChainOutput` in `src/models/options_inputs.py` |
| CLI framework | argparse | Standard pattern across all 8 existing tools |
| Numerical optimization | scipy.optimize | Already available for hedge ratio optimization |
| Statistical analysis | scipy.stats | Already used for normal distribution in Black-Scholes |

### What NOT to Add

| Library | Why Not |
|---|---|
| QuantLib | Massive C++ library with complex build requirements. Our Black-Scholes implementation in `src/analysis/options.py` already handles pricing and Greeks. QuantLib adds ~100MB and complicates `uv sync` for public users. Only justified if we needed exotic option pricing (American, Asian, barrier), which we do not. |
| py_vollib | Another implied vol library. We already have Newton-Raphson IV solver in `OptionsCalculator.calculate_implied_vol()`. |
| mibian | Abandoned. Last PyPI release 2018. |
| pyfolio | Quantopian is defunct. pyfolio is poorly maintained. We already have risk metrics, Sharpe, drawdown calculations. |
| QuantStats | Overlaps heavily with our existing `RiskCalculator`. Adding it creates confusion about which to use. |

### Four New CLIs (All Follow Existing 3-Layer Pattern)

**1. Rolling Hedge Tracker** (`src/strategies/hedge_tracker_cli.py`)
```
Models:  src/models/hedge_inputs.py         <- HedgePosition, RollSchedule, HedgeTrackingOutput
Calc:    src/strategies/hedge_tracker.py     <- HedgeTracker class (delta calc, roll detection, PnL)
CLI:     src/strategies/hedge_tracker_cli.py <- argparse, --ticker, --hedge-type, --days
```
Uses: yfinance (options chain), scipy.stats.norm (delta), pandas (time series), existing OptionsCalculator

**2. Hedge Sizer** (`src/strategies/hedge_sizer_cli.py`)
```
Models:  src/models/hedge_inputs.py         <- HedgeSizeInput, HedgeSizeOutput (SHARED with tracker)
Calc:    src/strategies/hedge_sizer.py       <- HedgeSizer class (position sizing, notional, contracts)
CLI:     src/strategies/hedge_sizer_cli.py   <- argparse, --portfolio-value, --hedge-pct, --ticker
```
Uses: existing OptionsCalculator.price_option(), yfinance for spot + chain, numpy for sizing math

**3. SQQQ vs Puts Comparison** (`src/strategies/hedge_comparison_cli.py`)
```
Models:  src/models/hedge_inputs.py         <- HedgeComparisonInput, HedgeComparisonOutput
Calc:    src/strategies/hedge_comparison.py  <- HedgeComparison class (SQQQ total return vs put payoff)
CLI:     src/strategies/hedge_comparison_cli.py <- argparse, --notional, --days, --scenario
```
Uses: yfinance (SQQQ price + dividends, QQQ options chain), existing OptionsCalculator, pandas for return calc

**4. Total Return Calculator** (`src/analysis/total_return_cli.py`)
```
Models:  src/models/total_return_inputs.py   <- TotalReturnInput, TotalReturnOutput
Calc:    src/analysis/total_return.py        <- TotalReturnCalculator (price + dividends + distributions)
CLI:     src/analysis/total_return_cli.py    <- argparse, --ticker, --start-date, --include-dividends
```
Uses: yfinance (history + dividends), pandas (return calculation), numpy (annualization)

### Installation Command

```bash
# Nothing. Zero new dependencies.
```

**Confidence: HIGH** -- I verified every capability exists in the current `pyproject.toml` dependencies by cross-referencing with the actual source code in `src/analysis/options.py` and `src/models/options_inputs.py`.

---

## M3: Interactive Knowledge Explorer (Single-File HTML)

### Decision: Cytoscape.js via CDN, with offline inline fallback

This is a TEMPLATE-BASED system. Python generates single-file `.html` files by injecting data into an HTML template. The HTML files use JavaScript for interactive visualization. No npm, no build tools, no bundling pipeline.

### JavaScript Libraries (CDN, not installed via npm)

| Library | Version | CDN Size (min) | Purpose | Confidence | Why This One |
|---|---|---|---|---|---|
| Cytoscape.js | >=3.33.0 | ~300KB | Force-directed graph layout, interactive node exploration, Canvas/WebGL rendering | HIGH | Best balance of features, docs, and performance. WebGL renderer (preview since v3.31.0, Jan 2025) handles thousands of nodes. First-party TypeScript support since 3.31. No external dependencies. MIT license. Proven in bioinformatics (large graphs). |

**Source:** Cytoscape.js blog (https://blog.js.cytoscape.org/) -- verified 3.33.0 released July 2025, WebGL renderer available.
**CDN:** `https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.33.0/cytoscape.min.js`

### What NOT to Use

| Library | Why Not |
|---|---|
| D3.js (d3-force) | Maximum flexibility but minimum out-of-the-box functionality. You write EVERYTHING from scratch: hit testing, zoom controls, node selection, styling. For a template-based system where the template must work generically, D3 is too low-level. Better for bespoke, one-off visualizations. |
| vis-network 10.0.2 | Performance degrades significantly at 1000+ nodes (Memgraph benchmarks confirm order-of-magnitude slower than WebGL approaches). Physics simulation blocks main thread with no web worker support. Tight coupling makes customization difficult. Fine for small graphs but the knowledge explorer needs to handle arbitrary sizes. |
| Sigma.js 3.0.2 | Best raw WebGL performance, but requires graphology as a separate dependency (two CDN loads). Documentation is sparse compared to Cytoscape.js. Smaller community. No built-in layout algorithms -- you must add ForceAtlas2 separately. Too many moving parts for a single-file template. |
| vis.js (legacy) | Superseded by vis-network. Do not use the old vis.js bundle. |
| React-based solutions | Single-file HTML. No React, no JSX, no build step. Period. |
| Three.js / WebGPU | 3D is unnecessary. Knowledge graphs are 2D networks. WebGPU browser support is still incomplete in early 2026. |

### Architecture: Template-Based Generation

```
Python side (generator):
    src/utils/knowledge_explorer.py          <- Template engine (string substitution)
    src/utils/templates/explorer.html         <- Single HTML template with Cytoscape.js

Output:
    fin-guru-private/explorers/{topic}.html   <- Generated single-file HTML
```

The Python generator:
1. Takes structured data (nodes + edges from agent analysis)
2. Serializes to JSON
3. Injects into HTML template via string substitution (no Jinja2 needed)
4. Writes single `.html` file

The HTML template:
1. Loads Cytoscape.js from CDN (with inline fallback for offline)
2. Reads injected JSON data from a `<script>` tag
3. Renders force-directed graph with Canvas (WebGL optional via config)
4. Provides: click-to-explore, search, zoom, node details panel, filtering

### Offline Strategy

For offline use, the template embeds the minified Cytoscape.js library inline:
```html
<script>/* cytoscape.min.js inlined here (~300KB) */</script>
```

For online use (smaller files), it loads from CDN:
```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.33.0/cytoscape.min.js"></script>
```

The generator supports both modes via a `--offline` flag.

### No Python Dependencies Needed

The template engine is pure Python string formatting. The interactive behavior is pure JavaScript inside the HTML template. No new Python packages required.

### Installation Command

```bash
# Nothing for Python side.
# Cytoscape.js loaded via CDN in the HTML template, or inlined for offline.
```

---

## Complete Dependency Summary

### NEW Dependencies (Total: 1)

| Package | Version | Milestone | Install Command |
|---|---|---|---|
| questionary | >=2.1.1 | M1 only | `uv add questionary` |

### Existing Dependencies Leveraged (No Changes)

| Package | Milestones Used | Key Capability |
|---|---|---|
| pydantic >=2.10.6 | M1, M2 | Models for all new tools |
| yfinance >=0.2.66 | M2 | Options chains, dividends, price history |
| scipy >=1.16.2 | M2 | norm.cdf/pdf for Greeks, optimize for hedge ratios |
| numpy >=2.3.3 | M2 | Numerical calculations |
| pandas >=2.3.2 | M2 | Time series, return calculations |
| PyYAML >=6.0.3 | M1 | Config file generation |
| python-dotenv >=1.1.1 | M1 | .env template creation |
| argparse (stdlib) | M1, M2 | CLI entry points |
| json (stdlib) | M1, M3 | State persistence, data serialization |
| pathlib (stdlib) | M1, M3 | File path handling |

### JavaScript (CDN only, not in pyproject.toml)

| Library | Version | Milestone | Load Method |
|---|---|---|---|
| Cytoscape.js | >=3.33.0 | M3 | CDN `<script>` or inline |

---

## Alternatives Considered (Cross-Cutting)

| Category | Recommended | Alternative | Why Not Alternative |
|---|---|---|---|
| CLI prompts | questionary 2.1.1 | InquirerPy 0.3.4 | Stale (no release since 2022), smaller community |
| CLI framework | argparse (keep) | click / typer | Would fragment existing 8-CLI codebase |
| Options pricing | scipy (keep) | QuantLib | 100MB+ binary dep, complex build, overkill for European options |
| Graph viz | Cytoscape.js 3.33 | vis-network 10.0 | Performance ceiling at ~1000 nodes, no WebGL |
| Graph viz | Cytoscape.js 3.33 | Sigma.js 3.0 | Requires graphology dep, sparse docs, no built-in layouts |
| Graph viz | Cytoscape.js 3.33 | D3.js force | Too low-level for template-based generation |
| TUI framework | Textual 7.4 (future) | -- | Already a dep. Reserved for future dashboard, NOT for onboarding |
| Template engine | str.format / f-strings | Jinja2 | One template with simple variable injection. Jinja2 is unnecessary complexity. |

---

## Risk Assessment

| Risk | Severity | Mitigation |
|---|---|---|
| questionary 2.x API breaking changes | LOW | Pin to >=2.1.1. API has been stable since 2.0. |
| yfinance options chain reliability | MEDIUM | Already a known risk in the system. Existing retry/fallback patterns in market_data.py apply. |
| Cytoscape.js WebGL renderer instability | LOW | WebGL is optional; Canvas renderer is the stable default. Use Canvas for <1000 nodes. |
| CDN unavailability for Cytoscape.js | LOW | Offline mode inlines the library. Template supports both modes. |
| Textual version drift (6.6 -> 7.4) | LOW | Not used in M1-M3. Update when building future dashboard. |

---

## Sources

### Verified (HIGH confidence)
- PyPI questionary 2.1.1: https://pypi.org/project/questionary/ (Aug 2025 release)
- PyPI textual 7.4.0: https://pypi.org/project/textual/ (Jan 2026 release)
- Cytoscape.js 3.31+ WebGL blog post: https://blog.js.cytoscape.org/2025/01/13/webgl-preview/
- Cytoscape.js 3.33.0 release: https://blog.js.cytoscape.org/news/ (July 2025)
- vis-network 10.0.2: https://www.npmjs.com/package/vis-network (Sep 2025)
- sigma 3.0.2: https://www.npmjs.com/package/sigma (May 2025)
- InquirerPy 0.3.4: https://github.com/kazhala/InquirerPy (stale since 2022)
- Existing codebase: `src/analysis/options.py`, `src/models/options_inputs.py`, `src/utils/progress_persistence.py`

### Cross-referenced (MEDIUM confidence)
- Memgraph graph viz benchmarks: https://memgraph.com/blog/you-want-a-fast-easy-to-use-and-popular-graph-visualization-tool
- Canvas vs WebGL performance: https://digitaladblog.com/2025/05/21/comparing-canvas-vs-webgl-for-javascript-chart-performance/
- Cytoscape.js cdnjs: https://cdnjs.com/libraries/cytoscape/3.31.0
