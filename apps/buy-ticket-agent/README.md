# Buy-Ticket Agent

Private scaffold for the shadow-mode buy-ticket workflow.

Run the smoke path from the repository root:

```bash
uv run python -m buy_ticket_agent.main --smoke
```

The smoke path writes a draft, writes a run log, initializes local SQLite state,
and sends a short notification when ntfy configuration is available.

The Layer 3 smoke step uses the existing ITC CLI. It runs the credential-free
capability path when analysis credentials are absent, and switches to a single
risk probe when those credentials are configured.
