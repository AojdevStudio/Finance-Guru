"""Categorize SimpleFIN transactions using ordered merchant patterns.

The table in this module holds only national brands and generic wording. A
household's own merchants (the local dry cleaner, the daycare, the church) are
private data and live in the instance directory as ``merchant-rules.yaml``,
loaded at sync time by :func:`load_merchant_rules` and appended to the public
table by :func:`merge_patterns`.
"""

import os
from collections.abc import Hashable, Mapping
from pathlib import Path

import yaml

# Order matters: the first matching category wins. Transfer and Travel come
# first so an explicit remittance is not read as a merchant, and so
# "American Express Travel" lands in Travel rather than Credit Card Payment.
CATEGORY_PATTERNS: dict[str, tuple[str, ...]] = {
    "Transfer": (
        "amex send",
        "taptap send",
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
        # Must precede Auto & Transport, whose "uber" pattern would otherwise
        # book a food delivery as a rideshare.
        "uber eats",
        "doordash",
        "whataburger",
        "panda express",
        "burger king",
        "auntie anne",
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
        # Card-side payment credits often read "PAYMENT - THANK YOU". Match only
        # payment-shaped thank-you strings: a bare "thank you" also appears in
        # merchant memos such as "THANK YOU FOR SHOPPING", which would drop a
        # real purchase debit from spend via NON_SPEND_CATEGORIES.
        "payment - thank you",
        "payment thank you",
        "thank you for your payment",
        # A bare "credit card" pattern used to live here. It matched SimpleFIN
        # payee normalizations of the form "<Merchant> Credit Card", which
        # booked a store purchase as a bill payment and dropped it from spend
        # totals as non-spend. Keep every pattern here payment-specific.
    ),
    "Giving": (
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
        "uber",
        "lyft",
        "shell",
        "exxon",
        "chevron",
        "valero",
        "gas station",
        "toll",
        "texaco",
        "bp gas",
        "car wash",
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
        "ulta",
        "nail",
        "hair",
        "lash",
        "wax",
    ),
    "Health & Wellness": (
        "cvs",
        "pharmacy",
        "walgreens",
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
        "fashion nova",
        "burlington",
        "janie & jack",
        "david yurman",
        "dollar general",
    ),
    "Family Care": (
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
        "prime video",
    ),
    "Cash Withdrawal": ("atm", "cash withdrawal", "cash advance"),
    "Tuition": (
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
        "ui.com",
        "ubiquiti",
        "newegg",
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
        "mortg",  # bank memos abbreviate: "ANYBANK MORTG TEL MTGPMT"
        "mtgpmt",
        "car payment",
        "student loan",
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
        # A returned-payment fee carries no other fee word, so ordering alone
        # does not keep it out of Entertainment's "bounce" pattern.
        "bounced check",
        "returned check",
        "nsf fee",
    ),
    # Deliberately after Fees & Interest, though position alone is not enough:
    # the fee patterns only win if one of them actually matches, so every
    # returned-payment wording is listed there explicitly.
    "Entertainment": (
        "playstation",
        "bounce",
        "gamestop",
        "amc theat",
        "ticketmaster",
    ),
    "Home & Garden": (
        "home depot",
        "lowes",
        "garden",
        "hardware",
        "furniture",
        # "LIVING SPACES" contains "spa" and was landing in Personal Care.
        "living spaces",
        "lawn",
        "wayfair",
    ),
    "Crypto Deposit": (
        "btc deposited",
        "bitcoin",
        "fidelity crypto",
        "eth deposited",
        "crypto",
    ),
}

PatternTable = dict[str, tuple[str, ...]]


class MerchantRulesError(ValueError):
    """The instance merchant-rules file is malformed."""


class _UniqueKeyLoader(yaml.SafeLoader):
    """SafeLoader that rejects a repeated mapping key.

    Plain ``safe_load`` keeps only the last value for a repeated key, so a
    second ``Groceries:`` block would silently drop the first one's patterns.
    """

    def construct_mapping(
        self, node: yaml.MappingNode, deep: bool = False
    ) -> dict[object, object]:
        seen: set[object] = set()
        for key_node, _ in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, Hashable):
                raise yaml.constructor.ConstructorError(
                    None, None, "found unhashable key", key_node.start_mark
                )
            if key in seen:
                raise yaml.constructor.ConstructorError(
                    None, None, f"duplicate key {key!r}", key_node.start_mark
                )
            seen.add(key)
        return super().construct_mapping(node, deep=deep)


def load_merchant_rules(path: Path) -> PatternTable:
    """Read household merchant patterns from the instance.

    The file maps a category name to a list of lowercase substrings, for
    example ``Family Care: [little sprouts daycare]``. A missing file means
    the household has no private rules yet and is not an error.

    Raises:
        MerchantRulesError: On a category the public table does not define, a
            category listed twice, or a value that is not a list of strings,
            so a typo blocks the sync instead of silently dropping rules.
    """
    if not path.is_file():
        return {}
    try:
        text = path.read_text(encoding="utf-8")
        loaded = yaml.load(text, Loader=_UniqueKeyLoader)
    except yaml.YAMLError as exc:
        raise MerchantRulesError(f"{path} is not valid YAML: {exc}") from exc
    if loaded is None:
        return {}
    if not isinstance(loaded, dict):
        raise MerchantRulesError(f"{path} must be a mapping of category to patterns")
    rules: PatternTable = {}
    for category, patterns in loaded.items():
        if category not in CATEGORY_PATTERNS:
            raise MerchantRulesError(
                f"{path}: unknown category {category!r}; "
                f"choose one of {', '.join(CATEGORY_PATTERNS)}"
            )
        if patterns is None:
            continue
        if not isinstance(patterns, list) or not all(
            isinstance(item, str) and item.strip() for item in patterns
        ):
            raise MerchantRulesError(
                f"{path}: {category!r} must be a list of non-empty strings"
            )
        rules[category] = tuple(item.strip().lower() for item in patterns)
    return rules


def merge_patterns(
    base: Mapping[str, tuple[str, ...]], extra: Mapping[str, tuple[str, ...]]
) -> PatternTable:
    """Append household patterns to each category of the public table.

    Category order, and so match precedence, comes from ``base``. Household
    patterns only extend a category; they never create or reorder one.
    """
    return {
        category: patterns + tuple(extra.get(category, ()))
        for category, patterns in base.items()
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
    patterns: Mapping[str, tuple[str, ...]] | None = None,
) -> str:
    """Return the first matching expense category.

    Args:
        text: Transaction payee and description text, joined.
        amount: Parsed transaction amount, when available.
        account_name: Owning account name. Required to distinguish business
            payroll from personal spending, because identical memo text
            ("Paid Check") means different things by account.
        patterns: Pattern table to match against. Defaults to the public
            table; the sync passes the public table merged with the
            household's ``merchant-rules.yaml``.

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

    table = CATEGORY_PATTERNS if patterns is None else patterns
    for category, category_patterns in table.items():
        if any(pattern in normalized for pattern in category_patterns):
            return category

    # Unmatched money arriving in a business account is revenue. Running this
    # after the table lets an explicit Transfer pattern claim an inter-account
    # move first, and keeps client names out of the repository: the account,
    # not the payer's name, is what identifies the income.
    if amount is not None and amount > 0 and is_business_account(account_name):
        return "Business Income"

    return "Uncategorized"
