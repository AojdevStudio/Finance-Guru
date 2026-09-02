#!/usr/bin/env bun

import { afterAll, describe, expect, it } from "bun:test";
import { mkdtempSync, readFileSync, realpathSync, rmSync, symlinkSync } from "fs";
import { tmpdir } from "os";
import { dirname, join, resolve } from "path";

const PLUGIN_ROOT = resolve(import.meta.dir, "../../..");
const SETTINGS_PATH = join(PLUGIN_ROOT, ".claude/settings.json");
const TEST_INSTANCE_ROOT = mkdtempSync(join(tmpdir(), "finance-guru-plugin-paths-"));

symlinkSync(join(PLUGIN_ROOT, ".claude"), join(TEST_INSTANCE_ROOT, ".claude"), "dir");

afterAll(() => {
  rmSync(TEST_INSTANCE_ROOT, { recursive: true, force: true });
});

function hookCommands(): string[] {
  const settings = JSON.parse(readFileSync(SETTINGS_PATH, "utf-8"));
  return Object.values(settings.hooks).flatMap((groups: any) =>
    groups.flatMap((group: any) => group.hooks.map((hook: any) => hook.command)),
  );
}

function commandPath(command: string): string {
  const expanded = command.replaceAll("$CLAUDE_PROJECT_DIR", TEST_INSTANCE_ROOT);
  return expanded.replace(/^bun run /, "").replace(/^"|"$/g, "");
}

describe("plugin hook paths", () => {
  it("resolves every project hook through the instance .claude symlink", () => {
    expect(realpathSync(TEST_INSTANCE_ROOT)).not.toBe(realpathSync(PLUGIN_ROOT));

    for (const command of hookCommands()) {
      expect(command).toContain("$CLAUDE_PROJECT_DIR/.claude/hooks/");
      const resolvedHook = realpathSync(commandPath(command));
      expect(dirname(resolvedHook)).toBe(realpathSync(join(PLUGIN_ROOT, ".claude/hooks")));
    }
  });
});
