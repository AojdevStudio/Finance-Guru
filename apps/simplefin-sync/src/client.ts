/**
 * The access URL embeds basic-auth credentials in userinfo
 * (https://USER:PASS@host/path). Bun's fetch (like browsers) strips
 * userinfo from request URLs for security, so we extract credentials
 * once and send them as a Basic auth header on every request.
 */
import type { SfinAccountSet, SfinAccountsQuery } from "./types";

export interface SimpleFinClient {
  baseUrl: string;
  fetchAccounts(query?: SfinAccountsQuery): Promise<SfinAccountSet>;
}

declare const secretBrand: unique symbol;

/** An Authorization header value that carries the access URL's credentials. */
export type BasicAuthHeader = string & { readonly [secretBrand]: true };

interface ParsedAccessUrl {
  baseUrl: string;
  authHeader: BasicAuthHeader;
}

function basicAuthHeader(username: string, password: string): BasicAuthHeader {
  const encoded = Buffer.from(`${username}:${password}`).toString("base64");
  return `Basic ${encoded}` as BasicAuthHeader;
}

export function parseAccessUrl(accessUrl: string): ParsedAccessUrl {
  let url: URL;
  try {
    url = new URL(accessUrl);
  } catch {
    throw new Error("SIMPLEFIN_ACCESS_URL is not a valid URL");
  }
  if (url.protocol !== "https:") {
    throw new Error(`Access URL must use HTTPS, got ${url.protocol}`);
  }
  if (!url.username || !url.password) {
    throw new Error("Access URL missing user:password userinfo");
  }
  return {
    baseUrl: `${url.origin}${url.pathname.replace(/\/$/, "")}`,
    authHeader: basicAuthHeader(
      decodeURIComponent(url.username),
      decodeURIComponent(url.password),
    ),
  };
}

export function createClient(accessUrl: string): SimpleFinClient {
  const { baseUrl, authHeader } = parseAccessUrl(accessUrl);

  return {
    baseUrl,
    async fetchAccounts(query = {}) {
      const params = new URLSearchParams();
      if (query.startDate !== undefined)
        params.set("start-date", String(query.startDate));
      if (query.endDate !== undefined)
        params.set("end-date", String(query.endDate));
      if (query.pending) params.set("pending", "1");
      if (query.balancesOnly) params.set("balances-only", "1");
      for (const id of query.accountIds ?? []) params.append("account", id);

      const qs = params.toString();
      const url = qs ? `${baseUrl}/accounts?${qs}` : `${baseUrl}/accounts`;

      const res = await fetch(url, {
        headers: { Authorization: authHeader },
      });

      if (res.status === 402) {
        throw new SimpleFinError(402, "Subscription expired or payment required");
      }
      if (res.status === 403) {
        throw new SimpleFinError(403, "Authentication failed — access URL invalid");
      }
      if (!res.ok) {
        const body = await res.text();
        throw new SimpleFinError(res.status, body);
      }

      return (await res.json()) as SfinAccountSet;
    },
  };
}

export class SimpleFinError extends Error {
  constructor(
    readonly status: number,
    body: string,
  ) {
    super(`SimpleFIN HTTP ${status}: ${body}`);
    this.name = "SimpleFinError";
  }
}

export function toSfinTimestamp(date: Date): number {
  return Math.floor(date.valueOf() / 1000);
}
