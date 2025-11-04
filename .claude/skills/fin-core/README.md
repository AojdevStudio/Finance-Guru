# Finance Guru Core Context Auto-Loader

**Built**: 2025-11-03
**Type**: Session-start hook + skill
**Purpose**: Automatically load Finance Guru system context at every session start

## Overview

This system ensures Finance Guru has complete context availability from the moment a session begins, without requiring manual skill invocation or file reading.

## Components

### 1. Skill File
**Location**: `{project}/.claude/skills/fin-core/SKILL.md` (project-specific)

Contains the core Finance Guru system overview:
- Core identity (Finance Guru v2.0.0, BMAD-CORE v6.0.0)
- Essential file references
- Production-ready tools (7 available)
- Multi-agent system overview
- Current strategic focus

### 2. Session Start Hook
**Location**: `{project-root}/.claude/hooks/load-fin-core-config.ts`

TypeScript hook that executes at session start and:
- Reads the fin-core skill content
- Reads `fin-guru/config.yaml`
- Reads `fin-guru/data/user-profile.yaml`
- Reads `fin-guru/data/system-context.md`
- Loads latest portfolio balances CSV (auto-detects newest)
- Loads latest portfolio positions CSV (auto-detects newest)
- Outputs all content as a formatted system-reminder

### 3. Settings Configuration
**Location**: `{project-root}/.claude/settings.json`

Registered in the `SessionStart` hooks array:
```json
"SessionStart": [
  {
    "hooks": [
      {
        "type": "command",
        "command": "npx tsx $CLAUDE_PROJECT_DIR/.claude/hooks/load-fin-core-config.ts"
      }
    ]
  }
]
```

## Auto-Loaded Content

At every session start, Claude receives:

1. **System Configuration** (config.yaml)
   - 13 specialist agents
   - 21 workflow tasks
   - 7 production tools
   - Temporal awareness config

2. **User Profile** (user-profile.yaml)
   - $500k portfolio structure
   - $13.3k/month W2 deployment
   - Aggressive growth strategy
   - Layer 2 Income plan

3. **System Context** (system-context.md)
   - Private family office positioning
   - Agent team structure
   - Privacy commitments

4. **Latest Portfolio Data** (CSV files)
   - Account balances (newest file)
   - Portfolio positions (newest file)

## How It Works

```
Session Start
    ↓
settings.json triggers hook
    ↓
load-fin-core-config.ts executes
    ↓
Reads all essential files
    ↓
Outputs formatted system-reminder
    ↓
Claude receives full context
    ↓
Ready for financial operations
```

## Testing

```bash
# Test the hook manually
echo '{"session_id":"test","event":"session_start"}' | \
  npx tsx .claude/hooks/load-fin-core-config.ts

# Verify skill content
cat ~/.claude/skills/fin-core/SKILL.md

# Check hook registration
cat .claude/settings.json | grep -A 10 SessionStart
```

## Benefits

✅ **Zero Manual Setup**: Context loaded automatically
✅ **Always Current**: Auto-detects latest CSV files
✅ **Complete Context**: All essential files in one load
✅ **Session Awareness**: Context available from first interaction
✅ **Type-Safe**: TypeScript hook with proper ES module support

## File Locations

**Skill**: `{project}/.claude/skills/fin-core/SKILL.md` (project-specific)
**Hook**: `{project}/.claude/hooks/load-fin-core-config.ts` (project-specific)
**Config**: `{project}/.claude/settings.json` (project-specific)

**All files are project-specific** - this setup only works in the family-office project.

## Environment Variables

The hook uses:
- `$CLAUDE_PROJECT_DIR` - Set by Claude Code to project root

## Next Session

When you start your next Claude Code session in this project, you'll see:

```
🏦 FINANCE GURU CORE CONTEXT LOADED
Session: {session_id}

📘 FIN-CORE SKILL
⚙️ SYSTEM CONFIGURATION  
👤 USER PROFILE
🌐 SYSTEM CONTEXT
💰 LATEST PORTFOLIO BALANCES
📊 LATEST PORTFOLIO POSITIONS

✅ Finance Guru context fully loaded and ready
```

---

**Status**: ✅ Production Ready
**Last Updated**: 2025-11-03
