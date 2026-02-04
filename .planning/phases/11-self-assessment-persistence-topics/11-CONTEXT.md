# Phase 11: Self-Assessment, Persistence & Additional Topics - Context

**Gathered:** 2026-02-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Add interactive self-assessment, localStorage persistence, and two new topic explorers (options-greeks, risk-management) to the knowledge explorer built in Phase 10. Users can track their understanding of financial concepts across sessions, choose learning modes that adjust prompt complexity, and explore two new comprehensive topic graphs. The template engine and build pipeline from Phase 10 are the foundation.

</domain>

<decisions>
## Implementation Decisions

### Knowledge State Cycling
- 4-state cycle: unknown (gray) -> familiar (blue) -> confident (green) -> mastered (gold)
- Color progression visual treatment — node color changes with each click
- Wrapping cycle — clicking mastered loops back to unknown
- "Reset All" button available to clear all states for a topic back to unknown
- States persist via localStorage (key per topic)

### Learning Modes Experience
- Three modes: Guided / Standard / Yolo (keep these exact names)
- Mode is **per-topic** — each topic remembers its own mode setting
- Top bar toggle — three buttons always visible at top of explorer (Guided | Standard | Yolo)
- Mode affects both prompt depth AND content visibility:
  - **Guided**: Basic "what is X?" prompts + prerequisite concepts highlighted
  - **Standard**: "Explain X with examples" prompts + related concepts shown
  - **Yolo**: "Analyze X in context of portfolio strategy with edge cases" prompts + everything unlocked
- Mode selection persisted in localStorage per topic

### New Topic Content Structure
- **Options-Greeks**: Comprehensive depth (~30+ nodes) — core 5 Greeks, second-order Greeks (charm, vanna), volatility surface, Greeks in portfolio context, strategies integration
- **Risk-Management**: Full risk framework (~25-30 nodes) — VaR, Sharpe, Beta, correlation, diversification, drawdown + hedging strategies, margin risk, tail risk, regime detection, position sizing
- **Cross-topic links**: Concepts that appear across topics show visual cross-references (e.g., "Theta" in options-greeks links to "covered call income" in dividends)
- **Portfolio-personalized**: Prompts reference actual portfolio positions and strategy (SQQQ, PLTR, JEPI, margin-living, DRIP v2) rather than generic examples

### Progress Visibility
- **Progress bar + fraction** at the top: "12/30 concepts mastered" with visual fill
- **Expandable state breakdown** below bar: counts per state (unknown/familiar/confident/mastered)
- **Completion threshold**: Confident + Mastered count toward progress bar (not just mastered)
- **Topic badges on landing page** (Phase 12): Each topic card shows completion percentage with tiered badges (bronze 33% / silver 66% / gold 100%)
- **Last studied timestamp**: Each topic shows relative time since last engagement ("Last studied: 3 days ago")
- Timestamp and progress stored in localStorage

### Claude's Discretion
- Exact node animations on state transitions
- Graph layout adjustments for larger concept graphs (30+ nodes)
- localStorage key naming and schema migration strategy
- Clipboard API fallback implementation details
- Exact color shades for the gray/blue/green/gold progression
- How cross-topic links are visually distinguished from within-topic edges

</decisions>

<specifics>
## Specific Ideas

- Keep the "Yolo" mode name — matches the aggressive investment personality
- Options-greeks should be comprehensive enough to support the SQQQ vs Puts comparison tool from Phase 9 (concepts like delta hedging, IV expansion, volatility drag)
- Risk-management should map to existing CLI tools (risk_metrics_cli, volatility_cli, correlation_cli) so users can go from concept understanding to running actual analysis
- Cross-topic links should feel like hyperlinks in a wiki — click to jump to that concept in the other topic's explorer
- Progress bar should be encouraging, not punishing — confident counts as progress, not just mastered

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 11-self-assessment-persistence-topics*
*Context gathered: 2026-02-03*
