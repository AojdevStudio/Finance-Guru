"""Fidelity CSV parsing in the dashboard portfolio loader."""

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


def test_parse_portfolio_skips_metadata_rows_and_cleans_symbols(
    tmp_path: Path, mocker
) -> None:
    mocker.patch(
        "src.ui.services.portfolio_loader.FinGuruConfig.load_layers",
        return_value={"layer1": ["SPAXX"]},
    )
    csv_path = tmp_path / "Portfolio_Positions_REDACTED.csv"
    csv_path.write_text(
        "Symbol,Quantity,Current Value,Today's Gain/Loss Dollar,Today's Gain/Loss Percent\n"
        "SPAXX**,100,$100.00,$0.00,0.00%\n"
        "Pending Activity,,$5.00,,\n"
        "Total,,$105.00,,\n"
    )

    snapshot = PortfolioLoader.parse_portfolio(csv_path)

    assert [(h.symbol, h.layer) for h in snapshot.holdings] == [("SPAXX", "layer1")]


def test_load_latest_returns_none_for_unreadable_csv(tmp_path: Path, mocker) -> None:
    bad_csv = tmp_path / "Portfolio_Positions_bad.csv"
    bad_csv.write_text("Symbol\nPLTR\n")
    mocker.patch.object(PortfolioLoader, "find_latest_csv", return_value=bad_csv)

    assert PortfolioLoader.load_latest() is None
