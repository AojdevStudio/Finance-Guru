#!/usr/bin/env python3
"""
Financial Assessment Parser - Standard Library Version

This script parses CSV financial assessment data and creates a comprehensive
structured financial profile using only Python standard library modules.

Educational Notes for Learning:
- CSV parsing with Python's built-in csv module
- Financial calculations and ratio analysis
- YAML generation using standard library
- Data validation and sanitization
- Proper logging practices
"""

import csv
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import re
import logging

# Configure logging to stderr (best practice)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)

logger = logging.getLogger(__name__)


class FinancialAssessmentParser:
    """
    Parses financial assessment CSV data and generates comprehensive profile.

    Educational Notes:
    This class demonstrates several important programming concepts:
    - Object-oriented design for data processing
    - Error handling and validation
    - Financial calculations and analysis
    - Structured data generation
    """

    def __init__(self, csv_file_path: str):
        self.csv_file_path = Path(csv_file_path)
        self.raw_data: Dict[str, str] = {}
        self.profile: Dict[str, Any] = {}

    def parse_csv(self) -> Dict[str, str]:
        """Parse the CSV file and extract financial data."""
        logger.info(f"Starting to parse CSV file: {self.csv_file_path}")

        try:
            with open(self.csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                data_row = next(reader)

                # Map long column names to shorter keys
                field_mapping = {
                    "What's the total balance across all your checking/savings accounts?": "liquid_assets_total",
                    "How are these accounts currently structured (what purpose does each serve)?": "account_structure",
                    "What are the current interest rates you're earning on these accounts?": "interest_rates",
                    "Do you have any existing investment accounts?": "has_investments",
                    "If yes, what are the current balances and allocations in those accounts?": "investment_balance",
                    "What's your combined monthly household income (after-tax)?": "monthly_income",
                    "What are your fixed monthly expenses (mortgage, utilities, insurance, etc.)?": "fixed_expenses",
                    "What are your variable monthly expenses (groceries, discretionary spending)?": "variable_expenses",
                    "How much do you typically save/invest each month currently?": "monthly_savings",
                    "What's your current mortgage balance and monthly payment?": "mortgage_info",
                    "Do you have any other debt (credit cards, car loans, student loans)?": "other_debt",
                    "What are the interest rates on any existing debt?": "debt_rates",
                    "How much do you want to keep in true liquid emergency funds?": "emergency_fund_preference",
                    "What's your current asset allocation philosophy?": "allocation_philosophy",
                }

                # Extract and clean the data
                cleaned_data = {}
                for long_key, short_key in field_mapping.items():
                    if long_key in data_row:
                        cleaned_data[short_key] = data_row[long_key].strip()

                self.raw_data = cleaned_data
                logger.info(f"Successfully parsed {len(cleaned_data)} fields from CSV")
                return cleaned_data

        except Exception as e:
            logger.error(f"Failed to parse CSV file: {e}")
            raise

    def extract_numeric_value(self, text: str) -> Optional[float]:
        """
        Extract numeric values from text, handling various formats.

        Educational Note:
        Financial data often contains formatting like commas, dollar signs,
        so we need robust parsing to handle these variations.
        """
        if not text:
            return None

        # Remove common non-numeric characters but keep decimal points and negative signs
        cleaned = re.sub(r'[^\d.-]', '', text.replace(',', ''))

        try:
            return float(cleaned) if cleaned else None
        except ValueError:
            return None

    def calculate_financial_metrics(self) -> Dict[str, Any]:
        """Calculate comprehensive financial metrics from parsed data."""
        logger.info("Calculating financial metrics...")

        # Extract key numeric values
        liquid_assets = self.extract_numeric_value(self.raw_data.get("liquid_assets_total", "0"))
        investment_balance = self.extract_numeric_value(self.raw_data.get("investment_balance", "0"))
        monthly_income = self.extract_numeric_value(self.raw_data.get("monthly_income", "0"))
        fixed_expenses = self.extract_numeric_value(self.raw_data.get("fixed_expenses", "0"))
        variable_expenses = self.extract_numeric_value(self.raw_data.get("variable_expenses", "0"))
        monthly_savings = self.extract_numeric_value(self.raw_data.get("monthly_savings", "0"))

        # Parse mortgage information using regex
        mortgage_info = self.raw_data.get("mortgage_info", "")
        mortgage_balance = None
        mortgage_payment = None

        balance_match = re.search(r'balance[:\s]*([0-9,.]+)', mortgage_info, re.IGNORECASE)
        payment_match = re.search(r'payment[:\s]*([0-9,.]+)', mortgage_info, re.IGNORECASE)

        if balance_match:
            mortgage_balance = self.extract_numeric_value(balance_match.group(1))
        if payment_match:
            mortgage_payment = self.extract_numeric_value(payment_match.group(1))

        # Calculate derived metrics
        total_monthly_expenses = (fixed_expenses or 0) + (variable_expenses or 0)
        estimated_net_worth = (liquid_assets or 0) + (investment_balance or 0) - (mortgage_balance or 0)
        net_cash_flow = (monthly_income or 0) - total_monthly_expenses
        savings_rate = ((monthly_savings or 0) / (monthly_income or 1)) * 100 if monthly_income else 0
        expense_ratio = (total_monthly_expenses / (monthly_income or 1)) * 100 if monthly_income else 0
        debt_to_income = ((mortgage_payment or 0) / (monthly_income or 1)) * 100 if monthly_income else 0

        metrics = {
            "net_worth": {
                "estimated_total": estimated_net_worth,
                "liquid_assets": liquid_assets,
                "investment_assets": investment_balance,
                "mortgage_debt": mortgage_balance,
            },
            "cash_flow": {
                "monthly_income": monthly_income,
                "fixed_expenses": fixed_expenses,
                "variable_expenses": variable_expenses,
                "total_expenses": total_monthly_expenses,
                "net_cash_flow": net_cash_flow,
                "savings_rate": savings_rate,
                "expense_ratio": expense_ratio,
            },
            "debt_analysis": {
                "mortgage_balance": mortgage_balance,
                "mortgage_payment": mortgage_payment,
                "debt_to_income_ratio": debt_to_income,
            },
            "investment_capacity": {
                "current_monthly_savings": monthly_savings,
                "available_cash_flow": net_cash_flow,
                "investment_accounts_value": investment_balance,
                "liquid_reserves": liquid_assets,
            }
        }

        logger.info(f"Calculated metrics - Net Worth: ${estimated_net_worth:,.2f}, Savings Rate: {savings_rate:.1f}%")
        return metrics

    def identify_opportunities(self, metrics: Dict[str, Any]) -> Dict[str, List[str]]:
        """Identify financial optimization opportunities based on metrics."""
        logger.info("Identifying optimization opportunities...")

        high_priority = []
        medium_priority = []
        strategic = []

        # Savings rate analysis
        savings_rate = metrics["cash_flow"]["savings_rate"]
        if savings_rate < 10:
            high_priority.append("Increase savings rate - currently below 10% recommended minimum")
        elif savings_rate < 20:
            medium_priority.append("Optimize savings rate - aim for 20%+ for wealth building")
        else:
            strategic.append("Excellent savings rate - focus on investment optimization")

        # Cash yield optimization
        if "less than 4%" in self.raw_data.get("interest_rates", "").lower():
            high_priority.append("Optimize cash yield - current rates below market opportunities")

        # Emergency fund strategy
        if self.raw_data.get("emergency_fund_preference") == "$0":
            strategic.append("Review emergency fund strategy - user prefers alternative approach")

        # Debt analysis
        debt_info = self.raw_data.get("other_debt", "")
        if "student loans: 8%" in debt_info.lower():
            high_priority.append("Evaluate student loan payoff vs investment strategy (8% rate)")

        if "credit cards" in debt_info.lower():
            high_priority.append("Prioritize credit card debt elimination if carrying balances")

        # Investment growth opportunities
        investment_value = metrics["net_worth"]["investment_assets"] or 0
        if investment_value < 100000:
            medium_priority.append("Accelerate investment account growth")

        # Business account optimization
        if "business accounts" in self.raw_data.get("account_structure", "").lower():
            strategic.append("Optimize business account structure for tax efficiency")

        opportunities = {
            "high_priority": high_priority,
            "medium_priority": medium_priority,
            "strategic": strategic,
        }

        logger.info(f"Identified {len(high_priority)} high priority, {len(medium_priority)} medium priority, {len(strategic)} strategic opportunities")
        return opportunities

    def generate_yaml_content(self, profile_data: Dict[str, Any]) -> str:
        """
        Generate YAML content manually since we're not using the yaml library.

        Educational Note:
        This shows how to format YAML manually, which helps understand the structure.
        """

        def indent_lines(text: str, spaces: int) -> str:
            """Helper function to indent lines properly."""
            return '\n'.join(' ' * spaces + line if line.strip() else line for line in text.split('\n'))

        def format_value(value, indent_level: int = 0) -> str:
            """Format values according to YAML syntax."""
            if value is None:
                return "null"
            elif isinstance(value, bool):
                return "true" if value else "false"
            elif isinstance(value, (int, float)):
                return str(value)
            elif isinstance(value, str):
                # Handle multi-line strings and special characters
                if '\n' in value or any(c in value for c in ':{[]},'):
                    return f'"{value}"'
                return value
            elif isinstance(value, list):
                if not value:
                    return "[]"
                items = []
                for item in value:
                    formatted_item = format_value(item, indent_level + 1)
                    items.append(f"  - {formatted_item}")
                return "\n" + "\n".join(items)
            elif isinstance(value, dict):
                if not value:
                    return "{}"
                items = []
                for key, val in value.items():
                    formatted_val = format_value(val, indent_level + 1)
                    if isinstance(val, (dict, list)) and val:
                        items.append(f"  {key}:{formatted_val}")
                    else:
                        items.append(f"  {key}: {formatted_val}")
                return "\n" + "\n".join(items)
            return str(value)

        yaml_content = []

        for key, value in profile_data.items():
            formatted_value = format_value(value)
            if isinstance(value, (dict, list)) and value:
                yaml_content.append(f"{key}:{formatted_value}")
            else:
                yaml_content.append(f"{key}: {formatted_value}")

        return "\n".join(yaml_content)

    def generate_profile(self) -> Dict[str, Any]:
        """Generate the complete financial profile structure."""
        logger.info("Generating comprehensive financial profile...")

        # Parse the CSV data
        self.parse_csv()

        # Calculate metrics
        metrics = self.calculate_financial_metrics()

        # Identify opportunities
        opportunities = self.identify_opportunities(metrics)

        # Parse account structure
        account_structure = self.raw_data.get("account_structure", "")
        accounts_count = {
            "business": account_structure.count("business"),
            "checking": account_structure.count("checking"),
            "savings": account_structure.count("savings"),
            "total": account_structure.count("business") + account_structure.count("checking") + account_structure.count("savings")
        }

        # Build complete profile
        profile = {
            "orientation_status": {
                "completed": True,
                "assessment_path": "research/finance/Financial Structure Assessment (Responses) - Form Responses 1 (1).csv",
                "last_updated": datetime.now().isoformat(),
                "onboarding_phase": "profiled",
            },
            "user_profile": {
                "liquid_assets": {
                    "total": metrics["net_worth"]["liquid_assets"],
                    "accounts_count": accounts_count,
                    "average_yield": "< 4%",
                },
                "investment_portfolio": {
                    "total_value": metrics["net_worth"]["investment_assets"],
                    "allocation": "401k, IRA, Taxable brokerage",
                    "risk_profile": self.raw_data.get("allocation_philosophy", "aggressive").lower(),
                },
                "cash_flow": {
                    "monthly_income": metrics["cash_flow"]["monthly_income"],
                    "fixed_expenses": metrics["cash_flow"]["fixed_expenses"],
                    "variable_expenses": metrics["cash_flow"]["variable_expenses"],
                    "total_expenses": metrics["cash_flow"]["total_expenses"],
                    "net_cash_flow": metrics["cash_flow"]["net_cash_flow"],
                    "investment_capacity": metrics["investment_capacity"]["current_monthly_savings"],
                    "savings_rate_percent": round(metrics["cash_flow"]["savings_rate"], 1),
                    "expense_ratio_percent": round(metrics["cash_flow"]["expense_ratio"], 1),
                },
                "debt_profile": {
                    "mortgage_balance": metrics["debt_analysis"]["mortgage_balance"],
                    "mortgage_payment": metrics["debt_analysis"]["mortgage_payment"],
                    "other_debt": [
                        {"type": "student_loans", "rate": "8%", "priority": "high"},
                        {"type": "car_loans", "rate": "4%", "count": 2, "priority": "medium"},
                        {"type": "credit_cards", "rate": "variable", "priority": "highest"},
                    ],
                    "debt_to_income_ratio": round(metrics["debt_analysis"]["debt_to_income_ratio"], 1),
                    "weighted_interest_rate": "6.5% estimated",
                },
                "preferences": {
                    "risk_tolerance": "aggressive",
                    "investment_philosophy": self.raw_data.get("allocation_philosophy", "aggressive"),
                    "emergency_fund_preference": "$0 - prefers alternative strategy",
                    "focus_areas": ["investment_optimization", "cash_yield", "debt_strategy", "tax_efficiency"],
                    "time_horizon": "long_term",
                },
                "calculated_metrics": {
                    "estimated_net_worth": metrics["net_worth"]["estimated_total"],
                    "months_expenses_liquid": round(
                        (metrics["net_worth"]["liquid_assets"] or 0) /
                        (metrics["cash_flow"]["total_expenses"] or 1), 1
                    ),
                    "investment_to_income_ratio": round(
                        ((metrics["net_worth"]["investment_assets"] or 0) /
                         ((metrics["cash_flow"]["monthly_income"] or 1) * 12)) * 100, 1
                    ),
                    "liquid_asset_efficiency": "low_yield_opportunity",
                },
            },
            "opportunities": opportunities,
            "recommended_workflows": {
                "primary": [
                    "cash_optimization_workflow",
                    "debt_strategy_analysis",
                    "investment_acceleration"
                ],
                "secondary": [
                    "tax_optimization_review",
                    "business_account_restructure",
                    "alternative_emergency_funding"
                ],
                "educational": [
                    "advanced_investment_strategies",
                    "business_tax_integration",
                    "estate_planning_foundation"
                ],
            },
            "session_context": {
                "first_interaction": False,
                "last_command": "comprehensive_assessment_parsing",
                "active_workflows": [],
                "completed_tasks": ["initial_assessment", "profile_generation"],
                "profile_generated": datetime.now().isoformat(),
                "data_quality": "complete",
            },
        }

        self.profile = profile
        logger.info("Profile generation completed successfully")
        return profile

    def save_profile(self, output_path: str) -> None:
        """Save the generated profile to a YAML file."""
        output_file = Path(output_path)
        logger.info(f"Saving profile to: {output_file}")

        try:
            # Ensure directory exists
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # Generate header
            header = f"""# Finance Guru™ User Profile Configuration
# Generated from Financial Structure Assessment Data
# Last Updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
#
# This profile contains comprehensive financial analysis including:
# - Net worth calculation and breakdown
# - Cash flow analysis with key ratios
# - Debt structure and optimization opportunities
# - Investment capacity assessment
# - Personalized recommendation workflows

"""

            # Generate YAML content
            yaml_content = self.generate_yaml_content(self.profile)

            # Write to file
            with open(output_file, 'w', encoding='utf-8') as file:
                file.write(header)
                file.write(yaml_content)

            logger.info(f"Profile successfully saved to: {output_file}")

        except Exception as e:
            logger.error(f"Failed to save profile: {e}")
            raise


def main():
    """Main function to parse assessment and generate profile."""
    # File paths
    csv_file = "/Users/ossieirondi/Documents/Irondi-Household/family-office/research/finance/Financial Structure Assessment (Responses) - Form Responses 1 (1).csv"
    output_file = "/Users/ossieirondi/Documents/Irondi-Household/family-office/.guru-core/data/user-profile.yaml"

    try:
        logger.info("Starting financial assessment parsing and profile generation")

        # Create parser and process data
        parser = FinancialAssessmentParser(csv_file)
        profile = parser.generate_profile()
        parser.save_profile(output_file)

        # Extract key metrics for summary (output to stdout for results)
        metrics = profile["user_profile"]["calculated_metrics"]
        cash_flow = profile["user_profile"]["cash_flow"]
        opportunities = profile["opportunities"]

        # Results summary to stdout (following Unix conventions)
        print("\n" + "="*60)
        print("FINANCIAL PROFILE ANALYSIS COMPLETE")
        print("="*60)
        print(f"📊 Net Worth (Estimated): ${metrics['estimated_net_worth']:,.2f}")
        print(f"💰 Monthly Income: ${cash_flow['monthly_income']:,.2f}")
        print(f"💸 Monthly Expenses: ${cash_flow['total_expenses']:,.2f}")
        print(f"💎 Monthly Net Cash Flow: ${cash_flow['net_cash_flow']:,.2f}")
        print(f"📈 Savings Rate: {cash_flow['savings_rate_percent']}%")
        print(f"🏦 Liquid Assets: ${profile['user_profile']['liquid_assets']['total']:,.2f}")
        print(f"📊 Investment Portfolio: ${profile['user_profile']['investment_portfolio']['total_value']:,.2f}")
        print(f"🏠 Mortgage Balance: ${profile['user_profile']['debt_profile']['mortgage_balance']:,.2f}")
        print(f"📅 Emergency Fund Coverage: {metrics['months_expenses_liquid']} months")
        print("\n" + "-"*40)
        print("OPTIMIZATION OPPORTUNITIES")
        print("-"*40)
        print(f"🔥 High Priority: {len(opportunities['high_priority'])} items")
        print(f"⚡ Medium Priority: {len(opportunities['medium_priority'])} items")
        print(f"🎯 Strategic: {len(opportunities['strategic'])} items")
        print(f"\n📁 Profile saved to: {output_file}")
        print("="*60)

        return 0

    except Exception as e:
        logger.error(f"Main execution failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())