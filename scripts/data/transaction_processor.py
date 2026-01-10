#!/usr/bin/env python3
"""
Transaction Processor for Finance Guru TransactionSyncing Skill

Reads Accounts_History.csv and enriches it with:
- Category (based on pattern matching)
- Balance (from original Fidelity CSV)
- Settlement Date (from original Fidelity CSV)

Usage:
    uv run python scripts/transaction_processor.py
"""

import csv
import re
from pathlib import Path
from typing import Optional

# Paths
ACCOUNTS_HISTORY = Path("notebooks/transactions/Accounts_History.csv")
FIDELITY_HISTORY = Path("notebooks/transactions/History_for_Account_Z05724592.csv")
OUTPUT_CSV = Path("notebooks/transactions/Accounts_History_Enhanced.csv")


# ============================================================================
# CATEGORY PATTERNS (from CategoryRules.md)
# ============================================================================

EXPENSE_PATTERNS = {
    "Groceries": [
        "h-e-b", "heb", "kroger", "costco", "wal-mart", "walmart",
        "wm supercenter",  # Walmart abbreviated
        "wholefds", "whole foods", "makola", "sam's club", "aldi",
        "trader joe", "african depot"
    ],
    "Dining Out": [
        "benihana", "golden corral", "papa john", "chuck e cheese",
        "wingstop", "cinemark", "mcdonald", "chick-fil-a", "chipotle",
        "starbucks", "coffee", "restaurant", "grill", "cafe", "makiin",
        "sparkly photo", "mexican sugar", "twin liquors", "annie",
        "toyota center", "levy@"  # Venue concessions
    ],
    "Auto & Transport": [
        "tesla", "supercha", "parking", "fastpark", "uber", "lyft",
        "shell", "exxon", "chevron", "valero", "buc-ee", "gas station", "toll"
    ],
    "Personal Care": [
        "salon", "spa", "barber", "sephora", "beauty supply", "supreme beauty",
        "ulta", "nail", "hair", "shaving grace", "gloss* skin", "cash app", "skims"
    ],
    "Health & Wellness": [
        "cvs", "pharmacy", "walgreens", "life time", "doctor", "medical",
        "dental", "clinic", "hospital", "urgent care", "texas childrens"
    ],
    "Shopping": [
        "marshalls", "target", "amazon", "tj maxx", "ross", "old navy",
        "gap", "nordstrom", "nordrack", "macy", "best buy", "apple store", "micro electron"
    ],
    "Family Care": [
        "aqua tots", "brightwheel", "brghtwhl", "daycare", "childcare",
        "school", "kid", "children", "pediatric", "urban air", "space center"
    ],
    "Bills & Utilities": [
        "autopay", "acctverify", "electric", "water", "internet",
        "comcast", "verizon", "t-mobile", "netflix", "spotify",
        "subscription", "bmobnk"
    ],
    "Cash Withdrawal": [
        "atm", "cash withdrawal", "cash advance"
    ],
    "Tuition": [
        "regent univer", "university", "college", "tuition",
        "education", "coursera", "udemy"
    ],
    "Business Expense": [
        "gumroad", "ups", "fedex", "office depot", "staples",
        "postal", "usps", "business", "linkedin", "zoom", "kindle"
    ],
    "Loan Payment": [
        "wells fargo", "loan payment", "mortgage", "car payment",
        "student loan", "credit card payment", "aes stdnt"
    ],
    "Home & Garden": [
        "home depot", "lowes", "sawyer", "smart core", "garden",
        "hardware", "furniture"
    ],
    "Cell Phone": [
        "att*bill", "at&t", "sprint"
    ],
    "Crypto Deposit": [
        "btc deposited", "bitcoin", "fidelity crypto", "eth deposited", "crypto"
    ],
    "Credit Card Payment": [
        "applecard", "gsbapayment", "chase payment", "amex payment", "discover payment"
    ],
}


def categorize_expense(description: str) -> str:
    """Categorize an expense based on description patterns."""
    desc_lower = description.lower()

    for category, patterns in EXPENSE_PATTERNS.items():
        for pattern in patterns:
            if pattern in desc_lower:
                return category

    return "Uncategorized"


def categorize_transaction(action: str, description: str) -> str:
    """Assign category based on action type and description."""
    action_lower = action.lower()
    desc_lower = description.lower()

    # Investment categories
    if "dividend" in action_lower:
        return "DIVIDEND"
    if "reinvestment" in action_lower:
        return "REINVESTMENT"
    if "margin interest" in action_lower:
        return "MARGIN_INTEREST"
    if "cap gain" in action_lower:
        return "CAP_GAIN"
    if "direct deposit" in action_lower:
        return "INCOME"
    if "journaled" in action_lower:
        return "INTERNAL_TRANSFER"
    if "you bought" in action_lower:
        return "BUY"
    if "you sold" in action_lower:
        return "SELL"
    if "reverse split" in action_lower:
        return "CORPORATE_ACTION"
    if "in lieu" in action_lower:
        return "CORPORATE_ACTION"
    if "transfer" in action_lower or "acat" in action_lower:
        return "TRANSFER"

    # Crypto transactions (Fidelity Crypto account)
    if "btc deposited" in action_lower or "bitcoin" in desc_lower or "eth deposited" in action_lower:
        return "Crypto Deposit"

    if "direct debit" in action_lower:
        # Check for specific bill types
        return categorize_expense(action + " " + description)
    if "electronic funds" in action_lower:
        return "EFT"

    # Expense categories (debit card, cash advance)
    if "debit card" in action_lower or "cash advance" in action_lower:
        # Use the action text which often contains merchant info
        return categorize_expense(action + " " + description)

    return "OTHER"


def build_fidelity_lookup(fidelity_path: Path) -> dict:
    """
    Build a lookup dictionary from the original Fidelity CSV.
    Key: (date, action_prefix, amount) -> (cash_balance, settlement_date)
    """
    lookup = {}

    if not fidelity_path.exists():
        print(f"Warning: {fidelity_path} not found")
        return lookup

    with open(fidelity_path, 'r', encoding='utf-8-sig') as f:
        # Skip header rows (Fidelity CSV has 2 header rows)
        lines = f.readlines()

        # Find the actual header row
        header_idx = None
        for i, line in enumerate(lines):
            if line.startswith("Run Date,"):
                header_idx = i
                break

        if header_idx is None:
            print("Warning: Could not find header in Fidelity CSV")
            return lookup

        reader = csv.DictReader(lines[header_idx:])

        for row in reader:
            try:
                date = row.get('Run Date', '').strip()
                action = row.get('Action', '').strip()
                amount_str = row.get('Amount ($)', '').strip()
                cash_balance = row.get('Cash Balance ($)', '').strip()
                settlement = row.get('Settlement Date', '').strip()

                if not date or not action:
                    continue

                # Create lookup key using date + first 50 chars of action + amount
                action_prefix = action[:50]
                key = (date, action_prefix, amount_str)
                lookup[key] = (cash_balance, settlement)

            except Exception as e:
                continue

    print(f"Built lookup with {len(lookup)} entries from Fidelity CSV")
    return lookup


def process_transactions():
    """Main processing function."""

    if not ACCOUNTS_HISTORY.exists():
        print(f"Error: {ACCOUNTS_HISTORY} not found")
        return

    # Build lookup from original Fidelity CSV
    fidelity_lookup = build_fidelity_lookup(FIDELITY_HISTORY)

    # Read and process Accounts_History.csv
    processed_rows = []
    categories_added = 0
    balances_found = 0
    settlements_found = 0

    with open(ACCOUNTS_HISTORY, 'r', encoding='utf-8-sig') as f:
        lines = f.readlines()

        # Skip empty lines at the start (CSV has BOM + 2 newlines before header)
        header_idx = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped and stripped.startswith("Run Date"):
                header_idx = i
                break

        print(f"Found header at line {header_idx + 1}")

        # Use DictReader on the lines starting from header
        reader = csv.DictReader(lines[header_idx:])
        fieldnames = list(reader.fieldnames) if reader.fieldnames else []

        # Remove None from fieldnames if present
        fieldnames = [f for f in fieldnames if f is not None]

        # Add new columns if not present
        if 'Category' not in fieldnames:
            fieldnames.append('Category')
        if 'Cash Balance ($)' not in fieldnames:
            fieldnames.append('Cash Balance ($)')

        for row in reader:
            # Handle None values safely
            date = (row.get('Run Date') or '').strip()
            action = (row.get('Action') or '').strip()
            description = (row.get('Description') or '').strip()
            amount = (row.get('Amount ($)') or '').strip()

            # Assign category
            category = categorize_transaction(action, description)
            row['Category'] = category
            categories_added += 1

            # Try to find balance and settlement from Fidelity lookup
            action_prefix = action[:50]
            key = (date, action_prefix, amount)

            if key in fidelity_lookup:
                cash_balance, settlement = fidelity_lookup[key]
                if cash_balance:
                    row['Cash Balance ($)'] = cash_balance
                    balances_found += 1
                if settlement:
                    row['Settlement Date'] = settlement
                    settlements_found += 1

            # Remove None keys from row
            cleaned_row = {k: v for k, v in row.items() if k is not None}
            processed_rows.append(cleaned_row)

    # Write enhanced CSV
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(processed_rows)

    print(f"\n{'='*60}")
    print("TRANSACTION PROCESSING COMPLETE")
    print(f"{'='*60}")
    print(f"Total rows processed: {len(processed_rows)}")
    print(f"Categories assigned:  {categories_added}")
    print(f"Balances found:       {balances_found}")
    print(f"Settlements found:    {settlements_found}")
    print(f"\nOutput saved to: {OUTPUT_CSV}")
    print(f"{'='*60}")

    # Print category breakdown
    category_counts = {}
    for row in processed_rows:
        cat = row.get('Category', 'Unknown')
        category_counts[cat] = category_counts.get(cat, 0) + 1

    print("\nCATEGORY BREAKDOWN:")
    for cat, count in sorted(category_counts.items(), key=lambda x: -x[1]):
        print(f"  {cat:20} {count:4}")


if __name__ == "__main__":
    process_transactions()
