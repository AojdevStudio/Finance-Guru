---
status: accepted
---

# Add SnapTrade live sync to the legacy CSV/Sheets Finance Guru

## Context

This repo (the family-office Finance Guru) syncs portfolio data by manual Fidelity
CSV upload/download into a Google Sheets DataHub, driven by Claude Code skills.
`docs/VISION.md` declares this system end-of-life: the successor (Keepfolio) retires
Google Sheets and the `.claude/skills` entirely and routes SnapTrade into a local
SQLite DB. But Keepfolio is not yet at feature parity, and real money is managed on
this system today. We are deliberately investing in the legacy system as a bridge —
eliminating the manual CSV chore now rather than waiting for Keepfolio.

## Decision

Add a live SnapTrade integration to the legacy system, keeping the Google Sheets
DataHub as the system of record:

- **Reuse Keepfolio's SnapTrade Connection.** The four credentials (`clientId`,
  `consumerKey`, `userId`, `userSecret`) are copied from Keepfolio into this repo's
  `.env`. No user registration, no Connection Portal flow, and no credential-storage
  layer are built here — the brokerage is already linked at the SnapTrade-user level.
- **A thin, stateless, read-only Python CLI** (`src/integrations/snaptrade/`) wraps
  the official SnapTrade Python SDK and emits normalized JSON for accounts /
  positions / balances / activities.
- **The skills keep their workflow.** Compare logic, safety STOP-conditions, formula
  protection, and Google Sheets writes are unchanged — only each skill's data source
  changes from CSV to the CLI.
- **Accounts route to Sheet regions via explicit config**
  (`config/snaptrade-accounts.yaml`); an account with no declared role refuses to
  sync rather than guessing.
- **The Google Sheet stays the single source of truth** — deduplication is done by
  reading existing Sheet rows; there is no local state store.
- **Dividends** are realized DIVIDEND activities; forward distribution yields remain a
  research step, not a sync output.
- **The CSV import path is deleted** per account, but only after SnapTrade is verified
  for that account. Retirement (Vanguard / Fidelity 401k) conversion is deferred
  until those brokerages are connected to SnapTrade.

## Consequences

- A future reader will find a live SnapTrade integration inside a repo `docs/VISION.md`
  describes as retired, with Google Sheets called "dead." This ADR records that as a
  deliberate bridge investment, not an oversight or a contradiction.
- Registration, the Connection Portal, and credential rotation remain Keepfolio's
  responsibility, because the SnapTrade Connection is shared. A Keepfolio
  factory-reset would revoke this repo's access.
- ~70–80% of Keepfolio's SnapTrade implementation (Rust credential layer, Bun sidecar
  HTTP server, SQLite, webview contract) is intentionally not reproduced — it is
  product-shipping machinery with no analog in a single-user Python/Sheets repo.
