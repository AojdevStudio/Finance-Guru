"""Portfolio Loader Service for Finance Guru™ TUI.

WHAT: Loads and parses Fidelity CSV portfolio snapshots
WHY: Provides portfolio data to dashboard header with validation
ARCHITECTURE: Service layer for CSV parsing and Pydantic validation

Author: Finance Guru™ Development Team
Created: 2025-11-17
"""

from datetime import datetime
from pathlib import Path

import pandas as pd

from src.config import FinGuruConfig
from src.models.dashboard_inputs import HoldingInput, PortfolioSnapshotInput


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
        csv_files = list(FinGuruConfig.PORTFOLIO_DIR.glob("Portfolio_Positions_*.csv"))
        if not csv_files:
            return None
        return max(csv_files, key=lambda p: p.stat().st_mtime)

    @staticmethod
    def _parse_currency(value: str | float) -> float:
        """Parse currency string (e.g., "$64583.53" or "+$935.45") to float.

        Handles ERROR, N/A, NaN, and other non-numeric values gracefully.

        Args:
            value: Currency string or already a float

        Returns:
            Float value (0.0 for unparseable values)
        """
        # Check for NaN first (before isinstance check)
        if pd.isna(value):
            return 0.0

        if isinstance(value, (int, float)):
            # Handle float('nan') case
            import math

            if math.isnan(value):
                return 0.0
            return float(value)

        # Remove $, +, -, commas, and whitespace
        cleaned = str(value).replace("$", "").replace("+", "").replace(",", "").strip()

        # Handle special non-numeric values
        if (
            not cleaned
            or cleaned == "-"
            or cleaned.upper() in ["ERROR", "N/A", "NA", "NAN", "--"]
        ):
            return 0.0

        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    @staticmethod
    def _parse_percent(value: str | float) -> float:
        """Parse percentage string (e.g., "+1.46%" or "-0.10%") to float.

        Handles ERROR, N/A, NaN, and other non-numeric values gracefully.

        Args:
            value: Percentage string or already a float

        Returns:
            Float percentage value (not divided by 100)
        """
        # Check for NaN first (before isinstance check)
        if pd.isna(value):
            return 0.0

        if isinstance(value, (int, float)):
            # Handle float('nan') case
            import math

            if math.isnan(value):
                return 0.0
            return float(value)

        # Remove %, +, -, commas, and whitespace
        cleaned = str(value).replace("%", "").replace("+", "").replace(",", "").strip()

        # Handle special non-numeric values
        if (
            not cleaned
            or cleaned == "-"
            or cleaned.upper() in ["ERROR", "N/A", "NA", "NAN", "--"]
        ):
            return 0.0

        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    @staticmethod
    def parse_portfolio(csv_path: Path) -> PortfolioSnapshotInput:
        """Parse CSV file into validated PortfolioSnapshotInput.

        Args:
            csv_path: Path to Fidelity CSV file

        Returns:
            Validated PortfolioSnapshotInput model

        Raises:
            ValueError: If CSV cannot be read or required columns are missing
        """
        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            raise ValueError(f"Failed to read CSV: {e}") from e

        # Validate columns
        required = ["Symbol", "Current Value", "Today's Gain/Loss Dollar"]
        missing = [col for col in required if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        # Load layer mappings
        layer_map = FinGuruConfig.load_layers()
        symbol_to_layer = {}
        for layer, symbols in layer_map.items():
            for symbol in symbols:
                symbol_to_layer[str(symbol).upper()] = layer

        # Parse holdings (Pydantic will validate automatically)
        holdings = []
        for _, row in df.iterrows():
            raw_symbol = str(row["Symbol"]).strip()
            if not raw_symbol or pd.isna(raw_symbol):
                continue

            # Skip Fidelity metadata rows
            if raw_symbol.lower() in ["pending activity", "pending", "total"]:
                continue

            # Clean symbol: remove special characters, keep only alphanumeric
            # Some symbols like "SPAXX**" need to be cleaned to "SPAXX"
            symbol = "".join(c for c in raw_symbol.upper() if c.isalnum())

            # Skip if symbol is empty after cleaning
            if not symbol:
                continue

            # Parse values, handling currency and percentage formats
            quantity = (
                float(row.get("Quantity", 0))
                if not pd.isna(row.get("Quantity"))
                else 0.0
            )
            current_value = PortfolioLoader._parse_currency(row["Current Value"])
            day_change = PortfolioLoader._parse_currency(
                row["Today's Gain/Loss Dollar"]
            )
            day_change_pct = PortfolioLoader._parse_percent(
                row.get("Today's Gain/Loss Percent", 0)
            )

            # Skip holdings with zero value (cash, etc.)
            if current_value == 0:
                continue

            # Skip if symbol doesn't pass Pydantic validation (e.g., contains numbers)
            # We'll catch ValidationError and skip invalid symbols
            try:
                holdings.append(
                    HoldingInput(
                        symbol=symbol,
                        quantity=quantity,
                        current_value=current_value,
                        day_change=day_change,
                        day_change_pct=day_change_pct,
                        layer=symbol_to_layer.get(symbol, "unknown"),
                    )
                )
            except Exception:
                # Skip invalid symbols (e.g., cash positions with numbers)
                continue

        if not holdings:
            raise ValueError("No valid holdings found in CSV")

        # Calculate totals
        total_value = sum(h.current_value for h in holdings)
        day_change = sum(h.day_change for h in holdings)
        day_change_pct = (day_change / total_value * 100) if total_value else 0.0

        # Pydantic model validates all inputs automatically
        return PortfolioSnapshotInput(
            total_value=total_value,
            day_change=day_change,
            day_change_pct=day_change_pct,
            holdings=holdings,
            timestamp=datetime.now(),
        )

    @classmethod
    def load_latest(cls) -> PortfolioSnapshotInput | None:
        """Convenience method: find latest CSV and parse it.

        Returns:
            PortfolioSnapshotInput if CSV found and parsed successfully, None otherwise
        """
        csv_path = cls.find_latest_csv()
        if not csv_path:
            return None
        try:
            return cls.parse_portfolio(csv_path)
        except Exception:
            # Return None on parse errors - app will handle gracefully
            return None
