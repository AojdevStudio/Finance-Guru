import type { SimpleFinClient } from "./client";
import type {
  SfinAccount,
  SfinAccountSet,
  SfinAccountsQuery,
  SfinError,
} from "./types";

/** Bridge warns at 45 days and hard-caps a single request at 90. Stay under the warning. */
export const WINDOW_SECONDS = 44 * 24 * 60 * 60;

export type DateWindow = {
  startDate: number;
  endDate?: number;
};

export function dateWindows(startDate: number, now: number): DateWindow[] {
  if (now <= startDate) {
    return [{ startDate }];
  }
  const windows: DateWindow[] = [];
  let cursor = startDate;
  while (cursor + WINDOW_SECONDS < now) {
    const endDate = cursor + WINDOW_SECONDS;
    windows.push({ startDate: cursor, endDate });
    cursor = endDate;
  }
  windows.push({ startDate: cursor });
  return windows;
}

export function isRangeLimitMessage(error: string | SfinError): boolean {
  const message = typeof error === "string" ? error : (error.msg ?? "");
  return /date range exceeds (limit|recommended range)/i.test(message);
}

function mergeErrors(
  pages: SfinAccountSet[],
  key: "errors" | "errlist",
): (string | SfinError)[] {
  const merged: (string | SfinError)[] = [];
  for (const page of pages) {
    for (const error of page[key] ?? []) {
      if (!isRangeLimitMessage(error)) {
        merged.push(error);
      }
    }
  }
  return merged;
}

export function mergeAccountSets(pages: SfinAccountSet[]): SfinAccountSet {
  const accounts = new Map<string, SfinAccount>();
  for (const page of pages) {
    for (const account of page.accounts ?? []) {
      const previous = accounts.get(account.id);
      if (!previous) {
        accounts.set(account.id, {
          ...account,
          transactions: [...(account.transactions ?? [])],
        });
        continue;
      }
      const seen = new Set((previous.transactions ?? []).map((txn) => txn.id));
      const extra = (account.transactions ?? []).filter(
        (txn) => !seen.has(txn.id),
      );
      accounts.set(account.id, {
        ...account,
        transactions: [...(previous.transactions ?? []), ...extra],
      });
    }
  }
  const lastWithConnections = [...pages]
    .reverse()
    .find((page) => page.connections !== undefined);
  return {
    errors: mergeErrors(pages, "errors"),
    errlist: mergeErrors(pages, "errlist"),
    accounts: [...accounts.values()],
    ...(lastWithConnections?.connections !== undefined
      ? { connections: lastWithConnections.connections }
      : {}),
  };
}

export async function fetchAccountHistory(
  client: Pick<SimpleFinClient, "fetchAccounts">,
  query: Pick<SfinAccountsQuery, "startDate" | "pending">,
  now: number,
  onWindow?: (index: number, total: number, window: DateWindow) => void,
): Promise<SfinAccountSet> {
  if (query.startDate === undefined) {
    throw new Error("startDate is required to page SimpleFIN history");
  }
  const windows = dateWindows(query.startDate, now);
  const pages: SfinAccountSet[] = [];
  for (const [index, window] of windows.entries()) {
    onWindow?.(index, windows.length, window);
    const pageQuery: SfinAccountsQuery = {
      startDate: window.startDate,
      pending: query.pending,
    };
    if (window.endDate !== undefined) {
      pageQuery.endDate = window.endDate;
    }
    pages.push(await client.fetchAccounts(pageQuery));
  }
  return mergeAccountSets(pages);
}
