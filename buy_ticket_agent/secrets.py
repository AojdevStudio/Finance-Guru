"""Bitwarden Secrets Manager integration for buy-ticket agent secrets."""

from __future__ import annotations

import json
import subprocess

from buy_ticket_agent.config import NotificationConfig, get_env


class SecretAccessError(RuntimeError):
    """Raised when a required Bitwarden secret cannot be retrieved."""


def get_bws_secret_value(secret_id: str) -> str:
    """Read a secret value through the Bitwarden Secrets Manager CLI.

    Secret values are never printed by this function. The caller receives only
    the parsed value field from the BWS JSON response.
    """
    command = ["bws", "secret", "get", secret_id, "--output", "json"]
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (
        subprocess.CalledProcessError,
        FileNotFoundError,
        subprocess.TimeoutExpired,
    ) as exc:
        raise SecretAccessError(
            "bws secret get failed for the configured ntfy topic secret."
        ) from exc

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise SecretAccessError("bws secret get returned invalid JSON.") from exc

    value = payload.get("value")
    if not isinstance(value, str) or not value.strip():
        raise SecretAccessError("bws secret get did not return a usable value.")
    return value.strip()


def resolve_notification_config() -> NotificationConfig | None:
    """Resolve ntfy configuration.

    Preferred path is Bitwarden via a configured secret id. `NTFY_TOPIC` remains
    supported for local smoke runs and tests when no BWS secret id is configured.
    """
    server_url = get_env("BUY_TICKET_AGENT_NTFY_URL") or get_env("NTFY_URL")
    if server_url is None:
        server_url = "https://ntfy.sh"

    secret_id = get_env("BUY_TICKET_AGENT_NTFY_TOPIC_SECRET_ID") or get_env(
        "NTFY_TOPIC_SECRET_ID"
    )
    if secret_id is not None:
        return NotificationConfig(
            server_url=server_url.rstrip("/"),
            topic=get_bws_secret_value(secret_id),
            source="bws",
        )

    topic = get_env("BUY_TICKET_AGENT_NTFY_TOPIC") or get_env("NTFY_TOPIC")
    if topic is None:
        return None
    return NotificationConfig(
        server_url=server_url.rstrip("/"),
        topic=topic,
        source="env",
    )
