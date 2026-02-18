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
5. Save to `fin-guru-private/fin-guru/analysis/` using naming conventions:
   - Analysis reports: `{topic}-{YYYY-MM-DD}.md`
   - Buy tickets: `buy-ticket-{YYYY-MM-DD}-{short-descriptor}.md`
   - Strategy docs: `{strategy-name}-master-strategy.md`

## Requirements

- All documents MUST include educational-only disclaimer
- All sources MUST be cited with timestamps
- All documents MUST include YAML frontmatter with date stamp
- Follow institutional-grade formatting standards
