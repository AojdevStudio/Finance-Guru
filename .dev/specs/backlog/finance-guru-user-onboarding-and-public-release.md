---
title: "Finance Guru User Onboarding and Public Release"
status: backlog
created: 2026-01-15
updated: 2026-02-02
author: "Ossie Irondi"
spec_id: finance-guru-user-onboarding-and-public-release
version: "1.0.0"
description: "Comprehensive onboarding flow and configuration automation for public distribution of Finance Guru"
tags:
  - finance-guru
  - onboarding
  - public-release
  - setup
  - configuration
references: []
supersedes: []
diagrams:
  human: ""
  machine: ""
---

# Finance Guru User Onboarding and Public Release Specification

**Linear Issue:** AOJ-194

## Problem Statement

### Why This Exists
Finance Guru is currently hardcoded with Ossie's personal financial data (name, portfolio values, strategies), making it impossible to distribute to other users. The system needs a comprehensive onboarding flow and configuration automation to become a public, distributable financial analysis tool that anyone can use with their own financial data.

### Who It's For
- New Finance Guru users who want to set up their own private AI-powered family office
- Developers who want to use Finance Guru for personal financial analysis
- Finance enthusiasts looking for institutional-grade portfolio management tools

### Cost of NOT Doing This
- Finance Guru remains a single-user system, limiting its impact
- Community growth blocked - unable to share valuable financial analysis tools
- Manual setup is error-prone, time-consuming (60+ minutes), and poorly documented
- Risk of accidentally exposing Ossie's private financial data if repo shared

### What Triggered This
Desire to open-source Finance Guru and help others build their own AI-powered family offices while maintaining a private fork with personal financial data.

## Technical Requirements

### Architecture Decisions

**1. Onboarding System**
- **Technology**: Python 3.12+ CLI using Claude Code's `AskUserQuestion` tool
- **Structure**: Maps to existing `user-profile.yaml` schema (liquid_assets, investment_portfolio, cash_flow, debt_profile, preferences)
- **Behavior**: Idempotent (safe to re-run, updates only missing values)
- **Resilience**: Resumable (saves progress to `.onboarding-progress.json`, continues after interruption)

**2. Data Models**

| Model | Format | Purpose | Example Values |
|-------|--------|---------|----------------|
| `user-profile.yaml` | YAML | Store user financial data | `monthly_income: 25000` |
| `CLAUDE.md` | Markdown template | Project documentation | Uses `{user_name}`, `{project-root}` |
| `MCP.json` | JSON | MCP server configuration | `exa`, `perplexity`, `gdrive` servers |
| `.onboarding-progress.json` | JSON | Checkpoint for resume | `{"completed": ["liquid_assets"], "current": "cash_flow"}` |

**3. Hooks Refactor**
- **Migration**: Clean break from bash/ts to Bun TypeScript (no backward compatibility)
- **Functionality**: Port existing hooks 1:1, keep exact same behavior
- **Hooks to Migrate**:
  1. `load-fin-core-config.ts` - Session start hook loading Finance Guru context
  2. `skill-activation-prompt.ts` - UserPromptSubmit hook for skill auto-activation
  3. `post-tool-use-tracker.sh` → Convert to `.ts` - PostToolUse hook for file tracking

**4. Template System**
- **CLAUDE.md**: Generic template with path variables (`{user_name}`, `{project-root}`, `{module-path}`)
- **user-profile.yaml**: Empty template populated by onboarding
- **MCP.json**: Pre-configured template with Finance Guru's required servers

**5. Performance Constraints**
- Setup.sh must complete in < 5 minutes on modern hardware
- Onboarding flow must complete in < 15 minutes for comprehensive assessment
- Bun hooks must execute in < 500ms (matching existing performance)

### Decisions Made with Rationale

**Decision 1**: Use CLI with `AskUserQuestion` tool (not web form)
- **Rationale**: Works immediately after git clone, no server needed, matches Claude Code UX patterns, leverages existing tooling
- **Tradeoff**: Less visually appealing than web form, but much faster to implement and no dependency on running server

**Decision 2**: Make API keys optional during setup
- **Rationale**: yfinance works without keys for core functionality, users can enhance later without blocking initial setup
- **Tradeoff**: Initial experience may have limited features, but removes friction from onboarding

**Decision 3**: Fork model for public/private repos (not branch model)
- **Rationale**: Clean separation of template vs personal data, standard Git workflow, easy to pull updates from upstream
- **Tradeoff**: Users need Git knowledge, but that's expected for this technical audience

**Decision 4**: Idempotent setup with progress saving
- **Rationale**: Professional UX, handles interruptions gracefully, supports iterative configuration
- **Tradeoff**: More complex state management, but critical for user experience quality

**Decision 5**: Clean break to Bun hooks (no bash/ts compatibility)
- **Rationale**: Simpler codebase, modern tooling, avoids dual maintenance burden
- **Tradeoff**: Forces users to install Bun, but it's a one-time setup cost

**Decision 6**: Comprehensive onboarding (not simplified)
- **Rationale**: Finance Guru's value comes from deep personalization; detailed profile enables better recommendations
- **Tradeoff**: Longer onboarding (15-20 min), but creates complete user profile from day one

**Decision 7**: Always create fresh MCP.json (not smart merge)
- **Rationale**: Safer than parsing/merging user configs, avoids breaking existing setups
- **Tradeoff**: Users with existing MCP servers must manually merge, but failure mode is explicit and recoverable

## Edge Cases & Error Handling

### Edge Case 1: User Interrupts Onboarding (Ctrl+C)
**Scenario**: User starts onboarding, answers 10 questions, then hits Ctrl+C

**Detection**: Python signal handler catches `SIGINT`

**Recovery Path**:
1. Save current progress to `.onboarding-progress.json` with answered questions
2. On next `setup.sh` run, detect progress file
3. Prompt: "Found incomplete onboarding. Resume from where you left off? (y/n)"
4. If yes: skip completed sections, continue from checkpoint
5. If no: offer to start fresh or cancel

**Implementation**: `scripts/onboarding_cli.py` with signal handling

---

### Edge Case 2: User Runs setup.sh Multiple Times
**Scenario**: User completes setup, then runs `./setup.sh` again days later

**Detection**: Check for existing `user-profile.yaml` with completed data

**Behavior** (Idempotent):
1. Scan existing `user-profile.yaml`, identify missing/empty fields
2. Prompt: "Profile already exists. Update missing fields? (y/n)"
3. If yes: ask only unanswered questions, preserve existing answers
4. If no: show current profile summary, offer to reset or exit

**Validation**: Never overwrite existing data without confirmation

---

### Edge Case 3: Missing Required Tools (uv, bun)
**Scenario**: User clones repo but hasn't installed `uv` or `bun`

**Detection**: setup.sh checks `command -v uv` and `command -v bun` at start

**Recovery**:
1. Display clear error: "Missing required tool: uv"
2. Show installation command: `curl -LsSf https://astral.sh/uv/install.sh | sh`
3. For Bun: `curl -fsSL https://bun.sh/install | bash`
4. Exit with status 1, instruct to re-run after installation

**Prevention**: Document requirements prominently in README

---

### Edge Case 4: User's MCP.json Already Exists
**Scenario**: User has existing MCP server configuration

**Detection**: Check for existing `.claude/mcp.json` before writing

**Recovery**:
1. Backup existing file: `mcp.json.backup-2026-01-15-123456`
2. Create fresh Finance Guru template
3. Display message:
   ```
   ⚠️ Existing MCP.json backed up to: mcp.json.backup-2026-01-15-123456

   Created fresh Finance Guru MCP.json with servers: exa, perplexity, gdrive

   To merge with your existing config:
   1. Review backed up file
   2. Manually add your existing servers to new MCP.json
   3. See docs: fin-guru/README.md#mcp-configuration
   ```

**Documentation**: Provide MCP merge guide in README

---

### Edge Case 5: Invalid Input During Onboarding
**Scenario**: User enters text "abc" when asked for monthly income (expects number)

**Validation Rules**:
- Dollar amounts: Numeric only, >= 0, optional commas (e.g., "25,000")
- Percentages: 0-100 range (e.g., risk tolerance)
- Enums: Must match predefined options (e.g., "aggressive" | "moderate" | "conservative")
- Dates: ISO format YYYY-MM-DD

**Recovery**:
1. Show clear error: "Invalid input: expected number, got 'abc'"
2. Provide example: "Example: 25000 or 25,000"
3. Re-prompt same question (don't advance)
4. After 3 invalid attempts, offer to skip question (leave blank)

**Implementation**: `scripts/validators.py` with retry logic

---

### Edge Case 6: Partial Data in user-profile.yaml
**Scenario**: User manually edited profile, left some fields empty

**Detection**: Parse YAML, check for empty values or missing keys

**Behavior**:
1. Load existing values into memory
2. During onboarding, skip questions with valid answers
3. Ask only questions with missing/empty values
4. Show progress: "Found 8 completed fields, asking 15 remaining questions"

**Validation**: Schema validation after onboarding to ensure completeness

---

### Edge Case 7: Platform Doesn't Support Bun
**Scenario**: User on Windows, ARM Linux, or other platform where Bun has issues

**Detection**: `bun --version` fails or returns incompatible version

**Recovery**:
1. Show error with platform info
2. Provide alternative:
   - Document how to keep bash/ts hooks temporarily
   - Link to Bun compatibility matrix
   - Suggest Docker-based alternative (if available)
3. Allow setup to continue without hooks (degraded mode)

**Documentation**: Add platform compatibility section to README

---

### Edge Case 8: User Cancels API Key Entry
**Scenario**: User doesn't have API keys yet, wants to skip

**Behavior**:
1. For each API key, offer: "Enter API key (or press Enter to skip)"
2. If skipped, add commented placeholder to `.env`:
   ```bash
   # OPTIONAL: Uncomment and add your key when ready
   # ALPHA_VANTAGE_API_KEY=your_key_here
   ```
3. Show summary of skipped keys at end
4. Explain which features require which keys

**Documentation**: Create API key acquisition guide

## User Experience

### Mental Model
Users expect: **"Clone repo → run setup → answer questions → Finance Guru works with MY data"**

### User Journey

**Step 1: Fork & Clone**
```bash
# User forks repo on GitHub: github.com/yourname/family-office
git clone https://github.com/yourname/family-office.git
cd family-office
```

**Step 2: Run Setup**
```bash
./setup.sh
```

**Step 3: Interactive Onboarding**
```
========================================
  Finance Guru™ Setup Wizard
========================================

Welcome! Let's set up your personal Finance Guru.

This will take about 15 minutes. You can interrupt anytime (Ctrl+C)
and resume later.

Progress: [████░░░░░░░░░░░░░░░░] 3 of 8 sections complete

────────────────────────────────────────
Section 1 of 8: Basic Information
────────────────────────────────────────

Question: What is your name?
> John Doe

Question: What is your age?
> 35

... (continues through all sections)
```

**Step 4: API Key Configuration**
```
────────────────────────────────────────
Optional: Configure API Keys
────────────────────────────────────────

Finance Guru works with free data (yfinance), but you can enhance
it with premium APIs:

1. Alpha Vantage (real-time prices, fundamentals)
   Get key at: https://www.alphavantage.co/support/#api-key

   Enter API key (or press Enter to skip):
   >

2. ITC Risk API (external risk scores)
   Get key at: https://www.itc.com/developer

   Enter API key (or press Enter to skip):
   > ABC123XYZ...

... (continues for each API)
```

**Step 5: MCP Server Configuration**
```
────────────────────────────────────────
MCP Server Configuration
────────────────────────────────────────

Creating MCP configuration with servers:
  ✓ exa (web research)
  ✓ perplexity (search/reasoning)
  ✓ gdrive (Google Workspace)

⚠️ Note: You'll need OAuth for gdrive server.
See: docs/mcp-setup.md

Created: .claude/mcp.json
```

**Step 6: Summary**
```
========================================
  Setup Complete! 🎉
========================================

Your Finance Guru is configured:
  ✓ User profile created: fin-guru/data/user-profile.yaml
  ✓ Environment configured: .env
  ✓ MCP servers configured: .claude/mcp.json
  ✓ Hooks installed: .claude/hooks/ (Bun)
  ✓ Private data protected: .gitignore updated

Next Steps:
  1. Open Claude Code in this directory
  2. Test Finance Guru: /finance-orchestrator
  3. Read documentation: fin-guru/README.md

To update your profile later, run: ./setup.sh
```

### Confusion Points & Solutions

| Confusion Point | User Question | Solution |
|-----------------|---------------|----------|
| **Fork Model** | "Do I edit the public repo or fork it?" | README diagram showing fork workflow |
| **API Keys** | "Why do I need so many API keys?" | Setup explains optional vs required, what each enables |
| **Data Location** | "Where is my data stored?" | Setup shows file paths, explains gitignore protection |
| **Updates** | "How do I get Finance Guru updates?" | Docs explain `git pull upstream main` from public repo |
| **Privacy** | "Is my financial data uploaded anywhere?" | Prominent note: "All data stays local. Nothing is uploaded." |
| **Hooks Broken** | "Why aren't hooks working?" | Verify section with `bun --version`, hook test command |

### Feedback Requirements

**During Onboarding**:
- ✅ Progress indicator: "Section 3 of 8: Investment Portfolio"
- ✅ Percentage complete: [████████░░░░░░░░░░░░] 40%
- ✅ Time estimate: "~10 minutes remaining"

**After Each Answer**:
- ✅ Confirm value: "✓ Set monthly income to $25,000"
- ✅ Context: "This helps calculate your investment capacity"

**On Completion**:
- ✅ Summary of configured values (sanitized, no full portfolio details in terminal)
- ✅ Files created/modified list
- ✅ Next steps with exact commands to run

**On Errors**:
- ✅ Clear error messages: "Error: Expected number between 0-100, got '150'"
- ✅ Remediation steps: "Please enter a value between 0 and 100"
- ✅ Support info: "Still having issues? See: docs/troubleshooting.md"

## Scope & Tradeoffs

### In Scope (MVP - All Components from AOJ-194)

#### 1. Remove Hardcoded User References ✅
- Replace "Ossie" in `fin-guru/config.yaml` (author field)
- Replace hardcoded data in `fin-guru/data/user-profile.yaml` with template
- Update any documentation mentioning Ossie specifically
- Add `{user_name}` template variables in relevant files

#### 2. Add First-Time User Onboarding ✅
- CLI tool using `AskUserQuestion` for interactive Q&A
- Comprehensive financial assessment (liquid_assets, investment_portfolio, cash_flow, debt_profile, preferences)
- Progress saving for interruption/resume
- Input validation with helpful error messages
- Summary report on completion

#### 3. Store User Profile for Personalization ✅
- Write to `fin-guru/data/user-profile.yaml`
- Schema validation ensuring completeness
- Idempotent updates (preserve existing data on re-run)
- Protect with .gitignore entry

#### 4. Apply User Context Throughout Responses ✅
- Agents read from `user-profile.yaml` instead of hardcoded values
- `load-fin-core-config` hook loads user profile at session start
- Template variables in CLAUDE.md resolved at runtime

#### 5. Fix setup.sh (CLAUDE.md, .env) ✅
- Generate `CLAUDE.md` from template (generic, not personalized)
- Interactive `.env` API key collection (optional, skippable)
- Directory structure creation (fin-guru-private/, notebooks/updates/)
- Dependency checks (uv, bun) with installation instructions

#### 6. Refactor Hooks to Bun ✅
- Convert all bash/ts hooks to Bun TypeScript
- Clean break (no backward compatibility)
- Keep exact same functionality (1:1 port)
- Hooks: load-fin-core-config, skill-activation-prompt, post-tool-use-tracker
- Test suite for each hook

#### 7. Add MCP.json Setup ✅
- Create fresh template with exa, perplexity, gdrive servers
- Backup existing MCP.json if present
- Interactive API key entry for MCP servers that need it
- Documentation for OAuth setup (gdrive)

#### 8. Setup Mirror Repo Structure ✅
- Document fork model in README (not automated)
- Update `.gitignore` to protect private data:
  - `fin-guru-private/`
  - `fin-guru/data/user-profile.yaml`
  - `notebooks/updates/*.csv`
  - `.env`
- Git setup guide for upstream/origin remotes

### Out of Scope (Explicitly NOT Included)

- ❌ **Web-based onboarding UI**: CLI only for MVP (future enhancement)
- ❌ **Automated fork creation**: No GitHub CLI integration, user forks manually
- ❌ **Encryption of user-profile.yaml**: Filesystem permissions only
- ❌ **Migration script for bash/ts hooks**: Clean break, users must use Bun
- ❌ **Smart merge of MCP.json**: Always create fresh, users manually merge
- ❌ **Multi-language support**: English only (i18n is future work)
- ❌ **Mobile/tablet support**: Desktop terminal only
- ❌ **Cloud sync of user data**: Local-only system
- ❌ **Telemetry/analytics**: No usage tracking

### Technical Debt Accepted

#### 1. No Encryption of Financial Data
**Debt**: User financial data stored in plaintext YAML, protected only by filesystem permissions (Unix 600)

**Justification**:
- Local-only system, matches current approach
- Encryption adds significant UX friction (password management, key storage)
- Target audience (developers) can implement their own encryption if needed

**Future Cost**: If cloud sync added later, will need encryption overhaul

---

#### 2. Clean Break on Hooks (No Backward Compatibility)
**Debt**: Users with existing bash/ts hook customizations must rewrite in Bun

**Justification**:
- Simpler codebase, avoids dual maintenance
- Bun is modern tooling standard, good forcing function
- Existing hooks are Finance Guru-specific, not widely customized

**Future Cost**: User complaints if they heavily customized bash hooks

---

#### 3. No Smart MCP.json Merge
**Debt**: Users with existing MCP servers must manually merge configs

**Justification**:
- Safer than attempting to parse/modify user configs (risk of breaking)
- Clear ownership model: backup + fresh template
- Failure mode is explicit and recoverable

**Future Cost**: Poor UX for users with complex MCP setups

---

#### 4. CLI-Only Onboarding (No Web UI)
**Debt**: Less accessible UX for non-technical users, no visual portfolio entry

**Justification**:
- Faster to implement (weeks vs months)
- Target audience (developers) comfortable with CLI
- Can iterate to web UI based on feedback

**Future Cost**: Limiting adoption to technical users only

---

#### 5. Manual Fork Setup (Not Automated)
**Debt**: Users must manually fork on GitHub, set up remotes

**Justification**:
- Avoids GitHub API/CLI dependencies
- Standard Git workflow for developers
- Reduces setup script complexity significantly

**Future Cost**: Higher barrier to entry for Git novices

### MVP vs Ideal

| Aspect | MVP (Shipping) | Ideal (Future) |
|--------|----------------|----------------|
| **Onboarding** | CLI with AskUserQuestion | Web UI with visual portfolio entry |
| **Fork Setup** | Manual with docs | One-click fork + automated git config |
| **API Keys** | Interactive CLI prompts | OAuth flow with web callback |
| **MCP Config** | Fresh template, manual merge | Smart merge with conflict resolution |
| **Hooks** | Bun only (clean break) | Both bash/ts and Bun (compatibility mode) |
| **Progress Save** | JSON checkpoint file | Cloud sync (optional) |
| **Validation** | Post-onboarding schema check | Real-time validation during input |
| **Security** | Filesystem permissions | Encrypted at rest with master password |

**Why Shipping MVP**:
1. **Time to Market**: Faster to ship (2-3 weeks vs 2-3 months for ideal)
2. **Validation**: Prove demand before building complex features
3. **Iteration**: Learn from user feedback, prioritize next features based on real usage
4. **Audience**: Core developer audience comfortable with CLI/manual steps
5. **Risk**: Lower implementation risk, fewer edge cases, simpler testing

## Integration Requirements

### Systems Affected

| System | Files Modified | Integration Points | Breaking Changes |
|--------|----------------|-------------------|------------------|
| **setup.sh** | `setup.sh` | Orchestrates onboarding, calls Python CLI | None (new functionality) |
| **fin-guru config** | `fin-guru/config.yaml` | Remove `author: Ossie`, add `{user_name}` | Yes: hardcoded author removed |
| **User profile** | `fin-guru/data/user-profile.yaml` | Transform to template, populated by onboarding | Yes: empty template by default |
| **CLAUDE.md** | `CLAUDE.md` | Convert to template with path variables | No: variables resolved at runtime |
| **Hooks** | `.claude/hooks/*` | Complete refactor to Bun TypeScript | Yes: bash/ts hooks removed |
| **Gitignore** | `.gitignore` | Add protections for private data | No: additive only |
| **README** | `README.md` | Add fork model, setup guide | No: additive only |
| **Session start** | `.claude/hooks/load-fin-core-config.ts` | Loads user profile at start | No: existing behavior preserved |
| **MCP config** | `.claude/mcp.json` | Fresh template creation | Yes: existing config backed up |

### Migration Path for Existing Setup (Ossie's Current State)

**Prerequisites**:
1. Commit all current changes
2. Backup entire repo: `cp -r family-office family-office-backup`
3. Create branch for migration: `git checkout -b migration-user-onboarding`

**Migration Steps**:

**Step 1: Backup Current Data**
```bash
# Backup existing user profile
cp fin-guru/data/user-profile.yaml fin-guru/data/user-profile-ossie-backup.yaml

# Backup existing hooks
tar -czf hooks-backup.tar.gz .claude/hooks/

# Backup MCP config
cp .claude/mcp.json .claude/mcp-backup.json
```

**Step 2: Implement Changes**
1. Pull changes from `feature/aoj-194` branch
2. Review modified files carefully
3. Test that old backup data is accessible

**Step 3: Run New Setup**
```bash
./setup.sh
```

**Step 4: Answer Onboarding Questions**
- Use values from `user-profile-ossie-backup.yaml` as reference
- Verify each answer matches existing data
- Setup should detect existing partial data and update only

**Step 5: Verify Migration**
```bash
# Compare profiles (should be equivalent)
diff fin-guru/data/user-profile.yaml fin-guru/data/user-profile-ossie-backup.yaml

# Test agents work
# (Launch Claude Code, run /finance-orchestrator)

# Verify hooks work
cd .claude/hooks
bun test

# Check MCP servers connect
# (Test via Claude Code MCP debug commands)
```

**Step 6: Cleanup**
```bash
# If all tests pass, delete backups
rm fin-guru/data/user-profile-ossie-backup.yaml
rm hooks-backup.tar.gz
rm .claude/mcp-backup.json

# Merge to main
git checkout main
git merge migration-user-onboarding
```

**Rollback Plan** (if migration fails):
```bash
# Restore from backup
cp family-office-backup/fin-guru/data/user-profile.yaml fin-guru/data/user-profile.yaml
tar -xzf hooks-backup.tar.gz -C .claude/
cp .claude/mcp-backup.json .claude/mcp.json

# Revert code changes
git checkout main
git branch -D migration-user-onboarding
```

### Migration Path for New Users

**Step 1: Fork Repository**
1. Visit: https://github.com/ossieirondi/family-office
2. Click "Fork" button
3. Name: `family-office-yourname`
4. Clone your fork: `git clone https://github.com/yourname/family-office-yourname.git`

**Step 2: Set Up Git Remotes**
```bash
cd family-office-yourname

# Add upstream (public template repo)
git remote add upstream https://github.com/ossieirondi/family-office.git

# Verify remotes
git remote -v
# origin    https://github.com/yourname/family-office-yourname.git (fetch/push)
# upstream  https://github.com/ossieirondi/family-office.git (fetch)
```

**Step 3: Install Dependencies**
```bash
# Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Bun (JavaScript runtime)
curl -fsSL https://bun.sh/install | bash

# Reload shell to update PATH
source ~/.bashrc  # or ~/.zshrc
```

**Step 4: Run Setup**
```bash
./setup.sh
```

Follow interactive onboarding (15-20 minutes)

**Step 5: Verify Setup**
```bash
# Check files created
ls -la fin-guru/data/user-profile.yaml
ls -la .env
ls -la .claude/mcp.json
ls -la .claude/hooks/*.ts

# Test hooks
cd .claude/hooks && bun test

# Launch Claude Code
# Test: /finance-orchestrator
```

**Step 6: First Commit (Your Data)**
```bash
# Your data is gitignored, so only config changes commit
git add -A
git status  # Verify no private data staged

git commit -m "Initial setup for personal Finance Guru"
git push origin main
```

**Future Updates** (pulling from public repo):
```bash
# Get latest features from public repo
git fetch upstream
git merge upstream/main

# Resolve any conflicts (rare, mostly documentation)
# Re-run setup if new features require config
./setup.sh

git push origin main
```

## Security & Compliance

### Sensitive Data Handling

**1. Financial Data (`user-profile.yaml`)**
- **Content**: Net worth, income, portfolio holdings, debt balances
- **Location**: `fin-guru/data/user-profile.yaml`
- **Protection**:
  - Gitignored (prevents accidental commits)
  - Filesystem permissions: `chmod 600` (owner read/write only)
  - No network transmission (local-only)
- **Access**: Read by Finance Guru agents at session start
- **Backup**: User responsible (not auto-backed up to avoid copies)

**2. API Keys (`.env`)**
- **Content**: Alpha Vantage, ITC Risk, OpenAI, Polygon API keys
- **Location**: `.env` file in project root
- **Protection**:
  - Gitignored (standard practice)
  - Loaded at runtime via python-dotenv
  - Never logged or displayed
- **Transmission**: Sent to respective APIs over HTTPS
- **Rotation**: User responsible (docs explain how)

**3. Portfolio CSVs (`notebooks/updates/`)**
- **Content**: Fidelity exports with real positions, balances, transactions
- **Location**: `notebooks/updates/*.csv`
- **Protection**:
  - Entire directory gitignored
  - Warning in setup: "Never commit CSV files from this directory"
- **Cleanup**: User should delete old CSVs periodically

**4. Personal Strategies (`fin-guru-private/`)**
- **Content**: Buy tickets, analysis reports, portfolio strategies
- **Location**: `fin-guru-private/fin-guru/`
- **Protection**:
  - Entire directory gitignored at root level
  - Separate from public template code
- **Collaboration**: User can selectively share individual documents if desired

### Authentication & Authorization

**Not Applicable** - Finance Guru is a local-only CLI tool with no authentication system

**MCP Server Authentication**:
- User provides own API keys for MCP servers
- Finance Guru doesn't handle MCP authentication
- OAuth flows (e.g., gdrive) handled by MCP server directly
- Docs explain how to obtain and configure each API key

### Privacy Commitments

**1. Data Sovereignty**
✅ All user data stays local on user's machine
✅ No cloud sync, no external database
✅ No telemetry, analytics, or usage tracking
✅ Finance Guru never transmits user financial data

**2. Open Source Transparency**
✅ All code public on GitHub (except user's private fork)
✅ No obfuscation or hidden data collection
✅ Clear documentation on what data is stored where

**3. User Control**
✅ User controls what data to share (if forking publicly)
✅ Clear gitignore prevents accidental exposure
✅ User can delete any data anytime (rm user-profile.yaml)
✅ No lock-in: data stored in standard formats (YAML, CSV)

**4. Compliance**
- **GDPR**: Not applicable (no personal data processing by Finance Guru service)
- **FINRA**: Educational tool disclaimer, not investment advice
- **PCI DSS**: Not applicable (no payment card data)
- **SOX**: Not applicable (not for corporate financial reporting)

**Educational Use Disclaimer** (Required in all outputs):
```
⚠️ EDUCATIONAL USE ONLY
This analysis is for educational purposes only. Not financial advice.
Consult a licensed financial advisor before making investment decisions.
Past performance does not guarantee future results.
```

### Security Best Practices

**1. Filesystem Permissions**
```bash
# Set restrictive permissions during setup
chmod 600 fin-guru/data/user-profile.yaml
chmod 600 .env
chmod 700 .claude/hooks/
```

**2. Gitignore Validation**
```bash
# Test that private data is ignored
git status | grep -E "(user-profile.yaml|\.env|notebooks/updates)"
# Should return nothing
```

**3. Pre-Commit Hook** (Optional future enhancement)
```bash
# Hook that blocks commit if private data detected
# Not in MVP scope
```

**4. Secrets Scanning** (Recommended for users)
```bash
# Use gitleaks or truffleHog to scan for accidentally committed secrets
gitleaks detect --source . --verbose
```

## Success Criteria & Testing

### Acceptance Criteria

#### Functional Requirements
- [ ] **AC1**: New user completes full setup in < 15 minutes (from fork to working Finance Guru)
- [ ] **AC2**: Setup creates valid `user-profile.yaml` passing schema validation (all required fields present)
- [ ] **AC3**: Finance Guru agents work with generic user profile (no "Ossie" appears in outputs)
- [ ] **AC4**: All 8 components from AOJ-194 implemented and tested
- [ ] **AC5**: Existing Ossie setup can migrate without data loss (verified by profile comparison)
- [ ] **AC6**: Onboarding is resumable after interruption (Ctrl+C then restart continues from checkpoint)
- [ ] **AC7**: setup.sh is idempotent (re-run updates missing fields only, preserves existing data)
- [ ] **AC8**: All Bun hooks function identically to original bash/ts hooks (verified by integration tests)

#### Quality Requirements
- [ ] **AC9**: All tests pass: `pytest tests/ -v` (Python unit tests)
- [ ] **AC10**: All hook tests pass: `bun test` in `.claude/hooks/` (Bun hook tests)
- [ ] **AC11**: Integration test passes: `./tests/integration/test-full-setup.sh` (end-to-end setup)
- [ ] **AC12**: Manual test checklist completed (fork, setup, test, verify gitignore)
- [ ] **AC13**: No hardcoded "Ossie" references in public codebase (grep -r "Ossie" returns only docs/examples)
- [ ] **AC14**: Gitignore prevents private data commits (verified with test commits)

#### Documentation Requirements
- [ ] **AC15**: README explains fork model with diagram
- [ ] **AC16**: Setup guide documents all steps (fork, clone, setup, configure)
- [ ] **AC17**: Troubleshooting doc covers common issues (missing tools, invalid inputs, hook failures)
- [ ] **AC18**: API key acquisition guide for each service (Alpha Vantage, ITC Risk, etc.)

### How You Know It's Done

**Test Scenario 1: Clean Fresh Setup**
```bash
# Starting from scratch
git clone https://github.com/yourname/family-office.git
cd family-office
time ./setup.sh  # Must complete in < 5 minutes

# Measure time to complete onboarding
# Must be < 15 minutes for comprehensive assessment

# Verify outputs
ls -la fin-guru/data/user-profile.yaml  # Exists, populated
ls -la .env  # Exists, has API keys (or placeholders)
ls -la .claude/mcp.json  # Exists, has exa/perplexity/gdrive

# Test Finance Guru
# Launch Claude Code, run /finance-orchestrator
# Verify: response uses YOUR name, not "Ossie"
```

**Test Scenario 2: Interrupted Onboarding**
```bash
# Start setup
./setup.sh
# Answer 5 questions
# Hit Ctrl+C

# Resume
./setup.sh
# Should detect progress, offer to continue
# Should skip answered questions
# Should complete from checkpoint
```

**Test Scenario 3: Idempotent Re-run**
```bash
# Complete setup
./setup.sh
# Answer all questions

# Re-run
./setup.sh
# Should detect existing profile
# Should offer to update missing fields only
# Should NOT overwrite existing answers
```

**Test Scenario 4: Migration from Ossie Setup**
```bash
# Backup current data
cp fin-guru/data/user-profile.yaml backup.yaml

# Run new setup
./setup.sh
# Answer questions using backup as reference

# Compare
diff fin-guru/data/user-profile.yaml backup.yaml
# Should be equivalent (may differ in formatting)

# Test agents still work
# Launch Claude Code, test all agents
```

**Test Scenario 5: Gitignore Protection**
```bash
# Add test data
echo "secret=123" >> .env
echo "9999,Acct123,Portfolio" >> notebooks/updates/test.csv

# Attempt to commit
git add -A
git status

# Verify these files NOT staged:
# - .env
# - notebooks/updates/test.csv
# - fin-guru/data/user-profile.yaml
# - fin-guru-private/*

# Clean up
git reset
```

## Testing Strategy

### Test Framework
- **Python**: pytest (`uv run pytest tests/python/ -v`)
- **Bun**: Built-in test runner (`bun test`) for hooks
- **Shell**: Bash integration tests (`./tests/integration/*.sh`)

### Test Command
```bash
# Run all tests
./scripts/run-all-tests.sh

# Individual test suites
uv run pytest tests/python/ -v  # Python unit tests
cd .claude/hooks && bun test    # Bun hook tests
./tests/integration/test-full-setup.sh  # Integration tests
```

### Unit Tests

**Python Tests** (`tests/python/`)

- [ ] **Test: Profile YAML validation** → File: `tests/python/test_profile_validation.py`
  - Valid profile passes schema
  - Missing required fields rejected
  - Invalid types rejected (string for numeric field)
  - Out-of-range values rejected (risk_tolerance > 100)

- [ ] **Test: YAML generation from template** → File: `tests/python/test_yaml_generation.py`
  - Template populates correctly with user answers
  - Nested structures preserved (liquid_assets.structure list)
  - Empty fields handled gracefully

- [ ] **Test: CLAUDE.md template rendering** → File: `tests/python/test_claude_md_template.py`
  - Variables replaced correctly ({user_name}, {project-root})
  - Path variables resolve to actual paths
  - Missing variables cause error

- [ ] **Test: Input validation (numeric, enums, ranges)** → File: `tests/python/test_input_validation.py`
  - Dollar amounts: numeric only, >= 0, commas allowed
  - Percentages: 0-100 range
  - Enums: only predefined values accepted
  - Dates: ISO format YYYY-MM-DD

- [ ] **Test: Progress save/resume logic** → File: `tests/python/test_progress_persistence.py`
  - Progress saved to `.onboarding-progress.json`
  - Resume loads progress correctly
  - Skip completed questions on resume
  - Handle corrupted progress file gracefully

- [ ] **Test: MCP.json template generation** → File: `tests/python/test_mcp_json_generation.py`
  - Template includes exa, perplexity, gdrive servers
  - API key placeholders present
  - Valid JSON structure
  - OAuth fields present for gdrive

- [ ] **Test: .gitignore rules** → File: `tests/python/test_gitignore_rules.py`
  - fin-guru-private/ ignored
  - user-profile.yaml ignored
  - notebooks/updates/*.csv ignored
  - .env ignored
  - Test: git status returns nothing for these files

**Bun Hook Tests** (`.claude/hooks/tests/`)

- [ ] **Test: load-fin-core-config hook** → File: `.claude/hooks/tests/test_load_fin_core_config.test.ts`
  - Loads user-profile.yaml at session start
  - Handles missing profile gracefully (uses template)
  - Loads latest portfolio CSV from notebooks/updates/
  - Outputs formatted context for Claude

- [ ] **Test: skill-activation-prompt hook** → File: `.claude/hooks/tests/test_skill_activation_prompt.test.ts`
  - Matches user prompts to skill triggers
  - Suggests relevant skills based on context
  - Handles skill-rules.json missing gracefully

- [ ] **Test: post-tool-use-tracker hook** → File: `.claude/hooks/tests/test_post_tool_use_tracker.test.ts`
  - Tracks Edit/Write tool calls
  - Records modified files
  - Detects project structure (frontend, backend, etc.)

- [ ] **Test: Hook performance** → File: `.claude/hooks/tests/test_hook_performance.test.ts`
  - Each hook executes in < 500ms
  - No memory leaks (run 1000 times)

### Integration Tests

**Shell Integration Tests** (`tests/integration/`)

- [ ] **Test: Full setup.sh flow (clean env → configured system)** → File: `tests/integration/test_full_setup.sh`
  - Creates directory structure
  - Runs onboarding (with mocked inputs)
  - Generates all config files
  - Installs hooks
  - Verifies Finance Guru works

- [ ] **Test: Onboarding interruption and resume** → File: `tests/integration/test_onboarding_resume.sh`
  - Start onboarding
  - Answer 5 questions
  - Send SIGINT (Ctrl+C)
  - Verify progress saved
  - Restart, verify resume offer
  - Continue, verify skip completed questions

- [ ] **Test: Idempotent re-run (preserves existing data)** → File: `tests/integration/test_idempotent_setup.sh`
  - Complete full setup
  - Manually edit user-profile.yaml (change one value)
  - Re-run setup.sh
  - Verify edited value preserved
  - Verify only missing fields prompted

- [ ] **Test: Finance Guru agents with new profile** → File: `tests/integration/test_agents_with_new_profile.py`
  - Create test profile (not Ossie's data)
  - Load profile via hook
  - Run finance-orchestrator agent
  - Verify agent uses test profile data
  - Verify no "Ossie" in agent output

- [ ] **Test: MCP server configuration** → File: `tests/integration/test_mcp_servers.sh`
  - Verify MCP.json created
  - Test each server listed (exa, perplexity, gdrive)
  - Verify API key placeholders present
  - (Actual connection tests require real API keys - out of scope)

- [ ] **Test: Gitignore protection** → File: `tests/integration/test_gitignore_protection.sh`
  - Create test private data files
  - Run `git add -A`
  - Verify private files NOT staged
  - Verify only public files staged

### Manual Test Checklist

**Pre-Release QA** (Perform before merging to main)

- [ ] **Fork repo on GitHub**
  - Verify fork button works
  - Verify forked repo accessible
  - Verify clone works: `git clone https://github.com/yourname/family-office.git`

- [ ] **Install dependencies**
  - Fresh machine (or Docker container)
  - Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
  - Install Bun: `curl -fsSL https://bun.sh/install | bash`
  - Verify versions: `uv --version`, `bun --version`

- [ ] **Run setup.sh from scratch**
  - Time it: `time ./setup.sh` (must be < 5 minutes)
  - Verify all prompts clear and helpful
  - Verify progress indicator works
  - Verify examples shown for each question

- [ ] **Test onboarding flow**
  - Start timer (should complete in < 15 minutes)
  - Answer all questions honestly (don't rush)
  - Note any confusing questions
  - Verify input validation (try invalid inputs)
  - Check summary at end is accurate

- [ ] **Interrupt onboarding midway**
  - Start setup.sh
  - Answer ~10 questions
  - Hit Ctrl+C
  - Verify progress saved message
  - Restart: `./setup.sh`
  - Verify "Resume from checkpoint?" prompt
  - Continue, verify skip completed questions
  - Complete onboarding

- [ ] **Check generated files**
  - `fin-guru/data/user-profile.yaml`: populated with your answers
  - `.env`: exists, has API keys or placeholders
  - `.claude/mcp.json`: exists, has exa/perplexity/gdrive
  - `CLAUDE.md`: exists, generic (no personal data)
  - `.claude/hooks/*.ts`: all Bun TypeScript, no .sh files

- [ ] **Test Finance Guru agents**
  - Open Claude Code in project directory
  - Run: `/finance-orchestrator`
  - Verify agent responds
  - **Critical**: Verify YOUR name appears, not "Ossie"
  - Verify agent uses YOUR portfolio data (not hardcoded)

- [ ] **Test all Bun hooks**
  - Session start hook: Close/reopen Claude Code, verify context loaded
  - Skill activation: Type "analyze portfolio", verify skill suggested
  - Post-tool-use: Edit a file, verify tracking works

- [ ] **Verify gitignore protection**
  - Create test file: `echo "test" >> notebooks/updates/test.csv`
  - Edit profile: `vim fin-guru/data/user-profile.yaml`
  - Edit .env: `echo "TEST_KEY=abc" >> .env`
  - Run: `git status`
  - **Critical**: None of these files should appear in git status
  - Clean up: `rm notebooks/updates/test.csv`

- [ ] **Test idempotent re-run**
  - Edit profile manually: change monthly_income value
  - Re-run: `./setup.sh`
  - Verify prompt: "Update missing fields?"
  - Verify edited value NOT overwritten
  - Verify only empty/missing fields asked

- [ ] **Test API key skipping**
  - Re-run setup: `./setup.sh`
  - When prompted for API keys, press Enter to skip
  - Verify .env has commented placeholders
  - Verify Finance Guru still works (with yfinance free data)

- [ ] **Test MCP server setup**
  - Check `.claude/mcp.json` contents
  - Verify servers: exa, perplexity, gdrive
  - Verify API key fields present
  - (Actual connection testing requires real API keys - out of scope)

- [ ] **Check documentation**
  - README explains fork model clearly
  - Setup guide is accurate (follow it step-by-step)
  - Troubleshooting doc covers common issues
  - API key guide has correct URLs

- [ ] **Test fork workflow (update from upstream)**
  - Add upstream remote: `git remote add upstream https://github.com/ossieirondi/family-office.git`
  - Fetch: `git fetch upstream`
  - Check for updates: `git log upstream/main`
  - Merge: `git merge upstream/main`
  - Verify no conflicts with your private data
  - Verify Finance Guru still works after update

## Implementation Tasks

<!-- RBP-TASKS-START -->

**Foundation Tasks**

### Task 1: Create Onboarding CLI Script Structure
- **ID:** task-001
- **Dependencies:** none
- **Files:**
  - `scripts/onboarding_cli.py` (new)
  - `scripts/validators.py` (new)
  - `scripts/progress_manager.py` (new)
- **Acceptance:**
  - Script runs without errors: `python scripts/onboarding_cli.py`
  - Help text displays: `python scripts/onboarding_cli.py --help`
  - Imports all validators successfully
- **Tests:** `tests/python/test_onboarding_cli_structure.py`

### Task 2: Implement Input Validation Module
- **ID:** task-002
- **Dependencies:** task-001
- **Files:**
  - `scripts/validators.py`
- **Acceptance:**
  - Dollar amount validation: accepts "25000", "25,000", rejects "abc"
  - Percentage validation: accepts 0-100, rejects 150
  - Enum validation: accepts predefined values only
  - Date validation: accepts YYYY-MM-DD, rejects invalid dates
- **Tests:** `tests/python/test_input_validation.py`

### Task 3: Implement Progress Save/Resume System
- **ID:** task-003
- **Dependencies:** task-001
- **Files:**
  - `scripts/progress_manager.py`
  - `.onboarding-progress.json` (generated at runtime)
- **Acceptance:**
  - Progress saved after each question answered
  - Interrupted onboarding creates checkpoint file
  - Resume detects checkpoint and offers to continue
  - Completed questions skipped on resume
- **Tests:** `tests/python/test_progress_persistence.py`

### Task 4: Create YAML Generation Module
- **ID:** task-004
- **Dependencies:** task-001
- **Files:**
  - `scripts/yaml_generator.py` (new)
  - `templates/user-profile-template.yaml` (new)
- **Acceptance:**
  - Template loads successfully
  - User answers populate template correctly
  - Nested structures preserved (e.g., liquid_assets.structure list)
  - Output validates against schema
- **Tests:** `tests/python/test_yaml_generation.py`

**Onboarding Flow Tasks**

### Task 5: Implement Liquid Assets Section
- **ID:** task-005
- **Dependencies:** task-002, task-004
- **Files:**
  - `scripts/onboarding_cli.py` (liquid_assets questions)
- **Acceptance:**
  - Asks for: total, accounts_count, average_yield
  - Optional: structure list (user can skip)
  - Validates numeric inputs
  - Saves to progress file
- **Tests:** `tests/python/test_liquid_assets_section.py`

### Task 6: Implement Investment Portfolio Section
- **ID:** task-006
- **Dependencies:** task-002, task-004
- **Files:**
  - `scripts/onboarding_cli.py` (investment_portfolio questions)
- **Acceptance:**
  - Asks for: total_value, retirement_accounts, allocation, risk_profile
  - Validates enums (risk_profile: aggressive|moderate|conservative)
  - Calculates total_net_worth
- **Tests:** `tests/python/test_investment_portfolio_section.py`

### Task 7: Implement Cash Flow Section
- **ID:** task-007
- **Dependencies:** task-002, task-004
- **Files:**
  - `scripts/onboarding_cli.py` (cash_flow questions)
- **Acceptance:**
  - Asks for: monthly_income, fixed_expenses, variable_expenses
  - Calculates investment_capacity automatically
  - Validates all numeric inputs
- **Tests:** `tests/python/test_cash_flow_section.py`

### Task 8: Implement Debt Profile Section
- **ID:** task-008
- **Dependencies:** task-002, task-004
- **Files:**
  - `scripts/onboarding_cli.py` (debt_profile questions)
- **Acceptance:**
  - Asks for: mortgage_balance, mortgage_payment, other_debt details
  - Calculates weighted_interest_rate
  - Handles multiple debt types (student loans, car loans, credit cards)
- **Tests:** `tests/python/test_debt_profile_section.py`

### Task 9: Implement Preferences Section
- **ID:** task-009
- **Dependencies:** task-002, task-004
- **Files:**
  - `scripts/onboarding_cli.py` (preferences questions)
- **Acceptance:**
  - Asks for: risk_tolerance, investment_philosophy, time_horizon
  - Validates enums
  - Optional focus_areas (multi-select)
- **Tests:** `tests/python/test_preferences_section.py`

### Task 10: Implement Onboarding Summary & Confirmation
- **ID:** task-010
- **Dependencies:** task-005, task-006, task-007, task-008, task-009
- **Files:**
  - `scripts/onboarding_cli.py` (summary display)
- **Acceptance:**
  - Displays summary of all answers (sanitized, no sensitive details in terminal history)
  - Asks for confirmation: "Save this profile? (y/n)"
  - If yes: writes to user-profile.yaml
  - If no: offers to restart or exit
  - Deletes progress file on successful completion
- **Tests:** `tests/python/test_onboarding_summary.py`

**Setup Script Enhancement Tasks**

### Task 11: Enhance setup.sh with Onboarding Integration
- **ID:** task-011
- **Dependencies:** task-010
- **Files:**
  - `setup.sh`
- **Acceptance:**
  - Checks for existing user-profile.yaml
  - If exists: offers to update missing fields (idempotent)
  - If not exists: runs full onboarding
  - Handles interruption gracefully
- **Tests:** `tests/integration/test_setup_onboarding_integration.sh`

### Task 12: Implement CLAUDE.md Template System
- **ID:** task-012
- **Dependencies:** none
- **Files:**
  - `templates/CLAUDE.md.template` (new)
  - `scripts/generate_claude_md.py` (new)
  - `setup.sh` (calls generation script)
- **Acceptance:**
  - Template contains generic content (no user-specific data)
  - Variables: {user_name}, {project-root}, {module-path}
  - Script resolves variables at generation time
  - Writes to `CLAUDE.md`
- **Tests:** `tests/python/test_claude_md_template.py`

### Task 13: Implement Interactive .env Setup
- **ID:** task-013
- **Dependencies:** none
- **Files:**
  - `scripts/env_setup.py` (new)
  - `.env.example`
  - `setup.sh` (calls env setup script)
- **Acceptance:**
  - Checks for existing .env (backs up if exists)
  - Prompts for each API key with:
    - Description of what API provides
    - URL to obtain key
    - "Press Enter to skip" option
  - Writes .env with keys or commented placeholders
  - Sets secure permissions: `chmod 600 .env`
- **Tests:** `tests/python/test_env_setup.py`

### Task 14: Implement MCP.json Generation
- **ID:** task-014
- **Dependencies:** none
- **Files:**
  - `templates/mcp.json.template` (new)
  - `scripts/generate_mcp_json.py` (new)
  - `setup.sh` (calls generation script)
- **Acceptance:**
  - Checks for existing .claude/mcp.json (backs up if exists)
  - Template includes: exa, perplexity, gdrive servers
  - API key placeholders present
  - OAuth fields for gdrive
  - Writes to `.claude/mcp.json`
- **Tests:** `tests/python/test_mcp_json_generation.py`

**Hook Refactor Tasks**

### Task 15: Refactor load-fin-core-config Hook to Bun
- **ID:** task-015
- **Dependencies:** none
- **Files:**
  - `.claude/hooks/load-fin-core-config.ts` (rewrite)
  - Delete: `.claude/hooks/load-fin-core-config.sh` (if exists)
- **Acceptance:**
  - Bun TypeScript implementation
  - Loads user-profile.yaml at session start
  - Loads latest portfolio CSV from notebooks/updates/
  - Outputs formatted context identical to bash version
  - Executes in < 500ms
- **Tests:** `.claude/hooks/tests/test_load_fin_core_config.test.ts`

### Task 16: Refactor skill-activation-prompt Hook to Bun
- **ID:** task-016
- **Dependencies:** none
- **Files:**
  - `.claude/hooks/skill-activation-prompt.ts` (rewrite)
  - Delete: `.claude/hooks/skill-activation-prompt.sh` (if exists)
- **Acceptance:**
  - Bun TypeScript implementation
  - Reads skill-rules.json
  - Matches user prompts to skill triggers
  - Outputs skill suggestions
  - Identical behavior to bash version
  - Executes in < 500ms
- **Tests:** `.claude/hooks/tests/test_skill_activation_prompt.test.ts`

### Task 17: Refactor post-tool-use-tracker Hook to Bun
- **ID:** task-017
- **Dependencies:** none
- **Files:**
  - `.claude/hooks/post-tool-use-tracker.ts` (new, converting from .sh)
  - Delete: `.claude/hooks/post-tool-use-tracker.sh`
- **Acceptance:**
  - Bun TypeScript implementation
  - Monitors Edit/Write tool calls
  - Records modified files
  - Auto-detects project structure
  - Identical behavior to bash version
  - Executes in < 200ms
- **Tests:** `.claude/hooks/tests/test_post_tool_use_tracker.test.ts`

### Task 18: Create Bun Hook Test Suite
- **ID:** task-018
- **Dependencies:** task-015, task-016, task-017
- **Files:**
  - `.claude/hooks/tests/test_hooks.test.ts` (new)
  - `.claude/hooks/package.json` (add test script)
- **Acceptance:**
  - All hooks have unit tests
  - Tests verify identical behavior to bash versions
  - Performance tests ensure < 500ms execution
  - Run with: `bun test`
- **Tests:** Self-testing (test suite tests itself)

**Data Protection Tasks**

### Task 19: Remove Hardcoded "Ossie" References
- **ID:** task-019
- **Dependencies:** none
- **Files:**
  - `fin-guru/config.yaml` (remove `author: Ossie`)
  - `fin-guru/workflows/workflow.yaml` (template variables)
  - `fin-guru/distribution-plan.md` (generic language)
  - `fin-guru/README.md` (examples use {user_name})
  - Any other files with hardcoded references
- **Acceptance:**
  - Search `grep -r "Ossie" .` returns only docs/examples
  - config.yaml uses `{user_name}` variable
  - No personal data in public codebase
- **Tests:** `tests/python/test_no_hardcoded_references.py`

### Task 20: Update .gitignore for Private Data Protection
- **ID:** task-020
- **Dependencies:** none
- **Files:**
  - `.gitignore`
- **Acceptance:**
  - Adds: `fin-guru-private/`
  - Adds: `fin-guru/data/user-profile.yaml`
  - Adds: `notebooks/updates/*.csv`
  - Adds: `.env`
  - Adds: `.onboarding-progress.json`
  - Verify: test files in these locations are ignored by git
- **Tests:** `tests/integration/test_gitignore_protection.sh`

**Documentation Tasks**

### Task 21: Write Fork Model README Section
- **ID:** task-021
- **Dependencies:** none
- **Files:**
  - `README.md` (add "Repository Structure" section)
  - `docs/fork-workflow.md` (new, detailed guide)
- **Acceptance:**
  - Explains public template vs private fork
  - Diagram showing workflow (ASCII or Mermaid)
  - Instructions for:
    - Forking on GitHub
    - Setting up remotes (origin, upstream)
    - Pulling updates from upstream
    - Protecting private data
  - Link to detailed guide
- **Tests:** Manual review

### Task 22: Write Comprehensive Setup Guide
- **ID:** task-022
- **Dependencies:** task-011, task-012, task-013, task-014
- **Files:**
  - `docs/setup-guide.md` (new)
  - `README.md` (link to setup guide)
- **Acceptance:**
  - Step-by-step instructions with code blocks
  - Prerequisites section (uv, bun, Git)
  - Onboarding section (what to expect, how long)
  - Troubleshooting section (common issues)
  - Screenshots or terminal recordings (optional)
- **Tests:** Manual review (follow guide on fresh machine)

### Task 23: Write API Key Acquisition Guide
- **ID:** task-023
- **Dependencies:** task-013
- **Files:**
  - `docs/api-keys.md` (new)
- **Acceptance:**
  - For each API: Alpha Vantage, ITC Risk, etc.
    - What it provides (features)
    - Why it's optional vs required
    - How to obtain (step-by-step with URLs)
    - Where to add in .env
    - How to test it works
- **Tests:** Manual review

### Task 24: Write Troubleshooting Documentation
- **ID:** task-024
- **Dependencies:** task-022
- **Files:**
  - `docs/troubleshooting.md` (new)
- **Acceptance:**
  - Common issues:
    - "uv/bun not found" → installation instructions
    - "Permission denied" → chmod/ownership fix
    - "Invalid input" → validation examples
    - "Hooks not working" → hook debugging steps
    - "MCP servers not connecting" → MCP debug commands
  - Each issue has:
    - Symptom description
    - Root cause
    - Resolution steps
    - Prevention tips
- **Tests:** Manual review

**Integration & Testing Tasks**

### Task 25: Create Integration Test: Full Setup Flow
- **ID:** task-025
- **Dependencies:** task-011, task-012, task-013, task-014
- **Files:**
  - `tests/integration/test_full_setup.sh` (new)
- **Acceptance:**
  - Test in Docker container (fresh environment)
  - Runs: `./setup.sh` with mocked inputs
  - Verifies all files created:
    - `user-profile.yaml`
    - `.env`
    - `.claude/mcp.json`
    - `CLAUDE.md`
  - Verifies hooks installed: `.claude/hooks/*.ts`
  - Test passes: `./tests/integration/test_full_setup.sh`
- **Tests:** Self-testing

### Task 26: Create Integration Test: Onboarding Resume
- **ID:** task-026
- **Dependencies:** task-003, task-011
- **Files:**
  - `tests/integration/test_onboarding_resume.sh` (new)
- **Acceptance:**
  - Starts onboarding, answers 5 questions
  - Sends SIGINT (simulates Ctrl+C)
  - Verifies `.onboarding-progress.json` created
  - Restarts onboarding
  - Verifies resume prompt appears
  - Continues, verifies completed questions skipped
  - Test passes: `./tests/integration/test_onboarding_resume.sh`
- **Tests:** Self-testing

### Task 27: Create Integration Test: Idempotent Re-run
- **ID:** task-027
- **Dependencies:** task-011
- **Files:**
  - `tests/integration/test_idempotent_setup.sh` (new)
- **Acceptance:**
  - Runs full setup once
  - Manually edits user-profile.yaml (change one value)
  - Re-runs setup
  - Verifies edited value preserved
  - Verifies only missing fields prompted
  - Test passes: `./tests/integration/test_idempotent_setup.sh`
- **Tests:** Self-testing

### Task 28: Create Integration Test: Gitignore Protection
- **ID:** task-028
- **Dependencies:** task-020
- **Files:**
  - `tests/integration/test_gitignore_protection.sh` (new)
- **Acceptance:**
  - Creates test files in protected directories:
    - `notebooks/updates/test.csv`
    - `.env` (adds test key)
    - `fin-guru/data/user-profile.yaml` (edits)
  - Runs: `git add -A && git status`
  - Verifies protected files NOT staged
  - Test passes: `./tests/integration/test_gitignore_protection.sh`
- **Tests:** Self-testing

### Task 29: Create Manual Test Checklist Document
- **ID:** task-029
- **Dependencies:** task-022
- **Files:**
  - `tests/MANUAL_TEST_CHECKLIST.md` (new)
- **Acceptance:**
  - Checklist covers all scenarios from "Manual Test Checklist" section above
  - Each item has:
    - Test description
    - Expected result
    - Checkbox for QA to mark complete
  - Used for pre-release QA
- **Tests:** Manual review

### Task 30: Create Master Test Runner Script
- **ID:** task-030
- **Dependencies:** task-025, task-026, task-027, task-028
- **Files:**
  - `scripts/run-all-tests.sh` (new)
- **Acceptance:**
  - Runs all test suites sequentially:
    - Python unit tests: `uv run pytest tests/python/ -v`
    - Bun hook tests: `cd .claude/hooks && bun test`
    - Integration tests: `./tests/integration/*.sh`
  - Reports summary: X/Y tests passed
  - Exits with code 0 if all pass, 1 if any fail
  - Run with: `./scripts/run-all-tests.sh`
- **Tests:** Self-testing
<!-- RBP-TASKS-END -->

---

## Implementation Notes

### Codebase-Specific Guidance

**Existing Patterns to Follow**:
1. **Python CLI Tools**: See `src/analysis/risk_metrics_cli.py` for CLI argument parsing patterns
2. **YAML Loading**: Use existing pattern in `load-fin-core-config.ts` for parsing user-profile.yaml
3. **Hook Structure**: Follow existing hook structure (input parsing, main logic, output formatting)
4. **Testing**: Follow existing pytest patterns in `tests/python/`

**Files to Reference**:
- **User Profile Schema**: `fin-guru/data/user-profile.yaml` (current Ossie's data shows complete schema)
- **Hook Patterns**: `.claude/hooks/load-fin-core-config.ts` (shows session start hook pattern)
- **Setup Script Pattern**: Current `setup.sh` (extend, don't rewrite from scratch)
- **CLI Tool Pattern**: `src/analysis/risk_metrics_cli.py` (argparse usage, input validation)

**Critical Dependencies**:
- **Python**: Use `uv` for all Python operations (`uv run python`, `uv run pytest`)
- **Bun**: Use `bun` for hooks (`bun test`, `bun run`)
- **YAML**: Use `PyYAML` for Python, built-in for Bun TypeScript
- **Validation**: Use existing `pydantic` for data validation (already in dependencies)

**Performance Targets**:
- Setup script: < 5 minutes total
- Onboarding: < 15 minutes (comprehensive assessment)
- Each hook: < 500ms execution time
- Python CLI: < 1 second startup time

**Error Handling Patterns**:
```python
# Python - use clear exceptions with remediation hints
try:
    value = int(user_input)
except ValueError:
    print(f"Error: Expected number, got '{user_input}'")
    print("Example: 25000 or 25,000")
    # Re-prompt, don't crash
```

```typescript
// Bun TypeScript - use optional chaining and null checks
const profile = await loadUserProfile();
if (!profile?.user_profile?.investment_portfolio) {
  console.error("Warning: Incomplete user profile, using defaults");
  return defaultProfile;
}
```

**Git Workflow for Implementation**:
1. Create feature branch: `git checkout -b feature/aoj-194-user-onboarding`
2. Implement tasks in order (task-001 → task-030)
3. Test each task before moving to next
4. Commit frequently with descriptive messages
5. Final commit: "feat: complete user onboarding system (AOJ-194)"
6. Push: `git push origin feature/aoj-194-user-onboarding`
7. Create PR to main with this spec linked

**Testing Strategy During Development**:
- **Task-level**: Write test first (TDD), implement until test passes
- **Section-level**: Run all tests for that section before moving on
- **Pre-PR**: Run full test suite: `./scripts/run-all-tests.sh`
- **Pre-Merge**: Complete manual test checklist

**Breaking Changes to Communicate**:
1. **Hooks**: Bash/ts hooks removed, Bun required (document in CHANGELOG)
2. **User Profile**: Empty by default, users must run onboarding (document in README)
3. **MCP Config**: Fresh template, existing configs backed up (document in setup output)

**Deployment Checklist** (before release):
- [ ] All tests pass (unit + integration + manual)
- [ ] Documentation complete (README, setup guide, troubleshooting)
- [ ] CHANGELOG.md updated with breaking changes
- [ ] Example onboarding completed successfully on 3 platforms (Mac, Linux, Windows/WSL)
- [ ] Existing Ossie setup successfully migrated without data loss
- [ ] Linear issue AOJ-194 marked complete with link to PR

---

## Implementation Plan Created

**File:** `specs/finance-guru-user-onboarding-and-public-release.md`

**Topic:** Finance Guru user onboarding system and public release preparation

**Open Questions:** 0 (all resolved via comprehensive interview)

**Key Decisions Made:**
1. **Comprehensive CLI onboarding** using Claude's `AskUserQuestion` tool (15-20 min assessment)
2. **Fork model** for public/private repos (documented, not automated)
3. **Clean break to Bun hooks** (no bash/ts backward compatibility)
4. **Idempotent setup** with progress saving/resume capability
5. **API keys optional** during setup (reduces friction, enables yfinance-based core functionality)
6. **Fresh MCP.json template** (backs up existing, no smart merge to avoid breaking user configs)
7. **Filesystem permissions only** for data security (no encryption, matches local-only use case)
8. **Full MVP scope** - all 8 AOJ-194 components in first release (onboarding, hardcoded refs removal, setup.sh enhancements, MCP automation, Bun hooks)

**Task Breakdown:** 30 discrete tasks ordered by dependency, each with clear acceptance criteria and associated tests

**Testing Strategy:** Comprehensive 3-layer approach (unit + integration + manual checklist)

**Success Criteria:** New user completes setup in < 15 min, Finance Guru works with their data, no "Ossie" references, all tests pass
