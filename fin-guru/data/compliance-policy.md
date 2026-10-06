<!-- Finance Guru(tm) Compliance Policy | v1.0 | 2026-10-06 -->

# Compliance Policy

## Disclaimer

This document is for _educational purposes only_ and does not constitute investment, legal, or tax advice. It is the standard a specialist uses to review a deliverable. Consult a licensed financial, tax, and legal professional before acting.

---

## Educational boundary

Every analysis, ticket, and review stays on the educational side of the Investment Advisers Act line.

- State that the work is educational and is not investment advice.
- Recommend that the owner consult a licensed professional.
- Disclose that investments can lose principal.
- Do not present a personalized recommendation as if a licensed adviser had approved it.

The required footer is:

> _Educational Notice: For educational purposes only; not investment advice. Consult a licensed financial professional before acting. All investments involve risk, including possible loss of principal._

An options or hedge note adds that premium spent on protection is lost if the market rises or stays flat, and that closing a hedge leaves later drawdowns unhedged.

## Required elements

A deliverable is incomplete until it has all five:

1. Analytical framework: the method and its theoretical basis.
2. Source attribution: each data source, with a timestamp.
3. Assumption documentation: the assumptions, and how the result moves if they change.
4. Risk quantification: VaR, Sharpe, maximum drawdown, or the metric the question actually needs, each from a calculator command.
5. Implementation guidance: the next step, or an explicit statement that no action is proposed.

Separate facts from assumptions. A claim without a source is an assumption.

## Data handling

- Never include account numbers, Social Security numbers, or other personal identifiers in a deliverable or in this repository.
- Timestamp time-sensitive figures, and cross-check a critical figure against a second source when one is available.
- Personal values stay in the instance directory. This policy file holds the rule, not the owner's numbers.

## What is not a compliance breach

A monthly distribution variance of ±5–15% on an options-based income fund is normal. Judge those holdings on trailing 12-month yield. Block only a red flag from `modern-income-vehicles.md`: a sustained decline above 30%, NAV erosion, or a strategy change.

## ITC at draft and at clearance

While a specialist drafts a buy ticket, ITC is an advisory overlay. A high score is written on the draft. The strategy advisor and the dividend specialist still write the draft.

Compliance clearance is the next step, and it keeps DR-4. The officer applies DR-1 through DR-5 in `.claude/skills/fin-guru-compliance-review/itc-divergence.md`. DR-4 is a mandatory BLOCK when the ITC score is above 0.85 or divergence is above 30%, including when VaR, drawdown, and concentration are inside their limits. A draft becomes final only after PASS or CONDITIONAL PASS. BLOCK and REVISIONS REQUIRED leave the ticket blocked.

Record the score and the decision rule on both the draft and the clearance. Concentration still follows `risk-framework.md`. Clearance passes when that concentration rule and the ITC decision rule both pass.
