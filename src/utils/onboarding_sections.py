"""
Onboarding Wizard Section Runners for Finance Guru

Eight section runner functions that prompt users through the financial
profile collection using questionary. Each function takes an
OnboardingState, collects data via interactive prompts, stores raw
values in state.data[section_name], and returns the updated state.

The section runners store human-readable strings for enum fields (e.g.,
"aggressive", "growth"). String-to-enum conversion happens in Plan 02's
convert_state_to_user_data function.

Author: Finance Guru Development Team
Created: 2026-02-05
"""

from typing import Optional

import questionary

from src.models.onboarding_inputs import OnboardingState, SectionName
from src.models.yaml_generation_inputs import (
    AllocationStrategy,
    InvestmentPhilosophy,
    RiskTolerance,
)
from src.utils.onboarding_validators import (
    ask_with_retry,
    validate_currency,
    validate_percentage,
    validate_positive_integer,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SEPARATOR = "\u2501" * 54  # heavy horizontal box line


def _print_section_header(number: int, name: str, description: str) -> None:
    """Print a consistent section header with number, name, and blurb."""
    print()
    print(_SEPARATOR)
    print(f"  Section {number} of 8: {name}")
    print(_SEPARATOR)
    print()
    print(f"  {description}")
    print()


def _format_currency(value: float) -> str:
    """Format a float as a dollar string for display."""
    return f"${value:,.2f}"


def _format_percentage_display(decimal: float) -> str:
    """Format a decimal (e.g. 0.045) as a percentage string."""
    return f"{decimal * 100:.2f}%"


# ---------------------------------------------------------------------------
# Section 1: Liquid Assets
# ---------------------------------------------------------------------------


def run_liquid_assets_section(state: OnboardingState) -> OnboardingState:
    """Collect liquid asset information (cash, savings, checking).

    Stores:
        total (float), accounts_count (int), average_yield (decimal float),
        structure (str or None)
    """
    _print_section_header(
        1,
        "Liquid Assets",
        "Let's start with your cash accounts (checking, savings, business).",
    )

    total = ask_with_retry(
        prompt_fn=lambda: questionary.text(
            "What is the total value of your liquid cash? (e.g., $25,000 or 25k)"
        ).ask(),
        validator=validate_currency,
        default=0.0,
    )
    if total is None:
        return state

    accounts_count = ask_with_retry(
        prompt_fn=lambda: questionary.text(
            "How many accounts do you have? (checking, savings, business)"
        ).ask(),
        validator=validate_positive_integer,
        default=1,
    )
    if accounts_count is None:
        return state

    average_yield_pct = ask_with_retry(
        prompt_fn=lambda: questionary.text(
            "What is the average yield on your cash? (e.g., 4.5 for 4.5%)"
        ).ask(),
        validator=validate_percentage,
        default=0.0,
    )
    if average_yield_pct is None:
        return state

    # Convert percentage to decimal for storage (4.5 -> 0.045)
    average_yield = average_yield_pct / 100.0

    structure: Optional[str] = questionary.text(
        "Describe your account structure (optional, press Enter to skip):"
    ).ask()

    if structure is not None:
        structure = structure.strip() or None

    state.data[SectionName.LIQUID_ASSETS.value] = {
        "total": total,
        "accounts_count": accounts_count,
        "average_yield": average_yield,
        "structure": structure,
    }

    state.mark_complete(SectionName.LIQUID_ASSETS, SectionName.INVESTMENTS)
    print()
    print(f"  Liquid Assets: Complete ({_format_currency(total)})")
    print()
    return state


# ---------------------------------------------------------------------------
# Section 2: Investments
# ---------------------------------------------------------------------------


def run_investments_section(state: OnboardingState) -> OnboardingState:
    """Collect investment portfolio details.

    Stores dict matching InvestmentPortfolioInput fields.
    Enum fields stored as raw human-readable strings.
    """
    _print_section_header(
        2,
        "Investment Portfolio",
        "Now let's gather information about your investment portfolio.",
    )

    total_value = ask_with_retry(
        prompt_fn=lambda: questionary.text(
            "What is the total value of your brokerage/investment accounts? (e.g., $100,000)"
        ).ask(),
        validator=validate_currency,
        default=0.0,
    )
    if total_value is None:
        return state

    brokerage: Optional[str] = questionary.text(
        "Primary brokerage name (optional, press Enter to skip):"
    ).ask()
    if brokerage is not None:
        brokerage = brokerage.strip() or None

    has_retirement = questionary.confirm(
        "Do you have retirement accounts (401k, IRA, etc.)?",
        default=False,
    ).ask()
    if has_retirement is None:
        return state

    retirement_value: Optional[float] = None
    if has_retirement:
        retirement_value = ask_with_retry(
            prompt_fn=lambda: questionary.text(
                "What is the total value of your retirement accounts?"
            ).ask(),
            validator=validate_currency,
            default=0.0,
        )
        if retirement_value is None:
            return state

    # Allocation strategy -- select from enum values
    allocation_choices = [e.value for e in AllocationStrategy]
    allocation_strategy = questionary.select(
        "What is your portfolio allocation strategy?",
        choices=allocation_choices,
    ).ask()
    if allocation_strategy is None:
        return state

    # Risk tolerance -- select from enum values
    risk_choices = [e.value for e in RiskTolerance]
    risk_tolerance = questionary.select(
        "What is your risk tolerance?",
        choices=risk_choices,
    ).ask()
    if risk_tolerance is None:
        return state

    google_sheets_id: Optional[str] = questionary.text(
        "Google Sheets portfolio tracker ID (optional, press Enter to skip):"
    ).ask()
    if google_sheets_id is not None:
        google_sheets_id = google_sheets_id.strip() or None

    account_number: Optional[str] = questionary.text(
        "Primary account number last 4 digits (optional, press Enter to skip):"
    ).ask()
    if account_number is not None:
        account_number = account_number.strip() or None

    state.data[SectionName.INVESTMENTS.value] = {
        "total_value": total_value,
        "brokerage": brokerage,
        "has_retirement": has_retirement,
        "retirement_value": retirement_value,
        "allocation_strategy": allocation_strategy,
        "risk_tolerance": risk_tolerance,
        "google_sheets_id": google_sheets_id,
        "account_number": account_number,
    }

    state.mark_complete(SectionName.INVESTMENTS, SectionName.CASH_FLOW)
    print()
    print(f"  Investment Portfolio: Complete ({_format_currency(total_value)})")
    print()
    return state


# ---------------------------------------------------------------------------
# Section 3: Cash Flow
# ---------------------------------------------------------------------------


def run_cash_flow_section(state: OnboardingState) -> OnboardingState:
    """Collect monthly cash flow information.

    Stores dict matching CashFlowInput fields.
    """
    _print_section_header(
        3,
        "Cash Flow",
        "Let's understand your monthly cash flow (after-tax income and expenses).",
    )

    monthly_income = ask_with_retry(
        prompt_fn=lambda: questionary.text(
            "What is your monthly after-tax income?"
        ).ask(),
        validator=validate_currency,
        default=0.0,
    )
    if monthly_income is None:
        return state

    print("  Fixed expenses are recurring bills (rent, insurance, subscriptions, etc.)")
    fixed_expenses = ask_with_retry(
        prompt_fn=lambda: questionary.text(
            "What are your total fixed monthly expenses?"
        ).ask(),
        validator=validate_currency,
        default=0.0,
    )
    if fixed_expenses is None:
        return state

    print("  Variable expenses include groceries, dining, entertainment, shopping, etc.")
    variable_expenses = ask_with_retry(
        prompt_fn=lambda: questionary.text(
            "What are your average variable monthly expenses?"
        ).ask(),
        validator=validate_currency,
        default=0.0,
    )
    if variable_expenses is None:
        return state

    current_savings = ask_with_retry(
        prompt_fn=lambda: questionary.text(
            "How much do you currently save each month?"
        ).ask(),
        validator=validate_currency,
        default=0.0,
    )
    if current_savings is None:
        return state

    surplus = monthly_income - fixed_expenses - variable_expenses
    print(f"  Calculated monthly surplus: {_format_currency(surplus)}")
    print()

    investment_capacity = ask_with_retry(
        prompt_fn=lambda: questionary.text(
            "What is your monthly investment capacity?"
        ).ask(),
        validator=validate_currency,
        default=0.0,
    )
    if investment_capacity is None:
        return state

    state.data[SectionName.CASH_FLOW.value] = {
        "monthly_income": monthly_income,
        "fixed_expenses": fixed_expenses,
        "variable_expenses": variable_expenses,
        "current_savings": current_savings,
        "investment_capacity": investment_capacity,
    }

    state.mark_complete(SectionName.CASH_FLOW, SectionName.DEBT)
    print()
    print("  Cash Flow: Complete")
    print()
    return state


# ---------------------------------------------------------------------------
# Section 4: Debt
# ---------------------------------------------------------------------------


def run_debt_section(state: OnboardingState) -> OnboardingState:
    """Collect debt obligation details.

    Stores dict matching DebtProfileInput fields. Rates are converted
    from percentage to decimal (4.5 -> 0.045) when stored.
    """
    _print_section_header(
        4,
        "Debt Profile",
        "Let's understand your debt obligations and liabilities.",
    )

    # --- Mortgage ---
    has_mortgage = questionary.confirm(
        "Do you have a mortgage?", default=False
    ).ask()
    if has_mortgage is None:
        return state

    mortgage_balance: Optional[float] = None
    mortgage_payment: Optional[float] = None
    if has_mortgage:
        mortgage_balance = ask_with_retry(
            prompt_fn=lambda: questionary.text(
                "What is your current mortgage balance?"
            ).ask(),
            validator=validate_currency,
            default=0.0,
        )
        mortgage_payment = ask_with_retry(
            prompt_fn=lambda: questionary.text(
                "What is your monthly mortgage payment?"
            ).ask(),
            validator=validate_currency,
            default=0.0,
        )

    # --- Student Loans ---
    has_student_loans = questionary.confirm(
        "Do you have student loans?", default=False
    ).ask()
    if has_student_loans is None:
        return state

    student_loan_balance: Optional[float] = None
    student_loan_rate: Optional[float] = None
    if has_student_loans:
        student_loan_balance = ask_with_retry(
            prompt_fn=lambda: questionary.text(
                "What is the total balance of your student loans?"
            ).ask(),
            validator=validate_currency,
            default=0.0,
        )
        student_loan_rate_pct = ask_with_retry(
            prompt_fn=lambda: questionary.text(
                "What is the average interest rate on your student loans? (e.g., 5.5 for 5.5%)"
            ).ask(),
            validator=validate_percentage,
            default=0.0,
        )
        student_loan_rate = (
            student_loan_rate_pct / 100.0 if student_loan_rate_pct else 0.0
        )

    # --- Auto Loans ---
    has_auto_loans = questionary.confirm(
        "Do you have any auto loans?", default=False
    ).ask()
    if has_auto_loans is None:
        return state

    auto_loan_balance: Optional[float] = None
    auto_loan_rate: Optional[float] = None
    if has_auto_loans:
        auto_loan_balance = ask_with_retry(
            prompt_fn=lambda: questionary.text(
                "What is the total balance of your auto loans?"
            ).ask(),
            validator=validate_currency,
            default=0.0,
        )
        auto_loan_rate_pct = ask_with_retry(
            prompt_fn=lambda: questionary.text(
                "What is the average interest rate on your auto loans? (e.g., 6.0 for 6%)"
            ).ask(),
            validator=validate_percentage,
            default=0.0,
        )
        auto_loan_rate = (
            auto_loan_rate_pct / 100.0 if auto_loan_rate_pct else 0.0
        )

    # --- Credit Cards ---
    has_credit_cards = questionary.confirm(
        "Do you carry credit card balances?", default=False
    ).ask()
    if has_credit_cards is None:
        return state

    credit_card_balance: Optional[float] = None
    if has_credit_cards:
        credit_card_balance = ask_with_retry(
            prompt_fn=lambda: questionary.text(
                "What is the total credit card balance?"
            ).ask(),
            validator=validate_currency,
            default=0.0,
        )

    # --- Weighted average & other ---
    weighted_rate_pct_raw: Optional[str] = questionary.text(
        "Weighted average debt interest rate (optional, e.g., 4.5 for 4.5%, Enter to skip):"
    ).ask()
    weighted_rate: Optional[float] = None
    if weighted_rate_pct_raw is not None and weighted_rate_pct_raw.strip():
        try:
            weighted_rate = validate_percentage(weighted_rate_pct_raw) / 100.0
        except ValueError:
            weighted_rate = None

    other_debt: Optional[str] = questionary.text(
        "Any other debt to describe? (optional, press Enter to skip):"
    ).ask()
    if other_debt is not None:
        other_debt = other_debt.strip() or None

    state.data[SectionName.DEBT.value] = {
        "has_mortgage": has_mortgage,
        "mortgage_balance": mortgage_balance,
        "mortgage_payment": mortgage_payment,
        "has_student_loans": has_student_loans,
        "student_loan_balance": student_loan_balance,
        "student_loan_rate": student_loan_rate,
        "has_auto_loans": has_auto_loans,
        "auto_loan_balance": auto_loan_balance,
        "auto_loan_rate": auto_loan_rate,
        "has_credit_cards": has_credit_cards,
        "credit_card_balance": credit_card_balance,
        "weighted_rate": weighted_rate,
        "other_debt": other_debt,
    }

    state.mark_complete(SectionName.DEBT, SectionName.PREFERENCES)
    print()
    print("  Debt Profile: Complete")
    print()
    return state


# ---------------------------------------------------------------------------
# Section 5: Preferences
# ---------------------------------------------------------------------------


def run_preferences_section(state: OnboardingState) -> OnboardingState:
    """Collect investment preferences and goals.

    Stores dict matching UserPreferencesInput fields.
    Enum fields stored as raw human-readable strings.
    """
    _print_section_header(
        5,
        "Investment Preferences",
        "Let's understand your investment approach and goals.",
    )

    # Investment philosophy -- select from enum values
    philosophy_choices = [e.value for e in InvestmentPhilosophy]
    investment_philosophy = questionary.select(
        "What is your investment philosophy?",
        choices=philosophy_choices,
    ).ask()
    if investment_philosophy is None:
        return state

    # Focus areas -- checkbox
    focus_area_choices = [
        "Dividend income",
        "Growth investing",
        "Index investing",
        "Margin strategies",
        "Tax efficiency",
        "Real estate",
        "Options/hedging",
    ]
    focus_areas = questionary.checkbox(
        "Select your focus areas (space to toggle, enter to confirm):",
        choices=focus_area_choices,
    ).ask()
    if focus_areas is None:
        return state

    # Emergency fund target
    def _validate_emergency_months(value: str) -> int:
        result = validate_positive_integer(value)
        if result > 24:
            raise ValueError(
                f"Emergency fund target should be 0-24 months, got {result}."
            )
        return result

    emergency_fund_months = ask_with_retry(
        prompt_fn=lambda: questionary.text(
            "Target emergency fund in months of expenses (0-24):"
        ).ask(),
        validator=_validate_emergency_months,
        default=6,
    )
    if emergency_fund_months is None:
        return state

    state.data[SectionName.PREFERENCES.value] = {
        "investment_philosophy": investment_philosophy,
        "focus_areas": focus_areas,
        "emergency_fund_months": emergency_fund_months,
    }

    state.mark_complete(SectionName.PREFERENCES, SectionName.BROKER)
    print()
    print("  Investment Preferences: Complete")
    print()
    return state


# ---------------------------------------------------------------------------
# Section 6: Broker
# ---------------------------------------------------------------------------


def run_broker_section(state: OnboardingState) -> OnboardingState:
    """Collect broker-specific information.

    If brokerage was already provided in the investments section,
    confirms or updates it. Provides CSV export guidance.
    """
    _print_section_header(
        6,
        "Broker Selection",
        "Finance Guru needs to know which broker you use to import your portfolio data.",
    )

    # Pre-fill from investments if available
    investments_data = state.data.get(SectionName.INVESTMENTS.value, {})
    existing_brokerage = investments_data.get("brokerage")

    if existing_brokerage:
        print(f"  Previously entered brokerage: {existing_brokerage}")
        keep = questionary.confirm(
            f"Keep '{existing_brokerage}' as your primary brokerage?",
            default=True,
        ).ask()
        if keep is None:
            return state
        if keep:
            brokerage = existing_brokerage
        else:
            brokerage_raw = questionary.text(
                "Enter your primary brokerage name:"
            ).ask()
            if brokerage_raw is None:
                return state
            brokerage = brokerage_raw.strip() or existing_brokerage
    else:
        brokerage_raw = questionary.text(
            "Enter your primary brokerage name (e.g., Fidelity, Schwab, Vanguard):"
        ).ask()
        if brokerage_raw is None:
            return state
        brokerage = brokerage_raw.strip() or "Unknown"

    # CSV export guidance (informational, no prompt needed)
    print()
    print("  CSV Export Guidance:")
    print("  -------------------")
    print(f"  To sync your portfolio from {brokerage}, you will need to export")
    print("  two CSV files from your brokerage account:")
    print("    1. Positions CSV (your stock/ETF holdings)")
    print("    2. Balances CSV (cash, margin debt, account totals)")
    print("  Save these files to: notebooks/updates/")
    print()

    state.data[SectionName.BROKER.value] = {
        "brokerage": brokerage,
    }

    state.mark_complete(SectionName.BROKER, SectionName.ENV_SETUP)
    print()
    print(f"  Broker Selection: Complete ({brokerage})")
    print()
    return state


# ---------------------------------------------------------------------------
# Section 7: Environment Setup
# ---------------------------------------------------------------------------


def run_env_setup_section(state: OnboardingState) -> OnboardingState:
    """Collect user identity, language, and optional API keys.

    All API keys are optional -- yfinance works without any keys.
    """
    _print_section_header(
        7,
        "Environment Setup",
        "Configure your identity and optional API integrations.",
    )

    # User name (required)
    def _validate_name(v: str) -> str:
        stripped = v.strip() if v else ""
        if not stripped:
            raise ValueError("Name cannot be empty.")
        return stripped

    user_name_raw = ask_with_retry(
        prompt_fn=lambda: questionary.text(
            "Your name (used in reports and agent communications):"
        ).ask(),
        validator=_validate_name,
        default="User",
    )
    if user_name_raw is None:
        return state
    user_name = user_name_raw.strip() if isinstance(user_name_raw, str) else str(user_name_raw)

    # Preferred language
    language_raw = questionary.text(
        "Preferred language for communication (default: English):"
    ).ask()
    if language_raw is None:
        return state
    language = language_raw.strip() or "English"

    # API Keys -- all optional
    print()
    print("  API Keys (all optional -- yfinance works without any keys)")
    print()

    has_av = questionary.confirm(
        "Do you have an Alpha Vantage API key? (unlocks real-time market data)",
        default=False,
    ).ask()
    if has_av is None:
        return state

    av_key: Optional[str] = None
    if has_av:
        av_key_raw = questionary.text(
            "Alpha Vantage API key:"
        ).ask()
        if av_key_raw is not None:
            av_key = av_key_raw.strip() or None

    has_bd = questionary.confirm(
        "Do you have a BrightData API key? (unlocks web scraping for research)",
        default=False,
    ).ask()
    if has_bd is None:
        return state

    bd_key: Optional[str] = None
    if has_bd:
        bd_key_raw = questionary.text(
            "BrightData API key:"
        ).ask()
        if bd_key_raw is not None:
            bd_key = bd_key_raw.strip() or None

    # Google Sheets credentials
    gs_creds_raw: Optional[str] = questionary.text(
        "Path to Google Sheets credentials JSON (optional, press Enter to skip):"
    ).ask()
    gs_creds: Optional[str] = None
    if gs_creds_raw is not None:
        gs_creds = gs_creds_raw.strip() or None

    state.data[SectionName.ENV_SETUP.value] = {
        "user_name": user_name,
        "language": language,
        "has_alphavantage": has_av,
        "alphavantage_key": av_key,
        "has_brightdata": has_bd,
        "brightdata_key": bd_key,
        "google_sheets_credentials": gs_creds,
    }

    state.mark_complete(SectionName.ENV_SETUP, SectionName.SUMMARY)
    print()
    print("  Environment Setup: Complete")
    print()
    return state


# ---------------------------------------------------------------------------
# Section 8: Summary
# ---------------------------------------------------------------------------


def run_summary_section(state: OnboardingState) -> OnboardingState:
    """Display a formatted summary of all collected data and confirm.

    Does NOT prompt for new data. Asks whether to save and generate
    configuration files or restart/defer.
    """
    _print_section_header(
        8,
        "Summary & Confirmation",
        "Please review your information below.",
    )

    # --- Display collected data ---
    _display_full_summary(state)

    # --- Confirmation ---
    confirmed = questionary.confirm(
        "Save this profile and generate configuration files?",
        default=True,
    ).ask()

    if confirmed is None:
        return state

    if confirmed:
        state.data[SectionName.SUMMARY.value] = {"confirmed": True}
        state.mark_complete(SectionName.SUMMARY)
        print()
        print("  Profile confirmed! Configuration generation will proceed.")
        print()
    else:
        restart = questionary.confirm(
            "Restart from the beginning? (No = keep progress for later)",
            default=False,
        ).ask()
        if restart:
            # Clear state for a fresh start
            state.completed_sections.clear()
            state.data.clear()
            state.current_section = SectionName.LIQUID_ASSETS
            print()
            print("  Progress cleared. Run the wizard again to restart.")
            print()
        else:
            print()
            print("  Progress saved. You can resume later.")
            print()
        state.data[SectionName.SUMMARY.value] = {"confirmed": False}

    return state


# ---------------------------------------------------------------------------
# Summary display helpers
# ---------------------------------------------------------------------------


def _display_full_summary(state: OnboardingState) -> None:
    """Print a nicely formatted summary of all collected section data."""
    border = "\u2550" * 56
    print(f"  {border}")
    print("                  Your Finance Guru Profile")
    print(f"  {border}")
    print()

    # Liquid Assets
    la = state.data.get(SectionName.LIQUID_ASSETS.value)
    if la:
        print("  Liquid Assets")
        print(f"    Total:         {_format_currency(la.get('total', 0))}")
        print(f"    Accounts:      {la.get('accounts_count', 'N/A')}")
        print(f"    Average Yield: {_format_percentage_display(la.get('average_yield', 0))}")
        if la.get("structure"):
            print(f"    Structure:     {la['structure']}")
        print()

    # Investments
    inv = state.data.get(SectionName.INVESTMENTS.value)
    if inv:
        print("  Investment Portfolio")
        print(f"    Total Value:   {_format_currency(inv.get('total_value', 0))}")
        if inv.get("brokerage"):
            print(f"    Brokerage:     {inv['brokerage']}")
        if inv.get("has_retirement"):
            print(f"    Retirement:    {_format_currency(inv.get('retirement_value', 0))}")
        print(f"    Allocation:    {inv.get('allocation_strategy', 'N/A')}")
        print(f"    Risk:          {inv.get('risk_tolerance', 'N/A')}")
        print()

    # Cash Flow
    cf = state.data.get(SectionName.CASH_FLOW.value)
    if cf:
        print("  Cash Flow")
        print(f"    Monthly Income:      {_format_currency(cf.get('monthly_income', 0))}")
        print(f"    Fixed Expenses:      {_format_currency(cf.get('fixed_expenses', 0))}")
        print(f"    Variable Expenses:   {_format_currency(cf.get('variable_expenses', 0))}")
        print(f"    Current Savings:     {_format_currency(cf.get('current_savings', 0))}")
        print(f"    Investment Capacity: {_format_currency(cf.get('investment_capacity', 0))}")
        print()

    # Debt
    debt = state.data.get(SectionName.DEBT.value)
    if debt:
        print("  Debt Profile")
        if debt.get("has_mortgage"):
            print(f"    Mortgage Balance:  {_format_currency(debt.get('mortgage_balance', 0))}")
            print(f"    Mortgage Payment:  {_format_currency(debt.get('mortgage_payment', 0))}")
        else:
            print("    Mortgage:          None")
        if debt.get("has_student_loans"):
            print(f"    Student Loans:     {_format_currency(debt.get('student_loan_balance', 0))}")
            print(f"    Student Loan Rate: {_format_percentage_display(debt.get('student_loan_rate', 0))}")
        if debt.get("has_auto_loans"):
            print(f"    Auto Loans:        {_format_currency(debt.get('auto_loan_balance', 0))}")
            print(f"    Auto Loan Rate:    {_format_percentage_display(debt.get('auto_loan_rate', 0))}")
        if debt.get("has_credit_cards"):
            print(f"    Credit Cards:      {_format_currency(debt.get('credit_card_balance', 0))}")
        if debt.get("weighted_rate") is not None:
            print(f"    Weighted Rate:     {_format_percentage_display(debt['weighted_rate'])}")
        if debt.get("other_debt"):
            print(f"    Other:             {debt['other_debt']}")
        print()

    # Preferences
    prefs = state.data.get(SectionName.PREFERENCES.value)
    if prefs:
        print("  Investment Preferences")
        print(f"    Philosophy:      {prefs.get('investment_philosophy', 'N/A')}")
        focus = prefs.get("focus_areas", [])
        if focus:
            print(f"    Focus Areas:     {', '.join(focus)}")
        else:
            print("    Focus Areas:     None specified")
        print(f"    Emergency Fund:  {prefs.get('emergency_fund_months', 'N/A')} months")
        print()

    # Broker
    broker = state.data.get(SectionName.BROKER.value)
    if broker:
        print("  Broker")
        print(f"    Brokerage:       {broker.get('brokerage', 'N/A')}")
        print()

    # Env Setup
    env = state.data.get(SectionName.ENV_SETUP.value)
    if env:
        print("  Environment")
        print(f"    User Name:       {env.get('user_name', 'N/A')}")
        print(f"    Language:        {env.get('language', 'English')}")
        print(f"    Alpha Vantage:   {'Configured' if env.get('alphavantage_key') else 'Not set'}")
        print(f"    BrightData:      {'Configured' if env.get('brightdata_key') else 'Not set'}")
        print(f"    Google Sheets:   {'Configured' if env.get('google_sheets_credentials') else 'Not set'}")
        print()

    print(f"  {border}")
    print()
