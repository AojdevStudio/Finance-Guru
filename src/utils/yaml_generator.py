"""YAML Generator Calculator for Finance Guru™.

This module generates configuration files from templates and validated user data.
Uses validated Pydantic models from yaml_generation_inputs.py to ensure type safety.

ARCHITECTURE NOTE:
This is Layer 2 of our 3-layer architecture:
    Layer 1: Pydantic Models - Data validation (yaml_generation_inputs.py)
    Layer 2: Calculator Classes (THIS FILE) - Business logic
    Layer 3: CLI Interface - Agent integration (yaml_generator_cli.py)

GENERATION PROCESS:
1. Load template files
2. Prepare user data with computed fields
3. Substitute template variables
4. Generate all configuration files

Author: Finance Guru™ Development Team
Created: 2026-01-16
"""

from datetime import date
from pathlib import Path
from typing import Any

from src.models.yaml_generation_inputs import (
    UserDataInput,
    YAMLGenerationOutput,
)


class YAMLGenerator:
    """Configuration file generator from templates.

    WHAT: Generates Finance Guru config files from user onboarding data
    WHY: Enables user-agnostic distribution by templating personal data
    HOW: Template variable substitution with validation

    USAGE EXAMPLE:
        # Create generator with template directory
        generator = YAMLGenerator(template_dir="scripts/onboarding/modules/templates")

        # Generate all configs
        output = generator.generate_all_configs(user_data)

        # Access generated content
        print(output.user_profile_yaml)
        print(output.config_yaml)
    """

    def __init__(self, template_dir: str):
        """Initialize YAML generator with template directory.

        Args:
            template_dir: Path to directory containing template files
        """
        self.template_dir = Path(template_dir)
        if not self.template_dir.exists():
            raise FileNotFoundError(f"Template directory not found: {template_dir}")

    def _load_template(self, template_name: str, extension: str = "yaml") -> str:
        """Load a template file.

        Args:
            template_name: Name of template (without .template extension)
            extension: File extension (yaml or md), empty string for no extension

        Returns:
            Template content as string

        Raises:
            FileNotFoundError: If template file doesn't exist
        """
        if extension:
            template_path = self.template_dir / f"{template_name}.template.{extension}"
        else:
            template_path = self.template_dir / f"{template_name}.template"

        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        return template_path.read_text(encoding="utf-8")

    def _prepare_user_data(self, data: UserDataInput) -> dict[str, Any]:
        """Prepare user data with computed fields for template substitution.

        Args:
            data: Validated user data input

        Returns:
            Dictionary with all template variables
        """
        now = date.today()
        user_name = data.identity.user_name

        # Compute possessive form (simple, just add 's)
        possessive_name = (
            f"{user_name}'" if user_name.endswith("s") else f"{user_name}'s"
        )

        # Format currency values
        def format_currency(value: float) -> str:
            """Format currency as $X,XXX.XX."""
            return f"${value:,.2f}"

        # Build template data dictionary
        template_data = {
            # Identity
            "user_name": user_name,
            "possessive_name": possessive_name,
            "language": data.identity.language,
            # Liquid assets
            "liquid_assets_total": data.liquid_assets.total,
            "liquid_assets_count": data.liquid_assets.accounts_count,
            "liquid_assets_yield": data.liquid_assets.average_yield,
            "liquid_assets_structure": data.liquid_assets.structure or "",
            # Portfolio
            "portfolio_value": data.portfolio.total_value,
            "portfolio_value_formatted": format_currency(data.portfolio.total_value),
            "brokerage": data.portfolio.brokerage or "Not specified",
            "has_retirement": "true" if data.portfolio.has_retirement else "false",
            "retirement_value": data.portfolio.retirement_value or 0,
            "allocation_strategy": data.portfolio.allocation_strategy.value,
            "risk_tolerance": data.portfolio.risk_tolerance.value,
            "google_sheets_id": data.portfolio.google_sheets_id or "",
            "account_number": data.portfolio.account_number or "",
            # Cash flow
            "monthly_income": data.cash_flow.monthly_income,
            "monthly_income_formatted": format_currency(data.cash_flow.monthly_income),
            "fixed_expenses": data.cash_flow.fixed_expenses,
            "variable_expenses": data.cash_flow.variable_expenses,
            "current_savings": data.cash_flow.current_savings,
            "investment_capacity": data.cash_flow.investment_capacity,
            "investment_capacity_formatted": format_currency(
                data.cash_flow.investment_capacity
            ),
            # Debt
            "has_mortgage": data.debt.has_mortgage,
            "mortgage_balance": data.debt.mortgage_balance or 0,
            "mortgage_payment": data.debt.mortgage_payment or 0,
            "has_student_loans": data.debt.has_student_loans,
            "student_loan_balance": data.debt.student_loan_balance or 0,
            "student_loan_rate": data.debt.student_loan_rate or 0,
            "has_auto_loans": data.debt.has_auto_loans,
            "auto_loan_balance": data.debt.auto_loan_balance or 0,
            "auto_loan_rate": data.debt.auto_loan_rate or 0,
            "has_credit_cards": data.debt.has_credit_cards,
            "credit_card_balance": data.debt.credit_card_balance or 0,
            "weighted_rate": data.debt.weighted_rate or 0,
            "other_debt": data.debt.other_debt or "",
            # Preferences
            "investment_philosophy": data.preferences.investment_philosophy.value,
            "focus_areas": data.preferences.focus_areas,
            "focus_areas_list": ", ".join(data.preferences.focus_areas),
            "emergency_fund_months": data.preferences.emergency_fund_months,
            # MCP
            "has_alphavantage": data.mcp.has_alphavantage,
            "alphavantage_key": data.mcp.alphavantage_key or "",
            "has_brightdata": data.mcp.has_brightdata,
            "brightdata_key": data.mcp.brightdata_key or "",
            # Environment
            "project_root": data.project_root or ".",
            "google_sheets_credentials": data.google_sheets_credentials or "",
            "repository_name": "family-office",
            # Timestamps
            "timestamp": now.isoformat(),
            "date": now.strftime("%Y-%m-%d"),
        }

        return template_data

    def _process_template(self, template: str, data: dict[str, Any]) -> str:
        """Process template with variable substitution.

        Supports:
        - Simple variables: {{variable}}
        - Conditional blocks: {{#if condition}}...{{/if}}

        Args:
            template: Template string
            data: Dictionary of template variables

        Returns:
            Processed template with substitutions
        """
        import re

        result = template

        # Handle conditional blocks {{#if variable}}...{{/if}}
        # Matches {{#if var}}content{{/if}} with optional whitespace
        if_pattern = re.compile(r"\{\{#if\s+(\w+)\}\}(.*?)\{\{/if\}\}", re.DOTALL)

        def replace_conditional(match: re.Match) -> str:
            """Replace conditional block based on truthiness."""
            condition = match.group(1)
            content = match.group(2)
            value = data.get(condition)
            # Include block if value is truthy (not None, False, 0, or empty string)
            return content if value else ""

        result = if_pattern.sub(replace_conditional, result)

        # Replace simple variables {{variable}}
        var_pattern = re.compile(r"\{\{(\w+)\}\}")

        def replace_variable(match: re.Match) -> str:
            """Replace variable with its value."""
            key = match.group(1)
            value = data.get(key)
            return str(value) if value is not None else ""

        result = var_pattern.sub(replace_variable, result)

        return result

    def generate_user_profile(self, data: UserDataInput) -> str:
        """Generate user-profile.yaml from template.

        Args:
            data: Validated user data

        Returns:
            Generated YAML content
        """
        template = self._load_template("user-profile", "yaml")
        prepared_data = self._prepare_user_data(data)
        return self._process_template(template, prepared_data)

    def generate_config(self, data: UserDataInput) -> str:
        """Generate config.yaml from template.

        Args:
            data: Validated user data

        Returns:
            Generated YAML content
        """
        template = self._load_template("config", "yaml")
        prepared_data = self._prepare_user_data(data)
        return self._process_template(template, prepared_data)

    def generate_system_context(self, data: UserDataInput) -> str:
        """Generate system-context.md from template.

        Args:
            data: Validated user data

        Returns:
            Generated markdown content
        """
        template = self._load_template("system-context", "md")
        prepared_data = self._prepare_user_data(data)
        return self._process_template(template, prepared_data)

    def generate_claude_md(self, data: UserDataInput) -> str:
        """Generate CLAUDE.md from template.

        Args:
            data: Validated user data

        Returns:
            Generated markdown content
        """
        template = self._load_template("CLAUDE", "md")
        prepared_data = self._prepare_user_data(data)
        return self._process_template(template, prepared_data)

    def generate_env(self, data: UserDataInput) -> str:
        """Generate .env file from template.

        Args:
            data: Validated user data

        Returns:
            Generated .env content
        """
        template = self._load_template("env", "")  # env.template (no extension)
        prepared_data = self._prepare_user_data(data)
        return self._process_template(template, prepared_data)

    def generate_mcp_json(self, data: UserDataInput) -> str:
        """Generate MCP server configuration JSON from template.

        Args:
            data: Validated user data

        Returns:
            Generated MCP JSON content
        """
        template = self._load_template("mcp", "json")
        prepared_data = self._prepare_user_data(data)
        return self._process_template(template, prepared_data)

    def generate_all_configs(self, data: UserDataInput) -> YAMLGenerationOutput:
        """Generate all configuration files.

        Args:
            data: Complete validated user data

        Returns:
            YAMLGenerationOutput with all generated content
        """
        return YAMLGenerationOutput(
            user_profile_yaml=self.generate_user_profile(data),
            config_yaml=self.generate_config(data),
            system_context_md=self.generate_system_context(data),
            claude_md=self.generate_claude_md(data),
            env_file=self.generate_env(data),
            mcp_json=self.generate_mcp_json(data),
            generation_date=date.today(),
            user_name=data.identity.user_name,
        )


def write_config_files(output: YAMLGenerationOutput, base_dir: str = ".") -> None:
    """Write generated configuration files to disk.

    Args:
        output: YAMLGenerationOutput with generated content
        base_dir: Base directory for output files (default: current directory)
    """
    base_path = Path(base_dir)

    # Define output paths
    files = {
        base_path / "fin-guru" / "data" / "user-profile.yaml": output.user_profile_yaml,
        base_path / "fin-guru" / "config.yaml": output.config_yaml,
        base_path / "fin-guru" / "data" / "system-context.md": output.system_context_md,
        base_path / "CLAUDE.md": output.claude_md,
        base_path / ".env": output.env_file,
        base_path / ".claude" / "mcp.json": output.mcp_json,
    }

    # Write files
    for file_path, content in files.items():
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
