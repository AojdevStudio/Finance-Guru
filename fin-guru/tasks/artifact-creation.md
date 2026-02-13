# Artifact Creation Workflow

## Purpose and Scope

This workflow guides the creation of professional-grade financial artifacts that meet institutional quality standards. The workflow transforms quantitative analysis into interactive, working deliverables that clients, investment committees, and stakeholders can use for decision-making and implementation.

### Core Objectives

- **Interactive Excel Models**: Working formulas, scenario analysis, and professional visualizations
- **Executive Presentations**: PowerPoint/PDF summaries with key insights and recommendations
- **Implementation Documentation**: Sources, assumptions, and execution roadmaps
- **Monitoring Dashboards**: Risk tracking and performance measurement tools

### Quality Standards

All artifacts must meet these institutional requirements:
- No circular references (unless intentional with toggles)
- Named ranges for all key variables
- Color-coded inputs (blue), calculations (green), outputs (yellow)
- Professional formatting and alignment
- Complete documentation and validation

## Usage Scenarios

### Scenario 1: Portfolio Analysis & Strategy Development

**When to Use**: Comprehensive portfolio reviews, client presentations, investment committee reports

**Typical Deliverables**:
- Excel optimization model with scenario analysis
- PowerPoint executive summary (10-15 slides)
- Implementation roadmap with milestones
- Risk monitoring dashboard

**Timeline**: 2-4 hours for complete package

### Scenario 2: Security-Specific Analysis

**When to Use**: Individual stock/ETF analysis, dividend strategy modeling, margin analysis

**Typical Deliverables**:
- Focused Excel model with sensitivity analysis
- PDF summary report (3-5 pages)
- Risk assessment with stress testing
- Buy/hold/sell recommendation with rationale

**Timeline**: 1-2 hours for complete analysis

### Scenario 3: Strategy Comparison & Selection

**When to Use**: Evaluating multiple investment approaches, factor analysis, allocation decisions

**Typical Deliverables**:
- Comparative Excel model with multiple strategies
- Tornado charts for sensitivity analysis
- Monte Carlo simulation results
- Strategy selection matrix with scoring

**Timeline**: 2-3 hours for comprehensive comparison

### Scenario 4: Risk Management & Stress Testing

**When to Use**: VaR analysis, portfolio stress testing, regulatory compliance, risk committee reports

**Typical Deliverables**:
- Risk analytics Excel model
- Stress test scenario results
- VaR distribution charts and tables
- Risk monitoring dashboard with alerts

**Timeline**: 1-3 hours depending on complexity

## Step-by-Step Excel Model Creation

### Phase 1: Model Structure Setup

**Step 1: Workbook Architecture**
```
Required Tabs:
1. Inputs    - Data validation, scenario selectors, parameter controls
2. Calculations - Transparent formulas, intermediate calculations
3. Scenarios - Bull/base/bear modeling, sensitivity analysis
4. Risk      - VaR calculations, stress tests, drawdown analysis
5. Outputs   - Executive dashboard, charts, summary tables
```

**Step 2: Named Ranges Definition**
- Create descriptive named ranges for all key variables
- Use consistent naming convention (e.g., Input_RiskFreeRate, Calc_Sharpe_Ratio)
- Group related ranges logically
- Document range purposes and dependencies

**Step 3: Color Coding System**
- **Blue cells**: User inputs and parameters
- **Green cells**: Calculations and formulas
- **Yellow cells**: Key outputs and results
- **Red text**: Warnings and alerts
- **Gray cells**: Reference data (not user-modifiable)

### Phase 2: Inputs Tab Development

**Step 4: Parameter Controls**
- Risk tolerance settings (Conservative/Moderate/Aggressive dropdowns)
- Time horizon selectors (1Y/3Y/5Y/10Y+ options)
- Return expectations with validation ranges
- Cost assumptions (fees, taxes, transaction costs)
- Constraint toggles (ESG, sector limits, etc.)

**Step 5: Scenario Selectors**
- Bull/Base/Bear market dropdown
- Economic environment settings
- Interest rate scenarios
- Volatility regime selection
- Custom scenario parameters

**Step 6: Data Validation**
- Input range constraints (e.g., risk tolerance 1-10)
- Dropdown lists for categorical inputs
- Error checking formulas with alerts
- Input dependency validation

### Phase 3: Calculations Tab Development

**Step 7: Core Financial Metrics**
```excel
# Return Calculations
Expected_Return = SUMPRODUCT(Asset_Weights, Asset_Returns)
Portfolio_Volatility = SQRT(Portfolio_Variance_Formula)
Sharpe_Ratio = (Expected_Return - Risk_Free_Rate) / Portfolio_Volatility
```

**Step 8: Risk Metrics**
```excel
# VaR Calculations (Monte Carlo or Parametric)
VaR_95 = PERCENTILE(Return_Distribution, 0.05)
VaR_99 = PERCENTILE(Return_Distribution, 0.01)
Maximum_Drawdown = MAX(Running_Drawdown_Series)
```

**Step 9: Optimization Formulas**
- Mean-variance optimization constraints
- Risk budgeting allocations
- Factor exposure calculations
- Rebalancing triggers and thresholds

### Phase 4: Scenarios Tab Development

**Step 10: Market Scenario Modeling**
- Bull market assumptions (+20% equity, low volatility)
- Base case modeling (historical averages)
- Bear market stress (-30% equity, high volatility)
- Custom scenario flexibility

**Step 11: Sensitivity Analysis**
- Tornado charts showing parameter impact
- Two-way sensitivity tables
- Key variable stress testing
- Breakeven analysis

**Step 12: Monte Carlo Integration**
- Random return generation
- Portfolio outcome distributions
- Probability of achieving goals
- Confidence interval calculations

### Phase 5: Risk Tab Development

**Step 13: VaR Modeling**
- Historical simulation VaR
- Parametric VaR (normal distribution)
- Monte Carlo VaR
- Expected shortfall (CVaR) calculations

**Step 14: Stress Testing**
- Historical crisis scenarios (2008, 2020, etc.)
- Hypothetical stress scenarios
- Factor shock testing
- Correlation breakdown scenarios

**Step 15: Liquidity Analysis**
- Average daily volume analysis
- Bid-ask spread impact
- Market impact estimation
- Liquidation timeline modeling

### Phase 6: Outputs Tab Development

**Step 16: Executive Dashboard**
- Key metrics summary table
- Traffic light risk indicators
- Progress toward goals tracking
- Performance attribution summary

**Step 17: Professional Charts**
- Risk/return scatter plots
- Performance trend lines
- Distribution histograms
- Waterfall attribution charts

**Step 18: Summary Tables**
- Asset allocation current vs. target
- Risk metrics comparison
- Scenario outcome summary
- Implementation action items

## Chart and Visualization Specifications

### Required Chart Types

**Line Charts - Performance Trends**
- Purpose: Show portfolio performance over time
- Format: Clean lines, appropriate scales, clear legends
- Data: Historical performance, projections, benchmarks
- Features: Markers for key events, confidence bands

**Bar Charts - Comparative Analysis**
- Purpose: Compare strategies, assets, or time periods
- Format: Consistent colors, clear labels, appropriate grouping
- Data: Returns, risk metrics, allocation weights
- Features: Data labels, reference lines, ranking indicators

**Scatter Plots - Risk/Return Relationships**
- Purpose: Visualize risk-adjusted performance
- Format: Bubble size for additional dimension, clear quadrants
- Data: Risk vs. return for assets or strategies
- Features: Efficient frontier overlay, benchmark positioning

**Histograms - Distribution Analysis**
- Purpose: Show return distributions and probability
- Format: Appropriate bins, normal curve overlay
- Data: Historical returns, Monte Carlo outcomes
- Features: VaR markers, percentile indicators

**Tornado Charts - Sensitivity Analysis**
- Purpose: Identify key drivers of portfolio outcomes
- Format: Horizontal bars, ranked by impact
- Data: Parameter sensitivity ranges
- Features: Base case centerline, impact quantification

**Waterfall Charts - Performance Attribution**
- Purpose: Break down portfolio performance sources
- Format: Connected bars showing cumulative effect
- Data: Asset allocation, security selection, interaction effects
- Features: Clear contribution labels, net result emphasis

### Professional Standards

**Color Scheme Consistency**
- Primary colors: Blue (#0066CC), Green (#00AA44), Red (#CC0000)
- Secondary colors: Gray (#666666), Orange (#FF8800)
- Background: White with light gray gridlines
- Avoid: Neon colors, excessive gradients, 3D effects

**Typography and Labels**
- Title: Bold, 14pt, descriptive and specific
- Axis labels: 11pt, clear units and formatting
- Data labels: 10pt, positioned for clarity
- Legend: 10pt, positioned strategically

**Data Source Citations**
- Include source and date in footnote
- Update timestamps for real-time data
- Cite calculation methodology
- Note any data limitations or assumptions

## Quality Standards and Validation

### Formula Quality Checks

**No Circular References**
- Use Excel's circular reference detection
- Implement intentional circulars with iteration toggles only
- Document any circular dependencies clearly
- Test formula integrity across scenarios

**Named Ranges Implementation**
- All key variables must use named ranges
- Consistent naming convention throughout
- Avoid hard-coded cell references in formulas
- Group related ranges logically

**Dynamic Formula Design**
- Formulas respond to scenario changes
- Input modifications flow through calculations
- Scenario selectors control formula behavior
- Error handling for invalid inputs

### Model Validation Process

**Step 1: Input Validation**
- Test all input controls and dropdowns
- Verify data validation rules work correctly
- Check input dependency relationships
- Validate scenario selector functionality

**Step 2: Calculation Verification**
- Cross-check key calculations manually
- Verify formulas against known benchmarks
- Test edge cases and boundary conditions
- Validate mathematical relationships

**Step 3: Scenario Testing**
- Run all scenario combinations
- Verify results make economic sense
- Check for formula errors across scenarios
- Test sensitivity analysis accuracy

**Step 4: Chart Validation**
- Verify charts update with input changes
- Check data series accuracy
- Validate chart formatting consistency
- Test chart readability and clarity

### Error Prevention

**Common Issues to Avoid**
- Hard-coded outputs in formulas
- Inconsistent cell formatting
- Missing error handling
- Unclear or missing documentation
- Broken chart links
- Inconsistent naming conventions

**Quality Checklist**
- [ ] All inputs are color-coded blue
- [ ] All calculations use named ranges
- [ ] All scenarios produce reasonable results
- [ ] All charts update dynamically
- [ ] All formulas include error handling
- [ ] All assumptions are documented
- [ ] Model passes stress testing
- [ ] Professional formatting applied

## Documentation Requirements

### Model Documentation Standards

**Assumptions Documentation**
- List all key assumptions with rationale
- Include data sources and collection dates
- Document calculation methodologies
- Note model limitations and caveats

**User Instructions**
- Clear step-by-step usage guide
- Explanation of all input controls
- Interpretation guide for outputs
- Troubleshooting common issues

**Methodology Documentation**
- Mathematical formulas and derivations
- Statistical methods and assumptions
- Optimization approach and constraints
- Risk measurement techniques

### Source Attribution

**Data Sources**
- Financial data providers (Bloomberg, Yahoo, etc.)
- Economic indicators (Fed, BLS, etc.)
- Company financials (10-K, earnings reports)
- Research reports and analysis

**Calculation Sources**
- Academic literature citations
- Industry standard methodologies
- Regulatory guidance references
- Professional standard practices

**Assumption Sources**
- Historical data analysis
- Industry benchmarks
- Expert judgment rationale
- Sensitivity analysis results

## Output Specifications

### Excel Model Deliverables

**File Naming Convention**
- Format: `YYYY-MM-DD_ModelType_ClientName_Version.xlsx`
- Example: `2025-09-17_PortfolioOptimization_ClientABC_v1.0.xlsx`
- Include version control and change log

**File Organization**
- Logical tab ordering (Inputs → Calculations → Scenarios → Risk → Outputs)
- Hidden tabs for complex calculations if necessary
- Protection on formula cells with user input areas unlocked
- Print settings optimized for key output pages

**Export Formats**
- Native Excel (.xlsx) for interactive use
- PDF export of key charts and tables
- CSV exports of raw data tables
- PNG/JPG exports of individual charts

### Presentation Deliverables

**PowerPoint Structure**
1. Executive Summary (1-2 slides)
2. Key Findings (2-3 slides)
3. Methodology Overview (1-2 slides)
4. Detailed Analysis (3-5 slides)
5. Risk Assessment (2-3 slides)
6. Implementation Plan (1-2 slides)
7. Appendix (supporting data and assumptions)

**PDF Report Structure**
1. Executive Summary (1 page)
2. Investment Thesis (1-2 pages)
3. Quantitative Analysis (2-3 pages)
4. Risk Analysis (1-2 pages)
5. Implementation Guidance (1 page)
6. Appendix (supporting documentation)

### Bundle Organization

**Delivery Package Structure**
```
ClientName_Analysis_YYYY-MM-DD/
├── Excel_Models/
│   ├── Portfolio_Optimization_Model.xlsx
│   ├── Risk_Analysis_Model.xlsx
│   └── Scenario_Analysis_Model.xlsx
├── Presentations/
│   ├── Executive_Summary.pptx
│   ├── Detailed_Analysis.pdf
│   └── Implementation_Guide.pdf
├── Documentation/
│   ├── Assumptions_and_Sources.pdf
│   ├── Methodology_Documentation.pdf
│   └── User_Instructions.pdf
└── Supporting_Data/
    ├── Market_Data.csv
    ├── Historical_Performance.csv
    └── Risk_Metrics.csv
```

**Quality Assurance Checklist**
- [ ] All files follow naming conventions
- [ ] Version numbers are consistent
- [ ] All cross-references work correctly
- [ ] Professional formatting applied throughout
- [ ] Sensitive data removed or anonymized
- [ ] Compliance disclaimers included
- [ ] Contact information and dates current

## Implementation Guidelines

### Workflow Integration

**Phase 4 Integration**: This artifact creation workflow implements the fourth phase of the Finance Guru analytical framework:

1. **Research Phase** → Market intelligence and data gathering
2. **Quantitative Analysis** → Risk/return modeling and optimization
3. **Strategy Development** → Implementation planning and optimization
4. **Artifact Creation** → This workflow transforms analysis into professional deliverables

### Tool Requirements

**Required Tools**:
- Excel with solver add-in for optimization
- PowerPoint for presentations
- Python code interpreter for complex analysis
- File management system for organization

**Optional Tools**:
- Adobe Acrobat for PDF enhancement
- Tableau/Power BI for advanced visualizations
- R/Python for statistical analysis
- LaTeX for mathematical documentation

### Quality Control Process

**Before Delivery Checklist**:
1. Independent review of calculations
2. Stress testing of all scenarios
3. Validation against benchmarks
4. Professional formatting review
5. Spelling and grammar check
6. Compliance review
7. Client confidentiality verification
8. Version control documentation

### Continuous Improvement

**Feedback Integration**:
- Collect client feedback on usability
- Track model performance over time
- Update methodologies based on new research
- Refine templates based on usage patterns
- Maintain library of successful models

**Template Maintenance**:
- Regular review and updates
- Version control for templates
- Documentation of template changes
- User training on template updates
- Quality assurance for new versions

---

## Usage Notes

This workflow should be executed in **modeling mode** as defined in the Finance Guru system prompt, utilizing the code interpreter for Excel generation and the desktop commander for file operations. All artifacts should be saved to the outputs directory unless otherwise specified by the user.

The workflow emphasizes professional quality, institutional standards, and practical implementation - core principles of the Finance Guru framework.
