"""Categorize SimpleFIN transactions using ordered merchant patterns."""

CATEGORY_PATTERNS: dict[str, tuple[str, ...]] = {
    "Groceries": (
        "h-e-b",
        "heb",
        "kroger",
        "costco",
        "wal-mart",
        "walmart",
        "wholefds",
        "whole foods",
        "makola",
        "sam's club",
        "aldi",
        "trader joe",
    ),
    "Dining Out": (
        "benihana",
        "golden corral",
        "papa john",
        "chuck e cheese",
        "wingstop",
        "cinemark",
        "mcdonald",
        "chick-fil-a",
        "chipotle",
        "starbucks",
        "coffee",
        "restaurant",
        "grill",
        "cafe",
        "makiin",
        "sparkly photo",
    ),
    "Auto & Transport": (
        "tesla",
        "supercha",
        "parking",
        "fastpark",
        "uber",
        "lyft",
        "shell",
        "exxon",
        "chevron",
        "valero",
        "buc-ee",
        "gas station",
        "toll",
    ),
    "Personal Care": (
        "salon",
        "spa",
        "barber",
        "sephora",
        "beauty supply",
        "supreme beauty",
        "ulta",
        "nail",
        "hair",
        "shaving grace",
        "cash app",
    ),
    "Health & Wellness": (
        "cvs",
        "pharmacy",
        "walgreens",
        "life time",
        "doctor",
        "medical",
        "dental",
        "clinic",
        "hospital",
        "urgent care",
    ),
    "Shopping": (
        "marshalls",
        "amazon",
        "skims",
        "tj maxx",
        "ross",
        "old navy",
        "gap",
        "nordstrom",
        "macy",
        "best buy",
        "apple store",
    ),
    "Family Care": (
        "aqua tots",
        "brightwheel",
        "brghtwhl",
        "daycare",
        "childcare",
        "kid",
        "children",
        "pediatric",
    ),
    "Bills & Utilities": (
        "autopay",
        "acctverify",
        "electric",
        "water",
        "internet",
        "comcast",
        "att",
        "verizon",
        "t-mobile",
        "netflix",
        "spotify",
        "subscription",
    ),
    "Cash Withdrawal": ("atm", "cash withdrawal", "cash advance"),
    "Tuition": (
        "regent univer",
        "university",
        "college",
        "tuition",
        "coursera",
        "udemy",
    ),
    "Business Expense": (
        "gumroad",
        "ups",
        "fedex",
        "office depot",
        "staples",
        "postal",
        "usps",
        "linkedin",
        "zoom",
        "openai",
        "chatgpt",
    ),
    "Loan Payment": (
        "loan payment",
        "mortgage",
        "car payment",
        "student loan",
        "credit card payment",
    ),
    "Home & Garden": (
        "home depot",
        "lowes",
        "sawyer",
        "smart core",
        "garden",
        "hardware",
        "furniture",
    ),
    "Crypto Deposit": (
        "btc deposited",
        "bitcoin",
        "fidelity crypto",
        "eth deposited",
        "crypto",
    ),
    "Credit Card Payment": (
        "applecard",
        "gsbapayment",
        "chase payment",
        "amex payment",
        "discover payment",
    ),
}

# "target" and "school" are deliberately omitted because their categories are ambiguous.


def categorize_expense(text: str | None, amount: float | None = None) -> str:
    """Return the first matching expense category.

    Args:
        text: Transaction description or payee text.
        amount: Parsed transaction amount, when available.

    Returns:
        The matching category, ``Exempt``, or ``Uncategorized``.
    """
    if amount is not None and abs(amount) < 1.00:
        return "Exempt"

    normalized = (text or "").lower()
    if "ifacctverify" in normalized or "verification" in normalized:
        return "Exempt"

    for category, patterns in CATEGORY_PATTERNS.items():
        if any(pattern in normalized for pattern in patterns):
            return category
    return "Uncategorized"
