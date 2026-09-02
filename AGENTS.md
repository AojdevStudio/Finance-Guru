

[Skills Index] Skills live in `./.claude/skills`. The single source of truth for the index is `CLAUDE.md`; read it there rather than maintaining a second copy here, which is how this file drifted out of date. Read a skill's full SKILL.md before using it.

[Codex Instance Skill Discovery] A scaffolded instance contains `.agents` and `.claude` symlinks to the engine's single `.claude` tree. When Codex starts from an instance directory, discover skills under `./.agents/skills`, consult the index in the engine's `CLAUDE.md`, and read the selected `SKILL.md` in full. Never copy skill content into the instance or maintain a second harness-specific skill tree.

[System of Record] `family_office.db` (SQLite, gitignored) holds positions, balances, transactions, and bank_transactions, fed by SnapTrade (brokerage) and SimpleFIN (bank/card). The Google Sheets DataHub is retired: do not write to Sheets and do not reintroduce a gdrive MCP dependency.

## What this repository is

Finance Guru is a self-hosted family office engine: typed Python calculators, a private SQLite ledger, and specialist agents that run inside Claude Code or Codex. It is the open-core engine behind Keepfolio. The README describes the product. This file tells a coding agent how to work in it.

## Operating rules

- Read `CLAUDE.md` first. It is the single source of truth for the skills index, the agent roster, the path variables, and the output rules.
- Run `date` and `date +"%Y-%m-%d"` before any market work. Store the results as `{current_datetime}` and `{current_date}`. Agent configuration files also use `{project-root}`, `{module-path}`, `{data-root}`, and `{user_name}`. Resolve every variable to a real path or value before use.
- Never do the arithmetic yourself. Call the CLI with `--output json` and quote what it returned.
- Private data lives in the instance, not the repo. Resolve `FIN_GURU_DATA_ROOT` or the working directory, read from `family_office.db`, and write artifacts into `analysis/` or `tickets/`. Tracked files never carry personal values. The pre-push compliance scan blocks a push that does.
- Every financial output carries the educational-only disclaimer, a "not investment advice" statement, a recommendation to consult licensed professionals, a risk disclosure, a date stamp, and its data source. The CLIs print the disclaimer. The skills expect it.
- Fail closed. If a guardrail input is missing, the answer is a block with a typed reason. Do not fill the gap with an estimate.
- Contributing a tool means all three layers: Pydantic input model, calculator class, CLI wrapper, plus a test that runs without a network.
- Research skills may call the MCP servers listed in `CLAUDE.md`. None of them are required to run the calculators or the sync.

## Layout

- `src/analysis/`, `src/utils/`, and `src/strategies/` hold 20 calculators. Each is a Pydantic model, a calculator class, and a `*_cli.py` wrapper. The full list is in `docs/reference/api.md`.
- `src/integrations/` holds the sync layer. `refresh_all` pulls SnapTrade and SimpleFIN into `family_office.db`. Partial provider responses raise before any write.
- `.claude/skills/` holds the workflows. `.claude/commands/fin-guru/agents/` holds the 11 specialist personas. The finance orchestrator in that directory routes between them.
- `tests/` holds the math, tested without a network, behind an 80% coverage gate. `uv run pytest -m "not integration"` skips the tests that need real API keys.
- `apps/simplefin-sync/` is the Bun workspace for the SimpleFIN broker sync.

## Toolchain

Python 3.12 or later, managed with `uv`. Bun for `apps/simplefin-sync/`. These gates mirror CI:

```bash
uv sync --dev
uv run ruff format --check .
uv run ruff check .
uv run mypy src/
uv run pytest -m "not integration"
```

## Development Commands

### Package Management

```bash
# Install all dependencies
uv sync

# Add new dependency
uv add <package-name>

# Remove dependency
uv remove <package-name>

# Run Python scripts
uv run python <script-path>
```

### Real-Time Market Data

```bash
# Get current stock price (single)
uv run python -m src.utils.market_data TSLA

# Get multiple stock prices
uv run python -m src.utils.market_data TSLA PLTR AAPL
```

### Risk Metrics Analysis

```bash
# Market Researcher - Quick risk scan
uv run python -m src.analysis.risk_metrics_cli TSLA --days 90

# Quant Analyst - Full analysis with benchmark
uv run python -m src.analysis.risk_metrics_cli TSLA --days 252 --benchmark SPY --output json

# Strategy Advisor - Portfolio comparison
for ticker in TSLA PLTR NVDA; do
    uv run python -m src.analysis.risk_metrics_cli $ticker --days 252 --benchmark SPY
done

# Save to file for report generation
uv run python -m src.analysis.risk_metrics_cli TSLA --days 90 \
    --output json \
    --save-to analysis/risk-analysis-tsla-$(date +%Y-%m-%d).json
```

**Available Metrics**: VaR (95%), CVaR, Sharpe Ratio, Sortino Ratio, Max Drawdown, Calmar Ratio, Annual Volatility, Beta, Alpha

**Documentation**: `guides/risk-metrics-tool-guide.md`

### Momentum Indicators

```bash
# Market Researcher - Quick momentum scan (all indicators)
uv run python -m src.utils.momentum_cli TSLA --days 90

# Quant Analyst - Specific indicator with custom periods
uv run python -m src.utils.momentum_cli TSLA --days 90 --indicator rsi --rsi-period 21

# Strategy Advisor - Portfolio momentum comparison
for ticker in TSLA PLTR NVDA; do
    uv run python -m src.utils.momentum_cli $ticker --days 90
done

# JSON output for programmatic analysis
uv run python -m src.utils.momentum_cli TSLA --days 90 --output json

# Custom MACD settings for different timeframes
uv run python -m src.utils.momentum_cli TSLA --days 252 \
    --macd-fast 8 \
    --macd-slow 21 \
    --macd-signal 9
```

**Available Indicators**: RSI, MACD, Stochastic Oscillator, Williams %R, ROC (Rate of Change)

**Features**: Confluence analysis (counts bullish/bearish signals across all indicators)

### Volatility Metrics

```bash
# Market Researcher - Quick volatility scan (all indicators)
uv run python -m src.utils.volatility_cli TSLA --days 90

# Compliance Officer - Position limit calculation
uv run python -m src.utils.volatility_cli TSLA --days 90 --output json

# Margin Specialist - Leverage assessment with custom ATR
uv run python -m src.utils.volatility_cli TSLA --days 90 --atr-period 20

# Strategy Advisor - Portfolio volatility comparison
for ticker in TSLA PLTR NVDA; do
    uv run python -m src.utils.volatility_cli $ticker --days 90
done

# Custom Bollinger Bands settings
uv run python -m src.utils.volatility_cli TSLA --days 90 \
    --bb-period 14 \
    --bb-std 2.5
```

**Available Indicators**: Bollinger Bands, ATR (Average True Range), Historical Volatility, Keltner Channels, Standard Deviation

**Features**: Volatility regime assessment (low/normal/high/extreme), position sizing guidance, stop-loss calculation

**Agent Use Cases**:

- Compliance Officer: Calculate position limits based on volatility regime
- Margin Specialist: Determine safe leverage ratios using ATR%
- Risk Assessment: Portfolio volatility tracking and regime monitoring

### Correlation & Covariance Analysis

```bash
# Basic portfolio correlation (2+ tickers required)
uv run python -m src.analysis.correlation_cli TSLA PLTR NVDA --days 90

# Pairwise correlation check
uv run python -m src.analysis.correlation_cli TSLA SPY --days 90

# Rolling correlation (time-varying)
uv run python -m src.analysis.correlation_cli TSLA SPY --days 252 --rolling 60

# JSON output for programmatic use
uv run python -m src.analysis.correlation_cli TSLA PLTR NVDA --days 90 --output json
```

**Available Analysis**: Pearson correlation matrices, covariance matrices, rolling correlations, diversification scoring, concentration risk detection

**Agent Use Cases**:

- Strategy Advisor: Portfolio diversification assessment, rebalancing signals
- Quant Analyst: Correlation matrices for portfolio optimization, factor analysis
- Risk Assessment: Concentration risk monitoring, correlation regime shifts

### Strategy Backtesting

```bash
# Test RSI strategy
uv run python -m src.strategies.backtester_cli TSLA --days 252 --strategy rsi

# Test with custom capital and costs
uv run python -m src.strategies.backtester_cli TSLA --days 252 --strategy rsi \
    --capital 500000 --commission 5.0 --slippage 0.001

# Test SMA crossover strategy
uv run python -m src.strategies.backtester_cli TSLA --days 252 --strategy sma_cross

# Buy-and-hold benchmark
uv run python -m src.strategies.backtester_cli TSLA --days 252 --strategy buy_hold

# JSON output
uv run python -m src.strategies.backtester_cli TSLA --days 252 --strategy rsi --output json
```

**Built-in Strategies**: RSI mean reversion, SMA crossover, buy-and-hold benchmark

**Features**: Transaction cost modeling (commissions + slippage), performance metrics (Sharpe, max drawdown, win rate), trade log generation, deployment recommendations

**Agent Use Cases**:

- Strategy Advisor: Validate investment hypotheses before deployment
- Quant Analyst: Test quantitative models, optimize parameters
- Compliance Officer: Assess strategy risk profile before approval

### Moving Average Analysis

```bash
# Single MA calculation (SMA, EMA, WMA, HMA)
uv run python -m src.utils.moving_averages_cli TSLA --days 200 --ma-type SMA --period 50

# Golden Cross detection (50/200 SMA - classic trend signal)
uv run python -m src.utils.moving_averages_cli TSLA --days 252 --fast 50 --slow 200

# EMA crossover (12/26 for MACD-style signals)
uv run python -m src.utils.moving_averages_cli TSLA --days 252 --ma-type EMA --fast 12 --slow 26

# Hull MA (minimal lag, responsive)
uv run python -m src.utils.moving_averages_cli TSLA --days 200 --ma-type HMA --period 50

# JSON output
uv run python -m src.utils.moving_averages_cli TSLA --days 200 --ma-type SMA --period 50 --output json
```

**Available MA Types**: SMA (simple), EMA (exponential), WMA (weighted), HMA (Hull - advanced)

**Features**: Golden Cross/Death Cross detection, trend analysis, crossover date tracking

**Agent Use Cases**:

- Market Researcher: Quick trend identification with standard MAs
- Quant Analyst: Test multiple MA types for strategy optimization
- Strategy Advisor: Monitor 50/200 Golden Cross for major trend signals

### Portfolio Optimization

```bash
# Maximum Sharpe ratio (aggressive growth)
uv run python -m src.strategies.optimizer_cli TSLA PLTR NVDA SPY --days 252 --method max_sharpe

# Risk parity allocation (all-weather portfolio)
uv run python -m src.strategies.optimizer_cli TSLA PLTR NVDA SPY --days 252 --method risk_parity

# Minimum variance (defensive, capital preservation)
uv run python -m src.strategies.optimizer_cli TSLA PLTR NVDA SPY --days 252 --method min_variance

# Mean-variance optimization
uv run python -m src.strategies.optimizer_cli TSLA PLTR NVDA SPY --days 252 --method mean_variance

# Black-Litterman with views
uv run python -m src.strategies.optimizer_cli TSLA PLTR NVDA --days 252 --method black_litterman \
    --view TSLA:0.15 --view PLTR:0.20

# With position limits (max 30% per stock)
uv run python -m src.strategies.optimizer_cli TSLA PLTR NVDA SPY --days 252 --method max_sharpe \
    --max-position 0.30

# JSON output
uv run python -m src.strategies.optimizer_cli TSLA PLTR NVDA SPY --days 252 --method max_sharpe --output json
```

**Optimization Methods**: Mean-Variance (Markowitz), Risk Parity, Min Variance, Max Sharpe, Black-Litterman

**Features**: Position limit controls, capital allocation guidance ($500k portfolio), efficient frontier generation, diversification scoring

**Agent Use Cases**:

- Strategy Advisor: Monthly portfolio rebalancing and new capital deployment ($5-10k)
- Quant Analyst: Portfolio construction with risk-return optimization
- Compliance Officer: Ensure position limits and concentration risk controls

## Document Output

Generated Finance Guru documents use split destinations:

- Analysis artifacts: `analysis/`
- Buy tickets: `tickets/`
- Format: Markdown with YAML frontmatter
- Naming: `{topic}-{strategy/analysis}-{YYYY-MM-DD}.md` (analysis), `buy-ticket-{YYYY-MM-DD}-{descriptor}.md` (tickets)
- Include: Date stamp, disclaimer, source citations

## Landing the Plane (Session Completion)

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:

   ```bash
   git pull --rebase
   git push
   git status  # MUST show "up to date with origin"
   ```

5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**

- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds

Use GitHub Issues or repo docs for follow-up tracking

## Cursor Cloud specific instructions

Durable, non-obvious notes for cloud agents. The startup update script already runs
`uv sync --dev` and `bun install`, so dependencies are ready — do not re-install them.

- **Toolchain paths**: `uv` lives at `~/.local/bin/uv` and `bun` at `~/.bun/bin/bun`. These
  are on `PATH` for interactive shells (added to `~/.bashrc`) but NOT for fresh
  non-interactive shells. If a command reports `uv: command not found`, run
  `export PATH="$HOME/.local/bin:$HOME/.bun/bin:$PATH"` first (or call the binaries by full path).
- **This is a CLI-first product — there is no long-running server to start.** The "app" is a
  set of Python analysis CLIs plus a Textual TUI. Run analysis with
  `uv run python -m src.analysis.risk_metrics_cli AAPL --days 252 --benchmark SPY` (fetches live
  data via yfinance — needs network, no API key). Launch the interactive dashboard with
  `uv run python -m src.cli.fin_guru` (quit with `q`). Full commands are documented above and in `docs/setup/SETUP.md`.
- **Do NOT keep a scaffolded `.env` around when running tests.** `setup.sh` copies
  `.env.example` → `.env`, which contains literal placeholder values (e.g.
  `FG_DIVIDEND_MONTHLY_INCOME=your_monthly_dividend_income_here`). `python-dotenv` loads `.env`,
  and those non-numeric placeholders make `src/analysis/margin_metrics.py` (and its tests) fail
  with `could not convert string to float: 'your_..._here'`. CI runs without a `.env`, so tests
  assume it is absent. If margin tests fail with that error, delete `.env` (it is gitignored) or
  replace the placeholders with real numbers.
- **Test suite runs in parallel with a coverage gate.** `pyproject.toml` sets
  `addopts` to use `-n auto` (pytest-xdist), `--reruns 1`, and `--cov-fail-under=80`. Just run
  `uv run pytest`. Use `uv run pytest -m "not integration"` to skip the 3 integration tests that
  need real API keys. Quality gates: `uv run ruff check .`, `uv run ruff format --check .`,
  `uv run mypy src/`.
