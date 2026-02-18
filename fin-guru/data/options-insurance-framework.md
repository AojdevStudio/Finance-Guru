<!-- Finance Guru(tm) Options Insurance Framework | v1.0 | 2026-02-17 -->

# Options Insurance Framework

## Disclaimer

This document is for _educational purposes only_ and does not constitute investment advice. Options trading involves substantial risk of loss and is not suitable for all investors. Consult a licensed financial advisor, tax professional, and legal counsel before implementing any options strategy. Past performance does not guarantee future results.

---

## The Insurance Analogy

The single most intuitive way to understand protective put options is through the lens of _homeowners insurance_. This analogy, drawn from Sean's advisory framework, maps directly onto every key concept.

### Homeowners Insurance = Protective Puts

| Insurance Concept | Options Equivalent | Explanation |
|---|---|---|
| Your home | Your portfolio (or underlying position) | The asset you are protecting |
| Insurance premium | Put option premium | The cost you pay for coverage |
| Policy term | Expiration date | How long the coverage lasts |
| Deductible | OTM amount (distance from current price to strike) | The loss you absorb before coverage kicks in |
| Coverage amount | Notional value of the put (strike x 100 shares) | The maximum payout if disaster strikes |
| Filing a claim | Put going in-the-money | The event that triggers your protection |
| Policy renewal | Rolling the put to a new expiration | Maintaining continuous coverage |

### The Core Logic

1. _You pay a premium for a coverage period._ Just like homeowners insurance, you pay upfront for protection that lasts a defined period (the option's expiration).

2. _If nothing bad happens, the premium is the cost of peace of mind._ Most months, nothing catastrophic happens. The put expires worthless, and the premium you paid was the price of sleeping soundly. This is not wasted money -- it is the cost of defined risk.

3. _If disaster strikes, insurance pays out._ If the market drops sharply, the put gains value, offsetting your portfolio losses. The insurance analogy holds perfectly: you do not want to use it, but when you need it, it is invaluable.

4. _Coverage amount (notional) vs premium cost vs deductible (OTM amount)._ A deeper OTM put is like a higher-deductible policy: cheaper premium, but you absorb more loss before coverage kicks in. An ATM put is like a zero-deductible policy: expensive, but protection starts immediately.

---

## Options Terminology as Insurance Terms

For anyone coming from a non-options background, mapping options jargon to insurance language makes the concepts immediately accessible:

### Premium = Insurance Premium

The price you pay to buy the put option. This is your maximum loss if the market stays flat or rises. It is paid upfront and is non-refundable, just like an insurance premium.

### Strike Price = Deductible Threshold

The strike price is the level at which your protection begins to pay out. The gap between the current market price and the strike price is your "deductible" -- the loss you absorb before the put starts generating value.

- _Higher strike_ (closer to current price) = lower deductible = more expensive
- _Lower strike_ (further from current price) = higher deductible = cheaper

### Expiration = Policy Term

The expiration date is when your coverage ends. After this date, the put no longer provides any protection. This is why _rolling_ (renewing before expiration) is critical for maintaining continuous coverage.

### In-the-Money = Claim Triggered

When the underlying price drops below the strike price, the put is "in the money" -- your claim has been triggered. The put now has intrinsic value equal to the difference between the strike price and the current price.

### Rolling = Policy Renewal

When your current put approaches expiration, you sell it (if it has residual value) and buy a new one with a later expiration. This is the options equivalent of renewing your insurance policy before it lapses.

---

## Black-Scholes and American Options (BS-01)

### The BS Model Assumes European Exercise

The Black-Scholes model, the foundational options pricing formula, assumes _European-style_ exercise: the option can only be exercised _at expiration_, not before. This simplification makes the math elegant but introduces a limitation for US equity options.

### US Equity Options Are American-Style

All standard US equity and ETF options are _American-style_: the holder can exercise _at any time_ before expiration. This means:

- A deep in-the-money American put can be exercised immediately for its intrinsic value
- The BS model may _undervalue_ deep ITM puts near expiry because it does not account for early exercise
- American options are always worth _at least_ as much as their European counterparts

### Limitation: BS Can Undervalue Deep ITM Puts Near Expiry

When a put is deep in-the-money and close to expiration:

- The BS model may price it below intrinsic value (because European exercise would wait until expiry)
- The actual market price will not drop below intrinsic value because any rational holder would exercise
- This creates a pricing floor that BS does not naturally capture

### Intrinsic Value Floor

For American-style puts, the minimum value is:

```
American Put Price >= max(Strike - Spot Price, 0)
```

This _intrinsic value floor_ is enforced by the market. No American put will trade below its intrinsic value because arbitrageurs would buy and immediately exercise.

### Finance Guru's Adjustment

When Finance Guru tools calculate option values, they apply this American-style adjustment:

- If the BS-calculated value falls below intrinsic value, the intrinsic value is used as the floor
- This ensures that pricing recommendations are realistic for US equity markets
- The adjustment is most significant for deep ITM puts with short time to expiration

---

## When Insurance Does Not Pay

Understanding when hedging costs money without providing benefit is essential for managing expectations and budgeting.

### Time Decay (Theta)

Every day that passes, the put loses a small amount of value -- even if nothing else changes. This is _theta decay_, and it accelerates as expiration approaches. It is the "interest" you pay on your insurance policy over time.

### Market Stays Flat or Rises

If the market stays flat or rises, the put expires worthless. The premium paid is gone. This is the _expected_ outcome most of the time -- insurance companies make money because most houses do not burn down.

### Cost of Protection Over Time

Continuous hedging (rolling puts month after month) creates a cumulative cost. Over a year, this might total 3-4% of portfolio value. This is a real drag on returns during bull markets.

### When to Self-Insure vs Buy Protection

Consider self-insuring (no puts) when:

- Portfolio is already well-diversified with low concentration risk
- Cash reserves are sufficient to weather a drawdown without forced selling
- Time horizon is long enough to ride out multi-year drawdowns
- Hedging cost exceeds the expected benefit given current volatility

Consider buying protection when:

- Portfolio is concentrated in a small number of positions
- A significant drawdown would force selling at the worst time (margin calls, life events)
- Elevated market risk (high valuations, macro uncertainty, earnings season)
- Peace of mind has genuine utility -- stress reduction has real value

---

## Sean's Three-Pillar Framework

This framework, drawn from advisory discussions with Sean, provides an intuitive structure for thinking about portfolio construction as a system of interconnected roles.

### Pillar 1: Insurance (Puts) -- Protect What You Have

_"Think of it like homeowners insurance. You pay a monthly premium, and if nothing bad happens, great -- you still have your house. If a tree falls on it, the insurance pays out. That is what a put does for your portfolio."_

- Protective puts are the insurance layer
- They cost money every month, and most months they expire worthless
- But the one month the market drops 15%, they prevent catastrophic portfolio damage
- The premium is the _known, bounded cost_ of preventing an _unknown, unbounded loss_

### Pillar 2: Rental Income (Dividends) -- Generate Cash Flow

_"Dividend-paying stocks are like rental properties. You own the asset, and it pays you regular income whether the market is up or down. The rent check comes regardless of what Zillow says your property is worth this week."_

- Dividends provide cash flow that is somewhat independent of price action
- This income can fund the insurance layer (paying put premiums from dividend income)
- DRIP (dividend reinvestment) compounds the income stream over time
- In drawdowns, dividend income continues even as prices decline

### Pillar 3: Equity Building (Growth Stocks) -- Compound Wealth

_"Growth stocks are like building equity in a property. You are not getting cash flow today, but the value compounds over time. It is like owning a startup -- you reinvest everything back in and the payoff comes later."_

- Growth positions drive long-term wealth accumulation
- They are the most volatile component and benefit the most from insurance protection
- In drawdowns, the income layer (dividends) can fund reinvestment into growth at lower prices
- The three pillars form a self-reinforcing system: growth builds value, income generates cash flow, insurance prevents catastrophic loss

### How the Pillars Interact

```
                   [Insurance / Puts]
                   Protects portfolio
                        |
              Funded by |
                        v
               [Income / Dividends]
               Generates cash flow
                        |
           Reinvested   | into
                        v
              [Growth / Equity Building]
              Compounds wealth over time
                        |
              Increases | value of
                        v
               [Portfolio Value]
               Which needs more [Insurance]
```

The system is circular: as the portfolio grows, the insurance need grows, but the income to fund it also grows. A well-constructed portfolio balances all three pillars.

---

This document is for _educational purposes only_. Options strategies carry risk of total premium loss. The Black-Scholes model and its adjustments are approximations, not guarantees of market pricing. Always consult qualified financial, tax, and legal advisors before implementing any options strategy.
