---
title: "Finance Guru private configuration"
description: "Environment variables for optional providers and local data sync"
category: setup
---

# Finance Guru private configuration

Keep credentials in a local `.env` file or process environment. `.env` and the
local SQLite database are gitignored; that is a safeguard, not permission to
print or commit their contents.

Before running a supported data sync, create the root environment file from the
checked-in sample. It supplies the required local database location even when
you do not configure an external provider:

```bash
cp .env.example .env
```

## Local data store

| Variable | Purpose | Default behavior |
| --- | --- | --- |
| `DATABASE_URL` | SQLite connection URL used by the supported sync modules. | Required; the checked-in sample sets `sqlite:///family_office.db`. |

The standard local database filename is `family_office.db`. Do not point a
public example or CI job at a real database.

## SnapTrade

The read-only SnapTrade integration requires these private values before it can
contact the provider:

| Variable | Purpose |
| --- | --- |
| `SNAPTRADE_CLIENT_ID` | SnapTrade application client identifier. |
| `SNAPTRADE_CONSUMER_KEY` | SnapTrade consumer key. |
| `SNAPTRADE_USER_ID` | Linked user identifier. |
| `SNAPTRADE_USER_SECRET` | Linked user secret. |

Account roles and enabled-state are stored separately in the local
`config/snaptrade-accounts.yaml` file after account discovery. Do not commit
that file when it contains personal routing information.

## SimpleFIN

SimpleFIN credentials are consumed by the Bun workspace under
`apps/simplefin-sync/`:

| Variable | Purpose |
| --- | --- |
| `SIMPLEFIN_SETUP_TOKEN` | One-time token used by the claim command. |
| `SIMPLEFIN_ACCESS_URL` | Long-lived access URL used for account reads. |
| `SIMPLEFIN_TRIGGER_INTERVAL_MS` | Optional poll interval for the local deposit-trigger process. |

The claim command refuses to overwrite an existing access URL. Treat both the
setup token and access URL as credentials and redact them from error reports.

Before claiming a setup token, initialize the workspace environment file, add
the token there, and run the workspace command:

```bash
cd apps/simplefin-sync
cp .env.example .env
# Set SIMPLEFIN_SETUP_TOKEN in apps/simplefin-sync/.env before continuing.
bun run claim
```

## Required research MCP integrations

Finance Guru agent workflows require configured access to these MCP servers:

- `exa` for research and market intelligence
- `bright-data` for web scraping and extraction
- `sequential-thinking` for multi-step reasoning
- `financial-datasets` for SEC filings and financial statements
- `web-search` for current market information

These are workflow integrations, not `.env` variables. Finance Guru
integrations must use the required MCP servers; do not add a Google Drive or
Google Sheets dependency to replace the local data boundary.

## Optional market and analysis configuration

| Variable | Used by |
| --- | --- |
| `FINNHUB_API_KEY` | Optional real-time price requests. |
| `ITC_API_KEY` | ITC risk-model requests. |
| `OPENAI_API_KEY` | Legacy or optional local agent workflows when explicitly configured. |

Market analysis can use public market-data sources without one of these keys,
but a provider may still receive the tickers you query. See [Privacy](../../PRIVACY.md).

## Test safety

Do not leave `.env.example` placeholders in a local `.env` while running the
test suite. Some configuration loaders parse numeric values at import time, so
placeholder text can fail tests before the test's actual behavior is reached.
For a clean local test run, remove the scaffolded `.env` or replace only the
values you intentionally use:

```bash
uv run pytest -m "not integration"
```
