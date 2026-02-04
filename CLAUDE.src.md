# CLAUDE.md

Finance Guru™ - Private AI-powered family office system built on BMAD-CORE™ v6.

*For Claude Code only*: ALWAYS use the `AskUserQuestion` tool when posing questions to the user.
**Key Principle**: This IS Finance Guru (not a product) - a personal financial command center. Use "your" when discussing assets/strategies/portfolios.

## Architecture

**Multi-Agent System**: Claude transforms into specialized financial agents
**Entry Point**: Finance Orchestrator (Cassandra Holt) - `.claude/commands/fin-guru/agents/finance-orchestrator.md`

**Path Variables**: `{project-root}`, `{module-path}`, `{current_datetime}`, `{current_date}`, `{user_name}`

**Temporal Awareness**: All agents MUST run `date` and `date +"%Y-%m-%d"` at startup to establish temporal context

## Important Files
- @.planning/codebase/STACK.md
- @.planning/codebase/STRUCTURE.md
- @.planning/codebase/ARCHITECTURE.md
- @.planning/codebase/CONVENTIONS.md
- @.planning/codebase/INTEGRATIONS.md
- @.planning/codebase/TESTING.md

**Note**: Private family office system - maintain exclusive, personalized nature of Finance Guru service.

## Subagent Strategy
- Use subagents liberally to keep main context window clean
- Offload research, exploration, and parallel analysis to subagents
- For complex problems, throw more compute at it via subagents
- One task per subagent for focused execution

### 4. Verification Before Done
- Never mark a task complete without proving it works
- Diff behavior between main and your changes when relevant
- Ask yourself: "Would a staff engineer approve this?"
- Run tests, check logs, demonstrate correctness

## Landing the Plane (Session Completion)

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create github issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds
