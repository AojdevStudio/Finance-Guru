import path from "node:path";

import { describe, expect, test } from "bun:test";

async function runDump(months: string): Promise<{
  exitCode: number;
  stderr: string;
}> {
  const proc = Bun.spawn([process.execPath, "run", path.join(import.meta.dir, "dump.ts"), months], {
    cwd: path.resolve(import.meta.dir, ".."),
    env: {
      ...process.env,
      SIMPLEFIN_ACCESS_URL: "invalid-for-months-test",
    },
    stdout: "pipe",
    stderr: "pipe",
  });
  const [exitCode, stderr] = await Promise.all([
    proc.exited,
    new Response(proc.stderr).text(),
  ]);
  return { exitCode, stderr };
}

describe("SimpleFIN dump CLI", () => {
  test.each(["not-a-number", "0", "-1", "1.5", "121"])(
    "rejects invalid months value %s before creating the client",
    async (months) => {
      const result = await runDump(months);

      expect(result.exitCode).toBe(1);
      expect(result.stderr).toContain(
        `months must be a whole number between 1 and 120, got "${months}"`,
      );
      expect(result.stderr).not.toContain("SIMPLEFIN_ACCESS_URL");
    },
  );
});
