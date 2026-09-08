"""Categorize SimpleFIN transactions using ordered merchant patterns."""

import os

# Order matters: the first matching category wins. Transfer and Travel come
# first so an explicit remittance is not read as a merchant, and so
# "American Express Travel" lands in Travel rather than Credit Card Payment.
CATEGORY_PATTERNS: dict[str, tuple[str, ...]] = {
    "Transfer": (
        "taptap send",
        "amex send",
        "cashed check",
        "zelle",
        "venmo",
        "cash app",
        # Moving money between own accounts is not spending. Keeping these out of
        # Uncategorized stops them inflating the expense review.
        "transferred to",
        "transfer to",
        "transfer withdrawal",
        "transfer deposit",
        "transfer from",
        # "Instant Transfer Received From ....0000" does not contain "transfer from".
        "instant transfer",
        "webxtransfer",
        "wire transfer",
        # Inbound movement between the owner's own Capital One accounts.
        "capital one bank",
    ),
    "Travel": (
        "american express travel",
        "amex travel",
        "delta",
        "southwest air",
        "united airlines",
        "american airlines",
        "airline",
        "enterprise",
        "hertz",
        "avis",
        "hotel",
        "airbnb",
        "expedia",
        "marriott",
        "hilton",
    ),
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
        # Precedes Dining Out so the butcher does not match "halal guys".
        "halal meat",
        "southwest farmers",
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
        # Must precede Auto & Transport, whose "uber" pattern would otherwise
        # book a food delivery as a rideshare.
        "uber eats",
        "doordash",
        "whataburger",
        "panda express",
        "burger king",
        "auntie anne",
        "pick up stix",
        "chicken salad chick",
        "piada",
        "nishiki",
        "gringos",
        "rouxpour",
        "halal guys",
        "broken egg",
        "thai",
    ),
    # Must precede Bills & Utilities: a card autopay string such as
    # "Chase Credit Cautopay" contains "autopay" and would otherwise be read as a
    # utility bill. Must follow Travel so "American Express Travel" stays Travel.
    "Credit Card Payment": (
        "applecard",
        "gsbapayment",
        "chase payment",
        "amex payment",
        "discover payment",
        "credit card payment",
        "american express credit card",
        "chase credit ca",
        "wf credit card",
        "apple credit card",
        "amex epayment",  # raw bank memo form: "DIRECT DEBIT AMEX EPAYMENT ACH PMT"
        "chase credit card",
        # The card-side leg of a bill payment, posted as a credit on the card.
        # Without it the payment lands in Uncategorized and inflates income.
        "thank you",
        # A bare "credit card" pattern used to live here. It matched SimpleFIN
        # payee normalizations of the form "<Merchant> Credit Card", which
        # booked a store purchase as a bill payment and dropped it from spend
        # totals as non-spend. Keep every pattern here payment-specific.
    ),
    "Giving": (
        "anglicanchurch",
        "church",
        "tithe",
        "offering",
        "ministry",
        "missions",
    ),
    "Auto & Transport": (
        "tesla",
        "supercha",
        "vehicle registration",
        "vehreg",
        "dmv",
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
        "texaco",
        "bp gas",
        "car wash",
        "parkify",
        "safelite",
        "auto glass",
    ),
    "Personal Care": (
        "salon",
        # A bare "spa" pattern used to live here. It matched Fidelity's core
        # money market, SPAXX, and booked every cash sweep as a spa visit.
        "day spa",
        "med spa",
        "massage",
        "barber",
        "sephora",
        "beauty supply",
        "supreme beauty",
        "ulta",
        "nail",
        "hair",
        "shaving grace",
        "cash app",
        "clean skin",
        "cloud 9 spa",
        "lash",
        "wax",
        "face reality",
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
        "mychart",
        # Giving matches "church" first, so a Methodist congregation still
        # lands in Giving and only the outpatient centers arrive here.
        "methodist",
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
        "shopwss",
        "fashion nova",
        "burlington",
        "uptown cheapskate",
        "janie & jack",
        "david yurman",
        "dollar general",
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
        "rhythm ops",
        "total wireless",
        "tidal",
        "prime video",
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
        "anthropic",
        "claude.ai",
        "cursor",
        "github",
        "vercel",
        "greptile",
        "openrouter",
        "slack",
        "paddle",
        # Homelab and fabrication hardware. Classified as business input by the
        # account owner 2026-09-08, alongside the existing developer tooling.
        "ui.com",
        "ubiquiti",
        "newegg",
        "bambula",
        "connectech",
        "pga frisco",
        # "GOOGLE  WORKSPACE" contains "spa" and was landing in Personal Care.
        # Matched on the bare word: the bank memo doubles the space after GOOGLE.
        "workspace",
    ),
    # "credit card payment" deliberately NOT listed here: it belongs to the
    # dedicated Credit Card Payment category below. Leaving it in Loan Payment
    # (which is matched first) sent card payments to the wrong bucket.
    "Loan Payment": (
        "loan payment",
        "mortgage",
        "mortg",  # Fidelity/Truist abbreviate: "TRUIST MORTG TEL MTGPMT"
        "mtgpmt",
        "car payment",
        "student loan",
        "aes stdnt",
    ),
    "Fees & Interest": (
        "interest charge",
        "finance charge",
        "annual fee",
        "annual membership fee",
        "membership fee",
        "late fee",
        "overdraft",
        "service charge",
        "maintenance fee",
        "maintenance charge",
        "sie fee",
        # Card issuer moving a balance between purchase and cash-advance buckets.
        "adj redist",
    ),
    # Deliberately after Fees & Interest: "bounce" would otherwise capture a
    # bounced-check fee before the fee patterns get a chance.
    "Entertainment": (
        "playstation",
        "andretti",
        "bounce",
        "gamestop",
        "amc theat",
        "ticketmaster",
    ),
    "Home & Garden": (
        "home depot",
        "lowes",
        "sawyer",
        "smart core",
        "garden",
        "hardware",
        "furniture",
        "bermuda dude",
        # "LIVING SPACES" contains "spa" and was landing in Personal Care.
        "living spaces",
        "lawn",
        "wayfair",
        "flower shop",
    ),
    "Crypto Deposit": (
        "btc deposited",
        "bitcoin",
        "fidelity crypto",
        "eth deposited",
        "crypto",
    ),
}

# Categories that move money rather than consume it. Expense reviews should
# exclude these from spend totals, otherwise a card purchase is counted twice:
# once on the card account and again when the card bill is paid.
NON_SPEND_CATEGORIES: frozenset[str] = frozenset(
    {"Transfer", "Credit Card Payment", "Crypto Deposit", "Exempt", "Retirement"}
)

# Categories belonging to a business entity rather than the household.
# Personal-spending reviews exclude these; business P&L includes them.
BUSINESS_CATEGORIES: frozenset[str] = frozenset(
    {"Payroll", "Business Expense", "Business Income"}
)

# Substrings identifying a business bank account by name. A written check means
# different things by account: employee payroll on a business account, unknown
# personal spending on a household one. Text alone cannot tell them apart.
# Only generic, non-identifying substrings live here. Entity names are private
# data, so extra hints are supplied at runtime via FG_BUSINESS_ACCOUNT_HINTS
# (comma-separated) rather than committed to the repo.
BUSINESS_ACCOUNT_HINTS: tuple[str, ...] = (
    "business",
    "llc",
)

_BUSINESS_HINT_ENV = "FG_BUSINESS_ACCOUNT_HINTS"


def _extra_business_hints() -> tuple[str, ...]:
    """Return operator-supplied business-account hints from the environment."""
    raw = os.environ.get(_BUSINESS_HINT_ENV, "")
    return tuple(hint.strip().lower() for hint in raw.split(",") if hint.strip())


# Substrings identifying a retirement account by name. Contributions and
# in-plan dividends are savings, not household consumption, and the account name
# is the only reliable signal: the feed's bare "contribution" memo is too generic
# to match on, since a charitable contribution is real spending.
RETIREMENT_ACCOUNT_HINTS: tuple[str, ...] = ("401(k)", "401k", "retirement")

# Check-writing patterns. Only classified as Payroll on a business account.
_CHECK_PATTERNS: tuple[str, ...] = ("paid check", "cashed check", "check paid")

_PAYROLL_PATTERNS: tuple[str, ...] = (
    "payroll",
    "gusto",
    "adp ",
    "paychex",
    "direct deposit to employee",
    # Employers vary the memo suffix ("...PAYROLL", "...DIR DEP", "...ACH"), so
    # matching the suffix misses payers. An inbound direct deposit is income by
    # definition; sub-dollar bank verification deposits are already returned
    # Exempt by the amount rule above, before this table is reached.
    "direct deposit",
)


def is_business_account(account_name: str | None) -> bool:
    """Return True when the account belongs to a business entity.

    Matches the generic hints plus any supplied via ``FG_BUSINESS_ACCOUNT_HINTS``.
    """
    normalized = (account_name or "").lower()
    hints = BUSINESS_ACCOUNT_HINTS + _extra_business_hints()
    return any(hint in normalized for hint in hints)


def is_retirement_account(account_name: str | None) -> bool:
    """Return True when the account is a retirement plan."""
    normalized = (account_name or "").lower()
    return any(hint in normalized for hint in RETIREMENT_ACCOUNT_HINTS)


# "target" and "school" are deliberately omitted because their categories are ambiguous.


def categorize_expense(
    text: str | None,
    amount: float | None = None,
    account_name: str | None = None,
) -> str:
    """Return the first matching expense category.

    Args:
        text: Transaction payee and description text, joined.
        amount: Parsed transaction amount, when available.
        account_name: Owning account name. Required to distinguish business
            payroll from personal spending, because identical memo text
            ("Paid Check") means different things by account.

    Returns:
        The matching category, ``Exempt``, or ``Uncategorized``.
    """
    if amount is not None and abs(amount) < 1.00:
        return "Exempt"

    normalized = (text or "").lower()
    if "ifacctverify" in normalized or "verification" in normalized:
        return "Exempt"

    # Fidelity's core position is the SPAXX money market, and sweeps into and
    # out of it are the settlement mechanism rather than income or spending.
    # Checked ahead of the table because "SPAXX" contains "spa".
    if "spaxx" in normalized or "core account" in normalized:
        return "Exempt"

    # Everything on a retirement account is savings or in-plan activity, never
    # household consumption, so the account decides before any text pattern runs.
    if is_retirement_account(account_name):
        return "Retirement"

    # Account-aware rules run before the text table: a check drawn on a business
    # account is employee payroll, which the generic patterns would read as a
    # Transfer and silently drop from the business P&L.
    if any(pattern in normalized for pattern in _PAYROLL_PATTERNS):
        return "Payroll"
    if is_business_account(account_name) and any(
        pattern in normalized for pattern in _CHECK_PATTERNS
    ):
        return "Payroll"

    for category, patterns in CATEGORY_PATTERNS.items():
        if any(pattern in normalized for pattern in patterns):
            return category

    # Unmatched money arriving in a business account is revenue. Running this
    # after the table lets an explicit Transfer pattern claim an inter-account
    # move first, and keeps client names out of the repository: the account,
    # not the payer's name, is what identifies the income.
    if amount is not None and amount > 0 and is_business_account(account_name):
        return "Business Income"

    return "Uncategorized"
