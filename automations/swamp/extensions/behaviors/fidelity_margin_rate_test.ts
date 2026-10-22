import { assertEquals, assertRejects, assertThrows } from "jsr:@std/assert@1.0.13";
import { behavior, parseRateTable, readMetrics, tierRateFor } from "./fidelity_margin_rate.ts";

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

Deno.test("a rate page that stalls mid-body fails the check at the timeout and writes nothing", async () => {
  // The engine process: it reports a fresh ledger, so only the page can fail.
  const engineOut = new TextEncoder().encode(JSON.stringify({
    margin_balance: 75000,
    annual_interest_rate: 0.10625,
    ledger_synced_at: new Date().toISOString(),
  }));
  const realCommand = Deno.Command;
  Deno.Command = class extends realCommand {
    override output() {
      return Promise.resolve({ success: true, code: 0, signal: null, stdout: engineOut, stderr: new Uint8Array() });
    }
  };

  // The clock: the test fires the timeout instead of waiting for it.
  const timeouts: number[] = [];
  const clock = new AbortController();
  // The network: headers arrive, the body never does, and the request's signal
  // errors the body the way a real fetch does.
  let fetched!: () => void;
  const fetchCalled = new Promise<void>((r) => fetched = r);
  const realFetch = globalThis.fetch;
  const realTimeout = AbortSignal.timeout;
  AbortSignal.timeout = (ms: number) => {
    timeouts.push(ms);
    return clock.signal;
  };
  globalThis.fetch = (_input: RequestInfo | URL, init?: RequestInit) => {
    const signal = init?.signal;
    fetched();
    return Promise.resolve(
      new Response(new ReadableStream({ start: (c) => signal?.addEventListener("abort", () => c.error(signal.reason)) })),
    );
  };
  const writes: string[] = [];
  try {
    const run = behavior.methods.check.execute({ maxLedgerAgeHours: 24 }, {
      repoDir: "/swamp",
      globalArgs: { instanceDir: "/instance", uvPath: "uv" },
      writeResource: (spec) => {
        writes.push(spec);
        return Promise.resolve({ name: spec });
      },
      logger: { info: () => {} },
    });
    await fetchCalled;
    clock.abort(new DOMException("The operation was aborted due to timeout", "TimeoutError"));
    await assertRejects(() => run, DOMException, "due to timeout");
    assertEquals(timeouts, [30_000]);
    assertEquals(writes, []);
  } finally {
    globalThis.fetch = realFetch;
    AbortSignal.timeout = realTimeout;
    Deno.Command = realCommand;
  }
});
