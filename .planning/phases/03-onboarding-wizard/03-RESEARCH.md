# Phase 3: Onboarding Wizard - Research

**Researched:** 2026-02-02
**Domain:** Interactive CLI onboarding with questionary, Pydantic validation, YAML/config generation
**Confidence:** HIGH

## Summary

Phase 3 builds an interactive Python CLI wizard that collects a user's financial profile across 8 sections and generates personalized configuration files (user-profile.yaml, CLAUDE.md, .env, MCP JSON). The codebase already has significant scaffolding: a TypeScript/Bun implementation (scripts/onboarding/) with complete section implementations, templates, input validators, and progress management. Critically, there is also a complete Python 3-layer implementation: Pydantic models (src/models/yaml_generation_inputs.py), a YAML generator calculator (src/utils/yaml_generator.py), and a CLI (src/utils/yaml_generator_cli.py). The existing Python Layer 1+2 code is production-quality and should be reused directly.

The primary new work is: (1) building a Python CLI wizard using `questionary` that prompts users through 8 sections, (2) connecting that wizard to the existing Pydantic models and YAML generator, (3) implementing a custom retry-then-skip wrapper around questionary's infinite-retry validation, and (4) ensuring CLAUDE.md and agent files use `{user_name}` instead of hardcoded names. The TypeScript scaffold in scripts/onboarding/ serves as the authoritative blueprint for question flow, section ordering, and user experience -- the Python implementation should replicate its behavior.

**Primary recommendation:** Build a Python `src/cli/onboarding_wizard.py` CLI (Layer 3) that uses questionary for interactive prompts, feeds answers into the existing `UserDataInput` Pydantic model (Layer 1), generates configs via `YAMLGenerator` (Layer 2), and writes to `fin-guru-private/`. Wrap questionary calls in a retry-with-skip helper to meet the "3 retries then skip" requirement.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| questionary | 2.1.1 | Interactive CLI prompts (text, select, confirm, checkbox) | Requirement ONBD-01 mandates it; XC-01 says it is the only allowed new dependency |
| pydantic | 2.10.6+ | Input/output validation models | Already in codebase; existing yaml_generation_inputs.py models are complete |
| pyyaml | 6.0.3+ | YAML file generation/reading | Already in codebase |

### Supporting (Already in Project)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pathlib (stdlib) | 3.12 | File path operations | All file creation/template loading |
| json (stdlib) | 3.12 | MCP JSON generation, progress persistence | .onboarding-progress.json, mcp.json |
| signal (stdlib) | 3.12 | SIGINT handler for Ctrl+C save (Phase 4, but design for it now) | Progress save on interrupt |
| shutil (stdlib) | 3.12 | Backup existing files before overwriting | .env, CLAUDE.md backup before generation |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| questionary | click prompts | click is already not in the project; questionary is explicitly required |
| questionary | PyInquirer | Abandoned since 2019; questionary is its successor |
| questionary | rich.prompt | No select/checkbox support; questionary is purpose-built for wizard flows |

**Installation:**
```bash
uv add questionary
```

**Note:** questionary 2.1.1 depends on prompt_toolkit, which will be pulled in automatically. This is the ONLY new dependency allowed per XC-01.

## Architecture Patterns

### Recommended Project Structure
```
src/
  cli/
    onboarding_wizard.py     # NEW: Layer 3 - Main wizard entry point + CLI
  models/
    yaml_generation_inputs.py # EXISTING: Layer 1 - All Pydantic models (already complete)
    onboarding_inputs.py      # NEW: Layer 1 - Wizard-specific models (section data, progress state)
  utils/
    yaml_generator.py         # EXISTING: Layer 2 - Template processing + file generation
    yaml_generator_cli.py     # EXISTING: Layer 3 - Non-interactive config generation
    onboarding_sections.py    # NEW: Layer 2 - Section runners (8 sections as functions)
    onboarding_validators.py  # NEW: Layer 2 - Retry-with-skip wrapper + domain validators

scripts/
  onboarding/
    modules/templates/        # EXISTING: All templates (user-profile, CLAUDE, env, mcp)
    sections/                 # EXISTING: TypeScript sections (REFERENCE ONLY, not executed)

tests/python/
    test_onboarding_wizard.py       # NEW: Wizard integration tests (mock questionary)
    test_onboarding_validators.py   # NEW: Validation + retry logic tests
    test_onboarding_sections.py     # NEW: Section runner unit tests
```

### Pattern 1: Retry-Then-Skip Wrapper
**What:** questionary has infinite retry by default (keeps prompting until valid). The requirement is 3 retries then offer skip. Build a wrapper function.
**When to use:** Every question that collects validated financial data (dollar amounts, percentages, counts).
**Example:**
```python
# Source: Custom pattern needed because questionary lacks retry limits
from typing import TypeVar, Optional, Callable

T = TypeVar("T")

def ask_with_retry(
    prompt_fn: Callable[[], Optional[str]],
    validator: Callable[[str], T],
    max_retries: int = 3,
    default_on_skip: Optional[T] = None,
    field_name: str = "value",
) -> Optional[T]:
    """
    Ask a question with retry limit. After max_retries, offer skip.

    Args:
        prompt_fn: Function that calls questionary and returns raw string or None
        validator: Function that validates and converts the string
        max_retries: Number of retry attempts before offering skip
        default_on_skip: Value to use if user skips
        field_name: Human-readable field name for error messages

    Returns:
        Validated value or default_on_skip if skipped
    """
    for attempt in range(max_retries):
        raw = prompt_fn()
        if raw is None:  # User pressed Ctrl+C or questionary returned None
            return default_on_skip
        try:
            return validator(raw)
        except (ValueError, ValidationError) as e:
            remaining = max_retries - attempt - 1
            if remaining > 0:
                print(f"  Invalid {field_name}: {e}")
                print(f"  {remaining} attempt(s) remaining.")
            else:
                skip = questionary.confirm(
                    f"  Skip {field_name}? (will use default: {default_on_skip})",
                    default=True,
                ).ask()
                if skip:
                    return default_on_skip
                # Give one more chance
                raw = prompt_fn()
                if raw is None:
                    return default_on_skip
                try:
                    return validator(raw)
                except (ValueError, ValidationError):
                    return default_on_skip
    return default_on_skip
```

### Pattern 2: Section Runner Pattern
**What:** Each of the 8 sections is a standalone function that takes onboarding state, prompts user, returns updated state.
**When to use:** Every section of the wizard.
**Example:**
```python
# Source: Mirrors TypeScript pattern in scripts/onboarding/sections/liquid-assets.ts
from src.models.onboarding_inputs import OnboardingState, SectionName, LiquidAssetsData

def run_liquid_assets_section(state: OnboardingState) -> OnboardingState:
    """Run Section 1: Liquid Assets."""
    print("Section 1 of 8: Liquid Assets")
    print("Let's start with your cash accounts.")

    total = ask_with_retry(
        prompt_fn=lambda: questionary.text(
            "Total liquid cash ($):",
            instruction="e.g. 15000 or $15,000",
        ).ask(),
        validator=validate_currency,
        default_on_skip=0.0,
        field_name="liquid assets total",
    )

    # ... more prompts ...

    data = LiquidAssetsData(total=total, accounts_count=count, average_yield=yield_pct)
    state.data["liquid_assets"] = data.model_dump()
    state.completed_sections.append("liquid_assets")
    state.current_section = "investments"
    return state
```

### Pattern 3: questionary.form() for Related Questions
**What:** Use questionary's form() for sections where questions are independent (no conditional logic).
**When to use:** Sections like cash flow where all 5 questions are always asked.
**Why not always:** form() does not support the retry-then-skip wrapper, so it only works for sections with simple text inputs using questionary's built-in validation.
**Decision:** Do NOT use form() -- the retry-then-skip requirement means each question needs individual control. Use sequential ask_with_retry calls instead.

### Pattern 4: Reuse Existing Python Layer 1+2
**What:** The existing `UserDataInput` model and `YAMLGenerator` class are complete and tested. The wizard collects data, converts to `UserDataInput`, then calls `generator.generate_all_configs()`.
**When to use:** At the end of the wizard, after all 8 sections are complete.
**Example:**
```python
# After all sections collected, convert to existing model
user_data = UserDataInput(
    identity=UserIdentityInput(user_name=state.data["env_setup"]["user_name"]),
    liquid_assets=LiquidAssetsInput(**state.data["liquid_assets"]),
    portfolio=InvestmentPortfolioInput(**state.data["investments"]),
    cash_flow=CashFlowInput(**state.data["cash_flow"]),
    debt=DebtProfileInput(**state.data["debt"]),
    preferences=UserPreferencesInput(**state.data["preferences"]),
    mcp=MCPConfigInput(**state.data.get("mcp_config", {})),
    project_root=str(Path.cwd()),
)
generator = YAMLGenerator("scripts/onboarding/modules/templates")
output = generator.generate_all_configs(user_data)
write_config_files(output, base_dir="fin-guru-private")
```

### Anti-Patterns to Avoid
- **Duplicating Pydantic models:** Do NOT create new models that overlap with yaml_generation_inputs.py. The existing UserDataInput, LiquidAssetsInput, CashFlowInput, etc. are already complete. Use them directly.
- **Using questionary.prompt() dict-based API:** The dict-based prompt() API makes retry-with-skip harder to implement. Use individual questionary.text()/select()/confirm() calls.
- **Writing YAML files manually:** Do NOT hand-write YAML. Always use the existing YAMLGenerator and its template processing.
- **Hardcoding output paths:** Use the existing write_config_files() function which knows all the correct output paths.
- **Building a new template engine:** The existing _process_template() in yaml_generator.py handles {{variable}} and {{#if}} blocks. Use it.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Template substitution | Custom string formatting | YAMLGenerator._process_template() | Already handles {{var}} and {{#if}} blocks, tested |
| Pydantic validation models | New model classes | yaml_generation_inputs.py models | Complete set of UserDataInput, LiquidAssetsInput, etc. already exists |
| YAML/config file writing | Manual file creation | write_config_files() | Knows all output paths, creates directories |
| Currency formatting | f-string formatting | YAMLGenerator._prepare_user_data() | Already formats $X,XXX.XX |
| Possessive name generation | Manual string logic | YAMLGenerator._prepare_user_data() | Already handles possessives like "Alex's" vs "James'" |
| File generation for all configs | Per-file generation | generator.generate_all_configs() | Generates all 6 config files in one call |
| Input type validation (currency, %) | Python parsing | Existing validators in input-validator.ts logic ported to Python | TypeScript versions already handle $10,000 and 4.5% formats |

**Key insight:** Roughly 60% of the code needed for Phase 3 already exists in the codebase as Python Layers 1+2. The wizard's job is simply to collect user input via questionary, validate it, and feed it to the existing generation pipeline. The TypeScript scaffold in scripts/onboarding/ is a reference implementation showing exact question flow and UX.

## Common Pitfalls

### Pitfall 1: questionary Returns None on Ctrl+C
**What goes wrong:** questionary's safe .ask() method returns None when user presses Ctrl+C. If not handled, passing None to Pydantic validators causes cryptic TypeErrors.
**Why it happens:** questionary catches KeyboardInterrupt and returns None instead of raising.
**How to avoid:** Always check for None return from .ask() before passing to validators. In the retry-with-skip wrapper, treat None as "user wants to skip/exit."
**Warning signs:** TypeError in validator functions, unexpected None in state data.

### Pitfall 2: questionary Requires a Real Terminal
**What goes wrong:** Tests fail with `io.UnsupportedOperation: Stdin is not a terminal` because questionary (via prompt_toolkit) requires a real TTY.
**Why it happens:** questionary is built on prompt_toolkit which needs terminal capabilities for cursor movement, colors, etc.
**How to avoid:** In tests, mock at the questionary function level (`mocker.patch('questionary.text')`) NOT at stdin level. Do not try to use monkeypatch for sys.stdin with questionary.
**Warning signs:** Tests pass locally but fail in CI, or tests fail with vt100/terminal errors.

### Pitfall 3: Template Variable Name Mismatch
**What goes wrong:** Generated config files have empty values or {{unresolved_variable}} placeholders.
**Why it happens:** The wizard collects data under different keys than the template expects. E.g., wizard stores "total_cash" but template uses "{{liquid_assets_total}}".
**How to avoid:** The existing YAMLGenerator._prepare_user_data() method defines the exact mapping. Always convert wizard responses into UserDataInput models, then let the generator handle template variable naming.
**Warning signs:** Empty fields in generated YAML, unresolved {{}} in output files.

### Pitfall 4: Output Path Confusion (fin-guru-private vs project root)
**What goes wrong:** user-profile.yaml gets written to the wrong location, or CLAUDE.md overwrites the repo's CLAUDE.md template.
**Why it happens:** The existing write_config_files() writes to project root by default. But the requirement says user-profile.yaml goes in fin-guru-private/, while CLAUDE.md goes at project root.
**How to avoid:** Carefully map where each generated file should go. user-profile.yaml and other private data go to fin-guru-private/. CLAUDE.md goes to project root (replacing the template). .env goes to project root. The generation flow should output user-profile.yaml to fin-guru-private/fin-guru/data/ NOT fin-guru/data/.
**Warning signs:** Private financial data in git-tracked directories, CLAUDE.md template overwritten without backup.

### Pitfall 5: Decimal vs Percentage Format Confusion
**What goes wrong:** User enters "4.5" meaning 4.5%, but the model stores 0.045 (decimal). Or vice versa.
**Why it happens:** The TypeScript scaffold converts percentage to decimal on collection (line 126 of liquid-assets.ts: `averageYield / 100`). The Pydantic model LiquidAssetsInput expects decimal form (ge=0, le=1 for average_yield).
**How to avoid:** Always convert user percentage input to decimal (divide by 100) before storing. Be explicit in prompts: "Enter as percentage, e.g. 4.5 for 4.5%".
**Warning signs:** average_yield showing 4.5 instead of 0.045, or percentage fields failing Pydantic validation (le=1).

### Pitfall 6: Existing Test Suite Regression
**What goes wrong:** Adding questionary as dependency or modifying model files breaks existing 365+ tests.
**Why it happens:** Tests import from src.models.yaml_generation_inputs. If models are changed, tests break.
**How to avoid:** Do NOT modify existing Pydantic models. Create new wizard-specific models (onboarding_inputs.py) for section data and progress state. Existing models are consumed at the final generation step.
**Warning signs:** test_yaml_generation.py failures, test_onboarding_cli_structure.py failures.

## Code Examples

Verified patterns from the existing codebase and official questionary docs:

### Basic questionary Text Prompt with Validation
```python
# Source: https://questionary.readthedocs.io/en/stable/pages/types.html
import questionary

answer = questionary.text(
    "What is your monthly income?",
    validate=lambda val: True if val.replace(",", "").replace("$", "").replace(".", "").isdigit()
        else "Please enter a valid dollar amount",
    instruction="e.g. $10,000 or 10000",
).ask()
```

### questionary Select for Enums
```python
# Source: https://questionary.readthedocs.io/en/stable/pages/types.html
risk = questionary.select(
    "What is your risk tolerance?",
    choices=["Conservative", "Moderate", "Aggressive"],
    default="Moderate",
).ask()
# Convert to enum: RiskTolerance(risk.lower())
```

### questionary Confirm for Optional Sections
```python
# Source: https://questionary.readthedocs.io/en/stable/pages/types.html
has_mortgage = questionary.confirm(
    "Do you have a mortgage?",
    default=False,
).ask()

if has_mortgage:
    balance = questionary.text("Mortgage balance ($):").ask()
    payment = questionary.text("Monthly payment ($):").ask()
```

### questionary Checkbox for Multi-Select
```python
# Source: https://questionary.readthedocs.io/en/stable/pages/types.html
focus_areas = questionary.checkbox(
    "Select your investment focus areas:",
    choices=[
        "Dividend income",
        "Growth investing",
        "Index investing",
        "Margin strategies",
        "Tax efficiency",
        "Real estate",
    ],
    validate=lambda x: True if len(x) > 0 else "Select at least one area",
).ask()
```

### Testing: Mock questionary at Function Level
```python
# Source: Community best practice from GitHub issue #49
import pytest

def test_liquid_assets_section(mocker):
    """Test liquid assets collection with mocked prompts."""
    mocker.patch("questionary.text").return_value.ask.side_effect = [
        "15000",   # total liquid cash
        "3",       # accounts count
        "4.5",     # average yield
        "",        # account structure (skip)
    ]
    mocker.patch("questionary.confirm").return_value.ask.return_value = False

    from src.utils.onboarding_sections import run_liquid_assets_section
    from src.models.onboarding_inputs import OnboardingState

    state = OnboardingState.create_new()
    result = run_liquid_assets_section(state)

    assert "liquid_assets" in result.completed_sections
    assert result.data["liquid_assets"]["total"] == 15000.0
```

### Existing Pydantic Model Usage (Layer 1)
```python
# Source: src/models/yaml_generation_inputs.py (verified in codebase)
from src.models.yaml_generation_inputs import (
    UserDataInput, UserIdentityInput, LiquidAssetsInput,
    InvestmentPortfolioInput, CashFlowInput, DebtProfileInput,
    UserPreferencesInput, MCPConfigInput,
    RiskTolerance, AllocationStrategy, InvestmentPhilosophy,
)

# All these models are complete and tested
data = UserDataInput(
    identity=UserIdentityInput(user_name="Alex", language="English"),
    liquid_assets=LiquidAssetsInput(total=10000.0, accounts_count=3, average_yield=0.04),
    portfolio=InvestmentPortfolioInput(
        total_value=100000.0,
        allocation_strategy=AllocationStrategy.AGGRESSIVE_GROWTH,
        risk_tolerance=RiskTolerance.AGGRESSIVE,
    ),
    # ... etc
)
```

### Existing YAML Generator Usage (Layer 2)
```python
# Source: src/utils/yaml_generator.py (verified in codebase)
from src.utils.yaml_generator import YAMLGenerator, write_config_files

generator = YAMLGenerator("scripts/onboarding/modules/templates")
output = generator.generate_all_configs(user_data)

# output has: user_profile_yaml, config_yaml, system_context_md, claude_md, env_file, mcp_json
# write_config_files(output, base_dir=".") writes all files
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| TypeScript/Bun onboarding (scripts/onboarding/) | Python CLI with questionary | Phase 3 transition | TS scaffold remains as reference; Python becomes the executable wizard |
| Hardcoded user-profile.yaml at fin-guru/data/ | Generated from template to fin-guru-private/ | Phase 3 | Private data moves out of tracked directory |
| Hardcoded CLAUDE.md | Template-generated CLAUDE.md with {user_name} | Phase 3 | Generic installation becomes possible |
| Manual .env creation | Interactive .env setup with optional API keys | Phase 3 | New users get guided setup |

**Key technical decision: Python, NOT TypeScript**

The ROADMAP says Phase 3 uses "questionary library" (Python) and XC-01 says "no new Python dependencies except questionary." The TypeScript scaffold in scripts/onboarding/ was an earlier prototype. The Phase 3 implementation MUST be in Python to follow the 3-layer pattern (XC-03) and be testable with pytest (XC-04). The TypeScript sections are reference material showing the question flow, NOT the executable implementation.

**Deprecated/outdated:**
- The TypeScript section files (scripts/onboarding/sections/*.ts) should NOT be executed. They serve only as a blueprint for the Python implementation's question flow and validation logic.
- The existing user-profile.yaml at fin-guru/data/user-profile.yaml is the current owner's hardcoded data. Phase 3 will NOT modify it; it will generate a NEW user-profile.yaml in fin-guru-private/ for new users.

## Open Questions

Things that could not be fully resolved:

1. **Where exactly does the generated user-profile.yaml go?**
   - What we know: fin-guru-private/ is already in .gitignore. The existing user-profile.yaml is at fin-guru/data/. Phase 2 creates the fin-guru-private/ directory structure.
   - What's unclear: Should the generated file go to fin-guru-private/fin-guru/data/user-profile.yaml (deep path) or fin-guru-private/user-profile.yaml (flat)?
   - Recommendation: Follow the convention from write_config_files() which puts it at `{base_dir}/fin-guru/data/user-profile.yaml`. With base_dir="fin-guru-private", the path would be `fin-guru-private/fin-guru/data/user-profile.yaml`. However, agents currently look at `fin-guru/data/user-profile.yaml`. This may need a symlink or path update in agents. The planner should decide the canonical location.

2. **How does setup.sh invoke the Python wizard?**
   - What we know: Phase 2 creates setup.sh which "orchestrates full first-time setup" (ONBD-05). Phase 3 builds the wizard itself.
   - What's unclear: Does setup.sh call `uv run python src/cli/onboarding_wizard.py` directly? Or does the wizard have its own entry point?
   - Recommendation: The wizard should be callable as `uv run python -m src.cli.onboarding_wizard` or `uv run python src/cli/onboarding_wizard.py`. setup.sh from Phase 2 should invoke it after dependency checks pass.

3. **Should the wizard update CLAUDE.md at project root or in fin-guru-private?**
   - What we know: CLAUDE.md at project root is git-tracked and currently contains hardcoded owner data. ONBD-07 says "CLAUDE.md generated from template."
   - What's unclear: Overwriting the tracked CLAUDE.md changes git state. Should the wizard write to project root (replacing the template) or to fin-guru-private/?
   - Recommendation: Write CLAUDE.md to project root since agents read it from there. The template (CLAUDE.template.md) stays in scripts/onboarding/modules/templates/. Backup existing CLAUDE.md before overwriting.

4. **Testing strategy for interactive prompts**
   - What we know: questionary requires a real terminal; cannot use stdin monkeypatching. Must mock at questionary function level.
   - What's unclear: Should we also have integration tests that actually run the prompts (e.g., with pexpect)?
   - Recommendation: Use pytest with mocker.patch for all unit tests. Skip pexpect integration tests for now -- they add CI complexity. The unit tests with mocked questionary provide adequate coverage of the business logic.

## Sources

### Primary (HIGH confidence)
- **Codebase inspection** - Read all existing files:
  - `src/models/yaml_generation_inputs.py` - Complete Pydantic models (11 models, all validated)
  - `src/utils/yaml_generator.py` - Template processor (6 generation methods, tested)
  - `src/utils/yaml_generator_cli.py` - Existing CLI for non-interactive generation
  - `scripts/onboarding/` - TypeScript scaffold with 8 section implementations
  - `scripts/onboarding/modules/templates/` - 6 template files (user-profile, CLAUDE, env, mcp, config, system-context)
  - `tests/python/test_yaml_generation.py` - Existing test patterns
  - `pyproject.toml` - Current dependency list (pydantic 2.10.6+, pyyaml 6.0.3+)

### Secondary (MEDIUM confidence)
- [questionary PyPI](https://pypi.org/project/questionary/) - Version 2.1.1, Python >=3.9, released 2025-08-28
- [questionary ReadTheDocs - Types](https://questionary.readthedocs.io/en/stable/pages/types.html) - API signatures for all 10 prompt types
- [questionary ReadTheDocs - Advanced](https://questionary.readthedocs.io/en/stable/pages/advanced.html) - Validation, forms, conditional questions, testing
- [questionary GitHub](https://github.com/tmbo/questionary) - 2000+ stars, active maintenance, MIT license

### Tertiary (LOW confidence)
- [questionary testing GitHub Issue #49](https://github.com/tmbo/questionary/issues/49) - Community discussion on testing approaches (mock vs pexpect)
- [The Blue Book - questionary](https://lyz-code.github.io/blue-book/questionary/) - Community reference on testing patterns

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - questionary is explicitly required by ONBD-01/XC-01; version verified on PyPI
- Architecture: HIGH - Existing codebase patterns (3-layer, Pydantic models, templates) are directly observed in source
- Pitfalls: HIGH - Terminal requirement and None-on-Ctrl+C verified in official docs; test patterns confirmed via community sources
- Code examples: HIGH - All examples either from official docs or directly from existing codebase files

**Research date:** 2026-02-02
**Valid until:** 2026-03-02 (30 days -- questionary 2.1.1 is stable, codebase patterns are locked)
