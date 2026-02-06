---
phase: 03-onboarding-wizard
verified: 2026-02-05T19:30:00Z
status: passed
score: 5/5 must-haves verified
re_verification: false
---

# Phase 3: Onboarding Wizard Verification Report

**Phase Goal:** A new user completes an interactive CLI session and has a fully personalized Finance Guru configuration

**Verified:** 2026-02-05T19:30:00Z

**Status:** passed

**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | User completes 8-section interactive onboarding and a valid user-profile.yaml is generated in fin-guru-private/ with their financial data | ✓ VERIFIED | Wizard CLI orchestrates all 8 sections via SECTION_ORDER (416 lines). Config generation writes to fin-guru-private/fin-guru/data/user-profile.yaml via write_config_files(). Test test_generates_all_files verifies output paths. |
| 2 | Entering invalid input shows a clear error and re-prompts up to 3 times, then offers a skip option | ✓ VERIFIED | ask_with_retry implements 3-retry logic (lines 176-199 onboarding_validators.py), questionary.confirm skip offer (lines 202-212), one final attempt if declined (lines 214-225). Tests test_ask_with_retry_valid_after_retries and test_ask_with_retry_skip_after_max_retries verify behavior. |
| 3 | CLAUDE.md is generated with the user's name and correct project-root path (no hardcoded personal names or absolute paths) | ✓ VERIFIED | Template uses {{user_name}} placeholder (CLAUDE.template.md). Wizard writes via explicit Path.write_text() (line 295 onboarding_wizard.py). Test test_generated_files_contain_user_name verifies no placeholders remain. Agent files use {user_name} (11 files found), zero hardcoded names (grep confirmed). |
| 4 | .env file is created with optional API keys (user can skip all keys and system still functions with yfinance) | ✓ VERIFIED | env_setup section prompts for API keys with explicit "optional" messaging (onboarding_sections.py). All confirm prompts can be skipped. .env written to project root (line 300 onboarding_wizard.py). Test test_all_api_keys_skipped verifies skip behavior. |
| 5 | Finance Guru agents load the generated user-profile.yaml and address the user by their configured name | ✓ VERIFIED | Hook path fixed to read from fin-guru-private/fin-guru/data/user-profile.yaml (lines 166-168 load-fin-core-config.ts), matching wizard output location. 11 agent files use {user_name} template variable. Runtime chain complete: wizard writes → hook reads → agents see user_name. |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/models/onboarding_inputs.py` | OnboardingState model with 8 SectionName enum values and wizard progress tracking | ✓ VERIFIED | 90 lines, substantive. Exports OnboardingState, SectionName enum (8 values), create_new(), is_section_complete(), mark_complete() methods. No stub patterns. |
| `src/utils/onboarding_validators.py` | Domain validators (currency, percentage, integer) and ask_with_retry wrapper with 3-retry-then-skip | ✓ VERIFIED | 226 lines, substantive. Exports validate_currency (handles $10k/1.5M), validate_percentage (0-100 range), validate_positive_integer, ask_with_retry (3 retries + confirm skip). No stub patterns. |
| `src/utils/onboarding_sections.py` | 8 section runner functions using questionary prompts | ✓ VERIFIED | 882 lines, substantive. All 8 runners importable: run_liquid_assets_section through run_summary_section. Each uses ask_with_retry for validated prompts, questionary.text/select/confirm/checkbox for input. No stub patterns. |
| `src/cli/onboarding_wizard.py` | Wizard CLI orchestrating 8 sections, state-to-model conversion, config file generation | ✓ VERIFIED | 416 lines, substantive. SECTION_ORDER defines flow, convert_state_to_user_data maps raw strings to Pydantic models with _safe_enum helper for enum conversion, generate_config_files writes 6 files to correct paths with backup. argparse with --dry-run. No stub patterns. |
| `tests/python/test_onboarding_validators.py` | Unit tests for validators and retry wrapper | ✓ VERIFIED | 257 lines, substantive. 34 tests covering currency/percentage/integer parsing (valid + invalid cases), ask_with_retry retry/skip/Ctrl+C logic. All pass. |
| `tests/python/test_onboarding_sections.py` | Unit tests for section runners with mocked questionary | ✓ VERIFIED | 405 lines, substantive. 11 tests covering liquid assets, investments, cash flow, preferences, env setup, summary sections with mocker.patch questionary. Verifies string storage for enums. All pass. |
| `tests/python/test_onboarding_wizard.py` | Integration tests for wizard flow and config generation | ✓ VERIFIED | 407 lines, substantive. 18 tests covering SECTION_ORDER verification, convert_state_to_user_data string-to-enum mapping, generate_config_files output paths/backup/mcp.json explicit write. All pass. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| src/cli/onboarding_wizard.py | src/utils/onboarding_sections.py | imports all 8 run_*_section functions | ✓ WIRED | Line 45-54 imports all 8 section runners. SECTION_ORDER list uses them (lines 61-70). |
| src/cli/onboarding_wizard.py | src/models/yaml_generation_inputs.py | converts OnboardingState.data to UserDataInput | ✓ WIRED | convert_state_to_user_data constructs UserDataInput (line 239). _safe_enum helper converts strings to enum instances for RiskTolerance, AllocationStrategy, InvestmentPhilosophy (lines 180-189, 222-226). |
| src/cli/onboarding_wizard.py | src/utils/yaml_generator.py | calls generate_all_configs() and write_config_files() | ✓ WIRED | Line 55 imports, line 284 calls generate_all_configs(), line 288 calls write_config_files(). |
| src/cli/onboarding_wizard.py | .claude/mcp.json | explicit Path write | ✓ WIRED | Lines 302-307 create .claude/ dir, backup existing mcp.json, write via mcp_path.write_text(output.mcp_json). Test test_mcp_json_written_via_explicit_path verifies. |
| .claude/hooks/load-fin-core-config.ts | fin-guru-private/fin-guru/data/user-profile.yaml | profilePath reads from wizard output location | ✓ WIRED | Lines 166-168 read from fin-guru-private/fin-guru/ for config/profile/context, matching wizard's write_config_files(base_dir="fin-guru-private") output. |
| tests/python/test_onboarding_sections.py | questionary | mocker.patch at questionary function level | ✓ WIRED | Tests mock at src.utils.onboarding_sections.questionary.* import site (not global). Pattern established for all section tests. |

### Requirements Coverage

| Requirement | Status | Blocking Issue |
|-------------|--------|----------------|
| ONBD-01 | ✓ SATISFIED | 8-section wizard with questionary prompts exists and runs |
| ONBD-02 | ✓ SATISFIED | ask_with_retry implements 3-retry-then-skip with clear error messages, tested |
| ONBD-04 | ✓ SATISFIED | YAML generation via YAMLGenerator.generate_all_configs() from user-profile.template.yaml |
| ONBD-07 | ✓ SATISFIED | CLAUDE.md generated from template with {{user_name}}, explicit Path.write_text to project root |
| ONBD-08 | ✓ SATISFIED | .env setup section prompts for optional API keys, all can be skipped |
| ONBD-09 | ✓ SATISFIED | mcp.json generated from template, written to .claude/mcp.json with backup and merge instructions |
| ONBD-17 | ✓ SATISFIED | Agent files use {user_name} (11 files), hook reads from fin-guru-private/, runtime chain complete |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| - | - | None found | - | All artifacts substantive, no TODO/FIXME/placeholder patterns, no stub implementations |

### Human Verification Required

#### 1. Complete End-to-End Onboarding Flow

**Test:** Run `uv run python src/cli/onboarding_wizard.py` and complete all 8 sections with real financial data.

**Expected:**
- Welcome banner displays with 8-section overview
- Each section prompts for relevant data with clear labels
- Invalid input (e.g., "abc" for dollar amount) shows error and re-prompts
- After 3 failed attempts, skip offer appears with sensible default
- Summary section displays all collected data formatted nicely
- Confirmation prompt appears
- On confirmation:
  - fin-guru-private/fin-guru/data/user-profile.yaml created with entered data
  - CLAUDE.md at project root contains entered name (not {{user_name}})
  - .env at project root contains entered API keys (or empty if skipped)
  - .claude/mcp.json at project root contains MCP server config
  - Existing files backed up to .backup extension
- Completion message with file paths printed

**Why human:** Requires interactive questionary prompts with real terminal input. Full flow integration test beyond unit test scope.

#### 2. Agent Runtime Name Loading

**Test:**
1. Complete onboarding wizard with name "TestUser"
2. Start new Claude Code session
3. Activate any Finance Guru agent (e.g., `/fin-guru:orchestrator`)
4. Check agent's first response

**Expected:**
- Agent addresses you as "TestUser" (the name entered in onboarding)
- Agent does NOT say "the owner" or use placeholder {user_name} literally
- Session context includes loaded user-profile.yaml content

**Why human:** Requires Claude Code session with hook execution. Hook runs at session start and injects profile into system context — can't verify programmatically without full Claude Code environment.

#### 3. Validation Retry Flow

**Test:** Run wizard and intentionally enter invalid data:
- Enter "not-a-number" for liquid assets total (should re-prompt)
- Enter "-500" for cash flow income (should reject negative)
- Enter "150%" for percentage field (should enforce 0-100 range)
- Fail validation 3 times

**Expected:**
- Clear error message shows on each failed attempt
- Attempt counter displays (1/3, 2/3, 3/3)
- After 3 failures, questionary.confirm prompt asks: "Use default value (X) and continue?"
- Accepting skip moves to next question with default value
- Declining skip gives one final attempt
- If final attempt fails, default is used automatically

**Why human:** Requires deliberate invalid input and observing interactive retry/skip prompts. Unit tests mock questionary but don't capture full UX flow.

#### 4. File Backup Behavior

**Test:**
1. Create fake existing files: CLAUDE.md, .env, .claude/mcp.json at project root
2. Run wizard to completion
3. Check filesystem

**Expected:**
- CLAUDE.md.backup exists with original content
- .env.backup exists with original content
- .claude/mcp.json.backup exists with original content
- New files contain wizard-generated content (original content not lost)

**Why human:** Test suite uses tmp_path fixtures which start empty. Testing backup of actual project-root files requires filesystem state setup beyond test isolation scope.

---

## Verification Conclusion

**All 5 observable truths VERIFIED.** Phase 3 goal achieved: a new user CAN complete an interactive CLI session and have a fully personalized Finance Guru configuration.

**Automated verification confirms:**
- All 7 required artifacts exist and are substantive (no stubs)
- All 6 key wiring links are correctly connected
- 63 tests pass covering validators, sections, and wizard integration
- 426 total tests pass with zero regressions
- questionary dependency installed
- Hook reads from wizard output location (runtime chain complete)
- Agent files use {user_name} template variable (11 files)
- Templates use {{user_name}} placeholder (5 files)
- No hardcoded personal names found

**Human verification needed for:**
- Full end-to-end wizard flow with real terminal interaction (recommended before Phase 4)
- Agent name loading at session start via hook (requires Claude Code session)
- Validation retry/skip UX flow (observing error messages and prompts)
- File backup behavior with existing project-root files

**Phase completion status:** PASSED — core functionality verified, human testing recommended for polish validation before Phase 4 (save/resume).

---

_Verified: 2026-02-05T19:30:00Z_
_Verifier: Claude (gsd-verifier)_
