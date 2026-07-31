---
name: transaction-syncing
description: Refresh investment activities and card/bank expenses into family_office.db, then review spending. Investment activities come from the DB transactions table (SnapTrade); debit-card and bank spending comes from the DB bank_transactions table (SimpleFIN), auto-categorized. Sync-first so nothing is stale. USE WHEN user mentions "sync transactions", "transaction history", "expense tracker", "categorize spending", OR "update expenses".
---

# TransactionSyncing

Refresh financial activity into `family_office.db`: investment activities (`transactions` table) and card/bank spending (`bank_transactions` table), auto-categorized for budget review.

`family_office.db` is the system of record. The Google Sheets export was retired 2026-07-31.

## Step 0: Refresh (sync-first, mandatory)

Both halves read from the local DB, refreshed FIRST so nothing is stale. Follow the shared **[Sync-First + DB-Read](../_shared/SyncFirstDbRead.md)** pattern. This skill needs two sources:

```bash
uv run python -m src.integrations.snaptrade.sync_transactions_db          # investment activities -> transactions
uv run python -m src.integrations.simplefin.sync_expenses_db --months 3   # card/bank spending -> bank_transactions
# or refresh everything at once:
uv run python -m src.integrations.refresh_all --months 3
```

Completion criterion: _the `transactions` and `bank_transactions` tables carry this run's `synced_at`._

## Direction and sign

`bank_transactions.direction` is resolved by `resolve_direction()` in `src/integrations/simplefin/sync_expenses_db.py`. Explicit feed wording wins over amount sign, because Fidelity's CMA reports inbound payroll with the same negative sign it uses for outflows. `amount` is signed to match direction, so `SUM(amount)` is real cash flow: credits positive, debits negative.

## Workflow Routing

| Workflow | Trigger | File |
|----------|---------|------|
| **IngestTransactions** | "ingest transactions", "import history", user points to a Downloads CSV | `workflows/IngestTransactions.md` |

CSV ingest is an archive and fallback path. The primary flow is the Step 0 refresh above.

## Examples

**Example 1: Sync after downloading Fidelity transaction history**
```
User: "sync transactions"
-> Reads History_for_Account_{account_id}.csv from notebooks/transactions/
-> Creates/updates Transactions tab with full Fidelity data
-> Routes DEBIT CARD PURCHASE entries to Expense Tracker
-> Auto-categorizes expenses (H-E-B -> Groceries, Tesla -> Auto & Transport)
-> Reports: "Added 45 transactions, 12 expenses categorized"
```

**Example 2: Import new transaction export**
```
User: "import the transaction history"
-> Invokes SyncTransactions workflow
-> Detects duplicates by date + action + amount
-> Skips existing entries, adds only new ones
-> Flags uncategorized expenses for manual review
```

**Example 3: Check recent transactions**
```
User: "import fidelity transactions and update expense tracker"
-> Full sync with expense routing
-> Generates summary of dividends received, purchases, margin interest
```

## Architecture Overview

### Data Flow

```
SnapTrade activities            SimpleFIN dump (bun run src/dump.ts)
        |                                |
        v                                v
  sync_transactions_db            sync_expenses_db (categorize.py)
        |                                |
        v                                v
+------------------+           +--------------------+
| transactions     |           | bank_transactions  |  <- categorized, upserted
| table (DB)       |           | table (DB)         |
+------------------+           +--------------------+
```

`family_office.db` is the terminus. Query the tables directly for review; there is no downstream export.

### Transaction Types Handled

| Fidelity Action | Table | Category |
|-----------------|-------|----------|
| DIVIDEND RECEIVED | transactions | DIVIDEND |
| REINVESTMENT | transactions | REINVESTMENT |
| DEBIT CARD PURCHASE | bank_transactions | Auto-categorized |
| MARGIN INTEREST | transactions | MARGIN_INTEREST |
| DIRECT DEPOSIT | bank_transactions (credit) | INCOME |
| LONG-TERM CAP GAIN | transactions | CAP_GAIN |
| JOURNALED | transactions | INTERNAL_TRANSFER |

### Smart Categorization

Categorization is executable and runs inside the expense adapter, so the
`category` column arrives pre-filled on every `bank_transactions` row. The rules
live in code at `src/integrations/simplefin/categorize.py`
(`categorize_expense(text, amount)`), which is the source of truth mirroring the
human-readable `CategoryRules.md`. Keep the two in sync when adding patterns.

**Sample patterns:**
- `H-E-B`, `KROGER`, `COSTCO`, `WAL-MART` -> Groceries
- `Tesla`, `SUPERCHA` -> Auto & Transport
- `BENIHANA`, `GOLDEN CORRAL`, `PAPA JOHN` -> Dining Out
- `CVS`, `PHARMACY` -> Health & Wellness
- amount < $1.00 or `verification` text -> Exempt; no match -> Uncategorized

## Input Sources: the local DB (primary)

### Half A: Investment activities (`transactions` table)

After Step 0's refresh, read investment activity from the DB:

```bash
sqlite3 family_office.db \
  "SELECT date, type, symbol, description, amount, quantity, currency FROM transactions ORDER BY date;"
```

Each row has a stable shape (`type`, `date`, `symbol`, `amount`, `quantity`,
`currency`, `description`). Map it onto the master Transactions tab (type -> Action,
date -> Date, amount -> Amount, etc.).

### Half B: Card / bank expenses (`bank_transactions` table)

Debit-card and bank spending has **no SnapTrade equivalent**, so it comes from
SimpleFIN via the expense adapter, already normalized and categorized:

```bash
sqlite3 family_office.db \
  "SELECT date, payee, description, amount, direction, category FROM bank_transactions ORDER BY date DESC;"
```

The adapter (`src/integrations/simplefin/sync_expenses_db.py`) pulls the SimpleFIN
dump, categorizes each row via the executable rules in
`src/integrations/simplefin/categorize.py` (the code source of truth mirroring
`CategoryRules.md`), and upserts into `bank_transactions` keyed on
`(account_id, txn_id)`. Route `direction == "debit"` rows to the Expense Tracker
using the `category` column.

**Dedupe:** the DB layer is idempotent (activities via `dedupe_key`, expenses via
the `(account_id, txn_id)` upsert key), so re-running a sync is always safe and
needs no external ledger to compare against.

**Fallback:** the Fidelity History CSV path below remains a manual reconciliation
fallback only; it is no longer the primary path.

## Core Workflow

### 1. Read Fidelity Transaction History CSV

**Location**: `notebooks/transactions/History_for_Account_{account_id}.csv`

**CSV Columns**:
```
Run Date, Action, Symbol, Description, Type, Price ($), Quantity,
Commission ($), Fees ($), Accrued Interest ($), Amount ($),
Cash Balance ($), Settlement Date
```

### 2. Reconcile against the DB

Compare CSV rows against the `transactions` table to spot anything the live sync
missed. Match on Date + Action + Amount. This is a reconciliation check, not an
import path: the live sync owns the data.

### 3. Generate Summary

```
SYNC SUMMARY - [Date]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

transactions:       45 inserted, 12 updated
bank_transactions:  18 inserted, 3 uncategorized

BY TYPE:
  Dividends: $342.50
  Margin Interest: -$18.43
  Debit Card: -$1,245.67
  Direct Deposit: +$5,054.09
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Uncategorized rows are the follow-up: add the pattern to
`src/integrations/simplefin/categorize.py` and mirror it in `CategoryRules.md`.

## Reference Files

- **CategoryRules.md**: Pattern matching rules for expense categorization
- **src/integrations/simplefin/categorize.py**: executable source of truth for categories
- **src/integrations/simplefin/sync_expenses_db.py**: direction resolution and upsert

## Pre-Flight Checklist

Before syncing transactions:
- [ ] `DATABASE_URL` and `SIMPLEFIN_ACCESS_URL` are set in `.env`
- [ ] SnapTrade account is enabled and routed in `config/snaptrade-accounts.yaml`
- [ ] Current date retrieved via `date` command

---

**Skill Type**: Domain (workflow guidance)
**Enforcement**: SUGGEST
**Priority**: Medium
**Line Count**: < 300 (following 500-line rule)
