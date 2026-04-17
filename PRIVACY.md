# Privacy Policy — Finance Guru™

_Last reviewed: 2026-04-17_

Finance Guru is a **private, single-user family-office system**. This document describes how data is handled inside this repository and its companion apps.

## TL;DR

- All financial data stays on the owner's machine
- No telemetry, no remote analytics, no third-party data sharing
- Nothing personally identifying is committed to git — enforced by `.gitignore` and `formula-protection` skill
- When data _does_ leave the laptop (Google Sheets DataHub, Fidelity APIs, ITC Risk Models), it goes directly to the owner's own accounts — no intermediary

## What data Finance Guru handles

| Category | Source | Storage | Exposure |
|----------|--------|---------|----------|
| Portfolio positions | Fidelity CSV export | `notebooks/updates/` (gitignored) | Local only + owner's Google Sheet |
| Account balances | Fidelity CSV export | `notebooks/updates/` (gitignored) | Local only + owner's Google Sheet |
| Transaction history | Fidelity CSV export | `notebooks/updates/` (gitignored) | Local only + owner's Google Sheet |
| Dividend events | Fidelity CSV export | `notebooks/updates/` (gitignored) | Local only + owner's Google Sheet |
| User profile (risk tolerance, goals) | Interactive onboarding | `fin-guru/data/user-profile.yaml` (gitignored) | Local only |
| Market data | yfinance / Finnhub / ITC | In-memory during analysis | Per-provider terms |

## What leaves your machine

1. **Google Sheets writes** — when you invoke `PortfolioSyncing`, `dividend-tracking`, `TransactionSyncing`, or `retirement-syncing` skills, data flows _from your laptop to your Google Drive_ via the `gdrive` MCP server. It's your own Sheet in your own Google account.
2. **Market-data queries** — yfinance, Finnhub, and ITC Risk Models APIs see which tickers you query, but not your position sizes.
3. **Claude Code session** — the LLM provider (Anthropic) sees conversation content including any data you paste into the session. Treat Claude Code like a privileged assistant — don't paste data you wouldn't email your accountant.

## What never leaves your machine

- Raw Fidelity CSVs (gitignored)
- SSNs, account numbers, and API keys (scrubbed by `src/utils/logging.py:ScrubPIIProcessor` before they reach any log)
- `.env` contents
- `finance-guru-desktop/` runtime state (also gitignored)

## Security checklist (before publishing the fork)

```bash
# Verify private files are ignored
git status --ignored

# Verify no secrets in the working tree
git diff --cached

# Verify .env is gitignored
git check-ignore .env

# Audit dependencies for known CVEs
uv run pip-audit || true
```

## PII scrubbing — how it works

The structured logger (`src/utils/logging.py`) runs every string through `ScrubPIIProcessor` before output. Redacted patterns:

- **SSN** (`NNN-NN-NNNN`) → `***-**-****`
- **Credit cards** (13-19 digit sequences) → `****`
- **API tokens** (prefixed `sk-`, `pk-`, `ghp_`, `ghs_`) → first 4 chars + `***`
- **Email local parts** → `***@domain.tld`

If you need to redact something else, extend `ScrubPIIProcessor` and add a unit test.

## Third-party services and their privacy posture

| Service | Required? | What it sees | Terms |
|---------|-----------|--------------|-------|
| Anthropic Claude | Yes | Conversation content | <https://www.anthropic.com/legal/privacy> |
| yfinance (Yahoo) | Default | Tickers you query | <https://policies.yahoo.com/> |
| Finnhub | Optional | Tickers + API key | <https://finnhub.io/privacy-policy> |
| ITC Risk Models | Optional | Tickers + API key | Per ITC agreement |
| Google (Sheets / Drive) | Optional | Sheet contents via gdrive MCP | <https://policies.google.com/privacy> |
| GitHub | When pushing | Repository contents | <https://docs.github.com/privacy> |

## Jurisdiction

Finance Guru is not a regulated service; it is a personal tool. No GDPR/CCPA obligations apply because there are no third-party data subjects. If you fork this project and expose it as a service to others, you become the data controller and those obligations apply to you.

## Contact

Issues or concerns: open a GitHub issue using the [Question template](.github/ISSUE_TEMPLATE/question.md) with the `privacy` label.
