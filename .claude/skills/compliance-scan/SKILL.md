---
name: compliance-scan
description: Privacy and security compliance scanner for the Finance Guru repo. Catches API tokens, account numbers, dispatcher URLs, owner-name leaks, untracked sensitive files, and gitignore gaps before they reach GitHub. Use this skill whenever the user says "compliance scan", "is this safe to push", "scan for PII", "secrets check", "pre-commit security", "pre-push security", "check for leaks", "PRIVACY.md compliance", "audit privacy", "any leaks", "check before push", or wants a sanity check before `git push`. Also run it proactively after editing PRIVACY.md, after creating any new file under `.claude/skills/`, `notebooks/`, `fin-guru-private/`, or `scripts/qa/`, and any time the user adds a new credential, deploy URL, or webhook. Privacy and security are non-negotiable in this repo — when in doubt, run it.
---

# Compliance Scan

The repo's last line of defense before something compromising hits GitHub. Layered scanner that runs the existing privacy tests, looks for new patterns of leakage, and (optionally) wires itself into `git push` so a failed scan blocks the push.

## When to invoke

Trigger on any of these phrases — and proactively before any push that touches `.claude/skills/`, `scripts/qa/`, `PRIVACY.md`, `.gitignore`, `notebooks/`, or `fin-guru/data/`:

- "compliance scan", "is this safe to push", "scan for PII", "secrets check"
- "pre-commit security", "pre-push security", "check for leaks", "check before I push"
- "PRIVACY.md compliance", "audit privacy", "any leaks?"
- After adding a new credential, deploy URL, dispatcher URL, webhook, or API key

## What it checks (six layers)

| # | Layer | Owner |
|---|-------|-------|
| 1 | Owner-name leak detector | reuses `tests/python/test_no_hardcoded_references.py` |
| 2 | Gitignore-coverage integration test | reuses `tests/integration/test_gitignore_protection.sh` |
| 3 | CRITICAL secret patterns (AWS/GitHub/Anthropic/OpenAI/Slack/JWT/private-key/Google API) | `scripts/scan.py` |
| 4 | HIGH PII patterns (account numbers, dispatcher URLs, SSNs, owner email) — sourced from `scripts/qa/pii-replacements.txt` plus built-ins | `scripts/scan.py` |
| 5 | Untracked files in sensitive paths (`.claude/skills/`, `notebooks/`, `fin-guru-private/`, `.env*`) | `scripts/scan.py` |
| 6 | PRIVACY.md "never leaves your machine" alignment with `.gitignore` | `scripts/scan.py` |

## Severity gate

Default policy:

| Severity | Examples | Behaviour |
|----------|----------|-----------|
| CRITICAL | API tokens, private keys, AWS access keys | **fail** — exit 1, block push |
| HIGH | Account numbers, dispatcher URLs, SSNs, owner email | **fail** — exit 1, block push |
| MEDIUM | Owner first/last name in non-allowed file | report — does not fail |
| INFO | Untracked file in sensitive path, PRIVACY/.gitignore drift | report — does not fail |

Override with `--fail-on CRITICAL` for "secrets only" mode or `--fail-on INFO` for the strictest posture.

## How to run

### One-shot scan of staged changes (default before `git commit`)

```bash
.claude/skills/compliance-scan/scripts/scan.py --scope staged
```

### Scan everything that's about to be pushed

```bash
.claude/skills/compliance-scan/scripts/scan.py --scope push
```

### Full working-tree audit (slower but comprehensive)

```bash
.claude/skills/compliance-scan/scripts/scan.py --scope tree
```

### Auto-add gitignore lines for any sensitive untracked files found

```bash
.claude/skills/compliance-scan/scripts/scan.py --scope tree --remediate gitignore
```

The remediation flag is conservative: it only touches `.gitignore`, only appends to it, and only for paths that match a known-sensitive prefix (`.claude/skills/`, `notebooks/`, `fin-guru-private/`, `.env*`). Idempotent — re-running won't create duplicate entries.

### Output formats

```bash
--format text   # default, human-readable
--format json   # machine-readable; pipe to jq
--format md     # markdown report (use for PR descriptions)
```

## Pre-push hook installation

Install once per clone:

```bash
.claude/skills/compliance-scan/scripts/install-pre-push.sh
```

This drops a `.git/hooks/pre-push` that runs `--scope push`. Failed scans block the push. Bypass for a one-off (you'll be asked why) with `git push --no-verify` — but this should be rare and called out in the commit message.

The hook is local to your clone (git hooks are not versioned). Re-run the installer after `git clone` on a new machine. The installer is idempotent.

## Allowlist for accepted exceptions

Some PII is deliberately committed (e.g., a golden test fixture captured from a real production run). Suppress these via `.claude/skills/compliance-scan/allowlist.json`:

```json
{
  "allow": [
    {
      "path": "tests/python/fixtures/fidelity_history_golden_expected.json",
      "reason": "Golden test fixture captured from real Fidelity history import",
      "approved_by": "ossie",
      "date": "2026-05-16"
    }
  ]
}
```

`path` is a fnmatch glob (`tests/**/golden_*.json` works). Matching files skip ALL pattern scans. Every entry needs a reason, an approver, and a date — that's the audit trail. Don't allowlist a path unless the value being shielded is genuinely meant to stay committed; for "I'll fix it later" use the private-fixture pattern instead (see `references/test-pii-pattern.md`).

## Auto-remediation behavior (gitignore only)

When `--remediate gitignore` is set, for each untracked file found in a sensitive path that is **not** currently gitignored, the scanner:

1. Identifies the smallest containing directory that's a sensible ignore unit (the immediate parent under `.claude/skills/`, the file itself for `.env*`, etc.)
2. Appends `<path>/` to `.gitignore` under a `# Compliance scan auto-remediation` block, creating the block if absent
3. Re-runs `git check-ignore` to verify the path is now shielded
4. Reports what was added so you can review the diff

The scanner never deletes, redacts, or rewrites files containing detected secrets — that's your call. It only silences future commits of paths that should already be private.

## Decision tree for the agent invoking this skill

```
User intent: "is this safe to push?" / "compliance scan"
│
├─ Has uncommitted work?
│   ├─ Yes → run --scope staged first; if clean, also run --scope tree to catch untracked files
│   └─ No  → run --scope push
│
├─ Findings of severity ≥ HIGH?
│   ├─ Yes → STOP. Show the findings. Do NOT auto-fix CRITICAL/HIGH (those need human judgment).
│   │       Suggest:
│   │         - For CRITICAL: rotate the leaked secret, then either drop the commit or rewrite history (heavy hammer — confirm explicitly).
│   │         - For HIGH: replace with template variable / env var / placeholder; re-stage; re-scan.
│   └─ No  → continue
│
├─ INFO finding "untracked sensitive path"?
│   ├─ Yes → Confirm with user: "Add `<path>/` to .gitignore?"
│   │       On yes, re-run with --remediate gitignore.
│   └─ No  → done
│
└─ Report PASS with the verdict line from the scanner output
```

## Layer 1 + 2 detail

Layers 1 and 2 are the existing tests. The scanner shells out to them as a single orchestration step:

```bash
uv run pytest tests/python/test_no_hardcoded_references.py -q --no-cov
bash tests/integration/test_gitignore_protection.sh
```

If those tests change shape (e.g., new fixtures), the scanner picks up the change automatically — no skill update required.

## Layer 3 + 4 pattern catalog

See `references/secret-patterns.md` for the full list of detected patterns, why each matters, and how to remediate when one fires.

## Layer 5 sensitive-path map

Currently shielded prefixes (extend in `scripts/scan.py:SENSITIVE_PATH_PREFIXES`):

- `.claude/skills/apps-script-run/` and any other skill with `apps-script`, `dispatcher`, or `webhook` in the name
- `notebooks/` (entire tree — financial CSVs)
- `fin-guru/data/` (except whitelisted methodology files)
- `fin-guru-private/`
- `.env`, `.env.*`, `*.env`
- `credentials/`, `private/`, `sensitive/`
- `*.key`, `*.pem`

## Layer 6 PRIVACY.md alignment

Reads PRIVACY.md, finds the "What never leaves your machine" section, extracts each bullet, and verifies the corresponding pattern is in `.gitignore`. Misalignment is INFO severity and lists the missing pattern.

## What this skill is NOT

- Not a git-history scrubber. For history rewrites use `scripts/qa/pii-replacements.txt` with `git-filter-repo` (a separate, destructive workflow documented in `.planning/phases/01-git-history-scrub-security-foundation/`).
- Not a vulnerability scanner. For dependency CVEs run `uv run pip-audit`.
- Not a secret rotator. When CRITICAL fires, you rotate the secret out-of-band — the scanner won't help with that.

## Files in this skill

- `SKILL.md` — this file
- `scripts/scan.py` — Python 3 scanner; no third-party deps; runnable as `./scan.py`
- `scripts/install-pre-push.sh` — idempotent installer for the git hook
- `references/secret-patterns.md` — full pattern catalog with remediation guidance
- `references/severity-guide.md` — when to escalate, when to ignore
