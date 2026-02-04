# Phase 9: SQQQ vs Puts Comparison - Context

**Gathered:** 2026-02-03
**Status:** Ready for planning

<domain>
## Phase Boundary

CLI tool that compares two hedge strategies -- holding SQQQ (3x inverse leveraged ETF) vs buying protective puts -- across user-defined market drop scenarios. Outputs payoffs, breakeven points, decay costs, and a recommendation. QQQ is the default underlying. The tool includes both sudden and gradual drop simulation modes with appropriate disclaimers.

</domain>

<decisions>
## Implementation Decisions

### Scenario Specification
- Interactive scenario selector -- NOT raw CLI flags
- When invoked by an agent, the agent uses `AskUserQuestion` with preset options
- When invoked directly, CLI presents an interactive multi-select menu
- Presets: Mild (-5%), Correction (-10%), Bear (-20%), Crash (-40%)
- Custom option available -- user can type their own percentage
- Underlying: QQQ by default, `--underlying` flag for others (SPY, etc.)

### Drop Simulation Modes
- Two modes: `--sudden` (instantaneous drop) and `--gradual` (day-by-day random walk to target)
- Default: gradual (more realistic)
- Both modes available, each with clear disclaimers about what they represent
- Detailed disclaimer section explaining: sudden overstates gains (theoretical max), gradual introduces path dependency (more realistic but varies)

### Time Dimension
- Claude's Discretion: holding period approach (default days, multi-period, etc.)

### Output Presentation
- Rich table with summary: side-by-side comparison (SQQQ vs Puts columns) per scenario
- Followed by plain-English summary/recommendation
- Recommendation included: "Based on your portfolio and scenarios, [strategy] is more cost-effective for protection beyond [threshold]"
- Highlight which strategy wins per scenario
- Cost detail: total cost + per-day cost for each strategy (SQQQ decay cost vs put premium)
- `--output json` supported for programmatic/agent use

### Decay & IV Communication
- SQQQ decay: show BOTH simple (-3x) and day-by-day compounded columns side by side, so user sees exactly where the gap comes from
- IV expansion: VIX-based estimate using VIX-SPX regression, with disclaimer that it's an estimate based on historical relationship
- Assumptions section at bottom of output listing all assumptions: daily rebalance ratio, IV model used, risk-free rate, put style, holding period, etc.

### Validation & Trust Signals
- Historical backtest comparison in output: run simulation against actual SQQQ/QQQ data from known drawdowns (2020 COVID, 2022 bear), show model vs actual with error percentage
- Known-answer test suite validates against ProShares prospectus return tables
- Sources section in output: cite yfinance (prices), CBOE (VIX), ProShares prospectus (rebalance methodology)
- Per-scenario confidence levels: "High confidence: -10% correction (well-modeled). Medium confidence: -40% crash (IV model extrapolated)"
- Black-Scholes with intrinsic value floor for American puts, plus disclaimer: "Put pricing uses Black-Scholes with intrinsic value floor. American exercise premium not modeled."

### Claude's Discretion
- Holding period approach (default duration, whether to show multi-period)
- Exact table formatting and color/styling in terminal
- VIX-SPX regression parameters (from research)
- Gradual mode random walk implementation details
- Interactive menu library choice (questionary or similar)

</decisions>

<specifics>
## Specific Ideas

- Interactive selector is primary UX -- agents invoke AskUserQuestion, CLI presents multi-select menu
- The tool should feel like a decision support tool, not just a calculator -- the recommendation and confidence levels are important
- Transparency is key: every number should be traceable to its assumption
- Historical comparison section builds trust by showing the model works on real data

</specifics>

<deferred>
## Deferred Ideas

None -- discussion stayed within phase scope

</deferred>

---

*Phase: 09-sqqq-vs-puts-comparison*
*Context gathered: 2026-02-03*
