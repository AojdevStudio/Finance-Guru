"""
Fidelity Transaction Parser Constants

Contains all mappings, patterns, and constants for transaction classification.

This module defines:
    - Fidelity action type → TransactionType mappings
    - Merchant extraction regex patterns
    - Expense category keyword patterns
    - Column name mappings for CSV parsing

MAINTENANCE:
To add new merchant patterns:
    1. Add to MERCHANT_PATTERNS dict under appropriate category
    2. Order patterns from most specific to least specific
    3. Test with sample data

Author: Finance Guru™ Development Team
Created: 2026-01-12
"""

import re
from typing import Callable, Pattern

from src.models.transaction_inputs import TransactionType, ExpenseCategory

# =============================================================================
# FIDELITY ACTION → TRANSACTION TYPE MAPPINGS
# =============================================================================

FIDELITY_ACTION_MAPPINGS: dict[str, TransactionType] = {
    # Spending (reclassify as expenses)
    "DEBIT CARD PURCHASE": TransactionType.EXPENSE,
    "ELECTRONIC FUNDS TRANSFER": TransactionType.EXPENSE,
    "CHECK PAID": TransactionType.EXPENSE,
    "WIRE SENT": TransactionType.EXPENSE,
    "ACH DEBIT": TransactionType.EXPENSE,
    "DIRECT DEBIT": TransactionType.EXPENSE,
    "DEBIT": TransactionType.EXPENSE,

    # Income (reclassify as income)
    "DIRECT DEPOSIT": TransactionType.INCOME,
    "ACH CREDIT": TransactionType.INCOME,
    "WIRE RECEIVED": TransactionType.INCOME,
    "DIVIDEND RECEIVED": TransactionType.INCOME,
    "DIVIDEND": TransactionType.INCOME,
    "INTEREST": TransactionType.INCOME,
    "INTEREST EARNED": TransactionType.INCOME,
    "LONG-TERM CAP GAIN": TransactionType.INCOME,
    "SHORT-TERM CAP GAIN": TransactionType.INCOME,
    "RETURN OF CAPITAL": TransactionType.INCOME,
    "CREDIT": TransactionType.INCOME,

    # Margin Activity
    "MARGIN INTEREST": TransactionType.MARGIN_COST,
    "INTEREST CHARGED": TransactionType.MARGIN_COST,
    "MARGIN DEBIT": TransactionType.MARGIN_DRAW,
    "MARGIN CREDIT": TransactionType.MARGIN_PAYDOWN,

    # Investment Activity
    "BUY": TransactionType.INVESTMENT,
    "BOUGHT": TransactionType.INVESTMENT,
    "SELL": TransactionType.INVESTMENT,
    "SOLD": TransactionType.INVESTMENT,
    "REINVESTMENT": TransactionType.INVESTMENT,
    "YOU BOUGHT": TransactionType.INVESTMENT,
    "YOU SOLD": TransactionType.INVESTMENT,

    # Transfers
    "TRANSFER IN": TransactionType.TRANSFER,
    "TRANSFER OUT": TransactionType.TRANSFER,
    "JOURNALED": TransactionType.TRANSFER,
    "JOURNAL": TransactionType.TRANSFER,
    "INTERNAL TRANSFER": TransactionType.TRANSFER,

    # Money Market Operations
    "REDEMPTION": TransactionType.AUTO_LIQUIDATION,
    "PURCHASE": TransactionType.AUTO_PURCHASE,
    "CASH MANAGEMENT": TransactionType.AUTO_PURCHASE,
}

# Partial match patterns for actions that may have additional text
FIDELITY_ACTION_PATTERNS: list[tuple[str, TransactionType]] = [
    ("DEBIT CARD", TransactionType.EXPENSE),
    ("DIVIDEND", TransactionType.INCOME),
    ("DIRECT DEPOSIT", TransactionType.INCOME),
    ("MARGIN INTEREST", TransactionType.MARGIN_COST),
    ("REINVEST", TransactionType.INVESTMENT),
    ("TRANSFER", TransactionType.TRANSFER),
    ("JOURNAL", TransactionType.TRANSFER),
    ("CAP GAIN", TransactionType.INCOME),
    ("INTEREST EARNED", TransactionType.INCOME),
]


# =============================================================================
# MERCHANT EXTRACTION PATTERNS
# =============================================================================

# Compiled regex patterns for extracting clean merchant names
# Each pattern: (regex, replacement/extractor)
# Use group(1) or callable to extract merchant name

MerchantExtractor = Callable[[re.Match], str]

MERCHANT_PATTERNS: list[tuple[Pattern, str | MerchantExtractor]] = [
    # Major retailers
    (re.compile(r"^AMAZON\.COM\*.*", re.I), "Amazon"),
    (re.compile(r"^AMZN\s+MKTP\s+US\*.*", re.I), "Amazon"),
    (re.compile(r"^AMAZON\s+PRIME\*.*", re.I), "Amazon Prime"),
    (re.compile(r"^WHOLEFDS?\s+MKT\s*#?\d*.*", re.I), "Whole Foods"),
    (re.compile(r"^WHOLE\s+FOODS.*", re.I), "Whole Foods"),
    (re.compile(r"^WAL-?MART.*", re.I), "Walmart"),
    (re.compile(r"^TARGET\s+\d+.*", re.I), "Target"),
    (re.compile(r"^COSTCO\s+WHSE.*", re.I), "Costco"),
    (re.compile(r"^SAM\'?S\s+CLUB.*", re.I), "Sam's Club"),
    (re.compile(r"^H-?E-?B\s*#?\d*.*", re.I), "H-E-B"),
    (re.compile(r"^KROGER\s*#?\d*.*", re.I), "Kroger"),

    # Ride share / Delivery
    (re.compile(r"^UBER\s+\*?EATS.*", re.I), "Uber Eats"),
    (re.compile(r"^UBER\s+\*?TRIP.*", re.I), "Uber"),
    (re.compile(r"^UBER\s+\*.*", re.I), "Uber"),
    (re.compile(r"^LYFT\s+\*.*", re.I), "Lyft"),
    (re.compile(r"^DOORDASH\*.*", re.I), "DoorDash"),
    (re.compile(r"^GRUBHUB.*", re.I), "Grubhub"),
    (re.compile(r"^INSTACART.*", re.I), "Instacart"),

    # Square merchants (SQ *)
    (re.compile(r"^SQ\s+\*(.+?)(?:\s+\w{2}\s*$|\s+\d)", re.I),
     lambda m: m.group(1).strip().title()),
    (re.compile(r"^SQ\s+\*(.+)", re.I),
     lambda m: m.group(1).strip().title()),

    # Toast merchants (TST*)
    (re.compile(r"^TST\*\s*(.+?)(?:\s+\w{2}\s*$|\s+\d)", re.I),
     lambda m: m.group(1).strip().title()),
    (re.compile(r"^TST\*(.+)", re.I),
     lambda m: m.group(1).strip().title()),

    # PayPal
    (re.compile(r"^PAYPAL\s+\*(.+?)(?:\s+\d)", re.I),
     lambda m: m.group(1).strip().title()),
    (re.compile(r"^PAYPAL\s+\*(.+)", re.I),
     lambda m: m.group(1).strip().title()),

    # Google services
    (re.compile(r"^GOOGLE\s+\*(.+)", re.I),
     lambda m: f"Google {m.group(1).strip().title()}"),

    # Apple
    (re.compile(r"^APPLE\.COM/BILL.*", re.I), "Apple"),
    (re.compile(r"^APPLE\s+STORE.*", re.I), "Apple Store"),
    (re.compile(r"^APL\*\s*APPLE.*", re.I), "Apple"),

    # Tesla
    (re.compile(r"^Tesla,?\s+Inc\.?\s+SUPERCHA.*", re.I), "Tesla Supercharger"),
    (re.compile(r"^Tesla\s+Property.*", re.I), "Tesla Insurance"),
    (re.compile(r"^TESLA\s+MOTORS.*", re.I), "Tesla"),

    # Gas stations
    (re.compile(r"^SHELL\s+(OIL|SERVICE).*", re.I), "Shell"),
    (re.compile(r"^EXXONMOBIL.*", re.I), "Exxon"),
    (re.compile(r"^CHEVRON\s*\d*.*", re.I), "Chevron"),
    (re.compile(r"^VALERO\s*\d*.*", re.I), "Valero"),
    (re.compile(r"^BUC-?EE\'?S.*", re.I), "Buc-ee's"),

    # Coffee shops
    (re.compile(r"^STARBUCKS.*", re.I), "Starbucks"),
    (re.compile(r"^DUNKIN.*", re.I), "Dunkin"),

    # Fast food
    (re.compile(r"^MCDONALD\'?S.*", re.I), "McDonald's"),
    (re.compile(r"^CHICK-?FIL-?A.*", re.I), "Chick-fil-A"),
    (re.compile(r"^CHIPOTLE.*", re.I), "Chipotle"),
    (re.compile(r"^WENDY\'?S.*", re.I), "Wendy's"),
    (re.compile(r"^TACO\s+BELL.*", re.I), "Taco Bell"),
    (re.compile(r"^WHATABURGER.*", re.I), "Whataburger"),
    (re.compile(r"^PAPA\s+JOHN\'?S?.*", re.I), "Papa John's"),
    (re.compile(r"^DOMINO\'?S.*", re.I), "Domino's"),
    (re.compile(r"^WINGSTOP.*", re.I), "Wingstop"),

    # Pharmacies
    (re.compile(r"^CVS/?PHARMACY.*", re.I), "CVS"),
    (re.compile(r"^WALGREENS.*", re.I), "Walgreens"),

    # Entertainment
    (re.compile(r"^NETFLIX.*", re.I), "Netflix"),
    (re.compile(r"^SPOTIFY.*", re.I), "Spotify"),
    (re.compile(r"^HULU.*", re.I), "Hulu"),
    (re.compile(r"^DISNEY\s*PLUS.*", re.I), "Disney+"),
    (re.compile(r"^HBO\s*MAX.*", re.I), "HBO Max"),
    (re.compile(r"^APPLE\s+TV.*", re.I), "Apple TV+"),
    (re.compile(r"^YOUTUBE\s+PREMIUM.*", re.I), "YouTube Premium"),
    (re.compile(r"^CINEMARK.*", re.I), "Cinemark"),
    (re.compile(r"^AMC\s+THEATRE.*", re.I), "AMC Theatres"),

    # ATM
    (re.compile(r"^ATM\d*\s+.*", re.I), "ATM Withdrawal"),

    # Banks/Financial
    (re.compile(r"^WELLS\s+FARGO.*", re.I), "Wells Fargo"),
    (re.compile(r"^CHASE.*", re.I), "Chase"),
    (re.compile(r"^APPLECARD\s+GSBA.*", re.I), "Apple Card Payment"),

    # Fitness
    (re.compile(r"^LIFE\s*TIME.*", re.I), "Life Time Fitness"),
    (re.compile(r"^PLANET\s+FITNESS.*", re.I), "Planet Fitness"),
    (re.compile(r"^LA\s+FITNESS.*", re.I), "LA Fitness"),
    (re.compile(r"^EQUINOX.*", re.I), "Equinox"),

    # Retail
    (re.compile(r"^BEST\s+BUY.*", re.I), "Best Buy"),
    (re.compile(r"^MARSHALLS.*", re.I), "Marshalls"),
    (re.compile(r"^TJ\s*MAXX.*", re.I), "TJ Maxx"),
    (re.compile(r"^ROSS\s+STORES.*", re.I), "Ross"),
    (re.compile(r"^OLD\s+NAVY.*", re.I), "Old Navy"),
    (re.compile(r"^NORDSTROM.*", re.I), "Nordstrom"),
    (re.compile(r"^MACY\'?S.*", re.I), "Macy's"),
    (re.compile(r"^HOME\s+DEPOT.*", re.I), "Home Depot"),
    (re.compile(r"^LOWE\'?S.*", re.I), "Lowe's"),
    (re.compile(r"^SEPHORA.*", re.I), "Sephora"),
    (re.compile(r"^ULTA.*", re.I), "Ulta"),

    # Childcare
    (re.compile(r"^AQUA\s*TOTS.*", re.I), "Aqua-Tots"),
    (re.compile(r"^BRGHTWHL.*", re.I), "Brightwheel"),
    (re.compile(r"^BRIGHTWHEEL.*", re.I), "Brightwheel"),
]


# =============================================================================
# EXPENSE CATEGORY PATTERNS
# =============================================================================

# Keywords that map to expense categories
# Order matters - first match wins
# Keywords are matched case-insensitively

CATEGORY_PATTERNS: dict[ExpenseCategory, list[str]] = {
    ExpenseCategory.GROCERIES: [
        "h-e-b", "heb", "kroger", "costco", "wal-mart", "walmart",
        "wholefds", "whole foods", "makola", "sam's club", "aldi",
        "trader joe", "sprouts", "publix", "safeway", "albertsons",
        "food lion", "piggly wiggly", "winn-dixie", "grocery",
    ],

    ExpenseCategory.DINING: [
        "benihana", "golden corral", "papa john", "chuck e cheese",
        "wingstop", "cinemark", "mcdonald", "chick-fil-a", "chipotle",
        "starbucks", "coffee", "restaurant", "grill", "cafe", "bistro",
        "pizza", "sushi", "taco", "burrito", "burger", "doordash",
        "uber eats", "grubhub", "postmates", "seamless", "domino",
        "wendy", "whataburger", "dunkin", "panera", "subway", "makiin",
        "sonic", "dairy queen", "ihop", "denny", "applebee", "chili's",
        "olive garden", "red lobster", "outback", "longhorn",
    ],

    ExpenseCategory.TRANSPORTATION: [
        "tesla", "supercha", "parking", "fastpark", "uber", "lyft",
        "shell", "exxon", "chevron", "valero", "buc-ee", "gas station",
        "toll", "ez-pass", "tollway", "metro", "transit", "airport",
        "rental car", "hertz", "enterprise", "avis", "budget rental",
    ],

    ExpenseCategory.GAS: [
        "shell oil", "exxonmobil", "chevron gas", "bp amoco", "mobil",
        "76 station", "speedway", "racetrac", "murphy usa", "quiktrip",
    ],

    ExpenseCategory.PERSONAL: [
        "salon", "spa", "barber", "sephora", "beauty supply", "supreme beauty",
        "ulta", "nail", "hair", "shaving grace", "gloss* skin", "cash app",
        "massage", "facial", "waxing", "cosmetics",
    ],

    ExpenseCategory.HEALTHCARE: [
        "cvs", "pharmacy", "walgreens", "life time", "doctor", "medical",
        "dental", "clinic", "hospital", "urgent care", "optometrist",
        "vision", "lab corp", "quest diagnostic", "insurance premium",
        "copay", "healthcare",
    ],

    ExpenseCategory.SHOPPING: [
        "marshalls", "target", "amazon", "skims", "tj maxx", "ross",
        "old navy", "gap", "nordstrom", "macy", "best buy", "apple store",
        "nike", "adidas", "home goods", "bed bath", "pottery barn",
        "williams sonoma", "crate barrel", "ikea", "wayfair",
    ],

    ExpenseCategory.FAMILY: [
        "aqua tots", "brightwheel", "brghtwhl", "daycare", "childcare",
        "school", "kid", "children", "pediatric", "baby", "toys r us",
        "buy buy baby", "carter",
    ],

    ExpenseCategory.UTILITIES: [
        "autopay", "acctverify", "electric", "water", "internet",
        "comcast", "att", "verizon", "t-mobile", "netflix", "spotify",
        "subscription", "xfinity", "spectrum", "frontier", "hulu",
        "disney+", "hbo", "streaming", "cable",
    ],

    ExpenseCategory.CELL_PHONE: [
        "t-mobile wireless", "verizon wireless", "at&t wireless",
        "sprint", "mint mobile", "cricket", "metro pcs",
    ],

    ExpenseCategory.ELECTRIC: [
        "centerpoint", "txu energy", "reliant energy", "direct energy",
        "electric bill", "power company",
    ],

    ExpenseCategory.WATER: [
        "water bill", "water utility", "municipal water", "city water",
    ],

    ExpenseCategory.MORTGAGE: [
        "mortgage", "home loan", "principal residence",
    ],

    ExpenseCategory.CASH: [
        "atm", "cash withdrawal", "cash advance", "cash back",
    ],

    ExpenseCategory.EDUCATION: [
        "regent univer", "university", "college", "tuition", "school",
        "education", "coursera", "udemy", "linkedin learning", "skillshare",
    ],

    ExpenseCategory.BUSINESS: [
        "gumroad", "ups", "fedex", "office depot", "staples", "postal",
        "usps", "business", "linkedin", "zoom", "notion", "slack",
        "microsoft 365", "adobe", "github", "aws", "hosting",
    ],

    ExpenseCategory.LOAN_PAYMENT: [
        "wells fargo draft", "wells fargo audraft", "loan payment",
        "car payment", "student loan", "credit card payment",
        "navient", "sallie mae", "sofi loan",
    ],

    ExpenseCategory.CREDIT_CARD: [
        "applecard", "gsbapayment", "chase payment", "amex payment",
        "discover payment", "capital one payment", "citi payment",
    ],

    ExpenseCategory.HOME_GARDEN: [
        "home depot", "lowes", "sawyer", "smart core", "garden",
        "hardware", "furniture", "ace hardware", "menards",
        "true value", "landscap",
    ],

    ExpenseCategory.CRYPTO: [
        "btc deposited", "bitcoin", "fidelity crypto", "eth deposited",
        "crypto", "coinbase", "binance", "kraken",
    ],

    ExpenseCategory.ENTERTAINMENT: [
        "cinemark", "amc theatre", "regal cinema", "bowling", "arcade",
        "dave & buster", "topgolf", "concert", "ticketmaster", "stubhub",
        "eventbrite", "museum", "zoo", "theme park", "six flags",
    ],

    ExpenseCategory.SUBSCRIPTIONS: [
        "monthly", "annual subscription", "recurring", "membership",
        "patreon", "substack",
    ],

    ExpenseCategory.TRAVEL: [
        "airline", "hotel", "airbnb", "vrbo", "expedia", "booking.com",
        "delta", "united", "southwest", "american airlines", "jetblue",
        "hilton", "marriott", "hyatt", "holiday inn", "motel",
    ],

    ExpenseCategory.SOFTWARE: [
        "app store", "google play", "software", "saas", "api",
        "digital service", "cloud service", "hostinger", "namecheap",
        "godaddy", "domain",
    ],

    ExpenseCategory.EXEMPT: [
        "ifacctverify", "verification", "test charge",
    ],
}


# =============================================================================
# CSV COLUMN MAPPINGS
# =============================================================================

# Standard Fidelity CSV column names (after skipping header rows)
FIDELITY_CSV_COLUMNS = {
    "run_date": "Run Date",
    "action": "Action",
    "symbol": "Symbol",
    "description": "Description",
    "type": "Type",
    "price": "Price ($)",
    "quantity": "Quantity",
    "commission": "Commission ($)",
    "fees": "Fees ($)",
    "accrued_interest": "Accrued Interest ($)",
    "amount": "Amount ($)",
    "cash_balance": "Cash Balance ($)",
    "settlement_date": "Settlement Date",
}

# Reversed for lookup
COLUMN_TO_FIELD = {v: k for k, v in FIDELITY_CSV_COLUMNS.items()}


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_transaction_type(action: str) -> TransactionType:
    """
    Map Fidelity action string to TransactionType.

    Args:
        action: The action field from Fidelity CSV

    Returns:
        Corresponding TransactionType enum value
    """
    action_upper = action.upper().strip()

    # Try exact match first
    if action_upper in FIDELITY_ACTION_MAPPINGS:
        return FIDELITY_ACTION_MAPPINGS[action_upper]

    # Try partial match patterns
    for pattern, tx_type in FIDELITY_ACTION_PATTERNS:
        if pattern in action_upper:
            return tx_type

    return TransactionType.OTHER


def extract_merchant(description: str) -> str | None:
    """
    Extract clean merchant name from Fidelity description.

    Args:
        description: The description field from Fidelity CSV

    Returns:
        Clean merchant name or None if not extractable
    """
    if not description:
        return None

    description = description.strip()

    for pattern, extractor in MERCHANT_PATTERNS:
        match = pattern.match(description)
        if match:
            if callable(extractor):
                return extractor(match)
            return extractor

    # Fallback: try to extract first meaningful part
    # Remove common suffixes like city/state codes
    parts = description.split()
    if parts:
        # Take first 2-3 meaningful words
        clean_parts = []
        for part in parts[:3]:
            # Stop at state codes or numbers
            if len(part) == 2 and part.isalpha():
                break
            if part.isdigit():
                break
            if "*" in part:
                part = part.replace("*", " ").strip()
            clean_parts.append(part)

        if clean_parts:
            return " ".join(clean_parts).title()

    return None


def categorize_expense(description: str, merchant: str | None = None) -> ExpenseCategory:
    """
    Categorize an expense based on description and merchant.

    Args:
        description: Original transaction description
        merchant: Extracted merchant name (optional)

    Returns:
        ExpenseCategory enum value
    """
    # Combine for matching
    search_text = description.lower()
    if merchant:
        search_text = f"{search_text} {merchant.lower()}"

    for category, keywords in CATEGORY_PATTERNS.items():
        for keyword in keywords:
            if keyword in search_text:
                return category

    return ExpenseCategory.UNCATEGORIZED


# Export all
__all__ = [
    "FIDELITY_ACTION_MAPPINGS",
    "FIDELITY_ACTION_PATTERNS",
    "MERCHANT_PATTERNS",
    "CATEGORY_PATTERNS",
    "FIDELITY_CSV_COLUMNS",
    "COLUMN_TO_FIELD",
    "get_transaction_type",
    "extract_merchant",
    "categorize_expense",
]
