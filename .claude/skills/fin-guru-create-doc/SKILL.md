---
name: fin-guru-create-doc
description: Create institutional-grade financial documents from templates. Handles analysis reports, buy tickets, compliance memos, Excel model specs, presentations, and onboarding reports.
---

# Document Creation Skill

Create professional financial documents using Finance Guru templates.

## Available Templates

| Template | Path | Purpose |
|----------|------|---------|
| Analysis Report | `{project-root}/fin-guru/templates/analysis-report.md` | Research and analysis reports |
| Buy Ticket | `{project-root}/fin-guru/templates/buy-ticket-template.md` | Capital deployment authorization |
| Compliance Memo | `{project-root}/fin-guru/templates/compliance-memo.md` | Regulatory compliance documentation |
| Excel Model Spec | `{project-root}/fin-guru/templates/excel-model-spec.md` | Financial model specifications |
| Presentation | `{project-root}/fin-guru/templates/presentation-format.md` | Stakeholder presentations |
| Onboarding Report | `{project-root}/fin-guru/templates/onboarding-report.md` | Client onboarding summaries |

## Workflow

1. Identify the appropriate template for the document type
2. Load the template from `{project-root}/fin-guru/templates/`
3. Gather required inputs (analysis data, recommendations, metrics)
4. Generate document with proper YAML frontmatter (date stamp, disclaimer, citations)
5. Save under `fin-guru-private/fin-guru/` using naming conventions:
   - Analysis reports: `analysis/{topic}-{YYYY-MM-DD}.md`
   - Buy tickets: `tickets/buy-ticket-{YYYY-MM-DD}-{short-descriptor}.md`
   - Strategy docs: `analysis/{strategy-name}-master-strategy.md`

## Delegation to Specialized Ticket Skills

For the two ticket types below, **do not draft here — delegate to the specialized skill**:

- **Buy tickets** (capital deployment) → use `fin-guru-buy-ticket`. That skill enforces portfolio CSV loading, live price snapshot, ITC advisory, allocation table generation, and pre-flight gates before writing to `fin-guru-private/fin-guru/tickets/`.
- **Options hedge tickets** (open / roll / close protective puts) → use `fin-guru-hedge-roll`. That skill handles mode selection (OPEN | ROLL | CLOSE), enforces framework invariants from `hedging-strategies.md`, and writes to `fin-guru-private/fin-guru/tickets/rolls/`.

This skill remains the entrypoint for: analysis reports, compliance memos, Excel model specs, presentations, and onboarding reports — everything else covered by the templates table above.

## Buy Ticket Contract (Legacy Reference)

This contract is now enforced by `fin-guru-buy-ticket`. Preserved here for documents that cite it:

- YAML frontmatter plus a structured `## Execution Summary` section
- Portfolio context must already be loaded
- Require deployment amount, allocation table, price snapshot, strategy rationale, risk notes, and sources/assumptions
- Save tickets to `fin-guru-private/fin-guru/tickets/`
- Treat ITC risk as advisory-only; include an ITC advisory only when upstream analysis provided it and the signal is materially elevated

## Requirements

- All documents MUST include educational-only disclaimer
- All sources MUST be cited with timestamps
- All documents MUST include YAML frontmatter with date stamp
- Follow institutional-grade formatting standards
