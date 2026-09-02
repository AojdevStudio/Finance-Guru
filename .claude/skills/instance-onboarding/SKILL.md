---
name: instance-onboarding
description: Scaffold a private Finance Guru instance, complete its profile, add a broker CSV, and perform the first local database readout. Use after installing the finance-guru plugin.
---

# Finance Guru instance onboarding

Create a local instance that keeps private values and financial files outside the public engine checkout. Run commands for the user, pausing before any step that needs a path or private input.

## 1. Choose the instance root

Ask for an absolute local directory dedicated to this Finance Guru instance. Do not suggest a shared, cloud-synced, or engine-repository directory.

Confirm that `${CLAUDE_PLUGIN_ROOT}` is set and names the installed Finance Guru plugin. If it is missing, stop and tell the user to install and invoke `finance-guru@finance-guru` from Claude Code before retrying.

## 2. Scaffold the instance

Run the initializer from the plugin root:

```bash
(
  cd "${CLAUDE_PLUGIN_ROOT}"
  uv run python -m src.cli.instance_init "<instance-root>" --repo "${CLAUDE_PLUGIN_ROOT}"
)
```

The initializer is convergent: it preserves existing files, initializes local-only git history, creates the uv environment, and links both Claude Code and Codex to the plugin's single `.claude` skill tree.

## 3. Complete the profile

Open `<instance-root>/user-profile.yaml` and walk through each empty section one at a time. Explain why a requested field is useful before asking for it. Never copy profile values into the plugin checkout, chat output, examples, or tracked documentation.

At minimum, confirm the user's objectives, time horizon, risk tolerance, liquidity needs, account types, and workflow preferences. Preserve any existing keys and values.

## 4. Add the first broker CSV

Ask the user for the path to a broker-exported CSV, inspect only its header to identify the export type, and copy the original file into the instance import directory:

```bash
cp "<broker-export.csv>" "<instance-root>/imports/"
```

CSV files are the first-hour onboarding path and remain local. SnapTrade and SimpleFIN are optional bring-your-own-credentials integrations; do not require either service to finish onboarding.

## 5. Start from the instance

Tell the user to start every future Finance Guru session from the instance so cwd resolves all private paths:

```bash
cd "<instance-root>"
claude
```

Codex uses the same starting directory and discovers the same skills through `<instance-root>/.agents/skills/`.

## 6. Show the local snapshot

From the instance directory, run the first readout:

```bash
uv run python -m src.integrations.refresh_all --show
```

An empty snapshot is expected before a supported CSV workflow imports records or optional live credentials are configured. If the command fails, show the exact error and stop; never imply that data refreshed successfully.

Finish by naming the instance path, whether a CSV was added, whether the profile is complete, and the observed `refresh_all --show` result. Do not echo the CSV filename, profile values, or CSV rows.

---

_Educational purposes only. Not investment advice. Financial data can be incomplete or inaccurate, and loss of principal is possible. Consult licensed financial, tax, and legal professionals before acting._
