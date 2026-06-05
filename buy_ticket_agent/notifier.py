"""ntfy notification client for buy-ticket smoke tickets."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote

import requests

from buy_ticket_agent.config import NotificationConfig


@dataclass(frozen=True)
class NotificationResult:
    """Result envelope for a notification attempt."""

    status: str
    source: str | None
    error: str | None = None


def push_ticket_preview(
    config: NotificationConfig | None,
    *,
    ticket_id: str,
    preview: str,
    timeout: int = 10,
) -> NotificationResult:
    """Push a short ticket preview to ntfy.

    The topic is used only to construct the request URL and is never returned.
    """
    if config is None:
        return NotificationResult(status="skipped", source=None)

    url = f"{config.server_url}/{quote(config.topic, safe='')}"
    headers = {
        "Title": "Buy-ticket smoke draft",
        "Tags": "chart_with_upwards_trend",
        "Priority": "default",
    }
    body = f"{ticket_id}: {preview}"

    try:
        response = requests.post(
            url, data=body.encode("utf-8"), headers=headers, timeout=timeout
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        return NotificationResult(
            status="failed",
            source=config.source,
            error=exc.__class__.__name__,
        )
    return NotificationResult(status="sent", source=config.source)
