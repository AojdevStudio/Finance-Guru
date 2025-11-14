

## Step-by-Step: How to Use This Sheet

### Make a Copy

1. Go to **File > Make a Copy** to save your own editable version.
2. In the **Portfolio Tab**, only edit:

   * Ticket
   * Cost Basis
   * Shares Owned
   * Manual Boost
   * Maintenance
3. Enter the ticket symbols (include any ticket that you don’t own but want to add to your portfolio), cost basis, shares owned, and maintenance requirement from your broker.
4. Click the **History and Dividend Button**.

   * **Do this once every day** you are using the spreadsheet.
   * The first time you click, it will ask for permissions since it will run a script (found under **Extensions > Apps Script**).
5. Visit CLM and CRF websites for Premium/Discount and NAV.
6. The **VIX index** and market trend are for reference only — not used in calculations.
7. **Equity %** is only for record-keeping and has no role in calculations.

---

### Deposit Optimizer

1. In the **Portfolio tab**, cell **B1** → Enter your deposit amount.
2. In cell **C1** → Select **CORE** or **SCORE**.

   * **Core mode:** Boosts core tickets (default CLM, CRF, GOF) regardless of score.
   * **Score mode:** Based on calculated score (input core tickets on **Weights Tab**, cell **B13** — symbols in all caps, comma-separated).
3. Click the **Optimizer** button.
4. After running, **blue cells** in column **F** show the recommended stocks to buy.
5. **Cell F1** shows the estimated **monthly income** with the suggested stocks.

---

### ROI %

* Calculates **Return On Investment** when adding back the dividends received.
* On the **Dividends tab**, enter:

  * Ticker symbol
  * Dividend amount
  * Date received
* Adjusts cost basis with the dividend received.

---

## Customizing Your Strategy

The **Weights Tab** controls score parameters and displays scoring breakdowns. Premade values exist in columns **O–S**.

| Parameter              | Description                                                                             |
| ---------------------- | --------------------------------------------------------------------------------------- |
| `costBase`             | “Value buy” flag; slightly increases weight for underperforming (paper loss) positions. |
| `yieldBoost`           | Rewards high dividend-yield names.                                                      |
| `exBoost`              | Rewards stocks near ex-dividend date.                                                   |
| `costBoost`            | Compares yield to price; rewards cheaper-looking tickets.                               |
| `manualBoost`          | Manual override knob (adjust in **Portfolio tab**, column N).                           |
| `modeBoost`            | In CORE mode, boosts core tickers.                                                      |
| `maintBoost`           | Boosts low-maintenance, penalizes 100% maintenance.                                     |
| `diversificationBoost` | Rewards positions <10% of total portfolio.                                              |
| `heavyPenalty`         | Penalizes holdings over the heavy threshold.                                            |
| `HeavyThreshold`       | Defines % of portfolio before penalties apply.                                          |
| `CAP_PCT`              | Deposit cap: never exceed set % of deposit or total portfolio.                          |
| `CORE_TICKERS`         | Defines your main positions (default CLM, CRF, GOF).                                    |
| `YIELD_THRESHOLDS`     | Defines breakpoints for `yieldBoost`.                                                   |
| `YIELD_VALUES`         | Assigns scores to yield thresholds.                                                     |
| `momentum`             | Boosts recent uptrends; small negatives favor mean reversion.                           |
| `volatility`           | Penalizes high volatility; small negatives for smoother returns.                        |
| `sharpeYield`          | “Dividend Sharpe”: rewards high yield with low volatility.                              |

**Tip:**
Use `0` to ignore, positive for boost, negative for penalty.

---

## HedgeAnalysis Tab

* Configure settings in **G1–H4**.
* **Downside Weight** sets portfolio drop tolerance (1 = full coverage, 0.5 = half coverage).
* Click **Analyze** and follow prompts to optimize hedging.

---

## Budget Planner Tab

Tracks which expenses are covered by dividends or margin income.

* **Cell H2:** Select pay frequency (weekly/biweekly).
* **Cell B4:** Sums dividends received for selected month (**H1**) minus expenses marked in column **F**.
* **Column F:** Tracks expenses covered by dividends (green = next covered expense).
* **Column A:** Expense categories (must match **Expense Tracker tab**).
* Add margin interest as an expense.
* **Cell H4:** Shows how much to deposit to cover uncovered expenses.
* **Cell I2:** Shows monthly amount to pay with debit card.

---

## Expense Tracker Tab

A transaction log feeding the **Budget Planner**.
Use the same category names as in Budget Planner.

---

## Dividends Tab

Maintains a record of dividends received.

* After inputting dividend data (columns A–D), click **Add Dividend** to move it to the tracking table.
* The **Portfolio Tab** uses this data for ROI calculations.
* **DRIP** entries (checked in column D) are excluded from ROI since already reflected in cost basis.
* The **Budget Planner** automatically sums all dividends.

---

## FIRE Model Tab

To activate:

1. Ensure **Budget Tab** has all expenses with checkmarks in column I and **Auto Pay** selected.
2. Margin interest entered (Portfolio Tab cell **G25**).
3. Dividends Tab completed with **DRIP** marked.
4. Click **Analyze** (cell **N1**).

---

## Option Tracker Tab

Tracks **Option ROI** impact on portfolio ROI.

---

**Disclaimer:**

> Quotes may be delayed up to 20 minutes. Information is for educational purposes only — not financial advice or trading recommendations.

---

Would you like me to convert this into a **GitHub-ready README.md** layout (with code fences, headings, and internal links between tabs)?
