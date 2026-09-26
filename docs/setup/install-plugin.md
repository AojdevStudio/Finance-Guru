# Install the Finance Guru plugin

## Add the marketplace

```bash
claude plugin marketplace add AojdevStudio/Finance-Guru
```

## Install the plugin

```bash
claude plugin install finance-guru@finance-guru
```

## Confirm the installation

```bash
claude plugin list
```

Confirm that the 11 specialist agents load. Run this from any directory:

```bash
claude -p "ok" --output-format stream-json --verbose --max-turns 1 </dev/null \
  | head -1 | jq '[.agents[] | select(startswith("finance-guru:"))]'
```

The output lists `finance-guru:fg-builder` through `finance-guru:fg-teaching-specialist`. Use this check, not `claude plugin details finance-guru`, which reports `Agents (0)` for this plugin even though every agent loads.

## Start onboarding

```bash
claude
```

```text
/finance-guru:instance-onboarding
```

## Start the first instance session

```bash
cd "<instance-root>"
claude
```
