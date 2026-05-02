#!/usr/bin/env bun
import { createClient, toSfinTimestamp } from "./client";

const accessUrl = process.env.SIMPLEFIN_ACCESS_URL?.trim();
if (!accessUrl) {
  console.error("✗ SIMPLEFIN_ACCESS_URL is empty.");
  process.exit(1);
}

const client = createClient(accessUrl);
const startDate = toSfinTimestamp(
  new Date(Date.now() - 90 * 24 * 60 * 60 * 1000),
);

const data = await client.fetchAccounts({ startDate, pending: true });
const outPath = process.argv[2] ?? "/tmp/simplefin-90d.json";
await Bun.write(outPath, JSON.stringify(data, null, 2));
console.log(`wrote ${outPath} · ${data.accounts.length} accounts · ${data.accounts.reduce((s, a) => s + (a.transactions?.length ?? 0), 0)} txns`);
