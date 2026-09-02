---
name: fin-guru-create-doc
description: Create institutional-grade financial documents from templates. Handles analysis reports, buy tickets, compliance memos, Excel model specs, presentations, and onboarding reports.
---

# Document Creation Skill

Create professional financial documents using Finance Guru templates.

## Capability probe

Before filling source gaps in a document, follow the shared **[paid MCP capability probe](../_shared/PaidMcpCapabilityProbe.md)**. This workflow wants `perplexity` for sourced synthesis and `exa` for deep discovery when upstream research is incomplete. If either is absent, announce the source-by-source `WebSearch` fallback and its coverage caveat; never omit a required source section silently.

## Available Templates

| Template | Path | Purpose |
|----------|------|---------|
| Analysis Report | `{project-root}/fin-guru/templates/analysis-report.md` | Research and analysis reports |
| Buy Ticket | `{project-root}/fin-guru/templates/buy-ticket-template.md` | Capital deployment authorization |
| Compliance Memo | `{project-root}/fin-guru/templates/compliance-memo.md` | Regulatory compliance documentation |
| Excel Model Spec | `{project-root}/fin-guru/templates/excel-model-spec.md` | Financial model specifications |
| Presentation | no template; write from the analysis report structure | Stakeholder presentations |
| Onboarding Report | no template; summarize the learner profile | Client onboarding summaries |

## Workflow

1. Identify the appropriate template for the document type
2. Load the template from `{project-root}/fin-guru/templates/`
3. Gather required inputs (analysis data, recommendations, metrics)
4. Generate document with proper YAML frontmatter (date stamp, disclaimer, citations)
5. Save under `analysis/` using naming conventions:
   - Analysis reports: `analysis/{topic}-{YYYY-MM-DD}.md`
   - Buy tickets: `tickets/buy-ticket-{YYYY-MM-DD}-{short-descriptor}.md`
   - Strategy docs: `analysis/{strategy-name}-master-strategy.md`

## Buy Ticket Contract

Buy tickets use the canonical `buy-ticket-template.md` contract:

- Builder is not a direct buy-ticket entrypoint; buy-ticket creation should begin from Strategy Advisor or Dividend Specialist
- YAML frontmatter plus a structured `## Execution Summary` section
- Portfolio context must already be loaded
- Require deployment amount, allocation table, price snapshot, strategy rationale, risk notes, and sources/assumptions
- Save tickets to `tickets/`
- Treat ITC risk as advisory-only; include an ITC advisory only when upstream analysis provided it and the signal is materially elevated

## Requirements

- All documents MUST include educational-only disclaimer
- All sources MUST be cited with timestamps
- All documents MUST include YAML frontmatter with date stamp
- Follow institutional-grade formatting standards
