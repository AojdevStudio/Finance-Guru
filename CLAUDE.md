<!-- SKILLS-INDEX-START -->
[Skills Index]|root: ./.claude/skills|IMPORTANT: Read full SKILL.md before using any skill. This index is for routing only.|backend-dev-guidelines:{name:backend-dev-guidelines,desc:Comprehensive backend development guide for Node.js/Express/TypeScript microservices.,files:{resources:{architecture-overview.md,async-and-errors.md,complete-examples.md,configuration.md,database-patterns.md,middleware-guide.md,routing-and-controllers.md,sentry-and-monitoring.md,services-and-repositories.md,testing-guide.md,validation-patterns.md}}}|dividend-tracking:{name:dividend-tracking,desc:Sync dividend data from Fidelity CSV to Dividends sheet.,files:{}}|error-tracking:{name:error-tracking,desc:Add Sentry v8 error tracking and performance monitoring to your project services.,files:{}}|fin-core:{name:fin-core,desc:| Finance Guru™ Core Context Loader Auto-loads essential Finance Guru system configuration and user profile at session s,files:{README.md}}|FinanceReport:{name:FinanceReport,desc:Generate institutional-quality PDF analysis reports for stocks and ETFs.,files:{StyleGuide.md,VisGuide.md,tools:{ChartKit.help.md,ChartKit.py,ReportGenerator.help.md,ReportGenerator.py},workflows:{FullResearchWorkflow.md,GenerateSingleReport.md,RegenerateBatch.md}}}|formula-protection:{name:formula-protection,desc:Prevent accidental modification of sacred spreadsheet formulas in Google Sheets Portfolio Tracker.,files:{}}|margin-management:{name:margin-management,desc:Update Margin Dashboard with Fidelity balance data and calculate margin-living strategy metrics.,files:{}}|MonteCarlo:{name:MonteCarlo,desc:Run Monte Carlo simulations for Finance Guru portfolio strategy.,files:{PortfolioParser.md,tools:{.gitkeep},workflows:{IncorporateBuyTicket.md,RunSimulation.md}}}|PortfolioSyncing:{name:PortfolioSyncing,desc:Import and sync broker CSV portfolio data to Google Sheets DataHub.,files:{workflows:{SyncPortfolio.md}}}|python-performance-optimization:{name:python-performance-optimization,desc:Profile and optimize Python code using cProfile, memory profilers, and performance best practices.,files:{}}|readiness-report:{name:readiness-report,desc:Evaluate how well a codebase supports autonomous AI development.,files:{references:{criteria.md,maturity-levels.md},scripts:{analyze_repo.py,generate_report.py}}}|retirement-syncing:{name:retirement-syncing,desc:Sync retirement account data from Vanguard and Fidelity CSV exports to Google Sheets DataHub.,files:{}}|route-tester:{name:route-tester,desc:Test authenticated routes in the your project using cookie-based authentication.,files:{}}|TransactionSyncing:{name:TransactionSyncing,desc:Import Fidelity transaction history CSV into Google Sheets with smart categorization.,files:{CategoryRules.md,workflows:{SyncTransactions.md}}}|[14 skills, 32 files]
<!-- SKILLS-INDEX-END -->

<!-- COMPRESSION-START -->
Finance Guru™ - Private AI family office on BMAD-CORE™ v6.
*Claude Code only*: ALWAYS use `AskUserQuestion` tool for user questions.
**Key**: This IS Finance Guru (not product) - personal financial command center. Use "your" for assets/strategies/portfolios.

[Architecture]
Multi-Agent System: Claude→specialized financial agents;Entry Point: Finance Orchestrator (Cassandra Holt) - `.claude/commands/fin-guru/agents/finance-orchestrator.md`;Path Variables: `{project-root}`,`{module-path}`,`{current_datetime}`,`{current_date}`,`{user_name}`;MCP Servers Required: exa,bright-data,sequential-thinking,financial-datasets,gdrive,web-search;Apps: `apps/plaid-dashboard/` (Bun/TS monorepo - dashboard+engine+db, uses turbo.json);Temporal Awareness: ALL agents MUST run `date` and `date +"%Y-%m-%d"` at startup;Compliance: ALL outputs include educational-only disclaimer,"not investment advice",consult professionals,risk disclosure

[Technology Stack]
Python: 3.12+|Package Manager: `uv`;Dependencies: pandas,numpy,scipy,scikit-learn,yfinance,streamlit,beautifulsoup4,requests,pydantic,python-dotenv;Architecture: 3-layer (Pydantic Models→Calculator Classes→CLI);Docs: `notebooks/tools-needed/type-safety-strategy.md`,`.claude/tools/python-tools.md`

[CLI Command Patterns]
Base: `uv run python <script> <ticker(s)> [flags]`;Common Flags: `--days N` (90=quarter,252=year),`--output json`,`--benchmark SPY`;Example Tickers: TSLA,PLTR,NVDA,SPY;Portfolio Loop: `for ticker in TSLA PLTR NVDA; do uv run python <tool> $ticker [flags]; done`;Package Management: `uv sync` (install),`uv add/remove <pkg>` (manage);Market Data: `uv run python src/utils/market_data.py TSLA [PLTR AAPL ...]`;Tests: `uv run pytest` (unit),`uv run pytest -m "not integration"` (skip API tests);Lint: `uv run black .` (format),`uv run mypy src/` (type check);Justfile: `just --list` (see all recipes),`just load-diagrams` (load mermaid context)

[Financial Analysis Tools]
Risk Metrics|src/analysis/risk_metrics_cli.py|VaR,CVaR,Sharpe,Sortino,Max DD,Calmar,Volatility,Beta,Alpha|--benchmark SPY,--save-to <path>|fin-guru-private/guides/risk-metrics-tool-guide.md;Momentum|src/utils/momentum_cli.py|RSI,MACD,Stochastic,Williams %R,ROC,Confluence|--indicator <type>,--rsi-period,--macd-*|-;Volatility|src/utils/volatility_cli.py|Bollinger Bands,ATR,Historical Vol,Keltner,StdDev,Regime|--atr-period,--bb-period,--bb-std|-;Correlation|src/analysis/correlation_cli.py|Pearson matrix,Covariance,Diversification,Concentration|--rolling <N> (requires 2+ tickers)|-;Backtesting|src/strategies/backtester_cli.py|RSI,SMA cross,Buy-hold,Sharpe,Win rate,Drawdown|--strategy <type>,--capital,--commission,--slippage|-;Moving Averages|src/utils/moving_averages_cli.py|SMA,EMA,WMA,HMA,Golden/Death Cross|--ma-type <type>,--period,--fast,--slow|-;Portfolio Optimizer|src/strategies/optimizer_cli.py|Max Sharpe,Risk Parity,Min Variance,Mean-Var,Black-Litterman|--method <type>,--max-position,--view <ticker:return>|-;ITC Risk|src/analysis/itc_risk_cli.py|ITC Risk Score,Risk Bands,High Risk Threshold,Price Context|--universe <crypto\|tradfi>,--full-table,--list-supported|-

[Agent-Tool Matrix]
Market Researcher|Momentum,Moving Averages,Risk Metrics,ITC Risk|Quick scans,trend identification,initial risk assessment,ITC risk level checks;Quant Analyst|All tools,ITC Risk|Deep analysis,custom parameters,optimization,factor analysis,ITC risk bands;Strategy Advisor|Optimizer,Backtesting,Correlation,ITC Risk|Portfolio construction,rebalancing,validation,diversification,risk zone analysis;Compliance Officer|Volatility,Risk Metrics,Backtesting|Position limits,risk profiles,strategy approval;Margin Specialist|Volatility|Leverage assessment,ATR-based position sizing

[Output & Validation]
Document Output: `fin-guru-private/fin-guru/analysis/`;Format: Markdown+YAML frontmatter;Required: Date stamp,disclaimer,citations;Naming Conventions: Analysis reports:`{topic}-{YYYY-MM-DD}.md`;Buy tickets:`buy-ticket-{YYYY-MM-DD}-{short-descriptor}.md` (max 2-3 words,e.g.,"hybrid-drip-v2");Strategy docs:`{strategy-name}-master-strategy.md` (no dates);Monthly reports:`monthly-refresh-{YYYY-MM-DD}.md`;Validation Checklist: Agent activation,workflow execution,document generation,compliance disclaimers,market data retrieval

[Version Info]
Finance Guru™: v2.0.0|BMAD-CORE™: v6.0.0|Build: 2025-10-08|Updated: 2026-01-09|Tools: 8/11 complete

Note: Private family office system - maintain exclusive,personalized nature of Finance Guru service.

[Style]
Markdown emphasis: underscores (`_text_`), not asterisks (`*text*`) — enforced by markdownlint (MD049)

[Bash Patterns (setup.sh)]
`set -e` active: guard `eval` with `if !` to capture failures; never eval multiline or non-command strings
`command -v` for existence checks (not `which`); use sentinel `"0.0"` for version fallback under set -e
Auto-install: `get_install_command()` returns both executable and instructional strings — guard before eval

[PR Review Workflow]
CodeRabbit + Claude bot review PRs automatically; fetch comments via `gh api repos/{owner}/{repo}/pulls/{n}/comments`
Address all comments before merge; check which are already resolved in latest commit before fixing

[Landing the Plane (Session Completion)]
When ending work session,MUST complete ALL steps. Work NOT complete until `git push` succeeds.
MANDATORY WORKFLOW: 1.File issues for remaining work - Create github issues for follow-up;2.Run quality gates (if code changed) - `uv run pytest`,`uv run black --check .`,`uv run mypy src/`;3.Update issue status - Close finished,update in-progress;4.PUSH TO REMOTE - MANDATORY: `git pull --rebase;git push;git status` (MUST show "up to date with origin");5.Clean up - Clear stashes,prune remote branches;6.Verify - All changes committed AND pushed;7.Hand off - Provide context for next session
CRITICAL RULES: Work NOT complete until `git push` succeeds;NEVER stop before pushing - leaves work stranded locally;NEVER say "ready to push when you are" - YOU must push;If push fails,resolve and retry until succeeds
<!-- COMPRESSION-END -->
