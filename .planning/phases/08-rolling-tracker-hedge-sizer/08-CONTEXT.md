# Phase 8: Rolling Tracker & Hedge Sizer - Context

**Gathered:** 2026-02-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Two CLI tools for options position management: Rolling Tracker monitors existing hedge positions (status, roll alerts, roll logging, history) and Hedge Sizer recommends contract counts for new hedges. Both follow the established 3-layer architecture (Pydantic -> Calculator -> CLI). Knowledge base files for agent consumption are also in scope. Hedge comparison (SQQQ vs puts) is Phase 9.

</domain>

<decisions>
## Implementation Decisions

### Position status display
- Color + label for roll alerts: positions within the roll window get `[ROLL NEEDED]` in colored text next to the position, with DTE highlighted
- Always fetch live option prices from Finnhub on every `status` call -- live pricing is the default, no --live flag needed
- Important: live option pricing uses Finnhub API, NOT yfinance
- Expired positions auto-archive to roll-history.yaml and disappear from status output
- DTE urgency color coding: Green >14 days, Yellow 7-14 days, Red <7 days
- Text markers alongside color coding ([ROLL], [EXPIRING]) for accessibility and piped output
- Summary row at bottom: total hedge cost, total current value, total P&L, portfolio coverage percentage

### Roll suggestion behavior
- Fixed 7-day DTE roll window (not configurable)
- Show top 1 best match per expiring position (single recommendation, not multiple candidates)
- Rank replacement contracts by closest match to configured targets (target OTM%, target DTE)
- Show estimated cost-to-roll: "Roll cost: $X.XX (new premium $Y.YY - remaining value $Z.ZZ)"
- Log-roll auto-detects the old position from positions.yaml by ticker -- only new strike/expiry/premium needed as input
- Live options chain scan every time (no caching)

### Hedge sizing & budget allocation
- Default ratio 1 contract per $50k portfolio value, configurable via `--ratio` CLI flag and config file
- Portfolio value cascade: auto-read from latest Fidelity balance CSV (`notebooks/updates/Balances_for_Account_*.csv`, parses "Total account value" row) -> fall back to user-profile.yaml config -> accept --portfolio-value flag
- When monthly cost exceeds budget: warn but show full recommendation ("Recommended: $720/mo, Budget: $500/mo (44% over)") -- do NOT scale down to fit budget
- Contracts split equally across underlyings, remainder goes to the first underlying (e.g., 5 contracts across QQQ + SPY = 3 QQQ + 2 SPY)
- Show coverage ratio: e.g., "6 contracts cover ~$300k notional (148% of $202k portfolio)"
- All commands support `--output json` for programmatic use

### Knowledge base scope
- Two knowledge files for Phase 8: `hedging-strategies.md` and `options-insurance-framework.md`
- Structure: quick-reference decision framework at top, deeper reference explanations below
- Include Sean's analogies from the advisory session: homeowners insurance for puts, rental property for dividends, private equity for equity growth
- Source material: `.dev/meeting-notes/2026-01-30-paycheck-to-portfolio-sean-review.md`
- Four agents reference hedging knowledge: Strategy Advisor, Quant Analyst, Teaching Specialist, Compliance Officer

### Claude's Discretion
- Exact color choices for roll alert labels (red/yellow/green scheme details)
- Exact ASCII table formatting library choice (rich, tabulate, or custom)
- Options chain API error handling and retry logic
- How to handle Finnhub API errors gracefully (fallback to entry-cost-only with a warning)
- Exact structure and section ordering within knowledge base files
- Internal data validation between positions.yaml and roll-history.yaml

</decisions>

<specifics>
## Specific Ideas

- Live option pricing uses Finnhub API, NOT yfinance -- firm decision from {user_name}
- Sean's sizing rule: ~1 contract per $50,000 of portfolio value, ~$500-$600/month budget
- Rolling cadence: every 5-7 days to maintain ~30 DTE
- Strike selection: 10-20% OTM (below current price)
- The `options_chain scanner (scan_chain)` has known stderr side effects (noted in STATE.md) -- rolling tracker needs a clean wrapper (`scan_chain_quiet` per spec)
- Hedging integration spec at `.dev/specs/backlog/finance-guru-hedging-integration.md` has full model definitions and CLI interfaces
- Text markers alongside color coding ensures output works in color-blind scenarios and when piped to files

</specifics>

<deferred>
## Deferred Ideas

None -- discussion stayed within phase scope

</deferred>

---

*Phase: 08-rolling-tracker-hedge-sizer*
*Context gathered: 2026-02-17 (updated from 2026-02-03)*
