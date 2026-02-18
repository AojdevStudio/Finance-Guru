<!-- Finance Guru(tm) Hedging Strategies | v1.0 | 2026-02-17 -->

# Hedging Strategies

## Disclaimer

This document is for _educational purposes only_ and does not constitute investment advice. Options trading involves substantial risk of loss and is not suitable for all investors. Consult a licensed financial advisor, tax professional, and legal counsel before implementing any hedging strategy. Past performance does not guarantee future results.

---

## Quick Reference

### When to Hedge

- Portfolio concentrated in growth/tech stocks with elevated downside risk
- Market regime shows elevated volatility (VIX > 20) or deteriorating breadth
- Upcoming macro catalyst (Fed meeting, earnings season, geopolitical event)
- Portfolio value crosses a threshold where a 20%+ drawdown would materially impact financial goals
- When peace of mind has quantifiable value -- like _homeowners insurance_, you pay a premium for the right to sleep at night

### Strategy Selection Matrix

| Strategy | Best For | Cost Profile | Protection Duration | Complexity |
|---|---|---|---|---|
| Protective Puts | Defined-risk portfolio insurance | Fixed premium (monthly) | Expires at chosen date | Low |
| Inverse ETFs (SQQQ, SH, SPXU) | Short-term tactical hedging | No premium; daily compounding drag | Must actively manage | Medium |
| Collar (buy put + sell call) | Reduced-cost hedging | Net credit or small debit | Expires at chosen date | High |

### Sizing Rules

- Approximately 1 put contract per ~$50,000 of portfolio value (each contract covers 100 shares of the underlying)
- Scale contracts proportionally: a $200,000 portfolio may warrant 3-4 contracts across multiple underlyings
- Never hedge more than you need -- over-hedging is a drag on returns

### Rolling Cadence

- Maintain approximately 30 DTE (days to expiration) for active protection
- Roll existing positions when they reach 5-7 DTE
- Evaluate replacement contracts at the time of roll for optimal strike and premium

### Strike Selection

- Target 10-20% OTM (out-of-the-money) for cost-efficient protection
- Closer strikes (5-10% OTM) cost more but provide tighter protection
- Further strikes (20-30% OTM) are cheaper but only pay out in severe drawdowns

### Budget Guideline

- Approximately $500-600/month for a ~$200,000 portfolio hedging program
- This equates to roughly 3-3.5% annualized cost of protection
- Compare this cost to the potential drawdown it prevents -- a 20% drawdown on $200,000 is $40,000

---

## Protective Put Strategy

### What It Is

A protective put is the purchase of a put option on an index or stock you hold (or are broadly exposed to). It grants the right to sell at the strike price before expiration, providing a _floor_ on losses.

Think of it like _homeowners insurance_: you pay a premium each period for the right to be made whole if disaster strikes. If the market stays flat or rises, the premium is the cost of protection -- peace of mind has value.

### How It Works

1. Buy a put option on the underlying (e.g., QQQ, SPY, IWM)
2. If the underlying drops below the strike price, the put gains value, offsetting portfolio losses
3. If the underlying stays above the strike, the put expires worthless and the premium is the total cost

### Cost Structure

- Premium per contract varies by underlying, strike, and expiration
- Each contract controls 100 shares of the underlying
- Example: A QQQ put at $380 strike (15% OTM from $450) with 30 DTE might cost $3.00-5.00 per share ($300-500 per contract)

### Payoff Profile

- _Maximum loss_: Premium paid (if market stays flat or rises)
- _Breakeven_: Strike price minus premium paid
- _Maximum gain_: Strike price minus zero (theoretically, if underlying drops to $0)

### Best For

- Defined-risk portfolio protection with a known maximum cost
- Investors who want to maintain upside exposure while capping downside
- Situations where you cannot or do not want to sell existing positions (tax considerations, conviction)

---

## Inverse ETF Strategy

### What It Is

Inverse ETFs (such as SQQQ, SH, SPXU) provide returns that are the _inverse_ of a benchmark index on a _daily_ basis. Buying SQQQ provides approximately -3x the daily return of the Nasdaq-100.

### Daily Compounding and Volatility Drag

Inverse ETFs reset daily. Over multi-day periods, compounding creates _volatility drag_:

- In a choppy, sideways market, the inverse ETF loses value even if the index ends flat
- In a sustained trend, the ETF may over- or under-perform the expected inverse return
- This effect worsens with leverage (3x > 2x > 1x)

### Best For

- Short-term tactical hedging (days to 1-2 weeks)
- Situations where options are unavailable or impractical
- NOT suitable for long-term portfolio hedging due to compounding drag

### Caution

- These are _trading instruments_, not insurance policies
- Holding SQQQ for months will almost certainly erode capital even if the market declines
- Requires active monitoring and rebalancing

---

## Rolling Strategy

### Why Roll

Rolling maintains continuous protection. A put that is 5 DTE provides minimal remaining protection and decays rapidly. Rolling to a new 30 DTE contract restores the hedge.

Think of rolling like _renewing an insurance policy before it lapses_ -- you do not want a gap in coverage.

### When to Roll

- **Target**: Roll when the existing put reaches 5-7 DTE
- **Early roll**: Consider rolling earlier if the put is deep in-the-money (lock in gains) or if volatility has spiked (premiums are elevated)
- **Skip roll**: If the hedging thesis has changed (e.g., market risk has subsided), let the put expire

### How to Evaluate Replacement Contracts

1. Check the current implied volatility environment (higher IV = more expensive puts)
2. Compare the new premium to the original -- is the cost-to-roll acceptable?
3. Reassess strike selection: if the underlying has moved significantly, adjust the strike accordingly
4. Evaluate whether the same underlying still represents the best hedge for current portfolio exposure

### Cost-to-Roll Calculation

```
Cost to Roll = New Put Premium - Residual Value of Expiring Put
```

- If the expiring put has residual value (still slightly OTM or ATM), sell it before buying the new one
- Net cost = new premium minus sale proceeds of old put
- Track cumulative rolling costs to ensure the hedging budget stays on target

---

## Multi-Underlying Allocation

### Diversified Hedging

Rather than hedging entirely with one index put, spread protection across multiple underlyings to match actual portfolio exposure:

| Underlying | Represents | Suggested Weight |
|---|---|---|
| QQQ | Tech/growth exposure | 40-50% |
| SPY | Broad market / large-cap | 30-40% |
| IWM | Small-cap exposure | 10-20% |

### Weight Allocation Approach

- Map portfolio holdings to index proxies (tech-heavy portfolio = heavier QQQ weighting)
- Adjust weights based on concentration -- if 60% of portfolio is in tech, hedge more with QQQ
- Rebalance hedge allocation when portfolio composition changes materially

### Correlation Benefit

- Different indexes do not move in perfect lockstep
- Diversified hedging smooths out protection gaps during sector rotations
- In broad market selloffs, all three indexes decline, providing comprehensive coverage
- In sector-specific drawdowns (e.g., tech correction), the QQQ hedge pays out while SPY/IWM hedges retain value

---

## Sean's Analogies: The Three-Pillar Framework

These analogies, drawn from advisory discussions, provide intuitive framing for portfolio construction:

### Pillar 1: Insurance (Protective Puts)

_"Think of it like homeowners insurance. You pay a monthly premium, and if nothing bad happens, great -- you still have your house. If a tree falls on it, the insurance pays out. That's what a put does for your portfolio."_

Puts are the insurance layer. They cost money every month, and most months they expire worthless. But the one month the market drops 15%, they prevent catastrophic portfolio damage.

### Pillar 2: Rental Income (Dividends)

_"Dividend-paying stocks are like rental properties. You own the asset, and it pays you regular income whether the market is up or down. The rent check comes regardless of what Zillow says your property is worth this week."_

Dividends provide cash flow that can fund the insurance layer (puts) or be reinvested for compounding.

### Pillar 3: Equity Building (Growth Stocks)

_"Growth stocks are like building equity in a property. You are not getting cash flow today, but the value compounds over time. It is like owning a startup -- you reinvest everything back in and the payoff comes later."_

Growth positions drive long-term wealth accumulation. They need the insurance layer because they are the most volatile, and they are funded by the income layer during drawdowns.

---

This document is for _educational purposes only_. Options strategies carry risk of total premium loss. Past performance does not guarantee future results. Always consult qualified financial, tax, and legal advisors before implementing any hedging strategy.
