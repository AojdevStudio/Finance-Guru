# Phase 2: Setup Automation & Dependency Checking - Research

**Researched:** 2026-02-03
**Domain:** Bash scripting, cross-platform dependency checking, terminal UX, progress tracking, idempotent setup scripts
**Confidence:** HIGH

## Summary

This phase rewrites the existing `setup.sh` into a robust, user-facing setup script that checks dependencies before modifying the filesystem, creates the `fin-guru-private/` directory structure, scaffolds config files with overwrite protection, and tracks progress for resumable re-runs. The script targets macOS, Linux (Ubuntu/Debian), and Windows WSL.

The existing `setup.sh` (389 lines) already handles directory creation and basic dependency warnings, but lacks several CONTEXT.md requirements: check-all-then-fail dependency behavior, OS-specific install commands, `--check-deps-only` flag, `.setup-progress` tracking, overwrite prompts for config files, terminal color detection with fallback, and prompted auto-install. The rewrite restructures 11 loosely-ordered steps into 5 phases: args, deps, dirs, config, install.

Research confirms all requirements are achievable with pure bash (no external libraries needed). The key patterns are: `command -v` for dependency detection, `grep -oE` for portable version extraction, `sort -V` for version comparison (verified on macOS), `[ -t 1 ]` for tty detection, `uname -s` plus `/proc/version` for OS detection, and a line-per-step progress file for idempotent re-runs.

**Primary recommendation:** Implement as pure bash with no external dependencies beyond the tools being checked. Use `set -e` with `|| { ... }` guards for the check-all-then-fail accumulator pattern. Use `sort -V` for version comparison (works on macOS 26.2 Apple sort 2.3).

## Standard Stack

### Core
| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| bash | 3.2+ (macOS ships 3.2, Linux 5.x) | Script interpreter | Universally available, POSIX-compatible, required by CONTEXT.md |
| command -v | builtin | Dependency existence checking | POSIX-standard, more reliable than `which` (which is not POSIX) |
| sort -V | Apple sort 2.3 / GNU coreutils 8.x | Version string comparison | Available on macOS (verified), Linux, and WSL. Handles semver correctly |
| grep -oE | BSD grep 2.6.0 / GNU grep 3.x | Version string extraction | Extended regex without PCRE (-oP not available on macOS BSD grep) |
| uname -s | builtin | OS kernel detection | Universal across macOS/Linux/WSL |

### Supporting
| Tool | Purpose | When to Use |
|------|---------|-------------|
| tput colors | Terminal color capability detection | Alternative to tty check; returns number of supported colors |
| /proc/version | WSL detection | Contains "Microsoft" or "microsoft" string on WSL |
| /etc/os-release | Linux distro detection | Available on Ubuntu/Debian/Fedora, not macOS |
| read -r -p | Interactive user prompts | For auto-install consent and overwrite prompts |
| printf | Formatted output with color codes | More portable than `echo -e` for ANSI escapes |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| sort -V | Custom bash arithmetic comparison | sort -V is simpler and handles edge cases; custom arithmetic needs careful major-then-minor logic (see Pitfall 1) |
| grep -oE | awk/sed for version extraction | grep -oE is most readable and concise for this use case |
| ANSI escape codes | tput setaf/sgr0 | tput is more portable but adds dependency on ncurses; ANSI escapes work on all modern terminals (macOS Terminal, iTerm2, VS Code, WSL) |
| Line-per-step progress file | JSON progress file | JSON requires jq or python to parse; line-per-step is grep-able with zero dependencies |
| set -e + || guards | Manual return code checking | set -e catches unexpected failures; || guards handle expected check-all-then-fail accumulation |

**Installation:**
```bash
# No installation needed -- this phase uses only bash builtins and standard Unix tools
# The script checks for these dependencies (which it helps install):
# - Python 3.12+ (brew install python@3.12 / apt install python3.12)
# - uv (curl -LsSf https://astral.sh/uv/install.sh | sh)
# - Bun (curl -fsSL https://bun.sh/install | bash)
```

## Architecture Patterns

### Recommended Script Structure
```
setup.sh
├── Header: set -e, SCRIPT_DIR, PROJECT_ROOT
├── Color detection: [ -t 1 ] && [ "$TERM" != "dumb" ]
├── Color variable definitions (or empty strings)
├── Utility functions:
│   ├── detect_os()           # macOS/linux/wsl
│   ├── get_install_command() # OS-specific install command per dep
│   ├── prompt_install()      # Interactive auto-install with consent
│   ├── check_dependency()    # Single dep check with version
│   ├── check_all_deps()      # Check all 3, accumulate, report
│   ├── create_dir()          # Idempotent mkdir -p with report
│   ├── is_step_complete()    # Check .setup-progress
│   ├── mark_step_complete()  # Append to .setup-progress
│   └── scaffold_file()       # Create file with overwrite prompt
├── Phase functions:
│   ├── create_directory_structure()  # fin-guru-private/ tree
│   ├── scaffold_config_files()       # user-profile, .env, README
│   └── install_python_deps()         # uv sync
├── CLI argument parser: --check-deps-only, --help
└── Main flow:
    ├── detect_os
    ├── check_all_deps || exit 1  (or exit after --check-deps-only)
    ├── create_directory_structure
    ├── scaffold_config_files
    ├── install_python_deps
    └── print_summary
```

### Pattern 1: Check-All-Then-Fail with set -e
**What:** Check all dependencies before reporting failures, despite `set -e` being active.
**When to use:** The dependency checking phase -- must report ALL missing deps, not just the first.
**Verified:** Tested on macOS bash. The `|| { ... }` pattern prevents `set -e` from exiting on individual check failures.
**Example:**
```bash
# Source: Verified on macOS bash (2026-02-03)
set -e

check_all_deps() {
  local missing=0

  # Each check uses || to prevent set -e from exiting
  check_dependency "python3" "Python" "3.12" || { missing=$((missing + 1)); }
  check_dependency "uv" "uv" "" || { missing=$((missing + 1)); }
  check_dependency "bun" "Bun" "" || { missing=$((missing + 1)); }

  if [ "$missing" -gt 0 ]; then
    # ... offer auto-install if not --check-deps-only ...
    return 1
  fi
  return 0
}

# In main flow:
check_all_deps || exit 1
# If we reach here, all deps are present
```

### Pattern 2: Terminal Color Detection with Graceful Fallback
**What:** Detect whether the terminal supports color output and fall back to plain text.
**When to use:** At script startup, before any output.
**Verified:** `[ -t 1 ]` returns false when piped (confirmed). `$TERM` is empty in non-interactive contexts (confirmed on macOS).
**Example:**
```bash
# Source: POSIX standard + macOS verification (2026-02-03)
if [ -t 1 ] && [ "${TERM:-dumb}" != "dumb" ]; then
  GREEN='\033[0;32m'
  RED='\033[0;31m'
  YELLOW='\033[1;33m'
  BLUE='\033[0;34m'
  BOLD='\033[1m'
  NC='\033[0m'
else
  GREEN=''
  RED=''
  YELLOW=''
  BLUE=''
  BOLD=''
  NC=''
fi
```
**Note:** Use `${TERM:-dumb}` (with default) instead of `"$TERM"` to handle the case where TERM is unset (not just empty). When TERM is unset, `[ "$TERM" != "dumb" ]` evaluates to true (empty string != "dumb"), which would incorrectly enable colors.

### Pattern 3: OS Detection for Install Commands
**What:** Detect macOS, Linux, and WSL to provide OS-specific install commands.
**When to use:** During dependency checking to show the correct install command.
**Verified:** `uname -s` returns "Darwin" on macOS (confirmed). WSL detection via `/proc/version` is the standard approach.
**Example:**
```bash
# Source: Universal OS Detector pattern + macOS verification (2026-02-03)
detect_os() {
  local kernel
  kernel=$(uname -s)
  case "$kernel" in
    Darwin) DETECTED_OS="macos" ;;
    Linux)
      if grep -qi microsoft /proc/version 2>/dev/null; then
        DETECTED_OS="wsl"
      else
        DETECTED_OS="linux"
      fi
      ;;
    *) DETECTED_OS="linux" ;;
  esac
}
```

### Pattern 4: Progress File for Resumable Re-runs
**What:** Track completed steps in a simple text file for idempotent re-runs.
**When to use:** After each major phase completes successfully.
**Example:**
```bash
# Source: Standard bash checkpoint pattern (multiple StackOverflow references)
PROGRESS_FILE=".setup-progress"

is_step_complete() {
  [ -f "$PROGRESS_FILE" ] && grep -q "^$1$" "$PROGRESS_FILE"
}

mark_step_complete() {
  echo "$1" >> "$PROGRESS_FILE"
}

# Usage in main flow:
if is_step_complete "dirs_created"; then
  echo "Verifying directory structure..."  # Still verify, just different message
else
  echo "Creating directory structure..."
fi
create_directory_structure
mark_step_complete "dirs_created"
```

### Pattern 5: Overwrite Prompt with Default-No
**What:** Prompt user before overwriting existing config files, defaulting to "no".
**When to use:** During config scaffolding when files already exist.
**Example:**
```bash
# Source: Standard bash prompt pattern
scaffold_file() {
  local target="$1"
  local description="$2"

  if [ -f "$target" ]; then
    # Check if stdin is a tty for interactive prompt
    if [ -t 0 ]; then
      printf "%s already exists. Overwrite? [y/N] " "$(basename "$target")"
      read -r response
      if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Kept existing:${NC} $target"
        return 0
      fi
    else
      # Non-interactive: default to no overwrite
      echo -e "${YELLOW}Kept existing:${NC} $target (non-interactive, skipping overwrite)"
      return 0
    fi
  fi
  # ... create the file ...
  echo -e "${GREEN}Created:${NC} $target"
}
```

### Anti-Patterns to Avoid
- **Using `which` instead of `command -v`:** `which` is not POSIX-standard and behaves differently across platforms (some versions print error messages, some have different exit codes). Always use `command -v`.
- **Using `grep -oP` on macOS:** macOS ships BSD grep which does not support Perl-compatible regex (`-P` flag). Use `grep -oE` (extended regex) for portable version extraction.
- **Using `echo -e` for portability:** `echo -e` behavior varies across shells and platforms. `printf` is more reliable for ANSI escape sequences. However, since this script is `#!/bin/bash` (not sh) and targets modern systems, `echo -e` is acceptable.
- **Checking `set -e` compatibility with functions:** Functions in bash inherit `set -e`, but the `||` compound command disables `set -e` for the left side. This is well-defined POSIX behavior. Use `check || { handle; }` not `check; if [ $? -ne 0 ]; then`.
- **Using `[[` conditionals without `#!/bin/bash`:** The `[[ ]]` syntax is bash-specific. Since setup.sh uses `#!/bin/bash`, this is fine. But if portability to `/bin/sh` were needed, use `[ ]` only.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Version comparison | Custom string splitting + arithmetic | `sort -V` comparison | sort -V handles multi-digit components, pre-release tags, and edge cases. Verified working on macOS Apple sort 2.3 |
| Dependency existence | `which` or `ls /usr/bin/X` | `command -v` | POSIX-standard, handles aliases, functions, and builtins correctly |
| Color support detection | Hardcoded ANSI or always-on colors | `[ -t 1 ]` tty check + TERM check | Prevents garbage output in pipes, CI, cron, and dumb terminals |
| JSON progress tracking | Custom JSON parser in bash | Line-per-step text file with grep | Bash has no native JSON support. jq adds a dependency. Text file + grep is zero-dependency |
| Cross-platform package manager detection | Checking for specific binary paths | `command -v brew` / `command -v apt` | Binary paths vary across installations (Homebrew: /opt/homebrew vs /usr/local) |

**Key insight:** This phase is pure bash scripting with no external library dependencies. Every pattern uses standard Unix tools available on all three target platforms. The complexity is in the orchestration (check-all-then-fail, progress tracking, overwrite prompts), not in any single operation.

## Common Pitfalls

### Pitfall 1: Python Version Comparison Bug (CRITICAL)
**What goes wrong:** The version comparison `[ "$major" -ge 3 ] && [ "$minor" -ge 12 ]` incorrectly rejects Python 4.1 (major=4 >= 3 OK, minor=1 < 12 FAIL).
**Why it happens:** The `&&` requires BOTH conditions to be true independently, but semantically "4.1 >= 3.12" should pass because major is strictly greater than 3.
**How to avoid:** Use `sort -V` for version comparison, or use proper numeric logic:
```bash
# WRONG (rejects 4.1):
[ "$major" -ge 3 ] && [ "$minor" -ge 12 ]

# CORRECT option 1 -- sort -V (simplest, verified on macOS):
version_gte() {
  [ "$(printf '%s\n' "$1" "$2" | sort -V | head -1)" = "$2" ]
}
version_gte "$found_version" "3.12"

# CORRECT option 2 -- arithmetic:
[ "$major" -gt 3 ] || { [ "$major" -eq 3 ] && [ "$minor" -ge 12 ]; }
```
**Verified:** Tested on macOS 2026-02-03. `sort -V` correctly orders "3.12" before "4.1". The `&&`-only approach fails for Python 4.1.
**Warning signs:** Tests only pass because current Python is 3.12-3.14 (minor >= 12). Bug would surface with Python 4.0+.
**Impact on Plan 01:** Plan 01 Task 1 step 10 prescribes the buggy pattern. The planner should use `sort -V` or the correct arithmetic pattern instead.

### Pitfall 2: set -e Exits on First Failed Dependency Check
**What goes wrong:** With `set -e` active, the first `command -v python3` failure exits the entire script before checking uv and bun.
**Why it happens:** `set -e` causes bash to exit on any command with non-zero exit code.
**How to avoid:** Use `|| { ... }` guards on each check, or wrap checks in a function that uses `|| true` per check and accumulates failures.
**Verified:** Tested on macOS bash. `false || { count=$((count + 1)); }` does NOT trigger `set -e` exit.
**Warning signs:** Running setup.sh with only Python missing shows Python error but not uv/bun status.

### Pitfall 3: TERM Unset vs Empty vs "dumb"
**What goes wrong:** When TERM is completely unset (not empty string), `[ "$TERM" != "dumb" ]` evaluates to true (empty != "dumb"), incorrectly enabling colors.
**Why it happens:** In some non-interactive contexts (CI, cron, some SSH sessions), TERM is unset rather than set to "dumb".
**How to avoid:** Use `${TERM:-dumb}` to default unset TERM to "dumb":
```bash
if [ -t 1 ] && [ "${TERM:-dumb}" != "dumb" ]; then
  # Enable colors
fi
```
**Warning signs:** ANSI escape codes appearing in CI logs or redirected output.

### Pitfall 4: read Prompt Hangs in Non-Interactive Context
**What goes wrong:** `read -r -p "Install? [y/N] "` hangs waiting for input when stdin is not a tty (e.g., piped input, CI).
**Why it happens:** `read` blocks on stdin. In non-interactive contexts, stdin may be /dev/null or a pipe with no data.
**How to avoid:** Check `[ -t 0 ]` (stdin is a tty) before prompting. If not interactive, default to "N" (skip install).
**Verified:** Tested on macOS. `echo "" | bash -c 'read -r response; echo "[$response]"'` returns empty string, which correctly defaults to "N".
**Warning signs:** Script hangs when run in CI or piped context.

### Pitfall 5: .setup-progress Not Gitignored
**What goes wrong:** `.setup-progress` file gets committed to the repo, polluting git history with user-specific setup state.
**Why it happens:** The file is not covered by any existing .gitignore pattern.
**Verified:** `git check-ignore .setup-progress` returns exit code 1 (NOT ignored) on this repo. Must be added to .gitignore.
**How to avoid:** Add `.setup-progress` explicitly to .gitignore in Plan 02 Task 2.

### Pitfall 6: Homebrew Not Installed When Offering brew install
**What goes wrong:** Script offers "Install Python via Homebrew? [y/N]" on macOS, user says yes, but Homebrew is not installed. The `brew install` command fails.
**Why it happens:** macOS detection assumes Homebrew is available.
**How to avoid:** Check `command -v brew` before offering Homebrew-based install. If Homebrew is missing, provide the Homebrew installation URL first, then the dep install command.
```bash
if [ "$DETECTED_OS" = "macos" ]; then
  if command -v brew &>/dev/null; then
    install_cmd="brew install python@3.12"
  else
    install_cmd="Install Homebrew first: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\" then: brew install python@3.12"
  fi
fi
```
**This is a Claude's Discretion item** -- CONTEXT.md leaves "whether to check for Homebrew/apt availability before offering auto-install" to discretion. **Recommendation: Do check.** It prevents a confusing failure mid-install.

### Pitfall 7: uv sync Fails When pyproject.toml Is Missing
**What goes wrong:** `uv sync` is called but pyproject.toml doesn't exist in the current directory (e.g., user ran setup.sh from wrong directory).
**Why it happens:** setup.sh uses `PROJECT_ROOT` but `uv sync` runs in cwd.
**How to avoid:** Always `cd "$PROJECT_ROOT"` before `uv sync`, or pass `--project "$PROJECT_ROOT"` flag. Verify pyproject.toml exists before running.

## Code Examples

### Example 1: Complete Version Comparison Function (Verified)
```bash
# Source: Verified on macOS 26.2, Apple sort 2.3 (2026-02-03)
# Returns 0 if $1 >= $2, 1 otherwise
version_gte() {
  [ "$(printf '%s\n' "$1" "$2" | sort -V | head -1)" = "$2" ]
}

# Usage:
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
if version_gte "$python_version" "3.12"; then
  echo "Python $python_version meets minimum (>= 3.12)"
fi
```

### Example 2: Complete check_dependency Function (Template)
```bash
# Source: Composite pattern from research
check_dependency() {
  local cmd="$1"
  local name="$2"
  local min_version="$3"

  if ! command -v "$cmd" &>/dev/null; then
    printf "  ${RED}[MISSING]${NC} %s (not found)\n" "$name"
    return 1
  fi

  # Get version
  local found_version=""
  case "$cmd" in
    python3) found_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1) ;;
    uv) found_version=$(uv --version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1) ;;
    bun) found_version=$(bun --version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1) ;;
  esac

  # Check minimum version if specified
  if [ -n "$min_version" ] && [ -n "$found_version" ]; then
    if ! version_gte "$found_version" "$min_version"; then
      printf "  ${RED}[MISSING]${NC} %s %s (>= %s required, found %s)\n" "$name" "$found_version" "$min_version" "$found_version"
      return 1
    fi
  fi

  if [ -n "$min_version" ]; then
    printf "  ${GREEN}[OK]${NC} %s %s (>= %s required)\n" "$name" "$found_version" "$min_version"
  else
    printf "  ${GREEN}[OK]${NC} %s %s\n" "$name" "$found_version"
  fi
  return 0
}
```

### Example 3: Full .setup-progress Flow (Template)
```bash
# Source: Standard checkpoint pattern
PROGRESS_FILE="$PROJECT_ROOT/.setup-progress"

is_step_complete() {
  [ -f "$PROGRESS_FILE" ] && grep -q "^$1$" "$PROGRESS_FILE"
}

mark_step_complete() {
  echo "$1" >> "$PROGRESS_FILE"
}

show_progress() {
  if [ -f "$PROGRESS_FILE" ]; then
    local total_steps=4  # deps, dirs, config, python
    local completed
    completed=$(wc -l < "$PROGRESS_FILE" | tr -d ' ')
    echo -e "${YELLOW}Resuming setup...${NC} ($completed/$total_steps steps completed)"
    while IFS= read -r step; do
      echo -e "  ${GREEN}[done]${NC} $step"
    done < "$PROGRESS_FILE"
  fi
}
```

### Example 4: Complete OS Detection with Package Manager Check (Template)
```bash
# Source: Composite from uname + Homebrew patterns (verified macOS 2026-02-03)
detect_os() {
  local kernel
  kernel=$(uname -s)
  case "$kernel" in
    Darwin)
      DETECTED_OS="macos"
      if command -v brew &>/dev/null; then
        PKG_MANAGER="brew"
      else
        PKG_MANAGER="none"
      fi
      ;;
    Linux)
      if grep -qi microsoft /proc/version 2>/dev/null; then
        DETECTED_OS="wsl"
      else
        DETECTED_OS="linux"
      fi
      if command -v apt &>/dev/null; then
        PKG_MANAGER="apt"
      else
        PKG_MANAGER="none"
      fi
      ;;
    *)
      DETECTED_OS="linux"
      PKG_MANAGER="none"
      ;;
  esac
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `which` for command detection | `command -v` | POSIX standard (long-standing) | `which` is unreliable across platforms; `command -v` is POSIX-guaranteed |
| Custom arithmetic version compare | `sort -V` | GNU coreutils 7.0 (2008), Apple sort includes it | Eliminates bugs in multi-component version comparison |
| Always-on ANSI colors | `[ -t 1 ]` + TERM check | Best practice since 2015+ | Prevents garbage output in CI/pipes/cron |
| grep -oP (PCRE) | grep -oE (ERE) | macOS adoption of BSD grep | macOS BSD grep lacks -P; -oE is universally supported |
| `echo -e` for escape codes | `printf` for portability | Long-standing best practice | `echo -e` behavior varies; printf is POSIX-standard |

**Deprecated/outdated:**
- **`which`:** Not POSIX-standard. Output format varies. Some systems alias it. Use `command -v`.
- **`grep -oP` on macOS:** BSD grep does not support PCRE. Use `grep -oE` with extended regex.
- **`set -e` without understanding compound commands:** The `||` compound command disables `set -e` for the left side. This is well-defined but often misunderstood.

## Existing Code Analysis

### Current setup.sh (389 lines)
The existing script has several reusable components:

**Keep as-is:**
- `create_dir()` function (lines 23-30) -- idempotent mkdir with reporting
- Directory list for fin-guru-private/ (lines 36-47) -- matches SETUP-02 requirements
- user-profile.yaml template (lines 74-131) -- complete YAML template
- fin-guru-private/README.md content (lines 139-178) -- documentation

**Must change:**
- Color definitions (lines 17-20) -- add tty/TERM detection
- No CLI argument parsing (--check-deps-only, --help missing)
- No OS detection function
- uv check on line 200 is embedded mid-flow, not in a proper dependency checker
- bun check on line 281 is embedded mid-flow, checks only existence
- No Python version check at all
- No .setup-progress tracking
- No overwrite prompts for existing config files
- Steps 8-9 (symlink creation) should be removed (deferred to Phase 3)
- Step 10 (onboarding wizard) should be removed (Phase 3 scope)
- Step 11 (MCP Launchpad) should be removed (optional, onboarding scope)

**Existing integration test** (`tests/integration/test_setup_onboarding_integration.sh`, 196 lines):
- Tests idempotency (runs setup.sh 3 times)
- Verifies directory structure creation
- Verifies user profile template creation
- Uses a mock onboarding CLI to prevent interactive prompts
- This test will need updating after the rewrite to reflect new behavior (no onboarding call, --check-deps-only, .setup-progress)

## Claude's Discretion Recommendations

The CONTEXT.md lists these as Claude's discretion. Here are research-informed recommendations:

### 1. Exact Step Ordering Within Setup
**Recommendation:** deps -> dirs -> config -> python_deps -> summary
- Dependencies MUST be first (CONTEXT.md locked decision: check-all-then-fail before any modification)
- Directories before config files (config files are written INTO the directory structure)
- Python deps after config (uv sync needs pyproject.toml, not config files, but logically belongs after environment setup)
- Summary last (needs to recap what happened)
**Confidence:** HIGH -- follows dependency ordering principle

### 2. Progress File Format (.setup-progress)
**Recommendation:** One step name per line, plain text
```
deps_checked
dirs_created
config_scaffolded
python_deps_installed
```
- Simplest format that's grep-able with zero dependencies
- No timestamps needed (setup is fast, order is implicit from line position)
- No JSON (would require jq or python to parse)
- Step names are human-readable for manual inspection
- Manual reset: `rm .setup-progress` (per CONTEXT.md decision: no --reset flag)
**Confidence:** HIGH -- zero-dependency, grep-compatible

### 3. Directory Structure Validation Depth
**Recommendation:** Verify one level deep -- check that expected subdirectories of fin-guru-private/ exist
- Always run the directory creation function (even on re-run) since `mkdir -p` is idempotent
- On re-run, change messaging from "Creating..." to "Verifying..."
- Do NOT validate file contents or permissions (over-engineering for a setup script)
- DO verify critical subdirectories exist (if user deleted one, recreate it)
**Confidence:** HIGH -- matches CONTEXT.md "verify state of skipped items"

### 4. Check for Homebrew/apt Availability Before Offering Auto-Install
**Recommendation:** YES, check before offering
- On macOS: check `command -v brew` before offering `brew install`
- On Linux/WSL: check `command -v apt` before offering `apt install`
- If package manager not found: show manual install URL instead
- Prevents confusing "command not found: brew" error during auto-install
**Confidence:** HIGH -- prevents user frustration, trivial to implement

### 5. Exact Error Message Wording
**Recommendation:** Follow these patterns:
- Missing dep: `[MISSING] Python (not found)` or `[MISSING] Python 3.10.1 (>= 3.12 required, found 3.10.1)`
- Found dep: `[OK] Python 3.14.0 (>= 3.12 required)`
- Install prompt: `Python 3.12 not found. Install via Homebrew? [y/N]`
- Install success: `Installed: Python 3.12 via Homebrew`
- Install declined: `Skipped: Python 3.12 (user declined)`
- Already done: `Already exists: fin-guru-private/`
- Overwrite prompt: `user-profile.yaml already exists. Overwrite? [y/N]`
- Kept existing: `Kept existing: user-profile.yaml`
**Confidence:** MEDIUM -- wording is subjective, but patterns are consistent

## Open Questions

1. **Should the script verify Homebrew is up to date before using it?**
   - Running `brew update` before `brew install` ensures the latest formula is available, but adds 10-30 seconds.
   - Recommendation: Do NOT run `brew update` -- it's slow and the user can do it themselves. Just run `brew install`.
   - Confidence: MEDIUM

2. **Should .setup-progress be relative to PROJECT_ROOT or cwd?**
   - If the user runs `./setup.sh` from a different directory, `.setup-progress` goes to cwd, not project root.
   - Recommendation: Always write to `$PROJECT_ROOT/.setup-progress`. The script already sets PROJECT_ROOT.
   - Confidence: HIGH

3. **Should the integration test be updated in this phase or Phase 4?**
   - The existing `test_setup_onboarding_integration.sh` tests behaviors that will change (onboarding call, idempotency patterns).
   - Recommendation: Update the integration test in Plan 02 as part of the restructuring. Broken tests should not persist.
   - Confidence: MEDIUM

## Sources

### Primary (HIGH confidence)
- **Local verification** (macOS 26.2, bash, 2026-02-03) -- sort -V, grep -oE, command -v, [ -t 1 ], uname -s, version extraction patterns all tested directly
- **POSIX standard** -- command -v, [ ] test, printf, read, set -e behavior with compound commands
- **Existing setup.sh** (389 lines) -- analyzed for reusable components and gaps
- **Existing integration test** (196 lines) -- analyzed for test patterns to preserve

### Secondary (MEDIUM confidence)
- **Baeldung: How to Check Whether Terminal Can Print Colors** -- tput vs ANSI escape approaches
- **StackOverflow: How to compare a program's version in a shell script** -- sort -V and arithmetic approaches
- **Unix StackExchange: All-round portable terminal color support check** -- tput setaf portability
- **kata198/bash-resume GitHub** -- Checkpoint/resume pattern for bash scripts
- **mdeacey/universal-os-detector GitHub** -- Cross-platform OS detection patterns
- **Detect OS and Distro in Bash (wuhrr.wordpress.com)** -- uname + /etc/os-release patterns

### Tertiary (LOW confidence)
- **Medium: Mastering Bash Scripting for DevOps** -- General best practices (confirmed against POSIX docs)
- **dev.co: How Do You Write Idempotent Bash Deployment Scripts** -- Idempotency patterns (generic)
- **cursorrules.org: Bash Best Practices and Coding Standards** -- Directory structure and naming (generic)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All tools verified on target platform (macOS 26.2), all POSIX-standard
- Architecture: HIGH - Function structure follows established bash patterns, verified on macOS
- Pitfalls: HIGH - Version comparison bug verified with test. set -e interaction verified. TERM edge case verified. .gitignore gap verified with git check-ignore
- Code examples: HIGH - All examples tested on macOS 26.2 (sort -V, grep -oE, command -v, tty detection)

**Research date:** 2026-02-03
**Valid until:** 2026-03-05 (30 days -- bash tooling is extremely stable, patterns don't change)
