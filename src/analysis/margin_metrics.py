"""Runtime margin-health metrics from the local DB snapshot plus local config.

Personal assumptions come from .env. Current portfolio facts are read from the
local ``family_office.db`` ``balances`` table (``--source db``, the default),
which the sync-first refresh (``src.integrations.refresh_all``) keeps current.
Fallbacks: ``--source snaptrade`` reads the SnapTrade API live, and
``--source csv`` reads the latest Fidelity ``Balances_for_Account_*.csv`` export.
"""

from __future__ import annotations

import csv
import os
import sqlite3
from datetime import date
from glob import glob
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict

from src.config.instance_paths import InstancePaths, load_instance_env

EDUCATIONAL_DISCLAIMER = (
    "For educational purposes only. This is not investment advice. Consult a "
    "licensed financial professional before making financial decisions. Investing "
    "and the use of margin involve risk, including possible loss of principal."
)
SUPPORTED_MARGIN_SOURCES = ("db", "snaptrade", "csv")


class MarginAccountRoutingError(ValueError):
    """Raised when taxable-margin account routing is missing or ambiguous."""


class IncompleteBalanceGenerationError(ValueError):
    """Raised when the latest DB balance generation is incomplete."""


class UnsupportedMarginSourceError(ValueError):
    """Raised when runtime metrics receive an unknown balance source."""


class FidelityBalances(BaseModel):
    """Current broker balances (from a Fidelity CSV or derived from SnapTrade)."""

    model_config = ConfigDict(frozen=True)

    source_file: str
    total_account_value: float
    total_account_day_change: float | None
    margin_buying_power: float | None
    margin_buying_power_day_change: float | None
    net_debit: float
    net_debit_day_change: float | None
    margin_interest_accrued_this_month: float | None


class MarginMetricsInput(BaseModel):
    """Validated inputs for the margin calculator."""

    model_config = ConfigDict(frozen=True)

    balances: FidelityBalances
    annual_rate: float
    jump_alert_threshold: float
    monthly_dividend_income: float | None = None
    today: date | None = None


class MarginMetrics(BaseModel):
    """Derived margin health metrics."""

    model_config = ConfigDict(frozen=True)

    as_of_date: str
    source_file: str
    portfolio_value: float
    margin_balance: float
    margin_buying_power: float | None
    margin_interest_accrued_this_month: float | None
    annual_interest_rate: float
    monthly_interest_cost: float
    annual_interest_cost: float
    monthly_dividend_income: float | None
    coverage_ratio: float | None
    portfolio_margin_ratio: float | None
    jump_alert_threshold: float
    margin_day_change: float | None
    alert_status: str
    months_elapsed: int | None
    disclaimer: str = EDUCATIONAL_DISCLAIMER


def parse_money(value: str | None) -> float | None:
    """Parse Fidelity/env money-like values, including accounting negatives."""
    if value is None:
        return None
    cleaned = value.strip().translate(str.maketrans("", "", "$,+%"))
    if not cleaned or cleaned in {"--", "N/A"}:
        return None
    negative = cleaned.startswith("(") and cleaned.endswith(")")
    cleaned = cleaned[1:-1].strip() if negative else cleaned
    if not cleaned:
        return None
    multiplier = 1_000.0 if cleaned.lower().endswith("k") else 1.0
    cleaned = cleaned[:-1] if multiplier == 1_000.0 else cleaned
    amount = float(cleaned) * multiplier
    return -amount if negative else amount


def parse_rate(value: str | None) -> float:
    """Parse annual interest rate as decimal.

    Accepts decimal form (``0.12``), percent form (``12%``), or whole percent (``12``).
    """
    parsed = parse_money(value)
    if parsed is None:
        msg = "FG_MARGIN_INTEREST_RATE_DECIMAL or --annual-rate is required"
        raise ValueError(msg)
    return parsed / 100 if parsed > 1 else parsed


def balances_glob() -> str:
    """Return the configured Fidelity balances glob."""
    return str(InstancePaths.resolve().imports / "Balances_for_Account_*.csv")


def latest_balances_csv() -> Path:
    """Return the most recently modified Fidelity balances CSV."""
    matches = sorted(glob(balances_glob()), key=lambda p: Path(p).stat().st_mtime)
    if not matches:
        msg = f"No Fidelity balances CSV found matching {balances_glob()}"
        raise FileNotFoundError(msg)
    return Path(matches[-1])


def read_fidelity_balances(path: str | Path | None = None) -> FidelityBalances:
    """Parse current facts from a Fidelity balances CSV."""
    csv_path = Path(path) if path is not None else latest_balances_csv()
    rows: dict[str, list[str]] = {}
    with csv_path.open(newline="") as f:
        for row in csv.reader(f):
            if not row:
                continue
            rows[row[0].strip().lower()] = row

    def cell(label: str, index: int) -> float | None:
        row = rows.get(label)
        if row is None or len(row) <= index:
            return None
        return parse_money(row[index])

    total_account_value = cell("total account value", 1)
    net_debit = cell("net debit", 1)
    if total_account_value is None:
        msg = f"Missing 'Total account value' in {csv_path}"
        raise ValueError(msg)
    if net_debit is None:
        msg = f"Missing 'Net debit' in {csv_path}"
        raise ValueError(msg)

    return FidelityBalances(
        source_file=str(csv_path),
        total_account_value=total_account_value,
        total_account_day_change=cell("total account value", 2),
        margin_buying_power=cell("margin buying power", 1),
        margin_buying_power_day_change=cell("margin buying power", 2),
        net_debit=net_debit,
        net_debit_day_change=cell("net debit", 2),
        margin_interest_accrued_this_month=cell(
            "margin interest accrued this month", 1
        ),
    )


def _broker_balances_from_snaptrade(client: Any, account_id: str) -> FidelityBalances:
    """Adapt live SnapTrade holdings into the broker-balances shape.

    Margin debt is derived (gross market value − net equity); SnapTrade does not
    expose the loan, accrued interest, or day-change directly, so those are None.
    """
    from src.integrations.snaptrade.client import derive_margin_debt

    raw = client.get_balances(account_id)
    first = raw[0] if raw else {}
    equity = client.get_account_equity(account_id)
    if equity is None:
        msg = "SnapTrade did not return account equity"
        raise ValueError(msg)
    margin_debt, _gross = derive_margin_debt(
        client.get_positions(account_id), client.get_options(account_id), equity
    )
    # Fidelity convention: net debit is negative; calculate_margin_metrics abs()-es it.
    net_debit = -margin_debt if margin_debt and margin_debt > 0 else 0.0
    return FidelityBalances(
        source_file=f"snaptrade:{account_id}",
        total_account_value=equity,
        total_account_day_change=None,
        margin_buying_power=first.get("buying_power"),
        margin_buying_power_day_change=None,
        net_debit=net_debit,
        net_debit_day_change=None,
        margin_interest_accrued_this_month=None,
    )


def _resolve_margin_routing(
    config_path: str | Path | None = None,
) -> tuple[str, set[str], Path]:
    """Return the unique taxable-margin account and current generation members."""
    from src.integrations.snaptrade.models import (
        AccountRole,
        SnapTradeAccountsConfig,
    )

    resolved_path = (
        Path(config_path)
        if config_path is not None
        else InstancePaths.resolve().snaptrade_accounts
    )
    config = SnapTradeAccountsConfig.from_path(resolved_path)
    matches = [
        account
        for account in config.accounts
        if account.enabled and account.role == AccountRole.TAXABLE_MARGIN
    ]
    if not matches:
        raise MarginAccountRoutingError(
            "No enabled taxable_margin account found in "
            f"{resolved_path}; configure exactly one account with "
            "role=taxable_margin and enabled=true"
        )
    if len(matches) > 1:
        raise MarginAccountRoutingError(
            f"Found {len(matches)} enabled taxable_margin accounts in "
            f"{resolved_path}; exactly one is required. Disable or reroute all but one"
        )
    generation_account_ids = {
        account.snaptrade_account_id for account in config.syncable
    }
    return matches[0].snaptrade_account_id, generation_account_ids, resolved_path


def read_snaptrade_balances(
    config_path: str | Path | None = None,
) -> FidelityBalances:
    """Pull live balances for the unique enabled taxable-margin account."""
    from src.integrations.snaptrade.client import SnapTradeClientWrapper

    margin_account_id, _generation_account_ids, _resolved_path = (
        _resolve_margin_routing(config_path)
    )
    client = SnapTradeClientWrapper.from_env()
    return _broker_balances_from_snaptrade(client, margin_account_id)


def read_db_balances(
    database_url: str | None = None,
    config_path: str | Path | None = None,
) -> FidelityBalances:
    """Read the latest balances snapshot the refresh wrote to the local DB.

    The sync-first refresh (``src.integrations.refresh_all``) writes one timestamp
    across all enabled+routed accounts. This reader requires that complete
    generation, then selects its unique taxable-margin row. Margin debt is the
    derived loan, so accrued interest and day-change are None.
    """
    from src.config.instance_paths import _db_path

    db = _db_path(database_url)
    if not db.exists():
        msg = (
            f"No local database at {db}; run the sync-first refresh "
            "(uv run python -m src.integrations.refresh_all) before reading margin metrics"
        )
        raise FileNotFoundError(msg)
    margin_account_id, generation_account_ids, resolved_config_path = (
        _resolve_margin_routing(config_path)
    )
    conn = sqlite3.connect(db)
    try:
        conn.row_factory = sqlite3.Row
        latest = conn.execute(
            "SELECT MAX(synced_at) AS synced_at FROM balances"
        ).fetchone()
        latest_synced_at = latest["synced_at"] if latest is not None else None
        if latest_synced_at is None:
            msg = "No balances rows in the local DB; run the sync-first refresh first"
            raise ValueError(msg)
        current_generation_rows = conn.execute(
            "SELECT account_id FROM balances WHERE synced_at = ?",
            (latest_synced_at,),
        ).fetchall()
        current_generation_account_ids = {
            current_row["account_id"] for current_row in current_generation_rows
        }
        if current_generation_account_ids != generation_account_ids:
            raise IncompleteBalanceGenerationError(
                f"Latest balance generation at {latest_synced_at} is incomplete for "
                f"{resolved_config_path}: expected {len(generation_account_ids)} "
                "enabled+routed account rows but found "
                f"{len(current_generation_account_ids)}; run the sync-first refresh "
                "and resolve any per-account sync errors"
            )
        row = conn.execute(
            "SELECT account_equity, buying_power, margin_debt, synced_at "
            "FROM balances WHERE account_id = ? AND synced_at = ?",
            (margin_account_id, latest_synced_at),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        raise IncompleteBalanceGenerationError(
            "The configured taxable_margin account is missing from the latest balance "
            "generation; run the sync-first refresh and resolve any per-account sync errors"
        )
    equity = row["account_equity"]
    if equity is None:
        msg = "Local DB balance row is missing account_equity"
        raise ValueError(msg)
    margin_debt = row["margin_debt"] or 0.0
    # Fidelity convention: net debit is negative; calculate_margin_metrics abs()-es it.
    net_debit = -margin_debt if margin_debt > 0 else 0.0
    return FidelityBalances(
        source_file=f"db:{db}",
        total_account_value=equity,
        total_account_day_change=None,
        margin_buying_power=row["buying_power"],
        margin_buying_power_day_change=None,
        net_debit=net_debit,
        net_debit_day_change=None,
        margin_interest_accrued_this_month=None,
    )


def months_elapsed_since_start(today: date | None = None) -> int | None:
    """Return elapsed strategy months from FG_STRATEGY_START_DATE."""
    raw = os.getenv("FG_STRATEGY_START_DATE")
    if not raw:
        return None
    start = date.fromisoformat(raw)
    current = today or date.today()
    return max(0, (current - start).days // 30)


class MarginMetricsCalculator:
    """Calculate margin-health metrics from validated inputs."""

    def __init__(self, inputs: MarginMetricsInput):
        self.inputs = inputs

    def calculate_all(self) -> MarginMetrics:
        """Return all derived margin metrics."""
        balances = self.inputs.balances
        margin_balance = abs(balances.net_debit)
        monthly_interest_cost = margin_balance * self.inputs.annual_rate / 12
        annual_interest_cost = monthly_interest_cost * 12
        coverage_ratio = (
            self.inputs.monthly_dividend_income / monthly_interest_cost
            if self.inputs.monthly_dividend_income is not None
            and monthly_interest_cost > 0
            else None
        )
        portfolio_margin_ratio = (
            balances.total_account_value / margin_balance
            if margin_balance > 0
            else None
        )

        if portfolio_margin_ratio is None or margin_balance == 0:
            alert_status = "no_margin"
        elif portfolio_margin_ratio < 2.5:
            alert_status = "critical"
        elif portfolio_margin_ratio < 3.0:
            alert_status = "red"
        elif portfolio_margin_ratio < 4.0:
            alert_status = "yellow"
        else:
            alert_status = "green"

        return MarginMetrics(
            as_of_date=(self.inputs.today or date.today()).isoformat(),
            source_file=balances.source_file,
            portfolio_value=round(balances.total_account_value, 2),
            margin_balance=round(margin_balance, 2),
            margin_buying_power=balances.margin_buying_power,
            margin_interest_accrued_this_month=(
                balances.margin_interest_accrued_this_month
            ),
            annual_interest_rate=self.inputs.annual_rate,
            monthly_interest_cost=round(monthly_interest_cost, 2),
            annual_interest_cost=round(annual_interest_cost, 2),
            monthly_dividend_income=self.inputs.monthly_dividend_income,
            coverage_ratio=(
                round(coverage_ratio, 2) if coverage_ratio is not None else None
            ),
            portfolio_margin_ratio=(
                round(portfolio_margin_ratio, 2)
                if portfolio_margin_ratio is not None
                else None
            ),
            jump_alert_threshold=self.inputs.jump_alert_threshold,
            margin_day_change=balances.net_debit_day_change,
            alert_status=alert_status,
            months_elapsed=months_elapsed_since_start(self.inputs.today),
        )


def calculate_margin_metrics(
    balances: FidelityBalances,
    *,
    annual_rate: float,
    jump_alert_threshold: float,
    monthly_dividend_income: float | None = None,
    today: date | None = None,
) -> MarginMetrics:
    """Calculate live margin metrics through validated models."""
    inputs = MarginMetricsInput(
        balances=balances,
        annual_rate=annual_rate,
        jump_alert_threshold=jump_alert_threshold,
        monthly_dividend_income=monthly_dividend_income,
        today=today,
    )
    return MarginMetricsCalculator(inputs).calculate_all()


def metrics_from_runtime(
    *,
    source: str = "db",
    csv_path: str | Path | None = None,
    annual_rate: float | None = None,
    monthly_dividend_income: float | None = None,
    today: date | None = None,
) -> MarginMetrics:
    """Load .env/config + current balances and return derived metrics.

    Source is the local DB snapshot by default (the sync-first store);
    ``source="snaptrade"`` reads the SnapTrade API live, and ``source="csv"``
    (or passing ``csv_path``) reads the legacy Fidelity balances CSV instead.
    """
    if source not in SUPPORTED_MARGIN_SOURCES:
        supported = ", ".join(SUPPORTED_MARGIN_SOURCES)
        raise UnsupportedMarginSourceError(
            f"Unsupported margin source {source!r}; expected one of: {supported}"
        )
    load_instance_env(InstancePaths.resolve(), override=False)
    if csv_path is not None or source == "csv":
        balances = read_fidelity_balances(csv_path)
    elif source == "snaptrade":
        balances = read_snaptrade_balances()
    else:
        balances = read_db_balances()
    resolved_rate = annual_rate or parse_rate(
        os.getenv("FG_MARGIN_INTEREST_RATE_DECIMAL")
        or os.getenv("FG_MARGIN_INTEREST_RATE")
    )
    threshold = parse_money(os.getenv("FG_MARGIN_JUMP_ALERT_THRESHOLD"))
    if threshold is None:
        msg = "FG_MARGIN_JUMP_ALERT_THRESHOLD is required"
        raise ValueError(msg)
    resolved_dividend = monthly_dividend_income
    if resolved_dividend is None:
        resolved_dividend = parse_money(os.getenv("FG_DIVIDEND_MONTHLY_INCOME", ""))
    return calculate_margin_metrics(
        balances,
        annual_rate=resolved_rate,
        jump_alert_threshold=threshold,
        monthly_dividend_income=resolved_dividend,
        today=today,
    )


def main(argv: list[str] | None = None) -> int:
    """Run the compatibility CLI entrypoint."""
    from src.analysis.margin_metrics_cli import main as cli_main

    return cli_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
