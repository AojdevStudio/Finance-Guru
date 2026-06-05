"""Tests for the buy-ticket agent smoke scaffold."""

from __future__ import annotations

import json
import sqlite3
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

from buy_ticket_agent.config import NotificationConfig
from buy_ticket_agent.main import main
from buy_ticket_agent.notifier import NotificationResult, push_ticket_preview
from buy_ticket_agent.pipeline import SmokeResult, run_layer3_smoke_cli, run_smoke
from buy_ticket_agent.secrets import (
    SecretAccessError,
    get_bws_secret_value,
    resolve_notification_config,
)
from buy_ticket_agent.state import connect_state, initialize_state, record_smoke_run


def test_initialize_state_is_idempotent(tmp_path: Path) -> None:
    """State schema can be initialized repeatedly without losing rows."""
    db_path = tmp_path / "state.db"

    initialize_state(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO runs (id, created_at, trigger, status) VALUES (?, ?, ?, ?)",
            ("run-1", "2026-06-05T00:00:00+00:00", "smoke", "completed"),
        )

    initialize_state(db_path)

    with sqlite3.connect(db_path) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        count = conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0]

    assert {"runs", "tickets", "decisions"}.issubset(tables)
    assert count == 1


def test_state_connections_enforce_foreign_keys(tmp_path: Path) -> None:
    """State connections enforce declared SQLite foreign key constraints."""
    db_path = tmp_path / "state.db"
    initialize_state(db_path)

    try:
        with connect_state(db_path) as conn:
            conn.execute(
                """
                INSERT INTO tickets
                    (id, run_id, created_at, ticker, status, draft_path, preview)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "ticket-1",
                    "missing-run",
                    "2026-06-05T00:00:00+00:00",
                    "SPY",
                    "completed",
                    "draft.json",
                    "preview",
                ),
            )
    except sqlite3.IntegrityError:
        pass
    else:
        raise AssertionError("Expected SQLite foreign key enforcement")


def test_record_smoke_run_is_idempotent_with_foreign_keys(tmp_path: Path) -> None:
    """Smoke run upserts do not violate foreign keys on repeated IDs."""
    db_path = tmp_path / "state.db"
    initialize_state(db_path)

    common = {
        "run_id": "run-1",
        "ticket_id": "ticket-1",
        "created_at": "2026-06-05T00:00:00+00:00",
        "ticker": "SPY",
        "log_path": tmp_path / "log.json",
    }
    record_smoke_run(
        db_path,
        **common,
        status="completed",
        draft_path=tmp_path / "draft-1.json",
        preview="first preview",
    )
    record_smoke_run(
        db_path,
        **common,
        status="notification_failed",
        draft_path=tmp_path / "draft-2.json",
        preview="second preview",
    )

    with sqlite3.connect(db_path) as conn:
        counts = (
            conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0],
            conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0],
            conn.execute("SELECT COUNT(*) FROM decisions").fetchone()[0],
        )
        status = conn.execute("SELECT status FROM tickets").fetchone()[0]
        preview = conn.execute("SELECT preview FROM tickets").fetchone()[0]

    assert counts == (1, 1, 1)
    assert status == "notification_failed"
    assert preview == "second preview"


def test_bws_secret_value_parses_without_printing_secret() -> None:
    """BWS resolver returns only the value field."""
    completed = MagicMock()
    completed.stdout = json.dumps({"value": "topic-value"})

    with patch(
        "buy_ticket_agent.secrets.subprocess.run", return_value=completed
    ) as run:
        value = get_bws_secret_value("secret-id")

    assert value == "topic-value"
    assert run.call_args.args[0] == [
        "bws",
        "secret",
        "get",
        "secret-id",
        "--output",
        "json",
    ]


def test_notification_config_prefers_bws_secret(monkeypatch) -> None:
    """Configured BWS secret id is used before direct topic environment."""
    monkeypatch.setenv("BUY_TICKET_AGENT_NTFY_TOPIC_SECRET_ID", "secret-id")
    monkeypatch.setenv("NTFY_TOPIC", "env-topic")

    with patch(
        "buy_ticket_agent.secrets.get_bws_secret_value",
        return_value="bws-topic",
    ):
        config = resolve_notification_config()

    assert config == NotificationConfig(
        server_url="https://ntfy.sh",
        topic="bws-topic",
        source="bws",
    )


def test_push_ticket_preview_posts_to_ntfy() -> None:
    """Notification client posts the preview body and reports sent."""
    config = NotificationConfig(
        server_url="https://ntfy.example.test",
        topic="topic/a?b=c",
        source="bws",
    )
    response = MagicMock()
    response.raise_for_status.return_value = None

    with patch(
        "buy_ticket_agent.notifier.requests.post", return_value=response
    ) as post:
        result = push_ticket_preview(
            config,
            ticket_id="ticket-1",
            preview="SPY shadow draft ready for review",
        )

    assert result.status == "sent"
    assert result.source == "bws"
    assert post.call_args.args[0] == "https://ntfy.example.test/topic%2Fa%3Fb%3Dc"
    assert b"ticket-1" in post.call_args.kwargs["data"]


def test_run_smoke_writes_draft_log_and_state(tmp_path: Path, monkeypatch) -> None:
    """Smoke run writes the expected artifacts and persists state rows."""
    monkeypatch.delenv("BUY_TICKET_AGENT_NTFY_TOPIC_SECRET_ID", raising=False)
    monkeypatch.delenv("NTFY_TOPIC_SECRET_ID", raising=False)
    monkeypatch.delenv("BUY_TICKET_AGENT_NTFY_TOPIC", raising=False)
    monkeypatch.delenv("NTFY_TOPIC", raising=False)
    monkeypatch.setenv("ITC_API_KEY", "test-key")

    completed = MagicMock()
    completed.returncode = 0
    completed.stdout = '{"symbol":"SP500","current_risk_score":0.4}'
    completed.stderr = "ok"

    with (
        patch(
            "buy_ticket_agent.pipeline.subprocess.run", return_value=completed
        ) as run,
        patch("buy_ticket_agent.pipeline._utc_now") as now,
    ):
        from datetime import UTC, datetime

        now.return_value = datetime(2026, 6, 5, 12, 0, 0, tzinfo=UTC)
        result = run_smoke(project_root=tmp_path)

    draft_path = tmp_path / result.draft_path
    log_path = tmp_path / result.log_path
    state_db = tmp_path / result.state_db

    assert result.status == "completed"
    assert result.notification.status == "skipped"
    assert result.notification.error is None
    assert draft_path.exists()
    assert log_path.exists()
    assert state_db.exists()

    draft = json.loads(draft_path.read_text())
    log = json.loads(log_path.read_text())
    assert draft["ticker"] == "SPY"
    assert draft["analysis_proxy"] == "SP500"
    assert "not investment advice" in draft["disclaimer"]
    assert log["layer3"]["status"] == "succeeded"
    assert log["layer3"]["command"][0] == "python"
    assert log["layer3"]["stdout_chars"] == len(completed.stdout)
    assert log["layer3"]["stderr_chars"] == len(completed.stderr)
    assert "stdout" not in log["layer3"]
    assert "stderr" not in log["layer3"]
    assert result.draft_path == (
        f"fin-guru-private/fin-guru/tickets/auto-drafts/{result.run_id}.json"
    )
    assert result.log_path.startswith("notebooks/auto-tickets/runs/smoke-20260605-")
    assert result.state_db == "notebooks/auto-tickets/state.db"

    command = run.call_args.args[0]
    assert command[1:] == [
        "src/analysis/itc_risk_cli.py",
        "SP500",
        "--universe",
        "tradfi",
        "--output",
        "json",
        "--no-price",
    ]

    with sqlite3.connect(state_db) as conn:
        run_count = conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
        ticket_count = conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
        decision_count = conn.execute("SELECT COUNT(*) FROM decisions").fetchone()[0]

    assert (run_count, ticket_count, decision_count) == (1, 1, 1)


def test_run_smoke_does_not_record_success_state_if_log_write_fails(
    tmp_path: Path, monkeypatch
) -> None:
    """Successful smoke runs do not persist state until the run log exists."""
    monkeypatch.delenv("BUY_TICKET_AGENT_NTFY_TOPIC_SECRET_ID", raising=False)
    monkeypatch.delenv("NTFY_TOPIC_SECRET_ID", raising=False)
    monkeypatch.delenv("BUY_TICKET_AGENT_NTFY_TOPIC", raising=False)
    monkeypatch.delenv("NTFY_TOPIC", raising=False)

    completed = MagicMock()
    completed.returncode = 0
    completed.stdout = '{"symbol":"SP500","current_risk_score":0.4}'
    completed.stderr = ""

    def write_json_or_fail_log(path: Path, payload: dict) -> None:
        if path.parent.name == "runs":
            raise OSError("log write failed")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    with (
        patch("buy_ticket_agent.pipeline.subprocess.run", return_value=completed),
        patch(
            "buy_ticket_agent.pipeline._write_json", side_effect=write_json_or_fail_log
        ),
    ):
        try:
            run_smoke(project_root=tmp_path)
        except OSError:
            pass
        else:
            raise AssertionError("Expected log write failure")

    state_db = tmp_path / "notebooks" / "auto-tickets" / "state.db"
    with sqlite3.connect(state_db) as conn:
        counts = (
            conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0],
            conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0],
            conn.execute("SELECT COUNT(*) FROM decisions").fetchone()[0],
        )

    assert counts == (0, 0, 0)


def test_layer3_smoke_cli_without_api_key_uses_capability_probe(
    tmp_path: Path, monkeypatch
) -> None:
    """Layer 3 smoke remains credential-free until analysis credentials exist."""
    monkeypatch.delenv("ITC_API_KEY", raising=False)
    completed = MagicMock()
    completed.returncode = 0
    completed.stdout = "supported tickers"
    completed.stderr = ""

    with patch(
        "buy_ticket_agent.pipeline.subprocess.run", return_value=completed
    ) as run:
        result = run_layer3_smoke_cli(project_root=tmp_path)

    assert result.status == "succeeded"
    assert run.call_args.args[0][1:] == [
        "src/analysis/itc_risk_cli.py",
        "--list-supported",
        "tradfi",
    ]


def test_run_smoke_layer3_failure_records_failure_without_draft(
    tmp_path: Path, monkeypatch
) -> None:
    """Layer 3 failures are logged without persisting raw CLI output."""
    monkeypatch.delenv("BUY_TICKET_AGENT_NTFY_TOPIC_SECRET_ID", raising=False)
    monkeypatch.delenv("NTFY_TOPIC_SECRET_ID", raising=False)
    monkeypatch.delenv("BUY_TICKET_AGENT_NTFY_TOPIC", raising=False)
    monkeypatch.delenv("NTFY_TOPIC", raising=False)

    completed = MagicMock()
    completed.returncode = 2
    completed.stdout = "SECRET_TOKEN=secret-value"
    completed.stderr = "private stderr output"

    with (
        patch("buy_ticket_agent.pipeline.subprocess.run", return_value=completed),
        patch("buy_ticket_agent.pipeline._utc_now") as now,
    ):
        from datetime import UTC, datetime

        now.return_value = datetime(2026, 6, 5, 12, 0, 0, tzinfo=UTC)
        result = run_smoke(project_root=tmp_path)

    log_path = tmp_path / result.log_path
    state_db = tmp_path / result.state_db
    log_text = log_path.read_text()
    log = json.loads(log_text)

    assert result.status == "layer3_failed"
    assert result.ticket_id is None
    assert result.draft_path is None
    assert result.notification is None
    assert not (
        tmp_path / "fin-guru-private" / "fin-guru" / "tickets" / "auto-drafts"
    ).exists()
    assert log["layer3"]["returncode"] == 2
    assert log["layer3"]["stdout_chars"] == len(completed.stdout)
    assert log["layer3"]["stderr_chars"] == len(completed.stderr)
    assert "SECRET_TOKEN" not in log_text
    assert "secret-value" not in log_text
    assert "private stderr output" not in log_text

    with sqlite3.connect(state_db) as conn:
        run_count = conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
        ticket_count = conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
        decision_count = conn.execute("SELECT COUNT(*) FROM decisions").fetchone()[0]

    assert (run_count, ticket_count, decision_count) == (1, 0, 0)


def test_run_smoke_does_not_record_failure_state_if_log_write_fails(
    tmp_path: Path, monkeypatch
) -> None:
    """Failed smoke runs do not persist state until the failure log exists."""
    monkeypatch.delenv("BUY_TICKET_AGENT_NTFY_TOPIC_SECRET_ID", raising=False)
    monkeypatch.delenv("NTFY_TOPIC_SECRET_ID", raising=False)
    monkeypatch.delenv("BUY_TICKET_AGENT_NTFY_TOPIC", raising=False)
    monkeypatch.delenv("NTFY_TOPIC", raising=False)

    completed = MagicMock()
    completed.returncode = 2
    completed.stdout = "failed"
    completed.stderr = ""

    with (
        patch("buy_ticket_agent.pipeline.subprocess.run", return_value=completed),
        patch(
            "buy_ticket_agent.pipeline._write_json",
            side_effect=OSError("log write failed"),
        ),
    ):
        try:
            run_smoke(project_root=tmp_path)
        except OSError:
            pass
        else:
            raise AssertionError("Expected log write failure")

    state_db = tmp_path / "notebooks" / "auto-tickets" / "state.db"
    with sqlite3.connect(state_db) as conn:
        counts = (
            conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0],
            conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0],
            conn.execute("SELECT COUNT(*) FROM decisions").fetchone()[0],
        )

    assert counts == (0, 0, 0)


def test_layer3_smoke_cli_timeout_returns_structured_failure(tmp_path: Path) -> None:
    """Layer 3 subprocess timeouts return a structured failure envelope."""
    with patch(
        "buy_ticket_agent.pipeline.subprocess.run",
        side_effect=subprocess.TimeoutExpired(
            cmd=["python"],
            timeout=60,
            output="partial",
            stderr="timed out",
        ),
    ):
        result = run_layer3_smoke_cli(project_root=tmp_path)

    assert result.status == "failed"
    assert result.returncode == -1
    assert result.error == "TimeoutExpired"
    assert result.stdout_chars == len("partial")
    assert result.stderr_chars == len("timed out")


def test_run_smoke_secret_failure_leaves_no_partial_artifacts(tmp_path: Path) -> None:
    """BWS failures stop before filesystem or state artifacts are created."""
    with patch(
        "buy_ticket_agent.pipeline.resolve_notification_config",
        side_effect=SecretAccessError("bws unavailable"),
    ):
        try:
            run_smoke(project_root=tmp_path)
        except SecretAccessError:
            pass
        else:
            raise AssertionError("Expected SecretAccessError")

    assert not (
        tmp_path / "fin-guru-private" / "fin-guru" / "tickets" / "auto-drafts"
    ).exists()
    assert not (tmp_path / "notebooks" / "auto-tickets" / "state.db").exists()
    assert not (tmp_path / "notebooks" / "auto-tickets" / "runs").exists()


def test_main_smoke_exits_zero(tmp_path: Path) -> None:
    """CLI smoke command prints a result envelope and exits successfully."""
    result = SmokeResult(
        run_id="run-1",
        ticket_id="ticket-1",
        status="completed",
        draft_path=str(tmp_path / "draft.json"),
        log_path=str(tmp_path / "log.json"),
        state_db=str(tmp_path / "state.db"),
        notification=NotificationResult(status="sent", source="bws"),
    )

    with patch("buy_ticket_agent.main.run_smoke_for_cli", return_value=result):
        assert main(["--smoke"]) == 0


def test_main_smoke_returns_nonzero_for_failed_result(tmp_path: Path) -> None:
    """CLI smoke command exits nonzero when the smoke result failed."""
    result = SmokeResult(
        run_id="run-1",
        ticket_id=None,
        status="layer3_failed",
        draft_path=None,
        log_path=str(tmp_path / "log.json"),
        state_db=str(tmp_path / "state.db"),
        notification=None,
    )

    with patch("buy_ticket_agent.main.run_smoke_for_cli", return_value=result):
        assert main(["--smoke"]) == 1
