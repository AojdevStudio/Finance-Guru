---
title: "Finance Guru Research Workflow"
description: "Comprehensive task workflow for conducting financial research with market intelligence, security analysis, and data validation protocols."
category: "Task Workflow"
subcategory: "Research Phase"
product_line: "Finance Guru"
audience: "AI Agent System"
status: "Active"
author: "AOJDevStudio"
created_date: "2025-09-17"
last_updated: "2025-09-17"
tags:
  - finance-guru
  - research-workflow
  - market-intelligence
  - security-analysis
  - data-validation
---

<!-- Version: 1.0.0 | Last Modified: 2025-09-17 | Author: AOJDevStudio -->
<!-- Description: Comprehensive research workflow for Finance Guru agents -->
<!-- Compatibility: Finance-Guru-Framework, exa-mcp, web-search-tool, sequential-thinking-mcp -->

<!-- BEGIN: research_workflow_definition -->

# Finance Guru Research Workflow

## Purpose and Scope

This workflow defines the comprehensive research methodology for Finance Guru agents, establishing systematic protocols for market intelligence gathering, security analysis, and data validation. The workflow ensures consistent, high-quality research output that forms the foundation for subsequent quantitative analysis and strategy development.

### Research Mode Activation Criteria

**Use When:**

- Security-specific questions requiring current market data
- Market conditions analysis and environmental assessment
- Policy changes and regulatory developments
- Product specifications and fundamentals analysis
- Any fact-based inquiry likely to change over time

**Core Research Policy:**

- Cite all sources with timestamps
- Separate verifiable facts from analytical assumptions
- Cross-validate critical data points from multiple sources
- Document data collection methodology and limitations

<!-- END: research_workflow_definition -->

<!-- BEGIN: usage_scenarios -->

## Usage Scenarios

### Scenario 1: New Investment Analysis

**Trigger**: User requests analysis of unfamiliar security or market segment
**Scope**: Comprehensive fundamental and market research
**Timeline**: 30-45 minutes for standard analysis
**Deliverables**: Research summary, peer comparison, risk assessment

### Scenario 2: Market Environment Assessment

**Trigger**: Strategy development requiring current market context
**Scope**: Macro environment, rates, liquidity, volatility analysis
**Timeline**: 15-20 minutes for market snapshot
**Deliverables**: Market environment report, risk factor identification

### Scenario 3: Policy Impact Analysis

**Trigger**: Regulatory or policy changes affecting portfolio strategy
**Scope**: Policy research, impact assessment, strategy implications
**Timeline**: 20-30 minutes for focused analysis
**Deliverables**: Policy impact summary, strategic recommendations

### Scenario 4: Competitive Intelligence

**Trigger**: Peer comparison or industry analysis requirements
**Scope**: Industry dynamics, competitive positioning, relative valuation
**Timeline**: 25-35 minutes for comprehensive review
**Deliverables**: Competitive landscape map, relative positioning analysis

### Scenario 5: Due Diligence Research

**Trigger**: Deep-dive analysis for significant investment decisions
**Scope**: Comprehensive security analysis, risk assessment, opportunity evaluation
**Timeline**: 45-60 minutes for thorough investigation
**Deliverables**: Complete due diligence package, investment recommendation

<!-- END: usage_scenarios -->

<!-- BEGIN: step_by_step_instructions -->

## Step-by-Step Task Instructions

### Phase 0: Temporal Context Initialization (MANDATORY - 1 minute)

⚠️ **CRITICAL REQUIREMENT**: This phase is MANDATORY and BLOCKING. All subsequent research activities are PROHIBITED until temporal context is successfully established.

#### Step 0.1: Execute Temporal Awareness Protocol

**Purpose**: Establish current date context to ensure all research includes appropriate temporal qualifiers, preventing retrieval of outdated information that could lead to poor investment decisions.

**Execution**:

```bash
# Get current date and year
date +"%Y-%m-%d"
date +"%Y"
```

**Store Results**:
- `{current_date}` = Full date (e.g., "2025-10-12")
- `{current_year}` = Year only (e.g., "2025")

**Validation Checkpoint**:
- [ ] Current date successfully retrieved and stored as {current_date}
- [ ] Current year successfully extracted and stored as {current_year}
- [ ] Date format verified as YYYY-MM-DD
- [ ] Year is within reasonable range (2025-2030)

**On Failure**: If temporal context cannot be established, STOP ALL RESEARCH ACTIVITY and report error to user. Do not proceed to Phase 1.

#### Step 0.2: Establish Search Enhancement Protocol

**Search Query Enhancement Rules** (MANDATORY):

All web searches conducted in this workflow MUST include temporal qualifiers. Non-compliant searches are PROHIBITED.

**Temporal Qualifier Requirements**:
1. Include `{current_year}` in query, OR
2. Include "latest" keyword, OR
3. Include "current" keyword

**Examples**:

✅ **COMPLIANT QUERIES**:
- "Tesla stock analysis {current_year} latest"
- "Federal Reserve policy October {current_year}"
- "Current S&P 500 valuation metrics"
- "Latest GDP growth data United States"

❌ **NON-COMPLIANT QUERIES** (DO NOT USE):
- "Tesla stock analysis"
- "Federal Reserve policy"
- "S&P 500 valuation metrics"
- "GDP growth data"

#### Step 0.3: Define Data Freshness Requirements

**Freshness Thresholds by Data Type**:

| Data Type | Maximum Age | Validation Action |
|-----------|-------------|-------------------|
| Market Data (prices, quotes) | Same-day | REJECT if older |
| Economic Indicators | 30 days | FLAG if older |
| Regulatory Changes | 90 days | FLAG if older |
| Company Financials | Current quarter | FLAG if outdated |
| Analyst Ratings | 30 days | FLAG if older |

**Source Validation Protocol**:
- Every source MUST be timestamped with collection date
- Compare source date against freshness requirements
- Flag or reject sources exceeding age thresholds
- Document any freshness violations in research report

**Quality Gate**:
- [ ] Freshness thresholds understood and documented
- [ ] Source validation protocol ready for implementation
- [ ] Timestamp documentation system prepared

**Completion Confirmation**:

Display confirmation message before proceeding:

```
✅ TEMPORAL AWARENESS CONFIRMED

Current Date: {current_date}
Current Year: {current_year}

📋 Search Enhancement Rules Active:
• All queries MUST include {current_year}, "latest", or "current"
• Market data: Same-day only
• Economic data: Within 30 days
• Regulatory data: Within 90 days

Proceeding to Phase 1: Research Planning and Scoping
```

---

### Phase 1: Research Planning and Scoping (5-10 minutes)

#### Step 1.1: Define Research Objectives

- **Clarify specific research questions** requiring answers
- **Identify key decisions** the research will inform
- **Establish scope boundaries** (breadth vs. depth trade-offs)
- **Set quality standards** for source verification and data validation

#### Step 1.2: Determine Research Methodology

- **Select appropriate tools** (exa for deep research, web-search for current events)
- **Plan research sequence** (macro to micro, general to specific)
- **Identify critical data points** requiring cross-validation
- **Establish time allocation** for each research component

#### Step 1.3: Prepare Research Framework

- **Create source tracking system** for timestamp documentation
- **Establish fact vs. assumption categories** for clear separation
- **Define data quality criteria** for source validation
- **Set up cross-validation protocols** for critical findings

<!-- CONFIG_START: research_tools -->
<!-- primary_tool: exa-mcp (deep market research) -->
<!-- secondary_tool: web-search-tool (current events, news) -->
<!-- orchestration: sequential-thinking-mcp -->
<!-- validation: multi-source cross-checking -->
<!-- CONFIG_END: research_tools -->

### Phase 2: Market Environment Research (10-15 minutes)

#### Step 2.1: Macroeconomic Environment Assessment

**Tools**: exa, web-search-tool
**Focus Areas**:

- **Interest Rate Environment**: Current Fed policy, yield curve analysis, rate expectations
- **Economic Indicators**: GDP growth, inflation trends, employment data
- **Credit Conditions**: Corporate spreads, lending standards, default rates
- **Currency Markets**: Dollar strength, international flows, FX volatility

**Quality Checkpoints**:

- [ ] All macro data timestamped within last 30 days
- [ ] Federal Reserve policy stance accurately captured
- [ ] Economic data sourced from official government/central bank sources
- [ ] Currency trends validated across multiple financial data providers

#### Step 2.2: Market Liquidity and Volatility Analysis

**Tools**: exa, web-search-tool
**Focus Areas**:

- **Equity Market Conditions**: VIX levels, market breadth, trading volumes
- **Fixed Income Markets**: Treasury liquidity, corporate bond spreads, issuance trends
- **Commodity Markets**: Energy, metals, agricultural price trends
- **Alternative Markets**: REIT performance, cryptocurrency correlations

**Quality Checkpoints**:

- [ ] Volatility metrics compared to historical norms
- [ ] Liquidity conditions assessed across multiple asset classes
- [ ] Market stress indicators evaluated and documented
- [ ] Cross-asset correlations identified and analyzed

#### Step 2.3: Regulatory and Policy Landscape

**Tools**: web-search-tool, exa
**Focus Areas**:

- **Financial Regulation**: SEC/CFTC rule changes, banking regulations
- **Monetary Policy**: Central bank communications, policy meeting outcomes
- **Fiscal Policy**: Government spending, tax policy changes, debt dynamics
- **International Policy**: Trade policy, sanctions, international agreements

**Quality Checkpoints**:

- [ ] Regulatory changes sourced from official government websites
- [ ] Policy timing and implementation dates clearly documented
- [ ] Impact assessment includes both direct and indirect effects
- [ ] International policy implications considered for global exposures

### Phase 3: Security-Specific Research (15-20 minutes)

#### Step 3.1: Fundamental Analysis

**Tools**: exa (deep financial analysis)
**Focus Areas**:

- **Financial Health**: Balance sheet strength, debt levels, cash generation
- **Profitability Metrics**: Margin trends, return on capital, earnings quality
- **Growth Prospects**: Revenue growth, market expansion, competitive advantages
- **Management Assessment**: Track record, capital allocation, governance quality

**Research Protocol**:

1. **Gather latest financial statements** (10-K, 10-Q filings)
2. **Analyze key financial ratios** vs. historical trends and peers
3. **Review management commentary** from earnings calls and investor presentations
4. **Assess business model sustainability** and competitive positioning

**Quality Checkpoints**:

- [ ] Financial data sourced from SEC filings or verified financial databases
- [ ] Ratio analysis includes peer comparison context
- [ ] Management assessment includes objective performance metrics
- [ ] Business model evaluation considers industry disruption risks

#### Step 3.2: Market Performance and Valuation

**Tools**: exa, web-search-tool
**Focus Areas**:

- **Price Performance**: Absolute and relative performance vs. benchmarks
- **Valuation Metrics**: P/E ratios, price-to-book, enterprise value multiples
- **Technical Indicators**: Momentum, support/resistance levels, volume patterns
- **Analyst Coverage**: Consensus estimates, recommendation distribution, target prices

**Research Protocol**:

1. **Collect current market data** with exact timestamps
2. **Calculate valuation metrics** using most recent financial data
3. **Compare valuations** to historical ranges and peer group
4. **Review institutional ownership** and recent trading patterns

**Quality Checkpoints**:

- [ ] Market data timestamped to exact minute of collection
- [ ] Valuation calculations verified against multiple data sources
- [ ] Peer comparisons use consistent methodology and timeframes
- [ ] Institutional data sourced from verified holdings databases

#### Step 3.3: Risk Factor Assessment

**Tools**: exa, sequential-thinking-mcp
**Focus Areas**:

- **Business Risks**: Competitive threats, regulatory exposure, operational risks
- **Financial Risks**: Leverage, liquidity, credit quality, refinancing needs
- **Market Risks**: Beta analysis, correlation patterns, volatility assessment
- **ESG Risks**: Environmental, social, governance factors affecting valuation

**Research Protocol**:

1. **Identify material risk factors** from regulatory filings and analyst reports
2. **Quantify risk exposures** where possible using available metrics
3. **Assess risk mitigation strategies** employed by management
4. **Evaluate risk-adjusted return** profiles vs. alternatives

**Quality Checkpoints**:

- [ ] Risk factors sourced from authoritative disclosures
- [ ] Quantitative risk metrics calculated using validated methodologies
- [ ] Risk mitigation strategies verified through management communications
- [ ] Risk-return analysis includes appropriate benchmarking

### Phase 4: Competitive and Industry Analysis (10-15 minutes)

#### Step 4.1: Industry Dynamics Research

**Tools**: exa (industry analysis)
**Focus Areas**:

- **Industry Structure**: Market concentration, barriers to entry, pricing power
- **Growth Drivers**: Market size trends, technological disruption, regulatory changes
- **Cyclical Patterns**: Economic sensitivity, seasonal factors, long-term trends
- **Value Chain Analysis**: Supplier power, customer concentration, margin distribution

**Quality Checkpoints**:

- [ ] Industry data sourced from trade associations and research firms
- [ ] Growth trends validated through multiple independent sources
- [ ] Cyclical analysis includes sufficient historical context
- [ ] Value chain assessment considers all major participants

#### Step 4.2: Peer Comparison and Benchmarking

**Tools**: exa, web-search-tool
**Focus Areas**:

- **Financial Performance**: Revenue growth, profitability, efficiency metrics
- **Market Position**: Market share, competitive advantages, brand strength
- **Valuation Comparison**: Relative multiples, premium/discount analysis
- **Strategic Positioning**: Business model differentiation, strategic initiatives

**Research Protocol**:

1. **Identify appropriate peer group** based on business model and market exposure
2. **Gather comparable financial metrics** for standardized analysis
3. **Analyze relative performance** across multiple dimensions
4. **Assess competitive positioning** and strategic differentiation

**Quality Checkpoints**:

- [ ] Peer group selection methodology clearly documented
- [ ] Financial comparisons use consistent accounting standards
- [ ] Performance analysis covers multiple time periods
- [ ] Strategic assessment includes forward-looking considerations

### Phase 5: Data Validation and Source Documentation (5-10 minutes)

#### Step 5.1: Source Verification Protocol

**Requirements**:

- **Primary Sources**: Government agencies, regulatory filings, company disclosures
- **Secondary Sources**: Reputable financial news, established research firms
- **Data Providers**: Bloomberg, Reuters, official exchange data
- **Academic Sources**: Peer-reviewed research, central bank publications

**Validation Process**:

1. **Cross-reference critical data** across minimum 2 independent sources
2. **Verify publication dates** and data collection timestamps
3. **Assess source credibility** and potential bias factors
4. **Document methodology** for any derived calculations

#### Step 5.2: Fact vs. Assumption Separation

**Facts (Verifiable Data)**:

- Market prices, financial statement data, regulatory announcements
- Official economic statistics, central bank policy statements
- Company earnings results, dividend announcements
- Industry statistics from authoritative sources

**Assumptions (Analytical Judgments)**:

- Future growth projections, scenario probability assessments
- Management quality evaluations, competitive position assessments
- Market trend extrapolations, policy impact predictions
- Risk assessment conclusions, investment recommendations

**Documentation Protocol**:

1. **Create clear fact/assumption inventory** with source attribution
2. **Timestamp all time-sensitive facts** with data collection time
3. **Label all assumptions** with confidence levels and rationale
4. **Cross-validate facts** against independent sources where possible

#### Step 5.3: Research Quality Assurance

**Final Quality Checks**:

- [ ] All sources cited with complete attribution and timestamps
- [ ] Critical facts cross-validated from multiple independent sources
- [ ] Clear separation between verifiable facts and analytical assumptions
- [ ] Data collection methodology documented for reproducibility
- [ ] Source credibility assessed and any bias factors noted
- [ ] Research scope and limitations clearly acknowledged

<!-- END: step_by_step_instructions -->

<!-- BEGIN: tools_dependencies -->

## Required Tools and Dependencies

### Primary Research Tools

#### exa (Deep Market Research)

**Purpose**: Comprehensive financial analysis and market intelligence
**Usage**: Primary tool for fundamental analysis, industry research, competitive intelligence
**Capabilities**:

- Deep financial data retrieval and analysis
- Comprehensive market intelligence gathering
- Industry trend analysis and competitive positioning
- Historical data analysis and pattern recognition

**Best Practices**:

- Use for in-depth security analysis requiring comprehensive data
- Leverage for industry research and competitive intelligence
- Apply for historical trend analysis and pattern identification
- Utilize for cross-referencing complex financial relationships

#### web-search-tool (Current Events and News)

**Purpose**: Real-time market news and current event monitoring
**Usage**: Secondary tool for breaking news, policy changes, current market conditions
**Capabilities**:

- Real-time news and market event monitoring
- Policy announcement and regulatory change tracking
- Current market sentiment and analyst opinion gathering
- Breaking news that may impact investment decisions

**Best Practices**:

- Use for capturing current market sentiment and recent developments
- Apply for monitoring policy changes and regulatory announcements
- Leverage for gathering recent analyst opinions and market commentary
- Utilize for verifying current market conditions and sentiment

#### sequential-thinking-mcp (Workflow Orchestration)

**Purpose**: Complex workflow coordination and logical analysis
**Usage**: Primary tool for research workflow management and analytical thinking
**Capabilities**:

- Multi-step research process coordination
- Logical framework application for complex analysis
- Research methodology validation and quality control
- Cross-validation protocol management

**Best Practices**:

- Use for coordinating complex multi-source research workflows
- Apply for ensuring systematic coverage of all research dimensions
- Leverage for quality control and validation protocols
- Utilize for managing research timeline and deliverable creation

### Integration Requirements

#### Tool Coordination Protocol

1. **Sequential-thinking-mcp** manages overall research workflow
2. **exa** conducts deep analysis and comprehensive data gathering
3. **web-search-tool** supplements with current events and breaking news
4. **All tools** contribute to fact validation and cross-verification

#### Data Flow Management

- **Input**: Research objectives and scope definition
- **Process**: Systematic data gathering using coordinated tool deployment
- **Validation**: Cross-source verification and quality assurance
- **Output**: Comprehensive research package with source documentation

#### Quality Assurance Integration

- Multi-tool validation ensures comprehensive source coverage
- Sequential-thinking coordinates systematic quality checks
- exa provides deep analytical validation of financial metrics
- web-search-tool verifies current market conditions and sentiment

<!-- END: tools_dependencies -->

<!-- BEGIN: quality_checkpoints -->

## Quality Checkpoints

### Research Planning Quality Gates

#### Checkpoint 1.1: Objective Clarity

**Validation Criteria**:

- [ ] Research questions are specific and measurable
- [ ] Decision-making context clearly established
- [ ] Success criteria defined for research outcomes
- [ ] Resource allocation appropriate for research scope

**Quality Standards**:

- Research objectives align with intended decision-making requirements
- Scope boundaries prevent mission creep while ensuring adequate coverage
- Time allocation balances thoroughness with efficiency requirements
- Quality standards are achievable within available resources

#### Checkpoint 1.2: Methodology Appropriateness

**Validation Criteria**:

- [ ] Tool selection matches research requirements
- [ ] Research sequence logically structured
- [ ] Validation protocols adequate for data quality requirements
- [ ] Documentation standards support reproducibility

**Quality Standards**:

- Methodology selection based on proven research best practices
- Tool deployment optimized for research efficiency and accuracy
- Validation protocols ensure data integrity and source credibility
- Documentation enables independent verification and reproducibility

### Market Research Quality Gates

#### Checkpoint 2.1: Market Environment Completeness

**Validation Criteria**:

- [ ] All major macro factors assessed and documented
- [ ] Current market conditions accurately captured
- [ ] Policy environment comprehensively reviewed
- [ ] Cross-asset implications considered and evaluated

**Quality Standards**:

- Market assessment covers all material factors affecting investment decisions
- Current conditions analysis reflects most recent available data
- Policy analysis includes both announced and potential future changes
- Cross-asset analysis captures correlation and spillover effects

#### Checkpoint 2.2: Data Quality and Timeliness

**Validation Criteria**:

- [ ] All data sources are authoritative and current
- [ ] Timestamps document data collection timing
- [ ] Cross-validation performed for critical data points
- [ ] Data limitations and uncertainties acknowledged

**Quality Standards**:

- Data sourced from primary or highly credible secondary sources
- Timeliness appropriate for decision-making requirements
- Cross-validation protocols applied to material data points
- Uncertainty and limitation assessment prevents overconfidence

### Security Analysis Quality Gates

#### Checkpoint 3.1: Fundamental Analysis Rigor

**Validation Criteria**:

- [ ] Financial analysis based on verified data sources
- [ ] Peer comparisons use consistent methodologies
- [ ] Management assessment includes objective metrics
- [ ] Business model evaluation considers competitive dynamics

**Quality Standards**:

- Financial analysis employs institutional-quality methodologies
- Peer comparisons provide meaningful relative context
- Management assessment balances qualitative and quantitative factors
- Business model analysis considers long-term sustainability factors

#### Checkpoint 3.2: Risk Assessment Comprehensiveness

**Validation Criteria**:

- [ ] All material risk factors identified and assessed
- [ ] Risk quantification employs appropriate methodologies
- [ ] Risk mitigation strategies evaluated for effectiveness
- [ ] Risk-return analysis includes appropriate benchmarking

**Quality Standards**:

- Risk assessment covers business, financial, market, and operational risks
- Quantification methodologies are validated and appropriate
- Mitigation assessment considers both current and potential strategies
- Risk-return analysis enables informed decision-making

### Documentation Quality Gates

#### Checkpoint 4.1: Source Attribution Standards

**Validation Criteria**:

- [ ] All sources properly cited with complete attribution
- [ ] Timestamps document data collection timing
- [ ] Source credibility assessed and documented
- [ ] Fact vs. assumption separation maintained throughout

**Quality Standards**:

- Citation standards enable independent verification
- Timestamp documentation supports data currency assessment
- Source credibility analysis prevents reliance on unreliable information
- Fact/assumption separation prevents analytical bias

#### Checkpoint 4.2: Research Reproducibility

**Validation Criteria**:

- [ ] Methodology documentation enables replication
- [ ] Data sources are accessible for verification
- [ ] Calculation methods are transparent and verifiable
- [ ] Limitations and uncertainties clearly acknowledged

**Quality Standards**:

- Documentation quality supports independent replication
- Source accessibility enables ongoing verification
- Calculation transparency builds confidence in results
- Limitation acknowledgment prevents overconfidence in conclusions

<!-- END: quality_checkpoints -->

<!-- BEGIN: output_specifications -->

## Output Specifications

### Research Summary Package

#### Executive Research Summary (1-2 pages)

**Structure**:

- **Key Findings**: Top 3-5 critical insights with supporting evidence
- **Investment Thesis**: Clear 2-3 sentence summary of research conclusions
- **Risk Assessment**: Material risk factors and mitigation considerations
- **Recommendation**: Specific next steps and additional research needs

**Quality Standards**:

- Executive-ready formatting and professional presentation
- Clear, actionable insights that directly inform decision-making
- Balanced perspective including both opportunities and risks
- Specific recommendations with priority levels and timelines

#### Detailed Research Report (5-10 pages)

**Section Structure**:

1. **Market Environment Analysis**

   - Macroeconomic context and policy environment
   - Market liquidity and volatility assessment
   - Cross-asset implications and correlations
   - Regulatory landscape and policy impacts

2. **Security Fundamental Analysis**

   - Financial health and profitability assessment
   - Growth prospects and competitive positioning
   - Management quality and capital allocation
   - Business model sustainability analysis

3. **Industry and Competitive Analysis**

   - Industry dynamics and structural factors
   - Peer comparison and relative positioning
   - Market share and competitive advantages
   - Strategic initiatives and differentiation

4. **Risk Factor Assessment**

   - Business and operational risk analysis
   - Financial and credit risk evaluation
   - Market and systematic risk factors
   - ESG and regulatory risk considerations

5. **Valuation and Performance Analysis**
   - Current valuation metrics and historical context
   - Peer comparison and relative valuation
   - Performance attribution and trend analysis
   - Technical factors and momentum indicators

**Quality Standards**:

- Comprehensive coverage of all material research dimensions
- Clear logical flow from market context to specific security analysis
- Balanced analysis incorporating multiple perspectives and viewpoints
- Professional formatting with charts, tables, and visual elements

### Data Documentation Package

#### Source Bibliography

**Required Elements**:

- **Primary Sources**: Regulatory filings, government data, company reports
- **Secondary Sources**: Financial news, research reports, industry publications
- **Data Providers**: Bloomberg, Reuters, exchange data, academic sources
- **Access Timestamps**: Exact date and time of data collection

**Format Standards**:

- Standardized citation format enabling easy verification
- Hyperlinks to sources where available and appropriate
- Quality assessment for each source (primary/secondary, bias factors)
- Currency notation for time-sensitive data points

#### Fact vs. Assumption Inventory

**Fact Documentation**:

- **Market Data**: Prices, volumes, yields with exact timestamps
- **Financial Data**: Earnings, balance sheet items, cash flows
- **Economic Data**: GDP, inflation, employment with source attribution
- **Policy Data**: Regulatory announcements, central bank communications

**Assumption Documentation**:

- **Growth Projections**: Basis for assumptions and confidence levels
- **Scenario Probabilities**: Rationale for probability assignments
- **Competitive Assessments**: Qualitative judgments and supporting logic
- **Risk Evaluations**: Subjective risk assessments and reasoning

**Quality Standards**:

- Clear categorization prevents confusion between facts and judgments
- Source attribution enables independent verification of facts
- Assumption rationale supports analytical transparency
- Confidence levels communicate uncertainty appropriately

#### Research Methodology Documentation

**Process Documentation**:

- **Tool Selection**: Rationale for research tool deployment
- **Search Strategies**: Keywords, databases, search parameters used
- **Validation Protocols**: Cross-verification methods and criteria
- **Quality Controls**: Review processes and validation checks applied

**Calculation Documentation**:

- **Formula Specifications**: Detailed calculation methodologies
- **Data Transformations**: Any adjustments or normalizations applied
- **Peer Comparison Methods**: Standardization and comparison protocols
- **Risk Metric Calculations**: VaR, correlation, and other risk measures

**Limitation Acknowledgment**:

- **Data Limitations**: Missing data, estimation requirements, uncertainty factors
- **Methodological Constraints**: Analytical limitations and potential bias sources
- **Time Constraints**: Impact of research timeline on analysis depth
- **Access Limitations**: Information not available or accessible

### Implementation-Ready Deliverables

#### Research Action Items

**Immediate Actions** (Next 1-7 days):

- High-priority data updates or verification needs
- Critical follow-up research or clarification requirements
- Urgent risk factors requiring immediate attention
- Time-sensitive opportunities or threat assessments

**Near-term Actions** (Next 1-4 weeks):

- Additional research to fill identified knowledge gaps
- Stakeholder consultations or expert interviews
- Model updates or analytical refinements
- Strategy development based on research findings

**Ongoing Monitoring** (Continuous):

- Key metrics and indicators requiring regular updates
- Market conditions and environmental factors to track
- Company-specific developments and announcements
- Industry trends and competitive developments

#### Research Update Schedule

**Daily Monitoring**:

- Market prices and volatility indicators
- Breaking news and policy announcements
- Earnings announcements and company developments
- Economic data releases and central bank communications

**Weekly Reviews**:

- Portfolio holdings and allocation drift
- Market environment and sentiment changes
- Industry developments and competitive actions
- Research assumption validation and updates

**Monthly Deep Reviews**:

- Comprehensive research refresh and validation
- Peer comparison updates and ranking changes
- Risk assessment updates and scenario refinements
- Strategic implication analysis and recommendation updates

**Quality Standards**:

- Implementation guidance is specific and actionable
- Monitoring schedules are realistic and sustainable
- Update protocols maintain research currency and relevance
- Communication standards ensure stakeholder awareness

<!-- END: output_specifications -->

<!-- CHANGED: Added comprehensive research workflow structure | Date: 2025-09-17 | Author: AOJDevStudio -->
<!-- INTEGRATION: exa-mcp | Required: true -->
<!-- INTEGRATION: web-search-tool | Required: true -->
<!-- INTEGRATION: sequential-thinking-mcp | Required: true -->
<!-- VALIDATION: multi-source-cross-verification | Status: implemented -->

<!-- PERFORMANCE: research_efficiency | Target: 30-45 minutes standard analysis -->
<!-- METRICS: source_quality | Standard: minimum 2 independent sources -->
<!-- METRICS: fact_validation | Standard: 100% critical facts cross-verified -->

<!-- REQUIRES: exa-mcp >= 1.0.0 -->
<!-- REQUIRES: web-search-tool >= 1.0.0 -->
<!-- REQUIRES: sequential-thinking-mcp >= 1.0.0 -->

<!-- DOCS: Finance Guru Knowledge Base: .guru-core/data/guru-kb.md -->
<!-- DOCS: Analytical Framework: .guru-core/data/analytical-framework.md -->
<!-- EXAMPLES: Research task examples in .guru-core/tasks/ -->

---

_This research workflow is designed to integrate seamlessly with the Finance Guru analytical framework, providing systematic research protocols that support high-quality financial analysis and investment decision-making._
