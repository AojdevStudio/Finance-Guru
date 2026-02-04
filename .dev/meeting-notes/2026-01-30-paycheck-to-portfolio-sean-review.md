---
title: Portfolio Review with Sean — Paycheck to Portfolio
date: 2026-01-30
type: meeting-notes
participants:
  - {user_name} (Client)
  - Sean (Advisor, Paycheck to Portfolio)
duration: ~40 minutes
tags: [portfolio, hedging, options, dividends, tax-strategy, living-off-portfolio]
privacy: private
---

# Portfolio Review — Sean (Paycheck to Portfolio)

**Date:** January 30, 2026
**Duration:** ~40 minutes

---

## 1. Purpose of the Call

- Confirm current portfolio structure and actions (selling assets, hedging, dividend funds, borrowing) are on the right path.
- Advisor framed the call as client-driven: high-level unless drilling into specifics.

---

## 2. Portfolio Context & Investing Evolution

**Evolution:**
- Started as FIRE / index-fund-only
- ~2020: Bitcoin accumulation phase → became Bitcoin maximalist, funneling household income into BTC
- Stopped accumulating BTC early 2023
- That experience built comfort with market risk, volatility, and individual stocks

**Current characteristics:**
- Fidelity account (primary)
- Notable individual stock positions (Tesla, Palantir, others)
- Custom tracker/spreadsheet combining Fidelity + other accounts with Google Finance data feeds
- Retirement accounts: mostly index funds (no dividend strategy there yet)
- Now incorporating dividend-paying funds (YMAX, MSTY, other high-yield/CEFs/covered call style funds)
- Exploring leverage (borrowing strategy) and hedging

---

## 3. Advisor's Core Framework: "Brokerage as Private Equity Business"

**Mental model:** Bitcoin accumulation strategy ≈ what advisor does in stocks:
- Concentrated capital funneling → net worth growth → borrow against equity (buy/borrow approach)

**Three-bucket approach:**
1. **Growth funds/holdings**: Build equity (grow "business value")
2. **Closed-end funds/income vehicles**: Accelerate compounding via distributions (often DRIP)
3. **Cash flow layer**: Service debt (margin interest) so portfolio stays fully invested

**Private equity analogy:**
- Acquiring "mom-and-pop" businesses, adding operational value, expanding, selling at higher valuation
- Mirrors buying stocks that grow in value
- Palantir gains = "added capital" (equity growth) — same mechanism PE relies on for profitable exits

---

## 4. Selling vs Borrowing — Tax Strategy

**Advisor stance:** Rarely sells
- Equity can be borrowed against; selling triggers taxes
- Highlighted tax cost of selling a gained position vs borrowing against it (no taxable event)

**Property tax context:**
- Bought home 2020, 20% down (FIRE influence)
- Refused escrow — believed it was effectively using his money
- Saved "escrow equivalent" in investment account (M1)
- Each year, sold portfolio holdings to pay Texas property taxes (tens of thousands range)
- This led to exploring borrowing strategies: invest → borrow against portfolio to pay taxes, rather than sell

**Key alignment:** Avoid selling appreciated assets; borrowing preserves compounding.

---

## 5. Hedging: SQQQ vs Put Options (Insurance Concept)

**Current hedge:**
- Not comfortable with options yet (despite understanding concept)
- Using SQQQ (3x inverse Nasdaq ETF) as hedge instead of buying put options
- Sized ~5% of portfolio, funded by trimming Tesla (~$12k-$15k)

**Advisor feedback on SQQQ:**
- Valid hedge form but not "insurance" the way a put is
- SQQQ useful if someone doesn't use options
- With Nasdaq down ~1%, SQQQ up ~3%, but 5% position won't materially offset losses across larger portfolio
- Hedge size matters; small hedge won't stabilize whole portfolio, and full offset isn't the goal

**Advisor's approach to options:**
- "Options are complicated in theory but can be simple in practice"
- Treats puts like homeowners insurance: not trying to avoid accidents — trying to survive them financially
- Options move based on Greeks and implied volatility (fear), not purely underlying price
- Fear/news reactions unpredictable → timing is unrealistic → prefer hedges "always on"

---

## 6. Practical Options Tutorial: QQQ Put Walkthrough

**Step-by-step in Fidelity:**

### A) Choose underlying and option type
- Use QQQ (and SPY in practice)
- Choose "Put" → "Buy to Open"

### B) Choose expiration
- Rule of thumb: ~30 days out
- Selected ~early March example

### C) Choose strike (how far OTM)
- Rule: 10% to 20% out of the money (below current price)
- Compute: current price × (10-20%) → subtract from current price
- Example landed on: ~560 strike put

### D) Understand bid/ask and premium
- Example mid price: ~$2.79 (approx. 2.795)

### E) Convert premium to dollars
- Premium × 100 (1 contract = 100 shares)
- Example: ~2.795 × 100 ≈ **$279 per contract**

---

## 7. How Puts Make Money — IV, Time Decay, Payoff

**Not linear.** Put value changes based on:
1. Underlying price movement
2. Implied volatility expansion (fear premium rising)
3. Time decay (premium erodes over time)

**Key concepts:**
- IV rises in sharp drops because everyone rushes to buy protection → premiums increase
- Can increase put value even before full price drop completes
- Time decay: longer you wait without a move, more premium erodes

**Visualization tool:** OptionsStrat
- Built long put on QQQ with same expiration/strike
- Expanded scenario range to 20% then 40% downside

**Key insight:**
- Max loss = premium paid (hundreds of dollars)
- Max gain = very large in extreme drops (black swan)
- If max loss small and max gain huge, why not always have it? → That's exactly why advisor keeps it always on

**Black swan example:** ~40% market drop → contract worth ~$18,000 per contract

---

## 8. Rolling Strategy — Always-On Hedge

**"Roll it" method:**
- Every 5-7 days, move hedge out to keep ~30 days to expiration
- Not focused on selling to harvest small gains
- Focus: stability and disaster insurance; sell during extreme events to capture surge

**Sizing guidance:**
- ~1 contract per $50,000 of portfolio value
- Example: $300k portfolio → 3 QQQ puts + 3 SPY puts
- Cost framework: ~$500-$600/month on insurance layer to "sleep at night"

---

## 9. Portfolio Cash Flow Philosophy — Why Dividends Matter

**Advisor's critique of "all growth" portfolios (when living off portfolio):**
- A business doesn't sell parts of itself to make payroll
- If you must sell holdings during down days to pay bills → forced to realize losses or sacrifice compounding at worst time

**Advisor's preference:**
- Cash flow (dividends/distributions) funds expenses and debt service
- Growth continues compounding without forced selling

---

## 10. Dividend Funds Review & Accounting Issue

**Funds discussed:** YMAX, MSTY, CLM/CRF, others

**Key point: returns incomplete without dividends**
- Without including distributions, can't conclude whether fund is up or down
- Analogy: judging rental property without counting rent checks

**Tools:**
- Snowball (dividend/performance tracking) — wasn't fully reconciling due to new account sync
- Only implementing "paycheck to portfolio" approach since ~October

**Fidelity platform friction:** UI is archaic, accounting headache with duplicative categorization

---

## 11. Living Off Portfolio — Equity Management

**Current situation:**
- Largely living off brokerage
- Consultant/freelancer; spouse works
- Paid property taxes from brokerage recently
- Brokerage equity ~92% (high equity / low leverage)

**Adapting guidance:**
- Takes ~3-4 months of real expense cycles to "feel" equity impact
- Track: income inflows, expense outflows, resulting equity % changes over time
- Portfolio can still grow while drawing from it if you avoid forced selling and keep compounding active

---

## 12. Building Tools / Software (Side Discussion)

- Built a terminal-based tool (AI/automation style) gaining interest on GitHub
- Users requesting Snowball-like UI (not UI-focused builder)
- Advisor trademarked "Paycheck to Portfolio" brand
- Advisor working with large company, tools expected to launch ~4-8 weeks
- Mutual interest in building better tracking/accounting tools

---

## 13. Key Decisions & Takeaways

1. **Borrow against equity** rather than selling appreciated assets (avoid taxable events, preserve compounding)
2. **SQQQ** can be hedge substitute, but **puts are more direct "insurance"** — hedge sizing matters
3. **Options can be simple:** 30 days out, 10-20% OTM strikes, premium × 100 = cash cost
4. **Don't judge dividend/income funds** without reintegrating dividends into total return
5. **Living off portfolio** becomes manageable once you track equity changes over few months

---

## 14. Action Items

### Client To Do:
1. Learn options mechanics using advisor's "market crash cheat code" content
2. Implement consistent hedging plan:
   - SPY + QQQ put structure
   - Determine budgeted monthly "insurance premium" amount
   - Rolling cadence (~weekly) to keep ~30 days to expiration
3. Fix performance accounting:
   - Ensure dividends/distributions captured and added back into total return
   - Reconcile Snowball syncing issues / adjust spreadsheet logic
4. Reassess fund "down" flags only after total-return accounting is correct

### Advisor To Do:
- Available for follow-up after client reviews options content and fixes dividend accounting
- Continue guidance on rolling/position sizing and fund quality once accurate total return visible

---

## 15. Open Questions

- Exact hedge sizing for specific holdings (concentration in individual stocks + income funds)
- Whether to prefer: always-on puts + smaller inverse ETF, inverse ETF only, or blended approach with defined triggers
- Best dividend funds mix for goals (cash flow needs, tax profile, volatility tolerance) once accurate return data available
- Operational workflow: how to systematize buying on down days and maintaining hedges given "set it and forget it" preference

---

## 16. Notable Themes

> "Structure is the structure" — whether Bitcoin or stocks, the key is building equity and borrowing against it.

> Options as insurance — focus on surviving drawdowns rather than predicting them.

> "You can't predict implied volatility / fear" — so timing perfect puts is unrealistic; keep protection on.

> "You can't say it's down without dividends" — total return must include distributions.
