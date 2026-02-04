# Phase 2: Setup Automation & Dependency Checking - Context

**Gathered:** 2026-02-03
**Status:** Ready for planning

<domain>
## Phase Boundary

First-run setup script (`setup.sh`) that checks dependencies, creates the `fin-guru-private/` directory structure, and scaffolds config files. A new user runs one command after cloning and gets a working environment. Onboarding wizard (Phase 3) is separate -- setup.sh prepares the environment, it does not collect financial profile data.

</domain>

<decisions>
## Implementation Decisions

### Output & messaging
- Step-by-step verbose output -- every action narrated as it happens ("Installing X... done. Creating Y... done.")
- Color-coded terminal output: green for success, red for errors, yellow for warnings. Detect terminal color support, fall back to plain text
- Full summary at the end: recap of what was installed, created, skipped, and the next command to run
- `--check-deps-only` flag shows checklist format: each dependency with checkmark/X and version found (e.g., "Python 3.12.1 (>= 3.12 required)")
- No version upgrade nagging -- if minimum is met, show green and move on

### Failure behavior
- Check ALL dependencies before failing -- run through the full dependency list, show the complete report, then exit with error if anything is missing
- Exact install commands per detected OS (macOS: Homebrew, Linux: apt, WSL: apt)
- Stop on ANY failure -- every step is treated as critical. No partial success states
- No version upgrade suggestions for deps that meet minimum

### Idempotency
- On re-run, show what's already done step-by-step ("Already exists: fin-guru-private/" etc.) -- full visibility of current state
- Track progress in `.setup-progress` file. On re-run, skip completed steps and resume ("Resuming from step 4/7...")
- No `--reset` or `--force` flag -- user can delete `.setup-progress` manually if needed
- If existing config files found (e.g., user-profile.yaml): prompt before overwrite ("user-profile.yaml exists. Overwrite? [y/N]"), default to no
- Verify state of skipped items -- not just existence but expected structure (e.g., fin-guru-private/ has expected subdirectories)

### Platform & prerequisites
- Support macOS, Linux (Ubuntu/Debian), and Windows WSL
- Assume ONLY git and bash are pre-installed -- everything else gets checked
- Offer to install missing dependencies: prompt "Python 3.12 not found. Install via Homebrew? [y/N]" and run the install if user agrees
- Minimum Python version: 3.12+
- Other dependencies checked: uv, Bun

### Claude's Discretion
- Exact step ordering within setup
- Progress file format (.setup-progress)
- Directory structure validation depth
- Whether to check for Homebrew/apt availability before offering auto-install
- Exact error message wording

</decisions>

<specifics>
## Specific Ideas

No specific requirements -- open to standard approaches. The key principle is: verbose, colorful, fail-hard, but check everything first before failing.

</specifics>

<deferred>
## Deferred Ideas

None -- discussion stayed within phase scope.

</deferred>

---

*Phase: 02-setup-automation*
*Context gathered: 2026-02-03*
