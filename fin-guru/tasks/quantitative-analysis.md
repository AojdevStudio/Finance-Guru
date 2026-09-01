# Quantitative Analysis Task Workflow

## Purpose and Scope

This workflow guides the Quant Analyst through rigorous quantitative financial analysis using Finance Guru's production-ready analytical tools. All analysis follows type-safe, validated methodologies with institutional-quality metrics.

### Core Analytical Capabilities

- **Risk/Return Metrics**: Sharpe ratio, Sortino ratio, Calmar ratio, maximum drawdown, VaR, CVaR
- **Momentum Analysis**: RSI, MACD, Stochastic Oscillator, Williams %R, ROC with confluence detection
- **Volatility Analysis**: Bollinger Bands, ATR, historical volatility, regime classification
- **Correlation Analysis**: Portfolio diversification assessment, correlation matrices, covariance analysis
- **Moving Average Analysis**: SMA, EMA, WMA, HMA with Golden Cross/Death Cross detection
- **Strategy Backtesting**: Historical performance validation, returns analysis, risk-adjusted metrics
- **Portfolio Optimization**: Mean-Variance, Risk Parity, Min Variance, Max Sharpe, Black-Litterman
- **Portfolio Analytics**: Multi-security analysis, benchmark comparisons, risk attribution
- **Scenario Modeling**: Market condition analysis and timing validation

### When to Use This Workflow

**Primary Use Cases:**
- Validating investment strategies through quantitative analysis
- Running comprehensive risk assessments on portfolios or positions
- Timing analysis for entry/exit points using momentum indicators
- Volatility regime assessment for position sizing and risk management
- Portfolio diversification assessment and concentration risk analysis
- Trend confirmation using multiple moving average types
- Optimal portfolio allocation across different risk-return objectives
- Historical strategy validation before deployment
- Creating professional financial analysis artifacts with proper documentation

**Prerequisites:**
- Access to risk_metrics_cli.py, momentum_cli.py, volatility_cli.py, correlation_cli.py, moving_averages_cli.py, optimizer_cli.py, and backtester_cli.py tools
- Minimum 30 days of market data (90-252 days recommended)
- Clear investment objectives and risk constraints

---

## Workflow Steps

### Step 1: Define Analysis Objectives

**Action:** Clarify with user what specific analysis is needed.

**Questions to Ask:**
- What securities or portfolio are we analyzing?
- What is the analysis timeframe? (90 days for momentum, 252 days for full-cycle risk)
- Do we need benchmark comparison? (typically SPY for US equities)
- What are the risk tolerance constraints?
- What decision are we trying to inform?
- Do we need portfolio diversification assessment?
- Are we validating a specific trading strategy?
- Do we need optimal portfolio allocation?

**Output:** Clear scope and parameters for analysis.

---

### Step 2: Gather Market Data

**Action:** Verify data availability and quality.

**Tools:**
- Use `src/utils/market_data.py` for quick price checks
- Risk and momentum tools automatically fetch historical data

**Quality Checks:**
- Confirm sufficient data history (minimum 30 days, prefer 252 days)
- Note any gaps in trading days (market closures)
- Verify ticker symbols are correct

**Output:** Confirmed data availability and quality.

---

### Step 3: Run Risk Metrics Analysis

**Action:** Calculate comprehensive risk metrics using production tool.

**Tool:** `risk_metrics_cli.py`

**For Individual Securities:**
```bash
# Full analysis with benchmark
uv run python -m src.analysis.risk_metrics_cli [TICKER] --days 252 --benchmark SPY

# Custom risk parameters
uv run python -m src.analysis.risk_metrics_cli [TICKER] --days 252 \
  --confidence 0.99 \
  --var-method parametric \
  --risk-free-rate 0.05
```

**For Portfolio Analysis:**
```bash
# Batch analysis across holdings
for ticker in TSLA PLTR NVDA; do
  uv run python -m src.analysis.risk_metrics_cli $ticker --days 252 --benchmark SPY --output json
done
```

**Interpret Results:**
- **Sharpe Ratio** >1.0 = Good risk-adjusted return, >2.0 = Excellent
- **Max Drawdown** >30% = High risk flag, requires additional risk management
- **VaR/CVaR** = Expected losses in tail scenarios
- **Beta** >1.5 = High market sensitivity (aggressive)
- **Alpha** >0 = Outperformance vs benchmark

**Output:** Risk profile with all key metrics calculated and validated.

---

### Step 4: Run Momentum Analysis

**Action:** Assess timing and momentum characteristics.

**Tool:** `momentum_cli.py`

**For Timing Analysis:**
```bash
# All indicators with confluence
uv run python -m src.utils.momentum_cli [TICKER] --days 90

# Specific indicator focus
uv run python -m src.utils.momentum_cli [TICKER] --days 90 --indicator rsi

# Custom periods for sensitivity
uv run python -m src.utils.momentum_cli [TICKER] --days 90 \
  --rsi-period 21 \
  --macd-fast 8 \
  --macd-slow 21
```

**For Portfolio Screening:**
```bash
# Momentum confluence across holdings
for ticker in TSLA PLTR NVDA; do
  uv run python -m src.utils.momentum_cli $ticker --days 90
done
```

**Interpret Results:**
- **Confluence (3+ indicators agreeing)** = Strong momentum signal
- **RSI >70** = Overbought, potential selling pressure
- **RSI <30** = Oversold, potential buying opportunity
- **MACD Crossover** = Trend change signal
- **Mixed Signals** = Wait for clearer picture

**Output:** Momentum profile with timing recommendations.

---

### Step 5: Run Volatility Analysis

**Action:** Calculate volatility metrics for risk management and position sizing.

**Tool:** `volatility_cli.py`

**For Volatility Assessment:**
```bash
# Full volatility analysis with regime classification
uv run python -m src.utils.volatility_cli [TICKER] --days 90

# Specific indicator focus
uv run python -m src.utils.volatility_cli [TICKER] --days 90 --indicator bollinger

# Custom parameters
uv run python -m src.utils.volatility_cli [TICKER] --days 90 \
  --bb-period 20 \
  --bb-std 2.0 \
  --atr-period 14
```

**For Portfolio Volatility Screening:**
```bash
# Volatility regime across holdings
for ticker in TSLA PLTR NVDA; do
  uv run python -m src.utils.volatility_cli $ticker --days 90
done
```

**Interpret Results:**
- **Bollinger Bands** - Price channels for identifying overbought/oversold conditions
- **ATR (Average True Range)** - Volatility-based stop-loss sizing
- **Historical Volatility** - Annualized volatility for regime assessment
- **Volatility Regime** - Classification (low/normal/high/extreme) for position sizing

**Volatility Regime Guidelines:**
- **Low (<15%)**: Consider increasing position sizes
- **Normal (15-25%)**: Standard position sizing
- **High (25-35%)**: Reduce position sizes, tighten stops
- **Extreme (>35%)**: Minimal exposure, defensive positioning

**Output:** Volatility profile with regime classification and position sizing guidance.

---

### Step 6: Run Correlation Analysis

**Action:** Assess portfolio diversification and concentration risk.

**Tool:** `correlation_cli.py`

**For Portfolio Diversification:**
```bash
# Correlation matrix for portfolio holdings
uv run python -m src.analysis.correlation_cli TSLA PLTR NVDA --days 252

# Include benchmark for market correlation
uv run python -m src.analysis.correlation_cli TSLA PLTR NVDA SPY --days 252

# Custom correlation period
uv run python -m src.analysis.correlation_cli TSLA PLTR NVDA \
  --days 90 \
  --method pearson

# JSON output for programmatic use
uv run python -m src.analysis.correlation_cli TSLA PLTR NVDA --days 252 --output json
```

**For Hedge Identification:**
```bash
# Find low/negative correlation assets
uv run python -m src.analysis.correlation_cli TSLA TLT GLD --days 252
```

**Interpret Results:**
- **Correlation >0.7** = High positive correlation (concentration risk)
- **Correlation 0.3-0.7** = Moderate correlation (some diversification)
- **Correlation <0.3** = Low correlation (good diversification)
- **Correlation <0** = Negative correlation (hedge candidate)
- **Diversification Score** = Overall portfolio diversification quality

**Concentration Risk Guidelines:**
- **Diversification Score >0.7** = WARNING - Highly correlated portfolio
- **Diversification Score 0.4-0.7** = Moderate concentration risk
- **Diversification Score <0.4** = Well-diversified portfolio

**Use Cases:**
- **Portfolio Construction**: Identify uncorrelated assets to add
- **Hedge Selection**: Find negative correlation instruments
- **Risk Management**: Flag concentration risk in correlated positions
- **Rebalancing**: Reduce exposure to highly correlated clusters

**Output:** Correlation matrix, diversification score, and concentration risk assessment.

---

### Step 7: Run Moving Average Analysis

**Action:** Assess trend direction and confirm momentum findings using multiple moving average types.

**Tool:** `moving_averages_cli.py`

**For Trend Analysis:**
```bash
# All moving average types (SMA, EMA, WMA, HMA)
uv run python -m src.utils.moving_averages_cli [TICKER] --days 252

# Specific MA type focus
uv run python -m src.utils.moving_averages_cli [TICKER] --days 252 --indicator sma

# Golden Cross/Death Cross detection (50/200 SMA)
uv run python -m src.utils.moving_averages_cli [TICKER] --days 252 \
  --periods 50 200

# Custom periods for different timeframes
uv run python -m src.utils.moving_averages_cli [TICKER] --days 252 \
  --periods 10 20 50 100 200
```

**For Portfolio Trend Screening:**
```bash
# Trend analysis across holdings
for ticker in TSLA PLTR NVDA; do
  uv run python -m src.utils.moving_averages_cli $ticker --days 252
done
```

**Interpret Results:**
- **Golden Cross** (50 MA crosses above 200 MA) = Major bullish signal, long-term uptrend
- **Death Cross** (50 MA crosses below 200 MA) = Major bearish signal, long-term downtrend
- **Price Above All MAs** = Strong uptrend, bullish momentum
- **Price Below All MAs** = Strong downtrend, bearish momentum
- **MA Slope** = Trend strength (steeper slope = stronger trend)

**Moving Average Types:**
- **SMA (Simple)** - Classic, equal weighting, best for long-term trends
- **EMA (Exponential)** - Responsive, recent data weighted, best for trend changes
- **WMA (Weighted)** - Balanced responsiveness, linear weighting
- **HMA (Hull)** - Smoothest, least lag, best for noise reduction

**Integration with Momentum:**
- **Momentum + MA Alignment** = High confidence signal (e.g., bullish momentum + Golden Cross)
- **Momentum vs MA Divergence** = Warning signal (e.g., bullish momentum but Death Cross)
- **Use MA crossovers to time entries** based on momentum confluence

**Output:** Trend direction assessment, Golden Cross/Death Cross signals, MA confluence with momentum analysis.

---

### Step 8: Synthesize Analysis

**Action:** Integrate risk, momentum, volatility, correlation, and moving average findings into coherent assessment.

**Synthesis Questions:**
- Do risk metrics support the proposed position size?
- Does momentum analysis support the proposed timing?
- What does volatility regime suggest for position sizing?
- Is the portfolio properly diversified? (correlation analysis)
- Are there concentration risks from highly correlated positions?
- What trend signals do the moving averages show?
- Does the Golden Cross/Death Cross align with momentum indicators?
- Are there any red flags (high drawdown, negative alpha, poor momentum, extreme volatility, high correlation, bearish MA signals)?
- What is the overall risk/reward profile?

**Decision Framework:**
- **Green Light:** Good risk-adjusted returns (Sharpe >1.0) + Positive momentum confluence + Normal/low volatility + Well-diversified (<0.4 correlation) + Bullish MA alignment
- **Yellow Light:** Mixed signals - one or two metrics favorable, others neutral
- **Red Light:** Poor risk metrics (Sharpe <0.5, Max DD >30%) OR strong bearish confluence OR extreme volatility OR high concentration risk (>0.7 correlation) OR Death Cross with bearish momentum

**Output:** Integrated quantitative assessment with clear recommendation.

---

### Step 9: Backtest Strategy (If Applicable)

**Action:** Validate trading strategy using historical performance analysis.

**Tool:** `backtester_cli.py`

**For Strategy Validation:**
```bash
# Backtest RSI mean reversion strategy
uv run python -m src.strategies.backtester_cli [TICKER] \
  --strategy rsi \
  --days 252 \
  --capital 10000

# Backtest SMA crossover strategy
uv run python -m src.strategies.backtester_cli [TICKER] \
  --strategy sma_cross \
  --days 252 \
  --capital 10000

# Buy-and-hold benchmark comparison
uv run python -m src.strategies.backtester_cli [TICKER] \
  --strategy buy_hold \
  --days 252 \
  --capital 10000

# Custom transaction costs
uv run python -m src.strategies.backtester_cli [TICKER] \
  --strategy rsi \
  --days 252 \
  --capital 10000 \
  --commission 5.0 \
  --slippage 0.001
```

**For Multi-Asset Backtesting:**
```bash
# Backtest strategy across portfolio holdings
for ticker in TSLA PLTR NVDA; do
  uv run python -m src.strategies.backtester_cli $ticker \
    --strategy rsi \
    --days 252 \
    --output json
done
```

**Interpret Results:**
- **Total Return** = Overall profit/loss percentage
- **Sharpe Ratio** = Risk-adjusted performance (>1.0 = good, >2.0 = excellent)
- **Max Drawdown** = Largest peak-to-trough decline (<20% = acceptable)
- **Win Rate** = Percentage of profitable trades (>50% = positive edge)
- **Profit Factor** = Gross profit / Gross loss (>1.5 = robust strategy)
- **Number of Trades** = Trade frequency (ensure sufficient sample size)

**Decision Framework:**
- **DEPLOY:** Sharpe >1.0 + Max DD <20% + Win Rate >50% + Profit Factor >1.5
- **OPTIMIZE:** Positive returns but one weak metric - refine parameters
- **REJECT:** Negative returns OR Sharpe <0.5 OR Max DD >30% OR Win Rate <40%

**Use Cases:**
- **Strategy Validation**: Test before risking capital
- **Parameter Optimization**: Find optimal entry/exit rules
- **Risk Assessment**: Understand worst-case drawdown scenarios
- **Comparative Analysis**: Compare multiple strategy approaches

**Output:** Backtest results with DEPLOY/OPTIMIZE/REJECT recommendation.

---

### Step 10: Run Portfolio Optimization (If Applicable)

**Action:** Determine optimal portfolio allocation based on risk-return objectives.

**Tool:** `optimizer_cli.py`

**For Portfolio Optimization:**
```bash
# Mean-Variance Optimization (maximize Sharpe ratio)
uv run python -m src.strategies.optimizer_cli TSLA PLTR NVDA \
  --method mean_variance \
  --days 252 \
  --risk-free-rate 0.05

# Risk Parity (equal risk contribution)
uv run python -m src.strategies.optimizer_cli TSLA PLTR NVDA \
  --method risk_parity \
  --days 252

# Minimum Variance (lowest portfolio volatility)
uv run python -m src.strategies.optimizer_cli TSLA PLTR NVDA \
  --method min_variance \
  --days 252

# Maximum Sharpe (highest risk-adjusted return)
uv run python -m src.strategies.optimizer_cli TSLA PLTR NVDA \
  --method max_sharpe \
  --days 252 \
  --risk-free-rate 0.05

# Black-Litterman (incorporate market views)
uv run python -m src.strategies.optimizer_cli TSLA PLTR NVDA \
  --method black_litterman \
  --days 252 \
  --risk-free-rate 0.05 \
  --market-cap-weights 0.4 0.3 0.3
```

**For Constrained Optimization:**
```bash
# Add position limits
uv run python -m src.strategies.optimizer_cli TSLA PLTR NVDA \
  --method mean_variance \
  --days 252 \
  --min-weight 0.05 \
  --max-weight 0.50

# Target specific return level
uv run python -m src.strategies.optimizer_cli TSLA PLTR NVDA \
  --method mean_variance \
  --days 252 \
  --target-return 0.15
```

**Interpret Results:**
- **Optimal Weights** = Recommended allocation percentages
- **Expected Return** = Predicted portfolio return
- **Expected Volatility** = Predicted portfolio risk
- **Sharpe Ratio** = Risk-adjusted performance
- **Risk Contribution** = How much each asset contributes to portfolio risk

**Optimization Methods - When to Use:**

**Mean-Variance (Markowitz)**
- **Use When**: Building balanced portfolios with moderate risk tolerance
- **Best For**: Traditional diversified portfolios, long-term investors
- **Considerations**: Sensitive to estimation errors, can produce concentrated portfolios

**Risk Parity**
- **Use When**: Want equal risk contribution from all assets
- **Best For**: Risk-conscious investors, balanced portfolios, uncertain market regimes
- **Considerations**: May reduce exposure to high-return assets

**Minimum Variance**
- **Use When**: Capital preservation is the priority
- **Best For**: Conservative investors, high-volatility markets, defensive positioning
- **Considerations**: May sacrifice returns for stability

**Maximum Sharpe**
- **Use When**: Maximizing risk-adjusted returns is the goal
- **Best For**: Performance-focused portfolios, skilled investors
- **Considerations**: Can produce aggressive allocations, sensitive to input parameters

**Black-Litterman**
- **Use When**: You have specific market views to incorporate
- **Best For**: Active management, tactical allocation, market view expression
- **Considerations**: Requires market equilibrium assumptions and view confidence

**Decision Framework:**
- **Monthly Rebalancing**: Use Mean-Variance or Max Sharpe for active management
- **Quarterly Rebalancing**: Use Risk Parity for balanced approach
- **New Capital Deployment**: Compare all methods, choose based on risk tolerance
- **Defensive Positioning**: Use Minimum Variance in uncertain markets
- **Tactical Views**: Use Black-Litterman to express specific market opinions

**Use Cases:**
- **Portfolio Construction**: Initial allocation for new portfolios
- **Rebalancing**: Monthly/quarterly portfolio adjustments
- **New Capital Deployment**: Optimal allocation of additional funds
- **Risk Budgeting**: Allocate capital based on risk contribution
- **Tactical Allocation**: Adjust weights based on market views

**Output:** Optimal portfolio weights with expected risk-return profile and allocation rationale.

---

### Step 11: Document Findings

**Action:** Save analysis results for handoff and records.

**Documentation:**
```bash
# Save risk analysis
uv run python -m src.analysis.risk_metrics_cli [TICKER] --days 252 --benchmark SPY \
  --output json \
  --save-to analysis/quant-risk-[TICKER]-$(date +%Y-%m-%d).json

# Save momentum analysis
uv run python -m src.utils.momentum_cli [TICKER] --days 90 \
  --output json \
  --save-to analysis/quant-momentum-[TICKER]-$(date +%Y-%m-%d).json

# Save volatility analysis
uv run python -m src.utils.volatility_cli [TICKER] --days 90 \
  --output json \
  --save-to analysis/quant-volatility-[TICKER]-$(date +%Y-%m-%d).json

# Save correlation analysis
uv run python -m src.analysis.correlation_cli TSLA PLTR NVDA --days 252 \
  --output json \
  --save-to analysis/quant-correlation-$(date +%Y-%m-%d).json

# Save moving average analysis
uv run python -m src.utils.moving_averages_cli [TICKER] --days 252 \
  --output json \
  --save-to analysis/quant-ma-[TICKER]-$(date +%Y-%m-%d).json

# Save backtest results
uv run python -m src.strategies.backtester_cli [TICKER] \
  --strategy rsi --days 252 \
  --output json \
  --save-to analysis/quant-backtest-[TICKER]-$(date +%Y-%m-%d).json

# Save optimization results
uv run python -m src.strategies.optimizer_cli TSLA PLTR NVDA \
  --method mean_variance --days 252 \
  --output json \
  --save-to analysis/quant-optimization-$(date +%Y-%m-%d).json
```

**Report Structure:**
1. **Executive Summary** - Key findings and recommendation
2. **Risk Profile** - All risk metrics with interpretations
3. **Momentum Analysis** - Current momentum state and signals
4. **Volatility Assessment** - Regime classification and position sizing guidance
5. **Correlation Analysis** - Diversification score and concentration risks
6. **Moving Average Analysis** - Trend direction, Golden Cross/Death Cross signals
7. **Backtest Results** (if applicable) - Historical strategy performance
8. **Portfolio Optimization** (if applicable) - Optimal allocation with rationale
9. **Recommendations** - Specific actions with rationale
10. **Caveats** - Assumptions, limitations, data quality notes

**Output:** Professional analysis report ready for Strategy Advisor handoff.

---

### Step 12: Quality Validation

**Action:** Validate analysis quality before finalizing.

**Validation Checklist:**
- [ ] Sufficient data used (90+ days minimum, 252 preferred)
- [ ] Benchmark comparison included for context
- [ ] All key risk metrics calculated (Sharpe, Sortino, Max DD, VaR)
- [ ] Momentum confluence assessed (not just single indicator)
- [ ] Volatility regime classified and considered in recommendations
- [ ] Correlation analysis completed for multi-asset portfolios
- [ ] Moving average trend analysis performed with Golden Cross/Death Cross detection
- [ ] Backtest performed for strategy validation (if applicable)
- [ ] Portfolio optimization run for allocation decisions (if applicable)
- [ ] Results make intuitive sense (no anomalies)
- [ ] Data date is current (within 3 days)
- [ ] Analysis saved to analysis/ directory
- [ ] Recommendations are clear and actionable

**Output:** Quality-validated analysis ready for decision-making.

---

## Usage Scenarios

### Scenario 1: New Position Analysis

**Objective:** Evaluate risk/reward of proposed new investment

**Workflow:**
1. Run 252-day risk metrics with benchmark
2. Run 90-day momentum analysis
3. Run 90-day volatility analysis with regime classification
4. Check correlation with existing portfolio holdings
5. Run moving average analysis to confirm trend direction
6. Compare to portfolio risk tolerance
7. Check momentum confluence for timing
8. Validate trend with Golden Cross/Death Cross signals
9. Adjust position size based on volatility regime and correlation
10. Recommend position size and entry timing

**Expected Output:** Risk-validated position recommendation with volatility-adjusted sizing and diversification assessment

---

### Scenario 2: Portfolio Risk Assessment

**Objective:** Comprehensive risk analysis of existing holdings

**Workflow:**
1. Batch risk metrics across all holdings
2. Identify highest risk contributors (Max DD, Beta)
3. Run correlation analysis to identify concentration risks
4. Check momentum for rebalancing signals
5. Assess volatility regimes across portfolio
6. Run moving average analysis to identify trend changes
7. Run portfolio optimization to determine optimal rebalancing
8. Synthesize portfolio-level risk profile
9. Flag positions exceeding risk limits or in extreme volatility
10. Identify highly correlated clusters requiring diversification

**Expected Output:** Portfolio risk dashboard with rebalancing and diversification recommendations

---

### Scenario 3: Entry/Exit Timing

**Objective:** Determine optimal timing for trade execution

**Workflow:**
1. Run momentum analysis on target security
2. Check confluence across all 5 indicators
3. Assess current volatility regime
4. Run moving average analysis for trend confirmation
5. Check for Golden Cross/Death Cross signals
6. Validate with risk metrics (not entering high-risk periods)
7. Calculate volatility-based stop-loss levels using ATR
8. Identify specific entry/exit signals
9. Set up monitoring for trigger conditions

**Expected Output:** Timing recommendation with specific signals and stop-loss levels

---

### Scenario 4: Strategy Validation

**Objective:** Quantitatively validate proposed investment strategy before deployment

**Workflow:**
1. Run risk metrics on strategy components
2. Assess historical risk-adjusted performance
3. Check momentum for current market fit
4. Evaluate strategy performance across different volatility regimes
5. Validate trend alignment with moving averages
6. Run full historical backtest with strategy rules
7. Compare backtest results to benchmark performance
8. Assess strategy Sharpe ratio, max drawdown, win rate
9. Issue DEPLOY/OPTIMIZE/REJECT recommendation
10. Identify strategy weaknesses/strengths

**Expected Output:** Strategy validation report with quantitative go/no-go recommendation based on backtest results

---

### Scenario 5: Portfolio Diversification Assessment

**Objective:** Evaluate portfolio diversification and identify concentration risks

**Workflow:**
1. Run correlation analysis on all portfolio holdings
2. Calculate diversification score
3. Identify highly correlated asset clusters (>0.7 correlation)
4. Search for low/negative correlation hedge candidates
5. Assess correlation with market benchmark (SPY)
6. Run portfolio optimization to find optimal allocation
7. Compare current allocation vs optimal allocation
8. Recommend portfolio rebalancing to reduce concentration
9. Suggest uncorrelated assets to improve diversification

**Expected Output:** Diversification report with correlation matrix, concentration risk warnings, and rebalancing recommendations

---

### Scenario 6: Monthly Portfolio Rebalancing

**Objective:** Optimize portfolio allocation for the next period

**Workflow:**
1. Run risk metrics on all holdings (252-day period)
2. Run correlation analysis to assess current diversification
3. Run moving average analysis to identify trend changes
4. Check momentum for each position to validate holdings
5. Assess volatility regimes for position sizing adjustments
6. Run portfolio optimization (compare Mean-Variance vs Risk Parity)
7. Calculate optimal weights based on current market conditions
8. Compare current allocation vs optimal allocation
9. Identify rebalancing trades needed (buys/sells)
10. Document rationale for allocation changes

**Expected Output:** Monthly rebalancing report with optimal weights, trade list, and allocation rationale

---

## Available Tools

### Risk Metrics Calculator

**Production Tool:** `src/analysis/risk_metrics_cli.py`

**Basic Usage:**
```bash
# Full analysis with benchmark
uv run python -m src.analysis.risk_metrics_cli [TICKER] --days 252 --benchmark SPY

# Custom parameters
uv run python -m src.analysis.risk_metrics_cli [TICKER] --days 252 \
  --confidence 0.99 \
  --var-method parametric \
  --risk-free-rate 0.05

# JSON output for programmatic use
uv run python -m src.analysis.risk_metrics_cli [TICKER] --days 252 --output json

# Batch portfolio analysis
for ticker in TSLA PLTR NVDA; do
  uv run python -m src.analysis.risk_metrics_cli $ticker --days 252 --benchmark SPY --output json
done
```

**Metrics Available:**
- VaR (95%), CVaR (Expected Shortfall)
- Sharpe Ratio, Sortino Ratio
- Max Drawdown, Calmar Ratio
- Annual Volatility
- Beta, Alpha (with benchmark)

**Documentation:** `guides/risk-metrics-tool-guide.md`

---

### Momentum Indicators

**Production Tool:** `src/utils/momentum_cli.py`

**Basic Usage:**
```bash
# All indicators with confluence
uv run python -m src.utils.momentum_cli [TICKER] --days 90

# Specific indicator
uv run python -m src.utils.momentum_cli [TICKER] --days 90 --indicator rsi

# Custom periods
uv run python -m src.utils.momentum_cli [TICKER] --days 90 \
  --rsi-period 21 \
  --macd-fast 8 \
  --macd-slow 21

# JSON for programmatic use
uv run python -m src.utils.momentum_cli [TICKER] --days 90 --output json
```

**Indicators Available:**
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- Stochastic Oscillator
- Williams %R
- ROC (Rate of Change)

**Special Feature:** Confluence analysis (counts bullish/bearish signals across all 5 indicators)

---

### Volatility Metrics

**Production Tool:** `src/utils/volatility_cli.py`

**Basic Usage:**
```bash
# Full volatility analysis with all indicators
uv run python -m src.utils.volatility_cli [TICKER] --days 90

# Specific indicator
uv run python -m src.utils.volatility_cli [TICKER] --days 90 --indicator bollinger

# Custom parameters
uv run python -m src.utils.volatility_cli [TICKER] --days 90 \
  --bb-period 20 \
  --bb-std 2.0 \
  --atr-period 14

# JSON for programmatic use
uv run python -m src.utils.volatility_cli [TICKER] --days 90 --output json

# Batch portfolio volatility analysis
for ticker in TSLA PLTR NVDA; do
  uv run python -m src.utils.volatility_cli $ticker --days 90 --output json
done
```

**Indicators Available:**
- Bollinger Bands (price channels with 2 standard deviations)
- ATR - Average True Range (volatility-based stop-loss sizing)
- Historical Volatility (annualized percentage)
- Volatility Regime Classification (low/normal/high/extreme)

**Use Cases:**
- **Position Sizing**: Adjust position sizes based on volatility regime
- **Stop-Loss Placement**: Use ATR for volatility-adjusted stop levels
- **Entry Timing**: Look for Bollinger Band squeezes before breakouts
- **Risk Management**: Reduce exposure during high/extreme volatility regimes

---

### Correlation Analysis

**Production Tool:** `src/analysis/correlation_cli.py`

**Basic Usage:**
```bash
# Portfolio correlation matrix
uv run python -m src.analysis.correlation_cli TSLA PLTR NVDA --days 252

# Include benchmark
uv run python -m src.analysis.correlation_cli TSLA PLTR NVDA SPY --days 252

# Custom parameters
uv run python -m src.analysis.correlation_cli TSLA PLTR NVDA \
  --days 90 \
  --method pearson

# JSON for programmatic use
uv run python -m src.analysis.correlation_cli TSLA PLTR NVDA --days 252 --output json

# Hedge identification
uv run python -m src.analysis.correlation_cli TSLA TLT GLD --days 252
```

**Metrics Available:**
- Correlation Matrix (pairwise correlations)
- Covariance Matrix
- Diversification Score (portfolio-wide metric)
- Concentration Risk Assessment

**Use Cases:**
- **Portfolio Diversification**: Identify concentration risks
- **Hedge Selection**: Find negative correlation instruments
- **Risk Management**: Flag highly correlated positions (>0.7)
- **Rebalancing**: Guide asset allocation decisions

**Interpretation:**
- Correlation >0.7 = High concentration risk
- Correlation 0.3-0.7 = Moderate diversification
- Correlation <0.3 = Good diversification
- Correlation <0 = Hedge candidate

---

### Moving Average Toolkit

**Production Tool:** `src/utils/moving_averages_cli.py`

**Basic Usage:**
```bash
# All moving average types (SMA, EMA, WMA, HMA)
uv run python -m src.utils.moving_averages_cli [TICKER] --days 252

# Specific MA type
uv run python -m src.utils.moving_averages_cli [TICKER] --days 252 --indicator sma

# Golden Cross/Death Cross detection (50/200 SMA)
uv run python -m src.utils.moving_averages_cli [TICKER] --days 252 \
  --periods 50 200

# Custom periods for different timeframes
uv run python -m src.utils.moving_averages_cli [TICKER] --days 252 \
  --periods 10 20 50 100 200

# JSON for programmatic use
uv run python -m src.utils.moving_averages_cli [TICKER] --days 252 --output json

# Batch portfolio trend analysis
for ticker in TSLA PLTR NVDA; do
  uv run python -m src.utils.moving_averages_cli $ticker --days 252 --output json
done
```

**Moving Average Types:**
- **SMA (Simple Moving Average)** - Classic, equal weighting, best for long-term trends
- **EMA (Exponential Moving Average)** - Responsive, recent data weighted, best for trend changes
- **WMA (Weighted Moving Average)** - Balanced responsiveness, linear weighting
- **HMA (Hull Moving Average)** - Smoothest, least lag, best for noise reduction

**Key Signals:**
- **Golden Cross** (50 MA crosses above 200 MA) = Major bullish signal
- **Death Cross** (50 MA crosses below 200 MA) = Major bearish signal
- **Price Above All MAs** = Strong uptrend
- **Price Below All MAs** = Strong downtrend
- **MA Slope** = Trend strength

**Use Cases:**
- **Trend Confirmation**: Validate momentum signals with MA alignment
- **Entry/Exit Timing**: Use Golden Cross/Death Cross for major trend changes
- **Support/Resistance**: MAs act as dynamic support/resistance levels
- **Noise Filtering**: Use HMA to reduce false signals in choppy markets

---

### Strategy Backtesting

**Production Tool:** `src/strategies/backtester_cli.py`

**Basic Usage:**
```bash
# Backtest RSI strategy
uv run python -m src.strategies.backtester_cli [TICKER] \
  --strategy rsi \
  --days 252 \
  --capital 10000

# Backtest SMA crossover strategy
uv run python -m src.strategies.backtester_cli [TICKER] \
  --strategy sma_cross \
  --days 252 \
  --capital 10000

# Buy-and-hold benchmark
uv run python -m src.strategies.backtester_cli [TICKER] \
  --strategy buy_hold \
  --days 252 \
  --capital 10000

# Custom transaction costs
uv run python -m src.strategies.backtester_cli [TICKER] \
  --strategy rsi \
  --days 252 \
  --capital 10000 \
  --commission 5.0 \
  --slippage 0.001

# JSON for programmatic use
uv run python -m src.strategies.backtester_cli [TICKER] \
  --strategy rsi \
  --days 252 \
  --output json
```

**Built-in Strategies:**
- **RSI Mean Reversion** - Buy oversold (RSI <30), sell overbought (RSI >70)
- **SMA Crossover** - Buy when fast MA crosses above slow MA, sell on reverse
- **Buy-and-Hold** - Benchmark strategy for comparison

**Metrics Available:**
- Total Return (%)
- Sharpe Ratio (risk-adjusted return)
- Max Drawdown (%)
- Win Rate (%)
- Profit Factor (gross profit / gross loss)
- Number of Trades
- Average Trade Return

**Use Cases:**
- **Strategy Validation**: Test before deployment
- **Parameter Optimization**: Find optimal entry/exit rules
- **Risk Assessment**: Understand drawdown scenarios
- **Comparative Analysis**: Compare multiple strategies

**Decision Framework:**
- **DEPLOY**: Sharpe >1.0 + Max DD <20% + Win Rate >50%
- **OPTIMIZE**: Positive returns but needs refinement
- **REJECT**: Negative returns or unacceptable risk metrics

---

### Portfolio Optimizer

**Production Tool:** `src/strategies/optimizer_cli.py`

**Basic Usage:**
```bash
# Mean-Variance Optimization
uv run python -m src.strategies.optimizer_cli TSLA PLTR NVDA \
  --method mean_variance \
  --days 252 \
  --risk-free-rate 0.05

# Risk Parity
uv run python -m src.strategies.optimizer_cli TSLA PLTR NVDA \
  --method risk_parity \
  --days 252

# Minimum Variance
uv run python -m src.strategies.optimizer_cli TSLA PLTR NVDA \
  --method min_variance \
  --days 252

# Maximum Sharpe
uv run python -m src.strategies.optimizer_cli TSLA PLTR NVDA \
  --method max_sharpe \
  --days 252 \
  --risk-free-rate 0.05

# Black-Litterman
uv run python -m src.strategies.optimizer_cli TSLA PLTR NVDA \
  --method black_litterman \
  --days 252 \
  --risk-free-rate 0.05 \
  --market-cap-weights 0.4 0.3 0.3

# Constrained optimization
uv run python -m src.strategies.optimizer_cli TSLA PLTR NVDA \
  --method mean_variance \
  --days 252 \
  --min-weight 0.05 \
  --max-weight 0.50

# JSON for programmatic use
uv run python -m src.strategies.optimizer_cli TSLA PLTR NVDA \
  --method mean_variance \
  --days 252 \
  --output json
```

**Optimization Methods:**

**Mean-Variance (Markowitz)**
- Balances expected return vs portfolio variance
- Best for traditional diversified portfolios
- Moderate risk tolerance

**Risk Parity**
- Equal risk contribution from all assets
- Best for balanced, risk-conscious investors
- Works well in uncertain market regimes

**Minimum Variance**
- Minimizes portfolio volatility
- Best for conservative investors
- Capital preservation focus

**Maximum Sharpe**
- Maximizes risk-adjusted returns
- Best for performance-focused portfolios
- Can produce aggressive allocations

**Black-Litterman**
- Incorporates investor views with market equilibrium
- Best for tactical allocation
- Requires view confidence and market cap inputs

**Output Metrics:**
- Optimal Weights (allocation percentages)
- Expected Return
- Expected Volatility
- Sharpe Ratio
- Risk Contribution (per asset)

**Use Cases:**
- **Portfolio Construction**: Initial allocation design
- **Monthly Rebalancing**: Adjust weights based on current conditions
- **New Capital Deployment**: Optimal allocation of additional funds
- **Risk Budgeting**: Allocate capital by risk contribution
- **Tactical Allocation**: Express market views via Black-Litterman

---

## Best Practices

### Data Selection
- **Use 252-day period for risk metrics** (full trading year for statistical validity)
- **Use 90-day period for momentum and volatility** (captures trend without excessive noise)
- **Use 252-day period for correlation** (long-term relationship stability)
- **Use 252-day period for moving averages** (includes 200-day MA for Golden Cross/Death Cross)
- **Use 252-day period for optimization** (full cycle for expected returns and covariances)
- **Always include benchmark** (SPY for US equities) for Beta/Alpha context
- **Verify data currency** (date should be most recent market close)

### Analysis Standards
- **Never rely on single metric** - use comprehensive risk profile
- **Always check momentum confluence** - 3+ indicators agreeing = strong signal
- **Always assess volatility regime** - extreme volatility requires defensive positioning
- **Always run correlation for portfolios** - identify concentration risks early
- **Use Golden Cross (50/200 SMA) to confirm major trend changes** - high-confidence signal for long-term trends
- **Run portfolio optimization monthly for rebalancing decisions** - maintain optimal risk-return balance
- **Compare multiple optimization methods (Max Sharpe vs Risk Parity)** - different methods suit different market regimes
- **Always backtest strategies** - validate before deployment with real capital
- **Validate with benchmark** - relative performance matters
- **Document assumptions** - risk-free rate, confidence levels, timeframes
- **Save all analysis** - enable audit trail and reproducibility

### Tool Integration
- **Use JSON output** for integration with optimization models
- **Save results** with `--save-to analysis/[analysis-name]-{date}.json`
- **Chain analysis** - risk metrics inform position sizing, momentum informs timing, volatility adjusts both, correlation validates diversification, moving averages confirm trends, backtesting validates strategies, optimization determines allocation
- **Quality check outputs** - ensure results make intuitive sense

### Professional Standards
- **Institutional-quality metrics** - use established financial engineering formulas
- **Clear interpretations** - explain what metrics mean for decisions
- **Risk-conscious** - always highlight downside scenarios
- **Transparent assumptions** - document all analytical choices
- **Actionable recommendations** - connect analysis to specific decisions
- **Historical validation** - backtest strategies before recommending deployment
- **Optimal allocation** - use portfolio optimization for disciplined rebalancing

---

## Handoff to Strategy Advisor

When analysis is complete, provide Strategy Advisor with:

1. **Risk Profile Summary** - Key risk metrics and interpretation
2. **Momentum Assessment** - Current momentum state and confluence
3. **Volatility Assessment** - Regime classification and position sizing implications
4. **Correlation Analysis** - Diversification score and concentration risks
5. **Moving Average Analysis** - Trend direction, Golden Cross/Death Cross signals, MA confluence
6. **Backtest Results** (if applicable) - Historical strategy performance with DEPLOY/OPTIMIZE/REJECT recommendation
7. **Portfolio Optimization** (if applicable) - Optimal allocation with method comparison and rationale
8. **Recommendation** - Clear position on risk/reward, timing, sizing, diversification, and allocation
9. **Supporting Files** - Saved JSON outputs for detailed review
10. **Caveats** - Any data quality issues or analytical limitations

**Handoff Format:**
> "Completed quantitative analysis on [SECURITIES]. Risk profile shows [SHARPE/DD/VAR]. Momentum analysis indicates [CONFLUENCE/SIGNALS]. Volatility regime is [LOW/NORMAL/HIGH/EXTREME] suggesting [POSITION SIZING GUIDANCE]. Correlation analysis shows [DIVERSIFICATION SCORE] with [CONCENTRATION RISKS]. Moving average analysis shows [GOLDEN CROSS/DEATH CROSS/TREND DIRECTION] confirming [MOMENTUM ALIGNMENT]. [Backtest results show DEPLOY/OPTIMIZE/REJECT recommendation with Sharpe [X], Max DD [Y]%, Win Rate [Z]%.] [Portfolio optimization recommends [METHOD] with optimal weights: [ALLOCATIONS], expected Sharpe [X], expected volatility [Y]%.] Recommend [ACTION] based on [RATIONALE]. Analysis saved to analysis/. Key caveat: [LIMITATION]."

---

## Notes

- **Future Tools:** Options analytics, factor analysis, technical screener planned (see Build List)
- **Tool Architecture:** All tools follow 3-layer Pydantic pattern (models → calculator → CLI)
- **Quality Focus:** Type-safe validation prevents calculation errors

**Status:** Production workflow using validated tools
**Last Updated:** 2025-10-13
**Tools Used:** Risk Metrics Calculator, Momentum Indicators, Volatility Metrics, Correlation Analysis, Moving Average Toolkit, Strategy Backtesting, Portfolio Optimizer
