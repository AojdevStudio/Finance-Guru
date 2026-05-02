---
name: fin-guru-buy-ticket
description: Orchestrates Finance Guru capital-deployment buy tickets. Invoke only when the user explicitly asks to draft a buy ticket, deploy cash, deploy a paycheck, allocate $X to a layer/category, or generate a deployment ticket. Do NOT self-invoke on paycheck detection, cash-balance changes, or any automatic signal — this skill runs only when the user says it runs. Loads the latest Fidelity positions, captures a price snapshot, runs ITC risk advisory for supported tickers, builds the allocation table, enforces pre-flight gates, and writes a compliant buy ticket to `fin-guru-private/fin-guru/tickets/`. Use whenever the user mentions: "buy ticket", "deploy cash", "deploy the paycheck", "deploy $X into Y", "allocate into layer 1/2", "DCA into X", "draft a deployment", "generate a ticket for [tickers]", "rebalance $X".
---

# Finance Guru Buy Ticket Skill

Orchestrates the 10-step capital-deployment workflow into a compliant buy ticket. **User-invoked only.** This skill is the canonical entrypoint for all buy tickets; the generic `fin-guru-create-doc` skill delegates here.

## When to Invoke

Invoke when the user says any of:

- "Make me a buy ticket" / "draft a buy ticket"
- "Deploy $X into [layer 2 / dividends / growth / QQQI / etc.]"
- "Deploy the [Avanade / K2SHA / Goucher] paycheck"
- "Allocate $X to [tickers]"
- "Rebalance $X into whatever is underweight"
- "Generate a deployment ticket"

**Do not invoke** from portfolio-state triggers (cash arrival, balance changes, rebalance signals). Those would require a hook, not a skill. Wait for the user.

## Workflow — 10 Enforced Steps

### Step 1: Temporal Awareness

```bash
date
date +"%Y-%m-%d"
```

Store `{current_datetime}` and `{current_date}` in working memory. Every buy ticket frontmatter needs this.

### Step 2: Load Portfolio Context

Find the latest Fidelity positions CSV by date-in-filename:

```bash
ls -t notebooks/updates/Portfolio_Positions_*.csv | head -1
```

Read the file. Extract:

- Total portfolio value
- Cash available (SPAXX + settled cash)
- Margin balance and utilization %
- Top holdings + concentration %
- Any same-day balance CSV (`Balances_for_Account_*.csv`) if present for margin debit / buying power

**Freshness check**: if the file is more than 2 days old, warn the user and ask if they want to continue with stale data or re-sync from Fidelity first.

### Step 3: Capture Price Snapshot

Primary:

```bash
uv run python src/utils/market_data.py TICKER1 TICKER2 TICKER3
```

**Graceful degradation**: `market_data.py` has had circular-import failures historically. If the command fails, fall back to the `Last Price` column from the positions CSV and annotate the ticket's `price_snapshot_as_of` field accordingly (e.g., `"Apr-21-2026 (Fidelity Portfolio_Positions CSV — market_data.py unavailable)"`). Never skip the price field.

Record the exact timestamp + source in the YAML frontmatter.

### Step 4: Build Allocation Table

From user-provided deployment amount + category weights:

- Weights must sum to 100%
- `shares = amount / price` — preserve fractional precision (Fidelity supports fractional fills on most tickers)
- Build the Execution Summary table matching `fin-guru/templates/buy-ticket-template.md`
- Totals row confirms dollar sum matches deployment amount (rounding tolerance: ±$0.01)

### Step 5: ITC Risk Advisory (Optional, Non-Blocking)

For each ticker, check if it's in the ITC universe. Supported tradfi: TSLA, AAPL, MSTR, NFLX, DXY, XAUUSD, and similar. Supported crypto: BTC, ETH, BNB, SOL, and similar. If supported:

```bash
uv run python src/analysis/itc_risk_cli.py TICKER --universe tradfi
uv run python src/analysis/itc_risk_cli.py TICKER --universe crypto
```

Interpret the score:

- 0.0–0.3 → 🟢 LOW — no advisory needed
- 0.3–0.7 → 🟡 MEDIUM — mention in risk notes, no advisory block
- 0.7–1.0 → 🔴 HIGH — add ITC Advisory section with reduced-position-size suggestion or staging guidance

If unsupported (most ETFs, covered-call funds), set `itc_applicability: unsupported` and **omit the ITC Advisory section entirely**. Do not include an empty block.

Never block ticket generation on ITC unavailability.

### Step 6: Load Strategy Frameworks

For a Layer 2 / dividend deployment, read:
- `fin-guru/data/margin-strategy.md`
- `fin-guru/data/dividend-framework.md`
- `fin-guru/data/modern-income-vehicles.md`

For a Layer 1 / growth deployment, read:
- `fin-guru/data/margin-strategy.md`
- Strategy documents relevant to growth holdings

For rebalancing:
- `fin-guru/data/margin-strategy.md`
- `fin-guru/data/cashflow-policy.md`

Cite the specific framework and section in the Strategy Rationale. Do not paste long excerpts — reference by name.

### Step 7: Fill the Template

Open `fin-guru/templates/buy-ticket-template.md`. Fill every placeholder. Required sections:

1. **YAML frontmatter** — all 11 fields. ITC fields: `supported` / `unsupported` / `not-run` and score 0.XX or N/A.
2. **Execution Summary** table with totals row
3. **Portfolio Context** — source CSV path + timestamps, cash before/after, remaining buffer
4. **Strategy Rationale** — why this deployment, why these weights, citing frameworks
5. **Execution Details** — price snapshot timestamp, fractional shares flag, DRIP status, monthly income target
6. **Risk Notes** — concentration, margin, volatility, position sizing
7. **ITC Advisory** — only when HIGH score; omit entirely otherwise
8. **Sources & Assumptions** — data source timestamps, sizing rationale, execution assumptions
9. **Progress Tracking** — month X of Y cycle, success probability if Monte Carlo was run, next planned deployment

### Step 8: Pre-Flight Gates (Warn, Don't Block)

Surface warnings if any of these trigger. User decides whether to proceed:

- **Cash buffer**: Remaining cash after deployment < $0 (would go negative or into margin unexpectedly)
- **Concentration**: Any single post-deploy position > 30% of portfolio
- **Margin coverage**: Dividend coverage of margin interest drops below 2× (fetch from margin dashboard context or calculate from CSV)
- **Stale data**: Positions CSV > 2 days old
- **Price staleness**: Price snapshot > 15 minutes old during market hours

Warnings go in Risk Notes, not as blocking errors.

### Step 9: Save the Ticket

Write to:

```
fin-guru-private/fin-guru/tickets/buy-ticket-{YYYY-MM-DD}-{descriptor}.md
```

Descriptor should be short and searchable:
- `layer2-reinforcement` / `layer2-deploy`
- `paycheck-catchup` / `w2-deployment` / `avanade-payroll`
- `dca-dip` / `rebalance-deploy`
- `ecat-addition` / `parr-scale-in` (ticker-specific)

### Step 10: Print a 5-Line Summary

After writing, tell the user (not more than 5 lines):

```
✅ Wrote: fin-guru-private/fin-guru/tickets/buy-ticket-YYYY-MM-DD-descriptor.md
Deployed: $X,XXX.XX across N tickers
Monthly income impact: +$X.XX (Y% effective yield)
Margin: $X,XXX.XX → $X,XXX.XX (utilization Z% → Z'%)
Next step: execute at Fidelity, confirm fills, then update DataHub
```

## Educational Disclaimer

Every ticket ends with:

> **Educational Notice:** For educational purposes only; not investment advice. Consult a licensed financial professional before acting. All investments involve risk, including possible loss of principal.

Extend with product-specific caveats when relevant (covered-call NAV erosion, single-stock volatility, margin interest risk).

## References

- `references/workflow-patterns.md` — full expansion of each step with example invocations and degraded-path handling
- `references/rationale-playbooks.md` — reusable "why this deployment" scaffolds cribbed from the 18 gold-standard tickets

## Templates

- Canonical template: `fin-guru/templates/buy-ticket-template.md` (do not modify; fill per workflow)

## Related Skills

- `fin-guru-hedge-roll` — for options lifecycle (open, roll, close); user-invoked separately
- `fin-guru-create-doc` — for non-buy-ticket documents (analysis, compliance memos, presentations)
- `margin-management` — for margin dashboard updates after deployments affect utilization
- `MonteCarlo` — for success-probability validation before major deployments (optional)
