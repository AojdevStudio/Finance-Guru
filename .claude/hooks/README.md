# Hooks

Claude Code hooks that load the instance context, track edited files, and run the build check.

---

## What Are Hooks?

Hooks are scripts that run at specific points in Claude's workflow:
- **SessionStart**: When a session starts
- **PreToolUse**: Before a tool executes
- **PostToolUse**: After a tool completes
- **Stop**: When user requests to stop

**Key insight:** Hooks can modify prompts, block actions, and track state - enabling features Claude can't do alone.

---

## Essential Hooks (Start Here)

### post-tool-use-tracker (PostToolUse)

**Purpose:** Tracks file changes to maintain context across sessions

**How it works:**
1. Monitors Edit/Write/MultiEdit tool calls
2. Records which files were modified
3. Creates cache for context management
4. Auto-detects project structure (frontend, backend, packages, etc.)

**Why it's essential:** Helps Claude understand what parts of your codebase are active.

**Integration:**
```bash
# Copy file
cp post-tool-use-tracker.sh your-project/.claude/hooks/

# Make executable
chmod +x your-project/.claude/hooks/post-tool-use-tracker.sh
```

**Add to settings.json:**
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|MultiEdit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/post-tool-use-tracker.sh"
          }
        ]
      }
    ]
  }
}
```

**Customization:** ✅ None needed - auto-detects structure

---

## For Claude Code

**When setting up hooks for a user:**

1. **Read [CLAUDE_INTEGRATION_GUIDE.md](../../CLAUDE_INTEGRATION_GUIDE.md)** first
2. **Always start with the two essential hooks**
3. **Ask before adding Stop hooks** - they can block if misconfigured
4. **Verify after setup:**
   ```bash
   ls -la .claude/hooks/*.sh | grep rwx
   ```

**Questions?** See [CLAUDE_INTEGRATION_GUIDE.md](../../CLAUDE_INTEGRATION_GUIDE.md)
