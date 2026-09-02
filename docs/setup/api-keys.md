---
title: "Finance Guru private configuration"
description: "Environment variables for optional providers and local data sync"
category: setup
---

# Finance Guru private configuration

Keep credentials in a local `.env` file or process environment. The engine
reads `.env` from the instance root, the directory named by
`FIN_GURU_DATA_ROOT` or the current working directory. `instance_init`
scaffolds that file from the checked-in `.env.example`, preserving real defaults
and commenting out empty values and credential placeholders for you to fill in.
The `.env` file is gitignored. The local SQLite database is committed to the
instance's local-only repository, which has no remote, and never to the public
engine checkout.

## Local data store

| Variable | Purpose | Default behavior |
| --- | --- | --- |
| `DATABASE_URL` | SQLite connection URL used by the supported sync modules. | Optional; defaults to `family_office.db` under the instance root. |

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

Account roles and enabled-state are stored separately in
`snaptrade-accounts.yaml` under the instance root after account discovery. See
the [live sync credentials guide](live-sync-credentials.md) for the discovery
command and the routing rules.

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

The instance initializer comments out `.env.example` placeholders so they do
not enter the process environment. If you copy `.env.example` manually instead,
comment out unused placeholders before running tests; some configuration loaders
parse numeric values at import time and reject placeholder text:

```bash
uv run pytest -m "not integration"
```
