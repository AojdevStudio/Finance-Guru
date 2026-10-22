"""SDK failures must not expose credentials through errors or CLI output."""

from __future__ import annotations

import traceback
from types import SimpleNamespace
from typing import Any

import pytest
from pydantic import SecretStr
from urllib3.exceptions import MaxRetryError

from src.integrations.snaptrade import cli
from src.integrations.snaptrade.client import SnapTradeAPIError, SnapTradeClientWrapper
from src.integrations.snaptrade.models import SnapTradeCredentials

SENTINEL = "SYNTHETIC_SNAPTRADE_SENTINEL"


class SyntheticSDKError(RuntimeError):
    def __init__(self, status: object) -> None:
        super().__init__(SENTINEL)
        self.status = status
        self.response_body = {"detail": SENTINEL}


@pytest.mark.parametrize(
    ("kind", "expected_status"),
    [
        ("transport", None),
        ("zero", None),
        ("body", 403),
        ("string", None),
        ("bool", None),
    ],
)
def test_sdk_failures_hide_private_details_in_errors_and_cli(
    kind: str,
    expected_status: int | None,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    if kind == "transport":
        upstream: Exception = MaxRetryError(
            None, f"/accounts?userSecret={SENTINEL}", "offline synthetic failure"
        )
    else:
        upstream = SyntheticSDKError(
            {"zero": 0, "body": 403, "string": SENTINEL, "bool": True}[kind]
        )

    def fail(**kwargs: Any) -> None:
        raise upstream

    client = SnapTradeClientWrapper(
        SnapTradeCredentials(
            client_id=SecretStr("synthetic-client"),
            consumer_key=SecretStr("synthetic-consumer"),
            user_id=SecretStr("synthetic-user"),
            user_secret=SecretStr(SENTINEL),
        ),
        sdk_client=SimpleNamespace(
            account_information=SimpleNamespace(list_user_accounts=fail)
        ),
    )

    with pytest.raises(SnapTradeAPIError) as failure:
        client.list_accounts()

    assert SENTINEL not in str(failure.value), (
        "SDK error exposes synthetic private detail"
    )
    assert SENTINEL not in "".join(traceback.format_exception(failure.value)), (
        "SDK traceback exposes synthetic private detail"
    )
    assert failure.value.status_code == expected_status

    monkeypatch.setattr(SnapTradeClientWrapper, "from_env", lambda: client)
    assert cli.main(["accounts", "--output", "json"]) == 1
    output = capsys.readouterr()
    assert output.out == ""
    assert "SnapTrade error" in output.err
    assert SENTINEL not in output.err, "CLI exposes synthetic private detail"
