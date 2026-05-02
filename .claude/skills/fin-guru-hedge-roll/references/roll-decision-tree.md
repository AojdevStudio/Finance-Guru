# Roll Decision Tree — ROLL vs SKIP vs ADJUST-STRIKE

Used by ROLL mode, step 3 (per-position roll decision). Evaluate each flagged position through this tree.

## Branch 1: Is the hedging thesis still valid?

Framework source: `hedging-strategies.md` lines 13-19 (when to hedge).

Check:
- Is the portfolio still concentrated in growth/tech? → thesis intact
- Is VIX still elevated, or has macro catalyst arrived and resolved? → thesis possibly resolved
- Is the user still in an accumulation phase where a 20%+ drawdown would materially damage financial goals? → thesis intact

**If thesis is no longer valid** → SKIP (let the put expire; recommend CLOSE mode for explicit unwind if the position has meaningful residual value > ~$0.50/sh)

**If thesis is intact** → continue to Branch 2.

---

## Branch 2: Is the put deep ITM?

Check: is current spot meaningfully below the strike? Specifically, is spot below (strike × 0.97)?

- **Deep ITM, 5%+ below strike**: The hedge paid out. Two options:
  - **Take the gain**: CLOSE the existing leg, realize the profit, and open a new put at a fresh 10-20% OTM strike (this is essentially a reset, not a roll). Use CLOSE mode then OPEN mode.
  - **Ride the protection**: If market volatility continues and thesis remains, ROLL to a new strike at the current 10-20% OTM level — but acknowledge you're giving up realized gains in favor of continued coverage.
  - **Which to pick**: depends on user preference and budget. Default recommendation: take the gain (CLOSE → OPEN at fresh strike) if residual > 2× initial premium; otherwise ROLL.

- **Slightly ITM or ATM**: Normal roll. Continue to Branch 3.

- **OTM (spot > strike)**: Normal case. Continue to Branch 3.

---

## Branch 3: Has IV spiked materially?

Check the current IV environment relative to entry:

- Compare current chain IV (from `options_chain_cli.py`) to the IV implied by the old put's entry premium
- If IV is up 30%+ from entry → spike
- If IV is up 10-30% → elevated but not spike
- If IV is flat or down → normal regime

**On IV spike**:
- New puts will be expensive (paying more for same coverage)
- Old puts, if OTM, may have gained a little value on the IV-lift (partial offset)
- Decision: ROLL if thesis demands continued coverage regardless of cost; SKIP if cost breaches budget by > 50% and thesis can tolerate a gap

**On normal IV**: Normal roll. Continue to Branch 4.

---

## Branch 4: Has the portfolio composition shifted materially?

Check: since last roll, has the mix of tickers changed enough to warrant re-weighting hedges?

Examples:
- Added significant IWM-like small-cap exposure → increase IWM weight in new roll
- Sold down a tech position → reduce QQQ weight
- Portfolio value grew or shrunk > 15% → adjust total contract count

**If composition shifted**: ADJUST-STRIKE or ADJUST-WEIGHT (which is a form of adjusted roll — different underlying allocation in the new legs).

**If stable**: Straight ROLL (same underlying, same strike distance).

---

## Branch 5: Is the specific strike still 10-20% OTM?

Check: given current spot and the old strike, what's the OTM %?

- **Strike 1.9% OTM** (like the April 2026 QQQ case) → too tight; ADJUST-STRIKE further OTM (cheaper premium, restores framework discipline)
- **Strike 8-12% OTM** → close to framework; acceptable to roll flat or slight adjustment
- **Strike 15-20% OTM** → in framework band; roll flat
- **Strike > 25% OTM** → too far; ADJUST-STRIKE closer (may have drifted during spot rally)

---

## Decision Summary Matrix

| Thesis | Moneyness | IV | Composition | Decision |
|---|---|---|---|---|
| Valid | OTM | Normal | Stable | **ROLL** (flat strike, new expiry) |
| Valid | OTM | Spike | Stable | **ROLL** (maybe further OTM to manage cost) |
| Valid | Deep ITM | Any | Any | **CLOSE + OPEN** (take gain, reset) or **ROLL** (give up gain for coverage) |
| Valid | OTM | Any | Shifted | **ADJUST-STRIKE** (re-weight underlyings or move strike) |
| Valid | Too tight (< 10%) | Any | Any | **ADJUST-STRIKE** (further OTM) |
| Valid | Too far (> 25%) | Any | Any | **ADJUST-STRIKE** (closer to spot) |
| Resolved | Any | Any | Any | **SKIP** (let expire, or CLOSE for residual) |

---

## Expressing the Decision in the Ticket

Whichever branch you land on, the Roll Strategy Rationale section of the hedge-roll-ticket-template.md must justify it:

- **Why this expiry?** (targets 30 DTE after next roll, avoids holiday week, etc.)
- **Why this strike?** (10-20% OTM target, cost efficiency, matched spot move)
- **Why not a collar?** (growth-layer conviction for user's specific tickers)
- **Why not SQQQ/inverse ETF?** (volatility drag on multi-week hold)

See the gold-standard `rolls/hedge-roll-2026-04-21-hedge-renewal.md` for how to phrase these — each "Why" gets 2-3 sentences tying back to framework and portfolio state.
