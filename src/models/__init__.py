"""
Financial models and portfolio optimization.

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
"""

from src.models.risk_inputs import (
    PriceDataInput,
    RiskCalculationConfig,
    RiskMetricsOutput,
)

from src.models.momentum_inputs import (
    MomentumDataInput,
    MomentumConfig,
    RSIOutput,
    MACDOutput,
    StochasticOutput,
    WilliamsROutput,
    ROCOutput,
    AllMomentumOutput,
)

from src.models.volatility_inputs import (
    VolatilityDataInput,
    VolatilityConfig,
    BollingerBandsOutput,
    ATROutput,
    HistoricalVolatilityOutput,
    KeltnerChannelsOutput,
    VolatilityMetricsOutput,
)

from src.models.correlation_inputs import (
    PortfolioPriceData,
    CorrelationConfig,
    CorrelationMatrixOutput,
    CovarianceMatrixOutput,
    RollingCorrelationOutput,
    PortfolioCorrelationOutput,
)

from src.models.backtest_inputs import (
    BacktestConfig,
    TradeSignal,
    TradeExecution,
    BacktestPerformanceMetrics,
    BacktestResults,
)

from src.models.moving_avg_inputs import (
    MovingAverageDataInput,
    MovingAverageConfig,
    MovingAverageOutput,
    CrossoverOutput,
    MovingAverageAnalysis,
)

from src.models.portfolio_inputs import (
    PortfolioDataInput,
    OptimizationConfig,
    OptimizationOutput,
    EfficientFrontierOutput,
)

from src.models.itc_risk_inputs import (
    ITCRiskRequest,
    RiskBand,
    ITCRiskResponse,
)

from src.models.transaction_inputs import (
    TransactionType,
    ExpenseCategory,
    RawFidelityTransaction,
    ClassifiedTransaction,
    TransactionBatch,
    MonthlyBudgetSummary,
    ParserConfig,
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
    # Transaction models
    "TransactionType",
    "ExpenseCategory",
    "RawFidelityTransaction",
    "ClassifiedTransaction",
    "TransactionBatch",
    "MonthlyBudgetSummary",
    "ParserConfig",
]
