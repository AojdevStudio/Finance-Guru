# Maturity Levels

Repositories progress through five levels. Each level represents a qualitative shift in what autonomous agents can accomplish.

## Level Progression Rules

1. **80% Threshold**: To unlock a level, pass ≥80% of criteria at that level
2. **Cumulative**: Must also pass all previous levels at 80%+
3. **Binary Criteria**: Each criterion is pass/fail (no partial credit)
4. **Skipped Criteria**: Not applicable criteria are excluded from the calculation

---

## Level 1: Initial

**Status**: Basic version control  
**Agent Capability**: Manual assistance only

### Requirements
The bare minimum for any collaborative development.

| Criterion | Pillar |
|-----------|--------|
| `formatter` | Style & Validation |
| `lint_config` | Style & Validation |
| `type_check` | Style & Validation |
| `build_cmd_doc` | Build System |
| `deps_pinned` | Build System |
| `vcs_cli_tools` | Build System |
| `unit_tests_exist` | Testing |
| `unit_tests_runnable` | Testing |
| `readme` | Documentation |
| `gitignore_comprehensive` | Security |

### What Agents Can Do
- Read and understand code
- Make simple edits with manual verification
- Cannot reliably validate their own changes

### What's Missing
Without L1, agents operate blind—no way to verify builds, run tests, or ensure code quality.

---

## Level 2: Managed

**Status**: Basic CI/CD and testing  
**Agent Capability**: Simple, well-defined tasks

### Requirements
Foundational automation and documentation.

| Criterion | Pillar |
|-----------|--------|
| `strict_typing` | Style & Validation |
| `pre_commit_hooks` | Style & Validation |
| `naming_consistency` | Style & Validation |
| `large_file_detection` | Style & Validation |
| `fast_ci_feedback` | Build System |
| `single_command_setup` | Build System |
| `release_automation` | Build System |
| `deployment_frequency` | Build System |
| `test_naming_conventions` | Testing |
| `test_isolation` | Testing |
| `agents_md` | Documentation |
| `documentation_freshness` | Documentation |
| `env_template` | Dev Environment |
| `structured_logging` | Observability |
| `code_quality_metrics` | Observability |
| `secrets_management` | Security |
| `codeowners` | Security |
| `branch_protection` | Security |
| `issue_templates` | Task Discovery |
| `issue_labeling_system` | Task Discovery |
| `pr_templates` | Task Discovery |

### What Agents Can Do
- Fix simple, well-scoped bugs
- Make straightforward changes with fast feedback
- Run tests and verify basic correctness

### What's Missing
Without L2, feedback loops are too slow. Agents wait minutes for CI instead of seconds for local checks.

---

## Level 3: Standardized

**Status**: Production-ready for agents  
**Agent Capability**: Routine maintenance

### Requirements
Clear processes defined and enforced. This is the target for most teams.

| Criterion | Pillar |
|-----------|--------|
| `code_modularization` | Style & Validation |
| `cyclomatic_complexity` | Style & Validation |
| `dead_code_detection` | Style & Validation |
| `duplicate_code_detection` | Style & Validation |
| `release_notes_automation` | Build System |
| `agentic_development` | Build System |
| `automated_pr_review` | Build System |
| `feature_flag_infrastructure` | Build System |
| `integration_tests_exist` | Testing |
| `test_coverage_thresholds` | Testing |
| `api_schema_docs` | Documentation |
| `automated_doc_generation` | Documentation |
| `service_flow_documented` | Documentation |
| `skills` | Documentation |
| `devcontainer` | Dev Environment |
| `devcontainer_runnable` | Dev Environment |
| `database_schema` | Dev Environment |
| `local_services_setup` | Dev Environment |
| `error_tracking_contextualized` | Observability |
| `distributed_tracing` | Observability |
| `metrics_collection` | Observability |
| `health_checks` | Observability |
| `dependency_update_automation` | Security |
| `log_scrubbing` | Security |
| `pii_handling` | Security |
| `backlog_health` | Task Discovery |

### What Agents Can Do
- Bug fixes and routine maintenance
- Test additions and documentation updates
- Dependency upgrades with confidence
- Feature work with clear specifications

### Example Repositories at L3
- FastAPI
- GitHub CLI
- pytest

---

## Level 4: Measured

**Status**: Comprehensive automation  
**Agent Capability**: Complex features

### Requirements
Advanced tooling and metrics for optimization.

| Criterion | Pillar |
|-----------|--------|
| `tech_debt_tracking` | Style & Validation |
| `n_plus_one_detection` | Style & Validation |
| `build_performance_tracking` | Build System |
| `unused_dependencies_detection` | Build System |
| `dead_feature_flag_detection` | Build System |
| `monorepo_tooling` | Build System |
| `version_drift_detection` | Build System |
| `flaky_test_detection` | Testing |
| `test_performance_tracking` | Testing |
| `agents_md_validation` | Documentation |
| `profiling_instrumentation` | Observability |
| `alerting_configured` | Observability |
| `deployment_observability` | Observability |
| `runbooks_documented` | Observability |
| `automated_security_review` | Security |
| `secret_scanning` | Security |

### What Agents Can Do
- Complex multi-file refactors
- Performance optimization with data
- Architecture improvements
- Security hardening

### Example Repositories at L4
- CockroachDB
- Temporal

---

## Level 5: Optimized

**Status**: Full autonomous capability  
**Agent Capability**: End-to-end development

### Requirements
Comprehensive observability, security, and automation.

| Criterion | Pillar |
|-----------|--------|
| `progressive_rollout` | Build System |
| `rollback_automation` | Build System |
| `circuit_breakers` | Observability |
| `dast_scanning` | Security |
| `privacy_compliance` | Security |
| `error_to_insight_pipeline` | Task Discovery |
| `product_analytics_instrumentation` | Task Discovery |

### What Agents Can Do
- Full feature development with minimal oversight
- Incident response and remediation
- Autonomous triage and prioritization
- Continuous improvement of the codebase itself

### What L5 Looks Like
Very few repositories achieve L5. It requires mature DevOps, comprehensive observability, and sophisticated automation.

---

## Calculating Scores

### Repository Score
```
Pass Rate = (Passed Criteria) / (Total Applicable Criteria) × 100%
```

### Level Determination
```
For each level L (1 to 5):
  If (pass rate at L ≥ 80%) AND (all lower levels ≥ 80%):
    Repository is at level L
```

### Organization Score
```
Org Level = floor(average of all repository levels)
Key Metric = % of active repos at L3+
```

---

## Priority Order for Improvement

1. **Fix L1 failures first**: These block basic operation
2. **Then L2**: Enable fast feedback loops
3. **Aim for L3**: Production-ready target
4. **L4+ is optimization**: Nice to have, not essential

### Quick Wins by Level

**L1 → L2**:
- Add pre-commit hooks
- Document setup commands
- Add AGENTS.md

**L2 → L3**:
- Add integration tests
- Set up devcontainer
- Configure automated reviews

**L3 → L4**:
- Add complexity analysis
- Set up flaky test detection
- Enable security scanning
