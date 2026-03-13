# IngestTransactions Workflow

Ingest Fidelity transaction history CSV from Downloads into the local rolling archive. Detects date range (30d/60d), creates date-stamped copy, merges unique rows into Accounts_History.csv.

## Triggers

- "ingest transactions", "import history", "bring in transactions"
- User points to `~/Downloads/History_for_Account_Z05724592.csv`
- User mentions downloading transaction history from Fidelity

## Step 1: Locate Source File

**Default location**: `~/Downloads/History_for_Account_Z05724592.csv`
**Alternative**: User may specify a different path.

```bash
# Verify file exists
ls -la ~/Downloads/History_for_Account_Z05724592.csv
```

If not found, ask user for the file location.

## Step 2: Read and Analyze the CSV

**CSV Schema** (13 columns, header on row 3, rows 1-2 are blank):
```
Run Date, Action, Symbol, Description, Type, Price ($), Quantity,
Commission ($), Fees ($), Accrued Interest ($), Amount ($),
Cash Balance ($), Settlement Date
```

**Detect date range**:
```bash
# Extract earliest and latest dates from the CSV (skip header rows, skip footer disclaimer)
awk -F',' 'NR>2 && $1 ~ /^[0-9]/ {print $1}' "$SOURCE_FILE" | sort -t/ -k3,3n -k1,1n -k2,2n | head -1  # earliest
awk -F',' 'NR>2 && $1 ~ /^[0-9]/ {print $1}' "$SOURCE_FILE" | sort -t/ -k3,3n -k1,1n -k2,2n | tail -1  # latest
```

**Classify period**:
- Calculate days between earliest and latest date
- <= 35 days = `30d`
- <= 65 days = `60d`
- > 65 days = `{N}d` (use actual count)

**Count transaction rows** (exclude blank lines and Fidelity disclaimer footer):
```bash
awk -F',' 'NR>2 && $1 ~ /^[0-9]/ {count++} END {print count}' "$SOURCE_FILE"
```

## Step 3: Copy with Date-Stamped Name

**Destination**: `notebooks/transactions/`

**Naming convention**: `History_for_Account_Z05724592_{YYYY-MM-DD}_{period}.csv`

Where:
- `{YYYY-MM-DD}` = the download/run date (latest date in file, or today's date)
- `{period}` = `30d`, `60d`, or `{N}d`

**Example**: `History_for_Account_Z05724592_2026-03-06_60d.csv`

```bash
cp ~/Downloads/History_for_Account_Z05724592.csv \
   notebooks/transactions/History_for_Account_Z05724592_2026-03-06_60d.csv
```

## Step 4: Merge into Accounts_History.csv

**Master archive**: `notebooks/transactions/Accounts_History.csv`

### Schema Normalization

The master archive may have a 14-column legacy schema (with Account, Account Number columns). New Fidelity downloads use a 13-column schema. Normalize as follows:

**Canonical 13-column schema** (used going forward):
```
Run Date, Action, Symbol, Description, Type, Price ($), Quantity,
Commission ($), Fees ($), Accrued Interest ($), Amount ($),
Cash Balance ($), Settlement Date
```

If the existing Accounts_History.csv has 14 columns (Account, Account Number after Run Date), strip those columns during merge. New rows always use 13-column format.

### Deduplication

Match on: `Run Date + Action + Amount($)`

```python
# Pseudocode for merge logic
existing_keys = set()
for row in accounts_history:
    key = f"{row['Run Date']}|{row['Action'][:60]}|{row['Amount ($)']}"
    existing_keys.add(key)

new_rows = []
for row in new_csv:
    key = f"{row['Run Date']}|{row['Action'][:60]}|{row['Amount ($)']}"
    if key not in existing_keys:
        new_rows.append(row)
```

### Merge Strategy

1. Read all data rows from Accounts_History.csv (skip header, skip footer disclaimer)
2. Read all data rows from new CSV (skip blank rows 1-2, skip header row 3, skip footer)
3. Deduplicate using key above
4. Combine: existing rows + new unique rows
5. Sort by Run Date descending (newest first)
6. Write back with single header row + combined data (NO footer disclaimer)

### Handle Missing Archive

If `Accounts_History.csv` doesn't exist:
- Copy the new CSV as the initial archive
- Strip blank rows and footer disclaimer
- Add proper header row

## Step 5: Update notebooks/updates/ Copy

After merging, also update `notebooks/updates/History_for_Account_Z05724592.csv` with the latest download so other skills (dividend-tracking, etc.) can reference it:

```bash
cp ~/Downloads/History_for_Account_Z05724592.csv \
   notebooks/updates/History_for_Account_Z05724592.csv
```

## Step 6: Extract Dividend Summary

From the newly ingested transactions, extract all `DIVIDEND RECEIVED` entries and report:

```
DIVIDEND INCOME (from this import)
Date       | Symbol | Amount  | Type
03/06/2026 | AMZY   | $3.61   | Cash
03/06/2026 | AMZY   | $14.82  | Margin
...
TOTAL: $XXX.XX
```

This data supplements (not replaces) the dividends.csv forward-looking projections.

## Step 7: Generate Ingestion Report

```
TRANSACTION INGESTION COMPLETE - {date}
---

SOURCE: ~/Downloads/History_for_Account_Z05724592.csv
PERIOD: {earliest_date} to {latest_date} ({N}d)
ARCHIVED AS: History_for_Account_Z05724592_{date}_{period}.csv

MERGE RESULTS:
  New rows added to Accounts_History: XX
  Duplicates skipped: XX
  Archive now covers: {earliest_archive_date} to {latest_archive_date}
  Total archive rows: XX

TRANSACTION BREAKDOWN:
  Dividends received:  $XXX.XX (XX entries)
  Reinvestments:       $XXX.XX (XX entries)
  Direct deposits:     +$X,XXX.XX (XX entries)
  Debit card:          -$X,XXX.XX (XX entries)
  Margin interest:     -$XX.XX (XX entries)
  Other:               $XXX.XX (XX entries)

NEXT STEPS:
  -> Run "sync transactions" to push to Google Sheets
  -> Run "sync dividends" to update Dividend Tracker
---
```

## Gap Detection

After merge, check for date gaps > 3 business days in the archive. Report any gaps:

```
GAP ALERT: No transactions between {date1} and {date2} ({N} business days)
This may indicate a missing export period. Consider downloading that range.
```

## Error Handling

### File not found
```
Source file not found at ~/Downloads/History_for_Account_Z05724592.csv
Please download your transaction history from Fidelity (last 30 or 60 days).
```

### Schema mismatch
```
WARNING: CSV schema doesn't match expected Fidelity format.
Expected 13 columns: Run Date, Action, Symbol, ...
Found: {N} columns
Please verify this is a Fidelity History export.
```

### Duplicate archive name
If `History_for_Account_Z05724592_{date}_{period}.csv` already exists:
- Compare file sizes. If identical, skip copy.
- If different, append a counter: `..._2026-03-06_60d_2.csv`

---

**Workflow Type**: Local file management
**Estimated Duration**: 10-20 seconds
**Dependencies**: CSV file access, notebooks/transactions/ directory
**Chains to**: SyncTransactions (optional, for Google Sheets push)
