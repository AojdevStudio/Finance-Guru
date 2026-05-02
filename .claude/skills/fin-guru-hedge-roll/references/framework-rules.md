# Framework Invariants — With "Why"

Compact restatement of the hedging framework rules, each with sourced reasoning. Reference during ticket drafting to explain decisions in rationale sections.

Source documents:
- `fin-guru/data/hedging-strategies.md` — operational rules
- `fin-guru/data/options-insurance-framework.md` — theoretical grounding (Black-Scholes, insurance analogy)

---

## Rule: Maintain ~30 DTE for active protection

**Source**: `hedging-strategies.md` line 37

**Why**: A put with 30+ DTE has meaningful extrinsic value (time premium). Its payoff curve is smooth and the Greeks are predictable — delta changes slowly with spot moves, theta decay is ~1-2% per day rather than accelerating.

Below 15 DTE, gamma explodes (small spot moves produce outsized delta changes) and theta decay accelerates, making the hedge unreliable as protection while simultaneously burning premium faster. The 30 DTE target is the sweet spot between premium cost and coverage quality.

---

## Rule: Roll at 5-7 DTE

**Source**: `hedging-strategies.md` line 38

**Why**: Two reasons. First, at 5-7 DTE most remaining extrinsic value has decayed, so the old put's residual isn't worth much — rolling captures what's left before it hits zero. Second, waiting until 1-2 DTE risks gap-risk: if a weekend or earnings event falls between roll-day and expiry, you might be unhedged during the highest-risk moment.

The 5-7 window is a compromise: not so early that you're throwing away residual value, not so late that you're exposed to gap-week risk.

---

## Rule: Strike 10-20% OTM

**Source**: `hedging-strategies.md` lines 42-45

**Why**: 10-20% OTM balances cost efficiency with coverage meaningfulness.

- Closer strikes (5-10% OTM): cost 1.5-2× more premium but cover more frequent/smaller drawdowns. Over-pays for coverage you rarely need.
- Target strikes (10-20% OTM): pay only when drawdown is meaningful (the scenario you're actually hedging against). Premium is manageable.
- Further strikes (20-30% OTM): cheap premium but only pay out in catastrophic scenarios. You're under-hedging moderate drawdowns.

The 10-20% range matches "real risk" — the drawdowns that would materially impact financial goals (line 18: "Portfolio value crosses a threshold where a 20%+ drawdown would materially impact financial goals").

---

## Rule: ~1 contract per ~$50,000 portfolio

**Source**: `hedging-strategies.md` lines 31-32

**Why**: Each put contract covers 100 shares of the underlying. For QQQ at ~$500/share, 1 contract = ~$50,000 notional. Covering a $200k portfolio with 4 QQQ contracts = $200k notional = 100% coverage.

The ratio scales: $100k portfolio = 2 contracts; $300k = 6 contracts; etc. This prevents both under-hedging (too few contracts, portfolio drops more than hedge covers) and over-hedging ("is a drag on returns" per line 33).

Adjust by underlying price — IWM at ~$200/share = 1 contract covers $20k notional, so you'd need more IWM contracts than QQQ contracts for the same coverage dollar.

---

## Rule: Budget $500-600/month for ~$200k portfolio

**Source**: `hedging-strategies.md` lines 47-51

**Why**: ~3-3.5% annualized cost of protection. Line 51: "Compare this cost to the potential drawdown it prevents — a 20% drawdown on $200,000 is $40,000."

Budget scales linearly with portfolio value. User's specific budget is in `fin-guru/data/user-profile.yaml` Layer 3 — override the framework default if the profile specifies.

**If cost exceeds budget**: options in priority order:
1. Further OTM strikes (cheaper)
2. Shorter expiry (cheaper per contract, but more frequent rolls)
3. Fewer contracts (under-hedge intentionally)
4. Collar (sell call to offset premium — but violates growth thesis if user has high-conviction growth names)

---

## Rule: Multi-underlying weights QQQ 40-50%, SPY 30-40%, IWM 10-20%

**Source**: `hedging-strategies.md` lines 150-174

**Why**: Different indices hedge different portfolio exposures. Tech-heavy portfolio needs more QQQ. Broad-market portfolio leans SPY. Small-cap exposure (if any) uses IWM.

Line 168: "Different indexes do not move in perfect lockstep. Diversified hedging smooths out protection gaps during sector rotations."

**Adjust to actual portfolio concentration**:
- User's current portfolio (Apr 2026): PLTR 27.8%, TSLA 13.4%, NVDA/GOOGL/MSTR/COIN significant → tech-heavy → QQQ weight up to 50-55%
- If IWM exposure is zero in the underlying portfolio, dropping IWM is defensible

---

## Rule: Never close-before-open within a roll (without acknowledging leg risk)

**Source**: Ticket template execution-order warning + `hedging-strategies.md` line 121-123 rolling discipline

**Why**: Closing the old put first creates a brief window (seconds to a minute) with no hedge. In calm markets this is fine. In high-vol sessions, a gap down during that window leaves the portfolio unprotected exactly when protection matters most.

**Mitigations**:
1. Use Fidelity's "roll" combo ticket if available (simultaneous legs)
2. Open-before-close (more capital required briefly, but zero leg risk)
3. Close-before-open during low-vol session open (wider-spread risk but manageable)

The default is close-before-open because it recovers residual value to offset new premium cost — acceptable tradeoff in normal markets, but the ticket must note leg risk explicitly.

---

## Rule: Inverse ETFs unsuitable for multi-week hedging

**Source**: `hedging-strategies.md` lines 96-113

**Why**: Inverse ETFs (SQQQ, SH, SPXU) reset daily. Over any choppy multi-day period, compounding creates volatility drag — line 99: "In a choppy, sideways market, the inverse ETF loses value even if the index ends flat."

For a 30-60 day hedge (standard protective put cycle), drag erodes capital meaningfully. Line 112: "Holding SQQQ for months will almost certainly erode capital even if the market declines."

**When inverse ETFs are acceptable**: days to 1-2 weeks, tactical only. Never as replacement for a protective put program.

---

## Rule: Protective puts > Collar when growth-layer conviction is high

**Source**: `options-insurance-framework.md` Pillar 3 (equity building) + `hedging-strategies.md` Strategy Selection Matrix

**Why**: A collar (buy put + sell call) finances the put by capping upside. If the user's growth layer (PLTR, TSLA, NVDA, MSTR, COIN) has high conviction, capping upside via short calls surrenders the asymmetric payoff that's the point of holding those names.

Line from Pillar 3 analogy: "Growth stocks are like building equity... the value compounds over time." Short calls break the compounding.

**When collar is acceptable**: pure-income portfolios, lower-conviction growth, cost-constrained hedging where budget doesn't fit pure puts.

---

## Rule: Educational framing, never "advice"

**Source**: Every ticket + `hedging-strategies.md` line 7 + `CLAUDE.md` project compliance

**Why**: Regulatory — Finance Guru outputs are educational, not investment advice. Every ticket must close with the educational notice, specifying options-specific risks (total premium loss, not suitable for all investors) and the consult-professionals-before-acting language.

Do not soft-pedal this. Every options ticket needs the full disclaimer.
