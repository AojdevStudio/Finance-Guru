import { describe, expect, test } from "bun:test";

import type { SfinAccount, SfinAccountSet, SfinAccountsQuery } from "./types";
import {
  WINDOW_SECONDS,
  dateWindows,
  fetchAccountHistory,
  isRangeLimitMessage,
  mergeAccountSets,
} from "./windows";

function account(
  id: string,
  txnIds: string[],
  extras: Partial<SfinAccount> = {},
): SfinAccount {
  return {
    id,
    name: id,
    currency: "USD",
    balance: "1.00",
    "balance-date": 1,
    org: { name: "Test" },
    transactions: txnIds.map((txnId) => ({
      id: txnId,
      posted: 1,
      amount: "1.00",
      description: txnId,
    })),
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
      page([account("a", ["t1"], { balance: "10.00" })]),
      page([account("a", ["t1", "t2"], { balance: "20.00" })]),
    ]);
    expect(merged.accounts).toHaveLength(1);
    expect(merged.accounts[0]?.balance).toBe("20.00");
    expect(merged.accounts[0]?.transactions?.map((txn) => txn.id)).toEqual([
      "t1",
      "t2",
    ]);
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
