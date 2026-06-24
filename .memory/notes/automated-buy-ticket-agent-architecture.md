---
title: Automated Buy-Ticket Agent — Architecture Notes
author: Elena Rodriguez-Park (Strategy Advisor)
date: 2026-04-19
status: Architecture draft — not yet implemented
tags: [automation, agentic, buy-ticket, fidelity, ibkr, simplefin]
---

# Automated Buy-Ticket Agent — Architecture

Codifying the manual buy-ticket workflow into a pay-date-triggered agentic system that generates (and optionally executes) tickets without human prompting.

---

## The Architecture (6 Layers)

```
┌─────────────────────────────────────────────────┐
│ LAYER 6: EXECUTION  →  Broker API               │
│ LAYER 5: APPROVAL   →  Human-in-loop gate       │
│ LAYER 4: TICKET GEN →  LLM + template fill      │
│ LAYER 3: ANALYSIS   →  Existing CLIs            │
│ LAYER 2: DATA PULL  →  SimpleFIN / broker feed  │
│ LAYER 1: TRIGGER    →  Pay-date detector (cron) │
└─────────────────────────────────────────────────┘
```

---

## Layer 1 — Trigger

Two options:

- **Calendar cron** — `0 9 15,30 * *` (15th + last day). Brittle: multi-employer pay dates don't align.
- **Event-driven (recommended)** — SimpleFIN polls Fidelity every 4h. When `deposit > $3000` hits, fire the pipeline. Matches actual income rhythm. SimpleFIN already scoped at $15/yr.

---

## Layer 2 — Data Pull

Current state: manual Fidelity CSV download → `notebooks/updates/`.

To automate:

- **SimpleFIN Bridge** → balances + transactions. Works today. Lives in `apps/simplefin-sync`.
- **Positions CSV** → still manual. Fidelity blocks programmatic positions export for retail.
  - **Workaround:** Playwright-automate Fidelity login and CSV download on a home box. Fragile, TOS-gray.
  - **Better:** Maintain positions state in the system itself (append trade confirmations as they execute), reconcile weekly via manual CSV.

---

## Layer 3 — Analysis (mostly solved)

Existing CLIs are the pipeline. Wrap in one orchestrator that emits JSON. Deterministic. No LLM needed here — that's the point.

```python
# apps/buy-ticket-agent/src/pipeline.py
results = {
    "itc":   run("itc_risk_cli.py", ticker),
    "risk":  run("risk_metrics_cli.py", ticker, days=252),
    "mom":   run("momentum_cli.py", ticker, days=90),
    "vol":   run("volatility_cli.py", ticker, days=90),
    "opt":   run("optimizer_cli.py", universe, method="max-sharpe"),
}
```

---

## Layer 4 — Ticket Generation (LLM)

Feed Layer 3 JSON + portfolio context + policy frameworks (`margin-strategy.md`, `modern-income-vehicles.md`) into Claude API:

- **Model:** `claude-sonnet-4-6` for allocation, escalate to `claude-opus-4-7` for strategic pivots
- **Prompt cache:** pin framework docs (don't change) → ~90% cost reduction
- **Tool use:** force JSON output matching `buy-ticket-template.md` schema
- **Hard-coded guardrails** (not negotiable by LLM):
  - Margin coverage ≥ 2x
  - Concentration ≤ 30% per position
  - ITC risk < 0.7 (or flagged with advisory block)

---

## Layer 5 — Approval Gate (non-negotiable)

Even for "full automation," this stays in:

- Ticket generated → pushed to phone (Pushover / ntfy.sh) with signed approval URL
- 15-min window to approve/reject
- **Default: reject** if no response (fail safe, not fail open)
- After ~30 successful approvals per strategy bucket, can flip `auto_execute=true` for that bucket only

---

## Layer 6 — Execution (the brick wall)

Fidelity has no retail API. Options:

| Broker   | API quality               | Margin rate   | Fit                            |
| -------- | ------------------------- | ------------- | ------------------------------ |
| Fidelity | ❌ None                    | 6-8%          | Current home                   |
| **IBKR** | ✅ TWS + Client Portal     | **2.5-4.5%**  | Best for this + cheapest margin|
| Schwab   | ⚠️ Individual approval    | 7-9%          | Slow onboarding                |
| Alpaca   | ✅ Clean REST              | Stocks only   | Wrong universe for Layer 2     |

**Honest take:** True execution automation requires moving the trading account to IBKR. Keep Fidelity as operating/banking. IBKR's 2.5-4.5% rate alone saves ~$1,800/yr on current $45.7K margin balance vs Fidelity 6-8%.

---

## Main Tradeoff

**Full-auto execution vs. notify-and-confirm.**

- Full-auto → needs broker migration + bulletproof guardrails + months of shadow runs
- Notify-and-confirm → 95% of agentic value, 1-tap mobile approval, no broker change, Fidelity stays

**Recommended path:** Build through Layer 5 first (notify-and-confirm on Fidelity). Run 3-6 months as shadow. Then decide whether execution autonomy justifies IBKR migration.

---

## Minimum Viable Stack

- **Language:** Python (matches stack, `uv` already in place)
- **Orchestrator:** Prefect (or plain cron — not Airflow, overkill)
- **LLM:** Anthropic SDK with prompt caching
- **Secrets:** Bitwarden CLI (already set up via Festus)
- **Notifications:** ntfy.sh (self-host on NAS) or Pushover
- **Logs:** structured JSON → `notebooks/auto-tickets/runs/`
- **State:** SQLite — don't over-engineer

---

## Phased Build Sequence

**Phase 1 — Shadow mode (no execution)**

1. SimpleFIN pay-date detector → fires pipeline
2. Pipeline runs all Layer 3 CLIs → JSON
3. Claude API assembles ticket → saves to `fin-guru-private/fin-guru/tickets/auto-drafts/`
4. Push notification with ticket preview
5. User manually executes trades in Fidelity (as today)

**Phase 2 — Approval loop**

6. Mobile approval URL → signed token → accepts/rejects ticket
7. Audit log of every run, decision, override

**Phase 3 — Execution (only if IBKR migration happens)**

8. IBKR Client Portal API integration
9. Per-bucket `auto_execute` flags, unlocked after N successful approvals
10. Post-trade reconciliation back into Google Sheets DataHub

---

## Open Questions

- [ ] Do we treat pay-date-triggered deployments as the ONLY source, or also support event-driven (e.g., VIX spike → rebalance)?
- [ ] Where does the pipeline run? NAS (Docker) vs cloud (cost, latency, secrets risk)?
- [ ] How does this interact with the `/margin-management` skill's coverage-ratio checks?
- [ ] Should Monte Carlo (MonteCarlo skill) run as a pre-flight gate on every ticket, or only monthly?

---

**Educational Notice:** This is architectural planning for a personal family-office automation system. Not investment advice. Any real-money automation requires extensive shadow testing, compliance review, and qualified professional consultation.
