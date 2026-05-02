# Rationale Playbooks — Cribbed from 18 Gold-Standard Tickets

Reusable "why this deployment" scaffolds organized by deployment type. Use as starting scaffold, not a template-paste — always adapt to the current portfolio state and deployment context.

## Layer 2 / Dividend Reinforcement

**Scaffold** (derived from `buy-ticket-2026-04-21-layer2-reinforcement.md`):

> **Why Layer 2 reinforcement (not Layer 1 growth or balanced):**
>
> 1. Current dividend run-rate is $[rate] vs YTD average of $[ytd]. Coverage ratio at Fidelity's [rate]% margin rate ($[interest]/mo) needs every tailwind. Strengthening income directly widens net margin spread.
>
> 2. Layer 1 growth exposure ([tickers]) = [X]% of portfolio. Adding more growth compounds concentration without solving the coverage math. Layer 2 is the binding constraint.
>
> 3. Framework (`margin-strategy.md`) Tier [1/2/3/4] at current [X]% margin utilization. Tier 1 prefers quality covered-call ETFs (JEPI/JEPQ/QQQI/SPYI family) over YieldMax single-stock products.
>
> 4. [No new tickers — doubles down on roster incumbents | Adding [new ticker] to diversify within Layer 2].

**Allocation scaffold**:

> - **JEPI [X]%**: S&P 500 covered-call premium income. Monthly pay, ~$[y]/sh = ~$[m]/mo income.
> - **JEPQ [X]%**: NDX covered-call premium income. Monthly pay, ~$[y]/sh = ~$[m]/mo.
> - **QQQI [X]%**: NEOS NDX high-income. Monthly pay.
> - **SPYI [X]%**: NEOS S&P 500 high-income. Monthly pay.
>
> Weighting rationale: [JEPI/JEPQ-heavy for JPM predictability | QQQI/SPYI-heavy for higher yield | 50/50 split for S&P-vs-NDX balance to match hedge structure].

## Growth DCA

**Scaffold**:

> **Why DCA into [tickers] at this level:**
>
> 1. [Ticker] has pulled back [X]% from recent high / is consolidating at [level] / broke out above [level]. Technical setup supports scaling in.
>
> 2. Fundamental thesis: [brief, cite research or framework]. No material change since last deployment.
>
> 3. Current position: [N] shares at avg cost $[x]. Adding $[y] at $[z] brings avg cost to $[new] and total position to [P]% of portfolio — [within / approaching / above] the [30%] concentration limit.
>
> 4. Framework (`margin-strategy.md`): Layer 1 growth layer mandate remains [X]% of portfolio; current Layer 1 = [Y]% so [under / over]-allocated.

## Paycheck Deployment

**Scaffold** (derived from `buy-ticket-2026-01-16-avanade-jan13.md` and `buy-ticket-2026-02-17-3-paycheck-catchup.md`):

> **Source of funds**: [Employer] paycheck on [date], deposited to Fidelity cash sweep. $[amount] after [tax withholding / 401k contribution / HSA].
>
> **Why [deployment strategy] for this paycheck:**
>
> 1. Cashflow policy (`cashflow-policy.md`): paychecks deploy within [N] business days; keep $[reserve] cash buffer; split [X]% Layer 2 / [Y]% Layer 1 per current phase.
>
> 2. Current cash balance pre-deploy: $[amount]. Post-deploy buffer: $[amount] (target $[target]).
>
> 3. [Any catchup context if paychecks accumulated]

## Rebalance Deployment

**Scaffold** (derived from `buy-ticket-2026-04-01-rebalance-deploy.md`):

> **Rebalance diagnosis:**
>
> 1. Current allocation vs target: [list deltas, e.g., "Layer 1 at 55% vs target 50% = +5% over"]
> 2. Underweight categories to feed: [list]
> 3. Overweight not being trimmed because: [tax lot / conviction / transaction cost reason]
>
> **Why this rebalance (vs wait for paycheck or trim overweight):**
>
> - [Specific trigger: quarter-end, distribution landed, significant market move]
> - Tax consideration: [realized gains avoided by feeding underweight rather than trimming]

## Consolidation / Scale-In

**Scaffold** (derived from `buy-ticket-2025-12-11-consolidation.md` and `buy-ticket-2025-12-09-parr-scale-in.md`):

> **Consolidation rationale:**
>
> 1. Position [ticker] currently at [N] shares spread across [Cash / Margin / Roth] accounts. Consolidating into [target account] to simplify tracking and align with [tax / strategy / dividend-eligibility] goal.
>
> 2. Net position size unchanged; this is an accounting movement, not new exposure.
>
> 3. Execution: [sell in account A, buy in account B, net zero portfolio change].

## When none of these fit

Write the rationale fresh. Reference frameworks directly. The scaffolds are starting points, not constraints. A novel deployment context deserves a novel rationale.

## What makes a rationale "gold standard"

Re-read `buy-ticket-2026-04-21-layer2-reinforcement.md` if unsure. The qualities that matter:

1. **Numeric anchoring** — every claim ties to a number (coverage ratio, utilization %, dividend rate)
2. **Framework citation** — named file, named tier/band, named rule
3. **Alternative consideration** — briefly states why the alternative (Layer 1, trim, different ticker) was rejected
4. **Portfolio state awareness** — references specific current holdings and weights, not generic assertions
5. **Risk acknowledgment** — states the tradeoff being accepted (upside cap, concentration, yield compression)

If the rationale reads like it could apply to any portfolio on any day, it's too generic. Re-write with specifics.
