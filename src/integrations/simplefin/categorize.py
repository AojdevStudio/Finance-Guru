"""Categorize SimpleFIN transactions using ordered merchant patterns.

The table in this module holds only national brands and generic wording. A
household's own merchants (the local dry cleaner, the daycare, the church) are
private data and live in the instance directory as ``merchant-rules.yaml``,
loaded at sync time by :func:`load_merchant_rules` and appended to the public
table by :func:`merge_patterns`.
"""

import os
from collections.abc import Callable, Hashable
from dataclasses import dataclass
from pathlib import Path

import yaml

PatternTable = tuple[tuple[str, tuple[str, ...]], ...]
"""Categories with their lowercase substrings. The first matching category wins."""

CATEGORY_PATTERNS: PatternTable = (
    (
        "Transfer",
        (
            "amex send",
            "taptap send",
            "cashed check",
            "zelle",
            "venmo",
            "cash app",
            "transferred to",
            "transfer to",
            "transfer withdrawal",
            "transfer deposit",
            "transfer from",
            "instant transfer",
            "webxtransfer",
            "wire transfer",
        ),
    ),
    (
        "Travel",
        (
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
    ),
    (
        "Groceries",
        (
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
    ),
    (
        "Dining Out",
        (
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
            "uber eats",
            "doordash",
            "whataburger",
            "panda express",
            "burger king",
            "auntie anne",
            "thai",
        ),
    ),
    (
        "Credit Card Payment",
        (
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
            "amex epayment",
            "chase credit card",
            "payment - thank you",
            "payment thank you",
            "thank you for your payment",
        ),
    ),
    (
        "Giving",
        (
            "church",
            "tithe",
            "offering",
            "ministry",
            "missions",
        ),
    ),
    (
        "Auto & Transport",
        (
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
    ),
    (
        "Personal Care",
        (
            "salon",
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
    ),
    (
        "Health & Wellness",
        (
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
    ),
    (
        "Shopping",
        (
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
    ),
    (
        "Family Care",
        (
            "daycare",
            "childcare",
            "kid",
            "children",
            "pediatric",
        ),
    ),
    (
        "Bills & Utilities",
        (
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
    ),
    ("Cash Withdrawal", ("atm", "cash withdrawal", "cash advance")),
    (
        "Tuition",
        (
            "university",
            "college",
            "tuition",
            "coursera",
            "udemy",
        ),
    ),
    (
        "Business Expense",
        (
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
            "workspace",
        ),
    ),
    (
        "Loan Payment",
        (
            "loan payment",
            "mortgage",
            "mortg",
            "mtgpmt",
            "car payment",
            "student loan",
        ),
    ),
    (
        "Fees & Interest",
        (
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
            "adj redist",
            "bounced check",
            "returned check",
            "nsf fee",
        ),
    ),
    (
        "Entertainment",
        (
            "playstation",
            "bounce",
            "gamestop",
            "amc theat",
            "ticketmaster",
        ),
    ),
    (
        "Home & Garden",
        (
            "home depot",
            "lowes",
            "garden",
            "hardware",
            "furniture",
            "living spaces",
            "lawn",
            "wayfair",
        ),
    ),
    (
        "Crypto Deposit",
        (
            "btc deposited",
            "bitcoin",
            "fidelity crypto",
            "eth deposited",
            "crypto",
        ),
    ),
)

CATEGORIES: tuple[str, ...] = tuple(category for category, _ in CATEGORY_PATTERNS)

HouseholdRules = dict[str, tuple[str, ...]]


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


def load_merchant_rules(path: Path) -> HouseholdRules:
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
    rules: HouseholdRules = {}
    for category, patterns in loaded.items():
        if category not in CATEGORIES:
            raise MerchantRulesError(
                f"{path}: unknown category {category!r}; "
                f"choose one of {', '.join(CATEGORIES)}"
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


def merge_patterns(base: PatternTable, extra: HouseholdRules) -> PatternTable:
    """Append household patterns to each category of the public table.

    Category order, and so match precedence, comes from ``base``. Household
    patterns only extend a category; they never create or reorder one.
    """
    return tuple(
        (category, patterns + extra.get(category, ())) for category, patterns in base
    )


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

BUSINESS_ACCOUNT_HINTS: tuple[str, ...] = (
    "business",
    "llc",
)

_BUSINESS_HINT_ENV = "FG_BUSINESS_ACCOUNT_HINTS"


def _extra_business_hints() -> tuple[str, ...]:
    """Return operator-supplied business-account hints from the environment."""
    raw = os.environ.get(_BUSINESS_HINT_ENV, "")
    return tuple(hint.strip().lower() for hint in raw.split(",") if hint.strip())


RETIREMENT_ACCOUNT_HINTS: tuple[str, ...] = ("401(k)", "401k", "retirement")

_CHECK_PATTERNS: tuple[str, ...] = ("paid check", "cashed check", "check paid")

_PAYROLL_PATTERNS: tuple[str, ...] = (
    "payroll",
    "gusto",
    "adp ",
    "paychex",
    "direct deposit to employee",
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


@dataclass(frozen=True)
class _Transaction:
    text: str
    amount: float | None
    account_name: str | None


_EXEMPT_BELOW_AMOUNT = 1.00


def _is_sub_dollar(txn: _Transaction) -> bool:
    return txn.amount is not None and abs(txn.amount) < _EXEMPT_BELOW_AMOUNT


def _is_account_verification(txn: _Transaction) -> bool:
    return "ifacctverify" in txn.text or "verification" in txn.text


def _is_core_cash_sweep(txn: _Transaction) -> bool:
    return "spaxx" in txn.text or "core account" in txn.text


def _is_retirement(txn: _Transaction) -> bool:
    return is_retirement_account(txn.account_name)


def _is_payroll_memo(txn: _Transaction) -> bool:
    return any(pattern in txn.text for pattern in _PAYROLL_PATTERNS)


def _is_business_check(txn: _Transaction) -> bool:
    return is_business_account(txn.account_name) and any(
        pattern in txn.text for pattern in _CHECK_PATTERNS
    )


def _is_business_inflow(txn: _Transaction) -> bool:
    return (
        txn.amount is not None
        and txn.amount > 0
        and is_business_account(txn.account_name)
    )


_Rule = tuple[str, Callable[[_Transaction], bool]]

_RULES_BEFORE_TABLE: tuple[_Rule, ...] = (
    ("Exempt", _is_sub_dollar),
    ("Exempt", _is_account_verification),
    ("Exempt", _is_core_cash_sweep),
    ("Retirement", _is_retirement),
    ("Payroll", _is_payroll_memo),
    ("Payroll", _is_business_check),
)

_RULES_AFTER_TABLE: tuple[_Rule, ...] = (("Business Income", _is_business_inflow),)


def categorize_expense(
    text: str | None,
    amount: float | None = None,
    account_name: str | None = None,
    patterns: PatternTable | None = None,
) -> str:
    """Return the first matching expense category.

    Rules run in order: ``_RULES_BEFORE_TABLE``, then the pattern table, then
    ``_RULES_AFTER_TABLE``.

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
    txn = _Transaction((text or "").lower(), amount, account_name)

    for category, applies in _RULES_BEFORE_TABLE:
        if applies(txn):
            return category

    table = CATEGORY_PATTERNS if patterns is None else patterns
    for category, category_patterns in table:
        if any(pattern in txn.text for pattern in category_patterns):
            return category

    for category, applies in _RULES_AFTER_TABLE:
        if applies(txn):
            return category

    return "Uncategorized"
