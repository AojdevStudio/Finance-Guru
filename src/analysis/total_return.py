"""Total Return Calculator for Finance Guru.

This module implements total return calculations including price return,
dividend return, DRIP (dividend reinvestment) return, and data quality
validation for dividend data from yfinance.

ARCHITECTURE NOTE:
This is Layer 2 of our 3-layer architecture:
    Layer 1: Pydantic Models (total_return_inputs.py) - Data validation
    Layer 2: Calculator Classes (THIS FILE) - Business logic
    Layer 3: CLI Interface - Agent integration

EDUCATIONAL CONTEXT:
Total return measures the complete performance of an investment, capturing
both price appreciation and income (dividends). This distinction matters
because price-only returns UNDERSTATE performance of dividend-paying stocks.

Sean's insight: "You can't say a fund is down without counting distributions."
A fund showing -3.95% price return might actually be UP +4.25% total return
once $8.20 in distributions are counted.

FORMULAS:
- Price Return = (End Price - Start Price) / Start Price
- Dividend Return = Sum(dividends per share) / Start Price
- Total Return = Price Return + Dividend Return
- DRIP Return = (final_shares * final_price) / (initial_shares * initial_price) - 1
- Annualized Return = (1 + total_return) ^ (365 / calendar_days) - 1

Author: Finance Guru Development Team
Created: 2026-02-17
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import yaml

from src.models.total_return_inputs import (
    DividendRecord,
    TotalReturnInput,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Path to dividend schedule YAML (in gitignored fin-guru-private/)
DIVIDEND_SCHEDULES_PATH = str(
    Path(__file__).resolve().parent.parent.parent
    / "fin-guru-private"
    / "dividend-schedules.yaml"
)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class DividendDataError(Exception):
    """Raised when dividend data has quality issues and force is not enabled.

    This error indicates gaps in dividend data that could produce misleading
    total return calculations. Use force=True to override and calculate anyway.
    """


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class TotalReturnResult:
    """Extended result wrapping TickerReturn with additional calculated fields.

    TickerReturn from Phase 6 provides the core fields. TotalReturnResult adds
    annualized return, DRIP details, and period breakdown that the calculator
    computes but TickerReturn does not store.
    """

    ticker: str
    start_date: date
    end_date: date
    price_return: float
    dividend_return: float
    total_return: float
    annualized_return: float | None = None
    drip_total_return: float | None = None
    drip_final_shares: float | None = None
    drip_share_growth: float | None = None
    period_breakdown: list[dict] = field(default_factory=list)
    dividend_count: int = 0
    data_quality_warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Schedule loader
# ---------------------------------------------------------------------------


def load_dividend_schedules() -> dict:
    """Load per-ticker dividend frequency metadata from YAML.

    Returns:
        Dict mapping ticker -> {frequency: int, label: str}.
        Empty dict if file does not exist (graceful fallback).

    The YAML file lives in fin-guru-private/ which is gitignored.
    Missing file is normal (first clone, CI environment).
    """
    path = Path(DIVIDEND_SCHEDULES_PATH)
    if not path.exists():
        return {}
    with open(path) as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        return {}
    return data


# ---------------------------------------------------------------------------
# Calculator
# ---------------------------------------------------------------------------


class TotalReturnCalculator:
    """Calculate price return, dividend return, total return, and DRIP return.

    Follows the Layer 2 calculator pattern from RiskCalculator.
    Accepts a TotalReturnInput plus raw price/dividend data, and provides
    individual calculation methods plus an orchestrating calculate_all().

    Args:
        data: Validated TotalReturnInput with ticker, dates, initial_shares.
        prices: List of prices for the period (at minimum [start_price, end_price]).
        dividends: List of DividendRecord for dividends during the period.
        ex_date_prices: Dict mapping ex-date -> close price for DRIP reinvestment.
    """

    def __init__(
        self,
        data: TotalReturnInput,
        prices: list[float] | None = None,
        dividends: list[DividendRecord] | None = None,
        ex_date_prices: dict[date, float] | None = None,
    ) -> None:
        self.data = data
        self.prices = prices or []
        self.dividends = dividends or []
        self.ex_date_prices = ex_date_prices or {}
        self._schedules: dict | None = None

    @property
    def _dividend_schedules(self) -> dict:
        """Lazy-load dividend schedules on first access."""
        if self._schedules is None:
            self._schedules = load_dividend_schedules()
        return self._schedules

    def calculate_price_return(self) -> float:
        """Calculate price-only return over the period.

        FORMULA: (ending_price - starting_price) / starting_price

        Only the first and last prices matter. Intermediate prices are
        irrelevant for period return (they affect drawdown, not return).

        Returns:
            Price return as decimal (0.10 = 10%).
        """
        if len(self.prices) < 2:
            raise ValueError("Need at least 2 price points for return calculation")
        starting = self.prices[0]
        ending = self.prices[-1]
        return (ending - starting) / starting

    def calculate_dividend_return(self) -> float:
        """Calculate dividend contribution to return.

        FORMULA: sum(dividend_per_share) / starting_price

        This is the income component of total return: how much cash
        the investor received as a percentage of their initial investment.

        Returns:
            Dividend return as decimal (0.04 = 4%).
        """
        if not self.prices:
            raise ValueError("Need prices to calculate dividend return")
        starting_price = self.prices[0]
        total_dividends = sum(d.amount for d in self.dividends)
        return total_dividends / starting_price

    def calculate_total_return(self) -> float:
        """Calculate total return (price + dividend).

        FORMULA: price_return + dividend_return

        This is the core insight: total return captures the COMPLETE
        performance story. A fund showing -3.95% price return might be
        +4.25% total return once distributions are counted.

        Returns:
            Total return as decimal (0.12 = 12%).
        """
        return self.calculate_price_return() + self.calculate_dividend_return()

    def calculate_drip_return(
        self,
    ) -> tuple[float, float, list[dict]]:
        """Calculate return with dividend reinvestment (DRIP).

        For each dividend, reinvest at ex-date close price to buy more shares.
        The growing share count means each subsequent dividend buys even more
        shares, compounding the effect.

        FORMULA per dividend:
            dividend_cash = current_shares * dividend_per_share
            new_shares = dividend_cash / close_price_on_ex_date
            current_shares += new_shares

        DRIP total return:
            (final_shares * final_price) / (initial_shares * initial_price) - 1

        Returns:
            Tuple of (drip_total_return, final_shares, period_breakdown).
            period_breakdown is a list of dicts with date, shares_acquired,
            cumulative_shares for each dividend event.
        """
        if len(self.prices) < 2:
            raise ValueError("Need at least 2 price points for DRIP calculation")

        shares = self.data.initial_shares
        initial_value = shares * self.prices[0]
        breakdown: list[dict] = []

        for div in self.dividends:
            # Determine reinvestment price: use ex_date_prices if available,
            # otherwise fall back to the last price in the series
            reinvest_price = self.ex_date_prices.get(div.ex_date, self.prices[-1])
            dividend_cash = shares * div.amount
            new_shares = dividend_cash / reinvest_price
            shares += new_shares
            breakdown.append(
                {
                    "date": div.ex_date,
                    "dividend_per_share": div.amount,
                    "reinvest_price": reinvest_price,
                    "shares_acquired": new_shares,
                    "cumulative_shares": shares,
                }
            )

        final_value = shares * self.prices[-1]
        drip_return = (final_value / initial_value) - 1.0
        return drip_return, shares, breakdown

    def calculate_annualized_return(self, total_return: float) -> float:
        """Annualize a period return using calendar days.

        Uses 365 calendar days (NOT 252 trading days) because dividend
        frequency varies (quarterly, monthly, weekly) and calendar time
        is the correct base for annualization.

        FORMULA: (1 + total_return) ^ (365 / calendar_days) - 1

        Args:
            total_return: Period return to annualize.

        Returns:
            Annualized return as decimal.
        """
        calendar_days = (self.data.end_date - self.data.start_date).days
        if calendar_days <= 0:
            raise ValueError("Period must be positive for annualization")
        return float((1.0 + total_return) ** (365.0 / calendar_days) - 1.0)

    def validate_dividend_data(self) -> list[str]:
        """Check for dividend data quality issues.

        Three checks:
        1. Expected frequency vs actual count (25% tolerance)
        2. Split artifact detection (any dividend >3x median)
        3. Known payer with zero dividends

        Returns:
            List of warning strings. Empty list means data looks clean.
        """
        warnings_list: list[str] = []
        ticker = self.data.ticker
        period_days = (self.data.end_date - self.data.start_date).days
        schedules = self._dividend_schedules

        # Check 1: Expected frequency vs actual count
        schedule = schedules.get(ticker)
        if schedule:
            expected_freq = schedule.get("frequency", 0)
            if expected_freq > 0:
                expected_count = max(1, int(expected_freq * period_days / 365))
                actual_count = len(self.dividends)

                # Known payer with zero dividends (Check 3)
                if actual_count == 0:
                    warnings_list.append(
                        f"No dividends found for {ticker} (expected dividend payer). "
                        f"yfinance may have data gaps. Results show price return only."
                    )
                elif actual_count < expected_count * 0.75:
                    # 25% tolerance
                    warnings_list.append(
                        f"Expected ~{expected_count} dividends for {ticker} over "
                        f"{period_days} days, found {actual_count}. "
                        f"Dividend data may be incomplete."
                    )

        # Check 2: Split artifact detection (>3x median)
        if len(self.dividends) >= 2:
            amounts = [d.amount for d in self.dividends]
            median_amount = statistics.median(amounts)
            if median_amount > 0:
                for div in self.dividends:
                    if div.amount > median_amount * 3:
                        warnings_list.append(
                            f"Dividend on {div.ex_date} ({div.amount:.4f}) is >3x "
                            f"median ({median_amount:.4f}). "
                            f"Possible stock split artifact -- suspicious value."
                        )

        return warnings_list

    def calculate_all(self, force: bool = False) -> TotalReturnResult:
        """Orchestrate all calculations and return a complete result.

        Runs validation first. If data quality warnings exist:
        - force=False -> raises DividendDataError (refuses to calculate)
        - force=True -> calculates anyway, includes warnings in result

        Args:
            force: If True, calculate despite data quality warnings.

        Returns:
            TotalReturnResult with all calculated fields.

        Raises:
            DividendDataError: When data has quality issues and force is False.
        """
        # Step 1: Validate data quality
        quality_warnings = self.validate_dividend_data()
        if quality_warnings and not force:
            raise DividendDataError(
                f"Dividend data quality issues for {self.data.ticker}: "
                + "; ".join(quality_warnings)
                + " Use force=True to calculate anyway."
            )

        # Step 2: Calculate returns
        price_ret = self.calculate_price_return()
        div_ret = self.calculate_dividend_return()
        total_ret = self.calculate_total_return()

        # Step 3: DRIP calculation
        drip_ret, final_shares, breakdown = self.calculate_drip_return()

        # Step 4: Annualize
        annualized = self.calculate_annualized_return(total_ret)

        # Step 5: Build result
        return TotalReturnResult(
            ticker=self.data.ticker,
            start_date=self.data.start_date,
            end_date=self.data.end_date,
            price_return=price_ret,
            dividend_return=div_ret,
            total_return=total_ret,
            annualized_return=annualized,
            drip_total_return=drip_ret,
            drip_final_shares=final_shares,
            drip_share_growth=final_shares / self.data.initial_shares,
            period_breakdown=breakdown,
            dividend_count=len(self.dividends),
            data_quality_warnings=quality_warnings,
        )


# Type exports
__all__ = [
    "DividendDataError",
    "TotalReturnCalculator",
    "TotalReturnResult",
    "load_dividend_schedules",
    "DIVIDEND_SCHEDULES_PATH",
]
