"""Portfolio Optimization Pydantic Models for Finance Guru™.

WHAT: Data models for portfolio optimization and asset allocation
WHY: Type-safe portfolio construction and optimization for $500k capital deployment
ARCHITECTURE: Layer 1 of 3-layer type-safe architecture

Used by: Strategy Advisor (allocation decisions), Quant Analyst (optimization), Compliance Officer (limits)

Author: Finance Guru™ Development Team
Created: 2025-10-13
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class PortfolioDataInput(BaseModel):
    """Historical price data for portfolio optimization.

    WHAT: Multi-asset price history for optimization calculations
    WHY: Enables calculation of expected returns, volatilities, and correlations
    VALIDATES:
        - At least 2 assets (need multiple assets for portfolio optimization)
        - Minimum 252 days (1 year) for reliable estimates
        - All price series have same length (synchronized data)
        - Prices are positive

    EDUCATIONAL NOTE:
    Portfolio optimization requires historical data to estimate:
    1. Expected returns (average future returns)
    2. Volatilities (risk of each asset)
    3. Correlations (how assets move together)

    The quality of optimization depends on data quality and length.
    Generally, 1-3 years of daily data is ideal for retail portfolios.
    """

    tickers: list[str] = Field(
        ...,
        min_length=2,
        description="Asset ticker symbols (minimum 2 for portfolio optimization)",
    )

    dates: list[date] = Field(
        ...,
        min_length=30,
        description="Trading dates (minimum 30 days, 252 recommended for reliable estimates)",
    )

    prices: dict[str, list[float]] = Field(
        ..., description="Price history for each ticker {ticker: [prices]}"
    )

    expected_returns: dict[str, float] | None = Field(
        default=None,
        description="Optional expected annual returns per asset (if None, estimated from history)",
    )

    @field_validator("tickers")
    @classmethod
    def tickers_must_be_uppercase(cls, v: list[str]) -> list[str]:
        """Ensure ticker symbols are uppercase and valid format.

        EDUCATIONAL NOTE:
        Standard convention is uppercase ticker symbols (TSLA not tsla).
        This prevents matching errors when comparing tickers.
        """
        for ticker in v:
            if ticker != ticker.upper():
                raise ValueError(f"Ticker '{ticker}' must be uppercase (e.g., 'TSLA')")
            if not ticker.isalpha():
                raise ValueError(f"Ticker '{ticker}' must contain only letters")
        return v

    @field_validator("prices")
    @classmethod
    def validate_prices_structure(
        cls, v: dict[str, list[float]], info
    ) -> dict[str, list[float]]:
        """Validate that all price series have same length and positive values.

        EDUCATIONAL NOTE:
        Portfolio optimization requires synchronized data. If TSLA has 300 days
        but PLTR has 250 days, we can't accurately calculate their correlation.
        All assets must have the exact same observation period.
        """
        if not v:
            raise ValueError("Prices dictionary cannot be empty")

        # Check all prices are positive
        for ticker, price_list in v.items():
            if any(p <= 0 for p in price_list):
                raise ValueError(f"All prices for {ticker} must be positive")

        # Check all series have same length
        lengths = [len(price_list) for price_list in v.values()]
        if len(set(lengths)) > 1:
            raise ValueError(
                f"All price series must have same length. Found: {dict(zip(v.keys(), lengths, strict=False))}"
            )

        # Check minimum length (30 days minimum, 252 recommended)
        if lengths[0] < 30:
            raise ValueError(
                f"Price series must have at least 30 days. Found: {lengths[0]} days. "
                f"Note: 252 days (1 year) recommended for reliable optimization."
            )

        # Check tickers match
        tickers_in_data = info.data.get("tickers", [])
        if tickers_in_data:
            for ticker in tickers_in_data:
                if ticker not in v:
                    raise ValueError(
                        f"Ticker {ticker} listed but no price data provided"
                    )

        return v

    @field_validator("expected_returns")
    @classmethod
    def validate_expected_returns(
        cls, v: dict[str, float] | None, info
    ) -> dict[str, float] | None:
        """Validate expected returns if provided.

        EDUCATIONAL NOTE:
        Expected returns are ANNUAL returns (e.g., 0.15 = 15% per year).
        These are forecasts, not historical averages. Be conservative!
        Historical returns are often poor predictors of future returns.
        """
        if v is None:
            return v

        # Check all returns are reasonable
        for ticker, ret in v.items():
            if ret < -0.90:
                raise ValueError(
                    f"Expected return for {ticker} is {ret:.1%}. "
                    "Returns below -90% are unrealistic (total loss)."
                )
            if ret > 2.0:
                raise ValueError(
                    f"Expected return for {ticker} is {ret:.1%}. "
                    "Returns above 200% per year are extremely aggressive. Verify this forecast."
                )

        # Check tickers match
        tickers_in_data = info.data.get("tickers", [])
        if tickers_in_data:
            for ticker in tickers_in_data:
                if ticker not in v:
                    raise ValueError(
                        f"Expected return provided but missing ticker {ticker}"
                    )

        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "tickers": ["TSLA", "SPY", "BND"],
                    "dates": ["2024-10-13"] * 252,  # Simplified for example
                    "prices": {
                        "TSLA": [250.0] * 252,
                        "SPY": [450.0] * 252,
                        "BND": [72.0] * 252,
                    },
                    "expected_returns": {
                        "TSLA": 0.20,  # 20% expected annual return
                        "SPY": 0.10,  # 10% expected annual return
                        "BND": 0.04,  # 4% expected annual return
                    },
                }
            ]
        }
    }


class OptimizationConfig(BaseModel):
    """Configuration for portfolio optimization.

    WHAT: Settings that control the optimization process
    WHY: Different optimization methods suit different investment goals
    USE CASES:
        - Strategy Advisor: Choose method based on return goals
        - Compliance Officer: Set position limits
        - Quant Analyst: Configure optimization constraints

    EDUCATIONAL NOTE:
    Five optimization methods available:

    1. **Mean-Variance** (Markowitz): Balances return vs risk
       - Best for: Investors with specific return targets
       - Requires: Return forecasts (uncertain!)

    2. **Risk Parity**: Each asset contributes equally to portfolio risk
       - Best for: "All-weather" portfolios, no return forecasts needed
       - Used by: Bridgewater Associates (Ray Dalio)

    3. **Minimum Variance**: Lowest risk allocation
       - Best for: Conservative investors, capital preservation
       - Ignores returns, focuses purely on risk reduction

    4. **Maximum Sharpe**: Best risk-adjusted return
       - Best for: Aggressive growth with risk awareness
       - Most popular among quantitative investors

    5. **Black-Litterman**: Market equilibrium + investor views
       - Best for: Incorporating specific investment opinions
       - Handles uncertainty better than pure Markowitz
    """

    method: Literal[
        "mean_variance", "risk_parity", "min_variance", "max_sharpe", "black_litterman"
    ] = Field(default="max_sharpe", description="Optimization method to use")

    risk_free_rate: float = Field(
        default=0.045,
        ge=0.0,
        le=0.20,
        description="Annual risk-free rate for Sharpe calculation (0.045 = 4.5%)",
    )

    target_return: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Target annual return for mean-variance optimization (None = unconstrained)",
    )

    allow_short: bool = Field(
        default=False,
        description="Allow short positions (False = long-only, appropriate for most retail investors)",
    )

    position_limits: tuple[float, float] = Field(
        default=(0.0, 1.0),
        description="Min and max position size per asset (0.0, 1.0) = 0-100%",
    )

    views: dict[str, float] | None = Field(
        default=None,
        description="Investor views on expected returns for Black-Litterman (ticker: annual_return)",
    )

    @field_validator("position_limits")
    @classmethod
    def validate_position_limits(cls, v: tuple[float, float]) -> tuple[float, float]:
        """Validate position limit constraints.

        EDUCATIONAL NOTE:
        Position limits prevent over-concentration. For a $500k portfolio:
        - (0.0, 0.30) = No position > 30% = max $150k per stock
        - (0.0, 0.25) = No position > 25% = max $125k per stock
        - (0.10, 0.40) = Each position 10-40% = $50k-$200k per stock

        Tighter limits = more diversification but potentially lower returns.
        """
        min_pos, max_pos = v

        if min_pos < 0.0 and not cls.allow_short:
            raise ValueError(
                f"Minimum position {min_pos:.1%} is negative but short selling is disabled. "
                "Set allow_short=True for short positions."
            )

        if min_pos >= max_pos:
            raise ValueError(
                f"Minimum position ({min_pos:.1%}) must be less than maximum ({max_pos:.1%})"
            )

        if max_pos > 1.0:
            raise ValueError(
                f"Maximum position {max_pos:.1%} exceeds 100%. "
                "Cannot allocate more than 100% to a single asset."
            )

        if min_pos < -1.0:
            raise ValueError(
                f"Minimum position {min_pos:.1%} below -100%. "
                "Cannot short more than 100% of portfolio value."
            )

        return v

    @model_validator(mode="after")
    def validate_method_specific_requirements(self) -> OptimizationConfig:
        """Validate that required parameters are present for each method.

        EDUCATIONAL NOTE:
        Different optimization methods need different inputs:
        - Black-Litterman requires views (your opinions on returns)
        - Mean-variance can optionally use target_return
        - Other methods ignore these parameters
        """
        if self.method == "black_litterman" and self.views is None:
            raise ValueError(
                "Black-Litterman optimization requires 'views' parameter. "
                "Specify expected returns for assets: views={'TSLA': 0.15, 'PLTR': 0.20}"
            )

        return self

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "method": "max_sharpe",
                    "risk_free_rate": 0.045,
                    "allow_short": False,
                    "position_limits": [0.0, 0.30],
                },
                {
                    "method": "mean_variance",
                    "risk_free_rate": 0.045,
                    "target_return": 0.12,
                    "allow_short": False,
                    "position_limits": [0.0, 1.0],
                },
                {
                    "method": "black_litterman",
                    "risk_free_rate": 0.045,
                    "allow_short": False,
                    "position_limits": [0.0, 1.0],
                    "views": {"TSLA": 0.15, "PLTR": 0.20},
                },
            ]
        }
    }


class OptimizationOutput(BaseModel):
    """Results from portfolio optimization.

    WHAT: Optimal portfolio weights and expected metrics
    WHY: Provides actionable allocation for capital deployment
    USE CASES:
        - Strategy Advisor: Generate deployment plan for $500k
        - Compliance Officer: Verify position limits compliance
        - Quant Analyst: Compare different optimization methods

    EDUCATIONAL NOTE:
    The optimal weights tell you how to allocate your capital.
    For a $500k portfolio with weights:
        {"TSLA": 0.25, "PLTR": 0.30, "NVDA": 0.20, "SPY": 0.25}

    Your allocation would be:
        - TSLA: $125,000 (25%)
        - PLTR: $150,000 (30%)
        - NVDA: $100,000 (20%)
        - SPY:  $125,000 (25%)
    """

    tickers: list[str] = Field(..., description="Asset ticker symbols")

    method: str = Field(..., description="Optimization method used")

    optimal_weights: dict[str, float] = Field(
        ..., description="Optimal allocation per asset (must sum to 1.0)"
    )

    expected_return: float = Field(..., description="Expected annual portfolio return")

    expected_volatility: float = Field(
        ...,
        ge=0.0,
        description="Expected annual portfolio volatility (standard deviation)",
    )

    sharpe_ratio: float = Field(
        ..., description="Expected Sharpe ratio (return per unit of risk)"
    )

    diversification_ratio: float = Field(
        ...,
        ge=1.0,
        description="Diversification ratio (portfolio_risk / weighted_avg_risk)",
    )

    @field_validator("optimal_weights")
    @classmethod
    def weights_must_sum_to_one(cls, v: dict[str, float]) -> dict[str, float]:
        """Ensure weights sum to 1.0 (fully invested).

        EDUCATIONAL NOTE:
        Weights must sum to 1.0 (100%) for a fully invested portfolio.
        We allow a small tolerance (0.001 = 0.1%) for numerical precision.
        """
        weight_sum = sum(v.values())
        if abs(weight_sum - 1.0) > 0.001:
            raise ValueError(
                f"Weights must sum to 1.0 (fully invested). Found sum = {weight_sum:.6f}"
            )
        return v

    @field_validator("diversification_ratio")
    @classmethod
    def diversification_ratio_must_be_valid(cls, v: float) -> float:
        """Validate diversification ratio is >= 1.0.

        EDUCATIONAL NOTE:
        Diversification ratio measures the benefit of diversification.
        - 1.0 = No diversification benefit (single asset or perfectly correlated)
        - 1.5 = Portfolio risk is 1.5x lower than weighted average
        - 2.0 = Excellent diversification (risk is 2x lower)

        It can never be < 1.0 (that would mean diversification increases risk!).
        """
        if v < 1.0:
            raise ValueError(
                f"Diversification ratio {v:.2f} is less than 1.0. "
                "This indicates a calculation error (ratio must be >= 1.0)."
            )
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "tickers": ["TSLA", "PLTR", "NVDA", "SPY"],
                    "method": "max_sharpe",
                    "optimal_weights": {
                        "TSLA": 0.25,
                        "PLTR": 0.30,
                        "NVDA": 0.20,
                        "SPY": 0.25,
                    },
                    "expected_return": 0.18,
                    "expected_volatility": 0.24,
                    "sharpe_ratio": 1.52,
                    "diversification_ratio": 1.45,
                }
            ]
        }
    }


class EfficientFrontierOutput(BaseModel):
    """Efficient frontier data for visualization.

    WHAT: Collection of optimal portfolios across risk levels
    WHY: Shows risk-return tradeoff, helps choose risk tolerance
    USE CASES:
        - Strategy Advisor: Visualize risk-return options
        - Quant Analyst: Identify optimal portfolio on frontier
        - Client Education: Show diversification benefits graphically

    EDUCATIONAL NOTE:
    The efficient frontier is a curve showing the best possible portfolios.
    Every point on the curve represents a portfolio with the highest return
    for its risk level (or lowest risk for its return level).

    Portfolios BELOW the curve are sub-optimal (same risk, less return).
    Portfolios ABOVE the curve are impossible (too good to be true!).

    The optimal portfolio for most investors is where the line from the
    risk-free rate is tangent to the frontier (Maximum Sharpe Ratio point).
    """

    returns: list[float] = Field(
        ...,
        min_length=10,
        description="Expected annual returns for frontier portfolios",
    )

    volatilities: list[float] = Field(
        ...,
        min_length=10,
        description="Expected annual volatilities for frontier portfolios",
    )

    sharpe_ratios: list[float] = Field(
        ..., min_length=10, description="Sharpe ratios for frontier portfolios"
    )

    optimal_portfolio_index: int = Field(
        ..., ge=0, description="Index of maximum Sharpe ratio portfolio in the frontier"
    )

    @model_validator(mode="after")
    def validate_frontier_consistency(self) -> EfficientFrontierOutput:
        """Ensure all frontier arrays have same length.

        EDUCATIONAL NOTE:
        Each point on the frontier has (return, volatility, sharpe_ratio).
        These arrays must have the same length so we can plot them together.
        """
        n_returns = len(self.returns)
        n_vols = len(self.volatilities)
        n_sharpes = len(self.sharpe_ratios)

        if not (n_returns == n_vols == n_sharpes):
            raise ValueError(
                f"Frontier arrays must have same length. "
                f"Found: returns={n_returns}, volatilities={n_vols}, sharpe_ratios={n_sharpes}"
            )

        if self.optimal_portfolio_index >= n_returns:
            raise ValueError(
                f"Optimal portfolio index {self.optimal_portfolio_index} "
                f"exceeds frontier length {n_returns}"
            )

        return self

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "returns": [
                        0.08,
                        0.10,
                        0.12,
                        0.14,
                        0.16,
                        0.18,
                        0.20,
                        0.22,
                        0.24,
                        0.26,
                    ],
                    "volatilities": [
                        0.12,
                        0.14,
                        0.16,
                        0.18,
                        0.20,
                        0.22,
                        0.24,
                        0.26,
                        0.28,
                        0.30,
                    ],
                    "sharpe_ratios": [
                        0.29,
                        0.39,
                        0.47,
                        0.53,
                        0.58,
                        0.61,
                        0.63,
                        0.63,
                        0.62,
                        0.60,
                    ],
                    "optimal_portfolio_index": 6,
                }
            ]
        }
    }


# Type exports for convenience
__all__ = [
    "PortfolioDataInput",
    "OptimizationConfig",
    "OptimizationOutput",
    "EfficientFrontierOutput",
]
