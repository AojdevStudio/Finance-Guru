#!/usr/bin/env bash
# Install the compliance-scan pre-push hook for this clone.
# Idempotent: re-running will replace the hook with the latest version.

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
HOOK_DIR="$REPO_ROOT/.git/hooks"
HOOK_PATH="$HOOK_DIR/pre-push"
SCAN_PATH=".claude/skills/compliance-scan/scripts/scan.py"

if [[ ! -d "$HOOK_DIR" ]]; then
    echo "compliance-scan: not in a git repo (no $HOOK_DIR)" >&2
    exit 1
fi

if [[ ! -f "$REPO_ROOT/$SCAN_PATH" ]]; then
    echo "compliance-scan: scanner missing at $SCAN_PATH" >&2
    exit 1
fi

if [[ ! -f "$REPO_ROOT/.review-gate" ]]; then
    echo "compliance-scan: no .review-gate at the repo root; the installed hook will skip the review gate until one exists." >&2
fi

# Existing hook? back it up if it isn't ours
if [[ -f "$HOOK_PATH" ]] && ! grep -q "compliance-scan/scripts/scan.py" "$HOOK_PATH"; then
    backup="$HOOK_PATH.backup.$(date +%s)"
    cp "$HOOK_PATH" "$backup"
    echo "compliance-scan: backed up existing pre-push hook to $backup" >&2
fi

cat > "$HOOK_PATH" <<'HOOK'
#!/usr/bin/env bash
# Auto-installed by compliance-scan/install-pre-push.sh
# Privacy-scan bypass for one-offs: git push --no-verify (explain in the commit message).
# The review gate below has its own switch, REVIEW_GATE_OFF=1, and only Ossie sets it.

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
SCAN="$REPO_ROOT/.claude/skills/compliance-scan/scripts/scan.py"

if [[ ! -x "$SCAN" ]]; then
    echo "compliance-scan: scanner not executable; skipping (run install-pre-push.sh)" >&2
    exit 0
fi

# argparse exits 2 for an unknown scope: a worktree on an older base has a
# scanner that predates --scope history. Degrade to the push scope that base
# already had, never misreport a version gap as a disclosure.
HISTORY_RC=0
"$SCAN" --scope history --skip-existing-tests || HISTORY_RC=$?
if [[ "$HISTORY_RC" -eq 2 ]]; then
    echo "compliance-scan: this checkout's scanner lacks --scope history; push scope only." >&2
elif [[ "$HISTORY_RC" -ne 0 ]]; then
    echo "" >&2
    echo "compliance-scan: BLOCKED push, a commit in this range discloses private data." >&2
    echo "  Removing it in a later commit does not help. The diff still publishes it." >&2
    echo "  Rebuild the branch from origin/main so no commit ever contained it." >&2
    exit 1
fi

if ! "$SCAN" --scope push --skip-existing-tests; then
    echo "" >&2
    echo "compliance-scan: BLOCKED push due to findings above." >&2
    echo "  - Fix the findings, OR" >&2
    echo "  - Bypass with: git push --no-verify  (and justify in your commit message)" >&2
    exit 1
fi

# Standing-exposure warning. The blocking scan above only sees what this push
# adds, so it is structurally blind to anything already committed. That blind
# spot let two PII files sit on the public remote for six months (2026-02-04 to
# 2026-08-11) while every push passed clean.
#
# Deliberately NON-blocking: a repo with pre-existing findings would otherwise
# be unpushable, and an unpushable hook just teaches everyone --no-verify. This
# reports and gets out of the way. Clear the backlog with:
#   .claude/skills/compliance-scan/scripts/scan.py --scope tree
# MEDIUM and INFO findings are report-only, so the scanner exits 0 while still
# returning them. Inspect the JSON on every exit status, not just failure, or
# the hook stays blind to the exact class it exists to surface. Status 2 means
# the scanner itself errored (e.g. no pattern source); say so, still don't block.
TREE_STATUS=0
TREE_OUT="$("$SCAN" --scope tree --skip-existing-tests --format json 2>/dev/null)" || TREE_STATUS=$?
COUNT="$(printf '%s' "$TREE_OUT" | grep -o '"severity"' | wc -l | tr -d ' ')" || COUNT=0
if [[ "${COUNT:-0}" -gt 0 ]]; then
    echo "" >&2
    echo "compliance-scan: NOTE — $COUNT standing finding(s) already in the tree." >&2
    echo "  This push is clean; the repo is not. Audit with:" >&2
    echo "    $SCAN --scope tree" >&2
    echo "  (not blocking)" >&2
elif [[ "$TREE_STATUS" -ne 0 ]]; then
    echo "" >&2
    echo "compliance-scan: WARNING — tree scan failed with status $TREE_STATUS." >&2
    echo "  Audit with: $SCAN --scope tree" >&2
    echo "  (not blocking)" >&2
fi

# Review gate (repo rule, 2026-09-20): the CI-equivalent checks plus a second-model
# diff review recorded for this exact HEAD (skill: ~/.agents/skills/review-gate).
# Without the skills store the checks run alone. Runs after the privacy scans so a
# disclosure is reported before any test time is spent.
GATE="$HOME/.agents/skills/review-gate/scripts/review-receipt.ts"
if [[ -f "$GATE" ]] && command -v bun >/dev/null 2>&1; then
    exec bun "$GATE" gate
fi
# No store: run the same check list the gate would (one command per line in .review-gate).
# Each check reads from /dev/null so it cannot swallow the rest of the list from the pipe.
if [[ -f "$REPO_ROOT/.review-gate" ]]; then
    checks="$(grep -v '^[[:space:]]*#' "$REPO_ROOT/.review-gate" | grep -v '^[[:space:]]*$' || true)"
    [[ -n "$checks" ]] || { echo "review-gate: .review-gate lists no checks; push blocked." >&2; exit 1; }
    printf '%s\n' "$checks" | while IFS= read -r check; do
        [[ -n "$check" ]] || continue
        echo "review-gate: running '$check'"
        (cd "$REPO_ROOT" && bash -c "$check" </dev/null) || { echo "review-gate: '$check' failed; push blocked." >&2; exit 1; }
    done
else
    echo "review-gate: no .review-gate at the repo root; review gate skipped." >&2
fi
HOOK

chmod +x "$HOOK_PATH"
chmod +x "$REPO_ROOT/$SCAN_PATH"

echo "compliance-scan: pre-push hook installed at $HOOK_PATH"
echo "compliance-scan: scanner ready at $SCAN_PATH"
echo ""
echo "Test it:"
echo "  $SCAN_PATH --scope tree"
echo ""
echo "Bypass when needed (rare):"
echo "  git push --no-verify"
