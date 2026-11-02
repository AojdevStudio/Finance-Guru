#!/usr/bin/env bun
import { createClient, toSfinTimestamp } from "./client";
import { fetchAccountHistory } from "./windows";

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
const now = Math.floor(Date.now() / 1000);
const startDate = toSfinTimestamp(
  new Date((now - months * 31 * 24 * 60 * 60) * 1000),
);

function redactCredentials(message: string): string {
  let s = message.replace(
    /https?:\/\/[^@\s/]+:[^@\s/]+@/g,
    "https://[redacted]@",
  );
  if (accessUrl) s = s.split(accessUrl).join("[redacted]");
  return s;
}

try {
  const client = createClient(accessUrl);
  const data = await fetchAccountHistory(
    client,
    { startDate, pending: true },
    now,
    (index, total, window) => {
      const from = new Date(window.startDate * 1000).toISOString().slice(0, 10);
      const to = window.endDate
        ? new Date(window.endDate * 1000).toISOString().slice(0, 10)
        : "now";
      console.error(`SimpleFIN dump window ${index + 1}/${total} ${from}..${to}`);
    },
  );
  process.stdout.write(JSON.stringify(data));
} catch (err) {
  const message = err instanceof Error ? err.message : "unknown error";
  console.error(`✗ SimpleFIN dump failed: ${redactCredentials(message)}`);
  process.exit(1);
}
