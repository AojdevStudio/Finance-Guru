#!/usr/bin/env bun
/**
 * Checks a PR body against the contract. The same rules as the gate and CI.
 *
 *   bun check.ts body.md [--title "fix(x): y"] [--draft]   # before opening a PR
 *   bun check.ts --event "$GITHUB_EVENT_PATH"              # in the pr-kit workflow
 *
 * Exit 0 passes, exit 1 lists every violation with its fix.
 */

import { readFileSync } from "node:fs";
import { parseArgs } from "node:util";
import { checkPullRequest, formatViolations, type PullRequest } from "./contract";

const { values, positionals } = parseArgs({
  allowPositionals: true,
  options: { title: { type: "string" }, draft: { type: "boolean" }, event: { type: "string" } },
});

function fromEvent(path: string): PullRequest {
  const event: unknown = JSON.parse(readFileSync(path, "utf8"));
  const pr = typeof event === "object" && event !== null && "pull_request" in event ? event.pull_request : undefined;
  if (typeof pr !== "object" || pr === null) throw new Error(`${path} holds no pull_request payload`);
  const fields: Record<string, unknown> = Object.fromEntries(Object.entries(pr));
  const { title, body, draft } = fields;
  return { title: typeof title === "string" ? title : "", body: typeof body === "string" ? body : "", draft: draft === true };
}

let pr: PullRequest;
if (values.event) {
  pr = fromEvent(values.event);
} else if (positionals[0]) {
  pr = { title: values.title, body: readFileSync(positionals[0], "utf8"), draft: values.draft };
} else {
  console.error('usage: bun check.ts <body.md> [--title "..."] [--draft] | --event <path>');
  process.exit(1);
}

const verdict = checkPullRequest(pr);
if (verdict.ok) {
  console.log(`PR body contract: pass. Door ${verdict.door}, blast radius ${verdict.blastRadius}.`);
} else {
  console.error(`PR body contract: ${verdict.violations.length} violation(s).\n${formatViolations(verdict.violations)}`);
  process.exit(1);
}
