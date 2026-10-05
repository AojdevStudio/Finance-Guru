#!/usr/bin/env bun

import { afterAll, describe, expect, it } from "bun:test";
import { mkdtempSync, readFileSync, realpathSync, rmSync, symlinkSync } from "fs";
import { tmpdir } from "os";
import { dirname, join, resolve } from "path";

const PLUGIN_ROOT = resolve(import.meta.dir, "../../..");
const SETTINGS_PATH = join(PLUGIN_ROOT, ".claude/settings.json");
const PLUGIN_HOOKS_PATH = join(PLUGIN_ROOT, "hooks/hooks.json");
const TEST_INSTANCE_ROOT = mkdtempSync(join(tmpdir(), "finance-guru-plugin-paths-"));

symlinkSync(join(PLUGIN_ROOT, ".claude"), join(TEST_INSTANCE_ROOT, ".claude"), "dir");

afterAll(() => {
  rmSync(TEST_INSTANCE_ROOT, { recursive: true, force: true });
});

interface HookHandler {
  command: string;
  args?: string[];
}
type HookEvents = Record<string, { hooks: HookHandler[] }[]>;

function handlers(path: string): HookHandler[] {
  const events: HookEvents = JSON.parse(readFileSync(path, "utf-8")).hooks;
  return Object.values(events).flatMap((groups) => groups.flatMap((group) => group.hooks));
}

function hookCommands(): string[] {
  return handlers(SETTINGS_PATH).map((hook) => hook.command);
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

  it("ships the session-start loader through the plugin hooks file", () => {
    const events = JSON.parse(readFileSync(PLUGIN_HOOKS_PATH, "utf-8")).hooks;

    expect(Object.keys(events)).toEqual(["SessionStart"]);
    for (const handler of handlers(PLUGIN_HOOKS_PATH)) {
      expect(handler.command).toBe("bun");
      const script = handler.args?.at(-1) ?? "";
      expect(script.startsWith("${CLAUDE_PLUGIN_ROOT}/.claude/hooks/")).toBe(true);
      expect(realpathSync(script.replace("${CLAUDE_PLUGIN_ROOT}", PLUGIN_ROOT))).toBe(
        realpathSync(join(PLUGIN_ROOT, ".claude/hooks/load-fin-core-config.ts")),
      );
    }
  });
});
