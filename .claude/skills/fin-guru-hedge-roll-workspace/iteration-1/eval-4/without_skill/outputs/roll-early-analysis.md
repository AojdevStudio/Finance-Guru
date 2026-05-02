---
title: VIX Spike Roll Decision — 12 DTE Puts
date: 2026-04-22
context: VIX at 25, protective puts at 12 DTE
disclaimer: Educational only. Not investment advice. Options involve substantial risk of total premium loss. Consult a licensed financial advisor before acting.
---

# Should You Roll Early? VIX at 25, 12 DTE Puts

_Educational analysis only — not investment advice. Consult qualified financial, tax, and legal professionals before making any options decisions._

---

## Situation Summary

- **Current VIX**: 25 (elevated — above the 20 threshold that signals heightened market stress)
- **Days to Expiration (DTE)**: 12
- **Decision**: Roll now at elevated IV, or wait until the standard 5-7 DTE window?

---

## The Core Tension

When VIX spikes, two competing forces collide:

| Force | Effect | Favors |
|---|---|---|
| Elevated implied volatility (IV) | New puts are more expensive to buy | Waiting |
| Time decay acceleration (theta) | Puts lose value faster near expiration | Rolling early |
| Protective coverage gap risk | 12 DTE is not far from the 5-7 DTE danger zone | Rolling early |

At 12 DTE you are already within 5 days of the standard roll trigger (5-7 DTE). The standard cadence calls for rolling _before_ coverage lapses — not reacting to it.

---

## Why VIX at 25 Changes the Calculus

### The IV Spike Problem

A VIX reading of 25 means implied volatility is elevated market-wide. When you buy a new put right now, you are paying a premium inflated by fear. That is expensive insurance.

**However**, the put you _currently hold_ has also risen in value due to the same IV spike. If it has moved in-the-money or toward-the-money, it has residual value you can capture by selling it before buying the replacement.

This is the cost-to-roll calculation:

```
Cost to Roll = New Put Premium − Residual Value of Expiring Put
```

The current IV spike works _both ways_: your expiring put is worth more right now, which offsets some of the cost of the new (also expensive) put.

### The Key Question: Is Your Put In-the-Money or Still OTM?

- **If deep ITM**: The put has captured gains. Rolling early locks in those gains and re-establishes protection at a new strike. **Strong case for rolling now.**
- **If ATM or slightly OTM**: The put has risen in value but still has intrinsic time value. Rolling may still make sense to avoid theta erosion over the next 12 days during a volatile regime.
- **If still far OTM**: The put's residual value may be modest. The new put will be expensive. Waiting a few days for IV to compress (if it does) reduces the roll cost — but you accept gap risk.

---

## Decision Framework for 12 DTE in a VIX-25 Environment

### Recommendation: _Lean toward rolling now, with one caveat_

**Roll now if any of these are true:**

1. Your put is at-the-money or in-the-money — lock in gains and reload protection
2. You believe the market selloff has further to run (VIX could push higher, market could drop more)
3. Your portfolio composition is tech-heavy or concentrated in high-beta names — these move hardest in volatility spikes
4. The net cost-to-roll is acceptable: the residual value of your expiring put offsets the elevated new premium to a tolerable degree
5. You cannot actively monitor the position over the next 12 days

**Consider waiting (days, not weeks) if:**

1. Your put is still deep OTM with minimal residual value — rolling now means buying expensive premium at peak fear
2. You expect VIX to mean-revert quickly (VIX tends to spike and fade; at 25, it is elevated but not historically extreme)
3. You have 2-3 days of flexibility before hitting the 7 DTE hard floor — a brief wait for IV compression could reduce the new premium by meaningful dollars per contract
4. Your current put still has substantial time value — selling into this spike captures that value

### The Hard Floor Rule

Regardless of IV conditions: **do not let puts expire below 5-7 DTE without rolling or making a conscious decision to exit the hedge.** At 12 DTE you have a brief window — but it is not a large one.

---

## Practical Steps if Rolling Now

1. **Check residual value of expiring put**: Pull the current bid price. This is your sale credit.
2. **Price a 30 DTE replacement**: Target a strike 10-20% OTM from current underlying price.
3. **Calculate net cost to roll**: New premium minus residual credit.
4. **Assess strike**: Has the underlying dropped significantly? If so, the original OTM strike may now be ATM or ITM — consider whether to roll to the same dollar strike (locking in more protection) or reset to a new 10-20% OTM level (lower cost, lighter protection).
5. **Execute as a spread order** when possible: Sell the expiring put and buy the new one simultaneously to reduce slippage and execution risk.

---

## VIX Context: What 25 Means Historically

- VIX below 20: Low fear, complacent market
- VIX 20-30: Elevated concern, moderate stress
- VIX 30-40: Significant stress / correction territory
- VIX above 40: Crisis / panic (COVID, 2008)

At 25, you are in elevated-but-not-crisis territory. This is the regime where hedges matter most — and where rolling to maintain coverage is most defensible.

---

## Summary Judgment

At 12 DTE with VIX at 25:

- You are close enough to the 5-7 DTE trigger that the roll decision is effectively _now or very soon_
- The IV spike makes new puts expensive, but also makes your current put more valuable — the net cost-to-roll may be more reasonable than it appears
- If your put is ITM or near-ATM, rolling now is the right move: lock in gains and reload
- If your put is still far OTM, you have a narrow window to wait for minor IV compression — but do not let it lapse below 7 DTE unrolled

**Default action with no other information**: Roll now. The cost of a coverage gap during a VIX-25 spike exceeds the cost of paying elevated premium for a replacement.

---

_This document is for educational purposes only. Options trading involves substantial risk of loss. Past performance does not guarantee future results. Consult a licensed financial advisor, tax professional, and legal counsel before implementing any strategy._
