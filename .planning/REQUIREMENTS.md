# Requirements

> Derived from PROJECT.md + research synthesis (2026-02-02)

## Scope Legend

| Scope | Meaning |
|-------|---------|
| **v1** | Must ship in this milestone |
| **v2** | Deferred to future iteration |
| **out** | Explicitly will NOT build |

---

## Milestone 1: User Onboarding & Public Release

### Security & Git Hygiene

| ID | Requirement | Scope | Phase | Notes |
|----|-------------|-------|-------|-------|
| ONBD-14 | Remove all hardcoded personal references from public codebase | v1 | 1 | Expand beyond personal names to account numbers, LLC names, employer names, spreadsheet IDs |
| ONBD-15 | Update .gitignore to protect all private data | v1 | 1 | user-profile.yaml, .env, CSV exports, fin-guru-private/, .onboarding-progress.json |
| SEC-01 | Run git filter-repo to scrub PII from git history | v1 | 1 | CRITICAL: brokerage account numbers, net worth figures, personal data in prior commits |
| SEC-02 | Pre-commit secrets hook prevents future PII commits | v1 | 1 | gitleaks or trufflehog pattern scanning |
| SEC-03 | Automated PII grep test in CI | v1 | 1 | Test that greps for known PII patterns returns zero matches |

### Setup Automation

| ID | Requirement | Scope | Phase | Notes |
|----|-------------|-------|-------|-------|
| ONBD-05 | setup.sh orchestrates full first-time setup | v1 | 2 | Dependency checks, onboarding, config generation |
| ONBD-06 | setup.sh is idempotent — re-run updates missing fields only | v1 | 2 | Detect existing files, diff against template, prompt for missing |
| SETUP-01 | Dependency checker verifies prerequisites (uv, bun, Python 3.12+) | v1 | 2 | Show exact install commands on failure, fail-fast |
| SETUP-02 | setup.sh creates fin-guru-private/ directory structure | v1 | 2 | hedging/, strategies/, analysis/ subdirectories |
| SETUP-03 | --check-deps-only flag for dry-run dependency verification | v1 | 2 | For CI/debugging use |

### Onboarding Wizard

| ID | Requirement | Scope | Phase | Notes |
|----|-------------|-------|-------|-------|
| ONBD-01 | Interactive CLI onboarding wizard collects user financial profile | v1 | 3 | questionary library, 8 sections: liquid assets, investments, cash flow, debt, preferences, broker, env, summary |
| ONBD-02 | Input validation handles dollar amounts, percentages, enums, dates with retry | v1 | 3 | Pydantic validators, 3 retries then skip option |
| ONBD-04 | YAML generator populates user-profile.template.yaml from answers | v1 | 3 | Template uses {{variable}} placeholders |
| ONBD-07 | CLAUDE.md generated from template with {user_name}, {project-root} variables | v1 | 3 | Replace hardcoded values with template variables |
| ONBD-08 | Interactive .env setup with optional API key collection | v1 | 3 | Alpha Vantage, ITC Risk, etc. — all optional |
| ONBD-09 | MCP.json template generation with exa, perplexity, gdrive servers | v1 | 3 | Backup existing, generate fresh, show merge instructions |
| ONBD-17 | Finance Guru agents work with generic user profile | v1 | 3 | Uses {user_name} not hardcoded names |
| ONBD-03 | Progress save/resume persists to .onboarding-progress.json | v1 | 4 | Resume after interruption, Ctrl+C safe via SIGINT handler |
| ONBD-16 | All existing 365+ tests still pass after changes | v1 | 4 | No regressions from onboarding changes |

### Hook Refactoring

| ID | Requirement | Scope | Phase | Notes |
|----|-------------|-------|-------|-------|
| ONBD-10 | Refactor load-fin-core-config hook to Bun TypeScript | v1 | 4 | 1:1 behavior port, output comparison testing |
| ONBD-11 | Refactor skill-activation-prompt hook to Bun TypeScript | v1 | 4 | Convert from bash to Bun |
| ONBD-12 | Refactor post-tool-use-tracker hook to Bun TypeScript | v1 | 4 | Convert from bash |
| ONBD-13 | Bun hook test suite with performance assertions (< 500ms) | v1 | 4 | All hooks must complete under 500ms |

### Deferred (M1)

| ID | Requirement | Scope | Notes |
|----|-------------|-------|-------|
| M1-D01 | `fin-guru doctor` diagnostic command | v2 | High value but not blocking release |
| M1-D02 | Contextual explanations per onboarding question | v2 | Can add incrementally post-release |

### Anti-Features (M1)

| ID | Requirement | Scope | Notes |
|----|-------------|-------|-------|
| M1-X01 | Web-based onboarding UI | out | CLI only, doubles implementation surface |
| M1-X02 | Automated GitHub fork creation | out | Users fork manually with docs |
| M1-X03 | Smart MCP.json merge | out | Backup + fresh template + merge instructions |
| M1-X04 | Multi-language i18n | out | English only |
| M1-X05 | Encryption of user-profile.yaml | out | Filesystem permissions only |
| M1-X06 | Telemetry or analytics | out | No tracking whatsoever |
| M1-X07 | Auto-install of dependencies | out | Check + show install commands, user installs |

---

## Milestone 2: Hedging & Portfolio Protection

### Shared Foundation

| ID | Requirement | Scope | Phase | Notes |
|----|-------------|-------|-------|-------|
| HEDG-01 | HedgeConfig Pydantic model reads hedging preferences from user-profile.yaml | v1 | 5 | Via config_loader.py |
| HEDG-02 | hedging_inputs.py shared models (HedgePosition, RollSuggestion, HedgeSizeRequest, etc.) | v1 | 5 | Follow established Pydantic conventions (Literal types, Field descriptions, field_validators) |
| HEDG-03 | total_return_inputs.py models (TotalReturnInput, DividendRecord, TickerReturn) | v1 | 5 | Self-contained, no circular imports |
| HEDG-08 | Private hedging data directory (fin-guru-private/hedging/) | v1 | 5 | positions.yaml, roll-history.yaml, budget-tracker.yaml |
| CFG-01 | config_loader.py provides validated HedgeConfig from user-profile.yaml | v1 | 5 | DRY bridge — prevents duplicated YAML parsing across 4 CLIs |
| CFG-02 | CLI flags override config file values | v1 | 5 | Config as defaults, flags as overrides |
| CFG-03 | Tools work without user-profile.yaml (CLI-flag-only operation) | v1 | 5 | Graceful fallback when config missing |

### Total Return Calculator

| ID | Requirement | Scope | Phase | Notes |
|----|-------------|-------|-------|-------|
| HEDG-07 | Total return CLI: price + dividend returns, DRIP modeling, multi-ticker | v1 | 6 | Simplest M2 tool, standalone value |
| TR-01 | Separate price return, dividend return, and total return in output | v1 | 6 | Three distinct numbers per ticker |
| TR-02 | DRIP modeling: reinvest dividends at ex-date close prices | v1 | 6 | Track growing share count over time |
| TR-03 | Data quality indicator when yfinance dividend data has gaps | v1 | 6 | Warn user, don't silently produce wrong numbers |

### Rolling Tracker & Hedge Sizer

| ID | Requirement | Scope | Phase | Notes |
|----|-------------|-------|-------|-------|
| HEDG-04 | Rolling tracker CLI: status, suggest-roll, log-roll, history subcommands | v1 | 7 | First argparse subcommand pattern in codebase |
| HEDG-05 | Hedge sizer CLI: sizing formula, budget validation, multi-underlying | v1 | 7 | floor(portfolio_value / 50000) baseline |
| RT-01 | Position status display: current positions, P&L, DTE, value | v1 | 7 | Reads positions.yaml, fetches current prices |
| RT-02 | DTE-based roll alerts (configurable threshold, default 7 days) | v1 | 7 | Standard 5-7 DTE roll window |
| RT-03 | Roll suggestion engine: scan options chain for replacements | v1 | 7 | Integrates with options_chain_cli scan_chain() |
| HS-01 | Contract sizing: 1 contract per $50k portfolio value | v1 | 7 | Configurable ratio via HedgeConfig |
| HS-02 | Budget validation: compare cost against monthly budget, show utilization % | v1 | 7 | Fetch current premiums via yfinance |
| HS-03 | Multi-underlying allocation (QQQ + SPY + IWM with weights) | v1 | 7 | Distribute contracts with configurable splits |
| BS-01 | Document Black-Scholes limitation on American-style options | v1 | 7 | Add intrinsic value floor, disclaimer |

### SQQQ vs Puts Comparison

| ID | Requirement | Scope | Phase | Notes |
|----|-------------|-------|-------|-------|
| HEDG-06 | SQQQ vs puts comparison CLI: scenario modeling, breakeven, decay | v1 | 8 | Isolated phase — highest complexity |
| HC-01 | Day-by-day SQQQ simulation with daily rebalancing and volatility drag | v1 | 8 | NOT simple -3x multiplication |
| HC-02 | Discrete scenario modeling (-5%, -10%, -20%, -40% market drops) | v1 | 8 | Simpler than Monte Carlo, adequate for comparison |
| HC-03 | Breakeven analysis per hedge type | v1 | 8 | At what % drop does each hedge profit? |
| HC-04 | IV expansion estimate for puts during crashes | v1 | 8 | VIX-SPX regression model |
| HC-05 | Clear disclaimer: SQQQ decay is path-dependent, results are approximate | v1 | 8 | Anti-feature: don't claim precision |

### Knowledge & Agents

| ID | Requirement | Scope | Phase | Notes |
|----|-------------|-------|-------|-------|
| HEDG-09 | Knowledge base files (hedging-strategies.md, options-insurance-framework.md, etc.) | v1 | 7 | Educational, generic content only |
| HEDG-10 | Agent definitions updated to reference new knowledge files | v1 | 7 | Strategy Advisor, Teaching Specialist, Quant Analyst |
| HEDG-11 | Architecture diagram (Mermaid .mmd) showing new components | v1 | 8 | After all components exist |
| HEDG-12 | All 4 CLI tools work with `uv run python src/analysis/<tool>_cli.py` | v1 | 8 | Integration test |
| HEDG-13 | Tests for all new components | v1 | 6-8 | Incremental per phase |

### Standard Patterns (All M2 Tools)

| ID | Requirement | Scope | Phase | Notes |
|----|-------------|-------|-------|-------|
| STD-01 | JSON + human-readable text output (--output json flag) | v1 | 6-8 | Established pattern across all 8 existing CLIs |
| STD-02 | Educational disclaimers on all output | v1 | 6-8 | Compliance requirement |
| STD-03 | --help with complete examples | v1 | 6-8 | Established pattern |
| STD-04 | Known-answer tests for all calculators | v1 | 6-8 | Validates correctness against hand-calculated values |

### Deferred (M2)

| ID | Requirement | Scope | Notes |
|----|-------------|-------|-------|
| M2-D01 | Roll history logging with cost tracking | v2 | Add after core rolling tracker works |
| M2-D02 | Cross-tool integration (total return feeding hedge comparison) | v2 | Nice-to-have, not core |
| M2-D03 | Portfolio-aware margin-interest-adjusted hedge cost | v2 | Complex, needs more design |

### Anti-Features (M2)

| ID | Requirement | Scope | Notes |
|----|-------------|-------|-------|
| M2-X01 | Live trade execution | out | Massive liability, regulatory complexity |
| M2-X02 | Real-time position monitoring | out | Requires persistent process, broker API |
| M2-X03 | New API integrations beyond yfinance | out | yfinance covers options chains + dividends |
| M2-X04 | Automated roll execution | out | Suggest rolls, user executes manually |
| M2-X05 | Monte Carlo simulation for hedges | out | Discrete scenarios are adequate |

---

## Milestone 3: Interactive Knowledge Explorer

### Template Engine & Core

| ID | Requirement | Scope | Phase | Notes |
|----|-------------|-------|-------|-------|
| EXPL-01 | Extract shared template engine from dividend-strategy-explorer.html | v1 | 9 | Bun build pipeline: JSON + template -> HTML |
| EXPL-02 | Topic JSON schema and validator | v1 | 9 | Schema defines concept graph structure |
| EXPL-03 | Template engine loads topic JSON and renders interactive HTML | v1 | 9 | Single template.html shared across topics |
| EXPL-04 | Dividend strategy topic migrated to JSON from prototype | v1 | 9 | First topic validates the pipeline |

### Self-Assessment & Interaction

| ID | Requirement | Scope | Phase | Notes |
|----|-------------|-------|-------|-------|
| EXPL-05 | localStorage persistence (state survives page refresh) | v1 | 10 | With try/catch + JSON export fallback |
| EXPL-06 | Learning mode selector (guided/standard/yolo) | v1 | 10 | Affects prompt output complexity |
| EXPL-08 | Touch/mobile support (tap to cycle, responsive sidebar) | v1 | 10 | Pointer events API for cross-device |
| EXPL-15 | Copy prompt works on all major browsers | v1 | 10 | navigator.clipboard.writeText with fallback |
| EXPL-16 | All explorers load in under 1 second | v1 | 10 | Zero external dependencies constraint |

### Additional Topics

| ID | Requirement | Scope | Phase | Notes |
|----|-------------|-------|-------|-------|
| EXPL-09a | Options-greeks topic data | v1 | 10 | Curated concept graph |
| EXPL-09b | Risk-management topic data | v1 | 10 | Curated concept graph |
| EXPL-09c | Portfolio-construction topic data | v2 | — | Defer to post-release |
| EXPL-09d | Tax-optimization topic data | v2 | — | Defer to post-release |

### Integration & Polish

| ID | Requirement | Scope | Phase | Notes |
|----|-------------|-------|-------|-------|
| EXPL-07 | Maya learner profile export (JSON matching learner_profile schema) | v1 | 11 | Download JSON, Maya reads at session start |
| EXPL-12 | CLI command `fin-guru explore <topic>` opens in browser | v1 | 11 | Python webbrowser.open() |
| EXPL-13 | Maya reads exported learner profile at session start | v1 | 11 | If file exists in fin-guru/data/ |
| EXPL-10 | Topic selector landing page (card grid) | v1 | 11 | index.html with completion badges |

### Deferred (M3)

| ID | Requirement | Scope | Notes |
|----|-------------|-------|-------|
| EXPL-11 | Cross-topic concept linking | v2 | Needs 4+ topics, localStorage sync across HTML files is architecturally unclear |
| EXPL-14 | Embeddable widget mode (iframe-safe) | v2 | Marketing optimization, not core value |
| EXPL-09c | Portfolio-construction topic | v2 | Content curation effort, add incrementally |
| EXPL-09d | Tax-optimization topic | v2 | Content curation effort, add incrementally |

### Anti-Features (M3)

| ID | Requirement | Scope | Notes |
|----|-------------|-------|-------|
| M3-X01 | Backend/database | out | Violates zero-dependency philosophy |
| M3-X02 | User accounts | out | Anonymous local state + JSON export |
| M3-X03 | Real-time AI integration in explorer | out | Generate prompts, user pastes to chatbot |
| M3-X04 | Drag-and-drop concept rearrangement | out | Expert-curated fixed layouts |
| M3-X05 | Spaced repetition / quiz mode | out | Different product category |
| M3-X06 | Payment/subscription | out | Free and open-source |

---

## Cross-Cutting Requirements

| ID | Requirement | Scope | Notes |
|----|-------------|-------|-------|
| XC-01 | No new Python dependencies except questionary | v1 | Stack research: zero deps for M2 |
| XC-02 | Integration through files (YAML, JSON), never cross-language imports | v1 | Architecture boundary rule |
| XC-03 | All new Python code follows 3-layer pattern | v1 | Models -> Calculators -> CLI |
| XC-04 | Tests for all new components | v1 | pytest, incremental per phase |
| XC-05 | Educational-only disclaimers on all financial output | v1 | Compliance requirement |
| XC-06 | No private financial data in public git history | v1 | CRITICAL: irreversible if violated |

---

## Phase → Requirement Mapping

| Phase | Requirements |
|-------|-------------|
| **1: Git Scrub** | SEC-01, SEC-02, SEC-03, ONBD-14, ONBD-15 |
| **2: Setup** | ONBD-05, ONBD-06, SETUP-01, SETUP-02, SETUP-03 |
| **3: Onboarding** | ONBD-01, ONBD-02, ONBD-04, ONBD-07, ONBD-08, ONBD-09, ONBD-17 |
| **4: Polish & Hooks** | ONBD-03, ONBD-10, ONBD-11, ONBD-12, ONBD-13, ONBD-16 |
| **5: Config & Models** | HEDG-01, HEDG-02, HEDG-03, HEDG-08, CFG-01, CFG-02, CFG-03 |
| **6: Total Return** | HEDG-07, TR-01, TR-02, TR-03, STD-01..04, HEDG-13 |
| **7: Tracker & Sizer** | HEDG-04, HEDG-05, RT-01..03, HS-01..03, BS-01, HEDG-09, HEDG-10, STD-01..04, HEDG-13 |
| **8: SQQQ vs Puts** | HEDG-06, HC-01..05, HEDG-11, HEDG-12, STD-01..04, HEDG-13 |
| **9: Template Engine** | EXPL-01, EXPL-02, EXPL-03, EXPL-04 |
| **10: Assessment** | EXPL-05, EXPL-06, EXPL-08, EXPL-09a, EXPL-09b, EXPL-15, EXPL-16 |
| **11: Integration** | EXPL-07, EXPL-10, EXPL-12, EXPL-13 |

---
*Last updated: 2026-02-02*
