# Hooks Configuration Guide

This guide explains how to configure and customize the hooks system for your project.

## Quick Start Configuration

### 1. Register Hooks in .claude/settings.json

Create or update `.claude/settings.json` in your project root:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bun run $CLAUDE_PROJECT_DIR/.claude/hooks/load-fin-core-config.ts"
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bun run $CLAUDE_PROJECT_DIR/.claude/hooks/skill-activation-prompt.ts"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|MultiEdit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "bun run $CLAUDE_PROJECT_DIR/.claude/hooks/post-tool-use-tracker.ts"
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/stop-build-check-enhanced.sh"
          },
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/error-handling-reminder.sh"
          }
        ]
      }
    ]
  }
}
```

### 2. Install Dependencies

```bash
cd .claude/hooks
npm install
```

### 3. Set Execute Permissions

Most hooks are now Bun TypeScript files invoked via `bun run` and do not need execute permissions. Only Stop hooks still use `.sh` files:

```bash
# Only needed for Stop hooks (stop-build-check-enhanced.sh, error-handling-reminder.sh)
chmod +x .claude/hooks/*.sh
```

## Customization Options

### Project Structure Detection

By default, hooks detect these directory patterns:

**Frontend:** `frontend/`, `client/`, `web/`, `app/`, `ui/`
**Backend:** `backend/`, `server/`, `api/`, `src/`, `services/`
**Database:** `database/`, `prisma/`, `migrations/`
**Monorepo:** `packages/*`, `examples/*`

#### Adding Custom Directory Patterns

Edit `.claude/hooks/post-tool-use-tracker.ts`, function `detectRepo()`:

```typescript
switch (firstDir) {
    // Add your custom directories here
    case 'my-custom-service':
    case 'admin-panel':
        return firstDir;
    // ... existing patterns
}
```

### Build Command Detection

The hooks auto-detect build commands based on:
1. Presence of `package.json` with "build" script
2. Package manager (pnpm > npm > yarn)
3. Special cases (Prisma schemas)

#### Customizing Build Commands

Edit `.claude/hooks/post-tool-use-tracker.ts`, function `getBuildCommand()`:

```typescript
// Add custom build logic at the top of getBuildCommand()
if (repo === 'my-service') {
    return `cd ${repoPath} && make build`;
}
```

### TypeScript Configuration

Hooks automatically detect:
- `tsconfig.json` for standard TypeScript projects
- `tsconfig.app.json` for Vite/React projects

#### Custom TypeScript Configs

Edit `.claude/hooks/post-tool-use-tracker.ts`, function `getTscCommand()`:

```typescript
// Add custom tsconfig logic at the top of getTscCommand()
if (repo === 'my-service') {
    return `cd ${repoPath} && npx tsc --project tsconfig.build.json --noEmit`;
}
```

### Prettier Configuration

The prettier hook searches for configs in this order:
1. Current file directory (walking upward)
2. Project root
3. Falls back to Prettier defaults

#### Custom Prettier Config Search

Edit `.claude/hooks/stop-prettier-formatter.sh`, function `get_prettier_config()`:

```bash
# Add custom config locations
if [[ -f "$project_root/config/.prettierrc" ]]; then
    echo "$project_root/config/.prettierrc"
    return
fi
```

### Error Handling Reminders

Configure file category detection in `.claude/hooks/error-handling-reminder.ts`:

```typescript
function getFileCategory(filePath: string): 'backend' | 'frontend' | 'database' | 'other' {
    // Add custom patterns
    if (filePath.includes('/my-custom-dir/')) return 'backend';
    // ... existing patterns
}
```

### Error Threshold Configuration

Change when to recommend the auto-error-resolver agent.

Edit `.claude/hooks/stop-build-check-enhanced.sh`:

```bash
# Default is 5 errors - change to your preference
if [[ $total_errors -ge 10 ]]; then  # Now requires 10+ errors
    # Recommend agent
fi
```

## Environment Variables

### Global Environment Variables

Set in your shell profile (`.bashrc`, `.zshrc`, etc.):

```bash
# Disable error handling reminders
export SKIP_ERROR_REMINDER=1

# Custom project directory (if not using default)
export CLAUDE_PROJECT_DIR=/path/to/your/project
```

### Per-Session Environment Variables

Set before starting Claude Code:

```bash
SKIP_ERROR_REMINDER=1 claude-code
```

## Hook Execution Order

Stop hooks run in the order specified in `settings.json`:

```json
"Stop": [
  {
    "hooks": [
      { "command": "...formatter.sh" },    // Runs FIRST
      { "command": "...build-check.sh" },  // Runs SECOND
      { "command": "...reminder.sh" }      // Runs THIRD
    ]
  }
]
```

**Why this order matters:**
1. Format files first (clean code)
2. Then check for errors
3. Finally show reminders

## Selective Hook Enabling

You don't need all hooks. Choose what works for your project:

### Minimal Setup (Skill Activation Only)

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bun run $CLAUDE_PROJECT_DIR/.claude/hooks/skill-activation-prompt.ts"
          }
        ]
      }
    ]
  }
}
```

### Build Checking Only (No Formatting)

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|MultiEdit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "bun run $CLAUDE_PROJECT_DIR/.claude/hooks/post-tool-use-tracker.ts"
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/stop-build-check-enhanced.sh"
          }
        ]
      }
    ]
  }
}
```

### Formatting Only (No Build Checking)

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|MultiEdit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "bun run $CLAUDE_PROJECT_DIR/.claude/hooks/post-tool-use-tracker.ts"
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/stop-prettier-formatter.sh"
          }
        ]
      }
    ]
  }
}
```

## Cache Management

### Cache Location

```
$CLAUDE_PROJECT_DIR/.claude/tsc-cache/[session_id]/
```

### Manual Cache Cleanup

```bash
# Remove all cached data
rm -rf $CLAUDE_PROJECT_DIR/.claude/tsc-cache/*

# Remove specific session
rm -rf $CLAUDE_PROJECT_DIR/.claude/tsc-cache/[session-id]
```

### Automatic Cleanup

The build-check hook automatically cleans up session cache on successful builds.

## Troubleshooting Configuration

### Hook Not Executing

1. **Check registration:** Verify hook is in `.claude/settings.json`
2. **Check permissions:** Run `chmod +x .claude/hooks/*.sh`
3. **Check path:** Ensure `$CLAUDE_PROJECT_DIR` is set correctly
4. **Check TypeScript:** Run `cd .claude/hooks && npx tsc` to check for errors

### False Positive Detections

**Issue:** Hook triggers for files it shouldn't

**Solution:** Add skip conditions in the relevant hook:

```typescript
// In post-tool-use-tracker.ts, inside processHook()
if (filePath.includes('/generated/')) {
    process.exit(0); // Skip generated files
}
```

### Performance Issues

**Issue:** Hooks are slow

**Solutions:**
1. Limit TypeScript checks to changed files only
2. Use faster package managers (pnpm > npm)
3. Add more skip conditions
4. Disable Prettier for large files

```bash
# Skip large files in stop-prettier-formatter.sh
file_size=$(wc -c < "$file" 2>/dev/null || echo 0)
if [[ $file_size -gt 100000 ]]; then  # Skip files > 100KB
    continue
fi
```

### Debugging Hooks

Add debug output to any hook:

```bash
# At the top of the hook script
set -x  # Enable debug mode

# Or add specific debug lines
echo "DEBUG: file_path=$file_path" >&2
echo "DEBUG: repo=$repo" >&2
```

View hook execution in Claude Code's logs.

## Advanced Configuration

### Custom Hook Event Handlers

You can create your own hooks for other events:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/my-custom-bash-guard.sh"
          }
        ]
      }
    ]
  }
}
```

### Monorepo Configuration

For monorepos with multiple packages:

```typescript
// In post-tool-use-tracker.ts, detectRepo() switch statement
case 'packages': {
    const parts = relativePath.split('/');
    if (parts.length >= 2) {
        return `packages/${parts[1]}`;
    }
    return firstDir;
}
```

### Docker/Container Projects

If your build commands need to run in containers:

```typescript
// In post-tool-use-tracker.ts, getBuildCommand()
if (repo === 'api') {
    return 'docker-compose exec api npm run build';
}
```

## Best Practices

1. **Start minimal** - Enable hooks one at a time
2. **Test thoroughly** - Make changes and verify hooks work
3. **Document customizations** - Add comments to explain custom logic
4. **Version control** - Commit `.claude/` directory to git
5. **Team consistency** - Share configuration across team

## See Also

- [README.md](./README.md) - Hooks overview
- [../../docs/HOOKS_SYSTEM.md](../../docs/HOOKS_SYSTEM.md) - Complete hooks reference
- [../../docs/SKILLS_SYSTEM.md](../../docs/SKILLS_SYSTEM.md) - Skills integration
