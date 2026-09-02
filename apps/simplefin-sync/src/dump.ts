#!/usr/bin/env bun
/**
 * Dump raw SimpleFIN /accounts JSON (incl. transactions) to stdout for the
 * Python spending sync to consume. Reuses the proven client/auth path.
 *
 *   bun run src/dump.ts [months=12] > out.json
 */
import { createClient, toSfinTimestamp } from "./client";

const MAX_MONTHS = 120;
const accessUrl = process.env.SIMPLEFIN_ACCESS_URL?.trim();
if (!accessUrl) {
  console.error("✗ SIMPLEFIN_ACCESS_URL is empty. Run `bun run claim` first.");
  process.exit(1);
}

const monthsArgument = process.argv[2] ?? "12";
const months = Number(monthsArgument);
if (!Number.isInteger(months) || months < 1 || months > MAX_MONTHS) {
  console.error(
    `✗ months must be a whole number between 1 and ${MAX_MONTHS}, got "${monthsArgument}"`,
  );
  process.exit(1);
}
const startDate = toSfinTimestamp(
  new Date(Date.now() - months * 31 * 24 * 60 * 60 * 1000),
);

// Defense-in-depth: never let a credential-bearing string reach stderr/logs.
function scrub(message: string): string {
  let s = message.replace(
    /https?:\/\/[^@\s/]+:[^@\s/]+@/g,
    "https://[redacted]@",
  );
  if (accessUrl) s = s.split(accessUrl).join("[redacted]");
  return s;
}

try {
  const client = createClient(accessUrl);
  const data = await client.fetchAccounts({ startDate, pending: true });
  process.stdout.write(JSON.stringify(data));
} catch (err) {
  const message = err instanceof Error ? err.message : "unknown error";
  console.error(`✗ SimpleFIN dump failed: ${scrub(message)}`);
  process.exit(1);
}
