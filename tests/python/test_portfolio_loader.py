"""Fidelity CSV parsing in the dashboard portfolio loader."""

import os
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from src.ui.services.portfolio_loader import PortfolioLoader


@pytest.mark.parametrize(
    ("cell", "expected"),
    [
        pytest.param("$64,583.53", 64583.53, id="currency"),
        pytest.param("+$935.45", 935.45, id="signed-currency"),
        pytest.param("+1.46%", 1.46, id="percent"),
        pytest.param("-0.10%", -0.10, id="negative-percent"),
        pytest.param(12.5, 12.5, id="number"),
        pytest.param(float("nan"), 0.0, id="nan-float"),
        pytest.param("NaN", 0.0, id="nan-text"),
        pytest.param("--", 0.0, id="dashes"),
        pytest.param("ERROR", 0.0, id="error"),
        pytest.param("", 0.0, id="blank"),
    ],
)
def test_parse_number(cell, expected) -> None:
    assert PortfolioLoader._parse_number(cell) == pytest.approx(expected)


@pytest.mark.parametrize("symbol", ["SPAXX**", "SPAXX **"])
def test_parse_portfolio_skips_metadata_rows_and_cleans_symbols(
    tmp_path: Path, mocker, symbol: str
) -> None:
    mocker.patch(
        "src.ui.services.portfolio_loader.FinGuruConfig.load_layers",
        return_value={"layer1": ["SPAXX"]},
    )
    csv_path = tmp_path / "Portfolio_Positions_REDACTED.csv"
    csv_path.write_text(
        "Symbol,Quantity,Current Value,Today's Gain/Loss Dollar,Today's Gain/Loss Percent\n"
        f"{symbol},100,$100.00,$0.00,0.00%\n"
        "Pending Activity,,$5.00,,\n"
        "Total,,$105.00,,\n"
    )

    snapshot = PortfolioLoader.parse_portfolio(csv_path)

    assert [(h.symbol, h.layer) for h in snapshot.holdings] == [("SPAXX", "layer1")]


def test_load_latest_raises_for_unreadable_csv(tmp_path: Path, mocker) -> None:
    bad_csv = tmp_path / "Portfolio_Positions_bad.csv"
    bad_csv.write_text("Symbol\nPLTR\n")
    mocker.patch.object(PortfolioLoader, "find_latest_csv", return_value=bad_csv)

    with pytest.raises(ValueError, match="Missing required columns"):
        PortfolioLoader.load_latest()


@pytest.mark.parametrize("symbol", ["BRK-B", "BRK.B"])
def test_share_class_symbol_keeps_its_layer(
    tmp_path: Path, mocker, symbol: str
) -> None:
    mocker.patch(
        "src.ui.services.portfolio_loader.FinGuruConfig.load_layers",
        return_value={"layer1": [symbol]},
    )
    csv_path = tmp_path / "Portfolio_Positions_synthetic.csv"
    csv_path.write_text(
        f"Symbol,Quantity,Current Value,Today's Gain/Loss Dollar\n{symbol},1,100,0\n"
    )
    holding = PortfolioLoader.parse_portfolio(csv_path).holdings[0]
    assert (holding.symbol, holding.layer) == (symbol, "layer1")


def test_load_latest_returns_none_when_no_csv_exists(mocker) -> None:
    mocker.patch.object(PortfolioLoader, "find_latest_csv", return_value=None)
    assert PortfolioLoader.load_latest() is None


def test_csv_reload_preserves_file_timestamp(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FIN_GURU_DATA_ROOT", str(tmp_path))
    imports = tmp_path / "imports"
    imports.mkdir()
    csv = imports / "Portfolio_Positions_synthetic.csv"
    csv.write_text(
        "Symbol,Quantity,Current Value,Today's Gain/Loss Dollar\nABC,1,100,0\n"
    )
    exported_at = datetime(2025, 1, 2, 12, 0)
    os.utime(csv, (exported_at.timestamp(), exported_at.timestamp()))

    first = PortfolioLoader.load_latest()
    second = PortfolioLoader.load_latest()

    assert first is not None and second is not None
    assert first.timestamp == second.timestamp == exported_at


def test_csv_future_timestamp_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FIN_GURU_DATA_ROOT", str(tmp_path))
    csv = tmp_path / "Portfolio_Positions_synthetic.csv"
    csv.write_text(
        "Symbol,Quantity,Current Value,Today's Gain/Loss Dollar\nABC,1,100,0\n"
    )
    future = datetime.now() + timedelta(days=1)
    os.utime(csv, (future.timestamp(), future.timestamp()))

    with pytest.raises(ValueError, match="future"):
        PortfolioLoader.parse_portfolio(csv)
