/**
 * Spec: https://www.simplefin.org/protocol.html
 *
 * Amounts are strings to preserve decimal precision — never coerce to
 * Number for math; use a decimal library if you need arithmetic.
 *
 * Timestamps are unix seconds (UTC), not milliseconds.
 */

declare const numericStringBrand: unique symbol;

/** A decimal string such as "-12.50", kept as text so no precision is lost. */
export type NumericString = string & { readonly [numericStringBrand]: true };

const NUMERIC_STRING = /^-?\d+(\.\d+)?$/;

export function toNumericString(value: string): NumericString {
  if (!NUMERIC_STRING.test(value)) {
    throw new Error(`Not a decimal string: ${JSON.stringify(value)}`);
  }
  return value as NumericString;
}

export interface SfinError {
  /** "prefix.subcode" — e.g. "gen.auth", "con.auth", "act.failed" */
  code?: string;
  msg?: string;
  /** Connection-level errors include this */
  conn_id?: string;
  /** Account-level errors include this */
  account_id?: string;
}

export interface SfinOrg {
  name: string;
  domain?: string;
  conn_id?: string;
  org_id?: string;
  sfin_url?: string;
  /** Institution domain (alias used by some bridges) */
  url?: string;
  /** Legacy field still emitted by some bridges */
  id?: string;
}

export interface SfinTransaction {
  /** Unique within account */
  id: string;
  /** Unix timestamp seconds; 0 if pending */
  posted: number;
  /** Positive = deposit/credit, negative = debit */
  amount: NumericString;
  description: string;
  payee?: string;
  memo?: string;
  /** When transaction actually occurred (vs when it posted) */
  transacted_at?: number;
  /** Default false; true for pending items */
  pending?: boolean;
  extra?: Record<string, unknown>;
}

export interface SfinAccount {
  id: string;
  name: string;
  /** ISO 4217 (e.g. "USD") OR an HTTPS URL for custom currencies */
  currency: string;
  balance: NumericString;
  /** Not all institutions provide this */
  "available-balance"?: NumericString;
  "balance-date": number;
  /** Connection ID linking account to org (some bridges) */
  conn_id?: string;
  org: SfinOrg;
  /** Optional — empty array when filtered out via `balances-only=1` */
  transactions?: SfinTransaction[];
  /** Investment positions when supported by the institution */
  holdings?: unknown[];
  extra?: Record<string, unknown>;
}

export interface SfinAccountSet {
  /** Always present; check even on HTTP 200 — partial failures are common */
  errors: (string | SfinError)[];
  /** Older spec name for the same partial-failure list — defensive */
  errlist?: (string | SfinError)[];
  accounts: SfinAccount[];
  /** Some bridges include this; not guaranteed */
  connections?: SfinOrg[];
}

export interface SfinAccountsQuery {
  /** Unix timestamp; transactions on/after this date (inclusive) */
  startDate?: number;
  /** Unix timestamp; transactions before this date (exclusive) */
  endDate?: number;
  pending?: boolean;
  /** Filter to specific account IDs (repeatable param under the hood) */
  accountIds?: string[];
  balancesOnly?: boolean;
}
