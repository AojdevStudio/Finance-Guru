"""SQLite state store for buy-ticket agent smoke runs."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS runs (
        id TEXT PRIMARY KEY,
        created_at TEXT NOT NULL,
        trigger TEXT NOT NULL,
        status TEXT NOT NULL,
        draft_path TEXT,
        log_path TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS tickets (
        id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        ticker TEXT NOT NULL,
        status TEXT NOT NULL,
        draft_path TEXT NOT NULL,
        preview TEXT NOT NULL,
        FOREIGN KEY(run_id) REFERENCES runs(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS decisions (
        id TEXT PRIMARY KEY,
        ticket_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        decision TEXT NOT NULL,
        source TEXT NOT NULL,
        FOREIGN KEY(ticket_id) REFERENCES tickets(id)
    )
    """,
)


@contextmanager
def connect_state(db_path: Path) -> Iterator[sqlite3.Connection]:
    """Open the SQLite state database and ensure parent directories exist."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def initialize_state(db_path: Path) -> None:
    """Create the smoke state schema idempotently."""
    with connect_state(db_path) as conn:
        for statement in SCHEMA_STATEMENTS:
            conn.execute(statement)


def record_smoke_run(
    db_path: Path,
    *,
    run_id: str,
    ticket_id: str,
    created_at: str,
    ticker: str,
    status: str,
    draft_path: Path,
    log_path: Path,
    preview: str,
) -> None:
    """Persist run, ticket, and initial decision rows in one transaction."""
    with connect_state(db_path) as conn:
        conn.execute(
            """
            INSERT INTO runs
                (id, created_at, trigger, status, draft_path, log_path)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                created_at = excluded.created_at,
                trigger = excluded.trigger,
                status = excluded.status,
                draft_path = excluded.draft_path,
                log_path = excluded.log_path
            """,
            (
                run_id,
                created_at,
                "smoke",
                status,
                str(draft_path),
                str(log_path),
            ),
        )
        conn.execute(
            """
            INSERT INTO tickets
                (id, run_id, created_at, ticker, status, draft_path, preview)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                run_id = excluded.run_id,
                created_at = excluded.created_at,
                ticker = excluded.ticker,
                status = excluded.status,
                draft_path = excluded.draft_path,
                preview = excluded.preview
            """,
            (
                ticket_id,
                run_id,
                created_at,
                ticker,
                status,
                str(draft_path),
                preview,
            ),
        )
        conn.execute(
            """
            INSERT INTO decisions
                (id, ticket_id, created_at, decision, source)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                ticket_id = excluded.ticket_id,
                created_at = excluded.created_at,
                decision = excluded.decision,
                source = excluded.source
            """,
            (
                f"{ticket_id}-pending",
                ticket_id,
                created_at,
                "pending",
                "smoke",
            ),
        )


def record_smoke_failure(
    db_path: Path,
    *,
    run_id: str,
    created_at: str,
    status: str,
    log_path: Path,
) -> None:
    """Persist a smoke run failure before any ticket draft exists."""
    with connect_state(db_path) as conn:
        conn.execute(
            """
            INSERT INTO runs
                (id, created_at, trigger, status, draft_path, log_path)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                created_at = excluded.created_at,
                trigger = excluded.trigger,
                status = excluded.status,
                draft_path = excluded.draft_path,
                log_path = excluded.log_path
            """,
            (
                run_id,
                created_at,
                "smoke",
                status,
                None,
                str(log_path),
            ),
        )
