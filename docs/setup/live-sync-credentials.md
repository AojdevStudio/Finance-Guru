---
title: "Live sync credentials"
description: "Bring-your-own-credentials setup for SnapTrade and SimpleFIN live sync"
category: setup
---

# Live sync credentials

Finance Guru works CSV-first. Live sync is optional. It connects two read-only
providers, [SnapTrade](https://snaptrade.com/) for brokerage data and [SimpleFIN](https://www.simplefin.org/) for bank and card
activity. You obtain the credentials yourself and keep them in local,
gitignored files. This guide names the variables each provider needs. Never
write a credential value into a tracked file, an issue, or a pull request.

## Where the `.env` lives

The engine loads `.env` from the instance root, the directory named by
`FIN_GURU_DATA_ROOT` or the current working directory. `instance_init` scaffolds
that file from `.env.example`, preserving real defaults and commenting out empty
values and credential placeholders. Edit the instance's `.env`, not a copy
inside the repository checkout.

## SnapTrade

SnapTrade supplies brokerage positions, balances, and transactions. The
integration is read-only and requires four variables in the instance `.env`.
Sign up for API access at [SnapTrade](https://snaptrade.com/) and take the
client ID and consumer key from the
[SnapTrade dashboard](https://dashboard.snaptrade.com/). The
[SnapTrade API docs](https://docs.snaptrade.com/) cover registering a user,
which returns the user ID and user secret.

| Variable | Purpose |
| --- | --- |
| `SNAPTRADE_CLIENT_ID` | SnapTrade application client identifier |
| `SNAPTRADE_CONSUMER_KEY` | SnapTrade consumer key |
| `SNAPTRADE_USER_ID` | Linked user identifier |
| `SNAPTRADE_USER_SECRET` | Linked user secret |

All four must be present. The credential loader in
`src/integrations/snaptrade/models.py` raises an error naming any missing
variable.

### Account routing

Sync only touches accounts you have explicitly enabled. The routing file is
`snaptrade-accounts.yaml` in the instance root. Generate it from your linked
accounts.

```bash
uv run python -m src.integrations.snaptrade.cli accounts --write-config
```

Then edit the file. Give each account a `role` and set `enabled: true` only
after you have verified the account against a broker export. Accounts left
`unassigned` or disabled never sync.

## SimpleFIN

SimpleFIN supplies bank and card transactions. Get a setup token from
[SimpleFIN Bridge](https://bridge.simplefin.org/), the paid SimpleFIN service
that connects to your bank and issues tokens. The recommended single location
for its long-lived credential is the instance `.env`. `refresh_all` loads that
file with override enabled before it starts [Bun](https://bun.sh/) in `apps/simplefin-sync/`, so an
uncommented `SIMPLEFIN_ACCESS_URL` in the instance `.env` wins. Bun reads the
workspace's `apps/simplefin-sync/.env` value only when the instance leaves
`SIMPLEFIN_ACCESS_URL` commented out.

| Variable | Purpose |
| --- | --- |
| `SIMPLEFIN_SETUP_TOKEN` | One-time token exchanged by the claim command |
| `SIMPLEFIN_ACCESS_URL` | Long-lived access URL used for account reads |
| `SIMPLEFIN_TRIGGER_INTERVAL_MS` | Optional poll interval for the local deposit-trigger process |

Claim the setup token once. The claim command writes the resulting access URL
into `apps/simplefin-sync/.env` and refuses to overwrite an existing one. To use
the recommended single location afterward, move that value to the instance
`.env`, uncomment `SIMPLEFIN_ACCESS_URL`, and comment out the workspace copy.

```bash
cd apps/simplefin-sync
cp .env.example .env
# Set SIMPLEFIN_SETUP_TOKEN in apps/simplefin-sync/.env before continuing.
bun run claim
```

Treat both the setup token and the access URL as credentials.

## What `refresh_all` does

`uv run python -m src.integrations.refresh_all` runs three legs in order, each
isolated from the others.

| Leg | Source | What it writes |
| --- | --- | --- |
| `positions` | SnapTrade | Positions and balances for config-enabled accounts into `family_office.db` |
| `transactions` | SnapTrade | Investment activities, including dividends, into the transactions table |
| `expenses` | SimpleFIN | Bank and card transactions, auto-categorized, into the bank transactions table |

A failed leg does not stop the others. The command exits non-zero when any leg
fails, so automation can detect a stale source. Run with `--show` to print the
synced tables without contacting either provider.
