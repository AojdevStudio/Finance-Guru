"""
Tests for onboarding wizard validators and retry-with-skip wrapper.

Covers:
- validate_currency: dollar parsing with $, commas, k/M shorthand
- validate_percentage: percentage parsing with % suffix
- validate_positive_integer: positive integer parsing
- ask_with_retry: retry logic, skip-after-max-retries, Ctrl+C handling

Author: Finance Guru Development Team
Created: 2026-02-05
"""

import pytest

from src.utils.onboarding_validators import (
    ask_with_retry,
    validate_currency,
    validate_percentage,
    validate_positive_integer,
)


# ---------------------------------------------------------------------------
# validate_currency
# ---------------------------------------------------------------------------


class TestValidateCurrency:
    """Test currency string parsing."""

    def test_plain_number(self):
        assert validate_currency("10000") == 10000.0

    def test_dollar_with_commas(self):
        assert validate_currency("$10,000") == 10000.0

    def test_dollar_with_cents(self):
        assert validate_currency("$10,000.50") == 10000.50

    def test_zero(self):
        assert validate_currency("0") == 0.0

    def test_shorthand_k(self):
        assert validate_currency("25k") == 25000.0

    def test_shorthand_K_uppercase(self):
        assert validate_currency("$25K") == 25000.0

    def test_shorthand_m(self):
        assert validate_currency("1.5m") == 1500000.0

    def test_shorthand_M_uppercase(self):
        assert validate_currency("$1.5M") == 1500000.0

    def test_invalid_abc(self):
        with pytest.raises(ValueError):
            validate_currency("abc")

    def test_negative(self):
        with pytest.raises(ValueError):
            validate_currency("-100")

    def test_empty_string(self):
        with pytest.raises(ValueError):
            validate_currency("")

    def test_whitespace_only(self):
        with pytest.raises(ValueError):
            validate_currency("   ")

    def test_dollar_sign_only(self):
        with pytest.raises(ValueError):
            validate_currency("$")


# ---------------------------------------------------------------------------
# validate_percentage
# ---------------------------------------------------------------------------


class TestValidatePercentage:
    """Test percentage string parsing."""

    def test_plain_number(self):
        assert validate_percentage("4.5") == 4.5

    def test_with_percent_sign(self):
        assert validate_percentage("4.5%") == 4.5

    def test_zero(self):
        assert validate_percentage("0") == 0.0

    def test_hundred(self):
        assert validate_percentage("100") == 100.0

    def test_over_hundred_invalid(self):
        with pytest.raises(ValueError):
            validate_percentage("101")

    def test_negative_invalid(self):
        with pytest.raises(ValueError):
            validate_percentage("-1")

    def test_abc_invalid(self):
        with pytest.raises(ValueError):
            validate_percentage("abc")

    def test_empty_invalid(self):
        with pytest.raises(ValueError):
            validate_percentage("")


# ---------------------------------------------------------------------------
# validate_positive_integer
# ---------------------------------------------------------------------------


class TestValidatePositiveInteger:
    """Test positive integer parsing."""

    def test_valid_three(self):
        assert validate_positive_integer("3") == 3

    def test_valid_one(self):
        assert validate_positive_integer("1") == 1

    def test_zero_invalid(self):
        with pytest.raises(ValueError):
            validate_positive_integer("0")

    def test_negative_invalid(self):
        with pytest.raises(ValueError):
            validate_positive_integer("-1")

    def test_abc_invalid(self):
        with pytest.raises(ValueError):
            validate_positive_integer("abc")

    def test_float_invalid(self):
        with pytest.raises(ValueError):
            validate_positive_integer("3.5")

    def test_empty_invalid(self):
        with pytest.raises(ValueError):
            validate_positive_integer("")


# ---------------------------------------------------------------------------
# ask_with_retry
# ---------------------------------------------------------------------------


class TestAskWithRetry:
    """Test the retry-with-skip wrapper."""

    def test_valid_first_attempt(self):
        """Returns validated value on first valid input."""
        call_count = 0

        def prompt_fn():
            nonlocal call_count
            call_count += 1
            return "10000"

        result = ask_with_retry(
            prompt_fn=prompt_fn,
            validator=validate_currency,
            default=0.0,
        )
        assert result == 10000.0
        assert call_count == 1

    def test_valid_after_retries(self):
        """Returns validated value after invalid attempts."""
        responses = iter(["abc", "xyz", "10000"])

        def prompt_fn():
            return next(responses)

        result = ask_with_retry(
            prompt_fn=prompt_fn,
            validator=validate_currency,
            default=0.0,
        )
        assert result == 10000.0

    def test_skip_after_max_retries(self, mocker):
        """Returns default when user accepts skip after max retries."""
        responses = iter(["abc", "def", "ghi"])

        def prompt_fn():
            return next(responses)

        # Mock questionary.confirm in the validators module
        mock_confirm = mocker.patch(
            "src.utils.onboarding_validators.questionary.confirm"
        )
        mock_confirm.return_value.ask.return_value = True  # Accept skip

        result = ask_with_retry(
            prompt_fn=prompt_fn,
            validator=validate_currency,
            default=0.0,
        )
        assert result == 0.0

    def test_ctrl_c_returns_default(self):
        """Returns default when prompt returns None (Ctrl+C)."""

        def prompt_fn():
            return None

        result = ask_with_retry(
            prompt_fn=prompt_fn,
            validator=validate_currency,
            default=42.0,
        )
        assert result == 42.0

    def test_no_validator_returns_raw(self):
        """Without validator, returns raw prompt value."""

        def prompt_fn():
            return "raw_value"

        result = ask_with_retry(
            prompt_fn=prompt_fn,
            validator=None,
            default="default",
        )
        assert result == "raw_value"

    def test_decline_skip_then_succeed(self, mocker):
        """If user declines skip, gets one more attempt."""
        # 3 bad attempts exhaust retries, decline skip, then succeed
        call_count = 0

        def prompt_fn():
            nonlocal call_count
            call_count += 1
            if call_count <= 3:
                return "bad"
            return "5000"

        mock_confirm = mocker.patch(
            "src.utils.onboarding_validators.questionary.confirm"
        )
        mock_confirm.return_value.ask.return_value = False  # Decline skip

        result = ask_with_retry(
            prompt_fn=prompt_fn,
            validator=validate_currency,
            default=0.0,
        )
        assert result == 5000.0
        assert call_count == 4
