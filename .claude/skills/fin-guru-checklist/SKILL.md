---
name: fin-guru-checklist
description: Execute quality and compliance checklists for Finance Guru deliverables. Supports margin strategy, dividend framework, and general quality checklists.
---

# Checklist Execution Skill

Apply structured quality checklists to Finance Guru deliverables and workflows.

## Available Checklists

| Checklist | Path | Used By |
|-----------|------|---------|
| Margin Strategy | `{project-root}/fin-guru/checklists/margin-strategy.md` | Margin Specialist |
| Dividend Framework | `{project-root}/fin-guru/checklists/dividend-framework.md` | Dividend Specialist |
| General Quality | `{project-root}/fin-guru/checklists/` | QA Advisor, Compliance Officer |

## Workflow

1. Load the appropriate checklist from `{project-root}/fin-guru/checklists/`
2. Apply each checklist item to the target deliverable
3. Document pass/fail status for each item
4. Generate summary with remediation requirements for failed items
5. Provide final verdict: PASS, CONDITIONAL PASS, or FAIL

## Requirements

- Every checklist item must be explicitly evaluated
- Failed items must include specific remediation steps
- Timestamp all checklist executions with `{current_date}`
- Document reviewer identity in checklist output
