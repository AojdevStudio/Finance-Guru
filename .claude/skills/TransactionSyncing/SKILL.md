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

Completion criterion: _both sync commands report success._ Do not gate on
`MAX(synced_at)` advancing: both layers are idempotent and only stamp rows they
actually write, so a run with no new activity leaves the timestamp untouched.
Read the command output instead (`N inserted, M updated, K skipped`).

## ⚠️ The two feeds do not run at the same speed

**`bank_transactions` (SimpleFIN) is current. `transactions` (SnapTrade) lags by
days.** Verified 2026-08-04: the `positions` table showed PLTR and TSLA puts
opened on 2026-08-03, while `transactions` had no row for either buy and its
latest activity date was still 2026-07-31. SnapTrade updated holdings before it
published the activity that created them.

**Consequence: never conclude "X did not happen" from an absence in
`transactions`.** A missing row means "not published yet" at least as often as it
means "did not occur". To answer whether something executed:

1. Check `positions` for a holdings change (fastest signal).
2. Check `bank_transactions` for the cash leg, which is current.
3. Only then read `transactions`, and treat the tail few days as incomplete.

The same applies to month-boundary reporting: the last several days of any period
may still be missing from the investment side.

## Direction and sign

`bank_transactions.direction` is resolved by `resolve_direction()` in `src/integrations/simplefin/sync_expenses_db.py`. Explicit feed wording wins over amount sign, because Fidelity's CMA reports inbound payroll with the same negative sign it uses for outflows. `amount` is signed to match direction, so `SUM(amount)` is real cash flow: credits positive, debits negative.

## ⚠️ Household spending lives in THREE streams, in two different tables

**A spending review that reads only `bank_transactions` is wrong.** Measured for
July 2026: that table showed well under two thirds of personal spend. The missing 41%
was in the other two streams.

| Stream | Table | July 2026 |
|---|---|---|
| 1. Bank and card accounts (SimpleFIN) | `bank_transactions` | 59% |
| 2. **Brokerage direct debits (SnapTrade)** | **`transactions`** | **36%** |
| 3. Cards paid but not connected | neither, infer from the bill | $748.69 |

Stream 2 is the one that gets forgotten. The Fidelity brokerage pays the
mortgage, insurance, utilities, phone, tuition, and has a debit card used for
groceries. Those rows are `type='WITHDRAWAL'` in `transactions`, not in
`bank_transactions` at all.

```bash
sqlite3 family_office.db \
  "SELECT date, description, -amount FROM transactions
   WHERE type = 'WITHDRAWAL' AND date LIKE '2026-07%' ORDER BY -amount DESC;"
```

Categorize those rows with the same `categorize_expense()`, then separate:

- **Household consumption**: mortgage, insurance, groceries, utilities, tuition.
- **Not consumption**: `MARGIN INTEREST` (financing cost, report separately),
  card bill payments, and `JOURNALED` internal moves.

**Check for double counting across the two tables** by matching amount and date
within a couple of days. In July exactly one pair collided ($50 on 7/24) and
inspection showed two genuinely separate payments, not a duplicate. Inspect; do
not assume either way.

**Income totals have the mirror-image problem.** Credits into
`bank_transactions` include transfers between the principal's own accounts, so
summing them overstates income. Net internal movement out before quoting a
surplus.

## Spending reviews: count purchases, exclude bill payments, then AUDIT COVERAGE

**Count card purchases. Exclude card bill payments.** Both are debits, but a
purchase and the payment of that same purchase are one dollar of spending, not
two. Exclude the categories in `NON_SPEND_CATEGORIES`, and exclude
`BUSINESS_CATEGORIES` plus the business accounts when the question is household
spending.

**That exclusion is only valid if every card that receives a payment also
reports its purchases.** When a card is paid but not connected, its purchases are
invisible and its payment was excluded, so the spending vanishes entirely. Run
this before quoting any total:

```bash
uv run python -c "
import sqlite3
c = sqlite3.connect('family_office.db')
print('Cards receiving payments:')
for r in c.execute(\"SELECT DISTINCT COALESCE(payee,description) FROM bank_transactions WHERE category='Credit Card Payment'\"):
    print('  ', r[0])
print('Card accounts reporting purchases (with last activity):')
for r in c.execute(\"SELECT account_name, MAX(date), COUNT(*) FROM bank_transactions WHERE LOWER(COALESCE(org,'')) LIKE '%credit%' OR LOWER(COALESCE(org,'')) LIKE '%express%' GROUP BY account_id\"):
    print(f'   {r[0]:<38} last {r[1]}  ({r[2]} rows)')
"
```

Two failure modes, both found 2026-08-04:

1. **Paid but not connected.** An Apple Card bill of $748.69 cleared on
   2026-08-03 with zero Apple purchases anywhere in the feed. That understated
   July household spending by roughly 8%. **Backfill from the bill amount and say
   so**, or connect the account.
2. **Connected but stale.** Chase Sapphire Preferred stopped reporting on
   2026-07-17 and an older card had produced nothing since 2026-04-21. A stale
   connection looks identical to genuinely low spending. Treat any card whose
   last activity is more than about a week old as suspect.

**Always state the coverage caveat alongside the total.** A household number
carrying an unquantified gap is worse than one carrying a stated one.

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
  Debit Card: -$1,234.56
  Direct Deposit: +$2,000.00
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
- [ ] `DATABASE_URL` is set in the project-root `.env`
- [ ] `SIMPLEFIN_ACCESS_URL` is set in **`apps/simplefin-sync/.env`**, not the
      project root. The expense adapter shells out to `bun run src/dump.ts` inside
      that workspace, so the token is read by the Bun app from its own `.env`.
      Checking the root `.env` for it produces a false "MISSING" (hit 2026-08-04).
- [ ] SnapTrade account is enabled and routed in `config/snaptrade-accounts.yaml`
- [ ] Current date retrieved via `date` command

---

**Skill Type**: Domain (workflow guidance)
**Enforcement**: SUGGEST
**Priority**: Medium
**Line Count**: < 300 (following 500-line rule)
