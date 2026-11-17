import { assertEquals, assertThrows } from "jsr:@std/assert@1.0.13";
import { parseResult, shouldAlert } from "./hedge_trigger.ts";

Deno.test("START and EXIT always alert, even when repeated", () => {
  assertEquals(shouldAlert("START", "START"), true);
  assertEquals(shouldAlert("EXIT", "EXIT"), true);
});

Deno.test("a repeated HOLD or NO_VERDICT stays quiet, a change alerts", () => {
  assertEquals(shouldAlert("HOLD", "HOLD"), false);
  assertEquals(shouldAlert("NO_VERDICT", "NO_VERDICT"), false);
  assertEquals(shouldAlert("HOLD", "START"), true);
  assertEquals(shouldAlert("NO_VERDICT", "HOLD"), true);
});

Deno.test("the first run alerts on anything but HOLD", () => {
  assertEquals(shouldAlert("HOLD", null), false);
  assertEquals(shouldAlert("NO_VERDICT", null), true);
});

Deno.test("engine output without an action is refused", () => {
  assertThrows(() => parseResult(JSON.stringify({ as_of: "2026-11-16", summary: "x" })), Error, "malformed");
});
