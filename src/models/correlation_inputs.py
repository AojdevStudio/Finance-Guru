"""
Pydantic models for correlation and covariance analysis.

WHAT: Data models for portfolio correlation and covariance calculations
WHY: Type-safe diversification analysis for Finance Guru agents
ARCHITECTURE: Layer 1 of 3-layer type-safe architecture

Used by: Strategy Advisor, Quant Analyst, Risk Assessment workflows
"""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class PortfolioPriceData(BaseModel):
    """
    WHAT: Historical price data for multiple assets
    WHY: Enables correlation analysis across portfolio holdings
    VALIDATES:
      - All tickers have same number of data points
      - Dates are identical across all assets
      - Prices are positive

    EDUCATIONAL NOTE:
    For correlation analysis, we need synchronized price data.
    Example: If analyzing TSLA, PLTR, NVDA diversification,
    we need the same dates for all three stocks so we can compare
    how they moved together or apart.
    """

    tickers: list[str] = Field(..., min_length=2, description="Asset ticker symbols (min 2 for correlation)")
    dates: list[date] = Field(..., min_length=30, description="Trading dates (must be same for all assets)")
    prices: dict[str, list[float]] = Field(..., description="Price series for each ticker")

    @field_validator('prices')
    @classmethod
    def validate_prices_structure(cls, v: dict[str, list[float]], info) -> dict[str, list[float]]:
        """
        Validate that all price series have the same length and positive values.

        EDUCATIONAL NOTE:
        We need equal-length price series because correlation measures how
        two things move TOGETHER. If one series has 90 days and another has
        60 days, we can't properly compare them.
        """
        if not v:
            raise ValueError('Prices dictionary cannot be empty')

        # Check all prices are positive
        for ticker, price_list in v.items():
            if any(p <= 0 for p in price_list):
                raise ValueError(f'All prices for {ticker} must be positive')

        # Check all series have same length
        lengths = [len(price_list) for price_list in v.values()]
        if len(set(lengths)) > 1:
            raise ValueError(
                f'All price series must have same length. Found: {dict(zip(v.keys(), lengths))}'
            )

        # Check tickers match
        tickers_in_data = info.data.get('tickers', [])
        if tickers_in_data:
            for ticker in tickers_in_data:
                if ticker not in v:
                    raise ValueError(f'Ticker {ticker} listed but no price data provided')

        return v

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "tickers": ["TSLA", "SPY"],
                "dates": ["2025-10-10", "2025-10-11", "2025-10-12"],
                "prices": {
                    "TSLA": [250.0, 252.5, 251.0],
                    "SPY": [450.0, 452.0, 451.5]
                }
            }]
        }
    }


class CorrelationConfig(BaseModel):
    """
    WHAT: Configuration for correlation analysis
    WHY: Standardizes correlation calculations across Finance Guru agents

    EDUCATIONAL NOTE:
    - Pearson correlation: Measures LINEAR relationship (-1 to +1)
      - +1.0 = Perfect positive correlation (move together)
      - 0.0 = No correlation (independent)
      - -1.0 = Perfect negative correlation (opposite moves - ideal hedge!)

    - Rolling window: How many days to use for time-varying correlation
      - Shorter window (30 days) = more responsive to recent changes
      - Longer window (90 days) = more stable, less noise
    """

    method: Literal["pearson", "spearman"] = Field(
        default="pearson",
        description="Correlation method (pearson for linear, spearman for rank-based)"
    )

    rolling_window: int | None = Field(
        default=None,
        ge=20,
        le=252,
        description="Rolling window for time-varying correlation (None = full period)"
    )

    min_periods: int = Field(
        default=30,
        ge=10,
        description="Minimum periods required for rolling correlation calculation"
    )


class CorrelationMatrixOutput(BaseModel):
    """
    WHAT: Correlation matrix results
    WHY: Shows pairwise correlations between all assets

    EDUCATIONAL NOTE:
    A correlation matrix is like a multiplication table, but for correlations.
    It shows how every asset correlates with every other asset.

    Example for TSLA, PLTR, NVDA:
                TSLA    PLTR    NVDA
        TSLA    1.00    0.65    0.72
        PLTR    0.65    1.00    0.58
        NVDA    0.72    0.58    1.00

    Reading this:
    - Diagonal is always 1.00 (asset perfectly correlates with itself)
    - TSLA/NVDA = 0.72 (strong positive correlation - move together)
    - PLTR/NVDA = 0.58 (moderate correlation - some independence)

    FOR YOUR PORTFOLIO:
    - High correlations (>0.7) = Not well diversified
    - Low correlations (<0.3) = Good diversification
    - Negative correlations (<0) = Excellent hedge
    """

    tickers: list[str] = Field(..., description="Asset ticker symbols")
    calculation_date: date = Field(..., description="Date of calculation")
    correlation_matrix: dict[str, dict[str, float]] = Field(
        ...,
        description="Full correlation matrix (ticker -> ticker -> correlation)"
    )
    average_correlation: float = Field(
        ...,
        ge=-1.0,
        le=1.0,
        description="Average pairwise correlation (portfolio concentration measure)"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "tickers": ["TSLA", "SPY"],
                "calculation_date": "2025-10-13",
                "correlation_matrix": {
                    "TSLA": {"TSLA": 1.0, "SPY": 0.65},
                    "SPY": {"TSLA": 0.65, "SPY": 1.0}
                },
                "average_correlation": 0.65
            }]
        }
    }


class CovarianceMatrixOutput(BaseModel):
    """
    WHAT: Covariance matrix results
    WHY: Used for portfolio optimization and risk calculation

    EDUCATIONAL NOTE:
    Covariance is like correlation but NOT standardized to -1 to +1.
    It measures how much two assets vary together in ACTUAL UNITS.

    WHY IT MATTERS:
    - Portfolio optimization algorithms (like Markowitz) use covariance matrices
    - Portfolio variance = weighted sum of covariances
    - Higher covariance = more risk when combining assets

    DIFFERENCE FROM CORRELATION:
    - Correlation: Standardized (-1 to +1), easier to interpret
    - Covariance: Raw units, better for math/optimization
    """

    tickers: list[str] = Field(..., description="Asset ticker symbols")
    calculation_date: date = Field(..., description="Date of calculation")
    covariance_matrix: dict[str, dict[str, float]] = Field(
        ...,
        description="Full covariance matrix (ticker -> ticker -> covariance)"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "tickers": ["TSLA", "SPY"],
                "calculation_date": "2025-10-13",
                "covariance_matrix": {
                    "TSLA": {"TSLA": 0.00156, "SPY": 0.00045},
                    "SPY": {"TSLA": 0.00045, "SPY": 0.00032}
                }
            }]
        }
    }


class RollingCorrelationOutput(BaseModel):
    """
    WHAT: Time-varying correlation between two assets
    WHY: Track how correlation changes over time (regime shifts)

    EDUCATIONAL NOTE:
    Correlations are NOT constant! They change based on market conditions.

    EXAMPLE - TSLA vs SPY:
    - Bull market (calm times): Correlation = 0.5 (moderate)
    - Crisis/volatility spike: Correlation = 0.9 (everything crashes together!)
    - This is why "diversification disappears when you need it most"

    USE CASE:
    Track rolling correlation to identify when your portfolio becomes
    dangerously concentrated (all correlations spike during stress).
    """

    ticker_1: str = Field(..., description="First asset")
    ticker_2: str = Field(..., description="Second asset")
    dates: list[date] = Field(..., description="Dates for rolling correlation")
    correlations: list[float] = Field(..., description="Rolling correlation values")
    current_correlation: float = Field(
        ...,
        ge=-1.0,
        le=1.0,
        description="Most recent correlation value"
    )
    average_correlation: float = Field(
        ...,
        ge=-1.0,
        le=1.0,
        description="Average correlation over the period"
    )
    correlation_range: tuple[float, float] = Field(
        ...,
        description="Min and max correlation observed (shows stability)"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "ticker_1": "TSLA",
                "ticker_2": "SPY",
                "dates": ["2025-10-10", "2025-10-11", "2025-10-12"],
                "correlations": [0.62, 0.65, 0.68],
                "current_correlation": 0.68,
                "average_correlation": 0.65,
                "correlation_range": [0.45, 0.85]
            }]
        }
    }


class PortfolioCorrelationOutput(BaseModel):
    """
    WHAT: Complete correlation analysis output
    WHY: Comprehensive diversification assessment for portfolio construction

    AGENT USE CASES:
    - Strategy Advisor: Portfolio diversification score, rebalancing signals
    - Quant Analyst: Factor model inputs, optimization constraints
    - Risk Assessment: Concentration risk monitoring, correlation regime shifts
    """

    calculation_date: date
    tickers: list[str]

    # Core analysis outputs
    correlation_matrix: CorrelationMatrixOutput
    covariance_matrix: CovarianceMatrixOutput

    # Portfolio-level metrics
    diversification_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Diversification score (1.0 = perfect, 0.0 = fully correlated)"
    )

    concentration_warning: bool = Field(
        ...,
        description="True if average correlation exceeds 0.7 (concentration risk)"
    )

    # Optional rolling analysis
    rolling_correlations: list[RollingCorrelationOutput] | None = Field(
        default=None,
        description="Time-varying correlations (if rolling window specified)"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "calculation_date": "2025-10-13",
                "tickers": ["TSLA", "PLTR", "NVDA"],
                "correlation_matrix": {
                    "tickers": ["TSLA", "PLTR", "NVDA"],
                    "calculation_date": "2025-10-13",
                    "correlation_matrix": {
                        "TSLA": {"TSLA": 1.0, "PLTR": 0.65, "NVDA": 0.72},
                        "PLTR": {"TSLA": 0.65, "PLTR": 1.0, "NVDA": 0.58},
                        "NVDA": {"TSLA": 0.72, "PLTR": 0.58, "NVDA": 1.0}
                    },
                    "average_correlation": 0.65
                },
                "covariance_matrix": {
                    "tickers": ["TSLA", "PLTR", "NVDA"],
                    "calculation_date": "2025-10-13",
                    "covariance_matrix": {}
                },
                "diversification_score": 0.42,
                "concentration_warning": False,
                "rolling_correlations": None
            }]
        }
    }
