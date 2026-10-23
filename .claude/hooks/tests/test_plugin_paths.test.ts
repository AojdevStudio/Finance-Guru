#!/usr/bin/env bun

import { describe, expect, it } from "bun:test";
import { readFileSync, realpathSync } from "fs";
import { join, resolve } from "path";

const PLUGIN_ROOT = resolve(import.meta.dir, "../../..");
const SETTINGS_PATH = join(PLUGIN_ROOT, ".claude/settings.json");
const PLUGIN_HOOKS_PATH = join(PLUGIN_ROOT, "hooks/hooks.json");
interface HookHandler {
  type: "command";
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

describe("plugin hook paths", () => {
  it("resolves product and developer hooks from the repository", () => {
    const scripts = [
      ".claude/hooks/load-fin-core-config.ts",
      ".claude/hooks/post-tool-use-tracker.ts",
      ".claude/hooks/stop-build-check-enhanced.sh",
      ".dev/pr-kit/open-pr/gate.ts",
    ];
    expect(hookCommands()).toEqual([
      `bun run $CLAUDE_PROJECT_DIR/${scripts[0]}`,
      `bun run $CLAUDE_PROJECT_DIR/${scripts[1]}`,
      `$CLAUDE_PROJECT_DIR/${scripts[2]}`,
      `bun "$CLAUDE_PROJECT_DIR/${scripts[3]}"`,
    ]);
    for (const script of scripts) {
      expect(realpathSync(join(PLUGIN_ROOT, script))).toBe(join(PLUGIN_ROOT, script));
    }
    expect(JSON.parse(readFileSync(SETTINGS_PATH, "utf-8")).hooks.PreToolUse).toEqual([{
      matcher: "Bash",
      hooks: [{
        type: "command",
        command: 'bun "$CLAUDE_PROJECT_DIR/.dev/pr-kit/open-pr/gate.ts"',
        timeout: 120,
        onFailure: "block",
      }],
    }]);
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
