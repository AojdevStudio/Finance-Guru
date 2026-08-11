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

# Existing hook? back it up if it isn't ours
if [[ -f "$HOOK_PATH" ]] && ! grep -q "compliance-scan/scripts/scan.py" "$HOOK_PATH"; then
    backup="$HOOK_PATH.backup.$(date +%s)"
    cp "$HOOK_PATH" "$backup"
    echo "compliance-scan: backed up existing pre-push hook to $backup" >&2
fi

cat > "$HOOK_PATH" <<'HOOK'
#!/usr/bin/env bash
# Auto-installed by compliance-scan/install-pre-push.sh
# Bypass for one-offs: git push --no-verify  (use sparingly and explain in commit message)

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
SCAN="$REPO_ROOT/.claude/skills/compliance-scan/scripts/scan.py"

if [[ ! -x "$SCAN" ]]; then
    echo "compliance-scan: scanner not executable; skipping (run install-pre-push.sh)" >&2
    exit 0
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
