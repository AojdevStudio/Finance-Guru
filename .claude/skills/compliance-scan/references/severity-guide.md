# Severity decision guide

When the scanner returns findings, use this to decide what to do.

## CRITICAL — stop everything

A working secret is in the file. The leaked secret is worth more than the time it takes to rotate it — there is no "I'll fix it tomorrow" path here.

1. **Rotate the secret immediately** (see remediation hint per finding).
2. **Confirm the new secret works** (try one API call).
3. **Then** decide what to do with the file:
   - If the bad commit hasn't been pushed: `git reset --soft HEAD~1`, edit, re-stage, re-scan.
   - If it has been pushed: rotate is still your first step (the leaked one is dead). Then either let history stand (the value is already worthless) or run `git-filter-repo` to scrub history if compliance requires it.
4. **Do not** add the secret string to `pii-replacements.txt` — that file ships in the public repo. The whole point is the secret is dead.

## HIGH — block, fix, then push

Personal data or infrastructure URL. Doesn't grant access by itself but identifies the owner or hands an attacker reconnaissance.

1. Replace the value with a template variable (`{account_id}`, `{user_name}`) or pull it from env at runtime.
2. If the value should be redactable across history, add a `literal:` or `regex:` line to `scripts/qa/pii-replacements.txt`.
3. Re-stage and re-scan. Findings should drop to zero.

## MEDIUM — judgment call

Owner name in a file that's not on the allowlist.

- **Code, configs, distributed docs, plans-that-might-be-shared** → genericize.
- **Personal scratch (planning, memory, runbooks, vision docs)** → add the file to `ALLOWED_FILES` in `tests/python/test_no_hardcoded_references.py` with a one-line comment explaining why.

## INFO — clean up at your leisure

Hygiene findings. Won't block a push under default policy.

- `untracked-in-sensitive-path` — fastest fix is `--remediate gitignore`. Confirm the diff before committing.
- `privacy-md-not-in-gitignore` — either patch PRIVACY.md to remove the unenforceable claim, or add the missing pattern to `.gitignore`.

## When NOT to bypass with `--no-verify`

The pre-push hook can be bypassed: `git push --no-verify`. Do this only when:

- The finding is a confirmed false positive AND you've documented why in the commit message.
- The finding is a duplicate of something already known and tracked.

Bypassing because "it's annoying" is exactly how the next leak ships. If a pattern produces frequent false positives, fix the pattern (in `scan.py` or `pii-replacements.txt`) instead of bypassing.

## Escalation thresholds

| Findings | Action |
|----------|--------|
| 1 CRITICAL | Stop, rotate, then continue |
| ≥3 HIGH in one commit | Pause and review what changed — likely a config file with a lot of personal data slipped in |
| Repeated MEDIUM in same file across runs | Either genericize once or add to allowlist; don't keep re-scanning the same noise |
| INFO only | Address opportunistically, or use `--remediate gitignore` to bulk-fix |
