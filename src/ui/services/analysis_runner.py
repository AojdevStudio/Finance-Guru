"""Analysis Runner Service for Finance Guru™ TUI.

WHAT: Executes analysis tools via direct Python imports (not subprocess)
WHY: 10x faster than subprocess, type-safe, direct access to results
ARCHITECTURE: Service layer that imports and calls existing calculators

Author: Finance Guru™ Development Team
Created: 2025-11-17
"""

from src.analysis.risk_metrics import RiskCalculator
from src.analysis.risk_metrics_cli import fetch_price_data as fetch_risk_data
from src.models.momentum_inputs import MomentumConfig
from src.models.moving_avg_inputs import MovingAverageConfig
from src.models.risk_inputs import RiskCalculationConfig
from src.models.volatility_inputs import VolatilityConfig
from src.utils.momentum import MomentumIndicators

# Import the actual calculation functions
from src.utils.momentum_cli import fetch_momentum_data
from src.utils.moving_averages import MovingAverageCalculator
from src.utils.moving_averages_cli import fetch_ma_data
from src.utils.volatility import calculate_volatility
from src.utils.volatility_cli import fetch_price_data as fetch_volatility_data


class AnalysisRunner:
    """Execute analysis tools via Python imports (not subprocess).

    Provides fast, type-safe access to all Finance Guru analysis tools.
    Each method returns an envelope with ok/error status and data.
    """

    @staticmethod
    def run_momentum(ticker: str, days: int, realtime: bool = True) -> dict:
        """Run momentum analysis for a ticker.

        Args:
            ticker: Stock ticker symbol
            days: Number of days of historical data
            realtime: Include real-time Finnhub data (default: True)

        Returns:
            Envelope dict with {ok, tool, data, error}
        """
        try:
            data = fetch_momentum_data(ticker, days, realtime=realtime)
            config = MomentumConfig()
            calculator = MomentumIndicators(config)
            results = calculator.calculate_all(data)
            return {
                "ok": True,
                "tool": "momentum",
                "data": results.model_dump(),
                "error": None,
            }
        except Exception as e:
            return {
                "ok": False,
                "tool": "momentum",
                "data": None,
                "error": str(e),
            }

    @staticmethod
    def run_volatility(ticker: str, days: int, realtime: bool = True) -> dict:
        """Run volatility analysis for a ticker.

        Args:
            ticker: Stock ticker symbol
            days: Number of days of historical data
            realtime: Include real-time Finnhub data (default: True)

        Returns:
            Envelope dict with {ok, tool, data, error}
        """
        try:
            data = fetch_volatility_data(ticker, days, realtime=realtime)
            config = VolatilityConfig()
            results = calculate_volatility(data, config)
            return {
                "ok": True,
                "tool": "volatility",
                "data": results.model_dump(),
                "error": None,
            }
        except Exception as e:
            return {
                "ok": False,
                "tool": "volatility",
                "data": None,
                "error": str(e),
            }

    @staticmethod
    def run_risk(ticker: str, days: int, realtime: bool = True) -> dict:
        """Run risk metrics analysis for a ticker.

        Args:
            ticker: Stock ticker symbol
            days: Number of days of historical data
            realtime: Include real-time Finnhub data (default: True)

        Returns:
            Envelope dict with {ok, tool, data, error}
        """
        try:
            data = fetch_risk_data(ticker, days, realtime=realtime)
            config = RiskCalculationConfig()
            calculator = RiskCalculator(config)
            results = calculator.calculate_risk_metrics(data)
            return {
                "ok": True,
                "tool": "risk",
                "data": results.model_dump(),
                "error": None,
            }
        except Exception as e:
            return {
                "ok": False,
                "tool": "risk",
                "data": None,
                "error": str(e),
            }

    @staticmethod
    def run_moving_averages(
        ticker: str, days: int, realtime: bool = True, fast: int = 50, slow: int = 200
    ) -> dict:
        """Run moving average analysis for a ticker.

        Args:
            ticker: Stock ticker symbol
            days: Number of days of historical data
            realtime: Include real-time Finnhub data (default: True)
            fast: Fast MA period (default: 50)
            slow: Slow MA period (default: 200)

        Returns:
            Envelope dict with {ok, tool, data, error}
        """
        try:
            data = fetch_ma_data(ticker, days, realtime=realtime)
            config = MovingAverageConfig(
                ma_type="SMA",
                period=fast,
                secondary_ma_type="SMA",
                secondary_period=slow,
            )
            calculator = MovingAverageCalculator(config)
            results = calculator.calculate_with_crossover(data)
            return {
                "ok": True,
                "tool": "moving_averages",
                "data": results.model_dump(),
                "error": None,
            }
        except Exception as e:
            return {
                "ok": False,
                "tool": "moving_averages",
                "data": None,
                "error": str(e),
            }

    @classmethod
    def run_analysis(
        cls, ticker: str, timeframe: int, tools: list[str]
    ) -> dict[str, dict]:
        """Run selected tools and return combined results as envelopes.

        Args:
            ticker: Stock ticker symbol
            timeframe: Number of days of historical data
            tools: List of tool names to run (e.g., ["momentum", "volatility"])

        Returns:
            Dictionary mapping tool names to result envelopes
        """
        results: dict[str, dict] = {}

        if "momentum" in tools:
            results["momentum"] = cls.run_momentum(ticker, timeframe)
        if "volatility" in tools:
            results["volatility"] = cls.run_volatility(ticker, timeframe)
        if "risk" in tools:
            results["risk"] = cls.run_risk(ticker, timeframe)
        if "moving_averages" in tools:
            results["moving_averages"] = cls.run_moving_averages(ticker, timeframe)

        return results
