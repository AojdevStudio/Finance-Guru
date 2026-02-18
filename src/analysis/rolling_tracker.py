"""Rolling Tracker Calculator for Finance Guru.

This module implements the RollingTracker calculator class (Layer 2) that manages
options hedge positions: status display with live pricing, roll suggestions, roll
logging, and history tracking.

ARCHITECTURE NOTE:
This is Layer 2 of our 3-layer architecture:
    Layer 1: Pydantic Models (hedging_inputs.py) - Data validation
    Layer 2: Calculator Classes (THIS FILE) - Business logic
    Layer 3: CLI Interface - Agent integration

EDUCATIONAL CONTEXT:
Rolling is the process of closing an expiring options position and opening a new
one with a later expiration date, potentially at a different strike price. This
maintains continuous portfolio protection without coverage gaps.

AMERICAN-STYLE OPTIONS LIMITATION (BS-01):
The Black-Scholes model prices European options (exercisable only at expiry).
Most US equity options are American-style (exercisable any time before expiry).
For deep in-the-money puts, the American option can be worth MORE than Black-Scholes
predicts because early exercise is sometimes optimal. We apply an intrinsic value
floor: the option price is at least max(strike - spot, 0) for puts. This is a
pragmatic approximation, not a full American pricing model (like binomial trees).

DISCLAIMER:
For educational purposes only. Not investment advice. Options involve significant
risk. Consult a qualified financial professional before trading options.

Author: Finance Guru Development Team
Created: 2026-02-18
"""

from __future__ import annotations

import contextlib
import io
import logging
import sys
from datetime import date
from pathlib import Path

import yaml

from src.analysis.options import price_option
from src.analysis.options_chain_cli import scan_chain
from src.config.config_loader import HedgeConfig
from src.models.hedging_inputs import HedgePosition
from src.models.options_inputs import OptionContractData
from src.utils.market_data import get_prices

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent
"""Project root directory (three levels up from src/analysis/rolling_tracker.py)."""

HEDGING_DIR = PROJECT_ROOT / "fin-guru-private" / "hedging"
"""Directory containing hedge position and roll history YAML files."""

# Default parameters for pricing
DEFAULT_IV = 0.30
"""Default implied volatility used when live IV is unavailable."""

DEFAULT_RISK_FREE_RATE = 0.045
"""Default risk-free rate for Black-Scholes pricing."""


def scan_chain_quiet(
    ticker: str,
    option_type: str,
    otm_min: float,
    otm_max: float,
    days_min: int,
    days_max: int,
    budget: float | None = None,
    target_contracts: int = 1,
):
    """Wrap scan_chain() with stderr suppressed.

    The options_chain_cli.scan_chain() function prints ~12 status messages to
    stderr during execution. This wrapper suppresses all stderr output while
    preserving the return value. Useful for programmatic callers (like
    suggest_rolls) that don't need progress chatter.

    Args:
        ticker: Stock ticker symbol.
        option_type: "call" or "put".
        otm_min: Minimum OTM percentage.
        otm_max: Maximum OTM percentage.
        days_min: Minimum days to expiry.
        days_max: Maximum days to expiry.
        budget: Budget for position sizing (None to skip).
        target_contracts: Target number of contracts.

    Returns:
        OptionsChainOutput with all matching contracts.
    """
    with contextlib.redirect_stderr(io.StringIO()):
        return scan_chain(
            ticker=ticker,
            option_type=option_type,
            otm_min=otm_min,
            otm_max=otm_max,
            days_min=days_min,
            days_max=days_max,
            budget=budget,
            target_contracts=target_contracts,
        )


def price_american_put(
    spot: float,
    strike: float,
    days_to_expiry: int,
    volatility: float,
    risk_free_rate: float = DEFAULT_RISK_FREE_RATE,
    dividend_yield: float = 0.0,
) -> float:
    """Price a put option with an intrinsic value floor for American-style options.

    Black-Scholes prices European options which cannot be exercised early. For
    American-style puts (the standard on US equity exchanges), early exercise
    can be optimal when the option is deep in-the-money. The BS price can
    therefore _undervalue_ the option.

    This function applies a pragmatic floor: the returned price is at least the
    intrinsic value ``max(strike - spot, 0)``. This captures the minimum value
    an American put holder can realize by exercising immediately.

    Reference: BS-01 -- see module docstring for full context.

    Args:
        spot: Current underlying price.
        strike: Put strike price.
        days_to_expiry: Days until expiration.
        volatility: Annualized implied volatility (e.g. 0.30 = 30%).
        risk_free_rate: Annual risk-free rate (default 4.5%).
        dividend_yield: Annual dividend yield (default 0%).

    Returns:
        Estimated American put price (>= intrinsic value).
    """
    intrinsic_value = max(strike - spot, 0.0)

    try:
        greeks = price_option(
            spot=spot,
            strike=strike,
            days_to_expiry=days_to_expiry,
            volatility=volatility,
            option_type="put",
            risk_free_rate=risk_free_rate,
            dividend_yield=dividend_yield,
        )
        return max(greeks.option_price, intrinsic_value)
    except Exception:
        # Deep ITM puts can cause GreeksOutput validation errors (negative
        # time_value, positive theta) because BS assumes European exercise.
        # Fall back to intrinsic value -- the minimum an American holder
        # can realize by exercising immediately.
        logger.debug(
            "BS pricing failed for put (spot=%.2f, strike=%.2f), "
            "using intrinsic value %.2f",
            spot,
            strike,
            intrinsic_value,
        )
        return intrinsic_value


def load_positions() -> list[HedgePosition]:
    """Load active hedge positions from positions.yaml.

    Reads ``fin-guru-private/hedging/positions.yaml`` and parses each entry
    through the HedgePosition Pydantic model. Invalid entries are skipped with
    a stderr warning (Pitfall 5: empty YAML returns None, not {}).

    Returns:
        List of validated HedgePosition instances.
    """
    positions_path = HEDGING_DIR / "positions.yaml"
    if not positions_path.exists():
        return []

    try:
        with open(positions_path) as f:
            data = yaml.safe_load(f) or {}
    except Exception:
        logger.warning("Failed to parse %s, returning empty list", positions_path)
        return []

    raw_positions = data.get("positions", [])
    if not isinstance(raw_positions, list):
        return []

    positions: list[HedgePosition] = []
    for entry in raw_positions:
        if not isinstance(entry, dict):
            continue
        try:
            positions.append(HedgePosition(**entry))
        except Exception as e:
            print(
                f"Warning: skipping invalid position entry: {e}",
                file=sys.stderr,
            )
    return positions


def save_positions(positions: list[HedgePosition]) -> None:
    """Save active hedge positions to positions.yaml.

    Uses ``model_dump(mode="json")`` for date serialization (dates become
    ISO-format strings). Creates parent directories if needed.

    Args:
        positions: List of HedgePosition instances to persist.
    """
    positions_path = HEDGING_DIR / "positions.yaml"
    positions_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "positions": [p.model_dump(mode="json") for p in positions],
    }
    with open(positions_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def load_roll_history() -> list[dict]:
    """Load roll history from roll-history.yaml.

    Returns:
        List of roll record dicts. Empty list if file doesn't exist or is empty.
    """
    history_path = HEDGING_DIR / "roll-history.yaml"
    if not history_path.exists():
        return []

    try:
        with open(history_path) as f:
            data = yaml.safe_load(f) or {}
    except Exception:
        logger.warning("Failed to parse %s, returning empty list", history_path)
        return []

    rolls = data.get("rolls", [])
    if not isinstance(rolls, list):
        return []
    return rolls


def save_roll_history(history: list[dict]) -> None:
    """Save roll history to roll-history.yaml.

    Args:
        history: List of roll record dicts to persist.
    """
    history_path = HEDGING_DIR / "roll-history.yaml"
    history_path.parent.mkdir(parents=True, exist_ok=True)

    data = {"rolls": history}
    with open(history_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def _dte_status(dte: int | None) -> tuple[str, str]:
    """Determine status label and color from days-to-expiry.

    Args:
        dte: Days to expiry (None for positions without expiry).

    Returns:
        Tuple of (status_label, dte_color).
    """
    if dte is None:
        return "OK", "green"
    if dte <= 7:
        return "ROLL", "red"
    if dte <= 14:
        return "EXPIRING", "yellow"
    return "OK", "green"


def _rank_contract_score(
    contract: OptionContractData, otm_mid: float, dte_mid: float
) -> float:
    """Score a contract by proximity to target OTM% and DTE midpoints.

    Lower score = better match.

    Args:
        contract: OptionContractData from scan results.
        otm_mid: Midpoint of target OTM range.
        dte_mid: Midpoint of target DTE range.

    Returns:
        Combined distance score.
    """
    otm_dist = abs(contract.otm_pct - otm_mid)
    dte_dist = abs(contract.days_to_expiry - dte_mid)
    # Normalize DTE distance to same scale as OTM%
    return otm_dist + (dte_dist / 10.0)


class RollingTracker:
    """Options hedge position manager with live pricing and roll suggestions.

    WHAT: Manages the lifecycle of hedge positions -- status, suggestions,
          execution, and history.
    WHY: Centralizes all position management logic so the CLI (Layer 3) only
         handles I/O and formatting.
    HOW: Reads positions from YAML, enriches with live pricing, identifies
         candidates for rolling, and logs executed rolls.

    USAGE:
        from src.config.config_loader import load_hedge_config
        from src.analysis.rolling_tracker import RollingTracker

        config = load_hedge_config()
        tracker = RollingTracker(config)

        # View current positions with live pricing
        status = tracker.get_status()

        # Get roll suggestions for expiring positions
        suggestions = tracker.suggest_rolls()

        # Execute a roll
        result = tracker.log_roll("QQQ", 420.0, date(2026, 6, 19), 8.50)

        # View roll history
        history = tracker.get_history()
    """

    def __init__(self, config: HedgeConfig) -> None:
        """Initialize RollingTracker with hedge configuration.

        Args:
            config: Validated HedgeConfig with roll window, OTM targets, etc.
        """
        self.config = config

    def get_status(self) -> dict:
        """Get enriched status of all active hedge positions.

        Loads positions from YAML, auto-archives expired positions, fetches
        live pricing for remaining positions, and calculates P&L.

        Auto-archival: Positions with ``expiry < today`` are moved to
        roll-history.yaml with reason "expired" and removed from active
        positions.

        For puts, current value is estimated using ``price_american_put()``
        with a default IV of 30%. For inverse ETFs, current value is the
        live share price times quantity.

        Returns:
            Dict with:
                - "positions": list of enriched position dicts
                - "summary": dict with total_hedge_cost, total_current_value,
                  total_pnl, position_count
        """
        positions = load_positions()
        today = date.today()

        # --- Auto-archive expired positions ---
        active: list[HedgePosition] = []
        expired: list[HedgePosition] = []
        for pos in positions:
            if pos.expiry is not None and pos.expiry < today:
                expired.append(pos)
            else:
                active.append(pos)

        if expired:
            history = load_roll_history()
            for pos in expired:
                history.append(
                    {
                        "roll_date": today.isoformat(),
                        "old_position": pos.model_dump(mode="json"),
                        "reason": "expired",
                    }
                )
            save_roll_history(history)
            save_positions(active)

        # --- Enrich active positions ---
        enriched: list[dict] = []
        total_hedge_cost = 0.0
        total_current_value = 0.0

        for pos in active:
            result = self._enrich_position(pos, today)
            enriched.append(result["position"])
            total_hedge_cost += result["entry_cost"]
            total_current_value += result["current_value"]

        summary = {
            "total_hedge_cost": round(total_hedge_cost, 2),
            "total_current_value": round(total_current_value, 2),
            "total_pnl": round(total_current_value - total_hedge_cost, 2),
            "position_count": len(enriched),
        }

        return {"positions": enriched, "summary": summary}

    def _enrich_position(self, pos: HedgePosition, today: date) -> dict:
        """Enrich a single position with live pricing, DTE, P&L, and status.

        Args:
            pos: The hedge position to enrich.
            today: Reference date for DTE calculation.

        Returns:
            Dict with keys: position (enriched dict), entry_cost, current_value.
        """
        # Calculate DTE
        dte: int | None = None
        if pos.expiry is not None:
            dte = (pos.expiry - today).days

        # Calculate entry cost
        if pos.hedge_type == "put":
            entry_cost = pos.premium_paid * 100 * pos.quantity
        else:
            entry_cost = pos.premium_paid * pos.quantity

        # Fetch live pricing
        current_value = entry_cost  # fallback
        pricing_error = False

        try:
            price_data = get_prices(pos.ticker)
            spot = price_data[pos.ticker].price
            current_value = self._price_position(pos, spot, dte)
        except Exception as e:
            logger.warning(
                "Pricing error for %s: %s -- using entry cost as fallback",
                pos.ticker,
                e,
            )
            pricing_error = True

        pnl = current_value - entry_cost
        status_label, dte_color = _dte_status(dte)

        position_dict = {
            "ticker": pos.ticker,
            "hedge_type": pos.hedge_type,
            "strike": pos.strike,
            "expiry": pos.expiry.isoformat() if pos.expiry else None,
            "dte": dte,
            "entry_premium": pos.premium_paid,
            "current_value": round(current_value, 2),
            "p_and_l": round(pnl, 2),
            "status": status_label,
            "dte_color": dte_color,
            "contract_symbol": pos.contract_symbol,
            "quantity": pos.quantity,
        }
        if pricing_error:
            position_dict["pricing_error"] = True

        return {
            "position": position_dict,
            "entry_cost": entry_cost,
            "current_value": current_value,
        }

    @staticmethod
    def _price_position(pos: HedgePosition, spot: float, dte: int | None) -> float:
        """Calculate current market value of a position.

        Args:
            pos: The hedge position.
            spot: Current underlying/ETF spot price.
            dte: Days to expiry (None for inverse ETFs).

        Returns:
            Current total value of the position.
        """
        if pos.hedge_type == "put" and dte is not None and dte > 0:
            per_contract = price_american_put(
                spot=spot,
                strike=pos.strike,  # type: ignore[arg-type]
                days_to_expiry=dte,
                volatility=DEFAULT_IV,
            )
            return per_contract * 100 * pos.quantity
        if pos.hedge_type == "inverse_etf":
            return spot * pos.quantity
        if pos.hedge_type == "put":
            # At or past expiry -- value is intrinsic only
            intrinsic = max((pos.strike or 0.0) - spot, 0.0)
            return intrinsic * 100 * pos.quantity
        return 0.0

    def suggest_rolls(self) -> list[dict]:
        """Identify expiring put positions and suggest replacement contracts.

        Filters active put positions to those with DTE <= 7 (fixed roll window,
        LOCKED decision). For each, scans the options chain using the config's
        OTM and DTE targets, ranks by proximity to target midpoints, and picks
        the top-1 best match.

        Returns:
            List of dicts, each containing:
                - current_position: summary of the expiring position
                - suggested: best replacement contract data (or None)
                - estimated_roll_cost: new_premium - remaining_value
                - new_premium: premium of suggested contract
                - remaining_value: current value of expiring position
                - message: status message (e.g., "no candidates found")
        """
        positions = load_positions()
        today = date.today()

        suggestions: list[dict] = []

        for pos in positions:
            # Only consider puts with expiry within 7 days
            if pos.hedge_type != "put":
                continue
            if pos.expiry is None:
                continue

            dte = (pos.expiry - today).days
            if dte > 7:
                continue

            # Calculate remaining value of current position
            remaining_value = 0.0
            try:
                price_data = get_prices(pos.ticker)
                spot = price_data[pos.ticker].price
                if dte > 0:
                    remaining_value = price_american_put(
                        spot=spot,
                        strike=pos.strike,  # type: ignore[arg-type]
                        days_to_expiry=dte,
                        volatility=DEFAULT_IV,
                    )
                else:
                    remaining_value = max((pos.strike or 0.0) - spot, 0.0)
            except Exception as e:
                logger.warning(
                    "Could not price current position for %s: %s", pos.ticker, e
                )

            # Scan for replacement contracts
            otm_mid = (self.config.min_otm_pct + self.config.max_otm_pct) / 2
            dte_mid = (self.config.target_dte_min + self.config.target_dte_max) / 2

            current_info = {
                "ticker": pos.ticker,
                "strike": pos.strike,
                "expiry": pos.expiry.isoformat(),
                "dte": dte,
                "contract_symbol": pos.contract_symbol,
                "quantity": pos.quantity,
            }

            try:
                result = scan_chain_quiet(
                    ticker=pos.ticker,
                    option_type="put",
                    otm_min=self.config.min_otm_pct,
                    otm_max=self.config.max_otm_pct,
                    days_min=self.config.target_dte_min,
                    days_max=self.config.target_dte_max,
                    budget=None,
                    target_contracts=pos.quantity,
                )

                if not result.contracts:
                    suggestions.append(
                        {
                            "current_position": current_info,
                            "suggested": None,
                            "estimated_roll_cost": None,
                            "new_premium": None,
                            "remaining_value": round(remaining_value, 2),
                            "message": "no candidates found",
                        }
                    )
                    continue

                # Rank by proximity to target midpoints
                ranked = sorted(
                    result.contracts,
                    key=lambda c: _rank_contract_score(c, otm_mid, dte_mid),
                )
                best = ranked[0]

                new_premium = best.last_price if best.last_price > 0 else best.mid
                estimated_roll_cost = new_premium - remaining_value

                suggestions.append(
                    {
                        "current_position": current_info,
                        "suggested": best.model_dump(mode="json"),
                        "estimated_roll_cost": round(estimated_roll_cost, 2),
                        "new_premium": round(new_premium, 2),
                        "remaining_value": round(remaining_value, 2),
                        "message": "candidate found",
                    }
                )

            except Exception as e:
                logger.warning("Chain scan failed for %s: %s", pos.ticker, e)
                suggestions.append(
                    {
                        "current_position": current_info,
                        "suggested": None,
                        "estimated_roll_cost": None,
                        "new_premium": None,
                        "remaining_value": round(remaining_value, 2),
                        "message": f"scan error: {e}",
                    }
                )

        return suggestions

    def log_roll(
        self,
        ticker: str,
        new_strike: float,
        new_expiry: date,
        new_premium: float,
    ) -> dict:
        """Execute a roll: archive old position and create new one.

        Finds the active put position matching ``ticker`` (auto-detect from
        positions.yaml, LOCKED decision), archives it to roll-history.yaml,
        and replaces it with a new position using the provided parameters.
        The new position inherits the same quantity as the old one.

        Args:
            ticker: Ticker of the position to roll (must match an active put).
            new_strike: Strike price for the new position.
            new_expiry: Expiration date for the new position.
            new_premium: Premium paid per contract for the new position.

        Returns:
            Dict with old_position, new_position, and roll_date.

        Raises:
            ValueError: If no active put position matches the ticker.
        """
        positions = load_positions()
        today = date.today()

        # Find matching put position
        match_idx: int | None = None
        for i, pos in enumerate(positions):
            if pos.ticker == ticker and pos.hedge_type == "put":
                match_idx = i
                break

        if match_idx is None:
            raise ValueError(
                f"No active put position found for ticker '{ticker}'. "
                f"Active positions: {[p.ticker for p in positions]}"
            )

        old_pos = positions[match_idx]

        # Archive old position
        history = load_roll_history()
        history.append(
            {
                "roll_date": today.isoformat(),
                "old_position": old_pos.model_dump(mode="json"),
                "reason": "rolled",
            }
        )
        save_roll_history(history)

        # Create new position
        new_pos = HedgePosition(
            ticker=ticker,
            hedge_type="put",
            strike=new_strike,
            expiry=new_expiry,
            quantity=old_pos.quantity,
            premium_paid=new_premium,
            entry_date=today,
        )

        # Replace old with new
        positions[match_idx] = new_pos
        save_positions(positions)

        return {
            "old_position": old_pos.model_dump(mode="json"),
            "new_position": new_pos.model_dump(mode="json"),
            "roll_date": today.isoformat(),
        }

    def get_history(self) -> list[dict]:
        """Return roll history from roll-history.yaml.

        Returns:
            List of roll record dicts. Empty list if no history exists.
        """
        return load_roll_history()


# Type exports
__all__ = [
    "RollingTracker",
    "scan_chain_quiet",
    "price_american_put",
]
