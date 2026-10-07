# Load Portfolio Context

**Task ID:** `load-portfolio-context`
**Category:** System Initialization
**Required By:** All financial specialists before analysis
**Auto-Run:** Yes (in agent critical-actions)

---

## Purpose

Load your current positions, balances, and margin health into working memory from `family_office.db`. That ledger is the single source of truth for positions and balances. Broker CSV exports under `imports/` are an ingestion path, not a second ledger, and this task does not read them.

Run the commands below from your instance directory, or with `FIN_GURU_DATA_ROOT` set, so the CLIs resolve `family_office.db`. The shared rule is `{project-root}/.claude/skills/_shared/SyncFirstDbRead.md`.

---

## Execution Steps

### 1. Refresh the ledger

Refresh before any read. Portfolio context depends on the positions sync, which writes `positions` and `balances`.

```bash
uv run python -m src.integrations.refresh_all
```

Read each `source: ok` or `source: error` line.

- If `positions` is `error`, stop. Surface the error. Do not quote positions or balances as fresh, and do not open a CSV to fill the gap.
- If `transactions` or `expenses` is `error`, record that under data gaps. Those sources do not replace the positions snapshot.
- `positions: ok` only means the positions sync did not raise. An instance with no enabled, routed account still prints `ok` and writes no rows. Step 2 is what shows whether a snapshot landed.

_Completion criterion:_ the `positions` and `balances` tables carry this run's `synced_at` before any read.

### 2. Read the positions snapshot

```bash
uv run python -m src.integrations.snaptrade.sync_db --show
```

Quote that output. It prints, per account, `account_equity`, settled cash, margin debt, `synced_at`, and each position (`symbol`, `instrument`, `quantity`, `avg_cost`).

If it prints only the database path and no account block, stop. Name `snaptrade-accounts.yaml` under data gaps: the instance has no enabled account with a role, so there is nothing to load.

Cash available is `settled_cash` on the `balances` row. A `SPAXX` position is settled money-market shares, not the cash figure. The ledger has no Fidelity "Margin" versus "Cash" type column and no pending-activity row. A position printed with `avg=None` has no cost basis. Record that lot under data gaps and do not invent one.

### 3. Read margin health from the calculator

```bash
uv run python -m src.analysis.margin_metrics --pretty
```

Leave the source flag off so the command reads the ledger. Do not point it at a live API call or a broker export. Quote the JSON, including its `disclaimer`. Do not recompute ratios.

Use these fields as printed:

- `source_file` must start with `db:`
- `portfolio_value` is account equity
- `margin_balance` is the derived margin debit
- `margin_buying_power`
- `portfolio_margin_ratio`
- `alert_status`
- `as_of_date`

`margin_day_change` and `margin_interest_accrued_this_month` are null on the ledger path. Record them as data gaps. Do not substitute zero, and do not read a balances CSV to obtain them.

If this command fails because a required `.env` value is missing (`FG_MARGIN_INTEREST_RATE_DECIMAL`, `FG_MARGIN_JUMP_ALERT_THRESHOLD`), keep the position snapshot from step 2 and record the typed error under data gaps. Do not estimate the missing input.

### 4. Check freshness

```bash
sqlite3 family_office.db "SELECT 'positions', MAX(synced_at) FROM positions
  UNION ALL SELECT 'balances', MAX(synced_at) FROM balances;"
```

Compare `synced_at` with `{current_date}` from `date +"%Y-%m-%d"`.

- Same calendar day as this refresh: proceed.
- More than two days behind `{current_date}`: the refresh did not land a current snapshot. Warn with the timestamp and ask the owner whether to proceed on those rows or fix the refresh first.
- SnapTrade `price`, `account_equity`, and `gross_market_value` lag one session even when `synced_at` is current. Holdings, quantities, cost basis, settled cash, and margin debt do not. Say so whenever you quote a dollar value that comes from price.

### 5. Validate before proceeding

- The refresh printed `positions: ok` for this run.
- `--show` printed at least one balances row and at least one position.
- `portfolio_value` from the margin JSON is greater than 0 when that command succeeded.
- `source_file` starts with `db:`.

A snapshot with fewer than five positions is still valid. Do not reject it, and do not go looking for a CSV that has more rows.

### 6. Store context

Keep the CLI text. Fill this summary only with values those commands printed. Leave every unknown under data gaps. If the margin command failed, omit the overview lines it did not print.

```
PORTFOLIO CONTEXT LOADED: [synced_at]

SOURCE:
- Ledger: family_office.db
- Refresh: positions ok at [synced_at]
- Margin source_file: [db:... from the JSON]

OVERVIEW:
- Portfolio value (account equity): [portfolio_value]
- Settled cash: [settled_cash from --show]
- Buying power: [margin_buying_power]
- Margin debit: [margin_balance]
- Portfolio-to-margin ratio: [portfolio_margin_ratio]
- Alert status: [alert_status]

HOLDINGS:
[position lines from sync_db --show, unchanged]

DATA GAPS:
- Today's gain/loss: not in the ledger
- All-time gain/loss and return: not in the ledger
- Margin versus cash position split: not in the ledger
- Pending activity: not in the ledger
- Accrued margin interest and day change: null on the db source
- Position weights and concentration: these commands do not emit them
- Price lag: account equity and position prices can be one session behind
- [any refresh warning, missing .env value, or transactions/expenses error]

DISCLAIMER:
[disclaimer field from the margin JSON, copied verbatim]

✅ Portfolio context ready for analysis
```

Do not rank holdings, multiply `quantity` by `price`, or sum gain/loss in this task. Later analysis that needs weights or concentration runs a calculator and quotes that output.

When a buy ticket asks for the portfolio context source, cite `family_office.db` and this `synced_at`.

---

## Error Handling

**No ledger, or the positions sync failed:**

Tell the owner the ledger has no current snapshot and that the next step is `uv run python -m src.integrations.refresh_all` from the instance. If the instance itself is missing, scaffold it with `uv run python -m src.cli.instance_init`. Do not ask for a Fidelity positions download.

**Margin command failed on a missing input:**

Keep the position snapshot. Name the typed error. Do not invent the ratio.

**Snapshot older than two days:**

Warn with the `synced_at` value. Recommendations from that snapshot do not describe a current book. Ask whether to proceed or to fix the refresh first.

**CSV fallback:**

A broker CSV is an explicit opt-in on the `portfolio-syncing` skill, used only when you ask for it or when a live source is down and you choose that fallback. This task does not run that path.

---

## Agent Integration

**In agent `<critical-actions>`:**

```xml
<i>Execute task: load-portfolio-context.md before any portfolio analysis or recommendations</i>
```

**When to skip:**

- You are asking a general educational question, not about your portfolio
- You are asking about market news, not your positions
- You explicitly say not to load your portfolio

**When mandatory:**

- Buy or sell recommendations
- Risk exposure
- Position sizing
- Rebalancing
- Performance analysis

---

## Output

1. The refresh lines, the `--show` snapshot, and the margin JSON.
2. The structured summary above, stored in working memory.
3. A ready state, or a stop with a typed reason when the refresh did not land.

---

## Notes

- The refresh replaces the positions and balances snapshot in `family_office.db`. This task does not write analysis files or tickets.
- This task does not make trading recommendations.
- Quote the CLIs. Do not fill a missing figure with an estimate.
- Agents should reference this loaded context for the rest of the session.

---

**Last Updated:** 2026-10-06
**Maintained By:** Finance Orchestrator (Cassandra Holt)
