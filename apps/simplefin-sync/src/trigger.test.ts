import { mkdtemp, readdir, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";

import { describe, expect, test } from "bun:test";

import type { SimpleFinClient } from "./client";
import type { SfinAccount, SfinAccountSet, SfinTransaction } from "./types";
import {
  buildBuyTicketCommand,
  buildBuyTicketEnv,
  createFileSeenStore,
  createMemorySeenStore,
  findNewDepositDetections,
  pollDepositTriggers,
} from "./trigger";

function transaction(overrides: Partial<SfinTransaction>): SfinTransaction {
  return {
    id: "tx-default",
    posted: 1_779_984_000,
    amount: "0.00",
    description: "test transaction",
    ...overrides,
  };
}

function account(transactions: SfinTransaction[]): SfinAccount {
  return {
    id: "account-default",
    name: "Test source",
    currency: "USD",
    balance: "100.00",
    "balance-date": 1_779_984_000,
    org: { name: "Test org" },
    transactions,
  };
}

function accountSet(transactions: SfinTransaction[]): SfinAccountSet {
  return {
    errors: [],
    accounts: [account(transactions)],
  };
}

describe("SimpleFIN deposit trigger", () => {
  test("detects only deposits over the threshold with sanitized keys", async () => {
    const seenStore = createMemorySeenStore();
    const { detections, skippedDuplicates } = await findNewDepositDetections(
      accountSet([
        transaction({ id: "tx-3100", amount: "3100.00" }),
        transaction({ id: "tx-threshold", amount: "3000.00" }),
        transaction({ id: "tx-debit", amount: "-5000.00" }),
      ]),
      seenStore,
    );

    expect(skippedDuplicates).toBe(0);
    expect(detections).toHaveLength(1);
    expect(detections[0].amount).toBe("3100.00");
    expect(detections[0].transactionKey).not.toContain("tx-3100");
    expect(detections[0].sourceAccountKey).not.toContain("account-default");
  });

  test("suppresses duplicate transaction ids within a single poll response", async () => {
    const seenStore = createMemorySeenStore();
    const { detections, skippedDuplicates } = await findNewDepositDetections(
      accountSet([
        transaction({ id: "tx-duplicate", amount: "3100.00" }),
        transaction({ id: "tx-duplicate", amount: "3100.00" }),
      ]),
      seenStore,
    );

    expect(detections).toHaveLength(1);
    expect(skippedDuplicates).toBe(1);
  });

  test("polling triggers once and suppresses duplicate transaction ids", async () => {
    const projectRoot = await mkdtemp(path.join(tmpdir(), "simplefin-trigger-"));
    const seenStore = createMemorySeenStore();
    const calls: string[] = [];
    const client: SimpleFinClient = {
      baseUrl: "https://simplefin.example.test",
      async fetchAccounts() {
        return accountSet([transaction({ id: "tx-1", amount: "3100.00" })]);
      },
    };

    try {
      const first = await pollDepositTriggers({
        client,
        seenStore,
        projectRoot,
        now: new Date("2026-06-05T12:00:00.000Z"),
        trigger: async (detection) => {
          calls.push(detection.transactionKey);
          return {
            status: "triggered",
            exitCode: 0,
            stdoutChars: 10,
            stderrChars: 0,
          };
        },
      });
      const second = await pollDepositTriggers({
        client,
        seenStore,
        projectRoot,
        now: new Date("2026-06-05T16:00:00.000Z"),
        trigger: async (detection) => {
          calls.push(detection.transactionKey);
          return {
            status: "triggered",
            exitCode: 0,
            stdoutChars: 10,
            stderrChars: 0,
          };
        },
      });

      expect(first).toMatchObject({
        detections: 1,
        triggered: 1,
        skippedDuplicates: 0,
        failed: 0,
      });
      expect(second).toMatchObject({
        detections: 0,
        triggered: 0,
        skippedDuplicates: 1,
        failed: 0,
      });
      expect(calls).toHaveLength(1);

      const logDir = path.join(projectRoot, "notebooks", "auto-tickets", "runs");
      const [logFile] = await readdir(logDir);
      const log = JSON.parse(await Bun.file(path.join(logDir, logFile)).text());
      expect(log).toMatchObject({
        event: "simplefin_deposit_detection",
        status: "triggered",
        amount: "3100.00",
      });
      expect(log.transaction_key).toBe(calls[0]);
      expect(log.transaction_key).not.toContain("tx-1");
    } finally {
      await rm(projectRoot, { recursive: true, force: true });
    }
  });

  test("persists seen transaction ids across store instances", async () => {
    const projectRoot = await mkdtemp(path.join(tmpdir(), "simplefin-trigger-"));
    const statePath = path.join(projectRoot, "notebooks", "auto-tickets", "seen.json");
    const client: SimpleFinClient = {
      baseUrl: "https://simplefin.example.test",
      async fetchAccounts() {
        return accountSet([transaction({ id: "tx-1", amount: "3100.00" })]);
      },
    };
    const calls: string[] = [];

    try {
      await pollDepositTriggers({
        client,
        seenStore: createFileSeenStore(statePath),
        projectRoot,
        trigger: async (detection) => {
          calls.push(detection.transactionKey);
          return {
            status: "triggered",
            exitCode: 0,
            stdoutChars: 10,
            stderrChars: 0,
          };
        },
      });
      const second = await pollDepositTriggers({
        client,
        seenStore: createFileSeenStore(statePath),
        projectRoot,
        trigger: async (detection) => {
          calls.push(detection.transactionKey);
          return {
            status: "triggered",
            exitCode: 0,
            stdoutChars: 10,
            stderrChars: 0,
          };
        },
      });

      expect(calls).toHaveLength(1);
      expect(second).toMatchObject({
        detections: 0,
        triggered: 0,
        skippedDuplicates: 1,
      });
      const state = JSON.parse(await Bun.file(statePath).text());
      expect(state.seen).toHaveLength(1);
      expect(state.seen[0]).not.toContain("tx-1");
    } finally {
      await rm(projectRoot, { recursive: true, force: true });
    }
  });

  test("caps repeated failed trigger attempts", async () => {
    const projectRoot = await mkdtemp(path.join(tmpdir(), "simplefin-trigger-"));
    const seenStore = createMemorySeenStore();
    const client: SimpleFinClient = {
      baseUrl: "https://simplefin.example.test",
      async fetchAccounts() {
        return accountSet([transaction({ id: "tx-1", amount: "3100.00" })]);
      },
    };
    const calls: string[] = [];

    try {
      const trigger = async (detection: { transactionKey: string }) => {
        calls.push(detection.transactionKey);
        return {
          status: "failed" as const,
          exitCode: 1,
          stdoutChars: 0,
          stderrChars: 10,
        };
      };
      const first = await pollDepositTriggers({
        client,
        seenStore,
        projectRoot,
        maxFailures: 2,
        trigger,
      });
      const second = await pollDepositTriggers({
        client,
        seenStore,
        projectRoot,
        maxFailures: 2,
        trigger,
      });
      const third = await pollDepositTriggers({
        client,
        seenStore,
        projectRoot,
        maxFailures: 2,
        trigger,
      });

      expect(calls).toHaveLength(2);
      expect(first).toMatchObject({ failed: 1, cappedFailures: 0 });
      expect(second).toMatchObject({ failed: 1, cappedFailures: 1 });
      expect(third).toMatchObject({
        detections: 0,
        skippedDuplicates: 1,
        failed: 0,
      });
    } finally {
      await rm(projectRoot, { recursive: true, force: true });
    }
  });

  test("marks successful triggers even when log writing fails", async () => {
    const projectRoot = await mkdtemp(path.join(tmpdir(), "simplefin-trigger-"));
    const seenStore = createMemorySeenStore();
    const client: SimpleFinClient = {
      baseUrl: "https://simplefin.example.test",
      async fetchAccounts() {
        return accountSet([transaction({ id: "tx-1", amount: "3100.00" })]);
      },
    };
    let transactionKey = "";

    try {
      await Bun.write(path.join(projectRoot, "notebooks"), "not a directory");
      await expect(
        pollDepositTriggers({
          client,
          seenStore,
          projectRoot,
          trigger: async (detection) => {
            transactionKey = detection.transactionKey;
            return {
              status: "triggered",
              exitCode: 0,
              stdoutChars: 10,
              stderrChars: 0,
            };
          },
        }),
      ).rejects.toThrow();

      expect(transactionKey).not.toBe("");
      expect(await seenStore.has(transactionKey)).toBe(true);
    } finally {
      await rm(projectRoot, { recursive: true, force: true });
    }
  });

  test("builds the buy-ticket subprocess command and sanitized trigger env", () => {
    const detection = {
      amount: "3100.00",
      transactionKey: "transaction-key",
      sourceAccountKey: "source-account-key",
      posted: 1_779_984_000,
      pending: false,
    };

    const env = buildBuyTicketEnv(detection, {
      PATH: "/bin",
      SIMPLEFIN_ACCESS_URL: "credential-bearing-url",
      SIMPLEFIN_TRIGGER_INTERVAL_MS: "1000",
    });

    expect(buildBuyTicketCommand()).toEqual([
      "uv",
      "run",
      "python",
      "-m",
      "buy_ticket_agent.main",
      "--smoke",
    ]);
    expect(env).toMatchObject({
      PATH: "/bin",
      BUY_TICKET_TRIGGER_SOURCE: "simplefin_deposit",
      BUY_TICKET_TRIGGER_AMOUNT: "3100.00",
      BUY_TICKET_TRIGGER_ACCOUNT_KEY: "source-account-key",
      BUY_TICKET_TRIGGER_TRANSACTION_KEY: "transaction-key",
    });
    expect(env).not.toHaveProperty("SIMPLEFIN_ACCESS_URL");
    expect(env).not.toHaveProperty("SIMPLEFIN_TRIGGER_INTERVAL_MS");
  });
});
