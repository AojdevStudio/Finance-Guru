# Roadmap: Finance Guru v3

## Overview

Transform Finance Guru from a single-user private system into a distributable financial analysis toolkit across three milestones: public release infrastructure (git scrub, setup automation, onboarding wizard), hedging and portfolio protection CLI tools (config loader, total return, rolling tracker, hedge sizer, SQQQ comparison), and an interactive knowledge explorer (template engine, self-assessment, Maya integration). Eleven phases derived from 63 v1 requirements, ordered by the dependency chain: onboarding produces config files that hedging tools consume, and the explorer builds on stable schemas.

## Milestones

- **M1: Public Release & Onboarding** - Phases 1-4
- **M2: Hedging & Portfolio Protection** - Phases 5-8
- **M3: Interactive Knowledge Explorer** - Phases 9-11

## Git & PR Strategy

Phase 1 rewrites git history (`git filter-repo`), so it must land directly on `main`. All subsequent work uses feature branches with one PR per milestone.

| Scope | Branch | PR | Lands On |
|-------|--------|-----|----------|
| Phase 1: Git Scrub | `main` (direct) | No PR — force push after history rewrite | `main` |
| Phases 2-4: M1 Onboarding | `feat/m1-onboarding` | PR #1 — created at Phase 2 start | `main` |
| Phases 5-8: M2 Hedging | `feat/m2-hedging` | PR #2 — created at Phase 5 start | `main` |
| Phases 9-11: M3 Explorer | `feat/m3-explorer` | PR #3 — created at Phase 9 start | `main` |

**Branch lifecycle per milestone:**
1. At first phase of milestone: `git checkout -b feat/m<N>-<name>`
2. Create draft PR immediately (tracks progress)
3. All phases within the milestone commit to this branch
4. At last phase completion: mark PR ready for review, merge to `main`

**Phase 1 is special:** It operates directly on `main` because `git filter-repo` rewrites the entire repository history. A PR is not possible — the rewritten history requires a force push.

## Phases

- [ ] **Phase 1: Git History Scrub & Security Foundation** - Remove all PII from git history and prevent future leaks
- [ ] **Phase 2: Setup Automation & Dependency Checking** - First-run setup script that works on any fresh machine
- [ ] **Phase 3: Onboarding Wizard** - Interactive CLI that collects financial profile and generates config files
- [ ] **Phase 4: Onboarding Polish & Hook Refactoring** - Save/resume, regression testing, and Bun hook ports
- [ ] **Phase 5: Config Loader & Shared Hedging Models** - Foundation layer all four hedging CLIs depend on
- [ ] **Phase 6: Total Return Calculator** - Price + dividend return CLI with DRIP modeling
- [ ] **Phase 7: Rolling Tracker & Hedge Sizer** - Options position management and contract sizing CLIs
- [ ] **Phase 8: SQQQ vs Puts Comparison** - Hedge strategy comparison with daily-compounded decay modeling
- [ ] **Phase 9: Template Engine & Dividend Topic Port** - Build pipeline that converts JSON + template into standalone HTML explorers
- [ ] **Phase 10: Self-Assessment, Persistence & Additional Topics** - Core interaction loop with localStorage and two new topics
- [ ] **Phase 11: Maya Integration, Mobile Polish & CLI Launcher** - Tie explorer back into Finance Guru ecosystem

## Dependency Map

```
MILESTONE 1 (Public Release)
  Phase 1: Git Scrub ---------> Phase 2: Setup Automation
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
  Phase 5: Config & Models <----------+
       |
       +--------> Phase 6: Total Return (independent after Phase 5)
       |
       +--------> Phase 7: Tracker & Sizer (independent after Phase 5)
       |               |
       |               | (options.py, options_chain scanner)
       |               v
       +--------> Phase 8: SQQQ vs Puts (isolated, highest risk)

MILESTONE 3 (Explorer)        [Phase 9 can start parallel with M2 Phase 7]
  Phase 9: Template Engine <-- existing prototype
       |
       v
  Phase 10: Assessment + Topics --> Phase 11: Maya Integration + Polish
```

**Critical path:** Phase 1 -> 2 -> 3 -> 5 -> 7 (longest dependency chain)

**Parallel opportunities:**
- Phase 6 and Phase 7 can run in parallel (both depend only on Phase 5)
- Phase 9 can start in parallel with Phase 7 (zero runtime dependency on Python code)
- Phase 6 and Phase 8 are independent (Phase 8 depends on Phase 5, not Phase 7)

## Research Flags

Phases that should run `/gsd:research-phase` before planning:

| Phase | Why | What to Research |
|-------|-----|------------------|
| 1 | Irreversible consequences if scrub is incomplete | git filter-repo vs BFG for this repo's history; exact PII exposure audit |
| 8 | Highest-risk calculation in the project | ProShares prospectus return tables for validation; VIX-SPX regression parameters; historical SQQQ vs QQQ calibration data |
| 9 | New build pipeline with unfamiliar library | Cytoscape.js configuration for graph layouts; WebGL vs Canvas decision; Bun build pipeline patterns |

Phases that can skip research (standard patterns):

| Phase | Why |
|-------|-----|
| 2 | Standard bash scripting with version checks |
| 3 | questionary is well-documented; existing TypeScript scaffold is the blueprint |
| 4 | 1:1 behavior port of existing hooks; Bun TypeScript is documented |
| 5 | Standard Pydantic model + YAML parsing; established codebase pattern |
| 6 | Standard financial calculation; yfinance API well-known; existing 3-layer pattern |
| 7 | Builds on existing options.py and options_chain_cli; known integration points |
| 10 | Standard browser APIs (localStorage, pointer events, clipboard) |
| 11 | Standard Python webbrowser.open(); Maya schema is defined |

## Phase Details

### Phase 1: Git History Scrub & Security Foundation

**Goal**: Repository is safe for public visibility with zero PII exposure risk
**Depends on**: Nothing (first phase, CRITICAL prerequisite)
**Milestone**: M1 - Public Release & Onboarding
**Branch**: `main` (direct — git filter-repo rewrites history, no PR possible)
**Requirements**: SEC-01, SEC-02, SEC-03, ONBD-14, ONBD-15
**Cross-cutting**: XC-06
**Research flag**: YES -- audit git history for exact PII exposure before scrubbing

**Success Criteria** (what must be TRUE):
  1. Running `git log --all -p | grep -iE "account|brokerage|Z057|net.worth|LLC"` returns zero matches across entire git history
  2. A pre-commit hook blocks any commit containing patterns matching known PII formats (account numbers, SSNs, API keys)
  3. `.gitignore` covers user-profile.yaml, .env, .onboarding-progress.json, fin-guru-private/, and CSV exports -- verified by CI grep test
  4. No file in the working tree contains hardcoded personal references (names, account numbers, LLC names, employer names, spreadsheet IDs)

**Plans**: 3 plans

Plans:
- [ ] 01-01-PLAN.md -- Working tree PII cleanup and .gitignore hardening (ONBD-14, ONBD-15)
- [ ] 01-02-PLAN.md -- PII expressions file and git-filter-repo history rewrite (SEC-01, XC-06)
- [ ] 01-03-PLAN.md -- Gitleaks pre-commit hook and CI PII check workflow (SEC-02, SEC-03)

---

### Phase 2: Setup Automation & Dependency Checking

**Goal**: A new user can run one command on a fresh machine and get a working environment
**Depends on**: Phase 1
**Milestone**: M1 - Public Release & Onboarding
**Branch**: `feat/m1-onboarding` (create branch + draft PR at phase start)
**Requirements**: ONBD-05, ONBD-06, SETUP-01, SETUP-02, SETUP-03

**Success Criteria** (what must be TRUE):
  1. Running `./setup.sh` on a machine with prerequisites installed completes without errors and creates the fin-guru-private/ directory structure
  2. Running `./setup.sh` on a machine missing Python 3.12+, uv, or Bun shows the exact install command for each missing dependency and exits with a non-zero code
  3. Running `./setup.sh --check-deps-only` performs a dry-run dependency check without creating files or starting onboarding
  4. Running `./setup.sh` a second time detects existing configuration and only prompts for missing fields (idempotent)

**Plans**: 2 plans

Plans:
- [ ] 02-01-PLAN.md -- Dependency checker with fail-fast behavior and --check-deps-only flag
- [ ] 02-02-PLAN.md -- Setup orchestration restructure with idempotent directory creation and config scaffolding

---

### Phase 3: Onboarding Wizard

**Goal**: A new user completes an interactive CLI session and has a fully personalized Finance Guru configuration
**Depends on**: Phase 2 (setup.sh must exist to orchestrate onboarding)
**Milestone**: M1 - Public Release & Onboarding
**Branch**: `feat/m1-onboarding` (continues on existing branch)
**Requirements**: ONBD-01, ONBD-02, ONBD-04, ONBD-07, ONBD-08, ONBD-09, ONBD-17
**Cross-cutting**: XC-01 (questionary is the only new dependency)

**Success Criteria** (what must be TRUE):
  1. User completes 8-section interactive onboarding and a valid user-profile.yaml is generated in fin-guru-private/ with their financial data
  2. Entering invalid input (non-numeric for dollar amounts, out-of-range percentages) shows a clear error and re-prompts up to 3 times, then offers a skip option
  3. CLAUDE.md is generated with the user's name and correct project-root path (no hardcoded "Ossie" or absolute paths)
  4. .env file is created with optional API keys (user can skip all keys and system still functions with yfinance)
  5. Finance Guru agents load the generated user-profile.yaml and address the user by their configured name

**Plans**: TBD

Plans:
- [ ] 03-01: TBD
- [ ] 03-02: TBD

---

### Phase 4: Onboarding Polish & Hook Refactoring

**Goal**: Onboarding is interruption-safe and all Claude hooks run as Bun TypeScript under 500ms
**Depends on**: Phase 3 (onboarding core must exist before adding save/resume)
**Milestone**: M1 - Public Release & Onboarding
**Branch**: `feat/m1-onboarding` (final phase — merge PR to main on completion)
**Requirements**: ONBD-03, ONBD-10, ONBD-11, ONBD-12, ONBD-13, ONBD-16

**Success Criteria** (what must be TRUE):
  1. Pressing Ctrl+C mid-onboarding saves progress to .onboarding-progress.json, and restarting onboarding resumes from the last incomplete section
  2. All 365+ existing pytest tests pass after onboarding and hook changes (zero regressions)
  3. All three hooks (load-fin-core-config, skill-activation-prompt, post-tool-use-tracker) run as Bun TypeScript and produce identical output to the original implementations
  4. Each hook completes execution in under 500ms (verified by test assertions)

**Plans**: TBD

Plans:
- [ ] 04-01: TBD
- [ ] 04-02: TBD

---

### Phase 5: Config Loader & Shared Hedging Models

**Goal**: All four hedging CLI tools have a shared foundation of validated Pydantic models and config access
**Depends on**: Phase 3 (user-profile.yaml schema must be stable)
**Milestone**: M2 - Hedging & Portfolio Protection
**Branch**: `feat/m2-hedging` (create branch + draft PR at phase start)
**Requirements**: HEDG-01, HEDG-02, HEDG-03, HEDG-08, CFG-01, CFG-02, CFG-03
**Cross-cutting**: XC-02, XC-03

**Success Criteria** (what must be TRUE):
  1. `config_loader.py` reads user-profile.yaml and returns a validated HedgeConfig with hedging preferences (budget, roll window, underlying weights)
  2. CLI flags override any value from the config file (e.g., `--budget 800` overrides the YAML budget of $500)
  3. Running any hedging CLI without user-profile.yaml works using only CLI flags (graceful fallback, no crash)
  4. fin-guru-private/hedging/ directory exists with positions.yaml, roll-history.yaml, and budget-tracker.yaml templates
  5. All shared Pydantic models (HedgePosition, RollSuggestion, HedgeSizeRequest, TotalReturnInput, DividendRecord, TickerReturn) pass validation tests with known inputs

**Plans**: TBD

Plans:
- [ ] 05-01: TBD

---

### Phase 6: Total Return Calculator

**Goal**: User can compare total returns (price + dividends) across tickers with DRIP modeling
**Depends on**: Phase 5 (shared models and config loader)
**Milestone**: M2 - Hedging & Portfolio Protection
**Branch**: `feat/m2-hedging` (continues on existing branch)
**Requirements**: HEDG-07, TR-01, TR-02, TR-03
**Cross-cutting**: STD-01, STD-02, STD-03, STD-04, XC-03, XC-04, XC-05
**HEDG-13 (incremental)**: Tests for total return components

**Success Criteria** (what must be TRUE):
  1. `uv run python src/analysis/total_return_cli.py SCHD --days 252` outputs three distinct numbers: price return, dividend return, and total return
  2. `uv run python src/analysis/total_return_cli.py SCHD JEPI VYM --days 252` compares all three tickers side-by-side
  3. DRIP mode shows growing share count over time as dividends are reinvested at ex-date close prices
  4. When yfinance dividend data has gaps, the output includes a data quality warning (not silent wrong numbers)
  5. `--output json` produces structured JSON and `--help` shows complete usage examples

**Plans**: TBD

Plans:
- [ ] 06-01: TBD

---

### Phase 7: Rolling Tracker & Hedge Sizer

**Goal**: User can monitor options positions, get roll alerts, and size new hedge contracts against their portfolio
**Depends on**: Phase 5 (shared models and config loader)
**Milestone**: M2 - Hedging & Portfolio Protection
**Branch**: `feat/m2-hedging` (continues on existing branch)
**Requirements**: HEDG-04, HEDG-05, RT-01, RT-02, RT-03, HS-01, HS-02, HS-03, BS-01, HEDG-09, HEDG-10
**Cross-cutting**: STD-01, STD-02, STD-03, STD-04, XC-03, XC-04, XC-05
**HEDG-13 (incremental)**: Tests for tracker and sizer components

**Success Criteria** (what must be TRUE):
  1. `uv run python src/analysis/rolling_tracker_cli.py status` displays current hedge positions with P&L, DTE, and current value from positions.yaml
  2. `uv run python src/analysis/rolling_tracker_cli.py suggest-roll` identifies positions within the DTE roll window (default 7 days) and scans the options chain for replacement candidates
  3. `uv run python src/analysis/hedge_sizer_cli.py --portfolio 200000 --underlyings QQQ,SPY` outputs contract counts (1 per $50k) with budget utilization percentage
  4. Knowledge base files (hedging-strategies.md, options-insurance-framework.md) exist and Strategy Advisor, Teaching Specialist, and Quant Analyst agent definitions reference them
  5. Black-Scholes limitation on American-style options is documented with intrinsic value floor applied to put pricing

**Plans**: TBD

Plans:
- [ ] 07-01: TBD
- [ ] 07-02: TBD

---

### Phase 8: SQQQ vs Puts Comparison

**Goal**: User can compare SQQQ hedging vs protective puts with accurate decay modeling and breakeven analysis
**Depends on**: Phase 5 (shared models); benefits from Phase 7 (options infrastructure) but not strictly required
**Milestone**: M2 - Hedging & Portfolio Protection
**Branch**: `feat/m2-hedging` (final phase — merge PR to main on completion)
**Requirements**: HEDG-06, HC-01, HC-02, HC-03, HC-04, HC-05, HEDG-11, HEDG-12
**Cross-cutting**: STD-01, STD-02, STD-03, STD-04, XC-03, XC-04, XC-05
**HEDG-13 (incremental)**: Tests for comparison components
**Research flag**: YES -- daily compounding validation, VIX-SPX regression parameters

**Success Criteria** (what must be TRUE):
  1. `uv run python src/analysis/hedge_comparison_cli.py --scenarios -5,-10,-20,-40` outputs SQQQ vs puts payoff for each market drop scenario
  2. SQQQ simulation uses day-by-day compounding with volatility drag (NOT simple -3x multiplication) and results are validated against historical SQQQ data
  3. Breakeven analysis shows at what percentage drop each hedge strategy becomes profitable
  4. IV expansion estimate uses VIX-SPX regression to model put repricing during crashes
  5. All 4 hedging CLI tools pass integration test: `uv run python src/analysis/<tool>_cli.py --help` works for total_return, rolling_tracker, hedge_sizer, and hedge_comparison
  6. Architecture diagram (.mmd) shows all new M2 components and their data flow

**Plans**: TBD

Plans:
- [ ] 08-01: TBD
- [ ] 08-02: TBD

---

### Phase 9: Template Engine & Dividend Topic Port

**Goal**: A build pipeline exists that converts topic JSON into standalone interactive HTML knowledge explorers
**Depends on**: Phase 3 (stable user-profile.yaml schema); can start parallel with Phase 7
**Milestone**: M3 - Interactive Knowledge Explorer
**Branch**: `feat/m3-explorer` (create branch + draft PR at phase start)
**Requirements**: EXPL-01, EXPL-02, EXPL-03, EXPL-04
**Research flag**: YES -- Cytoscape.js configuration, build pipeline patterns

**Success Criteria** (what must be TRUE):
  1. Running the Bun build script with the dividend topic JSON produces a single standalone HTML file with zero external dependencies (Cytoscape.js bundled or via CDN)
  2. The generated dividend explorer has feature parity with the existing prototype (playgrounds/dividend-strategy-explorer.html) -- same concepts, same graph layout, same interactions
  3. Topic JSON schema is defined and validated -- a malformed JSON file produces a clear build error, not a broken HTML file
  4. The template engine is reusable: changing only the topic JSON file produces a different explorer with different concepts

**Plans**: TBD

Plans:
- [ ] 09-01: TBD

---

### Phase 10: Self-Assessment, Persistence & Additional Topics

**Goal**: Users can self-assess their knowledge, persist progress across sessions, and explore options-greeks and risk-management topics
**Depends on**: Phase 9 (template engine must exist)
**Milestone**: M3 - Interactive Knowledge Explorer
**Branch**: `feat/m3-explorer` (continues on existing branch)
**Requirements**: EXPL-05, EXPL-06, EXPL-08, EXPL-09a, EXPL-09b, EXPL-15, EXPL-16

**Success Criteria** (what must be TRUE):
  1. Clicking a concept node cycles through knowledge states (unknown -> familiar -> confident -> mastered) and the state persists after page refresh via localStorage
  2. Learning mode selector (guided/standard/yolo) changes the complexity of generated prompts
  3. "Copy prompt" button works on Chrome, Safari, and Firefox (navigator.clipboard.writeText with fallback)
  4. Options-greeks and risk-management topic explorers are generated and functional
  5. All explorer pages load in under 1 second with zero external runtime dependencies

**Plans**: TBD

Plans:
- [ ] 10-01: TBD
- [ ] 10-02: TBD

---

### Phase 11: Maya Integration, Mobile Polish & CLI Launcher

**Goal**: Explorer connects back into Finance Guru through Maya learner profiles and a CLI launcher
**Depends on**: Phase 10 (assessment and persistence must work before exporting profiles)
**Milestone**: M3 - Interactive Knowledge Explorer
**Branch**: `feat/m3-explorer` (final phase — merge PR to main on completion)
**Requirements**: EXPL-07, EXPL-10, EXPL-12, EXPL-13

**Success Criteria** (what must be TRUE):
  1. Clicking "Export Profile" downloads a JSON file matching Maya's learner_profile schema with all self-assessed knowledge states
  2. `uv run python src/tools/fin_guru_cli.py explore dividend-strategy` opens the dividend explorer in the default browser
  3. Maya agent reads the exported learner profile at session start (if the file exists in fin-guru/data/) and references the user's knowledge levels
  4. Topic selector landing page (index.html) shows all available explorers as a card grid with completion badges

**Plans**: TBD

Plans:
- [ ] 11-01: TBD

---

## Coverage

### Requirement-to-Phase Mapping

**Milestone 1: Public Release & Onboarding (23 requirements)**

| Requirement | Phase | Category |
|-------------|-------|----------|
| SEC-01 | 1 | Security |
| SEC-02 | 1 | Security |
| SEC-03 | 1 | Security |
| ONBD-14 | 1 | Security |
| ONBD-15 | 1 | Security |
| ONBD-05 | 2 | Setup |
| ONBD-06 | 2 | Setup |
| SETUP-01 | 2 | Setup |
| SETUP-02 | 2 | Setup |
| SETUP-03 | 2 | Setup |
| ONBD-01 | 3 | Onboarding |
| ONBD-02 | 3 | Onboarding |
| ONBD-04 | 3 | Onboarding |
| ONBD-07 | 3 | Onboarding |
| ONBD-08 | 3 | Onboarding |
| ONBD-09 | 3 | Onboarding |
| ONBD-17 | 3 | Onboarding |
| ONBD-03 | 4 | Polish |
| ONBD-10 | 4 | Hooks |
| ONBD-11 | 4 | Hooks |
| ONBD-12 | 4 | Hooks |
| ONBD-13 | 4 | Hooks |
| ONBD-16 | 4 | Testing |

**Milestone 2: Hedging & Portfolio Protection (29 requirements)**

| Requirement | Phase | Category |
|-------------|-------|----------|
| HEDG-01 | 5 | Config |
| HEDG-02 | 5 | Models |
| HEDG-03 | 5 | Models |
| HEDG-08 | 5 | Data |
| CFG-01 | 5 | Config |
| CFG-02 | 5 | Config |
| CFG-03 | 5 | Config |
| HEDG-07 | 6 | CLI |
| TR-01 | 6 | CLI |
| TR-02 | 6 | CLI |
| TR-03 | 6 | CLI |
| HEDG-04 | 7 | CLI |
| HEDG-05 | 7 | CLI |
| RT-01 | 7 | CLI |
| RT-02 | 7 | CLI |
| RT-03 | 7 | CLI |
| HS-01 | 7 | CLI |
| HS-02 | 7 | CLI |
| HS-03 | 7 | CLI |
| BS-01 | 7 | CLI |
| HEDG-09 | 7 | Knowledge |
| HEDG-10 | 7 | Agents |
| HEDG-06 | 8 | CLI |
| HC-01 | 8 | CLI |
| HC-02 | 8 | CLI |
| HC-03 | 8 | CLI |
| HC-04 | 8 | CLI |
| HC-05 | 8 | CLI |
| HEDG-11 | 8 | Docs |
| HEDG-12 | 8 | Integration |

**Milestone 3: Interactive Knowledge Explorer (15 requirements)**

| Requirement | Phase | Category |
|-------------|-------|----------|
| EXPL-01 | 9 | Engine |
| EXPL-02 | 9 | Schema |
| EXPL-03 | 9 | Engine |
| EXPL-04 | 9 | Content |
| EXPL-05 | 10 | Persistence |
| EXPL-06 | 10 | Interaction |
| EXPL-08 | 10 | Mobile |
| EXPL-09a | 10 | Content |
| EXPL-09b | 10 | Content |
| EXPL-15 | 10 | Browser |
| EXPL-16 | 10 | Performance |
| EXPL-07 | 11 | Integration |
| EXPL-10 | 11 | UI |
| EXPL-12 | 11 | CLI |
| EXPL-13 | 11 | Integration |

**Cross-Cutting Requirements (apply incrementally across phases)**

| Requirement | Applies To | Category |
|-------------|-----------|----------|
| XC-01 | All phases | Dependencies |
| XC-02 | Phases 5-11 | Architecture |
| XC-03 | Phases 5-8 | Architecture |
| XC-04 | All phases | Testing |
| XC-05 | Phases 6-8 | Compliance |
| XC-06 | Phase 1 (primary), all phases | Security |
| STD-01 | Phases 6-8 | CLI Pattern |
| STD-02 | Phases 6-8 | Compliance |
| STD-03 | Phases 6-8 | CLI Pattern |
| STD-04 | Phases 6-8 | Testing |
| HEDG-13 | Phases 6-8 | Testing |

**Coverage summary:** 67/67 v1 requirements mapped (23 M1 + 29 M2 + 15 M3) + 11 cross-cutting. No orphans.

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8 -> 9 -> 10 -> 11
(With parallel opportunities noted in Dependency Map above)

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Git Scrub & Security | M1 | 0/3 | Planned | - |
| 2. Setup Automation | M1 | 0/2 | Planned | - |
| 3. Onboarding Wizard | M1 | 0/TBD | Not started | - |
| 4. Polish & Hooks | M1 | 0/TBD | Not started | - |
| 5. Config & Models | M2 | 0/TBD | Not started | - |
| 6. Total Return | M2 | 0/TBD | Not started | - |
| 7. Tracker & Sizer | M2 | 0/TBD | Not started | - |
| 8. SQQQ vs Puts | M2 | 0/TBD | Not started | - |
| 9. Template Engine | M3 | 0/TBD | Not started | - |
| 10. Assessment & Topics | M3 | 0/TBD | Not started | - |
| 11. Maya Integration | M3 | 0/TBD | Not started | - |

---
*Created: 2026-02-02*
*Depth: comprehensive (11 phases across 3 milestones)*
