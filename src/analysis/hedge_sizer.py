"""Hedge Sizer Calculator for Finance Guru.

This module sizes hedge contracts against a portfolio, allocates across
underlyings, validates budget against live premiums, and reads portfolio
value from Fidelity CSV exports.

ARCHITECTURE NOTE:
This is Layer 2 of our 3-layer architecture:
    Layer 1: Pydantic Models (hedging_inputs.py) - Data validation
    Layer 2: Calculator Classes (THIS FILE) - Business logic
    Layer 3: CLI Interface - Agent integration

EDUCATIONAL CONTEXT:
Hedge sizing determines how many put option contracts to buy for portfolio
protection.  The default formula is 1 contract per $50,000 of portfolio
value (configurable).  Each contract covers 100 shares of the underlying.

SIZING FORMULA (HS-01):
    contracts = floor(portfolio_value / ratio_per_contract)

    Example: $200,000 portfolio / $50,000 per contract = 4 contracts

ALLOCATION:
    When hedging across multiple underlyings (e.g., QQQ + SPY), contracts
    are distributed by weight.  Remainders go to the highest-weight
    underlying first.

    Example: 5 contracts across QQQ (60%) + SPY (40%)
        QQQ = floor(5 * 0.6) = 3, SPY = floor(5 * 0.4) = 2
        Remainder: 5 - (3 + 2) = 0 -> no remainder

    Example: 7 contracts across QQQ (60%) + SPY (40%)
        QQQ = floor(7 * 0.6) = 4, SPY = floor(7 * 0.4) = 2
        Remainder: 7 - (4 + 2) = 1 -> QQQ gets +1 = 5

PORTFOLIO VALUE CASCADE:
    1. CLI flag (--portfolio-value)
    2. Fidelity CSV (notebooks/updates/Balances_for_Account_*.csv)
    3. ValueError if nothing found

BUDGET VALIDATION:
    When the estimated monthly cost exceeds the budget, the tool warns
    but shows the full recommendation -- it does NOT scale down.

DISCLAIMER:
    For educational purposes only.  Not investment advice.
    Consult a qualified financial professional before trading options.

Author: Finance Guru Development Team
Created: 2026-02-18
"""

from __future__ import annotations

import contextlib
import io
import logging
import math
import statistics
from glob import glob
from pathlib import Path

from src.config.config_loader import HedgeConfig

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
"""Project root directory (three levels up from src/analysis/hedge_sizer.py)."""

DEFAULT_RATIO_PER_CONTRACT = 50_000.0
"""Default portfolio value per contract: $50,000. HS-01."""

BALANCES_GLOB = str(
    PROJECT_ROOT / "notebooks" / "updates" / "Balances_for_Account_*.csv"
)
"""Glob pattern for Fidelity balance CSV files."""


# ---------------------------------------------------------------------------
# Module-level helper functions
# ---------------------------------------------------------------------------


def calculate_contract_count(
    portfolio_value: float,
    ratio_per_contract: float = DEFAULT_RATIO_PER_CONTRACT,
) -> int:
    """Calculate how many hedge contracts to buy. HS-01.

    1 contract per $50k portfolio value (configurable).

    Args:
        portfolio_value: Total portfolio value in dollars.
        ratio_per_contract: Dollars of portfolio per contract.

    Returns:
        Number of contracts (integer, floored).
    """
    if portfolio_value <= 0 or ratio_per_contract <= 0:
        return 0
    return math.floor(portfolio_value / ratio_per_contract)


def allocate_contracts(
    total_contracts: int,
    underlying_weights: dict[str, float],
) -> dict[str, int]:
    """Distribute contracts across underlyings by weight.

    Floor-allocates each underlying, then distributes remainder
    to highest-weight underlyings first.

    Args:
        total_contracts: Total number of contracts to allocate.
        underlying_weights: Mapping of ticker -> weight (should sum to ~1.0).

    Returns:
        Mapping of ticker -> contract count.

    Example:
        >>> allocate_contracts(5, {"QQQ": 0.6, "SPY": 0.4})
        {'QQQ': 3, 'SPY': 2}
    """
    if total_contracts <= 0:
        return {ticker: 0 for ticker in underlying_weights}

    # Sort underlyings by weight descending
    sorted_tickers = sorted(
        underlying_weights.keys(),
        key=lambda t: underlying_weights[t],
        reverse=True,
    )

    # Floor-allocate
    allocations: dict[str, int] = {}
    for ticker in sorted_tickers:
        allocations[ticker] = math.floor(total_contracts * underlying_weights[ticker])

    # Distribute remainder to highest-weight underlyings first
    allocated = sum(allocations.values())
    remainder = total_contracts - allocated
    for ticker in sorted_tickers:
        if remainder <= 0:
            break
        allocations[ticker] += 1
        remainder -= 1

    return allocations


def read_portfolio_value_from_csv() -> float | None:
    """Read total account value from latest Fidelity balance CSV.

    Searches for ``notebooks/updates/Balances_for_Account_*.csv``,
    picks the most recently modified file, and extracts the
    "Total account value" row.

    Returns:
        Portfolio value as float, or None if not found / parse error.
    """
    csv_files = sorted(glob(BALANCES_GLOB), key=lambda p: Path(p).stat().st_mtime)
    if not csv_files:
        logger.debug("No Fidelity balance CSV files found at %s", BALANCES_GLOB)
        return None

    latest = csv_files[-1]  # most recent by mtime
    logger.debug("Reading portfolio value from %s", latest)

    try:
        with open(latest) as f:
            for line in f:
                if "total account value" in line.lower():
                    # Format: "Total account value,202688.46,-764.66"
                    parts = line.strip().split(",")
                    if len(parts) >= 2:
                        value_str = parts[1].strip().replace("$", "").replace(",", "")
                        return float(value_str)
    except (OSError, ValueError) as exc:
        logger.warning("Failed to read portfolio value from %s: %s", latest, exc)

    return None


# ---------------------------------------------------------------------------
# HedgeSizer class
# ---------------------------------------------------------------------------


class HedgeSizer:
    """Sizes hedge contracts against a portfolio.

    Constructor accepts a HedgeConfig for underlying weights, OTM/DTE
    targets, and monthly budget.  The three main methods are:

    - ``resolve_portfolio_value`` -- portfolio value cascade
    - ``calculate`` -- contract sizing and allocation
    - ``validate_budget`` -- budget validation with live premiums
    """

    def __init__(self, config: HedgeConfig) -> None:
        """Initialize with validated hedge configuration.

        Args:
            config: HedgeConfig from config_loader.
        """
        self.config = config

    # ----- Portfolio value cascade -----

    def resolve_portfolio_value(
        self,
        cli_value: float | None = None,
    ) -> tuple[float, str]:
        """Resolve portfolio value using the priority cascade.

        Priority:
            1. CLI flag (explicit user override)
            2. Fidelity CSV (latest Balances_for_Account_*.csv)
            3. ValueError if nothing found

        Args:
            cli_value: Portfolio value from CLI ``--portfolio-value`` flag.

        Returns:
            Tuple of (portfolio_value, source_label).

        Raises:
            ValueError: If no portfolio value can be resolved.
        """
        # 1. CLI flag
        if cli_value is not None and cli_value > 0:
            return (cli_value, "cli_flag")

        # 2. Fidelity CSV
        csv_value = read_portfolio_value_from_csv()
        if csv_value is not None:
            return (csv_value, "fidelity_csv")

        # 3. No value found
        msg = (
            "No portfolio value found. Provide --portfolio-value flag or "
            "ensure a Fidelity balance CSV exists at "
            "notebooks/updates/Balances_for_Account_*.csv"
        )
        raise ValueError(msg)

    # ----- Contract sizing and allocation -----

    def calculate(
        self,
        portfolio_value: float,
        underlyings: list[str] | None = None,
        ratio: float | None = None,
    ) -> dict:
        """Size and allocate hedge contracts.

        Args:
            portfolio_value: Total portfolio value in dollars.
            underlyings: Specific tickers to hedge. If None, uses config
                underlying_weights.
            ratio: Dollars of portfolio per contract. Defaults to 50,000.

        Returns:
            Dict with sizing results including total_contracts,
            allocations, coverage info.
        """
        effective_ratio = ratio if ratio is not None else DEFAULT_RATIO_PER_CONTRACT
        total_contracts = calculate_contract_count(portfolio_value, effective_ratio)

        # Determine weights
        if underlyings is not None:
            # Check if all requested underlyings are in config weights
            config_weights = self.config.underlying_weights
            all_in_config = all(t in config_weights for t in underlyings)

            if all_in_config:
                # Use config weights, re-normalized to requested underlyings
                raw = {t: config_weights[t] for t in underlyings}
                weight_sum = sum(raw.values())
                weights = (
                    {t: w / weight_sum for t, w in raw.items()}
                    if weight_sum > 0
                    else {t: 1.0 / len(underlyings) for t in underlyings}
                )
            else:
                # Fall back to equal weighting
                weights = {t: 1.0 / len(underlyings) for t in underlyings}
        else:
            weights = dict(self.config.underlying_weights)

        allocations = allocate_contracts(total_contracts, weights)

        # Notional coverage
        notional_coverage = total_contracts * effective_ratio
        coverage_pct = (
            (notional_coverage / portfolio_value * 100) if portfolio_value > 0 else 0.0
        )

        return {
            "portfolio_value": portfolio_value,
            "ratio_per_contract": effective_ratio,
            "total_contracts": total_contracts,
            "allocations": allocations,
            "weights_used": weights,
            "notional_coverage": notional_coverage,
            "coverage_pct": round(coverage_pct, 2),
            "underlyings": list(weights.keys()),
        }

    # ----- Budget validation -----

    def validate_budget(
        self,
        allocations: dict[str, int],
        config: HedgeConfig,
    ) -> dict:
        """Validate hedge cost against monthly budget using live premiums.

        For each underlying, scans the options chain for current premiums
        and estimates monthly cost.  When cost exceeds budget, warns but
        shows full recommendation (does NOT scale down).

        Args:
            allocations: Mapping of ticker -> contract count.
            config: HedgeConfig with OTM/DTE targets and budget.

        Returns:
            Dict with budget validation results.
        """
        from src.analysis.options_chain_cli import scan_chain

        per_underlying: list[dict] = []
        total_cost = 0.0
        all_estimated = True

        for ticker, contracts in allocations.items():
            if contracts <= 0:
                per_underlying.append(
                    {
                        "ticker": ticker,
                        "contracts": contracts,
                        "estimated_premium": 0.0,
                        "estimated_cost": 0.0,
                    }
                )
                continue

            try:
                # Suppress stderr from scan_chain (same pattern as plan notes)
                stderr_capture = io.StringIO()
                with contextlib.redirect_stderr(stderr_capture):
                    result = scan_chain(
                        ticker=ticker,
                        option_type="put",
                        otm_min=config.min_otm_pct,
                        otm_max=config.max_otm_pct,
                        days_min=config.target_dte_min,
                        days_max=config.target_dte_max,
                        budget=None,
                        target_contracts=1,
                    )

                if result.contracts:
                    premiums = [
                        c.last_price for c in result.contracts if c.last_price > 0
                    ]
                    if premiums:
                        median_premium = statistics.median(premiums)
                        cost = (
                            contracts * median_premium * 100
                        )  # 100 shares per contract
                        per_underlying.append(
                            {
                                "ticker": ticker,
                                "contracts": contracts,
                                "estimated_premium": round(median_premium, 2),
                                "estimated_cost": round(cost, 2),
                            }
                        )
                        total_cost += cost
                        continue

                # No valid premiums found
                per_underlying.append(
                    {
                        "ticker": ticker,
                        "contracts": contracts,
                        "estimated_premium": "estimate_unavailable",
                        "estimated_cost": "estimate_unavailable",
                    }
                )
                all_estimated = False

            except Exception as exc:
                logger.warning("Failed to scan chain for %s: %s", ticker, exc)
                per_underlying.append(
                    {
                        "ticker": ticker,
                        "contracts": contracts,
                        "estimated_premium": "estimate_unavailable",
                        "estimated_cost": "estimate_unavailable",
                    }
                )
                all_estimated = False

        monthly_budget = config.monthly_budget
        utilization_pct = (
            round(total_cost / monthly_budget * 100, 1) if monthly_budget > 0 else 0.0
        )
        within_budget = total_cost <= monthly_budget

        budget_warning: str | None = None
        if not within_budget:
            budget_warning = (
                f"Estimated monthly cost ${total_cost:,.2f} exceeds budget "
                f"${monthly_budget:,.2f} ({utilization_pct:.1f}% utilization). "
                f"Showing full recommendation -- consider adjusting OTM% or "
                f"reducing contract count."
            )

        if not all_estimated:
            note = (
                "Some underlyings could not be priced. "
                "Total cost reflects only priced underlyings."
            )
            if budget_warning:
                budget_warning += f" Note: {note}"
            else:
                budget_warning = note

        return {
            "total_estimated_monthly_cost": round(total_cost, 2),
            "monthly_budget": monthly_budget,
            "utilization_pct": utilization_pct,
            "within_budget": within_budget,
            "per_underlying": per_underlying,
            "budget_warning": budget_warning,
        }


# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------

__all__ = [
    "HedgeSizer",
    "allocate_contracts",
    "calculate_contract_count",
    "read_portfolio_value_from_csv",
]
