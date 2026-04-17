#!/usr/bin/env bun
/**
 * Smoke-test the SimpleFIN connection.
 *
 * Pulls all accounts plus the last 30 days of transactions (including
 * pending), then prints a one-line summary per account with the three
 * most recent transactions. Surfaces partial-failure errors that
 * SimpleFIN returns alongside HTTP 200 in `errors[]`.
 */
import { createClient, toSfinTimestamp } from "./client";

const accessUrl = process.env.SIMPLEFIN_ACCESS_URL?.trim();
if (!accessUrl) {
  console.error("✗ SIMPLEFIN_ACCESS_URL is empty. Run `bun run claim` first.");
  process.exit(1);
}

const client = createClient(accessUrl);
const startDate = toSfinTimestamp(
  new Date(Date.now() - 30 * 24 * 60 * 60 * 1000),
);

const data = await client.fetchAccounts({ startDate, pending: true });

const reportedErrors = [...(data.errors ?? []), ...(data.errlist ?? [])];
if (reportedErrors.length) {
  console.warn("⚠ SimpleFIN reported errors (partial failure):");
  for (const e of reportedErrors) {
    const msg = typeof e === "string" ? e : (e.msg ?? JSON.stringify(e));
    // Strip control chars before printing — error text is server-supplied.
    console.warn(`   ${msg.replace(/[\x00-\x1f\x7f]/g, "")}`);
  }
  console.warn();
}

console.log(`✓ ${data.accounts.length} account(s) retrieved\n`);

let totalTxns = 0;
for (const acct of data.accounts) {
  const isCurrencyCode = /^[A-Z]{3}$/.test(acct.currency);
  const balanceLine = isCurrencyCode
    ? Number(acct.balance).toLocaleString("en-US", {
        style: "currency",
        currency: acct.currency,
      })
    : `${acct.balance} ${acct.currency}`;

  console.log(`━━━ ${acct.org?.name ?? "(unknown org)"} · ${acct.name} ━━━`);
  console.log(`  Balance:      ${balanceLine}`);
  if (acct["available-balance"] !== undefined) {
    console.log(`  Available:    ${acct["available-balance"]}`);
  }
  const txns = acct.transactions ?? [];
  console.log(`  Transactions: ${txns.length}`);
  totalTxns += txns.length;

  const recent = [...txns]
    .sort((a, b) => b.posted - a.posted)
    .slice(0, 3);
  for (const t of recent) {
    const dateStr = t.posted
      ? new Date(t.posted * 1000).toISOString().slice(0, 10)
      : "PENDING   ";
    const amt = isCurrencyCode
      ? Number(t.amount).toLocaleString("en-US", {
          style: "currency",
          currency: acct.currency,
        })
      : t.amount;
    const desc = (t.payee || t.description || "").slice(0, 60);
    console.log(`    ${dateStr}  ${amt.padStart(12)}  ${desc}`);
  }
  console.log();
}

console.log("━".repeat(65));
console.log(`Total: ${data.accounts.length} accounts · ${totalTxns} txns`);
