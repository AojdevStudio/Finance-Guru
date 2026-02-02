"""
Options Analytics Pydantic Models for Finance Guru™

This module defines type-safe data structures for options pricing and Greeks.
All models use Pydantic for automatic validation and type checking.

ARCHITECTURE NOTE:
These models represent Layer 1 of our 3-layer architecture:
    Layer 1: Pydantic Models (THIS FILE) - Data validation
    Layer 2: Calculator Classes - Business logic
    Layer 3: CLI Interface - Agent integration

EDUCATIONAL CONTEXT:
Options are derivatives that give the right (but not obligation) to buy/sell
an asset at a specified price (strike) before expiration.

KEY CONCEPTS:
- CALL: Right to buy at strike price (profits when price goes up)
- PUT: Right to sell at strike price (profits when price goes down)
- STRIKE: The price at which you can exercise the option
- EXPIRY: Date when option expires
- IMPLIED VOLATILITY: Market's expectation of future volatility

GREEKS measure option price sensitivity:
- DELTA: Price sensitivity to stock price ($1 stock move = $Delta option move)
- GAMMA: Rate of Delta change (second derivative)
- THETA: Time decay ($ lost per day)
- VEGA: Volatility sensitivity ($ change per 1% volatility change)
- RHO: Interest rate sensitivity

Author: Finance Guru™ Development Team
Created: 2025-10-13
"""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class OptionInput(BaseModel):
    """
    Basic option contract specifications.

    WHAT: Defines an option contract
    WHY: Standard format for option identification
    VALIDATES:
        - Strike price is positive
        - Expiry is in the future
        - Option type is call or put
    """

    ticker: str = Field(
        ...,
        description="Underlying asset ticker",
        min_length=1,
        max_length=10,
    )

    strike: float = Field(
        ...,
        gt=0.0,
        description="Strike price (must be positive)"
    )

    expiry: date = Field(
        ...,
        description="Expiration date (must be future date)"
    )

    option_type: Literal["call", "put"] = Field(
        ...,
        description="Option type: call or put"
    )

    @field_validator("expiry")
    @classmethod
    def expiry_must_be_future(cls, v: date) -> date:
        """Ensure expiry is in the future."""
        if v <= date.today():
            raise ValueError(
                f"Expiry date {v} must be in the future (today is {date.today()})"
            )
        return v


class BlackScholesInput(BaseModel):
    """
    Inputs for Black-Scholes option pricing model.

    WHAT: Parameters needed for theoretical option valuation
    WHY: Black-Scholes is the standard model for European options
    VALIDATES:
        - All prices/rates are non-negative
        - Volatility is reasonable (0-300%)
        - Time to expiry is positive

    EDUCATIONAL NOTE:
    Black-Scholes assumptions:
    - European exercise (only at expiry)
    - No dividends during option life
    - Constant volatility and interest rate
    - Log-normal price distribution
    """

    spot_price: float = Field(
        ...,
        gt=0.0,
        description="Current stock price"
    )

    strike: float = Field(
        ...,
        gt=0.0,
        description="Option strike price"
    )

    time_to_expiry: float = Field(
        ...,
        gt=0.0,
        le=10.0,
        description="Time to expiry in years (e.g., 0.25 = 3 months)"
    )

    volatility: float = Field(
        ...,
        ge=0.01,
        le=3.0,
        description="Annual volatility as decimal (e.g., 0.35 = 35%)"
    )

    risk_free_rate: float = Field(
        default=0.045,
        ge=0.0,
        le=0.20,
        description="Annual risk-free rate (default: 4.5%)"
    )

    dividend_yield: float = Field(
        default=0.0,
        ge=0.0,
        le=0.20,
        description="Annual dividend yield (default: 0%)"
    )

    option_type: Literal["call", "put"] = Field(
        ...,
        description="Option type: call or put"
    )

    @field_validator("volatility")
    @classmethod
    def validate_volatility_reasonable(cls, v: float) -> float:
        """Warn if volatility is extreme."""
        if v > 1.5:
            import warnings
            warnings.warn(
                f"Volatility of {v:.0%} is very high (>150%). "
                "Verify this is correct for your asset."
            )
        return v


class GreeksOutput(BaseModel):
    """
    Option Greeks and pricing output.

    WHAT: Complete option valuation with sensitivities
    WHY: Greeks help manage option risk
    USE CASES:
        - Delta hedging: Use delta to hedge stock position
        - Gamma management: Monitor convexity risk
        - Theta decay: Track daily time value loss
        - Vega exposure: Manage volatility risk

    EDUCATIONAL NOTE:
    Greeks interpretation:
    - Delta 0.50 means: $1 stock up → $0.50 option up
    - Gamma 0.05 means: $1 stock up → Delta increases by 0.05
    - Theta -0.10 means: Lose $0.10 per day from time decay
    - Vega 0.20 means: 1% volatility up → $0.20 option up
    """

    # Identification
    ticker: str = Field(..., description="Underlying asset ticker")
    option_type: Literal["call", "put"] = Field(..., description="Option type")
    calculation_date: date = Field(..., description="Date of calculation")

    # Pricing
    option_price: float = Field(
        ...,
        ge=0.0,
        description="Theoretical option price"
    )

    intrinsic_value: float = Field(
        ...,
        ge=0.0,
        description="Intrinsic value (immediate exercise value)"
    )

    time_value: float = Field(
        ...,
        ge=0.0,
        description="Time value (option_price - intrinsic_value)"
    )

    # Greeks (First Order)
    delta: float = Field(
        ...,
        ge=-1.0,
        le=1.0,
        description="Delta: Price sensitivity to $1 stock move"
    )

    gamma: float = Field(
        ...,
        ge=0.0,
        description="Gamma: Rate of Delta change (always positive)"
    )

    theta: float = Field(
        ...,
        le=0.0,
        description="Theta: Daily time decay (always negative)"
    )

    vega: float = Field(
        ...,
        ge=0.0,
        description="Vega: Sensitivity to 1% volatility change"
    )

    rho: float = Field(
        ...,
        description="Rho: Sensitivity to 1% interest rate change"
    )

    # Moneyness
    moneyness: Literal["ITM", "ATM", "OTM"] = Field(
        ...,
        description="Moneyness: In/At/Out of the money"
    )

    # Input parameters (for reference)
    spot_price: float = Field(..., description="Spot price used")
    strike: float = Field(..., description="Strike price")
    time_to_expiry: float = Field(..., description="Time to expiry (years)")
    volatility: float = Field(..., description="Volatility used")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "ticker": "TSLA",
                    "option_type": "call",
                    "calculation_date": "2025-10-13",
                    "option_price": 25.50,
                    "intrinsic_value": 15.00,
                    "time_value": 10.50,
                    "delta": 0.65,
                    "gamma": 0.015,
                    "theta": -0.12,
                    "vega": 0.22,
                    "rho": 0.18,
                    "moneyness": "ITM",
                    "spot_price": 265.00,
                    "strike": 250.00,
                    "time_to_expiry": 0.25,
                    "volatility": 0.45
                }
            ]
        }
    }


class ImpliedVolInput(BaseModel):
    """
    Inputs for implied volatility calculation.

    WHAT: Reverse-engineer volatility from market option price
    WHY: Market price reflects market's volatility expectation
    HOW: Newton-Raphson iterative solver

    EDUCATIONAL NOTE:
    Implied volatility (IV) is what the market THINKS volatility will be.
    Historical volatility is what volatility WAS.
    If IV > historical vol: Market expects increased volatility (fear/uncertainty)
    If IV < historical vol: Market expects decreased volatility (complacency)
    """

    spot_price: float = Field(..., gt=0.0, description="Current stock price")
    strike: float = Field(..., gt=0.0, description="Option strike")
    time_to_expiry: float = Field(..., gt=0.0, description="Time to expiry (years)")
    market_price: float = Field(..., gt=0.0, description="Observed market price")
    option_type: Literal["call", "put"] = Field(..., description="Option type")
    risk_free_rate: float = Field(default=0.045, description="Risk-free rate")
    dividend_yield: float = Field(default=0.0, description="Dividend yield")


class ImpliedVolOutput(BaseModel):
    """
    Implied volatility calculation result.

    WHAT: Market-implied volatility from option price
    WHY: Shows market's fear/expectation
    """

    ticker: str = Field(..., description="Underlying ticker")
    implied_volatility: float = Field(
        ...,
        ge=0.0,
        le=5.0,
        description="Implied volatility (decimal, e.g., 0.45 = 45%)"
    )

    iterations: int = Field(..., description="Solver iterations required")
    converged: bool = Field(..., description="Whether solver converged")

    market_price: float = Field(..., description="Input market price")
    calculated_price: float = Field(..., description="Price at implied vol")

    pricing_error: float = Field(
        ...,
        description="Absolute difference between market and calculated"
    )


class PutCallParityInput(BaseModel):
    """
    Inputs for put-call parity check.

    WHAT: Relationship between call, put, stock, and bond prices
    WHY: Detects arbitrage opportunities
    FORMULA:
        Call - Put = Stock - PV(Strike)
        where PV = Present Value discounted at risk-free rate

    EDUCATIONAL NOTE:
    Put-call parity is an arbitrage relationship. If violated,
    there's a risk-free profit opportunity (very rare in liquid markets).
    """

    call_price: float = Field(..., gt=0.0, description="Call option price")
    put_price: float = Field(..., gt=0.0, description="Put option price")
    spot_price: float = Field(..., gt=0.0, description="Stock price")
    strike: float = Field(..., gt=0.0, description="Strike price")
    time_to_expiry: float = Field(..., gt=0.0, description="Time to expiry (years)")
    risk_free_rate: float = Field(default=0.045, description="Risk-free rate")
    dividend_yield: float = Field(default=0.0, description="Dividend yield")


class OptionContractData(BaseModel):
    """Market data + calculated Greeks for a single option contract."""
    contract_symbol: str = Field(..., description="Full option contract symbol")
    expiration: str = Field(..., description="Expiration date YYYY-MM-DD")
    strike: float = Field(..., gt=0.0, description="Strike price")
    otm_pct: float = Field(..., description="Percent out of the money")
    days_to_expiry: int = Field(..., ge=0, description="Days until expiration")
    last_price: float = Field(..., ge=0.0, description="Last traded premium")
    bid: float = Field(..., ge=0.0, description="Bid price")
    ask: float = Field(..., ge=0.0, description="Ask price")
    mid: float = Field(..., ge=0.0, description="Mid price (bid+ask)/2")
    volume: int = Field(default=0, ge=0, description="Trading volume")
    open_interest: int = Field(default=0, ge=0, description="Open interest")
    implied_volatility: float = Field(default=0.0, ge=0.0, description="Implied volatility from market")
    delta: float | None = Field(default=None, description="Calculated delta")
    gamma: float | None = Field(default=None, description="Calculated gamma")
    theta: float | None = Field(default=None, description="Calculated theta (per day)")
    vega: float | None = Field(default=None, description="Calculated vega")
    total_cost: float = Field(..., ge=0.0, description="Cost per contract (premium x 100)")
    contracts_in_budget: int | None = Field(default=None, description="Max contracts affordable")


class OptionsChainOutput(BaseModel):
    """Full options chain scan result."""
    ticker: str
    spot_price: float
    scan_date: str
    option_type: Literal["call", "put"]
    otm_range: tuple[float, float] = Field(..., description="OTM% filter range")
    days_range: tuple[int, int] = Field(..., description="Days to expiry filter range")
    budget: float | None = None
    target_contracts: int = 1
    expirations_available: list[str] = Field(default_factory=list)
    expirations_scanned: list[str] = Field(default_factory=list)
    contracts: list[OptionContractData] = Field(default_factory=list)
    total_found: int = 0

    model_config = {"arbitrary_types_allowed": True}


# Type exports
__all__ = [
    "OptionInput",
    "BlackScholesInput",
    "GreeksOutput",
    "ImpliedVolInput",
    "ImpliedVolOutput",
    "PutCallParityInput",
    "OptionContractData",
    "OptionsChainOutput",
]
