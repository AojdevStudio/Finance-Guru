import { assertEquals, assertThrows } from "jsr:@std/assert@1.0.13";
import { parseRateTable, readMetrics, tierRateFor } from "./fidelity_margin_rate.ts";

const html = Deno.readTextFileSync(new URL("./testdata/fidelity-rates-2026-10-22.html", import.meta.url));

Deno.test("parses Fidelity's tier table and base rate", () => {
  const table = parseRateTable(html);
  assertEquals(table.tiers.length, 5);
  assertEquals(table.baseRate, 0.10825);
  assertEquals(table.baseEffective, "September 18, 2026");
});

Deno.test("a debit picks its own tier: $75,000 is 10.625%, $150,000 is 10.575%", () => {
  const { tiers } = parseRateTable(html);
  assertEquals(tierRateFor(tiers, 75000), 0.10625);
  assertEquals(tierRateFor(tiers, 150000), 0.10575);
});

Deno.test("a debit with cents at a tier's top stays in that tier", () => {
  const { tiers } = parseRateTable(html);
  assertEquals(tierRateFor(tiers, 99999.5), 0.10625);
  assertEquals(tierRateFor(tiers, 100000), 0.10575);
});

Deno.test("a stale 10.875% configured rate differs from the tier rate", () => {
  const { tiers } = parseRateTable(html);
  assertEquals(Math.abs(tierRateFor(tiers, 75000) - 0.10875) > 0.000001, true);
});

Deno.test("a changed page layout fails instead of returning no tiers", () => {
  assertThrows(() => parseRateTable("<html>redesigned</html>"), Error, "page layout changed");
});

const now = new Date("2026-10-26T14:20:00Z");
const metrics = (syncedAt: string) =>
  JSON.stringify({ margin_balance: 75000, annual_interest_rate: 0.10625, as_of_date: "2026-10-26", ledger_synced_at: syncedAt });

Deno.test("a ledger synced minutes ago gives the engine's debt and configured rate", () => {
  const m = readMetrics(metrics("2026-10-26T14:18:00+00:00"), now, 24);
  assertEquals([m.margin_balance, m.annual_interest_rate], [75000, 0.10625]);
});

Deno.test("an old ledger fails even though as_of_date is today", () => {
  assertThrows(() => readMetrics(metrics("2001-01-01T14:00:00+00:00"), now, 24), Error, "Run the refresh method first");
});

Deno.test("engine output without ledger_synced_at fails", () => {
  assertThrows(
    () => readMetrics(JSON.stringify({ margin_balance: 75000, annual_interest_rate: 0.10625 }), now, 24),
    Error,
    "missing margin_balance",
  );
});
