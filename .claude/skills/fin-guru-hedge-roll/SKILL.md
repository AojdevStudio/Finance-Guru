---
name: fin-guru-hedge-roll
description: Orchestrates the full options hedge lifecycle for protective puts on QQQ/SPY/IWM — opening new hedges, rolling existing hedges, and closing hedges when thesis changes. Invoke only when the user explicitly asks to open, roll, renew, or close options hedges. Do NOT self-invoke from DTE thresholds, VIX spikes, or rolling-tracker status — this skill runs only when the user says it runs. The skill infers OPEN | ROLL | CLOSE mode from the user's phrasing and asks for clarification if ambiguous. Writes a compliant options ticket to `fin-guru-private/fin-guru/tickets/rolls/`. Use whenever the user says: "roll the hedge", "roll my puts", "renew the hedge", "draft a roll ticket", "open a hedge", "start hedging", "put on protection", "draft an open ticket", "close the hedge", "unwind the puts", "close out protection", "draft a close ticket", "my hedges are at 7 DTE — roll them", "protective put", "options insurance".
---

# Finance Guru Hedge Lifecycle Skill

Orchestrates the complete options-hedge lifecycle: **open**, **roll**, **close**. One skill, three mode-branches, shared framework source (`hedging-strategies.md`) and toolchain (`rolling_tracker_cli`, `options_chain_cli`, `hedge_sizer_cli`). **User-invoked only.**

## When to Invoke

Invoke when the user says any of:

**OPEN mode:**
- "Open a hedge" / "start hedging" / "put on protection"
- "I don't have any puts yet — help me put on a hedge program"
- "Protect this portfolio with puts"

**ROLL mode:**
- "Roll the hedge" / "roll my puts" / "renew the hedge"
- "My hedges are at 7 DTE — roll them"
- "Draft a roll ticket for [date]"

**CLOSE mode:**
- "Close the hedge" / "close my puts" / "unwind the puts"
- "Hedge is no longer needed"
- "Close the [ticker] puts and keep the [ticker] ones" (partial close)

**Do not invoke** from portfolio-state triggers (DTE counter crossing 7, VIX spiking, rolling-tracker daily status). Those would require a hook or scheduled agent, not a skill. Wait for the user.

## Mode Selection — First Action of Skill

Determine mode from user phrasing. Do **not** auto-detect from portfolio state alone.

| User phrasing signals | Mode |
|---|---|
| "open", "start hedging", "put on protection", "I have no puts" | **OPEN** |
| "roll", "renew", "roll my puts", "at X DTE roll them" | **ROLL** |
| "close", "unwind", "close out", "remove the hedge" | **CLOSE** |

If phrasing is ambiguous (e.g., "manage my hedges"), ask the user:

> "I can help with three hedge actions: **Open** new hedges, **Roll** existing ones near expiration, or **Close** positions. Which one?"

Never guess from portfolio state alone.

See `references/mode-selection.md` for edge cases.

---

## Workflow — OPEN Mode (6 Steps)

Opens a new protective-put program from scratch or adds to an existing one.

### Step 1: Temporal Awareness

```bash
date
date +"%Y-%m-%d"
```

### Step 2: Load Portfolio Context

Same pattern as buy-ticket skill:

```bash
ls -t notebooks/updates/Portfolio_Positions_*.csv | head -1
```

Extract total value, concentration by ticker and inferred sector (tech vs broad vs small-cap). The concentration profile drives multi-underlying allocation.

### Step 3: Size the Hedge Program

Budget comes from `fin-guru/data/user-profile.yaml` under Layer 3 (default $800/mo if unspecified).

```bash
uv run python src/analysis/hedge_sizer_cli.py --portfolio-value <v> --budget <b> --output json
```

Compute target contract count (~1 per $50k portfolio). Allocate across underlyings:

- **Framework default weights**: QQQ 40-50%, SPY 30-40%, IWM 10-20%
- **Adjust to portfolio concentration**:
  - Tech-heavy (>50% in tech/growth) → QQQ weight up (50%+)
  - Broad diversified → weights closer to default
  - Small-cap exposure → IWM weight up; if no small-cap, drop IWM

### Step 4: Scan Option Chains

For each underlying, find 10-20% OTM puts with 25-35 DTE:

```bash
uv run python src/analysis/options_chain_cli.py QQQ --type put --otm-min 10 --otm-max 20 --days-min 25 --days-max 35 --output json
uv run python src/analysis/options_chain_cli.py SPY --type put --otm-min 10 --otm-max 20 --days-min 25 --days-max 35 --output json
uv run python src/analysis/options_chain_cli.py IWM --type put --otm-min 10 --otm-max 20 --days-min 25 --days-max 35 --output json
```

Rank by:
1. Cost efficiency (premium as % of strike)
2. Greeks stability (delta near -0.15 to -0.25 for 10-20% OTM)
3. Liquidity (tight bid-ask, high open interest)

Present top 2-3 candidates per underlying; let user pick.

### Step 5: Fill `hedge-open-ticket-template.md`

Required sections: Execution Summary, Portfolio Context, Sizing Rationale, Contract Selection Rationale, Budget Impact, First Roll Trigger, Risk Notes, Execution Checklist, Sources & Assumptions, Post-Open State (yaml for rolling_tracker seeding).

### Step 6: Save and Seed Tracker

Write to `fin-guru-private/fin-guru/tickets/rolls/hedge-open-{YYYY-MM-DD}-{descriptor}.md`.

Descriptor examples: `initial-put-program`, `tech-hedge-addition`, `pre-earnings-protection`.

After the user confirms fills, offer to seed the rolling tracker:

```bash
uv run python src/analysis/rolling_tracker_cli.py log-open --ticker QQQ --strike 480 --expiry 2026-06-19 --qty 2 --entry-premium 2.00
```

Run this only on user confirmation — never pre-emptively.

---

## Workflow — ROLL Mode (7 Steps)

Rolls existing positions at or near the 5-7 DTE framework trigger.

### Step 1: Temporal Awareness

```bash
date
date +"%Y-%m-%d"
```

### Step 2: Audit Current Positions

```bash
uv run python src/analysis/rolling_tracker_cli.py status --output json
```

For each position compute:
- DTE (flag `[ROLL]` if ≤ 7)
- Residual value (from current bid)
- P&L (residual − entry premium)
- OTM% (strike vs current spot)

If no positions show in tracker but user says they have hedges, ask:
> "The rolling tracker shows no positions. Did you open these outside the tracker? If so, let's seed them first — give me the ticker, strike, expiry, and quantity per leg."

### Step 3: Per-Position Roll Decision

For each flagged position, evaluate against `fin-guru/data/hedging-strategies.md` (lines 117-147):

- **Is the hedging thesis still valid?** (Portfolio still concentrated? VIX elevated? Macro catalyst pending?)
- **Is the put deep ITM?** → Consider early close to lock gains rather than roll
- **Has IV spiked?** → Early-roll rational if thesis holds (sell old high, buy new high); otherwise skip
- **Decision output**: ROLL | SKIP | ADJUST-STRIKE

See `references/roll-decision-tree.md` for full branching logic.

### Step 4: Scan Replacement Contracts

For ROLL and ADJUST-STRIKE decisions, scan chains:

```bash
uv run python src/analysis/options_chain_cli.py QQQ --type put --otm-min 10 --otm-max 20 --days-min 20 --days-max 45 --output json
```

Rank candidates by:
1. Cost-to-roll (`new_premium − old_residual`)
2. Greeks stability
3. Liquidity

Present top 3 per underlying.

### Step 5: Cost-to-Roll and Framework Check

For each roll:

```
cost_to_roll = new_premium * qty * 100 − old_residual_value
```

Check framework:

- Monthly amortized cost (total roll debit / months covered) ≤ budget?
- Strike 10-20% OTM on new legs?
- New DTE lands in 30-60 range (for 30-DTE maintenance after next roll)?
- Contract count still matches `portfolio_value / $50k`?

If portfolio composition shifted materially since last roll, re-weight across underlyings.

### Step 6: Fill `hedge-roll-ticket-template.md`

Modeled on the gold-standard `rolls/hedge-roll-2026-04-21-hedge-renewal.md`. Required sections: Execution Summary (leg-by-leg SELL TO CLOSE then BUY TO OPEN), Portfolio Context, Current Hedge State (DTE/residual/P&L table), Roll Strategy Rationale (why expiry, why strikes, why not collar, why not SQQQ), Sizing & Cost Verification (framework checklist), Risk Notes (IV, leg-risk, assignment, tax on closes), Execution Checklist (bid/ask to verify, hard-stop net debit), Sources & Assumptions.

### Step 7: Save and Log Roll

Write to `fin-guru-private/fin-guru/tickets/rolls/hedge-roll-{YYYY-MM-DD}-{descriptor}.md`.

Descriptor examples: `hedge-renewal`, `early-roll-iv-spike`, `may-to-jun-rotation`.

After fills confirmed, offer to log the roll:

```bash
uv run python src/analysis/rolling_tracker_cli.py log-roll --old-contract "QQQ 2026-05-15 525P" --new-contract "QQQ 2026-06-19 480P" --qty 2 --net-debit 300
```

---

## Workflow — CLOSE Mode (5 Steps)

Unwinds positions when thesis changes, gains need to be captured, or budget reallocates.

### Step 1: Temporal Awareness

```bash
date
date +"%Y-%m-%d"
```

### Step 2: Audit Positions

```bash
uv run python src/analysis/rolling_tracker_cli.py status --output json
```

For each position identify: residual value, P&L, holding duration, tax lot status (short-term vs long-term).

For partial close, confirm with user which legs to close vs retain.

### Step 3: Confirm Close Rationale

Ask user to specify rationale (or confirm if inferred from context):

- Thesis changed (VIX normalized, macro risk subsided, concentration reduced)
- Gain capture (deep ITM, lock in gains before theta)
- Budget reallocation (hedge dollars moving to other use)
- Strategy pivot (replacing with collar, inverse ETF, or going unhedged)

Cross-check against `hedging-strategies.md` line 129:
> "Skip roll: If the hedging thesis has changed (e.g., market risk has subsided), let the put expire"

If thesis-change is the rationale AND positions have meaningful residual value (> $0.50/sh), closing now captures more value than letting expire. Note this in rationale.

See `references/close-rationale-playbooks.md` for scaffolds.

### Step 4: Fill `hedge-close-ticket-template.md`

Required sections: Execution Summary (SELL TO CLOSE per leg with target mid), Position History (per-leg open-to-close P&L), Close Rationale, Tax Impact Summary (STCL/STCG per leg), Post-Close Portfolio State (exposure being accepted, drawdown scenarios), Optional Replacement Strategy (if pivoting), Risk Notes, Execution Checklist, Sources & Assumptions, Post-Close Actions.

**Critical**: the Post-Close Portfolio State must explicitly describe the downside exposure the user is accepting. A hedge close is irreversible without a new open ticket; the user must acknowledge what they're walking away from.

### Step 5: Save and Remove from Tracker

Write to `fin-guru-private/fin-guru/tickets/rolls/hedge-close-{YYYY-MM-DD}-{descriptor}.md`.

Descriptor examples: `thesis-change-close`, `full-unwind`, `qqq-only-close`.

After fills confirmed, offer to remove from tracker:

```bash
uv run python src/analysis/rolling_tracker_cli.py close-position --contract "QQQ 2026-05-15 525P" --qty 2 --close-premium 0.44
```

---

## Enforced Framework Invariants (All Modes)

Surface as warnings, not blocking errors. User decides whether to proceed.

| Invariant | Applies To | Source |
|---|---|---|
| ~30 DTE maintenance, roll at 5-7 DTE | ROLL | `hedging-strategies.md` lines 37-39 |
| Strike 10-20% OTM on new legs | OPEN, ROLL | `hedging-strategies.md` lines 42-45 |
| ~1 contract per $50k portfolio | OPEN, ROLL | `hedging-strategies.md` lines 31-33 |
| Monthly amortized cost ≤ budget | OPEN, ROLL | `user-profile.yaml` Layer 3 + `hedging-strategies.md` lines 47-51 |
| Multi-underlying weights QQQ 40-50% / SPY 30-40% / IWM 10-20% | OPEN, ROLL (if re-weighting) | `hedging-strategies.md` lines 150-174 |
| Never close-before-open within a roll without explicit leg-risk acceptance | ROLL | Ticket template execution order warning |
| Close-mode post-close exposure must be explicitly acknowledged | CLOSE | Template requirement |

## Graceful Degradation

| Failure | Fallback | Annotation |
|---|---|---|
| `rolling_tracker_cli` shows no positions but user says hedges exist | Ask user to seed positions first | Block mode execution until positions available |
| `options_chain_cli` fails (yfinance down) | Ask user for manual bid/ask from Fidelity | Annotate "Chain data user-provided" in Sources |
| `market_data.py` circular-import | Use CSV or proxy (VOO for SPY, etc.) | Annotate proxy method in Sources |
| `hedge_sizer_cli` unavailable | Manual calculation: portfolio_value / $50k | Annotate "Sizing calculated manually" |

## Educational Disclaimer

Every ticket ends with:

> **Educational Notice:** For educational purposes only; not investment advice. Options strategies carry risk of total premium loss. Past performance does not guarantee future results. Always consult qualified financial, tax, and legal advisors before implementing any hedging strategy.

Extend per mode:
- OPEN: "Opening a protective put program commits monthly premium that is lost if market rises or stays flat."
- CLOSE: "Closing a hedge removes portfolio protection; subsequent drawdowns are borne in full."

## References

- `references/mode-selection.md` — edge cases for inferring OPEN | ROLL | CLOSE from user phrasing
- `references/framework-rules.md` — invariants with "why" sourced from hedging-strategies.md and options-insurance-framework.md
- `references/roll-decision-tree.md` — ROLL vs SKIP vs ADJUST-STRIKE decision logic
- `references/close-rationale-playbooks.md` — canonical "why close" scaffolds

## Templates

- `fin-guru/templates/hedge-open-ticket-template.md`
- `fin-guru/templates/hedge-roll-ticket-template.md`
- `fin-guru/templates/hedge-close-ticket-template.md`

## Related Skills

- `fin-guru-buy-ticket` — for capital-deployment tickets (separate workflow; invoke independently)
- `margin-management` — for margin dashboard updates after roll costs affect utilization
- `fin-guru-create-doc` — for non-ticket documents (analysis reports on hedge performance, etc.)

## Gold-Standard Reference

Read `fin-guru-private/fin-guru/tickets/rolls/hedge-roll-2026-04-21-hedge-renewal.md` before generating the first ROLL ticket in a session. That document sets the quality bar: numeric anchoring, framework diagnostics per position, explicit rationale for strike/expiry/no-collar/no-SQQQ, tax treatment noted, hard-stop net debit.
