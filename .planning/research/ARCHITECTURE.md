# Architecture Patterns

**Domain:** Finance Guru v3 -- Onboarding, Hedging CLI Tools, Knowledge Explorer
**Researched:** 2026-02-02
**Overall confidence:** HIGH (based on codebase inspection, not external sources)

## Executive Summary

Finance Guru v3 introduces three architecturally distinct components into an established Python 3.12+ financial analysis system. The existing 3-layer architecture (Pydantic Models -> Calculator Classes -> CLI Interfaces) is well-proven with 16 CLI files, 14 model files, and 10 calculator classes. The new components integrate at different levels: hedging tools slot directly into the existing 3-layer pattern, onboarding operates outside it as infrastructure tooling, and the knowledge explorer is an entirely separate static HTML pipeline. The critical insight is that these three components share a single data nexus -- `user-profile.yaml` -- but otherwise have no runtime dependencies on each other and should be built in dependency order.

## Recommended Architecture

### System Map

```
                    +---------------------------------+
                    |       user-profile.yaml         |
                    |  (central configuration nexus)  |
                    +-------+----------+--------------+
                            |          |
              +-------------+          +------------------+
              |                                           |
              v                                           v
+----------------------------+              +-----------------------------+
| ONBOARDING SYSTEM          |              | SESSION START HOOK          |
| (TypeScript/Bun)           |              | load-fin-core-config.ts     |
|                            |              | (reads profile at startup)  |
| scripts/onboarding/        |              +-----------------------------+
| - CLI wizard (index.ts)    |                        |
| - Section modules          |                        v
| - YAML generator           |              +-----------------------------+
| - Template engine          |              | AGENT SYSTEM                |
| - setup.sh orchestrator    |              | .claude/commands/fin-guru/  |
+----------------------------+              | (13 specialized agents)     |
                                            +-----------------------------+
                                                      |
                                                      v
+----------------------------+              +-----------------------------+
| KNOWLEDGE EXPLORER         |              | PYTHON 3-LAYER ARCHITECTURE |
| (Static HTML pipeline)     |              +-----------------------------+
|                            |              |                             |
| scripts/explorer/          |              | Layer 1: src/models/        |
| - build.ts (Bun)          |              |   *_inputs.py (14 files)    |
| - Topic JSON data files    |              |   __init__.py (exports)     |
| - Template HTML            |              |                             |
|                            |              | Layer 2: src/analysis/      |
| Output: docs/explorers/    |              |   src/strategies/           |
| - *.html (zero-dep pages)  |              |   src/utils/                |
+----------------------------+              |   (10 calculator classes)   |
              |                             |                             |
              v                             | Layer 3: src/analysis/      |
+----------------------------+              |   *_cli.py (16 CLI files)   |
| MAYA LEARNER PROFILE       |              +-----------------------------+
| fin-guru/data/             |                        ^
|   learner-profile.json     |                        |
| (optional integration)     |              +-----------------------------+
+----------------------------+              | HEDGING TOOLS (NEW)         |
                                            | (fits INTO 3-layer arch)    |
                                            |                             |
                                            | L1: hedging_inputs.py       |
                                            |     total_return_inputs.py  |
                                            |     config_loader.py        |
                                            |                             |
                                            | L2: rolling_tracker.py      |
                                            |     hedge_sizer.py          |
                                            |     hedge_comparison.py     |
                                            |     total_return.py         |
                                            |                             |
                                            | L3: rolling_tracker_cli.py  |
                                            |     hedge_sizer_cli.py      |
                                            |     hedge_comparison_cli.py |
                                            |     total_return_cli.py     |
                                            +-----------------------------+
```

### Component Boundaries

| Component | Responsibility | Communicates With | Runtime | Does NOT Touch |
|-----------|---------------|-------------------|---------|----------------|
| **Onboarding System** | Collects user financial profile, generates configs, installs hooks | Writes `user-profile.yaml`, `CLAUDE.md`, `.env`, `.mcp.json` | Bun TypeScript (CLI) | Python code, agent definitions, explorer |
| **Hedging CLI Tools** | 4 new financial analysis CLIs for portfolio protection | Reads `user-profile.yaml` (via config_loader), uses `options.py` (Black-Scholes), uses `market_data.py` | Python 3.12+ (uv) | Onboarding code, explorer, hook infrastructure |
| **Knowledge Explorer** | Static HTML generation for interactive self-assessment | Reads topic JSON data files, outputs standalone HTML, optionally writes learner-profile.json | Bun TypeScript (build script), Browser (runtime) | Python code, onboarding, hooks |
| **Config Loader** (new) | Reads hedging config section from user-profile.yaml | Called by hedging calculators (Layer 2) | Python (pyyaml) | CLI layer, explorer, onboarding |
| **Hook Infrastructure** (refactored) | Session start context loading, file tracking, build checks | Reads `user-profile.yaml`, `config.yaml`, portfolio CSVs | Bun TypeScript | Python tools, explorer build pipeline |

### Boundary Rules

1. **Onboarding WRITES configs; everything else READS them.** The onboarding system is the sole producer of user-profile.yaml, CLAUDE.md, .env, and .mcp.json. All other components are consumers.

2. **Hedging tools follow the 3-layer rule exactly.** No shortcuts. Models in `src/models/`, calculators in `src/analysis/` (or `src/strategies/`), CLIs as `*_cli.py` files. The config_loader.py sits at Layer 2 because it provides validated configuration data to calculators.

3. **The explorer has ZERO Python dependencies.** It is a Bun-based build tool that compiles JSON + HTML template into standalone HTML files. It shares no code with the Python codebase.

4. **Integration happens through files, not function calls.** Components communicate via YAML, JSON, and file system paths -- never by importing each other's modules across language boundaries.

## Data Flow

### Flow 1: Onboarding -> Configuration Files

```
User Input (interactive CLI prompts)
    |
    v
scripts/onboarding/index.ts
    |-- sections/liquid-assets.ts
    |-- sections/investment-portfolio.ts
    |-- sections/cash-flow.ts
    |-- sections/debt-profile.ts
    |-- sections/preferences.ts
    |-- sections/broker-selection.ts
    |-- sections/env-setup.ts
    |
    v
modules/yaml-generator.ts
    |
    +-> fin-guru/data/user-profile.yaml     (financial profile)
    +-> CLAUDE.md                           (from template, with {user_name} etc.)
    +-> .env                                (API keys)
    +-> .mcp.json                           (MCP server config)
    +-> .onboarding-progress.json           (resume state, deleted on completion)
```

**Key observations from codebase:**
- The onboarding wizard (`scripts/onboarding/index.ts`) already exists as a scaffold with TODO placeholders for section implementations
- The template system uses `{{variable}}` Handlebars-style placeholders (`user-profile.template.yaml`)
- Section modules already have TypeScript files created: `liquid-assets.ts`, `investment-portfolio.ts`, `cash-flow.ts`, `debt-profile.ts`, `preferences.ts`
- Progress module (`modules/progress.ts`) handles save/resume logic
- Input validator (`modules/input-validator.ts`) handles type-safe user input

### Flow 2: User Profile -> Hedging Tools (via Config Loader)

```
fin-guru/data/user-profile.yaml
    |
    | (read at runtime)
    v
src/utils/config_loader.py (NEW)
    |
    | Parses YAML, extracts hedging section:
    |   preferences.margin_strategy.*
    |   preferences.portfolio_strategy.*
    |   user_profile.investment_portfolio.current_holdings.*
    |
    v
HedgeConfig (Pydantic model from hedging_inputs.py)
    |
    | Validated config passed to calculators
    v
+---------------------------+---------------------------+
|                           |                           |
v                           v                           v
RollingTracker          HedgeSizer              HedgeComparison
(src/analysis/)         (src/analysis/)         (src/analysis/)
    |                       |                       |
    | reads                 | reads                 | reads
    v                       v                       v
options.py              options.py              volatility.py
(Black-Scholes)         (Black-Scholes)         risk_metrics.py
market_data.py          market_data.py          market_data.py
```

**Key integration points from codebase inspection:**

1. **options_chain_cli.py -> rolling_tracker**: The existing options chain scanner (`src/analysis/options_chain_cli.py`) outputs `OptionsChainOutput` with contract data including Greeks. The rolling tracker needs to consume this output to find replacement positions when suggesting rolls. The integration is through the `OptionsChainOutput` Pydantic model -- the rolling tracker calls `scan_chain()` directly or parses its JSON output.

2. **options.py (Black-Scholes) -> hedge_sizer**: The existing `OptionsCalculator` class and `price_option()` convenience function provide Greeks calculation. The hedge sizer needs delta for position sizing. It imports `price_option` from `src.analysis.options` exactly as `options_chain_cli.py` already does (line 62 of that file).

3. **user-profile.yaml -> config_loader -> hedging tools**: The user profile already contains the hedging configuration section under `preferences.margin_strategy` (margin rates, safety ratios, expense tiers) and `preferences.portfolio_strategy` (layer definitions, deployment amounts). The config_loader reads this YAML and returns validated Pydantic models.

### Flow 3: Hedging Private Data

```
Hedging CLI (user actions: log-roll, update positions)
    |
    v
fin-guru-private/hedging/
    |-- positions.yaml         (current hedge positions)
    |-- roll-history.yaml      (historical roll log)
    +-- budget-tracker.yaml    (monthly insurance spend)
```

This directory is gitignored and contains personal position data. The rolling tracker CLI writes to it; the hedge sizer and comparison tools read from it. This follows the existing pattern where `fin-guru-private/` contains all personal data.

### Flow 4: Total Return Calculator

```
User Input: TSLA PLTR NVDA --days 252
    |
    v
total_return_cli.py (Layer 3)
    |
    +-> market_data.py (price data via yfinance)
    +-> yfinance dividend data (direct)
    |
    v
TotalReturnCalculator (Layer 2)
    |-- Price return: (end_price - start_price) / start_price
    |-- Dividend return: sum(dividends) / start_price
    |-- DRIP modeling: reinvest dividends at ex-date prices
    |
    v
TotalReturnOutput (Layer 1 - Pydantic model)
    |
    v
CLI output (text table or JSON)
```

### Flow 5: Knowledge Explorer Build Pipeline

```
Topic Data Files (JSON)                 Template HTML
scripts/explorer/topics/                scripts/explorer/template.html
    |-- dividend-strategy.json              |
    |-- options-greeks.json                 |
    |-- risk-management.json                |
    |-- portfolio-construction.json         |
    +-- tax-optimization.json               |
        |                                   |
        +------- Build Script (Bun) --------+
                 scripts/explorer/build.ts
                        |
                        v
                 docs/explorers/
                    |-- index.html (topic selector)
                    |-- dividend-strategy.html
                    |-- options-greeks.html
                    |-- risk-management.html
                    |-- portfolio-construction.html
                    +-- tax-optimization.html
```

**Completely separate from the Python architecture.** No shared code, no shared runtime, no shared dependencies. The only touchpoint is the Maya learner profile export: when a user completes self-assessment in the browser, the explorer generates a JSON file that Maya (Teaching Specialist agent) can read at session start.

### Flow 6: Knowledge Explorer -> Maya Integration (Optional)

```
Browser (explorer HTML)
    |
    | User completes self-assessment
    v
learner-profile.json (downloaded by user or saved via CLI)
    |
    v
fin-guru/data/learner-profile.json
    |
    | (read at session start by Teaching Specialist agent)
    v
Maya Brooks (Teaching Specialist)
    |-- Skips known concepts
    |-- Starts with first fuzzy/unknown
    +-- Uses appropriate teaching mode (guided/standard/yolo)
```

## Patterns to Follow

### Pattern 1: Config Loader (New Abstraction)

**What:** A Layer 2 module that reads user-profile.yaml and returns validated Pydantic models for tool-specific configuration sections.

**When:** Any time a hedging tool needs user configuration (portfolio value, hedge budget, margin parameters, preferred strategies).

**Why not just read YAML in each CLI?** Three reasons: (1) DRY -- four CLIs would duplicate the same parsing logic. (2) Validation -- Pydantic catches config errors once, at load time. (3) Testability -- mock the config loader in tests instead of mocking YAML file reads in every test file.

**Implementation:**

```python
# src/utils/config_loader.py
import yaml
from pathlib import Path
from src.models.hedging_inputs import HedgeConfig

class ConfigLoader:
    """Load and validate user configuration from user-profile.yaml."""

    def __init__(self, profile_path: Path | None = None):
        if profile_path is None:
            project_root = Path(__file__).parent.parent.parent
            profile_path = project_root / "fin-guru" / "data" / "user-profile.yaml"
        self._profile_path = profile_path
        self._raw: dict | None = None

    def _load_raw(self) -> dict:
        if self._raw is None:
            with open(self._profile_path) as f:
                self._raw = yaml.safe_load(f) or {}
        return self._raw

    def load_hedge_config(self) -> HedgeConfig:
        """Extract and validate hedging configuration."""
        raw = self._load_raw()
        prefs = raw.get("user_profile", {}).get("preferences", {})
        margin = prefs.get("margin_strategy", {})
        portfolio = prefs.get("portfolio_strategy", {})
        holdings = raw.get("user_profile", {}).get("investment_portfolio", {})

        return HedgeConfig(
            portfolio_value=holdings.get("total_value", 0),
            margin_rate=margin.get("margin_rate", 0.10875),
            target_ratio=margin.get("target_ratio", 4.0),
            monthly_hedge_budget=portfolio.get("deployment_split", {}).get("layer_3_hedge", 800),
            # ... additional fields
        )
```

**Key constraint:** config_loader.py sits at Layer 2. It imports from Layer 1 models only. CLI files (Layer 3) instantiate it and pass the result to calculators.

### Pattern 2: Hedging Models Follow Established Conventions

**What:** New Pydantic models in `hedging_inputs.py` and `total_return_inputs.py` follow the exact same patterns as existing model files.

**From codebase inspection, the established conventions are:**

```python
# Conventions extracted from existing models:
# 1. Literal types for enums (not Python Enum classes)
option_type: Literal["call", "put"]

# 2. Field descriptions on every field
strike: float = Field(..., gt=0.0, description="Option strike price")

# 3. | None for optional fields (not Optional[])
beta: float | None = None

# 4. field_validator for business logic constraints
@field_validator("volatility")
@classmethod
def validate_volatility_reasonable(cls, v: float) -> float: ...

# 5. model_config for pandas/numpy support
model_config = {"arbitrary_types_allowed": True}

# 6. Educational docstrings with WHAT/WHY sections
class HedgePosition(BaseModel):
    """
    Active hedge position tracking.

    WHAT: Tracks a single protective options position
    WHY: Rolling hedges require tracking entry, current value, and roll triggers
    """
```

### Pattern 3: CLI Subcommand Pattern (Rolling Tracker)

**What:** The rolling tracker needs subcommands (`status`, `suggest-roll`, `log-roll`, `history`), which is different from existing single-purpose CLIs.

**When:** A tool needs multiple related operations on the same domain data.

**Implementation using argparse subparsers:**

```python
# src/analysis/rolling_tracker_cli.py
def main():
    parser = argparse.ArgumentParser(description='Rolling hedge position tracker')
    subparsers = parser.add_subparsers(dest='command', required=True)

    # status subcommand
    status_parser = subparsers.add_parser('status', help='Show current positions')
    status_parser.add_argument('--output', choices=['text', 'json'], default='text')

    # suggest-roll subcommand
    roll_parser = subparsers.add_parser('suggest-roll', help='Suggest replacement positions')
    roll_parser.add_argument('ticker', help='Underlying ticker')
    roll_parser.add_argument('--otm-min', type=float, default=10.0)
    roll_parser.add_argument('--otm-max', type=float, default=20.0)
    roll_parser.add_argument('--days-min', type=int, default=25)
    roll_parser.add_argument('--days-max', type=int, default=45)

    args = parser.parse_args()
    # Route to handler based on args.command
```

This is the first CLI in the codebase to use subcommands. Document this as an extension of the established pattern, not a departure from it.

## Anti-Patterns to Avoid

### Anti-Pattern 1: Cross-Language Imports

**What:** Having Python code import or call TypeScript/Bun code, or vice versa.

**Why bad:** Creates brittle coupling between runtimes. Testing becomes painful. Deployment becomes fragile.

**Instead:** Communicate through files (YAML, JSON) and CLI invocations. The onboarding system writes user-profile.yaml; Python tools read it. The explorer build script reads JSON; it never calls Python. The hook system reads YAML; it never imports Python modules.

### Anti-Pattern 2: Hedging Tools Reading YAML Directly in CLI Layer

**What:** Each `*_cli.py` file parsing `user-profile.yaml` with its own YAML loading code.

**Why bad:** Duplicated parsing logic across 4 CLIs. No validation at the parsing boundary. No single place to add new config fields. Mocking YAML reads in every test file.

**Instead:** Use the config_loader (Pattern 1). Each CLI calls `ConfigLoader().load_hedge_config()` and gets a validated Pydantic model. Tests mock the config loader, not the file system.

### Anti-Pattern 3: Explorer Importing Python Modules

**What:** Building the knowledge explorer as a Python tool that imports from `src/models/` or `src/analysis/`.

**Why bad:** The explorer is a static HTML build tool. Adding Python dependencies means it cannot be used independently. It violates the zero-dependency philosophy specified in the project constraints.

**Instead:** The explorer is a pure Bun TypeScript build pipeline: `JSON + HTML template -> standalone HTML files`. No Python anywhere in its chain.

### Anti-Pattern 4: Circular Dependencies Between New and Existing Models

**What:** Having `hedging_inputs.py` import from `options_inputs.py` which imports from `hedging_inputs.py`.

**Why bad:** Python import cycles cause runtime crashes. The existing codebase has zero circular dependencies -- maintaining this is critical.

**Instead:** Follow the established pattern: each model file is self-contained. If hedging models need option-related types, they either define their own or import from `options_inputs.py` (one-way dependency). The dependency arrow goes: `hedging_inputs.py` -> `options_inputs.py`, never the reverse.

### Anti-Pattern 5: Hardcoded User Data in Public Code

**What:** Embedding personal names, specific portfolio values, or personal ticker lists in code that will be public.

**Why bad:** This is a public release milestone. Private data in git history is permanent.

**Instead:** All personal references flow through `user-profile.yaml` and template variables (`{user_name}`, `{portfolio_value}`). The existing codebase has some hardcoded personal name references that must be removed as part of ONBD-14.

## Component Integration Matrix

### What Depends on What

```
                 user-profile  options.py  market_data  options_inputs  hedging_inputs  config_loader
                     .yaml     (Layer 2)    (Layer 2)     (Layer 1)      (Layer 1)       (Layer 2)
                 ------------ ----------- ------------ --------------- --------------- -------------
Onboarding          WRITES       ---          ---           ---             ---             ---
Config Loader       READS        ---          ---           ---          IMPORTS          ---
Rolling Tracker     ---        CALLS        CALLS        IMPORTS        IMPORTS         CALLS
Hedge Sizer         ---        CALLS        CALLS        IMPORTS        IMPORTS         CALLS
Hedge Comparison    ---          ---         CALLS          ---          IMPORTS         CALLS
Total Return        ---          ---         CALLS          ---            ---             ---
Explorer            ---          ---          ---           ---             ---             ---
Hook (session)      READS        ---          ---           ---             ---             ---
```

Key takeaways:
- The **explorer has zero dependencies** on the Python codebase
- **config_loader** is the bridge between user-profile.yaml and hedging tools
- **options.py** and **market_data.py** are shared infrastructure used by both existing and new tools
- **Onboarding is write-only** -- it produces config files and never consumes Python tool output

### Build Order (Dependency Chain)

```
Phase 1: Onboarding (no dependencies on hedging or explorer)
    |
    | Produces: user-profile.yaml (needed by hedging config_loader)
    | Produces: Refactored hooks (needed by all future sessions)
    | Produces: Clean public codebase (no hardcoded personal data)
    |
    v
Phase 2: Hedging Tools (depends on user-profile.yaml from Phase 1)
    |
    | Requires: user-profile.yaml with hedging config section
    | Requires: Existing options.py, market_data.py (already in codebase)
    | Requires: config_loader.py (new, built as part of this phase)
    |
    v
Phase 3: Knowledge Explorer (no dependency on Phase 1 or 2 at runtime)
    |
    | NOTE: While the explorer has no runtime dependency, it benefits from
    | Phase 1 being complete because:
    |   - Onboarding can reference explorers ("assess your knowledge first?")
    |   - The CLI command `fin-guru explore <topic>` integrates with the agent system
    |   - Maya integration reads learner-profile.json (Phase 3 output)
    |
    | Can technically start in parallel with Phase 2
```

**Build order rationale:**
1. **Onboarding FIRST** because it removes hardcoded references, establishes the template/variable system, and produces the user-profile.yaml that hedging tools need. Everything downstream depends on configuration files being properly generated.
2. **Hedging SECOND** because it depends on the config file schema being stable and the public codebase being clean. It also needs the existing options/market-data infrastructure, which is already established.
3. **Explorer THIRD** (or parallel with hedging) because it has zero runtime dependencies on either. However, its integration with Maya and onboarding is cleaner if those systems are already in place.

## Integration Risk Assessment

### Risk 1: user-profile.yaml Schema Coupling (HIGH)

**What could go wrong:** Three independent components (onboarding, config_loader, hooks) all parse the same YAML file. Schema changes in one component break the others.

**Likelihood:** HIGH -- the user-profile.yaml is already 320 lines with nested structure. Adding a hedging section increases surface area.

**Mitigation:** Define the user-profile.yaml schema explicitly in a shared Pydantic model. The onboarding YAML generator validates output against it. The config_loader validates input against it. Schema changes are caught at the model level, not at runtime YAML parsing.

**Concrete step:** Create `src/models/user_profile_schema.py` as the single source of truth for the profile structure. Both the Bun onboarding code and the Python config_loader reference this schema (Bun via generated JSON Schema, Python via direct import).

### Risk 2: Hook Refactoring Regression (MEDIUM)

**What could go wrong:** Refactoring `load-fin-core-config.ts` from its current form to a cleaner Bun TypeScript version breaks session start context loading. All agents lose their financial context.

**Likelihood:** MEDIUM -- the hook is straightforward (read files, output text) but it loads 6+ files including portfolio CSVs.

**Mitigation:** 1:1 behavioral port with output comparison testing. Run old hook and new hook side by side, diff outputs. The hook's output is a text blob injected as system-reminder -- any difference in structure breaks agent behavior.

### Risk 3: Options Chain Scanner Integration (MEDIUM)

**What could go wrong:** The rolling tracker needs to call `scan_chain()` from `options_chain_cli.py` to find replacement positions. But `scan_chain()` currently prints to stderr and returns a Pydantic model -- it is designed as a CLI function, not a library function.

**Likelihood:** MEDIUM -- the function is well-structured and returns `OptionsChainOutput`, but it has side effects (stderr prints, direct yfinance calls).

**Mitigation:** The rolling tracker should either: (a) call `scan_chain()` directly, accepting the stderr output (it goes to stderr, not stdout, so it does not corrupt output), or (b) extract the scanning logic into a cleaner Layer 2 function. Option (a) is pragmatic and avoids refactoring existing working code. Option (b) is architecturally cleaner but riskier.

**Recommendation:** Option (a) for initial implementation. The stderr prints are informational and do not affect the returned `OptionsChainOutput` model. Refactoring can happen later if needed.

### Risk 4: Explorer Build Tooling Complexity (LOW)

**What could go wrong:** The Bun-based template engine for the explorer adds build complexity to a project that currently has no build step for its HTML assets.

**Likelihood:** LOW -- the build is a simple JSON + template merge, not a complex bundler.

**Mitigation:** Keep the build script minimal. A single `build.ts` that reads topic JSON, injects data into template HTML, writes output files. No bundler, no CSS preprocessor, no framework. The existing prototype (`dividend-strategy-explorer.html`) proves the zero-dependency approach works.

### Risk 5: Private Data Leaking to Git (MEDIUM)

**What could go wrong:** During the public release cleanup, some private data reference survives in code, comments, or generated files.

**Likelihood:** MEDIUM -- the current codebase has personal data in `user-profile.yaml`, `config.yaml`, and agent references. The onboarding milestone must replace all of these with template variables.

**Mitigation:** Automated grep sweep for known private patterns (real names, account numbers, portfolio values, ticker-specific allocations). Add a pre-commit hook or CI check that blocks commits containing patterns matching `fin-guru-private/` content.

### Risk 6: Subcommand Pattern Adoption (LOW)

**What could go wrong:** The rolling tracker introduces argparse subcommands, which is a new pattern in the codebase. Future contributors might not follow it consistently.

**Likelihood:** LOW -- argparse subcommands are well-documented Python stdlib.

**Mitigation:** Document the subcommand pattern in `src/CLAUDE.md` as a recognized extension of the CLI pattern. Include a template. The rolling tracker serves as the reference implementation.

## File Location Map (New Components)

### Onboarding (Bun TypeScript)

```
scripts/onboarding/                         # EXISTING directory
    index.ts                                # EXISTING (scaffold, needs implementation)
    modules/
        progress.ts                         # EXISTING
        input-validator.ts                  # EXISTING
        yaml-generator.ts                   # EXISTING
        broker-types.ts                     # EXISTING
        broker-registry.ts                  # EXISTING
        parsers/fidelity-parser.ts          # EXISTING
        templates/
            user-profile.template.yaml      # EXISTING
            config.template.yaml            # EXISTING
            system-context.template.md      # EXISTING
            env.template                    # EXISTING
            CLAUDE.template.md              # EXISTING
            mcp.template.json               # EXISTING
    sections/
        liquid-assets.ts                    # EXISTING (needs implementation)
        investment-portfolio.ts             # EXISTING (needs implementation)
        cash-flow.ts                        # EXISTING (needs implementation)
        debt-profile.ts                     # EXISTING (needs implementation)
        preferences.ts                      # EXISTING (needs implementation)
        broker-selection.ts                 # EXISTING (needs implementation)
        env-setup.ts                        # EXISTING (needs implementation)
        summary.ts                          # EXISTING (needs implementation)
scripts/setup.sh                            # NEW (orchestrates full setup)
```

### Hedging Tools (Python 3-Layer)

```
src/models/
    hedging_inputs.py                       # NEW (Layer 1)
    total_return_inputs.py                  # NEW (Layer 1)
    __init__.py                             # MODIFY (add exports)

src/utils/
    config_loader.py                        # NEW (Layer 2)

src/analysis/
    rolling_tracker.py                      # NEW (Layer 2 calculator)
    rolling_tracker_cli.py                  # NEW (Layer 3 CLI with subcommands)
    hedge_sizer.py                          # NEW (Layer 2 calculator)
    hedge_sizer_cli.py                      # NEW (Layer 3 CLI)
    hedge_comparison.py                     # NEW (Layer 2 calculator)
    hedge_comparison_cli.py                 # NEW (Layer 3 CLI)
    total_return.py                         # NEW (Layer 2 calculator)
    total_return_cli.py                     # NEW (Layer 3 CLI)

fin-guru-private/hedging/                   # NEW (gitignored, private data)
    positions.yaml                          # NEW
    roll-history.yaml                       # NEW
    budget-tracker.yaml                     # NEW

fin-guru/knowledge/                         # NEW (public educational content)
    hedging-strategies.md                   # NEW
    options-insurance-framework.md          # NEW
    dividend-total-return.md                # NEW
    borrow-vs-sell-tax.md                   # NEW

tests/python/
    test_rolling_tracker.py                 # NEW
    test_hedge_sizer.py                     # NEW
    test_hedge_comparison.py                # NEW
    test_total_return.py                    # NEW
    test_config_loader.py                   # NEW
```

### Knowledge Explorer (Bun TypeScript + Static HTML)

```
scripts/explorer/
    build.ts                                # NEW (Bun build script)
    template.html                           # NEW (shared template)
    topics/
        topic-schema.json                   # NEW (JSON Schema for validation)
        dividend-strategy.json              # NEW (migrated from prototype)
        options-greeks.json                 # NEW
        risk-management.json                # NEW
        portfolio-construction.json         # NEW
        tax-optimization.json               # NEW

docs/explorers/                             # NEW (generated output)
    index.html                              # NEW (topic selector)
    dividend-strategy.html                  # NEW (generated)
    options-greeks.html                     # NEW (generated)
    risk-management.html                    # NEW (generated)
    portfolio-construction.html             # NEW (generated)
    tax-optimization.html                   # NEW (generated)

fin-guru/data/
    learner-profile.json                    # NEW (optional, Maya integration)
```

### Hook Refactoring (Bun TypeScript)

```
.claude/hooks/
    load-fin-core-config.ts                 # MODIFY (refactor to clean Bun TS)
    skill-activation-prompt.ts              # MODIFY (refactor from .sh to .ts)
    post-tool-use-tracker.ts                # EXISTS (already .ts)
```

## Sources

All findings derived from direct codebase inspection:
- `/Users/ossieirondi/Documents/Irondi-Household/family-office/.planning/codebase/ARCHITECTURE.md`
- `/Users/ossieirondi/Documents/Irondi-Household/family-office/.planning/codebase/STACK.md`
- `/Users/ossieirondi/Documents/Irondi-Household/family-office/.planning/PROJECT.md`
- `/Users/ossieirondi/Documents/Irondi-Household/family-office/src/analysis/options_chain_cli.py`
- `/Users/ossieirondi/Documents/Irondi-Household/family-office/src/analysis/options.py`
- `/Users/ossieirondi/Documents/Irondi-Household/family-office/src/models/options_inputs.py`
- `/Users/ossieirondi/Documents/Irondi-Household/family-office/src/models/__init__.py`
- `/Users/ossieirondi/Documents/Irondi-Household/family-office/src/config.py`
- `/Users/ossieirondi/Documents/Irondi-Household/family-office/fin-guru/data/user-profile.yaml`
- `/Users/ossieirondi/Documents/Irondi-Household/family-office/scripts/onboarding/index.ts`
- `/Users/ossieirondi/Documents/Irondi-Household/family-office/.claude/hooks/load-fin-core-config.ts`
- `/Users/ossieirondi/Documents/Irondi-Household/family-office/.claude/settings.json`
- `/Users/ossieirondi/Documents/Irondi-Household/family-office/.dev/specs/backlog/finance-guru-interactive-knowledge-explorer.md`
