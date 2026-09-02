"""Regression tests for idempotent buy-ticket draft notification retries."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from buy_ticket_agent.config import NotificationConfig
from buy_ticket_agent.main import main
from buy_ticket_agent.notifier import NotificationResult
from buy_ticket_agent.pipeline import CliEnvelope, SmokeResult, run_smoke
from buy_ticket_agent.secrets import SecretAccessError


def _configure_trigger(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("FIN_GURU_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("BUY_TICKET_TRIGGER_SOURCE", "simplefin_deposit")
    monkeypatch.setenv("BUY_TICKET_TRIGGER_TRANSACTION_KEY", "transaction-key")


def test_notification_retry_reuses_persisted_draft(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The same trigger retries delivery without regenerating its draft."""
    _configure_trigger(monkeypatch, tmp_path)
    fixed_now = datetime(2026, 6, 5, 12, 0, 0, tzinfo=UTC)
    cli_result = CliEnvelope(
        command=["python", "itc_risk_cli.py"],
        status="succeeded",
        returncode=0,
        stdout_chars=10,
        stderr_chars=0,
    )
    notification_config = NotificationConfig(
        server_url="https://ntfy.example.test",
        topic="topic",
        source="env",
    )
    notifications = [
        NotificationResult(status="failed", source="env", error="Timeout"),
        NotificationResult(status="sent", source="env"),
    ]

    with (
        patch(
            "buy_ticket_agent.pipeline.resolve_notification_config",
            return_value=notification_config,
        ),
        patch(
            "buy_ticket_agent.pipeline.run_layer3_smoke_cli",
            return_value=cli_result,
        ) as layer3,
        patch(
            "buy_ticket_agent.pipeline.push_ticket_preview",
            side_effect=notifications,
        ) as notify,
        patch("buy_ticket_agent.pipeline._utc_now", return_value=fixed_now),
    ):
        first = run_smoke()
        second = run_smoke()

    assert first.run_id == second.run_id
    assert first.ticket_id == second.ticket_id
    assert first.draft_path == second.draft_path
    assert first.persistence.status == "created"
    assert second.persistence.status == "reused"
    assert first.status == second.status == "completed"
    assert first.notification.status == "failed"
    assert second.notification.status == "sent"
    assert layer3.call_count == 1
    assert notify.call_count == 2
    assert len(list((tmp_path / "tickets" / "auto-drafts").glob("*.json"))) == 1

    with sqlite3.connect(tmp_path / "auto-tickets" / "state.db") as conn:
        assert conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0] == 1


def test_main_retries_failed_notification_after_persistence(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Persisted-but-unnotified results remain observable and retryable."""
    result = SmokeResult(
        run_id="run-1",
        ticket_id="ticket-1",
        status="completed",
        draft_path="draft.json",
        log_path="log.json",
        state_db="state.db",
        notification=NotificationResult(status="failed", source="env"),
    )

    with patch("buy_ticket_agent.main.run_smoke_for_cli", return_value=result):
        exit_code = main(["--smoke"])

    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "completed"
    assert payload["notification"]["status"] == "failed"
    assert exit_code == 1


def test_main_uses_repository_logger_for_secret_diagnostics(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Secret failures do not emit ad hoc print diagnostics."""
    with patch(
        "buy_ticket_agent.main.run_smoke_for_cli",
        side_effect=SecretAccessError("bws unavailable"),
    ):
        exit_code = main(["--smoke"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Secret access blocker" not in captured.err
