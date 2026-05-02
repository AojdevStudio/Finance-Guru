# Finance Guru™ — Canonical Definitions & Formulas

_Single source of truth for every named formula, threshold, classifier, and rule that governs Finance Guru analysis, deployment, and risk management._

**Audience:** Finance Guru agents (Cassandra and her specialists), KeepFolio engineers porting these rules into TypeScript, and the principal ({user_name}) reviewing methodology.

**Status:** v1.0 — 2026-05-02. Compiled from `src/` (Python toolkit), `fin-guru/data/`, `fin-guru/tasks/`, `.claude/skills/`, and `fin-guru-private/fin-guru/strategies/`. Every entry cites its origin so the glossary stays auditable.

**Maintenance rule:** When a formula or threshold changes anywhere else in the repo, update _this_ file too — divergence here is a bug.

---

## Contents

1. [Core constants](#1-core-constants)
2. [Layer architecture](#2-layer-architecture)
3. [Yield, income & distributions](#3-yield-income--distributions)
4. [Options income classifier](#4-options-income-classifier)
5. [Margin & leverage](#5-margin--leverage)
6. [Risk metrics](#6-risk-metrics)
7. [Volatility metrics](#7-volatility-metrics)
8. [Momentum & trend](#8-momentum--trend)
9. [Moving averages](#9-moving-averages)
10. [Options & Greeks](#10-options--greeks)
11. [Hedge sizing & roll mechanics](#11-hedge-sizing--roll-mechanics)
12. [Correlation & diversification](#12-correlation--diversification)
13. [Factor models](#13-factor-models)
14. [Total return](#14-total-return)
15. [Portfolio construction limits](#15-portfolio-construction-limits)
16. [Pre-flight gates](#16-pre-flight-gates)
17. [Decision triggers (green/yellow/red)](#17-decision-triggers-greenyellowred)
18. [Monte Carlo simulation](#18-monte-carlo-simulation)
19. [Spreadsheet safety](#19-spreadsheet-safety)
20. [Tax rules](#20-tax-rules)
21. [Milestones & 28-month roadmap](#21-milestones--28-month-roadmap)
22. [Compliance & disclosure](#22-compliance--disclosure)
23. [Source index](#23-source-index)

---

## 1. Core constants

| Constant | Value | Where defined | Used by |
|---|---|---|---|
| `TRADING_DAYS_PER_YEAR` | 252 | `src/analysis/risk_metrics.py` (and replicated in volatility, momentum, factors) | Annualization of daily returns, vol, Sharpe, Sortino, Calmar |
| `CALENDAR_DAYS_PER_YEAR` | 365 | `src/analysis/total_return.py:274-293` | Annualizing total return when dividend frequency varies |
| `RISK_FREE_RATE_DEFAULT` | 0.045 (4.5%) | `src/models/options_inputs.py`, `src/analysis/risk_metrics.py` | Sharpe, Sortino, Black-Scholes, Rho |
| `DIVIDEND_YIELD_DEFAULT` | 0.0; allowed `[0.0, 0.20]` | `src/models/options_inputs.py:120-121` | Black-Scholes input `q` |
| `IMPLIED_VOLATILITY_DEFAULT` | 0.30 (30%) | `src/analysis/rolling_tracker.py` | Fallback when live IV unavailable |
| `VAR_CONFIDENCE_DEFAULT` | 0.95 | `src/analysis/risk_metrics.py:158-198` | VaR / CVaR confidence band |
| `PORTFOLIO_PER_CONTRACT` | $50,000 | `src/analysis/hedge_sizer.py:96-114`, `.claude/skills/fin-guru-hedge-roll/SKILL.md:80-86` | Hedge sizing rule (the sizing rule) |
| `MARGIN_RATE_FIDELITY_DEFAULT` | 0.10875 (10.875%) | `.claude/skills/margin-management/SKILL.md:39`, `fin-guru/data/margin-strategy.md` | Monthly interest cost calc (Fidelity $1k–$24.9k tier) |
| `PUT_CALL_PARITY_TOLERANCE` | $0.10 | `src/analysis/options.py:251-298` | Arbitrage-detection band |
| `CONCENTRATION_LIMIT_HARD` | 0.30 (30%) | `.claude/skills/fin-guru-buy-ticket/SKILL.md:129` | Single-position deployment cap |
| `STRATEGY_START_DATE` | 2025-10-09 | `.claude/skills/margin-management/SKILL.md` | Anchor for `months_elapsed` and milestones |

---

## 2. Layer architecture

The portfolio is partitioned into three deliberate layers plus one special-case ticker. Layer assignment is _pattern-based_ on ticker (`fin-guru/data/system-context.md:87`, `.claude/skills/MonteCarlo/PortfolioParser.md:28-66`).

```
IF ticker IN [JEPI, JEPQ, CLM, CRF, ECAT, QQQI, SPYI, QQQY, YMAX, MSTY, AMZY, BDJ, ETY, ETV, BST, UTG]:  → Layer 2 (Income)
ELSE IF ticker IN [SQQQ, UVXY, VXX]:                                                                       → Layer 3 (Hedge)
ELSE IF ticker IN [PLTR, TSLA, NVDA, AAPL, MSTR, COIN, SOFI, VOO, VTI, QQQ, FNILX, FZROX, FZILX, SPMO, PARR, VXUS]:  → Layer 1 (Growth)
ELSE IF ticker == GOOGL:                                                                                   → Layer 1 (special scale-in)
ELSE:                                                                                                      → UNKNOWN — alert user
```

### 2.1 Layer 1 — Growth Engine

- _Definition:_ Buy-and-hold growth equities and broad-market index funds. Never sold; diluted naturally as Layer 2 grows.
- _Current value (as of Q1 2026):_ ~$175k–$192k.
- _Allocation rule:_ Keep 100%. New W2 capital does NOT flow here (except the SPMO weekly DCA and the GOOGL scale-in).
- _Source:_ `fin-guru-private/fin-guru/strategies/active/portfolio-master-strategy.md`.

### 2.2 Layer 2 — Income Generation

- _Definition:_ Monthly-distribution vehicles built with W2 deployments. Target final value $350k–$400k by Month 28.
- _Target blended TTM yield:_ 24–30% annualized.
- _Monthly deployment:_ $12,517 (94% of total $13,317 W2).
- _Allocation:_ Five buckets (see § 3.4).
- _Source:_ `fin-guru-private/fin-guru/strategies/active/dividend-income-master-strategy.md`.

### 2.3 Layer 3 — Downside Protection

- _Definition:_ Tail-risk hedge against 30–50% market drawdowns.
- _Current vehicle (post 2026-03-06):_ Protective puts on QQQ + SPY, 15% OTM, ~30 DTE. _Previously SQQQ (exited 2026-03-06)._
- _Sizing rule:_ 1 contract per $50,000 of portfolio value. _This is the canonical sizing rule; budget bends to match actual market premium, not the other way around._
- _Target weights across underlyings:_ QQQ 40–50%, SPY 30–40%, IWM 10–20% (default; tilt by portfolio composition).
- _Source:_ `fin-guru-private/fin-guru/strategies/risk-management/downside-protection-strategy.md`, `.claude/skills/fin-guru-hedge-roll/`.

### 2.4 GOOGL — special scale-in

- _Status:_ Scaling 6 → ~$7.5k–$12.5k by Q2 2026 (~$1,000/month from Layer 2 YieldMax bucket).
- Treated as a Layer 1 holding for risk purposes but funded out of Layer 2 cash.

---

## 3. Yield, income & distributions

### 3.1 Dividend yield

```
dividend_yield  =  Σ(distributions over trailing 12 months) / current_price
```

- Annualized rate, expressed as decimal in `[0.0, 0.20]` per Pydantic field constraint.
- _Canonical metric for Layer 2 funds is Trailing 12-Month (TTM) yield, never monthly snapshots._ This is a behavioral rule, not just a data preference (`fin-guru/data/modern-income-vehicles.md:233-239`).
- Used as `q` input to Black-Scholes (see § 10.1).
- _Source:_ `src/models/options_inputs.py:120-121`, `fin-guru/data/modern-income-vehicles.md`.

### 3.2 Estimated monthly dividends

**Per-ticker actual (post-pay):**

```
dividends_received_ticker  =  quantity  ×  amount_per_share
```

**Per-ticker estimated (forward-looking):**

```
estimated_dividend_per_ticker  =  quantity_held × expected_distribution_per_share_monthly
                               ≡  (position_value × annual_yield) / 12
```

**Portfolio monthly:**

```
monthly_dividend_income  =  Σ estimated_dividend_per_ticker
```

**Aggregation rules** (`.claude/skills/dividend-tracking/SKILL.md:79-83`):
- Sum quantities across Margin + Cash accounts per ticker; one row per ticker.
- Skip rows where `Amount per share == "--"` (non-dividend payers).
- For _received_ totals, only include pay dates that have already passed.
- Date format in sheet: `MM/DD/YYYY`.
- DRIP flag: `TRUE` = reinvested (shares grew), `FALSE` = cash. Default `TRUE` during accumulation.

**Known orphan tickers** (as of 2026-04-21): `SPMO`, `NVDA` — historical-log roster does not yet aggregate their dividends; they land in raw log only.

### 3.3 Total return decomposition

From `src/analysis/total_return.py:176-293`:

```
price_return       =  (ending_price − starting_price) / starting_price
dividend_return    =  Σ(dividend_per_share) / starting_price
total_return       =  price_return + dividend_return
annualized_return  =  (1 + total_return)^(365 / calendar_days) − 1   # base = calendar 365, NOT trading 252
```

**DRIP return** (compounding effect, per-dividend reinvestment at ex-date close):

```
new_shares_per_div  =  (current_shares × dividend_per_share) / ex_date_close
drip_return         =  (final_shares × final_price) / (initial_shares × initial_price) − 1
```

**Dividend data quality checks** (raise `DividendDataError` unless `force=True`):
1. Frequency mismatch — actual count vs expected ±25%.
2. Split artifact — single dividend > 3× median is suspicious.
3. Zero dividends from a known payer — flag as data gap.

### 3.4 Five-bucket Layer 2 allocation

`fin-guru-private/fin-guru/strategies/.../bucket-allocations.json`. Total monthly deployment must sum to $12,517 (validation invariant).

| # | Bucket | Weight | $/month | Target yield | Variance band | Holdings |
|---|---|---:|---:|---:|---:|---|
| 1 | JPMorgan Income | 27% | $3,380 | 8–10% | ±10% | JEPI 50% / JEPQ 50% |
| 2 | CEF Stable | 20% | $2,503 | 20–22% | ±15% | CLM 33% / CRF 33% / ECAT 20% |
| 3 | Covered-Call ETFs | 35% | $4,381 | 12–20% | ±15% | QQQI 33% / SPYI 33% / QQQY 34% |
| 4 | YieldMax Volatility | 10% | $1,252 | 60–85% | ±25% | YMAX 33% / MSTY 34% / AMZY 33% |
| 5 | DRIP v2 CEFs | 8% | $1,001 | 8–10% | ±10% | BDJ 20% / ETY 20% / ETV 20% / BST 20% / UTG 20% |

### 3.5 Distribution variance bands (by vehicle class)

From `fin-guru/data/modern-income-vehicles.md:128-272`:

| Vehicle | TTM yield | Normal monthly variance (Green) |
|---|---:|---:|
| Covered-call ETFs | 7–10% | ±5–10% |
| Modern CEFs | 12–22% | ±5–15% |
| YieldMax single-stock | 60–85% | ±10–25% |

The classifier is applied _before_ judging variance: a −9% month on a Class 3 fund is normal; the same on a Class 1 fund is yellow. See § 17.

---

## 4. Options income classifier

The taxonomy that BK-06 codifies in `packages/data/income.ts`. From `fin-guru/data/modern-income-vehicles.md:20-124, 262-271`.

**Inputs (jointly evaluated):**

```
P  =  options_premium_income / total_distributions          # premium share of distributions
σ  =  stdev(monthly_distributions) / mean(monthly_distributions)   # monthly variance ratio
Y  =  trailing_12mo_yield                                   # annualized TTM yield
```

**Three classes:**

| Class | Label | Premium share P | Variance σ (monthly) | TTM yield Y | Examples |
|---|---|---:|---:|---:|---|
| 1 | Options Premium Funds (covered-call ETFs) | 0.60–0.80 | ±5–10% | 7–10% | JEPI, JEPQ, QQQI, SPYI, QQQY |
| 2 | Modern CEFs (blended) | mixed (premiums + dividends + bonds + cap gains; often levered) | ±5–15% | 12–22% | ECAT, CLM, CRF, BDJ, ETY, ETV, BST, UTG |
| 3 | Volatility Harvesting (YieldMax single-stock) | 0.80–0.95 | ±10–25% | 60–85% | YMAX, MSTY, AMZY |

**Classification routine (decision priority):**

1. Match by ticker against the canonical roster in `MonteCarlo/PortfolioParser.md:28-66` — this is the cheap path.
2. If ticker unknown, compute (P, σ, Y) over trailing 6+ months and pick the class whose three bands all match.
3. If multiple classes match, pick the one with tightest σ band (most conservative).
4. If none match, return `UNKNOWN` and require user adjudication before the fund enters Layer 2 deployment.

**Why P alone is insufficient:** a CEF can have P near zero but still belong to Class 2 because of leverage and blended sources. The σ and Y bands disambiguate.

**Companion rule — variance-vs-yield invariant** (`modern-income-vehicles.md:262-272`):

```
| Yield band Y     | Expected σ |
|-----------------:|-----------:|
| 2–4%             | ±1–2%      |   (traditional bonds, dividend aristocrats — out of scope for Layer 2)
| 7–10%            | ±5–7%      |   (Class 1)
| 12–22%           | ±5–15%     |   (Class 2)
| 20–30%           | ±10–20%    |   (high-yield CEFs / preferred stocks)
| 60–85%           | ±10–30%    |   (Class 3)
```

A fund whose σ falls outside its yield band is a data-quality flag.

---

## 5. Margin & leverage

### 5.1 Margin balance vs margin draw

```
margin_balance  =  | Net_debit |        # absolute value of "Net debit" row in Fidelity Balances CSV
```

```
remaining_cash         =  current_cash − deployment_amount
margin_draw_required   =  max(0, deployment_amount − current_cash)
                       ≡  max(0, −remaining_cash)
```

`margin_balance` is the _stock_ (snapshot at a point in time). `margin_draw` is the _flow_ (new borrowing on a deployment). Treat them as different units.

_Sources:_ `.claude/skills/margin-management/SKILL.md`, `.claude/skills/fin-guru-buy-ticket/references/workflow-patterns.md:138-144`.

### 5.2 Carrying cost

```
monthly_interest_cost  =  margin_balance × annual_rate / 12
annual_interest_cost   =  monthly_interest_cost × 12
```

Default `annual_rate = 0.10875` for Fidelity $1k–$24.9k tier. Other broker reference rates (`fin-guru/data/margin-strategy.md`):

| Broker | Rate |
|---|---:|
| Interactive Brokers | 2.5–4.5% |
| Robinhood Gold | 5.25% |
| Fidelity | 6–8% (negotiable; current tier 10.875%) |
| Schwab | 7–9% |

_Target (long-term):_ refinance to sub-5%, ideally 2.5–4%.

### 5.3 Coverage ratio (dividends ÷ interest)

```
coverage_ratio  =  monthly_dividend_income / monthly_interest_cost
```

Excel implementation: `=IFERROR(B10 / B11, 0)` (`margin-management/SKILL.md:119-124`). The `IFERROR` is mandatory — bare division throws `#DIV/0!` when margin = 0.

**Tiered policy** (`fin-guru/data/margin-strategy.md:13-44`):

| Tier | Coverage target | Max margin utilization | Maintenance buffer | Asset universe |
|---|---:|---:|---:|---|
| 1 — Conservative | ≥ 3.0× | 20–30% of portfolio | 3× minimum | Dividend aristocrats, high-quality CEFs only |
| 2 — Moderate | ≥ 2.0× | 30–50% | 2× | Dividend growth + high-yield mix |
| 3 — Aggressive | ≥ 1.5× | 50–75% | 1.5× | Daily monitoring, multiple income sources required |

### 5.4 Portfolio-to-margin safety ratio

```
portfolio_to_margin_ratio  =  total_account_value / margin_balance
```

| Ratio | Status | Action |
|---:|---|---|
| ≥ 4.0:1 | 🟢 Green | Continue per strategy |
| 3.5–4.0:1 | 🟡 Yellow | Pause scaling, monitor weekly |
| 3.0–3.5:1 | 🟠 Alert | Stop new draws, inject $20k business income |
| < 3.0:1 | 🔴 Red | All draws halted, mandatory business-income injection |
| < 2.5:1 | ⚫ Critical | $30k+ injection, consider selling hedge (SQQQ/puts) |

### 5.5 Margin jump alert

Halt and require explicit confirmation if:

```
new_margin_balance > previous_margin_balance + $5,000
```

Rationale: a $5k+ uncommitted draw is large enough to be intentional rather than incidental.

### 5.6 Self-sustaining leverage rule

Borrow only amounts where:

```
monthly_dividend_income  >  (margin_balance × annual_rate / 12) × 1.5
```

The 1.5× safety multiplier accommodates dividend cuts and rate increases. Net spread `(portfolio_yield − margin_rate)` must be positive at all times; target ≥ 5% annually.

### 5.7 Margin scaling milestones

Anchor: `STRATEGY_START_DATE = 2025-10-09`. `months_elapsed = (today − start).days // 30`.

| Milestone | Month | Trigger | Action | Required ratio |
|---|---:|---|---|---:|
| Phase 1 | 0 | Portfolio > $300k | Begin $4,500/month draw (rent/utilities) | ≥ 4.0:1 |
| Month 6 | 6 | Dividends > $2,000/month AND ratio > 4:1 | Scale to $6,213/month (add mortgage) | ≥ 4.0:1 |
| Month 12 | 12 | Dividends > $4,500/month | Break-even; hold or scale to $8,000/month | ≥ 3.5:1 |
| Month 18 | 18 | Dividends > $7,000/month AND margin declining | Scale to $10,000/month | ≥ 3.0:1 |
| Month 28 | 28 | Dividends > $8,300/month (≈$100k annualized) | Full FI declared (69.2% MC probability) | ≥ 2.5:1 |

### 5.8 Business-income backstop

- _Available:_ $22,000/month from business operations.
- _Philosophy:_ insurance only — not a primary strategy lever.
- _Mandatory use:_ ratio < 3:1 (margin call risk).
- _Optional use:_ market correction 20–30%, or to accelerate FI timeline.
- _Monte Carlo expectation:_ used in 98.5% of paths at least once.

---

## 6. Risk metrics

All formulas from `src/analysis/risk_metrics.py`. Annualization factor `√252` everywhere unless noted. Default `risk_free_rate = 0.045`.

| # | Metric | Formula | Range / benchmark |
|---|---|---|---|
| 6.1 | **Sharpe ratio** | `((μ_daily − R_f/252) / σ_daily) × √252` | <1 poor · 1–2 good · >2 excellent |
| 6.2 | **Sortino ratio** | `((μ_daily − R_f/252) / σ_downside) × √252`; `σ_downside = std(r where r < 0)` | Same bands; penalizes downside only |
| 6.3 | **Annual volatility** | `σ_daily × √252` | <25% low · 25–50% normal · 50–75% high · >75% extreme |
| 6.4 | **Max drawdown** | `min((Price_t − running_max) / running_max)` | −5% mild · −20% bear · −50%+ crisis |
| 6.5 | **Calmar ratio** | `annualized_return / |max_drawdown|`, where `annualized_return = μ_daily × 252` | Higher is better; hedge-fund favorite |
| 6.6 | **VaR (historical)** | `percentile(returns, (1 − conf) × 100)` | At conf=0.95: VaR = −0.035 → "95% of days, losses ≤ 3.5%" |
| 6.7 | **VaR (parametric)** | `μ + (z × σ)`; z₉₅ = −1.645 | — |
| 6.8 | **CVaR / Expected Shortfall** | `mean(returns where returns ≤ VaR)` | Always ≥ |VaR| in magnitude |
| 6.9 | **Beta** | `Cov(asset, benchmark) / Var(benchmark)` | <0.5 low · 0.5–1.5 average · >1.5 high · negative = hedge |
| 6.10 | **Alpha (CAPM)** | `R_asset − [R_f + β × (R_bench − R_f)]`; annualized = `α_daily × 252` | Significance via t-stat: |t| > 2.0 |

**Portfolio-level risk targets** (`fin-guru/data/risk-framework.md:149-153`):
- Max 1-day VaR @ 95%: 2% of portfolio.
- Max drawdown limit: 15% peak-to-trough.
- Single-position cap: 10% (general); see § 15 for deployment-specific 30% cap.
- Max leverage ratio: 2:1 for conservative strategies.

**Risk escalation levels** (`risk-framework.md:169-174`):
- Level 1: 75% of risk-limit utilization.
- Level 2: 90%.
- Level 3 (breach): 100% — immediate corrective action.

---

## 7. Volatility metrics

`src/utils/volatility.py`.

| # | Metric | Formula | Defaults |
|---|---|---|---|
| 7.1 | **Bollinger Bands** | `Mid = SMA(close, n)`; `Upper/Lower = Mid ± k·σ`; `%B = (close − Lower) / (Upper − Lower)`; `Bandwidth = (Upper − Lower) / Mid · 100` | n=20, k=2 |
| 7.2 | **ATR (Avg True Range)** | `TR = max(H − L, |H − C_prev|, |L − C_prev|)`; `ATR = EMA(TR, n)`; `ATR% = ATR / price · 100` | n=14 (Wilder) |
| 7.3 | **Historical volatility** | `r = ln(C_t / C_{t-1})`; `HV_daily = std(r)`; `HV_annual = HV_daily · √252` | n=20 |
| 7.4 | **Keltner Channels** | `Mid = EMA(close, n)`; `Upper/Lower = Mid ± k·ATR` | n=20, k=2 |

**Volatility regime classification** (`src/utils/volatility.py:318-368`):

| Regime | Annual vol | ATR% |
|---|---|---|
| Low | < 25% | < 2.5% |
| Normal | 25–50% | 2.5–5% |
| High | 50–75% | 5–7.5% |
| Extreme | > 75% | > 7.5% |

ATR has a position-sizing use: stop-loss is conventionally placed `2 × ATR` below entry.

---

## 8. Momentum & trend

`src/utils/momentum.py`.

| # | Indicator | Formula | Signal thresholds |
|---|---|---|---|
| 8.1 | **RSI** | `RS = avg_gain / avg_loss`; `RSI = 100 − 100/(1 + RS)` (Wilder smoothing) | >70 overbought · <30 oversold · 50 neutral |
| 8.2 | **MACD** | `MACD = EMA(12) − EMA(26)`; `Signal = EMA(MACD, 9)`; `Hist = MACD − Signal` | MACD > Signal bullish; histogram rising = strengthening |
| 8.3 | **Stochastic %K, %D** | `%K = 100·(C − L_n)/(H_n − L_n)`; `%D = SMA(%K, 3)` | %K > 80 OB · %K < 20 OS; n=14 default |
| 8.4 | **Williams %R** | `−100·(H_n − C)/(H_n − L_n)` | > −20 OB · < −80 OS |
| 8.5 | **Rate of Change (ROC)** | `((C − C_n)/C_n) · 100` | >0 bullish, <0 bearish, zero-cross = potential reversal |

---

## 9. Moving averages

`src/utils/moving_averages.py`.

| # | MA | Formula | Behaviour |
|---|---|---|---|
| 9.1 | **SMA** | `(P₁ + … + Pₙ)/n` | Equal-weight, slow, smooth |
| 9.2 | **EMA** | `EMA_t = α·Price + (1−α)·EMA_{t−1}`; `α = 2/(n+1)` | Recency-weighted, faster |
| 9.3 | **WMA** | `Σ(P_i · i) / Σi`, where `Σi = n(n+1)/2` | Linear weighting |
| 9.4 | **HMA (Hull)** | `WMA(2·WMA(n/2) − WMA(n), √n)` | Minimal lag, max smoothness |

**Crossover signals:**
- _Golden cross:_ SMA(50) crosses above SMA(200) → bullish.
- _Death cross:_ SMA(50) crosses below SMA(200) → bearish.

---

## 10. Options & Greeks

`src/analysis/options.py`. Black-Scholes (with continuous dividend yield `q`):

### 10.1 Pricing

```
d₁  =  [ln(S/K) + (r − q + σ²/2)·T] / (σ·√T)
d₂  =  d₁ − σ·√T

C   =  S·e^(−qT)·N(d₁) − K·e^(−rT)·N(d₂)
P   =  K·e^(−rT)·N(−d₂) − S·e^(−qT)·N(−d₁)
```

### 10.2 Greeks

| Greek | Call | Put | Interpretation |
|---|---|---|---|
| **Δ Delta** | `e^(−qT)·N(d₁)` | `e^(−qT)·[N(d₁) − 1]` | $/share underlying move → $/contract option move |
| **Γ Gamma** | `e^(−qT)·n(d₁) / (S·σ·√T)` | (same) | Δ change per $1 underlying move |
| **Θ Theta** | combo of S·n(d₁)·σ·e^(−qT)/(2√T), r·K·e^(−rT)·N(d₂), q·S·e^(−qT)·N(d₁); divide by 365 for daily | (sign-adjusted) | $/day from time decay |
| **V Vega** | `S·e^(−qT)·√T·n(d₁) / 100` | (same) | $/contract per 1% vol change |
| **ρ Rho** | `K·T·e^(−rT)·N(d₂) / 100` | `−K·T·e^(−rT)·N(−d₂) / 100` | $/contract per 1% rate change |

`n(·)` = standard normal PDF; `N(·)` = standard normal CDF.

### 10.3 Implied volatility

Newton–Raphson root-finding:

```
vol_new  =  vol_old + (target_price − calc_price) / vega
```

Tolerance ~$0.01, max 100 iterations, bounded `[0.01, 5.0]`.

### 10.4 Put-call parity (arbitrage check)

```
C − P  =  S·e^(−qT) − K·e^(−rT)
```

Flag arbitrage if `|LHS − RHS| > $0.10` (`PUT_CALL_PARITY_TOLERANCE`).

---

## 11. Hedge sizing & roll mechanics

### 11.1 The sizing rule (canonical)

```
contracts  =  floor(portfolio_value / $50,000)
```

`PORTFOLIO_PER_CONTRACT = $50,000`. Recompute when portfolio crosses each $50k threshold. ($200k → 4; $250k → 5; $300k → 6.)

_Source:_ `src/analysis/hedge_sizer.py:96-114`, `.claude/skills/fin-guru-hedge-roll/SKILL.md:80-86`.

### 11.2 Multi-underlying allocation

Default weights: `QQQ 40–50%`, `SPY 30–40%`, `IWM 10–20%`. Algorithm:

1. Floor-allocate per ticker: `contracts_i = floor(total · weight_i)`.
2. Distribute leftover contracts to highest-weight underlyings first.

Tilt by portfolio composition: tech-heavy ↑QQQ to 50%+; small-cap exposure ↑IWM.

### 11.3 Strike, DTE, and roll discipline

| Parameter | Rule | Source |
|---|---|---|
| OTM band | 10–20% (strike ≈ spot · 0.85 for puts) | `framework-rules.md:31-40` |
| Maintenance DTE | ~30 days | `framework-rules.md:11-17` |
| Roll trigger | DTE 5–7 (or ≤ 23 in current ops) | `framework-rules.md:21-27`, `portfolio-master-strategy.md` |
| New expiry after roll | 30–60 DTE (target 30 maintenance) | `roll-decision-tree.md:94-102` |
| Strike drift bands | <10% OTM → adjust further; 10–20% acceptable; >25% adjust closer | `roll-decision-tree.md:68-76` |

### 11.4 Cost-to-roll

```
cost_to_roll  =  (new_premium · qty · 100) − old_residual_value
```

Framework checks before executing:
- Monthly amortized cost ≤ Layer 3 budget?
- Strike still 10–20% OTM on new legs?
- New DTE in 30–60 range?
- Contract count still matches `portfolio_value / $50k`?

### 11.5 Hedge budget

Annual hedge cost target: **3.0–3.5% of portfolio** (`framework-rules.md:57-69`). Override per-user via `fin-guru/data/user-profile.yaml` Layer 3 budget.

### 11.6 Inverse-ETF prohibition for multi-week hedges

`SQQQ`, `SH`, `SPXU` are **not** suitable for 30–60 day hedging. Daily reset compounding causes volatility drag in choppy markets (~3–5%/month). Acceptable for tactical days-to-1-week use only; never as a replacement for a put program (`framework-rules.md:102-110`).

### 11.7 SQQQ simulation parameters (when SQQQ is being modeled)

- Leverage: −3 (inverse 3× daily target).
- Annual expense: 0.95% (fee-waived through Sept 2026).
- Daily fee: `0.0095 / 252 ≈ 0.00377%`.
- Update: `value · (1 + LEVERAGE · daily_return − daily_fee)`.

### 11.8 IV expansion (VIX–SPX regression table)

`src/analysis/hedge_comparison.py:48-57`. Calibrated on 2008 GFC, 2018 Volmageddon, 2020 COVID, 2025 Tariffs:

| SPX drop | 0.00 | −0.05 | −0.10 | −0.20 | −0.40 |
|---|---:|---:|---:|---:|---:|
| VIX | 18.0 | 28.0 | 38.0 | 55.0 | 80.0 |

Linear piecewise interpolation between rows; extrapolation beyond −0.40 used cautiously.

### 11.9 Put hedge effectiveness (post 2026-03-06 setup)

| Market decline | Per-contract value | Notes |
|---|---|---|
| −10% | ~$2,000–4,000 | Offsets ~$8k–16k of $200k portfolio |
| −20% | ~$6,000–10,000 | Offsets ~$24k–40k |
| −30% | ~$12,000–18,000 | Offsets ~$48k–72k |
| −40% | ~$18,000+ | Tail-risk catch |

Funding model: $4,517 reserve covers ~4.5 months; ongoing premiums then funded from monthly dividend income (~$1,072/month current) → puts are self-funding.

---

## 12. Correlation & diversification

`src/analysis/correlation.py`.

| # | Metric | Formula | Bands |
|---|---|---|---|
| 12.1 | **Pearson correlation** | `Cov(X,Y) / (σ_X · σ_Y)` | 0.5–0.7 strong · 0.3–0.5 moderate · 0–0.3 weak · <0 hedge |
| 12.2 | **Covariance matrix** | `Cov(X,Y) = E[(X−μ_X)(Y−μ_Y)]` | Feeds portfolio variance `σ²_p = wᵀ Σ w` |
| 12.3 | **Diversification score** | `1 − avg_correlation` | >0.6 excellent · 0.4–0.6 good · 0.2–0.4 moderate · <0.2 poor |
| 12.4 | **Rolling correlation** | Pearson over a window (default 60 days) | Rising correlations = diversification breakdown |

**Concentration warning:** average correlation > 0.7 across the book triggers a portfolio-level alert.

**Pairwise correlation cap:** ≤ 0.85 between any two Layer 2 holdings (`fin-guru-private/.../concentration-limits.json`). Currently monitored: CLM–CRF at 0.861 (acceptable in context).

---

## 13. Factor models

`src/analysis/factors.py`. OLS regression with standard errors from residual variance matrix.

| Model | Specification |
|---|---|
| **CAPM (1-factor)** | `R = α + β·MKT + ε` |
| **Fama-French 3-factor** | `R = α + β_m·MKT + β_s·SMB + β_v·HML + ε` |
| **Carhart 4-factor** | `R = α + β_m·MKT + β_s·SMB + β_v·HML + β_mom·MOM + ε` |

Where `MKT = market excess return`, `SMB = small-minus-big`, `HML = high-minus-low (book/market)`, `MOM = momentum (winners − losers)`.

- Annualized α: `α_daily × 252`.
- Significance: |t-stat| > 2.0.
- Model fit interpretation: R² < 0.30 → idiosyncratic dominates; R² > 0.80 → systematic dominates.

---

## 14. Total return

See § 3.3 for primary formulas. Key invariants worth restating:

- **Total return uses calendar 365 for annualization**, not trading 252 — because dividend frequency is calendar-based.
- A fund can post negative price return _and_ positive total return (DRIP + dividends > price decline).
- DRIP compounding magnifies returns disproportionately when prices are low at distribution dates.

---

## 15. Portfolio construction limits

| Scope | Rule | Source |
|---|---|---|
| **Single position (general risk)** | ≤ 10% of total portfolio | `risk-framework.md:149-153` |
| **Single position (deployment cap)** | ≤ 30% post-deploy; warn above | `fin-guru-buy-ticket/SKILL.md:129` |
| **PLTR exception** | Up to 30% of Layer 1 (currently 31.53%, approved) — natural dilution as portfolio grows | `concentration-limits.json` |
| **TSLA tactical cap** | ≤ 15% (was trimmed Nov 2025 from 20.78%) | `concentration-limits.json` |
| **Single Layer 2 fund** | ≤ 5% of Layer 2 | `concentration-limits.json` |
| **Layer 2 bucket** | Target weight + 10% (e.g., 27% target → max 37%) | `concentration-limits.json` |
| **Sector concentration** | ≤ 25% (per brainstorming framework) | `risk-framework.md` |
| **Equity allocation (balanced)** | 60–80% | `risk-framework.md:155-159` |
| **Fixed income allocation** | 20–40% | `risk-framework.md:155-159` |
| **Alternatives** | ≤ 20% | `risk-framework.md:155-159` |
| **Cash floor** | ≥ 5% for liquidity | `risk-framework.md:155-159` |
| **Pairwise correlation** | ≤ 0.85 between any two Layer 2 holdings | `concentration-limits.json` |

---

## 16. Pre-flight gates

Run before any deployment, roll, or sync. From `.claude/skills/fin-guru-buy-ticket/references/workflow-patterns.md` and related skills.

### 16.1 Cash buffer

```
remaining_cash  =  current_cash − deployment_amount
```

- `remaining_cash < 0` → margin draw of `|remaining_cash|` required (warn).
- `remaining_cash < emergency_reserve_target` → warn (target read from `user-profile.yaml`).

### 16.2 Concentration

```
new_pct  =  (existing_value + deployment[ticker]) / (portfolio_value + deployment_total)
```

Warn if `new_pct > 0.30`.

### 16.3 Margin coverage

```
coverage_ratio  =  monthly_dividend_income / monthly_margin_interest
```

Warn if `coverage_ratio < 2.0`.

### 16.4 Data freshness

| Artifact | Stale threshold | Action |
|---|---|---|
| Positions CSV | > 2 days | Ask user to re-export from Fidelity; confirm before proceeding |
| Price snapshot (during market hours) | > 15 min | Annotate stale-data warning in Risk Notes |
| Balances CSV (margin dashboard) | > 7 days | Trigger update alert at session start |

### 16.5 Sync safety gates (PortfolioSyncing)

**STOP** (require user confirmation):
1. CSV has fewer tickers than sheet (possible sale or missing data).
2. Any quantity change > 10%.
3. Any cost basis change > 20%.
4. ≥ 3 formula errors detected in target sheet.
5. Margin balance jumped > $5,000 (see § 5.5).
6. SPAXX discrepancy > $100.

**FLAG** (alert but proceed):
- SPAXX differs by $1–$100.
- Pending Activity vs Net debit differs by > $100.

### 16.6 Transaction dedup keys

| Tracker | Match key |
|---|---|
| Transactions tab | `Date | Action | Amount` |
| Expense tracker | `Date | Description | Amount` |

### 16.7 Retirement aggregation

Sum same ticker across multiple accounts. Flag any quantity change > 20% (large-change warning).

---

## 17. Decision triggers (green/yellow/red)

Single-source rule book. Variance bands from § 3.5; class semantics from § 4.

### 17.1 Distribution variance flags (Layer 2)

| Flag | Trigger | Action |
|---|---|---|
| 🟢 **Green** | Variance within class band; TTM yield stable | Continue regular deployment per bucket allocation |
| 🟡 **Yellow** | 2–3 consecutive months of −10% to −15%, OR TTM yield down 15–20%, OR NAV declining alongside distributions | Pause new purchases for 30 days; investigate strategy/manager changes; check NAV; compare peers |
| 🔴 **Red** | > 30% sustained decline over 3 months, OR > 50% single-month drop, OR NAV erodes faster than distributions (ROC death spiral), OR manager announces strategy change/fee hike, OR forced deleveraging | **Sell within 48 hours;** rotate proceeds to Bucket 1 (JEPI/JEPQ); document reason |

### 17.2 Margin scaling triggers

| Condition | Action | Priority |
|---|---|---|
| Month 6: Dividends > $2,000 AND ratio > 4:1 | Scale to $6,213/month | Confidence-based |
| Month 12: Dividends > $4,500 | Break-even — hold or scale to $8,000 | Confidence-based |
| Portfolio-to-margin ratio < 3.5:1 | Pause scaling; monitor weekly | Warning |
| Portfolio-to-margin ratio < 3.0:1 | Stop draws; inject $20k business income | Alert |
| Portfolio-to-margin ratio < 2.5:1 | $30k+ injection; consider selling hedge | Critical |

### 17.3 Portfolio drawdown triggers

| Condition | Action | Priority |
|---|---|---|
| Portfolio drops 15% in a single month | Pause contributions for 2 weeks; assess | Caution |
| Cumulative drop ≥ 25% | Stop margin draws; inject business income if needed | Alert |
| Cumulative drop ≥ 40% (crisis) | Stop margin; use business income; **buy the dip** | Emergency |

### 17.4 ITC risk advisory bands

| ITC score | Label | Behaviour |
|---|---|---|
| 0.0–0.3 | 🟢 Low | No advisory needed |
| 0.3–0.7 | 🟡 Medium | Mention in Risk Notes; no size cut unless combined signals |
| 0.7–1.0 | 🔴 High | Full advisory; recommend 30–50% size reduction OR staged entry |
| Unsupported | N/A | Omit advisory block (most ETFs/CEFs) |

### 17.5 Hedge thesis test (rolls)

Before rolling a hedge:
- Portfolio still concentrated in growth/tech? → thesis intact.
- VIX still elevated / macro catalyst pending? → thesis may resolve.
- 20%+ drawdown still materially damages goals? → thesis intact.

If all three test negative → **skip** (let the hedge expire).

### 17.6 VIX regime triggers

| VIX | Regime | Layer 2 effect | Action |
|---|---|---|---|
| 0–15 | Complacency | Lower options premium | Maintain ≥ 5% hedge |
| 15–25 | Normal | Optimal for covered calls | No action |
| 25–40 | Elevated uncertainty | Higher options premium | Monitor; may scale hedge |
| 40–100 | Panic | Extreme premiums; NAV risk | Consider scaling to 10% hedge; **continue buying at discount** |

---

## 18. Monte Carlo simulation

`.claude/skills/MonteCarlo/`. Used to validate the 28-month plan; rerun whenever assumptions shift.

### 18.1 Inputs

- 10,000 paths.
- Historical returns 2020–2025 with regime-aware sampling.
- Active management modeled (rotation logic).
- Realistic yield degradation (not flat assumption).

### 18.2 Output metrics

**Success:** P($100k), P($75k), P($50k), margin-call rate, backstop usage rate.

**Risk:** margin ratio (must stay ≥ 3:1), max drawdown (peak-to-trough), break-even timing.

**Portfolio:** Median, P5, P95 at month 28 per layer.

### 18.3 Headline result (Oct 2025 run)

| Metric | Value | Interpretation |
|---|---|---|
| P($100k @ Month 28) | 69.2% | Strong probability of FI hit |
| Median income (Month 28) | $110,661 | Exceeds target by 10.7% |
| P95 income | $138,392 | 38% upside |
| P5 income | $65,326 | Worst-case still 65% of target |
| Median portfolio (Month 28) | $409,356 | +9.7% over capital deployed |
| Capital deployed | $373,076 | — |
| Median break-even | Month 15 | — |
| Median max drawdown | −1.7% | P95 = 0%; worst case −92.6% (5%) |
| Backstop usage rate | 98.5% | Business income used at least once |

---

## 19. Spreadsheet safety

`.claude/skills/formula-protection/SKILL.md`, `PortfolioSyncing/SKILL.md`, `dividend-tracking/SKILL.md`.

### 19.1 Sacred (never modify)

| Sheet | Cell pattern | Why |
|---|---|---|
| DataHub | Col C `=GOOGLEFINANCE(A2,"price")` | Live price |
| DataHub | Cols D–E (`=C2−G2`, `=D2/G2`) | $/% change |
| DataHub | Cols H–M | Gains/losses |
| Dividend Tracker | Col F `=D2 · E2` | Shares × DPS |
| Dividend Tracker | Total row `=SUM(F2:F50)` | Expected dividends |
| Margin Dashboard | `=IFERROR(B10/B11, 0)` | Coverage ratio |

### 19.2 Allowed surgical edits

- Wrap a broken formula in `IFERROR(...)` to mask `#N/A`, `#DIV/0!`, `#REF!`.
- Repair sheet renames (`Sheet1!A1` → `'DataHub'!A1`).
- Expand range when new rows are added (`SUM(F2:F50)` → `SUM(F2:F100)`).
- Fix obvious typos (`B100` referring to a row that doesn't exist).

### 19.3 Forbidden

- Changing formula logic (e.g., `SUM` → `AVERAGE`).
- Replacing a formula with a static value.
- Deleting any formula.
- Modifying `GOOGLEFINANCE` parameters.

### 19.4 Writable columns by sheet

| Sheet | Writable | Locked |
|---|---|---|
| DataHub | A (Ticker), B (Quantity), G (Avg Cost) — from CSV | C–F (live price/change), H–M (gains), N–S (mixed) |
| Margin Dashboard | A–E (Date, Balance, Rate, Cost, Notes) | Coverage ratio, summary totals |
| Dividend Tracker | A–D rows 2–43 (Input area, max 42 records) | Row 1 header, rows 44+, cols G–U (historical log) |
| Retirement section (rows 46–62) | B (Quantity) only | A (Ticker), C–S (formulas) |

### 19.5 Apps Script integration (Dividend Tracker)

After writing input rows, click the "Add Dividend" button to trigger processing. Preferred path: `/InterceptBrowser` (authenticated session bypasses Google bot detection). Fallback: Apps Script macro `addDividendFast` directly. Last resort: ask user to click manually.

---

## 20. Tax rules

`fin-guru/data/tax-optimization.md`.

### 20.1 Dividend classification

| Type | Tax rate | Holding requirement | Sources |
|---|---|---|---|
| **Qualified** | 0%, 15%, or 20% (cap-gains) | Held > 60 days within 121-day window around ex-dividend | Most S&P 500, dividend aristocrats, qualified foreign, qualified ETFs |
| **Non-qualified** | Up to 37% federal + state (ordinary) | n/a | REITs, MLPs, BDCs, money-market, certain foreign |

### 20.2 2025 tax-rate spread (qualified vs non-qualified)

| Income | Qualified | Non-qualified | Spread |
|---:|---:|---:|---:|
| $47,025 | 0% | 22% | 22 pp |
| $100,000 | 15% | 24% | 9 pp |
| $200,000 | 15% | 32% | 17 pp |
| $500,000 | 20% | 37% | 17 pp |

(Add 3.8% NIIT for high earners.)

### 20.3 Account-location strategy

| Account type | Best assets |
|---|---|
| Traditional IRA / 401(k) | High-yield non-qualified (REITs, bond funds, BDCs, high-yield CEFs) |
| Roth IRA | Highest-expected-return assets (dividend-growth, EM, small-cap value) |
| Taxable brokerage | Qualified-dividend stocks, munis, tax-managed funds, qualified-dividend index funds |

### 20.4 Tax-loss harvesting

- Realize losses to offset dividend income (prefer short-term to offset ordinary).
- Maintain similar (not identical) exposure during 30-day wash window.
- Tax alpha potential: 0.5–1.5% annual after-tax return uplift.
- Direct indexing on dividend baskets unlocks sub-position harvesting.

### 20.5 2025 brackets (MFJ — for reference)

| Rate | Income range |
|---|---|
| 10% | $0–$23,200 |
| 12% | $23,200–$94,300 |
| 22% | $94,300–$201,050 |
| 24% | $201,050–$383,900 |
| 32% | $383,900–$487,450 |
| 35% | $487,450–$731,200 |
| 37% | $731,200+ |

§199A QBI phase-out:
- Single: $191,950 → $241,950
- MFJ: $383,900 → $483,900

### 20.6 Tax-equivalent yield

```
TEY  =  muni_yield / (1 − marginal_tax_rate)
```

Example: 4% muni at 32% bracket = 5.88% taxable equivalent.

---

## 21. Milestones & 28-month roadmap

Anchor: `STRATEGY_START_DATE = 2025-10-09`. Capital deployment cumulative.

| Phase | Window | Capital deployed | Expected dividends | Milestone |
|---|---|---:|---:|---|
| Foundation | Months 1–6 | $79,902 | $1,000–2,000/mo | All 11 positions established |
| Acceleration | Months 7–12 | $159,804 | $3,000–4,500/mo | First fund rotation likely (MSTY/YMAX yield compression) |
| Break-even zone | Months 13–18 | $239,706 | $5,000–7,000/mo | Dividends > $4,500/mo (covers fixed expenses) |
| Scale or consolidate | Months 19–24 | $319,608 | $7,000–9,000/mo | Decision point: scale margin or pay it down |
| Victory lap | Months 25–28 | $373,076 | ~$9,222/mo ≈ $110,661/yr | Financial independence (69.2% MC probability) |

### 21.1 Fund-rotation triggers (active management)

| Condition | Action | Priority |
|---|---|---|
| Single fund cuts > 50% | Sell within 48h; rotate to JEPI/JEPQ | Immediate |
| Single fund cuts 30–50% | Pause purchases; monitor 30 days | High |
| Blended Layer 2 yield < 24% | Major rebalance within 2 weeks (replace 2–3 underperformers) | High |

### 21.2 Quarterly review (every 3 months)

1. Run correlation matrix (`correlation_cli.py`).
2. Trim positions > 25% over bucket target.
3. Stop contributions to positions < 3% of Layer 2.
4. Replace underperformers with > 20% yield degradation across 2 quarters.
5. Validate hedge ratio (≈ 5%); adjust if drifted.
6. Update Monte Carlo if regime shifted.

### 21.3 Operating cadence

| Frequency | Items |
|---|---|
| **Daily** | Portfolio value · margin balance (if active) · portfolio-to-margin ratio (if active) |
| **Weekly** | Layer 2 distributions collected · TTM yield per holding · flag > 15% monthly changes |
| **Monthly week 1** | W2 deployment per bucket allocation (buy ticket workflow) |
| **Monthly week 2** | Record dividends · update trailing 30-day yield |
| **Monthly week 3** | Recalculate portfolio beta · review hedge effectiveness |
| **Monthly week 4** | Update dashboard · progress toward $100k |
| **Quarterly** | See § 21.2 |

---

## 22. Compliance & disclosure

`fin-guru/data/compliance-policy.md`.

### 22.1 Mandatory deliverable elements

Every analysis output must include:
1. **Analytical framework** — methodology and theoretical basis stated.
2. **Source attribution** — all data cited with timestamps.
3. **Assumption documentation** — assumptions listed with sensitivity analysis.
4. **Risk quantification** — VaR, Sharpe, max DD, etc.
5. **Implementation guidance** — actionable next steps.

### 22.2 Educational disclaimer (mandatory footer)

Every ticket and analysis ends with:

> _"Educational Notice: For educational purposes only; not investment advice. Consult a licensed financial professional before acting. All investments involve risk, including possible loss of principal."_

Options-specific extension:

> _"Opening a protective put program commits monthly premium that is lost if market rises or stays flat."_
>
> _"Closing a hedge removes portfolio protection; subsequent drawdowns are borne in full."_

### 22.3 Data handling

- Never include account numbers, SSNs, or sensitive personal identifiers in any output.
- Always cite sources with timestamps; cross-reference critical data.
- Separate facts from assumptions; document modeling assumptions and limitations.

### 22.4 Performance-bench commitment

| Standard | Target |
|---|---|
| Calculation accuracy | 99.5% |
| Framework completeness | 100% |
| Reproducibility | Independent reproducibility required |

---

## 23. Source index

Where to look for canonical authority on each topic. The first row of each cluster is the primary source.

### Python toolkit (`src/`)
- Risk metrics → `src/analysis/risk_metrics.py` + `src/models/risk_inputs.py`
- Volatility → `src/utils/volatility.py`
- Momentum → `src/utils/momentum.py`
- Moving averages → `src/utils/moving_averages.py`
- Options & Greeks → `src/analysis/options.py` + `src/models/options_inputs.py`
- Hedge sizing → `src/analysis/hedge_sizer.py`
- Hedge comparison (SQQQ vs puts) → `src/analysis/hedge_comparison.py`
- Correlation → `src/analysis/correlation.py`
- Factor models → `src/analysis/factors.py`
- Total return / DRIP → `src/analysis/total_return.py`
- ITC risk → `src/analysis/itc_risk.py`
- Rolling tracker → `src/analysis/rolling_tracker.py`
- Architecture rules → `src/CLAUDE.md`

### Agent reference data (`fin-guru/data/`)
- Risk framework → `risk-framework.md`
- Margin strategy (tier framework) → `margin-strategy.md`
- Modern income vehicles (classifier source) → `modern-income-vehicles.md`
- Tax optimization → `tax-optimization.md`
- Compliance policy → `compliance-policy.md`
- Analytical framework → `analytical-framework.md`
- Hedging strategies → `hedging-strategies.md`, `options-insurance-framework.md`
- Spreadsheet contracts → `spreadsheet-architecture.md`, `spreadsheet-quick-ref.md`
- User profile (deployment & milestones) → `user-profile.yaml`
- System context → `system-context.md`

### Skills (`.claude/skills/`)
- Margin dashboard ops → `margin-management/SKILL.md`
- Dividend sync → `dividend-tracking/SKILL.md`
- Buy-ticket workflow + pre-flight gates → `fin-guru-buy-ticket/SKILL.md` + `references/workflow-patterns.md`
- Hedge roll lifecycle → `fin-guru-hedge-roll/SKILL.md` + `references/framework-rules.md` + `references/roll-decision-tree.md`
- Monte Carlo → `MonteCarlo/SKILL.md` + `PortfolioParser.md`
- Portfolio CSV sync → `PortfolioSyncing/SKILL.md`
- Transaction sync + categorization → `TransactionSyncing/SKILL.md` + `CategoryRules.md`
- Retirement aggregation → `retirement-syncing/SKILL.md`
- Formula protection → `formula-protection/SKILL.md`
- Reports → `FinanceReport/SKILL.md`

### Private strategies (`fin-guru-private/fin-guru/strategies/`)
- Master allocation → `active/portfolio-master-strategy.md`
- Layer 2 specifics → `active/dividend-income-master-strategy.md`
- DRIP v2 simulation → `active/self-sustaining-leverage-drip-strategy-v2.md`
- Downside protection (current) → `risk-management/downside-protection-strategy.md`
- Numeric configs → `active/bucket-allocations.json`, `deployment-formula.json`, `risk-thresholds.json`, `active-management-triggers.json`, `concentration-limits.json`

---

## Appendix A. Formula quick card

```
# Yield & income
dividend_yield                 = Σ_TTM(distributions) / current_price
dividends_received_ticker      = quantity × amount_per_share
estimated_dividend_per_ticker  = quantity × monthly_DPS  ≡  position_value · annual_yield / 12
monthly_dividend_income        = Σ estimated_dividend_per_ticker

# Total return
price_return                   = (P_end − P_start) / P_start
dividend_return                = Σ DPS / P_start
total_return                   = price_return + dividend_return
annualized_return              = (1 + total_return)^(365 / days) − 1
drip_return                    = (final_shares × final_price) / (init_shares × init_price) − 1

# Margin
margin_balance                 = | Net_debit |                         # CSV row
margin_draw                    = max(0, deployment − cash)
monthly_interest               = margin_balance × annual_rate / 12
coverage_ratio                 = monthly_dividend_income / monthly_interest
portfolio_to_margin_ratio      = total_account_value / margin_balance
self_sustaining_rule           = monthly_div > monthly_interest × 1.5

# Risk metrics
sharpe                         = (μ − R_f/252) / σ × √252
sortino                        = (μ − R_f/252) / σ_downside × √252
annual_vol                     = σ_daily × √252
max_drawdown                   = min((P_t − running_max) / running_max)
calmar                         = (μ × 252) / |max_drawdown|
var_historical                 = percentile(returns, (1 − conf) × 100)
cvar                           = mean(returns where r ≤ VaR)
beta                           = Cov(asset, bench) / Var(bench)
alpha_capm                     = R − [R_f + β × (R_bench − R_f)]

# Options (Black-Scholes)
d1                             = [ln(S/K) + (r − q + σ²/2)·T] / (σ·√T)
d2                             = d1 − σ·√T
call                           = S·e^(−qT)·N(d1) − K·e^(−rT)·N(d2)
put                            = K·e^(−rT)·N(−d2) − S·e^(−qT)·N(−d1)
delta_call                     = e^(−qT)·N(d1)
gamma                          = e^(−qT)·n(d1) / (S·σ·√T)
vega                           = S·e^(−qT)·√T·n(d1) / 100
theta_daily                    = θ_annual / 365
rho_call                       = K·T·e^(−rT)·N(d2) / 100
put_call_parity                = C − P = S·e^(−qT) − K·e^(−rT)         # arb if |Δ| > $0.10

# Hedge sizing
contracts                      = floor(portfolio_value / $50,000)
otm_strike_for_put             = spot × 0.85                            # 15% OTM
cost_to_roll                   = (new_premium · qty · 100) − old_residual
annual_hedge_budget            = portfolio_value × 0.030..0.035

# Pre-flight gates
remaining_cash                 = current_cash − deployment_amount
new_position_pct               = (existing + deploy[ticker]) / (portfolio + deploy_total)
                                                                        # warn if > 0.30

# Volatility
true_range                     = max(H − L, |H − C_prev|, |L − C_prev|)
atr                            = EMA(TR, 14)
bollinger_band                 = SMA(close, 20) ± 2·σ
keltner_band                   = EMA(close, 20) ± 2·ATR

# Momentum
rsi                            = 100 − 100/(1 + avg_gain/avg_loss)
macd                           = EMA(12) − EMA(26)
macd_signal                    = EMA(MACD, 9)
roc                            = (C − C_n)/C_n × 100

# Moving averages
sma                            = (P1 + … + Pn) / n
ema                            = α·P + (1 − α)·EMA_prev,  α = 2/(n+1)
hma                            = WMA(2·WMA(n/2) − WMA(n), √n)

# Tax
tax_equivalent_yield           = muni_yield / (1 − marginal_tax_rate)
after_tax_yield                = gross_yield × (1 − effective_tax_rate)

# Strategy timing
months_elapsed                 = (today − 2025-10-09).days // 30
```

---

_End of file._
