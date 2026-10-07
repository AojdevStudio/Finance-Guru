"""The portfolio-context task reads the ledger after a refresh.

Specialists run ``fin-guru/tasks/load-portfolio-context.md`` before portfolio
work. The ledger is the source of truth; a Fidelity CSV in ``imports/`` is not.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TASK = REPO_ROOT / "fin-guru" / "tasks" / "load-portfolio-context.md"

# Instructions that sent specialists at a second ledger.
FORBIDDEN_SNIPPETS = (
    'find imports -name "Portfolio_Positions',
    "Please download latest positions from Fidelity",
    "Balances_for_Account_",
    "Portfolio_Positions_",
    "--source csv",
)


def test_portfolio_context_task_reads_the_ledger_after_refresh() -> None:
    text = TASK.read_text(encoding="utf-8")

    assert "family_office.db" in text
    assert "uv run python -m src.integrations.refresh_all" in text
    assert "uv run python -m src.integrations.snaptrade.sync_db --show" in text
    assert "uv run python -m src.analysis.margin_metrics --pretty" in text
    assert "synced_at" in text
    for snippet in FORBIDDEN_SNIPPETS:
        assert snippet not in text
