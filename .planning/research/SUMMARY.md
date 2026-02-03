# Project Research Summary

**Project:** Finance Guru v3 (Public Release, Hedging CLIs, Knowledge Explorer)
**Domain:** CLI financial analysis toolkit -- private-to-public transformation + options hedging + interactive education
**Researched:** 2026-02-02
**Confidence:** HIGH

## Executive Summary

Finance Guru v3 is a three-milestone evolution of an established Python 3.12+ financial analysis system with 8 existing CLI tools, 365+ tests, and a proven 3-layer architecture (Pydantic Models -> Calculator Classes -> CLI). The v3 work adds three architecturally distinct components: a public-facing onboarding system (TypeScript/Bun), four new hedging CLI tools (Python, fitting the existing 3-layer pattern), and a static HTML knowledge explorer (Bun build pipeline + Cytoscape.js). The single most important finding across all research is that these three components share a configuration nexus (`user-profile.yaml`) but have zero runtime dependencies on each other, which means they should be built in strict dependency order (M1 -> M2 -> M3) but M3 can start in parallel with M2 once onboarding stabilizes the profile schema.

The recommended approach is conservative on dependencies and aggressive on leveraging existing code. Only ONE new Python dependency is needed across all three milestones (`questionary` for M1 interactive prompts). M2 hedging tools require zero new dependencies -- the existing scipy, yfinance, and options.py infrastructure covers Black-Scholes, Greeks, options chains, and dividends. M3 uses Cytoscape.js via CDN for graph visualization in generated single-file HTML. The stack research is definitive: no QuantLib, no click/typer migration, no React, no build frameworks.

The critical risks cluster around two areas. First, M1's public release requires scrubbing real financial PII from git history (brokerage account numbers, net worth figures, LLC names) -- this is a CRITICAL prerequisite that cannot be deferred. Simply adding gitignore rules does not remove data from prior commits. Second, M2's SQQQ-vs-puts comparison tool must model daily-rebalanced leveraged ETF returns with volatility drag, not simple -3x multiplication. Getting this wrong produces misleading hedge comparisons in exactly the high-volatility scenarios where hedging matters most. Both risks have clear mitigations documented in PITFALLS.md.

## Key Findings

### Recommended Stack

The stack decision is unusually clean: one new dependency for M1, zero for M2, one CDN library for M3. The existing codebase already contains everything needed for options pricing (scipy norm.cdf/pdf), market data (yfinance), data models (Pydantic), and CLI infrastructure (argparse). See [STACK.md](./STACK.md) for full analysis.

**Core technologies (additions only):**
- **questionary >=2.1.1** (M1): Interactive CLI prompts for onboarding wizard -- most popular Python prompt library, MIT license, async support
- **Cytoscape.js >=3.33.0** (M3): Force-directed graph visualization via CDN -- WebGL renderer for large graphs, Canvas default for reliability, no npm install

**Rejected alternatives with strong rationale:**
- QuantLib (100MB+ binary, overkill for European-style Black-Scholes already implemented)
- click/typer (would fragment 8 existing argparse CLIs)
- vis-network (performance ceiling at ~1000 nodes)
- Sigma.js (requires separate graphology dependency, sparse docs)
- D3.js (too low-level for template-based generation)
- Jinja2 (one template with simple variable injection does not justify a dependency)

### Expected Features

Feature research identified clear MVP boundaries per milestone with explicit anti-features. The most important finding is that M2 should ship in two drops (core tools first, SQQQ comparison second) because the path-dependent decay modeling is the riskiest single feature. See [FEATURES.md](./FEATURES.md) for full feature landscape.

**Must have (table stakes):**
- M1: Dependency checker, interactive onboarding, input validation, config generation, .gitignore protection, idempotent re-run, clear README
- M2: Position status display, DTE roll alerts, contract sizing formula, budget validation, price+dividend return separation, multi-ticker comparison, JSON+text output
- M3: Self-assessment per concept, localStorage persistence, visual knowledge map, copy-to-clipboard prompt generation, 3+ topics, mobile/touch support

**Should have (differentiators):**
- M1: Save/resume on Ctrl+C (critical for 15-min onboarding), Bun hook ports with test assertions
- M2: Roll suggestion engine (scans options chain for replacements -- unique in CLI tools), DRIP modeling in total return, config-driven defaults from user profile
- M3: Learning mode selector (Guided/Standard/YOLO), Maya learner profile export, CLI launcher

**Defer:**
- M1: `fin-guru doctor` command, contextual explanations per question
- M2: SQQQ vs puts analyzer to Drop 2 (highest complexity), roll history logging, cross-tool integration
- M3: Cross-topic concept linking (high complexity, needs 4+ topics first), embeddable widget mode, topic selector landing page

**Anti-features (explicitly do NOT build):**
- Live trade execution or automated roll execution (liability, regulatory)
- Web-based onboarding UI (doubles implementation surface)
- Telemetry or analytics (destroys trust for financial tools)
- Backend/database for explorer (violates zero-dependency philosophy)
- Monte Carlo for hedges (discrete scenarios are simpler and adequate)

### Architecture Approach

The architecture centers on file-based integration between three isolated components. Onboarding (TypeScript/Bun) WRITES configuration files; hedging tools (Python) and hooks (TypeScript) READ them. The explorer has ZERO dependencies on the Python codebase. A new `ConfigLoader` abstraction (Python Layer 2) bridges `user-profile.yaml` to all four hedging tools, eliminating duplicated YAML parsing across CLIs. The rolling tracker introduces the codebase's first argparse subcommand pattern (`status`, `suggest-roll`, `log-roll`, `history`). See [ARCHITECTURE.md](./ARCHITECTURE.md) for system map, data flows, and integration matrix.

**Major components:**
1. **Onboarding System** (TypeScript/Bun) -- collects financial profile, generates user-profile.yaml, .env, .mcp.json, CLAUDE.md
2. **Config Loader** (Python, new) -- reads user-profile.yaml, returns validated Pydantic HedgeConfig; DRY bridge to hedging tools
3. **4 Hedging CLIs** (Python, 3-layer) -- rolling tracker, hedge sizer, hedge comparison, total return; all follow established pattern
4. **Knowledge Explorer** (Bun build + browser runtime) -- JSON + HTML template -> standalone zero-dependency HTML files with Cytoscape.js
5. **Hook Infrastructure** (Bun TypeScript, refactored) -- session start context loading, mixed-runtime cleanup

**Key boundary rules:**
- Integration happens through files (YAML, JSON), never cross-language imports
- Onboarding is write-only; everything else is read-only against config files
- Explorer shares zero code with Python codebase
- New hedging models import from options_inputs.py (one-way), never circular

### Critical Pitfalls

Research identified 19 pitfalls across 4 severity levels. The top 5 are make-or-break for the project. See [PITFALLS.md](./PITFALLS.md) for complete analysis with detection and prevention strategies.

1. **Private financial data in git history** (CRITICAL, M1) -- Real account numbers, net worth, LLC names persist in git history even after gitignore. Run `git filter-repo` before any public release. Rotate all API keys that were ever committed.
2. **Hardcoded personal references beyond "Ossie"** (CRITICAL, M1) -- Existing test only greps for name. Account number Z05724592 hardcoded in hooks. LLC names, employer names, spreadsheet IDs all present. Expand scrub patterns to comprehensive PII search.
3. **SQQQ modeled as simple -3x multiplication** (CRITICAL, M2) -- Daily-rebalanced leveraged ETF returns diverge 5-20% from simple multiplication over 30 days. Must use day-by-day simulation with volatility drag. Validate against historical data.
4. **Black-Scholes applied to American-style options** (CRITICAL, M2) -- QQQ/SPY options are American-style; BS underprices ITM puts. Document limitation, add intrinsic value floor at minimum.
5. **Financial calculator output treated as actionable** (CRITICAL, M2) -- Every calculator needs known-answer tests, data freshness indicators, confidence bands, and conservative rounding (floor, not round).

## Implications for Roadmap

Based on combined research, here is the suggested phase structure across all three milestones. The ordering follows the dependency chain discovered in architecture research: onboarding produces config files that hedging tools consume, and the explorer benefits from stable config schema.

### Milestone 1: Public Release & Onboarding

#### Phase 1: Git History Scrub & Security Foundation
**Rationale:** CRITICAL prerequisite. Nothing else matters if PII leaks when repo goes public. Must complete before ANY public visibility.
**Delivers:** Clean git history, expanded scrub patterns test, pre-commit secrets hook, .gitignore audit
**Addresses:** Pitfall 1 (git history PII), Pitfall 2 (hardcoded references), Pitfall 16 (pre-commit hook)
**Avoids:** Irreversible exposure of financial data

#### Phase 2: Setup Automation & Dependency Checking
**Rationale:** setup.sh is the first thing a new user runs. Must work on a fresh machine before onboarding wizard exists.
**Delivers:** Robust setup.sh with version checks, fail-fast on missing deps, `--check-deps-only` flag
**Addresses:** Pitfall 7 (setup fails on fresh machine), table stakes (dependency checker)
**Avoids:** First-run failure that causes immediate abandonment

#### Phase 3: Onboarding Wizard (Core Flow)
**Rationale:** Depends on setup.sh working. Produces user-profile.yaml that all M2 tools need.
**Delivers:** Interactive CLI wizard with questionary, input validation, config file generation (YAML, .env, MCP.json)
**Uses:** questionary (only new dependency), existing progress_persistence.py, existing TypeScript scaffold
**Addresses:** Table stakes (interactive prompts, validation, config generation, progress indicator)

#### Phase 4: Onboarding Polish & Hook Refactoring
**Rationale:** Save/resume and hook ports are differentiators that elevate quality but do not block M2.
**Delivers:** Ctrl+C save/resume, idempotent re-run, Bun hook ports with test assertions, README with fork workflow
**Addresses:** Differentiators (save/resume, Bun hooks), table stakes (idempotent re-run, README, help text)
**Avoids:** Pitfall 13 (long onboarding without value) by making onboarding optional -- tools work without it

### Milestone 2: Hedging & Portfolio Protection

#### Phase 5: Config Loader & Shared Hedging Models
**Rationale:** All 4 hedging tools depend on ConfigLoader and shared Pydantic models. Build the foundation first.
**Delivers:** config_loader.py, hedging_inputs.py, total_return_inputs.py, HedgeConfig model
**Implements:** Architecture Pattern 1 (Config Loader), Pattern 2 (Hedging Models conventions)
**Avoids:** Anti-Pattern 2 (each CLI parsing YAML directly)

#### Phase 6: Total Return Calculator
**Rationale:** Simplest of the 4 tools, no dependency on options infrastructure. Good "warm-up" that delivers standalone value.
**Delivers:** Total return CLI with price+dividend separation, multi-ticker comparison, DRIP modeling
**Addresses:** Table stakes (return separation, multi-ticker), differentiator (DRIP modeling)
**Avoids:** Pitfall 6 (yfinance dividend gaps) with data quality indicators and cross-validation

#### Phase 7: Rolling Tracker & Hedge Sizer
**Rationale:** These two tools share the most infrastructure (options.py, options chain scanner, market_data.py). Build together.
**Delivers:** Rolling tracker with status+DTE alerts+roll suggestions, hedge sizer with contract sizing+budget validation
**Uses:** Existing OptionsCalculator, options_chain_cli scan_chain(), market_data.py
**Implements:** Architecture Pattern 3 (subcommand pattern for tracker)
**Avoids:** Pitfall 4 (Black-Scholes on American options) with documented limitations, Pitfall 5 (accuracy) with known-answer tests

#### Phase 8: SQQQ vs Puts Comparison (M2 Drop 2)
**Rationale:** Highest complexity, highest risk feature. Isolated to its own phase so it does not block other tools.
**Delivers:** Hedge comparison CLI with daily-compounded SQQQ modeling, IV expansion, breakeven analysis
**Addresses:** Differentiator (SQQQ vs puts with decay -- genuinely novel in CLI tools)
**Avoids:** Pitfall 3 (simple multiplication) with day-by-day simulation, Pitfall 12 (IV expansion) with VIX-SPX regression

### Milestone 3: Interactive Knowledge Explorer

#### Phase 9: Template Engine & Dividend Topic Port
**Rationale:** Every M3 feature depends on the template engine. Extract from prototype first.
**Delivers:** Bun build pipeline (JSON + template -> HTML), topic JSON schema, dividend topic ported from prototype
**Uses:** Cytoscape.js via CDN, existing dividend-strategy-explorer.html as source
**Avoids:** Pitfall 10 (unmaintainable single file) with modular source + bundled output

#### Phase 10: Self-Assessment, Persistence & Additional Topics
**Rationale:** Core interaction loop (assess, persist, generate prompt) must work before adding advanced features.
**Delivers:** Click-to-cycle knowledge states, localStorage with JSON export fallback, copy-to-clipboard prompts, 2 new topics (options-greeks, risk-management)
**Avoids:** Pitfall 9 (localStorage eviction) with try/catch + JSON export, Pitfall 8 (mobile Safari) with pointer events API

#### Phase 11: Maya Integration, Mobile Polish & CLI Launcher
**Rationale:** Integration features that tie the explorer back into the Finance Guru ecosystem.
**Delivers:** Maya learner profile export, learning mode selector, `fin-guru explore <topic>` CLI, mobile/touch polish
**Addresses:** Differentiators (Maya integration, learning modes, CLI launcher)
**Avoids:** Pitfall 15 (accessibility) with ARIA labels and list view fallback

### Phase Ordering Rationale

- **M1 before M2** is non-negotiable: hedging tools need user-profile.yaml with a stable schema, and the public release scrub must happen before any external visibility.
- **Phase 5 (shared models) before Phases 6-8** prevents duplicated config parsing code across 4 CLIs and establishes the HedgeConfig contract early.
- **Phase 6 (total return) before Phase 7 (tracker/sizer)** because total return has no dependency on the options infrastructure and serves as a complexity ramp.
- **Phase 8 (SQQQ comparison) isolated** because it contains the project's highest-risk calculation (path-dependent decay modeling) and should not block the other three tools.
- **M3 can start Phase 9 in parallel with M2 Phase 7** because the explorer has zero runtime dependency on Python code. However, M3 content benefits from M2 knowledge files.
- **Phase 9 (template engine) must precede Phases 10-11** because all explorer features depend on the build pipeline existing.

### Research Flags

**Phases likely needing `/gsd:research-phase` during planning:**
- **Phase 1 (Git History Scrub):** Needs research into git filter-repo vs BFG Repo Cleaner for this specific repo's history. What exactly was committed? How many commits need scrubbing?
- **Phase 8 (SQQQ vs Puts):** Path-dependent daily compounding with volatility drag is non-trivial. Needs research into ProShares prospectus return tables for validation targets, and historical VIX-SPX regression parameters for IV expansion modeling.
- **Phase 9 (Template Engine):** Needs research into Cytoscape.js configuration for the specific graph layouts, interaction patterns, and WebGL vs Canvas decision criteria.

**Phases with standard patterns (skip research-phase):**
- **Phase 2 (Setup Automation):** Standard bash scripting with version checks. Well-documented patterns.
- **Phase 3 (Onboarding Wizard):** questionary library is well-documented with clear API. Existing TypeScript scaffold provides the blueprint.
- **Phase 5 (Config Loader):** Standard Pydantic model + YAML parsing. Established pattern in codebase.
- **Phase 6 (Total Return):** Standard financial calculation. yfinance API is well-known. Existing 3-layer pattern applies directly.

## Risk Register

| Rank | Risk | Severity | Likelihood | Milestone | Mitigation | Owner |
|------|------|----------|------------|-----------|------------|-------|
| 1 | Financial PII exposed in git history when repo goes public | CRITICAL | HIGH | M1 | Run git filter-repo, rotate all keys, scan with gitleaks before public | Phase 1 |
| 2 | Hardcoded PII beyond "Ossie" survives scrub | CRITICAL | HIGH | M1 | Expand scrub test to account numbers, LLC names, employers, spreadsheet IDs | Phase 1 |
| 3 | SQQQ modeled with simple multiplication, not daily compounding | CRITICAL | MEDIUM | M2 | Day-by-day simulation, volatility drag formula, historical validation | Phase 8 |
| 4 | Black-Scholes misprices American-style puts during crash | CRITICAL | MEDIUM | M2 | Document limitation, add intrinsic value floor, disclaimers | Phase 7 |
| 5 | Financial calculator output used without validation | CRITICAL | MEDIUM | M2 | Known-answer tests, freshness indicators, confidence bands | Phases 6-8 |
| 6 | yfinance dividend data gaps corrupt total return | HIGH | MEDIUM | M2 | Data quality indicator, user-supplied CSV override, cross-validation | Phase 6 |
| 7 | setup.sh fails on fresh machine | HIGH | HIGH | M1 | Version checks, bare Docker test, fail-fast with install instructions | Phase 2 |
| 8 | user-profile.yaml schema coupling across 3 components | HIGH | MEDIUM | M1-M2 | Shared Pydantic schema model, validate at both write and read boundaries | Phase 3, 5 |
| 9 | Canvas graph broken on mobile Safari | HIGH | MEDIUM | M3 | Pointer events API, devicePixelRatio handling, test on real iPhone early | Phase 10 |
| 10 | localStorage eviction loses assessment progress | HIGH | MEDIUM | M3 | try/catch, JSON export/import, save-status timestamps | Phase 10 |
| 11 | Single-file HTML unmaintainable beyond 2000 lines | HIGH | HIGH | M3 | Develop modular, bundle to single file at build time | Phase 9 |

## Dependency Map

```
MILESTONE 1 (Public Release)
  Phase 1: Git Scrub ──────────> Phase 2: Setup Automation
                                      |
                                      v
                                Phase 3: Onboarding Wizard
                                      |
                                      v
                                Phase 4: Polish & Hooks
                                      |
                                      | PRODUCES: user-profile.yaml (stable schema)
                                      |
MILESTONE 2 (Hedging)                 v
  Phase 5: Config Loader + Models <───┘
       |
       +───────> Phase 6: Total Return (independent)
       |
       +───────> Phase 7: Rolling Tracker + Hedge Sizer
       |              |
       |              | (options.py, options_chain scanner)
       |              v
       +───────> Phase 8: SQQQ vs Puts (isolated, highest risk)

MILESTONE 3 (Explorer)          [can start Phase 9 in parallel with M2 Phase 7]
  Phase 9: Template Engine <────────── existing prototype
       |
       v
  Phase 10: Assessment + Topics ──> Phase 11: Maya Integration + Polish
```

**Critical path:** Phase 1 -> Phase 2 -> Phase 3 -> Phase 5 -> Phase 7 (longest dependency chain)
**Parallel opportunities:** Phase 6 || Phase 7 (after Phase 5), Phase 9 || Phase 7 (different runtimes)

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Only 1 new Python dep (questionary, verified on PyPI). All M2 capabilities confirmed in existing codebase via source inspection. Cytoscape.js version and CDN verified. |
| Features | MEDIUM-HIGH | Table stakes well-sourced from clig.dev, professional options tools, and existing prototype. SQQQ decay modeling complexity may be underestimated. |
| Architecture | HIGH | Based entirely on codebase inspection, not external sources. All integration points verified against actual source files. 3-layer pattern is proven. |
| Pitfalls | HIGH | Critical pitfalls verified with codebase evidence (specific file paths, line numbers). External research backed by multiple sources (GitGuardian, SSRN, yfinance GitHub issues). |

**Overall confidence:** HIGH

### Gaps to Address

- **SQQQ daily compounding validation:** Need historical SQQQ vs QQQ data to calibrate volatility drag parameters and validate the simulation model against reality. Address during Phase 8 planning.
- **user-profile.yaml schema versioning:** No schema version field exists today. Need to add one during M1 onboarding work (Phase 3) so future tools can detect profile version. Address during Phase 3 planning.
- **American option pricing improvement path:** The intrinsic value floor is a minimum fix. Whether to implement Barone-Adesi-Whaley or binomial tree should be evaluated during Phase 7 planning based on actual pricing error magnitude.
- **Cross-topic concept linking feasibility:** FEATURES.md flags this as HIGH complexity. The localStorage sync across separate HTML files is architecturally unclear. Defer to post-M3 or research during Phase 10.
- **Hook refactoring scope:** Three different runtimes (.sh, .ts, .cjs) need consolidation to Bun-only. Exact migration path needs Phase 4 planning.
- **Options chain scanner integration:** rolling_tracker needs scan_chain() from options_chain_cli.py, but that function has stderr side effects. Decision: pragmatic approach (accept stderr) vs clean extraction. Resolve during Phase 7 planning.

## Open Questions

1. **What is the git history exposure?** Has user-profile.yaml, .mcp.json, or any CSV with account numbers ever been committed? This determines the scope of Phase 1.
2. **Should M2 tools work without user-profile.yaml?** FEATURES.md suggests onboarding should be optional, but the config_loader design assumes the file exists. Need a graceful fallback with CLI-flag-only operation.
3. **What is the target audience size for M3 explorer?** If primarily personal use, mobile Safari polish (Phase 10) is lower priority than if it will be shared/embedded.
4. **Should the SQQQ comparison show the approximate nature prominently or should it be suppressed until accuracy is validated?** The FEATURES.md anti-feature of "precise SQQQ decay modeling" suggests approximation, but the tool still needs to be useful.
5. **How many topics are realistic for M3 initial release?** Research suggests 3 minimum (dividend, options-greeks, risk-management). Content curation for 5 topics is a significant effort that may extend M3 timeline.

## Sources

### Primary (HIGH confidence)
- Existing codebase: `src/analysis/options.py`, `src/models/options_inputs.py`, `src/utils/progress_persistence.py`, `scripts/onboarding/index.ts`, `.claude/hooks/load-fin-core-config.ts`
- PyPI questionary 2.1.1: https://pypi.org/project/questionary/
- Cytoscape.js 3.33.0: https://blog.js.cytoscape.org/
- GitGuardian State of Secrets Sprawl 2025: 23.8M secrets leaked, 70% from 2022 still active
- yfinance GitHub issues #930, #1273, #2070: documented dividend data reliability problems

### Secondary (MEDIUM confidence)
- SSRN 5119860 (Wang 2025): Multi-day return properties of leveraged ETFs
- clig.dev: Command Line Interface Guidelines (CLI onboarding best practices)
- Memgraph graph viz benchmarks: Cytoscape.js vs vis-network vs Sigma.js performance comparison
- MDN Storage Quotas: localStorage limits and browser eviction policies

### Tertiary (LOW confidence)
- "Fifty problems with standard web APIs in 2025" (zerotrickpony.com): Cross-browser Canvas issues
- OpenClaw onboarding wizard: Single reference implementation for CLI onboarding patterns
- Irec metacognitive scaffolding paper (arxiv 2506.20156): Self-regulated learning system design

---
*Research completed: 2026-02-02*
*Ready for roadmap: yes*
