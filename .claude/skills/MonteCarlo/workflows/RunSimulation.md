# RunSimulation Workflow

Execute the Monte Carlo v3.0 simulation with auto-detected portfolio values.

## Prerequisites

- Latest Fidelity positions CSV in `notebooks/updates/Portfolio_Positions_*.csv`
- Python environment configured with `uv`

## Workflow Steps

### Step 1: Get Current Date

```bash
date +"%Y-%m-%d"
```

Store as `{simulation_date}` for output file naming.

### Step 2: Auto-Detect Portfolio Values

Read the latest Fidelity positions CSV from `notebooks/updates/`:

```bash
ls -t notebooks/updates/Portfolio_Positions_*.csv | head -1
```

Parse the CSV to extract current values for each layer:

**Layer 1 (Growth)** - Sum of:
- PLTR, TSLA, NVDA, AAPL, VOO, FNILX, SPMO, VXUS, FZILX, SOFI, COIN, MSTR

**Layer 2 (Income)** - Sum of:
- JEPI, JEPQ, QQQI, SPYI, QQQY, CLM, CRF, ECAT, BDJ, ETY, ETV, BST, UTG, YMAX, AMZY, MSTY

**Layer 3 (Hedge)** - Sum of:
- SQQQ

**GOOGL Position**:
- GOOGL

**Starting Margin**:
- Look for "Pending activity" row or calculate from margin market value

### Step 3: Update Simulation Starting Values

Edit `src/strategies/dividend_margin_monte_carlo.py` to update the starting values in `run_single_scenario()`:

```python
# Initialize portfolio components with ACTUAL {simulation_date} values
layer1_portfolio = {layer1_value}   # Layer 1: Growth portfolio
income_portfolio = {layer2_value}   # Layer 2: Current dividend portfolio value
googl_position = {googl_value}      # Starting GOOGL value
hedge_position = {hedge_value}      # Layer 3: Current SQQQ hedge value
margin_balance = {margin_value}     # Starting margin debt
```

### Step 4: Run Simulation

```bash
uv run python src/strategies/dividend_margin_monte_carlo.py
```

This produces:
- Console output with summary statistics
- `docs/fin-guru/analysis/monte-carlo-v3-{date}.json`
- `docs/fin-guru/analysis/monte-carlo-v3-full-results-{date}.csv`

### Step 5: Generate Excel Workbook

Update the paths in `scripts/simulations/monte_carlo_excel_export.py` if needed, then run:

```bash
uv run python scripts/simulations/monte_carlo_excel_export.py
```

This produces:
- `docs/fin-guru/analysis/monte-carlo-v3-analysis-{date}.xlsx`

### Step 6: Report Results

Present key metrics to the user:

**Success Metrics:**
- P($100k income): {probability_100k}
- P($75k income): {probability_75k}
- P($50k income): {probability_50k}
- Margin call rate: {margin_call_rate}

**Portfolio at Month 28 (Median):**
- Total value: ${median_total}
- Layer 1: ${median_layer1}
- Layer 2: ${median_layer2}
- Layer 3: ${median_hedge}
- GOOGL: ${median_googl}

**Income at Month 28:**
- Annual dividend: ${median_dividend}
- Range (P5-P95): ${p5_dividend} - ${p95_dividend}

**Margin Safety:**
- Median ratio: {median_ratio}:1
- Minimum ratio: {min_ratio}:1
- Backstop usage: {backstop_rate}%

## Output Files

- JSON summary: `docs/fin-guru/analysis/monte-carlo-v3-{simulation_date}.json`
- Full scenarios: `docs/fin-guru/analysis/monte-carlo-v3-full-results-{simulation_date}.csv`
- Excel analysis: `docs/fin-guru/analysis/monte-carlo-v3-analysis-{simulation_date}.xlsx`

## Layer Classification Reference

### Layer 1 (Growth) - Keep 100%, NO new deployment
| Ticker | Description |
|--------|-------------|
| PLTR | Palantir - Core growth |
| TSLA | Tesla - Core growth |
| NVDA | Nvidia - Core growth |
| AAPL | Apple - Core growth |
| VOO | S&P 500 ETF |
| FNILX | Zero-cost S&P 500 |
| SPMO | Momentum factor |
| VXUS | International |
| FZILX | Zero-cost international |
| SOFI | Fintech growth |
| COIN | Crypto proxy |
| MSTR | Bitcoin proxy |
| PARR | New growth position |

### Layer 2 (Income) - Build with W2, $11,517/month
| Bucket | Tickers | Allocation |
|--------|---------|------------|
| JPMorgan Income | JEPI, JEPQ | 27% |
| CEF Stable | CLM, CRF, ECAT | 20% |
| Covered Call ETFs | QQQI, SPYI, QQQY | 35% |
| YieldMax | YMAX, AMZY | 10% |
| DRIP v2 CEFs | BDJ, ETY, ETV, BST, UTG | 8% |

### Layer 3 (Hedge) - Build with W2, $800/month
| Ticker | Description |
|--------|-------------|
| SQQQ | 3x Inverse Nasdaq |

### GOOGL Scale-In - Diverted from Layer 2, $1,000/month
| Ticker | Description |
|--------|-------------|
| GOOGL | Alphabet - Top AI stock 2026 |
