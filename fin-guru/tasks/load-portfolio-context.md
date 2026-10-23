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

Read each `source: ok` or `source: error` line. Under `positions: ok` the refresh also prints:

- `generation <synced_at>`: the UTC timestamp this run wrote on every account it synced. Keep it for step 4.
- `no enabled, routed account synced`: the run wrote no rows. Stop and name `snaptrade-accounts.yaml` under data gaps.
- `warning: cost basis unavailable for <quantity> <symbol> <instrument> units`: one line per lot with no cost basis.

- If `positions` is `error`, stop. Surface the error. Do not quote positions or balances as fresh, and do not open a CSV to fill the gap.
- If `transactions` or `expenses` is `error`, record that under data gaps. Those sources do not replace the positions snapshot.
- `positions: ok` only means the positions sync did not raise. An instance with no enabled, routed account still prints `ok`, writes no rows, and prints no `generation` line.

_Completion criterion:_ the refresh printed `positions: ok` and a `generation` line before any read.

### 2. Read the positions snapshot

```bash
uv run python -m src.integrations.snaptrade.sync_db --show
```

Quote that output. It prints a `# generation <synced_at>` line, then, per account, `account_equity`, settled cash, margin debt, `synced_at`, and each position (`symbol`, `instrument`, `quantity`, `avg_cost`).

It prints only the latest generation. Rows kept from an earlier run, such as an account disabled since, do not appear. Do not query the tables directly to add them back.

If it prints no `generation` line or no account block, stop. Name `snaptrade-accounts.yaml` under data gaps: the instance has no enabled account with a role, so there is nothing to load.

Cash available is `settled_cash` on the `balances` row. A `SPAXX` position is settled money-market shares, not the cash figure. The ledger has no Fidelity "Margin" versus "Cash" type column and no pending-activity row. A position printed with `avg=None` has no cost basis. Record that lot under data gaps and do not invent one.

`avg_cost` covers only the lots that carry a cost basis. For each symbol named in a refresh `warning: cost basis unavailable` line, the printed `avg` is not the basis of the whole `quantity`. Record the warning under data gaps, even when `avg` is not `None`.

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

If this command fails, keep the position snapshot from step 2 and record the typed error under data gaps. Do not estimate any margin figure. Typed failures include:

- a required `.env` value is missing (`FG_MARGIN_INTEREST_RATE_DECIMAL`, `FG_MARGIN_JUMP_ALERT_THRESHOLD`)
- `MarginAccountRoutingError`: `snaptrade-accounts.yaml` has zero or more than one enabled `taxable_margin` account
- `IncompleteBalanceGenerationError`: the latest balance generation is missing an enabled, routed account or the margin account
- `StaleBalanceSnapshotError`: the complete balance generation is older than 24 hours, more than five minutes in the future, or has a malformed or timezone-less timestamp. Run the sync-first refresh before retrying.
- `FileNotFoundError` or `ValueError`: the ledger or its balances rows are missing
- `StaleEquitySnapshotError`: the refresh stored NULL margin debt because SnapTrade equity had no valid sync time in the last 12 hours. The refresh printed `warning: account equity stale (last synced <ts>)`. Never treat the missing debt as zero

### 4. Check freshness

Compare the `# generation` line from step 2 with the `generation` line the refresh printed in step 1. Both come from the CLIs, so no extra query is needed.

- They match exactly: every account block in step 2 was written by this refresh. Proceed.
- They differ, or the refresh printed no `generation` line: the refresh wrote no new generation. Stop. Do not quote the step 2 rows as current. Name `snaptrade-accounts.yaml` under data gaps.

The margin calculator checks ledger generation freshness. A complete generation must be at most 24 hours old and no more than five minutes in the future. This timestamp records the ledger write. It does not prove provider equity freshness.

Also compare the generation date with today's UTC date from `date -u +"%Y-%m-%d"`. The generation is UTC, so a local `{current_date}` can differ by a day in the evening. A matching generation is from this run, so a different date means the system clock or the refresh is wrong. Warn with the timestamp.
- SnapTrade `price`, `account_equity`, and `gross_market_value` lag one session even when `synced_at` is current. Holdings, quantities, cost basis, and settled cash do not. Say so whenever you quote a dollar value that comes from price.
- Margin debt is gross market value minus `account_equity`. SnapTrade syncs equity about once a day, so the refresh stores margin debt only when equity is less than 12 hours old.

### 5. Validate before proceeding

- The refresh printed `positions: ok` for this run.
- The `--show` generation equals the refresh `generation` line.
- `--show` printed at least one balances row. An account block with `0 positions` is a valid cash-only snapshot.
- When the margin command succeeded, `portfolio_value` is greater than 0 and `source_file` starts with `db:`.
- When it failed, its typed error is under data gaps. The positions snapshot is still valid context.

A snapshot with fewer than five positions is still valid. Do not reject it, and do not go looking for a CSV that has more rows.

### 6. Store context

Keep the CLI text. Fill this summary only with values those commands printed. Leave every unknown under data gaps. If the margin command failed, omit the `Margin source_file` line and the overview lines it did not print.

```
PORTFOLIO CONTEXT LOADED: [synced_at]

SOURCE:
- Ledger: family_office.db
- Refresh: positions ok, generation [synced_at]
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
- Incomplete cost basis: [each refresh `warning: cost basis unavailable` line, or "none"]
- [any refresh warning, missing .env value, or transactions/expenses error]

DISCLAIMER:
[disclaimer field from the margin JSON, copied verbatim. If the margin command failed, part 6 of the fin-guru-output-contract skill, citing family_office.db and this synced_at]

✅ Portfolio context ready for analysis
```

Do not rank holdings, multiply `quantity` by `price`, or sum gain/loss in this task. Later analysis that needs weights or concentration runs a calculator and quotes that output.

When a buy ticket asks for the portfolio context source, cite `family_office.db` and this `synced_at`.

---

## Error Handling

**No ledger, or the positions sync failed:**

Tell the owner the ledger has no current snapshot and that the next step is `uv run python -m src.integrations.refresh_all` from the instance. If the instance itself is missing, scaffold it with `uv run python -m src.cli.instance_init`. Do not ask for a Fidelity positions download.

**Margin command failed:**

Keep the position snapshot. Name the typed error. Do not invent the ratio.

**Generation mismatch:**

The `--show` generation is older than the refresh `generation` line. Those rows do not describe a current book. Stop and name the cause under data gaps.

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

1. The refresh lines, the `--show` snapshot, and the margin JSON when that command succeeded.
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
