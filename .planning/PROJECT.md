# Finance Guru v3 — Public Release & Tool Expansion

## What This Is

Transform Finance Guru from a single-user private family office system into a distributable, multi-user financial analysis toolkit while adding hedging/portfolio protection CLI tools and an interactive knowledge assessment system. Three milestones: onboarding infrastructure for public release, hedging strategy CLI tools from the Paycheck to Portfolio advisory session, and a template-based interactive knowledge explorer for education and marketing.

## Core Value

Anyone can clone the repo, run setup, and have a working personalized Finance Guru with their own financial data — no hardcoded references, no manual configuration, and a growing suite of institutional-grade CLI analysis tools.

## Requirements

### Validated

These capabilities exist and are working in the current codebase:

- ✓ 3-layer type-safe architecture (Pydantic Models -> Calculator Classes -> CLI) — established
- ✓ 8 production CLI analysis tools (risk metrics, momentum, volatility, correlation, backtesting, optimizer, moving averages, ITC risk) — established
- ✓ Options pricing and chain scanner (Black-Scholes, Greeks, options_chain_cli.py) — established
- ✓ Market data fetching via yfinance with get_prices() utility — established
- ✓ 365+ pytest tests with established test patterns — established
- ✓ 13-agent system with Finance Orchestrator (Cassandra Holt) entry point — established
- ✓ User profile system (user-profile.yaml) with financial data schema — established
- ✓ Session start hook loading core context (load-fin-core-config.ts) — established
- ✓ Google Sheets portfolio tracker with PortfolioSyncing skill — established
- ✓ Private data separation (fin-guru-private/ gitignored) — established
- ✓ Dividend strategy explorer prototype (playgrounds/dividend-strategy-explorer.html) — established
- ✓ Codebase map at .planning/codebase/ — established

### Active

#### Milestone 1: User Onboarding & Public Release (Core)

- [ ] **ONBD-01**: Interactive CLI onboarding wizard collects user financial profile (liquid assets, investments, cash flow, debt, preferences)
- [ ] **ONBD-02**: Input validation module handles dollar amounts, percentages, enums, dates with retry logic
- [ ] **ONBD-03**: Progress save/resume system persists to .onboarding-progress.json and resumes after interruption
- [ ] **ONBD-04**: YAML generator populates user-profile.template.yaml from onboarding answers
- [ ] **ONBD-05**: setup.sh orchestrates full first-time setup (dependency checks, onboarding, config generation)
- [ ] **ONBD-06**: setup.sh is idempotent — re-run updates missing fields only, preserves existing data
- [ ] **ONBD-07**: CLAUDE.md generated from template with {user_name}, {project-root}, {module-path} variables
- [ ] **ONBD-08**: Interactive .env setup with optional API key collection (Alpha Vantage, ITC Risk, etc.)
- [ ] **ONBD-09**: MCP.json template generation with exa, perplexity, gdrive servers (backup existing)
- [ ] **ONBD-10**: Refactor load-fin-core-config hook to Bun TypeScript (1:1 behavior port)
- [ ] **ONBD-11**: Refactor skill-activation-prompt hook to Bun TypeScript (1:1 behavior port)
- [ ] **ONBD-12**: Refactor post-tool-use-tracker hook to Bun TypeScript (convert from bash)
- [ ] **ONBD-13**: Bun hook test suite with performance assertions (< 500ms per hook)
- [ ] **ONBD-14**: Remove all hardcoded personal name references from public codebase (config.yaml, workflows, etc.)
- [ ] **ONBD-15**: Update .gitignore to protect all private data (user-profile.yaml, .env, CSV exports, fin-guru-private/)
- [ ] **ONBD-16**: All existing 365+ tests still pass after changes (no regressions)
- [ ] **ONBD-17**: Finance Guru agents work with generic user profile (uses {user_name}, not hardcoded)

#### Milestone 2: Hedging & Portfolio Protection Integration

- [ ] **HEDG-01**: HedgeConfig Pydantic model reads hedging preferences from user-profile.yaml via config_loader.py
- [ ] **HEDG-02**: hedging_inputs.py shared models (HedgePosition, RollSuggestion, HedgeSizeRequest, HedgeComparisonInput, etc.)
- [ ] **HEDG-03**: total_return_inputs.py models (TotalReturnInput, DividendRecord, TickerReturn)
- [ ] **HEDG-04**: Rolling strategy tracker CLI (status, suggest-roll, log-roll, history subcommands)
- [ ] **HEDG-05**: Portfolio-aware hedge sizer CLI (sizing formula, budget validation, multi-underlying support)
- [ ] **HEDG-06**: SQQQ vs puts comparison CLI (scenario modeling, breakeven analysis, decay accounting)
- [ ] **HEDG-07**: Total return calculator CLI (price + dividend returns, DRIP modeling, multi-ticker comparison)
- [ ] **HEDG-08**: Private hedging data directory (fin-guru-private/hedging/ with positions.yaml, roll-history.yaml, budget-tracker.yaml)
- [ ] **HEDG-09**: Knowledge base files (hedging-strategies.md, options-insurance-framework.md, dividend-total-return.md, borrow-vs-sell-tax.md)
- [ ] **HEDG-10**: Agent definitions updated to reference new knowledge files (Strategy Advisor, Teaching Specialist, Quant Analyst)
- [ ] **HEDG-11**: Architecture diagram (Mermaid .mmd) showing new components and data flow
- [ ] **HEDG-12**: All 4 new CLI tools work with `uv run python src/analysis/<tool>_cli.py`
- [ ] **HEDG-13**: Tests for all new components (rolling tracker, hedge sizer, hedge comparison, total return, config loader)

#### Milestone 3: Interactive Knowledge Explorer

- [ ] **EXPL-01**: Extract shared template engine from dividend-strategy-explorer.html prototype
- [ ] **EXPL-02**: Topic JSON schema and validator for knowledge graph data
- [ ] **EXPL-03**: Template engine loads topic JSON and renders interactive explorer HTML
- [ ] **EXPL-04**: Dividend strategy topic data migrated to JSON format from prototype
- [ ] **EXPL-05**: localStorage persistence (knowledge state survives page refresh)
- [ ] **EXPL-06**: Learning mode selector (guided/standard/yolo) affects prompt output
- [ ] **EXPL-07**: Maya learner profile export (downloads JSON matching learner_profile schema)
- [ ] **EXPL-08**: Touch/mobile support (drag, tap to cycle knowledge, responsive sidebar)
- [ ] **EXPL-09**: 4 additional topic data files (options-greeks, risk-management, portfolio-construction, tax-optimization)
- [ ] **EXPL-10**: Topic selector landing page (card grid showing all available explorers)
- [ ] **EXPL-11**: Cross-topic concept linking (shared nodes across topics)
- [ ] **EXPL-12**: CLI command `fin-guru explore <topic>` opens explorer in browser
- [ ] **EXPL-13**: Maya reads exported learner profile at session start (if file exists)
- [ ] **EXPL-14**: Embeddable widget mode (iframe-safe, focused layout)
- [ ] **EXPL-15**: Copy prompt works on all major browsers (Chrome, Safari, Firefox)
- [ ] **EXPL-16**: All explorers load in under 1 second (zero external dependencies)

### Out of Scope

- Web-based onboarding UI — CLI only for this release (future enhancement)
- Automated GitHub fork creation — users fork manually with documentation
- Encryption of user-profile.yaml — filesystem permissions only (local-only system)
- Smart merge of MCP.json — always create fresh, users manually merge existing configs
- Multi-language support — English only
- Cloud sync of user data — local-only system
- Telemetry or analytics — no usage tracking
- Streamlit dashboard updates — separate concern
- New API integrations beyond yfinance for hedging tools
- Agent personality changes
- Backend/database for knowledge explorer — static HTML files only
- User accounts or real-time sync with Finance Guru CLI from explorer
- Payment/subscription for explorer

## Context

**Source Material**: Three detailed backlog specs at `.dev/specs/backlog/`:
- `finance-guru-user-onboarding-and-public-release.md` (30 tasks, Linear AOJ-194)
- `finance-guru-hedging-integration.md` (7 scopes, from Jan 30 2026 Paycheck to Portfolio session with Sean)
- `finance-guru-interactive-knowledge-explorer.md` (4 phases, Linear AOJ-231)

**Existing Codebase**: Brownfield Python 3.12+ project with established 3-layer architecture, 8 production CLI tools, 365+ tests, 13-agent system. Codebase map at `.planning/codebase/`.

**Current Portfolio Context**: $219k Fidelity TOD brokerage, $26.7k margin balance, actively using SQQQ hedge position ($12.7k), executing Layer 2 dividend income strategy with 10+ income ETFs.

**Hedging Strategy Context**: From Jan 30 2026 session with Sean (Paycheck to Portfolio):
- QQQ/SPY protective puts: 10-20% OTM, ~30 DTE, roll every 5-7 days
- Sizing: ~1 contract per $50k portfolio value
- Monthly insurance budget: ~$500-600
- SQQQ as alternative/complement to puts
- Total return must include dividends in performance accounting

**Knowledge Explorer Context**: Working prototype exists at `playgrounds/dividend-strategy-explorer.html`. Proven concept: self-assess → generate prompt → copy to any chatbot. Maps to Maya's learner profile system and James Cooper's onboarding flow.

## Constraints

- **Tech Stack**: Python 3.12+ with uv, Pydantic v2, pytest, argparse CLIs — must follow established 3-layer architecture
- **Hooks Runtime**: Bun TypeScript — clean break from bash/ts (no backward compatibility)
- **Privacy**: No private financial data in git history — all personal data gitignored
- **Testing**: All new code must have pytest tests; existing 365+ tests must not regress
- **CLI Pattern**: All new tools use `uv run python <script>` with argparse, --output json, --days N flags
- **Knowledge Files**: Educational/generic content only in public repo — no personal portfolio details
- **Explorer**: Zero external dependencies — single HTML file per topic, localStorage only
- **Performance**: Hooks < 500ms, setup < 5 minutes, onboarding < 15 minutes, explorer loads < 1 second

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| One project, 3 sequential milestones | Onboarding → Hedging → Explorer follows dependency chain | — Pending |
| Specs as guidance, not locked | Allow adjustment during planning when better approaches emerge | — Pending |
| Comprehensive planning depth | Full research to validate specs against codebase reality | — Pending |
| Core onboarding first, docs later | Ship working system before polishing documentation | — Pending |
| Bun hooks, clean break | Simpler codebase, modern tooling, no dual maintenance | — Pending |
| Fork model for public release | Clean separation of template vs personal data | — Pending |
| Idempotent setup with progress saving | Professional UX, handles interruptions, iterative config | — Pending |
| API keys optional during setup | yfinance works without keys, reduces onboarding friction | — Pending |
| Fresh MCP.json (no smart merge) | Safer than parsing user configs, explicit failure mode | — Pending |
| Static HTML explorers (no backend) | Zero-dependency philosophy, ships anywhere | — Pending |

---
*Last updated: 2026-02-02 after initialization*
