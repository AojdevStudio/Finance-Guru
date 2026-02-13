"""YAML Generation Input Models for Finance Guru™.

Pydantic models for type-safe YAML configuration generation.
These models validate user onboarding data before generating config files.

ARCHITECTURE NOTE:
This is Layer 1 of our 3-layer architecture:
    Layer 1: Pydantic Models (THIS FILE) - Data validation
    Layer 2: Calculator Classes - Business logic (yaml_generator.py)
    Layer 3: CLI Interface - Agent integration (yaml_generator_cli.py)

Author: Finance Guru™ Development Team
Created: 2026-01-16
"""

from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator


class RiskTolerance(StrEnum):
    """User risk tolerance levels."""

    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class AllocationStrategy(StrEnum):
    """Portfolio allocation strategies."""

    PASSIVE = "passive"
    ACTIVE = "active"
    HYBRID = "hybrid"
    AGGRESSIVE_GROWTH = "aggressive_growth"
    INCOME_FOCUSED = "income_focused"


class InvestmentPhilosophy(StrEnum):
    """Investment philosophy options."""

    GROWTH = "growth"
    VALUE = "value"
    DIVIDEND = "dividend"
    AGGRESSIVE_GROWTH_PLUS_INCOME = "aggressive_growth_plus_income"
    BALANCED = "balanced"


class UserIdentityInput(BaseModel):
    """User identity and basic information."""

    user_name: str = Field(..., min_length=1, max_length=100, description="User's name")
    language: str = Field(
        default="English", description="Preferred communication language"
    )

    @field_validator("user_name")
    @classmethod
    def validate_user_name(cls, v: str) -> str:
        """Ensure user name is not empty after stripping whitespace."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("User name cannot be empty or whitespace")
        return stripped


class LiquidAssetsInput(BaseModel):
    """Liquid assets (savings, checking accounts)."""

    total: float = Field(..., ge=0, description="Total liquid assets")
    accounts_count: int = Field(..., ge=0, description="Number of accounts")
    average_yield: float = Field(
        ..., ge=0, le=1, description="Average yield (as decimal, e.g., 0.04)"
    )
    structure: str | None = Field(None, description="Description of account structure")


class InvestmentPortfolioInput(BaseModel):
    """Investment portfolio details."""

    total_value: float = Field(..., ge=0, description="Total portfolio value")
    brokerage: str | None = Field(None, description="Primary brokerage name")
    has_retirement: bool = Field(default=False, description="Has retirement accounts")
    retirement_value: float | None = Field(
        None, ge=0, description="Total retirement account value"
    )
    allocation_strategy: AllocationStrategy = Field(
        ..., description="Portfolio allocation strategy"
    )
    risk_tolerance: RiskTolerance = Field(..., description="Risk tolerance level")
    google_sheets_id: str | None = Field(
        None, description="Google Sheets portfolio tracker ID"
    )
    account_number: str | None = Field(
        None, description="Primary account number (last 4 digits or masked)"
    )


class CashFlowInput(BaseModel):
    """Monthly cash flow information."""

    monthly_income: float = Field(..., gt=0, description="Monthly after-tax income")
    fixed_expenses: float = Field(..., ge=0, description="Fixed monthly expenses")
    variable_expenses: float = Field(..., ge=0, description="Variable monthly expenses")
    current_savings: float = Field(..., ge=0, description="Current monthly savings")
    investment_capacity: float = Field(
        ..., ge=0, description="Monthly investment capacity"
    )

    @field_validator("investment_capacity")
    @classmethod
    def validate_investment_capacity(cls, v: float, info) -> float:
        """Ensure investment capacity doesn't exceed income."""
        if "monthly_income" in info.data:
            monthly_income = info.data["monthly_income"]
            if v > monthly_income:
                raise ValueError(
                    f"Investment capacity (${v:,.2f}) cannot exceed monthly income (${monthly_income:,.2f})"
                )
        return v


class DebtProfileInput(BaseModel):
    """Debt obligations and rates."""

    has_mortgage: bool = Field(default=False, description="Has mortgage")
    mortgage_balance: float | None = Field(None, ge=0, description="Mortgage balance")
    mortgage_payment: float | None = Field(
        None, ge=0, description="Monthly mortgage payment"
    )
    has_student_loans: bool = Field(default=False, description="Has student loans")
    student_loan_balance: float | None = Field(
        None, ge=0, description="Student loan balance"
    )
    student_loan_rate: float | None = Field(
        None, ge=0, le=1, description="Student loan interest rate (decimal)"
    )
    has_auto_loans: bool = Field(default=False, description="Has auto loans")
    auto_loan_balance: float | None = Field(None, ge=0, description="Auto loan balance")
    auto_loan_rate: float | None = Field(
        None, ge=0, le=1, description="Auto loan interest rate (decimal)"
    )
    has_credit_cards: bool = Field(default=False, description="Has credit card debt")
    credit_card_balance: float | None = Field(
        None, ge=0, description="Credit card balance"
    )
    weighted_rate: float | None = Field(
        None, ge=0, le=1, description="Weighted average debt interest rate"
    )
    other_debt: str | None = Field(None, description="Other debt description")


class UserPreferencesInput(BaseModel):
    """User investment preferences and goals."""

    investment_philosophy: InvestmentPhilosophy = Field(
        ..., description="Investment philosophy"
    )
    focus_areas: list[str] = Field(
        default_factory=list, description="Investment focus areas"
    )
    emergency_fund_months: int = Field(
        ..., ge=0, le=24, description="Target emergency fund (months of expenses)"
    )


class MCPConfigInput(BaseModel):
    """MCP server configuration."""

    has_alphavantage: bool = Field(
        default=False, description="Has Alpha Vantage API key"
    )
    alphavantage_key: str | None = Field(None, description="Alpha Vantage API key")
    has_brightdata: bool = Field(default=False, description="Has BrightData API key")
    brightdata_key: str | None = Field(None, description="BrightData API key")


class UserDataInput(BaseModel):
    """Complete user data for YAML generation."""

    identity: UserIdentityInput
    liquid_assets: LiquidAssetsInput
    portfolio: InvestmentPortfolioInput
    cash_flow: CashFlowInput
    debt: DebtProfileInput
    preferences: UserPreferencesInput
    mcp: MCPConfigInput = Field(default_factory=MCPConfigInput)

    # Environment
    project_root: str | None = Field(None, description="Project root directory")
    google_sheets_credentials: str | None = Field(
        None, description="Path to Google Sheets credentials JSON"
    )


class YAMLGenerationOutput(BaseModel):
    """Output from YAML generation."""

    user_profile_yaml: str = Field(
        ..., description="Generated user-profile.yaml content"
    )
    config_yaml: str = Field(..., description="Generated config.yaml content")
    system_context_md: str = Field(
        ..., description="Generated system-context.md content"
    )
    claude_md: str = Field(..., description="Generated CLAUDE.md content")
    env_file: str = Field(..., description="Generated .env file content")
    mcp_json: str = Field(..., description="Generated MCP configuration JSON content")
    generation_date: date = Field(..., description="Date of generation")
    user_name: str = Field(..., description="User name from input")
