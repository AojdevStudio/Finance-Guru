"""Finance Guru Onboarding Wizard CLI.

Layer 3 CLI that orchestrates the 8-section interactive onboarding flow,
converts collected data into Pydantic models, and generates all configuration
files (user-profile.yaml, config.yaml, system-context.md, CLAUDE.md, .env,
.mcp.json) in the instance. Templates come from the engine this module ships in.

Callable via: uv run python -m src.cli.onboarding_wizard

ARCHITECTURE NOTE:
This is Layer 3 of the onboarding architecture:
    Layer 1: Pydantic Models (yaml_generation_inputs.py) - Data validation
    Layer 2: Calculators (yaml_generator.py, onboarding_sections.py) - Logic
    Layer 3: CLI Interface (THIS FILE) - Orchestration

Author: Finance Guru Development Team
Created: 2026-02-05
"""

import argparse
import atexit
import json
import shutil
import signal
import sys
import tempfile
import warnings
from collections.abc import Callable
from pathlib import Path
from typing import Any

import questionary

from src.config.instance_paths import InstancePaths
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
from src.utils.yaml_generator import YAMLGenerator, config_file_targets

SECTION_ORDER: list[tuple[SectionName, Callable[..., Any]]] = [
    (SectionName.LIQUID_ASSETS, run_liquid_assets_section),
    (SectionName.INVESTMENTS, run_investments_section),
    (SectionName.CASH_FLOW, run_cash_flow_section),
    (SectionName.DEBT, run_debt_section),
    (SectionName.PREFERENCES, run_preferences_section),
    (SectionName.BROKER, run_broker_section),
    (SectionName.ENV_SETUP, run_env_setup_section),
    (SectionName.SUMMARY, run_summary_section),
]


PROGRESS_FILE_NAME = ".onboarding-progress.json"


def _progress_file() -> Path:
    """Return the progress file in the instance, since it holds private answers."""
    return InstancePaths.resolve().root / PROGRESS_FILE_NAME


def save_progress(state: OnboardingState) -> None:
    """Atomically save wizard progress to the instance's .onboarding-progress.json.

    Uses tempfile + rename pattern for crash safety:
    write to temp file in same directory, then atomic rename.
    """
    data = state.model_dump(mode="json")
    progress_file = _progress_file()
    tmp_fd, tmp_path = tempfile.mkstemp(
        dir=str(progress_file.parent),
        suffix=".tmp",
        prefix=".onboarding-progress-",
    )
    try:
        with open(tmp_fd, "w") as f:
            json.dump(data, f, indent=2)
        Path(tmp_path).rename(progress_file)
    except Exception:
        Path(tmp_path).unlink(missing_ok=True)
        raise


def load_progress() -> "OnboardingState | None":
    """Load saved progress, return None if not found or corrupt.

    A corrupt file (invalid JSON or schema mismatch) is silently
    ignored -- the wizard starts fresh. This handles edge cases
    where a prior save was interrupted mid-write (though atomic
    rename makes this unlikely).
    """
    progress_file = _progress_file()
    if not progress_file.exists():
        return None
    try:
        data = json.loads(progress_file.read_text())
        return OnboardingState.model_validate(data)
    except (json.JSONDecodeError, Exception):
        return None


def delete_progress() -> None:
    """Delete progress file after successful completion."""
    _progress_file().unlink(missing_ok=True)


class WizardInterruptHandler:
    """Two-layer safety net for saving wizard progress on interrupt.

    Layer 1: SIGINT handler -- catches Ctrl+C, saves progress, prints message.
    Layer 2: atexit handler -- backup save on any clean exit.

    Note: questionary (via prompt_toolkit) installs its own SIGINT handler
    during prompts, so .ask() returns None on Ctrl+C. The SIGINT handler
    here is a BACKUP for interrupts between prompts (during processing).
    The primary interrupt detection is checking for None return from .ask().
    """

    def __init__(self) -> None:
        self._state: OnboardingState | None = None
        self._active: bool = False

    def setup(self) -> None:
        """Register signal and atexit handlers."""
        signal.signal(signal.SIGINT, self._handle_sigint)
        atexit.register(self._save_on_exit)
        self._active = True

    def update_state(self, state: OnboardingState) -> None:
        """Update the current state reference after each section."""
        self._state = state

    def deactivate(self) -> None:
        """Deactivate after successful completion (prevent stale saves)."""
        self._active = False
        self._state = None

    def _handle_sigint(self, signum: int, frame: object) -> None:
        """SIGINT handler: save progress and exit."""
        self._save_on_exit()
        print("\n\nProgress saved. Run the wizard again to resume.")
        raise SystemExit(0)

    def _save_on_exit(self) -> None:
        """Save progress if there is anything to save."""
        if not self._active or self._state is None:
            return
        if (
            hasattr(self._state, "completed_sections")
            and len(self._state.completed_sections) > 0
        ):
            import contextlib

            with contextlib.suppress(Exception):
                save_progress(self._state)


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


def _safe_enum(enum_cls, raw_value: str, default):
    """Safely convert a string to an enum instance with fallback."""
    if raw_value is None:
        return default
    try:
        return enum_cls(raw_value)
    except ValueError:
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
        ValueError: If Environment Setup stored no owner name.
    """
    la = state.data.get(SectionName.LIQUID_ASSETS.value, {})
    inv = state.data.get(SectionName.INVESTMENTS.value, {})
    cf = state.data.get(SectionName.CASH_FLOW.value, {})
    debt = state.data.get(SectionName.DEBT.value, {})
    prefs = state.data.get(SectionName.PREFERENCES.value, {})
    env = state.data.get(SectionName.ENV_SETUP.value, {})

    user_name = env.get("user_name")
    if not isinstance(user_name, str) or not user_name.strip():
        raise ValueError(
            "Environment Setup has no owner name. "
            "Run the wizard again and enter your name."
        )

    identity = UserIdentityInput(
        user_name=user_name,
        language=env.get("language", "English"),
    )

    liquid_assets = LiquidAssetsInput(
        total=la.get("total", 0.0),
        accounts_count=la.get("accounts_count", 0),
        average_yield=la.get("average_yield", 0.0),
        structure=la.get("structure"),
    )

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
        google_sheets_id=None,
        account_number=inv.get("account_number"),
    )

    cash_flow = CashFlowInput(
        monthly_income=cf.get("monthly_income", 1000.0),
        fixed_expenses=cf.get("fixed_expenses", 0.0),
        variable_expenses=cf.get("variable_expenses", 0.0),
        current_savings=cf.get("current_savings", 0.0),
        investment_capacity=cf.get("investment_capacity", 0.0),
    )

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

    preferences = UserPreferencesInput(
        investment_philosophy=_safe_enum(
            InvestmentPhilosophy,
            prefs.get("investment_philosophy"),
            InvestmentPhilosophy.BALANCED,
        ),
        focus_areas=prefs.get("focus_areas", []),
        emergency_fund_months=prefs.get("emergency_fund_months", 6),
    )

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
        google_sheets_credentials=None,
    )


_ENGINE_ROOT = Path(__file__).resolve().parents[2]
_TEMPLATE_DIR = _ENGINE_ROOT / "scripts" / "onboarding" / "modules" / "templates"
_BACKED_UP = {"CLAUDE.md", ".env", ".mcp.json"}


def _backup_file(path: Path) -> None:
    """Create a .backup copy of a file if it exists."""
    if path.exists():
        backup_path = path.parent / f"{path.name}.backup"
        backup_path.unlink(missing_ok=True)
        shutil.copy2(path, backup_path)
        print(f"  Backed up: {path} -> {backup_path}")


def generate_config_files(user_data: UserDataInput, paths: InstancePaths) -> None:
    """Generate all configuration files and write them into the instance.

    Templates come from the engine this module ships in. Every file goes under
    the instance root, and existing CLAUDE.md, .env, and .mcp.json files get a
    .backup copy first.

    Args:
        user_data: Validated user data from the onboarding wizard.
        paths: The instance that owns every generated file.

    Raises:
        ValueError: If any target resolves outside the instance root. Nothing
            is written in that case.
    """
    output = YAMLGenerator(str(_TEMPLATE_DIR)).generate_all_configs(user_data)
    targets = config_file_targets(output, paths)

    for file_path, content in targets.items():
        if file_path.name in _BACKED_UP:
            _backup_file(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")

    print()
    print("  Generated configuration files:")
    for file_path in targets:
        print(f"    - {file_path}")
    print()
    print("  NOTE: If you had a custom .mcp.json, a backup was created.")
    print("  You may need to manually merge your custom MCP server entries")
    print("  into the newly generated file.")
    print()


def run_wizard(dry_run: bool = False) -> None:
    """Run the full 8-section onboarding wizard.

    Supports save/resume: if a previous session was interrupted, the wizard
    detects .onboarding-progress.json and offers to resume from where the
    user left off. Progress is saved after each completed section and on
    Ctrl+C. The progress file is deleted on successful completion.

    Args:
        dry_run: If True, skip file generation and print what would
            be generated instead.
    """
    paths = InstancePaths.resolve()
    if paths.root.is_relative_to(_ENGINE_ROOT):
        print()
        print("  The wizard writes your private files to an instance, not the engine.")
        print("  Set FIN_GURU_DATA_ROOT to your instance, or run from the instance.")
        print()
        raise SystemExit(1)

    print()
    print(_BANNER)
    print()

    saved_state = load_progress()
    start_index = 0

    if saved_state is not None and len(saved_state.completed_sections) > 0:
        n_complete = len(saved_state.completed_sections)
        print(
            f"  Found saved progress: {n_complete} of "
            f"{len(SECTION_ORDER)} sections complete."
        )
        resume = questionary.confirm(
            "Resume from where you left off?", default=True
        ).ask()
        if resume:
            state = saved_state
            section_names = [name for name, _ in SECTION_ORDER]
            if state.current_section in section_names:
                start_index = section_names.index(state.current_section)
            else:
                start_index = n_complete
        else:
            delete_progress()
            state = OnboardingState.create_new()
    else:
        state = OnboardingState.create_new()

    handler = WizardInterruptHandler()
    handler.setup()

    try:
        for _section_name, runner_fn in SECTION_ORDER[start_index:]:
            state = runner_fn(state)
            handler.update_state(state)
            if len(state.completed_sections) > 0:
                save_progress(state)
    except KeyboardInterrupt:
        if len(state.completed_sections) > 0:
            save_progress(state)
        print("\n\n  Progress saved. Run the wizard again to resume.\n")
        return

    summary_data = state.data.get(SectionName.SUMMARY.value, {})
    if not summary_data.get("confirmed", False):
        print("  Onboarding was not confirmed. No files generated.")
        return

    try:
        user_data = convert_state_to_user_data(state, str(paths.root))
    except ValueError as error:
        print(f"  {error} No files generated.")
        raise SystemExit(1) from error

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
        for file_path in (
            paths.profile,
            paths.config,
            paths.system_context,
            paths.root / "CLAUDE.md",
            paths.env_file,
            paths.root / ".mcp.json",
        ):
            print(f"    - {file_path}")
        print()
        handler.deactivate()
        delete_progress()
        return

    try:
        generate_config_files(user_data, paths)
    except ValueError as error:
        print(f"  {error}")
        raise SystemExit(1) from error

    handler.deactivate()
    delete_progress()

    print(_COMPLETION)
    print()


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
        print("  Onboarding interrupted.")
        print()
        sys.exit(130)


if __name__ == "__main__":
    main()
