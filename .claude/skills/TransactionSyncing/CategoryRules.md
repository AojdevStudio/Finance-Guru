# CategoryRules - Expense Categorization Patterns

Pattern matching rules for auto-categorizing card and bank purchases.

> **Executable source of truth:** these rules are implemented in code at
> `src/integrations/simplefin/categorize.py` (`categorize_expense(text, amount)`),
> which the SimpleFIN expense sync runs so every `bank_transactions` row arrives
> pre-categorized. This document is the human-readable mirror. When you add or
> change a pattern here, update `categorize.py` (and its test) to match.

## How to Add New Patterns

To add a new categorization rule:

1. Identify the merchant name pattern from Fidelity descriptions
2. Add to the appropriate category section below
3. Patterns are **case-insensitive**
4. Use partial matches (e.g., "h-e-b" matches "H-E-B #063 Pearland TX")

---

## Category Patterns

### Groceries
Supermarkets, grocery stores, food supplies

**Patterns**:
- `h-e-b`, `heb`
- `kroger`
- `costco`
- `wal-mart`, `walmart`
- `wholefds`, `whole foods`
- `makola`
- `target` (when food context)
- `sam's club`
- `aldi`
- `trader joe`

**Examples**:
- "H-E-B #063 Pearland TX" -> Groceries
- "COSTCO WHSE #1 PEARLAND TX" -> Groceries
- "MAKOLA IMPORTS HOUSTON TX" -> Groceries

---

### Dining Out
Restaurants, fast food, entertainment dining

**Patterns**:
- `benihana`
- `golden corral`
- `papa john`
- `chuck e cheese`
- `wingstop`
- `cinemark`
- `mcdonald`
- `chick-fil-a`
- `chipotle`
- `starbucks`
- `coffee`
- `restaurant`
- `grill`
- `cafe`
- `makiin`
- `sparkly photo` (event dining)

**Examples**:
- "BENIHANA SUGAR LAND" -> Dining Out
- "TST*MAKIIN Houston TX" -> Dining Out
- "PAPA JOHN'S #2 PEARLAND TX" -> Dining Out

---

### Auto & Transport
Vehicle expenses, fuel, parking, transportation

**Patterns**:
- `tesla`
- `supercha` (Tesla Supercharger)
- `parking`
- `fastpark`
- `uber`
- `lyft`
- `shell`
- `exxon`
- `chevron`
- `valero`
- `buc-ee`
- `gas station`
- `toll`

**Examples**:
- "Tesla, Inc. SUPERCHA600118984238637" -> Auto & Transport
- "FASTPARKHOU HOUSTON TX" -> Auto & Transport
- "Tesla Property Casual Fremont CA" -> Auto & Transport

---

### Personal Care
Grooming, beauty, self-care

**Patterns**:
- `salon`
- `spa`
- `barber`
- `sephora`
- `beauty supply`
- `supreme beauty`
- `ulta`
- `nail`
- `hair`
- `shaving grace`
- `gloss* skin`
- `cash app*` (often personal transfers)

**Examples**:
- "K STAR SALON & SPA MANVEL TX" -> Personal Care
- "A SHAVING GRACE BARBER PEARLAND TX" -> Personal Care
- "SEPHORA PEACHT PEACHTREE CI GA" -> Personal Care

---

### Health & Wellness
Medical, pharmacy, fitness

**Patterns**:
- `cvs`
- `pharmacy`
- `walgreens`
- `life time` (gym)
- `doctor`
- `medical`
- `dental`
- `clinic`
- `hospital`
- `urgent care`

**Examples**:
- "CVS/PHARMACY # MANVEL TX" -> Health & Wellness
- "LIFE TIME #320" -> Health & Wellness

---

### Shopping
Retail, clothing, general merchandise

**Patterns**:
- `marshalls`
- `target` (non-food)
- `amazon`
- `skims`
- `tj maxx`
- `ross`
- `old navy`
- `gap`
- `nordstrom`
- `macy`
- `best buy`
- `apple store`

**Examples**:
- "MARSHALLS #877 PEARLAND TX" -> Shopping
- "SP SKIMS CHECKOUT.SKIM CA" -> Shopping

---

### Family Care
Childcare, family activities, kids

**Patterns**:
- `aqua tots`
- `brightwheel`, `brghtwhl`
- `daycare`
- `childcare`
- `school`
- `kid`
- `children`
- `pediatric`

**Examples**:
- "AQUA TOTS - PEARLAND" -> Family Care
- "BRGHTWHL R* REDEEMER" -> Family Care

---

### Bills & Utilities
Recurring bills, subscriptions, utilities

**Patterns**:
- `autopay`
- `acctverify`
- `electric`
- `water`
- `internet`
- `comcast`
- `att`
- `verizon`
- `t-mobile`
- `netflix`
- `spotify`
- `subscription`

**Examples**:
- "BMO ACCTVERIFY" -> Bills & Utilities

---

### Cash Withdrawal
ATM and cash transactions

**Patterns**:
- `atm`
- `cash withdrawal`
- `cash advance`

**Examples**:
- "ATM0043 11555 MAGNOLIA PEARLAND TX" -> Cash Withdrawal
- "ATMXD10 *SEDONA LAKES MANVEL TX" -> Cash Withdrawal

---

### Tuition
Education expenses

**Patterns**:
- `regent univer`
- `university`
- `college`
- `tuition`
- `school`
- `education`
- `coursera`
- `udemy`

**Examples**:
- "REGENT UNIVERSPURCHASE" -> Tuition

---

### Business Expense
Work-related purchases

**Patterns**:
- `gumroad`
- `ups`
- `fedex`
- `office depot`
- `staples`
- `postal`
- `usps`
- `business`
- `linkedin`
- `zoom`

**Examples**:
- "GUMROAD* SHAWN GRADY" -> Business Expense
- "POSTAL COPY CENTER-931 PEARLAND TX" -> Business Expense

---

### Loan Payment
Debt payments

**Patterns**:
- `wells fargo` + `draft` or `audraft`
- `loan payment`
- `mortgage`
- `car payment`
- `student loan`

**Examples**:
- "WELLS FARGO AUDRAFT" -> Loan Payment

---

### Home & Garden
Home improvement, garden, maintenance

**Patterns**:
- `home depot`
- `lowes`
- `sawyer`
- `smart core`
- `garden`
- `hardware`
- `furniture`

**Examples**:
- "SAWYER + S* SMART CORE" -> Home & Garden

---

### Crypto Deposit
Cryptocurrency deposits and transfers

**Patterns**:
- `btc deposited`
- `bitcoin`
- `fidelity crypto`
- `eth deposited`
- `crypto`

**Examples**:
- "0.17713256 BTC deposited" -> Crypto Deposit
- "Fidelity Crypto® 8449251033" -> Crypto Deposit

---

### Credit Card Payment
Credit card bill payments

**Patterns**:
- `applecard`
- `gsbapayment`
- `chase payment`
- `amex payment`
- `discover payment`

**Examples**:
- "DIRECT DEBIT APPLECARD GSBAPAYMENT" -> Credit Card Payment

---

### Exempt
Verification transactions, zero amounts

**Patterns**:
- `ifacctverify`
- `verification`
- Amount = $0.00 or < $1.00

**Examples**:
- "WELLS FARGO IFACCTVERIFY" -> Exempt

---

## Uncategorized

Any transaction not matching the above patterns is marked as **"Uncategorized"** and flagged for manual review in the sync summary.

**Common uncategorized reasons**:
- New merchant not in patterns
- Unusual description format
- One-time or rare purchase

**To resolve**: Add the pattern to the appropriate category above.

---

## Pattern Matching Algorithm

```python
def categorize_expense(description: str) -> str:
    desc = description.lower()

    # Check each category's patterns
    for category, patterns in CATEGORY_PATTERNS.items():
        for pattern in patterns:
            if pattern in desc:
                return category

    return "Uncategorized"

CATEGORY_PATTERNS = {
    "Groceries": ["h-e-b", "heb", "kroger", "costco", "wal-mart", "walmart", ...],
    "Dining Out": ["benihana", "golden corral", "papa john", ...],
    "Auto & Transport": ["tesla", "supercha", "parking", "fastpark", ...],
    # ... etc
}
```

---

## Extending Categories

When the user wants to add new categories or patterns:

1. **Add to existing category**: Update the patterns list above
2. **Create new category**: Add a new section with patterns and examples
3. **Expense Tracker sync**: Ensure the category name matches Budget Planner

**Budget Planner categories** (must match exactly):
- Groceries
- Dining Out
- Auto & Transport
- Personal Care
- Health & Wellness
- Shopping
- Family Care
- Bills & Utilities
- Cash Withdrawal
- Tuition
- Business Expense
- Loan Payment
- Home & Garden
- Crypto Deposit
- Credit Card Payment
- Exempt
- Software & Tech
- Cell Phone
- Gas
- Water
- Light Bill
- Mortgage

---

**Last Updated**: 2026-08-31
**Maintainer**: Finance Guru TransactionSyncing skill

---

## Ordering rules (2026-08-04)

`CATEGORY_PATTERNS` is an ordered dict and **the first match wins**, so placement
is behavior, not style. Three orderings are load-bearing:

1. **Travel before Credit Card Payment** so "American Express Travel" is a trip,
   not a card payment.
2. **Credit Card Payment before Bills & Utilities.** A card autopay memo reads
   "Chase Credit Cautopay", which contains the substring `autopay`. With Bills &
   Utilities first, every card payment was mis-filed as a utility bill.
3. **`credit card payment` belongs to Credit Card Payment, not Loan Payment.**
   It used to sit in Loan Payment, which is matched earlier, so card payments
   never reached their own category.

## Match against payee AND description

The sync joins both fields before categorizing. `description` is the raw bank
memo (`DIRECT DEBIT AMEX EPAYMENT ACH PMT`); `payee` is SimpleFIN's normalized
merchant name (`American Express Credit Card`). Matching description alone left
67% of debit volume Uncategorized. **When adding a pattern, cover the
abbreviated memo form too**, for example `vehreg` alongside
`vehicle registration`, and `amex epayment` alongside `amex payment`.

## Non-spend categories

`NON_SPEND_CATEGORIES` in `categorize.py` holds `Transfer`,
`Credit Card Payment`, `Crypto Deposit`, `Exempt`, and `Retirement`. These move money rather
than consume it and **must be excluded from spend totals**. Including them
double-counts: once when a purchase hits the card, again when the card bill is
paid. On 2026-08-04 that inflated a 30-day review roughly 3x.

## Categories added 2026-08-04

### Giving
Church and ministry contributions.

**Patterns**: `anglicanchurch`, `church`, `tithe`, `offering`, `ministry`, `missions`

### Fees & Interest
Card interest and bank charges, kept out of merchant spend.

**Patterns**: `interest charge`, `finance charge`, `annual fee`, `late fee`, `overdraft`, `service charge`, `maintenance fee`

### Additions to existing categories

- **Transfer**: `transferred to`, `transfer to`, `transfer withdrawal`, `webxtransfer`, `wire transfer`
- **Credit Card Payment**: `credit card payment`, `american express credit card`, `chase credit ca`, `wf credit card`, `apple credit card`, `amex epayment`, `credit card`
- **Loan Payment**: `mortg`, `mtgpmt`, `aes stdnt` (bank memos abbreviate)
- **Auto & Transport**: `vehicle registration`, `vehreg`, `dmv`
- **Business Expense**: `anthropic`, `claude.ai`, `cursor`, `github`, `vercel`

## Deliberately left Uncategorized

`Paid Check` and `Target` are ambiguous by nature: a written check or a Target
run can be groceries, household, or shopping. Guessing is worse than a visible
gap. Review these by hand.
