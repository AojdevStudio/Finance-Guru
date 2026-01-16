# Finance Guru™

> **Institutional-grade multi-agent family office system providing comprehensive financial intelligence, quantitative analysis, strategic portfolio planning, and compliance oversight.**

**Version:** 2.0.0 (BMAD v6)
**Author:** {user_name}
**Date:** 2025-10-08

---

## Overview

Finance Guru™ is a sophisticated multi-agent framework that transforms Claude into your personal family office. Built on BMAD-CORE™ v6, it provides:

- **Institutional-Grade Analysis** - Methodologies from Goldman Sachs, Renaissance Technologies, and elite family offices
- **Multi-Agent Orchestration** - 13 specialized financial agents working in concert
- **Comprehensive Workflows** - Research → Quant → Strategy → Artifacts pipeline
- **Educational Focus** - All outputs are educational-only, requiring consultation with licensed advisors

---

## Installation

```bash
# Using BMAD installer (recommended)
bmad install fin-guru

# Manual installation
1. Copy fin-guru/ to your project
2. Load any agent from fin-guru/agents/
3. Type *help to see available commands
```

---

## Components

### 🤖 Agents (13 Specialists)

#### Core Orchestration
- **Finance Orchestrator** (Cassandra Holt) - Master Portfolio Coordinator
  - Entry point for all Finance Guru engagements
  - Routes requests to appropriate specialists
  - Maintains compliance and audit trail

#### Primary Specialists
- **Market Researcher** (Dr. Aleksandr Petrov) - Intelligence Gathering
  - Market research and competitive intelligence
  - Macro regime identification
  - Catalyst discovery and validation

- **Quant Analyst** (Dr. Priya Desai) - Quantitative Modeling
  - Statistical analysis and backtesting
  - Portfolio optimization
  - Monte Carlo simulations

- **Strategy Advisor** (Elena Rodriguez-Park) - Portfolio Planning
  - Converts analysis into actionable strategies
  - Implementation roadmaps
  - Risk-adjusted optimization

- **Compliance Officer** (Marcus Allen) - Risk & Compliance
  - Educational-only positioning enforcement
  - Source citation verification
  - Risk transparency and disclosure

- **Teaching Specialist** (Maya Brooks) - Financial Education
  - ADHD-friendly micro-learning
  - Progressive profiling
  - Adaptive teaching modes

#### Domain Specialists
- **Margin Specialist** (Richard Chen) - Margin Trading Strategies
- **Dividend Specialist** (Sarah Martinez) - Income Optimization
- **Onboarding Specialist** (James Cooper) - Client Profiling

#### Support Agents
- **Builder** (Alexandra Kim) - Document & Artifact Creation
- **QA Advisor** (Dr. Jennifer Wu) - Quality Assurance
- **Specialist** - Base Template
- **Agent Template** - Template for creating new agents

### 📋 Tasks (21 Workflows)

**Research & Analysis**
- research-workflow
- quantitative-analysis
- create-deep-research-prompt
- index-docs

**Strategy & Planning**
- strategy-integration
- dividend-analysis
- risk-profile

**Compliance & Quality**
- compliance-review
- execute-checklist
- trace-requirements

**Teaching & Learning**
- teaching-workflow
- adaptive-teaching
- build-learner-profile
- assessment-orientation
- context-aware-loading

**Document Creation**
- artifact-creation
- create-doc
- facilitate-brainstorming-session
- advanced-elicitation

**Utilities**
- profile-parser
- kb-mode-interaction

### 📄 Templates (7 Documents)
- analysis-report.md
- compliance-memo.md
- excel-model-spec.md
- income-strategy-template.md
- learner-profile-template.md
- onboarding-report.md
- presentation-format.md

### ✅ Checklists (4 Frameworks)
- analyst-checklist.md
- margin-strategy.md
- cashflow-policy.md
- dividend-framework.md

---

## Quick Start

### 1. Load the Finance Orchestrator

```
Load agent: fin-guru/agents/finance-orchestrator.md
```

### 2. View Available Commands

```
*help
```

### 3. Start with Onboarding (Recommended)

```
*onboarding
```

This will build your financial profile and set up personalized strategies.

---

## Usage Examples

### Example 1: Market Research

```
*market-research
> *research "Technology sector trends for Q4 2025"
```

### Example 2: Portfolio Analysis

```
*quant
> *analyze "Calculate Sharpe ratio and risk metrics for my portfolio"
```

### Example 3: Strategic Planning

```
*strategy
> *strategize "Develop dividend income strategy with 5% target yield"
```

### Example 4: Learn About Investing

```
*teaching
> *teach "Explain dividend investing fundamentals"
> *guided  # Switch to ADHD-friendly mode
```

---

## Workflow Pipeline

Finance Guru™ uses a systematic 4-stage workflow:

```
1. RESEARCH → 2. QUANT → 3. STRATEGY → 4. ARTIFACTS
```

**Stage 1: Research (Market Researcher)**
- Gather market intelligence
- Identify catalysts and risks
- Validate data sources

**Stage 2: Quant (Quant Analyst)**
- Statistical analysis
- Risk/return modeling
- Backtesting strategies

**Stage 3: Strategy (Strategy Advisor)**
- Convert analysis to actionable plans
- Implementation roadmaps
- Monitoring frameworks

**Stage 4: Artifacts (Builder)**
- Create deliverables
- Format reports
- Generate presentations

Each stage can be invoked independently or as part of the full pipeline.

---

## Configuration

Module configuration is in `fin-guru/config.yaml`

Key settings:
```yaml
module_name: "Finance Guru™"
module_code: fin-guru
primary_agent: finance-orchestrator
default_mode: consultative
compliance_required: true
educational_only: true
```

---

## Data & Knowledge Base

Finance Guru™ includes comprehensive knowledge bases:

- **system-context.md** - Your private family office context
- **user-profile.yaml** - Your personal financial profile
- **risk-framework.md** - Risk management guidelines
- **compliance-policy.md** - Compliance and disclosure requirements
- **margin-strategy.md** - Margin trading frameworks
- **dividend-framework.md** - Income investing strategies
- **cashflow-policy.md** - Cash flow optimization

---

## External Tool Requirements

Finance Guru™ requires these MCP servers/tools:

- **exa** - Deep research and market intelligence
- **bright-data** - Web scraping and data gathering
- **sequential-thinking** - Complex multi-step workflows
- **code-interpreter** - Python execution for quant analysis
- **financial-datasets** - SEC filings and financial data
- **web-search** - Real-time market information

---

## Development Roadmap

### Phase 1: Core Foundation ✅
- [x] 13 BMAD v6 agents
- [x] 21 task workflows
- [x] 7 document templates
- [x] 4 quality checklists
- [x] Comprehensive knowledge base

### Phase 2: Enhancements (Future)
- [ ] Additional workflow automations
- [ ] Enhanced backtesting frameworks
- [ ] Tax optimization strategies
- [ ] Portfolio monitoring dashboards
- [ ] Multi-currency support

### Phase 3: Integration (Future)
- [ ] Real-time data feeds
- [ ] Brokerage API integration
- [ ] Portfolio tracking automation
- [ ] Alert systems

---

## Important Disclaimers

⚠️ **EDUCATIONAL ONLY**

Finance Guru™ provides educational content only. It is NOT:
- Investment advice
- Financial planning services
- Tax or legal counsel
- A substitute for licensed professionals

Always consult licensed financial advisors, tax professionals, and legal counsel before making investment decisions.

⚠️ **NO GUARANTEES**

Past performance does not guarantee future results. All investments carry risk, including possible loss of principal.

---

## Contributing

To extend Finance Guru™:

1. **Add New Agents** - Use `agent-template.md` as starting point
2. **Create Workflows** - Follow task workflow patterns
3. **Extend Knowledge Base** - Add to `data/` directory
4. **Submit Improvements** - Via pull request

---

## Support

- **Documentation**: This README and agent help commands
- **Issues**: Report via GitHub or project tracker
- **Questions**: Use `*help` command within any agent

---

## License

Copyright © 2025 {user_name}
Finance Guru™ is a trademark.
Built on BMAD-CORE™ v6.

---

## Version History

**v2.0.0** (2025-10-08) - BMAD v6 Rebuild
- Complete rebuild using BMAD-CORE™ v6 architecture
- XML-based agent configurations
- Enhanced activation sequences
- Module installer infrastructure
- Comprehensive documentation

**v1.0.0** (2025-09-25) - Initial Release
- Original Finance Guru™ system
- YAML-based agent configurations
- Core workflow pipeline

---

**Built with ❤️ using BMAD-CORE™ v6**
