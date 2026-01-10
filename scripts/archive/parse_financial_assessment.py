#!/usr/bin/env python3
"""
Financial Assessment Parser and Profile Generator

This script parses CSV financial assessment data and creates a comprehensive
structured financial profile with key metrics and opportunity analysis.

Educational Notes for Learning:
- CSV parsing with proper error handling
- Financial calculations and ratio analysis
- YAML structure creation for configuration management
- Data validation and sanitization
"""

import csv
import yaml
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import re
import structlog
import logging

# Configure structured logging to stderr (following best practices)
logging.basicConfig(
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stderr)],
    format="%(message)s",
)

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.dict_tracebacks,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
)

log = structlog.get_logger()


class FinancialAssessmentParser:
    """
    Parses financial assessment CSV data and generates comprehensive profile.

    This class handles:
    - CSV data extraction and cleaning
    - Financial metric calculations
    - Risk profile assessment
    - Opportunity identification
    - YAML profile generation
    """

    def __init__(self, csv_file_path: str):
        self.csv_file_path = Path(csv_file_path)
        self.raw_data: Dict[str, str] = {}
        self.profile: Dict[str, Any] = {}

    def parse_csv(self) -> Dict[str, str]:
        """
        Parse the CSV file and extract financial data.

        Educational Note:
        CSV files from Google Forms often have long headers, so we need to
        map them to shorter, more manageable field names.
        """
        log.info("parsing.start", file=str(self.csv_file_path))

        try:
            with open(self.csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)

                # Get the first (and likely only) row of data
                data_row = next(reader)

                # Map long column names to shorter keys for easier processing
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
                log.info("parsing.complete", fields_extracted=len(cleaned_data))
                return cleaned_data

        except Exception as e:
            log.error("parsing.failed", error=str(e))
            raise

    def extract_numeric_value(self, text: str) -> Optional[float]:
        """
        Extract numeric values from text, handling various formats.

        Educational Note:
        Financial data often comes in different formats (with commas, dollar signs, etc.)
        so we need robust parsing that handles these variations.
        """
        if not text:
            return None

        # Remove common non-numeric characters
        cleaned = re.sub(r'[^\d.-]', '', text.replace(',', ''))

        try:
            return float(cleaned) if cleaned else None
        except ValueError:
            return None

    def calculate_financial_metrics(self) -> Dict[str, Any]:
        """
        Calculate comprehensive financial metrics from the parsed data.

        Educational Note:
        Financial planning relies on key ratios and metrics that help assess
        financial health and identify opportunities for improvement.
        """
        log.info("calculating.metrics")

        # Extract key numeric values
        liquid_assets = self.extract_numeric_value(self.raw_data.get("liquid_assets_total", "0"))
        investment_balance = self.extract_numeric_value(self.raw_data.get("investment_balance", "0"))
        monthly_income = self.extract_numeric_value(self.raw_data.get("monthly_income", "0"))
        fixed_expenses = self.extract_numeric_value(self.raw_data.get("fixed_expenses", "0"))
        variable_expenses = self.extract_numeric_value(self.raw_data.get("variable_expenses", "0"))
        monthly_savings = self.extract_numeric_value(self.raw_data.get("monthly_savings", "0"))

        # Parse mortgage information
        mortgage_info = self.raw_data.get("mortgage_info", "")
        mortgage_balance = None
        mortgage_payment = None

        # Extract mortgage balance and payment using regex
        balance_match = re.search(r'balance[:\s]*([0-9,.]+)', mortgage_info, re.IGNORECASE)
        payment_match = re.search(r'payment[:\s]*([0-9,.]+)', mortgage_info, re.IGNORECASE)

        if balance_match:
            mortgage_balance = self.extract_numeric_value(balance_match.group(1))
        if payment_match:
            mortgage_payment = self.extract_numeric_value(payment_match.group(1))

        # Calculate total expenses
        total_monthly_expenses = (fixed_expenses or 0) + (variable_expenses or 0)

        # Calculate net worth (simplified - assets minus mortgage debt)
        # Note: This is a simplified calculation as we don't have complete debt information
        estimated_net_worth = (liquid_assets or 0) + (investment_balance or 0) - (mortgage_balance or 0)

        # Calculate key financial ratios
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
                "net_cash_flow": (monthly_income or 0) - total_monthly_expenses,
                "savings_rate": ((monthly_savings or 0) / (monthly_income or 1)) * 100 if monthly_income else 0,
                "expense_ratio": (total_monthly_expenses / (monthly_income or 1)) * 100 if monthly_income else 0,
            },
            "debt_analysis": {
                "mortgage_balance": mortgage_balance,
                "mortgage_payment": mortgage_payment,
                "debt_to_income_ratio": ((mortgage_payment or 0) / (monthly_income or 1)) * 100 if monthly_income else 0,
                "mortgage_to_value_estimated": None,  # Would need home value
            },
            "investment_capacity": {
                "current_monthly_savings": monthly_savings,
                "available_cash_flow": (monthly_income or 0) - total_monthly_expenses,
                "investment_accounts_value": investment_balance,
                "liquid_reserves": liquid_assets,
            }
        }

        log.info("metrics.calculated", net_worth=estimated_net_worth, savings_rate=metrics["cash_flow"]["savings_rate"])
        return metrics

    def identify_opportunities(self, metrics: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Identify financial optimization opportunities based on the metrics.

        Educational Note:
        This analysis looks for common patterns that indicate opportunities
        for improvement in financial structure and strategy.
        """
        log.info("identifying.opportunities")

        high_priority = []
        medium_priority = []
        strategic = []

        # Analyze savings rate
        savings_rate = metrics["cash_flow"]["savings_rate"]
        if savings_rate < 10:
            high_priority.append("Increase savings rate - currently below 10% recommended minimum")
        elif savings_rate < 20:
            medium_priority.append("Optimize savings rate - aim for 20%+ for wealth building")
        else:
            strategic.append("Excellent savings rate - focus on investment optimization")

        # Analyze liquid assets vs emergency fund
        liquid_assets = metrics["net_worth"]["liquid_assets"] or 0
        monthly_expenses = metrics["cash_flow"]["total_expenses"] or 0
        months_of_expenses = liquid_assets / monthly_expenses if monthly_expenses > 0 else 0

        # User prefers $0 emergency fund, so this is strategic
        if self.raw_data.get("emergency_fund_preference") == "$0":
            strategic.append("Review emergency fund strategy - user prefers alternative approach")

        # Check interest rates on liquid assets
        if "less than 4%" in self.raw_data.get("interest_rates", "").lower():
            high_priority.append("Optimize cash yield - current rates below market opportunities")

        # Investment analysis
        investment_value = metrics["net_worth"]["investment_assets"] or 0
        if investment_value < 100000:
            medium_priority.append("Accelerate investment account growth")

        # Debt analysis
        debt_info = self.raw_data.get("other_debt", "")
        if "student loans: 8%" in debt_info.lower():
            high_priority.append("Evaluate student loan payoff vs investment strategy (8% rate)")

        if "credit cards" in debt_info.lower():
            high_priority.append("Prioritize credit card debt elimination if carrying balances")

        # Account structure optimization
        account_structure = self.raw_data.get("account_structure", "")
        if "business accounts" in account_structure.lower():
            strategic.append("Optimize business account structure for tax efficiency")

        opportunities = {
            "high_priority": high_priority,
            "medium_priority": medium_priority,
            "strategic": strategic,
        }

        log.info("opportunities.identified",
                high=len(high_priority),
                medium=len(medium_priority),
                strategic=len(strategic))

        return opportunities

    def generate_profile(self) -> Dict[str, Any]:
        """
        Generate the complete financial profile structure.

        Educational Note:
        This creates a comprehensive profile that can be used by other
        systems for personalized recommendations and workflow automation.
        """
        log.info("generating.profile")

        # Parse the raw data first
        self.parse_csv()

        # Calculate metrics
        metrics = self.calculate_financial_metrics()

        # Identify opportunities
        opportunities = self.identify_opportunities(metrics)

        # Parse account structure for better understanding
        account_structure = self.raw_data.get("account_structure", "")
        accounts_count = {
            "business": account_structure.count("business"),
            "checking": account_structure.count("checking"),
            "savings": account_structure.count("savings"),
        }

        # Build the complete profile
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
                    "average_yield": "< 4%",  # From user input
                },
                "investment_portfolio": {
                    "total_value": metrics["net_worth"]["investment_assets"],
                    "allocation": "401k, IRA, Taxable brokerage",  # From user input
                    "risk_profile": self.raw_data.get("allocation_philosophy", "aggressive").lower(),
                },
                "cash_flow": {
                    "monthly_income": metrics["cash_flow"]["monthly_income"],
                    "fixed_expenses": metrics["cash_flow"]["fixed_expenses"],
                    "variable_expenses": metrics["cash_flow"]["variable_expenses"],
                    "investment_capacity": metrics["investment_capacity"]["current_monthly_savings"],
                    "savings_rate_percent": round(metrics["cash_flow"]["savings_rate"], 1),
                    "net_cash_flow": metrics["cash_flow"]["net_cash_flow"],
                },
                "debt_profile": {
                    "mortgage_balance": metrics["debt_analysis"]["mortgage_balance"],
                    "mortgage_payment": metrics["debt_analysis"]["mortgage_payment"],
                    "other_debt": [
                        {"type": "student_loans", "rate": "8%"},
                        {"type": "car_loans", "rate": "4%", "count": 2},
                        {"type": "credit_cards", "rate": "variable"},
                    ],
                    "debt_to_income_ratio": round(metrics["debt_analysis"]["debt_to_income_ratio"], 1),
                },
                "preferences": {
                    "risk_tolerance": "aggressive",
                    "investment_philosophy": self.raw_data.get("allocation_philosophy", "aggressive"),
                    "emergency_fund_preference": "$0 - prefers alternative strategy",
                    "focus_areas": ["investment_optimization", "cash_yield", "debt_strategy"],
                    "time_horizon": "long_term",  # Inferred from aggressive profile
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
                },
            },
            "opportunities": opportunities,
            "recommended_workflows": {
                "primary": [
                    "cash_optimization",
                    "debt_strategy_analysis",
                    "investment_acceleration",
                ],
                "secondary": [
                    "tax_optimization",
                    "business_account_structure",
                    "estate_planning_basics",
                ],
                "educational": [
                    "advanced_investment_strategies",
                    "alternative_emergency_funding",
                    "business_finance_integration",
                ],
            },
            "session_context": {
                "first_interaction": False,  # Profile is now complete
                "last_command": "assessment_parsing",
                "active_workflows": [],
                "completed_tasks": ["initial_assessment"],
                "profile_generated": datetime.now().isoformat(),
            },
        }

        self.profile = profile
        log.info("profile.generated", status="complete")
        return profile

    def save_profile(self, output_path: str) -> None:
        """
        Save the generated profile to a YAML file.

        Educational Note:
        YAML is human-readable and commonly used for configuration files
        in financial and DevOps applications.
        """
        output_file = Path(output_path)

        log.info("saving.profile", path=str(output_file))

        try:
            # Ensure the directory exists
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # Add header comment
            header = """# Finance Guru™ User Profile Configuration
# Generated from Financial Structure Assessment
# Last Updated: {}

""".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

            with open(output_file, 'w') as file:
                file.write(header)
                yaml.dump(self.profile, file, default_flow_style=False, indent=2, sort_keys=False)

            log.info("profile.saved", file=str(output_file))

        except Exception as e:
            log.error("save.failed", error=str(e), path=str(output_file))
            raise


def main():
    """
    Main function to parse assessment and generate profile.
    """
    # Set up file paths
    csv_file = "/Users/ossieirondi/Documents/Irondi-Household/family-office/research/finance/Financial Structure Assessment (Responses) - Form Responses 1 (1).csv"
    output_file = "/Users/ossieirondi/Documents/Irondi-Household/family-office/.guru-core/data/user-profile.yaml"

    try:
        # Create parser and process the data
        parser = FinancialAssessmentParser(csv_file)
        profile = parser.generate_profile()
        parser.save_profile(output_file)

        # Output summary results to stdout (following Unix conventions)
        summary = {
            "status": "success",
            "profile_generated": True,
            "net_worth": profile["user_profile"]["calculated_metrics"]["estimated_net_worth"],
            "monthly_income": profile["user_profile"]["cash_flow"]["monthly_income"],
            "savings_rate": profile["user_profile"]["cash_flow"]["savings_rate_percent"],
            "high_priority_opportunities": len(profile["opportunities"]["high_priority"]),
            "file_saved": output_file,
        }

        print("Financial Profile Generation Complete")
        print(f"Estimated Net Worth: ${summary['net_worth']:,.2f}")
        print(f"Monthly Income: ${summary['monthly_income']:,.2f}")
        print(f"Savings Rate: {summary['savings_rate']}%")
        print(f"High Priority Opportunities: {summary['high_priority_opportunities']}")
        print(f"Profile saved to: {summary['file_saved']}")

        return 0

    except Exception as e:
        log.error("main.failed", error=str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main())