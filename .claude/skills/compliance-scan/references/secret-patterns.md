# Secret & PII pattern catalog

Reference for the patterns the scanner recognizes, why each is dangerous, and how to remediate when one fires.

## CRITICAL — credentials and tokens

A CRITICAL hit means a working secret is in the file. Treat the secret as compromised the moment it's logged anywhere outside your machine — git history, CI logs, screenshots.

| Rule | Example shape | Why critical | First action |
|------|---------------|--------------|--------------|
| `aws-access-key` | `AKIA...` (20 chars) | Direct IAM access | Disable in AWS IAM console immediately, then rotate |
| `github-pat-classic` | `ghp_<36 chars>` | Repo write, possibly org admin | Revoke at github.com/settings/tokens |
| `github-pat-fine-grained` | `github_pat_<82 chars>` | Scoped repo access | Revoke at github.com/settings/personal-access-tokens |
| `github-server-token` | `ghs_<36 chars>` | Server-to-server auth | Revoke and reissue from the GitHub App |
| `anthropic-key` | `sk-ant-<40+ chars>` | Bills your Anthropic account | Rotate at console.anthropic.com |
| `openai-key` | `sk-proj-...` or `sk-<48 chars>` | Bills your OpenAI account | Rotate at platform.openai.com |
| `slack-bot-token` | `xoxb-<digits>-<digits>-<chars>` | Bot can post/read messages | Rotate at api.slack.com/apps |
| `slack-user-token` | `xoxp-<digits>-<digits>-<digits>-<hex>` | Acts as the user | Rotate immediately; tokens with this prefix are very high-trust |
| `google-api-key` | `AIza<35 chars>` | Bills your GCP project | Rotate in GCP Console > Credentials, restrict by referrer/IP |
| `private-key-pem` | `-----BEGIN ... PRIVATE KEY-----` | Identity / signing key | Treat the key as compromised, regenerate the keypair |
| `jwt-token` | `eyJ...eyJ...sig` | Active session/auth | Invalidate the session and rotate the signing secret |
| `bright-data-token` | 64 lowercase hex chars | Proxy/scraping credit | Rotate at brightdata.com (matches their format) |

### After rotating

- Drop the local commit (if not yet pushed): `git reset --soft HEAD~1` then re-stage with the secret replaced.
- If the secret made it to a pushed commit, you also need history rewrite — see `.planning/phases/01-git-history-scrub-security-foundation/` for the `git-filter-repo` workflow. Force-push afterward and notify anyone who has cloned.

## HIGH — PII and infrastructure URLs

A HIGH hit means data that identifies the owner, exposes infrastructure, or breaks PRIVACY.md is in the file. Not necessarily a working secret, but reaches GitHub it stays forever.

| Rule | Example | Why high | Fix |
|------|---------|----------|-----|
| `fidelity-account` | `Z00000000` (matches `Z0\d{7,}`) | Account number ID | Replace with `{account_id}` template variable |
| `ssn` | `NNN-NN-NNNN` | Identity / financial | Move to env, never commit |
| `apps-script-dispatcher` | `https://script.google.com/macros/s/.../exec` | Live deploy URL — anyone with it can invoke the script | Move URL to `.env`; reference via env var |
| `google-script-deployment-id` | `AKfyc...` (~55 chars) | Apps Script deploy ID | Same as above — env var only |

### Plus everything in `scripts/qa/pii-replacements.txt`

That file is the canonical PII map for this repo (account numbers, employer names, LLC names, owner email, business domains, etc.). The scanner loads it dynamically — keep it up to date as the source of truth.

When you add a new PII pattern, add it there (with both `literal:` and `regex:` forms when useful) and the scanner will pick it up on next run with no code change.

## MEDIUM — owner name in non-allowed location

The existing `tests/python/test_no_hardcoded_references.py` defines an `ALLOWED_FILES` set for places the owner's name is allowed (LICENSE, planning docs, gitignored notebooks, etc.). A hit outside that set is MEDIUM:

- Decide: should the file be genericized (use `{user_name}` template) or added to `ALLOWED_FILES` with a justification comment?
- Generic distributed code → genericize.
- Personal docs that will never be distributed (planning, memory, runbooks) → add to `ALLOWED_FILES`.

## INFO — hygiene and drift

- `untracked-in-sensitive-path` — A new file appeared in `.claude/skills/`, `notebooks/`, `fin-guru-private/`, etc., and isn't gitignored. Run with `--remediate gitignore` to auto-add the appropriate ignore line. Confirm the diff before committing the gitignore change.
- `privacy-md-not-in-gitignore` — PRIVACY.md claims a path "never leaves your machine" but `.gitignore` doesn't actually shield it. Either tighten the gitignore or update PRIVACY.md to match reality.

## Adding a new pattern

1. **PII you know the literal/regex form of:** add it to `scripts/qa/pii-replacements.txt` (HIGH severity, picked up automatically).
2. **A new credential format:** edit `CRITICAL_PATTERNS` in `.claude/skills/compliance-scan/scripts/scan.py`. Include the rotation URL in the remediation hint.
3. **A new sensitive path prefix:** edit `SENSITIVE_PATH_PREFIXES` in the same file.

After any addition, run `--scope tree` once and verify no new false positives.

## Known false-positive triggers

The 64-hex Bright Data pattern can collide with content hashes (sha256 hex). When it fires, check whether the line is a hash literal (e.g., a lockfile entry, a fingerprint) or an actual token. Lockfiles are excluded by extension already, but other formats may need `should_skip` updates if false positives become noisy.

## What this catalog deliberately does not cover

- **Heuristic entropy detection** (à la `truffleHog`'s entropy mode). Too noisy without tuning; we prefer named patterns with crisp remediation guidance.
- **Vulnerability/CVE scanning.** Use `uv run pip-audit` for Python deps and `npm audit` for the JS workspaces.
- **Dependency provenance.** Out of scope.
