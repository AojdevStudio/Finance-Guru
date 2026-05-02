# Close Rationale Playbooks

Reusable scaffolds for the Close Rationale section of `hedge-close-ticket-template.md`. Use as starting points, always adapt to the specific trigger.

## Playbook A: Thesis Change

**When to use**: macro risk has materially subsided — VIX normalized, feared catalyst resolved, portfolio concentration reduced organically.

**Scaffold**:

> **Trigger for close**: Thesis changed.
>
> **Specific change**: [e.g., VIX fell from 35 peak on [date] to 15 current; Fed meeting on [date] resolved with no hawkish surprise; PLTR concentration reduced from 27.8% to 18% after trim on [date]].
>
> **Detailed reasoning**: The protective put program was opened on [date] when [specific risk signal]. That signal has now resolved as follows: [enumerate]. The cost-benefit of continuing to pay premium no longer supports the hedge.
>
> **Framework consistency** (hedging-strategies.md line 129): "Skip roll: If the hedging thesis has changed (e.g., market risk has subsided), let the put expire." This close aligns with skip-roll guidance, executed early to capture residual value of $[amount] rather than letting it decay to zero.

## Playbook B: Gain Capture (Deep ITM)

**When to use**: the hedge paid out during a drawdown and now has substantial residual value; locking the gain before it decays.

**Scaffold**:

> **Trigger for close**: Gain capture on deep-ITM positions.
>
> **Detailed reasoning**: The [UNDERLYING] puts were opened on [date] with strike $[strike] when spot was ~$[entry-spot]. Current spot is $[current-spot], putting the position [X]% ITM with residual value $[amount] per share (~[Y]× initial premium of $[premium]).
>
> Continuing to hold risks theta decay eroding the gain. Rolling would give up the realized gain in favor of re-hedging at a fresh 10-20% OTM strike; we are taking the gain instead.
>
> **Follow-up consideration**: If the drawdown regime is expected to continue, open a new protective put program at current 10-20% OTM strikes (separate OPEN ticket). Otherwise, redeploy the realized gain per budget.

## Playbook C: Budget Reallocation

**When to use**: hedge dollars are needed elsewhere (scaling growth, funding an opportunity, life-event liquidity).

**Scaffold**:

> **Trigger for close**: Budget reallocation.
>
> **Destination of funds**: [specific use — e.g., Layer 2 income deployment, life expense, opportunity capital]
>
> **Detailed reasoning**: The hedge program was running at $[monthly]/month per budget allocation in user-profile.yaml Layer 3. Closing these positions returns $[residual-credit] to cash and frees $[monthly] in ongoing budget that will redeploy to [destination].
>
> **Risk tradeoff accepted**: By closing, the portfolio is unhedged against [specific scenario]. This is accepted because [risk mitigation: e.g., reduced concentration, higher cash buffer, alternate hedging planned].

## Playbook D: Strategy Pivot

**When to use**: replacing protective puts with a different hedging approach (collar, inverse ETF, structured product).

**Scaffold**:

> **Trigger for close**: Strategy pivot from protective puts to [new strategy].
>
> **Detailed reasoning**: [Why the new strategy fits current conditions better. E.g., "Portfolio has rotated toward income-producing holdings where upside cap via short calls is acceptable; a collar structure reduces net hedging cost from $[old-monthly] to $[new-monthly] while maintaining downside floor."]
>
> **Follow-up**: Separate hedge-open ticket will document the new strategy. These positions must close first to free capital and avoid double-hedging.

## Playbook E: Partial Close (Mixed Rationale)

**When to use**: user wants to close some legs but keep others, typically because concentration changed unevenly.

**Scaffold**:

> **Trigger for close**: Partial unwind.
>
> **Legs being closed**: [list — e.g., "QQQ $525P (2x) expiring May 15"]
> **Legs being retained**: [list — e.g., "SPY $590P (2x) expiring May 15"]
>
> **Detailed reasoning per closed leg**: [Why this specific underlying no longer needs hedging — e.g., "Tech exposure reduced from 50% to 35% after PLTR trim; QQQ-specific hedge no longer proportional."]
>
> **Remaining hedge coverage**: After partial close, the portfolio retains $[notional] of SPY-based downside protection. This covers broad-market drawdown but not tech-specific drawdown. User acknowledges the asymmetric coverage.

## Playbook F: Hedge Expired Worthless (Retrospective Close)

**When to use**: hedge expired OTM during flat/up market; premium is a sunk cost; ticket is closing the books retrospectively.

**Scaffold**:

> **Trigger for close**: Position expired worthless on [expiry-date].
>
> **Detailed reasoning**: Protective puts opened [date] expired OTM as market moved from $[entry-spot] to $[expiry-spot]. Total premium paid of $[premium] is fully realized as loss. This is the expected "insurance premium" cost per the framework — a 70-80% premium-loss rate is normal for a hedge program during flat/up market regimes.
>
> **No action required at Fidelity**: Positions already expired; cash impact was recorded at expiration. This ticket documents the close for audit trail.
>
> **Program continuation**: [Decision on whether to continue program — usually yes if thesis still valid, in which case OPEN ticket follows.]

---

## What Every Close Rationale Must Include

Regardless of playbook:

1. **Specific trigger** — not generic "market changed"; name the signal
2. **Numerical justification** — residual value, realized P&L, cost-benefit
3. **Framework citation** — which line of `hedging-strategies.md` supports this action
4. **Forward-looking decision** — what comes next (nothing, replacement, continued unhedged)
5. **Risk acknowledgment** — specifically what downside the portfolio is now exposed to

A close rationale without at least these five elements is too thin. The post-close state section amplifies the risk acknowledgment quantitatively (-10% / -20% / -30% scenarios).
