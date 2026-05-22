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
