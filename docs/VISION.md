# Finance Guru — Vision Document

> _"A fully autonomous, unbiased family office with agentic personalities grounded in math and truth, helping me achieve financial freedom."_
> — Ossie Irondi, March 13, 2026

---

## 1. What Finance Guru IS

Finance Guru is three things:

1. **A wealth-building engine** — optimized for one outcome: growing net worth and achieving financial freedom as fast as mathematically sound strategy allows.
2. **A financial co-pilot** — an always-on partner that thinks alongside me about money decisions. Not just data, but judgment and perspective.
3. **A brokerage-first financial operating system** — built for someone who has eliminated traditional banking and lives entirely out of their brokerage account. No checking account assumption. Margin is operating capital. Every income stream flows through and is tracked here.

It is NOT a software product (yet). It is NOT a Claude Code skill pack. It is NOT a collection of scripts. It is a _standalone macOS native application_ that happens to be powered by AI agents.

**Brand**: Finance Guru. The name stays. Gold FG monogram on black. Luxury minimal aesthetic.

---

## 2. The North Star

**Autonomous daily briefing.** Every morning, Finance Guru has already analyzed overnight changes, assessed portfolio health, identified opportunities, and prepared recommendations. It reaches me through:

- Push notification on macOS (tap to open full briefing)
- Email digest (formatted, actionable)
- In-app (ready and waiting when I open it)
- Slack/Discord message (private channel, mobile-accessible)

When I open Finance Guru and see a clear, well-reasoned morning briefing that I didn't ask for — that's when I know this thing is real.

---

## 3. Architecture

### 3.1 Standalone macOS Native App

- **Zero Claude Code dependency.** No hooks, no `.claude/skills`, no PAI entanglement.
- **Built on pi-mono SDK** — unified LLM API, agent harness, TUI/web UI libraries.
- **Native macOS window app** — **Tauri v2** (confirmed). Menubar presence, native notifications, dock icon. Feels like a real Mac app.
- **UI/UX reference: Wealthfolio** — FG adopts Wealthfolio's proven UX patterns (navigation, portfolio views, activity tables, holdings layout) rebuilt fresh with Shadcn/Radix components under FG's gold-on-black luxury aesthetic. We adapt patterns, not their code.
- **Dark and light themes** — Gold FG accent carries through both. Dark is the hero experience.
- **Web app support comes before Windows.** Cross-platform via web when ready.
- **Mobile** — Architect for Mac + iPhone. Start single-machine, extend to mobile companion (briefings, alerts) when ready.

### 3.2 Monorepo with Packages (Repo must be scaffolded with the RepoArchitect Skill `~/.claude/skills/RepoArchitect/SKILL.md`)

One repository, clear internal packages:

```
finance-guru/
├── packages/
│   ├── core/                    # Agent orchestration, dispatch, session management
│   │   ├── src/
│   │   │   ├── orchestrator.ts  # Cassandra's routing logic
│   │   │   ├── agents/          # Agent YAML definitions + loaders
│   │   │   ├── context/         # Context injection engine
│   │   │   └── index.ts         # Public API
│   │   ├── tests/
│   │   └── package.json
│   │
│   ├── data/                    # SnapTrade integration + local DB (SQLite → Postgres)
│   │   ├── src/
│   │   │   ├── snaptrade/       # SnapTrade client, webhooks, sync (direct API, no middleman)
│   │   │   ├── db/              # Schema, migrations, queries (Drizzle + bun:sqlite)
│   │   │   ├── enrichment/      # Transaction categorization, position enrichment
│   │   │   ├── income/          # W2, business, dividend income tracking
│   │   │   └── index.ts
│   │   ├── tests/
│   │   └── package.json
│   │
│   ├── tools/                   # Python CLI tools (3-layer: Pydantic → Calculator → CLI)
│   │   ├── src/
│   │   │   ├── risk/            # VaR, CVaR, Sharpe, Sortino, Drawdown, Beta, Alpha
│   │   │   ├── momentum/        # RSI, MACD, Stochastic, Williams %R, ROC
│   │   │   ├── volatility/      # Bollinger, ATR, Historical Vol, Keltner, Regime
│   │   │   ├── moving_avg/      # SMA, EMA, WMA, HMA, Golden/Death Cross
│   │   │   ├── correlation/     # Pearson, diversification scoring
│   │   │   ├── optimizer/       # Mean-Variance, Risk Parity, Min Var, Max Sharpe, BL
│   │   │   ├── backtest/        # Strategy validation, performance metrics
│   │   │   ├── hedging/         # Hedge sizer, rolling tracker, SQQQ vs puts
│   │   │   └── total_return/    # DRIP modeling, dividend-adjusted returns
│   │   ├── tests/               # The 365+ existing tests live here
│   │   ├── pyproject.toml       # uv-managed, Python 3.12
│   │   └── bridge.ts            # TS↔Python interop (spawns CLI via Bun.spawn, parses JSON output)
│   │
│   ├── agents/                  # Agent personalities, YAML definitions, prompt templates
│   │   ├── definitions/         # 11 agent YAML files (cassandra.yaml, quant.yaml, etc.)
│   │   ├── src/
│   │   │   ├── personality.ts   # Voice/style injection per agent
│   │   │   ├── routing.ts       # Intent → agent mapping
│   │   │   └── index.ts
│   │   ├── tests/
│   │   └── package.json
│   │
│   ├── strategy/                # Strategy engine (configurable profiles, not hardcoded)
│   │   ├── src/
│   │   │   ├── profiles/        # YAML strategy configs (fire-method.yaml, etc.)
│   │   │   ├── engine.ts        # Strategy evaluation, rebalancing logic
│   │   │   ├── compliance.ts    # personal/strict/educational modes
│   │   │   └── index.ts
│   │   ├── tests/
│   │   └── package.json
│   │
│   ├── simulation/              # Monte Carlo, backtesting, scenario analysis
│   │   ├── src/
│   │   │   ├── montecarlo.ts    # 10k scenario engine, 4-layer model
│   │   │   ├── scenarios.ts     # What-if scenario builder
│   │   │   └── index.ts
│   │   ├── tests/
│   │   └── package.json
│   │
│   ├── briefing/                # Autonomous briefing engine
│   │   ├── src/
│   │   │   ├── scheduler.ts     # Cron/launchd scheduling for daily runs
│   │   │   ├── generator.ts     # Briefing content assembly (calls agents + tools)
│   │   │   ├── delivery/        # Push, email (Resend), Slack, Discord, in-app
│   │   │   └── index.ts
│   │   ├── tests/
│   │   └── package.json
│   │
│   └── ui/                      # Native app shell + chat + agent panels
│       ├── src/
│       │   ├── chat/            # Chat interface components
│       │   ├── panels/          # Agent-specific panels (Quant, Strategy, Margin, etc.)
│       │   ├── views/           # Core navigation views (DataHub, Insights, Performance, etc.)
│       │   ├── command-palette/ # Cmd+K power-user interface
│       │   ├── briefing-view/   # Morning briefing display
│       │   └── index.ts
│       ├── tests/
│       └── package.json
│
├── app/                         # macOS native app entry point (Tauri v2)
│   ├── src/
│   │   ├── main.ts              # Tauri main process entry
│   │   ├── sidecar/             # Bun sidecar lifecycle manager (spawn, health, restart)
│   │   └── tray.ts              # Menubar + notifications
│   ├── assets/                  # FG monogram, icons, brand assets
│   └── package.json
│
├── config/                      # User-facing configuration
│   ├── strategies/              # Strategy YAML profiles
│   ├── agents.yaml              # Agent roster override
│   ├── preferences.yaml         # User preferences (delivery channels, schedule)
│   └── snaptrade.yaml           # SnapTrade environment config
│
├── docs/
│   └── VISION.md                # This document
│
├── scripts/
│   ├── setup.sh                 # First-time dev environment setup
│   ├── dev.sh                   # Start all packages in dev mode
│   └── migrate.sh               # DB migration runner
│
├── .github/
│   └── workflows/
│       ├── ci.yml               # Lint + test all packages
│       └── build.yml            # macOS app build
│
├── bun.lock
├── package.json                 # Root workspace config
├── bunfig.toml                  # Bun workspace configuration
├── tsconfig.json                # Root TS config with path aliases
├── .gitignore
├── LICENSE
└── README.md
```

Clean boundaries. Single checkout. Each package independently testable.

### 3.3 Key Architectural Decisions

1. **packages/tools/ stays Python, gets a TS bridge.**
Your 3-layer Pydantic/Calculator/CLI architecture and 365+ tests are proven. Don't rewrite them.
The bridge.ts file spawns CLI tools via `Bun.spawn()` and parses their JSON output — composability via JSON interchange.

2. **packages/agents/ separates YAML definitions from runtime.**
Agent definitions live in definitions/*.yaml (portable). The TypeScript code in src/ handles loading, personality injection, and routing. This keeps "who the agents are" separate from "how agents run."

3. **packages/strategy/ is config-driven, not code-driven.**
Strategy profiles are YAML files in config/strategies/. The engine evaluates them. Your Fin-Guru FIRE Method is the default config, not hardcoded logic.

4. **app/ is separate from packages/ui/.**
The UI package contains reusable components (chat, panels, views). The app/ directory is the Tauri v2 native shell entry point. This lets you ship a web app later without restructuring — just create a new entry point that consumes packages/ui/.

5. **No pi-mono SDK coupling in the scaffold.**
pi-mono is referenced as the agent harness, but the scaffold doesn't assume its internal structure. When pi-mono's API stabilizes, packages/core/ will import it as a dependency.

6. **Tauri v2 with Bun sidecar architecture.**
Tauri v2 is the confirmed desktop shell. The TS backend (agents, data, strategy, briefing) runs as a compiled Bun sidecar (`bun build --compile` produces a standalone binary — no runtime required for end users). The Bun sidecar owns all SQLite writes. The frontend reads via Tauri commands. Sidecar lifecycle managed via ~200 lines of Rust in app/src/sidecar/.

7. **TypeScript core over Rust core — the agent-centric decision.**
Finance Guru is agent-centric, not data-centric. The center of gravity is AI orchestration via pi-mono (TypeScript). Adding Rust to the backend would force every agent call across a TS↔Rust IPC boundary for data access — the worst possible location for latency given agent dispatch runs on every user interaction. LLM calls dominate latency by 3-4 orders of magnitude vs. any DB query; there is no performance justification for Rust at 40 positions. TypeScript + Python covers 100% of the compute requirement. Rust is reserved for the Tauri shell code only (~500 lines).

8. **Bun workspaces, not Turborepo/Nx.**
Bun has native workspace support via bunfig.toml. No additional build orchestration tooling at this scale.

---

### 3.4 Dependency Graph (one-way, no cycles)

```
app → ui → core → agents
                 → strategy
                 → simulation → tools (via bridge)
                 → briefing → data, agents (not core — avoids cycle)
                 → data → tools (via bridge)
```

- app depends on ui
- ui depends on core (for agent dispatch)
- core depends on agents, data, strategy, simulation, briefing
- briefing depends on data, agents (not core — avoids cycle)
- simulation and data depend on tools (via bridge)
- tools depends on nothing (leaf node, pure Python)

### 3.5 Data Layer: SnapTrade → Local DB Hybrid

- **SnapTrade** (direct API integration, your own credentials, no Wealthfolio Connect middleman) provides live brokerage position, transaction, and balance data. Supports Fidelity, Schwab, Interactive Brokers, and 100+ brokerages.
- **Local database** (`bun:sqlite` + Drizzle ORM) stores the enriched, analyzed version. The Bun sidecar owns all writes. Schema informed by Wealthfolio's proven `holdings_snapshots` and `daily_account_valuation` patterns.
- **SnapTrade is the feed. The local DB is the truth.** Enrichment, analysis results, strategy state, Monte Carlo outputs — all local.
- **CSV import as fallback.** SnapTrade is primary. CSV import stays for: historical data migration, brokerages SnapTrade doesn't cover, and manual corrections.
- **Plaid — v2+ only.** If future needs require non-brokerage accounts (checking, savings, credit cards), Plaid can be added behind the same data provider abstraction without rearchitecting.
- **Google Sheets is dead.** No more syncing to Sheets, no more sacred formulas, no more formula protection skills. The app owns its data.
- **Market data:** yfinance + Finnhub. Two fixed providers. No pluggable abstraction needed at this scale.

### 3.6 Brokerage-First Living Philosophy

Finance Guru is designed for a specific operating model: **living entirely out of a brokerage account.** This shapes every feature decision.

- No checking account assumption. Margin is operating capital.
- Income tracking covers _all_ income streams: W2 salary, business income, dividends, capital gains distributions — everything that flows through the brokerage.
- Margin health is a first-class view, not a footnote.
- The Layer 2 (Income) strategy is the deployment mechanism — W2 and business income fund dividend income vehicles until dividends are self-sustaining.
- Net worth tracking (real estate, vehicles, liabilities) is deferred to v2+. V1 focuses on portfolio and margin.

---

## 4. The Agents

### 4.1 Named Personas with Voice

The agents have names, roles, and distinct communication styles. This isn't theater — it's legibility. When Cassandra coordinates, the Quant speaks in numbers, and the Compliance Officer raises flags, you immediately know _who_ is saying _what_ and _why_.

### 4.2 Agent Roster

| Agent | Role | Voice |
|-------|------|-------|
| **Cassandra Holt** | Finance Orchestrator | Decisive, clear, routes to specialists |
| **Dr. Aleksandr Petrov** | Market Researcher | Thorough, citation-heavy, temporally aware |
| **Quant Analyst** | Quantitative Analysis | Numbers-first, statistical rigor, confidence intervals |
| **Elena Rodriguez-Park** | Strategy Advisor | Long-term thinking, portfolio construction, trade-offs |
| **Marcus Allen** | Compliance Officer | Risk flags, guardrails, reality checks |
| **Richard Chen** | Margin Specialist | Leverage analysis, margin safety, scaling |
| **Sarah Martinez** | Dividend Specialist | Income optimization, yield analysis, DRIP strategy |
| **Maya Brooks** | Teaching Specialist | ADHD-friendly education, micro-learning, adaptive |
| **Alexandra Kim** | Builder | Document generation, reports, artifacts |
| **Dr. Jennifer Wu** | QA Advisor | Quality control, verification, methodology review |
| **James Cooper** | Onboarding Specialist | User setup, progressive profiling |

### 4.3 Agent Architecture

Agents are _not_ Claude Code commands. They are:

- Defined in YAML (portable, not BMAD-CORE XML)
- Dispatched by the orchestrator with precise context injection
- Given exactly the right files/APIs at dispatch time (not a dump of everything)
- Stateful within a session, stateless across sessions (DB is the state)
- Backed by configurable LLM (Claude, GPT, Gemini via pi-mono's unified API)

---

## 5. The Interface

### 5.1 Core Navigation Views

Finance Guru ships with these views from day one:

| View | What it does | FG-exclusive? |
|------|-------------|---------------|
| **DataHub** | Full portfolio holdings — positions, quantities, cost basis, allocation | Borrowed pattern, FG data |
| **Investment Tracking** | Buy/sell activity, transaction history, CSV import | Borrowed pattern |
| **Portfolio Insights** | Python quant tools surface here — risk metrics, momentum, correlation, optimization | **FG-exclusive** |
| **Performance Dashboard** | Total return, time-weighted returns, historical performance charts | Borrowed pattern |
| **Income Tracking** | All income streams: dividends, W2, business income, distributions | **FG-exclusive** (competitors only track investment income) |
| **Margin Health** | Margin balance, coverage ratio, interest accrual, scaling thresholds | **FG-exclusive** |
| **Morning Briefing** | Autonomous daily briefing, full analysis display | **FG-exclusive** |
| **Agent Panels** | Per-agent dedicated panels: Quant, Strategy, Margin, Dividends | **FG-exclusive** |

The DataHub replaces what was the Google Sheets "DataHub" tab — same concept, app-native.

### 5.2 Chat + Agent Panels

**Primary**: Chat interface. Talk to Finance Guru like an advisor.
- "What should I do with this $5k?"
- "How's my margin health looking?"
- "Run a Monte Carlo on my current allocation"
- The system routes to the right agent behind the scenes.

**Secondary**: Agent panels. Each agent has its own tab/panel.
- Click "Quant" to see quantitative analysis dashboards
- Click "Strategy" for allocation recommendations and rebalancing
- Click "Margin" for margin health, scaling thresholds, interest tracking
- Click "Dividends" for income projections, DRIP status, yield analysis

**Tertiary**: Command palette (Cmd+K) for power users.
- `/analyze GOOGL` — full research + quant + strategy pipeline
- `/rebalance layer-2` — generate rebalancing recommendations
- `/briefing` — force-generate a briefing now
- `/montecarlo` — run simulation with current positions

### 5.3 Daily Interaction Modes

Finance Guru supports _all_ interaction modes simultaneously:

| Mode | When | How |
|------|------|-----|
| **Morning briefing** | Daily, automatic | Push + email + in-app |
| **Conversational** | When I sit down to think | Chat interface |
| **Dashboard** | Quick health check | Core navigation views |
| **Fully autonomous** | Strategy execution | Background, alerts on anomalies |

---

## 6. What Survives from the Current System

### 6.1 Python CLI Tools (3-Layer Architecture)

**ALL tools survive.** The Pydantic → Calculator → CLI pattern is sound. Tools must become:

- **Ticker-agnostic**: No hardcoded defaults to PLTR, TSLA, or any specific ticker. Every tool takes tickers as input parameters, period.
- **Strategy-neutral**: Tools are analytical instruments. They compute metrics, not opinions. Strategy logic lives in the strategy engine, not in the tools.
- **Composable**: Output formats support piping into other tools. JSON is the interchange format.

Current tools to port:
1. Risk Metrics (VaR, CVaR, Sharpe, Sortino, Drawdown, Beta, Alpha)
2. Momentum Indicators (RSI, MACD, Stochastic, Williams %R, ROC)
3. Volatility Metrics (Bollinger, ATR, Historical Vol, Keltner, Regime)
4. Moving Averages (SMA, EMA, WMA, HMA, Golden/Death Cross)
5. Correlation & Covariance (Pearson, diversification scoring)
6. Portfolio Optimizer (Mean-Variance, Risk Parity, Min Variance, Max Sharpe, Black-Litterman)
7. Backtesting Framework (strategy validation, performance metrics)
8. Hedging Tools (hedge sizer, rolling tracker, SQQQ vs puts comparison)
9. Total Return Calculator (DRIP modeling, dividend-adjusted returns)

### 6.2 Monte Carlo Simulation

The 4-layer portfolio model survives:
- Layer 1 (Growth): Core holdings, no deployment changes
- Layer 2 (Income): Dividend/income vehicles, active deployment target
- Layer 3 (Hedge): Options insurance, SQQQ, protective puts
- GOOGL Scale-In: Dedicated accumulation position

10,000 scenario simulations. Probability-based decision making. Run on demand (_prn_).

### 6.3 Hedging Framework

Sean's advisory philosophy survives:
- Options as insurance (always-on, not timing-based)
- 1 contract per $50k portfolio value
- SQQQ daily rebalancing drag analysis
- Rolling tracker with DTE-based alerts
- Monthly hedging budget validation

### 6.4 Agent Personalities & Roles

All 11 agents carry forward with their names and voices. The orchestration pattern (Cassandra dispatches to specialists) is proven and stays.

---

## 7. What Dies

| What | Why |
|------|-----|
| **Google Sheets as data hub** | Replaced by SnapTrade → local DB. No more syncing, formula protection, or sacred columns. |
| **Automated CSV download workflow** | SnapTrade provides live data. CSV import stays as a _fallback_ for edge cases, not the primary pipeline. |
| **Claude Code hooks/skills** | FG is a standalone app. No `.claude/skills`, no session-start hooks, no `UserPromptSubmit` activation. Current Claude Code skills continue running until the app reaches feature parity — then they're retired. Clean break, no migration. |
| **BMAD-CORE agent definitions** | Agents move to YAML. Portable, simple, not framework-dependent. |
| **PAI entanglement** | Finance Guru is its own process. It doesn't share context with dental projects, church media, or anything else. |
| **Streamlit/Textual TUI** | Replaced by native macOS app with proper UI. |
| **Multiple repo confusion** | One monorepo. No more `family-office` vs `fin-guru` vs `fin-guru-desktop` confusion. |
| **Addon/plugin system** | FG is a private family office tool. Extensibility comes from the agent system and strategy YAML, not third-party plugins. |
| **Net worth tracking (v1)** | Deferred to v2+. V1 focuses on portfolio + margin. |

---

## 8. Strategy Engine

### 8.1 Configurable, Not Hardcoded

My strategy (Layer 1/2/3/GOOGL, margin-living, Hybrid DRIP v2) is the _default configuration_, not baked-in logic. The system supports:

- Defining custom strategies via configuration
- Multiple strategy profiles (aggressive, conservative, income-focused)
- Strategy backtesting before deployment
- Strategy comparison (what-if scenarios)

### 8.2 My Default Strategy

```yaml
name: "Fin-Guru FIRE Method"
layers:
  growth:
    description: "Core holdings for long-term appreciation"
    action: "HOLD — do not deploy new capital"
    rebalance: false
  income:
    description: "Dividend and income vehicles"
    deployment: "$13,317/month from W2"
    strategy: "Hybrid DRIP v2 with active rotation"
    target: "$100k annual dividend income"
  hedge:
    description: "Portfolio insurance"
    instruments: ["protective puts", "SQQQ"]
    budget: "$500-600/month"
    philosophy: "Always-on, not timing-based"
  scale_in:
    ticker: "GOOGL"
    deployment: "$1,000/month diverted from Layer 2"

margin:
  philosophy: "Confidence-based scaling, not time-based mandates"
  safety_ratio: 4.0  # minimum portfolio:margin ratio
  interest_rate: 0.11825  # Fidelity rate
  backstop: "$22k/month business income"

income_sources:
  w2: "$13,317/month"
  business: "$22,000/month"
  dividends: "tracked via Income Tracking view, growing toward $100k/year"
```

### 8.3 Compliance Mode

```yaml
compliance:
  mode: "personal"  # "personal" | "strict" | "educational"
  # personal: No disclaimers, no "not investment advice" boilerplate
  # strict: Full disclaimers, educational framing (for shared outputs)
  # educational: Middle ground, risk disclosures without legalese
```

---

## 9. Technology Stack

### 9.1 Core

| Component | Technology | Why |
|-----------|-----------|-----|
| **Agent harness** | pi-mono SDK (TypeScript) | Unified LLM API, agent lifecycle, context management |
| **Runtime** | Bun | Fast, TypeScript-native, good DX; `bun build --compile` for sidecar binary |
| **Desktop shell** | Tauri v2 (confirmed) | Proven by Wealthfolio, native macOS, smaller binary than Electron, Rust security model |
| **LLM** | Claude (primary), configurable | pi-mono supports any provider |
| **Build system** | Bun workspaces | Native workspace support, no Turborepo needed at this scale |

### 9.2 Data

| Component | Technology | Why |
|-----------|-----------|-----|
| **Live brokerage data** | SnapTrade (direct API, v1) | Investment-focused, 100+ brokerages including Fidelity, direct integration |
| **Non-brokerage accounts** | Plaid (v2+, if needed) | Checking/savings/credit if ever required |
| **CSV import** | Custom importer | Fallback for historical migration and edge-case brokerages |
| **Local database** | `bun:sqlite` + Drizzle ORM | Bun built-in SQLite driver, type-safe ORM, Bun sidecar owns writes |
| **Schema reference** | Wealthfolio patterns | `holdings_snapshots`, `daily_account_valuation` schema patterns are well-proven |
| **Market data** | yfinance + Finnhub | Free baseline + real-time; fixed providers, not pluggable |

### 9.3 Analysis

| Component | Technology | Why |
|-----------|-----------|-----|
| **CLI tools** | Python 3.12 + uv | Proven 3-layer architecture, 365+ tests |
| **Models** | Pydantic v2 | Type safety, validation, serialization |
| **Compute** | pandas, numpy, scipy, scikit-learn | Battle-tested numerical libraries |
| **Simulation** | Custom Monte Carlo engine | 10k scenario, 4-layer model |
| **TS bridge** | `Bun.spawn()` + JSON | Spawns CLI tools, parses JSON output |

### 9.4 UI/Frontend

| Component | Technology | Why |
|-----------|-----------|-----|
| **Components** | Shadcn/Radix UI | Same stack Wealthfolio uses; proven for this use case |
| **Styling** | Tailwind CSS | Utility-first, compatible with dark/light themes |
| **Charts** | Recharts or equivalent | Wealthfolio-equivalent charting capability |
| **UX reference** | Wealthfolio | Adapt their proven navigation patterns, not their code |
| **Theme** | Dark + Light (gold FG accent) | Dark is the hero; light available |

### 9.5 Delivery

| Component | Technology | Why |
|-----------|-----------|-----|
| **Push notifications** | macOS native (Tauri notification API) | OS-level alerts |
| **Email** | Resend or SendGrid | Formatted briefing digests |
| **Messaging** | Slack API / Discord webhooks | Mobile-accessible alerts |

---

## 10. What Success Looks Like

### Month 1: Foundation
- [ ] Monorepo scaffolded with package boundaries
- [ ] Tauri v2 app shell with Bun sidecar lifecycle working
- [ ] pi-mono SDK integrated, agents defined in YAML
- [ ] SnapTrade connected, pulling live Fidelity positions and transactions
- [ ] Local SQLite database storing enriched portfolio data
- [ ] At least 3 Python CLI tools callable from TypeScript via bridge

### Month 3: Usable
- [ ] All core navigation views shipping: DataHub, Investment Tracking, Performance, Income Tracking, Margin Health
- [ ] Agent panels for Quant, Strategy, and Margin
- [ ] Daily briefing generates and delivers via at least one channel
- [ ] Monte Carlo simulation runnable from the app
- [ ] Portfolio Insights view with Python quant tools surfaced
- [ ] No Google Sheets dependency for any workflow

### Month 6: Powerful
- [ ] All 9 CLI tools ported and integrated
- [ ] Full agent roster active with voice and routing
- [ ] Strategy engine with configurable profiles
- [ ] Multi-channel briefing delivery (push + email + Slack)
- [ ] Hedging framework fully operational with rolling tracker
- [ ] Income Tracking comprehensive across all income streams

### Ongoing: Autonomous
- [ ] Rebalancing recommendations generated proactively
- [ ] Anomaly detection (margin alerts, unusual moves, dividend changes)
- [ ] Strategy backtesting on new positions before deployment
- [ ] Mobile companion app (read-only briefings + alerts on iPhone)
- [ ] Net worth tracking (v2+)

---

## 11. Wealthfolio: Reference and Inspiration

Wealthfolio (https://github.com/afadil/wealthfolio) was discovered during vision refinement and validates several architectural instincts:

**What it validates for Finance Guru:**
- Tauri v2 + local SQLite is the right desktop app foundation
- The market genuinely demands privacy-first, local-first financial tools
- Beautiful UI is not optional — it directly drives adoption
- SnapTrade is a viable brokerage sync provider (Wealthfolio uses it via their Connect service; FG integrates directly)
- The `holdings_snapshots` and `daily_account_valuation` SQLite schema patterns are well-designed

**Where Finance Guru goes further:**
- Wealthfolio has zero quantitative analysis tools. FG's 9 Python CLI tools are a genuine moat.
- Wealthfolio has one generic LLM chat. FG has 11 specialized agent personas with routing.
- Wealthfolio does not produce autonomous briefings. FG's North Star is a proactive daily briefing.
- Wealthfolio tracks portfolio. FG is a complete financial operating system including margin, income strategy, and all income sources.
- Wealthfolio assumes traditional banking. FG is built for brokerage-first living.

**What FG adopts (patterns, not code):**
- Navigation structure and portfolio view layouts
- Holdings/activity/performance view organization
- Dark/light theme approach with accent color
- Shadcn/Radix component library choice

---

## 12. Principles

1. **Math over opinion.** Every recommendation is backed by quantitative analysis. Agents are grounded in data, not vibes.

2. **Autonomy over prompting.** The system should do things _without being asked_. The briefing, the alerts, the analysis — proactive, not reactive.

3. **Isolation over entanglement.** Finance Guru is its own world. It doesn't leak into other projects, other configs, other contexts.

4. **Local-first over cloud-dependent.** Data lives on my machine. SnapTrade feeds it, but the DB is mine. No vendor lock-in on my financial data.

5. **Configurable over hardcoded.** My strategy is a configuration, not code. Tickers are parameters, not constants. Strategies are profiles, not assumptions.

6. **Ship over perfect.** No timeline pressure, but bias toward working software. A feature that works today beats a perfect feature planned for next month.

7. **Me first, abstraction second.** Build for Ossie. If the abstractions are clean enough for others to use later, great. But never sacrifice my workflow for hypothetical users.

8. **Brokerage-first.** Every feature is designed for someone who lives out of their brokerage. Margin is operating capital. Income tracking covers all income, not just dividends.

---

## 13. What This Document Is

This is _Ossie's vision_. Not Obi's architecture recommendation. Not the community's feature request list. Not a product spec for investors.

This is what I want Finance Guru to be. Every architectural decision, every technology choice, every feature priority flows from this document.

When in doubt, re-read Section 2 (The North Star) and Section 12 (Principles).

---

_Document created: March 13, 2026_
_Last updated: March 17, 2026 — Added brokerage-first identity, Tauri v2 confirmed, SnapTrade as v1 data provider, TS core confirmed, updated views, Wealthfolio reference section_
_Author: Ossie Irondi_
_Status: Living document — update as vision evolves_
