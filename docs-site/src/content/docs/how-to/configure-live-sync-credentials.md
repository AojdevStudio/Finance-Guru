---
title: "Configure live sync credentials"
description: "Set up SnapTrade and SimpleFIN credentials for optional live brokerage and bank sync."
sidebar:
  order: 2
---

Live sync is optional. Finance Guru works with broker CSV exports alone. Configure these credentials only when you want the read-only [SnapTrade](https://snaptrade.com/) brokerage sync or the [SimpleFIN](https://www.simplefin.org/) bank and card sync.

Keep credentials in a local `.env` file or process environment. `.env` and the local [SQLite](https://www.sqlite.org/) database are gitignored. That is a safeguard, not permission to print or commit their contents.

## Prepare the environment file

Create the environment file from the checked-in sample if you have not already.

```bash
cp .env.example .env
```

An instance created by the initializer already has a `.env` scaffolded from the same sample. Do not leave placeholder text in numeric settings you do not use, because some configuration loaders parse values at import time.

## SnapTrade

The read-only SnapTrade integration requires these private values before it can contact the provider. Sign up for API access at [SnapTrade](https://snaptrade.com/) and take the client ID and consumer key from the [SnapTrade dashboard](https://dashboard.snaptrade.com/). The [SnapTrade API docs](https://docs.snaptrade.com/) cover registering a user, which returns the user ID and user secret.

| Variable | Purpose |
| --- | --- |
| `SNAPTRADE_CLIENT_ID` | SnapTrade application client identifier. |
| `SNAPTRADE_CONSUMER_KEY` | SnapTrade consumer key. |
| `SNAPTRADE_USER_ID` | Linked user identifier. |
| `SNAPTRADE_USER_SECRET` | Linked user secret. |

Account roles and enabled-state are stored separately in a local account-routing file after account discovery. In an instance this file lives at `snaptrade-accounts.yaml` under the instance root. Do not commit it when it contains personal routing information.

## SimpleFIN

SimpleFIN credentials are consumed by the [Bun](https://bun.sh/) workspace under `apps/simplefin-sync/`. Get a setup token from [SimpleFIN Bridge](https://bridge.simplefin.org/), the paid SimpleFIN service that connects to your bank and issues tokens.

| Variable | Purpose |
| --- | --- |
| `SIMPLEFIN_SETUP_TOKEN` | One-time token used by the claim command. |
| `SIMPLEFIN_ACCESS_URL` | Long-lived access URL used for account reads. |
| `SIMPLEFIN_TRIGGER_INTERVAL_MS` | Optional poll interval for the local deposit-trigger process. |

Before claiming a setup token, initialize the workspace environment file, add the token there, and run the workspace claim command.

```bash
cd apps/simplefin-sync
cp .env.example .env
# Set SIMPLEFIN_SETUP_TOKEN in apps/simplefin-sync/.env before continuing.
bun run claim
```

The claim command refuses to overwrite an existing access URL. Treat both the setup token and the access URL as credentials and redact them from error reports.

## Verify

Run the all-source refresh and confirm it reaches your providers.

```bash
uv run python -m src.integrations.refresh_all --show
```

See [Run the data syncs](../run-the-syncs/) for the individual sync commands, and [Troubleshoot common failures](../troubleshoot/) when a refresh fails.

_This page is built from `docs/setup/api-keys.md` and `.env.example` in the repository._
