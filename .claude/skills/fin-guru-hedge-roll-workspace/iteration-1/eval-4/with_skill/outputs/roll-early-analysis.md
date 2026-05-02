---
title: Early Roll Analysis — VIX Spike to 25, 12 DTE
date: 2026-04-22
type: decision-support
mode: ROLL
branch: 3 (IV Spike)
ticket_drafted: false
---

# Should You Roll Early? VIX 25 Spike | 12 DTE Puts

_Decision-support analysis. No ticket drafted yet. Confirm the recommended path to proceed._

---

## Decision Tree Walk-Through

### Branch 1: Is the hedging thesis still valid?

VIX at 25 signals elevated volatility — it sits above the 20-threshold that `hedging-strategies.md` (lines 13-19) cites as a "hedge now" trigger. A spike to 25 does _not_ indicate market risk has subsided; it indicates it has _increased_. The thesis is intact.

**Result: thesis valid → continue to Branch 2.**

---

### Branch 2: Is the put deep ITM?

The scenario assumes puts are OTM (a VIX reading of 25 is a moderate spike, not a crash). VIX 25 does not alone imply the underlying has fallen through the strike. Absent specific position data showing spot < strike × 0.97, we treat these as OTM.

**Result: OTM → continue to Branch 3.**

---

### Branch 3: Has IV spiked materially? ← _This is the operative branch._

VIX moved to 25 from a baseline that for most of 2025-2026 hovered in the 15-20 range. That represents approximately a 25-65% IV expansion depending on entry point — comfortably in the "spike" zone (Branch 3 threshold: IV up 30%+ from entry = spike).

**What the spike means for your positions at 12 DTE:**

| Factor | Effect |
|--------|--------|
| New puts (replacement legs) | Expensive — same strike/expiry costs 30-50%+ more premium than in a calm market |
| Your current puts (12 DTE, OTM) | Have gained _some_ value from IV lift — the vega component offset partial theta decay |
| Residual value of your puts | Higher than it would be at the same DTE in a flat-IV environment |
| Cost-to-roll | `new_premium − old_residual` → both legs are inflated; net cost may be modestly elevated |

**Decision Matrix entry:**

> Valid thesis | OTM | IV Spike | Stable composition → **ROLL** (possibly further OTM to manage cost)

---

## IV Impact on New Premiums

When VIX spikes, the entire put surface reprices upward. A replacement put that would cost $3.00-3.50 in a 17-VIX environment may run $4.20-5.50 at VIX 25 for the same strike and DTE. That is the premium you would be _entering_ at — locking in elevated protection cost.

Key consideration from `hedging-strategies.md` line 128:

> _"Early roll: Consider rolling earlier if… volatility has spiked (premiums are elevated)"_

The framework explicitly names IV spikes as a legitimate early-roll trigger. The logic: your old put has vega-lifted residual value right now. Selling it captures that residual before VIX normalizes (which would cause residual value to decay on _two_ axes simultaneously — theta AND vega compression).

---

## Residual Value of Your Current Puts (12 DTE, OTM)

At 12 DTE, your puts have two value components:

1. **Intrinsic value** — zero if OTM
2. **Extrinsic/time value** — meaningful, because VIX lift has temporarily inflated the implied move expectations priced into your contracts

In a normal (non-spike) environment, 12 DTE OTM puts might carry $0.40-0.80 per share in residual. At VIX 25, that same contract might carry $0.80-1.40. This is your window: the IV spike is temporarily _subsidizing_ your exit.

At 5-7 DTE (standard roll trigger), VIX normalization could have reduced that residual back toward $0.20-0.40. You would roll at the standard time but capture less credit on the old leg.

---

## Framework Citation

Source: `fin-guru/data/hedging-strategies.md`, Rolling Strategy section (lines 117-147):

> "Early roll: Consider rolling earlier if the put is deep in-the-money (lock in gains) or if volatility has spiked (premiums are elevated)"

The IV-spike early-roll is canonically supported. This is not an ad hoc deviation — it is Framework-documented behavior.

Additionally, `references/roll-decision-tree.md` Branch 3:

> "New puts will be expensive (paying more for same coverage). Old puts, if OTM, may have gained a little value on the IV-lift (partial offset). Decision: ROLL if thesis demands continued coverage regardless of cost; SKIP if cost breaches budget by > 50% and thesis can tolerate a gap."

Since VIX 25 is an elevated (not extreme) spike, the cost-to-roll will be higher than baseline but is unlikely to breach the >50% budget threshold. The thesis remains intact.

---

## Trade-off Summary

| Path | Pros | Cons |
|------|------|------|
| **Roll now (12 DTE)** | Captures vega-lifted residual on old puts; replaces coverage before VIX potentially spikes further; avoids gap exposure if market moves sharply in next 5 days | New puts expensive at current IV; locking in elevated entry premium; slightly early (framework says 5-7 DTE standard) |
| **Wait for 5-7 DTE** | Standard framework path; no deviation required | Residual value likely lower if VIX normalizes; still pay elevated new-put premium if VIX stays elevated; if VIX spikes further you're unhedged at an awkward DTE window |
| **Skip roll entirely** | Zero premium cost | Thesis intact (VIX 25 = risk elevated), going unhedged contradicts framework; not recommended |

---

## Recommended Action

**Roll now.**

Rationale:

1. **IV lift is a time-limited residual subsidy.** At 12 DTE, you still have enough time value in your current puts to sell at a meaningful credit. The vega component of residual value is high right now — that window narrows as VIX normalizes or time erodes both axes.

2. **The framework explicitly supports early rolls on IV spikes.** This is not breaking the framework; it is executing an optional branch the framework designed for exactly this scenario.

3. **VIX 25 confirms the thesis, not the exit.** This is not a "skip roll" scenario. The elevated volatility signal is why you hold protective puts in the first place.

4. **Strike adjustment advisory.** When selecting replacement contracts, consider going slightly _further_ OTM (12-18% vs the standard 10-15%) to reduce the impact of inflated premiums while maintaining meaningful crash protection. The savings on premium are real at VIX 25; the slightly wider strike still covers any -12%+ drawdown scenario.

**One caveat:** If you want to be precise, run the options chain to confirm the actual cost-to-roll before executing. Scan 30-45 DTE puts at 12-18% OTM on your underlyings and compare net debit to your monthly budget. If the net debit is more than 1.5× a normal month, consider waiting 3-5 days for a VIX pull-back before rolling. VIX 25 is elevated but not extreme.

---

## Next Step — Ticket Offer

If you'd like to proceed, I can draft a full roll ticket including:

- Leg-by-leg execution (SELL TO CLOSE expiring puts at current bid-mid, BUY TO OPEN replacement contracts at target strikes/expiries)
- Cost-to-roll calculation against your monthly budget
- Strike selection rationale (why further OTM under IV-spike conditions)
- Framework compliance checklist (30 DTE target, 10-20% OTM, contract count vs portfolio value)
- Execution checklist with hard-stop net debit
- Tax notes on the closing legs

**Just confirm:** _"Yes, draft the roll ticket"_ and I'll run the options chain scan and produce a compliant ticket to `fin-guru-private/fin-guru/tickets/rolls/`.

---

## 3-Line Summary

VIX 25 is a Branch 3 IV-spike scenario: your 12 DTE puts have vega-lifted residual value that will erode if volatility normalizes before expiry, making rolling now advantageous over waiting for the standard 5-7 DTE trigger. The framework (`hedging-strategies.md` line 128) explicitly supports early rolls on IV spikes, and the decision tree (Branch 3) confirms ROLL is correct when thesis is intact and the put is OTM. Recommended action is to roll now at a slightly further-OTM strike to offset elevated new-put premiums; no ticket drafted — confirm to proceed.

---

> **Educational Notice:** This analysis is for educational purposes only and does not constitute investment advice. Options strategies carry substantial risk, including total loss of premium paid. Past performance does not guarantee future results. Consult a qualified financial advisor, tax professional, and legal counsel before implementing any options strategy.
