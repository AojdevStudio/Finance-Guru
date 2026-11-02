import { describe, expect, test } from "bun:test";

import {
  toNumericString,
  type SfinAccount,
  type SfinAccountSet,
  type SfinAccountsQuery,
  type SfinTransaction,
} from "./types";
import {
  WINDOW_SECONDS,
  dateWindows,
  fetchAccountHistory,
  isRangeLimitMessage,
  mergeAccountSets,
} from "./windows";

function txn(
  id: string,
  extras: Partial<SfinTransaction> = {},
): SfinTransaction {
  return {
    id,
    posted: 1,
    amount: toNumericString("1.00"),
    description: id,
    ...extras,
  };
}

function account(
  id: string,
  txns: (string | SfinTransaction)[],
  extras: Partial<SfinAccount> = {},
): SfinAccount {
  return {
    id,
    name: id,
    currency: "USD",
    balance: toNumericString("1.00"),
    "balance-date": 1,
    org: { name: "Test" },
    transactions: txns.map((entry) =>
      typeof entry === "string" ? txn(entry) : entry,
    ),
    ...extras,
  };
}

function page(
  accounts: SfinAccount[],
  extras: Partial<SfinAccountSet> = {},
): SfinAccountSet {
  return { errors: [], accounts, ...extras };
}

describe("dateWindows", () => {
  test("returns one open window when the span is under 44 days", () => {
    const start = 1_000_000;
    const now = start + WINDOW_SECONDS - 1;
    expect(dateWindows(start, now)).toEqual([{ startDate: start }]);
  });

  test("splits a long span into exclusive 44-day windows plus an open tail", () => {
    const start = 1_700_000_000;
    const now = start + WINDOW_SECONDS * 2 + 10;
    expect(dateWindows(start, now)).toEqual([
      { startDate: start, endDate: start + WINDOW_SECONDS },
      { startDate: start + WINDOW_SECONDS, endDate: start + WINDOW_SECONDS * 2 },
      { startDate: start + WINDOW_SECONDS * 2 },
    ]);
  });
});

describe("mergeAccountSets", () => {
  test("unions transactions by account and keeps the latest balance", () => {
    const merged = mergeAccountSets([
      page([account("a", ["t1"], { balance: toNumericString("10.00") })]),
      page([account("a", ["t1", "t2"], { balance: toNumericString("20.00") })]),
    ]);
    expect(merged.accounts).toHaveLength(1);
    expect(merged.accounts[0]?.balance).toBe(toNumericString("20.00"));
    expect(merged.accounts[0]?.transactions?.map((txn) => txn.id)).toEqual([
      "t1",
      "t2",
    ]);
  });

  test("a posted copy replaces a pending copy of the same transaction, in either order", () => {
    const pending = txn("t1", { posted: 0, pending: true, amount: toNumericString("-5.00") });
    const posted = txn("t1", { posted: 1_700_000_500, amount: toNumericString("-5.25") });

    for (const windows of [[pending, posted], [posted, pending]]) {
      const merged = mergeAccountSets(
        windows.map((copy) => page([account("a", ["t0", copy, "t2"])])),
      );
      expect(merged.accounts[0]?.transactions).toEqual([
        txn("t0"),
        posted,
        txn("t2"),
      ]);
    }
  });

  test("drops Bridge range-cap warnings so the Python sync does not abort", () => {
    const merged = mergeAccountSets([
      page([], {
        errors: [
          "Requested date range exceeds limit of 90 days and was capped.",
          "real error",
        ],
        errlist: [
          {
            code: "gen.api",
            msg: "Requested date range exceeds recommended range of 45 days. In the future, this may be capped.",
          },
        ],
      }),
    ]);
    expect(merged.errors).toEqual(["real error"]);
    expect(merged.errlist).toEqual([]);
  });
});

describe("isRangeLimitMessage", () => {
  test("matches both Bridge wordings", () => {
    expect(
      isRangeLimitMessage(
        "Requested date range exceeds limit of 90 days and was capped.",
      ),
    ).toBe(true);
    expect(
      isRangeLimitMessage({
        code: "gen.api",
        msg: "Requested date range exceeds recommended range of 45 days. In the future, this may be capped.",
      }),
    ).toBe(true);
    expect(isRangeLimitMessage("Authentication failed")).toBe(false);
  });
});

describe("fetchAccountHistory", () => {
  test("pages the span and merges the results", async () => {
    const queries: SfinAccountsQuery[] = [];
    const start = 1_700_000_000;
    const now = start + WINDOW_SECONDS + 5;
    const client = {
      async fetchAccounts(query: SfinAccountsQuery = {}) {
        queries.push(query);
        const txnId = query.endDate === undefined ? "tail" : "head";
        return page([account("a", [txnId])]);
      },
    };

    const result = await fetchAccountHistory(
      client,
      { startDate: start, pending: true },
      now,
    );

    expect(queries).toEqual([
      {
        startDate: start,
        endDate: start + WINDOW_SECONDS,
        pending: true,
      },
      { startDate: start + WINDOW_SECONDS, pending: true },
    ]);
    expect(result.accounts[0]?.transactions?.map((txn) => txn.id)).toEqual([
      "head",
      "tail",
    ]);
  });
});
