<!-- markdownlint-configure-file {"MD024": {"siblings_only": true}} -->

# Changelog

All notable changes to Finance Guru™ will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
