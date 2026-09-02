---
title: "Environment variables"
description: "Variables read from the instance .env file, grouped by integration."
sidebar:
  order: 3
---

These variables come from the checked-in `.env.example` sample. Copy it to a local `.env` and fill in real values locally. Do not commit `.env`. All market-data keys are optional because the default provider works without keys.

## Instance and data store

| Variable | Purpose |
| --- | --- |
| `FIN_GURU_DATA_ROOT` | Instance data root. Every private file lives under this directory. Defaults to the current working directory. |
| `DATABASE_URL` | Optional database URL. Defaults to `family_office.db` under the instance data root. The sample sets `sqlite:///family_office.db`. |

## Market data

| Variable | Purpose |
| --- | --- |
| `FINNHUB_API_KEY` | Optional real-time price requests. |
| `ITC_API_KEY` | ITC risk-model requests. |
| `OPENAI_API_KEY` | Optional, for specific agent tasks. |

## SnapTrade live sync

Read-only bridge. Values live only in the local `.env`.

| Variable | Purpose |
| --- | --- |
| `SNAPTRADE_CLIENT_ID` | SnapTrade application client identifier. |
| `SNAPTRADE_CONSUMER_KEY` | SnapTrade consumer key. |
| `SNAPTRADE_USER_ID` | Linked user identifier. |
| `SNAPTRADE_USER_SECRET` | Linked user secret. |

## SimpleFIN

Optional local bank and card sync.

| Variable | Purpose |
| --- | --- |
| `SIMPLEFIN_ACCESS_URL` | Long-lived access URL used for account reads. |
| `SIMPLEFIN_SETUP_TOKEN` | One-time token used by the claim command. |
| `SIMPLEFIN_TRIGGER_INTERVAL_MS` | Optional poll interval for the local deposit-trigger process. |

## Email and notifications

| Variable | Purpose |
| --- | --- |
| `SMTP_SERVER`, `SMTP_PORT` | SMTP server settings for report email. |
| `EMAIL_FROM`, `EMAIL_PASSWORD` | Sending address and app password. |
| `SLACK_WEBHOOK_URL` | Slack notification webhook. |

## Portfolio settings

| Variable | Purpose |
| --- | --- |
| `DEFAULT_RISK_TOLERANCE` | Default risk tolerance profile. |
| `REBALANCE_THRESHOLD` | Rebalance trigger threshold. |
| `TAX_RATE` | Tax rate used in calculations. |

## Personal strategy inputs

The `FG_`-prefixed variables carry personal strategy values such as portfolio structure, income, dividend targets, margin rates, draw targets, and projection inputs. The sample file lists every name with a placeholder. These values are private. Set them only in a local `.env`, and never write a real value into a tracked file. See [data classification](../data-classification/) for the rule that decides what may be tracked.

## Placeholder safety

Do not leave sample placeholders in a local `.env` while running the test suite. Some configuration loaders parse numeric values at import time, so placeholder text can fail tests before the behavior under test is reached. See [Troubleshoot common failures](../../how-to/troubleshoot/).

_This page is built from `.env.example` in the repository._
