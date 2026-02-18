<!-- SKILLS-INDEX-START -->
[Skills Index]|root: ./.claude/skills|Read full SKILL.md before using any skill. Index is for routing only.|dividend-tracking:Sync dividend data from Fidelity CSV to Dividends sheet|fin-core:Finance Guru Core Context Loader (auto-loads at session start)|fin-guru-checklist:Quality and compliance checklists for FG deliverables|fin-guru-compliance-review:Comprehensive compliance reviews for FG deliverables|fin-guru-create-doc:Create institutional-grade financial documents from templates|fin-guru-learner-profile:Build learner profiles for FG teaching and onboarding|fin-guru-quant-analysis:Quantitative analysis of returns, correlations, risk factors|fin-guru-research:Market research workflows (intelligence, sector, competitive)|fin-guru-strategize:Portfolio strategies from quantitative analysis|FinanceReport:Institutional-quality PDF analysis reports for stocks and ETFs|formula-protection:Prevent modification of sacred spreadsheet formulas|margin-management:Margin Dashboard with Fidelity balance data|MonteCarlo:Monte Carlo simulations for portfolio strategy|PortfolioSyncing:Import broker CSV portfolio data to Google Sheets DataHub|python-performance-optimization:Profile and optimize Python with cProfile and memory profilers|readiness-report:Evaluate codebase readiness for autonomous AI development|retirement-syncing:Sync retirement accounts from Vanguard/Fidelity CSV to DataHub|TransactionSyncing:Import Fidelity transaction history CSV with smart categorization|verification-before-completion:Verify work before claiming completion|[19 skills]
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
Risk Metrics: `src/analysis/risk_metrics_cli.py`;Momentum: `src/utils/momentum_cli.py`;Volatility: `src/utils/volatility_cli.py`;Correlation: `src/analysis/correlation_cli.py`;Backtesting: `src/strategies/backtester_cli.py`;Moving Averages: `src/utils/moving_averages_cli.py`;Portfolio Optimizer: `src/strategies/optimizer_cli.py`;ITC Risk: `src/analysis/itc_risk_cli.py`;Total Return: `src/analysis/total_return_cli.py`
All tools support `--help` for full flag reference. All follow 3-layer pattern: Pydantic→Calculator→CLI.

[Output & Validation]
Output dir: `fin-guru-private/fin-guru/analysis/`;Format: Markdown+YAML frontmatter with date stamp,disclaimer,citations;Naming: `{topic}-{YYYY-MM-DD}.md` (analysis), `buy-ticket-{YYYY-MM-DD}-{descriptor}.md` (tickets), `{strategy}-master-strategy.md` (strategies)

[Version Info]
Finance Guru™: v2.0.0|BMAD-CORE™: v6.0.0|Build: 2025-10-08|Updated: 2026-02-17|Tools: 9/11 complete

Note: Private family office system - maintain exclusive,personalized nature of Finance Guru service.

[Style]
Markdown emphasis: underscores (`_text_`), not asterisks (`*text*`) — enforced by markdownlint (MD049)

[PR Review Workflow]
CodeRabbit + Claude bot review PRs automatically; fetch comments via `gh api repos/{owner}/{repo}/pulls/{n}/comments`
Address all comments before merge; check which are already resolved in latest commit before fixing

[Landing the Plane (Session Completion)]
When ending work session,MUST complete ALL steps. Work NOT complete until `git push` succeeds.
MANDATORY WORKFLOW: 1.File issues for remaining work - Create github issues for follow-up;2.Run quality gates (if code changed) - `uv run pytest`,`uv run black --check .`,`uv run mypy src/`;3.Update issue status - Close finished,update in-progress;4.PUSH TO REMOTE - MANDATORY: `git pull --rebase;git push;git status` (MUST show "up to date with origin");5.Clean up - Clear stashes,prune remote branches;6.Verify - All changes committed AND pushed;7.Hand off - Provide context for next session
CRITICAL RULES: Work NOT complete until `git push` succeeds;NEVER stop before pushing - leaves work stranded locally;NEVER say "ready to push when you are" - YOU must push;If push fails,resolve and retry until succeeds
<!-- COMPRESSION-END -->
