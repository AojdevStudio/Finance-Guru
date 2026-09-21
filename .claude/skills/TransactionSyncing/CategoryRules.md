# CategoryRules - Expense Categorization Patterns

Pattern matching rules for auto-categorizing card and bank purchases.

> **Executable source of truth:** the rules live in code at
> `src/integrations/simplefin/categorize.py` (`categorize_expense`), which the
> SimpleFIN expense sync runs so every `bank_transactions` row arrives
> pre-categorized. This document mirrors that table and records the lessons
> behind its ordering. When you change a pattern, change the code and its test
> first, then this file.

## Two tables: public brands and household merchants

The public table in `categorize.py` holds **national brands and generic
wording only**. Anything that identifies a household (a local restaurant, the
daycare, the church, a lender, a county utility) is private data under
`DataClassification.md` and never goes in a tracked file.

Household merchants live in the instance directory as **`merchant-rules.yaml`**,
a mapping of category name to a list of lowercase substrings. The sync loads it
with `load_merchant_rules()` and appends each list to its category with
`merge_patterns()`, so household patterns extend a category but never create or
reorder one. A missing file is fine; a typo in a category name blocks the sync
with a typed error rather than silently dropping rules.

```yaml
# merchant-rules.yaml (instance directory, never committed to the engine)
Groceries:
  - corner market
Family Care:
  - little sprouts daycare
```

## How to add a pattern

1. Decide whether the merchant is a national brand (public table) or a
   household merchant (`merchant-rules.yaml`). When in doubt, it is household.
2. Copy the substring from the **raw bank memo**, not from SimpleFIN's cleaned
   payee. Memos are truncated and abbreviated; a pattern that only matches the
   payee form fails on the description alone.
3. Patterns are case-insensitive substrings. Anything shorter than about six
   characters, or a common English word, needs a collision check against the
   stored feed before it ships (see below).
4. For the public table, add a test in `tests/python/test_categorize.py` using
   a placeholder memo and a round amount.

## Matching algorithm

- Amounts under $1.00 and verification memos are `Exempt` before any pattern
  runs, as are SPAXX core sweeps and a `RETURNED PAYMENT FEE`.
- A retirement account returns `Retirement` for every row.
- Payroll wording, and checks on a business account, return `Payroll`.
- Then the table runs in order and **the first category with a hit wins**.
- An unmatched credit on a business account is `Business Income`.
- Everything else is `Uncategorized`.

The sync matches against **payee and description joined**. Matching only the
description missed every payee-shaped pattern and left most debit volume
uncategorized (2026-08-04).

## Non-spend and business categories

Categories that move money rather than consume it are excluded from spend
totals, otherwise a card purchase is counted twice: once on the card and again
when the bill is paid. Non-spend: `Credit Card Payment`, `Crypto Deposit`, `Exempt`, `Retirement`, `Transfer`.
Business (excluded from household reviews, included in business P&L):
`Business Expense`, `Business Income`, `Payroll`.

## Ordering rules

Order in the table is the whole precedence mechanism. The invariants it
encodes, each of which was a live bug once:

- `Transfer` and `Travel` come first so an explicit remittance is not read as a
  merchant and "American Express Travel" is Travel, not a card payment.
- `Dining Out` precedes `Auto & Transport` so `uber eats` beats `uber`.
- `Credit Card Payment` precedes `Bills & Utilities` so a card autopay memo is
  not read as a utility. **Every pattern in that category must be
  payment-specific**: a bare `credit card` once booked store purchases as bill
  payments, and a bare `automatic payment` would book any biller's autopay as
  non-spend.
- `Fees & Interest` precedes `Entertainment`, but position alone is not
  enough: an earlier category only wins if one of its patterns matches, so
  every returned-payment wording is listed in fees explicitly.
- `credit card payment` is deliberately absent from `Loan Payment`.

## Substring collisions

Patterns are plain substrings, so a short one fires inside unrelated words.
Three that misfiled real money: `spa` matched `SPAXX` (every core sweep became
Personal Care), `credit card` matched `<Merchant> Credit Card` payees, and
`uber` claimed `Uber Eats`. Fixes: `day spa` and `med spa` replace `spa`, a
SPAXX guard runs ahead of the table, and `GOOGLE  WORKSPACE` (doubled space)
and `LIVING SPACES` carry explicit patterns.

**Always replay the rules over the stored feed before and after a change.**
Removing a broad pattern is only safe once every merchant it carried has a
pattern of its own, and adding a generic word can silently reclassify history,
because the sync upserts the category on every row it touches.

## The card-payment credit leg

A bill payment posts twice: a debit on the funding account and a credit on the
card, worded `PAYMENT - THANK YOU` or truncated by the issuer to
`AUTOMATIC PAYMENT - THANK`. `thank you` and `payment - thank` sit in Credit
Card Payment so the credit leg does not inflate income figures summed from
credits. A bounced payment posts as a `Returned Payment` debit for the amount
it unwinds; it is the mirror of a non-spend event and nets in the same category,
while the issuer's separate `RETURNED PAYMENT FEE` is real spend.

## Deliberately left Uncategorized

`Paid Check` is ambiguous by nature: a written check can be groceries,
household, or shopping. `School` is the same case (a fee and a fundraiser land
in different buckets), and so is any Apple Pay passthrough where the memo
carries only the wallet prefix and a merchant the owner has not identified.
Guessing is worse than a visible gap. Review these by hand, then add the
merchant to `merchant-rules.yaml`.

## Public table

Generated from `CATEGORY_PATTERNS` in table order. Regenerate rather than edit
by hand.

### Transfer

`amex send`, `taptap send`, `cashed check`, `zelle`, `venmo`, `cash app`, `transferred to`, `transfer to`, `transfer withdrawal`, `transfer deposit`, `transfer from`, `instant transfer`, `webxtransfer`, `wire transfer`

### Travel

`american express travel`, `amex travel`, `delta`, `southwest air`, `united airlines`, `american airlines`, `airline`, `enterprise`, `hertz`, `avis`, `hotel`, `airbnb`, `expedia`, `marriott`, `hilton`

### Groceries

`h-e-b`, `heb`, `kroger`, `costco`, `wal-mart`, `walmart`, `wholefds`, `whole foods`, `sam's club`, `aldi`, `trader joe`

### Dining Out

`benihana`, `golden corral`, `papa john`, `chuck e cheese`, `wingstop`, `cinemark`, `mcdonald`, `chick-fil-a`, `chipotle`, `starbucks`, `coffee`, `restaurant`, `grill`, `cafe`, `uber eats`, `doordash`, `whataburger`, `panda express`, `burger king`, `auntie anne`, `thai`

### Credit Card Payment

`applecard`, `gsbapayment`, `chase payment`, `amex payment`, `discover payment`, `credit card payment`, `american express credit card`, `chase credit ca`, `wf credit card`, `apple credit card`, `amex epayment`, `chase credit card`, `thank you`

### Giving

`church`, `tithe`, `offering`, `ministry`, `missions`

### Auto & Transport

`tesla`, `supercha`, `vehicle registration`, `vehreg`, `dmv`, `parking`, `uber`, `lyft`, `shell`, `exxon`, `chevron`, `valero`, `gas station`, `toll`, `texaco`, `bp gas`, `car wash`, `safelite`, `auto glass`

### Personal Care

`salon`, `day spa`, `med spa`, `massage`, `barber`, `sephora`, `beauty supply`, `ulta`, `nail`, `hair`, `lash`, `wax`

### Health & Wellness

`cvs`, `pharmacy`, `walgreens`, `doctor`, `medical`, `dental`, `clinic`, `hospital`, `urgent care`

### Shopping

`marshalls`, `amazon`, `skims`, `tj maxx`, `ross`, `old navy`, `gap`, `nordstrom`, `macy`, `best buy`, `apple store`, `fashion nova`, `burlington`, `janie & jack`, `david yurman`, `dollar general`

### Family Care

`daycare`, `childcare`, `kid`, `children`, `pediatric`

### Bills & Utilities

`autopay`, `acctverify`, `electric`, `water`, `internet`, `comcast`, `att`, `verizon`, `t-mobile`, `netflix`, `spotify`, `subscription`, `prime video`

### Cash Withdrawal

`atm`, `cash withdrawal`, `cash advance`

### Tuition

`university`, `college`, `tuition`, `coursera`, `udemy`

### Business Expense

`gumroad`, `ups`, `fedex`, `office depot`, `staples`, `postal`, `usps`, `linkedin`, `zoom`, `openai`, `chatgpt`, `anthropic`, `claude.ai`, `cursor`, `github`, `vercel`, `greptile`, `openrouter`, `slack`, `paddle`, `ui.com`, `ubiquiti`, `newegg`, `workspace`

### Loan Payment

`loan payment`, `mortgage`, `mortg`, `mtgpmt`, `car payment`, `student loan`

### Fees & Interest

`interest charge`, `finance charge`, `annual fee`, `annual membership fee`, `membership fee`, `late fee`, `overdraft`, `service charge`, `maintenance fee`, `maintenance charge`, `sie fee`, `adj redist`, `bounced check`, `returned check`, `nsf fee`

### Entertainment

`playstation`, `bounce`, `gamestop`, `amc theat`, `ticketmaster`

### Home & Garden

`home depot`, `lowes`, `garden`, `hardware`, `furniture`, `living spaces`, `lawn`, `wayfair`

### Crypto Deposit

`btc deposited`, `bitcoin`, `fidelity crypto`, `eth deposited`, `crypto`
