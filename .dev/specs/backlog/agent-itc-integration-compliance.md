# Agent ITC Integration - Compliance Officer

**Generated:** 2026-01-09 20:03:32 CST
**Status:** Ready for Implementation
**RBP Compatible:** Yes

## Problem Statement

### Why This Exists

The Compliance Officer agent is missing ITC Risk Models API integration that was added to Market Researcher, Strategy Advisor, and Quant Analyst during the ITC implementation. This creates an inconsistency where three agents can check market-implied risk signals but the compliance gatekeeper cannot.

**Who It's For:** Compliance Officer agent when reviewing strategy approvals, position limit assessments, and risk dashboard validation for ITC-supported tickers (TSLA, AAPL, MSTR, NFLX, SP500, commodities).

**Cost of NOT Doing This:** Compliance reviews lack market-implied risk signals that other agents use, potentially approving strategies without considering ITC's high-risk warnings (>0.7 threshold) that might trigger position size reductions or additional risk disclosure requirements.

### Use Cases

1. **Strategy Approval Validation:** When Strategy Advisor presents a buy ticket, Compliance can cross-check ITC risk score to ensure high-risk entries (>0.7) have appropriate position sizing and risk disclosures
2. **Position Limit Monitoring:** Use ITC risk bands to inform dynamic position limits (e.g., reduce max allocation when ticker approaches high-risk price zones)
3. **Risk Dashboard Completeness:** Include ITC risk scores in compliance reports alongside VaR/CVaR for comprehensive risk view

## Technical Requirements

### Architecture Overview

**Pattern:** Follow existing ITC integration pattern established in other agents:
- Add `<tool>` entry in agent's critical-actions section
- Add `<workflow>` with execution steps
- Add example command blocks
- Add divergence detection guidance

**No Code Changes Required:** CLI tool (`src/analysis/itc_risk_cli.py`) already exists and is production-ready with 31 passing tests.

### Agent Prompt Updates

**File:** `.claude/commands/fin-guru/agents/compliance-officer.md`

**Location:** After line 29 (after existing tool definitions, before `</critical-actions>`)

**Content to Add:**

```markdown
  <i>🔍 ITC RISK VALIDATION: Use itc_risk_cli.py to cross-validate strategy approvals with market-implied risk for supported tickers</i>
```

**Location:** After menu section, before workflows section (around line 70)

**Content to Add:**

```markdown
<tool name="ITC Risk Models API">
  <purpose>
    Market-implied risk validation for compliance reviews. Cross-check quantitative risk metrics
    with ITC's price-based risk scores for strategy approval and position limit decisions.
  </purpose>

  <supported_tickers universe="tradfi">
    TSLA, AAPL, MSTR, NFLX, SP500, DXY, XAUUSD, XAGUSD, XPDUSD, PL, HG, NICKEL
  </supported_tickers>

  <supported_tickers universe="crypto">
    BTC, ETH, and 27 others (see calculator for full list)
  </supported_tickers>

  <when_to_use>
    - Strategy Advisor presents buy ticket for ITC-supported ticker
    - Position limit review for high-volatility holdings
    - Risk dashboard validation requiring multi-source risk assessment
  </when_to_use>
</tool>

<workflow name="ITC Risk Validation for Strategy Approval" type="compliance-check">
  <trigger>Strategy Advisor submits buy ticket for TSLA, AAPL, MSTR, NFLX, or other ITC-supported ticker</trigger>

  <execution>
    <step n="1">Check if ticker is ITC-supported (see supported_tickers list above)</step>
    <step n="2">Run ITC risk check: uv run python src/analysis/itc_risk_cli.py TICKER --universe tradfi</step>
    <step n="3">Compare ITC risk score with internal VaR/Sharpe metrics from Quant Analyst</step>
    <step n="4">Apply compliance decision rules based on risk divergence</step>
  </execution>

  <decision_rules>
    <rule condition="ITC risk > 0.7 AND internal VaR low">
      Action: CONDITIONAL APPROVAL with position size reduction to 50% of proposed allocation
      Rationale: Market-implied risk signals elevated despite historical metrics showing low risk
      Required Disclosure: "ITC market risk elevated - reducing position size as precaution"
    </rule>

    <rule condition="ITC risk > 0.7 AND internal VaR high">
      Action: REVISIONS REQUIRED - recommend waiting for pullback or using dollar-cost averaging
      Rationale: Both market-implied and quantitative risk elevated
      Required Disclosure: "High risk on multiple measures - entry timing suboptimal"
    </rule>

    <rule condition="ITC risk < 0.3 AND internal VaR high">
      Action: FLAG FOR INVESTIGATION but approve conditionally
      Rationale: Divergence suggests either market underpricing risk or internal metrics stale
      Required Disclosure: "Risk metrics diverge - monitor closely post-entry"
    </rule>

    <rule condition="ITC risk 0.3-0.7 (moderate) matching internal metrics">
      Action: APPROVE with standard risk disclosure
      Rationale: Risk assessment alignment across methodologies
    </rule>
  </decision_rules>

  <example>
    <command purpose="Validate TSLA buy ticket strategy approval">
      uv run python src/analysis/itc_risk_cli.py TSLA --universe tradfi
    </command>

    <output_interpretation>
      Current Risk Score: 0.82 (HIGH)
      Risk Level: 🔴 HIGH (> 0.7)
      Current Price: $445.23
      High Risk Threshold: $500 (distance: +12.3%)

      Compliance Decision: CONDITIONAL APPROVAL
      - Reduce proposed $10k allocation to $5k (50% reduction)
      - Add disclosure: "ITC market risk elevated (0.82/1.0) - proceeding with reduced size"
      - Monitor: If price approaches $500, reassess position
    </output_interpretation>
  </example>
</workflow>

<guidance type="ITC-Internal Divergence Analysis">
  When ITC risk diverges from internal quantitative metrics, investigate root cause:

  **ITC High + Internal Low Risk:**
  - Possible Causes: Price approaching resistance, recent volatility spike not in 90-day VaR window, sentiment shift
  - Compliance Action: Reduce position size, add monitoring trigger, require re-approval if price moves >5%

  **ITC Low + Internal High Risk:**
  - Possible Causes: Recent drawdown, high historical volatility, market underpricing near-term risk
  - Compliance Action: Approve but flag for weekly monitoring, investigate why market isn't pricing in risk

  **Both Elevated (>0.7 ITC, >15% VaR95):**
  - Compliance Action: BLOCK entry until risk subsides or use phased entry (3 tranches over 6 weeks)
</guidance>
```

## Edge Cases & Error Handling

### Unsupported Tickers

**Scenario:** Strategy Advisor submits buy ticket for NVDA (not ITC-supported)

**Handling:**
- Compliance Officer attempts ITC check → CLI returns error "NVDA not supported by ITC API"
- Compliance proceeds with internal metrics only (VaR, Sharpe, volatility)
- No blocking issue - ITC is supplemental, not required

### ITC API Unavailable

**Scenario:** ITC API down or rate limit hit

**Handling:**
- CLI retries 3 times with exponential backoff
- If all retries fail, agent sees error message
- Compliance Officer logs: "ITC unavailable - proceeding with internal metrics only"
- Strategy approval continues using risk_metrics_cli.py and volatility_cli.py
- No blocking issue - degraded mode acceptable

### Divergence Between ITC and All Internal Metrics

**Scenario:** ITC shows 0.85 (very high risk), but VaR95 is 2.1% (low), Sharpe is 1.8 (strong), volatility is 12% (low)

**Handling:**
- Compliance Officer flags this as "HIGH PRIORITY INVESTIGATION"
- Creates investigation task: "Determine why ITC risk (0.85) massively diverges from all internal metrics"
- Conditional approval: Approve 25% of proposed allocation pending investigation resolution
- Documents in compliance log with timestamp for audit trail

## User Experience

### Mental Model

**Compliance Officer Perspective:** ITC provides a "second opinion" from the market's pricing behavior. When ITC disagrees with internal quantitative metrics, it's not about trusting one over the other - it's a signal to investigate and proceed cautiously.

**Key Principle:** ITC risk > 0.7 doesn't automatically block a trade, but it does trigger position size reductions and additional disclosure requirements.

### Confusion Points & Solutions

**1. Confusion: "Do I always need to check ITC for every strategy approval?"**

**Solution:** No - only check ITC for supported tickers (TSLA, AAPL, MSTR, NFLX, SP500, commodities). For unsupported tickers (NVDA, PLTR, etc.), use internal metrics only.

**2. Confusion: "What if ITC says high risk but I want to approve anyway?"**

**Solution:** You can approve, but you MUST:
- Reduce position size (typically 50% reduction for ITC >0.7)
- Add explicit risk disclosure to buy ticket
- Document decision rationale in compliance log

**3. Confusion: "ITC and VaR disagree - which one wins?"**

**Solution:** Neither "wins" - divergence is valuable information:
- Both high → Strong signal to reduce size or delay
- One high, one low → Investigate why, proceed cautiously with reduced size
- Both low → Normal approval process

### Feedback Requirements

**At Each Step:**

1. **ITC Check Start:** "🔍 Checking ITC risk for TSLA..."
2. **ITC Result:** "✅ ITC Risk: 0.42 (MEDIUM) - within acceptable range"
3. **Divergence Detected:** "⚠️ DIVERGENCE: ITC risk (0.82) HIGH but VaR95 (2.1%) LOW - investigating..."
4. **Compliance Decision:** "✓ CONDITIONAL APPROVAL: Reduce allocation to $5k (50% of proposed), add ITC risk disclosure"

## Scope & Tradeoffs

### In Scope (MVP - All Implemented)

✅ **Core Functionality:**
- Add ITC tool definition to Compliance Officer agent
- Add ITC Risk Validation workflow with decision rules
- Add divergence analysis guidance
- Add example command blocks

✅ **Integration:**
- No code changes needed (CLI already exists)
- Agent prompt updates only
- Follows established pattern from other 3 agents

✅ **Quality Features:**
- Decision rule matrix for all risk scenarios
- Divergence investigation guidance
- Example output interpretation
- Audit trail documentation requirements

### Out of Scope

❌ **Automated Risk Scoring:** No automated compliance score calculation (human judgment required)
❌ **Historical ITC Trend Analysis:** No tracking of ITC risk changes over time (point-in-time only)
❌ **Integration with External Compliance Systems:** No export to Bloomberg Terminal or other external tools

### Technical Debt Knowingly Accepted

**1. No Automated Compliance Score:**
- **Accepted:** Compliance Officer must manually interpret ITC + internal metrics and apply decision rules
- **Why:** Compliance decisions require human judgment and context awareness
- **Mitigation:** Clear decision rule matrix provides consistent framework
- **Future:** Could add compliance score formula if pattern emerges

**2. No ITC Risk Trend Tracking:**
- **Accepted:** Can't show "ITC risk was 0.3 last week, now 0.8 - big spike!"
- **Why:** No persistent storage layer for historical ITC data
- **Mitigation:** Agents can manually run ITC checks weekly and compare
- **Future:** Could add CSV logging if historical trends become critical

## Integration Requirements

### Agent Workflow Integration

**Compliance Officer:** When reviewing Strategy Advisor buy tickets:
1. Load buy ticket content
2. Extract ticker symbol
3. Check if ticker in ITC supported list
4. If supported: Run `itc_risk_cli.py TICKER --universe tradfi`
5. Parse JSON output for current_risk_score
6. Apply decision rules based on risk level and internal metric comparison
7. Document ITC risk in compliance review output

### File Modifications Required

**Modified Files:**
- `.claude/commands/fin-guru/agents/compliance-officer.md` (add ITC tool and workflow sections)

**No New Files Created**

## Security & Compliance

### Sensitive Data

**API Key Storage:**
- ITC_API_KEY stored in `.env` file (git-ignored)
- Already configured during ITC implementation
- Compliance Officer agent uses same key as other agents

**User Data:**
- No PII transmitted to ITC API (only ticker symbols)
- No portfolio holdings shared with external service

### Compliance Considerations

**Educational Use Only:**
- All Compliance Officer outputs include disclaimer: "For educational purposes only. Not investment advice."
- ITC data is supplemental to internal analysis, not authoritative
- Human review required for all strategy approvals (no auto-approval based on ITC alone)

**Audit Trail:**
- All ITC checks must be documented in compliance logs with timestamp
- Decision rationale must reference ITC risk score when applicable
- Divergence investigations must be logged for audit purposes

## Success Criteria & Testing

### Acceptance Criteria

**Functional Requirements:**

✅ **FR1:** Compliance Officer agent can invoke ITC risk check for supported tickers
- **Test:** Manual agent activation, provide TSLA buy ticket, verify ITC check runs
- **Expected:** Agent runs `itc_risk_cli.py TSLA --universe tradfi` and interprets output

✅ **FR2:** Compliance Officer applies decision rules correctly based on ITC risk level
- **Test:** Provide buy ticket with ITC risk 0.85 (high) and VaR 2.1% (low)
- **Expected:** Agent returns "CONDITIONAL APPROVAL with 50% position size reduction"

✅ **FR3:** Compliance Officer handles unsupported tickers gracefully
- **Test:** Provide NVDA buy ticket (not ITC-supported)
- **Expected:** Agent proceeds with internal metrics only, no error

✅ **FR4:** Compliance Officer documents ITC risk in compliance review output
- **Test:** Review compliance decision output
- **Expected:** Output includes "ITC Risk: 0.XX (LEVEL)" and decision rationale

**Non-Functional Requirements:**

✅ **NFR1:** ITC check completes within 5 seconds
- **Test:** Run ITC CLI manually, measure time
- **Expected:** < 5 seconds for single ticker

✅ **NFR2:** Agent prompt remains under token limits
- **Test:** Load full agent prompt in Claude
- **Expected:** No truncation warnings

### Testing Strategy

**Manual Agent Testing:**

**Test 1: Normal Flow - ITC Supported Ticker**
```bash
# Activate Compliance Officer agent
# Provide buy ticket: "Review this: Buy $10k TSLA at $445"
# Expected: Agent runs ITC check, interprets risk, applies decision rule
```

**Test 2: Divergence Detection**
```bash
# Activate Compliance Officer agent
# Provide: "Buy ticket for TSLA. Internal VaR is 2.1% (low), but check ITC risk"
# Expected: Agent detects divergence, recommends investigation, conditional approval
```

**Test 3: Unsupported Ticker**
```bash
# Activate Compliance Officer agent
# Provide: "Review buy ticket for NVDA $8k"
# Expected: Agent skips ITC check (not supported), uses internal metrics only
```

**Test 4: High Risk Scenario**
```bash
# Manually set TSLA ITC risk to 0.92 (very high)
# Activate agent with buy ticket
# Expected: Agent blocks or heavily reduces allocation, requires phased entry
```

**Integration Validation:**

1. Verify Compliance Officer agent loads without errors after update
2. Verify ITC tool and workflow sections render correctly in agent prompt
3. Verify example commands execute successfully when copy-pasted
4. Verify decision rules align with other agents' ITC integration patterns

## Implementation Tasks

<!-- RBP-TASKS-START -->

### Task 1: Add ITC Tool Definition to Compliance Officer
- **ID:** compliance-itc-001
- **Dependencies:** none
- **Files:** `.claude/commands/fin-guru/agents/compliance-officer.md`
- **Acceptance:** ITC tool section added after line 29 with purpose, supported tickers, and when_to_use guidance
- **Tests:** Manual: Load agent prompt, verify no syntax errors

### Task 2: Add ITC Risk Validation Workflow
- **ID:** compliance-itc-002
- **Dependencies:** compliance-itc-001
- **Files:** `.claude/commands/fin-guru/agents/compliance-officer.md`
- **Acceptance:** Workflow section added with trigger, execution steps, decision rules, and example interpretation
- **Tests:** Manual: Activate agent, provide buy ticket, verify workflow executes

### Task 3: Add Divergence Analysis Guidance
- **ID:** compliance-itc-003
- **Dependencies:** compliance-itc-002
- **Files:** `.claude/commands/fin-guru/agents/compliance-officer.md`
- **Acceptance:** Guidance section added for ITC-internal metric divergence scenarios with compliance actions
- **Tests:** Manual: Test divergence scenario, verify agent investigates and documents

### Task 4: Validate Agent Integration End-to-End
- **ID:** compliance-itc-004
- **Dependencies:** compliance-itc-003
- **Files:** None (testing only)
- **Acceptance:** All 4 test scenarios pass (normal flow, divergence, unsupported ticker, high risk)
- **Tests:** Execute test suite documented in Testing Strategy section

<!-- RBP-TASKS-END -->

### Test Command

```bash
# Manual testing only - no automated tests for agent prompts
# Activate Compliance Officer agent in Claude Code and run test scenarios
```

## Implementation Notes

### Codebase-Specific Guidance

**Files to Modify:**

1. **`.claude/commands/fin-guru/agents/compliance-officer.md`**
   - Follow existing agent structure (tool definitions before workflows)
   - Use same XML tag style as other agents (`<tool>`, `<workflow>`, `<guidance>`)
   - Match indentation and formatting of existing sections
   - Add content after line 29 (critical-actions) and around line 70 (after menu)

**Pattern to Follow:**

Reference Market Researcher agent for ITC integration pattern:
- Tool definition format
- Workflow execution steps format
- Example command block format
- Divergence analysis structure

**Testing Workflow:**

1. Read current compliance-officer.md file
2. Add ITC tool section (compliance-itc-001)
3. Add ITC workflow section (compliance-itc-002)
4. Add divergence guidance (compliance-itc-003)
5. Manually activate agent and test scenarios (compliance-itc-004)

---

**End of Specification**

**Status:** ✅ Ready for Implementation - Zero Open Questions
