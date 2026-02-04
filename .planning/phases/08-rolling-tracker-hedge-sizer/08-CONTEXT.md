# Phase 8: Rolling Tracker & Hedge Sizer - Context

**Gathered:** 2026-02-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Two CLI tools for options position management: Rolling Tracker monitors existing hedge positions (status, roll alerts, roll logging, history) and Hedge Sizer recommends contract counts for new hedges. Both follow the established 3-layer architecture (Pydantic -> Calculator -> CLI). Hedge comparison (SQQQ vs puts) is Phase 9.

</domain>

<decisions>
## Implementation Decisions

### Position tracking workflow
- Positions enter the system via both manual CLI entry (`log-position` command) and Fidelity CSV import
- Positions auto-detected as expired when DTE reaches 0 -- system marks them and user confirms or overrides
- Each position stores essentials + context: ticker, strike, expiry, quantity, cost basis, type (put/call), date opened, plus reason for hedge, target portfolio value at time, and which layer it protects
- Active positions in `positions.yaml`, completed rolls and expired positions in separate `roll-history.yaml`

### Roll alert behavior
- Fixed 7-day DTE roll window (not configurable)
- Replacement candidates ranked by optimized strike + expiry (best value via delta-adjusted or per-day cost), not just cheapest or same-strike
- Top 3 replacement candidates shown per position
- Live options chain scan every time (no caching)

### Contract sizing logic
- Default ratio 1 contract per $50k portfolio value, configurable via `--ratio` CLI flag and config file
- Portfolio value auto-detected from latest `notebooks/updates/Portfolio_Positions_*.csv` file (sum of Current Value column), with `--portfolio` CLI flag as override
- Multi-underlying budget allocation weighted by portfolio exposure (how much of portfolio each underlying represents)
- Budget warning at 80% utilization of monthly hedge allocation ($800/month from user-profile.yaml)

### Output and display
- `status` command displays ASCII table with columns: Ticker, Strike, Expiry, DTE, Qty, Cost, Current Value, P&L, P&L%
- Summary row at bottom showing: total hedge cost, total current value, total P&L, and portfolio coverage percentage
- DTE urgency uses both color coding (Green >14, Yellow 7-14, Red <7) and text markers ([ROLL], [EXPIRING]) for accessibility
- All commands (status, suggest-roll, log-roll, history, and sizer) support `--output json` for programmatic use

### Claude's Discretion
- Exact ASCII table formatting library choice (rich, tabulate, or custom)
- Options chain API error handling and retry logic
- CSV import parsing details and edge case handling
- Exact delta-adjusted ranking formula for replacement candidates
- Internal data validation between positions.yaml and roll-history.yaml

</decisions>

<specifics>
## Specific Ideas

- Portfolio value should come from the latest Fidelity CSV export (`notebooks/updates/Portfolio_Positions_*.csv`) rather than user-profile.yaml, because the profile is not auto-updated and may be stale
- Budget warning threshold at 80% leaves room for adjustments rather than warning only at full utilization
- Text markers alongside color coding ensures output works in color-blind scenarios and when piped to files

</specifics>

<deferred>
## Deferred Ideas

None -- discussion stayed within phase scope

</deferred>

---

*Phase: 08-rolling-tracker-hedge-sizer*
*Context gathered: 2026-02-03*
