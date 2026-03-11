<div align="center">

# 🏦 Finance Guru Desktop

**Stop running Python CLIs at 6am. Click a button.**

*The private family office command center — institutional-grade analysis, native desktop speed.*

![Version](https://img.shields.io/badge/version-0.1.0-22c55e?style=flat-square)
![Tests](https://img.shields.io/badge/tests-56%20passing-22c55e?style=flat-square)
![Built with](https://img.shields.io/badge/built%20with-Electron%20%2B%20Bun-3b82f6?style=flat-square)
![License](https://img.shields.io/badge/license-AGPL--3.0-f59e0b?style=flat-square)

</div>

---

## The Problem

You built one of the most capable personal finance engines in existence. Nine quantitative analysis tools. Risk metrics, correlation matrices, options chains, Monte Carlo simulations, backtesting frameworks. All of it production-grade, all of it running locally.

And every morning you open a terminal and type:

```bash
uv run python src/analysis/risk_metrics_cli.py TSLA --days 252 --output json
```

That's not a workflow. That's punishment.

---

## The Insight

> **The engine was always powerful enough. The interface just hadn't caught up.**

Finance Guru Desktop wraps the entire family-office Python engine in a native Electron GUI — no browser tabs, no Streamlit reloads, no terminal archaeology. The analysis tools you built are one click away.

---

## What It Does

```
┌───────────────────────────────────────────────────────┐
│                Finance Guru Desktop                   │
│                                                       │
│  ┌────────────────┐        ┌────────────────────────┐ │
│  │   Sidebar      │        │    Analysis Panel      │ │
│  │                │        │                        │ │
│  │  📈 Total Return│──────►│  Plotly dark charts    │ │
│  │  📉 Risk Metrics│        │  Animated risk gauges  │ │
│  │  🔗 Correlation │        │  Data tables           │ │
│  │  📊 Options     │        │  Compliance notes      │ │
│  │                │        └────────────────────────┘ │
│  │  ── Skills ──  │                                   │
│  │  Quant Analysis│        ┌────────────────────────┐ │
│  │  Strategize    │──────►│      Chat Panel        │ │
│  │                │        │  Claude + Skills +     │ │
│  │  ── Agents ──  │        │  Agent streaming       │ │
│  │  Orchestrator  │        └────────────────────────┘ │
│  └────────────────┘                                   │
└──────────────────────────────┬────────────────────────┘
                               │ spawn()
                               ▼
          ┌────────────────────────────────────┐
          │      Family Office Engine          │
          │                                    │
          │  .venv/bin/python3                 │
          │  src/analysis/risk_metrics_cli.py  │
          │  src/analysis/correlation_cli.py   │
          │  src/analysis/total_return_cli.py  │
          │  src/analysis/options_chain_cli.py │
          └────────────────────────────────────┘
```

---

## ⚡ Run It — Right Now

### Prerequisites

Make sure the family-office engine is set up (it almost certainly is):

```bash
# From the family-office root (one level up from this project)
ls .venv/bin/python3    # Should exist
uv run python src/analysis/risk_metrics_cli.py AAPL --help  # Should respond
```

### First Time Setup

```bash
cd finance-guru-desktop
bun install
```

That's it. One command. No Python packages to configure — it uses the existing `.venv`.

### Launch

```bash
bun run start          # Build renderer + open app
```

### Development Mode (with DevTools)

```bash
bun run start:dev      # Opens Chromium DevTools automatically
```

---

## The V1 Command Set

| Tool | Input | Output | What it shows |
|------|-------|--------|---------------|
| **📈 Total Return** | Tickers, days | Bar chart + table | Price return, dividend return, DRIP return |
| **📉 Risk Metrics** | Ticker, days, benchmark | Animated gauges | Sharpe, VaR 95/99, drawdown, volatility, beta, alpha |
| **🔗 Correlation** | 2+ tickers, days | Heatmap | Cross-correlation matrix |
| **📊 Options Chain** | Ticker, expiry, type | Data table | Strikes, OI, IV, Greeks |

Click a tool → fill the modal form → watch the chart appear. No terminal required.

---

## Chat & Agents

The **Chat** tab connects to Claude via the Agent SDK with streaming output. Skills and Specialist agents from the command palette route here automatically.

**Auth check on startup:** If `ANTHROPIC_API_KEY` isn't set and `~/.claude/` credentials aren't found, the app shows a clear setup warning. Analysis tools remain usable — only chat is gated.

---

## Architecture

```
main.js                    # Electron bootstrap, single instance lock, PATH fix
preload.js                 # Narrow IPC bridge (app / analysis / csv / chat)
renderer.js                # Entry point → bundled by esbuild → dist/renderer.bundle.js
│
├── src/main/
│   ├── config/
│   │   ├── runtimePaths.js      # Single source of truth for all path assumptions
│   │   └── validateRuntime.js   # Startup health check (Python, src/, Claude auth)
│   └── ipc/
│       ├── analysis.ipc.js      # Spawns Python CLIs, allowlist-only, 60s timeout
│       ├── csv.ipc.js           # File dialog + path-restricted CSV reader
│       ├── chat.ipc.js          # Agent SDK sessions, message queue, streaming
│       └── dialog.ipc.js        # Native file dialogs
│
└── src/renderer/
    ├── commands/registry.js     # V1 command definitions + ALLOWED_ANALYSIS_COMMANDS
    ├── state/portfolio.state.js # Observable portfolio state
    └── ui/
        ├── CommandPalette.js    # Sidebar buttons
        ├── ChatView.js          # Streaming chat with markdown + tool call display
        ├── Modal.js             # Dynamic arg forms from command definitions
        └── renderers/           # Plotly charts, animated gauges, data tables
```

---

## Other Commands

```bash
bun run watch          # Auto-rebuild renderer on every save (use with bunx electron .)
bun run build:renderer # One-off renderer build (dist/renderer.bundle.js)
bun test               # 56 tests across 6 suites
bun test --watch       # Watch mode
```

---

## Security Model

- **Analysis commands**: Allowlisted in `ALLOWED_ANALYSIS_COMMANDS` — no arbitrary process execution
- **CSV reads**: Restricted to `fin-guru-private/fin-guru/analysis/` and `notebooks/updates/`
- **IPC bridge**: Preload exposes named methods only — no `ipcRenderer.send` escape hatch
- **Python args**: Passed as array to `spawn()` — shell injection is structurally impossible

---

## The Story

This was built in a single session from a 19-task plan. The goal was simple: the Python analysis engine deserved a real interface, not a terminal shortcut.

Every tool maps 1:1 to a CLI you already trust. The desktop app adds nothing artificial — it's a secure, tested wrapper that turns `uv run python src/analysis/risk_metrics_cli.py TSLA --days 252 --output json` into a button click and a chart.

Your family office. Your data. Runs completely local.

---

<div align="center">

*Built for the Irondi household. Not a product — a command center.*

</div>
