# Paid MCP capability probe

Run this capability probe before the first external-research step in a workflow that may use `exa`, `bright-data`, `perplexity`, or `financial-datasets`.

1. Name the MCP capabilities the current workflow wants before attempting a call.
2. Check the tools available in the current session for the matching MCP tool prefixes. Do not infer availability from documentation, environment variables, or a prior session.
3. Report one of these outcomes to the user:
   - `available` — name the MCP that will be used.
   - `WebSearch fallback` — name the missing MCP and state the quality caveat before searching.
   - `blocked` — name every missing capability and explain how to add it.
4. Never omit a research step silently because a tool is absent.

## Fallback policy

| Missing MCP | Allowed fallback | Required caveat |
| --- | --- | --- |
| `exa` | `WebSearch` and `WebFetch` | Results may be less comprehensive and semantic discovery may be weaker. |
| `bright-data` | `WebSearch` and `WebFetch` | Dynamic, blocked, or deeply nested pages may be inaccessible. |
| `perplexity` | `WebSearch` and `WebFetch` with explicit source-by-source synthesis | The synthesis is manual and may cover fewer sources. |
| `financial-datasets` | `WebSearch` restricted to issuer filings, regulator databases, and other primary sources | Data is unnormalized; cross-period comparisons and filing arithmetic need extra validation. |

Use the `financial-datasets` fallback only when primary-source filings can answer the request. Stop when the task requires normalized statements, reliable bulk filing data, or a value that cannot be verified from primary sources.

If the selected fallback tools are also unavailable, or the task cannot tolerate the caveat, stop and say:

> Missing capability: `<mcp-name>`. Add and authenticate the `<mcp-name>` MCP server in your Claude Code MCP configuration, restart the session, and run this workflow again.

List every missing MCP in the stop message. Never ask the user to paste an API key into chat or a tracked file.
