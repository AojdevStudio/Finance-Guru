---
title: "Hooks System Documentation"
description: "How Claude Code hooks enable automatic context loading and skill activation"
category: reference
---

# Hooks System Documentation

Finance Guru uses Claude Code hooks to enable automatic context loading, skill activation, and validation. This document explains how the hooks system works and how to customize it.

## Overview

Hooks are scripts that run at specific points in Claude's workflow:

| Hook Type | When It Runs | Purpose |
|-----------|--------------|---------|
| **SessionStart** | When session begins | Load context, initialize state |
| **UserPromptSubmit** | When user submits prompt | Suggest skills, modify context |
| **PreToolUse** | Before tool executes | Validate, gate actions |
| **PostToolUse** | After tool completes | Track changes, update state |
| **Stop** | When stop requested | Validate, cleanup |

## Current Hook Configuration

Located in `.claude/settings.json`:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "npx tsx $CLAUDE_PROJECT_DIR/.claude/hooks/load-fin-core-config.ts"
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/skill-activation-prompt.sh"
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
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/post-tool-use-tracker.sh"
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

---

## SessionStart: load-fin-core-config.ts

**Purpose**: Loads Finance Guru context at session start.

**Location**: `.claude/hooks/load-fin-core-config.ts`

### What It Loads

1. **fin-core skill** (`.claude/skills/fin-core/SKILL.md`)
   - Core Finance Guru knowledge
   - Agent routing rules
   - Compliance requirements

2. **System configuration** (`fin-guru/config.yaml`)
   - Agent roster (13 agents)
   - Task definitions (21 tasks)
   - Tool integrations
   - Workflow pipeline

3. **User profile** (`fin-guru/data/user-profile.yaml`)
   - Portfolio structure
   - Risk tolerance (aggressive)
   - Investment strategy
   - Current holdings

4. **System context** (`fin-guru/data/system-context.md`)
   - Repository structure
   - Privacy rules
   - Agent team overview

5. **Latest portfolio data** (`notebooks/updates/`)
   - `Balances_for_Account_{account_id}.csv` - Account balances, margin data
   - `Portfolio_Positions_MMM-DD-YYYY.csv` - Current holdings

### Data Freshness Alerts

The hook checks file age and alerts if data is stale:

```
⚠️ OUTDATED: Balances file is older than 7 days
⚠️ OUTDATED: Portfolio positions file is older than 7 days

📥 ACTION REQUIRED:
Please update your portfolio data by downloading the latest files from Fidelity
```

### How It Works

```typescript
// 1. Reads session info from stdin
const input: HookInput = JSON.parse(inputData);

// 2. Loads all context files
const skillContent = loadFile(skillPath);
const configContent = loadFile(configPath);
const profileContent = loadFile(profilePath);
const systemContext = loadFile(systemContextPath);

// 3. Finds latest portfolio files (by date in filename)
const latestBalances = getLatestFile(updatesDir, /^Balances_.*\.csv$/);
const latestPositions = getLatestPositionsFile(updatesDir);

// 4. Outputs formatted context (injected as system-reminder)
console.log(output);
```

---

## UserPromptSubmit: skill-activation-prompt.sh

**Purpose**: Automatically suggests relevant skills based on user prompts and file context.

**Location**: `.claude/hooks/skill-activation-prompt.sh`

### How It Works

1. Reads user prompt from stdin
2. Loads `skill-rules.json` for activation triggers
3. Matches prompt against:
   - **Keywords**: "backend", "API", "route"
   - **Intent patterns**: Regex matching user intent
   - **File paths**: What files user is working with
   - **Content patterns**: Code patterns in files
4. Injects skill suggestions into Claude's context

### skill-rules.json Format

```json
{
  "skill-name": {
    "type": "domain | guardrail",
    "enforcement": "suggest | block",
    "priority": "high | medium | low",
    "promptTriggers": {
      "keywords": ["keyword1", "keyword2"],
      "intentPatterns": ["regex.*pattern"]
    },
    "fileTriggers": {
      "pathPatterns": ["src/api/**/*.ts"],
      "contentPatterns": ["import.*Prisma"]
    }
  }
}
```

### Enforcement Levels

- **suggest**: Skill appears as suggestion, Claude can choose to use it
- **block**: Must use skill before proceeding (guardrail)

---

## PostToolUse: post-tool-use-tracker.sh

**Purpose**: Tracks file changes to maintain context across sessions.

**Location**: `.claude/hooks/post-tool-use-tracker.sh`

**Triggers on**: Edit, MultiEdit, Write tool calls

### What It Does

1. Monitors file modifications
2. Records which files were changed
3. Creates cache for context management
4. Auto-detects project structure

### Use Case

Helps Claude understand what parts of your codebase are actively being modified, which improves context relevance.

---

## Stop: Validation Hooks

### stop-build-check-enhanced.sh

**Purpose**: Validates TypeScript compilation before session ends.

**Use when**: You want to ensure no type errors before completing work.

**Customization required**: Edit service detection for your project structure.

### error-handling-reminder.sh

**Purpose**: Ensures error handling is in place before completion.

**Runs**: TypeScript hook via tsx that checks for error patterns.

---

## Adding Custom Hooks

### Step 1: Create the Hook Script

```bash
#!/bin/bash
# .claude/hooks/my-custom-hook.sh

# Read stdin (JSON with session context)
input=$(cat)

# Process and output
echo "My custom hook ran"

exit 0
```

### Step 2: Make It Executable

```bash
chmod +x .claude/hooks/my-custom-hook.sh
```

### Step 3: Add to settings.json

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/my-custom-hook.sh"
          }
        ]
      }
    ]
  }
}
```

### Step 4: Test

```bash
echo '{"session_id": "test"}' | ./.claude/hooks/my-custom-hook.sh
```

---

## Hook Input/Output Format

### Input (stdin)

Hooks receive JSON on stdin:

```json
{
  "session_id": "abc123",
  "event": "session_start",
  "prompt": "user's prompt text",  // UserPromptSubmit only
  "tool_name": "Edit",             // PreToolUse/PostToolUse only
  "tool_input": {...}              // PreToolUse/PostToolUse only
}
```

### Output (stdout)

Output is injected into Claude's context as `<system-reminder>`:

```
Your hook output here will appear in Claude's context
```

### Exit Codes

- **0**: Success, continue
- **Non-zero**: Failure, may block depending on hook type

---

## Debugging Hooks

### Check Hook Execution

```bash
# Test a hook manually
echo '{"session_id": "test", "event": "session_start"}' | \
  npx tsx .claude/hooks/load-fin-core-config.ts
```

### Verify Permissions

```bash
ls -la .claude/hooks/*.sh | grep rwx
```

### Check settings.json Syntax

```bash
cat .claude/settings.json | jq .
```

### Common Issues

| Issue | Solution |
|-------|----------|
| Hook not running | Check file is executable (`chmod +x`) |
| Permission denied | Check file permissions |
| Hook hangs | Ensure script exits (doesn't wait for input) |
| Output not appearing | Check stdout, not stderr |

---

## Hook Files Reference

| File | Type | Purpose |
|------|------|---------|
| `load-fin-core-config.ts` | SessionStart | Load Finance Guru context |
| `skill-activation-prompt.sh` | UserPromptSubmit | Auto-suggest skills |
| `skill-activation-prompt.ts` | (Called by .sh) | TypeScript logic |
| `post-tool-use-tracker.sh` | PostToolUse | Track file changes |
| `stop-build-check-enhanced.sh` | Stop | TypeScript validation |
| `error-handling-reminder.sh` | Stop | Error pattern check |
| `error-handling-reminder.ts` | (Called by .sh) | TypeScript logic |
| `tsc-check.sh` | (Optional) | TypeScript compilation |
| `trigger-build-resolver.sh` | (Optional) | Auto-fix build errors |

---

## Best Practices

1. **Keep hooks fast**: They run synchronously and can slow down the session
2. **Exit cleanly**: Always `exit 0` for success
3. **Output to stdout**: Claude only sees stdout, not stderr
4. **Handle missing files gracefully**: Don't crash on missing optional files
5. **Test manually first**: Run hooks standalone before adding to settings.json
6. **Use TypeScript for complexity**: Wrap complex logic in .ts files called by .sh wrappers

---

## Context Efficiency

The hooks system is designed for token efficiency:

- Context is loaded once at session start, not on every prompt
- Skills load on-demand, not all upfront
- File tracking helps Claude stay focused on relevant code
- Heavy computation (CLI tools) happens outside context window

Typical session uses only **26% of context** (52k/200k tokens) with full Finance Guru loaded.
