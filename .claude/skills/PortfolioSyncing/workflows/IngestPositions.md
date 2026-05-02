# IngestPositions Workflow

Ingest Fidelity portfolio CSVs from Downloads into `notebooks/updates/`. Handles duplicate file detection, regular vs dividend view classification, and Balances file updates.

## Critical Rules

- **MOVE, never copy**: Always use `mv`, NEVER `cp`. Files must be removed from `~/Downloads/` after ingestion. Leaving copies behind causes confusion on re-runs.
- **Use `fd` for file discovery**: zsh glob expansion fails if any pattern has zero matches, killing the entire command. Always use `fd` instead of `ls` with globs.

## Triggers

This workflow runs in two contexts — standalone, or as the first half of the E2E chain. See `SKILL.md` → "Workflow Routing" for the authoritative trigger table.

- **Standalone (ingest-only mode)**: `ingest positions`, `import positions`, `bring in positions`, `move fidelity files`, or the user mentions downloading positions/balances from Fidelity but doesn't ask for the sheet to be updated.
- **Chained (E2E mode)**: `portfolio-sync`, `sync portfolio`, `import fidelity`, `run the full skill`, `run the full skill e2e`, `full portfolio sync`, `sync my portfolio`, or the user says they just downloaded from Fidelity and wants the sheet updated. In this mode, this workflow finishes with a one-line handoff and SyncPortfolio runs next, automatically (no "Proceed?" prompt).

If the trigger is ambiguous, prefer chained/E2E — that matches what users usually mean when they ask about syncing.

## Step 1: Locate Source Files in Downloads

**Account ID**: Read from `fin-guru/data/user-profile.yaml` → `accounts[].account_id` at runtime. NEVER hardcode.

Scan `~/Downloads/` for all matching files. **CRITICAL**: Use `fd` (not `ls` with globs) because zsh kills the entire command if _any_ glob pattern has zero matches.

```bash
# Find all position and balance CSVs (including (1), (2) duplicates)
# MUST use fd — zsh glob expansion fails if Balances file doesn't exist
fd --type f 'Portfolio_Positions_.*\.csv$' ~/Downloads/ --max-depth 1
fd --type f 'Balances_for_Account_.*\.csv$' ~/Downloads/ --max-depth 1
fd --type f 'History_for_Account_.*\.csv$' ~/Downloads/ --max-depth 1
```

**NEVER use these patterns** (they fail silently in zsh):
```bash
# ❌ WRONG — zsh aborts entire command if any glob has no matches
ls -lt ~/Downloads/Portfolio_Positions_*.csv ~/Downloads/Balances_*.csv 2>/dev/null
# ❌ WRONG — same zsh glob issue
ls ~/Downloads/*.csv | head -10
```

**Expected files (typical download session):**

| File | What It Is |
|------|-----------|
| `Portfolio_Positions_MMM-DD-YYYY.csv` | First position download (regular OR dividend view) |
| `Portfolio_Positions_MMM-DD-YYYY (1).csv` | Second position download (the other view) |
| `Balances_for_Account_{ACCOUNT_ID}.csv` | Balance export |
| `Balances_for_Account_{ACCOUNT_ID} (1).csv` | Duplicate balance if re-downloaded |

**If no files found**: Ask user if they've downloaded from Fidelity yet.

## Step 2: Classify Regular vs Dividend View

Both position files download as `Portfolio_Positions_MMM-DD-YYYY.csv`. Distinguish by reading the header row (row 1):

```bash
# Read header of each positions file
head -1 "FILE_PATH"
```

**Classification rules:**

| Header Contains | View Type |
|----------------|-----------|
| `Ex-date` AND `Amount per share` AND `Pay date` AND `Dist. yield` | **Dividend View** |
| `Today's Gain/Loss Dollar` AND `Cost Basis Total` AND `Average Cost Basis` | **Regular View** |

**Quick check**: If header contains `Ex-date` -> dividend view. Otherwise -> regular view.

## Step 3: Move Regular View (No Rename Needed)

The regular view file is already date-tagged by Fidelity: `Portfolio_Positions_MMM-DD-YYYY.csv`

```bash
# Move regular view as-is (already properly named)
mv ~/Downloads/Portfolio_Positions_MMM-DD-YYYY.csv notebooks/updates/Portfolio_Positions_MMM-DD-YYYY.csv
```

If the regular view was the `(1)` tagged file:
```bash
# Remove the (1) tag when moving
mv "~/Downloads/Portfolio_Positions_MMM-DD-YYYY (1).csv" notebooks/updates/Portfolio_Positions_MMM-DD-YYYY.csv
```

## Step 4: Move and Rename Dividend View

Rename the dividend view to follow the `Dividend_Positions_MMM-DD-YYYY.csv` convention:

```bash
# Extract date from the original filename (e.g., "Mar-06-2026" from "Portfolio_Positions_Mar-06-2026.csv")
# Rename to Dividend_Positions_MMM-DD-YYYY.csv
mv "~/Downloads/Portfolio_Positions_MMM-DD-YYYY.csv" notebooks/updates/Dividend_Positions_MMM-DD-YYYY.csv
# OR if it was the (1) file:
mv "~/Downloads/Portfolio_Positions_MMM-DD-YYYY (1).csv" notebooks/updates/Dividend_Positions_MMM-DD-YYYY.csv
```

**Example**:
```bash
mv "~/Downloads/Portfolio_Positions_Mar-06-2026 (1).csv" notebooks/updates/Dividend_Positions_Mar-06-2026.csv
```

## Step 5: Move Balances File

Balances file overwrites the existing one (no date tag, single canonical file):

```bash
# Move balances (overwrites existing)
mv ~/Downloads/Balances_for_Account_{ACCOUNT_ID}.csv notebooks/updates/Balances_for_Account_{ACCOUNT_ID}.csv
```

**Duplicate handling**: If `Balances_for_Account_{ACCOUNT_ID} (1).csv` exists, it's a re-download. Use the newest one (highest number or no number = first download):
```bash
# If (1) exists, it's the newer download — use it, discard the older
mv "~/Downloads/Balances_for_Account_{ACCOUNT_ID} (1).csv" notebooks/updates/Balances_for_Account_{ACCOUNT_ID}.csv
# Clean up the older one if still present
rm -f ~/Downloads/Balances_for_Account_{ACCOUNT_ID}.csv 2>/dev/null
```

## Step 6: Verify and Report

```bash
# Verify files landed correctly
ls -la notebooks/updates/Portfolio_Positions_*.csv | tail -3
ls -la notebooks/updates/Dividend_Positions_*.csv | tail -3
ls -la notebooks/updates/Balances_for_Account_*.csv
```

The report format depends on the invocation mode (see `SKILL.md` → "Workflow Routing"). Use the mode the skill was invoked in; do not improvise a third variant.

### Mode A — Chained from E2E flow (default for "portfolio-sync")

When this workflow is running as the first half of the E2E chain, emit a single handoff line and **immediately continue into SyncPortfolio**. Do NOT print the full report, do NOT ask "Proceed?", do NOT wait for confirmation.

```
Ingest complete ({N} files moved, ~/Downloads/ cleaned). Chaining into SyncPortfolio ->
```

The full summary will appear at the end of SyncPortfolio, where it's actually useful (the positions are in the sheet by then).

### Mode B — Standalone ingest ("ingest positions" trigger)

When the user explicitly asked to ingest only (not sync), print the full report and stop. The user wants a breakpoint here to inspect files before writing to the sheet.

```
POSITION INGESTION COMPLETE - {date}
---

FILES MOVED:
  Regular View:  Portfolio_Positions_{date}.csv ✅
  Dividend View: Dividend_Positions_{date}.csv ✅
  Balances:      Balances_for_Account_{ACCOUNT_ID}.csv ✅

DOWNLOADS CLEANED:
  Removed {N} files from ~/Downloads/

NEXT STEPS (user's choice — do not auto-run):
  → "portfolio-sync" to push positions to Google Sheets
  → "sync dividends" to update Dividend Tracker
---
```

**Why the mode matters**: The historical version of this workflow always printed Mode B, which caused agents to stop and ask "Proceed?" even when the user had clearly asked for the full end-to-end flow. The fix is to let the trigger phrase decide — if the user said "portfolio-sync" or any E2E phrase, use Mode A. If they said "ingest positions", use Mode B.

## Edge Cases

### Only one positions file downloaded
- Classify it (regular or dividend) and move accordingly
- Report which view is missing

### Multiple dates in Downloads
- If `Portfolio_Positions_Mar-05-2026.csv` AND `Portfolio_Positions_Mar-06-2026.csv` exist:
  - Process only the **latest date** by default
  - Ask user if they want to import older files too

### File already exists in notebooks/updates/
- If `Portfolio_Positions_MMM-DD-YYYY.csv` already exists in destination:
  - Compare file sizes. If identical, skip with note.
  - If different, overwrite (newer download wins)

### No Balances file
- Proceed with positions only
- Warn: "Balances file not found in Downloads. SPAXX and Margin values won't update during sync."

## Error Handling

### File not found
```
No Fidelity CSV files found in ~/Downloads/.
Please download from Fidelity:
  1. Positions (regular view) — Portfolio tab → Download
  2. Positions (dividend view) — Portfolio tab → Dividend View → Download
  3. Balances — Balances tab → Download
```

### Cannot classify view type
```
WARNING: Could not determine if this is the regular or dividend view.
Header row: {first 100 chars of header}
Please confirm: Is this the [regular] or [dividend] view?
```

---

**Workflow Type**: Local file management
**Estimated Duration**: 5-10 seconds
**Dependencies**: CSV files in ~/Downloads/
**Chains to**: SyncPortfolio (for Google Sheets push)
