# Feature Landscape

**Domain:** CLI financial analysis toolkit (public release), options hedging tools, interactive knowledge explorer
**Researched:** 2026-02-02
**Overall Confidence:** MEDIUM-HIGH (verified against existing codebase, spec files, and ecosystem research)

---

## Milestone 1: CLI Onboarding & Public Release

### Table Stakes

Features users expect. Missing = product feels incomplete or abandoned at first contact.

| Feature | Why Expected | Complexity | Milestone | Dependencies | Notes |
|---------|--------------|------------|-----------|--------------|-------|
| **Dependency checker at startup** | Every serious CLI tool verifies prerequisites (uv, bun, Python 3.12+) before proceeding. Failing silently or crashing on missing deps = immediate abandonment. | Low | M1 | None | setup.sh checks `command -v`. Show install commands on failure. clig.dev guidelines: "If your command has prerequisites, tell the user what they are." |
| **Interactive prompt-driven onboarding** | Standard for developer tools (npm init, create-react-app, cookiecutter). Users expect guided Q&A, not reading a YAML schema. | Med | M1 | Dependency checker | Use questionary or InquirerPy for prompts. argparse is wrong tool for interactive Q&A. Existing progress_persistence.py has OnboardingState model ready. |
| **Input validation with retry** | Every CLI wizard validates input inline and re-prompts on error. Crashing on "abc" for a dollar amount is unacceptable. | Med | M1 | Prompt library | Pydantic already in stack. Validators for dollar amounts, percentages, enums, dates. Retry 3x then offer to skip. |
| **Progress indicator** | Users need to know where they are in a multi-step process. "Section 3 of 8" + progress bar is minimum. | Low | M1 | Prompt library | rich library (already common with Python CLIs) for progress bars and styled output. |
| **Configuration file generation** | Output must be usable config files (YAML, .env, JSON), not just console output. Users expect "answers in, config out." | Med | M1 | Validation | user-profile.yaml, .env, MCP.json generation. YAML generator already exists (yaml_generator.py). |
| **Idempotent re-run** | Standard for infrastructure tools (terraform, ansible). Re-running setup must not destroy existing config. "Update missing fields only" is the expected pattern. | Med | M1 | Config generation | Detect existing files, diff against template, prompt for missing only. Progress persistence module already started. |
| **.gitignore protection** | Any tool handling sensitive data (API keys, financial profiles) MUST gitignore those files. Leaking secrets to GitHub = liability. | Low | M1 | None | Already partially in place. Need to verify coverage: user-profile.yaml, .env, CSV exports, fin-guru-private/, .onboarding-progress.json. |
| **Clear README with setup instructions** | Open-source projects without clear "Getting Started" in the README get zero adoption. Fork model needs explicit documentation. | Low | M1 | All M1 features | Fork workflow diagram, prerequisites, time estimates, example terminal output. |
| **Helpful error messages** | CLI Guidelines (clig.dev): "If your program fails for an expected reason, show the user what went wrong and how to fix it." | Low | M1 | None | Every exception should include: what happened, why, how to fix. |
| **--help on all commands** | Basic CLI hygiene. argparse provides this, but help text must be complete with examples. | Low | M1 | None | Already established pattern in all existing CLIs. |

### Differentiators

Features that set product apart. Not expected, but valued.

| Feature | Value Proposition | Complexity | Milestone | Dependencies | Notes |
|---------|-------------------|------------|-----------|--------------|-------|
| **Save/resume onboarding (Ctrl+C safe)** | Most CLI wizards lose all progress on interrupt. Resumable onboarding from checkpoint file is rare and shows polish. Finance profile is 15+ min, so this matters. | Med | M1 | Progress persistence | progress_persistence.py already has OnboardingState model with sections, timestamps, data dict. Signal handler on SIGINT saves state. |
| **Contextual explanations per question** | "This helps calculate your investment capacity" after each answer. Most wizards just ask questions; this one teaches while onboarding. | Low | M1 | Prompt system | Maps to Finance Guru's teaching philosophy. Each question paired with a 1-line "why this matters." |
| **MCP server auto-configuration** | No other open-source financial tool auto-configures Claude Code MCP servers. This is unique to the Finance Guru + Claude Code ecosystem. | Med | M1 | .env setup | Template-based: backup existing, generate fresh, show merge instructions. Novel feature in ecosystem. |
| **Bun TypeScript hooks with performance assertions** | Most Claude Code projects use bash hooks. Bun hooks with <500ms test assertions show engineering discipline. | Med-High | M1 | Bun installed | Clean break from bash. 3 hooks to port: load-fin-core-config, skill-activation-prompt, post-tool-use-tracker. |
| **`fin-guru doctor` diagnostic command** | A "doctor" command that checks: deps installed, config valid, hooks working, data files present, tests passing. Standard in polished CLIs (homebrew doctor, flutter doctor, OpenClaw doctor). | Med | M1 | All M1 | Not in current spec but HIGH value. Single command to debug setup issues. Consider adding. |

### Anti-Features (M1)

Features to explicitly NOT build. Common mistakes in this domain.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Web-based onboarding UI** | Adds server dependency, doubles implementation surface, target audience (developers) is comfortable with CLI. Time cost: months vs weeks. | CLI with rich formatting (rich library). Revisit web UI based on adoption data. |
| **Automated GitHub fork creation** | GitHub API/CLI dependency, auth complexity, fails in enterprise/gitlab environments. | Document fork workflow clearly with screenshots. Users fork manually. |
| **Smart MCP.json merge** | Parsing and merging user configs risks breaking existing setups. Failure mode is silent corruption. | Backup + fresh template + merge instructions. Explicit > clever. |
| **Multi-language i18n** | Massive ongoing maintenance burden for a v3 release. English-speaking developer audience. | English only. Add i18n infrastructure (string extraction) if demand emerges. |
| **Encryption of user-profile.yaml** | Adds password management, key derivation, and recovery complexity. Local-only system with filesystem permissions is appropriate. | chmod 600 on sensitive files. Document in security section. |
| **Telemetry or analytics** | Destroys trust with privacy-conscious financial tool users. Even opt-in telemetry is a red flag for financial data tools. | No tracking whatsoever. Prominently state "no telemetry" in README. |
| **Auto-install of dependencies** | Silently running `curl | sh` or `pip install` during setup is a security anti-pattern. Users should control what gets installed. | Check for deps, show exact install commands, exit. Let user install. |

---

## Milestone 2: Hedging & Portfolio Protection Tools

### Table Stakes

| Feature | Why Expected | Complexity | Milestone | Dependencies | Notes |
|---------|--------------|------------|-----------|--------------|-------|
| **Position status display** | Any position tracker must show: current positions, P&L, days to expiry, current value. This is the minimum viable feature of a rolling tracker. | Med | M2 | Config loader | Read from positions.yaml. Fetch current prices via yfinance. Calculate P&L vs entry. |
| **DTE-based roll alerts** | Professional options traders track DTE religiously. "Your QQQ put expires in 3 days" is the primary value of a roll tracker. Without alerts, users track expiry manually. | Med | M2 | Position status | Configurable threshold (default: 7 days). Research shows 5-7 DTE is standard roll window for protective puts. |
| **Contract sizing formula** | Sean's "1 contract per $50k" is a standard institutional sizing heuristic. The sizer must implement this as the baseline. Without it, users guess contract counts. | Low | M2 | HedgeConfig model | floor(portfolio_value / 50000). Split across underlyings. |
| **Budget validation** | Users set a monthly hedge budget ($500-600). The tool MUST compare calculated cost against budget and flag overages. Budget awareness is the entire point of a sizer. | Low | M2 | Contract sizing | Fetch current premiums, multiply by contracts, compare to budget. Show utilization %. |
| **Price + dividend return separation** | Sean specifically called this out: "You can't say it's down without counting dividends." Total return that separates price return from dividend return is the core requirement. | Med | M2 | yfinance dividend data | yfinance provides dividend history. Calculate: price-only return, dividend return, total return. Three separate numbers. |
| **Multi-ticker comparison** | Total return is meaningless in isolation. Users compare "YMAX vs SPY vs QQQ" to evaluate high-dividend ETFs. | Low-Med | M2 | Total return calc | Accept multiple tickers, output comparison table. Already pattern in correlation_cli. |
| **JSON + human-readable output** | Established pattern across all 8 existing CLIs. All new tools must support both output formats. | Low | M2 | None | `--output json` flag. model_dump_json(indent=2) for JSON. Formatted tables for text. |
| **Educational disclaimers** | Every existing Finance Guru tool includes educational-only disclaimers. New tools must maintain compliance. | Low | M2 | None | "This is educational analysis, not investment advice." Standard boilerplate. |

### Differentiators

| Feature | Value Proposition | Complexity | Milestone | Dependencies | Notes |
|---------|-------------------|------------|-----------|--------------|-------|
| **Roll suggestion engine** | Most roll trackers just alert. This one SUGGESTS replacement positions by calling the existing options chain scanner. "Your QQQ 480 put expires Friday. Suggested replacement: QQQ 475 put, March 15, $3.20." | High | M2 | Options chain scanner, DTE alerts | Integrates rolling_tracker with options_chain_cli logic. Finds puts in configured OTM range with target DTE. Unique feature -- no CLI tool does this. |
| **SQQQ vs puts scenario modeling with decay** | No open-source tool compares inverse ETFs against puts with proper decay accounting. SQQQ's daily rebalancing decay is widely misunderstood. Modeling both hedges side-by-side with real math is genuinely novel. | High | M2 | Black-Scholes (existing), SQQQ decay model | Path-dependent SQQQ decay is the hard part. Use historical volatility to estimate 30-day decay. IV expansion estimate for puts during crashes. Research confirms: "Leveraged ETFs suffer from path-dependent drift" -- modeling this accurately is a differentiator. |
| **Breakeven analysis per hedge type** | "At what % drop does each hedge become profitable?" is the question every hedger asks. Showing breakeven for SQQQ vs puts gives users the decision framework. | Med | M2 | Scenario modeling | Solve for the market drop % where hedge P&L = 0. Include in comparison output. |
| **DRIP modeling in total return** | Most total return calculators just add dividends to price. DRIP modeling (reinvesting dividends into fractional shares at ex-div date) shows compounding effect over time. | Med | M2 | Total return calc | Buy fractional shares at close price on ex-dividend date. Track growing share count. Show DRIP vs non-DRIP total return. |
| **Roll history with cost tracking** | Logging every roll (old position closed, new opened, net cost) creates an audit trail. Over time, this shows true hedging cost and pattern. Professional feature missing from consumer tools. | Med | M2 | Rolling tracker | YAML-based roll-history.yaml in fin-guru-private/hedging/. Append-only log. Running total of hedge spend. |
| **Portfolio-aware multi-underlying hedge allocation** | Splitting contracts across QQQ + SPY + IWM with budget awareness and configurable weights. More sophisticated than single-underlying sizing. | Med | M2 | Contract sizing, budget validation | Distribute contracts evenly with remainder to primary underlying. Handle odd splits gracefully. |
| **Config-driven defaults from user profile** | All 4 tools auto-load preferences from user-profile.yaml (budget, underlyings, DTE target, OTM range). Users configure once, tools read automatically. Personal touch = Finance Guru's brand. | Low-Med | M2 | M1 onboarding (config loader) | config_loader.py returns typed HedgeConfig model. CLI flags override config values. |

### Anti-Features (M2)

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Live trade execution** | Massive liability, regulatory complexity (broker API integration, order management). Way beyond CLI analysis tool scope. | CLI outputs recommendations. User executes manually on broker platform. |
| **Real-time position monitoring** | Requires persistent process, broker API, websocket feeds. Completely different architecture from batch CLI tools. | On-demand `status` command. User runs when they want to check. |
| **New API integrations beyond yfinance** | Each new API = new dependency, API key management, rate limiting, error handling. yfinance covers options chains and dividends. | yfinance for all market data. Document limitations. Add APIs later if yfinance proves insufficient. |
| **Precise SQQQ decay modeling** | Path-dependent daily rebalancing is genuinely impossible to model precisely without knowing the exact daily price path in advance. Claiming precision = misleading. | Approximate with historical volatility. Clear disclaimer: "SQQQ decay is path-dependent; this is an estimate." |
| **Automated roll execution** | Same as live trade execution. Triggering rolls automatically = broker integration + regulatory concerns. | Suggest rolls. User logs completed rolls manually via `log-roll` command. |
| **Monte Carlo simulation for hedges** | Tempting but massive complexity with questionable marginal value over scenario analysis for this use case. | Discrete scenario modeling (-5%, -10%, -20%, -40%). Simpler, more interpretable, adequate for hedge comparison. |

---

## Milestone 3: Interactive Knowledge Explorer

### Table Stakes

| Feature | Why Expected | Complexity | Milestone | Dependencies | Notes |
|---------|--------------|------------|-----------|--------------|-------|
| **Self-assessment per concept** | The core mechanic: user marks their understanding of each concept (unknown/learning/known/expert). Without self-assessment, it is just a static document. | Low-Med | M3 | Template engine | Click/tap to cycle through knowledge states. Visual color coding per state. Working prototype already exists in dividend-strategy-explorer.html. |
| **Persistent state (page refresh safe)** | localStorage persistence is mandatory. Users will close the tab and come back. Losing assessment state = frustration and abandonment. | Low | M3 | Self-assessment | localStorage keyed by topic. JSON.stringify state on every change. Load on page init. Prototype already uses localStorage. |
| **Visual knowledge map** | The entire value proposition is VISUAL -- a spatial/graph representation of concept relationships. A flat list is not an explorer. | Med | M3 | Topic data format | Node-link visualization. CSS grid/flexbox for layout. Connections between related concepts. Prototype proves feasibility. |
| **Copy-to-clipboard prompt generation** | "Assess, generate prompt, copy to chatbot" is the core loop. The prompt must incorporate the user's current knowledge state (what they know vs don't know). | Low | M3 | Self-assessment state | Generate contextual prompt: "I know X, Y, Z. I'm learning A, B. I don't know C, D. Help me understand..." navigator.clipboard.writeText() with fallback. |
| **Multiple topics** | A single topic is a demo. Users expect at least 3-4 topics to make the tool worthwhile. Spec calls for 5 total (dividends + 4 new). | Med-High | M3 | Template engine, JSON schema | Dividend (existing prototype), options-greeks, risk-management, portfolio-construction, tax-optimization. Each needs curated concept graph. |
| **Mobile/touch support** | Significant portion of education browsing happens on mobile. Explorer must be usable on phones/tablets. | Med | M3 | Visual map | Responsive CSS. Touch events for cycle-state. Collapsible sidebar. Viewport meta tag. |
| **Zero external dependencies** | Part of the core philosophy. Single HTML file per topic, no build step, no CDN, no framework. Opens instantly, works offline. | Design constraint | M3 | None | All CSS and JS inline. No fetch calls for data (embedded in HTML or loaded from sibling JSON). Sub-1-second load time. |
| **Accessible color coding** | Knowledge states need distinct visual treatment. Must work for colorblind users (patterns + colors, not colors alone). | Low | M3 | Visual map | Use patterns/icons alongside colors. High contrast. ARIA labels on interactive elements. |

### Differentiators

| Feature | Value Proposition | Complexity | Milestone | Dependencies | Notes |
|---------|-------------------|------------|-----------|--------------|-------|
| **Learning mode selector** | Guided/Standard/YOLO modes change prompt output complexity. Guided = explain everything. YOLO = advanced briefing. Personalizes the chatbot interaction style. | Low-Med | M3 | Prompt generation | Three templates per topic. Mode selector persisted to localStorage. Unique -- most education tools have one output level. |
| **Maya learner profile export** | Export JSON matching the learner_profile schema for use in Finance Guru AI sessions. Creates a feedback loop: self-assess in Explorer, import profile into Claude session, get personalized teaching. | Med | M3 | Self-assessment state | JSON blob with: {topic, knowledge_states, learning_mode, last_updated, strengths, gaps}. Download as file. Maya agent reads at session start. Closes the assess-teach-learn loop. |
| **Cross-topic concept linking** | Shared nodes across topics (e.g., "Delta" appears in both options-greeks and risk-management). Updating knowledge in one topic reflects in others. | High | M3 | Multiple topics | Concept registry with cross-references. localStorage sync across topics. Genuinely novel for static HTML education tools. |
| **Template engine for topic creation** | Extract the rendering engine from the prototype so creating new topics = writing a JSON file, not building new HTML. Community can contribute topics. | Med | M3 | Prototype refactor | Single template.html + per-topic data.json. Template reads JSON, renders graph. This enables scale. |
| **CLI launcher (`fin-guru explore <topic>`)** | Bridge between CLI tools and HTML explorer. `fin-guru explore options-greeks` opens in default browser. Integrated UX. | Low | M3 | Template engine | Python `webbrowser.open()` on the HTML file. Trivial implementation but meaningful UX integration. |
| **Topic selector landing page** | Card grid showing all available explorers with completion badges. "You've mastered 3 of 5 topics." Gamification light. | Low-Med | M3 | Multiple topics, localStorage | index.html reading localStorage across all topics. Completion = all concepts at "known" or higher. |
| **Embeddable widget mode** | iframe-safe, focused layout for embedding in documentation or blog posts. Marketing and distribution channel. | Med | M3 | Template engine | CSS media query for iframe context. Remove navigation chrome. Focused single-topic view. |

### Anti-Features (M3)

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Backend/database** | Violates zero-dependency philosophy. Adds hosting, auth, deployment complexity. localStorage is sufficient for personal assessment. | localStorage only. All data client-side. |
| **User accounts** | No authentication system needed for local-first self-assessment. Accounts = infrastructure = maintenance = cost. | Anonymous local state. Export/import JSON for portability. |
| **Real-time AI integration in explorer** | Would require API keys, network requests, latency, cost. The explorer generates prompts; the user pastes them into their own AI tool. | Generate prompt text. User copies to their chatbot of choice. Keeps explorer offline-capable. |
| **Drag-and-drop concept rearrangement** | Complex interaction model, accessibility nightmare, unclear value over fixed expert-curated layouts. | Fixed layout per topic (expert-curated by topic author). Consistent, predictable, accessible. |
| **Spaced repetition / quiz mode** | Different product category entirely (Anki, flashcards). Scope creep that delays shipping the core assess-and-prompt loop. | Self-assessment is user-driven, not quiz-driven. User decides their own knowledge level. |
| **Payment/subscription** | Monetization adds infrastructure, legal, and support burden. Explorer is a marketing tool for Finance Guru adoption. | Free and open-source. Value comes from Finance Guru ecosystem adoption, not direct revenue. |
| **Community topic submissions (live)** | Content moderation, quality control, review process. Unsustainable for a small team. | Accept topic JSON via GitHub PRs. Review and merge manually. Standard open-source contribution model. |

---

## Cross-Milestone Feature Dependencies

```
M1 Onboarding
├── user-profile.yaml generation ──> M2 config_loader.py reads hedging section
├── .env API key setup ──────────> M2 tools use yfinance (works without keys)
├── setup.sh fin-guru-private/ ──> M2 hedging/ directory created during setup
├── Bun hook refactor ───────────> Independent (no M2/M3 dependency)
└── .gitignore protection ───────> M2 positions.yaml, roll-history.yaml protected

M2 Hedging Tools
├── options.py (existing) ───────> Rolling tracker suggest-roll uses Black-Scholes
├── options_chain_cli.py (exist) > Rolling tracker scans for replacement puts
├── hedging_inputs.py (shared) ──> All 4 tools share Pydantic models
├── config_loader.py ────────────> All 4 tools read HedgeConfig from profile
├── Total return calculator ─────> Independent (no dependency on other M2 tools)
└── Knowledge files ─────────────> M3 explorer could render hedging topic from this content

M3 Knowledge Explorer
├── Template engine ─────────────> All topics depend on this
├── Dividend topic (existing) ───> Port from prototype to template format
├── Topic JSON schema ───────────> All new topics must validate against schema
├── Cross-topic linking ─────────> Depends on multiple topics existing
├── Maya learner profile ────────> Depends on self-assessment being complete
└── CLI launcher ────────────────> Depends on template engine (knows file locations)
```

### Critical Path

1. **M1 must complete before M2** -- hedging tools need config_loader.py which depends on user-profile.yaml generation from onboarding.
2. **M2 knowledge files inform M3 content** -- hedging-strategies.md and related knowledge files can seed the hedging topic in M3, but M3 is not blocked by M2.
3. **M3 template engine must be extracted early** -- all M3 features depend on this; it should be the first M3 task.
4. **M2 tools are mostly independent of each other** -- rolling tracker, hedge sizer, hedge comparison, and total return can be built in parallel once shared models and config_loader exist.

---

## Complexity Assessment Summary

| Feature | Complexity | Risk | Milestone |
|---------|-----------|------|-----------|
| Dependency checker | Low | Low | M1 |
| Interactive onboarding prompts | Med | Low | M1 |
| Input validation + retry | Med | Low | M1 |
| Progress save/resume | Med | Med -- signal handling edge cases | M1 |
| Config file generation (YAML, .env, MCP) | Med | Low | M1 |
| Idempotent re-run | Med | Med -- diffing existing config | M1 |
| Bun hook ports | Med-High | Med -- behavior parity verification | M1 |
| Hardcoded reference removal | Low | Low -- grep and replace | M1 |
| Rolling tracker (status + DTE alerts) | Med | Low | M2 |
| Roll suggestion engine | High | Med -- integrating with options scanner | M2 |
| Portfolio-aware hedge sizer | Low-Med | Low | M2 |
| SQQQ vs puts with decay modeling | High | High -- path-dependent math is approximate | M2 |
| Total return with DRIP | Med | Low -- yfinance dividend data available | M2 |
| Roll history logging | Med | Low | M2 |
| Template engine extraction | Med | Med -- refactoring working prototype | M3 |
| Self-assessment + localStorage | Low-Med | Low -- proven in prototype | M3 |
| Multiple topics (4 new) | Med-High | Med -- content curation effort | M3 |
| Cross-topic linking | High | High -- state sync across separate HTML files | M3 |
| Maya learner profile export | Med | Low | M3 |
| Mobile/touch support | Med | Med -- testing across devices | M3 |

---

## MVP Recommendation per Milestone

### M1: Ship These First (Table Stakes + 1 Differentiator)

**Must have:**
1. Dependency checker in setup.sh
2. Interactive prompt-driven onboarding with validation
3. Config file generation (YAML, .env, MCP.json)
4. Progress indicator showing section N of M
5. .gitignore protection for all sensitive files
6. README with fork workflow and setup instructions
7. Hardcoded reference removal (grep "Ossie" returns nothing)
8. Idempotent re-run

**Ship with (differentiators):**
9. Save/resume on Ctrl+C -- high impact for 15-min onboarding
10. Bun hook ports with test assertions

**Defer:**
- `fin-guru doctor` command (high value but not blocking release)
- Contextual explanations per question (can add incrementally)

### M2: Ship These First (Core Tools)

**Must have:**
1. Rolling tracker: status + DTE alerts
2. Hedge sizer: sizing formula + budget validation
3. Total return: price + dividend separation, multi-ticker
4. All tools: JSON + text output, educational disclaimers

**Ship with (differentiators):**
5. Roll suggestion engine (key differentiator, justifies M2 existence)
6. DRIP modeling in total return
7. Config-driven defaults from user profile

**Defer:**
8. SQQQ vs puts analyzer -- highest complexity, can ship as follow-up
9. Cross-tool integration (total return feeding into hedge comparison)
10. Roll history logging (add after core rolling tracker works)

**Recommendation:** Consider shipping M2 in two drops. Drop 1: rolling tracker + hedge sizer + total return. Drop 2: SQQQ comparison + roll history. The SQQQ decay modeling is the riskiest feature and should not block the other three tools.

### M3: Ship These First (Core Explorer)

**Must have:**
1. Template engine extracted from prototype
2. Topic JSON schema and validator
3. Dividend topic ported to template format
4. Self-assessment with localStorage persistence
5. Copy-to-clipboard prompt generation
6. Mobile/touch support
7. At least 2 additional topics (options-greeks, risk-management)

**Ship with (differentiators):**
8. Learning mode selector (low effort, high perception of personalization)
9. Maya learner profile export
10. CLI launcher (`fin-guru explore <topic>`)

**Defer:**
- Cross-topic concept linking (highest complexity, adds most value after 4+ topics exist)
- Embeddable widget mode (marketing optimization, not core value)
- Remaining topics (portfolio-construction, tax-optimization) -- add incrementally
- Topic selector landing page (build after 3+ topics exist)

---

## Sources

**CLI Onboarding Ecosystem:**
- clig.dev -- Command Line Interface Guidelines (HIGH confidence, authoritative open-source guide)
- Cookiecutter / Hypermodern Python Cookiecutter -- Python project templating patterns (MEDIUM confidence)
- questionary library -- Python CLI prompts, 2.1.1 latest (MEDIUM confidence, WebSearch + PyPI)
- InquirerPy -- Python port of Inquirer.js (MEDIUM confidence, GitHub)
- OpenClaw onboarding wizard (docs.clawd.bot) -- CLI onboarding reference implementation (LOW confidence, single source)
- oclif framework -- CLI framework patterns for commands, config, plugins (MEDIUM confidence)

**Options Hedging Tools:**
- OptionStrat / OptionsForge protective put calculators -- feature reference for hedge analysis (HIGH confidence, domain-specific tools)
- CBOE Options Institute tools -- professional options calculator with Greeks (HIGH confidence, authoritative)
- tastytrade backtesting tool -- options backtesting feature set (HIGH confidence, professional platform)
- TradeStation beta hedging calculator -- portfolio hedge sizing reference (HIGH confidence, professional)
- Days to Expiry blog -- DTE management and rolling strategy patterns (MEDIUM confidence)
- Seeking Alpha SQQQ analysis articles -- leveraged ETF decay mechanics (MEDIUM confidence)
- Robot Wealth -- portfolio hedging with put options guide (MEDIUM confidence)

**Knowledge Explorer / Education:**
- Concept Explorer (conceptexplorer.space) -- interactive knowledge tree reference (MEDIUM confidence)
- Adaptive learning platforms survey (Coursera article) -- personalization feature patterns (MEDIUM confidence)
- Mentimeter online assessment tools survey -- assessment tool feature landscape (LOW confidence, different domain)
- Outgrow calculators/surveys for personalized learning -- self-assessment pattern reference (LOW confidence)
- PKM apps 2026 survey (toolfinder.co) -- knowledge management patterns: graph view, backlinks, networked thought (MEDIUM confidence)
- Irec metacognitive scaffolding paper (arxiv 2506.20156) -- self-regulated learning system design (MEDIUM confidence, academic)
