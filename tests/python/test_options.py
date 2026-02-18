"""Tests for Options Calculator (Black-Scholes pricing and Greeks).

Tests cover:
- Call and put option pricing
- Greeks calculation (delta, gamma, theta, vega, rho)
- Implied volatility solver
- Put-call parity check
- Moneyness classification
- Convenience function
- Edge cases

RUNNING TESTS:
    uv run pytest tests/python/test_options.py -v
"""

import pytest

from src.analysis.options import OptionsCalculator, price_option
from src.models.options_inputs import (
    BlackScholesInput,
    ImpliedVolInput,
    PutCallParityInput,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def calculator():
    return OptionsCalculator()


@pytest.fixture
def atm_call_input():
    """ATM call: spot = strike = 100, 3 months, 30% vol."""
    return BlackScholesInput(
        spot_price=100.0,
        strike=100.0,
        time_to_expiry=0.25,
        volatility=0.30,
        risk_free_rate=0.05,
        dividend_yield=0.0,
        option_type="call",
    )


@pytest.fixture
def atm_put_input():
    """ATM put: spot = strike = 100, 3 months, 30% vol."""
    return BlackScholesInput(
        spot_price=100.0,
        strike=100.0,
        time_to_expiry=0.25,
        volatility=0.30,
        risk_free_rate=0.05,
        dividend_yield=0.0,
        option_type="put",
    )


@pytest.fixture
def itm_call_input():
    """ITM call: spot=120, strike=100."""
    return BlackScholesInput(
        spot_price=120.0,
        strike=100.0,
        time_to_expiry=0.25,
        volatility=0.30,
        risk_free_rate=0.05,
        dividend_yield=0.0,
        option_type="call",
    )


@pytest.fixture
def otm_call_input():
    """OTM call: spot=80, strike=100."""
    return BlackScholesInput(
        spot_price=80.0,
        strike=100.0,
        time_to_expiry=0.25,
        volatility=0.30,
        risk_free_rate=0.05,
        dividend_yield=0.0,
        option_type="call",
    )


# ---------------------------------------------------------------------------
# Option pricing
# ---------------------------------------------------------------------------


class TestOptionPricing:
    def test_call_price_positive(self, calculator, atm_call_input):
        result = calculator.price_option(atm_call_input)
        assert result.option_price > 0

    def test_put_price_positive(self, calculator, atm_put_input):
        result = calculator.price_option(atm_put_input)
        assert result.option_price > 0

    def test_itm_call_has_intrinsic_value(self, calculator, itm_call_input):
        result = calculator.price_option(itm_call_input)
        # Intrinsic value = spot - strike = 120 - 100 = 20
        assert result.intrinsic_value == pytest.approx(20.0, abs=0.01)
        assert result.option_price >= result.intrinsic_value

    def test_otm_call_no_intrinsic_value(self, calculator, otm_call_input):
        result = calculator.price_option(otm_call_input)
        assert result.intrinsic_value == 0.0
        assert result.time_value == result.option_price

    def test_time_value_positive(self, calculator, atm_call_input):
        result = calculator.price_option(atm_call_input)
        assert result.time_value > 0

    def test_call_price_known_answer(self, calculator):
        """Known-answer test against standard BS result."""
        bs = BlackScholesInput(
            spot_price=100.0,
            strike=100.0,
            time_to_expiry=1.0,
            volatility=0.20,
            risk_free_rate=0.05,
            dividend_yield=0.0,
            option_type="call",
        )
        result = calculator.price_option(bs)
        # Standard BS call ~= $10.45 for these parameters
        assert result.option_price == pytest.approx(10.45, abs=0.5)

    def test_put_price_with_dividend(self, calculator):
        bs = BlackScholesInput(
            spot_price=100.0,
            strike=100.0,
            time_to_expiry=0.5,
            volatility=0.25,
            risk_free_rate=0.05,
            dividend_yield=0.02,
            option_type="put",
        )
        result = calculator.price_option(bs)
        assert result.option_price > 0


# ---------------------------------------------------------------------------
# Greeks
# ---------------------------------------------------------------------------


class TestGreeks:
    def test_call_delta_between_0_and_1(self, calculator, atm_call_input):
        result = calculator.price_option(atm_call_input)
        assert 0 < result.delta < 1

    def test_put_delta_between_neg1_and_0(self, calculator, atm_put_input):
        result = calculator.price_option(atm_put_input)
        assert -1 < result.delta < 0

    def test_atm_call_delta_near_05(self, calculator, atm_call_input):
        result = calculator.price_option(atm_call_input)
        assert result.delta == pytest.approx(0.5, abs=0.1)

    def test_itm_call_delta_near_1(self, calculator, itm_call_input):
        result = calculator.price_option(itm_call_input)
        assert result.delta > 0.7

    def test_gamma_positive(self, calculator, atm_call_input):
        result = calculator.price_option(atm_call_input)
        assert result.gamma > 0

    def test_theta_negative(self, calculator, atm_call_input):
        result = calculator.price_option(atm_call_input)
        assert result.theta < 0  # Time decay

    def test_vega_positive(self, calculator, atm_call_input):
        result = calculator.price_option(atm_call_input)
        assert result.vega > 0

    def test_call_rho_positive(self, calculator, atm_call_input):
        result = calculator.price_option(atm_call_input)
        assert result.rho > 0

    def test_put_rho_negative(self, calculator, atm_put_input):
        result = calculator.price_option(atm_put_input)
        assert result.rho < 0

    def test_put_theta_negative(self, calculator, atm_put_input):
        result = calculator.price_option(atm_put_input)
        assert result.theta < 0


# ---------------------------------------------------------------------------
# Moneyness
# ---------------------------------------------------------------------------


class TestMoneyness:
    def test_itm_call(self, calculator, itm_call_input):
        result = calculator.price_option(itm_call_input)
        assert result.moneyness == "ITM"

    def test_otm_call(self, calculator, otm_call_input):
        result = calculator.price_option(otm_call_input)
        assert result.moneyness == "OTM"

    def test_atm_call(self, calculator, atm_call_input):
        result = calculator.price_option(atm_call_input)
        assert result.moneyness == "ATM"

    def test_itm_put(self, calculator):
        """Slightly ITM put (not deep ITM to avoid edge cases)."""
        bs = BlackScholesInput(
            spot_price=95.0,
            strike=100.0,
            time_to_expiry=0.5,
            volatility=0.30,
            risk_free_rate=0.05,
            option_type="put",
        )
        result = calculator.price_option(bs)
        assert result.moneyness == "ITM"

    def test_otm_put(self, calculator):
        bs = BlackScholesInput(
            spot_price=120.0,
            strike=100.0,
            time_to_expiry=0.25,
            volatility=0.30,
            risk_free_rate=0.05,
            option_type="put",
        )
        result = calculator.price_option(bs)
        assert result.moneyness == "OTM"

    def test_atm_put(self, calculator, atm_put_input):
        result = calculator.price_option(atm_put_input)
        assert result.moneyness == "ATM"


# ---------------------------------------------------------------------------
# Implied volatility
# ---------------------------------------------------------------------------


class TestImpliedVolatility:
    def test_implied_vol_converges(self, calculator, atm_call_input):
        # First price the option to get a "market price"
        greeks = calculator.price_option(atm_call_input)
        market_price = greeks.option_price

        # Then solve for implied vol
        iv_input = ImpliedVolInput(
            spot_price=100.0,
            strike=100.0,
            time_to_expiry=0.25,
            market_price=market_price,
            option_type="call",
            risk_free_rate=0.05,
        )
        result = calculator.calculate_implied_vol(iv_input)

        assert result.converged is True
        assert result.implied_volatility == pytest.approx(0.30, abs=0.02)
        assert result.pricing_error < 0.01

    def test_implied_vol_put(self, calculator, atm_put_input):
        greeks = calculator.price_option(atm_put_input)
        market_price = greeks.option_price

        iv_input = ImpliedVolInput(
            spot_price=100.0,
            strike=100.0,
            time_to_expiry=0.25,
            market_price=market_price,
            option_type="put",
            risk_free_rate=0.05,
        )
        result = calculator.calculate_implied_vol(iv_input)

        assert result.converged is True
        assert result.implied_volatility == pytest.approx(0.30, abs=0.02)

    def test_implied_vol_iterations_tracked(self, calculator, atm_call_input):
        greeks = calculator.price_option(atm_call_input)

        iv_input = ImpliedVolInput(
            spot_price=100.0,
            strike=100.0,
            time_to_expiry=0.25,
            market_price=greeks.option_price,
            option_type="call",
            risk_free_rate=0.05,
        )
        result = calculator.calculate_implied_vol(iv_input)

        assert result.iterations > 0
        assert result.iterations < 100


# ---------------------------------------------------------------------------
# Put-call parity
# ---------------------------------------------------------------------------


class TestPutCallParity:
    def test_parity_holds(self, calculator):
        """When pricing with same BS params, parity should hold."""
        call_params = BlackScholesInput(
            spot_price=100.0,
            strike=100.0,
            time_to_expiry=0.25,
            volatility=0.30,
            risk_free_rate=0.05,
            option_type="call",
        )
        put_params = BlackScholesInput(
            spot_price=100.0,
            strike=100.0,
            time_to_expiry=0.25,
            volatility=0.30,
            risk_free_rate=0.05,
            option_type="put",
        )
        call_price = calculator.price_option(call_params).option_price
        put_price = calculator.price_option(put_params).option_price

        parity_input = PutCallParityInput(
            call_price=call_price,
            put_price=put_price,
            spot_price=100.0,
            strike=100.0,
            time_to_expiry=0.25,
            risk_free_rate=0.05,
        )
        result = calculator.check_put_call_parity(parity_input)

        assert result["arbitrage"] is False
        assert result["difference"] < 0.10

    def test_parity_detects_arbitrage(self, calculator):
        """Mismatched prices should trigger arbitrage detection."""
        parity_input = PutCallParityInput(
            call_price=20.0,
            put_price=5.0,
            spot_price=100.0,
            strike=100.0,
            time_to_expiry=0.25,
            risk_free_rate=0.05,
        )
        result = calculator.check_put_call_parity(parity_input)

        assert result["arbitrage"] is True
        assert "VIOLATED" in result["interpretation"]

    def test_parity_with_dividend(self, calculator):
        parity_input = PutCallParityInput(
            call_price=10.0,
            put_price=9.0,
            spot_price=100.0,
            strike=100.0,
            time_to_expiry=0.5,
            risk_free_rate=0.05,
            dividend_yield=0.02,
        )
        result = calculator.check_put_call_parity(parity_input)

        assert "lhs" in result
        assert "rhs" in result
        assert "difference" in result


# ---------------------------------------------------------------------------
# Convenience function
# ---------------------------------------------------------------------------


class TestConvenienceFunction:
    def test_price_option_call(self):
        result = price_option(
            spot=100.0,
            strike=100.0,
            days_to_expiry=90,
            volatility=0.30,
            option_type="call",
        )
        assert result.option_price > 0
        assert result.option_type == "call"

    def test_price_option_put(self):
        result = price_option(
            spot=100.0,
            strike=100.0,
            days_to_expiry=90,
            volatility=0.30,
            option_type="put",
        )
        assert result.option_price > 0
        assert result.option_type == "put"

    def test_price_option_with_dividend(self):
        result = price_option(
            spot=100.0,
            strike=100.0,
            days_to_expiry=180,
            volatility=0.25,
            option_type="call",
            dividend_yield=0.02,
        )
        assert result.option_price > 0
