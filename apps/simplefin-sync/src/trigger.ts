#!/usr/bin/env bun
/**
 * SimpleFIN deposit trigger for the buy-ticket smoke pipeline.
 */
import { createHash } from "node:crypto";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";

import { createClient, toSfinTimestamp, type SimpleFinClient } from "./client";
import type { SfinAccount, SfinAccountSet, SfinTransaction } from "./types";

const DEFAULT_THRESHOLD = "3000.00";
const MONEY_SCALE = 4;
const DEFAULT_POLL_INTERVAL_MS = 4 * 60 * 60 * 1000;

export interface DepositDetection {
  transactionKey: string;
  sourceAccountKey: string;
  amount: string;
  posted: number;
  pending: boolean;
}

export interface TriggerResult {
  status: "triggered" | "failed";
  exitCode: number;
  stdoutChars: number;
  stderrChars: number;
}

export interface SeenTransactionStore {
  has(key: string): boolean | Promise<boolean>;
  mark(key: string): void | Promise<void>;
}

export interface PollOptions {
  client: SimpleFinClient;
  seenStore: SeenTransactionStore;
  projectRoot: string;
  threshold?: string;
  trigger?: (detection: DepositDetection) => Promise<TriggerResult>;
  now?: Date;
  lookbackDays?: number;
}

export interface PollResult {
  scannedAccounts: number;
  detections: number;
  triggered: number;
  skippedDuplicates: number;
  failed: number;
}

export function createMemorySeenStore(
  initialKeys: Iterable<string> = [],
): SeenTransactionStore {
  const seen = new Set(initialKeys);
  return {
    has(key: string) {
      return seen.has(key);
    },
    mark(key: string) {
      seen.add(key);
    },
  };
}

function parseDecimalUnits(value: string): bigint | null {
  const match = value.trim().match(/^([+-]?)(\d+)(?:\.(\d+))?$/);
  if (!match) return null;

  const [, sign, whole, fractionRaw = ""] = match;
  const extra = fractionRaw.slice(MONEY_SCALE);
  if (/[1-9]/.test(extra)) return null;

  const fraction = fractionRaw.slice(0, MONEY_SCALE).padEnd(MONEY_SCALE, "0");
  const units = BigInt(whole) * 10_000n + BigInt(fraction || "0");
  return sign === "-" ? -units : units;
}

export function isDepositOverThreshold(
  transaction: SfinTransaction,
  threshold = DEFAULT_THRESHOLD,
): boolean {
  const amount = parseDecimalUnits(transaction.amount);
  const thresholdUnits = parseDecimalUnits(threshold);
  if (amount === null || thresholdUnits === null) return false;
  return amount > thresholdUnits;
}

function stableKey(...parts: string[]): string {
  return createHash("sha256").update(parts.join("\u001f")).digest("hex").slice(0, 16);
}

export function detectionFromTransaction(
  account: SfinAccount,
  transaction: SfinTransaction,
  threshold = DEFAULT_THRESHOLD,
): DepositDetection | null {
  if (!isDepositOverThreshold(transaction, threshold)) return null;
  return {
    transactionKey: stableKey(account.id, transaction.id),
    sourceAccountKey: stableKey(account.id),
    amount: transaction.amount,
    posted: transaction.posted,
    pending: transaction.pending ?? false,
  };
}

export async function findNewDepositDetections(
  accountSet: SfinAccountSet,
  seenStore: SeenTransactionStore,
  threshold = DEFAULT_THRESHOLD,
): Promise<{ detections: DepositDetection[]; skippedDuplicates: number }> {
  const detections: DepositDetection[] = [];
  const queuedThisPoll = new Set<string>();
  let skippedDuplicates = 0;

  for (const account of accountSet.accounts) {
    for (const transaction of account.transactions ?? []) {
      const detection = detectionFromTransaction(account, transaction, threshold);
      if (!detection) continue;

      if (
        queuedThisPoll.has(detection.transactionKey) ||
        (await seenStore.has(detection.transactionKey))
      ) {
        skippedDuplicates += 1;
        continue;
      }
      queuedThisPoll.add(detection.transactionKey);
      detections.push(detection);
    }
  }

  return { detections, skippedDuplicates };
}

export function buildBuyTicketCommand(): string[] {
  return ["uv", "run", "python", "-m", "buy_ticket_agent.main", "--smoke"];
}

export function buildBuyTicketEnv(
  detection: DepositDetection,
  baseEnv: NodeJS.ProcessEnv = process.env,
): NodeJS.ProcessEnv {
  return {
    ...baseEnv,
    BUY_TICKET_TRIGGER_SOURCE: "simplefin_deposit",
    BUY_TICKET_TRIGGER_AMOUNT: detection.amount,
    BUY_TICKET_TRIGGER_ACCOUNT_KEY: detection.sourceAccountKey,
    BUY_TICKET_TRIGGER_TRANSACTION_KEY: detection.transactionKey,
  };
}

async function countStreamChars(stream: ReadableStream<Uint8Array>): Promise<number> {
  const decoder = new TextDecoder();
  const reader = stream.getReader();
  let chars = 0;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    chars += decoder.decode(value, { stream: true }).length;
  }

  chars += decoder.decode().length;
  return chars;
}

export async function runBuyTicketSubprocess(
  detection: DepositDetection,
  projectRoot: string,
): Promise<TriggerResult> {
  const proc = Bun.spawn(buildBuyTicketCommand(), {
    cwd: projectRoot,
    env: buildBuyTicketEnv(detection),
    stdout: "pipe",
    stderr: "pipe",
  });

  const [stdoutChars, stderrChars, exitCode] = await Promise.all([
    countStreamChars(proc.stdout),
    countStreamChars(proc.stderr),
    proc.exited,
  ]);

  return {
    status: exitCode === 0 ? "triggered" : "failed",
    exitCode,
    stdoutChars,
    stderrChars,
  };
}

async function writeTriggerLog(
  projectRoot: string,
  detection: DepositDetection,
  result: TriggerResult,
  now: Date,
): Promise<void> {
  const logDir = path.join(projectRoot, "notebooks", "auto-tickets", "runs");
  const logPath = path.join(
    logDir,
    `simplefin-trigger-${now.toISOString().replace(/[:.]/g, "-")}-${detection.transactionKey}.json`,
  );
  const payload = {
    event: "simplefin_deposit_detection",
    created_at: now.toISOString(),
    status: result.status,
    amount: detection.amount,
    source_account_key: detection.sourceAccountKey,
    transaction_key: detection.transactionKey,
    posted: detection.posted,
    pending: detection.pending,
    buy_ticket: result,
  };

  await mkdir(logDir, { recursive: true });
  await writeFile(logPath, `${JSON.stringify(payload, null, 2)}\n`);
}

export async function pollDepositTriggers(options: PollOptions): Promise<PollResult> {
  const now = options.now ?? new Date();
  const lookbackDays = options.lookbackDays ?? 7;
  const startDate = toSfinTimestamp(
    new Date(now.valueOf() - lookbackDays * 24 * 60 * 60 * 1000),
  );
  const accountSet = await options.client.fetchAccounts({
    startDate,
    pending: true,
  });
  const { detections, skippedDuplicates } = await findNewDepositDetections(
    accountSet,
    options.seenStore,
    options.threshold,
  );
  const trigger =
    options.trigger ??
    ((detection: DepositDetection) =>
      runBuyTicketSubprocess(detection, options.projectRoot));

  let triggered = 0;
  let failed = 0;
  for (const detection of detections) {
    const result = await trigger(detection);
    await writeTriggerLog(options.projectRoot, detection, result, now);
    if (result.status === "triggered") {
      await options.seenStore.mark(detection.transactionKey);
      triggered += 1;
    } else {
      failed += 1;
    }
  }

  return {
    scannedAccounts: accountSet.accounts.length,
    detections: detections.length,
    triggered,
    skippedDuplicates,
    failed,
  };
}

async function runCli(argv: string[]): Promise<number> {
  const accessUrl = process.env.SIMPLEFIN_ACCESS_URL?.trim();
  if (!accessUrl) {
    console.error("SIMPLEFIN_ACCESS_URL is empty. Run `bun run claim` first.");
    return 1;
  }

  const projectRoot = path.resolve(import.meta.dir, "..", "..", "..");
  const client = createClient(accessUrl);
  const seenStore = createMemorySeenStore();
  const watch = argv.includes("--watch");
  const intervalMs =
    Number(process.env.SIMPLEFIN_TRIGGER_INTERVAL_MS ?? "") ||
    DEFAULT_POLL_INTERVAL_MS;

  do {
    const result = await pollDepositTriggers({
      client,
      seenStore,
      projectRoot,
    });
    console.log(JSON.stringify(result));
    if (!watch) break;
    await Bun.sleep(intervalMs);
  } while (true);

  return 0;
}

if (import.meta.main) {
  const exitCode = await runCli(Bun.argv.slice(2));
  process.exit(exitCode);
}
