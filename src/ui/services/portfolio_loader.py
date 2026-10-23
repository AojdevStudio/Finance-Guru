"""Portfolio Loader Service for Finance Guru™ TUI.

WHAT: Loads and parses Fidelity CSV portfolio snapshots
WHY: Provides portfolio data to dashboard header with validation
ARCHITECTURE: Service layer for CSV parsing and Pydantic validation

Author: Finance Guru™ Development Team
Created: 2025-11-17
"""

import math
from datetime import datetime
from pathlib import Path

import pandas as pd
from pydantic import ValidationError

from src.config import FinGuruConfig, InstancePaths
from src.models.dashboard_inputs import HoldingInput, PortfolioSnapshotInput

_FIDELITY_NON_HOLDING_ROWS = frozenset({"pending activity", "pending", "total"})

_NUMBER_NOISE = str.maketrans("", "", "$%+,")


def _normalize_fidelity_symbol(raw_symbol: str) -> str:
    """Strip Fidelity's markers from a symbol, so "SPAXX**" becomes "SPAXX"."""
    return raw_symbol.upper().replace("*", "").strip()


class PortfolioLoader:
    """Loads portfolio data from Fidelity CSV files.

    Handles CSV parsing, validation, and conversion to Pydantic models.
    """

    @staticmethod
    def find_latest_csv() -> Path | None:
        """Find the most recent Portfolio_Positions_*.csv file.

        Returns:
            Path to latest CSV file, or None if no files found
        """
        csv_files = list(
            InstancePaths.resolve().imports.glob("Portfolio_Positions_*.csv")
        )
        if not csv_files:
            return None
        return max(csv_files, key=lambda p: p.stat().st_mtime)

    @staticmethod
    def _parse_number(value: str | float) -> float:
        """Parse a Fidelity currency or percent cell to a float.

        Accepts values such as "$64583.53", "+$935.45", "+1.46%", or a number.
        Percent values stay in percent units (not divided by 100). Blank,
        "--", "ERROR", "N/A", and NaN cells parse to 0.0.

        Args:
            value: Cell value from the CSV.

        Returns:
            Parsed float, or 0.0 when the cell holds no number.
        """
        if pd.isna(value):
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)

        cleaned = str(value).translate(_NUMBER_NOISE).strip()
        try:
            number = float(cleaned)
        except ValueError:
            return 0.0
        return 0.0 if math.isnan(number) else number

    @staticmethod
    def parse_portfolio(csv_path: Path) -> PortfolioSnapshotInput:
        """Parse CSV file into validated PortfolioSnapshotInput.

        Preserve the file's modification time so reloading does not renew its age.

        Args:
            csv_path: Path to Fidelity CSV file

        Returns:
            Validated PortfolioSnapshotInput model

        Raises:
            ValueError: If CSV cannot be read or required columns are missing
        """
        try:
            snapshot_time = datetime.fromtimestamp(csv_path.stat().st_mtime)
            df = pd.read_csv(csv_path)
        except (OSError, ValueError) as e:
            raise ValueError(f"Failed to read CSV: {e}") from e

        required = ["Symbol", "Current Value", "Today's Gain/Loss Dollar"]
        missing = [col for col in required if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        layer_map = FinGuruConfig.load_layers()
        symbol_to_layer = {}
        for layer, symbols in layer_map.items():
            for symbol in symbols:
                symbol_to_layer[str(symbol).upper()] = layer

        holdings = []
        for _, row in df.iterrows():
            raw_symbol = str(row["Symbol"]).strip()
            if not raw_symbol or pd.isna(raw_symbol):
                continue

            if raw_symbol.lower() in _FIDELITY_NON_HOLDING_ROWS:
                continue

            symbol = _normalize_fidelity_symbol(raw_symbol)

            if not symbol:
                continue

            quantity = (
                float(row.get("Quantity", 0))
                if not pd.isna(row.get("Quantity"))
                else 0.0
            )
            current_value = PortfolioLoader._parse_number(row["Current Value"])
            day_change = PortfolioLoader._parse_number(row["Today's Gain/Loss Dollar"])
            day_change_pct = PortfolioLoader._parse_number(
                row.get("Today's Gain/Loss Percent", 0)
            )

            if current_value == 0:
                continue

            try:
                holdings.append(
                    HoldingInput.model_validate(
                        {
                            "symbol": symbol,
                            "quantity": quantity,
                            "current_value": current_value,
                            "day_change": day_change,
                            "day_change_pct": day_change_pct,
                            "layer": symbol_to_layer.get(symbol, "unknown"),
                        }
                    )
                )
            except ValidationError:
                continue

        if not holdings:
            raise ValueError("No valid holdings found in CSV")

        total_value = sum(h.current_value for h in holdings)
        day_change = sum(h.day_change for h in holdings)
        day_change_pct = (day_change / total_value * 100) if total_value else 0.0

        return PortfolioSnapshotInput(
            total_value=total_value,
            day_change=day_change,
            day_change_pct=day_change_pct,
            holdings=holdings,
            timestamp=snapshot_time,
        )

    @classmethod
    def load_latest(cls) -> PortfolioSnapshotInput | None:
        """Convenience method: find latest CSV and parse it.

        Returns:
            PortfolioSnapshotInput if a CSV exists, None if none exists.

        Raises:
            ValueError: If the latest CSV cannot be parsed.
        """
        csv_path = cls.find_latest_csv()
        if not csv_path:
            return None
        return cls.parse_portfolio(csv_path)
