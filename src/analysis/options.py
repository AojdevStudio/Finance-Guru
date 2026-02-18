"""Options Analytics Engine for Finance Guru™.

This module implements Black-Scholes option pricing and Greeks calculations.
All calculations follow standard derivatives pricing formulas.

ARCHITECTURE NOTE:
This is Layer 2 of our 3-layer architecture:
    Layer 1: Pydantic Models - Data validation (options_inputs.py)
    Layer 2: Calculator Classes (THIS FILE) - Business logic
    Layer 3: CLI Interface - Agent integration

EDUCATIONAL CONTEXT:
The Black-Scholes model (1973) revolutionized derivatives pricing.
It provides theoretical fair value for European options using:
- Stock price, strike, time, volatility, interest rate

FORMULA (Call):
    C = S * N(d1) - K * e^(-rT) * N(d2)
    where:
        d1 = [ln(S/K) + (r + σ²/2)T] / (σ√T)
        d2 = d1 - σ√T
        N() = cumulative normal distribution

GREEKS (derivatives of price formula):
- Delta = ∂C/∂S (first derivative wrt stock price)
- Gamma = ∂²C/∂S² (second derivative wrt stock price)
- Theta = ∂C/∂t (derivative wrt time)
- Vega = ∂C/∂σ (derivative wrt volatility)
- Rho = ∂C/∂r (derivative wrt interest rate)

Author: Finance Guru™ Development Team
Created: 2025-10-13
"""

from datetime import date
from math import exp, log, sqrt

from scipy.stats import norm

from src.models.options_inputs import (
    BlackScholesInput,
    GreeksOutput,
    ImpliedVolInput,
    ImpliedVolOutput,
    PutCallParityInput,
)


class OptionsCalculator:
    """Black-Scholes options pricing and Greeks calculator.

    WHAT: Calculates theoretical option prices and sensitivities
    WHY: Essential for options trading and risk management
    HOW: Black-Scholes-Merton model (1973)

    USAGE EXAMPLE:
        # Create input
        bs_input = BlackScholesInput(
            spot_price=265.0,
            strike=250.0,
            time_to_expiry=0.25,  # 3 months
            volatility=0.45,  # 45%
            risk_free_rate=0.045,
            option_type="call"
        )

        # Calculate
        calculator = OptionsCalculator()
        greeks = calculator.price_option(bs_input)

        # Check results
        print(f"Option Price: ${greeks.option_price:.2f}")
        print(f"Delta: {greeks.delta:.3f}")
    """

    def price_option(self, params: BlackScholesInput) -> GreeksOutput:
        """Calculate option price and all Greeks.

        Args:
            params: Validated Black-Scholes parameters

        Returns:
            GreeksOutput: Price and all sensitivities

        EDUCATIONAL NOTE:
        This method calculates EVERYTHING in one pass:
        1. d1 and d2 (intermediate values)
        2. Option price using Black-Scholes formula
        3. All five Greeks
        4. Intrinsic and time value
        5. Moneyness classification
        """
        # Extract parameters
        S = params.spot_price
        K = params.strike
        T = params.time_to_expiry
        sigma = params.volatility
        r = params.risk_free_rate
        q = params.dividend_yield
        is_call = params.option_type == "call"

        # Calculate d1 and d2
        d1, d2 = self._calculate_d1_d2(S, K, T, sigma, r, q)

        # Calculate option price
        if is_call:
            price = self._call_price(S, K, T, r, q, d1, d2)
        else:
            price = self._put_price(S, K, T, r, q, d1, d2)

        # Calculate Greeks
        delta = self._calculate_delta(is_call, d1, T, q)
        gamma = self._calculate_gamma(S, d1, T, sigma, q)
        theta = self._calculate_theta(is_call, S, K, T, r, q, sigma, d1, d2)
        vega = self._calculate_vega(S, T, d1, q)
        rho = self._calculate_rho(is_call, K, T, r, d2)

        # Calculate intrinsic and time value
        intrinsic = max(S - K, 0.0) if is_call else max(K - S, 0.0)
        time_value = price - intrinsic

        # Determine moneyness
        if is_call:
            if S > K * 1.02:
                moneyness = "ITM"
            elif S < K * 0.98:
                moneyness = "OTM"
            else:
                moneyness = "ATM"
        else:
            if S < K * 0.98:
                moneyness = "ITM"
            elif S > K * 1.02:
                moneyness = "OTM"
            else:
                moneyness = "ATM"

        return GreeksOutput(
            ticker="UNKNOWN",  # Will be set by caller
            option_type=params.option_type,
            calculation_date=date.today(),
            option_price=float(price),
            intrinsic_value=float(intrinsic),
            time_value=float(time_value),
            delta=float(delta),
            gamma=float(gamma),
            theta=float(theta),
            vega=float(vega),
            rho=float(rho),
            moneyness=moneyness,  # type: ignore
            spot_price=S,
            strike=K,
            time_to_expiry=T,
            volatility=sigma,
        )

    def calculate_implied_vol(self, params: ImpliedVolInput) -> ImpliedVolOutput:
        """Calculate implied volatility using Newton-Raphson method.

        WHAT: Reverse-engineer volatility from market price
        WHY: Implied vol shows market's expectation
        HOW: Iterative solver (Newton-Raphson)

        ALGORITHM:
        1. Start with initial guess (e.g., 30%)
        2. Calculate option price at this vol
        3. Calculate vega (sensitivity to vol)
        4. Update guess: new_vol = old_vol + (market_price - calc_price) / vega
        5. Repeat until convergence

        EDUCATIONAL NOTE:
        Newton-Raphson converges quickly (usually < 10 iterations)
        unless the option is deep ITM/OTM or near expiry.
        """
        S = params.spot_price
        K = params.strike
        T = params.time_to_expiry
        target_price = params.market_price
        r = params.risk_free_rate
        q = params.dividend_yield

        # Initial guess: 30% vol
        vol = 0.30
        tolerance = 0.0001  # $0.01 price tolerance
        max_iterations = 100

        for iteration in range(max_iterations):
            # Create BS input with current vol guess
            bs_input = BlackScholesInput(
                spot_price=S,
                strike=K,
                time_to_expiry=T,
                volatility=vol,
                risk_free_rate=r,
                dividend_yield=q,
                option_type=params.option_type,
            )

            # Calculate price and vega at current vol
            greeks = self.price_option(bs_input)
            calc_price = greeks.option_price
            vega = greeks.vega

            # Check convergence
            price_diff = target_price - calc_price
            if abs(price_diff) < tolerance:
                return ImpliedVolOutput(
                    ticker="UNKNOWN",
                    implied_volatility=float(vol),
                    iterations=iteration + 1,
                    converged=True,
                    market_price=target_price,
                    calculated_price=calc_price,
                    pricing_error=abs(price_diff),
                )

            # Newton-Raphson update
            # New vol = old vol + (target - calculated) / vega
            # Vega is in dollar terms per 1% vol change, so divide by 100
            if vega > 0:
                vol = vol + price_diff / (vega * 100)
            else:
                # Vega should never be zero, but handle edge case
                break

            # Ensure vol stays within bounds
            vol = max(0.01, min(vol, 5.0))

        # Failed to converge
        bs_input = BlackScholesInput(
            spot_price=S,
            strike=K,
            time_to_expiry=T,
            volatility=vol,
            risk_free_rate=r,
            dividend_yield=q,
            option_type=params.option_type,
        )
        greeks = self.price_option(bs_input)

        return ImpliedVolOutput(
            ticker="UNKNOWN",
            implied_volatility=float(vol),
            iterations=max_iterations,
            converged=False,
            market_price=target_price,
            calculated_price=greeks.option_price,
            pricing_error=abs(target_price - greeks.option_price),
        )

    def check_put_call_parity(self, params: PutCallParityInput) -> dict:
        """Check put-call parity relationship.

        FORMULA:
            C - P = S - K * e^(-rT)

        WHY IT MATTERS:
        Put-call parity is an arbitrage relationship. If violated,
        there's a risk-free profit opportunity.

        Returns:
            Dict with:
            - lhs: Left-hand side (Call - Put)
            - rhs: Right-hand side (Stock - PV(Strike))
            - difference: |LHS - RHS|
            - arbitrage: Boolean (True if difference > tolerance)
        """
        C = params.call_price
        P = params.put_price
        S = params.spot_price
        K = params.strike
        T = params.time_to_expiry
        r = params.risk_free_rate
        q = params.dividend_yield

        # Left-hand side: C - P
        lhs = C - P

        # Right-hand side: S * e^(-qT) - K * e^(-rT)
        rhs = S * exp(-q * T) - K * exp(-r * T)

        difference = abs(lhs - rhs)

        # Arbitrage if difference > $0.10 (accounting for transaction costs)
        arbitrage_exists = difference > 0.10

        return {
            "lhs": float(lhs),
            "rhs": float(rhs),
            "difference": float(difference),
            "arbitrage": arbitrage_exists,
            "interpretation": (
                f"Put-call parity {'VIOLATED' if arbitrage_exists else 'holds'}: "
                f"C-P = ${lhs:.2f}, S-PV(K) = ${rhs:.2f}, "
                f"difference = ${difference:.2f}"
            ),
        }

    # Private helper methods

    def _calculate_d1_d2(
        self, S: float, K: float, T: float, sigma: float, r: float, q: float
    ) -> tuple[float, float]:
        """Calculate d1 and d2 for Black-Scholes.

        FORMULAS:
            d1 = [ln(S/K) + (r - q + σ²/2)T] / (σ√T)
            d2 = d1 - σ√T
        """
        d1 = (log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * sqrt(T))
        d2 = d1 - sigma * sqrt(T)
        return d1, d2

    def _call_price(
        self, S: float, K: float, T: float, r: float, q: float, d1: float, d2: float
    ) -> float:
        """Calculate call option price.

        FORMULA:
            C = S * e^(-qT) * N(d1) - K * e^(-rT) * N(d2)
        """
        call = S * exp(-q * T) * norm.cdf(d1) - K * exp(-r * T) * norm.cdf(d2)
        return max(call, 0.0)  # Price can't be negative

    def _put_price(
        self, S: float, K: float, T: float, r: float, q: float, d1: float, d2: float
    ) -> float:
        """Calculate put option price.

        FORMULA:
            P = K * e^(-rT) * N(-d2) - S * e^(-qT) * N(-d1)
        """
        put = K * exp(-r * T) * norm.cdf(-d2) - S * exp(-q * T) * norm.cdf(-d1)
        return max(put, 0.0)

    def _calculate_delta(self, is_call: bool, d1: float, T: float, q: float) -> float:
        """Calculate delta.

        FORMULAS:
            Call: Δ = e^(-qT) * N(d1)
            Put:  Δ = e^(-qT) * [N(d1) - 1] = -e^(-qT) * N(-d1)

        INTERPRETATION:
            Delta = 0.65 means: $1 stock up → $0.65 option up
        """
        if is_call:
            return exp(-q * T) * norm.cdf(d1)
        else:
            return exp(-q * T) * (norm.cdf(d1) - 1)

    def _calculate_gamma(
        self, S: float, d1: float, T: float, sigma: float, q: float
    ) -> float:
        """Calculate gamma.

        FORMULA:
            Γ = e^(-qT) * n(d1) / (S * σ * √T)
            where n() = standard normal PDF

        INTERPRETATION:
            Gamma = 0.05 means: $1 stock up → Delta increases by 0.05

        EDUCATIONAL NOTE:
        Gamma is highest for ATM options near expiry.
        This is when options are most sensitive to price changes.
        """
        gamma = exp(-q * T) * norm.pdf(d1) / (S * sigma * sqrt(T))
        return max(gamma, 0.0)

    def _calculate_theta(
        self,
        is_call: bool,
        S: float,
        K: float,
        T: float,
        r: float,
        q: float,
        sigma: float,
        d1: float,
        d2: float,
    ) -> float:
        """Calculate theta (time decay).

        EDUCATIONAL NOTE:
        Theta is ALWAYS negative (options lose value over time).
        Theta accelerates as expiry approaches.
        ATM options have highest theta.

        INTERPRETATION:
            Theta = -0.10 means: Lose $0.10 per day from time decay
        """
        term1 = -(S * norm.pdf(d1) * sigma * exp(-q * T)) / (2 * sqrt(T))

        if is_call:
            term2 = -r * K * exp(-r * T) * norm.cdf(d2)
            term3 = q * S * exp(-q * T) * norm.cdf(d1)
            theta = term1 + term2 + term3
        else:
            term2 = r * K * exp(-r * T) * norm.cdf(-d2)
            term3 = -q * S * exp(-q * T) * norm.cdf(-d1)
            theta = term1 + term2 + term3

        # Convert to per-day theta (divide by 365)
        return theta / 365

    def _calculate_vega(self, S: float, T: float, d1: float, q: float) -> float:
        """Calculate vega.

        FORMULA:
            V = S * e^(-qT) * √T * n(d1)

        INTERPRETATION:
            Vega = 0.22 means: 1% volatility up → $0.22 option price up

        EDUCATIONAL NOTE:
        Vega is highest for ATM options with time remaining.
        Short-dated and far OTM/ITM options have low vega.
        """
        vega = S * exp(-q * T) * sqrt(T) * norm.pdf(d1)
        # Divide by 100 to get per-1% change
        return vega / 100

    def _calculate_rho(
        self, is_call: bool, K: float, T: float, r: float, d2: float
    ) -> float:
        """Calculate rho.

        FORMULAS:
            Call: ρ = K * T * e^(-rT) * N(d2)
            Put:  ρ = -K * T * e^(-rT) * N(-d2)

        INTERPRETATION:
            Rho = 0.18 means: 1% rate up → $0.18 option price up
        """
        if is_call:
            rho = K * T * exp(-r * T) * norm.cdf(d2)
        else:
            rho = -K * T * exp(-r * T) * norm.cdf(-d2)

        # Divide by 100 to get per-1% change
        return rho / 100


# Convenience functions
def price_option(
    spot: float,
    strike: float,
    days_to_expiry: int,
    volatility: float,
    option_type: str = "call",
    risk_free_rate: float = 0.045,
    dividend_yield: float = 0.0,
) -> GreeksOutput:
    """Convenience function for option pricing.

    Args:
        spot: Current stock price
        strike: Option strike price
        days_to_expiry: Days until expiration
        volatility: Annual volatility (e.g., 0.45 = 45%)
        option_type: "call" or "put"
        risk_free_rate: Annual risk-free rate
        dividend_yield: Annual dividend yield

    Returns:
        GreeksOutput with price and all Greeks
    """
    bs_input = BlackScholesInput(
        spot_price=spot,
        strike=strike,
        time_to_expiry=days_to_expiry / 365,
        volatility=volatility,
        risk_free_rate=risk_free_rate,
        dividend_yield=dividend_yield,
        option_type=option_type,  # type: ignore
    )

    calculator = OptionsCalculator()
    return calculator.price_option(bs_input)


# Type exports
__all__ = [
    "OptionsCalculator",
    "price_option",
]
