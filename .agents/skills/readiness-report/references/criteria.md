# Agent Readiness Criteria

Complete reference of all 81 criteria evaluated across nine technical pillars.

## Criteria Format

Each criterion is binary (pass/fail) and includes:
- **ID**: Unique identifier (snake_case)
- **Level**: Maturity level (1-5) where criterion is evaluated
- **Detection**: How to check if the criterion is met
- **Impact**: What happens when this criterion fails

---

## 1. Style & Validation

Automated tools that catch bugs instantly. Without them, agents waste cycles on syntax errors and style drift.

| Criterion | Level | Detection | Impact |
|-----------|-------|-----------|--------|
| `formatter` | 1 | Prettier, Black, Ruff format, gofmt config exists | Agent submits code with formatting issues, waits for CI, fixes blindly |
| `lint_config` | 1 | ESLint, Ruff, golangci-lint, or language-specific linter configured | Style inconsistencies accumulate, harder to review |
| `type_check` | 1 | TypeScript strict, mypy, Go (static by default) | Type errors caught late in CI instead of immediately |
| `strict_typing` | 2 | TypeScript strict:true, mypy strict=true | Partial typing allows bugs to slip through |
| `pre_commit_hooks` | 2 | .pre-commit-config.yaml or Husky config | Checks run in CI instead of locally, slower feedback |
| `naming_consistency` | 2 | Linter rules or documented conventions | Inconsistent names make codebase harder to navigate |
| `large_file_detection` | 2 | Git LFS, pre-commit check-added-large-files | Large files bloat repository, slow clones |
| `code_modularization` | 3 | import-linter, Nx boundaries, Bazel modules | Architecture degrades over time |
| `cyclomatic_complexity` | 3 | gocyclo, lizard, radon, SonarQube | Complex functions harder to understand and modify |
| `dead_code_detection` | 3 | vulture, knip, deadcode in CI | Unused code clutters codebase |
| `duplicate_code_detection` | 3 | jscpd, PMD CPD, SonarQube | Duplicated code increases maintenance burden |
| `tech_debt_tracking` | 4 | TODO scanner, SonarQube, linter TODO rules | Tech debt accumulates without visibility |
| `n_plus_one_detection` | 4 | nplusone, bullet gem, query analyzer | Performance issues in database queries |

---

## 2. Build System

Fast, reliable builds enable rapid iteration. Slow CI kills agent productivity.

| Criterion | Level | Detection | Impact |
|-----------|-------|-----------|--------|
| `build_cmd_doc` | 1 | Build commands documented in README/AGENTS.md | Agent doesn't know how to build |
| `deps_pinned` | 1 | Lockfile exists (package-lock.json, uv.lock, go.sum) | Non-reproducible builds |
| `vcs_cli_tools` | 1 | gh/glab CLI authenticated | Can't interact with PRs/issues |
| `fast_ci_feedback` | 2 | CI completes in <10 minutes | Agent waits too long for feedback |
| `single_command_setup` | 2 | One command to set up dev environment | Agent can't bootstrap quickly |
| `release_automation` | 2 | Automated release workflow exists | Manual releases slow deployment |
| `deployment_frequency` | 2 | Regular releases (weekly+) | Infrequent deploys signal process issues |
| `release_notes_automation` | 3 | Auto-generated changelogs/release notes | Manual release notes are error-prone |
| `agentic_development` | 3 | AI agent commits visible in history | No prior agent integration |
| `automated_pr_review` | 3 | Danger.js, automated review bots | Reviews require human intervention |
| `feature_flag_infrastructure` | 3 | LaunchDarkly, Statsig, Unleash, custom system | Hard to ship incrementally |
| `build_performance_tracking` | 4 | Build caching, timing metrics | Build times creep up unnoticed |
| `heavy_dependency_detection` | 4 | Bundle size analysis (webpack-bundle-analyzer) | Bundle bloat goes unnoticed |
| `unused_dependencies_detection` | 4 | depcheck, deptry in CI | Bloated dependency tree |
| `dead_feature_flag_detection` | 4 | Stale flag detection tooling | Abandoned flags clutter code |
| `monorepo_tooling` | 4 | Nx, Turborepo, Bazel for monorepos | Cross-package changes are error-prone |
| `version_drift_detection` | 4 | Version consistency checks | Packages diverge silently |
| `progressive_rollout` | 5 | Canary deploys, gradual rollouts | All-or-nothing deployments are risky |
| `rollback_automation` | 5 | One-click rollback capability | Slow recovery from bad deploys |

---

## 3. Testing

Tests verify that changes work. Without them, agents can't validate their own work.

| Criterion | Level | Detection | Impact |
|-----------|-------|-----------|--------|
| `unit_tests_exist` | 1 | Test files present (*_test.*, *.spec.*) | No way to verify basic correctness |
| `unit_tests_runnable` | 1 | Test command documented and works | Agent can't run tests |
| `test_naming_conventions` | 2 | Consistent test file naming | Tests hard to find |
| `test_isolation` | 2 | Tests can run in parallel | Slow test runs |
| `integration_tests_exist` | 3 | E2E/integration test directory | Only unit-level coverage |
| `test_coverage_thresholds` | 3 | Coverage enforcement in CI | Coverage drifts down |
| `flaky_test_detection` | 4 | Test retry, quarantine, or tracking | Flaky tests erode trust |
| `test_performance_tracking` | 4 | Test timing metrics | Slow tests accumulate |

---

## 4. Documentation

Documentation tells the agent what it needs to know. Missing docs mean wasted exploration.

| Criterion | Level | Detection | Impact |
|-----------|-------|-----------|--------|
| `readme` | 1 | README.md exists with setup instructions | Agent doesn't know project basics |
| `agents_md` | 2 | AGENTS.md or CLAUDE.md exists | Agent lacks operational guidance |
| `documentation_freshness` | 2 | Key docs updated in last 180 days | Stale docs mislead agent |
| `api_schema_docs` | 3 | OpenAPI spec, GraphQL schema, or API docs | Agent must reverse-engineer APIs |
| `automated_doc_generation` | 3 | Doc generation in CI | Docs drift from code |
| `service_flow_documented` | 3 | Architecture diagrams (mermaid, PlantUML) | Agent lacks system context |
| `skills` | 3 | Skills directory (.claude/skills/, .factory/skills/) | No specialized agent instructions |
| `agents_md_validation` | 4 | CI validates AGENTS.md commands work | AGENTS.md becomes stale |

---

## 5. Dev Environment

Reproducible environments prevent "works on my machine" issues.

| Criterion | Level | Detection | Impact |
|-----------|-------|-----------|--------|
| `env_template` | 2 | .env.example or documented env vars | Agent guesses at configuration |
| `devcontainer` | 3 | .devcontainer/devcontainer.json exists | Environment setup is manual |
| `devcontainer_runnable` | 3 | Devcontainer builds and works | Devcontainer is broken |
| `database_schema` | 3 | Schema files or migration directory | Database structure undocumented |
| `local_services_setup` | 3 | docker-compose.yml for dependencies | External services need manual setup |

---

## 6. Debugging & Observability

When things go wrong, observability helps diagnose issues quickly.

| Criterion | Level | Detection | Impact |
|-----------|-------|-----------|--------|
| `structured_logging` | 2 | Logging library with structured output | Logs hard to parse |
| `code_quality_metrics` | 2 | Coverage reporting in CI | No visibility into code quality |
| `error_tracking_contextualized` | 3 | Sentry, Bugsnag with context | Errors lack context for debugging |
| `distributed_tracing` | 3 | OpenTelemetry, trace IDs | Can't trace requests across services |
| `metrics_collection` | 3 | Prometheus, Datadog, or custom metrics | No runtime visibility |
| `health_checks` | 3 | Health/readiness endpoints | Can't verify service status |
| `profiling_instrumentation` | 4 | CPU/memory profiling tools | Performance issues hard to diagnose |
| `alerting_configured` | 4 | PagerDuty, OpsGenie, alert rules | Issues discovered late |
| `deployment_observability` | 4 | Deploy tracking, dashboards | Can't correlate issues to deploys |
| `runbooks_documented` | 4 | Runbooks directory or linked docs | No guidance for incident response |
| `circuit_breakers` | 5 | Resilience patterns implemented | Cascading failures |

---

## 7. Security

Security criteria protect the codebase and data.

| Criterion | Level | Detection | Impact |
|-----------|-------|-----------|--------|
| `gitignore_comprehensive` | 1 | .gitignore excludes secrets, build artifacts | Sensitive files committed |
| `secrets_management` | 2 | GitHub secrets, vault, cloud secrets | Hardcoded secrets |
| `codeowners` | 2 | CODEOWNERS file exists | No clear ownership |
| `branch_protection` | 2 | Protected main branch | Unreviewed changes to main |
| `dependency_update_automation` | 3 | Dependabot, Renovate configured | Dependencies go stale |
| `log_scrubbing` | 3 | Log sanitization for PII | Sensitive data in logs |
| `pii_handling` | 3 | PII redaction mechanisms | PII exposure risk |
| `automated_security_review` | 4 | CodeQL, Snyk, SonarQube in CI | Security issues caught late |
| `secret_scanning` | 4 | GitHub secret scanning enabled | Leaked credentials |
| `dast_scanning` | 5 | Dynamic security testing | Runtime vulnerabilities missed |
| `privacy_compliance` | 5 | GDPR/privacy tooling | Compliance gaps |

---

## 8. Task Discovery

Structured task management helps agents find and understand work.

| Criterion | Level | Detection | Impact |
|-----------|-------|-----------|--------|
| `issue_templates` | 2 | .github/ISSUE_TEMPLATE/ exists | Inconsistent issue quality |
| `issue_labeling_system` | 2 | Consistent labels on issues | Issues hard to categorize |
| `pr_templates` | 2 | pull_request_template.md exists | PRs lack context |
| `backlog_health` | 3 | Issues have descriptive titles, labels | Unclear what to work on |

---

## 9. Product & Analytics

Connect errors to insights and understand user behavior.

| Criterion | Level | Detection | Impact |
|-----------|-------|-----------|--------|
| `error_to_insight_pipeline` | 5 | Sentry-GitHub issue creation automation | Errors don't become actionable issues |
| `product_analytics_instrumentation` | 5 | Mixpanel, Amplitude, PostHog, Heap | No user behavior data to inform decisions |

---

## Skipped Criteria

Some criteria are skipped based on repository type:
- **Libraries**: Skip deployment-related criteria (progressive_rollout, health_checks)
- **CLI tools**: Skip web-specific criteria (dast_scanning)
- **Database projects**: Skip N+1 detection (they ARE the database)
- **Single apps**: Skip monorepo tooling criteria

The analysis script automatically determines which criteria to skip based on detected repository characteristics.
