#!/usr/bin/env bun
/**
 * Setup tokens are SINGLE-USE: a successful claim destroys the token.
 * If POST returns 403 the token has either already been claimed or is
 * invalid — the protocol spec recommends treating that as a possible
 * compromise and disabling the token in your bridge dashboard.
 *
 * Spec: https://www.simplefin.org/protocol.html#claiming-the-access-url
 */
import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { persistAccessUrl } from "./env-file";

const ENV_PATH = resolve(import.meta.dir, "../.env");

const setupToken = process.env.SIMPLEFIN_SETUP_TOKEN?.trim();
if (!setupToken) {
  console.error("✗ SIMPLEFIN_SETUP_TOKEN is empty in .env");
  process.exit(1);
}

if (process.env.SIMPLEFIN_ACCESS_URL?.trim()) {
  console.error("✗ SIMPLEFIN_ACCESS_URL already populated. Refusing to overwrite.");
  console.error("  Clear it manually in .env if you intend to re-claim.");
  process.exit(1);
}

const claimUrl = Buffer.from(setupToken, "base64").toString("utf-8").trim();
let claimOrigin: string;
try {
  const parsed = new URL(claimUrl);
  if (parsed.protocol !== "https:") {
    console.error(`✗ Decoded setup token uses non-HTTPS scheme: ${parsed.protocol}`);
    process.exit(1);
  }
  claimOrigin = parsed.origin;
} catch {
  console.error("✗ Decoded setup token is not a valid URL");
  process.exit(1);
}

console.log(`→ Claiming setup token at: ${claimOrigin}`);

// Per spec, POST with empty body and explicit Content-Length: 0
const res = await fetch(claimUrl, {
  method: "POST",
  headers: { "Content-Length": "0" },
});

if (res.status === 403) {
  console.error("✗ HTTP 403 — token already claimed or invalid");
  console.error("  Generate a fresh setup token in the SimpleFIN dashboard.");
  process.exit(1);
}
if (!res.ok) {
  console.error(`✗ Claim failed: HTTP ${res.status}`);
  console.error(await res.text());
  process.exit(1);
}

const accessUrl = (await res.text()).trim();
try {
  const parsed = new URL(accessUrl);
  if (parsed.protocol !== "https:") {
    throw new Error(`non-HTTPS scheme: ${parsed.protocol}`);
  }
  if (!parsed.username || !parsed.password) {
    throw new Error("missing user:password userinfo");
  }
} catch (err) {
  console.error("✗ Response doesn't look like a valid access URL:", err);
  process.exit(1);
}

let updated: string;
try {
  updated = persistAccessUrl(readFileSync(ENV_PATH, "utf-8"), accessUrl);
} catch (err) {
  console.error(`✗ ${err instanceof Error ? err.message : String(err)}`);
  console.error("  Recover the access URL manually:");
  console.error(`  ${accessUrl}`);
  process.exit(1);
}
writeFileSync(ENV_PATH, updated);

const { hostname } = new URL(accessUrl);
console.log(`✓ Access URL saved to .env (host: ${hostname})`);
console.log("✓ Setup token cleared (single-use, now dead)");
console.log("→ Next: bun run accounts");
