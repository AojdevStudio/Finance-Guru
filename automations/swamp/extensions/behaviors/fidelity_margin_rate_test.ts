import { assertEquals, assertThrows } from "jsr:@std/assert@1.0.13";
import { configuredRate, marginAccountId, parseRateTable, tierRateFor, usableDebt } from "./fidelity_margin_rate.ts";

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

Deno.test("the stale 10.875% config differs from the tier rate", () => {
  const { tiers } = parseRateTable(html);
  const stale = configuredRate("FG_MARGIN_INTEREST_RATE=10.875%\nFG_MARGIN_INTEREST_RATE_DECIMAL=0.10875\n");
  assertEquals(Math.abs(tierRateFor(tiers, 75000) - stale) > 0.000001, true);
});

Deno.test("a changed page layout fails instead of returning no tiers", () => {
  assertThrows(() => parseRateTable("<html>redesigned</html>"), Error, "page layout changed");
});

const now = new Date("2026-10-26T14:15:00Z");

Deno.test("a fresh balances row gives its debt", () => {
  const row = { margin_debt: 75000, synced_at: "2026-10-26T14:10:00+00:00" };
  assertEquals(usableDebt(row, now, 36).debt, 75000);
});

Deno.test("a NULL debt from a stale-equity sync fails the run", () => {
  const row = { margin_debt: null, synced_at: "2026-10-26T14:10:00+00:00" };
  assertThrows(() => usableDebt(row, now, 36), Error, "equity was stale at sync");
});

Deno.test("a balances row older than the limit fails instead of picking a tier", () => {
  const row = { margin_debt: 150000, synced_at: "2026-10-22T12:47:09+00:00" };
  assertThrows(() => usableDebt(row, now, 36), Error, "older than 36 hours");
});

Deno.test("an empty ledger fails", () => {
  assertThrows(() => usableDebt(undefined, now, 36), Error, "No balances row");
});

Deno.test("a debit with cents at a tier's top stays in that tier", () => {
  const { tiers } = parseRateTable(html);
  assertEquals(tierRateFor(tiers, 99999.5), 0.10625);
  assertEquals(tierRateFor(tiers, 100000), 0.10575);
});

const routing = (accounts: string) => `generated_at: x\naccounts:\n${accounts}`;
const account = (id: string, role: string, enabled = true) =>
  `  - snaptrade_account_id: ${id}\n    role: ${role}\n    enabled: ${enabled}\n`;

Deno.test("the check reads the taxable_margin account, not another account", () => {
  const yaml = routing(account("ira-1", "retirement") + account("margin-1", "taxable_margin"));
  assertEquals(marginAccountId(yaml), "margin-1");
});

Deno.test("zero or two enabled margin accounts fail", () => {
  assertThrows(() => marginAccountId(routing(account("ira-1", "retirement"))), Error, "0 enabled");
  const two = routing(account("m-1", "taxable_margin") + account("m-2", "taxable_margin"));
  assertThrows(() => marginAccountId(two), Error, "2 enabled");
  assertEquals(marginAccountId(routing(account("m-1", "taxable_margin") + account("m-2", "taxable_margin", false))), "m-1");
});
