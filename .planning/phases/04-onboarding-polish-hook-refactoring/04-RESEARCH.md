# Phase 4: Onboarding Polish & Hook Refactoring - Research

**Researched:** 2026-02-02
**Domain:** Python SIGINT handling for CLI save/resume, Bun TypeScript hook refactoring, Claude Code hook configuration
**Confidence:** HIGH

## Summary

Phase 4 has two distinct workstreams: (A) making the Phase 3 onboarding wizard interruption-safe with progress persistence, and (B) completing the Bun TypeScript hook migration with a performance test suite. Research reveals that the hook workstream is nearly complete -- all three hooks are already ported to TypeScript and only configuration cleanup and dead file removal remain. The onboarding workstream requires a focused SIGINT handler pattern with JSON persistence, which is well-established in Python.

The critical discovery from codebase inspection is that the hook migration is 80%+ done. `load-fin-core-config.ts` is fully ported and directly invoked. `post-tool-use-tracker.ts` is fully ported and directly invoked, but its dead `.sh` predecessor (178 lines) still exists on disk. `skill-activation-prompt.ts` is fully ported but still called through a 6-line bash wrapper (`skill-activation-prompt.sh`) that pipes stdin. The remaining hook work is: (1) update settings.json to call `skill-activation-prompt.ts` directly via `bun run`, (2) delete two dead shell files, and (3) write a Bun test suite with `< 500ms` performance assertions for all three hooks.

For onboarding save/resume (ONBD-03), the standard Python approach is: register a `signal.signal(signal.SIGINT, handler)` that sets a flag, check the flag between questionary prompts, and save `OnboardingState` to `.onboarding-progress.json` using atomic write (write-to-temp then rename). On restart, check for the progress file and resume from `current_section`. questionary's `.ask()` returns `None` on Ctrl+C, which already provides a natural interrupt point -- but the SIGINT handler adds a safety net for saving even mid-prompt.

**Primary recommendation:** Split Phase 4 into two parallel tracks: (1) a quick hook cleanup plan (settings.json update, dead file deletion, Bun performance test suite), and (2) an onboarding save/resume plan (SIGINT handler, progress file schema, resume logic). The hook track is small and low-risk. The onboarding track depends on Phase 3 output but the patterns are standard.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| signal (stdlib) | Python 3.12 | SIGINT handler registration | Built-in, no dependencies; standard approach for Ctrl+C handling |
| json (stdlib) | Python 3.12 | Progress file serialization | .onboarding-progress.json persistence |
| atexit (stdlib) | Python 3.12 | Backup save on normal exit | Ensures progress saved even on clean exit |
| pathlib (stdlib) | Python 3.12 | Atomic file operations via rename | tempfile + rename pattern for crash-safe writes |
| bun:test | Bun 1.3.7 | Hook test runner | Already used in existing test suite (97+ tests) |

### Supporting (Already in Project)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pydantic | 2.10.6+ | OnboardingState model serialization | `.model_dump_json()` for progress file, `.model_validate_json()` for loading |
| questionary | 2.1.1 | Returns None on Ctrl+C | Natural interrupt detection between prompts |
| bun | 1.3.7 | TypeScript runtime for hooks | Already installed, all hooks already use shebang `#!/usr/bin/env bun` |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| signal.signal() | try/except KeyboardInterrupt | Signal handler saves BEFORE exception propagates; try/except only catches after questionary returns None, which may miss saves during prompt_toolkit rendering |
| JSON progress file | SQLite | Overkill for a single document; JSON is human-readable and debuggable |
| atexit + signal.signal() | contextlib.ExitStack | Less explicit; signal + atexit is the standard two-layer safety net |
| Manual Date.now() timing | Bun's built-in performance hooks | Bun has no built-in `expect.toCompleteWithin()` assertion; manual timing with `Date.now()` or `performance.now()` is the standard approach |

**Installation:**
No new dependencies required. All tools are either Python stdlib or already in the project.

## Architecture Patterns

### Recommended Project Structure
```
src/
  cli/
    onboarding_wizard.py     # MODIFIED: Add SIGINT handler, progress load/save
  models/
    onboarding_inputs.py     # MODIFIED: Add .to_progress_json() / .from_progress_json() methods

.claude/
  hooks/
    load-fin-core-config.ts           # EXISTING: No changes needed
    skill-activation-prompt.ts        # EXISTING: No changes needed (already ported)
    skill-activation-prompt.sh        # DELETE: Dead bash wrapper
    post-tool-use-tracker.ts          # EXISTING: No changes needed (already ported)
    post-tool-use-tracker.sh          # DELETE: Dead bash original
    tests/
      test_hook_performance.test.ts   # NEW: Performance assertions for all 3 hooks
  settings.json                       # MODIFIED: Update UserPromptSubmit to call .ts directly
```

### Pattern 1: Two-Layer SIGINT Safety Net
**What:** Register both `signal.signal(signal.SIGINT, handler)` and `atexit.register(save_fn)` for belt-and-suspenders progress saving.
**When to use:** In the onboarding wizard main entry point, before any prompts begin.
**Example:**
```python
# Source: Python stdlib documentation + standard pattern
import signal
import atexit
import json
from pathlib import Path

PROGRESS_FILE = Path(".onboarding-progress.json")
_interrupted = False

def _sigint_handler(signum, frame):
    """Handle Ctrl+C: set flag, save progress, re-raise."""
    global _interrupted
    _interrupted = True
    # Don't save here -- let the main loop handle it
    # This avoids race conditions with questionary's own Ctrl+C handling
    raise KeyboardInterrupt  # Let Python's default behavior proceed

def setup_interrupt_handling(state_getter):
    """
    Register SIGINT handler and atexit save.

    Args:
        state_getter: Callable that returns current OnboardingState
    """
    def save_on_exit():
        state = state_getter()
        if state and len(state.completed_sections) > 0:
            save_progress(state)

    signal.signal(signal.SIGINT, _sigint_handler)
    atexit.register(save_on_exit)
```

### Pattern 2: Atomic JSON Progress File
**What:** Write progress to a temp file then rename for crash safety. Load with validation.
**When to use:** Every time progress needs to be saved (after each section, on interrupt, on exit).
**Example:**
```python
# Source: Standard atomic write pattern
import tempfile
import json
from pathlib import Path

PROGRESS_FILE = Path(".onboarding-progress.json")

def save_progress(state) -> None:
    """Atomically save progress to .onboarding-progress.json."""
    data = state.model_dump(mode="json")
    # Write to temp file in same directory (same filesystem for atomic rename)
    tmp_fd, tmp_path = tempfile.mkstemp(
        dir=PROGRESS_FILE.parent,
        suffix=".tmp",
        prefix=".onboarding-progress-"
    )
    try:
        with open(tmp_fd, "w") as f:
            json.dump(data, f, indent=2)
        Path(tmp_path).rename(PROGRESS_FILE)
    except Exception:
        Path(tmp_path).unlink(missing_ok=True)
        raise

def load_progress():
    """Load progress from file, return None if not found or corrupt."""
    if not PROGRESS_FILE.exists():
        return None
    try:
        data = json.loads(PROGRESS_FILE.read_text())
        return OnboardingState.model_validate(data)
    except (json.JSONDecodeError, ValidationError):
        # Corrupt file -- start fresh
        return None
```

### Pattern 3: Section-Level Resume
**What:** On restart, check progress file, skip completed sections, resume from `current_section`.
**When to use:** At wizard startup, before entering the section loop.
**Example:**
```python
# Source: Standard state machine pattern
from src.models.onboarding_inputs import OnboardingState, SectionName

SECTION_ORDER = list(SectionName)
SECTION_RUNNERS = {
    SectionName.liquid_assets: run_liquid_assets_section,
    SectionName.investments: run_investments_section,
    # ... all 8 sections
}

def run_wizard():
    """Main wizard loop with resume support."""
    # Try to resume from saved progress
    state = load_progress()
    if state and len(state.completed_sections) > 0:
        print(f"Resuming from section: {state.current_section.value}")
        print(f"Completed: {len(state.completed_sections)} of {len(SECTION_ORDER)} sections")
        resume = questionary.confirm("Resume from where you left off?", default=True).ask()
        if not resume:
            state = OnboardingState.create_new()
    else:
        state = OnboardingState.create_new()

    # Run sections from current position
    start_idx = SECTION_ORDER.index(state.current_section)
    for section in SECTION_ORDER[start_idx:]:
        try:
            runner = SECTION_RUNNERS[section]
            state = runner(state)
            save_progress(state)  # Save after each completed section
        except KeyboardInterrupt:
            save_progress(state)
            print(f"\nProgress saved. Run the wizard again to resume.")
            return
```

### Pattern 4: Bun Hook Performance Test with Timing Assertion
**What:** Spawn the hook as a child process, measure wall-clock time, assert < 500ms.
**When to use:** For each of the 3 hooks in the performance test suite.
**Example:**
```typescript
// Source: Existing test pattern from test_load_fin_core_config.test.ts + timing
import { describe, it, expect } from "bun:test";
import { spawn } from "child_process";
import { join } from "path";

const HOOK_PATH = join(import.meta.dir, "../load-fin-core-config.ts");
const MAX_EXECUTION_MS = 500;

async function runHookTimed(input: any): Promise<{
  stdout: string;
  stderr: string;
  exitCode: number;
  durationMs: number;
}> {
  const start = performance.now();
  return new Promise((resolve, reject) => {
    const proc = spawn("bun", [HOOK_PATH], {
      env: { ...process.env }
    });
    let stdout = "";
    let stderr = "";

    proc.stdout.on("data", (data) => { stdout += data.toString(); });
    proc.stderr.on("data", (data) => { stderr += data.toString(); });

    proc.stdin.write(JSON.stringify(input));
    proc.stdin.end();

    proc.on("close", (code) => {
      const durationMs = performance.now() - start;
      resolve({ stdout, stderr, exitCode: code || 0, durationMs });
    });

    proc.on("error", reject);
  });
}

describe("hook performance", () => {
  it("should complete in under 500ms", async () => {
    const result = await runHookTimed({
      session_id: "perf-test",
      event: "session_start"
    });
    expect(result.exitCode).toBe(0);
    expect(result.durationMs).toBeLessThan(MAX_EXECUTION_MS);
  });
});
```

### Pattern 5: Direct Bun Invocation in settings.json (Replacing Bash Wrapper)
**What:** Call TypeScript hooks directly with `bun run` instead of through a bash wrapper.
**When to use:** For skill-activation-prompt.ts -- the last hook still using a bash intermediary.
**Example:**
```json
{
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
```
**Why this works:** The existing `load-fin-core-config.ts` already uses this exact pattern (`bun run $CLAUDE_PROJECT_DIR/.claude/hooks/load-fin-core-config.ts`) and works correctly. The `.ts` file already handles stdin reading identically to the `.sh` wrapper. The bash wrapper (`cat | bun skill-activation-prompt.ts`) simply pipes stdin, which `bun run` handles natively since Claude Code pipes hook input to stdin automatically.

### Anti-Patterns to Avoid
- **Catching SIGINT inside questionary:** Do NOT try to override prompt_toolkit's internal signal handling. questionary already returns None on Ctrl+C -- work with that, not against it.
- **Saving progress synchronously in the signal handler:** Signal handlers should be fast. Set a flag, let the main loop save. Or use `atexit` for the actual write.
- **Using `os._exit()` in signal handler:** This skips atexit handlers and file buffer flushes. Use `sys.exit()` or re-raise `KeyboardInterrupt`.
- **Testing hook performance with cold Bun starts:** The first `bun run` invocation may be slower due to JIT warmup. Run a warmup iteration before the timed test, or set a slightly higher threshold (500ms is generous for these hooks).
- **Keeping dead bash files "just in case":** The .sh files are fully replaced by .ts files. Keeping them creates confusion about which is canonical.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Progress file serialization | Custom JSON serializer | Pydantic `model_dump(mode="json")` / `model_validate()` | Handles datetime serialization, enums, nested models automatically |
| Atomic file write | Manual open/write/close | tempfile.mkstemp + Path.rename | rename is atomic on same filesystem; prevents corrupt partial writes |
| Ctrl+C detection in prompts | Custom keyboard listener | questionary `.ask()` returns None | Already built into questionary; just check the return value |
| Hook stdin reading | Custom stdin parser | Existing pattern in all 3 hooks | Each .ts file already has complete stdin → JSON parsing with TTY detection |
| Test helper for spawning hooks | New test utility | Existing `runHook()` pattern from tests/ | Already used across all 4 test files (97+ tests); proven, debugged |

**Key insight:** The hook migration is already done at the code level. What remains is configuration hygiene (settings.json update), cleanup (delete dead .sh files), and verification (performance test suite). The onboarding work adds save/resume on top of Phase 3's wizard using stdlib patterns -- no new libraries needed.

## Common Pitfalls

### Pitfall 1: questionary Swallows SIGINT Before Your Handler Runs
**What goes wrong:** You register a SIGINT handler expecting it to fire on Ctrl+C, but questionary (via prompt_toolkit) catches the signal first, returns None from `.ask()`, and your handler never fires.
**Why it happens:** prompt_toolkit installs its own SIGINT handler during prompt input. When the prompt is active, Ctrl+C is caught by prompt_toolkit, not your handler.
**How to avoid:** Use a dual strategy: (1) check for None return from `.ask()` as the PRIMARY interrupt detection, (2) use SIGINT handler only as a BACKUP for interrupts that happen between prompts (e.g., during processing). (3) Use `atexit` as a final safety net.
**Warning signs:** SIGINT handler never fires during testing because questionary always handles it first.

### Pitfall 2: Progress File Left Behind After Successful Completion
**What goes wrong:** User completes onboarding successfully, but `.onboarding-progress.json` still exists. Next time they run the wizard, it tries to resume a completed session.
**Why it happens:** The progress file is saved after every section but never deleted on successful completion.
**How to avoid:** Delete `.onboarding-progress.json` after the wizard completes successfully (after all config files are generated). Only save progress when the wizard is interrupted or exits early.
**Warning signs:** Wizard always asks "Resume from where you left off?" even after successful completion.

### Pitfall 3: settings.json Hook Order Matters
**What goes wrong:** Updating the UserPromptSubmit hook command breaks other hooks or causes double execution.
**Why it happens:** settings.json hooks fire all matching handlers for an event. If you add a new entry instead of replacing the old one, both fire.
**How to avoid:** Replace the existing `skill-activation-prompt.sh` command in-place. Do NOT add a second UserPromptSubmit entry. Verify with `/hooks` command after changing.
**Warning signs:** Skill activation messages appear twice, or errors about missing .sh file.

### Pitfall 4: Bun Cold Start Exceeds 500ms on First Run
**What goes wrong:** Performance test fails intermittently because the first hook invocation takes 600-800ms due to Bun JIT compilation and module resolution.
**Why it happens:** Bun compiles TypeScript on first execution. Subsequent runs use cached compilation.
**How to avoid:** In the performance test, add a warmup invocation before the timed run. Or measure the average of 3 runs. The 500ms threshold is per-invocation in production, where Bun's transpile cache is warm.
**Warning signs:** First test run fails, subsequent runs pass. CI failures that don't reproduce locally.

### Pitfall 5: Dead .sh Files Confuse Future Developers
**What goes wrong:** Someone sees `post-tool-use-tracker.sh` (178 lines of bash+jq) and thinks it's the canonical implementation. They modify it, but nothing changes because the .ts version is what actually runs.
**Why it happens:** The .sh files were the original implementations and are still on disk.
**How to avoid:** Delete dead .sh files as part of this phase. The .ts files ARE the implementations. CONFIG.md and README.md may reference .sh paths -- update those too.
**Warning signs:** Changes to .sh files have no effect. Two files for the same hook with different logic.

### Pitfall 6: Existing 365+ Tests Break from Unrelated Changes
**What goes wrong:** Modifying the onboarding wizard code or hook configuration causes pytest failures in the existing test suite.
**Why it happens:** Tests may import from modified modules, or rely on file paths that change.
**How to avoid:** (1) Run the full pytest suite before AND after changes: `uv run pytest tests/python/ -x -q`. (2) The hook changes (settings.json, deleting .sh files) should NOT affect Python tests at all. (3) The onboarding changes only modify files created in Phase 3 -- no existing test imports should break.
**Warning signs:** Import errors in test files, missing module errors.

## Code Examples

Verified patterns from the existing codebase and official documentation:

### Progress File Schema (.onboarding-progress.json)
```json
{
  "current_section": "cash_flow",
  "completed_sections": ["liquid_assets", "investments"],
  "data": {
    "liquid_assets": {
      "total": 15000.0,
      "accounts_count": 3,
      "average_yield": 0.045,
      "structure": null
    },
    "investments": {
      "total_value": 100000.0,
      "allocation_strategy": "aggressive_growth",
      "risk_tolerance": "aggressive"
    }
  },
  "started_at": "2026-02-02T10:30:00Z"
}
```

### Updating settings.json UserPromptSubmit Hook
```json
{
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
```
**Source:** Verified pattern from existing SessionStart hook in `.claude/settings.json` (line 8), which already uses `bun run $CLAUDE_PROJECT_DIR/.claude/hooks/load-fin-core-config.ts` successfully.

### Verifying stdin Piping Works Without Bash Wrapper
```bash
# Current (via bash wrapper):
#   skill-activation-prompt.sh: cat | bun skill-activation-prompt.ts
#
# Replacement (direct bun run):
#   bun run .claude/hooks/skill-activation-prompt.ts
#
# Both receive JSON on stdin from Claude Code. The .ts file reads stdin
# using process.stdin events (lines 57-83 of skill-activation-prompt.ts).
# bun run passes stdin through transparently.
```
**Source:** Verified by reading `skill-activation-prompt.ts` lines 57-83 and comparing with `load-fin-core-config.ts` lines 137-157, which uses the identical stdin reading pattern and already works with direct `bun run` invocation.

### Bun Performance Test Structure
```typescript
// File: .claude/hooks/tests/test_hook_performance.test.ts
import { describe, it, expect } from "bun:test";
import { spawn } from "child_process";
import { join } from "path";

const HOOKS_DIR = join(import.meta.dir, "..");
const MAX_MS = 500;

// Reusable timed runner
async function timeHook(
  hookPath: string,
  input: Record<string, unknown>
): Promise<{ exitCode: number; durationMs: number }> {
  const start = performance.now();
  return new Promise((resolve) => {
    const proc = spawn("bun", [hookPath], { env: { ...process.env } });
    proc.stdin.write(JSON.stringify(input));
    proc.stdin.end();
    proc.on("close", (code) => {
      resolve({
        exitCode: code || 0,
        durationMs: performance.now() - start,
      });
    });
  });
}

describe("Hook Performance (< 500ms)", () => {
  // Warmup run to prime Bun's transpile cache
  it("warmup: prime bun cache", async () => {
    await timeHook(join(HOOKS_DIR, "load-fin-core-config.ts"), {
      session_id: "warmup", event: "session_start"
    });
  });

  it("load-fin-core-config.ts completes in < 500ms", async () => {
    const r = await timeHook(join(HOOKS_DIR, "load-fin-core-config.ts"), {
      session_id: "perf", event: "session_start"
    });
    expect(r.exitCode).toBe(0);
    expect(r.durationMs).toBeLessThan(MAX_MS);
  });

  it("skill-activation-prompt.ts completes in < 500ms", async () => {
    const r = await timeHook(join(HOOKS_DIR, "skill-activation-prompt.ts"), {
      session_id: "perf",
      transcript_path: "/tmp/t.txt",
      cwd: join(HOOKS_DIR, "../.."),
      permission_mode: "normal",
      prompt: "test prompt"
    });
    expect(r.exitCode).toBe(0);
    expect(r.durationMs).toBeLessThan(MAX_MS);
  });

  it("post-tool-use-tracker.ts completes in < 500ms", async () => {
    const r = await timeHook(join(HOOKS_DIR, "post-tool-use-tracker.ts"), {
      tool_name: "Edit",
      tool_input: { file_path: join(HOOKS_DIR, "../../src/test.ts") },
      session_id: "perf"
    });
    expect(r.exitCode).toBe(0);
    expect(r.durationMs).toBeLessThan(MAX_MS);
  });
});
```

### SIGINT + atexit + questionary Integration
```python
# Source: Python stdlib signal module docs + questionary behavior
import signal
import atexit
import sys

class WizardInterruptHandler:
    """Manages graceful shutdown of the onboarding wizard."""

    def __init__(self):
        self._state = None
        self._save_fn = None

    def setup(self, save_fn):
        """Register interrupt handlers.

        Args:
            save_fn: Callable that takes OnboardingState and saves it.
        """
        self._save_fn = save_fn
        signal.signal(signal.SIGINT, self._handle_sigint)
        atexit.register(self._save_on_exit)

    def update_state(self, state):
        """Update the current state reference (called after each section)."""
        self._state = state

    def _handle_sigint(self, signum, frame):
        """SIGINT handler: save and exit."""
        self._save_on_exit()
        print("\nProgress saved. Run the wizard again to resume.")
        sys.exit(0)

    def _save_on_exit(self):
        """Save progress if there's anything to save."""
        if self._state and self._save_fn and len(self._state.completed_sections) > 0:
            try:
                self._save_fn(self._state)
            except Exception:
                pass  # Best effort on exit
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Bash hooks with jq parsing | Bun TypeScript hooks with native JSON | Phase 4 (partially done already) | 3 hooks already ported; only config cleanup remains |
| bash wrapper piping stdin to .ts | Direct `bun run .ts` invocation | Phase 4 | Removes process spawn overhead (eliminates bash + cat + pipe) |
| No interrupt handling in wizard | SIGINT handler + atexit + progress file | Phase 4 | Ctrl+C saves progress; restart resumes |
| No hook performance testing | Bun test suite with < 500ms assertions | Phase 4 | Regression detection for hook speed |

**Deprecated/outdated:**
- `skill-activation-prompt.sh` (6-line bash wrapper): Replaced by direct `bun run` invocation of `.ts` file. DELETE.
- `post-tool-use-tracker.sh` (178-line bash+jq): Replaced by `.ts` port. DELETE.
- CONFIG.md references to `.sh` files: UPDATE after deletion.
- hooks/package.json `test` script references: UPDATE if it references .sh files.

## Open Questions

Things that could not be fully resolved:

1. **Does the `post-tool-use-tracker.ts` have exact output parity with the `.sh` version?**
   - What we know: The `.ts` file (237 lines) implements identical logic to the `.sh` file (178 lines) -- same `detectRepo()` switch-case, same `getBuildCommand()` and `getTscCommand()` functions, same file paths and logging format. Both exit 0 on all code paths (success and error).
   - What's unclear: There may be subtle behavioral differences in edge cases (e.g., grep vs. String.includes() for repo detection, sort vs. Set for deduplication).
   - Recommendation: The existing test suite (33 tests in `test_post_tool_use_tracker.test.ts`) already validates the .ts version comprehensively. Run the test suite to confirm parity. No separate .sh-vs-.ts comparison test is needed -- the .ts tests ARE the parity tests.

2. **Should the warmup run be included in the performance test or handled separately?**
   - What we know: Bun's first execution of a .ts file compiles it; subsequent runs use cache. The 500ms threshold is for production use where cache is warm.
   - What's unclear: Whether CI environments will have warm caches.
   - Recommendation: Include a warmup test that runs first (Bun test runner executes tests in file order within a describe block). Label it clearly. If CI is flaky, consider measuring average of 3 runs instead of single shot.

3. **Where exactly is .onboarding-progress.json created?**
   - What we know: It should be created at the project root (same directory as pyproject.toml) for discoverability. It should NOT be in fin-guru-private/ because it's a temporary file, not a persistent config.
   - What's unclear: Whether it should be gitignored.
   - Recommendation: Create at project root. Add to .gitignore since it contains partially-entered financial data and is only needed during an interrupted session.

4. **Phase 3 is not yet implemented -- how much can we plan concretely?**
   - What we know: Phase 3 Plan 01 defines the exact files that will exist: `src/models/onboarding_inputs.py`, `src/utils/onboarding_validators.py`, `src/utils/onboarding_sections.py`, `src/cli/onboarding_wizard.py`. The OnboardingState model will have `current_section`, `completed_sections`, and `data` fields.
   - What's unclear: The exact implementation details of the wizard's main loop (Phase 3 Plan 02, not yet created).
   - Recommendation: The save/resume logic wraps around the wizard's section loop. The patterns above work regardless of the exact loop structure because they operate on OnboardingState -- which is defined in Phase 3 Plan 01's spec. Plan the hook track independently; plan the onboarding track with the assumption that Phase 3 creates the files described in 03-01-PLAN.md.

## Sources

### Primary (HIGH confidence)
- **Codebase inspection** -- direct file reads, no external sources needed for hook state:
  - `.claude/settings.json` -- current hook configuration (verified: SessionStart uses `bun run .ts`, UserPromptSubmit still uses `.sh`)
  - `.claude/hooks/load-fin-core-config.ts` (259 lines) -- fully ported, stdin reading pattern at lines 137-157
  - `.claude/hooks/skill-activation-prompt.ts` (183 lines) -- fully ported, stdin reading at lines 57-83
  - `.claude/hooks/skill-activation-prompt.sh` (6 lines) -- bash wrapper: `cat | bun skill-activation-prompt.ts`
  - `.claude/hooks/post-tool-use-tracker.ts` (237 lines) -- fully ported, stdin at lines 136-155
  - `.claude/hooks/post-tool-use-tracker.sh` (178 lines) -- dead bash+jq original
  - `.claude/hooks/tests/` -- 4 test files, 97+ tests, `bun:test` framework, `runHook()` spawn pattern
  - `.claude/hooks/package.json` -- dependencies: @types/node, tsx, typescript
  - `.claude/hooks/tsconfig.json` -- ES2022 target, NodeNext modules
  - `.planning/phases/03-onboarding-wizard/03-RESEARCH.md` -- Phase 3 architecture decisions
  - `.planning/phases/03-onboarding-wizard/03-01-PLAN.md` -- Phase 3 file structure spec

- **Claude Code hooks documentation** (https://code.claude.com/docs/en/hooks):
  - Hooks receive JSON on stdin, return via stdout + exit code
  - `$CLAUDE_PROJECT_DIR` environment variable available for path resolution
  - `command` field in settings.json supports any shell command including `bun run`
  - Default timeout is 600 seconds for command hooks
  - UserPromptSubmit has no matcher support; always fires

- **Python stdlib documentation** (training data, HIGH confidence for stdlib):
  - `signal.signal(signal.SIGINT, handler)` -- standard SIGINT registration
  - `atexit.register(fn)` -- called on normal interpreter termination
  - `tempfile.mkstemp()` + `Path.rename()` -- atomic write pattern

### Secondary (MEDIUM confidence)
- **Bun test runner** (https://bun.com/docs/cli/test):
  - No built-in performance assertion API; use `performance.now()` + `expect().toBeLessThan()`
  - Default per-test timeout is 5000ms (configurable via `--timeout`)
  - Tests run in file order within describe blocks
- **Bun 1.3.7** installed locally, confirmed with `bun --version`

### Tertiary (LOW confidence)
- Python discuss.python.org thread on SIGTERM/SIGINT handling -- confirms that Python converts SIGINT to KeyboardInterrupt by default, and signal handlers can override this
- Various sources on questionary's Ctrl+C behavior returning None -- consistent with Phase 3 research findings

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- All stdlib Python, existing Bun toolchain, no new dependencies
- Architecture: HIGH -- Patterns verified directly from codebase (existing hook tests, existing settings.json patterns, Phase 3 research)
- Pitfalls: HIGH -- Signal handling edge cases documented from official Python docs; hook configuration verified from Claude Code docs; questionary behavior confirmed in Phase 3 research
- Code examples: HIGH -- All patterns derive from existing codebase files or Python stdlib; Bun test pattern directly extends existing test suite

**Research date:** 2026-02-02
**Valid until:** 2026-03-04 (30 days -- stdlib patterns are stable, hook architecture is locked)
