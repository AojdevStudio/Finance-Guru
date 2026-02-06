"""
Finance Guru Onboarding Wizard CLI

Layer 3 CLI that orchestrates the 8-section interactive onboarding flow,
converts collected data into Pydantic models, and generates all configuration
files (user-profile.yaml, config.yaml, system-context.md, CLAUDE.md, .env,
mcp.json) to their correct output locations.

Callable via: uv run python src/cli/onboarding_wizard.py

ARCHITECTURE NOTE:
This is Layer 3 of the onboarding architecture:
    Layer 1: Pydantic Models (yaml_generation_inputs.py) - Data validation
    Layer 2: Calculators (yaml_generator.py, onboarding_sections.py) - Logic
    Layer 3: CLI Interface (THIS FILE) - Orchestration

Author: Finance Guru Development Team
Created: 2026-02-05
"""

import argparse
import shutil
import sys
import warnings
from pathlib import Path

# Add project root to path for direct invocation
_project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_project_root))

from src.models.onboarding_inputs import OnboardingState, SectionName
from src.models.yaml_generation_inputs import (
    AllocationStrategy,
    CashFlowInput,
    DebtProfileInput,
    InvestmentPhilosophy,
    InvestmentPortfolioInput,
    LiquidAssetsInput,
    MCPConfigInput,
    RiskTolerance,
    UserDataInput,
    UserIdentityInput,
    UserPreferencesInput,
)
from src.utils.onboarding_sections import (
    run_broker_section,
    run_cash_flow_section,
    run_debt_section,
    run_env_setup_section,
    run_investments_section,
    run_liquid_assets_section,
    run_preferences_section,
    run_summary_section,
)
from src.utils.yaml_generator import YAMLGenerator, write_config_files

# ---------------------------------------------------------------------------
# Section execution order
# ---------------------------------------------------------------------------

SECTION_ORDER: list[tuple[SectionName, callable]] = [
    (SectionName.LIQUID_ASSETS, run_liquid_assets_section),
    (SectionName.INVESTMENTS, run_investments_section),
    (SectionName.CASH_FLOW, run_cash_flow_section),
    (SectionName.DEBT, run_debt_section),
    (SectionName.PREFERENCES, run_preferences_section),
    (SectionName.BROKER, run_broker_section),
    (SectionName.ENV_SETUP, run_env_setup_section),
    (SectionName.SUMMARY, run_summary_section),
]

# ---------------------------------------------------------------------------
# Welcome / completion banners
# ---------------------------------------------------------------------------

_BANNER = """
\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
  Finance Guru Onboarding Wizard
\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

  Welcome! This wizard will collect your financial information
  and configure Finance Guru for your personal use.

  You will complete 8 sections:
    1. Liquid Assets     5. Investment Preferences
    2. Investments        6. Broker Selection
    3. Cash Flow          7. Environment Setup
    4. Debt Profile       8. Summary & Confirmation

  Tip: You can skip any question after 3 invalid attempts.
  Press Ctrl+C at any time to exit.
""".strip()


_COMPLETION = """
\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
  Onboarding Complete!
\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

  Your Finance Guru is now configured and ready.

  Next steps:
    1. Start a new Claude Code session to load your profile
    2. Invoke Finance Guru agents via slash commands
    3. Try: /fin-guru to speak with the Finance Orchestrator
""".strip()


# ---------------------------------------------------------------------------
# State-to-model conversion
# ---------------------------------------------------------------------------


def _safe_enum(enum_cls, raw_value: str, default):
    """Safely convert a string to an enum instance with fallback."""
    if raw_value is None:
        return default
    try:
        return enum_cls(raw_value)
    except ValueError:
        # Try case-insensitive match
        for member in enum_cls:
            if member.value.lower() == raw_value.lower():
                return member
        warnings.warn(
            f"Unknown {enum_cls.__name__} value '{raw_value}', "
            f"using default '{default.value}'",
            stacklevel=2,
        )
        return default


def convert_state_to_user_data(
    state: OnboardingState, project_root: str
) -> UserDataInput:
    """Convert completed wizard state into a validated UserDataInput.

    The wizard's section runners store human-readable strings in
    state.data (e.g., "aggressive", "growth"). This function converts
    those strings to actual enum instances for UserDataInput.

    Args:
        state: Completed OnboardingState with data from all 8 sections.
        project_root: Absolute path to the project root directory.

    Returns:
        Validated UserDataInput ready for YAML generation.

    Raises:
        KeyError: If required section data is missing.
    """
    # --- Section data with safe defaults ---
    la = state.data.get(SectionName.LIQUID_ASSETS.value, {})
    inv = state.data.get(SectionName.INVESTMENTS.value, {})
    cf = state.data.get(SectionName.CASH_FLOW.value, {})
    debt = state.data.get(SectionName.DEBT.value, {})
    prefs = state.data.get(SectionName.PREFERENCES.value, {})
    env = state.data.get(SectionName.ENV_SETUP.value, {})

    # --- Identity (from env_setup section) ---
    identity = UserIdentityInput(
        user_name=env.get("user_name", "User"),
        language=env.get("language", "English"),
    )

    # --- Liquid Assets ---
    liquid_assets = LiquidAssetsInput(
        total=la.get("total", 0.0),
        accounts_count=la.get("accounts_count", 0),
        average_yield=la.get("average_yield", 0.0),
        structure=la.get("structure"),
    )

    # --- Investment Portfolio (enum conversion critical here) ---
    portfolio = InvestmentPortfolioInput(
        total_value=inv.get("total_value", 0.0),
        brokerage=inv.get("brokerage"),
        has_retirement=inv.get("has_retirement", False),
        retirement_value=inv.get("retirement_value"),
        allocation_strategy=_safe_enum(
            AllocationStrategy,
            inv.get("allocation_strategy"),
            AllocationStrategy.PASSIVE,
        ),
        risk_tolerance=_safe_enum(
            RiskTolerance,
            inv.get("risk_tolerance"),
            RiskTolerance.MODERATE,
        ),
        google_sheets_id=inv.get("google_sheets_id"),
        account_number=inv.get("account_number"),
    )

    # --- Cash Flow ---
    cash_flow = CashFlowInput(
        monthly_income=cf.get("monthly_income", 1000.0),
        fixed_expenses=cf.get("fixed_expenses", 0.0),
        variable_expenses=cf.get("variable_expenses", 0.0),
        current_savings=cf.get("current_savings", 0.0),
        investment_capacity=cf.get("investment_capacity", 0.0),
    )

    # --- Debt Profile ---
    debt_profile = DebtProfileInput(
        has_mortgage=debt.get("has_mortgage", False),
        mortgage_balance=debt.get("mortgage_balance"),
        mortgage_payment=debt.get("mortgage_payment"),
        has_student_loans=debt.get("has_student_loans", False),
        student_loan_balance=debt.get("student_loan_balance"),
        student_loan_rate=debt.get("student_loan_rate"),
        has_auto_loans=debt.get("has_auto_loans", False),
        auto_loan_balance=debt.get("auto_loan_balance"),
        auto_loan_rate=debt.get("auto_loan_rate"),
        has_credit_cards=debt.get("has_credit_cards", False),
        credit_card_balance=debt.get("credit_card_balance"),
        weighted_rate=debt.get("weighted_rate"),
        other_debt=debt.get("other_debt"),
    )

    # --- Preferences (enum conversion) ---
    preferences = UserPreferencesInput(
        investment_philosophy=_safe_enum(
            InvestmentPhilosophy,
            prefs.get("investment_philosophy"),
            InvestmentPhilosophy.BALANCED,
        ),
        focus_areas=prefs.get("focus_areas", []),
        emergency_fund_months=prefs.get("emergency_fund_months", 6),
    )

    # --- MCP Config (from env_setup) ---
    mcp = MCPConfigInput(
        has_alphavantage=env.get("has_alphavantage", False),
        alphavantage_key=env.get("alphavantage_key"),
        has_brightdata=env.get("has_brightdata", False),
        brightdata_key=env.get("brightdata_key"),
    )

    return UserDataInput(
        identity=identity,
        liquid_assets=liquid_assets,
        portfolio=portfolio,
        cash_flow=cash_flow,
        debt=debt_profile,
        preferences=preferences,
        mcp=mcp,
        project_root=project_root,
        google_sheets_credentials=env.get("google_sheets_credentials"),
    )


# ---------------------------------------------------------------------------
# Config file generation
# ---------------------------------------------------------------------------

_TEMPLATE_DIR = "scripts/onboarding/modules/templates"


def _backup_file(path: Path) -> None:
    """Create a .backup copy of a file if it exists."""
    if path.exists():
        backup_path = path.parent / f"{path.name}.backup"
        shutil.copy2(path, backup_path)
        print(f"  Backed up: {path} -> {backup_path}")


def generate_config_files(
    user_data: UserDataInput, project_root: Path
) -> None:
    """Generate all configuration files and write to correct locations.

    Private config files (user-profile.yaml, config.yaml, system-context.md)
    are written under fin-guru-private/ via write_config_files().

    Project-root files (CLAUDE.md, .env, .claude/mcp.json) are written
    separately via explicit Path.write_text() to their correct locations.

    Args:
        user_data: Validated user data from the onboarding wizard.
        project_root: Path to the project root directory.
    """
    template_dir = project_root / _TEMPLATE_DIR
    generator = YAMLGenerator(str(template_dir))
    output = generator.generate_all_configs(user_data)

    # --- Write private config files to fin-guru-private/ ---
    private_base = project_root / "fin-guru-private"
    write_config_files(output, str(private_base))

    # --- Write project-root files with backup ---

    # CLAUDE.md
    claude_path = project_root / "CLAUDE.md"
    _backup_file(claude_path)
    claude_path.write_text(output.claude_md, encoding="utf-8")

    # .env
    env_path = project_root / ".env"
    _backup_file(env_path)
    env_path.write_text(output.env_file, encoding="utf-8")

    # .claude/mcp.json
    mcp_dir = project_root / ".claude"
    mcp_dir.mkdir(parents=True, exist_ok=True)
    mcp_path = mcp_dir / "mcp.json"
    _backup_file(mcp_path)
    mcp_path.write_text(output.mcp_json, encoding="utf-8")

    # --- Print results ---
    print()
    print("  Generated configuration files:")
    print(f"    - {private_base / 'fin-guru' / 'data' / 'user-profile.yaml'}")
    print(f"    - {private_base / 'fin-guru' / 'config.yaml'}")
    print(f"    - {private_base / 'fin-guru' / 'data' / 'system-context.md'}")
    print(f"    - {claude_path}")
    print(f"    - {env_path}")
    print(f"    - {mcp_path}")
    print()
    print("  NOTE: If you had a custom .claude/mcp.json, a backup was created.")
    print("  You may need to manually merge your custom MCP server entries")
    print("  into the newly generated file.")
    print()


# ---------------------------------------------------------------------------
# Wizard orchestrator
# ---------------------------------------------------------------------------


def run_wizard(dry_run: bool = False) -> None:
    """Run the full 8-section onboarding wizard.

    Args:
        dry_run: If True, skip file generation and print what would
            be generated instead.
    """
    print()
    print(_BANNER)
    print()

    state = OnboardingState.create_new()

    # Execute each section in order
    for _section_name, runner_fn in SECTION_ORDER:
        state = runner_fn(state)

    # Check if summary was confirmed
    summary_data = state.data.get(SectionName.SUMMARY.value, {})
    if not summary_data.get("confirmed", False):
        print("  Onboarding was not confirmed. No files generated.")
        return

    # Convert state to validated model
    project_root = Path.cwd()
    user_data = convert_state_to_user_data(state, str(project_root))

    if dry_run:
        print()
        print("  [DRY RUN] Would generate configuration files for:")
        print(f"    User: {user_data.identity.user_name}")
        print(f"    Language: {user_data.identity.language}")
        print(f"    Portfolio: ${user_data.portfolio.total_value:,.2f}")
        print(f"    Risk: {user_data.portfolio.risk_tolerance.value}")
        print(f"    Philosophy: {user_data.preferences.investment_philosophy.value}")
        print()
        print("  [DRY RUN] Files would be written to:")
        print(f"    - fin-guru-private/fin-guru/data/user-profile.yaml")
        print(f"    - fin-guru-private/fin-guru/config.yaml")
        print(f"    - fin-guru-private/fin-guru/data/system-context.md")
        print(f"    - {project_root / 'CLAUDE.md'}")
        print(f"    - {project_root / '.env'}")
        print(f"    - {project_root / '.claude' / 'mcp.json'}")
        print()
        return

    # Generate and write config files
    generate_config_files(user_data, project_root)

    print(_COMPLETION)
    print()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Parse arguments and run the onboarding wizard."""
    parser = argparse.ArgumentParser(
        prog="onboarding-wizard",
        description="Finance Guru interactive onboarding wizard. "
        "Collects your financial information and generates personalized "
        "configuration files.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run the wizard but skip file generation (preview what would be generated)",
    )

    args = parser.parse_args()

    try:
        run_wizard(dry_run=args.dry_run)
    except KeyboardInterrupt:
        print()
        print()
        print("  Onboarding interrupted. Progress not saved "
              "(save/resume is Phase 4).")
        print()
        sys.exit(130)


if __name__ == "__main__":
    main()
