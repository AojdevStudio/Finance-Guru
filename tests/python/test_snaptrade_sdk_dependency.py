import tomllib
from pathlib import Path

from packaging.requirements import Requirement
from packaging.version import Version


def test_snaptrade_sdk_stays_on_supported_major_version() -> None:
    pyproject_path = Path(__file__).parents[2] / "pyproject.toml"
    pyproject = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    requirement = next(
        Requirement(dependency)
        for dependency in pyproject["project"]["dependencies"]
        if Requirement(dependency).name == "snaptrade-python-sdk"
    )

    assert Version("11.0.197") not in requirement.specifier
    assert Version("11.999.999") not in requirement.specifier
    assert Version("12.0.0") not in requirement.specifier
    assert Version("13.0.42") in requirement.specifier
    assert Version("13.999.999") in requirement.specifier
    assert Version("14.0.0") not in requirement.specifier


def test_installed_sdk_constructs_and_reads_positions_offline(monkeypatch) -> None:
    import json

    import urllib3

    from src.integrations.snaptrade.client import SnapTradeClientWrapper
    from src.integrations.snaptrade.models import SnapTradeCredentials

    requests = []

    def request(self, method, url, **kwargs):
        requests.append((method, url, kwargs))
        return urllib3.HTTPResponse(
            body=json.dumps(
                {
                    "results": [
                        {
                            "instrument": {
                                "kind": "stock",
                                "id": "00000000-0000-4000-8000-000000000002",
                                "symbol": "TEST",
                                "raw_symbol": "TEST",
                            },
                            "units": "2",
                            "price": "10",
                            "cost_basis": "8",
                        },
                        {
                            "instrument": {
                                "kind": "option",
                                "id": "00000000-0000-4000-8000-000000000003",
                                "symbol": "SPY   260918P00620000",
                                "option_type": "PUT",
                                "strike_price": "620",
                                "expiration_date": "2026-09-18",
                                "multiplier": "100",
                                "underlying": {
                                    "id": "00000000-0000-4000-8000-000000000004",
                                    "symbol": "SPY",
                                },
                            },
                            "units": "1",
                            "price": "3.93",
                            "cost_basis": "4.61675",
                        },
                    ],
                    "data_freshness": {"as_of": "2026-10-22T00:00:00Z"},
                }
            ).encode(),
            status=200,
            headers={"Content-Type": "application/json"},
        )

    monkeypatch.setattr(urllib3.PoolManager, "request", request)
    client = SnapTradeClientWrapper(
        SnapTradeCredentials(
            client_id="synthetic-client",
            consumer_key="synthetic-consumer",
            user_id="synthetic-user",
            user_secret="synthetic-secret",
        )
    )
    positions = client.get_positions("00000000-0000-4000-8000-000000000001")
    options = client.get_options("00000000-0000-4000-8000-000000000001")
    assert positions[0]["symbol"] == "TEST"
    assert positions[0]["average_purchase_price"] == 8
    assert options[0]["symbol"] == "-SPY260918P620"
    assert options[0]["average_purchase_price"] == 4.61675
    assert len(requests) == 2
    assert all("userId=synthetic-user" in url for _, url, _ in requests)
    assert all("clientId=synthetic-client" in url for _, url, _ in requests)
    assert all(
        method == "GET" and "/positions/all" in url for method, url, _ in requests
    )
    assert all("Signature" in kwargs["headers"] for _, _, kwargs in requests)
