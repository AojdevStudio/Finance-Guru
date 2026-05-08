"""Runtime margin-health metrics from live broker balances plus local config.

Personal assumptions come from .env. Current portfolio facts come from the latest
Fidelity ``Balances_for_Account_*.csv`` export.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from dataclasses import asdict, dataclass
from datetime import date
from glob import glob
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

DEFAULT_PORTFOLIO_DIR = Path("notebooks/updates")


@dataclass(frozen=True)
class FidelityBalances:
    """Current values parsed from a Fidelity balances CSV."""

    source_file: str
    total_account_value: float
    total_account_day_change: float | None
    margin_buying_power: float | None
    margin_buying_power_day_change: float | None
    net_debit: float
    net_debit_day_change: float | None
    margin_interest_accrued_this_month: float | None


@dataclass(frozen=True)
class MarginMetrics:
    """Derived margin health metrics."""

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


def parse_money(value: str | None) -> float | None:
    """Parse Fidelity/env money-like values into floats."""
    if value is None:
        return None
    cleaned = (
        value.strip()
        .replace("$", "")
        .replace(",", "")
        .replace("+", "")
        .replace("%", "")
    )
    if not cleaned or cleaned in {"--", "N/A"}:
        return None
    multiplier = 1.0
    if cleaned.lower().endswith("k"):
        multiplier = 1_000.0
        cleaned = cleaned[:-1]
    return float(cleaned) * multiplier


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
    portfolio_dir = Path(
        os.getenv("FIN_GURU_PORTFOLIO_DIR", str(DEFAULT_PORTFOLIO_DIR))
    )
    return str(portfolio_dir / "Balances_for_Account_*.csv")


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


def months_elapsed_since_start(today: date | None = None) -> int | None:
    """Return elapsed strategy months from FG_STRATEGY_START_DATE."""
    raw = os.getenv("FG_STRATEGY_START_DATE")
    if not raw:
        return None
    start = date.fromisoformat(raw)
    current = today or date.today()
    return max(0, (current - start).days // 30)


def calculate_margin_metrics(
    balances: FidelityBalances,
    *,
    annual_rate: float,
    jump_alert_threshold: float,
    monthly_dividend_income: float | None = None,
    today: date | None = None,
) -> MarginMetrics:
    """Calculate live margin metrics from balances and config."""
    margin_balance = abs(balances.net_debit)
    monthly_interest_cost = margin_balance * annual_rate / 12
    annual_interest_cost = monthly_interest_cost * 12
    coverage_ratio = (
        monthly_dividend_income / monthly_interest_cost
        if monthly_dividend_income is not None and monthly_interest_cost > 0
        else None
    )
    portfolio_margin_ratio = (
        balances.total_account_value / margin_balance if margin_balance > 0 else None
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
        as_of_date=(today or date.today()).isoformat(),
        source_file=balances.source_file,
        portfolio_value=round(balances.total_account_value, 2),
        margin_balance=round(margin_balance, 2),
        margin_buying_power=balances.margin_buying_power,
        margin_interest_accrued_this_month=balances.margin_interest_accrued_this_month,
        annual_interest_rate=annual_rate,
        monthly_interest_cost=round(monthly_interest_cost, 2),
        annual_interest_cost=round(annual_interest_cost, 2),
        monthly_dividend_income=monthly_dividend_income,
        coverage_ratio=round(coverage_ratio, 2) if coverage_ratio is not None else None,
        portfolio_margin_ratio=(
            round(portfolio_margin_ratio, 2)
            if portfolio_margin_ratio is not None
            else None
        ),
        jump_alert_threshold=jump_alert_threshold,
        margin_day_change=balances.net_debit_day_change,
        alert_status=alert_status,
        months_elapsed=months_elapsed_since_start(today),
    )


def metrics_from_runtime(
    *,
    csv_path: str | Path | None = None,
    annual_rate: float | None = None,
    monthly_dividend_income: float | None = None,
    today: date | None = None,
) -> MarginMetrics:
    """Load .env/config + latest CSV and return derived live metrics."""
    load_dotenv()
    balances = read_fidelity_balances(csv_path)
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


def _json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    return value


def main() -> None:
    """Run the margin metrics CLI."""
    parser = argparse.ArgumentParser(description="Calculate live margin health metrics")
    parser.add_argument("--csv", help="Specific Fidelity balances CSV to read")
    parser.add_argument(
        "--annual-rate",
        type=parse_rate,
        help="Annual margin rate as decimal or percent; defaults to .env",
    )
    parser.add_argument(
        "--monthly-dividend-income",
        type=parse_money,
        help="Current monthly dividend income; defaults to FG_DIVIDEND_MONTHLY_INCOME if set",
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    args = parser.parse_args()

    metrics = metrics_from_runtime(
        csv_path=args.csv,
        annual_rate=args.annual_rate,
        monthly_dividend_income=args.monthly_dividend_income,
    )
    print(
        json.dumps(
            asdict(metrics),
            default=_json_default,
            indent=2 if args.pretty else None,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
