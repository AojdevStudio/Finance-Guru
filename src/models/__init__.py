"""Financial models and portfolio optimization.

This package contains all Pydantic models for Finance Guru™.
Models provide type-safe data structures with automatic validation.

Available Models:
    - risk_inputs: Risk calculation models (PriceDataInput, RiskMetricsOutput)
    - momentum_inputs: Momentum indicator models (MomentumDataInput, RSIOutput, etc.)
    - volatility_inputs: Volatility metrics models (VolatilityDataInput, BollingerBandsOutput, etc.)
    - correlation_inputs: Correlation/covariance models (PortfolioPriceData, CorrelationMatrixOutput, etc.)
    - backtest_inputs: Backtesting models (BacktestConfig, TradeSignal, BacktestResults, etc.)
    - moving_avg_inputs: Moving average models (MovingAverageDataInput, MovingAverageOutput, etc.)
    - portfolio_inputs: Portfolio optimization models (PortfolioDataInput, OptimizationOutput, etc.)
    - itc_risk_inputs: ITC Risk API models (ITCRiskRequest, RiskBand, ITCRiskResponse)
    - hedging_inputs: Hedging position models (HedgePosition, RollSuggestion, HedgeSizeRequest)
    - total_return_inputs: Total return models (TotalReturnInput, DividendRecord, TickerReturn)
"""

from src.models.backtest_inputs import (
    BacktestConfig,
    BacktestPerformanceMetrics,
    BacktestResults,
    TradeExecution,
    TradeSignal,
)
from src.models.correlation_inputs import (
    CorrelationConfig,
    CorrelationMatrixOutput,
    CovarianceMatrixOutput,
    PortfolioCorrelationOutput,
    PortfolioPriceData,
    RollingCorrelationOutput,
)
from src.models.hedging_inputs import (
    HedgePosition,
    HedgeSizeRequest,
    RollSuggestion,
)
from src.models.itc_risk_inputs import (
    ITCRiskRequest,
    ITCRiskResponse,
    RiskBand,
)
from src.models.momentum_inputs import (
    AllMomentumOutput,
    MACDOutput,
    MomentumConfig,
    MomentumDataInput,
    ROCOutput,
    RSIOutput,
    StochasticOutput,
    WilliamsROutput,
)
from src.models.moving_avg_inputs import (
    CrossoverOutput,
    MovingAverageAnalysis,
    MovingAverageConfig,
    MovingAverageDataInput,
    MovingAverageOutput,
)
from src.models.options_inputs import (
    BlackScholesInput,
    GreeksOutput,
    ImpliedVolInput,
    ImpliedVolOutput,
    OptionContractData,
    OptionInput,
    OptionsChainOutput,
    PutCallParityInput,
)
from src.models.portfolio_inputs import (
    EfficientFrontierOutput,
    OptimizationConfig,
    OptimizationOutput,
    PortfolioDataInput,
)
from src.models.risk_inputs import (
    PriceDataInput,
    RiskCalculationConfig,
    RiskMetricsOutput,
)
from src.models.total_return_inputs import (
    DividendRecord,
    TickerReturn,
    TotalReturnInput,
)
from src.models.volatility_inputs import (
    ATROutput,
    BollingerBandsOutput,
    HistoricalVolatilityOutput,
    KeltnerChannelsOutput,
    VolatilityConfig,
    VolatilityDataInput,
    VolatilityMetricsOutput,
)

__all__ = [
    # Risk models
    "PriceDataInput",
    "RiskCalculationConfig",
    "RiskMetricsOutput",
    # Momentum models
    "MomentumDataInput",
    "MomentumConfig",
    "RSIOutput",
    "MACDOutput",
    "StochasticOutput",
    "WilliamsROutput",
    "ROCOutput",
    "AllMomentumOutput",
    # Volatility models
    "VolatilityDataInput",
    "VolatilityConfig",
    "BollingerBandsOutput",
    "ATROutput",
    "HistoricalVolatilityOutput",
    "KeltnerChannelsOutput",
    "VolatilityMetricsOutput",
    # Correlation models
    "PortfolioPriceData",
    "CorrelationConfig",
    "CorrelationMatrixOutput",
    "CovarianceMatrixOutput",
    "RollingCorrelationOutput",
    "PortfolioCorrelationOutput",
    # Backtest models
    "BacktestConfig",
    "TradeSignal",
    "TradeExecution",
    "BacktestPerformanceMetrics",
    "BacktestResults",
    # Moving average models
    "MovingAverageDataInput",
    "MovingAverageConfig",
    "MovingAverageOutput",
    "CrossoverOutput",
    "MovingAverageAnalysis",
    # Portfolio optimization models
    "PortfolioDataInput",
    "OptimizationConfig",
    "OptimizationOutput",
    "EfficientFrontierOutput",
    # ITC Risk models
    "ITCRiskRequest",
    "RiskBand",
    "ITCRiskResponse",
    # Options models
    "OptionInput",
    "BlackScholesInput",
    "GreeksOutput",
    "ImpliedVolInput",
    "ImpliedVolOutput",
    "PutCallParityInput",
    "OptionContractData",
    "OptionsChainOutput",
    # Hedging models
    "HedgePosition",
    "RollSuggestion",
    "HedgeSizeRequest",
    # Total return models
    "TotalReturnInput",
    "DividendRecord",
    "TickerReturn",
]
