"""Factor Analysis Pydantic Models for Finance Guru™.

This module defines type-safe data structures for factor analysis.
All models use Pydantic for automatic validation and type checking.

ARCHITECTURE NOTE:
These models represent Layer 1 of our 3-layer architecture:
    Layer 1: Pydantic Models (THIS FILE) - Data validation
    Layer 2: Calculator Classes - Business logic
    Layer 3: CLI Interface - Agent integration

EDUCATIONAL CONTEXT:
Factor analysis decomposes returns into systematic factors:
- MARKET: Overall market movements (beta to S&P 500)
- SIZE: Small-cap vs large-cap performance (SMB = Small Minus Big)
- VALUE: Value vs growth performance (HML = High Minus Low book-to-market)
- MOMENTUM: Recent winners vs losers (WML/MOM)

WHY IT MATTERS:
- Understand what drives your returns (skill vs exposure)
- Compare performance against appropriate benchmarks
- Identify hidden risks in your portfolio
- Attribution: "My 15% return came from: 8% market + 3% size + 2% value + 2% alpha"

Author: Finance Guru™ Development Team
Created: 2025-10-13
"""

from datetime import date

from pydantic import BaseModel, Field, field_validator, model_validator


class FactorDataInput(BaseModel):
    """Input data for factor analysis.

    WHAT: Time-series of asset returns and factor returns
    WHY: Need aligned return data for regression analysis
    VALIDATES:
        - All series have same length (temporal alignment)
        - Returns are reasonable (-100% to +1000%)
        - Minimum 30 observations for statistical significance

    USAGE EXAMPLE:
        factor_data = FactorDataInput(
            ticker="TSLA",
            asset_returns=[0.02, -0.01, 0.03, ...],  # Daily returns
            market_returns=[0.01, -0.005, 0.015, ...],  # SPY returns
            smb_returns=[0.001, -0.002, 0.001, ...],  # Size factor
            hml_returns=[-0.001, 0.002, -0.001, ...],  # Value factor
            mom_returns=[0.002, 0.001, 0.003, ...],  # Momentum factor (optional)
            risk_free_rate=0.045  # 4.5% annual
        )
    """

    ticker: str = Field(
        ...,
        description="Asset ticker symbol",
        min_length=1,
        max_length=10,
    )

    asset_returns: list[float] = Field(
        ...,
        description="Asset daily returns (minimum 30 observations)",
        min_length=30,
    )

    market_returns: list[float] = Field(
        ...,
        description="Market (SPY/SPX) daily returns",
        min_length=30,
    )

    smb_returns: list[float] | None = Field(
        default=None,
        description="Size factor (Small Minus Big) returns (optional for 3-factor)",
        min_length=30,
    )

    hml_returns: list[float] | None = Field(
        default=None,
        description="Value factor (High Minus Low) returns (optional for 3-factor)",
        min_length=30,
    )

    mom_returns: list[float] | None = Field(
        default=None,
        description="Momentum factor returns (optional for 4-factor)",
        min_length=30,
    )

    risk_free_rate: float = Field(
        default=0.045,
        ge=0.0,
        le=0.20,
        description="Annual risk-free rate (default: 4.5%)",
    )

    @field_validator(
        "asset_returns", "market_returns", "smb_returns", "hml_returns", "mom_returns"
    )
    @classmethod
    def validate_returns_reasonable(cls, v: list[float] | None) -> list[float] | None:
        """Ensure returns are within reasonable bounds.

        EDUCATIONAL NOTE:
        Daily returns outside -50% to +100% are extremely rare and
        usually indicate data errors (unless there's a stock split).
        """
        if v is None:
            return v

        for ret in v:
            if ret < -0.50 or ret > 1.0:
                raise ValueError(
                    f"Return {ret:.2%} outside reasonable bounds (-50% to +100%). "
                    "Check for data errors or unadjusted stock splits."
                )
        return v

    @model_validator(mode="after")
    def validate_alignment(self) -> "FactorDataInput":
        """Ensure all return series have matching lengths."""
        asset_len = len(self.asset_returns)

        if len(self.market_returns) != asset_len:
            raise ValueError(
                f"Market returns length ({len(self.market_returns)}) "
                f"doesn't match asset returns ({asset_len})"
            )

        if self.smb_returns and len(self.smb_returns) != asset_len:
            raise ValueError("SMB returns length doesn't match asset returns")

        if self.hml_returns and len(self.hml_returns) != asset_len:
            raise ValueError("HML returns length doesn't match asset returns")

        if self.mom_returns and len(self.mom_returns) != asset_len:
            raise ValueError("MOM returns length doesn't match asset returns")

        return self


class FactorExposureOutput(BaseModel):
    """Factor exposure (beta) estimates from regression.

    WHAT: Sensitivity of asset to each risk factor
    WHY: Shows which factors drive your returns
    USE CASES:
        - Portfolio construction: Ensure desired factor exposures
        - Risk management: Identify factor concentration risks
        - Performance attribution: Decompose returns by factor

    EDUCATIONAL NOTE:
    Think of betas as "sensitivity knobs":
    - market_beta = 1.5 means "1.5x as sensitive as market"
    - size_beta = 0.3 means "slight tilt toward small caps"
    - value_beta = -0.2 means "slight tilt toward growth"
    """

    ticker: str = Field(..., description="Asset ticker symbol")
    analysis_date: date = Field(..., description="Date of analysis")

    # Factor Betas (Exposures)
    market_beta: float = Field(
        ..., description="Market factor beta (typically 0.5 to 2.0 for stocks)"
    )

    size_beta: float | None = Field(
        default=None, description="SMB factor beta (positive = small-cap tilt)"
    )

    value_beta: float | None = Field(
        default=None,
        description="HML factor beta (positive = value tilt, negative = growth tilt)",
    )

    momentum_beta: float | None = Field(
        default=None, description="Momentum factor beta (positive = momentum tilt)"
    )

    # Alpha (Excess Return)
    alpha: float = Field(
        ..., description="Alpha (excess return not explained by factors, annualized)"
    )

    # Model Quality
    r_squared: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="R-squared (proportion of variance explained by model)",
    )

    # Standard Errors (for statistical significance)
    alpha_tstat: float = Field(
        ..., description="T-statistic for alpha (> 2.0 suggests significance)"
    )

    market_beta_tstat: float = Field(..., description="T-statistic for market beta")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "ticker": "TSLA",
                    "analysis_date": "2025-10-13",
                    "market_beta": 1.85,
                    "size_beta": 0.15,
                    "value_beta": -0.32,
                    "momentum_beta": 0.45,
                    "alpha": 0.12,
                    "r_squared": 0.68,
                    "alpha_tstat": 2.45,
                    "market_beta_tstat": 18.5,
                }
            ]
        }
    }


class AttributionOutput(BaseModel):
    """Return attribution by factor.

    WHAT: Decomposition of total return into factor contributions
    WHY: Answers "Where did my returns come from?"
    USE CASES:
        - Performance reporting: Show clients what drove returns
        - Strategy evaluation: Verify strategy is working as intended
        - Risk assessment: Identify dominant return sources

    EDUCATIONAL NOTE:
    Attribution formula:
        Total Return = Σ(factor_beta * factor_return) + alpha + residual

    Example interpretation:
        15% total return =
            8% from market exposure (beta * market return)
          + 2% from size exposure (size beta * SMB return)
          + 1% from value exposure (value beta * HML return)
          + 3% from alpha (manager skill)
          + 1% residual (unexplained)
    """

    ticker: str = Field(..., description="Asset ticker symbol")
    analysis_date: date = Field(..., description="Date of analysis")

    # Total Performance
    total_return: float = Field(..., description="Total annualized return")

    # Factor Contributions (additive)
    market_attribution: float = Field(
        ..., description="Return attributed to market factor"
    )

    size_attribution: float | None = Field(
        default=None, description="Return attributed to size factor"
    )

    value_attribution: float | None = Field(
        default=None, description="Return attributed to value factor"
    )

    momentum_attribution: float | None = Field(
        default=None, description="Return attributed to momentum factor"
    )

    alpha_attribution: float = Field(
        ..., description="Return attributed to alpha (skill/luck)"
    )

    residual: float = Field(..., description="Unexplained return (model error)")

    # Factor Importance (as % of total)
    market_importance: float = Field(
        ..., ge=0.0, le=1.0, description="Market contribution as % of total return"
    )

    alpha_importance: float = Field(
        ..., ge=0.0, le=1.0, description="Alpha contribution as % of total return"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "ticker": "TSLA",
                    "analysis_date": "2025-10-13",
                    "total_return": 0.15,
                    "market_attribution": 0.08,
                    "size_attribution": 0.02,
                    "value_attribution": 0.01,
                    "momentum_attribution": 0.02,
                    "alpha_attribution": 0.03,
                    "residual": -0.01,
                    "market_importance": 0.53,
                    "alpha_importance": 0.20,
                }
            ]
        }
    }


class FactorAnalysisOutput(BaseModel):
    """Complete factor analysis results.

    WHAT: Combined exposure and attribution analysis
    WHY: Provides complete picture of factor dynamics
    """

    exposure: FactorExposureOutput = Field(..., description="Factor exposures (betas)")

    attribution: AttributionOutput = Field(
        ..., description="Return attribution by factor"
    )

    summary: str = Field(..., description="Human-readable summary of findings")

    recommendations: list[str] = Field(
        default_factory=list,
        description="Actionable recommendations based on factor analysis",
    )


# Type exports
__all__ = [
    "FactorDataInput",
    "FactorExposureOutput",
    "AttributionOutput",
    "FactorAnalysisOutput",
]
