<!-- markdownlint-configure-file {"MD024": {"siblings_only": true}} -->

# Changelog

All notable changes to Finance Guru™ will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.3.2](https://github.com/AojdevStudio/Finance-Guru/compare/v2.3.1...v2.3.2) (2026-09-03)


### Documentation

* link every third-party vendor mention to its site ([#174](https://github.com/AojdevStudio/Finance-Guru/issues/174)) ([290c106](https://github.com/AojdevStudio/Finance-Guru/commit/290c106f4a2e7db5ea34e13c669e6cd2a2b9231a))

## [2.3.1](https://github.com/AojdevStudio/Finance-Guru/compare/v2.3.0...v2.3.1) (2026-09-02)


### Documentation

* README first screen, canonical AGENTS.md, and the plugin-and-tools truth ([#166](https://github.com/AojdevStudio/Finance-Guru/issues/166)) ([277ab9d](https://github.com/AojdevStudio/Finance-Guru/commit/277ab9d16af5abfdd9b1bffb3f0d56819196b6c6))

## [2.3.0](https://github.com/AojdevStudio/Finance-Guru/compare/v2.2.0...v2.3.0) (2026-09-02)


### Added

* **config:** resolve every private path from one instance data root ([#133](https://github.com/AojdevStudio/Finance-Guru/issues/133)) ([c70d05b](https://github.com/AojdevStudio/Finance-Guru/commit/c70d05bb13669c06db50b5696e85bcda4ecde5b8))
* **instance:** scaffold a local-only instance directory ([#135](https://github.com/AojdevStudio/Finance-Guru/issues/135)) ([bac7c5a](https://github.com/AojdevStudio/Finance-Guru/commit/bac7c5a2d3148fab15a35e12e6a821ef7d0f56f5))
* **plugin:** package Finance Guru as a Claude Code plugin with a Codex surface ([#145](https://github.com/AojdevStudio/Finance-Guru/issues/145)) ([fa9739b](https://github.com/AojdevStudio/Finance-Guru/commit/fa9739bb3aec600ac7c7fb5b8fd4f33f5259eb4c)), closes [#131](https://github.com/AojdevStudio/Finance-Guru/issues/131)


### Fixed

* **buy-ticket:** fail closed on NAV, margin rate, and Layer 3 ITC, and model persistence apart from notification ([#159](https://github.com/AojdevStudio/Finance-Guru/issues/159)) ([3735eae](https://github.com/AojdevStudio/Finance-Guru/commit/3735eae1e91b50d201edf095a50b78635b6ec3e8))
* **cli:** restore the broken CLI help paths, harden onboarding state writes, and add plugin-mode instance init ([#156](https://github.com/AojdevStudio/Finance-Guru/issues/156)) ([8546d5c](https://github.com/AojdevStudio/Finance-Guru/commit/8546d5c0df8cea94ab88e3c73b9e4a9a49b2cb6d))
* **deps:** cap the SnapTrade SDK below 12 ([#142](https://github.com/AojdevStudio/Finance-Guru/issues/142)) ([d5817d4](https://github.com/AojdevStudio/Finance-Guru/commit/d5817d4520437324c4cdc2b7d006fcad1abd8e6a)), closes [#131](https://github.com/AojdevStudio/Finance-Guru/issues/131)
* **deps:** upgrade gitpython, nltk, soupsieve, and pygments past their advisories ([#151](https://github.com/AojdevStudio/Finance-Guru/issues/151)) ([947bf9f](https://github.com/AojdevStudio/Finance-Guru/commit/947bf9f967fb0d7bd19ce8292de5917a4977a06a))
* **docs-site:** make bun.lock the only lockfile and bump astro to 7.2.10 ([#152](https://github.com/AojdevStudio/Finance-Guru/issues/152)) ([171b6d6](https://github.com/AojdevStudio/Finance-Guru/commit/171b6d6fcbe624bc88d101b82b8b204e8748a5de))
* **instance:** ignore inherited git environment when scaffolding ([#140](https://github.com/AojdevStudio/Finance-Guru/issues/140)) ([c1e77fb](https://github.com/AojdevStudio/Finance-Guru/commit/c1e77fbcdb6fa15b23229fc17b6134349e50b2a3)), closes [#131](https://github.com/AojdevStudio/Finance-Guru/issues/131)
* **instance:** scrub placeholder env values and run chart tools as modules ([#149](https://github.com/AojdevStudio/Finance-Guru/issues/149)) ([feaf759](https://github.com/AojdevStudio/Finance-Guru/commit/feaf759377235dece2ca348cf52ee1a0eebc5f48)), closes [#131](https://github.com/AojdevStudio/Finance-Guru/issues/131)
* **margin:** route margin metrics to the unique taxable_margin account and validate the balance generation ([#155](https://github.com/AojdevStudio/Finance-Guru/issues/155)) ([8c94e83](https://github.com/AojdevStudio/Finance-Guru/commit/8c94e83a454bb7968277cdf4a89a94d857787008))
* **simplefin:** correct sync direction, payroll and retirement categorization, and close the privacy gate that missed them ([#128](https://github.com/AojdevStudio/Finance-Guru/issues/128)) ([89f3c4f](https://github.com/AojdevStudio/Finance-Guru/commit/89f3c4ff5135989f10b5371a362258681ee7b420))
* **simplefin:** fail partial syncs loudly and gate the deposit trigger on settled transactions ([#154](https://github.com/AojdevStudio/Finance-Guru/issues/154)) ([5917d28](https://github.com/AojdevStudio/Finance-Guru/commit/5917d28a29f44afb1d94496f97793343a203e949))
* **snaptrade:** key activities on provider identity, canonicalize dates, and fail closed on incomplete balances ([#157](https://github.com/AojdevStudio/Finance-Guru/issues/157)) ([89fb024](https://github.com/AojdevStudio/Finance-Guru/commit/89fb024f80762f0568c2a623afa3ce19d2e30b4b))


### Changed

* **deps:** upgrade the 12 packages from the stale dependabot PR ([#124](https://github.com/AojdevStudio/Finance-Guru/issues/124)) ([d13f5ab](https://github.com/AojdevStudio/Finance-Guru/commit/d13f5ab69d99750229bc91d00c8dc9a257f20817))
* **privacy:** clear the standing layer-7 and pattern findings ([#141](https://github.com/AojdevStudio/Finance-Guru/issues/141)) ([a8fcf0e](https://github.com/AojdevStudio/Finance-Guru/commit/a8fcf0ed7135fc3acde3ebcb5aa56e709d1cb08e)), closes [#130](https://github.com/AojdevStudio/Finance-Guru/issues/130)
* **privacy:** rewrite standing financial figures as ratios per DataClassification ([#129](https://github.com/AojdevStudio/Finance-Guru/issues/129)) ([62b1ad9](https://github.com/AojdevStudio/Finance-Guru/commit/62b1ad9e9d682fcf509f364b92f910aa592fe706))
* **privacy:** untrack the last three instance artifacts ([#132](https://github.com/AojdevStudio/Finance-Guru/issues/132)) ([8d441f8](https://github.com/AojdevStudio/Finance-Guru/commit/8d441f82ce32dc9f607238a954278df707dfc1c6))
* **sheets:** retire the Google Sheets DataHub; family_office.db is the system of record ([#114](https://github.com/AojdevStudio/Finance-Guru/issues/114)) ([42be217](https://github.com/AojdevStudio/Finance-Guru/commit/42be217693cda90bc27a5b763ad2512eebcc9490))


### Documentation

* establish source-backed Wiki documentation ([#121](https://github.com/AojdevStudio/Finance-Guru/issues/121)) ([0269048](https://github.com/AojdevStudio/Finance-Guru/commit/02690486e5dcaa175a32f302f9c7d12afe6eb499))
* **readme:** acknowledge the September sweep, address agents directly, and drop template filler ([#163](https://github.com/AojdevStudio/Finance-Guru/issues/163)) ([a2e269b](https://github.com/AojdevStudio/Finance-Guru/commit/a2e269b6e8899249e800d0cc49ca4aa1600adbd9))
* **readme:** rewrite the README as a story with generated architecture, guardrail, and demo assets ([#162](https://github.com/AojdevStudio/Finance-Guru/issues/162)) ([18c8fd5](https://github.com/AojdevStudio/Finance-Guru/commit/18c8fd5beb4712218e54863f6ef098fbad929d06))
* reposition the README and setup guides for installers ([#146](https://github.com/AojdevStudio/Finance-Guru/issues/146)) ([ef04e11](https://github.com/AojdevStudio/Finance-Guru/commit/ef04e1171d2f88c37d97db648af392dc67e9e432)), closes [#131](https://github.com/AojdevStudio/Finance-Guru/issues/131)
* **site:** add the Diátaxis documentation site on the AOJ Starlight starter ([#147](https://github.com/AojdevStudio/Finance-Guru/issues/147)) ([83077d6](https://github.com/AojdevStudio/Finance-Guru/commit/83077d60fe1b171f5fdeac2f5f10c75f5c0b7e08)), closes [#131](https://github.com/AojdevStudio/Finance-Guru/issues/131)
* **skills:** fix the five skill and onboarding contract bugs ([#144](https://github.com/AojdevStudio/Finance-Guru/issues/144)) ([2683f1d](https://github.com/AojdevStudio/Finance-Guru/commit/2683f1d22b6e96c7989343b436af913227148c18)), closes [#137](https://github.com/AojdevStudio/Finance-Guru/issues/137)
* **skills:** point every skill, agent, and task at the instance layout ([#136](https://github.com/AojdevStudio/Finance-Guru/issues/136)) ([d0515b1](https://github.com/AojdevStudio/Finance-Guru/commit/d0515b1d629b4e3cf663b54888f872de501eb45b)), closes [#131](https://github.com/AojdevStudio/Finance-Guru/issues/131)
* **wiki:** ledger rows for the instance data root claims ([#143](https://github.com/AojdevStudio/Finance-Guru/issues/143)) ([f512ee4](https://github.com/AojdevStudio/Finance-Guru/commit/f512ee45b59d483b156bff048ee296d039b144fe)), closes [#131](https://github.com/AojdevStudio/Finance-Guru/issues/131)


### Security

* scrub PII from HEAD and stop the scanner passing blind ([#123](https://github.com/AojdevStudio/Finance-Guru/issues/123)) ([4939a58](https://github.com/AojdevStudio/Finance-Guru/commit/4939a58d5c1a22745e53559e319f9228f6e13e2c))
* untrack qa PII replacement files ([bb9c5a3](https://github.com/AojdevStudio/Finance-Guru/commit/bb9c5a3ab2c6997545391f84681db897d46e975f))

## [Unreleased]

### Changed

- Migrated the data-syncing skills to a DB-backed, sync-first live path so
  portfolio, transaction, dividend, and margin reads come from
  `family_office.db` instead of exported spreadsheets (#114).

### Removed

- Retired the Google Sheets DataHub across docs and skills; `family_office.db`
  is now the system of record (#114).
- Dropped the `gdrive` MCP setup instructions from the setup documentation, and
  removed the residual Google references from the privacy policy and the
  runbook index (#114).

### Fixed

- Restored the Travel and Transfer categories in transaction categorization,
  and unpinned the affected test from a private script (#114).
- SimpleFIN expense categorization now matches on the normalized `payee` as
  well as the raw `description`, which had left 67% of 30-day debit volume
  uncategorized, and credit card payments no longer fall through to
  `Loan Payment`.
- Transaction direction no longer trusts the Fidelity CMA amount sign, which is
  wrong in both directions; debit-card purchases, cash advances, and the two
  legs of an internal transfer are now resolved from the feed wording.

### Security

- Scrubbed PII from HEAD and stopped the compliance scanner passing blind
  (#123), and untracked the QA PII replacement files (#122).
- Business-account detection no longer hard-codes entity names in source; extra
  hints are supplied at runtime through `FG_BUSINESS_ACCOUNT_HINTS`.

## [2.2.0] - 2026-07-27

### Added

- Deterministic buy-ticket pipeline with event triggers, smoke coverage,
  generation guardrails, notifications, state handling, and sanitized advisory
  fields (#75-#79).
- SnapTrade account discovery plus live positions, balances, and paginated
  activity sync, replacing legacy CSV reads (#81).
- Live margin metrics derived from current account balances.
- Canonical Finance Guru definitions glossary with automated drift detection
  (#70).
- Compliance scanning skill with secret and PII detection, allowlisting, and
  pre-push integration.
- Reproducible development and operations infrastructure: dev container,
  quality gates, feature flags, structured logging, observability guidance,
  monitoring rules, and recurring runbooks.

### Changed

- Aligned Finance Guru agents, skills, and buy-ticket routing around the
  canonical definitions and guarded pipeline.
- Moved personal strategy values to environment configuration.
- Updated core dependencies, including pandas 3, yfinance 1.3, and current
  GitHub Actions runtimes.
- Reworked the repository README and contributor guidance to match the
  checked-in system (#110).

### Removed

- Retired the Plaid dashboard in favor of the SnapTrade integration (#81).
- Removed legacy Beads workflow dependencies and vendored generic agent skills.

### Fixed

- Correctly parse Fidelity accounting-parenthesis negatives in margin CSV
  fallbacks (#89).
- Prevent dividend double-counting in total-return calculations (#92).
- Use relative risk contributions in risk-parity optimization (#91).
- Keep Black-Litterman views unit-consistent (#99).
- Fail closed when the ITC CLI cannot return a score (#80).
- Prevent `src/utils/*_cli.py` direct invocation from shadowing Python's
  standard `logging` module.
- Allow Cursor-authored changes to trigger Claude Code Review.
- Keep release workflow runs non-failing when the release token is absent.

### Security

- Hardened PII and secret scanning and removed hardcoded personal strategy
  values from version-controlled configuration.

## [2.1.0] - 2026-04-16

### Added
- _Finance Guru Desktop v1_ (`finance-guru-desktop/`) — Electron + Agent SDK desktop app
  - Electron main process bootstrap with preload IPC bridge (analysis, csv, chat namespaces)
  - HTML shell with sidebar, tabs, panels, modal, status bar
  - CSS theme system — 7 modular files, dark theme, financial green accent
  - Observable State class and portfolio state module
  - IPC handlers for Python analysis bridge and CSV reader
  - v1 command registry and analysis allowlist
  - CommandPalette component with click handlers for tools, skills, agents
  - Modal dialog with dynamic form builder for command arguments
  - Plotly dark theme utility with CSS variable bridge
  - Analysis renderers — Plotly charts, animated gauges, data tables
  - Renderer wiring — command palette, modal args, analysis execution, CSV loading
  - Chat IPC handlers with Agent SDK streaming and message queue
  - ChatView with Agent SDK streaming, skill activation, and agent dispatch
  - esbuild bundler for renderer
  - Runtime path validation for repo-bound desktop app
- _Agent skills system_ — new `.agents/skills/` directory with 17 skill modules (browser automation, brainstorming, coding tutor, document review, frontend design, orchestrating swarms, and more)
- _Portfolio & Transaction syncing workflows_ — IngestPositions and IngestTransactions workflows for broker CSV import
- _Options chain CLI_ (`src/analysis/options_pricer_cli.py`) — Greeks, strategy analysis, and chain data
- _Readiness report skill_ — evaluate codebase readiness for autonomous AI development
- _Hedging & Portfolio Protection_ — complete Milestone 2 (v2.0) with hedging integration and interactive knowledge explorer specs
- _Runtime path validation_ — repo-bound desktop app validation with comprehensive tests
- _v3 roadmap_ — 11 phases across 3 milestones with requirements specification
- _Tmux persona team wrapper_ — Overstory-powered guru session management
- _GitHub social card_ and FUNDING.yml for repository
- _MCP Launchpad verification step_ in setup flow
- _Dividend strategy playground_ and config cleanup
- Codex full review report and validation system
- Broker CSV mapping templates for multi-broker support
- Pre-codex validation script and reporting
- Comprehensive testing infrastructure (Master Test Runner)
- Integration tests: Full setup flow, Onboarding resume, Idempotent re-run
- Gitignore protection tests for sensitive data

### Changed
- _Repo hygiene overhaul_ — untracked GSD/planning files, removed beads/guru legacy, slimmed CLAUDE.md
- _Agent roster update_ — added Finance Guru agents, removed legacy backend skills
- _Docs reorganization_ — category subdirs with frontmatter, updated index and internal links
- _README rewrite_ — hero banner, architecture diagram, narrative format via AwesomeReadme skill
- Converted hooks to Bun runtime for better performance
- Enhanced setup.sh with onboarding integration
- Removed legacy error-handling hook, documented justfile recipes
- Moved specs and dev artifacts into `.dev/` directory

### Fixed
- Agent SDK chat — use string prompt with session resume
- Mocked dividend schedules for CI compatibility
- Tightened runtime validation tests, SDK dependency, and auth checks
- PR review findings across CLI, specs, and skill
- Addressed Codex P0 critical issues
- Removed hardcoded user name references for fork compatibility

### Security
- Upgraded protobuf to >=6.33.5 for CVE recursion depth bypass
- Updated urllib3 to 2.6.3 for 3 high-severity vulnerabilities
- Patched Pillow CVE, added type stubs for CI
- Replaced hardcoded PII with template variables in working tree

## [2.0.0] - 2025-10-08

### Major Release
Finance Guru™ v2.0.0 - Private AI-powered family office system built on BMAD-CORE™ v6.

### Added

#### Core Infrastructure
- Multi-agent orchestration system with 8 specialized financial agents
  - Cassandra Holt (Finance Orchestrator)
  - Market Researcher
  - Quant Analyst
  - Strategy Advisor
  - Compliance Officer
  - Margin Specialist
  - Dividend Specialist
  - Tax Optimizer
- Interactive onboarding wizard with financial assessment
  - User profile generation system
  - Risk tolerance configuration
  - Strategy recommendations
  - YAML profile generation from questionnaire responses
  - Onboarding summary and confirmation flow
- Session start hooks for context injection
  - `load-fin-core-config.ts` - System configuration loader
  - `skill-activation-prompt.ts` - Skill routing system
  - `post-tool-use-tracker.ts` - Usage tracking

#### Analysis Tools (11 Production-Ready)
- **Risk Analysis**
  - Risk Metrics CLI (`src/analysis/risk_metrics_cli.py`)
    - VaR, CVaR, Sharpe Ratio, Sortino Ratio
    - Maximum Drawdown, Calmar Ratio
    - Beta, Alpha calculations
  - ITC Risk CLI (`src/analysis/itc_risk_cli.py`)
    - Market-implied risk scores
    - Risk bands for entry/exit timing
    - Support for crypto and TradFi universes
- **Technical Analysis**
  - Momentum CLI (`src/utils/momentum_cli.py`)
    - RSI, MACD, Stochastic, Williams %R, ROC
    - Confluence indicators
  - Moving Averages CLI (`src/utils/moving_averages_cli.py`)
    - SMA, EMA, WMA, HMA
    - Golden/Death Cross detection
  - Volatility CLI (`src/utils/volatility_cli.py`)
    - Bollinger Bands, ATR, Historical Volatility
    - Keltner Channels, StdDev, Regime detection
- **Portfolio Management**
  - Correlation CLI (`src/analysis/correlation_cli.py`)
    - Pearson matrix, Covariance analysis
    - Diversification scoring, Concentration metrics
  - Portfolio Optimizer CLI (`src/strategies/optimizer_cli.py`)
    - Max Sharpe, Risk Parity, Min Variance
    - Mean-Variance, Black-Litterman
  - Backtester CLI (`src/strategies/backtester_cli.py`)
    - RSI strategy, SMA crossover, Buy-and-hold
    - Sharpe calculation, Win rate, Drawdown tracking
- **Options Analysis**
  - Options Pricer CLI (`src/analysis/options_pricer_cli.py`)
    - Black-Scholes pricing model
    - Greeks calculation (Delta, Gamma, Theta, Vega, Rho)
    - Implied Volatility

#### Finance Guru Skills (9 Skills)
- `fin-core` - Core Finance Guru system context loader
- `margin-management` - Margin Dashboard integration and tracking
- `PortfolioSyncing` - Fidelity CSV → Google Sheets synchronization
- `MonteCarlo` - Monte Carlo simulation runner for portfolio stress testing
- `retirement-syncing` - Retirement account sync (Vanguard/Fidelity)
- `dividend-tracking` - Dividend data synchronization and tracking
- `FinanceReport` - PDF analysis report generator
- `TransactionSyncing` - Transaction history import and categorization
- `formula-protection` - Spreadsheet formula protection system

#### Architecture & Type Safety
- 3-layer architecture pattern: Pydantic Models → Calculator Classes → CLI
- Type-safe validation across all tools
- Standardized CLI interface patterns
- Comprehensive error handling and validation

#### Documentation
- Complete setup guide (SETUP.md)
- API reference documentation (api.md)
- Hooks system documentation (hooks.md)
- Contributing guidelines (contributing.md)
- API key acquisition guide (api-keys.md)
- Troubleshooting guide (TROUBLESHOOTING.md)
- Documentation index hub (index.md)

#### Project Infrastructure
- Automated setup script (`setup.sh`)
  - Python virtual environment setup
  - Dependency installation with `uv`
  - Private directory structure creation
  - Symlink installation for commands and skills
  - MCP.json generation
  - Interactive .env setup
- Comprehensive .gitignore for financial data protection
- Fork-friendly architecture with privacy safeguards
- CLAUDE.md template system
- RBP (Ralph + Beads + PAI) integration
  - Beads workflow context
  - Session close protocol
  - Task tracking and management

#### Testing
- Unit tests for all calculator classes
- CLI integration tests
- Hook functionality tests (Bun-based)
- Gitignore protection tests
- Full setup flow integration tests
- Onboarding resume tests
- Idempotent re-run tests

#### Integration & APIs
- yfinance for market data (default, no API key required)
- Optional Finnhub API for real-time intraday prices
- Optional ITC Risk Models API for external risk intelligence
- Google Drive MCP server integration for portfolio tracking
- Perplexity MCP for AI-powered market research
- Exa MCP for web intelligence gathering
- Sequential-thinking MCP for complex reasoning

### Technical Details
- **Python**: 3.12+ with `uv` package manager
- **Dependencies**: pandas, numpy, scipy, scikit-learn, yfinance, streamlit, beautifulsoup4, requests, pydantic, python-dotenv
- **CLI Runtime**: Bun for hooks and utilities
- **Orchestration**: Claude Code
- **License**: GNU Affero General Public License v3.0 (AGPLv3)

### Security & Privacy
- All financial data stays local
- .gitignore protection for sensitive files
- No external data transmission without explicit user action
- Private fork model for personal use
- Session-based context with auto-cleanup

### Known Limitations
- Tools: 8/11 tools complete (per CLAUDE.md)
- Market data limited to yfinance without API keys
- Options Pricer uses basic Black-Scholes (no exotic options)
- Backtester uses simple strategies (no ML-based)

## Project Links

- _Repository_: [AojdevStudio/Finance-Guru](https://github.com/AojdevStudio/Finance-Guru)
- _Documentation_: [Documentation index](docs/index.md)
- _Setup Guide_: [Setup guide](docs/setup/SETUP.md)
- _Contributing_: [Contribution guide](docs/CONTRIBUTING.md)

## Version History

- **v2.1.0** (2026-04-16) - Finance Guru Desktop v1, agent skills system, hedging milestone, repo hygiene
- **v2.0.0** (2025-10-08) - Initial major release with full agent system
- **Unreleased** - Current development branch

---

**Note**: This is a private family office system. All changes are for personal use unless explicitly stated otherwise.

**Educational Disclaimer**: Finance Guru™ is for educational purposes only. Not investment advice. Consult licensed professionals before making investment decisions.


## Links
[Unreleased]: https://github.com/AojdevStudio/Finance-Guru/compare/v2.2.0...HEAD
[2.2.0]: https://github.com/AojdevStudio/Finance-Guru/releases/tag/v2.2.0
